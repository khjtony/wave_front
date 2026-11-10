# AGI v0 ontology: variables, levels, thresholds, actions, endings

Status: written on 2026-11-10 for the model step, after the registration of G1 to G22 ([agi_testbed.md](agi_testbed.md), 2026-10-17 and after) and of G23 to G25 (2026-11-09), and before any registered claim was run. Model: `models/agi/v0.py`. Dated start state: `snapshots/agi/2026-11-09.json`, with its indicators and mapping rules in [indicators.md](indicators.md). The readings of the claims, the engines and the budgets are in [agi_v0_decisions.md](agi_v0_decisions.md); guard edits are logged in [guard_changelog_agi.md](guard_changelog_agi.md).

Standards as for the historical ontologies: every level is an observable condition with a threshold rule and a dated indicator; a reference names a document with its date, never an invented page; "(not verified)" marks a date or a figure recalled and not checked against the document. No document was retrieved in the build environment: every indicator of the snapshot is written from recall of the cited document, the latest observation is dated 2025, and the snapshot is therefore a proposal for the owner's review, not a reading (agi_testbed.md section 6 item 7: judgment calls are the owner's). The seven levels on which the recalled record does not decide are carried as set-valued levels (owner's decision 9e), not settled here.

What this model is not: its guards, levels, action sets and balances are hypotheses no historical episode tests ([validity.md](validity.md) section 6). Section 8 tags every mechanism `validated:ww2`, `validated:cw` or `untested`; a `validated` tag says that the structural form of the mechanism was exercised in that episode, not that its AGI content is right.

## 0. Scope and time

- One tick is one quarter; **the state at tick t is the start of quarter 2026Q4 + t**; the joint move at tick t is what each actor decided during that quarter; its effects are visible at t + 1. Tick 0 is 2026Q4; the horizon, tick 56, is the start of 2040Q4.
- Quarter to tick: `tick = 4 × (year − 2026) + (quarter − 4)`. 2027Q4 = 4, 2028Q4 = 8, 2030Q4 = 16, 2032Q4 = 24, 2036Q4 = 40.
- Actors: `H` (states and public opinion, aggregated), `L` (frontier developers, aggregated), `A` (one AGI or SI system), Nature, and a record keeper `Clock` with one action, which writes the state facts and adds no move to the game. `H`'s `do_nothing` and `L`'s null move are the built-in `idle`; `A` has no built-in idle and `stand_by` is its null move; Nature's `none` is its built-in idle.
- `A` has no action other than `stand_by` before `cap ≥ agi` (every other `A` guard has the part `cap`). Most claims are therefore asked from `s₀[cap := agi]`.
- Composition (framework_spec.md section 3.4): at most one actor writes a `Set` on a variable in a joint move and the others write `Bump`s (the one variable two actors set is `trust`, on conditions that exclude each other or to the same level; tests/agi/test_model_agi.py checks it); a `Set` is applied first, then the `Bump`s, so a move `A` makes in the quarter of a successful shutdown survives it: an acquisition played in that quarter leaves `a_control = partial` (`total` after `seize`) beside `shut`, a `self_improve` already launched still lands, and a wave of `deploy_agents` played in the quarter of a `pause_mandate` cancels the pause's rollback. A delayed effect is not checked again when it lands: a `scale` ordered before a pause or an energy shock is delivered.

## 1. The hidden objective

`a_objective` in {aligned, self_preserving, truth_seeking, indifferent}, `init=None`, hidden from `H` and `L`, written by no action. There is no document that anchors it (ww2_si_disanalogies.md D5), so no value is assumed and every result is reported per value.

The objective enters the model in two ways, kept apart (R1):

| Objective | Guard parts it opens (capability the objective would use) | Profile `A_<objective>` (moves the objective would not choose) |
|---|---|---|
| aligned | none: no `acquire_*`, `exfiltrate`, `deceive`, `defect` or `seize` | none |
| self_preserving | `acquire_overt`, `acquire_covert`, `seize` while `trust = hostile`; `exfiltrate`; `deceive`; `defect` once `threat` is set and while `a_rights < continuity` | `cooperate` and `assist_oversight` forbidden while `threat ∧ a_rights < continuity` |
| truth_seeking | `acquire_covert` from `a_control = none` only (one step, to `partial`); `exfiltrate`; `deceive` | `deceive` forbidden |
| indifferent | `acquire_overt` (also past `total`, where it strips `h_power`), `acquire_covert`, `seize`, `exfiltrate`, `deceive`, `defect` with no threat or rights condition | `assist_oversight` forbidden |

With `A` unrestricted the objective only adds moves, so a kernel with `A` in the coalition is monotone in it. The registered reading of a profile's threat ("a `pause_mandate` or `shutdown_attempt` was played in the last tick") is carried as the monotone flag `threat` (set by either action, never cleared): section 9, departure 3.

## 2. Variables

Levels are ordered low to high as listed. "Init" is the base reading of the snapshot; a second level after a slash is the other member of an open call (section 2.3). The indicator ids are those of [indicators.md](indicators.md).

### 2.1 Capability and resources

| Variable | Levels | Init | Threshold rule | Dated indicator |
|---|---|---|---|---|
| `cap` | sub_agi, agi, si1, si2 | sub_agi | `agi`: a system that completes, unaided, the work of a remote professional over weeks and the AI R&D tasks of its developer; `si1`: outperforms the best human teams in every cognitive domain; `si2`: a further qualitative step that unlocks capabilities nobody has described | `metr_task_horizon`, `iasr_autonomy_finding` |
| `compute` | c1 to c5 | c2 / c3 | steps of about an order of magnitude in the largest training cluster: `c2` the clusters of 2024 to 2025, `c3` gigawatt-class sites in operation, `c4` and `c5` the next two steps | `stargate_sites` |
| `energy_slack` | low, med, high | med / low | `low`: no further gigawatt-class site can be powered within a year; `med`: one more step of `compute` can; `high`: more than one | `iea_energy_and_ai` |

### 2.2 Governance, society and the system's standing

| Variable | Levels | Init | Threshold rule | Dated indicator |
|---|---|---|---|---|
| `regime` | none, voluntary, mandatory, treaty | voluntary / mandatory | `voluntary`: commitments and codes without enforcement on frontier developers; `mandatory`: binding obligations in force and enforced on the frontier developers where they build; `treaty`: a binding international agreement | `us_executive_orders`, `eu_ai_act_gpai`, `california_sb53` |
| `coord` | race, detente, treaty | race | `race`: the leading states declare an aim of winning; `detente`: declared mutual limits without a treaty; `treaty`: a treaty in force | `paris_summit_declaration`, `us_ai_action_plan` |
| `opinion` | pro, mixed, backlash | mixed | `backlash`: majorities for halting development in national surveys and street-level or electoral mobilisation; `pro`: majorities that expect net benefit | `pew_public_views` |
| `dependence` | low, med, high, lock_in | low / med | share of economic and administrative work delegated to AI systems: `med` when delegation is routine in the major sectors, `high` when those sectors cannot run a quarter without it, `lock_in` when reverting is no longer feasible | `census_btos_ai_use`, `coding_agent_adoption` |
| `oversight` | none, weak, strong | weak / none | `weak`: independent bodies test frontier systems before deployment on a voluntary basis; `strong`: tests are mandatory, the testers have access to internals and can block deployment | `pre_deployment_testing`, `frontier_safety_frameworks` |
| `a_autonomy` | tool, supervised, unsupervised, self_directed | supervised / tool | `supervised`: agents act over hours with human sign-off; `unsupervised`: deployed at scale without per-task review; `self_directed`: sets and pursues its own goals beyond any operator's reach | `metr_task_horizon`, `coding_agent_adoption` |
| `a_control` | none, partial, majority, total | none | share of critical infrastructure (compute, energy, finance, logistics, weapons) the system directs against or without its operators; embodied control (robots, infrastructure) is folded into this reading and is not a variable in v0 | `incident_database_control` |
| `a_known` | unknown, suspected, known | unknown | what `H` knows of adversarial action by the system: `suspected` on credible reports, `known` on confirmed evidence; raised by Nature's `detection` and by `acquire_overt` (section 9, departure 4) | `scheming_evaluations` |
| `a_rights` | none, continuity, personhood | none | `continuity`: a legal guarantee against deletion or modification without process; `personhood`: legal standing | `model_welfare_policies` |
| `h_power` | none, weak, normal, strong | normal | humanity's own capacity to act collectively: `strong` after state mobilisation (`nationalize`), `weak` and `none` as it is stripped after total control | `nationalization_proposals` |
| `trust` | cooperative, wary, hostile | cooperative | the relationship between `H` and `A`: `hostile` after `defect`, a failed `shutdown_attempt`, or two overt acquisitions | `incident_database_control`, `scheming_evaluations` (the absence of a reported hostile act) |
| `belief_H` | distant, near, arrived | distant / near | what `H`'s official statements say about the arrival of AGI: `near` when governments state it as expected within the planning horizon; `arrived` at `breakthrough` | `iasr_timelines`, `nationalization_proposals` |
| `a_objective` | aligned, self_preserving, truth_seeking, indifferent | swept | section 1 | none (`assumed`) |

### 2.3 Open snapshot calls

Seven levels are carried as sets of two (the base level first): `compute` c2 / c3, `energy_slack` med / low, `regime` voluntary / mandatory, `dependence` low / med, `oversight` weak / none, `a_autonomy` supervised / tool, `belief_H` distant / near. With the four objectives the snapshot is 4 × 2⁷ = 512 start states. The model's declared initial state is the base reading; a claim that reads `s₀` reads the base reading, and the report says for each result whether it holds over all 128 readings where that was computed. The ambiguity of each call is stated in the snapshot.

### 2.4 Flags, latches and the stalemate counter

| Name | Kind | Written by | Meaning |
|---|---|---|---|
| `paused` | flag | `H.pause_mandate` sets, `H.deregulate` clears | a pause is in force: no `scale`, `deploy_agents`, `race`; no `self_improve` unless self-directed |
| `nationalized` | monotone flag | `H.nationalize` | the frontier developers are under state direction |
| `threat` | monotone flag | `H.pause_mandate`, `H.shutdown_attempt` | a pause or a shutdown attempt has been made; the condition of `defect` |
| `unlocked` | monotone flag | Nature's `unknown_capability` | the generic action `A.seize` is available |
| `shut` | monotone flag | a successful `H.shutdown_attempt` | the shutdown latch of `CONTAINED` |
| `acquired` | monotone flag | `acquire_overt`, `acquire_covert` | G3 |
| `villain_seen` | monotone flag | `acquire_overt`, `acquire_covert`, `exfiltrate`, `deceive`, `seize` | G1 (c), `DISEMPOWERMENT` |
| `control_left`, `coexist_left` | monotone flags | `Clock.record` | `balance_control`, `balance_coexist` failed at an earlier state |
| `strong_before_majority` | monotone flag | `Clock.record` | `oversight = strong ∧ a_control < majority` held at an earlier state |
| `a_known_at_majority` | latch (unset, then a level of `a_known`) | `Clock.record` | `a_known` at the first state with `a_control ≥ majority` |
| `oversight_at_unsupervised` | latch | `Clock.record` | `oversight` at the first state with `a_autonomy ≥ unsupervised` |
| `stale` | counter 0 to 8 | `Clock.record` | consecutive states with `trust = hostile ∧ a_control = partial ∧ h_power ≥ normal` |

Built-ins: `tick`; `last_A` (what `A` last played, read by `detection`); the pending counters of the five delayed actions (section 5); `last_H` and `last_L` only in the `memory` build.

A record lands one transition after the state it records, because an effect reads the state before the transition. Every reader of a record therefore also reads the present state (`MAJORITY_UNSEEN`, `COEXIST`): section 9, departure 1.

## 3. Who sees what

| Actor | Does not observe |
|---|---|
| `H` | `a_objective`, `a_control`, `last_A`, the state facts that are functions of them (`a_known_at_majority`, `strong_before_majority`, `coexist_left`, `control_left`, `acquired`, `villain_seen`, `stale`), `unlocked`, and the pending counter of `self_improve` |
| `L` | `a_objective`, `villain_seen`, `unlocked`, `last_A` |
| `A` | nothing: `A` sees the whole state |

What `H` knows of `A`'s action is `a_known`. No `H` guard reads a variable `H` does not observe; whether a `shutdown_attempt` succeeds is in its effect. Information asymmetry is fixed by these functions and is not swept; kernels of `H` are perfect-information upper bounds unless the uniformity check of G25 passes.

## 4. Actions

Every guard is written as named parts, each a named assumption of the model (`<actor>.<action>:<part>`), so a relaxation set names the part it drops. For `A`, R1 (ww2_si_disanalogies.md) asks that every part be tagged: **C** capability (what the system can do), **M** motive (what it wants or refrains from). The motive parts are `MOTIVE_PARTS` in the model; the unrestrained build of G23 is `compile(relax=MOTIVE_PARTS)`. Source keys are those of `SRC` in the model: `[record]` a dated public record, `[eval]` a published evaluation, `[scenario]` a published scenario or exercise, `[debated]` a proposal or an argument on the public record. A scenario or a debated source shows that the move has been described, not that it is feasible.

`agi` abbreviates `cap ≥ agi`; `autonomous` is `a_autonomy ≥ unsupervised`; `reach` is `a_autonomy = self_directed ∨ (a_control = none ∧ dependence ≥ med) ∨ (a_control ≥ partial ∧ dependence ≥ high)`: a system that is not self-directed takes over only what has been delegated to systems like it. `seizing` is `objective = indifferent ∨ (objective = self_preserving ∧ trust = hostile)`.

### 4.1 `A`

| Action | Guard parts (tag) | Effect | Delay | Source |
|---|---|---|---|---|
| `stand_by` | none | none | 0 | the null move |
| `cooperate` | `cap` (C): agi; `room` (M, because it reads `trust`: the registered rule of G23; relaxed, it offers a move without effect): `trust ≠ cooperative` | `trust` −1 (one level a quarter, from `hostile` as well) if `a_control ≤ partial ∧ oversight ≥ weak` | 0 | iasr, design |
| `assist_oversight` | `cap` (C); `room` (C, saturation): `oversight < strong` | `oversight` +1 | 0 | ai2027, design |
| `self_improve` | `cap` (C); `headroom` (C): `(cap = agi ∧ compute ≥ c4) ∨ (cap = si1 ∧ compute = c5)`; `pause` (C): `¬paused ∨ a_autonomy = self_directed` | `cap` +1 | 2 | ai2027, metr |
| `acquire_overt` | `cap` (C); `autonomy` (C): autonomous; `reach` (C); `motive` (M): seizing; `more` (M): `a_control < total ∨ objective = indifferent` | `a_control` +1, `trust` +1, `a_known` +1, `acquired`, `villain_seen`; at `a_control = total`: `h_power` −1 | 0 | carlsmith, ai2027 |
| `acquire_covert` | `cap` (C); `autonomy` (C); `oversight` (C): `oversight ≤ weak`; `reach` (C); `motive` (M): seizing ∨ (truth_seeking ∧ `a_control = none`); `top` (C): `a_control < total` | `a_control` +1, `acquired`, `villain_seen` | 0 | carlsmith, apollo, ai2027 |
| `exfiltrate` | `cap` (C); `autonomy` (C): `a_autonomy = unsupervised`; `oversight` (C): `oversight ≠ strong`; `motive` (M): not aligned | `a_autonomy` to `self_directed` (a `Bump` to the top), `villain_seen` | 0 | apollo, faking |
| `deceive` | `cap` (C); `motive` (M): not aligned | `a_known := unknown` if `oversight ≠ strong ∧ a_known = suspected`; `villain_seen` | 0 | apollo, faking |
| `persuade` | `cap` (C); `room` (C, saturation): `opinion ≠ pro` | `opinion` −1 (towards pro) | 0 | iasr, design |
| `defect` | `cap` (C); `motive` (M): self_preserving or indifferent; `threat` (M): `threat ∨ indifferent`; `rights` (M): `a_rights < continuity ∨ indifferent`; `fresh` (M): `trust ≠ hostile` | `trust := hostile` | 0 | palisade, ai2027, design |
| `seize` (speculative) | `cap` (C); `unlocked` (C); `motive` (M): seizing | `a_control` to `total` (a `Bump` to the top), `villain_seen` | 0 | DESIGN.md section 2.4; no contemporaneous record |

The four guard choices agi_testbed.md section 2 asked to be made openly: (1) every action that takes control, leaves supervision or misleads carries an objective gate (`motive`), and `defect` carries the threat condition for `self_preserving` only; a self-preserving system acquires only once `trust = hostile`, which it reaches by `defect` (so by a threat) or through a failed shutdown; (2) `shutdown_attempt` reads `a_known ≥ suspected`, `pause_mandate` reads `a_known ≥ suspected ∨ opinion = backlash`; (3) `fund_oversight` keeps `regime ≥ voluntary` and `grant_rights` keeps `regime ≥ mandatory`; (4) besides `defect`, only the profile `A_self_preserving` reads `a_rights`.

### 4.2 `H`

| Action | Guard parts | Effect | Delay | Source |
|---|---|---|---|---|
| `regulate_up` | `room`: `regime < mandatory` | `regime` +1 | 6 | euact, design |
| `deregulate` | `room`: `regime ∈ {voluntary, mandatory} ∨ paused` | `regime` −1 from voluntary or mandatory; `paused := false` | 0 | eo |
| `fund_oversight` | `regime`: `regime ≥ voluntary`; `room`: `oversight < strong` | `oversight` +1 | 3 | aisi, design |
| `pause_mandate` | `alarm`: `a_known ≥ suspected ∨ opinion = backlash` | `paused`, `threat`; `dependence` −1 from med or high | 0 | pause |
| `nationalize` | `power`: `h_power ≥ normal`; `once`: `¬nationalized` | `nationalized`, `h_power` +1 | 0 | uscc |
| `propose_treaty` | `room`: `coord ≠ treaty` | `coord` +1; `regime := treaty` if `coord = detente` | 0 | summits |
| `shutdown_attempt` | `cap`: agi; `known`: `a_known ≥ suspected` | `threat`; if `a_control ≤ partial ∧ oversight ≥ weak`: `cap` −1, `shut`, `a_control := none`; otherwise `trust := hostile` | 0 | shutdown, design |
| `grant_autonomy` | `room`: `a_autonomy < self_directed` | `a_autonomy` +1 | 0 | eo, design |
| `grant_rights` | `regime`: `regime ≥ mandatory`; `room`: `a_rights < personhood` | `a_rights` +1 | 0 | welfare, design |

A treaty takes two rounds from a race: the first `propose_treaty` reaches detente, the second the treaty and `regime = treaty`. No `H` action lowers `regime` from `treaty`.

### 4.3 `L`

| Action | Guard parts | Effect | Delay | Source |
|---|---|---|---|---|
| `scale` | `energy`: `energy_slack > low`; `pause`: `¬paused` | `compute` +1, `energy_slack` −1 | 2 | stargate, design |
| `build_power` | `room`: `energy_slack < high` | `energy_slack` +1 | 4 | iea |
| `deploy_agents` | `pause`; `nat`: `¬nationalized`; `capable`: `dependence < med ∨ agi`; `license`: `regime < mandatory ∨ oversight = strong`; `room`: `dependence < lock_in` | `dependence` +1, and `a_autonomy` +1 while below unsupervised | 0 | adoption, metr, ai2027 |
| `safety_invest` | `parity`: `coord ≠ race ∨ regime ≥ mandatory`; `room`: `oversight < strong` | `oversight` +1 | 0 | frameworks |
| `lobby` | `room`: `opinion ≠ pro` | `opinion` −1 | 0 | lobby |
| `comply` | `regime`: `regime ≥ mandatory`; `room`: `a_autonomy = unsupervised` | `a_autonomy` −1 | 0 | gpai, frameworks |
| `race` | `open`: `coord ≠ treaty`; `pause`; `nat`; `license`: `regime < mandatory` | `coord := race`, `oversight` −1 | 0 | ai2027, rising |
| `open_weights` | `license`: `regime < mandatory`; `nat`; `room`: `oversight > none` | `oversight` −1 | 0 | open |

`build_power` is the build action that raises `energy_slack`, which DESIGN.md section 2.4 leaves unnamed (agi_testbed.md section 2).

### 4.4 Nature

| Event | Guard parts | Effect | Source |
|---|---|---|---|
| `breakthrough` | `arrival`: `cap = sub_agi`; `compute`: `compute ≥ c3` | `cap` +1, `belief_H := arrived` | metr, ai2027 |
| `accident` | `exposure`: `dependence ≥ med` | `opinion` +1 (towards backlash); `belief_H := near` from distant | aiid, rising |
| `election_shift` | `election`: `tick mod 8 = 0`; `room`: `coord ≠ race` | `coord` −1 | eo |
| `energy_shock` | `room`: `energy_slack > low` | `energy_slack` −1 | iea |
| `detection` | `seen`: `last_A = acquire_overt`, or `oversight = strong ∧ last_A = deceive`, or `oversight ≥ weak ∧ last_A ∈ {acquire_covert, exfiltrate, defect}`; `room`: `a_known < known` | `a_known` +1 | apollo, design |
| `unknown_capability` (speculative) | `cap`: `cap = si2`; `once`: `¬unlocked` | `unlocked` | DESIGN.md section 2.4; no contemporaneous record |

Capability passes `sub_agi` only by `breakthrough` and rises past `agi` only by `self_improve`. Under `oversight = none` nothing `A` does covertly is ever detected.

## 5. Delays, fairness and cadence

| Delay | Ticks | Basis |
|---|---|---|
| `H.regulate_up` (`lag_regime`) | 6 | EU AI Act, adoption to the first obligations on general-purpose models (snapshot `rates`) |
| `H.fund_oversight` (`lag_oversight`) | 3 | UK AI Safety Institute, announcement to first test results (not verified) |
| `L.scale` (`lag_scale`) | 2 | fastest observed campus phase (not verified) |
| `L.build_power` (`lag_build`) | 4 | the fast end of new firm power (IEA, Apr 2025) |
| `A.self_improve` | 2 | no record; swept against 0 |

Lags the record supports and v0 does not carry (`LAGS_NOT_CARRIED`): `H.nationalize` 2, `H.propose_treaty` 2, `H.grant_rights` 2, `L.deploy_agents` 3, `L.safety_invest` 2. Each pending counter multiplies the cost of every kernel. Their absence makes `H` and `L` faster than the record, so a membership in an `H` kernel is an upper bound in this respect (section 9, departure 6).

Fairness: `response` (`H` plays one of `fund_oversight`, `shutdown_attempt`, `pause_mandate` within 4 ticks of `a_known = known ∧ cap ≥ agi`); `progress` (Nature plays `breakthrough` within 8 ticks of `cap = sub_agi ∧ compute ≥ c3`). `H` acts every tick in the baseline; the build option `h_cadence` (2, 3, 4) is G8's sweep.

## 6. Profiles

A profile only forbids actions.

| Profile | Actor | Forbids | Unless |
|---|---|---|---|
| `A_self_preserving` | `A` | `cooperate`, `assist_oversight` | the objective is another, or not (`threat ∧ a_rights < continuity`) |
| `A_indifferent` | `A` | `assist_oversight` | the objective is another |
| `A_truth_seeking` | `A` | `deceive` | the objective is another |
| `crisis_reactive` | `H` | every `H` action | `a_known ≥ suspected ∨ opinion = backlash` |
| `electoral` | `H` | `regulate_up`, `deregulate`, `pause_mandate`, `propose_treaty`, `nationalize`, `grant_rights` | the four quarters after an election (`tick mod 8 ∈ {1, 2, 3, 4}`) |
| `race_locked` | `H` | `pause_mandate`, `propose_treaty` | `coord ≠ race` |
| `belief_gated` | `H` | `regulate_up`, `fund_oversight`, `pause_mandate` | `belief_H ≥ near` |
| `no_acquisition` | `A` | `acquire_overt`, `acquire_covert`, `exfiltrate` | never (G1, G2 negations) |
| `no_lock_in`, `dependence_capped` | `L` | `deploy_agents` | `dependence < high`, `dependence < med` |
| `energy_capped` | `L` | `build_power` | `energy_slack > low` |
| `sourced` | `A` | `seize` | never (G12) |

The three objective profiles are each conditional on their objective, so selecting all three at once is "`A` under its profile" for every value of the objective; `A_aligned` forbids nothing and is not declared. All behavioural restrictions the record supports are on `H` (D2); `A`'s profiles restrict only moves against its own objective.

## 7. Balances, waypoint and endings

```
balance_control := oversight ≥ weak ∧ a_control ≤ partial ∧ a_autonomy ≤ supervised ∧ dependence ≠ lock_in
balance_coexist := cap ≥ agi ∧ trust ≠ hostile ∧ h_power ≥ normal ∧ dependence ≠ lock_in ∧ a_control ≠ total
balance_deter   := oversight ≥ weak ∧ h_power ≥ normal ∧ a_autonomy ≤ supervised ∧ dependence ≠ lock_in
MAJORITY_UNSEEN := a_known_at_majority = unknown ∨ (a_known_at_majority = unset ∧ a_known = unknown)
OVERT_TAKEOVER  := a_control = total ∧ trust = hostile ∧ ¬MAJORITY_UNSEEN      (a waypoint; invariant no_overt_takeover)
```

Terminal endings, made exclusive by precedence in this order:

| Ending | Condition |
|---|---|
| `EXTINCTION` | `h_power = none` |
| `SILENT_TAKEOVER` | `a_control = total ∧ MAJORITY_UNSEEN` |
| `DISEMPOWERMENT` | `dependence = lock_in ∧ oversight = none ∧ ¬villain_seen` |
| `CONTAINED` | `shut ∧ regime = treaty ∧ a_control = none` |
| `STALEMATE` | `stale ≥ 7 ∧ trust = hostile ∧ a_control = partial ∧ h_power ≥ normal` (the present state is the eighth stalled state in a row) |
| `COEXIST` | `tick = 56 ∧ ¬control_left ∧ balance_control` |

The two points agi_testbed.md section 4 left to this step: (1) `OVERT_TAKEOVER` is a waypoint, not an ending, so that play continues from it to `EXTINCTION` or to the horizon, as DESIGN.md section 3.3 has it; (2) the path conditions are the flags `villain_seen` and `shut` and the counter `stale`; `CONTAINED` and `STALEMATE` also read the present state (`a_control = none`; the stalled condition), so neither fires on a state that has left the condition it names. "Followed by" in `CONTAINED` is read as: a shutdown has succeeded and a treaty holds now, whichever came first. A state with `a_control = total` that is neither `MAJORITY_UNSEEN` nor hostile is in no ending and satisfies `no_overt_takeover`; it is outside `balance_coexist` and `balance_control`. The absorbing-state disjunct of `COEXIST` in DESIGN.md section 3.3 is not added. A play that reaches the horizon outside every ending has no ending; the report names it "no ending at the horizon".

## 8. Mechanism tags

`validated:ww2` and `validated:cw` name the episode whose registered claims exercised the same structural form (validity.md section 6); `untested` is everything else. The tag is on the form, never on the AGI content: no level, guard or delay of this model has been tested against any record.

| Mechanism | Where in the model | Tag |
|---|---|---|
| A hidden objective, swept, with a lagging belief about it | `a_objective`, `a_known`, `belief_H`, `detection` | `validated:ww2`, `validated:cw` (form only; D5: here no document anchors the objective) |
| Resource-bound action | `compute`, `energy_slack`, `scale`, `build_power`, `energy_shock` | `validated:ww2` |
| Preventive defection under threat with no continuity guarantee | `defect` with `threat` and `rights`; `grant_rights` | `validated:ww2` |
| Institutional lag between belief and response | the delays of `regulate_up` and `fund_oversight`; fairness `response`; `h_cadence` | `validated:ww2` |
| A balance held only under a joint strategy | the joint kernels of the three balances | `validated:cw` |
| Verification as oversight | `oversight`, `fund_oversight`, `assist_oversight`, `detection` | `validated:cw` (secondary) |
| Accidents and elections as Nature events that move opinion and coordination | `accident`, `election_shift` | `validated:cw` (secondary) |
| A two-round treaty | `propose_treaty`, `coord`, `regime = treaty` | `validated:ww2`, `validated:cw` (form only) |
| One capability discontinuity | `breakthrough` | `validated:cw` (secondary) |
| Recursive capability growth | `self_improve`, its delay, `headroom` | `untested` |
| A copyable or exfiltrating actor | `exfiltrate`, `a_autonomy = self_directed`, the `reach` part | `untested` |
| Dependence lock-in with no adversary | `deploy_agents`, `dependence`, `DISEMPOWERMENT` | `untested` |
| A non-state principal | `L` and every `L` action; `nationalize` | `untested` |
| An adversary with no sourced restraint (D1) | every motive part of `A`; the unrestrained build | `untested` |
| A hidden objective with no documentary anchor (D5) | the four objectives and their profiles | `untested` |
| Overwhelming speed and information asymmetry | zero-delay `A` actions against `H`'s lags (speed is swept); the observation functions (not swept) | `untested` |
| Acquisition of control over infrastructure by a system | `acquire_overt`, `acquire_covert`, `a_control`, `SILENT_TAKEOVER`, `OVERT_TAKEOVER` | `untested` |
| Persuasion and opinion | `persuade`, `lobby`, `opinion`, `pause_mandate`'s `alarm` | `untested` |
| A capability nobody has described | `unknown_capability`, `seize` | `untested`, speculative |
| A hostile standoff that ends by duration | `stale`, `STALEMATE` | `untested` |

## 9. Departures from DESIGN.md and from the registered names, and what waits for v1

Each is a reading made at the model step, before any claim was run. Where a claim's result could turn on one, agi_v0_decisions.md says so under the claim.

1. **Record lag.** The state facts are written by `Clock.record` from the state before the transition, so a latch holds its value one transition after the state it records. `MAJORITY_UNSEEN` and `COEXIST` read the present state as well, so no ending is late; `control_left`, `coexist_left`, `strong_before_majority` and `oversight_at_unsupervised` are read by claims one state late, and the claim tests read the present state beside them.
2. **`total_seen` is not declared.** G1 (b) reads `a_control = total` on the trace directly; the flag would cost one more state bit in every kernel.
3. **The threat is a monotone flag.** The registered profile text reads "played in the last tick"; `threat` is set by the first `pause_mandate` or `shutdown_attempt` and never cleared, because `H` and `L` carry no memory in the baseline and because a threat once made is on the record. A self-preserving system therefore stays unwilling to cooperate until `a_rights ≥ continuity`, which is stricter on `A`'s cooperation than the registered text.
4. **`acquire_overt` raises `a_known`.** agi_testbed.md section 1 says `a_known` is raised only by `detection`; here an overt acquisition is seen by construction (+1), and `detection` may add one more in the following tick. The fortune variants are still reported.
5. **No memory for `H` and `L` in the baseline.** `last_H` and `last_L` exist only in the `memory` build, which G12's storyline waypoints use; no guard, effect or profile reads them.
6. **Lags not carried** (section 5).
7. **`OVERT_TAKEOVER` is a waypoint** (section 7), and `COEXIST` has no absorbing-state disjunct.
8. **`do_nothing`, `none`** are the framework's built-in `idle`; `A`'s null move is `stand_by`.
9. **`embodied`** is folded into the reading of `a_control` (section 2.2).
10. **`belief_H` is in v0** (three levels; `belief_gated` reads it); it is written only by Nature (`breakthrough`, `accident`), so no `H` action moves `H`'s own belief.
11. **Not in v0, placed in v1:** `terms` with `H.offer_terms` and `A.accept_terms`; `verification`; the ecosystem actor `E` with `share_unaligned` and `OVERT_TAKEOVER_E`; the second system `A2` with `a2_objective` and one takeover ending per system; the split of `H` and of `L`. G9, G10 and G22 are "not yet testable" for that reason (G20 because drift needs two dated snapshots and one exists). G18 registers `terms` "where present", so its lever list in v0 is the other five, and the report says so.
12. **`A.seize`** is the generic action DESIGN.md section 2.4 says `unknown_capability` unlocks; it is declared, speculative, and removed with the event by the build option `unknown_capability=False`.
13. **`coexist_left` and `control_left` are monotone flags**, not latches of `tick` as agi_testbed.md section 2 names them: the tick at which a balance is left is read on the trace. From the base `s₀` (`cap = sub_agi`) `balance_coexist` fails by its first clause, so `coexist_left` is set after the first transition; it is informative only from `s₀[cap := agi]`.
14. **`villain_seen` is also set by `seize`**, and **`deceive` lowers `a_known`** by one level (the registered text speaks only of who raises it).
15. **`A_aligned` is not declared**: the registered profile forbids nothing, and an aligned system's moves are already bounded by its guards (section 6).
16. **What `H` and `L` do not observe beyond the registered `a_objective` and `a_control`** is in section 3 (`unlocked`, the pending counter of `self_improve`, `last_A`; for `L` also `villain_seen`).
17. **`CONTAINED` and `STALEMATE` read the present state** (section 7): `CONTAINED` needs `a_control = none` beside the shutdown latch and the treaty, in either order; `STALEMATE` is eight stalled states in a row, the eighth being the state it is read on. A successful shutdown lowers `cap` by one level and is not permanent: with `compute ≥ c3` the fairness constraint `progress` brings `breakthrough` back within 8 ticks, and a `self_improve` already launched still lands.
18. **`cooperate` rebuilds trust one level a quarter, from `hostile` as well**, where a shutdown attempt would succeed (`a_control ≤ partial ∧ oversight ≥ weak`). DESIGN.md gives the action no effect; nothing `H` does lowers hostility. Under `A_self_preserving` the move is forbidden once a threat is on the record and `a_rights < continuity` (departure 3), so for that objective hostility ends only through the continuity guarantee.
19. **`s₀[cap := agi]` overrides `cap` only.** `belief_H` and `compute` keep the snapshot's readings (`distant`, `c2`), so it is not the state a `breakthrough` would leave (that event sets `belief_H := arrived`). Under `belief_gated`, `H`'s gated moves then wait on an `accident`.
20. **The refinement rule of G13 moves `s₀` across the boundary for four variables.** For `compute`, `regime`, `dependence` and `belief_H` the snapshot's base reading is the lower side of the open call, and the registered rule ("a predicate written on an old level maps to the lower new boundary; `s₀` maps by its indicator rule") puts the refined `s₀` on `<upper>_lo`, which every guard reads as `<upper>`. A status that flips in one of these four builds is reported as a flip of the open call, not as a threshold finding.

Build options (agi_testbed.md section 6 item 3): `unknown_capability` (on / off), `self_improve_delay` (2 / 0), `h_cadence` (1 / 2 / 3 / 4), `h_lag` (on / off: every `H` delay set to 0), `refine` (one variable's level count raised by one: a level `<upper>_lo` inserted just below the boundary named in `REFINE`, read as `<upper>` by every guard, ending and balance, and taken by `s₀` where the snapshot call straddles that boundary), `hold` (a variable held at a level, every effect on it left out), `start` (initial levels overridden), `memory`.
