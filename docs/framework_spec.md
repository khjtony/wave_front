# Framework specification (phase 0)

This is the contract for the `wavefront` Python package: the modeling DSL, the compiled model, the explicit-state engine, the bounded model checker, the analysis layer, the report, and the CLI. Implementation agents build against this document; reviewers check against it. Where the earlier sketch in DESIGN.md section 6.3 used Python lambdas for guards, this specification replaces them with declarative expression objects so that the same model can be interpreted by the explicit engine and compiled to Z3.

Python 3.11 or later. Package name `wavefront`, distribution name `wave-front`. Core has no third-party runtime dependency. `z3-solver` is an optional dependency used only by `wavefront.bmc`. Dev dependencies: `pytest`, `hypothesis`, `ruff`.

---

## 1. Semantics

A model defines a finite concurrent game.

- **State.** A valuation of all variables, represented at runtime as a tuple of small non-negative integers, one per variable in declaration order (built-in variables included). Level names map to indices in declaration order; comparisons between levels compare indices.
- **Actors.** Named players. One built-in actor `Nature` always exists; its actions are called events, and it always has the event `none`. Each actor always has at least one available action in every non-terminal reachable state; the engine raises `ModelError` naming the state and actor if not. Every actor gets an implicit `idle` action with no guard and no effect unless declared with `idle=False`. An actor declared with `cadence=k` decides at most once every k ticks (section 3.1).
- **Joint move.** One action per actor including Nature, chosen simultaneously. The transition is deterministic given the joint move. Nature's nondeterminism is therefore the choice of its event.
- **Transition.** Apply the chosen actions' effects, then the system updates (tick increment, delay counters, cadence counters, last-action variables, latches, fairness counters). Effect composition rules are in section 3.4.
- **Tick.** A built-in counter variable `tick` from 0 to `horizon`. States with `tick == horizon` are terminal. With `horizon=None` the model is *untimed*: there is no `tick`, no horizon terminal, the reachable graph may contain cycles, and kernels mean "keep φ forever". With a horizon, kernels mean "keep φ until the horizon".
- **Endings.** Named predicates. A state satisfying an ending is terminal: it has no moves. Endings must be mutually exclusive on reachable states; the engine raises `ModelError` otherwise. `tick == horizon` is also terminal; such a state may satisfy no ending, in which case it is reported as `HORIZON`.
- **Initial states.** The product of the declared initial values; a variable declared with `init=None` contributes every level (this is how hidden objectives and parameters are swept).
- **Observation.** Each actor declares the set of variables it observes. An actor's action guards, its fairness triggers and its profile `unless` conditions may only reference variables that actor observes; the compiler raises `ModelError` otherwise. This keeps *availability* observation-consistent. The phase 0 solvers nevertheless compute perfect-information strategies (one move per state), so for a coalition with hidden variables a forcing or keeping result is an upper bound on what the coalition can actually do; the analysis layer checks whether a computed strategy happens to be uniform (section 7) and the report says so. Uniform memoryless strategy synthesis is later-phase work. Nature observes everything. Properties may reference anything.
- **Coalition semantics.** For a coalition C of actors (Nature may be included), the controllable predecessor is
  `CPre_C(X) = { s | ∃ joint C-move available in s such that ∀ completions by the other actors available in s, step(s, move) ∈ X }`.
  `⟨⟨C⟩⟩◇T` is the least fixpoint `μX. T ∪ CPre_C(X)` (the attractor); `⟨⟨C⟩⟩□φ` is the greatest fixpoint `νX. φ ∩ (Term ∪ CPre_C(X))`. Terminal states have no moves: a terminal state is in a safety fixpoint iff it satisfies φ, and in an attractor iff it is in T. The rank of a state in an attractor is its stage index in `X₀ = T, X_{i+1} = T ∪ CPre_C(X_i)`: the least number of ticks within which C can force the target.
  Plain reachability `EF T` is the attractor for the coalition of all actors including Nature. Concurrent games are not determined, so "C can force T" and "the rest can keep ¬T" are computed separately; a state in neither is *contested*.

## 2. Package layout

```
wavefront/
  __init__.py
  model/
    __init__.py        re-exports Model, V, Set, Bump, Inc, Reset, Ite, ModelError
    expr.py            expression trees (section 3.2)
    effects.py         effect objects (section 3.3)
    model.py           Model, Actor, declarations (section 3.1)
    compile.py         CompiledModel (section 4)
  engine/
    __init__.py        re-exports explore, attractor, safe, witness, Graph
    graph.py           Graph (section 5.1)
    explore.py         explore (section 5.2)
    solve.py           attractor, safe, contested (section 5.3)
    trace.py           Trace, witness (section 5.4)
  bmc/                 Z3 encoding, relaxations (section 6)
  analysis/            viability, pivotal, relax, sensitivity, cluster, budget (section 7)
  report/              markdown report (section 8)
  evidence/            snapshot schema and loader (section 9); corpora/ (dated documents for
                       the replay harness, docs/replay_harness.md; crest.py in section 9)
  cli.py               `wf` entry point (section 10)
```

## 3. The DSL (`wavefront.model`)

### 3.1 Declarations

```python
from wavefront.model import Model, V, Set, Bump, Inc, Reset, Ite

m = Model("two_power", horizon=24, description="...")

m.var("cap", levels=["low", "mid", "high"], init="low", monotone=True)
m.var("aims", levels=["limited", "hegemonic"], init=None, hidden_from=["INC"])
m.counter("stock", max=5, init=2)          # integer 0..max
m.flag("rights", init=False)               # boolean, levels False/True

INC = m.actor("INC", observes=V.all_except("aims"), remember_last=True)
CH  = m.actor("CH",  observes=V.all(), cadence=1)   # cadence=k: decides once every k ticks
N   = m.nature()                            # the built-in Nature actor

INC.action("concede",
    guard=(V.belief <= "uncertain") & (V.cap < "high"),
    effect=[Bump("control", +1), Set("belief", "limited")],
    delay=0, source="citation or rationale", speculative=False)
INC.action("fund_oversight", effect=[Bump("oversight", +1)], delay=2)
N.event("detect", guard=(V.oversight == "strong") & (V.deceiving == True),
        effect=[Set("belief", "hegemonic")])

m.latch("belief_at_majority", of="belief", when=(V.control >= "majority"))
m.fairness("respond", actor="INC",
           trigger=(V.belief == "hegemonic") & (V.control >= "partial"),
           within=4, responses=["sanction", "shutdown", "fund_oversight"])
m.profile("crisis_reactive", actor="INC", forbid=["sanction", "shutdown"],
          unless=(V.belief >= "uncertain"))

m.invariant("balance", (V.oversight >= "weak") & (V.control <= "partial"))
m.ending("TAKEOVER", V.control == "total")
m.ending("COEXIST", (V.tick == m.horizon) & V.invariant("balance"))
```

Rules:

- Names are identifiers; a name may be used once across variables, actors, actions of one actor, latches, fairness constraints, profiles, invariants and endings. Built-in names (`tick`, `last_<actor>`, `pending_<actor>_<action>`, `fair_<name>`, `cadence_<actor>`) are reserved: no declared name may start with `last_`, `pending_`, `fair_` or `cadence_`.
- `levels` must have at least two entries. `init` must be a level or `None`. `monotone=True` makes the compiler verify statically that no effect decreases the variable (a `Bump` with a negative amount or a `Set` to a lower level than any reachable value is a `ModelError` at compile time for `Set` only when the target is the lowest level; otherwise the engine checks at explore time and raises).
- `hidden_from` is a list of actor names. `observes` is `V.all()`, `V.all_except(*names)`, or `V.only(*names)`. A variable in `hidden_from` of actor X is removed from X's observation set whatever `observes` says.
- `delay=d` with d ≥ 1 defers the whole effect list. The compiler adds the counter `pending_<actor>_<action>` in `0..d`. Choosing the action in the transition from tick t to t+1 sets the counter to d in that transition's system update; each later transition decrements it, and when it goes from 1 to 0 the effect is applied in that same transition. The effect is therefore visible in the state at tick t+1+d, and the action is unavailable at ticks t+1 .. t+d. Example, d=1: chosen at t, unavailable at t+1, effect visible at t+2.
- `remember_last=True` adds the variable `last_<actor>` with levels `["none"] + action names`, updated to the chosen action each tick.
- `cadence=k` on `m.actor(...)`, an int k ≥ 1 (default 1), is the actor's decision period. With k = 1 nothing is added and the actor decides every tick. With k ≥ 2 the compiler adds the counter `cadence_<actor>` in `0..k-1`, initial 0. The actor's declared actions are available only when the counter is 0; its built-in `idle` is always available. Choosing a declared action in the transition from tick t to t+1 sets the counter to k-1 in that transition's system update; choosing `idle` decrements it towards 0 (`max(counter - 1, 0)`). An actor with cadence k therefore decides at most once every k ticks, with idle ticks between: chosen at t, only `idle` at t+1 .. t+k-1, declared actions available again at t+k. Example, k=3: a decision at tick 0, then the next one at tick 3 at the earliest. The period is a refractory period, not a fixed schedule: an actor that idles keeps its counter at 0 and may decide at any later tick. **Fairness overrides the cadence:** when one of the actor's fairness restrictions binds (its counter equals `within`), the cadence counter is ignored and the actor's available actions are the responses of every binding restriction whose own guards, delay counters and profiles allow them (an actor compelled to respond does respond); choosing a declared response sets the cadence counter to k-1 like any declared action, choosing `idle` (when it is a response) decrements it. Delays and profiles are unchanged: a delayed action is unavailable while pending whatever the cadence counter says, and a selected profile forbids as before. A cadence k ≥ 2 needs the built-in `idle` (`idle=False` with k ≥ 2 is a `ModelError`); Nature has no cadence.
- `latch(name, of, when)` adds a variable with the levels of `of`, initial value `"unset"` prepended to those levels, which takes the current value of `of` in the system update of the first tick in which `when` holds, and never changes afterwards.
- `fairness(name, actor, trigger, within, responses)` adds the counter `fair_<name>` in `0..within`. In the system update it becomes `min(counter + 1, within)` if `trigger` holds in the new state and the actor's chosen action was not in `responses`, and `0` otherwise. When the counter equals `within`, the actor's available actions are restricted to `responses` (those whose own guards hold). If none is available the engine raises `ModelError`.
- `profile(name, actor, forbid, unless)` is inert unless selected at explore time; when selected, the listed actions are unavailable for that actor in states where `unless` does not hold. `unless` defaults to never.
- `invariant(name, expr)` and `ending(name, expr)` declare named predicates. `V.invariant("name")` and `V.ending("name")` reference them inside other expressions.
- `source` is free text stored on the action and reported in the parameter budget; `speculative=True` is stored and counted separately.
- `assume(name, expr)` restricts the initial state set to states satisfying `expr`. It is a named assumption like the others below.
- **Named assumptions.** Every action guard (named `<actor>.<action>`), fairness constraint, profile and `assume` is a named assumption. `compile(model, profile=None, relax=frozenset())` takes assumption names to relax: a relaxed guard becomes `TRUE`, a relaxed fairness constraint is removed, a relaxed `assume` no longer filters initial states, a relaxed profile is not applied. Relaxation only ever loosens. `CompiledModel.assumptions()` lists the names.
- **Parted guards.** A guard may be declared as named parts, `guard={"china_quiet": ~V.china_war, "ussr_weak": V.arms_USSR == "weak"}` or a list of `(name, expr)` pairs, meaning their conjunction. Part names are identifiers, unique within the action; each part is a separate named assumption `<actor>.<action>:<part>`, and relaxing it drops that conjunct while the rest of the guard stays. Relaxing `<actor>.<action>` relaxes every part. `assumptions()` lists the non-trivial parts in declaration order in place of the guard's name; a plain expression guard keeps the single name `<actor>.<action>`. The observation check applies to every part.

### 3.1a Settled details (from the phase 0 implementation review)

- `var(..., init=...)` defaults to the first level; `init=None` still means every level. `counter` and `flag` accept `init=None` the same way.
- `Set(var, value)` also accepts an integer expression (for example `Set("a", V.b)` or `Set("stock", V.cap + 2)`), evaluated on the pre-state and clamped to the variable's range. A literal out of range is a compile-time `ModelError`. A flag may be used directly as a condition; a level or counter may not.
- Reserved names, in addition to the built-ins: `Nature`; `all`, `all_except`, `only`, `invariant`, `ending`, `ref` (they would collide with the `V` namespace methods; use `V["name"]` for awkward names); Python keywords. `idle` and `none` are reserved action names for every actor.
- `m.nature()` takes no arguments. Nature cannot use `remember_last` or `cadence` and cannot appear in `hidden_from`.
- State layout: `tick` first in timed models; then declared variables and latches in declaration order; then `pending_<actor>_<action>` (actor order, then action order), `last_<actor>` (actor order), `fair_<name>` (declaration order) and `cadence_<actor>` (actor order, only for actors with cadence k ≥ 2). The cadence counters come last so that a model without a cadence keeps every index it had. Each actor's built-in action (`idle`, or `none` for Nature) is at action index 0; declared actions follow in declaration order, so shortest witnesses prefer doing nothing among equal-length traces.
- `assumptions()` lists declared actions whose guard is not the constant `TRUE` (as `<actor>.<action>`, or one entry `<actor>.<action>:<part>` per non-trivial part of a parted guard), then fairness constraints, then the selected profiles, then `assume` names. Relaxing a trivial guard, a trivial part or an unselected profile is a no-op, not an error. `budget()` reports `guard_parts`, the number of non-trivial parts over all actions, beside `guards`, and `cadence`, the number of actors declared with a cadence k ≥ 2 (0 for a model without one).
- A latch whose `when` already holds in an initial state is set there, to the initial value of `of`.
- Delayed effect lists are evaluated on the pre-state of the transition in which they fire and composed as a second phase after the immediate effects: delayed `Set`s override, delayed `Bump`s add, then clamping. Two delayed `Set`s with different values in one transition are a `ModelError`; a delayed `Set` overriding an immediate `Set` is not.
- Latch conditions and fairness triggers read the state after the tick, delay, cadence and last-action updates (latches before fairness counters).
- `V.only(...)` also includes the actor's own built-ins (`tick`, its `last_*`, its `pending_*`, `fair_*` and `cadence_*` counters). `hidden_from` removes variables after any `observes` choice.
- `explore(cm, initial=[...])` takes explicit initial states as given and does not apply `assume` filters; only `cm.initial_states()` is filtered.
- `AttractorResult.strategy` has entries only for states that joined through a move; `SafeResult.strategy` only for non-terminal kernel states.
- `Graph.moves[i]` and `Graph.avail[i]` are shared between states with identical availability and must be treated as read-only.
- Cadence (settled when it was added, docs/framework_changes.md): `cadence` must be an int ≥ 1 (a bool is refused); k ≥ 2 with `idle=False` is a `ModelError` at declaration, and the compiler checks the attribute again, so a cadence assigned after declaration is validated too. Availability of a cadenced actor in a state s, with G the actions allowed by guards, delay counters and selected profiles: if some fairness restriction of the actor binds, G restricted to the responses of every binding restriction (the cadence counter is not consulted); otherwise G if `cadence_<actor>` is 0, else G ∩ {`idle`}. A relaxed fairness constraint does not override (it no longer exists). The counter update runs after the delay counters and before the last-action variables; a delayed action chosen sets both its `pending_` counter and the cadence counter, which then run independently. The counter is a state variable like the others: it appears in traces, in `state_dict` and in the visualizer as a numeric built-in, and expressions may read it (`V["cadence_A"]`) subject to the observation rule. `fingerprint(model)` includes the cadences only when some actor has k ≥ 2, so models without a cadence keep their fingerprints. In a flattened game (section 14) the coarse cadence counters, like the other coarse counters, are frozen during a crisis and update on the return transition, in which the crisis action counts as a declared action of the crisis actor.
- `ruff format` is configured to exclude Markdown files, because the installed ruff also reformats Python snippets inside documentation.

### 3.2 Expressions (`wavefront.model.expr`)

`V` is a namespace: `V.name` is a `VarRef`. `V.tick` is the built-in tick. Expression nodes are immutable dataclasses:

- Comparisons: `VarRef op (level name | int | bool | VarRef)` for `== != < <= > >=`. Level names are resolved against the variable's levels at compile time; an unknown name is a `ModelError`. Comparing two `VarRef`s compares indices.
- Boolean: `&`, `|`, `~`, `Expr.implies(other)`, `VarRef.is_in([...levels])`.
- Arithmetic on counters and the tick: `+`, `-`, `min`, `max` as `wavefront.model.expr.Min/Max`, and `Ite(cond, a, b)`. Results may be compared.
- Constants `TRUE`, `FALSE`.

Every node supports `free_vars() -> frozenset[str]`, `to_python(compiled) -> Callable[[tuple], bool|int]` (compiled through generated source so that evaluation is one function call per guard), and `to_z3(ctx, state_vars_at_tick) -> z3.ExprRef` (implemented in `wavefront.bmc`, not here: `expr.py` exposes a visitor so that `bmc` can walk the tree without importing z3 into the core).

### 3.3 Effects (`wavefront.model.effects`)

- `Set(var, value)`: assign a level, counter value, or flag.
- `Bump(var, amount)`: add `amount` to the index, clamped to the variable's range. `strict=True` raises `ModelError` instead of clamping.
- `Inc(counter, amount=1)`, `Reset(counter)`: sugar over Bump and Set for counters.
- `SetIf(cond, var, value)`: conditional assignment, evaluated on the pre-state.

### 3.4 Effect composition in a joint move

All effects of all chosen actions are evaluated against the pre-state. Then, per variable: if any `Set` targets it, the `Set` value is taken (two `Set`s with different values on one variable in the same joint move is a `ModelError` at explore time naming the state and the actions); then all `Bump`s on it are summed and added; then the result is clamped (or `strict` raises). System updates run after that, in this order: tick increment, delay counters and delayed effects, cadence counters, last-action variables, latches, fairness counters.

## 4. CompiledModel (`wavefront.model.compile`)

`compile(model, profile=None) -> CompiledModel`, with:

- `variables: list[VarSpec]` in state order, each with `name, kind ('level'|'counter'|'flag'|'builtin'), levels, size`.
- `index: dict[str, int]`, `horizon: int`.
- `actors: list[ActorSpec]` with `name, actions: list[ActionSpec]`, Nature last.
- `ActionSpec`: `name, guard (callable on state tuple), effects, delay, source, speculative, is_idle, guard_expr, guard_parts`. `guard_expr` is the compiled guard (`TRUE` when relaxed; for a parted guard the conjunction of its unrelaxed non-trivial parts); `guard_parts: tuple[tuple[str, Expr], ...]` lists a parted guard's parts in declaration order with relaxed parts as `TRUE`, and is empty for a plain guard.
- `initial_states() -> list[tuple]`.
- `available(state) -> list[list[int]]`: per actor, indices of available actions (guards, delay counters, fairness restriction, profile, cadence counter).
- `step(state, joint_move: tuple[int, ...]) -> tuple`: deterministic successor.
- `is_terminal(state) -> bool`, `ending_of(state) -> str | None` (`"HORIZON"` when terminal by tick and no ending holds).
- `evaluate(expr_or_name, state) -> bool|int` for invariants, endings and ad-hoc expressions.
- `budget() -> dict`: counts of variables, levels, actions, guards, speculative actions, fairness constraints, delays, actors with a cadence (`cadence`), latches (the parameter budget).
- `observation_check()` is run at compile; violations raise `ModelError` naming actor, construct and variable.
- `observe(actor_name, state) -> tuple`: the projection of the state onto the actor's observed variables, in state order.
- `assumptions() -> list[str]` as in section 3.1.

## 5. Explicit engine (`wavefront.engine`)

### 5.1 Graph

```python
@dataclass
class Graph:
    model: CompiledModel
    states: list[tuple]              # id -> state
    index: dict[tuple, int]
    initial: list[int]
    moves: list[list[tuple[int,...]]]   # id -> joint moves (empty for terminal states)
    succ: list[list[int]]               # id -> successor id per joint move, aligned with moves
    avail: list[list[list[int]]]        # id -> per actor available action indices
    depth: list[int]                    # first-reached BFS depth
    terminal: list[bool]
    ending: list[str | None]
```

Helper methods: `states_where(pred: Expr | str | Callable) -> set[int]`, `ending_states(name) -> set[int]`, `size()`.

### 5.2 explore

`explore(cm, initial=None, max_states=1_000_000, on_progress=None) -> Graph`. Breadth-first from the initial states; raises `ModelError` on the conditions in section 1 and `BudgetExceeded` when `max_states` is passed. Must handle 10^5 states with 10^2 joint moves each in under a few minutes in CPython; profile the hot loop; guards and effects are compiled to Python functions once.

### 5.3 solve

- `attractor(g, coalition: set[str], target: set[int]) -> AttractorResult(win: set[int], strategy: dict[int, tuple], rank: dict[int, int])`. Counter-based worklist algorithm: for each state and each C-move, the number of completions whose successor is outside the current winning set; a state joins when some C-move's counter reaches zero. `rank` is the iteration at which a state joined (the forced distance in ticks). `strategy[s]` is the C-move that made s join (as the sub-tuple of the joint move restricted to the coalition, with actor order).
- `safe(g, coalition, phi: set[int]) -> SafeResult(kernel: set[int], strategy: dict[int, tuple])`. Greatest fixpoint; `strategy[s]` is some C-move all of whose completions stay in the kernel.
- `contested(g, coalition, target_or_phi, kind: 'reach'|'keep') -> ContestedResult(forced: set[int], blocked: set[int], contested: set[int])`, where `blocked` for `reach` is `safe(rest, ¬target).kernel` and for `keep` is `attractor(rest, ¬phi).win`; `rest` is every actor including Nature not in the coalition.

Correctness is tested against brute force on tiny games: enumerate all memoryless uniform coalition strategies and check the fixpoint results exactly (section 11).

### 5.4 Traces

`Trace` is a list of `(state_id, joint_move)` pairs ending in a state with no move. `witness(g, source: int, targets: set[int]) -> Trace | None` is a BFS shortest path. `Trace.render(g) -> str` prints a table of tick, each actor's action, and the variables that changed, using level names.

## 6. Bounded model checking (`wavefront.bmc`)

`encode(cm, k) -> Encoding`: Z3 Int constants per variable per tick `0..k` with domain constraints; per actor per tick an Int for the chosen action index; `chosen_i(t) → (¬assume_i ∨ guard_i(t))` for every guard where `assume_i` is a Bool constant (one per action guard and one per fairness constraint); availability of delayed actions, fairness restrictions and cadences encoded from the same built-in counters (a declared action of a cadenced actor needs `cadence_<actor> == 0` or some `assume_<f> ∧ fair_<f> ≥ within` of that actor); per variable the next value from the composition rule of section 3.4 using `If` chains; system updates; terminal states frozen (`terminal(t) → state(t+1) == state(t)`, where terminal covers endings and `tick == horizon`). Relaxable assumptions are the named assumptions of section 3.1: guards, fairness constraints, profiles and `assume` restrictions, each with a Bool `assume_<name>`.
A parted guard gets one Bool per part and the clause `chosen → ∧_i (¬assume_<actor>.<action>:<part_i> ∨ part_i(t))`; `reach(..., relax=...)` and `relax` take and return part names (`<actor>.<action>` in `reach` stands for all its parts).

- `reach(cm, k, target: Expr | str, relax=frozenset()) -> BmcTrace | None` with every non-relaxed assumption asserted true; the target is an ending name, `HORIZON`, an invariant name or an expression (a value expression counts as true when non-zero, as in the explicit engine). The trace is shortest (binary search on depth); `BmcTrace(states, moves, relaxed)` renders the same table as `Trace.render` and replays with `cm.step`.
- Settled encoding choices: each tick has an `active` Bool so a path may stop once the target is reached (otherwise a target state with no available move would make a valid query unsatisfiable); transitions on which the explicit engine raises (conflicting Sets in one phase, a strict Bump out of range, a monotone decrease) are excluded by constraints; terminal states are frozen and their chosen actions fixed to index 0; the unsat core is z3-minimized but not guaranteed minimal; `relax` uses `z3.Optimize` with `elim_01=False`. The encoder reuses the compiler's private level-resolution helpers so names resolve exactly as the compiler does; a refactor of `compile.py` must keep them or expose a public equivalent.
- `relax(cm, k, target, max_relax=3, max_sets=20) -> RelaxResult(reachable_as_is, core, minimum_size, minimal_sets, trace)`: if unreachable, the unsat core over the `assume` constants; then `z3.Optimize` with soft `assume_i` to find a minimum-cardinality relaxation set, and enumerate all minimum sets by blocking clauses up to a limit.
- Cross-check test: on random small models, `reach` agrees with `explore` + `attractor(all actors)` restricted to depth k, and `relax` minimal set sizes agree with brute-force relaxation over the explicit engine for models with at most 6 guards.

## 7. Analysis (`wavefront.analysis`)

- `viability(g, coalition, invariant_name) -> SafeResult` (the kernel).
- `point_of_no_return(trace, kernel) -> int | None`: index of the first trace state outside the kernel.
- `distance(g, state_id, kernel, coalition, adversary: set[str]) -> Distance(forced, shortest, margin)` (also `distance_table` for many states from one pair of fixpoints): `forced` is the rank in `attractor(adversary, complement(kernel))` (None if the adversary cannot force leaving; always None from inside the coalition's own kernel when the adversary is disjoint from it, so it is informative outside the kernel and for joint kernels against one member); `shortest` is the rank in `attractor(all actors and Nature, complement(kernel))`, the fewest steps of arbitrary play that leave the kernel; `margin` is the number of consecutive ticks the coalition can play arbitrarily and still be inside the kernel whatever the others do (the stage index of `M₀ = kernel, M_{i+1} = {s ∈ M_i | every joint move from s stays in M_i}`); it is `None` outside the kernel, infinite when no play leaves the kernel, and otherwise equals `shortest - 1`, so it is reported for readability rather than as new information.
- `is_uniform(g, coalition, strategy: dict[int, tuple]) -> UniformityResult(uniform, jointly_uniform, conflicts)`: `uniform` holds when, for every member, that member's component of the coalition move is the same on every pair of strategy states with equal `cm.observe(member, state)` (the strategy is playable by members acting on their own observations); `jointly_uniform` is the weaker check on the joint observation tuple; `conflicts` lists (member, state, state) triples. `strategy_closure(g, coalition, strategy, sources)` restricts a strategy to the part used from given states, which is what reports check.
- `pivotal(g, ending_name, actors=None, include_nature=False, initial=None) -> PivotalResult(forcing: list[frozenset], blocking: list[frozenset])`: minimal coalitions (by inclusion) that can force the ending from every state in `initial` (default: every initial state), and minimal ones that can block it from every such state. Per-hypothesis results pass the initial states of one hidden value.
- `relax_explicit(model, ending_name, max_size=2, coalition=None, profile=None, initial=None, max_states=...) -> RelaxSets`: brute-force minimal relaxation sets over the named assumptions (section 3.1) using re-explore; `RelaxSets` is a `list[list[str]]` with `assumptions`, `minimum_size`, `ill_formed` (relaxations whose model raised `ModelError`) and `undecided` (explorations over budget), neither of which counts as a result. With `coalition=None` the question is reachability from *some* initial state (matching the bounded encoding); with a coalition it is forceability from *every* initial state (matching `pivotal`), which is not monotone in relaxations (loosening can help either side), so only the brute-force variant answers it. `minimal_relaxation_size(model, ending, max_size, ...)` returns ρ(E).
- `sensitivity(model, invariant_name, coalition, adversary=None, profile=None, initial=None, max_states=...) -> list[SensitivityRow]`: perturbs initial *states*: for each declared variable and each value it takes in the initial states, one level down and one up where legal (latches recomputed; perturbations violating an `assume` dropped; explicit initial states perturbed as given), then recomputes kernel membership and the `shortest` distance, and the `forced` distance when an adversary is given; rows sorted by membership flips, then change of `shortest`, then of `forced`. `sensitivity_table` answers several queries from one exploration.
- `cluster(traces, g) -> list[Cluster]`: group traces by the frozenset of `(actor, action)` pairs whose guard was non-trivially satisfied along the trace (a guard that is `TRUE` does not count); each cluster has a signature and a representative shortest trace.
- `budget(cm) -> dict` (the keys of section 4 and 3.1a, `cadence` included), `fingerprint(model) -> str` (a hash of the declarations, printed on every report), and `informativeness(model, negative_controls: list[tuple[str, str, int]]) -> float`: fraction of (ending, op, n) controls satisfied, where op is one of `>=`, `==`, `<=` and compares the minimal relaxation set size with n (so "needs at least three", "needs exactly one" and "needs at most one" are all expressible).

## 8. Report (`wavefront.report`)

`wavefront.analysis.run_all(model, coalitions=None, profile=None, initial=None, max_relax=2, max_states=...) -> Analysis` bundles the graph, per-coalition kernel membership of the initial states (and, for joint coalitions, the forced distance out of the joint kernel when one member defects), per-ending contested status per coalition with shortest witnesses (`HORIZON` counts as an ending in timed models), minimal relaxation sets, pivotal coalitions, sensitivity rows, uniformity notes on the used part of each strategy, the budget, the fingerprint and the speculative actions used by any reported trace. Default coalitions: each actor alone and all non-Nature actors together.

When a model sweeps a hidden variable (`init=None`), every ending tends to be reachable from *some* initial state and the relaxation table is uninformative; reports for such models are produced per hypothesis by passing `initial=` the initial states of one hidden value (the CLI's `--snapshot` fixes them the same way).

`render(analysis) -> str` produces Markdown with, in order: the front-page caveat ("every result is conditional on the model version and the initial state; no bare reachability result is a finding"); the parameter budget; initial states and kernel membership per coalition; endings with forced/blocked/contested status per coalition and the shortest witness trace; minimal relaxation sets; pivotal coalitions; sensitivity table; the list of speculative actions used by any reported trace.

## 9. Evidence (`wavefront.evidence`)

`snapshots/schema.json` (JSON Schema draft 2020-12) for the snapshot format in DESIGN.md section 5.1: `date`, `model`, `variables: {name: {level, confidence, indicators: [{id, value, source, observed, rule}]}}`, `rates`. `load_snapshot(path, cm) -> tuple` maps a snapshot to an initial state (variables not in the snapshot take their declared init; a snapshot level not in the variable's levels is an error). Provenance fields are required; the loader refuses a variable with no indicator unless `confidence == "assumed"`.

Settled loader details: level variables take level names, counters integers, flags booleans; a swept variable (`init=None`) must be fixed by the snapshot; built-in variables cannot be set in `variables`; a latch the snapshot does not set whose condition already holds in the loaded state is set, as for the model's own initial states; the returned state is not filtered by `assume`; the `model` string and `rates` are shape-checked only (the name is not compared with the model's, and rates are not applied in phase 0); duplicate JSON keys are rejected; all problems are reported together. `SnapshotError` subclasses `ModelError` so the CLI reports a bad snapshot as a user error (exit 2). `validate_snapshot(data) -> list[str]`, `snapshot_to_state(data, cm)` and `read_snapshot(path)` are also public.

Built-ins (phase 2, decision F2 of docs/phase2_kickoff.md): an optional top-level `builtins: {name: {value, confidence, indicators, rule}}` sets built-in variables, filled into the state after the variables. Settable are `pending_<actor>_<action>` (an integer from 0 to the action's delay: the ticks until the delayed effect applies, with the semantics of section 3.1), `last_<actor>` (an action name of the actor, `idle` or `none`), a latch (`unset` or a level of the variable it copies, given as that variable is given: a level name, a boolean for a flag, an integer for a counter or the tick) `fair_<name>` (an integer from 0 to `within`) and `cadence_<actor>` (an integer from 0 to the actor's cadence minus 1: the ticks until its declared actions are available again); `tick` is not settable. Indicators follow the variables' provenance rule (none only with `assumed`), and `rule` is required. An unknown built-in name, a declared variable named in `builtins`, a value out of range, and a latch given as `unset` while its condition holds in the loaded state are errors naming the built-in.

Clock consistency of hindsight start states (owner's decision 7, 2026-10-15; `clock_consistency` in `wavefront/evidence/hindsight_ww2.py`, used by both WW2 builders): a start state follows the model's own clock where the record lags it by one tick. After the event-dated reading of quarter Q (tick index(Q) + 1), the model is stepped once from the model-consistent snapshot of the quarter before (with its built-ins) under the realized joint move of Q. A variable written in that step by (a) a landed decision, the delayed effect of a recorded decision landing in that transition (decided at tick t with delay d, t + 1 + d = index(Q) + 1), or (b) the immediate effect of a realized move of Q, takes the model's value when the reading of Q differs from it and the reading of Q + 1 equals it; the entry names the decision or move as its first indicator, with a note giving the overridden reading and the record's date, and keeps the overridden indicators. Nothing else changes: a disagreement longer than one tick, a record that leads the model, a move placed by [NSL], and the last quarter of a series stay as the record reads them. The pass imports the domain model only when it runs; a caller can pass its own `Clock` (compiled model and fixed hidden objectives) or skip the pass.

CIA estimates corpus (`wavefront/evidence/corpora/crest.py`, source `crest`; the other corpus modules, `extract`, `harness_rules`, `review` and `replay` are described in docs/replay_harness.md and still lack their paragraphs here). An `IndexedCorpus` over `data/cw/corpora/raw/crest/` (PDFs and a hand-written `MANIFEST.json`; no fetch step): `build_index(corpus)` reads each PDF's text layer with `pdftotext` (poppler-utils; no OCR, a PDF without a text layer yields no document and is listed under `skipped`) and writes `index.json`; `scripts/fetch_corpora.py crest` and `--check crest` run it and check it. The Steury (1996) volume is split into its estimates by `STEURY_1996`, its table of contents (estimates and editorial sections with the volume page each starts on), and the printed page numbers read from the foot of each page (`volume_page_numbers`); the editor's sections, headings, running heads and page numbers and the declassification stamps are left out of the text; a split whose first pages carry a running head or lack the estimate's heading is an error, not a silent split. A document is dated by its estimate's own date: a separately fetched file by its name (`<series>_<number>[_MH]_<YYYY-MM-DD>_<title>.pdf`), an estimate of the volume by the date `STEURY_1996` gives with its basis (printed in the corpus or recorded with a source in the repository); an estimate without one is undated and not indexed. `Document` has an optional `work` (default empty): the work a document is a copy or a part of when a corpus holds it more than once (here the estimate's number, shared by the volume's extract, the full text and its parts); the extractor writes it into each proposal record (`work`) and the `two-document` harness rule counts proposing documents by work, else by id.

Episodes of the replay harness (`wavefront/evidence/episodes.py`, `wavefront/evidence/replay_cw.py`). An `Episode` names what the extractor, the harness rules, the review step and the replay read for one domain model: its text-derived variables with levels and initial levels, its ontology (the threshold rules), the period wording of the extractor's prompt, the model of its replay snapshots, its hindsight snapshots and its periods. `ww2` (quarters, the WW2 v0 tables of `hindsight_ww2`) is the default everywhere and behaves as before; `cw` (the Cold War v0 model) has the three belief variables of docs/ontology_cw.md section 3 as text variables, all outside the harness rules, and runs by year: the period `Y` reads the documents dated to 31 December of Y - 1 and its snapshot is the state on 1 January Y, the beliefs from accepted proposals and every other variable, rate and built-in carried from the hindsight snapshot as `assumed`. A proposals file of an episode other than WW2 records it (`episode`); a directory holds one episode. `VariableSpec.episode` selects the prompt's instructions, so the backends take no episode argument. `replay_cw.compare` and `render_report` give the Cold War metrics (per year against the hindsight truth and the contemporaneous beliefs; the C6 and C7 inputs); docs/replay_harness.md, section "The Cold War episode".

## 10. CLI (`wavefront.cli`, entry point `wf`)

Models are referenced as `path/to/model.py:attr` (the module attribute holding the `Model`) with `model` as the default attribute. Subcommands:

```
wf explore MODEL [--profile P] [--max-states N]
wf reach   MODEL --ending E [--trace]
wf force   MODEL --coalition A,B --ending E
wf viable  MODEL --coalition A --invariant I [--snapshot FILE]
wf mine    MODEL --ending E [--k K] [--max-relax N]
wf pivot   MODEL --ending E
wf report  MODEL [--out FILE]
```

Every subcommand accepts `--profile` and `--max-states`; `mine` accepts `--coalition` (forceability) and `--bmc` (bounded search through `wavefront.bmc`, with `--k` defaulting to the horizon); `pivot` accepts `--nature`; `report` accepts repeatable `--coalition` and `--max-relax`. A model reference may also name a function returning a `Model` or a dotted module. Exit code 0 on success, 2 on `ModelError` (message on stderr naming the state and construct) and on usage errors, 1 when the model cannot be loaded, the state budget is exceeded, or an optional module is missing.

## 11. Tests (`tests/`)

- `tests/model/`: DSL construction, compile errors (unknown level, observation violation, duplicate names, missing available action, conflicting Sets, ending exclusivity), effect composition, delays, cadences, latches, fairness counters, profiles, monotone checks.
- `tests/engine/`: hand-built games with known answers; brute-force cross-check of `attractor` and `safe` against enumeration of all memoryless per-state coalition strategies on random tiny models (hypothesis, at most 3 actors, 2 actions each, at most 4 variables with 2 or 3 levels, horizon at most 4); a non-determined concurrent game whose result must be `contested`; witness traces are shortest.
- `tests/bmc/`: cross-checks of section 6.
- `tests/analysis/`, `tests/report/`, `tests/evidence/`, `tests/cli/`.
- Performance smoke test: a synthetic model with about 10^5 reachable states explores in under 120 seconds (marked `slow`).

Run with `pytest -q`; lint with `ruff check .` and `ruff format --check .`; both clean is part of every gate.

## 12. Visualizer (`wavefront.viz`)

A static, self-contained HTML page generated from engine output: initial state, trajectory board (status band, decision lanes with alternatives classified safe/risky/losing, variable heatmap), decision tree with hand-built counterfactuals and fork markers, compare view, landscape of the reachable space with forward and backward wavefronts, and the report tables. Design, data bundle and acceptance criteria are in [visualizer.md](visualizer.md). CLI: `wf viz MODEL --out FILE`.

## 13. Reserved for later phases

- **Multi-resolution time** was reserved here in phase 0 and is implemented in phase 2 as section 14 (`wavefront.engine.multires`); the constrained attractor, nested crises and tick-weighted ranks remain open there.
- **Uniform strategy synthesis** for coalitions with hidden variables (SAT encoding of one move per observation class).
- **Unbounded fairness** (Büchi or Streett objectives) and the external cross-check against PRISM-games once the exporter exists.
- **The brute-force cross-check in section 11** enumerates per-state memoryless strategies, which is what the solvers compute.

## 14. Multi-resolution time (`wavefront.engine.multires`)

The multi-resolution item reserved in section 13, implemented (phase 2, PLAN.md step 2.2, demanded by coldwar_testbed.md C3) by flattening, as theory.md section 7 permits. A coarse compiled model gets crisis sub-games; the flattened game is an object that the engine accepts in place of a `CompiledModel`.

```python
from wavefront.engine import Crisis, explore, flatten

cuba = Crisis(
    "USSR", "crisis", sub_cm,                     # coarse actor and action; fine compiled model
    entry=lambda year: {"esc": year["esc"]},      # coarse state_dict -> fine initial values
    exit=lambda day, year: {"esc": day["esc"]},   # (fine terminal state_dict, entry state_dict)
    name="cuba",                                  #   -> levels of the coarse variables changed
)
fm = flatten(coarse_cm, [cuba])
g = explore(fm)                                   # then attractor, safe, contested, witness, ...
```

- `Crisis(actor, action, sub, entry, exit, name=None)`. `actor.action` is a declared coarse action with no effect and no delay. `sub` is a timed compiled model. `entry(coarse_state_dict)` returns fine initial values for the variables it names; every other fine variable takes its declared initial value, and a fine variable declared with `init=None` must be named. `exit(fine_state_dict, coarse_state_dict)` is called on a terminal fine state with the state the crisis was entered from and returns the levels of the coarse variables the crisis changes. Map values are level names, counter integers or booleans; the strings of `state_dict` are accepted. `name` (default `action`) labels the crisis in states and messages.
- `flatten(coarse_cm, crises) -> FlatModel`. Raises `ModelError` naming the crisis for an unknown actor or action, a crisis action with an effect or delay, an untimed sub-game, a fine actor (Nature included) that is not a coarse actor of the same name, two crises with one name or on one action. Entry and exit maps are checked when applied: a name that is not a declared variable of the model concerned, a value out of range, a returned object that is not a mapping, a swept fine variable not fixed by `entry`, an entry state violating a fine `assume`, an exit lowering a monotone coarse variable.
- **State encoding.** A coarse state is the coarse model's own tuple, so `variables`, `index`, `initial_states()` and explicit initial states are the coarse model's. A fine state is `s + (k,) + h`: the entered-from coarse state `s` (frozen), the crisis index `k` and the fine state `h`. `format_state` prints it as `[crisis cuba from {coarse state}] {fine state}`; `state_dict` adds the fine variables as `<crisis>.<variable>`. `is_fine`, `split`, `coarse_part` and `fine_ending_of` decode states.
- **Semantics.** (1) In a coarse state, any joint move in which the crisis actor plays the crisis action leads to `s + (k,) + ι(s)`; the other actors' moves in it are discarded and the coarse tick does not advance; two crisis actions in one joint move are a `ModelError`. (2) In a fine state whose fine part is not terminal the moves and `step` are the fine model's; a coarse actor that is not a fine actor plays its built-in `idle` (`none` for Nature, a synthetic `idle` for an actor declared `idle=False`). (3) A fine state whose fine part is terminal (fine horizon or fine ending) has one joint move, the crisis actor's crisis action with every other actor's built-in action, whose successor is the coarse transition from `s` with the exit levels as its only immediate effects: the tick advances by one, delay counters, latches, fairness counters and `last_<actor>` update as in any coarse transition with that joint move (so `last_<actor>` records the crisis, and a delayed `Set` falling due overrides an exit level). The crisis fits inside one coarse tick; delays, cadence counters, latches and fairness counters of the coarse model are frozen during it and resume on return. (4) Coarse invariants and endings are evaluated on coarse states; on a fine state every coarse invariant holds and no coarse ending holds; a fine state is never terminal (a fine ending only ends the sub-game). Ad-hoc expressions and Python predicates read the frozen coarse part. (5) Fine actors are coarse actors by name, so coalitions mean the same at both levels.
- **Joint moves.** Flat actors are the coarse actors in the same order; each actor's action list is its coarse actions (same indices), a synthetic `idle` if needed, then each crisis's fine actions at an offset. `format_move` and `Graph.move_names` print the fine actions' own names.
- **What runs on a flattened game.** `explore`, `attractor`, `safe`, `contested`, `witness`, `Trace.render`, and the analysis functions that take a graph (`viability`, `distance`, `distance_table`, `point_of_no_return`, `silent_phase`, `pivotal`, `is_uniform`, `strategy_closure`, `cluster`), and `report.render` on an `Analysis` assembled from them. `run_all`, `relax_explicit`, `sensitivity`, the CLI, `wavefront.bmc`, the symbolic path and the visualizer recompile a `Model` or assume the coarse layout and do not take a flattened game. A fine model's assumptions are relaxed by compiling it with `relax=` and flattening again. Nested crises are not supported. `assumptions()` lists the coarse model's; `budget()` adds `crises` and the sub-games' summed `crisis_variables`, `crisis_actions`, `crisis_guards` and `crisis_speculative_actions`, and its `state_space_bound` covers fine states.
- **Ranks** on a flattened game count its transitions: a crisis costs its entry, its fine steps and its return, while the coarse tick advances by one. Report columns headed "ticks" read as transitions for a flattened game.
- **Trace rendering.** `Trace.render` uses a model's `trace_tick(state, step)` and `trace_changes(state, next_state)` when it defines them (only `FlatModel` does): the tick column reads `3 [cuba 1]` inside a crisis, and the changes column shows `enter crisis cuba (...)`, `cuba.<variable>: a -> b` and `return from crisis cuba; ...`. Output for ordinary models is unchanged.
- **Tests.** `tests/engine/test_multires.py`: soundness by flattening (a hand-built game and random ones against the same game inlined by hand into one model, every fixpoint compared state by state, ranks included; the lifting equation of theory.md section 7 against separate solves of the sub-game), controllability through the crisis, nondeterministic exit, frozen counters and the error cases. `tests/toy/test_crisis.py` runs the toy `models/toy/crisis.py` through the engine, the analysis functions and the report renderer.

## 15. Symbolic engine (`wavefront.symbolic`)

Decision F1 of docs/phase2_kickoff.md: an in-house reduced ordered BDD package (`bdd.py`), a binary encoding of a compiled model (`encode.py`) and the fixpoints of section 5.3 over that encoding (`solve.py`). The record of what was built, the cross-checks and the benchmark is docs/engine_scaling.md. The contract:

- `encode(cm, var_order=None, actions="top") -> Encoding`: one current bit vector and one next bit vector per state variable (interleaved), action bits per actor (Nature included), a domain constraint, availability per actor and action (guards with their named parts, delay counters, profiles, the fairness restriction, the cadence counter with the fairness override), `live`, `term` (every ending and the horizon), `initial`, `error` (the transitions on which the explicit engine raises), `preimage` by substitution and `image` by a partitioned relational product. `predicate(target)` takes an ending name, `HORIZON`, an invariant name or an expression. Helpers map explicit states to cubes and back, and give an explicit state's availability and successor.
- `cpre(enc, C, X)`, `attractor(enc, C, T)`, `safe(enc, C, phi, within=None, method="auto")`, `contested(enc, C, goal, kind)`, `reachable(enc, initial, check=True)`, `shortest(enc, state, target)` and `witness(enc, cm, state, target, C)` have the semantics of section 5.3 and of the explicit engine (`wavefront.engine`): on every state reachable from a start state the memberships, ranks, strategy moves, contested regions and witness lengths equal the explicit engine's, and `reachable(check=True)` raises `ModelError` with the explicit engine's message wherever `explore` would (an actor without an available action, overlapping endings, conflicting `Set`s, a strict `Bump` out of range, a monotone decrease).
- Results are predicates over current-state bits with `contains(state)`, `count(within=None)` and `stats` (seconds, nodes and peak nodes per iteration); attractors and kernels give `strategy_move(state)`.

Deviations from the explicit engine, all stated in docs/engine_scaling.md section 6: the fixpoints run over the whole domain, so a count is meaningful only restricted to a set closed under successors (`within=R`, typically a reachable set); `safe` on a timed model is computed backward one tick layer at a time (the same greatest fixpoint); `shortest` is computed forward from one state by breadth-first layers (the all-actor attractor over the whole domain does not fit in memory on WW2 v0); transitions in `error` are not excluded from the fixpoints, only reported by `reachable(check=True)`; `margin` is reported as `shortest - 1`.

Not covered: the CLI (section 10) does not call the engine yet; uniform-strategy checks (section 7) and pivotal coalitions are not computed on symbolic results; the flattened game of section 14 is not encoded.

BDD cores. Two managers implement one interface: `bdd.BDD`, the pure-Python reference, and `bdd_c.BDD`, a compiled C core (`wavefront/symbolic/_core/`, built by `python -m wavefront.symbolic._core.build` with the `fast` extra). `wavefront.symbolic.manager(kind=None)` returns a new manager: with no argument it follows the environment variable `WAVEFRONT_BDD` (unset or `c`: the compiled core when its extension imports, the reference otherwise; `python`: the reference); an explicit `manager("c")` does not fall back. `encode(cm, ...)` takes `manager=` and otherwise uses that default. Invariant: both cores give identical results. They keep the same canonical form (complement edges, TRUE = 0, FALSE = 1, the high edge of a stored node never complemented) and run the same recursions, so every operation returns the same function, and `node_count`, `support`, `pick_one` (the 0 branch first) and `count` (exact integers) return the same values; node numbers may differ, and functions are compared across managers with `transfer`. Garbage collection has the same roots (`gc` arguments, `protect`, registered `bdd_roots()` holders, held weakly) and `maybe_gc` the same policy; only the clearing of computed tables differs (docs/engine_scaling.md section 7). Every `stats` entry of a result names the core (`"core": "c"` or `"python"`). `tests/symbolic/test_bdd_differential.py` checks the invariant; the rest of `tests/symbolic/` passes under either core.

Tests (`tests/symbolic/`): every BDD operation against truth tables; the encoding, reachability, attractors, kernels by both methods, contested regions, `shortest` and witnesses against the explicit engine on random models from both generators (hypothesis examples, seeded sweeps, a sweep with collection at every step, a sweep in which every model has cadences); the toy model with and without a profile; WW2 v0 from hindsight states whose exact kernels the explicit engine computes (section 11 budget: 1939Q2 in the default suite, the 1938 states marked `slow`).
