# WW2 v0 action catalogue

Status: skeleton fixed by the architect (the action list, the feasibility principle, the effect shapes). The historian-facing content (the contemporaneous debate each action is cited to, the exact guard thresholds, delays, and the speculative tags) is filled in phase 1 step 1.2 and reviewed before the model is coded. Read [ww2_testbed.md](ww2_testbed.md) section 7 and [ontology_ww2.md](ontology_ww2.md) first.

## The feasibility principle

A guard says when an action was *feasible* for the actor: capability, institutional constraint, prior condition. A guard never encodes a preference, a motive or a prediction of what the actor would choose; that is what the engine's nondeterminism explores. "Hitler would not have attacked Poland without the Soviet pact" is a preference and is not a guard. "A western offensive required the Polish front to be closed" is a feasibility constraint and is a guard, cited to the planning record.

Each action carries `source=` naming the contemporaneous record in which the alternative was debated or planned (Cabinet minutes, Hansard, the Führer conferences, DGFP, FRUS, the Imperial Conferences), with a date. An action with no such record is `speculative=True`. Delays are institutional lags, cited.

## Germany (`GER`)

| Action | Feasibility guard (sketch) | Effect | Delay | Source slot | Speculative? |
|---|---|---|---|---|---|
| `rearm` | `arms_GER < total` | `arms_GER += 1` | 4 (one year from decision to force) | rearmament programmes 1936 to 1939; Tooze | |
| `remilitarize_rhineland` | `rhineland == demilitarized ∧ arms_GER >= rising` | `rhineland := remilitarized; treaty := dead` | 0 | the March 1936 decision record | |
| `withdraw_rhineland` | `rhineland == remilitarized ∧ last_WEST == resist_rhineland` | `rhineland := demilitarized` | 0 | the documented March 1936 contingency to withdraw if France moved | |
| `court_italy` | `¬axis ∧ italy_estranged` | `axis := True` | 0 | the Oct 1936 protocols; the May 1939 Pact of Steel | |
| `annex_austria` | `austria == independent ∧ axis ∧ arms_GER >= rising` | `austria := annexed; ind_GER += 1` | 0 | the 1934 attempt blocked by Italy; the Feb to March 1938 record | |
| `demand_sudeten` | `sudeten == czech ∧ arms_GER >= high` | opens a crisis that WEST answers with `concede` or `declare_war`; raises `belief_WEST` to uncertain | 0 | the May and September 1938 record | |
| `occupy_bohemia` | `sudeten == german ∧ bohemia == czech` | `bohemia := german; ind_GER += 1; belief_WEST := hegemonic` | 0 | the March 1939 record | |
| `propose_pact_ussr` | `¬nazi_soviet_pact ∧ ¬anglo_soviet_alliance` | joint with USSR `accept_pact`: `nazi_soviet_pact := True; oil_GER := secured` | 0 | the August 1939 record | |
| `attack_poland` | `poland == independent ∧ arms_GER >= high` | `poland := partitioned` if the pact holds, else `german` after a campaign | 0 | Case White planning, April to August 1939 | |
| `attack_france` | `war_west_ger == war ∧ france == at_war ∧ poland != independent ∧ arms_GER >= high` | `france := fallen` via Nature `campaign_west` (nondeterministic: the 1940 outcome was contested in planning) | 0 | Case Yellow, Oct 1939 to May 1940 | |
| `air_offensive` | `france == fallen ∧ britain == at_war ∧ channel_air == contested` | Nature resolves `channel_air` | 0 | the July 1940 directives | |
| `invade_britain` | `channel_air == german ∧ france == fallen` | `britain := invaded` | 0 | Sea Lion planning, July to Sept 1940 | |
| `offer_terms_britain` | `france == fallen ∧ britain == at_war` | enables WEST `negotiate` | 0 | the July 1940 Reichstag speech | |
| `align_balkans` | `balkans == neutral ∧ (nazi_soviet_pact ∨ france == fallen)` | `balkans := german_aligned; oil_GER := secured` | 0 | the 1940 Romanian alignment | |

## The West (`WEST`)

| Action | Feasibility guard (sketch) | Effect | Delay | Source slot | Speculative? |
|---|---|---|---|---|---|
| `rearm` | `arms_WEST < high` | `arms_WEST += 1` | 4 | the 1936 Defence Requirements decisions; the French programmes | |
| `resist_rhineland` | `rhineland == remilitarized ∧ last_GER == remilitarize_rhineland` | `commit_WEST := wary` and opens a crisis | 0 | the French Cabinet, 7 to 9 March 1936; the Flandin mission | |
| `concede` | a German demand is open (`sudeten == czech ∧ last_GER == demand_sudeten`) | `sudeten := german; belief_WEST stays; commit_WEST := wary` | 0 | the Munich record, Sept 1938 | |
| `declare_war` | `war_west_ger == peace ∧ (a German attack on a guaranteed state or an open demand refused)` | `war_west_ger := war; france := at_war; britain := at_war; commit_WEST := at_war` | 0 | the Sept 1938 and Sept 1939 Cabinet records | |
| `guarantee_poland` | `poland == independent ∧ belief_WEST == hegemonic ∧ commit_WEST >= wary` | `polish_guarantee := True; commit_WEST := resolved` | 0 | Cabinet and Hansard, 17 to 31 March 1939 (the institutional feasibility rests on the belief change; this is the registered T4 claim) | |
| `approach_ussr` | `polish_guarantee ∧ ¬nazi_soviet_pact` | joint with USSR `accept_alliance`: `anglo_soviet_alliance := True` | 0 | the April to August 1939 talks | |
| `negotiate` | `france == fallen ∧ britain == at_war ∧ last_GER == offer_terms_britain` | `britain := negotiated` | 0 | the War Cabinet, 26 to 28 May 1940 (Lukacs 1999) | |
| `fight_on` | `france == fallen ∧ britain == at_war` | `commit_WEST := at_war` (no other effect) | 0 | the same record | |

## The Soviet Union (`USSR`)

| Action | Feasibility guard (sketch) | Effect | Delay | Source slot | Speculative? |
|---|---|---|---|---|---|
| `rearm` | `arms_USSR == weak` | `arms_USSR := strong` | 4 | the 1939 to 1941 expansion | |
| `accept_pact` | `last_GER == propose_pact_ussr ∧ ¬anglo_soviet_alliance` | with GER: pact | 0 | the August 1939 record | |
| `accept_alliance` | `last_WEST == approach_ussr ∧ ¬nazi_soviet_pact` | with WEST: alliance | 0 | the 1939 talks (Soviet conditions on Poland and the Baltics) | |
| `occupy_east_poland` | `nazi_soviet_pact ∧ poland == partitioned` | (already in `partitioned`) | 0 | 17 Sept 1939 | |
| `join_axis` | `aims_USSR == opportunist ∧ nazi_soviet_pact ∧ france == fallen` | `ussr_axis := True` | 0 | the Nov 1940 Berlin talks; the Soviet counter-conditions | |

## Japan (`JPN`)

| Action | Feasibility guard (sketch) | Effect | Delay | Source slot | Speculative? |
|---|---|---|---|---|---|
| `sign_anticomintern` | `¬anticomintern` | with GER: `anticomintern := True` | 0 | Nov 1936 | |
| `strike_north` | `anticomintern ∧ arms_JPN == high ∧ arms_USSR == weak ∧ war_west_ger == war` | opens `siberia` to Nature `campaign_siberia` | 0 | the 1938 to 1939 border fighting; the Nomonhan outcome as the constraint | |

## Nature

| Event | Guard | Effect | Source slot |
|---|---|---|---|
| `purge` | `arms_USSR == strong` | `arms_USSR := weak` | 1937 to 1938 |
| `campaign_west` | an attack on France is under way | resolves `france := fallen` or leaves `at_war` (nondeterministic) | the planning assessments of 1939 to 1940 |
| `air_battle` | an air offensive is under way | `channel_air := german` or `british` | July to Oct 1940 |
| `campaign_siberia` | `strike_north` under way | `siberia := japanese` only if `arms_USSR == weak` and the USSR is engaged in Europe; otherwise no effect | Nomonhan |
| `us_neutrality_revision` | `war_west_ger == war ∧ commit_US == isolationist` | `commit_US := wary` | Nov 1939 |
| `us_engages` | `france == fallen ∧ commit_US == wary` | `commit_US := engaged` | Sept 1940 |
| `italy_reconciles` | `italy_estranged ∧ ¬axis` | `italy_estranged := False` | the Stresa alternative, 1935 to 1936 |

## Constraints

- Fairness `democratic_response` on WEST: once `belief_WEST == hegemonic` and a German attack has occurred, WEST plays `declare_war` or `rearm` within 2 ticks. Source slot: the 1939 record.
- Profile `fight_on`: forbids `negotiate` (the registered T5 alternative).
- Profile `appeaser`: forbids `declare_war` while `belief_WEST != hegemonic`.
- Assume `ussr_defensive`: `aims_USSR == defensive`.

## Historian's review checklist (step 1.2)

- [ ] every action's source names a dated record in which the alternative was debated or planned
- [ ] every guard is a feasibility or institutional constraint, not a preference
- [ ] the actions that exist only for negative controls are marked and their guards cite the documented constraints
- [ ] no action needed by T1, T2, T4, T5, T8 or T10 is missing; nothing is added beyond what the record supports without a speculative tag
