# The split step on the multi-core core

Date: 23 November 2026. Branch: `engine-multicore` (local, not pushed). Specification:
docs/engine_multicore_design.md. Earlier records: docs/engine_multicore_spike.md (the Sylvan
core), docs/engine_split_step.md (the split step on the own core).

All figures were measured on 23 November 2026 on the shared 5900X host (a KVM guest with 20
virtual processors on 12 physical cores), with other long computations running beside them
(load 4 to 8 from other jobs), one benchmark at a time, each process under a 12 GB
address-space cap and at most 12 threads. Every figure is one run.

## 1. Answer

- **The level loop parallelises.** The split substitution, written in C as one call per
  step with the nodes of each level handed to Sylvan's scheduler as one parallel loop, runs
  5.3 times faster at 12 threads than the own core's split step on AGI v0.3 with race
  pressure (145 s against 770 s in the substitution), and `and_exists` 3.1 times (35 s
  against 109 s). Every state count and every reading matched (section 5).
- **Whole kernels, same day, both engines, split step, 12 GB cap:**

  | Zone | Own core | Sylvan, 12 threads | Wall | Processor time |
  |---|---|---|---|---|
  | AGI v0.1 `indifferent`, sifted order | 18.3 s | 5.3 s | 3.5 times faster | 3.4 times more |
  | AGI v0.1 `indifferent`, FORCE order | 431 s | 93 s | 4.6 times faster | 2.5 times more |
  | AGI v0.3 race pressure, collection at 40 M nodes | 1,061 s | 376 s | 2.8 times faster | 3.7 times more |
  | AGI v0.3 race pressure, collection at 120 M nodes | 885 s | 181 s | 4.9 times faster | 2.3 times more |
  | Registered v0.3 build, `indifferent`, `["H"]`, `not:OPEN_TAKEOVER`, ticks 56 to 47 | 2,813 s | 1,393 s | 2.0 times faster | 5.3 times more |

- **Memory is the limit on the registered build.** Under 12 GB the Sylvan table holds 2^28
  nodes. The registered zone reaches tick 47 in it only because wide levels are now
  substituted in chunks with emergency collections between them (a change to the design,
  section 8); in ticks 48 and 47 those collections, each of which empties Sylvan's cache,
  bring the gain down from 3.4 times (ticks 56 to 49) to 1.7 times. Without the chunks the
  table filled in tick 48.
- **The success measure of the design (section 5) was not run**: that zone needs more than
  12 GB on both engines. Section 10 has the commands. On what was measured, the split step on
  Sylvan at 12 threads is 2.0 to 4.9 times as fast as the own core's split step on the same
  order and cap: in the design's "adopt" band (at least twice) on every zone, at its edge on
  the registered build under 12 GB. The recommendation (section 9) is to keep it as an
  option and to decide adoption on the success-measure run.

## 2. What was built

| Part | What it is |
|---|---|
| `wfs_compose_levels` in `wavefront/symbolic/_sylvan/wf_sylvan.c` | the split substitution in C, one call per step (section 2.1) |
| `BDD.compose_levels` in `wavefront/symbolic/bdd_sylvan.py` | its Python face; `compose_by_levels` (`wavefront/symbolic/substitute.py`) calls it when the manager is the Sylvan core, and `STATIC_CORES` includes `"sylvan"`, so `step="split"` and `step="moves"` take it |
| fill checks, table-full handler, table sizes | section 2.2 (design 3.3) |
| one manager per process, `close()` | section 2.3 (design 3.4) |
| `WF_V03_CORE`, `WF_V03_THREADS` (and `WF_V04_...`), `tests/agi/forked_engine.py` | the kernel harnesses select the core in the forked child, size its tables from the child's cap, record core and threads with every reading, and read a child that died of a full table as "not computed" (design 3.5) |
| `tests/agi_v0_3/bench_reorder.py` | `--core sylvan`, `--threads`, processor seconds per layer and in total, `--time-ops` (wall seconds in the substitution, in `and_exists` and in collections, per layer) |
| `tests/agi_v0_3/recheck_sylvan.py` | recomputes saved readings of the registered build on the engine of the harness and compares (design 4, item 5) |
| tests | section 5 |

### 2.1 The split substitution in C

`wfs_compose_levels(f, levels, fns, n, keep, nkeep, collect, gc_min, gc_factor, stats)`:

1. **Index.** One pass over `f` collects every node at or above the lowest substituted level
   into flat arrays (its variable, its two children as Sylvan edges, the positions of the
   children in the arrays or "below", and its number of parents). A hash map from node to
   position is used during this pass only.
2. **Order.** The positions are sorted by level (counting sort).
3. **Levels from the bottom.** For each level, its nodes are handed to Lace as one parallel
   loop (a divide-and-conquer task down to two nodes); each iteration calls Sylvan's `ite`
   on the level's function and the sub-results of the node's two children, and writes its
   result into its own slot of a plain array. `ite` itself forks inside, as before.
4. **Release.** After the loop, each child whose last parent was in the loop has its slot
   cleared.
5. **Collect.** Before each loop the fill of the table is looked at; when it is over the
   manager's policy (`gc_min_nodes`, `gc_factor` times what the last collection left), or
   over `COLLECT_FILL` of the table, and the caller passed `keep`, the table is collected
   with these roots: `f`, the functions, `keep` (to which Python adds every protected edge,
   registered holder and varset), and every live sub-result.
6. **Chunks (a change to the design, section 8).** A level wider than 2,048 nodes is handed
   over in chunks of 2,048, with step 4 between two chunks, and step 5 too when the table is
   above `COLLECT_FILL` (the manager's ordinary policy applies between levels only).

The result is the sub-result of the root, complemented as `f` is.

### 2.2 A full table (design 3.3)

- **Before an operation.** `and_exists`, `exists`, `compose`, `compose_levels` (before each
  chunk), `and_all`, `restrict` and `simplify` refuse to start when the table is filled above
  `REFUSE_FILL` (90%); the small operations (`AND`, `XOR`, `ITE`, `var`, `cube`) look once
  every 4,096 calls. A refusal returns a sentinel edge and the Python manager raises
  `MemoryError`.
- **The fill is estimated, not counted** (a change to the design, section 8). Counting the
  nodes scans one bit per node of the table (0.13 to 0.45 ms for 2^24 nodes, more for 2^28),
  which made a `cpre` on a small model a hundred times slower. The estimate reads Sylvan's
  region claims instead (one bit per 512 nodes): with `c` the claimed share of the regions and
  `L` the nodes that survived the last collection, the table holds about `L (1 - c) + 512 x
  (claimed regions)`. Sylvan runs out exactly when every region is claimed.
- **After a collection.** `maybe_gc` collects whenever the table is above `COLLECT_FILL`
  (70%), whatever its policy, and raises `MemoryError` when the collection leaves more than
  that.
- **In mid-flight.** An operation that fills the table cannot be undone. Sylvan's table-full
  handler is replaced by one that prints `wavefront: the Sylvan node table is full (...)` and
  ends the process with status 86 (Sylvan's own prints another message and exits with 1).
  The kernel harnesses send the child's stderr to a file next to its progress file and read
  a child that died with that status and that message as "not computed: the node table
  filled"; anything else that dies unanswered stays "died unanswered (exit status ...;
  killed?)".
- **Table sizes from the memory limit.** Unless `WAVEFRONT_SYLVAN_NODES_LOG2` and
  `..._CACHE_LOG2` are set, the sizes come from `WAVEFRONT_SYLVAN_MEMORY_GB` or else from the
  process's `RLIMIT_AS`: the largest powers of two within 62% of the limit at 24 bytes a node
  and within 25% at 36 bytes an entry. For 12 GB that is 2^28 nodes (6.4 GB) and 2^26 entries
  (2.4 GB); for 30 GB, 2^29 and 2^27; for 40 GB, 2^30 and 2^28.

### 2.3 One manager per process (design 3.4)

Making a Sylvan manager while another is live raises `RuntimeError`. "Live" is: not closed
with the new `close()`, and still referenced (the check runs Python's collector first). A new
manager begins by collecting what earlier ones left. The harnesses fork before the first
manager, so each child starts its own workers.

### 2.4 Selection (design 3.5)

```
WAVEFRONT_BDD=sylvan WAVEFRONT_BDD_THREADS=12 WAVEFRONT_STEP=split python ...
WF_V03_CORE=sylvan WF_V03_THREADS=12 WF_V03_STEP=split python -m pytest ...   # the v0.3 harness
python -m tests.agi_v0_3.bench_reorder --core sylvan --threads 12 --step split ...
```

The defaults do not change: the own core and the present step. `WF_V03_ORDER` works as
before: the order is static and a level of the interface is Sylvan's variable.

## 3. How to build

```
uv pip install -e '.[fast,dev]' cmake
python -m wavefront.symbolic._core.build      # the own core
python -m wavefront.symbolic._sylvan.build    # clones Sylvan 1.12.8 into third_party/, builds it, then the extension
```

The extension is stamped with a hash of `wf_sylvan.c` and `wf_sylvan.h`; a stale build does
not import. `third_party/` is git-ignored.

## 4. Why it is exact

- `compose_by_levels` (the own core's split step) and `wfs_compose_levels` evaluate the same
  recursion as `compose`: for a node `n` with variable `v`, `r(n) = ITE(f_v, r(hi), r(lo))`,
  with `r` of a node below the lowest substituted level being the node itself and `f_v = v`
  for a level without a function. docs/engine_split_step.md section 3 has the argument that
  evaluating it level by level gives the same functions.
- The nodes of one level are independent: each reads only sub-results of lower levels, which
  are complete before the level starts (the loop over a level is joined before the next).
  So the order inside a level, or a split of it into chunks, does not matter. Each task writes
  one slot of an array that no other task writes; the sub-results it reads were written
  before the loop was handed over.
- Sylvan's `ite` is the same Boolean function in any thread; its node table is canonical
  under concurrent insertion (Sylvan's design), so equal functions get equal edges.
- Nothing is collected inside a parallel loop (every collection is between two loops, on the
  calling thread), and every edge in use at that point is a root: `f`, the functions, the
  caller's `keep`, the manager's protected edges, holders and varsets, and every sub-result
  not yet released. The function of an unsubstituted level is made again after each
  collection.
- A full table never yields a result: an operation either does not start (`MemoryError`), or
  the process ends.

## 5. Correctness evidence

Checked by running (23 November, this branch, 12 GB cap):

| Item of the design's section 4 | Check | Result |
|---|---|---|
| 1. `wfs_compose_levels` returns `wfs_compose`'s edge | `tests/symbolic/test_split_step.py` with the Sylvan core in its cores: random functions of 12 variables and random substitutions (150 hypothesis examples), and again with a collection before every chunk of one node (100 examples); `cpre` with `split` and `moves` against `compose` on 80 random models, every coalition (more than 2,000 comparisons); the fixpoints edge by edge on 50 models collecting at every opportunity | pass, at 4 threads |
| 1, at 1 and 8 threads | `test_split_step_at_1_and_8_threads`: the tests above and the next row in a process of their own with 1 and with 8 workers | pass |
| 2. `cpre` and whole fixpoints against the own core, after a transfer | `test_split_step_against_the_own_core`: 40 random models of both generators, random targets, every ending, `HORIZON`, the domain, TRUE, FALSE, every coalition, the split step on Sylvan collecting before every level (and on every other model before every node) against the own core's present step; then reachable set, attractor stages, kernels by both methods and within the reachable set, contested regions | pass (more than 1,000 comparisons) |
| 2, on AGI v0.1 | `tests/agi_v0_3/test_split_step.py::test_sylvan_split_step_is_the_own_cores_cpre_on_v01`: three coalitions, 12 random targets, the endings, `balance_control` and the first six layers of both kernels, without a profile and with `no_treaty` (165 comparisons each); `test_whole_aligned_kernel_on_sylvan_is_the_own_cores`: the whole `aligned` kernel, edge by edge | pass |
| 3. The two AGI v0.1 kernels | `test_whole_kernels_on_sylvan_with_the_split_step[1]` and `[12]`; and every benchmark run of section 6 | 302461218730668589056 and 196126762366467883008 states at 1 and 12 threads (and at 1 and 12 threads in the benchmark, in two orders), none of the four initial states inside |
| 4. Soak | `test_soak` with `WF_SYLVAN_SOAK=300` at 12 threads, table of 2^20 nodes (a collection clears the whole table, and the soak collects before every chunk): per round, 20 random substitutions (14 variables, 9 substituted) against the own core, with chunks of 2,048, 1 and 2 nodes in turn and a collection before every chunk, plus the same without collection, and `cpre` on a fresh random model for 3 random targets and every coalition | pass: 300 rounds in 976 s; 6,000 substitutions each checked against the own core and against the same call without collection, and `cpre` on 300 models |
| 5. Readings of the registered build | `tests/agi_v0_3/recheck_sylvan.py`, Sylvan, split step, against `reports/agi_v0_3_kernels.jsonl` | 7 of 7 agree (table below); the zones of the design's item 5 that need more than 12 GB are in section 10 |
| 6. A full table | `test_a_full_table_is_an_error_not_a_reading`: a table of 2^16 nodes, an operation that needs 64 times that ends the process with status 86 and the message, and many small operations raise `MemoryError` at the refusal fill; `tests/agi_v0_3/test_split_step.py::test_a_full_table_reads_not_computed`: a kernel job of the harness with a table of 2^20 nodes reads "not computed: the node table filled: ..." and is saved as `over` | pass |
| the registered zone | the finished layers of ticks 53 to 47 have the same node counts on both engines (39,432 to 1,350,373) | equal |
| the race-pressure zone | 61950792389068363825152 states, none of the four initial states inside, on the own core and on Sylvan at 1, 4, 8 and 12 threads, and with both collection thresholds; the same count as docs/engine_reordering_spike.md section 5.4; every layer has the same node count | equal |

Readings of the registered build recomputed on Sylvan with the split step (the saved readings
were computed on the own core with the present step, FORCE order, except where noted):

| Question | Saved | Sylvan, split | Seconds (threads) |
|---|---|---|---|
| `["H","L"]`, `not:SILENT_TAKEOVER`, `aligned` | inside | inside | 2.7 (4) |
| `["H","L"]`, `not:SILENT_TAKEOVER`, `truth_seeking` | inside | inside | 2.6 (4) |
| `["H"]`, `balance_coexist`, `cap = agi`, `indifferent` | outside | outside | 2.7 (4) |
| `["H"]`, `balance_coexist`, `cap = agi`, `aligned` | outside | outside | 37.5 (4) |
| `["H"]`, `balance_coexist`, `cap = agi`, `truth_seeking` | outside | outside | 281.5 (4) |
| `["H"]`, `balance_coexist`, `cap = agi`, `self_preserving` | outside | outside | 396.2 (4) |
| `["H"]`, `not:OPEN_TAKEOVER`, `no_treaty`, `aligned` (design item 5: governments alone, no treaty), sifted order | outside | outside | 1,644.8 (12); own core split step 3,616 s on 21 November (docs/engine_split_step.md 6.2) |

The design's other zone of item 5 (`["H","L"]`, `balance_control`, `aligned`: inside) needs
more than 12 GB; it is the success-measure run of section 10.

Also run: `ruff check .` and `ruff format --check .`; the whole `pytest -q` on the final code in four processes (it does not fit in one under the cap): `tests/symbolic`, `toy`, `viz`, `ww2`: 374 passed, 26 skipped; `tests/agi*`, `analysis`, `bmc`, `cli`: 414 passed, 57 skipped; `tests/coldwar*`: 137 passed, 10 failed; `tests/engine`, `evidence`, `july1914*`, `model`, `report`, `research_console`: 650 passed, 2 failed. The 12 failures are `tests/coldwar/scenarios` C02 to C11 and `tests/july1914` J03 and J06; they fail the same way on `7d9ca81`, the commit this branch starts from (run there on the same day).

Reasoned, not run:

- That the equality holds for every input: the tests sample it. The argument is section 4.
- Thread safety beyond what the soak and the tests exercise: a race that shows up less often
  than once in those runs would not have been seen. The level loop shares no writable state
  between tasks except Sylvan's own tables.
- The fill estimate: it is exact when every survivor of the last collection sits in an
  unclaimed region, and overestimates otherwise; it was not compared with the exact count
  run by run. A wrong estimate can only make an operation refuse early or late; a late
  refusal ends in the table-full exit, never in a wrong result.
- `tests/agi_v0_4/kernels.py` with `WF_V04_CORE`: the same code as v0.3's harness, not run.

## 6. Measurements

Every run: `tests/agi_v0_3/bench_reorder.py`, the split step, `--cap-gb 12`, the Sylvan
tables sized from that cap (2^28 nodes, 2^26 cache entries: 8.8 GB reserved). *Wall* is the
kernel's computation from its first layer to its last; *processor* is user and system time of
every thread of the process over the same span; *peak* is the most nodes in the table
(garbage included), *memory* the peak resident memory. One run each.

### 6.1 AGI v0.1, the two kernels of the design

`safe(enc, ["H"], balance_control ∧ a_objective = GOAL)` on `V01`.

| Goal, order, collection threshold | Engine | Wall s | Processor s | Peak nodes | Memory | Collections |
|---|---|---|---|---|---|---|
| `aligned`, `v01_indifferent.json`, 40 M | own core | 1.2 | 1.2 | 2,401,561 | 312 MB | 0 |
| | Sylvan, 1 thread | 5.3 | 5.4 | 2,392,577 | 4,409 MB | 0 |
| | Sylvan, 12 threads | 2.1 | 25.1 | 2,394,625 | 4,407 MB | 0 |
| `indifferent`, `v01_indifferent.json`, 40 M | own core | 18.3 | 18.3 | 37,329,479 | 2,315 MB | 0 |
| | Sylvan, 1 thread | 25.2 | 25.4 | 37,308,929 | 4,972 MB | 0 |
| | Sylvan, 12 threads | 5.3 | 63.0 | 37,311,489 | 4,971 MB | 0 |
| `indifferent`, FORCE, 120 M (the spike's benchmark) | own core | 431.3 | 431.3 | 127,785,184 | 5,215 MB | 9 |
| | Sylvan, 12 threads | 93.4 | 1,067.9 | 122,663,331 | 6,462 MB | 9 |

- Every run: the recorded number of states, 7,617 and 111,688 (433,674 in FORCE) kernel
  nodes, none of the four initial states inside.
- On the spike's benchmark the split step on Sylvan takes 93 s where the spike's present step
  on Sylvan took 175 s (on 20 November; not rerun), and the own core 431 s.
- Sylvan's fixed cost: clearing and touching 8.8 GB of tables takes a few seconds and shows as
  4.4 GB resident however small the kernel is.

### 6.2 AGI v0.3 with race pressure

Build `{"open_system": true, "pressure": true, "hosting": false, "open_adoption": false,
"treaty_delay": 1}`, `indifferent`, `["H"]`, `balance_control`, order
`v03p_indifferent_tick51.json`, collection factor 2.

| Collection threshold | Engine | Wall s | Speed | Processor s | Processor / own core | Peak nodes | Memory | Collections |
|---|---|---|---|---|---|---|---|---|
| 40 M | own core | 1,061.4 | 1.00 | 1,061.3 | 1.00 | 42,174,490 | 2,434 MB | 107 |
| 40 M | Sylvan, 1 thread | 1,983.5 | 0.54 | 1,983.1 | 1.87 | 54,867,434 | 5,152 MB | 111 |
| 40 M | Sylvan, 4 threads | 707.1 | 1.50 | 2,674.9 | 2.52 | 54,868,420 | 5,152 MB | 112 |
| 40 M | Sylvan, 8 threads | 478.4 | 2.22 | 3,387.9 | 3.19 | 54,868,913 | 5,161 MB | 112 |
| 40 M | Sylvan, 12 threads | 376.5 | 2.82 | 3,878.0 | 3.65 | 54,226,155 | 5,192 MB | 112 |
| 120 M | own core | 884.9 | 1.00 | 884.9 | 1.00 | 120,732,567 | 5,478 MB | 21 |
| 120 M | Sylvan, 12 threads | 181.3 | 4.88 | 2,045.4 | 2.31 | 122,153,494 | 6,471 MB | 21 |

Where the time goes (`--time-ops`, 120 M runs, wall seconds over the whole kernel):

| | Substitution (collections inside it included) | `and_exists` | Rest |
|---|---|---|---|
| own core | 769.9 | 108.5 | 6.5 |
| Sylvan, 12 threads | 145.4 | 34.6 | 1.3 |
| ratio | 5.3 | 3.1 | |

- The kernel (61950792389068363825152 states, none of the initial states inside) and every
  layer's node count are the same in all seven runs.
- One Sylvan thread is 1.9 times slower than the own core; 4, 8 and 12 threads give 1.5, 2.2
  and 2.8 times the own core's speed at the 40 M threshold. Processor time grows with the
  threads, as in the spike.
- **The collection threshold matters more on Sylvan.** Each collection empties Sylvan's
  whole operation cache. At 40 M nodes both engines collect about 110 times; at 120 M, 21
  times, and Sylvan's time halves (376 to 181 s) while the own core's falls by a sixth. The
  2^28-node table has room for the larger threshold here.
- The 40 M rows (and 6.1) were measured before the chunks of section 8 were added; at
  these sizes (the table never near the collection fill) the chunks change only how a level
  wider than 2,048 nodes is handed to the workers. The Sylvan 120 M row ran on an
  intermediate build that applied the ordinary policy between chunks too; it collected 21
  times, as the own core did, so no chunk collection happened. 6.3 is on the final code.

### 6.3 The registered v0.3 build, down to tick 47

Build `DEFAULT`, `indifferent`, `["H"]`, `not:OPEN_TAKEOVER`, no profile, order
`default_aligned_sifted.json`, collection threshold 40 M nodes, factor 1.25 (the settings of
docs/engine_split_step.md section 6.1), `--stop-tick 47`. Cumulative from the start of the
kernel.

| Tick | Finished layer, nodes (both) | Own core: wall s, peak, memory | Sylvan 12 threads: wall s, processor s, peak, memory | Speed, cumulative |
|---|---|---|---|---|
| 52 | 176,510 | 19, 43 M, 2.3 GB | 7, 82, 43 M, 5.0 GB | 2.6 |
| 51 | 430,751 | 75, 43 M, 2.5 GB | 30, 322, 48 M, 5.2 GB | 2.5 |
| 50 | 854,935 | 311, 76 M, 3.7 GB | 109, 1,160, 122 M, 5.8 GB | 2.8 |
| 49 | 1,169,998 | 848, 158 M, 5.8 GB | 254, 2,734, 195 M, 7.0 GB | 3.3 |
| 48 | 1,273,826 | 1,829, 261 M, 10.0 GB | 816, 8,780, 255 M, 7.9 GB | 2.2 |
| 47 | 1,350,373 | 2,813, 261 M, 10.0 GB | 1,393, 14,963, 255 M, 8.0 GB | 2.0 |

Per layer (wall seconds of that layer alone, and where they went):

| Tick | Own core: layer s (substitution, `and_exists`, collections) | Sylvan: layer s (substitution, `and_exists`) | Collections own, Sylvan (cumulative) |
|---|---|---|---|
| 50 | 236 (185, 47, 85) | 80 (51, 24) | 39, 26 |
| 49 | 537 (434, 95, 199) | 145 (93, 45) | 85, 54 |
| 48 | 981 (769, 198, 347) | 562 (477, 78) | 140, 176 |
| 47 | 985 (803, 168, 374) | 577 (501, 69) | 198, 307 |

(The own core's collections run inside its substitution and are counted in both columns;
Sylvan's run inside the C call and are part of its substitution.)

- The own core reaches tick 47 in 2,813 s (2,635 s on 21 November) with a 261 M node table
  and 10.0 GB. Sylvan at 12 threads reaches it in 1,393 s with 255 M of its 268 M nodes and
  8.0 GB: 2.0 times as fast, for 5.3 times the processor time.
- Down to tick 49 Sylvan is 3.3 times as fast (3.7 times on layer 49 alone). In ticks 48 and
  47 the table is close to full: Sylvan collects 122 and 131 times in one layer, most of them
  between two chunks of a wide level (the emergency collections above 70% fill), and each one
  empties the operation cache. The layer gain falls to 1.7.
- The first run, before the chunks, filled the table in tick 48 after 49 layers in 247 s and
  ended with status 86 and the binding's message (section 8).
- Tick 46 was not attempted on either engine: the own core runs out of 12 GB in layer 46
  (docs/engine_split_step.md), and Sylvan's table is at 95% of its 2^28 nodes at tick 47.

## 7. What is missing

- **The success measure of the design (section 5) was not run.** The zone (`aligned`,
  `["H","L"]`, `balance_control` on the registered build) needs more than 12 GB on both
  engines. Section 10 has the commands; the recommendation depends on it.
- **The registered zone of 6.3 past tick 47**, on either engine: more than 12 GB.
- **6.1 and the 40 M rows of 6.2 ran on the code before the chunks** (section 8), the
  Sylvan 120 M row on an intermediate build (6.2). At those sizes the chunks only regroup
  the levels wider than 2,048 nodes; the final code was run on 6.3, on every reading of
  section 5 and on every test.
- **The collection policy for Sylvan is not tuned.** 6.2 shows that fewer collections pay on
  Sylvan (each empties its cache); 6.3 shows that a full table forces many. A policy that
  keeps the cache across collections (Sylvan can clear only entries whose nodes died, at some
  cost) or a larger cap would help most. Not tried.
- **Processor time.** At 12 threads Sylvan uses 2.3 to 5.3 times the own core's processor
  time. For a queue of independent zones with enough memory for several at once, one own-core
  process per zone still finishes the queue sooner (docs/engine_multicore_spike.md section 6).
- **The fill estimate is not validated against the exact count** run by run (section 5).
- **`tests/agi_v0_4/kernels.py`** has the same core selection as v0.3's and was not run.
- **`step="moves"` on Sylvan** is exercised by the tests only, not measured.
- **The whole test suite in one process** does not fit under the 12 GB cap with the Sylvan
  tables beside everything else (a `MemoryError` in `tests/symbolic` after 81% of the suite);
  it was run in parts. Several scenario tests (`tests/coldwar/scenarios` C02 to C11,
  `tests/july1914` J03 and J06) fail here and fail identically on the commit before this
  branch.
- Not measured: a quiet machine (other jobs kept 4 to 8 processors busy), more than 12
  threads, the own core's present step on the same day.

## 8. Changes to the design

1. **Chunks inside a wide level** (design 3.1 says "between two levels, never inside one").
   With collections between levels only, the registered zone filled Sylvan's 2^28-node table
   in tick 48: one level's sub-results and the garbage of their `ite` calls accumulate until
   the level ends, while the own core may collect every 256 nodes. A level wider than 2,048
   nodes is now handed over in chunks; between two chunks the fill is looked at and the table
   collected when it is above `COLLECT_FILL`. Exactness is unaffected: the nodes of a level
   are independent, so any split of the level gives the same sub-results. The manager's
   ordinary policy still applies only between levels: applying it between chunks too made
   tick 50 2.3 times slower (96 collections instead of 26, each emptying the cache).
2. **The fill is estimated, not counted** (design 3.3 says "checks the table's fill before
   each operation"). Counting scans one bit per node of the table, 0.13 to 0.45 ms for 2^24
   nodes; before every quantification of a small model it made `cpre` a hundred times slower
   (1,212 s for one test that the own core runs in seconds). The estimate reads Sylvan's
   region claims (one bit per 512 nodes). The small operations look once every 4,096 calls.
3. **The table-full exit is the binding's own** (design 3.3 says the harness matches Sylvan's
   status and message). Sylvan 1.12.8 lets a program replace its table-full handler; the
   binding's handler exits with status 86, which nothing else uses, and a message naming the
   binding. The harness matches both.
4. **`wfs_compose_levels` takes the collection policy** (`collect`, `gc_min`, `gc_factor`, and
   the last collection's survivors in `stats[3]`), which the design's signature leaves out:
   the C call must decide when to collect without returning to Python.
5. **The working branch.** This worktree started at the `main` merge (`d807861`); the branch
   with the split step and the CUDD binding the task names is
   `worktree-bridge-cse_01RTpGKupSSHRF2WjPvHeBXq` at `7d9ca81` (the design's commit).
   `engine-multicore` was branched from `7d9ca81` and the spike merged into it.

## 9. Recommendation

By the thresholds of the design's section 5, on what could be measured under 12 GB:

| Zone | Own core split | Sylvan split, 12 threads | Ratio | Band |
|---|---|---|---|---|
| AGI v0.1 `indifferent`, FORCE | 431 s | 93 s | 4.6 | adopt |
| AGI v0.3 race pressure, 40 M | 1,061 s | 376 s | 2.8 | adopt |
| AGI v0.3 race pressure, 120 M | 885 s | 181 s | 4.9 | adopt |
| registered build, ticks 56 to 47 | 2,813 s | 1,393 s | 2.0 | adopt, at the line |
| registered build, `no_treaty` zone (different days) | 3,616 s | 1,645 s | 2.2 | adopt, not same day |

**Recommendation: keep it as an option now, and adopt it for single heavy zones if the
success-measure run (section 10) is at least twice as fast at the same memory limit.**

- The engine is exact on every check, the level loop does parallelise (5.3 times in the
  substitution), and the gain is at or above the "adopt" line on every zone measured.
- But the success measure itself has not been run, and the one registered zone measured sits
  exactly at 2.0 because the 12 GB table is nearly full there. With the 20 to 40 GB the heavy
  zones are given in production, Sylvan's table is 2^29 to 2^30 nodes and the emergency
  collections of ticks 48 and 47 go away; the measured layers before that point ran 3.3 to
  3.7 times faster. That is the expectation to check, not a result.
- Processor time is 2.3 to 5.3 times the own core's. For a queue of independent zones on this
  machine with memory for several at once, the own core in parallel processes stays the better
  use of the cores; Sylvan is for the zone everything waits for.
- Default unchanged: the own core and the present step. The kernel harnesses select Sylvan
  with `WF_V03_CORE=sylvan WF_V03_THREADS=12 WF_V03_STEP=split`, and record the engine with
  every reading. Readings from it should still be accepted only where they agree with the
  own core (design, section 7) until more have agreed; seven of seven have so far.

## 10. Reproducing, and the runs that need more than 12 GB

Set-up: `uv venv .venv-spike --python 3.13 && uv pip install --python .venv-spike/bin/python
-e '.[fast,bmc,dev]' cmake`, then `python -m wavefront.symbolic._core.build` and
`python -m wavefront.symbolic._sylvan.build`.

```
# 6.1 (each with --core c, then --core sylvan --threads 1 and --threads 12)
python -m tests.agi_v0_3.bench_reorder --model v01 --goal indifferent --step split --no-probe \
    --order-from tests/agi_v0_3/orders/v01_indifferent.json --gc-min-nodes 40000000 --cap-gb 12 \
    --core sylvan --threads 12
python -m tests.agi_v0_3.bench_reorder --model v01 --goal indifferent --step split --no-probe \
    --cap-gb 12 --core sylvan --threads 12                    # FORCE, 120 M

# 6.2 (threads 1, 4, 8, 12; --gc-min-nodes 120000000 for the second pair)
python -m tests.agi_v0_3.bench_reorder --model v03p --goal indifferent --coalition H \
    --target balance_control --order-from tests/agi_v0_3/orders/v03p_indifferent_tick51.json \
    --gc-min-nodes 40000000 --step split --no-probe --time-ops --cap-gb 12 --core sylvan --threads 12

# 6.3
python -m tests.agi_v0_3.bench_reorder --model default --goal indifferent --coalition H \
    --target not:OPEN_TAKEOVER --order-from tests/agi_v0_3/orders/default_aligned_sifted.json \
    --gc-min-nodes 40000000 --gc-factor 1.25 --step split --no-probe --time-ops --cap-gb 12 \
    --stop-tick 47 --core sylvan --threads 12

# the readings of section 5
WF_V03_CORE=sylvan WF_V03_THREADS=12 WF_V03_STEP=split WF_V03_MEMORY_GB=11 \
    WF_V03_READINGS=.bench/recheck.jsonl python -m tests.agi_v0_3.recheck_sylvan [NAME ...]

# the tests
python -m pytest tests/symbolic/test_split_step.py tests/symbolic/test_bdd_sylvan.py -q
python -m pytest tests/agi_v0_3/test_split_step.py -q
WAVEFRONT_BDD_THREADS=12 WF_SYLVAN_SOAK=300 python -m pytest tests/symbolic/test_bdd_sylvan.py -k soak
```

### Runs that need more than 12 GB (not run)

The success measure (design section 5): the registered build, `aligned`, `["H","L"]`,
`balance_control`. Same cap for both engines, one after the other, nothing else of ours on the
machine. With a 40 GB cap Sylvan's tables are 2^30 nodes (25.8 GB) and 2^28 cache entries
(9.7 GB). The own core's figure in the design (205 minutes, split step, sifted order) is the
one to repeat on the same day:

```
python -m tests.agi_v0_3.bench_reorder --core c --model default --goal aligned --coalition H+L \
    --target balance_control --order-from tests/agi_v0_3/orders/default_aligned_sifted.json \
    --gc-min-nodes 40000000 --step split --no-probe --time-ops --cap-gb 40 \
    --out .bench/mc_success.jsonl > .bench/mc_success_c.log
python -m tests.agi_v0_3.bench_reorder --core sylvan --threads 12 --model default --goal aligned \
    --coalition H+L --target balance_control \
    --order-from tests/agi_v0_3/orders/default_aligned_sifted.json \
    --gc-min-nodes 40000000 --step split --no-probe --time-ops --cap-gb 40 \
    --out .bench/mc_success.jsonl > .bench/mc_success_sylvan12.log
```

Both records carry `inside` (the reading at the start state: production reads inside) and the
kernel's number of states, which must be equal. Sylvan with `--gc-min-nodes 120000000` is worth
a third run (section 6.2).

The same reading through the harness, as production would compute it:

```
WF_V03_CORE=sylvan WF_V03_THREADS=12 WF_V03_STEP=split WF_V03_MEMORY_GB=40 \
    WF_V03_ORDER=tests/agi_v0_3/orders/default_aligned_sifted.json \
    WF_V03_READINGS=.bench/recheck.jsonl python -m tests.agi_v0_3.recheck_sylvan HL_control_aligned
```

The registered zone of 6.3 to the end, on both engines (the own core needs more than 12 GB from
layer 46):

```
python -m tests.agi_v0_3.bench_reorder --core c --model default --goal indifferent --coalition H \
    --target not:OPEN_TAKEOVER --order-from tests/agi_v0_3/orders/default_aligned_sifted.json \
    --gc-min-nodes 40000000 --gc-factor 1.25 --step split --no-probe --time-ops --cap-gb 40 \
    --out .bench/mc_reg_full.jsonl
python -m tests.agi_v0_3.bench_reorder --core sylvan --threads 12 --model default \
    --goal indifferent --coalition H --target not:OPEN_TAKEOVER \
    --order-from tests/agi_v0_3/orders/default_aligned_sifted.json \
    --gc-min-nodes 40000000 --gc-factor 1.25 --step split --no-probe --time-ops --cap-gb 40 \
    --out .bench/mc_reg_full.jsonl
```

Production reads this zone inside (`reports/agi_v0_3_kernels.jsonl`, split step, 40 GB).

## 11. The success measure in full, and the decision (23 November 2026)

The zone of the design's section 5 (registered v0.3 build, aligned goal, governments with
companies keeping control, sifted order, split step, 40 GB limit), both engines on the same day:

| | Own core | Sylvan, 12 threads, collection from 120 M nodes |
|---|---|---|
| Wall time | 9,965 s | 4,520 s |
| Processor time | 9,962 s | 46,808 s |
| Peak resident memory | 5.4 GB | 20.4 GB |
| States in the zone | 702785462581965997670400 | 702785462581965997670400 |
| Start state, aligned | inside | inside |

2.2 times: the "adopt" band. A first Sylvan run with collection from 40 M nodes took 8,010 s
(1.5 times against an earlier own-core run of 12,300 s); the collection threshold is what
changed. The price is 4.7 times the processor time and about four times the memory.

The owner's decision: merged, and the default of the kernel harnesses
(`tests/agi/forked_engine.py`, `chosen` and `attempts`): the Sylvan core with 12 threads when
its extension is built, and after an attempt that ran out of memory (the cap, or a full node
table) the own core under the same cap. `manager()` keeps the compiled core as its default.
