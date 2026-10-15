/* A reduced ordered BDD manager in C11: the compiled core behind
 * wavefront/symbolic/bdd_c.py. Semantics are those of the reference manager
 * wavefront/symbolic/bdd.py (see docs/engine_scaling.md section 7).
 *
 * An edge is a uint32_t (node << 1) | complement; TRUE is 0 and FALSE is 1. Node 0 is
 * the constant one. Nodes are a struct of three uint32_t arrays (var, lo, hi); the hi edge
 * of a stored node is never complemented and lo != hi. Node indices are below 2^31 - 1, so
 * the largest edge is 2^32 - 3 and the two values above it are error codes.
 *
 * Every function taking a manager is not thread safe. Functions returning an edge return
 * BDD_ERR when memory (or the node limit) is exhausted; the manager stays consistent. */
#ifndef WAVEFRONT_BDD_CORE_H
#define WAVEFRONT_BDD_CORE_H

#include <stddef.h>
#include <stdint.h>

/* cffi-begin: build.py hands this region to cffi (each #define value becomes ...) */
#define BDD_ERR 0xFFFFFFFFu     /* out of memory or past the node limit */
#define BDD_MISSING 0xFFFFFFFEu /* transfer: a level without an image (bdd_error_level) */
#define BDD_TERMVAR 0x40000000u /* the level of the constant node */
#define BDD_MAX_VARS 32768u
#define BDD_MAX_NODES 0x7FFFFFFFu /* node indices 0 .. 2^31 - 2 */
#define BDD_NSTATS 12

typedef struct bdd_mgr bdd_mgr;

bdd_mgr *bdd_new(void);
void bdd_delete(bdd_mgr *m);
const char *bdd_core_source_hash(void);

/* variables and nodes */
int32_t bdd_add_var(bdd_mgr *m);
uint32_t bdd_num_vars(const bdd_mgr *m);
uint32_t bdd_mk(bdd_mgr *m, uint32_t level, uint32_t lo, uint32_t hi);
uint32_t bdd_top(const bdd_mgr *m, uint32_t f);
uint32_t bdd_low(const bdd_mgr *m, uint32_t f);
uint32_t bdd_high(const bdd_mgr *m, uint32_t f);
uint32_t bdd_live_nodes(const bdd_mgr *m);
uint32_t bdd_table_nodes(const bdd_mgr *m);
uint32_t bdd_error_level(const bdd_mgr *m);

/* boolean operations */
uint32_t bdd_and(bdd_mgr *m, uint32_t f, uint32_t g);
uint32_t bdd_xor(bdd_mgr *m, uint32_t f, uint32_t g);
uint32_t bdd_ite(bdd_mgr *m, uint32_t f, uint32_t g, uint32_t h);
uint32_t bdd_and_all(bdd_mgr *m, const uint32_t *fs, size_t n);
uint32_t bdd_cube(bdd_mgr *m, const uint32_t *levels, const uint8_t *vals, size_t n);

/* quantification; a varset is registered once and named by its id */
int32_t bdd_varset(bdd_mgr *m, const uint32_t *levels, size_t n);
uint32_t bdd_exists(bdd_mgr *m, uint32_t f, int32_t vs);
uint32_t bdd_and_exists(bdd_mgr *m, uint32_t f, uint32_t g, int32_t vs);

/* substitution */
uint32_t bdd_restrict(bdd_mgr *m, uint32_t f, const uint32_t *levels, const uint8_t *vals,
                      size_t n);
uint32_t bdd_simplify(bdd_mgr *m, uint32_t f, uint32_t care);
uint32_t bdd_compose(bdd_mgr *m, uint32_t f, const uint32_t *levels, const uint32_t *fns,
                     size_t n);
uint32_t bdd_rename(bdd_mgr *m, uint32_t f, const uint32_t *from, const uint32_t *to, size_t n);
uint32_t bdd_transfer(bdd_mgr *src, bdd_mgr *dst, uint32_t f, const uint32_t *map, size_t nmap);

/* queries */
int bdd_evaluate(const bdd_mgr *m, uint32_t f, const uint8_t *bits, size_t n);
int64_t bdd_pick_one(const bdd_mgr *m, uint32_t f, uint32_t *levels, uint8_t *bits, size_t cap);
int64_t bdd_support(bdd_mgr *m, const uint32_t *roots, size_t n, uint8_t *out, size_t cap);
int64_t bdd_node_count(bdd_mgr *m, const uint32_t *roots, size_t n);
int64_t bdd_dump(bdd_mgr *m, const uint32_t *roots, size_t n, uint32_t *nodes, uint32_t *vars,
                 uint32_t *los, uint32_t *his, size_t cap);
int bdd_count(bdd_mgr *m, uint32_t f, const int32_t *pos, size_t npos, uint32_t total,
              uint32_t *out, size_t limbs);

/* memory */
int64_t bdd_gc(bdd_mgr *m, const uint32_t *roots, size_t n);
void bdd_stats(const bdd_mgr *m, uint64_t *out);
/* cffi-end */

#endif
