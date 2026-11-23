# Multi-core engine: design for combining it with the split step

Status: design, 23 November 2026. Nothing here is built. It follows the three engine
experiments of 20 to 22 November (docs/engine_multicore_spike.md,
docs/engine_reordering_spike.md, docs/engine_split_step.md) and the owner's instruction to
combine them.

## 1. What we know

| Experiment | Result on the registered AGI v0.3 build |
|---|---|
| Split step (own C core) | The same edge; a third to a fifth of the memory; no change in time. In production since 21 November. |
| Static order from sifting | 1.3 to 1.8 times faster where the order suits the question, slower where it does not. Optional. |
| Sylvan, 12 threads, present step | 1.5 times faster on one zone (57 against 86 minutes), 11 hours of processor time, 28.5 GB reserved. Identical readings. On AGI v0.1: 2.7 to 4.4 times. |

Time is now the constraint: with the split step the largest zones fit in 20 to 40 GB and take
one to two days on one core.

## 2. The problem with the obvious combination

`compose_by_levels` (wavefront/symbolic/substitute.py) is a Python loop that calls
`mgr.ITE` once per node of the layer. Sylvan parallelises *inside* one large operation. A
million small `ITE` calls issued one after another from Python give it nothing to parallelise,
and each call crosses the cffi boundary. Running the present split step on the Sylvan core
would therefore be slower than both parents.

The per-layer profile of the own core says where the time is: all of it in the substitution
(`compose`, or its split form) and in the six `and_exists` of a step. Both must run in
parallel for the wall time to fall.

## 3. Design

### 3.1 The split substitution moves into C, as one parallel Sylvan task

A new entry point in `wavefront/symbolic/_sylvan/wf_sylvan.c`:

    uint64_t wfs_compose_levels(uint64_t f, const uint32_t *levels, const uint64_t *fns,
                                size_t n, const uint64_t *keep, size_t nkeep,
                                uint64_t *stats);

It does what `compose_by_levels` does, with the same result (the edge `wfs_compose` returns):

1. **Index the layer.** One sequential pass over `f` collects, per level, the nodes that are
   substituted into, with their two children and a parent count (the `waiting` table of the
   Python version). Arrays, not Python dicts: a layer has 10^5 to 10^7 nodes.
2. **Level by level, bottom up.** For one level, every node's sub-result
   `ITE(fn[level], r(high), r(low))` depends only on sub-results of lower levels, which are
   complete. So the nodes of one level are independent: run them as Lace tasks
   (a parallel loop over the level's array, each iteration calling Sylvan's `ite`), which is
   exactly the shape Sylvan's scheduler is built for. Parallelism comes from two places: many
   nodes of a level at once, and each `ite` forking inside itself.
3. **Release early.** After a level is done, decrement the parent counts of its children's
   sub-results and drop those that reach zero, as the Python version does.
4. **Collect inside the step.** Sylvan's own collection is off in this binding, and stays off.
   Between two levels (never inside one: tasks hold unprotected edges), when the node table
   is above a threshold, call the binding's collection with the roots: `f`, the `fns`, the
   caller's `keep`, and every live sub-result. A level whose tasks would not fit even after
   a collection ends the computation with an error code, not with Sylvan's `exit(1)` (3.3).

The sub-results of a level are written to a plain array indexed by the node's position in the
level, so tasks never write to a shared hash table.

`Encoding.preimage(split=True)` calls it when the manager is the Sylvan core
(`STATIC_CORES` gains `"sylvan"`, and `compose_by_levels` dispatches on `mgr.core`).

### 3.2 `and_exists` stays Sylvan's own

Already parallel. No change. Its intermediate memory is a third of the substitution's
(docs/engine_split_step.md), and it is one call, so it cannot be collected inside; the table
must be sized for it.

### 3.3 Running out of table is an answer, not a crash

Today a full table makes Sylvan print and end the process. Three changes:

- The binding checks the table's fill before each operation it starts and after each
  collection; if a collection frees less than a set fraction, `wfs_*` returns an error and
  the Python manager raises `MemoryError`, as the own core does. This covers the split
  substitution (checked per level) and the start of `and_exists`.
- An `and_exists` that fills the table in mid-flight still ends the process: Sylvan has no
  way back from there. The kernel harnesses already run each kernel in a forked child and
  read a child that died unanswered as "not computed"; they are changed to say "the node
  table filled" when the exit status and the message match.
- Table sizes are derived from the memory limit of the run, not set by hand: with a limit of
  M bytes, about 0.62 M for nodes (24 bytes each) and 0.25 M for the cache (36 bytes each),
  rounded down to powers of two.

### 3.4 One table per process, enforced

A second live manager in one process raises, unless the first has been closed. The harnesses
already make one manager per forked child; the fork happens before Sylvan is initialised, so
the child starts its own workers (threads do not survive a fork).

### 3.5 Selection

`WAVEFRONT_BDD=sylvan`, `WAVEFRONT_BDD_THREADS=n`, `WAVEFRONT_STEP=split` select it; the
defaults do not change (own core, present step). The kernel harnesses
(tests/agi_v0_3/kernels.py, tests/agi_v0_4/kernels.py) gain `WF_V03_CORE` / `WF_V04_CORE` and
`..._THREADS`, record both in each saved reading, and set the table sizes from their memory
limit. The static order option (`WF_V03_ORDER`) works unchanged: Sylvan's order is static and
a caller's level is Sylvan's variable.

## 4. Correctness plan

Nothing computed on the new path is trusted until all of these hold:

1. `wfs_compose_levels` returns the same edge as `wfs_compose` on random functions and
   mappings, including with a collection forced between every two levels, at 1 and at 8
   threads (extend tests/symbolic/test_split_step.py and test_bdd_sylvan.py).
2. `cpre` and whole fixpoints equal the own core's, edge by edge after transfer, on the small
   models and on AGI v0.1 for several coalitions and a profile.
3. The two AGI v0.1 kernels have exactly 302461218730668589056 and 196126762366467883008
   states, none of the four initial states inside, at 1 and 12 threads.
4. A thread-safety soak: the differential tests repeated a few hundred times at 12 threads.
5. On the registered v0.3 build: readings already saved with the own core are recomputed and
   must agree (aligned: governments with companies keep control, inside; governments alone
   rule out an open-weight AI takeover without a treaty, outside).
6. A full table is reported as `MemoryError` or as "not computed", never as a wrong reading:
   run a kernel with a table that is deliberately too small.

## 5. What success looks like

Measured on the registered v0.3 build, aligned goal, governments with companies keeping
control (own core, present step: 86 minutes; own core, split step with the sifted order:
205 minutes; Sylvan, present step, 12 threads: 57 minutes):

- **Adopt** if the split step on Sylvan at 12 threads is at least twice as fast as the own
  core's split step on the same order, within the same memory limit.
- **Keep as an option** between 1.3 and 2 times.
- **Drop** below 1.3 times: the engineering and the second engine to keep correct are not
  worth it, and the next lever is solving for the start state only.

Processor time is reported beside wall time, because several zones in parallel on the own
core may still finish a queue sooner.

## 6. Order of work

1. Merge `engine-multicore-spike` into a branch from the working branch (which already has
   the split step and the reordering tools); resolve the overlaps in cores.py, encode.py,
   docs/framework_spec.md section 15 and tests/symbolic.
2. 3.3 and 3.4 (small, and they make everything after safer to test).
3. 3.1 with the correctness items 1 to 4.
4. 3.5 and correctness items 5 and 6.
5. The measurement of section 5 and a recommendation.

## 7. Risks

- **The level loop may not parallelise well** if most levels are narrow or the `ite` calls
  of a level share so much that workers duplicate each other's work. The spike saw
  processor time grow 2.6 to 4.3 times at 12 threads for this reason. Section 5's "drop"
  line is for this case.
- **Collections empty the whole operation cache** in Sylvan. Collecting often inside the
  step trades memory against recomputation; the threshold needs measuring.
- **A defect in a parallel engine can be silent.** Hence item 5: readings from this path are
  accepted only where they agree with the own core, until enough have agreed.
