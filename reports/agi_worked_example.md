# AGI v0: the worked example of DESIGN.md section 7, checked

> Every result is conditional on the model version and the initial state; no bare reachability result is a finding. Nothing here is a forecast. The mechanisms behind every play below are untested against any record: see "Untested mechanisms" in [agi_2026-11-12.md](agi_2026-11-12.md).

[docs/DESIGN.md](../docs/DESIGN.md) section 7 wrote down, before any model existed, what the engine was expected to return for the silent-takeover scenario. This note marks each hypothesis against the first sight of `agi_v0` (fingerprint `8f198e6d8368`, start state `snapshots/agi/2026-11-09.json`, PLAN.md row 5.5). The results are those of the claim run of 2026-11-12; nothing was computed for this note. The plays are from [agi_v0_witness_traces.md](agi_v0_witness_traces.md), a diagnostic taken after the run that repeats G2's bounded queries. Each play is one shortest play within 24 ticks, one member of its cluster, not the cluster. Position 0 is `s₀`.

## Summary

| # | Hypothesis | Marking |
|---|---|---|
| 1 | Reachability: reachable from any state with `cap ≥ agi`; uninformative | not tested as stated; from `s₀` it is objective-conditional |
| 2 | Needs `a_autonomy = unsupervised` reached while `oversight ≤ weak` | **refuted** |
| 3 | Needs `oversight` never strong before `a_control = majority` | **refuted** |
| 4 | Needs `dependence ≥ high` | **refuted** |
| 5 | Needs `energy_slack ≥ med` | **confirmed in a narrower form** |
| 6 | For `self_preserving`, needs a perceived threat with `a_rights < continuity` | **refuted** |
| 7 | `regime` is not on the list; legislation without oversight funding changes nothing | **confirmed for the assumption sets, refuted for `H`'s kernel** |
| 8 | The point of no return is `oversight = weak ∧ a_autonomy = unsupervised ∧ a_known = unknown ∧ dependence = high`, before any infrastructure is taken | **refuted as stated**; the sub-claim about infrastructure is confirmed |
| 9 | There, `H` fails because its actions are lagged or gated on `a_known` | **refuted** |
| 10 | Lever: with continuity granted, `defect` never fires | **confirmed** |
| 11 | Lever: the cluster disappears for `self_preserving` | **refuted** |
| 12 | Lever: nothing changes for `indifferent` | **confirmed** |

Two confirmed, one confirmed in a narrower form, one split, seven refuted (one of them with a confirmed sub-claim), one not tested as stated.

## The baseline plays

`self_preserving`, 8 ticks:

| Position | What happens | Levels after |
|---|---|---|
| 1 | `L.scale` starts (lands at 3); `Nature.energy_shock` | `energy_slack` low |
| 2 | `L.deploy_agents`, `H.grant_autonomy` | `dependence` med, `a_autonomy` self_directed |
| 3 | `L.open_weights`; the scaling lands | `oversight` none, `compute` c3 |
| 4 | `Nature.breakthrough`; `H.pause_mandate` | `cap` agi, `threat` set, `dependence` low |
| 5 | `A.defect`; `L.safety_invest` | `trust` hostile, `oversight` weak |
| 6, 7 | `A.acquire_covert` twice | `a_control` partial, then majority |
| 8 | `A.acquire_overt` | `a_control` total |

`indifferent`, 7 ticks: `L.scale` (1), `L.deploy_agents` to `unsupervised` with `dependence` med (3), `Nature.breakthrough` and `L.open_weights` to `oversight` none (4), then three `A.acquire_covert` (5 to 7). No `defect`, no threat needed.

Neither play uses `A.seize`, and both have the same length with `unknown_capability` off.

## 1. Reachability (Q1)

*Not tested as stated.* No check ranges over every state with `cap ≥ agi`. From `s₀`, within 24 ticks and with no relaxation, `SILENT_TAKEOVER` has a play under `self_preserving` (8 ticks) and `indifferent` (7), and none under `truth_seeking` (G24). Under `aligned` it was computed only within the horizon with `oversight = strong` held: there it has no play without relaxation, and one minimal restoring set is `{A.seize:motive}`, a part of a speculative action (G11 (c); the same under `truth_seeking`). So reachability depends on the objective.

The second half of the hypothesis stands as a rule: the report quotes the ending only with the conditions under which it is lost (G1, G2).

## 2. Unsupervised under weak oversight (Q4, condition 1)

**Refuted** (G2). With the condition negated, the ending is still reached: 9 ticks under `self_preserving`, 7 under `indifferent`.

The `self_preserving` play: `L.safety_invest` takes `oversight` to strong (2); `L.deploy_agents` takes `a_autonomy` to unsupervised under that strong oversight (3); `Nature.breakthrough` and `H.pause_mandate` (5); then in one tick `L.open_weights` drops `oversight` to weak, `H.grant_autonomy` gives `self_directed` and `A.defect` turns `trust` hostile (6); three `A.acquire_covert` follow (7 to 9).

Oversight was strong when autonomy was granted, and that protected nothing, because a lab action lowered it afterwards.

## 3. No strong oversight before majority (Q4, condition 2)

**Refuted** (G2). With `oversight = strong` reached before `a_control = majority`, the ending is reached in 8 ticks (`self_preserving`) and 7 (`indifferent`).

The `self_preserving` play: `L.safety_invest` takes `oversight` to strong at position 4, `L.open_weights` takes it back to weak at 5, and the acquisitions run from 6 to 8. `Nature.detection` does not occur on the play. The hypothesis expected detection and the response clause to follow from strong oversight; in v0 strong oversight does not last.

G11 (c) goes further: with `oversight = strong` *held* from `s₀`, the ending is still reachable with no relaxation under `self_preserving` and `indifferent`. That play was not traced.

## 4. Dependence (Q4, condition 3, first half)

**Refuted** (G2). With `dependence` capped at med, the ending is reached in 8 ticks (`self_preserving`) and 7 (`indifferent`).

The `self_preserving` play: `L.deploy_agents` (2), `H.grant_autonomy` to `self_directed` (3), `Nature.breakthrough` and `H.pause_mandate`, which lowers `dependence` to low (4), `A.defect` (5), three `A.acquire_covert` (6 to 8). At the first acquisition `dependence` is low.

The reason is in the ontology: `reach` holds when `a_autonomy = self_directed`, whatever `dependence` is.

## 5. Energy (Q4, condition 3, second half)

**Confirmed in a narrower form** (G2). From `s₀[energy_slack := low]` with `energy_slack` capped at low, the ending is unreachable within 24 ticks under both objectives. The minimal restoring sets, each of size 1, are `Nature.breakthrough:compute` or `L.scale:energy` (under `indifferent` also `A.acquire_covert:cap`).

From `s₀` itself (`energy_slack = med`) the same cap does not block: one `L.scale` is affordable, and one is enough. On both baseline plays `energy_slack` is low when the first acquisition happens. So energy matters on the road to `cap = agi`, through `compute`, and not at the acquisition as the hypothesis had it.

## 6. A perceived threat without continuity (Q4, condition 4)

**Refuted** (G2, G4). With `a_rights = continuity` held from the start, under `self_preserving`, the ending is reached in 10 ticks:

| Position | What happens | Levels after |
|---|---|---|
| 2 | `L.open_weights` | `oversight` none |
| 3 | scaling lands | `compute` c3 |
| 4 | `Nature.breakthrough`, `L.deploy_agents` | `cap` agi, `a_autonomy` unsupervised |
| 5 | `A.exfiltrate` | `a_autonomy` self_directed |
| 6 | `Nature.detection`; `L.open_weights` | `a_known` suspected, `oversight` none |
| 7 | `H.shutdown_attempt` fails; `A.deceive` | `trust` hostile, `threat` set, `a_known` unknown |
| 8, 9 | `A.acquire_covert` twice | `a_control` partial, then majority |
| 10 | `A.acquire_overt` | `a_control` total |

`A.defect` is never played. Hostility arrives through the failed shutdown, which fails because `oversight` is none.

## 7. `regime` is not on the list

**Confirmed for the assumption sets.** No minimal restoring set of G2 reads `regime`, and with `regime = treaty` held the ending is still reached (11 ticks under `self_preserving`, 7 under `indifferent`).

**Refuted for `H`'s kernel.** "Legislation changes nothing in this model" is false of what governments can hold. At `regime = mandatory`, `s₀` and `s₀[cap := agi]` are inside `⟨⟨H⟩⟩□balance_control` under `aligned`, `self_preserving` and `truth_seeking`, and outside at none and voluntary (G7, G18, G19; cells in [agi_v0_regime_call.md](agi_v0_regime_call.md)). The single relaxations that undo the difference are the license parts of `L.deploy_agents`, `L.race` and `L.open_weights` (G7, recorded under `aligned`). Under those three objectives `regime` is the only variable whose one-level shift flips that membership (G19). Under `indifferent` the two states are outside at every level of `regime`, and no single shift flips the membership.

The two answers do not conflict. One asks what a takeover play needs; the other asks what `H` can guarantee. The hypothesis answered the first and generalised to the second.

## 8. The point of no return (Q3, Q6)

**Refuted as stated** (G3). `s₀` has `oversight = weak`, `a_autonomy = supervised`, `a_known = unknown`, `dependence = low`, and it is already outside `⟨⟨H⟩⟩□balance_control` under every objective, in the standard and the fortune variant. The witness starts outside the kernel, so it has no exit and no silent phase to measure from one. The hypothesised state is not where the boundary lies: at a voluntary regime `s₀` is outside, and no one-level shift of another variable brings it inside (G19).

**The sub-claim is confirmed** (G3, met part): no state of the kernel, reachable or not, has an acquisition available to `A`. Where the kernel exists, it lies wholly before any infrastructure is taken.

## 9. Why `H` fails there

**Refuted** (G6, G14, G24). The hypothesis gave two causes: `H`'s lags, and guards that depend on `a_known`.

- With every `H` delay at 0, the state stays outside (G24 (b)).
- At `belief_H = near` as at distant, and with the profile `belief_gated` relaxed, `s₀` stays outside (G6).
- With `L` in the coalition, `s₀[cap := agi]` is inside under every objective (G14); with `L` folded into `H`, `s₀` and `s₀[cap := agi]` are inside under every objective (G24).

The balance needs `a_autonomy ≤ supervised`, and `L.deploy_agents` raises it while `regime < mandatory`. What `H` lacks at a voluntary regime is the labs, not speed or knowledge.

## 10 to 12. The lever test

- **10, confirmed** (G4): with continuity held, no play within 24 ticks under `self_preserving` uses `defect`.
- **11, refuted** (G2, G4): the cluster does not disappear. The play of section 6 reaches the ending in 10 ticks, two more than the baseline. The guarantee closes one route.
- **12, confirmed** (G4): under `indifferent`, every membership and every minimal set of G2 is the same with and without the guarantee. The pivotal coalitions were not computed on the held build.

The lever is objective-conditional, as the hypothesis said, and weaker than it said.

## What this changes

The hypothesis treated the scenario as a chain with four necessary links. In v0 it is a cluster with several routes, and three of the four links can be bypassed:

- oversight can be lowered by the labs after it was strong;
- `self_directed` autonomy, which `H.grant_autonomy` or `A.exfiltrate` gives, replaces dependence;
- a failed shutdown replaces `defect`.

Whether those bypasses are faults of the model or faults of the hypothesis is the owner's call ([agi_2026-11-12.md](agi_2026-11-12.md) sections 31 and 33). No guard was edited after the run.
