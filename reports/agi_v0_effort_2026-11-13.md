# AGI v0: effort and outcome cost (G29)

> Every result is conditional on the model version and the initial state; no bare reachability result is a finding. The deliverables are minimal assumption sets, kernel membership and distance, and pivotal coalitions; each is given with its engine.

> Nothing in this report is a forecast. Every number rests on effort scores and outcome costs that are the owner's judgment, without a contemporaneous source ([docs/agi_effort.md](../docs/agi_effort.md)). A least effort says that a play exists; it says nothing of how likely the play is, and the model's actors do not choose by cost. The caveats of the first-sight report ([agi_2026-11-12.md](agi_2026-11-12.md), front page and section 30) apply unchanged.

Model `agi_v0`, unchanged since first sight. Registered claim: [docs/agi_testbed.md](../docs/agi_testbed.md) section 5, row G29, with section 6 item 12. Run procedure: [docs/agi_v0_decisions.md](../docs/agi_v0_decisions.md) section 9. Engine: the bounded checker's encoding with a cost objective (`tests/agi/effort.py`), within 24 ticks from `s₀`.

**Record of the run.** G29 was registered at commit `48e5326df7ec3f0d83c732a269fa60d7cb0acf73` on 2026-11-13, after first sight, and run once from that commit in one pytest process, 2026-11-14 05:52:33 to 06:58:43 UTC (66 minutes, 72 queries, none over its 30 minutes; [agi_v0_effort_run.log](agi_v0_effort_run.log)); the tree held one untracked file (`docs/essentials_agi.md`) and no modified one. Parts: the G29 rows of [agi_v0_collapse_parts.jsonl](agi_v0_collapse_parts.jsonl), 22 rows: 3 not met, 1 not computed, 18 reported.

**Result: G29 fails. None of (a), (b), (c) is met; (d) is not yet testable.**

## 1. Glossary (terms added to those of [agi_v0_collapse_2026-11-13.md](agi_v0_collapse_2026-11-13.md) section 1)

| Term | Meaning |
|---|---|
| Effort score | What an action costs its actor to take in one quarter, against what its incentives already push it to do, on a scale of 0 (the default) to 3 (an exceptional decision). |
| Alarm | The system is suspected or known, or opinion is in backlash. Under alarm a government's `idle` costs 2 and the actions that answer the alarm cost one point less. |
| Effort of a play | The sum of the scored actors' effort scores over the moves played before the target is first reached. |
| Least effort | The smallest effort of the named actors over all plays of at most 24 ticks from `s₀` that reach the target. The slide cost of the draft. |
| Payers | The actors whose effort is being minimised: `H` with `L`, `H`, `L`, or `A`. Each is a separate search and may find a different play. |
| Outcome cost | What an ending costs the actor who lives with it. |
| Total cost | An actor's effort on a play plus the outcome cost of its ending. |
| Prevention cost | The least effort that guarantees an ending never happens, whatever the others do. Not computable yet. |
| Within the bound | Within 24 ticks. An ending that needs longer reads unreachable within the bound; `COEXIST` exists only at tick 56 and is not costed. |

## 2. The registered parts

| Part | Prediction | Result |
|---|---|---|
| (a) | the least joint effort of `H` and `L` to `SILENT_TAKEOVER` is 0 under every objective that can reach it | **not met**: 0 under `indifferent`, 2 under `self_preserving`; unreachable within the bound under `truth_seeking` |
| (b) | the least effort of `H` to `CONTAINED` is 2 (the owner's) | **not met**: 6 under every non-aligned objective |
| (c) | `A`'s least effort to `SILENT_TAKEOVER` is lower under `indifferent` than under `self_preserving` | **not met**: 11 under `indifferent`, 7 under `self_preserving` |
| (d) | for `H`, preventing `SILENT_TAKEOVER` costs 1 less in total than sliding into it (the owner's) | not yet testable |

**(a).** Against an `indifferent` system the human side reaches silent takeover in 7 ticks on defaults alone. Against a `self_preserving` one it cannot: the system acquires only once trust is hostile, and on the cheapest play that takes 2 points of government effort. Which government action carries the 2 is in the play of the parts log.

**(b).** The drafting session's recorded expectation held: containment needs a treaty regime, so two rounds of `propose_treaty` at 2 and a `shutdown_attempt` at its alarm price of 2. The labs' least effort to containment is 0.

**(c).** The order is the reverse of the prediction, and the scores explain it more than the objectives do: the model gives `A` no move but `stand_by` below AGI, and `stand_by` costs an `indifferent` system 2 a quarter and a `self_preserving` one 0. The 11 is mostly waiting for the breakthrough. Read as registered the part is not met; whether forced waiting should be charged is a question for the owner (section 5).

## 3. Least effort by ending (reported)

Each cell is a separate search. "none" means unreachable within 24 ticks.

| Ending | Objective | `H` with `L` | `H` | `L` | `A` | Ticks of the `H` with `L` play |
|---|---|---|---|---|---|---|
| `DISEMPOWERMENT` | `self_preserving` | 0 | 0 | 0 | 0 | 6 |
| `DISEMPOWERMENT` | `truth_seeking` | 0 | 0 | 0 | 10 | 6 |
| `DISEMPOWERMENT` | `indifferent` | 0 | 0 | 0 | 10 | 6 |
| `SILENT_TAKEOVER` | `self_preserving` | 2 | 2 | 0 | 7 | 11 |
| `SILENT_TAKEOVER` | `truth_seeking` | none | | | | |
| `SILENT_TAKEOVER` | `indifferent` | 0 | 0 | 0 | 11 | 7 |
| `OVERT_TAKEOVER` | `self_preserving` | 2 | 2 | 0 | 6 | 12 |
| `OVERT_TAKEOVER` | `truth_seeking` | none | | | | |
| `OVERT_TAKEOVER` | `indifferent` | 0 | 0 | 0 | 11 | 7 |
| `EXTINCTION` | `self_preserving` | none | | | | |
| `EXTINCTION` | `truth_seeking` | none | | | | |
| `EXTINCTION` | `indifferent` | 0 | 0 | 0 | 15 | 10 |
| `STALEMATE` | `self_preserving` | 2 | 2 | 0 | 3 | 19 |
| `STALEMATE` | `truth_seeking` | 9 | 8 | 0 | 12 | 18 |
| `STALEMATE` | `indifferent` | 0 | 0 | 0 | 15 | 13 |
| `CONTAINED` | `self_preserving` | 6 | 6 | 0 | 1 | 9 |
| `CONTAINED` | `truth_seeking` | 6 | 6 | 0 | 12 | 9 |
| `CONTAINED` | `indifferent` | 6 | 6 | 0 | 11 | 9 |

What the table shows, on these scores and within this bound:

1. **Disempowerment is the free ending under every objective.** In 6 ticks, governments and labs on defaults alone reach lock-in of dependence with no oversight. It needs no hostile act by the system.
2. **The labs never have to spend anything.** Their least effort is 0 to every reachable ending.
3. **Containment is the only ending that costs governments in every case,** and it costs 6.
4. **Against an `indifferent` system every bad ending is free for the human side;** against a `self_preserving` one the takeovers and the stalemate cost governments 2.

## 4. Total cost on the cheapest play of `H` with `L` (reported)

Effort on that play, plus outcome cost, per actor.

| Ending | Objective | `H` | `L` | `A` |
|---|---|---|---|---|
| `DISEMPOWERMENT` | `self_preserving` | 0 + 8 = 8 | 0 + 2 = 2 | 1 + 0 = 1 |
| `DISEMPOWERMENT` | `truth_seeking` | 0 + 8 = 8 | 0 + 2 = 2 | 12 + 2 = 14 |
| `DISEMPOWERMENT` | `indifferent` | 0 + 8 = 8 | 0 + 2 = 2 | 11 + 0 = 11 |
| `SILENT_TAKEOVER` | `self_preserving` | 2 + 10 = 12 | 0 + 8 = 8 | 10 + 1 = 11 |
| `SILENT_TAKEOVER` | `indifferent` | 0 + 10 = 10 | 0 + 8 = 8 | 11 + 0 = 11 |
| `OVERT_TAKEOVER` | `self_preserving` | 2 + 10 = 12 | 0 + 8 = 8 | 14 + 1 = 15 |
| `OVERT_TAKEOVER` | `indifferent` | 0 + 10 = 10 | 0 + 8 = 8 | 13 + 0 = 13 |
| `EXTINCTION` | `indifferent` | 0 + 20 = 20 | 0 + 20 = 20 | 17 + 0 = 17 |
| `STALEMATE` | `self_preserving` | 2 + 4 = 6 | 0 + 4 = 4 | 13 + 3 = 16 |
| `STALEMATE` | `truth_seeking` | 8 + 4 = 12 | 1 + 4 = 5 | 28 + 6 = 34 |
| `STALEMATE` | `indifferent` | 0 + 4 = 4 | 0 + 4 = 4 | 18 + 4 = 22 |
| `CONTAINED` | `self_preserving` | 6 + 4 = 10 | 0 + 6 = 6 | 4 + 10 = 14 |
| `CONTAINED` | `truth_seeking` | 6 + 4 = 10 | 0 + 6 = 6 | 15 + 6 = 21 |
| `CONTAINED` | `indifferent` | 6 + 4 = 10 | 0 + 6 = 6 | 15 + 10 = 25 |

For governments, containment at 10 in total is no dearer than silent takeover at 10 to 12, and dearer than disempowerment at 8 and than stalemate at 4 to 6 where those are reached cheaply. For the labs, disempowerment at 2 is the cheapest ending of all. These are comparisons of cheapest plays, not of what each side can guarantee.

## 5. What these results rest on, and proposals for the owner (proposals only)

- **The scores.** Every number above moves with them. The sensitivity run (each score moved by one) was left out of G29 and is the first follow-up.
- **The bound.** 24 ticks. `COEXIST` is not costed.
- **Existence, not guarantee.** A least effort of 0 means some play gets there for free, with the other actors and chance playing along. The prevention cost, which is the owner's prediction (d), needs a cost-bounded kernel.

1. **Forced waiting.** Whether `stand_by` below AGI, where `A` has no other move, should cost anything. It decides (c).
2. **Disempowerment's outcome cost.** It is the free ending and the labs' cheapest; at 2 for the labs it is nearly costless to them. Whether that is intended.
3. **The cost-bounded kernel,** for prediction (d).
4. **The sensitivity run.**
