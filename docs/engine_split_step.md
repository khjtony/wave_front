# The split step: substituting one node at a time

Question: one step of a guarantee zone (`⟨⟨C⟩⟩□φ`, `wavefront.symbolic.safe`, one controllable predecessor per tick layer) ends in a small layer but needs a huge working set on the largest model. Can the step be carried out so that the huge intermediate never forms, with the same result?

All figures were measured on 2026-11-20 and 2026-11-21 on the shared 5900X host, one process pinned to one core, under an address-space cap of 12 GB, the compiled core. Other jobs ran on the machine (load average 2 to 3).

## 1. Answer

- **What fills the memory is not the result of the substitution but its sub-results.** `cpre` substitutes the next-state functions into the layer with one `compose` call. That call keeps one sub-result per node of the layer until it returns. On the registered build the sub-results together are 20 to 37 times the size of the result (section 2). The quantifications after it are cheap.
- **The split step releases them.** `step="split"` runs the same substitution one node of the layer at a time, from the bottom level up, and drops each sub-result after the last node that uses it. The manager can then collect inside the step. The result is the same edge (section 3).
- **It cuts the memory of a heavy step by a factor of 3 to 4 at the same speed.** On the zone of the task, the node table at tick 49 is 242 million nodes and 10.0 GB where the present step needs 990 million and 34.8 GB. With collections made more often (factor 1.25) it is 158 million and 5.9 GB, and the run passes tick 47 inside 12 GB, the layer on which the present step reached 67.9 GB and the limit of the node table. It then runs out of 12 GB in layer 46 (section 6.1).
- **It does not make anything faster, and it does not help a small model.** The same sub-results are created. On AGI v0.1 it changes nothing in memory and costs 4 to 12% in time (section 6.3).
- **Two whole zones of the registered build read the same.** `aligned` with `no_treaty` reads outside in 3.6 GB (present step: 9.6 GB). `aligned` without a profile reads inside in 3.8 GB under the 12 GB cap, where the present step ran out of memory and needed 18.2 GB under a larger cap (section 6.2).
- **`step="moves"` trades time for memory once more.** It does the split step once per joint move of the coalition: about a third of the memory for about twice the time on one measured step (section 6.4).
- **Quantifying action bits early does not help here; it hurts.** Section 4 lists what was tried and dropped, with the numbers.
- **Every reading and count matched** (section 5).

Recommendation (section 8): keep it optional. `compose` stays the library default; the kernel jobs of the registered build should run with `split`.

## 2. Where the memory goes

Zone: build `DEFAULT`, `a_objective = indifferent`, coalition `["H"]`, target `not:OPEN_TAKEOVER`, order `tests/agi_v0_3/orders/default_aligned_sifted.json`, collection threshold 40 million nodes. The present step, operation by operation (nodes of each result, and nodes the operation added to the table):

| Layer computed | Layer before, nodes | `compose` result | `compose` added | The six `and_exists` together added | Layer, nodes |
|---|---|---|---|---|---|
| 53 | 2,711 | 77,597 | 1,537,206 | 1,034,496 | 39,432 |
| 52 | 39,432 | 1,104,911 | 31,125,103 | 10,398,210 | 176,510 |
| 51 | 176,510 | 4,422,556 | 132,155,991 | 38,020,931 | 430,751 |

- The `compose` result is 25 to 29 times the layer it is made from. It is not small, but it is not what fills the table: the call adds 20 to 30 times its own result on these layers, and 37 times at layer 50 (481 million nodes for a result of 12.9 million).
- `compose` computes, for every node `n` of the layer with variable `v`, the sub-result `r(n) = ITE(f_v, r(high), r(low))`, bottom up, and keeps all of them in a memo until the call returns. A next-state function reads the action bits of several actors and state bits from the whole order (`fair_pressure` reads 28 state bits and the action bits of five actors). So the sub-result of a node in the middle of the order is a graph over all the variables above it that the functions below it read, and two such sub-results share little.
- Per level, the cost sits in the middle of the order. At the step that computes layer 52, the nodes of the levels of `oversight`, `a_autonomy`, `dependence`, `opinion`, `regime` and `coord` cost 800 to 5,000 new nodes each; those levels hold 350 to 2,700 nodes each. The levels of the fairness counters themselves cost 36 to 560 per node.
- No collection can run inside one manager call, and the present step collects only between layers. So the whole sum of the sub-results is in the table at once. That sum is the "live nodes during the step" of the baseline table.

## 3. The technique, and why it is exact

### 3.1 `split`

`compose_by_levels(mgr, f, mapping, keep)` in `wavefront/symbolic/substitute.py`:

1. Walk `f` once and record, for every node at or above the lowest substituted level, its level, its two children, and how many parents it has.
2. Take the levels from the bottom up. For each node compute `r(n) = ITE(mapping[v], r(high), r(low))` with one `ITE` call. A child below every substituted level is its own sub-result. A variable without an entry in the mapping stands for itself.
3. When the last parent of a node is done, forget its sub-result.
4. Every 256 nodes, let the manager collect (`maybe_gc`, the manager's own policy) with the sub-results still in use, `f`, the mapping and the caller's edges as roots.

`safe`, `attractor` and `contested` pass their own live edges as `keep`, and also collect after each quantification. A direct call of `cpre` passes none and never collects.

Why the result is the same edge:

- `compose` is defined by the same recursion, `r(n) = ITE(mapping[v], r(high), r(low))` with `r` of a node below the last substituted level being the node itself. The compiled core and the reference both implement it that way (`compose_rec` in `bdd_core.c`, `BDD.compose` in `bdd.py`).
- The split step evaluates that recursion in another order (by level instead of depth first) and with the same `ITE`. By induction over the levels from the bottom, every `r(n)` is the same function in both.
- A manager has one edge per function (reduced, ordered, complement edges in canonical form). So the two return the same edge, not only the same set.
- Dropping a sub-result and collecting do not change any function. An edge in use is always a root of the collection: the tests collect after every single node to check this.
- Nothing after the substitution changes. The opponents are quantified first and existentially on the complement, then the coalition, actor by actor, with the same availability predicates and in the same order as before. The alternation between coalition, opponents and Nature is untouched.

What is alive at one time is the sub-results of the nodes below the level in work that still have a parent at or above it. That is at most the width of the layer at that level, not the whole layer. On layer 50 of the zone (854,935 nodes) the widest cut holds 72,871 nodes.

### 3.2 `moves`

`step="moves"` computes

```
cpre(X) = active ∧ ⋁_c  avail_C[c] ∧ ¬ ∃ a_O . avail_O ∧ ¬X(f(s, c, a_O))
```

over the joint moves `c` of the coalition, each case with the split substitution and the next-state functions restricted to `a_C = c`. It is used when the coalition has between 2 and 64 joint moves; otherwise the step is `split`.

Why it is the same function:

- `∃ a_C . g(s, a_C)` is the disjunction of `g` over all codes of the coalition's action bits (Shannon expansion).
- A code that is not an action is never available: `avail` of an actor is `⋁_j chosen(j) ∧ guard_j` over its actions only. So the disjunction runs over the moves, and `avail_C` restricted to a move is the conjunction of the members' `action_avail` entries.
- `avail_O` does not read the coalition's bits, so restricting `∃ a_O . avail_O ∧ ¬P` to `a_C = c` restricts only `P`.
- `P = X(f(s, a))` restricted to `a_C = c` is `X` with the restricted functions substituted: action bits are not substituted, so restriction and substitution commute.
- The cases are joined with `OR`; the result is one function, hence one edge.

Each case's functions no longer read the coalition's action bits, so each sub-result is a smaller graph. The cases repeat work that the single substitution shares, so the step takes longer.

### 3.3 Selecting it

- `cpre`, `attractor`, `safe`, `contested`: `step="compose" | "split" | "moves"`.
- `WAVEFRONT_STEP=compose|split|moves` when no argument is given. Unset means `compose`.
- `Encoding.preimage(x, split=True, keep=...)` for the substitution alone.
- The benchmark harness: `--step`, and `--gc-factor` for the collection policy.
- The CUDD binding keeps to `compose` whatever is asked: its levels move under reordering and a collection gives up its handles.

## 4. What was tried and dropped

Each was checked equal to the present step before it was measured. Times are for the step that computes the named layer.

| Scheme | Measured | Verdict |
|---|---|---|
| Substitute one state variable at a time (next-state bits as placeholders) and quantify each opponent's action bits as soon as no remaining function reads them | The intermediate after partial substitution relates current and next bits and is larger than the final result: 18 million nodes at layer 52 where the full result has 1.1 million. Layer 52 took 215 s in the best order of three (present step: 19 s); two orders ran out of 12 GB | dropped: early quantification makes the intermediate bigger here, because a half-substituted layer is a relation, not a set |
| Cofactor the step on the actions of `H` (11 cases), plain `compose` per case | The cases together add 2.5 times the nodes of the one `compose` (328 million against 132 million at layer 51) | kept only together with the split substitution, as `moves` |
| Simplify the next-state functions with the layer's states as care set | 47 million nodes added against 31 million at layer 52 | dropped |
| Shannon expansion of the layer on chosen state variables before substituting (`fair_pressure`, `cap`, `opinion`) | At layer 52 the best single variable saves 41% of the nodes added. At layer 50 it saves nothing in time (145 s against 147 s) and 17% of the live nodes; two and three variables are slower (210 s, 356 s) | dropped: not stable from layer to layer |
| Simplify every sub-result with the available moves on the layer's states as care set | The care set has 180,330 nodes; the step was stopped after 4 times the plain step's time without finishing | dropped |
| Action bits at the bottom of the order | The conjunction of the availability predicates alone does not fit in 12 GB | dropped |
| Cut the layer at an upper level into sub-graphs and substitute them one after the other | Computed on the node list of layer 50: 7 sub-graphs repeat 2.9 times the nodes for a widest cut 1.8 times smaller; 149 sub-graphs repeat 7.9 times for 3.5 | dropped: the sub-graphs share most of their nodes |

The quantifications were never the problem: the six `and_exists` of a step together add about a third of what the substitution adds (section 2).

## 5. Correctness evidence

Checked by running:

- `tests/symbolic/test_split_step.py`, on the reference manager and on the compiled core:
  - `compose_by_levels` returns the edge of `compose` on random functions of 12 variables with random substitutions (150 hypothesis examples per core), and again with a collection after every single node (100 examples per core): the result, the target, the substituted functions and an unrelated edge passed as `keep` all survive.
  - `cpre` with `step="split"` and with `step="moves"` returns the edge of `step="compose"` on 80 random models (40 of each generator; the rich one selects profiles), for every coalition from the empty one to all actors, on three random targets, every ending, `HORIZON`, the domain, TRUE and FALSE per model: more than 2,000 comparisons per core.
  - The fixpoints edge by edge on 50 models per core and per split step: reachable set, attractor with every stage, kernels by both methods and within the reachable set, contested regions. The split run collects after every node of every substitution and after every quantification.
  - The explicit cross-check (`check_model`, every coalition, strategies and witnesses) on 15 + 15 models with each split step selected through `WAVEFRONT_STEP` and a collection at every opportunity.
  - The selection rule: default, environment, argument over environment, unknown value, and the fallback of `moves` to `split`.
- Mutants of the new code, each rejected by that file: the two branches of the `ITE` swapped; a sub-result released one parent early; the sub-results left out of the collection's roots; the caller's layer and kernel left out; the quantified result left out. (A sixth mutant, the target left out of the step's roots, changes nothing: `compose_by_levels` keeps its own target.) One real error was caught this way during the work: a variable's own function made once per level and freed by a collection.
- `tests/agi_v0_3/test_split_step.py`, AGI v0.1 (`V01`), the compiled core, the order `orders/v01_indifferent.json`:
  - `cpre` with each split step equals the present `cpre` as an edge for the coalitions `["H"]`, `["H","L"]` and `["A"]`, on 12 random targets, the six endings, `balance_control`, and the first six tick layers of the kernels of `balance_control ∧ a_objective = GOAL` for `aligned` and `indifferent` and each of the three coalitions: 165 comparisons, once without a profile and once with `no_treaty` selected.
  - Marked `slow`: the two whole kernels `⟨⟨H⟩⟩□(balance_control ∧ a_objective = GOAL)` under `split` and under `moves` have 302461218730668589056 states (`aligned`) and 196126762366467883008 states (`indifferent`), and none of the four initial states is inside.
- `tests/symbolic` as a whole passes with `WAVEFRONT_STEP` unset, `split` and `moves` (50 passed, 18 skipped, each time). The 18 tests of the CUDD binding are skipped: it is not built in this environment.
- On the registered build every layer that both steps computed has the same number of nodes (section 6.1), and the two zones of section 6.2 read the same at the start state as under the present step.
- `ruff check .` and `ruff format --check .` pass.

Reasoned, not run:

- The argument of section 3 that the edges are equal for every input. The tests sample it; they do not prove it.
- The CUDD binding with a split step asked for: it takes the `compose` path by a test of the manager's `core` attribute. That path is the present one, but the binding could not be built here, so the fallback itself was not executed.

## 6. Measurements

Every run: one process on one core, address-space cap 12 GB, the compiled core, `tests/agi_v0_3/bench_reorder.py`. *Node table* is the high-water mark of the manager's node table, garbage not yet collected included; *memory* is the peak resident memory of the process; *time* is the wall clock from the start of the fixpoint to the end of the layer.

### 6.1 The zone of the task

Build `DEFAULT`, `a_objective = indifferent`, coalition `["H"]`, target `not:OPEN_TAKEOVER`, no profile, order `default_aligned_sifted.json`, collection threshold 40 million nodes.

- *Present step*: the figures handed over with the task (live nodes during the step, resident memory), measured before this work with the same order and threshold. They were not rerun here: from tick 50 on they need more than 12 GB.
- *Split, factor 2*: the same collection policy as the present step (collect again when the table is twice what the last collection left).
- *Split, factor 1.25*: `--gc-factor 1.25`, collecting more often.

| Layer (tick) | Finished layer, nodes | Present step: live nodes, memory | Split, factor 2: node table, memory, time | Split, factor 1.25: node table, memory, time |
|---|---|---|---|---|
| 52 | 176,510 | 45 M, 2.3 GB | 43 M, 2.3 GB, 19 s | 43 M, 2.3 GB, 19 s |
| 51 | 430,751 | 171 M, 5.4 GB | 43 M, 2.5 GB, 77 s | 43 M, 2.5 GB, 79 s |
| 50 | 854,935 | 481 M, 17.9 GB | 121 M, 5.5 GB, 274 s | 76 M, 3.7 GB, 319 s |
| 49 | 1,169,998 | 990 M, 34.8 GB | 242 M, 10.0 GB, 707 s | 158 M, 5.9 GB, 832 s |
| 48 | 1,273,826 | not given | out of memory at 12 GB, 1,101 s | 261 M, 10.1 GB, 1,735 s |
| 47 | 1,350,373 | 1,666 M, 67.9 GB, then the 2^31-node limit | | 261 M, 10.1 GB, 2,635 s |
| 46 | | | | out of memory at 12 GB, 3,331 s |

- The finished layers have the same node counts as the present step's (0.18, 0.43, 0.85, 1.17 and 1.35 million in the task's table).
- With the same collection policy the node table is 4.0 to 4.1 times smaller at ticks 50 and 49, and the resident memory 3.2 to 3.5 times.
- With factor 1.25 the split step passes tick 47 inside 12 GB, at 10.1 GB. That is the layer on which the present step reached 67.9 GB and the limit of the node table. The price of the tighter policy is 16 to 18% of the time at ticks 50 and 49.
- At ticks 52 and 51 the memory is the collection threshold's doing (the first collection comes at 40 million nodes), not the step's.
- Under 12 GB the table can hold 376 million nodes (28.6 bytes a node with the unique table, plus 1.6 GB of computed tables). Layer 46 needs more than that at once even when released: the widest cut of the layer times the size of a sub-result.
- Time. The present step finished layer 52 after 19.2 s and layer 51 after 89.2 s in the profiling run of section 2 (which also sizes every result); the split step after 19.3 s and 76.9 s. The two steps create the same sub-results, so no speed-up is expected or claimed. From tick 50 on the present step could not be timed under the cap.

### 6.2 Two whole zones of the registered build

Build `DEFAULT`, `a_objective = aligned`, coalition `["H"]`, target `not:OPEN_TAKEOVER`, the same order and threshold. The present step's rows are the records of docs/engine_reordering_spike.md section 9 and were not rerun.

| Profile | Step | Time | Memory | Node table | Reading at the start state |
|---|---|---|---|---|---|
| `no_treaty` | present (`compose`), 12 GB cap | 3,877 s | 9,641 MB | not recorded | outside |
| `no_treaty` | `split`, factor 2, 12 GB cap | 3,616 s | 3,567 MB | 73,098,161 | outside |
| none | present (`compose`), 12 GB cap | out of memory after 13 layers and 857 s | | | no reading |
| none | present (`compose`), 30 GB cap | 6,243 s | 18.2 GB | not recorded | inside |
| none | `split`, factor 1.5, 12 GB cap | 6,134 s | 3,819 MB | 81,233,838 | inside |

- Both readings are the present step's, and production's in the FORCE order (outside; inside, there with about 26 GB).
- The zone without a profile did not fit in 12 GB with the present step. With the split step it finishes there in 3.8 GB.
- Memory: 2.7 times less with `no_treaty`, 4.8 times less without a profile (there with the collection factor at 1.5 instead of 2).
- The times are from different runs on a shared machine. They say "no slower", not "faster".
- Under `split` the kernel with `no_treaty` has 10745571244955131088879616 states and 657,535 nodes, and none of the four initial states is inside. The kernel without a profile has 10790031558679106831843328 states and 1,268,572 nodes, and of the four initial states only the `aligned` one is inside. No count of the present step's kernels was recorded to compare with; the readings are what was compared.
- These zones are small beside the zone of 6.1: their largest layers have 173,605 and 272,690 nodes.

### 6.3 AGI v0.1, both whole kernels, every step, same day

`⟨⟨H⟩⟩□(balance_control ∧ a_objective = GOAL)` on `V01`. Every run has the recorded number of states and none of the four initial states inside.

| Goal, order, threshold | Step | Time | Memory | Node table | States in the kernel |
|---|---|---|---|---|---|
| `aligned`, `v01_indifferent.json`, 40 M | compose | 0.9 s | 312 MB | 2,401,561 | 302461218730668589056 |
| | split | 1.0 s | 303 MB | 2,401,561 | 302461218730668589056 |
| | moves | 2.9 s | 309 MB | 2,395,220 | 302461218730668589056 |
| `indifferent`, `v01_indifferent.json`, 40 M | compose | 15.2 s | 2,316 MB | 37,329,479 | 196126762366467883008 |
| | split | 15.8 s | 2,322 MB | 37,329,479 | 196126762366467883008 |
| | moves | 22.9 s | 2,308 MB | 37,539,332 | 196126762366467883008 |
| `indifferent`, `v01_indifferent.json`, 2 M | compose | 16.1 s | 302 MB | 2,782,695 | 196126762366467883008 |
| | split | 18.0 s | 303 MB | 2,888,234 | 196126762366467883008 |
| | moves | 31.8 s | 305 MB | 2,226,733 | 196126762366467883008 |
| `indifferent`, FORCE order, 40 M | compose | 727 s | 3,157 MB | 67,248,236 | 196126762366467883008 |
| | split | 780 s | 3,152 MB | 55,574,885 | 196126762366467883008 |

- On this model the split step does not help. A step's sub-results are a few million nodes, below any collection threshold worth setting, so the memory is the threshold's. `split` is 4 to 12% slower on the runs longer than a second (one Python call per node, and more collections), `moves` 1.5 to 3.4 times slower.
- The sifted-order rows create 37 million nodes in the whole kernel and never collect at the 40-million threshold.

### 6.4 `moves`

One step in isolation (the step that computes layer 50 of the zone of 6.1 from layer 51, 430,751 nodes; collection threshold 4 million; the plain result of 12.9 million nodes kept alive beside it for the comparison):

| | Substitution time | Most live nodes after a collection |
|---|---|---|
| `split` | 147 s | 56.4 M |
| the 11 moves of `H`, one after the other | 316 s | 26.6 M |

Without the 12.9 million nodes held for the comparison the working sets are about 43.5 and 13.7 million: 3.2 times less memory for 2.2 times the time.

The zone of 6.1 with `--step moves --gc-factor 1.25`, stopped after tick 50 (the layers have the same node counts):

| Layer (tick) | `split`, factor 1.25: node table, memory, time | `moves`, factor 1.25: node table, memory, time |
|---|---|---|
| 52 | 43 M, 2.3 GB, 19 s | 40 M, 2.2 GB, 22 s |
| 51 | 43 M, 2.5 GB, 79 s | 41 M, 2.2 GB, 130 s |
| 50 | 76 M, 3.7 GB, 319 s | 47 M, 2.6 GB, 463 s |

Up to tick 51 the collection threshold of 40 million nodes sets both. At tick 50 `moves` holds a table 1.6 times smaller for 1.45 times the time of the whole run. It was not run further, so whether it passes layer 46 inside 12 GB is not known.

## 7. Not done

- **The zone of 6.1 is not finished.** Under 12 GB the split step stops in layer 46 of 57. How far it goes under a larger cap is not known; section 9 has the commands.
- **No speed-up.** The split step creates the same sub-results as `compose`. The cost of the substitution itself (20 to 37 times its result) is untouched. Not tried: a substitution from the top of the layer down that carries the reaching condition of each node, so that a sub-result is built only for the contexts in which its node is reached; a transition relation clustered per actor (only the finest partition, one variable at a time, was tried, section 4).
- **The present step was not rerun on the registered build past tick 51** (it needs 18 GB and more). The comparison of 6.1 uses the figures handed over with the task, and 6.2 the records of the reordering spike. For the two zones of 6.2 the readings agree; the numbers of states under the present step were never recorded, so they were not compared.
- **`moves` was run on the zone of 6.1 only to tick 50.**
- **The collection policy is set by hand.** The factor 1.25 of 6.1 is an argument of the harness. The step does not know the memory cap; a policy that tightens as the table nears the cap would get the same without a setting.
- **`compose_by_levels` is Python driving one `ITE` per node.** That costs 4 to 12% on a small model. A version inside the compiled core, with the same release rule, would remove it; it would also need the reference manager's counterpart and the differential tests.
- **`moves` splits on the coalition only**, and only up to 64 joint moves. Cofactoring on an opponent's actions as well is exact by the same argument (`∃ a_O` is a disjunction over the opponent's moves) and was measured only without the release (section 4).
- **Attractors and the plain iteration** are covered by the tests, not by a benchmark.
- **The CUDD binding** was not built here; with it the step stays `compose` (section 3.3).
- **The whole test suite** was not run; `tests/symbolic` (under each step), `tests/agi_v0_3`, `tests/toy`, `tests/engine` and `tests/model` were.

## 8. Recommendation

**Keep it optional, and switch it on for the heavy zones now.**

- Library default: `compose` stays. On models whose steps are small (AGI v0.1, the WW2 states of the test suite) `split` gains nothing and costs 4 to 12%.
- Kernel jobs of the registered AGI v0.3 build (`tests/agi_v0_3/kernels.py` and the kernel queue): run with `WAVEFRONT_STEP=split`. It is exact, the tests compare it edge by edge, two zones computed with it read as production's (6.2), it costs no time on those zones and it divides their memory by 3 to 4. With the collection factor at 1.25 the division is nearer 6 at a price of about 17% in time.
- `moves`: a last resort when a zone still does not fit. It is exact and tested the same way, and it costs about twice the time.
- Make `split` the default of the library only if a version inside the compiled core removes its overhead on small models.
- The order still matters more than the step: the sifted order made the zone 2 to 20 times cheaper (docs/engine_reordering_spike.md), the split step 3 to 4 times smaller in memory only. They combine: every figure here is in the sifted order.

## 9. Reproducing

Set-up: `uv venv .venv-spike --python 3.13 && uv pip install --python .venv-spike/bin/python -e '.[fast,bmc,dev]' && .venv-spike/bin/python -m wavefront.symbolic._core.build`.

```
# 6.1, split, the present collection policy, then factor 1.25
python -m tests.agi_v0_3.bench_reorder --core c --model default --goal indifferent \
    --coalition H --target not:OPEN_TAKEOVER \
    --order-from tests/agi_v0_3/orders/default_aligned_sifted.json \
    --gc-min-nodes 40000000 --step split --cap-gb 12
python -m tests.agi_v0_3.bench_reorder ... --gc-min-nodes 40000000 --gc-factor 1.25 --step split --cap-gb 12

# 6.2 (the second zone: without --profiles, with --gc-factor 1.5)
python -m tests.agi_v0_3.bench_reorder --core c --model default --goal aligned \
    --coalition H --target not:OPEN_TAKEOVER --profiles no_treaty \
    --order-from tests/agi_v0_3/orders/default_aligned_sifted.json \
    --gc-min-nodes 40000000 --step split --cap-gb 12

# 6.3
python -m tests.agi_v0_3.bench_reorder --core c --model v01 --goal indifferent \
    --order-from tests/agi_v0_3/orders/v01_indifferent.json --gc-min-nodes 40000000 --step split

# the tests
python -m pytest tests/symbolic/test_split_step.py tests/agi_v0_3/test_split_step.py -q
WAVEFRONT_STEP=split python -m pytest tests/symbolic -q
```

Runs that need more than 12 GB (not run here; `--stop-tick N` ends a run after layer `N`, `--no-probe` leaves out the sizing of every `and_exists` result):

```
# the zone of 6.1 to the end with the split step (how much it needs is not known)
python -m tests.agi_v0_3.bench_reorder --core c --model default --goal indifferent \
    --coalition H --target not:OPEN_TAKEOVER \
    --order-from tests/agi_v0_3/orders/default_aligned_sifted.json \
    --gc-min-nodes 40000000 --gc-factor 1.25 --step split --cap-gb 30 --out zone_split.jsonl

# the same with one move of H at a time (about twice the time, about a third of the memory)
python -m tests.agi_v0_3.bench_reorder ... --gc-factor 1.25 --step moves --cap-gb 30 --out zone_moves.jsonl

# the present step on the same day, layers 52 to 47, for the time column of 6.1 (68 GB at tick 47)
python -m tests.agi_v0_3.bench_reorder ... --gc-min-nodes 40000000 --step compose --cap-gb 72 --stop-tick 47
```
