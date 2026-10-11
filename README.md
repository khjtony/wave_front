# wave_front

A reachability-based simulator of the power relationship between AGI/SI and humanity.

Instead of forecasting, the project models each actor (human coalition, frontier labs, an AGI with a hidden objective, nature) as a set of constraints and available actions, then uses game-based model checking to compute:

- which endings are reachable from the current real-world state, and the trace that gets there;
- the *viability kernel*: the states from which humans can still enforce a stated balance, and the point of no return on any trajectory;
- the minimal set of assumptions each ending depends on, and which coalition is pivotal for it;
- how the current state estimate, built from dated and sourced snapshots of news and policy, drifts relative to that boundary.

Status: design stage. Read [docs/DESIGN.md](docs/DESIGN.md).
