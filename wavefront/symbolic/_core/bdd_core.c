/* A reduced ordered BDD manager in C11, the compiled core of wavefront.symbolic.
 *
 * The semantics are those of the reference manager wavefront/symbolic/bdd.py, operation
 * by operation: the same canonical form (complement edges, TRUE = 0, FALSE = 1, the hi
 * edge of a stored node never complemented), the same recursions and terminal cases, so
 * every operation returns the same function, and the canonical-form queries (node_count,
 * support, pick_one, count) the same values. See docs/engine_scaling.md section 7.
 *
 * Tables
 *   - Nodes: three uint32_t arrays var, lo, hi, grown by doubling. A free node has
 *     var = BDD_TERMVAR and is chained through lo (free list, last freed first reused).
 *     During a collection the top bit of var marks a live node.
 *   - Unique table: open addressing with linear probing; an 8-byte slot holds the node
 *     index (0 = empty) and the top 32 bits of the hash of its key (var, lo, hi), so that a
 *     probe reads the node arrays only when the tags agree. It doubles past a load of 0.7
 *     and is rebuilt by every collection.
 *   - Computed tables (and, xor, ite, exists, and_exists): open addressing in buckets of
 *     WAYS = 4 entries of 16 bytes (one 64-byte line). A table doubles past a load of 0.5
 *     until it reaches its cap, the power of two at or above the node table's capacity
 *     (between CACHE_MIN and CACHE_MAX entries); at the cap, an entry whose bucket is full
 *     replaces one of its ways (a lossy cache). A collection drops, in place, the entries
 *     that mention a reclaimed node and keeps the others; nothing else clears a computed
 *     table.
 *   - Per-call memo tables (restrict, simplify, compose, rename, transfer, count) are
 *     open-addressing maps from a 64-bit key, freed when the call returns.
 *
 * Errors: an operation that runs out of memory (or past BDD_MAX_NODES) unwinds with
 * longjmp to its entry point, which frees the per-call tables and returns BDD_ERR. Nodes
 * built before the failure are garbage for the next collection. */
#include "bdd_core.h"

#include <setjmp.h>
#include <stdlib.h>
#include <string.h>

/* Each entry point stores the address of its own jmp_buf in the manager for the length of
 * the call; the pointer is never used after the call returns. */
#if defined(__GNUC__) && !defined(__clang__) && __GNUC__ >= 12
#pragma GCC diagnostic ignored "-Wdangling-pointer"
#pragma GCC diagnostic ignored "-Wclobbered" /* arguments are not modified after setjmp */
#endif

#ifndef BDD_SOURCE_HASH
#define BDD_SOURCE_HASH "unknown"
#endif

#define MARK 0x80000000u
#define VMASK 0x7FFFFFFFu
#define NODE_INIT (1u << 10)
#define UNIQUE_INIT (1u << 11)
#define CACHE_INIT (1u << 10)
#define CACHE_MIN (1u << 18)
#define CACHE_MAX (1u << 25)
#define WAYS 4 /* entries per computed-table bucket: one 64-byte line */
#define NTMP 4

/* A computed-table entry: key (a, b, c), result r; a = 0 marks an empty slot (every cached
 * operation has a first operand above 1). Two-operand tables leave c = 0. */
typedef struct {
    uint32_t a, b, c, r;
} cent;

typedef struct {
    cent *e;
    size_t bmask; /* buckets - 1 */
    size_t count;
} cache;

/* A unique-table slot: the node index (n = 0: empty) and the top 32 bits of its key's hash,
 * so that most probes that miss do not read the node arrays. */
typedef struct {
    uint32_t n, tag;
} uent;

typedef struct {
    uint8_t *mask;
    int32_t maxv;
} varset_t;

typedef struct {
    uint64_t *keys; /* 0 = empty */
    uint32_t *vals;
    size_t mask, count;
} map64;

struct bdd_mgr {
    uint32_t *var, *lo, *hi;
    uint32_t cap, used, free_head, nfree;
    size_t ccap; /* the computed tables' cap */
    uent *utab;
    size_t umask, ucount;
    cache cand, cxor, cex, cite, cae;
    varset_t *vs;
    uint32_t nvs, vscap;
    uint32_t nvars;
    uint64_t gc_runs;
    uint32_t err_level;
    map64 memo;
    void *tmp[NTMP];
    uint32_t *stk, *vis;
    size_t stk_cap, vis_cap;
    jmp_buf *jbp;
};

/* Node fields: the nodes are a struct of three arrays. */
#define VAR(m, n) ((m)->var[n])
#define LO(m, n) ((m)->lo[n])
#define HI(m, n) ((m)->hi[n])

/* -- helpers ---------------------------------------------------------------------------- */

static inline uint64_t mix64(uint64_t x) {
    x ^= x >> 33;
    x *= 0xff51afd7ed558ccdULL;
    x ^= x >> 33;
    x *= 0xc4ceb9fe1a85ec53ULL;
    x ^= x >> 33;
    return x;
}

static inline uint64_t hash2(uint32_t a, uint32_t b) {
    return mix64(((uint64_t)a << 32) | b);
}

static inline uint64_t hash3(uint32_t a, uint32_t b, uint32_t c) {
    return mix64((((uint64_t)a << 32) | b) ^ ((uint64_t)c * 0x9E3779B97F4A7C15ULL));
}

static void fail(bdd_mgr *m) { longjmp(*m->jbp, 1); }

static void map_free(map64 *mp) {
    free(mp->keys);
    free(mp->vals);
    mp->keys = NULL;
    mp->vals = NULL;
    mp->mask = mp->count = 0;
}

static void cleanup(bdd_mgr *m) {
    map_free(&m->memo);
    for (int i = 0; i < NTMP; i++) {
        free(m->tmp[i]);
        m->tmp[i] = NULL;
    }
}

/* Every exported operation that may allocate starts with GUARD: on failure it frees the
 * per-call tables and returns errret. */
#define GUARD(m, errret)                                                                     \
    jmp_buf jb_;                                                                             \
    if (setjmp(jb_)) {                                                                       \
        cleanup(m);                                                                          \
        return errret;                                                                       \
    }                                                                                        \
    (m)->jbp = &jb_

static void map_init(bdd_mgr *m, map64 *mp, size_t cap) {
    size_t size = 64;
    while (size < 2 * cap) size <<= 1;
    mp->keys = calloc(size, sizeof(uint64_t));
    mp->vals = malloc(size * sizeof(uint32_t));
    if (!mp->keys || !mp->vals) {
        map_free(mp);
        fail(m);
    }
    mp->mask = size - 1;
    mp->count = 0;
}

static inline int map_get(const map64 *mp, uint64_t key, uint32_t *val) {
    size_t h = mix64(key) & mp->mask;
    for (;;) {
        uint64_t k = mp->keys[h];
        if (k == key) {
            *val = mp->vals[h];
            return 1;
        }
        if (k == 0) return 0;
        h = (h + 1) & mp->mask;
    }
}

static void map_put(bdd_mgr *m, map64 *mp, uint64_t key, uint32_t val) {
    if (2 * (mp->count + 1) > mp->mask + 1) {
        size_t size = 2 * (mp->mask + 1);
        uint64_t *keys = calloc(size, sizeof(uint64_t));
        uint32_t *vals = malloc(size * sizeof(uint32_t));
        if (!keys || !vals) {
            free(keys);
            free(vals);
            fail(m);
        }
        for (size_t i = 0; i <= mp->mask; i++) {
            uint64_t k = mp->keys[i];
            if (!k) continue;
            size_t h = mix64(k) & (size - 1);
            while (keys[h]) h = (h + 1) & (size - 1);
            keys[h] = k;
            vals[h] = mp->vals[i];
        }
        free(mp->keys);
        free(mp->vals);
        mp->keys = keys;
        mp->vals = vals;
        mp->mask = size - 1;
    }
    size_t h = mix64(key) & mp->mask;
    for (;;) {
        uint64_t k = mp->keys[h];
        if (k == key) {
            mp->vals[h] = val;
            return;
        }
        if (k == 0) {
            mp->keys[h] = key;
            mp->vals[h] = val;
            mp->count++;
            return;
        }
        h = (h + 1) & mp->mask;
    }
}

static void *tmp_alloc(bdd_mgr *m, int slot, size_t bytes) {
    void *p = realloc(m->tmp[slot], bytes ? bytes : 1);
    if (!p) fail(m);
    m->tmp[slot] = p;
    return p;
}

static void tmp_release(bdd_mgr *m) {
    for (int i = 0; i < NTMP; i++) {
        free(m->tmp[i]);
        m->tmp[i] = NULL;
    }
}

/* -- computed tables -------------------------------------------------------------------- */

static void set_cache_cap(bdd_mgr *m) {
    size_t cap = CACHE_MIN;
    while (cap < m->cap && cap < CACHE_MAX) cap <<= 1;
    m->ccap = cap;
}

static cent *cent_alloc(size_t entries) {
    cent *e = aligned_alloc(64, entries * sizeof(cent));
    if (e) memset(e, 0, entries * sizeof(cent));
    return e;
}

static int cache_init(cache *c) {
    c->e = cent_alloc(CACHE_INIT);
    c->bmask = CACHE_INIT / WAYS - 1;
    c->count = 0;
    return c->e != NULL;
}

static inline int cget(const cache *c, uint32_t a, uint32_t b, uint32_t cc, uint32_t *r) {
    const cent *e = c->e + (hash3(a, b, cc) & c->bmask) * WAYS;
    for (int i = 0; i < WAYS; i++) {
        if (e[i].a == a && e[i].b == b && e[i].c == cc) {
            *r = e[i].r;
            return 1;
        }
    }
    return 0;
}

/* Store into the bucket: the same key, else an empty way, else the way the hash names. */
static void cplace(cent *tab, size_t bmask, size_t *count, uint32_t a, uint32_t b, uint32_t cc,
                   uint32_t r) {
    uint64_t h = hash3(a, b, cc);
    cent *e = tab + (h & bmask) * WAYS;
    cent *slot = NULL;
    for (int i = 0; i < WAYS; i++) {
        if (e[i].a == a && e[i].b == b && e[i].c == cc) {
            e[i].r = r;
            return;
        }
        if (!slot && e[i].a == 0) slot = &e[i];
    }
    if (slot)
        (*count)++;
    else
        slot = &e[(h >> 60) & (WAYS - 1)]; /* lossy: replace one way */
    slot->a = a;
    slot->b = b;
    slot->c = cc;
    slot->r = r;
}

static void cache_grow(cache *c) {
    size_t buckets = 2 * (c->bmask + 1);
    cent *tab = cent_alloc(buckets * WAYS);
    if (!tab) return; /* keep the old table */
    size_t count = 0;
    for (size_t i = 0; i < (c->bmask + 1) * WAYS; i++)
        if (c->e[i].a) cplace(tab, buckets - 1, &count, c->e[i].a, c->e[i].b, c->e[i].c, c->e[i].r);
    free(c->e);
    c->e = tab;
    c->bmask = buckets - 1;
    c->count = count;
}

static inline void cput(const bdd_mgr *m, cache *c, uint32_t a, uint32_t b, uint32_t cc,
                        uint32_t r) {
    size_t slots = (c->bmask + 1) * WAYS;
    if (2 * (c->count + 1) > slots && slots < m->ccap) cache_grow(c);
    cplace(c->e, c->bmask, &c->count, a, b, cc, r);
}

/* -- manager ---------------------------------------------------------------------------- */

const char *bdd_core_source_hash(void) { return BDD_SOURCE_HASH; }

void bdd_delete(bdd_mgr *m) {
    if (!m) return;
    free(m->var);
    free(m->lo);
    free(m->hi);
    free(m->utab);
    free(m->cand.e);
    free(m->cxor.e);
    free(m->cex.e);
    free(m->cite.e);
    free(m->cae.e);
    for (uint32_t i = 0; i < m->nvs; i++) free(m->vs[i].mask);
    free(m->vs);
    cleanup(m);
    free(m->stk);
    free(m->vis);
    free(m);
}

bdd_mgr *bdd_new(void) {
    bdd_mgr *m = calloc(1, sizeof(bdd_mgr));
    if (!m) return NULL;
    m->var = malloc(NODE_INIT * sizeof(uint32_t));
    m->lo = malloc(NODE_INIT * sizeof(uint32_t));
    m->hi = malloc(NODE_INIT * sizeof(uint32_t));
    m->utab = calloc(UNIQUE_INIT, sizeof(uent));
    int ok = m->var && m->lo && m->hi && m->utab;
    ok = ok && cache_init(&m->cand) && cache_init(&m->cxor) && cache_init(&m->cex);
    ok = ok && cache_init(&m->cite) && cache_init(&m->cae);
    if (!ok) {
        bdd_delete(m);
        return NULL;
    }
    m->cap = NODE_INIT;
    set_cache_cap(m);
    m->used = 1;
    VAR(m, 0) = BDD_TERMVAR;
    LO(m, 0) = 0;
    HI(m, 0) = 0;
    m->umask = UNIQUE_INIT - 1;
    return m;
}

int32_t bdd_add_var(bdd_mgr *m) {
    if (m->nvars >= BDD_MAX_VARS) return -1;
    return (int32_t)m->nvars++;
}

uint32_t bdd_num_vars(const bdd_mgr *m) { return m->nvars; }
uint32_t bdd_top(const bdd_mgr *m, uint32_t f) { return VAR(m, f >> 1); }
uint32_t bdd_low(const bdd_mgr *m, uint32_t f) { return LO(m, f >> 1) ^ (f & 1); }
uint32_t bdd_high(const bdd_mgr *m, uint32_t f) { return HI(m, f >> 1) ^ (f & 1); }
uint32_t bdd_live_nodes(const bdd_mgr *m) { return m->used - m->nfree; }
uint32_t bdd_table_nodes(const bdd_mgr *m) { return m->used; }
uint32_t bdd_error_level(const bdd_mgr *m) { return m->err_level; }

/* -- node construction ------------------------------------------------------------------ */

static inline uint64_t unique_hash(uint32_t v, uint32_t lo, uint32_t hi) {
    return hash3(v, lo, hi);
}

static void unique_insert(uent *tab, size_t mask, uint64_t h, uint32_t n) {
    size_t i = h & mask;
    while (tab[i].n) i = (i + 1) & mask;
    tab[i].n = n;
    tab[i].tag = (uint32_t)(h >> 32);
}

static void unique_grow(bdd_mgr *m) {
    size_t size = 2 * (m->umask + 1);
    uent *tab = calloc(size, sizeof(uent));
    if (!tab) fail(m);
    for (size_t i = 0; i <= m->umask; i++) {
        uint32_t n = m->utab[i].n;
        if (n) unique_insert(tab, size - 1, unique_hash(VAR(m, n), LO(m, n), HI(m, n)), n);
    }
    free(m->utab);
    m->utab = tab;
    m->umask = size - 1;
}

static void nodes_grow(bdd_mgr *m) {
    if (m->cap >= BDD_MAX_NODES) fail(m);
    uint64_t want = (uint64_t)m->cap * 2;
    if (want > BDD_MAX_NODES) want = BDD_MAX_NODES;
    size_t bytes = (size_t)want * sizeof(uint32_t);
    uint32_t *v = realloc(m->var, bytes);
    if (!v) fail(m);
    m->var = v;
    uint32_t *l = realloc(m->lo, bytes);
    if (!l) fail(m);
    m->lo = l;
    uint32_t *h = realloc(m->hi, bytes);
    if (!h) fail(m);
    m->hi = h;
    m->cap = (uint32_t)want;
    set_cache_cap(m);
}

static uint32_t mk(bdd_mgr *m, uint32_t v, uint32_t low, uint32_t high) {
    if (low == high) return low;
    uint32_t neg = high & 1;
    if (neg) {
        low ^= 1;
        high ^= 1;
    }
    uint64_t hk = unique_hash(v, low, high);
    uint32_t tag = (uint32_t)(hk >> 32);
    size_t h = hk & m->umask;
    for (;;) {
        uint32_t n = m->utab[h].n;
        if (!n) break;
        if (m->utab[h].tag == tag && LO(m, n) == low && HI(m, n) == high && VAR(m, n) == v)
            return n << 1 | neg;
        h = (h + 1) & m->umask;
    }
    if (10 * (m->ucount + 1) > 7 * (m->umask + 1)) {
        unique_grow(m);
        h = hk & m->umask;
        while (m->utab[h].n) h = (h + 1) & m->umask;
    }
    uint32_t n;
    if (m->free_head) {
        n = m->free_head;
        m->free_head = LO(m, n);
        m->nfree--;
    } else {
        if (m->used >= m->cap) nodes_grow(m);
        n = m->used++;
    }
    VAR(m, n) = v;
    LO(m, n) = low;
    HI(m, n) = high;
    m->utab[h].n = n;
    m->utab[h].tag = tag;
    m->ucount++;
    return n << 1 | neg;
}

uint32_t bdd_mk(bdd_mgr *m, uint32_t level, uint32_t lo, uint32_t hi) {
    GUARD(m, BDD_ERR);
    return mk(m, level, lo, hi);
}

/* -- AND, XOR, ITE ---------------------------------------------------------------------- */

static uint32_t and_rec(bdd_mgr *m, uint32_t f, uint32_t g) {
    if (f == g) return f;
    if (f > g) {
        uint32_t t = f;
        f = g;
        g = t;
    }
    if (f <= 1) return f == 0 ? g : 1;
    if ((f ^ g) == 1) return 1;
    uint32_t r;
    if (cget(&m->cand, f, g, 0, &r)) return r;
    uint32_t nf = f >> 1, ng = g >> 1;
    uint32_t vf = VAR(m, nf), vg = VAR(m, ng);
    uint32_t v, f0, f1, g0, g1;
    if (vf <= vg) {
        uint32_t c = f & 1;
        f0 = LO(m, nf) ^ c;
        f1 = HI(m, nf) ^ c;
        v = vf;
    } else {
        f0 = f1 = f;
        v = vg;
    }
    if (vg == v) {
        uint32_t c = g & 1;
        g0 = LO(m, ng) ^ c;
        g1 = HI(m, ng) ^ c;
    } else {
        g0 = g1 = g;
    }
    uint32_t r0 = and_rec(m, f0, g0);
    uint32_t r1 = and_rec(m, f1, g1);
    r = r0 != r1 ? mk(m, v, r0, r1) : r0;
    cput(m, &m->cand, f, g, 0, r);
    return r;
}

static inline uint32_t or_rec(bdd_mgr *m, uint32_t f, uint32_t g) {
    return and_rec(m, f ^ 1, g ^ 1) ^ 1;
}

static uint32_t xor_rec(bdd_mgr *m, uint32_t f, uint32_t g) {
    uint32_t neg = (f ^ g) & 1;
    f &= ~1u;
    g &= ~1u;
    if (f == g) return 1 ^ neg;
    if (f > g) {
        uint32_t t = f;
        f = g;
        g = t;
    }
    if (f == 0) return g ^ 1 ^ neg;
    uint32_t r;
    if (!cget(&m->cxor, f, g, 0, &r)) {
        uint32_t nf = f >> 1, ng = g >> 1;
        uint32_t vf = VAR(m, nf), vg = VAR(m, ng);
        uint32_t v, f0, f1, g0, g1;
        if (vf <= vg) {
            f0 = LO(m, nf);
            f1 = HI(m, nf);
            v = vf;
        } else {
            f0 = f1 = f;
            v = vg;
        }
        if (vg == v) {
            g0 = LO(m, ng);
            g1 = HI(m, ng);
        } else {
            g0 = g1 = g;
        }
        uint32_t r0 = xor_rec(m, f0, g0);
        uint32_t r1 = xor_rec(m, f1, g1);
        r = mk(m, v, r0, r1);
        cput(m, &m->cxor, f, g, 0, r);
    }
    return r ^ neg;
}

static uint32_t ite_rec(bdd_mgr *m, uint32_t f, uint32_t g, uint32_t h) {
    if (f <= 1) return f == 0 ? g : h;
    if (g == h) return g;
    if (g == f)
        g = 0;
    else if (g == (f ^ 1))
        g = 1;
    if (h == f)
        h = 1;
    else if (h == (f ^ 1))
        h = 0;
    if (g == h) return g;
    if (g <= 1) {
        if (h <= 1) return g == 0 ? f : f ^ 1;
        if (g == 0) return and_rec(m, f ^ 1, h ^ 1) ^ 1;
        return and_rec(m, f ^ 1, h);
    }
    if (h <= 1) {
        if (h == 1) return and_rec(m, f, g);
        return and_rec(m, f, g ^ 1) ^ 1;
    }
    if (g == (h ^ 1)) return xor_rec(m, f, h);
    if (f & 1) {
        uint32_t t = g;
        f ^= 1;
        g = h;
        h = t;
    }
    uint32_t neg = g & 1;
    if (neg) {
        g ^= 1;
        h ^= 1;
    }
    uint32_t r;
    if (!cget(&m->cite, f, g, h, &r)) {
        uint32_t nf = f >> 1, ng = g >> 1, nh = h >> 1;
        uint32_t vf = VAR(m, nf), vg = VAR(m, ng), vh = VAR(m, nh);
        uint32_t v = vf;
        if (vg < v) v = vg;
        if (vh < v) v = vh;
        uint32_t f0, f1, g0, g1, h0, h1;
        if (vf == v) {
            f0 = LO(m, nf);
            f1 = HI(m, nf);
        } else {
            f0 = f1 = f;
        }
        if (vg == v) {
            g0 = LO(m, ng);
            g1 = HI(m, ng);
        } else {
            g0 = g1 = g;
        }
        if (vh == v) {
            uint32_t c = h & 1;
            h0 = LO(m, nh) ^ c;
            h1 = HI(m, nh) ^ c;
        } else {
            h0 = h1 = h;
        }
        uint32_t r0 = ite_rec(m, f0, g0, h0);
        uint32_t r1 = ite_rec(m, f1, g1, h1);
        r = mk(m, v, r0, r1);
        cput(m, &m->cite, f, g, h, r);
    }
    return r ^ neg;
}

uint32_t bdd_and(bdd_mgr *m, uint32_t f, uint32_t g) {
    GUARD(m, BDD_ERR);
    return and_rec(m, f, g);
}

uint32_t bdd_xor(bdd_mgr *m, uint32_t f, uint32_t g) {
    GUARD(m, BDD_ERR);
    return xor_rec(m, f, g);
}

uint32_t bdd_ite(bdd_mgr *m, uint32_t f, uint32_t g, uint32_t h) {
    GUARD(m, BDD_ERR);
    return ite_rec(m, f, g, h);
}

uint32_t bdd_and_all(bdd_mgr *m, const uint32_t *fs, size_t count) {
    if (count == 0) return 0;
    GUARD(m, BDD_ERR);
    uint32_t *items = tmp_alloc(m, 0, count * sizeof(uint32_t));
    memcpy(items, fs, count * sizeof(uint32_t));
    size_t n = count;
    while (n > 1) { /* balanced, as in the reference */
        size_t k = 0;
        for (size_t i = 0; i + 1 < n; i += 2) items[k++] = and_rec(m, items[i], items[i + 1]);
        if (n % 2) items[k++] = items[n - 1];
        n = k;
    }
    uint32_t r = items[0];
    tmp_release(m);
    return r;
}

uint32_t bdd_cube(bdd_mgr *m, const uint32_t *levels, const uint8_t *vals, size_t n) {
    GUARD(m, BDD_ERR);
    uint32_t f = 0;
    for (size_t i = 0; i < n; i++) /* levels from the bottom up */
        f = vals[i] ? mk(m, levels[i], 1, f) : mk(m, levels[i], f, 1);
    return f;
}

/* -- quantification --------------------------------------------------------------------- */

int32_t bdd_varset(bdd_mgr *m, const uint32_t *levels, size_t n) {
    if (m->nvs == m->vscap) {
        uint32_t cap = m->vscap ? 2 * m->vscap : 16;
        varset_t *vs = realloc(m->vs, cap * sizeof(varset_t));
        if (!vs) return -1;
        m->vs = vs;
        m->vscap = cap;
    }
    int32_t maxv = -1;
    for (size_t i = 0; i < n; i++)
        if ((int32_t)levels[i] > maxv) maxv = (int32_t)levels[i];
    uint8_t *mask = calloc((size_t)maxv + 2, 1);
    if (!mask) return -1;
    for (size_t i = 0; i < n; i++) mask[levels[i]] = 1;
    m->vs[m->nvs].mask = mask;
    m->vs[m->nvs].maxv = maxv;
    return (int32_t)m->nvs++;
}

static uint32_t ex_rec(bdd_mgr *m, uint32_t f, const varset_t *vs, uint32_t sid) {
    if (f <= 1) return f;
    uint32_t n = f >> 1;
    uint32_t v = VAR(m, n);
    if ((int32_t)v > vs->maxv) return f;
    uint32_t r;
    if (cget(&m->cex, f, sid, 0, &r)) return r;
    uint32_t c = f & 1;
    uint32_t f0 = LO(m, n) ^ c, f1 = HI(m, n) ^ c;
    if (vs->mask[v]) {
        uint32_t r0 = ex_rec(m, f0, vs, sid);
        if (r0 == 0)
            r = 0;
        else
            r = or_rec(m, r0, ex_rec(m, f1, vs, sid));
    } else {
        uint32_t r0 = ex_rec(m, f0, vs, sid);
        uint32_t r1 = ex_rec(m, f1, vs, sid);
        r = r0 != r1 ? mk(m, v, r0, r1) : r0;
    }
    cput(m, &m->cex, f, sid, 0, r);
    return r;
}

static uint32_t ae_rec(bdd_mgr *m, uint32_t f, uint32_t g, const varset_t *vs, uint32_t sid) {
    if (f == g) return ex_rec(m, f, vs, sid);
    if (f > g) {
        uint32_t t = f;
        f = g;
        g = t;
    }
    if (f <= 1) return f == 0 ? ex_rec(m, g, vs, sid) : 1;
    if ((f ^ g) == 1) return 1;
    uint32_t nf = f >> 1, ng = g >> 1;
    uint32_t vf = VAR(m, nf), vg = VAR(m, ng);
    uint32_t v = vf < vg ? vf : vg;
    if ((int32_t)v > vs->maxv) return and_rec(m, f, g);
    uint32_t r;
    if (cget(&m->cae, f, g, sid, &r)) return r;
    uint32_t f0, f1, g0, g1;
    if (vf == v) {
        uint32_t c = f & 1;
        f0 = LO(m, nf) ^ c;
        f1 = HI(m, nf) ^ c;
    } else {
        f0 = f1 = f;
    }
    if (vg == v) {
        uint32_t c = g & 1;
        g0 = LO(m, ng) ^ c;
        g1 = HI(m, ng) ^ c;
    } else {
        g0 = g1 = g;
    }
    if (vs->mask[v]) {
        uint32_t r0 = ae_rec(m, f0, g0, vs, sid);
        if (r0 == 0)
            r = 0;
        else
            r = or_rec(m, r0, ae_rec(m, f1, g1, vs, sid));
    } else {
        uint32_t r0 = ae_rec(m, f0, g0, vs, sid);
        uint32_t r1 = ae_rec(m, f1, g1, vs, sid);
        r = r0 != r1 ? mk(m, v, r0, r1) : r0;
    }
    cput(m, &m->cae, f, g, sid, r);
    return r;
}

uint32_t bdd_exists(bdd_mgr *m, uint32_t f, int32_t vs) {
    GUARD(m, BDD_ERR);
    return ex_rec(m, f, &m->vs[vs], (uint32_t)vs);
}

uint32_t bdd_and_exists(bdd_mgr *m, uint32_t f, uint32_t g, int32_t vs) {
    GUARD(m, BDD_ERR);
    return ae_rec(m, f, g, &m->vs[vs], (uint32_t)vs);
}

/* -- substitution ----------------------------------------------------------------------- */

typedef struct {
    int32_t maxv;
    const int8_t *val;   /* restrict: -1 free, else the value */
    const uint32_t *fn;  /* compose: BDD_ERR = identity; rename: the target level */
} subst_t;

static uint32_t restrict_rec(bdd_mgr *m, uint32_t f, const subst_t *s) {
    if (f <= 1) return f;
    uint32_t n = f >> 1;
    uint32_t v = VAR(m, n);
    if ((int32_t)v > s->maxv) return f;
    uint32_t r;
    if (!map_get(&m->memo, n, &r)) {
        int8_t b = s->val[v];
        if (b < 0) {
            uint32_t r0 = restrict_rec(m, LO(m, n), s);
            uint32_t r1 = restrict_rec(m, HI(m, n), s);
            r = r0 != r1 ? mk(m, v, r0, r1) : r0;
        } else {
            r = restrict_rec(m, b ? HI(m, n) : LO(m, n), s);
        }
        map_put(m, &m->memo, n, r);
    }
    return r ^ (f & 1);
}

static uint32_t restrict_entry(bdd_mgr *m, uint32_t f, const uint32_t *levels, const uint8_t *vals, size_t n) {
    int8_t *val = tmp_alloc(m, 0, (size_t)m->nvars + 1);
    memset(val, -1, (size_t)m->nvars + 1);
    subst_t s = {-1, val, NULL};
    for (size_t i = 0; i < n; i++) {
        if ((int32_t)levels[i] > s.maxv) s.maxv = (int32_t)levels[i];
        if (levels[i] < m->nvars) val[levels[i]] = vals[i] ? 1 : 0;
    }
    map_init(m, &m->memo, 1024);
    uint32_t r = restrict_rec(m, f, &s);
    cleanup(m);
    return r;
}

uint32_t bdd_restrict(bdd_mgr *m, uint32_t f, const uint32_t *levels, const uint8_t *vals,
                      size_t n) {
    if (n == 0) return f;
    GUARD(m, BDD_ERR);
    return restrict_entry(m, f, levels, vals, n);
}

static uint32_t simplify_rec(bdd_mgr *m, uint32_t f, uint32_t c) {
    if (c == 0 || f <= 1) return f;
    if (f == c) return 0;
    if ((f ^ c) == 1) return 1;
    uint64_t key = ((uint64_t)f << 32) | c;
    uint32_t r;
    if (map_get(&m->memo, key, &r)) return r;
    uint32_t nf = f >> 1, nc = c >> 1;
    uint32_t vf = VAR(m, nf), vc = VAR(m, nc);
    uint32_t k = c & 1;
    uint32_t c0 = LO(m, nc) ^ k, c1 = HI(m, nc) ^ k;
    if (vc < vf) {
        r = simplify_rec(m, f, or_rec(m, c0, c1));
    } else {
        k = f & 1;
        uint32_t f0 = LO(m, nf) ^ k, f1 = HI(m, nf) ^ k;
        if (vc > vf) c0 = c1 = c;
        if (c0 == 1) {
            r = simplify_rec(m, f1, c1);
        } else if (c1 == 1) {
            r = simplify_rec(m, f0, c0);
        } else {
            uint32_t r0 = simplify_rec(m, f0, c0);
            uint32_t r1 = simplify_rec(m, f1, c1);
            r = r0 != r1 ? mk(m, vf, r0, r1) : r0;
        }
    }
    map_put(m, &m->memo, key, r);
    return r;
}

uint32_t bdd_simplify(bdd_mgr *m, uint32_t f, uint32_t care) {
    GUARD(m, BDD_ERR);
    map_init(m, &m->memo, 1024);
    uint32_t r = simplify_rec(m, f, care);
    cleanup(m);
    return r;
}

static uint32_t compose_rec(bdd_mgr *m, uint32_t f, const subst_t *s) {
    if (f <= 1) return f;
    uint32_t n = f >> 1;
    uint32_t v = VAR(m, n);
    if ((int32_t)v > s->maxv) return f;
    uint32_t r;
    if (!map_get(&m->memo, n, &r)) {
        uint32_t r0 = compose_rec(m, LO(m, n), s);
        uint32_t r1 = compose_rec(m, HI(m, n), s);
        uint32_t g = s->fn[v];
        if (g == BDD_ERR) g = mk(m, v, 1, 0);
        r = ite_rec(m, g, r1, r0);
        map_put(m, &m->memo, n, r);
    }
    return r ^ (f & 1);
}

static uint32_t compose_entry(bdd_mgr *m, uint32_t f, const uint32_t *levels, const uint32_t *fns, size_t n) {
    uint32_t *fn = tmp_alloc(m, 0, ((size_t)m->nvars + 1) * sizeof(uint32_t));
    for (uint32_t i = 0; i <= m->nvars; i++) fn[i] = BDD_ERR;
    subst_t s = {-1, NULL, fn};
    for (size_t i = 0; i < n; i++) {
        if ((int32_t)levels[i] > s.maxv) s.maxv = (int32_t)levels[i];
        if (levels[i] < m->nvars) fn[levels[i]] = fns[i];
    }
    map_init(m, &m->memo, 1024);
    uint32_t r = compose_rec(m, f, &s);
    cleanup(m);
    return r;
}

uint32_t bdd_compose(bdd_mgr *m, uint32_t f, const uint32_t *levels, const uint32_t *fns,
                     size_t n) {
    if (n == 0) return f;
    GUARD(m, BDD_ERR);
    return compose_entry(m, f, levels, fns, n);
}

static uint32_t rename_rec(bdd_mgr *m, uint32_t f, const subst_t *s) {
    if (f <= 1) return f;
    uint32_t n = f >> 1;
    uint32_t v = VAR(m, n);
    if ((int32_t)v > s->maxv) return f;
    uint32_t r;
    if (!map_get(&m->memo, n, &r)) {
        uint32_t r0 = rename_rec(m, LO(m, n), s);
        uint32_t r1 = rename_rec(m, HI(m, n), s);
        uint32_t w = s->fn[v];
        if (w < VAR(m, r0 >> 1) && w < VAR(m, r1 >> 1))
            r = r0 != r1 ? mk(m, w, r0, r1) : r0;
        else
            r = ite_rec(m, mk(m, w, 1, 0), r1, r0);
        map_put(m, &m->memo, n, r);
    }
    return r ^ (f & 1);
}

static uint32_t rename_entry(bdd_mgr *m, uint32_t f, const uint32_t *from, const uint32_t *to, size_t n) {
    uint32_t *fn = tmp_alloc(m, 0, ((size_t)m->nvars + 1) * sizeof(uint32_t));
    for (uint32_t i = 0; i <= m->nvars; i++) fn[i] = i;
    subst_t s = {-1, NULL, fn};
    for (size_t i = 0; i < n; i++) {
        if ((int32_t)from[i] > s.maxv) s.maxv = (int32_t)from[i];
        if (from[i] < m->nvars) fn[from[i]] = to[i];
    }
    map_init(m, &m->memo, 1024);
    uint32_t r = rename_rec(m, f, &s);
    cleanup(m);
    return r;
}

uint32_t bdd_rename(bdd_mgr *m, uint32_t f, const uint32_t *from, const uint32_t *to, size_t n) {
    if (n == 0) return f;
    GUARD(m, BDD_ERR);
    return rename_entry(m, f, from, to, n);
}

typedef struct {
    bdd_mgr *src, *dst;
    const uint32_t *map;
    size_t nmap;
} xfer_t;

static uint32_t transfer_rec(const xfer_t *x, uint32_t f) {
    if (f <= 1) return f;
    bdd_mgr *src = x->src;
    uint32_t n = f >> 1;
    uint32_t r;
    if (!map_get(&src->memo, n, &r)) {
        uint32_t r0 = transfer_rec(x, LO(src, n));
        uint32_t r1 = transfer_rec(x, HI(src, n));
        uint32_t v = VAR(src, n);
        uint32_t w = x->map ? (v < x->nmap ? x->map[v] : BDD_ERR) : v;
        if (w == BDD_ERR || w >= x->dst->nvars) {
            src->err_level = v;
            x->dst->err_level = w;
            longjmp(*src->jbp, 2);
        }
        r = ite_rec(x->dst, mk(x->dst, w, 1, 0), r1, r0);
        map_put(src, &src->memo, n, r);
    }
    return r ^ (f & 1);
}

uint32_t bdd_transfer(bdd_mgr *src, bdd_mgr *dst, uint32_t f, const uint32_t *map,
                      size_t nmap) {
    jmp_buf jb;
    switch (setjmp(jb)) {
    case 0:
        break;
    case 2:
        cleanup(src);
        cleanup(dst);
        return BDD_MISSING;
    default:
        cleanup(src);
        cleanup(dst);
        return BDD_ERR;
    }
    src->jbp = &jb;
    dst->jbp = &jb;
    map_init(src, &src->memo, 1024);
    xfer_t x = {src, dst, map, nmap};
    uint32_t r = transfer_rec(&x, f);
    cleanup(src);
    return r;
}

/* -- queries ---------------------------------------------------------------------------- */

int bdd_evaluate(const bdd_mgr *m, uint32_t f, const uint8_t *bits, size_t n) {
    uint32_t c = f & 1;
    uint32_t node = f >> 1;
    while (node) {
        uint32_t v = VAR(m, node);
        if (v >= n) return -1;
        uint32_t e = bits[v] ? HI(m, node) : LO(m, node);
        c ^= e & 1;
        node = e >> 1;
    }
    return c == 0;
}

int64_t bdd_pick_one(const bdd_mgr *m, uint32_t f, uint32_t *levels, uint8_t *bits,
                     size_t cap) {
    if (f == 1) return -1;
    size_t k = 0;
    while (f > 1) {
        uint32_t n = f >> 1, c = f & 1;
        uint32_t f0 = LO(m, n) ^ c;
        if (k >= cap) return -2;
        levels[k] = VAR(m, n);
        if (f0 != 1) {
            bits[k++] = 0;
            f = f0;
        } else {
            bits[k++] = 1;
            f = HI(m, n) ^ c;
        }
    }
    return (int64_t)k;
}

/* Depth-first marking from roots, recording each visited node in m->vis; the marks are
 * removed by unmark(). Returns the number of nodes visited, or -1 (no marks left) when
 * memory runs out. */
static int push(uint32_t **buf, size_t *cap, size_t k, uint32_t x) {
    if (k >= *cap) {
        size_t nc = *cap ? 2 * *cap : 4096;
        uint32_t *b = realloc(*buf, nc * sizeof(uint32_t));
        if (!b) return 0;
        *buf = b;
        *cap = nc;
    }
    (*buf)[k] = x;
    return 1;
}

static void unmark(bdd_mgr *m, size_t k) {
    for (size_t i = 0; i < k; i++) VAR(m, m->vis[i]) &= VMASK;
}

static int64_t collect(bdd_mgr *m, const uint32_t *roots, size_t n) {
    size_t sp = 0, k = 0;
    for (size_t i = 0; i < n; i++)
        if (!push(&m->stk, &m->stk_cap, sp++, roots[i] >> 1)) goto oom;
    while (sp) {
        uint32_t x = m->stk[--sp];
        if (VAR(m, x) & MARK) continue;
        if (!push(&m->vis, &m->vis_cap, k, x)) goto oom;
        VAR(m, x) |= MARK;
        k++;
        if (x) {
            if (!push(&m->stk, &m->stk_cap, sp++, LO(m, x) >> 1)) goto oom;
            if (!push(&m->stk, &m->stk_cap, sp++, HI(m, x) >> 1)) goto oom;
        }
    }
    return (int64_t)k;
oom:
    unmark(m, k);
    return -1;
}

int64_t bdd_node_count(bdd_mgr *m, const uint32_t *roots, size_t n) {
    int64_t k = collect(m, roots, n);
    if (k > 0) unmark(m, (size_t)k);
    return k;
}

int64_t bdd_support(bdd_mgr *m, const uint32_t *roots, size_t n, uint8_t *out, size_t cap) {
    int64_t k = collect(m, roots, n);
    if (k < 0) return k;
    int64_t found = 0;
    for (int64_t i = 0; i < k; i++) {
        uint32_t x = m->vis[i];
        if (!x) continue;
        uint32_t v = VAR(m, x) & VMASK;
        if (v < cap && !out[v]) {
            out[v] = 1;
            found++;
        }
    }
    unmark(m, (size_t)k);
    return found;
}

int64_t bdd_dump(bdd_mgr *m, const uint32_t *roots, size_t n, uint32_t *nodes, uint32_t *vars,
                 uint32_t *los, uint32_t *his, size_t cap) {
    int64_t k = collect(m, roots, n);
    if (k < 0) return k;
    unmark(m, (size_t)k);
    if ((size_t)k > cap) return -2;
    for (int64_t i = 0; i < k; i++) {
        uint32_t x = m->vis[i];
        nodes[i] = x;
        vars[i] = VAR(m, x);
        los[i] = LO(m, x);
        his[i] = HI(m, x);
    }
    return k;
}

/* count: fixed-width little-endian numbers of W limbs, all below 2^total. */
typedef struct {
    bdd_mgr *m;
    const int32_t *pos;
    size_t npos;
    uint32_t total;
    size_t w;
    uint32_t *pool; /* m->tmp[0] */
    size_t used, cap;
    uint32_t *t; /* scratch */
} count_t;

static uint32_t count_pos(count_t *ct, uint32_t n) {
    if (n == 0) return ct->total;
    uint32_t v = VAR(ct->m, n);
    if (v >= ct->npos || ct->pos[v] < 0) {
        ct->m->err_level = v;
        longjmp(*ct->m->jbp, 3);
    }
    return (uint32_t)ct->pos[v];
}

static void big_shl(uint32_t *x, size_t w, uint32_t k) {
    size_t limbs = k / 32;
    uint32_t bits = k % 32;
    if (limbs) {
        for (size_t i = w; i-- > 0;) x[i] = i >= limbs ? x[i - limbs] : 0;
    }
    if (bits) {
        for (size_t i = w; i-- > 0;) {
            uint32_t lo = i ? x[i - 1] >> (32 - bits) : 0;
            x[i] = (x[i] << bits) | lo;
        }
    }
}

/* out = (complemented ? 2^(total - q) - c : c) << (q - p) */
static void count_edge(count_t *ct, uint32_t *out, const uint32_t *c, uint32_t comp, uint32_t q,
                       uint32_t p) {
    size_t w = ct->w;
    if (comp) {
        memset(out, 0, w * sizeof(uint32_t));
        uint32_t k = ct->total - q;
        out[k / 32] = 1u << (k % 32);
        uint64_t borrow = 0;
        for (size_t i = 0; i < w; i++) {
            uint64_t d = (uint64_t)out[i] - c[i] - borrow;
            out[i] = (uint32_t)d;
            borrow = (d >> 63) & 1;
        }
    } else {
        memcpy(out, c, w * sizeof(uint32_t));
    }
    big_shl(out, w, q - p);
}

static size_t count_rec(count_t *ct, uint32_t n) {
    uint32_t slot;
    if (map_get(&ct->m->memo, (uint64_t)n + 1, &slot)) return slot;
    bdd_mgr *m = ct->m;
    uint32_t p = count_pos(ct, n);
    uint32_t lo = LO(m, n), hi = HI(m, n);
    size_t s0 = count_rec(ct, lo >> 1);
    size_t s1 = count_rec(ct, hi >> 1);
    uint32_t q0 = count_pos(ct, lo >> 1), q1 = count_pos(ct, hi >> 1);
    if (ct->used + ct->w > ct->cap) {
        size_t nc = 2 * ct->cap;
        ct->pool = tmp_alloc(m, 0, nc * sizeof(uint32_t));
        ct->cap = nc;
    }
    size_t s = ct->used;
    ct->used += ct->w;
    uint32_t *out = ct->pool + s;
    count_edge(ct, out, ct->pool + s0, lo & 1, q0, p + 1);
    count_edge(ct, ct->t, ct->pool + s1, hi & 1, q1, p + 1);
    uint64_t carry = 0;
    for (size_t i = 0; i < ct->w; i++) {
        uint64_t sum = (uint64_t)out[i] + ct->t[i] + carry;
        out[i] = (uint32_t)sum;
        carry = sum >> 32;
    }
    map_put(m, &m->memo, (uint64_t)n + 1, (uint32_t)s);
    return s;
}

int bdd_count(bdd_mgr *m, uint32_t f, const int32_t *pos, size_t npos, uint32_t total,
              uint32_t *out, size_t limbs) {
    jmp_buf jb;
    switch (setjmp(jb)) {
    case 0:
        break;
    case 3:
        cleanup(m);
        return 1;
    default:
        cleanup(m);
        return -1;
    }
    m->jbp = &jb;
    count_t ct = {m, pos, npos, total, total / 32 + 1, NULL, 0, 0, NULL};
    if (limbs < ct.w) return -2;
    ct.cap = 1024 * ct.w;
    ct.pool = tmp_alloc(m, 0, ct.cap * sizeof(uint32_t));
    ct.t = tmp_alloc(m, 1, ct.w * sizeof(uint32_t));
    map_init(m, &m->memo, 1024);
    /* the constant node: one assignment of the (empty) remaining levels */
    memset(ct.pool, 0, ct.w * sizeof(uint32_t));
    ct.pool[0] = 1;
    ct.used = ct.w;
    map_put(m, &m->memo, 1, 0);
    uint32_t n = f >> 1;
    size_t s = count_rec(&ct, n);
    uint32_t q = count_pos(&ct, n);
    memset(out, 0, limbs * sizeof(uint32_t));
    count_edge(&ct, out, ct.pool + s, f & 1, q, 0);
    cleanup(m);
    return 0;
}

/* -- garbage collection ----------------------------------------------------------------- */

static inline int alive(const bdd_mgr *m, uint32_t e) {
    uint32_t n = e >> 1;
    return n == 0 || (VAR(m, n) & MARK);
}

/* Drop, in place, the entries that mention a reclaimed node. edges says which of b and c
 * are edges (bit 0: b, bit 1: c); a and r always are. */
static void sweep_cache(const bdd_mgr *m, cache *c, int edges) {
    size_t slots = (c->bmask + 1) * WAYS;
    for (size_t i = 0; i < slots; i++) {
        cent *e = &c->e[i];
        if (!e->a) continue;
        if (!alive(m, e->a) || !alive(m, e->r) || ((edges & 1) && !alive(m, e->b)) ||
            ((edges & 2) && !alive(m, e->c))) {
            e->a = e->b = e->c = e->r = 0;
            c->count--;
        }
    }
}

int64_t bdd_gc(bdd_mgr *m, const uint32_t *roots, size_t n) {
    /* mark (node 0 is the constant and always kept) */
    size_t sp = 0;
    for (size_t i = 0; i < n; i++) {
        if (!push(&m->stk, &m->stk_cap, sp++, roots[i] >> 1)) goto oom;
    }
    while (sp) {
        uint32_t x = m->stk[--sp];
        if (x == 0 || (VAR(m, x) & MARK)) continue;
        VAR(m, x) |= MARK;
        if (!push(&m->stk, &m->stk_cap, sp++, LO(m, x) >> 1)) goto oom;
        if (!push(&m->stk, &m->stk_cap, sp++, HI(m, x) >> 1)) goto oom;
    }
    /* computed tables keep the entries whose nodes all survive */
    sweep_cache(m, &m->cand, 1);
    sweep_cache(m, &m->cxor, 1);
    sweep_cache(m, &m->cex, 0);
    sweep_cache(m, &m->cite, 3);
    sweep_cache(m, &m->cae, 1);
    /* sweep the nodes and rebuild the unique table */
    memset(m->utab, 0, (m->umask + 1) * sizeof(uent));
    m->ucount = 0;
    int64_t freed = 0;
    for (uint32_t i = m->used; i-- > 1;) {
        uint32_t v = VAR(m, i);
        if (v & MARK) {
            v &= VMASK;
            VAR(m, i) = v;
            unique_insert(m->utab, m->umask, unique_hash(v, LO(m, i), HI(m, i)), i);
            m->ucount++;
        } else if (v != BDD_TERMVAR) {
            VAR(m, i) = BDD_TERMVAR;
            HI(m, i) = 0;
            LO(m, i) = m->free_head;
            m->free_head = i;
            m->nfree++;
            freed++;
        }
    }
    m->gc_runs++;
    if (m->stk_cap > (1u << 20)) { /* do not keep a large stack between collections */
        free(m->stk);
        m->stk = NULL;
        m->stk_cap = 0;
    }
    return freed;
oom:
    for (uint32_t i = 1; i < m->used; i++) VAR(m, i) &= VMASK;
    return -1;
}

void bdd_stats(const bdd_mgr *m, uint64_t *out) {
    size_t cache_bytes = (m->cand.bmask + m->cxor.bmask + m->cex.bmask + m->cite.bmask +
                          m->cae.bmask + 5) * WAYS * sizeof(cent);
    out[0] = m->used - m->nfree;
    out[1] = m->used;
    out[2] = m->ucount;
    out[3] = m->cand.count;
    out[4] = m->cxor.count;
    out[5] = m->cite.count;
    out[6] = m->cex.count;
    out[7] = m->cae.count;
    out[8] = m->gc_runs;
    out[9] = m->nvars;
    out[10] = (uint64_t)m->cap * 3 * sizeof(uint32_t) + (m->umask + 1) * sizeof(uent);
    out[11] = cache_bytes;
}
