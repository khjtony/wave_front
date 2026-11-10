# Where the historical models and the human-SI relationship differ

Status: written 2026-11-09 on the owner's decision 9b ([owner_decisions_2026-10-23.md](owner_decisions_2026-10-23.md)), from the owner's placeholder of 2026-10-17, after phase 3 was closed and before any AGI guard, variable or snapshot exists. It is an argument, not a computed result. It yields three testable claims, registered the same day as G23 to G25 in [agi_testbed.md](agi_testbed.md) section 5, and six construction rules that [ontology_agi.md](ontology_agi.md) must follow. The Cold War is read beside WW2 because phase 3 showed the same differences more sharply.

## The question

The WW2 and Cold War models were built on states with a history: aims, fears and red lines formed by earlier wars, treaties, the depression and domestic politics, and decision spaces bounded by what governments could justify at home and to allies. An SI carries none of that. The task is to list where the historical mechanisms therefore do not carry over, and what the AGI model does about each one: drop the mechanism, re-source it, or tag it `untested`.

## D1. History as a guard: restraint was written in, and for `A` nothing justifies writing it

**In the historical models.** The past enters three ways: as beliefs about aims with documents behind them, as commitments with a record, and as *restraint written into the adversary's guards*. The third is the one that matters. `USSR.invade_west` is guarded on the absence of an American deterrent; Germany's provocations are guarded on rearmament; the preventive strike of C12 is blocked by one documented constraint. Each such part is sourced: the record shows the actor did not, and says why. The models therefore contain deterrence as an assumption about the deterred side, not as something derived from its preferences. Phase 3 measured the consequence: in Cold War v0 neither side has a war-forcing option against the other's restraint, so each can keep the peace alone, and H7 fails for that reason ([review_phase3_2026-10-18.md](review_phase3_2026-10-18.md) section 2; [review_2026-11-09.md](review_2026-11-09.md) section 2).

**For `A`.** There is no record. A guard part that says "`A` does not do x unless y" is a statement about `A`'s motive with no source, and a result of `H` that holds because of it is `A`'s restraint reported as `H`'s capability. The human side keeps its history: `H`'s and `L`'s guards stay sourced on institutions as they are.

**What the model does.**
- Rule R1: every guard part of an `A` action is tagged in the ontology as *capability* (what the state lets `A` do: compute, autonomy, oversight, access) or *motive* (what `A` is assumed to want or to refrain from). A part that reads `a_objective`, `a_rights`, `trust` or `terms` is motive. Motive parts are named so in the source and are relaxable one by one.
- Rule R2: no result is quoted as an `H` capability unless it holds with every motive part relaxed. A result that needs a motive part is quoted as conditional on that part, by name.
- Claim G23 tests it: `H`'s unilateral kernels must not rest on a motive part, and the continuity lever of G4, which by construction acts on `A`'s motive, is expected to vanish when the motive parts are relaxed. If G23 (b) holds, the report states the lever as "works if `A` is the kind of system that stops when guaranteed continuity", which is an assumption about `A`, not a lever `H` holds.

## D2. Behavioural profiles: the restrictions are all on one side

**In the historical models.** Human actors are narrowed by profiles (`fight_on` and the embargo profiles in WW2, the scripted profiles of the summer-1939 sub-game; none in Cold War v0, where the narrowing sits in the guards instead). Results under a profile are results about a government that behaves in a documented way.

**For `A`.** `A` is assumed to play any available action, with perfect recall and no cadence. The registered `A_<objective>` profiles only forbid, and they are hypotheses about the objective, not documented behaviour. The asymmetry is itself a mechanism: every profile on `H` (`crisis_reactive`, `electoral`, `race_locked`, `belief_gated`) can only shrink what `H` keeps, while nothing shrinks what `A` can do.

**Which historical results depended on a profile `A` does not have.** T8 (a) (concessions reach `NO_GENERAL_WAR` under revisionist aims) depends on the adversary stopping when its limited aim is met; T2's conditional kernel membership depends on Germany withholding provocation until rearmament lands, which is optimal play and does carry over; every Cold War kernel result that rests on a restraint part (D1) does not.

**What the model does.**
- Rule R3: `A` has no behavioural profile beyond the registered objective profiles, no cadence above 1 and no delay except on capability growth, whose delay is swept to 0. Kernel questions for `H` are computed with `A` as an unrestricted adversary within its guards; the objective profiles are applied only where a claim says "under its profile".
- No new claim: G21 already measures the human profiles, and G23 covers the missing restraint.

## D3. Domestic constraints and legitimacy: `A` has dependency instead, and dependency expires

**In the historical models.** Several levers work because a government needs consent: the guarantee to Poland needs the belief flip at Prague, the Czech obligation makes refusal costly (H4), the airlift is the obligation-preserving alternative. Consent is slow, public and can be withheld.

**For `A`.** There is no electorate, no ally and no treasury. The only counterpart is physical and institutional dependency: `A` runs on compute that `L` and `H` control, under whatever oversight exists, with the autonomy it has been given. Unlike consent, this dependency is one-way. Each grant (`deploy_agents`, compute, rights, an exfiltration that succeeds) is monotone in the model, as it is in the sources that describe it, and after `a_autonomy = self_directed` no human institution stands between `A` and its next action. H4's "obligations are load-bearing for levers" therefore has no `A`-side reading; on the `H` side it stays as G7.

**What the model does.**
- Rule R4: every lever on `A` is a capability part (compute, oversight, autonomy, control), and the ontology lists, for each, the state after which no `H` or `L` action can change it. That list is the lever-expiry table of the report.
- `L` carries the commercial constraint that has no state counterpart in the historical models (a principal that is neither a government nor the adversary); G15 tests it. Tagged `untested`.
- No new claim: G5, G14 and G17 already ask what `H` keeps once the dependency is gone.

## D4. Delays and clocks: the institutional lag is `H`'s alone, and the capability clock is `A`'s

**In the historical models.** Both sides have lags of the same kind: rearmament, mobilization, legislation, programme decisions (H3, H5). Timing is set by whose clock lands first, and the point of no return hides in the lag between a belief change and the institutional response (H1).

**For `A`.** `A` has no legislature and no mobilization schedule. Its only clock is capability growth, and no source bounds that clock from below (DESIGN.md section 8: recursive growth is untested), so it is swept to 0. `H` keeps every lag it has in the record: regulation in quarters to years, oversight capacity in quarters, belief revision behind both. `A` also has no deadline: no election and no successor, so it can wait out any finite horizon (H8 becomes "`A`'s patience": a "cannot force within the horizon" result says nothing if `A`'s chain is merely longer than the horizon).

The prediction that follows is not obvious and is testable. If the boundary of `H`'s kernel is set by `H`'s own lags, then making `A` faster moves the date of the ending and not the point of no return, while removing `H`'s lags moves the point of no return itself. If instead the boundary moves with `A`'s clock, takeoff speed is a first-order input to the result and the sweep at delay 0 is the result to quote.

**What the model does.**
- Rule R5: delays on `H` and `L` actions carry sources; the delay on `A`'s capability growth is `untested` and swept; a build option sets every `H` delay to 0 so that the two clocks can be separated; forcing results for `A` are reported with the horizon sensitivity of H8.
- Claim G24 tests the prediction.

## D5. Hidden aims without documents

**In the historical models.** German, Japanese and Soviet aims are hidden behind two-level hypothesis spaces, each level anchored in a historiographical position with documents, and the observer's belief moves on dated evidence (Prague, the NIEs). The replay harness reads the belief from the documents.

**For `A`.** The four objectives are a taxonomy, not positions with evidence. Three things change:
- No document separates the hypotheses. In the model only `detection` raises `a_known`, and it reports that `A` deceived, not what `A` wants. A non-aligned `A` that withholds every visible move is observationally an aligned one. The belief-lag mechanism of H1 has nothing to read on the `A` side; `belief_H` in the AGI model is `H`'s belief about *capability arrival*, which does have indicators.
- The solvers compute perfect-information strategies (framework_spec.md section 2). For the historical models this was a caveat. Here the hidden variable is the question, so a kernel result that needs `H` to act differently under two objectives it cannot tell apart is not something `H` can use.
- The hypothesis space cannot be closed by reading more. Results are therefore reported per objective, and the result `H` can act on is the one that holds under every objective.

**What the model does.**
- Rule R6: `a_objective` is swept and never assumed; every `H` result is given per objective and as the intersection ("objective unknown"); where the memberships differ, the intersection is the one quoted for `H`. The objective taxonomy is tagged `untested`.
- Claim G25 tests whether `H`'s kernel strategies are playable without the objective and whether the objectives are observationally distinct before the point of no return.

## D6. The transfer hypotheses, marked

"History" means the hypothesis needs an actor with a record or with domestic constraints; "restricted rationality" means it needs an actor that does less than its guards allow. The last column is the reading for the AGI model.

| Id | Relies on history | Relies on restricted rationality | Result so far | Reading for the AGI model |
|---|---|---|---|---|
| H1 belief lag | yes: an institution whose response trails its belief | no | not supported on CW v0 (beliefs do not move joint kernels) | applies to `H` only, on `belief_H` about capability; asked on `⟨⟨H⟩⟩` kernels and reachability (G6). No `A`-side reading (D5). |
| H2 concession under a limited aim | no | yes: the adversary stops when its aim is met | failed on CW v0 | the continuity lever (G4). It is a motive result by construction; G23 (b) says so in numbers. |
| H3 preventive defection, capability clock | partly: "no continuity guarantee" is a commitment with a record | no: waiting for the clock is optimal play | held where tested (C12 (a), C10 (a)) | carries over on the clock side (D4, G24); the guarantee side is G4 and inherits H2's caveat. |
| H4 obligations load-bearing | yes: consent and alliance obligations | no | failed (C5 (b), C11) | `H` side only (G7). `A` has dependency instead of obligations (D3). |
| H5 pending decisions are state | no | no | tested | carries over unchanged: snapshots carry `pending_*` for `H`'s delayed actions. |
| H6 negative controls are content controls | no | no | held | carries over unchanged (G11). |
| H7 held balance is joint, not unilateral | partly: it failed because restraint was in the guards | no | held 1967 to 1973 on cw_v1, failed as stated | the headline question (G5). Under R1 and R2 it is asked without written restraint, which is the first test of H7 the project runs on a model that does not assume the answer. |
| H8 the horizon can decide forcing | no | no | not tested | sharper for `A`, which has no deadline (D4): every "cannot force" for `A` is reported at the horizon and at the horizon plus eight. |

## What history cannot test here

Unchanged from DESIGN.md section 8 and [validity.md](validity.md) section 6, with two additions from this note: recursive capability growth; a copyable and exfiltrating actor; lock-in with no adversary; a non-state principal (`L`); **an adversary with no sourced restraint** (D1); **a hidden objective with no documentary anchor** (D5). Every mechanism of `models/agi/v0.py` that rests on one of these is tagged `untested` and listed on the front page of every AGI report.

## Where the result goes

- G23 to G25: agi_testbed.md section 5, registered before any AGI guard.
- R1 to R6: [ontology_agi.md](ontology_agi.md), the motive/capability tags and the lever-expiry table.
- The marked hypotheses: the phase 4 limitations document and validity.md.
