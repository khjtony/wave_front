# wave_front

A reachability-based simulator of power relationships between strategic actors, built to study the relationship between AGI/SI and humanity.

Instead of forecasting, the project models each actor as a set of constraints and available actions, then uses game-based model checking to compute:

- which endings are reachable from a given state, and the trace that gets there;
- the *viability kernel*: the states from which a coalition can still enforce a stated balance, and the point of no return on any trajectory;
- the minimal set of assumptions each ending depends on, and which coalition is pivotal for it;
- how a state estimate built from dated, sourced snapshots drifts relative to that boundary.

Because the AGI case has no outcomes to check against, the framework is developed on the Second World War and validated on the Cold War, two episodes with different structures where outcomes, decision records, resource data and dated documents all exist. The plan was to instantiate the AGI model only after both suites passed; the Cold War suite did not, and the status below says on what basis the AGI model was built.

Status (2026-11-12): phases 0 and 1 passed their gates and the phase 2 work is built: the framework core, the bounded and symbolic engines (with a compiled BDD core), WW2 v0 and v1, the summer-1939 and July 1914 crisis models, and the replay harness run blind on real FRUS documents. Phase 2 passed on 2026-10-28 under the owner's amendments ([docs/PHASES.md](docs/PHASES.md)). Phase 3 (the Cold War) did not pass its suite: C1, C12 and C13 pass and C2 to C11 fail ([reports/cw_v0.md](reports/cw_v0.md)); it was closed on 2026-11-09 on its gate's second clause, with every failure explained and none attributed to the engine. The AGI model went ahead on that basis, by the owner's decision. AGI v0 was run once, at first sight, on 2026-11-12: of the claims G1 to G25, registered before any AGI guard, 1 passed, 17 failed and 7 were skipped ([reports/agi_2026-11-12.md](reports/agi_2026-11-12.md)). The failures stand. No AGI mechanism is validated and nothing in the report is a forecast ([docs/validity.md](docs/validity.md) section 6.1).

Try it on the example model:

```
pip install -e '.[dev,bmc]'
pip install -e '.[fast]' && python -m wavefront.symbolic._core.build   # optional: the compiled BDD core
wf report models/toy/two_power.py --out reports/toy_report.md
wf viz models/toy/two_power.py --out reports/toy_viz.html   # open in a browser
```

- [docs/HANDOFF.md](docs/HANDOFF.md): start here in a new session: setup, rules, where things stand, what waits on the owner.
- [docs/DESIGN.md](docs/DESIGN.md): evaluation of the idea, the framework, and the AGI domain model.
- [docs/ww2_testbed.md](docs/ww2_testbed.md): the WW2 model, pre-registered tests, data sources, anti-hindsight protocol.
- [docs/coldwar_testbed.md](docs/coldwar_testbed.md): the Cold War as the validation episode, with its own pre-registered claims.
- [docs/agi_testbed.md](docs/agi_testbed.md): the AGI model's claims G1 to G25, registered before any AGI guard, with the three balance predicates and the protocol for the AGI runs.
- [docs/review_2026-10-17.md](docs/review_2026-10-17.md): the review of status and roadmap against the project's goal.
- [docs/PHASES.md](docs/PHASES.md): the seven phases, each with a gate.
- [docs/PLAN.md](docs/PLAN.md): the steps inside each phase, with acceptance checks and owners.
- [docs/framework_spec.md](docs/framework_spec.md): the contract the `wavefront` package implements.
- [docs/visualizer.md](docs/visualizer.md): the trace visualizer: initial state, decisions, divergence, the viability boundary.
