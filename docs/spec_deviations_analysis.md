# Deviations of the analysis layer, report and CLI from the spec

This note lists where `wavefront.analysis`, `wavefront.report` and `wavefront.cli` differ from `framework_spec.md` sections 7, 8 and 10, or settle something the spec leaves open. The spec itself is unchanged.

## Signatures

| Spec | Implemented | Reason |
|---|---|---|
| `is_uniform(cm, coalition, strategy, g) -> bool \| list` | `is_uniform(g, coalition, strategy) -> UniformityResult(uniform, conflicts)` | The graph already carries the compiled model, and a single result type avoids a return value that is either a bool or a list. `UniformityResult` is truthy exactly when the strategy is uniform. |
| `cluster(traces, cm)` | `cluster(traces, g)` | Traces hold state ids, so the graph is needed to read them; `g.model` is the compiled model. |
| `render(model, g, results: dict)` | `render(analysis)` | `run_all` returns an `Analysis` dataclass that already holds the model, the compiled model and the graph; a dict of loosely specified results would duplicate it. |
| `pivotal(g, ending_name, actors=None, include_nature=False)` | adds `initial=None` | theory.md 4.5 defines the families relative to an initial set `I₀`; per-hypothesis pivotal coalitions need it. |
| `relax_explicit(model, ending_name, max_size=2, coalition=None)` | adds `profile=None`, `initial=None`, `max_states` | The relaxed models must be compiled with the same profile as the analysed one, and with explicit initial states (a snapshot) the search should start from them. With explicit initial states, relaxing an `assume` has no effect. |
| `sensitivity(model, invariant_name, coalition)` | adds `adversary=None`, `profile=None`, `initial=None`, `max_states` | `adversary` gives the `forced` distance (spec: "the adversarial distance"); without it only `shortest` is computed, because against the complement of the coalition `forced` is always `None` inside the kernel and 0 outside it (theory.md Lemma 5). |

## Return values and semantics settled here

- `relax_explicit` returns `RelaxSets`, a `list[list[str]]` subclass with `assumptions`, `max_size`, `ill_formed` (sets whose relaxed model raised `ModelError`, with the message) and `undecided` (sets whose exploration exceeded `max_states`). Neither kind counts as a result. Supersets of ill-formed sets are still tried. Supersets of sets that worked are skipped.
- Reachability in `relax_explicit` means the ending is reached from **some** initial state, matching the bounded encoding's `Init(x^0)`. Forceability (`coalition` given) means the coalition can force the ending from **every** initial state, matching `pivotal`.
- `Distance.margin` is `None` for a state outside the kernel and `math.inf` when no play ever leaves the kernel. By the definition `M_{i+1} = {s ∈ M_i | every joint move stays in M_i}`, the margin of a kernel state equals `shortest - 1`. The implementation computes the stage index directly, and a test checks it against the literal iteration.
- `silent_phase(trace, g, coalition, invariant_name) -> SilentPhase(t_K, t_L, t_phi)` is an addition from theory.md 4.2. `t_L` uses the attractor of every actor not in the coalition, Nature included, to `¬φ`.
- `is_uniform` checks uniformity per member: for each member `a`, `a`'s component of the sub-move must agree on states with equal `cm.observe(a, s)`. `uniform` is this per-member result, and `conflicts` are `(member, s, t)` triples. The weaker check on the joint observation tuple is kept as `jointly_uniform` / `joint_conflicts`. `run_all` checks only the part of each strategy that is actually used from the initial states where the result holds (`strategy_closure`).
- `sensitivity` perturbs initial **states**. For each declared variable and each value it takes in the initial states, it moves the value one level down and one level up where legal, then compares each base state with its perturbation. With the model's own initial states, latches are recomputed for the perturbed state and perturbed states that violate an `assume` are dropped. Explicit initial states are perturbed as given. The `shortest`/`forced` columns are minima over the states concerned, with 0 for a state outside the kernel. Rows are sorted by membership flips, then by the change of `shortest`, then of `forced`. All perturbations are explored in one exploration; if that raises `ModelError` each row is explored on its own and failing rows carry the error.
- `run_all` treats `HORIZON` as an ending in timed models. For joint coalitions it also reports, per member, the forced distance out of the joint kernel when that member defects (adversary = non-members, Nature and the member; theory.md 4.3, use 1). Witnesses are the shortest plain-reachability traces from the nearest initial state. The report labels them as illustrations, not findings.
- The report adds a model fingerprint (a hash of the declarations) and states the relaxation bound, because every result is conditional on the model version.

## CLI

- Exit codes: 0 on success and 2 on `ModelError`, as specified. 1 when the model reference cannot be loaded, when the exploration budget is exceeded, or when an optional dependency (`wavefront.bmc`, `wavefront.evidence`) is missing. `argparse` usage errors also exit with 2.
- A model reference may name a function returning a `Model`, or a dotted module (`package.module:attr`). A file inside a package (directories with `__init__.py`) is imported under its package name, so relative imports work.
- Extra options: `--profile` and `--max-states` on every subcommand; `mine --coalition` (explicit forceability) and `mine --bmc` (bounded search with `wavefront.bmc.relax`; `--k` defaults to the horizon); `pivot --nature`; `report --coalition` (repeatable) and `report --max-relax`.
