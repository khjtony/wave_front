# Multi-core BDD core: an engineering spike

Date: 2026-11-20. Branch: `engine-multicore-spike` (local, not pushed).

**Question.** Does a multi-core BDD library make the heaviest computation of this project, a safety kernel `⟨⟨C⟩⟩□φ` on the symbolic engine, substantially faster than the project's own single-threaded C core (docs/engine_scaling.md section 7)?

**Answer.** Yes for the wall time of one kernel, at a high price in processor time.

- A third BDD core on the multi-core package Sylvan was built, passes the differential checks against the own core and gives the same kernels on the benchmark.
- On the benchmark kernel (`indifferent`, 152 million nodes at the peak) it took 175 s on 12 threads against 473 s for the own core on the same day: 2.7 times faster.
- On one thread it is 1.5 times slower than the own core (710 s). The 12-thread run used 2,020 processor-seconds against 473: 4.3 times the work for 2.7 times the speed. Eight threads gave almost all of the gain (182 s).
- Recommendation (section 8): adopt as an opt-in core for single long kernels, with the work of section 7 remaining; keep the own core as the default and for batches of kernels run side by side.

## 1. Choice of library

Sylvan (Tom van Dijk; https://github.com/trolando/sylvan, Apache-2.0) at version 1.12.8, commit `cd934c18`, with its scheduler Lace 1.11.1. Reasons:

- Its operations are parallel inside one call (work-stealing over the two cofactor branches, a lock-free node table and operation cache). The fixpoints here are a sequential Python loop over a few hundred very large calls, so nothing else would help (section 5).
- It has every operation the fixpoints call: `and`, `xor`, `ite`, `exists`, `and_exists`, functional composition (`sylvan_compose`, parallel and cached) and the Coudert-Madre `restrict`.
- It uses complement edges, so its canonical form has the same node counts as the own core's, and its edges translate to this project's edge integers by one bit flip.
- It is a C library with a C API, maintained, and it built here without root (cmake from pip, no GMP or hwloc needed).

Not evaluated: other multi-threaded packages (OxiDD, BeeDeeDee, HermesBDD). I did not find a reason to prefer one of them in the time of the spike and did not build them, so this document makes no claim about them.

## 2. What was built

| File | What it is |
|---|---|
| `wavefront/symbolic/_sylvan/wf_sylvan.c`, `wf_sylvan.h` | 425 lines of C over Sylvan: edge translation, the operations, a collector hook that marks the roots Python names, and the queries Sylvan lacks in the form needed (`pick_one` with the 0 branch first, exact counts past 64 bits, a node dump for `transfer`) |
| `wavefront/symbolic/_sylvan/build.py` | fetches the pinned Sylvan commit into `third_party/`, builds it with cmake as static position-independent libraries, then compiles the extension with cffi |
| `wavefront/symbolic/bdd_sylvan.py` | the manager: the interface of `bdd.BDD` and `bdd_c.BDD` |
| `wavefront/symbolic/cores.py` | `WAVEFRONT_BDD=sylvan`, `manager("sylvan")`, `sylvan_available()` |
| `tests/symbolic/test_bdd_sylvan.py`, `tests/symbolic/test_bdd.py` | the differential checks against the own core; the truth-table tests run on the third core too |
| `tests/symbolic/bench_multicore.py` | the benchmark of section 4 |

`encode.py` and `solve.py` are unchanged.

**How the interface is met.**

- **Edges.** Sylvan's edge is a node index with the complement in bit 63 and FALSE as 0. The layer turns it into `(index << 1) | (1 - complement)`, so TRUE is 0, FALSE is 1 and `f ^ 1` is negation, as in the other cores.
- **Operations.** `AND`, `XOR`, `ITE`, `exists`, `and_exists`, `compose` and `simplify` are Sylvan's. `rename` is a composition with variables. `restrict` is Sylvan's cofactor by a cube. `and_all` is a balanced tree of `and`. A varset is the cube Sylvan quantifies over.
- **Garbage collection.** Sylvan normally collects by itself when its table is full, from roots the program has registered one by one. The callers of this interface instead hold plain integers between the points where they call `maybe_gc`. So Sylvan's automatic collection is switched off, and `gc` runs one Sylvan collection whose marking hook marks the roots of the interface: the `gc` arguments, protected edges, registered holders, and the varsets.
- **Threads.** `WAVEFRONT_BDD_THREADS` workers (default 1) start with the first manager. They are not pinned to processors and sleep when idle.

## 3. Build and selection

```
uv pip install -e '.[fast,dev]' cmake        # cffi, and a cmake of 3.23 or later
python -m wavefront.symbolic._core.build     # the own core, as before
python -m wavefront.symbolic._sylvan.build   # clones and builds Sylvan under third_party/, then the extension
WAVEFRONT_BDD=sylvan WAVEFRONT_BDD_THREADS=12 \
  WAVEFRONT_SYLVAN_NODES_LOG2=28 WAVEFRONT_SYLVAN_CACHE_LOG2=26 python ...
```

- The build needs git, a C11 compiler and network access to github.com (Sylvan's build fetches Lace). `--prefix DIR` uses an installed Sylvan instead. `third_party/` is in `.gitignore`.
- `WAVEFRONT_SYLVAN_NODES_LOG2` (default 24) and `WAVEFRONT_SYLVAN_CACHE_LOG2` (default 23) are the sizes of the node table and of the operation cache, as powers of two. A node costs 24 bytes and a cache entry 36 bytes. The values above are 6.4 GB and 2.4 GB, the largest that fit a 12 GB address-space cap.
- The core is never the default and never a fallback (docs/framework_spec.md section 15).

## 4. Correctness

All of the following was run in the spike's own virtualenv on 2026-11-20.

| Check | Against | Result |
|---|---|---|
| random operation sequences: 19 operations on 10 variables, 300 hypothesis sequences of 40 steps; after each step equal edges after a transfer in each direction, equal `node_count`, `support`, `count`, `pick_one`, `top` | own C core | pass |
| the same with a Sylvan collection at every step (roots passed, protected and held by a holder): the table holds exactly what the roots reach, and every live result still agrees; 60 hypothesis sequences of 30 steps and 20 seeded ones of 60 steps | own C core | pass |
| exact counts over 150 levels, transfers under a permutation, the reference's errors | own C core | pass |
| encoding and fixpoints edge by edge (reachable set, attractor, two kernels per ending) on 40 random models | own C core | pass |
| the explicit cross-check, every coalition, 30 + 30 models; and 20 models with a collection at every opportunity | explicit engine | pass |
| truth tables of every operation (`test_bdd.py`, 150 hypothesis examples) | truth tables | pass |
| the whole of `tests/symbolic` with `WAVEFRONT_BDD=sylvan` and 4 threads (51 tests, 253 s) | explicit engine and both other cores | pass |
| benchmark kernel `aligned`: states in the kernel, kernel BDD nodes, membership of the four initial states | own C core | equal: 302,461,218,730,668,589,056 states, 33,009 nodes, all four outside |
| benchmark kernel `indifferent`, on 1, 4, 8 and 12 threads | own C core | equal in all four runs: 196,126,762,366,467,883,008 states, 433,674 nodes, all four outside |

The test files run Sylvan on 4 threads, so the parallel paths are the ones compared. `simplify` returned the same function as the own core in every step of these tests; the contract only asks for agreement on the care set, because Sylvan's `restrict` is not this project's code.

## 5. Benchmark

The computation is the one named in the task: AGI v0.1 (the v0.3 build with the open system off), FORCE variable order, collection deferred to 120 million nodes, `safe(enc, ["H"], balance_control ∧ a_objective = GOAL)` by tick layers.

```
WAVEFRONT_BDD=c python -m tests.symbolic.bench_multicore indifferent
WAVEFRONT_BDD=sylvan WAVEFRONT_BDD_THREADS=12 WAVEFRONT_SYLVAN_NODES_LOG2=28 \
  WAVEFRONT_SYLVAN_CACHE_LOG2=26 python -m tests.symbolic.bench_multicore indifferent
```

The machine is a KVM guest with 20 virtual processors on a Ryzen 9 5900X (12 physical cores), shared with other long computations: the other jobs kept two to four processors busy during these runs, and not the same number for every row. One benchmark ran at a time, each under a 12 GB address-space cap. Every figure is one run.

**`indifferent`** (56 tick layers, 7 collections on either core).

| Core | Threads | Wall s | Speed against the own core | Processor s | in `compose` s | in `and_exists` s | in collections s | Peak nodes | Peak resident GB |
|---|---|---|---|---|---|---|---|---|---|
| own C core | 1 | 473.2 | 1.00 | 473.3 | 298.7 | 163.6 | 10.5 | 152,231,606 | 5.10 |
| Sylvan | 1 | 710.1 | 0.67 | 711.7 | 450.2 | 248.4 | 9.9 | 152,045,358 | 6.57 |
| Sylvan | 4 | 296.2 | 1.60 | 1,178.8 | 202.8 | 83.8 | 9.0 | 152,045,358 | 6.96 |
| Sylvan | 8 | 182.4 | 2.59 | 1,418.9 | 123.7 | 48.1 | 7.4 | 152,045,358 | 6.83 |
| Sylvan | 12 | 174.7 | 2.71 | 2,020.1 | 124.2 | 42.5 | 7.6 | 152,045,358 | 7.25 |

The owner's earlier figure for the own core was about 314 s; today it measured 473 s with other jobs on the machine. The comparison above uses today's figure.

**`aligned`** (table of 2^27 nodes, cache of 2^25 entries).

| Core | Threads | Wall s | Speed against the own core | Processor s | Peak nodes | Peak resident GB |
|---|---|---|---|---|---|---|
| own C core | 1 | 23.1 | 1.00 | 23.5 | 57,537,918 | 3.08 |
| Sylvan | 1 | 29.6 | 0.78 | 30.8 | 57,501,555 | 3.03 |
| Sylvan | 12 | 6.3 | 3.64 | 82.0 | 57,501,555 | 3.03 |

**`self_preserving`** (table of 2^28 nodes, cache of 2^26 entries).

| Core | Threads | Wall s | Speed against the own core | Processor s | in `compose` s | in `and_exists` s | in collections s | Collections | Peak nodes | Peak resident GB |
|---|---|---|---|---|---|---|---|---|---|---|
OWN_ROW
| Sylvan | 12 | 974.6 | SPEED | 11,380.0 | 557.3 | 350.7 | 64.8 | 51 | 238,937,782 | 8.32 |

The Sylvan run found 259,418,167,803,592,593,408 states in the kernel (1,219,205 nodes), all four initial states outside. Its peak is 89% of the 268-million-node table, so this kernel is close to the largest this core can compute under a 12 GB cap. It collected after 51 of its 57 layers: one layer is enough to pass the threshold again (120 million nodes and twice what survived the previous collection), and every collection empties Sylvan's cache.

The peak node counts of the two cores differ by 0.1%: the count includes intermediate results not yet collected, and the two packages build slightly different intermediates. The results are the same functions.

**Memory.** The own core's resident memory follows the live nodes (5.1 GB at the peak). Sylvan's tables are allocated in full at the start: 8.8 GB of address space here, of which 6.6 to 7.3 GB became resident. Under a 12 GB cap the Sylvan core holds at most 2^28 = 268 million nodes, because the table size is a power of two and the next size is 12.9 GB for the nodes alone. When that table is full the process ends.

### Where the time goes

- **The Python loop costs nothing.** On the own core, 473.3 of the 473.2 s are inside six manager methods. The layered kernel makes 56 calls of `compose` (one preimage per tick) and 280 calls of `and_exists` (five actors per tick). Any gain has to come from inside those calls, and Sylvan does parallelise inside them.
- **One thread of Sylvan is 1.5 times slower than the own core** on both operations (450 against 299 s, 248 against 164 s). Its nodes are 16 bytes plus 8 in the table against 12 plus 8, its table is built for concurrent insertion, and a collection empties its whole cache where the own core keeps the entries that survive.
- **`and_exists` scales better than `compose`.** From 1 to 12 threads `and_exists` gains 5.8 times and `compose` 3.6 times. `compose` gains nothing from 8 to 12 threads.
- **The work grows with the threads.** Processor time goes from 712 s on one thread to 1,179, 1,419 and 2,020 s on 4, 8 and 12. The workers were busy almost all of the wall time in every run (processor time is 99.5%, 97% and 96% of wall time times threads). I could not separate the causes: the machine does not allow `perf` (`perf_event_paranoid` is 4). The candidates, by reasoning only: two workers computing the same subproblem before either has cached it; workers spinning while they look for work to steal; 12 workers and the other jobs sharing 12 physical cores behind 20 virtual ones; and all workers missing the processor cache into the same 9 GB of tables.
- **Layers after a collection are slow.** The layers that follow one of the 7 collections take about twice as long as their neighbours on Sylvan with 12 threads (9 to 12 s against 4 to 6 s), because the cache is empty. With a 268-million-node table the collection threshold could be raised and some of the 7 avoided. Not tried.

## 6. What a kernel batch should use

The kernels of a claim are independent of each other (one per start objective, per build). The own core runs one per process on one thread. Per processor-second it does 4.3 times the work of Sylvan on 12 threads and 2.5 times the work of Sylvan on 4. So when there are at least as many kernels waiting as cores, and memory for them (about 5 to 10 GB each), the own core in parallel processes finishes the batch sooner. The Sylvan core helps in the other case: one kernel that everything else waits for, or more cores than kernels.

## 7. What is missing

1. **One table per process.** Sylvan has one node table, so every manager of the Sylvan core is a view of it. A collection asked for by one manager reclaims edges that another live manager holds without protecting them. The engine's own use (one encoding, results registered as holders) is safe, and the tests pass, but the interface promises independent managers. The fix is either a rule (one Sylvan manager per process) enforced in `manager()`, or reference counts for edges held in Python.
2. **A full table ends the process.** There is no `MemoryError`: Sylvan prints a message and exits with status 1. The tables do not grow either (growth happens inside Sylvan's automatic collection, which is off). Needed: growth at `maybe_gc`, and a table-full handler that at least reports the computation that died. The forked kernel jobs of `tests/agi_v0_3/kernels.py` would read such a death as "the kernel's process died unanswered".
3. **Fork.** Worker threads do not survive a fork. A process that made a Sylvan manager and then forks gets a `RuntimeError` in the child on the next manager. The kernel jobs fork before they encode, so they are not affected; anything that forks later is.
4. **`transfer` is slow.** It walks the BDD in Python. Fine for tests, minutes for a kernel of millions of nodes. `tests/agi/common.py` stores kernels as node tables for later evaluation; that path was not tried on this core.
5. **`simplify`** is Sylvan's `restrict`: equal to the own core's result in every test, but not by construction.
6. **Packaging.** The build clones from github.com and needs cmake 3.23. Nothing checks the licence notice requirements of Apache-2.0 for a redistributed binary; today nothing is redistributed.
7. **Not measured.** `self_preserving` on the own core today (the owner's figure of about 3,036 s is from another day); any run with more than 12 threads; any run on a quiet machine; the attractors and forward reachability (`image` uses the same operations, but no figure was taken); WW2 or Cold War models at benchmark size.
8. **Tuning not tried.** The collection threshold (section 5), Sylvan's cache granularity, a cache larger than the node table's quarter.

## 8. Recommendation

**Adopt with named work remaining**, as an opt-in core, not as the default.

- The gain is real and the answers are identical: 2.7 times on `indifferent`, 3.6 times on `aligned`, with 8 threads enough for most of it.
- It is not a replacement for the own core. On one thread it is slower, it costs 4.3 times the processor time on 12 threads, it holds fewer nodes under the same memory cap, and items 1 and 2 of section 7 are behaviour the rest of the code does not expect.
- Before any registered claim is computed on it: item 2 (a full table must not look like a killed job), the one-manager rule of item 1, and one `self_preserving` run on both cores on the same day.
- For a queue of kernels on this machine the own core, one process per kernel, remains the better use of the cores (section 6).
