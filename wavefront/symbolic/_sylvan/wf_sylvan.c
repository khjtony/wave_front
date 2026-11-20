/* See wf_sylvan.h. */
#include "wf_sylvan.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <sylvan.h>

#ifndef WFS_SOURCE_HASH
#define WFS_SOURCE_HASH "unknown"
#endif

#define COMP UINT64_C(0x8000000000000000)
#define TERMVAR 0x40000000u

static inline MTBDD S(uint64_t e) { return (e >> 1) | ((e & 1) ? 0 : COMP); }
static inline uint64_t E(MTBDD s) { return ((s & ~COMP) << 1) | ((s >> 63) ^ 1); }

static int started;
static uint64_t gc_runs, table_nodes, cache_entries;
static uint32_t error_level;
static const uint64_t *gc_roots;
static size_t gc_nroots;

const char *wfs_source_hash(void) { return WFS_SOURCE_HASH; }

/* -- garbage collection: only on request, from the roots the caller names ---------------- */

VOID_TASK_2(wfs_mark_range, size_t, first, size_t, count) {
    if (count > 64) {
        SPAWN(wfs_mark_range, first, count / 2);
        CALL(wfs_mark_range, first + count / 2, count - count / 2);
        SYNC(wfs_mark_range);
        return;
    }
    for (size_t i = first; i < first + count; i++) CALL(mtbdd_gc_mark_rec, S(gc_roots[i]));
}

VOID_TASK_0(wfs_mark) {
    if (gc_nroots) CALL(wfs_mark_range, 0, gc_nroots);
}

/* the tables keep the size they were given */
VOID_TASK_0(wfs_no_resize) {}

unsigned wfs_init(unsigned workers, unsigned nodes_log2, unsigned cache_log2) {
    if (started) return lace_workers();
    if (workers < 1) workers = 1;
    lace_set_pinning(LACE_PIN_OFF);
    lace_set_stacksize((size_t)64 << 20);
    lace_set_scratch_size((size_t)16 << 20);
    lace_start(workers, 1 << 17);
    table_nodes = UINT64_C(1) << nodes_log2;
    cache_entries = UINT64_C(1) << cache_log2;
    sylvan_set_sizes(table_nodes, table_nodes, cache_entries, cache_entries);
    sylvan_init_package();
    sylvan_init_mtbdd();
    sylvan_gc_hook_main(wfs_no_resize_CALL);
    sylvan_gc_add_mark(wfs_mark_CALL);
    sylvan_gc_disable();
    started = 1;
    return lace_workers();
}

unsigned wfs_workers(void) { return started ? lace_workers() : 0; }

uint64_t wfs_live_nodes(void) {
    size_t filled = 0;
    sylvan_table_usage(&filled, NULL);
    return filled;
}

int64_t wfs_gc(const uint64_t *roots, size_t n) {
    uint64_t before = wfs_live_nodes();
    gc_roots = roots;
    gc_nroots = n;
    sylvan_gc_enable();
    sylvan_gc_collect();
    sylvan_gc_disable();
    gc_roots = NULL;
    gc_nroots = 0;
    gc_runs++;
    return (int64_t)(before - wfs_live_nodes());
}

void wfs_stats(uint64_t *out) {
    out[0] = wfs_live_nodes();
    out[1] = table_nodes;
    out[2] = cache_entries;
    out[3] = gc_runs;
    out[4] = table_nodes * 24;
    out[5] = cache_entries * 36;
}

/* -- nodes ------------------------------------------------------------------------------ */

/* Nodes are made on a Lace worker: the node table allocates from per-worker regions. */
TASK_1(MTBDD, wfs_var_task, uint32_t, level) { return mtbdd_ithvar(level); }

uint64_t wfs_var(uint32_t level) { return E(RUN(wfs_var_task, level)); }

uint32_t wfs_top(uint64_t f) {
    MTBDD s = S(f);
    return mtbdd_isleaf(s) ? TERMVAR : mtbdd_getvar(s);
}

uint64_t wfs_low(uint64_t f) { return E(mtbdd_getlow(S(f))); }
uint64_t wfs_high(uint64_t f) { return E(mtbdd_gethigh(S(f))); }

/* -- operations ------------------------------------------------------------------------- */

uint64_t wfs_and(uint64_t f, uint64_t g) { return E(sylvan_and(S(f), S(g))); }
uint64_t wfs_xor(uint64_t f, uint64_t g) { return E(sylvan_xor(S(f), S(g))); }
uint64_t wfs_ite(uint64_t f, uint64_t g, uint64_t h) { return E(sylvan_ite(S(f), S(g), S(h))); }

static MTBDD and_range(const uint64_t *fs, size_t n) {
    if (n == 1) return S(fs[0]);
    MTBDD a = and_range(fs, n / 2);
    if (a == sylvan_false) return a;
    MTBDD b = and_range(fs + n / 2, n - n / 2);
    return sylvan_and(a, b);
}

uint64_t wfs_and_all(const uint64_t *fs, size_t n) { return n ? E(and_range(fs, n)) : 0; }

static MTBDD cube(const uint32_t *levels, const uint8_t *vals, size_t n) {
    MTBDD r = sylvan_true;
    for (size_t i = 0; i < n; i++) {
        r = vals[i] ? mtbdd_makenode(levels[i], sylvan_false, r)
                    : mtbdd_makenode(levels[i], r, sylvan_false);
    }
    return r;
}

TASK_3(MTBDD, wfs_cube_task, const uint32_t *, levels, const uint8_t *, vals, size_t, n) {
    return cube(levels, vals, n);
}

uint64_t wfs_cube(const uint32_t *levels, const uint8_t *vals, size_t n) {
    return E(RUN(wfs_cube_task, levels, vals, n));
}

TASK_2(MTBDD, wfs_varset_task, const uint32_t *, levels, size_t, n) {
    MTBDD r = sylvan_true;
    for (size_t i = n; i-- > 0;) r = mtbdd_makenode(levels[i], sylvan_false, r);
    return r;
}

uint64_t wfs_varset(const uint32_t *levels, size_t n) {
    return E(RUN(wfs_varset_task, levels, n));
}

uint64_t wfs_exists(uint64_t f, uint64_t vs) { return E(sylvan_exists(S(f), S(vs))); }

uint64_t wfs_and_exists(uint64_t f, uint64_t g, uint64_t vs) {
    return E(sylvan_and_exists(S(f), S(g), S(vs)));
}

TASK_4(MTBDD, wfs_restrict_task, MTBDD, f, const uint32_t *, levels, const uint8_t *, vals,
       size_t, n) {
    return CALL(sylvan_cofactor, f, cube(levels, vals, n));
}

uint64_t wfs_restrict(uint64_t f, const uint32_t *levels, const uint8_t *vals, size_t n) {
    return E(RUN(wfs_restrict_task, S(f), levels, vals, n));
}

uint64_t wfs_simplify(uint64_t f, uint64_t care) { return E(sylvan_restrict(S(f), S(care))); }

TASK_4(MTBDD, wfs_compose_task, MTBDD, f, const uint32_t *, levels, const uint64_t *, fns,
       size_t, n) {
    MTBDDMAP map = mtbdd_map_empty();
    for (size_t i = 0; i < n; i++) map = mtbdd_map_add(map, levels[i], S(fns[i]));
    return CALL(sylvan_compose, f, map, 0);
}

uint64_t wfs_compose(uint64_t f, const uint32_t *levels, const uint64_t *fns, size_t n) {
    return E(RUN(wfs_compose_task, S(f), levels, fns, n));
}

/* -- queries ---------------------------------------------------------------------------- */

int wfs_evaluate(uint64_t f, const uint8_t *bits, size_t n) {
    MTBDD s = S(f);
    while (!mtbdd_isleaf(s)) {
        uint32_t v = mtbdd_getvar(s);
        if (v >= n) return -1;
        s = bits[v] ? mtbdd_gethigh(s) : mtbdd_getlow(s);
    }
    return s == sylvan_true;
}

int64_t wfs_pick_one(uint64_t f, uint32_t *levels, uint8_t *bits, size_t cap) {
    MTBDD s = S(f);
    size_t k = 0;
    if (s == sylvan_false) return -1;
    while (!mtbdd_isleaf(s)) {
        if (k >= cap) return -1;
        MTBDD lo = mtbdd_getlow(s);
        levels[k] = mtbdd_getvar(s);
        bits[k] = lo == sylvan_false;
        s = bits[k] ? mtbdd_gethigh(s) : lo;
        k++;
    }
    return (int64_t)k;
}

int64_t wfs_support(const uint64_t *roots, size_t n, uint8_t *out, size_t cap) {
    int64_t k = 0;
    MTBDD all = sylvan_true;
    for (size_t i = 0; i < n; i++) all = sylvan_and(all, mtbdd_support(S(roots[i])));
    for (; !mtbdd_isleaf(all); all = mtbdd_gethigh(all)) {
        uint32_t v = mtbdd_getvar(all);
        if (v >= cap) return -1;
        out[v] = 1;
        k++;
    }
    return k;
}

/* a map from node index to a 32-bit value (open addressing, linear probing) */
typedef struct {
    uint64_t *key; /* index + 1; 0 is an empty slot */
    uint32_t *val;
    size_t mask, n;
} imap;

static int imap_init(imap *m, size_t cap) {
    m->key = calloc(cap, sizeof(uint64_t));
    m->val = malloc(cap * sizeof(uint32_t));
    m->mask = cap - 1;
    m->n = 0;
    return m->key && m->val;
}

static void imap_free(imap *m) {
    free(m->key);
    free(m->val);
}

static inline size_t imap_slot(const imap *m, uint64_t k) {
    size_t i = (size_t)((k * UINT64_C(0x9E3779B97F4A7C15)) >> 20) & m->mask;
    while (m->key[i] && m->key[i] != k) i = (i + 1) & m->mask;
    return i;
}

static int imap_put(imap *m, uint64_t k, uint32_t v) {
    if ((m->n + 1) * 2 > m->mask + 1) {
        imap big;
        if (!imap_init(&big, (m->mask + 1) * 2)) {
            imap_free(&big);
            return 0;
        }
        for (size_t i = 0; i <= m->mask; i++) {
            if (m->key[i]) {
                size_t j = imap_slot(&big, m->key[i]);
                big.key[j] = m->key[i];
                big.val[j] = m->val[i];
            }
        }
        big.n = m->n;
        imap_free(m);
        *m = big;
    }
    size_t i = imap_slot(m, k);
    if (!m->key[i]) m->n++;
    m->key[i] = k;
    m->val[i] = v;
    return 1;
}

/* the nodes reachable from the roots, each node after its children (the constant first) */
typedef struct {
    imap seen;
    uint64_t *order;
    size_t n, cap;
    int oom;
} walk;

static void walk_rec(walk *w, MTBDD s) {
    uint64_t idx = s & ~COMP;
    if (w->oom || w->seen.key[imap_slot(&w->seen, idx + 1)]) return;
    if (!mtbdd_isleaf(s)) {
        walk_rec(w, mtbdd_getlow(s));
        walk_rec(w, mtbdd_gethigh(s));
        if (w->oom) return;
    }
    if (w->n == w->cap) {
        uint64_t *bigger = realloc(w->order, 2 * w->cap * sizeof(uint64_t));
        if (!bigger) {
            w->oom = 1;
            return;
        }
        w->order = bigger;
        w->cap *= 2;
    }
    if (w->n >= UINT32_MAX || !imap_put(&w->seen, idx + 1, (uint32_t)w->n)) {
        w->oom = 1;
        return;
    }
    w->order[w->n++] = idx;
}

static int walk_roots(walk *w, const uint64_t *roots, size_t n) {
    w->n = 0;
    w->cap = 1024;
    w->oom = 0;
    w->order = malloc(w->cap * sizeof(uint64_t));
    if (!imap_init(&w->seen, 4096) || !w->order) return 0;
    for (size_t i = 0; i < n; i++) walk_rec(w, S(roots[i]));
    return !w->oom;
}

static void walk_free(walk *w) {
    imap_free(&w->seen);
    free(w->order);
}

int64_t wfs_node_count(const uint64_t *roots, size_t n) {
    walk w;
    int64_t r = walk_roots(&w, roots, n) ? (int64_t)w.n : -1;
    walk_free(&w);
    return r;
}

int64_t wfs_dump(const uint64_t *roots, size_t n, uint64_t *nodes, uint32_t *vars,
                 uint64_t *los, uint64_t *his, size_t cap) {
    walk w;
    int64_t r = -1;
    if (walk_roots(&w, roots, n) && w.n <= cap) {
        for (size_t i = 0; i < w.n; i++) {
            MTBDD s = w.order[i] | COMP; /* the edge (node << 1) of the interface */
            nodes[i] = w.order[i];
            if (mtbdd_isleaf(s)) {
                vars[i] = TERMVAR;
                los[i] = his[i] = 0;
            } else {
                vars[i] = mtbdd_getvar(s);
                los[i] = E(mtbdd_getlow(s));
                his[i] = E(mtbdd_gethigh(s));
            }
        }
        r = (int64_t)w.n;
    }
    walk_free(&w);
    return r;
}

/* Exact counts: numbers of `w` 32-bit limbs, little-endian.
 * acc += (negate ? 2^width - x : x) << shift */
static void big_add_shifted(uint32_t *acc, const uint32_t *x, int negate, uint32_t width,
                            uint32_t shift, size_t w, uint32_t *tmp) {
    const uint32_t *v = x;
    if (negate) {
        uint64_t borrow = 0;
        for (size_t i = 0; i < w; i++) {
            uint64_t bit = (i == width / 32) ? (UINT64_C(1) << (width % 32)) : 0;
            uint64_t d = bit - x[i] - borrow;
            tmp[i] = (uint32_t)d;
            borrow = (d >> 32) & 1;
        }
        v = tmp;
    }
    size_t limb = shift / 32;
    uint32_t bits = shift % 32;
    uint64_t carry = 0;
    for (size_t i = limb; i < w; i++) {
        uint32_t part = v[i - limb] << bits;
        if (bits && i > limb) part |= v[i - limb - 1] >> (32 - bits);
        uint64_t sum = (uint64_t)acc[i] + part + carry;
        acc[i] = (uint32_t)sum;
        carry = sum >> 32;
    }
}

/* cnt[i] is the number of assignments of the levels at positions p[i] .. total - 1 that
 * satisfy Sylvan's uncomplemented edge to node i (p of the constant is total). */
int wfs_count(uint64_t f, const int32_t *pos, size_t npos, uint32_t total, uint32_t *out,
              size_t limbs) {
    size_t w = total / 32 + 1;
    if (limbs < w) return -1;
    walk wk;
    int rc = -1;
    uint32_t *cnt = NULL, *tmp = NULL, *p = NULL;
    uint64_t root = f;
    if (!walk_roots(&wk, &root, 1)) goto done;
    cnt = calloc(wk.n * w, sizeof(uint32_t));
    tmp = malloc(w * sizeof(uint32_t));
    p = malloc(wk.n * sizeof(uint32_t));
    if (!cnt || !tmp || !p) goto done;
    for (size_t i = 0; i < wk.n; i++) {
        MTBDD s = wk.order[i];
        if (mtbdd_isleaf(s)) {
            p[i] = total;
            continue;
        }
        uint32_t v = mtbdd_getvar(s);
        if (v >= npos || pos[v] < 0) {
            error_level = v;
            rc = 1;
            goto done;
        }
        p[i] = (uint32_t)pos[v];
        MTBDD kids[2] = {mtbdd_getlow(s), mtbdd_gethigh(s)};
        for (int k = 0; k < 2; k++) {
            uint32_t j = wk.seen.val[imap_slot(&wk.seen, (kids[k] & ~COMP) + 1)];
            big_add_shifted(cnt + i * w, cnt + j * w, (kids[k] & COMP) != 0, total - p[j],
                            p[j] - p[i] - 1, w, tmp);
        }
    }
    MTBDD s = S(f);
    uint32_t j = wk.seen.val[imap_slot(&wk.seen, (s & ~COMP) + 1)];
    memset(out, 0, limbs * sizeof(uint32_t));
    big_add_shifted(out, cnt + j * w, (s & COMP) != 0, total - p[j], p[j], w, tmp);
    rc = 0;
done:
    walk_free(&wk);
    free(cnt);
    free(tmp);
    free(p);
    return rc;
}

uint32_t wfs_error_level(void) { return error_level; }
