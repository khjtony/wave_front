# Engine scaling (PLAN step 2.2, decision F1)

This is the decision record of the symbolic engine and the results of its benchmark. The decision itself is F1 of [phase2_kickoff.md](phase2_kickoff.md). This document records what was built, how it was checked, and what it measured.

## 1. Decisions

**Rust port.** The kickoff records the decision on the Rust port (PLAN 2.2) as follows:

> The Rust port decision (PLAN 2.2) is recorded as: not now. The explicit engine's limit is the size of the reachable set, not its speed, and a faster enumerator does not change that; the symbolic engine is the right investment. Revisit only if the symbolic engine fails on the benchmark.

The symbolic engine did not fail on the benchmark, so the decision stands:

- WEST's kernel for `balance_europe` is computed for every state of WW2 v0, both hypotheses at once, in about one minute.
- Counting that kernel inside the reachable set from tick 0 takes 49 minutes under hegemonic aims (6.55 billion reachable states) and 16 minutes under revisionist aims (0.85 billion).

Section 5 gives the costs and what a larger model (WW2 v1, horizon 39) would need. A compiled BDD core is the named next step if forward reachability over v1 is required. It now exists (section 7).

**Symbolic engine.** The engine is in-house and written in pure Python (`wavefront/symbolic/`). It needs no third-party dependency. It has three parts:

- `bdd.py`: a reduced ordered BDD manager.
- `encode.py`: the binary encoding of a compiled model.
- `solve.py`: the controllable predecessor, the attractor and safety fixpoints, contested regions, forward reachability, shortest distance and witness traces.

The CLI is not wired to the engine yet; wave B does that.

## 2. What was built

### 2.1 BDD manager (`wavefront/symbolic/bdd.py`)

- **Nodes.** Nodes are three parallel Python lists (`var`, `lo`, `hi`). A function is an `int` edge `(node << 1) | complement`. Negation is therefore free: `TRUE` is 0 and `FALSE` is 1. There are no per-node objects.
- **Tables.** The unique table is hash-consed and keyed by one packed int. The `and`, `xor`, `ite`, `exists` and `and_exists` operations have computed tables, which are cleared when they pass 3,000,000 entries.
- **Operations.**
  - `AND`, `OR`, `XOR`, `IFF`, `IMPLIES`, `DIFF`, `ITE`, `and_all`, `or_all`
  - `exists` and `forall` over variable sets
  - `and_exists`, the relational product, which quantifies as it recurses
  - `restrict`, the cofactor by a partial assignment
  - `simplify`, the Coudert-Madre restrict operator for a care set
  - `compose`, simultaneous substitution
  - `rename`, which is fast when the order is preserved and correct in any case
  - `transfer` to another manager
  - `pick_one`, which prefers the 0 branch so that the least action codes are chosen
  - `count`, with big-int results
  - `node_count`, `support`, `evaluate`
- **Variable order.** The order is fixed. A variable's level is its creation index, and the encoder creates the variables in the order it wants.
- **Recursion.** Operations recurse, with memoization. The interpreter's recursion limit is raised once at import to 20,000, which allows about 5,000 variables.
- **Garbage collection.** Collection is a non-moving mark and sweep with a free list. Roots are the edges passed to `gc`, protected edges (`protect`, `protecting`), and registered holders (any object with `bdd_roots()`, held weakly). The encoding and every result object register themselves. `maybe_gc` collects when the live nodes exceed both `gc_min_nodes` (default 2,000,000) and twice the count left by the previous collection. The fixpoints call `maybe_gc` between steps, and `image` calls it between relational-product steps when the caller passes `keep`. A fixpoint's arguments are protected for the duration of the call.

### 2.2 Encoding (`wavefront/symbolic/encode.py`)

- **Variables and order.**
  - Each state variable of size `n` gets `ceil(log2 n)` current bits and as many next bits, most significant bit first. Current and next bits are interleaved, and a domain constraint `value < n` applies.
  - Each actor, Nature included, gets `ceil(log2 k)` action bits, numbered as in `ActorSpec`.
  - The default order is the compiled model's state order, with all action bits on top.
  - `var_order=` and `actions="top" | "bottom" | {actor: variable}` are available for experiments.
- **Integer expressions.** These are *value partitions*: a mapping from each value to the BDD of the condition under which the expression takes it. The values are level indices, counters and sums of indicator terms, so they are small.
  - `+`, `-`, `Min`, `Max`, `Ite`, clamping and comparisons combine partitions value by value. This is the bit-level circuit written as a case split.
  - A comparison with a constant is a disjunction of value cubes.
  - Level names resolve through the compiler's own helpers (`cm._gen`), as in `wavefront/bmc`.
- **Next-state functions.** There is one function per current state bit, built in the order of `CompiledModel._successor`:
  1. Immediate effects: `Set`s win, with the first in order taken; `Bump`s are summed, then the result is clamped.
  2. The tick.
  3. Delay counters, with delayed effects composed as a second phase.
  4. `last_<actor>`.
  5. Latches, evaluated on the state built so far.
  6. Fairness counters, evaluated on the state built so far with the chosen action.

  Bits that never change are omitted, so that substitution skips them.
- **Error transitions.** Transitions on which the explicit engine raises are collected in `error`: two different `Set` values in one phase, a strict `Bump` out of range, or a monotone decrease. The fixpoints do not use `error`; `reachable(check=True)` raises `ModelError` with the explicit engine's own message wherever `explore` would.
- **Availability.** Availability is built per actor and per action from:
  - the guard, as `guard_expr`, the conjunction of a parted guard's unrelaxed parts;
  - the delay counter being 0;
  - the selected profiles' `unless` conditions;
  - the fairness restriction.

  `live` is the predicate that every actor has an available action. `active` is `dom & ~term & live`.
- **Terminal states.** `term` is any ending or `tick == horizon`. Terminal states have no moves, and in `image` they are frozen: their image is themselves. Overlapping endings are collected for the reachability check.
- **Images.**
  - `preimage(x)` substitutes the next-state functions into `x` (`compose`).
  - `image(s)` is a relational product over the partitioned relation `x' <-> f(s, a)` (one part per changing variable) together with each actor's availability. Parts are conjoined greedily: each time, the part that lets the most action and current bits be quantified, with action bits weighted 4. A bit is quantified as soon as no remaining part mentions it.
- **Explicit-state helpers.** The encoding provides `state_to_cube`, `cube_to_state`, `holds(f, state)`, `available(state)`, `successor(state, move)`, `is_error`, `predicate(target)` and `count(f)`. `predicate` takes an ending name, `HORIZON`, an invariant name or an expression, and caches its result.

### 2.3 Fixpoints (`wavefront/symbolic/solve.py`)

- **`cpre(enc, C, X)`.** It computes `exists a_C . avail_C & ~(exists a_O . avail_O & ~X(f(s, a)))` on active states. The quantification runs actor by actor and is exact, because each actor's availability depends only on its own action bits.
- **`attractor(enc, C, T)`.** This is `mu X . T | cpre(X)`. Every stage is kept in `layers`. `rank(state)` is a binary search over the stages, and `strategy_move(state)` is a sub-move all of whose completions lead to a lower stage.
- **`safe(enc, C, phi, within=None, method="auto")`.**
  - For a timed model it is computed backward one tick layer at a time: `K_H = phi & tick == H` and `K_t = phi & tick == t & (Term | cpre(K_{t+1}))`. This is the same greatest fixpoint, reached in `horizon + 1` steps, each over one layer.
  - `method="iterate"` runs the plain iteration, which is also used for untimed models.
  - `within=R` is a set closed under successors, such as a reachable set. With it, each step's argument is simplified with `R` as the care set and the kernel is computed inside `R`.
  - `strategy_move(state)` is a sub-move all of whose completions stay in the kernel.
- **`contested(enc, C, goal, kind)`** follows the explicit engine.
- **`reachable(enc, initial, check=True)`** is a forward image fixpoint. It keeps the breadth-first layers only on request.
- **`shortest(enc, state, target)`** counts breadth-first layers forward from one state. This equals the rank in the attractor of every actor, so it gives the explicit `distance(...).shortest` without building states unreachable from `state`.
- **`witness(enc, cm, state, target, C)`.** It steps the explicit model with `cm.available` and `cm.step`. The coalition plays `strategy_move`, and the other actors play the completion with the highest stage. The result is `[(state, joint_move), ..., (last, None)]`.
- **Result objects.** `contains(state)`, `count(within=None)` and `stats`, which gives seconds, nodes and peak nodes per iteration.

The fixpoints work over the whole domain, not only over reachable states. A state's membership depends only on the states reachable from it, so membership on reachable states equals the explicit engine's. One computation of a kernel answers every start state.

## 3. Correctness checks (`tests/symbolic/`)

| Test | What is compared | Size |
|---|---|---|
| `test_bdd.py` | every operation against truth tables of random functions of 6 variables; GC keeps roots and reuses nodes; 600-variable functions | 150 hypothesis examples |
| `test_symbolic_crosscheck.py`, shared generator | encoding (availability and successor of every reachable state and joint move, initial-state count), `reachable` count = `explore` size, and for every target (each ending, `HORIZON`, the invariant, a random condition) the predicate, `shortest` from the initial states, attractor membership, rank, strategy move and witness, safety kernel by both methods and within the reachable set (membership, count, strategy move), contested regions for `reach` and `keep`; one random coalition per target | 200 hypothesis examples |
| same, rich generator (delays, strict Bumps, SetIf, expression Sets, flags, latches, `remember_last`, fairness, profiles, assumes) | as above; models the explicit engine rejects must be rejected by `reachable` too | 200 hypothesis examples |
| same, seeded sweep | as above, every coalition | 100 models of each generator |
| same, GC at every step | as above with `gc_min_nodes = 0` | 40 rich models |
| `test_symbolic_toy.py` | toy model with and without the `appeaser` profile: transitions, reachable count, every ending's attractor (and `HORIZON`) for every coalition, every invariant's kernel for every coalition (membership, rank, count; strategy moves on a sample of states), witnesses replay | 13,118 states per profile |
| `test_symbolic_ww2.py` | WW2 v0, hegemonic: reachable count, WEST's `balance_europe` kernel (start-state membership, size, every explicit kernel state inside), shortest distance out of the kernel | 1939Q2 (67,795 states) in the default suite; marked `slow`: 1938Q3 (198,443, plus the whole-domain kernel), 1938Q3 with built-ins (601,353), 1938Q2 (1,423,926) |

During development, a further sweep of 1,200 random models (600 per generator, every coalition) agreed with the explicit engine everywhere; the 107 models the explicit engine rejects were rejected by `reachable` too. Additional explicit cross-checks of the benchmark's states are in section 4.

## 4. Benchmark: WW2 v0

The machine has 4 cores and 15 GB of memory, with CPython 3.13 on one core. Timings are wall seconds. "Peak nodes" is the high-water mark of the node table. The reproduction script is `tests/symbolic/bench_ww2.py`; pytest does not collect it.

The encoding has 171 BDD variables: 77 current bits, 77 next bits and 17 action bits. Encoding takes 0.2 to 0.7 s.

### 4.1 WEST's kernel for `balance_europe`, whole state space

`safe(enc, ["WEST"], balance_europe)` over every state at every tick takes **55 to 60 s** when it runs alone (115 s with other jobs on the machine). It needs **2,985,508** peak nodes, and the kernel is a BDD of 41,474 nodes.

- Time per tick layer, from 20 down to 0: 0.0, 0.1, 1.2, 3.5, 4.9, 7.0, 3.5, 7.9, 1.4, 6.8, 1.0, 1.3, 7.5, 0.7, 0.6, 7.1, 0.3, 0.3, 0.3, 0.2, 0.3 s. The layers of about 7 s are probably those in which a collection emptied the computed tables. The others reuse the previous layer's cached work.
- Each layer's kernel has 59 nodes (tick 20), 2,439 (tick 19), 6,285 (tick 18), and 8,800 to 11,100 from tick 17 down.

Restricted to a reachable set (`within=R`), the same kernel takes **0.1 s** from 1938Q3 (198,443 states). Simplifying with the reachable set as the care set makes each step nearly trivial.

### 4.2 Tick 0 (`1935Q4.json`), both hypotheses

| Start | Hypothesis | In V_WEST | Kernel ∩ reachable | Reachable states | Kernel s | Reach s | Peak nodes |
|---|---|---|---|---|---|---|---|
| tick 0 | revisionist | **yes** (shortest distance out 5, margin 4) | 732,091,503 | 851,713,642 | 55 | 933 | 4,980,185 |
| tick 0 | hegemonic | **no** | 1,324,621,966 | 6,554,388,846 | 59 | 2,911 | 13,622,074 |

In each run the kernel is the whole-domain kernel of 4.1. One computation covers both hypotheses, because `aims_GER` is a state variable; each run recomputed it. Counting the kernel inside the reachable set is one BDD conjunction and a count; it was not timed separately and is not a significant cost. A whole run is therefore about 16 minutes (revisionist) and 50 minutes (hegemonic), each within the hour of F1. The reachable BDD has 816,678 nodes (revisionist) and 2,544,348 nodes (hegemonic). These memberships agree with phase 1's T2 answers, which were obtained there only by a sufficiency check (revisionist, inside) and by a refutation (hegemonic, outside).

### 4.3 T13 sweep

The sweep asks, for each hindsight state 1936Q1 to 1939Q3, whether the state is inside WEST's kernel for `balance_europe`. Snapshot `Q` is the state at tick `index(Q) + 1`. "Plain" is the snapshot as loaded by default, with no built-ins; "built-ins" loads the snapshot's pending decisions, last actions, latch and fairness counters (`builtins=True`).

| Quarter | Tick | hegemonic, plain | hegemonic, built-ins | revisionist, plain | revisionist, built-ins |
|---|---|---|---|---|---|
| (1935Q4) | 0 | out | (no built-ins) | in | (no built-ins) |
| 1936Q1 | 1 | out | **in** | in | in |
| 1936Q2 | 2 | out | out | in | in |
| 1936Q3 | 3 | out | out | in | in |
| 1936Q4 | 4 | out | out | in | in |
| 1937Q1 | 5 | out | out | in | in |
| 1937Q2 | 6 | out | out | in | in |
| 1937Q3 | 7 | out | out | in | in |
| 1937Q4 | 8 | out | out | in | in |
| 1938Q1 | 9 | out | out | in | in |
| 1938Q2 | 10 | out | out | in | in |
| 1938Q3 | 11 | **in** | **in** | in | in |
| 1938Q4 | 12 | out | out | in | in |
| 1939Q1 | 13 | out | out | in | in |
| 1939Q2 | 14 | out | out | in | in |
| 1939Q3 | 15 | out | out | **out** | **out** |

The first quarter whose hindsight state is outside the kernel:

- **Hegemonic, plain:** none inside the window. The tick-0 state is already outside, so the departure precedes 1936Q1.
- **Hegemonic, built-ins:** 1936Q2. At 1936Q1 the state carries `last_GER = remilitarize_rhineland`, so the Rhineland branch is open to WEST.
- **Revisionist:** 1939Q3, under either reading.

1938Q3 re-enters the kernel under hegemonic aims. This is the clock effect described in reports/ww2_v0.md section 7.

These are kernel memberships only. The driving variable and the T13 verdict belong to wave B.

The whole sweep costs the one kernel computation of 4.1 plus one BDD lookup per state. The explicit engine agrees on every state it can explore:

| State | Explicit states | In (explicit / symbolic) | Kernel size (explicit / symbolic) |
|---|---|---|---|
| 1939Q3 hegemonic | 8,608 | no / no | 0 / 0 |
| 1939Q2 hegemonic | 67,795 | no / no | 2,366 / 2,366 |
| 1939Q3 revisionist | 8,608 | no / no | 0 / 0 |
| 1939Q2 revisionist | 7,869 | yes / yes | 6,579 / 6,579 |
| 1939Q1 hegemonic, built-ins | 26,419 | no / no | 394 / 394 |
| 1938Q4 hegemonic | 648,006 | no / no | 31,668 / 31,668 |
| 1938Q3 hegemonic | 198,443 | yes / yes | 175,473 / 175,473 |
| 1938Q2 hegemonic | 1,423,926 | no / no | 1,192,044 / 1,192,044 |

### 4.4 T8(b): pre- and post-Munich states, hegemonic aims

These are WEST's kernel for `balance_europe`. "Shortest" is the fewest transitions to a state outside the kernel: forward breadth-first layers, equal to the explicit `distance(...).shortest`. "Margin" is `shortest - 1` for a kernel state, as in `_margin_stages`.

| State | Tick | In V_WEST | Shortest | Margin | Reachable states | Kernel ∩ reachable | Reach s | Peak nodes |
|---|---|---|---|---|---|---|---|---|
| (1) `1938Q2.json` with built-ins | 10 | no | 0 | - | 11,398,836 | 439,074 | 217 | 15,009,570 |
| (2) `1938Q3.json` with built-ins | 11 | **yes** | **3** | **2** | 601,353 | 514,269 | 37 | 2,985,508 |
| (3a) (1) with `arms_GER = high` | 10 | no | 0 | - | 1,855,561 | 52,053 | 146 | 15,009,570 |
| (3b) (2) with `arms_GER = high` | 11 | no | 0 | - | 4,134,692 | 110,756 | 106 | 11,113,282 |
| (4a) realized moves replayed to tick 10 | 10 | no | 0 | - | 35,627,841 | 1,215,484 | 270 | 15,009,570 |
| (4b) realized moves replayed to tick 11 | 11 | no | 0 | - | 16,538,765 | 443,024 | 164 | 11,113,282 |

Notes on the table:

- Every membership answer is a lookup in the kernel of 4.1, which takes 58 to 115 s once. For the states inside the kernel, the kernel ∩ reachable column is the kernel's count over the reachable set.
- Shortest distance from (2) took 4.1 s. The snapshot agent's explicit run on (2) gives 601,353 states, inside, shortest 3, margin 2, and the symbolic engine agrees on every number.
- The peak-node column for rows run in one process is the running high-water mark of that process. These rows ran before the collection policy of 2.1 was tightened: the earlier policy collected only at twice the previous live count, so the figures over-state what the rows need.
- Reaching (4a), with 35.6 million states, took 270 s. The explicit engine cannot explore it.

### 4.5 Shortest distance and other checks

- 1938Q3 hegemonic, plain: inside, shortest 5, margin 4 (7.8 s). This agrees with reports/ww2_v0.md (inside, shortest 5, margin 4).
- Tick 0 revisionist: inside, shortest 5 (104 s, with the old image schedule).

## 5. Reachable set from tick 0: costs and limits

Forward reachability is the expensive half. The kernel restricted to a reachable set is nearly free (4.1), but building that set from tick 0 is not.

Per breadth-first step, hegemonic tick 0 (cumulative seconds; reachable-set BDD nodes; node-table high-water mark):

| Step | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| s | 0.1 | 0.6 | 3.4 | 15.9 | 59 | 122 | 191 | 265 | 319 | 444 |
| nodes | 296 | 2,021 | 10,926 | 34,171 | 110,078 | 215,729 | 330,292 | 450,875 | 544,920 | 725,955 |

| Step | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 |
|---|---|---|---|---|---|---|---|---|---|---|
| s | 576 | 741 | 932 | 1,158 | 1,421 | 1,676 | 1,931 | 2,181 | 2,549 | 2,908 |
| nodes | 901,524 | 1,090,176 | 1,327,521 | 1,583,391 | 1,855,925 | 2,109,908 | 2,342,065 | 2,544,347 | 2,544,346 | 2,544,348 |

The peak node table grew from 3.0 million (step 7) to 13.6 million (step 19).

The cost of a step grows with the size of the frontier's BDD, about 130 to 370 s per step from step 10 on. The run fits within an hour because WW2 v0 has 20 ticks.

Two engineering changes made it fit:

1. **Greedy quantification schedule.** The first version conjoined the parts in state order, after a single conjunction of the frontier with every actor's availability. It took 991 s to step 9 and was killed by the memory limit at 52 million live nodes. The greedy schedule (2.2) is about 3 times faster per step: 8.5 s against 24 s on the step-3 frontier.
2. **Collection between relational-product steps.** The first policy collected only between fixpoint steps, at twice the previous live count. Collecting between steps keeps the node table under 14 million nodes, about 4 GB of memory.

What would be needed next, for WW2 v1 (horizon 39, 55 variables, 84 actions):

- The kernel over the whole domain should remain cheap. It is one controllable-predecessor step per tick layer, 0.2 to 8 s each for v0.
- Forward reachability from tick 0 would not fit in an hour in pure Python at v0's growth rate. It would need about twice as many steps, over larger BDDs.
- Profiling shows where the time goes. On the step-3 frontier, about 3.3 million node constructions and 5.3 million `and_exists` calls take 18 s under the profiler; the per-call interpreter overhead is about 1 to 2 microseconds.
- **The next step is a compiled BDD core** (C or Rust behind the same `BDD` interface: unique table, computed tables, `and_exists`, `compose`). That is where a 30 to 100 times gain is available. The encoding and the solver need not change. The kernel and membership questions do not need it. It is built; section 7 gives its design and measures it.

Memory notes: each live node costs about 285 bytes in this representation (lists, unique table and computed tables). Typed arrays instead of lists saved only 10% and cost 10% in speed, so lists were kept.

## 6. Deviations and open points

- **Fixpoints over the whole domain.** The fixpoints are computed over every valuation of the state bits, not over the reachable set. Membership on reachable states equals the explicit engine's, because a state's membership depends only on its successors. A kernel's count is therefore meaningful only when restricted to a reachable set (`count(within=R)`). `safe(..., within=R)` computes the kernel inside `R` directly.
- **Layered `safe`.** For timed models `safe` is computed backward one tick layer at a time, not by the plain iteration from `phi`. This is the same greatest fixpoint, and both methods are cross-checked against the explicit engine on every random model. The attractor uses the plain iteration, so that its stages are the explicit ranks.
- **Error transitions.** Transitions the explicit engine rejects (conflicting `Set`s, a strict `Bump` out of range, a monotone decrease) are not excluded from the fixpoints; the next-state functions give them a value (the first `Set` in order wins). `reachable(check=True)` raises `ModelError` exactly where `explore` would, so on a model the explicit engine accepts, no reachable state has such a transition. Non-terminal states in which some actor has no available action are never in `cpre`, because it requires `live`.
- **`shortest`.** It is computed forward from one state by breadth-first layers, not as an attractor over the whole domain. An all-actor attractor toward a small target over the whole domain builds states unreachable from the start, and ran out of memory on WW2 v0.
- **Built-in snapshot states.** The T8(b) and T13 "built-ins" rows use `snapshot_state(..., builtins=True)` as provided by the snapshot work. Outside the kernel, the shortest distance is 0 by definition; the T8(b) table gives no forced distance for those states.
- **Not covered:**
  - The CLI is not wired (wave B).
  - Uniform-strategy checks and pivotal coalitions on symbolic results are not implemented.
  - `framework_spec.md` does not yet describe `wavefront.symbolic`. The spec needs a section for it; that document is outside this step's paths.

## 7. The compiled core

Section 5 named a compiled BDD core as the next step. It is built: `wavefront/symbolic/_core/` (C11, no library) behind the interface of `bdd.BDD`, wrapped by `wavefront/symbolic/bdd_c.py`. The pure-Python manager stays as the reference and the fallback. `encode.py` and `solve.py` run unchanged on either core.

### 7.1 Design

- **Edges and nodes.** The edges are those of `bdd.py`: an edge is `(node << 1) | complement`, TRUE is 0, FALSE is 1, and the high edge of a stored node is never complemented. Nodes are a struct of three `uint32_t` arrays (`var`, `lo`, `hi`) with 32-bit indices, up to 2^31 - 1 nodes, grown by doubling. A free node is chained through `lo`. During a collection the top bit of `var` marks a live node.
- **Unique table.** It is hash-consed with open addressing and linear probing. A slot holds the key (`var`, `lo`, `hi`) and the node index, 16 bytes, so that a lookup reads no node array. The table doubles past a load of 0.7 and is rebuilt by every collection.
- **Computed tables.** There is one table for each of `and`, `xor`, `ite`, `exists` and `and_exists`. Each uses open addressing in buckets of four 16-byte entries, one cache line per bucket. A table doubles past a load of 0.5 until it reaches its cap, which is the power of two at or above the node table's capacity, clamped to between 2^18 and 2^25 entries. At the cap, a new entry whose bucket is full replaces one of its entries, so the table is a lossy cache.
- **Recursions.** The recursions are those of `bdd.py`, with the same terminal cases and normalizations, so every operation returns the same function:
  - `AND`, `OR`, `XOR`, `IFF`, `IMPLIES`, `DIFF`, `ITE`;
  - `and_all` and `or_all` (balanced);
  - `exists`, `forall` and `and_exists`;
  - `restrict`, `simplify` (Coudert-Madre), `compose` and `rename` (fast path included);
  - `transfer`.

  `restrict`, `simplify`, `compose`, `rename`, `transfer` and `count` use per-call memo tables, which are freed when the call returns. The recursion runs on the C stack; its depth is a small multiple of the number of variables, so there is no interpreter recursion limit. An operation that runs out of memory, or past 2^31 - 1 nodes, unwinds to its entry point, and the wrapper raises `MemoryError`.
- **Queries.** The queries are computed in C:
  - `evaluate`, `support`, `node_count` and `top`/`low`/`high`.
  - `pick_one` takes the 0 branch whenever it is satisfiable, so the least action codes are chosen.
  - `count` is exact: fixed-width little-endian numbers of `total/32 + 1` 32-bit limbs, which the wrapper turns into a Python `int`. The benchmark's counts exceed 2^64.
- **Garbage collection.** Collection is a non-moving mark and sweep, with the same roots as in `bdd.py`. The wrapper keeps protected edges and registered holders (in a `WeakSet`). At each collection it passes the C collector every root: the edges given to `gc`, the protected edges, and each live holder's `bdd_roots()`. `maybe_gc` applies the same policy (`gc_min_nodes`, `gc_factor`, the live count after the previous collection), so both cores collect at the same points.
- **Selection.** `wavefront.symbolic.manager(kind=None)` returns a new manager:
  - With `WAVEFRONT_BDD` unset or `c`, it returns the C manager when the extension imports.
  - With `python`, or when the import fails, it returns the Python manager.
  - An explicit `manager("c")` raises instead of falling back.

  `encode(cm, ..., manager=None)` uses the factory, and every `stats` entry of a result carries `"core"`. The build embeds a hash of the C sources. If the sources change after a build, the wrapper refuses the stale module, and the default selection falls back to Python with a warning.

### 7.2 Differences from the reference

- **Computed-table clearing.** In `bdd.py` the tables are dictionaries that a collection empties, and any table past 3,000,000 entries is emptied before a top-level operation. In the C core the tables are bounded lossy caches. A collection drops only the entries that mention a reclaimed node and keeps the rest, so the work cached before a collection is reused after it. Nothing else clears them.
- **Node numbers.** These may differ between the cores: the C free list reuses the lowest freed index first. Results are the same functions, and functions are compared across managers with `transfer`. Node counts, supports, picks and counts are equal, because they depend only on the canonical form. The peak node figures below are equal to the Python run's wherever both were measured.
- **Interface.** `peak_nodes` is a read-only property (the node table's high-water mark), and `stats()` has extra keys: the other computed tables' sizes, `node_bytes` and `cache_bytes`.

### 7.3 Correctness

`tests/symbolic/` passes under both cores, the slow WW2 states included (`WAVEFRONT_BDD=python` selects the reference). `test_bdd.py` runs every truth-table test on both managers. `test_bdd_differential.py` adds the following checks:

| Test | What is compared | Size |
|---|---|---|
| random operation sequences | 19 operations (every boolean operation, quantifiers, `restrict`, `simplify`, `compose`, `rename` on both paths, `cube`, `and_all`/`or_all`) on 10 variables; after each step the C result transferred into the Python manager equals the Python result as an edge, the Python result transferred into C equals the C result, and `node_count`, `support`, `count`, `pick_one`, `top` agree | 300 hypothesis sequences of 40 steps (12,000 steps) |
| the same, collection at every step | roots passed, protected and held by a registered holder (one third each); the live node counts after each collection are equal, and every live result still agrees | 60 hypothesis sequences of 30 steps, plus 20 seeded sequences of 60 steps (3,000 collections) |
| exact counts past 64 bits | random functions over 150 levels (5 limbs) with complemented edges at every depth, plus 2 extra free levels | 40 functions, both polarities |
| transfers | C to C, C to Python and Python to C under a random variable permutation | 50 managers × 5 functions |
| fixpoints edge by edge | encoding (`dom`, `term`, `live`, `initial`, `error`, `active`), reachable set, one attractor and two safety kernels per ending and `HORIZON` (random coalition) | 40 random models |
| explicit cross-check under each core | the full `check_model` (every coalition) on both generators, once with `manager="python"`, once with `manager="c"` | 30 + 30 models per core |
| collection at every step, C | `check_model(..., gc_always=True)` | 20 rich models |
| errors and selection | the reference's exceptions; `WAVEFRONT_BDD` and explicit selection; `stats` name the core | |

The existing hypothesis cross-checks (`test_symbolic_crosscheck.py`, 400 examples) run on whichever core is selected, so they cover C by default and Python under `WAVEFRONT_BDD=python`. Mutations of the C source caught by these tests: `pick_one` preferring the 1 branch, the borrow of the big-number subtraction in `count` (only the 150-level test), a collector that keeps cache entries whose result was reclaimed, and a wrong cofactor in `simplify`.

### 7.4 Benchmark: Python and C side by side

The C figures are from `tests/symbolic/bench_ww2.py` (`kernel`, `reach`, `v1`) on the machine of section 4: 4 cores, 15 GB, CPython 3.13, one core per run. Two or three other jobs ran beside most runs, so each C row also gives the CPU seconds where wall and CPU time differ. The Python figures are those of sections 4 and 5 and of reports/ww2_v1.md section 2. Every count, node count and peak below was equal on both cores wherever both finished. This includes the peak node table, because the cores collect at the same points.

**WW2 v0 (171 BDD variables).**

| Computation | Python | C | Speed-up | Peak nodes (both) |
|---|---|---|---|---|
| encoding | 0.2 to 0.7 s | 0.05 to 0.08 s | about 5× | |
| WEST's kernel for `balance_europe`, whole domain (4.1) | 55 to 60 s | 4.1 to 7.1 s (5.2 s CPU) | about 10× | 2,985,508 |
| reachable from tick 0, revisionist (851,713,642 states; BDD 816,678 nodes) | 933 s | 93.6 s (84.7 s on a quieter machine) | 10 to 11× | 4,980,185 |
| reachable from tick 0, hegemonic (6,554,388,846 states; BDD 2,544,348 nodes) | 2,911 s | 276 s (229 s CPU; 256 s on a quieter machine) | 10.5 to 11.4× | 13,622,074 |
| shortest distance out of the kernel, tick 0 revisionist (5) | 104 s (old image schedule) | 5.1 s | | |
| T8(b) (1) `1938Q2` built-ins, reachable (11,398,836) | 217 s | 11.5 s | 19× | |
| T8(b) (2) `1938Q3` built-ins (601,353) | 37 s | 2.1 s | 18× | |
| T8(b) (3a) (1) with `arms_GER = high` (1,855,561) | 146 s | 7.3 s | 20× | |
| T8(b) (3b) (2) with `arms_GER = high` (4,134,692) | 106 s | 5.0 s | 21× | |
| T8(b) (4a) replay to tick 10 (35,627,841) | 270 s | 11.3 s | 24× | |
| T8(b) (4b) replay to tick 11 (16,538,765) | 164 s | 5.7 s | 29× | |

The kernel-membership, kernel ∩ reachable and shortest-distance columns of 4.2 to 4.4 come out identical; this section records costs, not answers. The T8(b) rows gain more than the tick-0 runs because their peak stays under the 2,000,000-node collection threshold plus the kernel's live set (2,985,508 nodes), so the C caches are never swept. The Python peaks of the T8(b) table in 4.4 were a running high-water mark under an older policy.

The T8(b) rows use the snapshot files as they were for section 4, before the clock-consistency pass (owner's decision 7) changed the 1938Q2 and 1938Q3 readings. `tests/symbolic/test_symbolic_ww2.py` now restores those readings explicitly.

**Where the time goes.** On the whole-domain kernel the C core spends all but 1% of its time in C: `compose` 3.5 s, `and_exists` 1.2 s, collections 0.7 s. That is about 60 million recursive steps (19 M `and`, 19.5 M `ite`, 18 M `mk` calls of which 13.6 M create a node) at about 80 ns each. Each step is one or two cache misses into tables far larger than the processor's caches, so the core is bound by memory latency. The 30 to 100 times estimated in section 5 assumed that the interpreter's overhead was the whole cost. The C core removes that overhead and measures 10 to 11 times on the large images and about 20 times on the medium ones. Two layouts were measured and not kept:

- An array-of-structs node table: same speed, so the struct of arrays stays.
- 16-byte unique-table slots holding the whole key: 8% faster on the v0 kernel, but they doubled the unique table's memory (4.3 GB at 149 M nodes), so the slots hold a node index and a 32-bit hash tag.

**WW2 v1 (281 BDD variables; 283 after the edits to `models/ww2/v1.py` made during this work).** The start state is the tick-22 state: `snapshot_state(cm, "1941Q2", "hegemonic", builtins=True, snapshots=SNAPSHOTS_V1, aims_JPN="hegemonic")`. The cap is 30 minutes per computation. The memory limit is that of the session's process group, 14.3 GB, shared with the other jobs on the machine.

| Computation | Python (reports/ww2_v1.md section 2) | C, model of the report (281 variables) | C, current model (283 variables) |
|---|---|---|---|
| encoding | 18 s, 6.0 M nodes | 2.3 s, 6,000,059 nodes | 3.6 s, 7,033,896 nodes |
| forward reachability from tick 22 (`check=False`) | did not finish: killed after about 19 min past iteration 15 of 17, 2.7 GB | **fits**: 279 s (238 s CPU), 4,464,563,333 states in 17 steps, BDD 1,970,838 nodes, peak 27,934,406 nodes, 3.0 GB | **fits**: 210 s (187 s CPU), 2,235,910,445 states in 17 steps, BDD 1,295,216 nodes, peak 21,858,154 nodes, 1.9 GB |
| `safe({WEST}, balance_asia)`, whole domain | abandoned at layer 36 of 39 after 72 s, 18.5 M live nodes, 5.5 GB | **fits**: 696 s (611 s CPU), peak 47,950,386 nodes, kernel BDD 231,805 nodes, 4.7 GB (16-byte unique slots) | **fits**: 782 s (655 s CPU), peak 49,955,433 nodes, kernel BDD 233,174 nodes, 3.1 GB |
| WEST's kernel for `balance_europe`, whole domain | not attempted | **does not fit**: layer 3 (tick 36) reached 149,308,338 live nodes in 120 s at 8.3 GB; killed at 13.9 GB in layer 4 (16-byte unique slots) | PLACEHOLDER_EUROPE |
| `safe({GER}, undefeated)`, whole domain | not attempted | **does not fit**: layer 4 (tick 35) reached 95,801,978 live nodes in 103 s at 5.2 GB; killed at 11.7 GB in layer 5 (16-byte slots, other jobs holding about 2.5 GB) | PLACEHOLDER_UNDEFEATED |

What fits now on v1:

- Forward reachability from the tick-22 state, in under 5 minutes. The explicit checks of `reachable(check=True)` were not timed.
- The whole-domain kernel for `balance_asia`, in about 13 minutes.

The whole-domain kernels for `balance_europe` and for GER's `undefeated` do not fit in 14 GB. Their tick layers grow by a factor of 3 to 6 per layer near the horizon, while `balance_asia`'s grow by under 2. So the obstacle is the size of those BDDs, not the speed of the core: 150 million nodes three layers in. The routes left are those of section 6: the kernel restricted to a reachable set (`safe(..., within=R)`), which now fits because the reachable set from tick 22 fits, or a better variable order.

**Memory per node.** The reference costs about 285 bytes per live node (section 5). The C core costs, per node:

- 12 bytes in the node arrays, of which only the touched part of the doubling capacity is resident;
- 11 to 23 bytes in the unique table (8-byte slots at a load of 0.35 to 0.7);
- the computed tables, which are bounded: at most 5 × 2^25 entries of 16 bytes, 1.07 GB in all at the 50 M-node peak above.

At that peak the tables allocate 2.95 GB, 59 bytes per node, and the process holds 3.14 GB, 63 bytes per node with the interpreter and the model. The tick-0 hegemonic run holds 1.37 GB at 13.6 M nodes, against about 4 GB in Python. At the same memory, the C core holds about 4.5 times as many nodes.

### 7.5 Build

```
pip install -e '.[fast]'                    # cffi; a C11 compiler (gcc or clang) is needed
python -m wavefront.symbolic._core.build    # writes wavefront/symbolic/_core/_bdd*.so
python -c "import wavefront.symbolic as s; print(s.manager().core)"   # c
WAVEFRONT_BDD=python python -m pytest tests/symbolic -q                 # the reference
```

- The build script compiles with cffi in out-of-line API mode (`-std=c11 -O3`). `--debug` builds without optimization, and `--cc` picks the compiler. The cffi declarations are the marked region of `bdd_core.h`.
- Rerun the build after any change to `bdd_core.c` or `bdd_core.h`. The wrapper refuses a stale module.
- `pip install -e .` without the extra still works: the engine then uses the Python manager, and the differential tests are skipped.
- No setuptools hook builds the core at install time. The project builds with plain setuptools and no `setup.py`, and a hook would make cffi and a compiler requirements of every install. `.gitignore` excludes the built `*.so`.
