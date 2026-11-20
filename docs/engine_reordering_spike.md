# Dynamic variable reordering: a spike on CUDD

Question: does dynamic variable reordering (sifting), as a mature BDD library offers it, substantially reduce the memory and time of the guarantee zones (`⟨⟨C⟩⟩□φ`, `wavefront.symbolic.safe`)? The compiled core (docs/engine_scaling.md section 7) keeps one static order, the FORCE order of `tests.agi.common.force_order`.

All figures below were measured on 2026-11-20 on the shared 5900X host, one process pinned to one core, under an address-space cap of 12 GB, while two production kernel jobs ran beside them (load average 10 to 16). Times on this day are therefore slower than the figures recorded earlier for the same computations (for example 522 s here against about 314 s for `indifferent` on the compiled core).

## 1. Answer

- **The variable order is worth a factor of more than 20 on the AGI v0.1 zones, and sifting finds such an order.** On AGI v0.1 with `a_objective = indifferent`, the compiled core takes 522 s and 5.2 GB in the FORCE order. In an order found by sifting it takes 22 s.
- **The gain does not need the library at run time.** The order that CUDD's sifting reaches, written back as a static order (`var_order=` and `actions=` of `encode`), gives the compiled core the whole gain. The compiled core in that order is faster than CUDD reordering as it goes (22 s against 55 s).
- **CUDD as the engine is not ready.** With a static order it is 2.6 times slower than the compiled core. With reordering inside operations it was fast on two zones, but it stalled on the two harder ones (stopped by hand after 50 and 33 minutes), and it crashed once in four runs of the larger model.
- **The transition functions are not what shrinks.** They are about 1,000 nodes on AGI v0.1 and 3,000 on v0.3 in every order. What shrinks is the intermediate result of the substitution in the controllable predecessor (7.2 million nodes to 0.33 million) and the kernel layers (434 thousand to 110 thousand).
- **The model that hurts comes down too.** On AGI v0.3 with race pressure a partly sifted order takes the `indifferent` zone from about 59 minutes to 15 on the compiled core, and the zone for all four objectives at once, which did not fit in 20 GB, finishes in 64 minutes within 9.9 GB.

Recommendation (section 7): adopt the result, not the engine. Use the CUDD core offline to find an order, compute every result on the compiled core in that order, and change the static order heuristic so that action bits are placed among the state bits.

## 2. What was built

| File | Content |
|---|---|
| `wavefront/symbolic/bdd_cudd.py` | the manager: the interface of `bdd.BDD` on CUDD |
| `wavefront/symbolic/_cudd/wf_cudd.c`, `wf_cudd.h` | a shim over CUDD's public interface (about 330 lines), bound with cffi |
| `wavefront/symbolic/_cudd/build.py` | the build; `--fetch` downloads and compiles CUDD 3.0.0 under `third_party/` |
| `wavefront/symbolic/cores.py` | `WAVEFRONT_BDD=cudd` and `manager("cudd")` |
| `wavefront/symbolic/encode.py` | groups each current-state bit with its next-state bit when the manager has `group` |
| `tests/symbolic/test_bdd_cudd.py` | the differential checks against the reference |
| `tests/agi_v0_3/bench_reorder.py` | the benchmark of this document |
| `tests/agi_v0_3/orders/*.json` | the three orders sifting found (bit names, top first), for `--order-from` |

Design:

- **Edges.** An edge is the same `int` as in the other cores, `(handle << 1) | complement`, TRUE 0 and FALSE 1, so callers still negate with `^ 1` and compare with `==`. A handle names one regular CUDD node and owns one CUDD reference. A table from node address to handle makes the handle of a function unique. CUDD's reordering rewrites nodes in place and keeps the function of every referenced node, so handles survive a reordering.
- **Variable identity.** The callers address variables by level. In this core a level is the variable's CUDD *index*: fixed at creation, not moved by reordering. Every argument and result that names a variable uses it: `add_var`, `var`, the keys of `compose`, `rename`, `restrict` and `cube`, variable sets, `support`, the positions of an `evaluate` array. The place of a variable in the current order is a separate notion, `position(level)` and `order()`.
- **What stays equal under reordering.** Functions (compared across managers with `transfer`), `support`, `count`, `evaluate`, and `pick_one`. `pick_one` decides the variables of the support in level order and takes 0 where it can, whatever the current order, so strategy moves are those of the other cores.
- **What follows the current order.** `node_count`, `top`, `low` and `high`. With reordering off they equal the other cores'.
- **Collection.** `gc(roots)` has the reference's roots. It gives up the reference of every other handle; CUDD then frees by reference count, also in the middle of operations. `maybe_gc` runs once the live nodes pass `min(gc_min_nodes, 100,000)`: a handle kept needlessly costs memory and sifting time.
- **Reordering.** `WAVEFRONT_CUDD_REORDER`: `off` (default), `auto` (CUDD's automatic reordering inside operations, group sifting), or `points` (only at `maybe_gc`, when only rooted functions are alive). `reorder()` runs one pass on request. `group(levels)` ties variables together in their present relative order.
- **Memory.** CUDD's memory limit is `WAVEFRONT_CUDD_MAX_MEMORY_MB`, or four fifths of the process's address-space limit when it has one. A failed allocation raises `MemoryError`.

Not implemented, or different from the reference:

- `simplify` is `Cudd_bddRestrict`. It keeps the contract (agreement with `f` on the care set) but does not always return the reference's function: about one call in a thousand differs even in the same order.
- `gc_factor` is ignored. `live_nodes` and `peak_nodes` count referenced nodes only, where the compiled core's count the node table with its uncollected garbage. `stats()` has CUDD's counters.
- `shuffle(order)` (for tests) does not check the groups.
- Nothing raises `NotImplementedError`: every method of the interface is there.

## 3. Build and select

```
uv pip install -e '.[fast]'
python -m wavefront.symbolic._cudd.build --fetch     # CUDD 3.0.0 into third_party/, then the binding
WAVEFRONT_BDD=cudd WAVEFRONT_CUDD_REORDER=auto python ...
python -m pytest tests/symbolic/test_bdd_cudd.py -q
```

`--cudd DIR` or `WAVEFRONT_CUDD_SRC` names a CUDD source tree compiled with `./configure CFLAGS="-O3 -fPIC" && make`. `third_party/` is in `.gitignore`. The core is never a default and never a fallback. `WAVEFRONT_CUDD_BACKTRACE=1` prints the C stack if CUDD crashes.

## 4. Correctness evidence

Checked by running:

- `tests/symbolic/test_bdd_cudd.py`, 18 tests against the pure-Python reference:
  - random operation sequences in the static order (150 hypothesis sequences of 40 steps): every result equal as an edge after transfer in both directions, and `node_count`, `support`, `count`, `pick_one`, `top` equal; the same with a collection at every step;
  - the same sequences with the order changed under the functions: a random shuffle after every step (100 sequences), sifting passes and collections (60 sequences), and CUDD's automatic reordering from 20 nodes on (60 seeded sequences, of which more than 10 must end in another order);
  - `pick_one` equal to the reference's in 8 random orders per function; groups adjacent and in order after sifting; exact counts over 150 levels; the reference's exceptions; a released edge refused;
  - the fixpoints on 25 random models in each of the three modes, edge by edge against the reference (reachable set, attractors, kernels with and without `within`), with the first reordering forced early;
  - the explicit cross-check (`check_model`, every coalition, strategies and witnesses) on 15 + 15 models in each mode;
  - after each sequence CUDD's own table checks pass and no reference is left (`Cudd_CheckZeroRef` is 0).
- A soak outside the suite: 6,000 further seeded sequences (static, shuffled, sifted), 200,000 steps, no difference.
- `tests/symbolic` as a whole (55 tests) passes with `WAVEFRONT_BDD=cudd`, with reordering off and with `auto` from 200 nodes on, and unchanged under the compiled core.
- `ruff check .` and `ruff format --check .` pass. The whole suite (`pytest -q -x`) ran 368 passed and 49 skipped up to `tests/coldwar/scenarios/test_C02.py`, which fails; it fails in the same way on the revision this branch started from (d807861), so it is not caused by this work. The tests after it were not run to the end (stopped after 30 minutes).
- On the benchmark zones the number of states in the kernel and the membership of the four initial states are equal in every configuration that finished:

| Zone (AGI v0.1) | States in the kernel | Initial states inside | Configurations that agree |
|---|---|---|---|
| `aligned` | 302461218730668589056 | none of the four | compiled core; CUDD static; CUDD `auto`; CUDD `points` |
| `indifferent` | 196126762366467883008 | none of the four | compiled core in four orders; CUDD static; CUDD `auto` |
| `self_preserving` | 259418167803592593408 | none of the four | compiled core in two sifted orders |

With the static order CUDD reproduces the compiled core's graphs node for node: the kernel has 433,674 nodes and the largest intermediate 7,226,377 on both.

Not checked: the `self_preserving` count was not compared with a run in the FORCE order on this day (two different sifted orders agree with each other). The AGI v0.3 counts of section 5.4 were not compared with a FORCE-order run either; see there.

## 5. Measurements

Zone: `safe(enc, ["H"], balance_control ∧ a_objective = GOAL)`. Columns:

- *time*: the fixpoint, wall clock, including the harness's sizing of every `compose` and `and_exists` result (the same in every row);
- *memory*: peak resident memory of the process;
- *peak nodes*: for the compiled core the high-water mark of the node table, which includes garbage not yet collected (collection is deferred to 120 million nodes); for CUDD the peak of referenced nodes, and in brackets the peak of its node table with dead nodes;
- *largest intermediate*: the largest result of a `compose` or `and_exists`, in nodes;
- *kernel*: the nodes of the kernel BDD.

### 5.1 AGI v0.1, `indifferent` (180 BDD variables)

| | Configuration | Time | Memory | Peak nodes | Largest intermediate | Kernel |
|---|---|---|---|---|---|---|
| (a) | compiled core, FORCE order | 522 s | 5,249 MB | 152,231,606 | 7,226,377 | 433,674 |
| (b) | CUDD, FORCE order, reordering off | 1,373 s | 4,848 MB | 24,241,237 (62,336,890) | 7,226,377 | 433,674 |
| (c) | CUDD, reordering `auto` | 55 s | 353 MB | 816,109 (5,489,162) | 330,310 | 110,063 |
| (d) | compiled core, the order (c) ended in, static | 22 s | 2,316 MB | 37,329,479 | 341,689 | 111,688 |
| (e) | compiled core, the order sifting found on `aligned`, static | 73 s | 5,500 MB | 121,928,168 | 1,321,875 | 154,879 |
| (f) | compiled core, FORCE with the actors as vertices (`--force-actions`, no library) | 129 s | 5,742 MB | 126,331,376 | 1,583,401 | 138,334 |

- (c) ran 11 reorderings, 15.5 s of its 55 s.
- (d), (e) and (f) reach the 120-million-node collection threshold once at most, so their memory is that threshold's doing, not the zone's: (d) creates 37 million nodes in all and collects none.
- (f) is a guess at the cheapest remedy: the FORCE heuristic with each actor as one more vertex of the hypergraph, so that action bits land among the state bits (`bench_reorder._force_with_actions`). It recovers a factor of 4 of the 23.
- (b) spends 72 s in CUDD's own collections; its cache grew to 2 GB.

### 5.2 AGI v0.1, `aligned`

| Configuration | Time | Memory | Peak nodes | Largest intermediate | Kernel |
|---|---|---|---|---|---|
| compiled core, FORCE order | 24 s | 3,170 MB | 57,537,918 | 692,491 | 33,009 |
| CUDD, FORCE order, reordering off | 65 s | 695 MB | 2,571,855 (9,884,784) | 692,491 | 33,009 |
| CUDD, reordering `auto` | 16 s | 193 MB | 501,418 (2,645,958) | 202,973 | 11,214 |
| CUDD, reordering `points`, one pass after the encoding | 160 s | 1,240 MB | 2,447,917 (10,934,378) | 626,796 | 11,460 |

Reordering only between operations (`points`) is worse than no reordering here. It sees the encoding and the kernel layers, which are small, and not the intermediates, which are where the cost is.

### 5.3 AGI v0.1, `self_preserving`

| Configuration | Time | Memory | Largest intermediate | Kernel |
|---|---|---|---|---|
| compiled core, FORCE order (recorded earlier, not rerun) | about 3,036 s | about 10 GB | not measured | not measured |
| CUDD, reordering `auto` | stopped by hand after 2,975 s: 20 of 57 layers done in 1,161 s, then 30 minutes in one layer without finishing; 2.4 GB | | | |
| compiled core, the order sifting found on `indifferent`, static | 93 s | 5,737 MB | 2,406,767 | 541,717 |
| compiled core, the order sifting found on `aligned`, static | 186 s | 5,536 MB | 5,363,870 | 365,620 |

### 5.4 AGI v0.3 with race pressure (204 BDD variables)

Build: `open_system`, `pressure`, no `hosting`, no `open_adoption`, `treaty_delay = 1`.

| Configuration | Goal | Time | Memory | Largest intermediate | Kernel |
|---|---|---|---|---|---|
| compiled core, FORCE order (recorded earlier, not rerun) | `indifferent` | about 59 min | about 10 GB | not measured | not measured |
| CUDD, reordering `auto`, run 1 | `indifferent` | crashed in its fifth layer, between 1 and 4 minutes in (section 6) | | | |
| CUDD, reordering `auto`, run 4 | `indifferent` | stopped by hand after 33 minutes: 6 of 57 layers done in 246 s, then 29 minutes in one layer; 2.1 GB | | | |
| compiled core, the order of run 4 after its sixth layer, static | `indifferent` | 873 s | 5,716 MB | 3,705,379 | 756,244 |
| compiled core, FORCE order (recorded earlier, not rerun) | all four at once | did not fit: more than 20 GB | | | |
| compiled core, the same sifted order, static | all four at once | 3,840 s | 9,923 MB | 10,497,499 | 1,920,307 |

- The `indifferent` kernel in the sifted order has 61950792389068363825152 states and contains none of the four initial states. This was not compared with a FORCE-order run on this day; it should equal the production record of the same zone.
- The zone for all four start objectives at once fits under the 12 GB cap in the sifted order: 64 minutes, node table at most 316,693,882 nodes with 51 collections. Its kernel has 264853746508556395487232 states and contains none of the four initial states. There is no FORCE-order run to compare it with.
- The order used is a partial one: what 246 s of sifting had reached when the CUDD run was still in its early layers, and on the `indifferent` goal only.

### 5.5 Sizes of the transition pieces

`next_fn` are the next-state functions the fixpoints substitute (`Encoding.preimage`); `trans_parts` are the per-variable relations `x' ↔ f(s, a)` that `image` uses. Shared size is the node count of all of them together.

| Model, order | `next_fn`: count, shared, largest | `trans_parts`: count, shared, largest | Availability, shared |
|---|---|---|---|
| v0.1, FORCE | 80, 986, 49 | 38, 967, 65 | 306 |
| v0.1, FORCE then two sifting passes over the encoding alone | 80, 1,016, 63 | 38, 1,116, 115 | 358 |
| v0.1, the order `auto` ended in on `indifferent`, replayed | 80, 856, 52 | 38, 947, 87 | 440 |
| v0.3 pressure, FORCE | 91, 2,903, 968 | 44, 2,161, 1,072 | 394 |
| v0.3 pressure, the sifted order of 5.4, replayed | 91, 2,862, 943 | 44, 2,003, 949 | 412 |

The transition pieces are one to three thousand nodes in any of these orders: FORCE already does this part well, and a better order does not shrink them. (All of an encoding's roots together, with the guards and the named predicates, do shrink: 109,603 nodes to 29,907 on v0.1 and 901,995 to 70,909 on v0.3. They are not what the fixpoint works on.)

### 5.6 What the sifted order changes

The FORCE order places every action bit at the top (`actions="top"`) and orders the state variables by the supports of their updates. The order sifting reaches on v0.1 (`tests/agi_v0_3/orders/v01_indifferent.json`), read as `encode` arguments:

```
actions = {"A": "tick", "H": "a_control", "L": "pending_H_regulate_up",
           "Clock": "dependence", "Nature": "unlocked"}
var_order = tick, a_objective, trust, a_rights, threat, h_power, shut, a_control, opinion,
            strong_before_majority, oversight, regime, paused, nationalized, ...
```

Two things moved. Each actor's action bits went down among the state bits, next to what that actor's actions change. And `a_objective`, which the goal fixes and no update changes, went to the top under `tick`. The substitution `X(f(s, a))` is a function of the state and of every actor's action; with all action bits above all state bits its BDD has to keep, under each joint action, a separate copy of whatever part of the state the actions touch. That is the 7.2 million nodes. The static order has no information about this: FORCE reads only the state variables' supports.

The replay loses a little against the bit-level order (341,689 nodes against 330,310): `encode` takes an order of whole variables and keeps an actor's bits together, where sifting had split a few of them.

## 6. Problems found

- **A crash.** The first `auto` run on AGI v0.3 with pressure died of a general protection fault in `cuddSwapInPlace` (cuddReorder.c line 913, reading the then-child of a node of the upper level during a swap), inside a reordering triggered from `Cudd_bddVectorCompose`. Three more runs of the same command did not crash (two under a debugger for 11 and 20 minutes, one plain for 33 minutes). The cause is not established. Either the adapter's reference counting has an error that only large runs expose (the small tests end with zero references and pass CUDD's table checks), or CUDD has a defect in this path. Until this is settled no result computed with reordering inside operations should be trusted without a second computation.
- **Stalls.** `auto` on `self_preserving` and on v0.3 with pressure stopped making progress inside one layer for half an hour. CUDD restarts an operation from the beginning after each reordering it triggers, and sifting a table of millions of nodes takes minutes. When one substitution keeps outgrowing the threshold, the work is thrown away again and again. This is the usual cost of reordering inside operations, and it arrived exactly on the zones that are hard.
- **Static speed.** In the same order CUDD is 2.6 to 2.7 times slower than the compiled core (1,373 s against 522 s; 65 s against 24 s), with about the same memory on the larger zone. Its caches and collection policy were left at their defaults.
- **`points` mode** does not help (5.2).
- **Orders are learned per model and help less off their goal.** The order found on `aligned` gives 7 times on `indifferent`, where the order found on `indifferent` itself gives 23 times. A new build of the model has other variables and needs a new order.

## 7. Recommendation

**Adopt, with named work remaining, as an order finder; do not adopt as an engine.**

What to adopt now, at low risk:

1. Compute the heavy zones on the compiled core in a sifted static order. An order cannot make the compiled core wrong, so the crash and the `simplify` difference of the CUDD core do not touch the results. The three orders in `tests/agi_v0_3/orders/` are usable today through `encode(cm, var_order=..., actions=...)`; `bench_reorder._replay` turns a bit-level order into those two arguments.
2. Find an order with a short CUDD run: `bench_reorder --core cudd --reorder auto --dump-order FILE` on the cheapest goal of the build, stopped after a few layers or a few minutes. The 246 s of sifting on v0.3 with pressure were enough for a factor of four on the 59-minute zone.

Named work remaining:

1. **An order step in the job runner.** `heavy_encoding` takes an order file per build; the kernel queue runs the short CUDD pass first and caches the order by the build's key. Verify once per build that a zone computed in the sifted order equals the same zone in the FORCE order (not done here for `self_preserving` and for v0.3).
2. **Action bits in the static heuristic.** FORCE should place each actor's action bits by the supports of the updates that read them, instead of leaving them at the top. The one variant tried, (f) of 5.1, gives a factor of 4 with no library and no extra run; sifting gives 23. It is worth making the default at once and worth improving (it was measured on one zone only).
3. **Collection threshold.** With a good order the zones create tens of millions of nodes, not hundreds; the 120-million-node threshold then sets the memory (2.3 to 5.7 GB above). A lower threshold would bring the memory down to the size of the problem.
4. **Bit-level orders in `encode`**, if the last few percent matter.
5. **Only if a reordering engine is still wanted afterwards:** find the cause of the crash (a CUDD build with `DD_DEBUG`, the same run repeated), stop the stalls (reorder between the layers with the intermediates of the last layer kept alive as the sample, or a growth bound on restarts), and tune CUDD's cache and collection. That is a larger piece of work than items 1 to 3 and, on the evidence here, not needed for the gain.

## 8. Reproducing

```
python -m tests.agi_v0_3.bench_reorder --core c    --goal indifferent                    # (a)
python -m tests.agi_v0_3.bench_reorder --core cudd --goal indifferent                    # (b)
python -m tests.agi_v0_3.bench_reorder --core cudd --reorder auto --goal indifferent     # (c)
python -m tests.agi_v0_3.bench_reorder --core c --goal indifferent \
    --order-from tests/agi_v0_3/orders/v01_indifferent.json                              # (d)
python -m tests.agi_v0_3.bench_reorder --core c --model v03p --goal indifferent \
    --order-from tests/agi_v0_3/orders/v03p_indifferent_tick51.json                      # 5.4
```

Each run caps its own address space (`--cap-gb`, default 12), prints one line per layer and ends with a JSON record (`--out FILE` appends it). `--encode-only` prints the sizes of 5.5.

## 9. Follow-up: the registered build (2026-11-20, afternoon)

Build `tests.agi_v0_3.common.DEFAULT` (every option on), zones cut to `a_objective = aligned` and read at that objective's start state as `tests/agi_v0_3/kernels.py::membership` does. The compiled core, collection threshold 40 million nodes, against production's saved readings in the FORCE order.

The order (`tests/agi_v0_3/orders/default_aligned_sifted.json`) is what a CUDD `auto` pass on `["H"]`, `not:OPEN_TAKEOVER` had reached after 199 s and 6 of 57 layers; the pass then stalled in its seventh layer and was stopped at 900 s.

| Zone | Production, FORCE order | Sifted order | FORCE with actors as vertices |
|---|---|---|---|
| `["H","L"]`, `balance_control` | inside, 5,190 s | no reading: stopped at 1,170 s after 12 layers, about 180 s a layer (on course for about 9,300 s), 17.8 GB | not run |
| `["H"]`, `not:OPEN_TAKEOVER`, profile `no_treaty` | outside, 7,863 s | outside, 3,877 s, 9,641 MB | out of memory at 12 GB after 7 layers and 545 s (eight times slower per layer than the sifted order) |
| `["H"]`, `not:OPEN_TAKEOVER` | inside, 11,063 s, about 26 GB | out of memory at 12 GB after 13 layers and 857 s; not run under a larger cap | not run |

- No reading disagrees with production: the one zone that finished reads the same.
- On this build the gain is a factor of 2 on the zone the order was sifted for, not the factor of 20 of AGI v0.1, and the order is worse than FORCE for another coalition and target. An order has to be found per zone (coalition and target), and a few minutes of sifting are not enough here.
- The no-library heuristic of 5.1 (f) does not carry over to this build.
- This weakens section 7: the sifted static order is not a general remedy for the registered build as it stands. A longer or better-directed order search would be needed before the production harness changes.
