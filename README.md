# wave_front

A reachability-based simulator of power relationships between strategic actors, built to study the relationship between AGI/SI and humanity.

Instead of forecasting, the project models each actor as a set of constraints and available actions, then uses game-based model checking to compute:

- which endings are reachable from a given state, and the trace that gets there;
- the *viability kernel*: the states from which a coalition can still enforce a stated balance, and the point of no return on any trajectory;
- the minimal set of assumptions each ending depends on, and which coalition is pivotal for it;
- how a state estimate built from dated, sourced snapshots drifts relative to that boundary.

Because the AGI case has no outcomes to check against, the framework is developed on the Second World War and validated on the Cold War, two episodes with different structures where outcomes, decision records, resource data and dated documents all exist. The AGI model is instantiated only after both suites pass.

Status: design stage.

- [docs/DESIGN.md](docs/DESIGN.md): evaluation of the idea, the framework, and the AGI domain model.
- [docs/ww2_testbed.md](docs/ww2_testbed.md): the WW2 model, pre-registered tests, data sources, anti-hindsight protocol.
- [docs/coldwar_testbed.md](docs/coldwar_testbed.md): the Cold War as the validation episode, with its own pre-registered claims.
- [docs/PHASES.md](docs/PHASES.md): the seven phases, each with a gate.
