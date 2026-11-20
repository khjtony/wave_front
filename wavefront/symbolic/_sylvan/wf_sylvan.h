/* The Sylvan core behind wavefront/symbolic/bdd_sylvan.py: a thin layer over Sylvan
 * (https://github.com/trolando/sylvan), a multi-core BDD package on the Lace work-stealing
 * scheduler. See docs/engine_multicore_spike.md.
 *
 * Edges are those of the other cores: a uint64_t (node << 1) | complement with TRUE 0 and
 * FALSE 1. Sylvan's own edge is the node index with the complement in bit 63 and FALSE 0, so
 * the translation flips the complement bit. Sylvan has one node table per process: every
 * function here works on that table, and wfs_init must have returned before any other call.
 * Automatic garbage collection is off; nodes are reclaimed by wfs_gc only. When the node
 * table is full Sylvan ends the process. */
#ifndef WAVEFRONT_WF_SYLVAN_H
#define WAVEFRONT_WF_SYLVAN_H

#include <stddef.h>
#include <stdint.h>

/* cffi-begin: build.py hands this region to cffi (each #define value becomes ...) */
#define WFS_NSTATS 6

const char *wfs_source_hash(void);
/* Start Lace with `workers` threads and allocate a node table of 2^nodes_log2 nodes and an
 * operation cache of 2^cache_log2 entries (24 and 36 bytes each). Returns the number of
 * workers; a second call changes nothing and returns the number running. */
unsigned wfs_init(unsigned workers, unsigned nodes_log2, unsigned cache_log2);
unsigned wfs_workers(void);

uint64_t wfs_var(uint32_t level);
uint32_t wfs_top(uint64_t f); /* 0x40000000 for a constant */
uint64_t wfs_low(uint64_t f);
uint64_t wfs_high(uint64_t f);

uint64_t wfs_and(uint64_t f, uint64_t g);
uint64_t wfs_xor(uint64_t f, uint64_t g);
uint64_t wfs_ite(uint64_t f, uint64_t g, uint64_t h);
uint64_t wfs_and_all(const uint64_t *fs, size_t n);
/* levels strictly decreasing */
uint64_t wfs_cube(const uint32_t *levels, const uint8_t *vals, size_t n);

/* a varset is the positive cube of its levels (strictly increasing); a garbage-collection
 * root for as long as it is used */
uint64_t wfs_varset(const uint32_t *levels, size_t n);
uint64_t wfs_exists(uint64_t f, uint64_t vs);
uint64_t wfs_and_exists(uint64_t f, uint64_t g, uint64_t vs);

/* levels strictly decreasing */
uint64_t wfs_restrict(uint64_t f, const uint32_t *levels, const uint8_t *vals, size_t n);
uint64_t wfs_simplify(uint64_t f, uint64_t care);
uint64_t wfs_compose(uint64_t f, const uint32_t *levels, const uint64_t *fns, size_t n);

int wfs_evaluate(uint64_t f, const uint8_t *bits, size_t n);
int64_t wfs_pick_one(uint64_t f, uint32_t *levels, uint8_t *bits, size_t cap);
int64_t wfs_support(const uint64_t *roots, size_t n, uint8_t *out, size_t cap);
int64_t wfs_node_count(const uint64_t *roots, size_t n);
int64_t wfs_dump(const uint64_t *roots, size_t n, uint64_t *nodes, uint32_t *vars,
                 uint64_t *los, uint64_t *his, size_t cap);
/* 0, or 1 when f depends on a level without a position (wfs_error_level), or -1 */
int wfs_count(uint64_t f, const int32_t *pos, size_t npos, uint32_t total, uint32_t *out,
              size_t limbs);
uint32_t wfs_error_level(void);

int64_t wfs_gc(const uint64_t *roots, size_t n);
uint64_t wfs_live_nodes(void);
void wfs_stats(uint64_t *out);
/* cffi-end */

#endif
