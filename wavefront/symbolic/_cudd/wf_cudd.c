/* See wf_cudd.h. Only CUDD's public interface (cudd.h, mtr.h) is used. */
#define _GNU_SOURCE
#include "wf_cudd.h"

#include <execinfo.h>
#include <limits.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "mtr.h" /* before cudd.h, which declares the group functions only then */

#include "cudd.h"

#ifndef WF_SOURCE_HASH
#define WF_SOURCE_HASH "unknown"
#endif

#define N(e) ((DdNode *)(e))
#define E(n) ((uintptr_t)(n))

static uintptr_t ret(DdNode *r) {
    if (r != NULL) Cudd_Ref(r);
    return E(r);
}

const char *wf_source_hash(void) { return WF_SOURCE_HASH; }

/* On SIGSEGV, write the C stack to stderr (addresses for addr2line) and die as usual. */
static void on_segv(int sig) {
    void *frames[96];
    int n = backtrace(frames, 96);
    static const char msg[] = "wf_cudd: SIGSEGV, C stack:\n";
    if (write(2, msg, sizeof msg - 1) < 0) n = 0;
    backtrace_symbols_fd(frames, n, 2);
    signal(sig, SIG_DFL);
    raise(sig);
}

void wf_trace_crashes(void) { signal(SIGSEGV, on_segv); }

DdManager *wf_new(size_t max_memory, unsigned int cache_slots) {
    DdManager *dd = Cudd_Init(0, 0, CUDD_UNIQUE_SLOTS,
                              cache_slots ? cache_slots : CUDD_CACHE_SLOTS, max_memory);
    if (dd == NULL) return NULL;
    /* failures come back as NULL results; nothing is printed and the process goes on */
    Cudd_RegisterOutOfMemoryCallback(dd, Cudd_OutOfMemSilent);
    if (max_memory) Cudd_SetMaxMemory(dd, max_memory);
    Cudd_AutodynDisable(dd);
    return dd;
}

void wf_delete(DdManager *dd) { Cudd_Quit(dd); }

int wf_add_var(DdManager *dd) {
    DdNode *v = Cudd_bddNewVar(dd);
    return v == NULL ? -1 : (int)Cudd_NodeReadIndex(v);
}

uintptr_t wf_one(DdManager *dd) { return ret(Cudd_ReadOne(dd)); }
uintptr_t wf_var(DdManager *dd, int index) { return ret(Cudd_bddIthVar(dd, index)); }
void wf_ref(uintptr_t f) { Cudd_Ref(N(f)); }
void wf_deref(DdManager *dd, uintptr_t f) { Cudd_RecursiveDeref(dd, N(f)); }

void wf_deref_many(DdManager *dd, const uintptr_t *fs, int n) {
    for (int i = 0; i < n; i++) Cudd_RecursiveDeref(dd, N(fs[i]));
}

uintptr_t wf_and(DdManager *dd, uintptr_t f, uintptr_t g) {
    return ret(Cudd_bddAnd(dd, N(f), N(g)));
}

uintptr_t wf_xor(DdManager *dd, uintptr_t f, uintptr_t g) {
    return ret(Cudd_bddXor(dd, N(f), N(g)));
}

uintptr_t wf_ite(DdManager *dd, uintptr_t f, uintptr_t g, uintptr_t h) {
    return ret(Cudd_bddIte(dd, N(f), N(g), N(h)));
}

static DdNode *and_range(DdManager *dd, const uintptr_t *fs, int lo, int hi) {
    if (hi - lo == 1) {
        Cudd_Ref(N(fs[lo]));
        return N(fs[lo]);
    }
    int mid = lo + (hi - lo) / 2;
    DdNode *a = and_range(dd, fs, lo, mid);
    if (a == NULL) return NULL;
    DdNode *b = and_range(dd, fs, mid, hi);
    if (b == NULL) {
        Cudd_RecursiveDeref(dd, a);
        return NULL;
    }
    DdNode *r = Cudd_bddAnd(dd, a, b);
    if (r != NULL) Cudd_Ref(r);
    Cudd_RecursiveDeref(dd, a);
    Cudd_RecursiveDeref(dd, b);
    return r;
}

uintptr_t wf_and_all(DdManager *dd, const uintptr_t *fs, int n) {
    if (n <= 0) return wf_one(dd);
    return E(and_range(dd, fs, 0, n));
}

uintptr_t wf_cube(DdManager *dd, const int *indices, const uint8_t *values, int n) {
    DdNode *cube = Cudd_ReadOne(dd);
    Cudd_Ref(cube);
    for (int i = 0; i < n; i++) {
        DdNode *v = Cudd_bddIthVar(dd, indices[i]);
        if (v == NULL) {
            Cudd_RecursiveDeref(dd, cube);
            return 0;
        }
        DdNode *next = Cudd_bddAnd(dd, cube, values == NULL || values[i] ? v : Cudd_Not(v));
        if (next == NULL) {
            Cudd_RecursiveDeref(dd, cube);
            return 0;
        }
        Cudd_Ref(next);
        Cudd_RecursiveDeref(dd, cube);
        cube = next;
    }
    return E(cube);
}

uintptr_t wf_exists(DdManager *dd, uintptr_t f, uintptr_t cube) {
    return ret(Cudd_bddExistAbstract(dd, N(f), N(cube)));
}

uintptr_t wf_and_exists(DdManager *dd, uintptr_t f, uintptr_t g, uintptr_t cube) {
    return ret(Cudd_bddAndAbstract(dd, N(f), N(g), N(cube)));
}

uintptr_t wf_cofactor(DdManager *dd, uintptr_t f, uintptr_t cube) {
    return ret(Cudd_Cofactor(dd, N(f), N(cube)));
}

uintptr_t wf_simplify(DdManager *dd, uintptr_t f, uintptr_t care) {
    return ret(Cudd_bddRestrict(dd, N(f), N(care)));
}

uintptr_t wf_compose(DdManager *dd, uintptr_t f, const int *indices, const uintptr_t *fns, int n) {
    int size = Cudd_ReadSize(dd);
    DdNode **vector = malloc(sizeof(DdNode *) * (size_t)(size > 0 ? size : 1));
    if (vector == NULL) return 0;
    for (int i = 0; i < size; i++) vector[i] = Cudd_bddIthVar(dd, i);
    for (int i = 0; i < n; i++) vector[indices[i]] = N(fns[i]);
    DdNode *r = Cudd_bddVectorCompose(dd, N(f), vector);
    free(vector);
    return ret(r);
}

int wf_is_const(uintptr_t f) { return Cudd_IsConstant(N(f)); }

int wf_top(uintptr_t f) {
    return Cudd_IsConstant(N(f)) ? INT_MAX : (int)Cudd_NodeReadIndex(N(f));
}

/* The children of a node as stored (of the regular pointer), not referenced. */
uintptr_t wf_then(uintptr_t f) { return E(Cudd_T(N(f))); }
uintptr_t wf_else(uintptr_t f) { return E(Cudd_E(N(f))); }

/* 1 or 0; -1 when the walk needs an index at or past n */
int wf_evaluate(DdManager *dd, uintptr_t f, const uint8_t *bits, int n) {
    (void)dd;
    DdNode *p = N(f);
    int comp = 0;
    for (;;) {
        if (Cudd_IsComplement(p)) {
            comp ^= 1;
            p = Cudd_Regular(p);
        }
        if (Cudd_IsConstant(p)) return 1 ^ comp;
        int v = (int)Cudd_NodeReadIndex(p);
        if (v >= n) return -1;
        p = bits[v] ? Cudd_T(p) : Cudd_E(p);
    }
}

int wf_support(DdManager *dd, const uintptr_t *roots, int n, uint8_t *out, int nvars) {
    int *s = Cudd_VectorSupportIndex(dd, (DdNode **)roots, n);
    if (s == NULL) return -1;
    int size = Cudd_ReadSize(dd), k = 0;
    for (int i = 0; i < size && i < nvars; i++) {
        out[i] = s[i] ? 1 : 0;
        k += out[i];
    }
    free(s);
    return k;
}

int wf_node_count(const uintptr_t *roots, int n) {
    return Cudd_SharingSize((DdNode **)roots, n);
}

/* The assignment the reference manager picks: walk the variables of the support in index
 * order, taking 0 whenever the 0-cofactor is satisfiable. Independent of the current
 * order. Returns the number of (index, bit) pairs written, or -1 on failure. */
int wf_pick_one(DdManager *dd, uintptr_t f, int *indices, uint8_t *bits, int cap) {
    DdNode *zero = Cudd_ReadLogicZero(dd);
    DdNode *g = N(f);
    int k = 0, size = Cudd_ReadSize(dd);
    Cudd_Ref(g);
    while (!Cudd_IsConstant(g)) {
        int *s = Cudd_SupportIndex(dd, g);
        if (s == NULL) goto fail;
        int v = 0;
        while (v < size && !s[v]) v++;
        free(s);
        if (v >= size || k >= cap) goto fail;
        DdNode *x = Cudd_bddIthVar(dd, v);
        DdNode *next = Cudd_Cofactor(dd, g, Cudd_Not(x));
        if (next == NULL) goto fail;
        Cudd_Ref(next);
        int bit = 0;
        if (next == zero) {
            Cudd_RecursiveDeref(dd, next);
            next = Cudd_Cofactor(dd, g, x);
            if (next == NULL) goto fail;
            Cudd_Ref(next);
            bit = 1;
        }
        indices[k] = v;
        bits[k] = (uint8_t)bit;
        k++;
        Cudd_RecursiveDeref(dd, g);
        g = next;
    }
    Cudd_RecursiveDeref(dd, g);
    return k;
fail:
    Cudd_RecursiveDeref(dd, g);
    return -1;
}

/* The number of minterms of f over nvars variables, little-endian 32-bit limbs.
 * 0 on success, -1 on failure, -2 when out is too short. */
int wf_count(DdManager *dd, uintptr_t f, int nvars, uint32_t *out, int limbs) {
    int digits = 0;
    DdApaNumber num = Cudd_ApaCountMinterm(dd, N(f), nvars, &digits);
    if (num == NULL) return -1;
    for (int i = 0; i < limbs; i++) out[i] = 0;
    int rc = 0;
    for (int i = 0; i < digits; i++) {
        int limb = digits - 1 - i; /* the most significant digit comes first */
        if (limb < limbs)
            out[limb] = num[i];
        else if (num[i] != 0)
            rc = -2;
    }
    free(num);
    return rc;
}

int wf_group(DdManager *dd, int low_index, int size) {
    return Cudd_MakeTreeNode(dd, (unsigned int)low_index, (unsigned int)size, MTR_FIXED) != NULL;
}

static Cudd_ReorderingType method_of(int method) {
    switch (method) {
    case WF_SIFT: return CUDD_REORDER_SIFT;
    case WF_SIFT_CONVERGE: return CUDD_REORDER_SIFT_CONVERGE;
    case WF_GROUP_SIFT_CONVERGE: return CUDD_REORDER_GROUP_SIFT_CONV;
    default: return CUDD_REORDER_GROUP_SIFT;
    }
}

int wf_reorder(DdManager *dd, int method, int minsize) {
    return Cudd_ReduceHeap(dd, method_of(method), minsize);
}

int wf_shuffle(DdManager *dd, const int *permutation) {
    return Cudd_ShuffleHeap(dd, (int *)permutation);
}

void wf_autodyn(DdManager *dd, int on, int method) {
    if (on)
        Cudd_AutodynEnable(dd, method_of(method));
    else
        Cudd_AutodynDisable(dd);
}

int wf_position(DdManager *dd, int index) { return Cudd_ReadPerm(dd, index); }
void wf_set_max_growth(DdManager *dd, double g) { Cudd_SetMaxGrowth(dd, g); }
void wf_set_next_reordering(DdManager *dd, unsigned int next) { Cudd_SetNextReordering(dd, next); }

void wf_set_sift_limits(DdManager *dd, int max_var, int max_swap) {
    if (max_var > 0) Cudd_SetSiftMaxVar(dd, max_var);
    if (max_swap > 0) Cudd_SetSiftMaxSwap(dd, max_swap);
}

void wf_set_max_cache(DdManager *dd, unsigned int slots) { Cudd_SetMaxCacheHard(dd, slots); }

/* 0 when CUDD's own consistency checks pass */
int wf_check(DdManager *dd) {
    FILE *saved = Cudd_ReadStdout(dd);
    FILE *quiet = fopen("/dev/null", "w"); /* the checks print table statistics */
    if (quiet != NULL) Cudd_SetStdout(dd, quiet);
    int a = Cudd_DebugCheck(dd);
    int b = Cudd_CheckKeys(dd);
    if (quiet != NULL) {
        Cudd_SetStdout(dd, saved);
        fclose(quiet);
    }
    return a != 0 || b != 0;
}

int wf_check_zero_ref(DdManager *dd) { return Cudd_CheckZeroRef(dd); }

void wf_stats(DdManager *dd, uint64_t *out) {
    out[0] = (uint64_t)Cudd_ReadNodeCount(dd);
    out[1] = (uint64_t)Cudd_ReadPeakLiveNodeCount(dd);
    out[2] = (uint64_t)Cudd_ReadPeakNodeCount(dd);
    out[3] = (uint64_t)Cudd_ReadKeys(dd);
    out[4] = (uint64_t)Cudd_ReadDead(dd);
    out[5] = (uint64_t)Cudd_ReadMemoryInUse(dd);
    out[6] = (uint64_t)Cudd_ReadCacheSlots(dd);
    out[7] = (uint64_t)Cudd_ReadGarbageCollections(dd);
    out[8] = (uint64_t)Cudd_ReadReorderings(dd);
    out[9] = (uint64_t)Cudd_ReadReorderingTime(dd);
    out[10] = (uint64_t)Cudd_ReadSize(dd);
    out[11] = (uint64_t)Cudd_ReadGarbageCollectionTime(dd);
}
