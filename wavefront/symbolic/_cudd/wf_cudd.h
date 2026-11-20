/* A thin shim over CUDD for wavefront.symbolic.bdd_cudd.
 *
 * An edge is CUDD's own DdNode pointer (complement in the low bit) carried as uintptr_t, so
 * that the Python side handles plain integers. Every function that returns an edge returns
 * it referenced (Cudd_Ref), or 0 when CUDD failed (out of memory); the caller owns that
 * reference and gives it back with wf_deref.
 */
#ifndef WF_CUDD_H
#define WF_CUDD_H

#include <stddef.h>
#include <stdint.h>

typedef struct DdManager DdManager;

/* cffi-begin */
DdManager *wf_new(size_t max_memory, unsigned int cache_slots);
void wf_delete(DdManager *dd);
int wf_add_var(DdManager *dd);
uintptr_t wf_one(DdManager *dd);
uintptr_t wf_var(DdManager *dd, int index);
void wf_ref(uintptr_t f);
void wf_deref(DdManager *dd, uintptr_t f);
void wf_deref_many(DdManager *dd, const uintptr_t *fs, int n);

uintptr_t wf_and(DdManager *dd, uintptr_t f, uintptr_t g);
uintptr_t wf_xor(DdManager *dd, uintptr_t f, uintptr_t g);
uintptr_t wf_ite(DdManager *dd, uintptr_t f, uintptr_t g, uintptr_t h);
uintptr_t wf_and_all(DdManager *dd, const uintptr_t *fs, int n);
uintptr_t wf_cube(DdManager *dd, const int *indices, const uint8_t *values, int n);
uintptr_t wf_exists(DdManager *dd, uintptr_t f, uintptr_t cube);
uintptr_t wf_and_exists(DdManager *dd, uintptr_t f, uintptr_t g, uintptr_t cube);
uintptr_t wf_cofactor(DdManager *dd, uintptr_t f, uintptr_t cube);
uintptr_t wf_simplify(DdManager *dd, uintptr_t f, uintptr_t care);
uintptr_t wf_compose(DdManager *dd, uintptr_t f, const int *indices, const uintptr_t *fns, int n);

int wf_is_const(uintptr_t f);
int wf_top(uintptr_t f);
uintptr_t wf_then(uintptr_t f);
uintptr_t wf_else(uintptr_t f);
int wf_evaluate(DdManager *dd, uintptr_t f, const uint8_t *bits, int n);
int wf_support(DdManager *dd, const uintptr_t *roots, int n, uint8_t *out, int nvars);
int wf_node_count(const uintptr_t *roots, int n);
int wf_pick_one(DdManager *dd, uintptr_t f, int *indices, uint8_t *bits, int cap);
int wf_count(DdManager *dd, uintptr_t f, int nvars, uint32_t *out, int limbs);

int wf_group(DdManager *dd, int low_index, int size);
int wf_reorder(DdManager *dd, int method, int minsize);
int wf_shuffle(DdManager *dd, const int *permutation);
void wf_autodyn(DdManager *dd, int on, int method);
int wf_position(DdManager *dd, int index);
void wf_set_max_growth(DdManager *dd, double g);
void wf_set_next_reordering(DdManager *dd, unsigned int next);
void wf_set_sift_limits(DdManager *dd, int max_var, int max_swap);
void wf_set_max_cache(DdManager *dd, unsigned int slots);
int wf_check(DdManager *dd);
int wf_check_zero_ref(DdManager *dd);
void wf_stats(DdManager *dd, uint64_t *out);
const char *wf_source_hash(void);

#define WF_NSTATS 12
#define WF_SIFT 0
#define WF_SIFT_CONVERGE 1
#define WF_GROUP_SIFT 2
#define WF_GROUP_SIFT_CONVERGE 3
/* cffi-end */

#endif
