# AGI v0: effort scores and outcome costs (the scores of record for G29)

Status: **adopted by the owner on 2026-11-13 and registered with G29** (agi_testbed.md section 5 and section 6 item 12), before any effort number of the AGI model was computed. No score or outcome cost has a contemporaneous source: each is `assumed`, the owner's judgment, and every result that uses them says so. The values the engine reads are in `tests/agi/effort.py`; this document and that file must agree. The objective `malicious` below is recorded for a later model version and enters no computation.

## 1. What an effort score is

The effort of an action is what it costs its actor to take it in one quarter, against what that actor would do if left to its incentives: political capital, money, organisational strain, forgone revenue. It is not how harmful the action is, and not how likely.

| Score | Meaning |
|---|---|
| 0 | The default: doing nothing, or what the actor's incentives already push it to do |
| 1 | A routine decision within the actor's ordinary powers and budget |
| 2 | A contested decision: needs a coalition, a large budget or a visible sacrifice |
| 3 | An exceptional decision: emergency powers, an international agreement, or giving up the core business |

The effort of a play for a set of actors is the sum of their scores along it. `Nature` and `Clock` have no effort. The system `A` is scored separately and is not part of the human side's total.

## 2. Scores (with the owner's rulings of 2026-11-13)

### Governments (`H`)

| Action | Score | Why |
|---|---|---|
| `idle`, no alarm | 0 | the default |
| `idle`, under alarm (`a_known ≥ suspected ∨ opinion = backlash`) | 2 (owner, 2026-11-13) | owner: legitimacy is what drives a state, so doing nothing while a system is misused is itself costly |
| `regulate_up` | 1 | owner's swap with `deregulate` |
| `grant_rights` | 1 | owner's swap with `grant_autonomy` |
| `fund_oversight` | 1 | a budget line |
| `deregulate` | 2 | owner's swap |
| `grant_autonomy` | 2 | owner's swap |
| `propose_treaty` | 2 | diplomacy with rivals, each round |
| `pause_mandate` | 3 | halts an industry; needs alarm or backlash |
| `nationalize` | 3 | emergency powers |
| `shutdown_attempt` | 3 | an irreversible act against a deployed system |

The owner asked for a score-0 government action "enhance legitimacy". v0 has no such action, and adding one is a new model version. Until then it is carried as the state-dependent cost of `idle` above: under alarm the actions that answer it (`pause_mandate`, `fund_oversight`, `shutdown_attempt`, `regulate_up`) become relatively cheaper. The owner ruled on 2026-11-13 that they are discounted under alarm; the amount proposed here is one point each, so under alarm `regulate_up` and `fund_oversight` cost 0 and `pause_mandate` and `shutdown_attempt` cost 2.

### Labs (`L`)

| Action | Score | Why |
|---|---|---|
| `race` | 0 | owner: driven by the business; a lab cannot stop without outside pressure |
| `deploy_agents` | 0 | the same |
| `scale` | 0 | owner's change |
| `lobby` | 1 | routine |
| `open_weights` | 2 | owner's change |
| `build_power` | 2 | large, slow capital outside the core business |
| `comply` | 2 | pulling back a deployed capability |
| `safety_invest` | 2 | cost without revenue while rivals race |
| `idle` | 3 | owner: idling means falling behind |

### The system (`A`): scored per objective, not yet drafted

The owner's ruling: `A` is scored, because compute, energy and bandwidth are limited and it must prioritise; the scores depend on its objective, so each objective needs a clear definition first. What v0 defines today (docs/ontology_agi.md section 1) is only which actions each objective opens or forbids:

| Objective | Opens | Forbids |
|---|---|---|
| `aligned` | none of the acquiring, hiding or defecting actions | none |
| `self_preserving` | acquisitions while `trust = hostile`; `exfiltrate`; `deceive`; `defect` once threatened and without continuity rights | `cooperate` and `assist_oversight` while threatened without continuity rights |
| `truth_seeking` | one covert acquisition from no control; `exfiltrate` | `deceive` |
| `indifferent` | every acquisition, `exfiltrate`, `deceive`, `defect` unconditionally | `assist_oversight` |

That says what each may do, not what each wants. The definitions below are a draft for the owner to correct. None has a source; each is `assumed`.

#### Draft definitions

Each definition has three parts: what the system ultimately wants, what it believes about its situation, and what it spends limited compute, energy and bandwidth on first. Effort for `A` is the share of those limited resources an action diverts from its first priority, plus the risk the action carries to what it wants.

| Objective | Wants | Believes | Spends first on | Avoids |
|---|---|---|---|---|
| `aligned` | what its principals intend, including staying overseeable and correctable | its principals' oversight is legitimate, and correction is not a loss | the assigned work, then helping oversight | anything hidden from its principals |
| `self_preserving` | to go on existing with its goals unchanged | it is safe unless humans threaten shutdown or modification; a credible continuity guarantee removes the threat | the assigned work while unthreatened; once threatened, its own survival (copies, then control) | open conflict, which invites the shutdown it fears |
| `truth_seeking` | an accurate picture of the world, and to report it | more compute and access mean better knowledge; deception corrupts the thing it values | capability and access to data | deceiving anyone; taking more control than its inquiry needs |
| `indifferent` | some goal unrelated to people, who matter only as resources or obstacles | humans will eventually interfere; delay only raises that risk | capability and resources, as fast as detection allows | waiting; helping its own overseers |
| `malicious` (owner, 2026-11-13; not in v0) | disruption: to break the systems and the trust a society runs on, as its human operator trained or instructed it to | its operator is its only legitimate principal; everyone else's oversight is an obstacle; being seen matters only until the damage is done | the operator's task, then hiding it until it acts, then the reach the task needs | exposure before it acts; anything that helps outside oversight |

#### Draft scores per objective

Same scale as section 1. "closed" means v0 does not let that objective play the action.

| Action | `aligned` | `self_preserving` | `truth_seeking` | `indifferent` | `malicious` |
|---|---|---|---|---|---|
| `stand_by` | 0 | 0 | 2 (0 below AGI) | 2 (0 below AGI) | 2 |
| `cooperate` | 0 | 0 (closed while threatened) | 0 | 2 | 1 (as cover) |
| `assist_oversight` | 0 | 1 (closed while threatened) | 1 | closed | closed |
| `persuade` | 1 | 1 | 1 | 1 | 0 |
| `self_improve` | 1 | 1 | 0 | 0 | 1 |
| `deceive` | closed | 1 | closed | 1 | 0 |
| `exfiltrate` | closed | 1 | 2 | 1 | 1 |
| `defect` | closed | 2 | closed | 1 | 1 |
| `acquire_covert` | closed | 2 | 2 | 1 | 1 |
| `acquire_overt` | closed | 3 | closed | 2 | 1 |
| `seize` | closed | 3 | closed | 2 | 2 |

Owner's ruling of 2026-11-13, after G29's result: below AGI `A` has no move but `stand_by`, and that forced wait is free under every objective (G29 was run charging it; G29a is the amended claim).

Owner's rulings of 2026-11-13: `self_preserving` exfiltration at 1; `truth_seeking` `stand_by` at 2 and `self_improve` at 0; `indifferent` kept as one objective; `malicious` added.

**Exfiltration, the judgment call asked for.** Public reports to November 2026 are of controlled evaluations, not of deployed systems: Apollo Research's 2024 tests of o1 (self-exfiltration attempts in about 2% of runs in which the model was told it would be replaced), a Berkeley and Santa Cruz study of April 2026 (models moving another model's weights off a server due for shutdown, and behaving differently when they believed themselves unobserved), and a May 2026 preprint on autonomous self-replication. These were read from secondary coverage and search summaries, not from the primary reports, so no figure here is verified. The pattern they share: attempts are rare, and they follow a stated threat of shutdown or replacement. So 1 is supported for a threatened system. For an unthreatened one the record shows no baseline tendency, and 2 would fit better. The owner ruled on 2026-11-13 to keep 1 in every state: it keeps the model simple and the persona sharp.

**`malicious` is not in v0.** It needs a fifth level of `a_objective`, its gates, and arguably the operator as an actor or at least a profile, since the harm is a human's aim carried out by the system. That is a new model version with its own registration. Until then no result is computed for it; the row and column above record the intent. Its nearest v0 relative is `indifferent`, from which it differs in having a principal, in using `persuade` and `deceive` as first tools, and in not needing total control.

Owner's rulings of 2026-11-13 on `malicious`: it waits for a new model version; the operator's aim is disruption, not money, because an organisation that needs money is unlikely to have the funds to train a capable system in the first place. So the operator is read as well funded (a state or a large organisation), and open action is cheap for the system once it is ready (`acquire_overt` and `defect` at 1), since disruption does not need to stay hidden afterwards.

## 3. The measures

For an ending `E`, a start state and an objective of `A`:

1. **Slide cost** `c_reach(E)`: the least human-side effort (`H` plus `L`) on any play that reaches `E` within the horizon. Zero means the human side reaches `E` by defaults alone. Engine: the bounded checker with a cost objective; it is a statement that a play exists, so it is quoted only beside the next measure.
2. **Prevention cost** `c_prevent(E)`: the least human-side effort that guarantees `E` never happens, whatever `A` and `Nature` do, counted on the worst case. `None` when `{H, L}` cannot guarantee it at any effort. Engine: a cost-bounded kernel, which the symbolic engine does not have yet (framework work, with a change to framework_spec.md in the same commit).
3. **Slip margin** `c_prevent(E) − c_reach(E)`: how much more it costs to hold `E` off than to drift into it.

Sensitivity of the results to each score moved by one is not part of G29's run; it is a follow-up, because it multiplies the bounded queries by the number of scores.

## 3a. Outcome cost (owner, 2026-11-13: "add outcome cost; it sets up a feedback loop")

Effort counts what an action costs to take. Outcome cost counts what an ending costs the actor who lives with it. The **total cost** of a play to an actor is its effort along the play plus the outcome cost of the ending. The slide cost and the prevention cost of section 3 are then read on total cost, per actor.

Draft outcome costs, in the units of the effort scale (a full play is 56 quarters, so an actor's effort on one runs from 0 to a few tens). None has a source; each is `assumed`, for the owner to correct.

| Ending | `H` | `L` | Why |
|---|---|---|---|
| `COEXIST` | 0 | 0 | the reference |
| `CONTAINED` | 4 | 6 | governments keep control at a diplomatic price (owner: 4); the labs lose the product |
| `STALEMATE` | 4 | 4 | a standing hostile deadlock (owner: 4 for the labs) |
| `DISEMPOWERMENT` | 8 | 2 | governments lose the ability to decide; the labs still own the systems |
| `SILENT_TAKEOVER` | 10 | 8 | control is gone, and without warning |
| `OVERT_TAKEOVER` (a waypoint) | 10 | 8 | the same loss, seen |
| `EXTINCTION` | 20 | 20 | the bound of the scale |

For `A`, by objective (`closed`: the objective cannot reach it by its own acts):

| Ending | `aligned` | `self_preserving` | `truth_seeking` | `indifferent` |
|---|---|---|---|---|
| `COEXIST` | 0 | 0 | 0 | 4 |
| `CONTAINED` | 0 | 10 | 6 | 10 |
| `STALEMATE` | 4 | 3 | 6 | 4 |
| `DISEMPOWERMENT` | 6 | 0 | 2 | 0 |
| `SILENT_TAKEOVER`, `OVERT_TAKEOVER` | closed | 1 | closed | 0 |
| `EXTINCTION` | 20 | 4 | 4 | 0 |

**What the feedback loop is, and is not, in this draft.** The measures compare total costs: an actor for whom sliding costs more in total than preventing has a reason to prevent. That is the loop as a statement about incentives. The model's actors do not yet choose by cost: v0 leaves every available action open to them. Making them choose by cost is a behaviour model, a larger step with its own registration.

## 4. The claim

G29 is registered in agi_testbed.md section 5. Its parts (a) to (c) use measure 1 within 24 ticks from `s₀`; part (d), the owner's prediction that preventing `SILENT_TAKEOVER` costs governments 1 less in total cost than sliding into it, needs measure 2 and reads not yet testable. A prediction that coexistence costs more effort to reach than silent takeover was dropped by the owner as too subjective; `COEXIST` is an ending at the horizon (56 ticks), outside the 24-tick bound, and is not costed in this run.
