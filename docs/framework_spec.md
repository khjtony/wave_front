# Framework specification (phase 0)

This is the contract for the `wavefront` Python package: the modeling DSL, the compiled model, the explicit-state engine, the bounded model checker, the analysis layer, the report, and the CLI. Implementation agents build against this document; reviewers check against it. Where the earlier sketch in DESIGN.md section 6.3 used Python lambdas for guards, this specification replaces them with declarative expression objects so that the same model can be interpreted by the explicit engine and compiled to Z3.

Python 3.11 or later. Package name `wavefront`, distribution name `wave-front`. Core has no third-party runtime dependency. `z3-solver` is an optional dependency used only by `wavefront.bmc`. Dev dependencies: `pytest`, `hypothesis`, `ruff`.

---

## 1. Semantics

A model defines a finite concurrent game.

- **State.** A valuation of all variables, represented at runtime as a tuple of small non-negative integers, one per variable in declaration order (built-in variables included). Level names map to indices in declaration order; comparisons between levels compare indices.
- **Actors.** Named players. One built-in actor `Nature` always exists; its actions are called events, and it always has the event `none`. Each actor always has at least one available action in every non-terminal reachable state; the engine raises `ModelError` naming the state and actor if not. Every actor gets an implicit `idle` action with no guard and no effect unless declared with `idle=False`.
- **Joint move.** One action per actor including Nature, chosen simultaneously. The transition is deterministic given the joint move. Nature's nondeterminism is therefore the choice of its event.
- **Transition.** Apply the chosen actions' effects, then the system updates (tick increment, delay counters, fairness counters, latches, last-action variables). Effect composition rules are in section 3.4.
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
  evidence/            snapshot schema and loader (section 9)
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
CH  = m.actor("CH",  observes=V.all())
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

- Names are identifiers; a name may be used once across variables, actors, actions of one actor, latches, fairness constraints, profiles, invariants and endings. Built-in names (`tick`, `last_<actor>`, `pending_<actor>_<action>`, `fair_<name>`) are reserved.
- `levels` must have at least two entries. `init` must be a level or `None`. `monotone=True` makes the compiler verify statically that no effect decreases the variable (a `Bump` with a negative amount or a `Set` to a lower level than any reachable value is a `ModelError` at compile time for `Set` only when the target is the lowest level; otherwise the engine checks at explore time and raises).
- `hidden_from` is a list of actor names. `observes` is `V.all()`, `V.all_except(*names)`, or `V.only(*names)`. A variable in `hidden_from` of actor X is removed from X's observation set whatever `observes` says.
- `delay=d` with d ≥ 1 defers the whole effect list. The compiler adds the counter `pending_<actor>_<action>` in `0..d`. Choosing the action in the transition from tick t to t+1 sets the counter to d in that transition's system update; each later transition decrements it, and when it goes from 1 to 0 the effect is applied in that same transition. The effect is therefore visible in the state at tick t+1+d, and the action is unavailable at ticks t+1 .. t+d. Example, d=1: chosen at t, unavailable at t+1, effect visible at t+2.
- `remember_last=True` adds the variable `last_<actor>` with levels `["none"] + action names`, updated to the chosen action each tick.
- `latch(name, of, when)` adds a variable with the levels of `of`, initial value `"unset"` prepended to those levels, which takes the current value of `of` in the system update of the first tick in which `when` holds, and never changes afterwards.
- `fairness(name, actor, trigger, within, responses)` adds the counter `fair_<name>` in `0..within`. In the system update it becomes `min(counter + 1, within)` if `trigger` holds in the new state and the actor's chosen action was not in `responses`, and `0` otherwise. When the counter equals `within`, the actor's available actions are restricted to `responses` (those whose own guards hold). If none is available the engine raises `ModelError`.
- `profile(name, actor, forbid, unless)` is inert unless selected at explore time; when selected, the listed actions are unavailable for that actor in states where `unless` does not hold. `unless` defaults to never.
- `invariant(name, expr)` and `ending(name, expr)` declare named predicates. `V.invariant("name")` and `V.ending("name")` reference them inside other expressions.
- `source` is free text stored on the action and reported in the parameter budget; `speculative=True` is stored and counted separately.
- `assume(name, expr)` restricts the initial state set to states satisfying `expr`. It is a named assumption like the others below.
- **Named assumptions.** Every action guard (named `<actor>.<action>`), fairness constraint, profile and `assume` is a named assumption. `compile(model, profile=None, relax=frozenset())` takes assumption names to relax: a relaxed guard becomes `TRUE`, a relaxed fairness constraint is removed, a relaxed `assume` no longer filters initial states, a relaxed profile is not applied. Relaxation only ever loosens. `CompiledModel.assumptions()` lists the names.

### 3.1a Settled details (from the phase 0 implementation review)

- `var(..., init=...)` defaults to the first level; `init=None` still means every level. `counter` and `flag` accept `init=None` the same way.
- `Set(var, value)` also accepts an integer expression (for example `Set("a", V.b)` or `Set("stock", V.cap + 2)`), evaluated on the pre-state and clamped to the variable's range. A literal out of range is a compile-time `ModelError`. A flag may be used directly as a condition; a level or counter may not.
- Reserved names, in addition to the built-ins: `Nature`; `all`, `all_except`, `only`, `invariant`, `ending`, `ref` (they would collide with the `V` namespace methods; use `V["name"]` for awkward names); Python keywords. `idle` and `none` are reserved action names for every actor.
- `m.nature()` takes no arguments. Nature cannot use `remember_last` and cannot appear in `hidden_from`.
- State layout: `tick` first in timed models; then declared variables and latches in declaration order; then `pending_<actor>_<action>` (actor order, then action order), `last_<actor>` (actor order) and `fair_<name>` (declaration order). Each actor's built-in action (`idle`, or `none` for Nature) is at action index 0; declared actions follow in declaration order, so shortest witnesses prefer doing nothing among equal-length traces.
- `assumptions()` lists declared actions whose guard is not the constant `TRUE` (as `<actor>.<action>`), then fairness constraints, then the selected profiles, then `assume` names. Relaxing a trivial guard or an unselected profile is a no-op, not an error.
- A latch whose `when` already holds in an initial state is set there, to the initial value of `of`.
- Delayed effect lists are evaluated on the pre-state of the transition in which they fire and composed as a second phase after the immediate effects: delayed `Set`s override, delayed `Bump`s add, then clamping. Two delayed `Set`s with different values in one transition are a `ModelError`; a delayed `Set` overriding an immediate `Set` is not.
- Latch conditions and fairness triggers read the state after the tick, delay and last-action updates (latches before fairness counters).
- `V.only(...)` also includes the actor's own built-ins (`tick`, its `last_*`, its `pending_*` and `fair_*` counters). `hidden_from` removes variables after any `observes` choice.
- `explore(cm, initial=[...])` takes explicit initial states as given and does not apply `assume` filters; only `cm.initial_states()` is filtered.
- `AttractorResult.strategy` has entries only for states that joined through a move; `SafeResult.strategy` only for non-terminal kernel states.
- `Graph.moves[i]` and `Graph.avail[i]` are shared between states with identical availability and must be treated as read-only.
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

All effects of all chosen actions are evaluated against the pre-state. Then, per variable: if any `Set` targets it, the `Set` value is taken (two `Set`s with different values on one variable in the same joint move is a `ModelError` at explore time naming the state and the actions); then all `Bump`s on it are summed and added; then the result is clamped (or `strict` raises). System updates run after that, in this order: tick increment, delay counters and delayed effects, last-action variables, latches, fairness counters.

## 4. CompiledModel (`wavefront.model.compile`)

`compile(model, profile=None) -> CompiledModel`, with:

- `variables: list[VarSpec]` in state order, each with `name, kind ('level'|'counter'|'flag'|'builtin'), levels, size`.
- `index: dict[str, int]`, `horizon: int`.
- `actors: list[ActorSpec]` with `name, actions: list[ActionSpec]`, Nature last.
- `ActionSpec`: `name, guard (callable on state tuple), effects, delay, source, speculative, is_idle`.
- `initial_states() -> list[tuple]`.
- `available(state) -> list[list[int]]`: per actor, indices of available actions (guards, delay counters, fairness restriction, profile).
- `step(state, joint_move: tuple[int, ...]) -> tuple`: deterministic successor.
- `is_terminal(state) -> bool`, `ending_of(state) -> str | None` (`"HORIZON"` when terminal by tick and no ending holds).
- `evaluate(expr_or_name, state) -> bool|int` for invariants, endings and ad-hoc expressions.
- `budget() -> dict`: counts of variables, levels, actions, guards, speculative actions, fairness constraints, delays, latches (the parameter budget).
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

`encode(cm, k) -> Encoding`: Z3 Int constants per variable per tick `0..k` with domain constraints; per actor per tick an Int for the chosen action index; `chosen_i(t) → (¬assume_i ∨ guard_i(t))` for every guard where `assume_i` is a Bool constant (one per action guard and one per fairness constraint); availability of delayed actions and fairness restrictions encoded from the same built-in counters; per variable the next value from the composition rule of section 3.4 using `If` chains; system updates; terminal states frozen (`terminal(t) → state(t+1) == state(t)`, where terminal covers endings and `tick == horizon`). Relaxable assumptions are the named assumptions of section 3.1: guards, fairness constraints, profiles and `assume` restrictions, each with a Bool `assume_<name>`.

- `reach(cm, k, target: Expr | str) -> Trace | None` with all assumptions asserted true.
- `relax(cm, k, target, max_relax=3) -> RelaxResult(core: list[str], minimal_sets: list[list[str]])`: if unreachable, the unsat core over the `assume` constants; then `z3.Optimize` with soft `assume_i` to find a minimum-cardinality relaxation set, and enumerate all minimum sets by blocking clauses up to a limit.
- Cross-check test: on random small models, `reach` agrees with `explore` + `attractor(all actors)` restricted to depth k, and `relax` minimal set sizes agree with brute-force relaxation over the explicit engine for models with at most 6 guards.

## 7. Analysis (`wavefront.analysis`)

- `viability(g, coalition, invariant_name) -> SafeResult` (the kernel).
- `point_of_no_return(trace, kernel) -> int | None`: index of the first trace state outside the kernel.
- `distance(g, state_id, kernel, coalition, adversary: set[str]) -> Distance(forced, shortest, margin)`: `forced` is the rank in `attractor(adversary, complement(kernel))` (None if the adversary cannot force leaving; always None from inside the coalition's own kernel when the adversary is disjoint from it, so it is informative outside the kernel and for joint kernels against one member); `shortest` is the rank in `attractor(all actors and Nature, complement(kernel))`, the fewest steps of arbitrary play that leave the kernel; `margin` is the number of consecutive ticks the coalition can play arbitrarily and still be inside the kernel whatever the others do (the stage index of `M₀ = kernel, M_{i+1} = {s ∈ M_i | every joint move from s stays in M_i}`).
- `is_uniform(cm, coalition, strategy: dict[int, tuple], g) -> bool | list`: whether the computed strategy assigns the same coalition move to every pair of states with the same observation for every member; returns the offending pairs otherwise.
- `pivotal(g, ending_name, actors=None, include_nature=False) -> PivotalResult(forcing: list[frozenset], blocking: list[frozenset])`: minimal coalitions (by inclusion) that can force the ending from every initial state, and minimal ones that can block it from every initial state.
- `relax_explicit(model, ending_name, max_size=2, coalition=None) -> list[list[str]]`: brute-force minimal relaxation sets over the named assumptions (section 3.1) using re-explore. With `coalition=None` the question is reachability; with a coalition it is forceability by that coalition, which is not monotone in relaxations (loosening can help either side), so only the brute-force variant answers it.
- `sensitivity(model, invariant_name, coalition) -> list[SensitivityRow]`: for each variable with a legal ±1 change of its initial value, recompute kernel membership of the initial states and the adversarial distance; rows sorted by effect.
- `cluster(traces, cm) -> list[Cluster]`: group traces by the frozenset of `(actor, action)` pairs whose guard was non-trivially satisfied along the trace (a guard that is `TRUE` does not count); each cluster has a signature and a representative shortest trace.
- `budget(cm) -> dict` and `informativeness(model, negative_controls: list[tuple[str, str, int]]) -> float`: fraction of (ending, op, n) controls satisfied, where op is one of `>=`, `==`, `<=` and compares the minimal relaxation set size with n (so "needs at least three", "needs exactly one" and "needs at most one" are all expressible).

## 8. Report (`wavefront.report`)

`render(model, g, results: dict) -> str` produces Markdown with, in order: the front-page caveat ("every result is conditional on the model version and the initial state; no bare reachability result is a finding"); the parameter budget; initial states and kernel membership per coalition; endings with forced/blocked/contested status per coalition and the shortest witness trace; minimal relaxation sets; pivotal coalitions; sensitivity table; the list of speculative actions used by any reported trace.

## 9. Evidence (`wavefront.evidence`)

`snapshots/schema.json` (JSON Schema draft 2020-12) for the snapshot format in DESIGN.md section 5.1: `date`, `model`, `variables: {name: {level, confidence, indicators: [{id, value, source, observed, rule}]}}`, `rates`. `load_snapshot(path, cm) -> tuple` maps a snapshot to an initial state (variables not in the snapshot take their declared init; a snapshot level not in the variable's levels is an error). Provenance fields are required; the loader refuses a variable with no indicator unless `confidence == "assumed"`.

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

Exit code 0 on success, 2 on `ModelError`, with the error message naming the state and construct.

## 11. Tests (`tests/`)

- `tests/model/`: DSL construction, compile errors (unknown level, observation violation, duplicate names, missing available action, conflicting Sets, ending exclusivity), effect composition, delays, latches, fairness counters, profiles, monotone checks.
- `tests/engine/`: hand-built games with known answers; brute-force cross-check of `attractor` and `safe` against enumeration of all memoryless per-state coalition strategies on random tiny models (hypothesis, at most 3 actors, 2 actions each, at most 4 variables with 2 or 3 levels, horizon at most 4); a non-determined concurrent game whose result must be `contested`; witness traces are shortest.
- `tests/bmc/`: cross-checks of section 6.
- `tests/analysis/`, `tests/report/`, `tests/evidence/`, `tests/cli/`.
- Performance smoke test: a synthetic model with about 10^5 reachable states explores in under 120 seconds (marked `slow`).

Run with `pytest -q`; lint with `ruff check .` and `ruff format --check .`; both clean is part of every gate.

## 12. Reserved for later phases

- **Multi-resolution time.** A coarse-level action may later be defined by a nested sub-game: a second compiled model whose initial state is a function of the coarse state and whose terminal states map back to coarse states. The macro-transition's successor set is then the set of coarse states the sub-game can reach, and coalition questions are lifted by computing the sub-game's attractor and safety sets. Phase 0 must not preclude this: `step`, `explore` and the solvers take a `CompiledModel` and never assume a single global model. See theory.md section 7.
- **Uniform strategy synthesis** for coalitions with hidden variables (SAT encoding of one move per observation class).
- **Unbounded fairness** (Büchi or Streett objectives) and the external cross-check against PRISM-games once the exporter exists.
- **The brute-force cross-check in section 11** enumerates per-state memoryless strategies, which is what the solvers compute.
