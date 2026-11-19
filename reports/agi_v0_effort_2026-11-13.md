# AGI v0: effort and the cost of the ending (G29)

> Terms updated on 18 November 2026 to match docs/agi_glossary.html. Numbers and findings are unchanged.

> Every result is conditional on the model version and the initial state; no bare reachability result is a finding. The deliverables are minimal assumption sets, guarantee zone readings (inside or outside) and distance, and pivotal players; each is given with its engine.

> Nothing in this report is a forecast. Every number rests on action efforts and costs of the endings that are the owner's judgment, without a contemporaneous source ([docs/agi_effort.md](../docs/agi_effort.md)). A cheapest path cost says that a path exists; it says nothing of how likely the path is, and the model's actors do not choose by cost. The caveats of the first-run report ([agi_2026-11-12.md](agi_2026-11-12.md), front page and section 30) apply unchanged.

Model `agi_v0`, unchanged since the first run. Pre-registered claim: [docs/agi_testbed.md](../docs/agi_testbed.md) section 5, row G29, with section 6 item 12. Run procedure: [docs/agi_v0_decisions.md](../docs/agi_v0_decisions.md) section 9. Engine: the bounded checker's encoding with a cost objective (`tests/agi/effort.py`), within the search length (24 quarters) from `s₀`.

**Record of the run.** G29 was pre-registered at commit `48e5326df7ec3f0d83c732a269fa60d7cb0acf73` on 2026-11-13, after the first run, and run once from that commit in one pytest process, 2026-11-14 05:52:33 to 06:58:43 UTC (66 minutes, 72 queries, none over its 30 minutes; [agi_v0_effort_run.log](agi_v0_effort_run.log)); the tree held one untracked file (`docs/essentials_agi.md`) and no modified one. Parts: the G29 rows of [agi_v0_collapse_parts.jsonl](agi_v0_collapse_parts.jsonl), 22 rows: 3 did not hold, 1 not computed, 18 reported.

**Result: G29 did not hold. None of (a), (b), (c) held; (d) is not yet testable.**

## 1. Glossary (terms added to those of [agi_v0_collapse_2026-11-13.md](agi_v0_collapse_2026-11-13.md) section 1)

| Term | Meaning |
|---|---|
| Action effort | What an action costs its actor to take in one quarter, against what its incentives already push it to do, on a scale of 0 (the default) to 3 (an exceptional decision). |
| Alarm | The frontier AI system is suspected or known, or opinion is in backlash. Under alarm a government's `idle` costs 2 and the actions that answer the alarm cost one point less. |
| Effort of a path | The sum of the scored actors' action efforts over the rounds before the target is first reached. |
| Cheapest path cost | The smallest effort of the named actors over all paths of at most 24 quarters from `s₀` that reach the target. The cheapest path cost of the draft, where it is called the slide cost. |
| Payers | The actors whose effort is being minimised: `H` with `L`, `H`, `L`, or `A`. Each is a separate search and may find a different path. |
| Cost of the ending | What an ending costs the actor who lives with it. |
| Total cost | An actor's effort on a path plus the cost of its ending. |
| Prevention cost | The least effort that guarantees an ending never happens, whatever the others do. Not computable yet. |
| Within the search length | Within 24 quarters. An ending that needs longer reads unreachable within the search length; `COEXIST` exists only at quarter 56 and is not costed. |

## 2. The pre-registered parts

| Part | Predicted result | Result |
|---|---|---|
| (a) | the cheapest path cost of `H` and `L` to `SILENT_TAKEOVER` is 0 under every goal that can reach it | **did not hold**: 0 under `indifferent`, 2 under `self_preserving`; unreachable within the search length under `truth_seeking` |
| (b) | the cheapest path cost of `H` to `CONTAINED` is 2 (the owner's) | **did not hold**: 6 under every non-aligned goal |
| (c) | `A`'s cheapest path cost to `SILENT_TAKEOVER` is lower under `indifferent` than under `self_preserving` | **did not hold**: 11 under `indifferent`, 7 under `self_preserving` |
| (d) | for `H`, preventing `SILENT_TAKEOVER` costs 1 less in total than sliding into it (the owner's) | not yet testable |

**(a).** Against an `indifferent` frontier AI system, governments with the frontier AI companies reach silent takeover in 7 quarters on defaults alone. Against a `self_preserving` one they cannot: the AI acquires only once the human-AI relation is hostile, and on the cheapest path that takes 2 points of government effort. Which government action carries the 2 is in the path of the parts log.

**(b).** The drafting session's recorded predicted result held: AI contained needs treaty-backed regulation, so two rounds of `propose_treaty` at 2 and a `shutdown_attempt` at its alarm price of 2. The frontier AI companies' cheapest path cost to AI contained is 0.

**(c).** The order is the reverse of the predicted result, and the action efforts explain it more than the goals do: the model gives `A` no action but `stand_by` below AGI, and `stand_by` costs an `indifferent` frontier AI system 2 a quarter and a `self_preserving` one 0. The 11 is mostly waiting for the AGI breakthrough. Read as pre-registered the part did not hold; whether forced waiting should be charged is a question for the owner (section 5).

## 3. Cheapest path cost by ending (reported)

Each cell is a separate search. "none" means unreachable within the search length (24 quarters).

| Ending | Goal | `H` with `L` | `H` | `L` | `A` | Quarters of the `H` with `L` path |
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

What the table shows, on these action efforts and within this search length:

1. **Disempowerment is the free ending under every goal.** In 6 quarters, governments and frontier AI companies on defaults alone reach living on AI with no oversight. It needs no hostile act by the frontier AI system.
2. **The frontier AI companies never have to spend anything.** Their cheapest path cost is 0 to every reachable ending.
3. **AI contained is the only ending that costs governments in every case,** and it costs 6.
4. **Against an `indifferent` frontier AI system every bad ending is free for governments with the frontier AI companies;** against a `self_preserving` one the takeovers and the stalemate cost governments 2.

## 4. Total cost on the cheapest path of `H` with `L` (reported)

Effort on that path, plus the cost of the ending, per actor.

| Ending | Goal | `H` | `L` | `A` |
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

For governments, AI contained at 10 in total is no dearer than silent takeover at 10 to 12, and dearer than disempowerment at 8 and than stalemate at 4 to 6 where those are reached cheaply. For the frontier AI companies, disempowerment at 2 is the cheapest ending of all. These are comparisons of cheapest paths, not of what each side can guarantee.

## 5. What these results rest on, and proposals for the owner (proposals only)

- **The action efforts.** Every number above moves with them. The action effort change run (each action effort moved by one) was left out of G29 and is the first follow-up.
- **The search length.** 24 quarters. `COEXIST` is not costed.
- **Existence, not guarantee.** A cheapest path cost of 0 means some path gets there for free, with the other actors and chance going along. The prevention cost, which is the owner's predicted result (d), needs a cost-bounded guarantee zone.

1. **Forced waiting.** Whether `stand_by` below AGI, where `A` has no other action, should cost anything. It decides (c). (Ruled by the owner: it costs nothing. Section 6.)
2. **The cost of the disempowerment ending.** It is the free ending and the frontier AI companies' cheapest; at 2 for the companies it is nearly costless to them. Whether that is intended.
3. **The cost-bounded guarantee zone,** for predicted result (d).
4. **The action effort change run.** (Done: section 7.)

## 6. G29a: part (c) with the forced wait free (held)

After the result above the owner ruled that below AGI, where `A` has no action but `stand_by`, the wait costs it nothing under any goal. That is G29's one amendment (agi_testbed.md section 6 item 2). G29's results above stand as computed; G29a was pre-registered at commit `fc1eea96264e2c7995b02a7b747cd4c37439d589` and run once from it, 2026-11-14 07:49:59 to 08:01:43 UTC, 18 queries.

**(c) Held:** `A`'s cheapest path cost to `SILENT_TAKEOVER` is 3 under `indifferent` and 7 under `self_preserving`. Under the original wording it was 11 against 7 and did not hold; validity.md's rule applies: both wordings are reported, and the one that held is the amended one.

`A`'s cheapest path cost to each ending under the amended action efforts (reported):

| Ending | `self_preserving` | `truth_seeking` | `indifferent` |
|---|---|---|---|
| `DISEMPOWERMENT` | 0 | 1 | 1 |
| `CONTAINED` | 1 | 3 | 2 |
| `STALEMATE` | 3 | 3 | 3 |
| `SILENT_TAKEOVER` | 7 | none | 3 |
| `OVERT_TAKEOVER` | 6 | none | 3 |
| `EXTINCTION` | none | none | 7 |

No action effort of `H` or `L` changed, so parts (a) and (b) and every `H` and `L` column of sections 3 and 4 are unaffected. The `A` columns of sections 3 and 4 are those of G29 and charge the wait.

## 7. Action effort changes (a diagnostic after the run, not a claim)

Each action effort moved by one in each direction, one at a time, on the amended action efforts, and G29's three pre-registered quantities searched again: 176 searches, [agi_v0_effort_sensitivity.json](agi_v0_effort_sensitivity.json). Of 169 action effort changes, 39 change a quantity and **one changes a verdict**.

| Part | Base | What moves it | Verdict |
|---|---|---|---|
| (a) `H` with `L` to `SILENT_TAKEOVER` | 2 (`self_preserving`), 0 (`indifferent`) | raising `H.idle`, `L.race`, `L.deploy_agents` or `L.scale` makes the free path cost 1 to 5; `H.shutdown_attempt` moves the 2 to 1 or 3 | did not hold, under every action effort change |
| (b) `H` to `CONTAINED` | 6 | `H.propose_treaty` (4 or 8), `H.shutdown_attempt` (5 or 7), `H.idle` raised (8) | did not hold, under every action effort change; never below 4 |
| (c) `A` to `SILENT_TAKEOVER` | 7 against 3 | several of `A`'s action efforts move one side by 1 to 4 | held, except with `indifferent`'s `stand_by` raised by one (7 against 7) |

**The zero of disempowerment.** A second diagnostic raised each action effort of `H` and `L` by one and searched the cheapest path cost to `DISEMPOWERMENT` again (`python -m tests.agi.effort_sensitivity_ending`, under `self_preserving`; [agi_v0_effort_sensitivity_disempowerment.json](agi_v0_effort_sensitivity_disempowerment.json)). The path stays 6 quarters long and its cost rests on four action efforts:

| Action effort raised by one | Cheapest path cost of `H` with `L` |
|---|---|
| none (base) | 0 |
| `H.idle` | 4 |
| `L.deploy_agents` | 3 |
| `L.race` | 2 |
| `L.scale` | 1 |
| any of the other fifteen | 0 |

So "free" is exactly the statement that governments doing nothing without alarm, and the frontier AI companies in a peer race, deploying AI agents and scaling up, each cost nothing. Those four zeros are the owner's rulings. One point on any of them makes the path cost something; none of them closes it. The length of six quarters does not move with the action efforts: it comes from the model, which carries no deployment delay (docs/ontology_agi.md, lags not carried), and is not a credible date.

