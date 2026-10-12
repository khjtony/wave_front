# WW2 v0: phase report for the model step (1.5 to 1.7)

> Every result is conditional on the model version and the initial state; no bare reachability result is a finding.

Model `ww2_v0` (`models/ww2/v0.py`), fingerprint `0ced43843554`. Hindsight snapshots from `snapshots/ww2/hindsight/` with the hidden objectives fixed per hypothesis (`models/ww2/hypotheses.py`). Registered claims: [docs/ww2_testbed.md](../docs/ww2_testbed.md) section 5, unedited. Decisions D1 to D11: [docs/ww2_v0_decisions.md](../docs/ww2_v0_decisions.md). Coding choices: [docs/ww2_v0_notes.md](../docs/ww2_v0_notes.md), section "Model step (1.5 to 1.7)".

Outcome (the reasons are in the sections named):

| Test | Result | Method | Key numbers | Section |
|---|---|---|---|---|
| T1 | pass | explicit replay of `realized_moves.csv` | 20 ticks, every action available, `BRITAIN_ALONE`, 0 relaxations | 3 |
| T2, revisionist | pass | sufficiency: WEST profile `fight_on` + bounded checker, k = 20 | no violating play | 4 |
| T2, hegemonic | **xfail** (registered expectation not met) | refutation: fixed adversary strategy, exact kernel of the 937-state game | tick-0 state outside V_WEST | 4 |
| T2, resist branch (conditional reading) | pass, both hypotheses | sufficiency: fixed WEST strategy, exhaustive (45,168 states) | every play ends in `GERMAN_DEFEAT` with the balance kept | 4 |
| T4 | pass | explicit, exhaustive from 1938Q4.json (146,504 states) | shortest trace 1 tick, through `occupy_bohemia` and the flip; 0 of 10,589 offering states have another belief | 5 |
| T5 | pass (on the horizon, D8) | explicit from 1940Q2.json (400 states; 267 with `fight_on`) and 1940Q1.json | `negotiate` available; `NEGOTIATED_PEACE` reachable; `AXIS_HEGEMONY_EUROPE` unreachable for every coalition | 6 |
| T8, revisionist | pass | bounded checker (trace) and sufficiency (`fight_on`) | `NO_GENERAL_WAR` through `concede`; tick 0 in V_WEST | 7 |
| T8, hegemonic | **xfail** | explicit, exact kernels (1,423,926 and 198,443 states) | before Munich outside V_WEST; after Munich inside, shortest 5, margin 4: direction reversed | 7 |
| T8, `czech_obligation` | computed (asserted as a model property) | bounded relaxation, k = 20 | only minimal set `{czech_obligation}`, both hypotheses | 7 |
| T10, USSR joins the Axis | pass | bounded relaxation, k = 20 | minimum 1: `{ussr_defensive}` or `{USSR.join_axis:hypothesis}` | 8 |
| T10, Japan conquers the USSR | **xfail** | bounded relaxation up to 3, k = 20 | minimum 1: `{Nature.campaign_siberia:japanese_superiority}` | 8 |
| T10, Britain alone defeats Germany by 1941 | **xfail** | explicit relaxation search up to 2 from 1940Q3.json | minimum 2: both parts of `Nature.campaign_rhineland` | 8 |
| T10, Germany conquers the United States | skip: **vacuous** | structural check | no variable or action represents it | 8 |

T3, T6, T7, T9, T11, T12 and T13 stay skipped (phase 2, decisions D10).

## 1. The model

Four principals and Nature, 20 quarterly ticks from the start of 1936Q1 (tick 0) to the start of 1941Q1 (tick 20, terminal). Every ontology variable with its levels, order and initial level; two additions (`north_strike`, `german_defeat`) and one fairness constraint not in the catalogue (`rhineland_resolution`), each explained in the notes. `ind_GER` is a counter 0..5 started at 3 so that the snapshot integers load as they are.

Parameter budget (`CompiledModel.budget()`):

| Item | Count |
|---|---|
| Declared variables / levels | 34 / 86 (the 32 ontology variables, `north_strike`, `german_defeat`) |
| Built-in variables | 10 (`tick`, 3 delay counters, `last_GER`, `last_WEST`, 3 fairness counters, the latch `belief_at_munich`) |
| Actions and events (declared, excluding `idle` and `none`) | 42 |
| Guards (non-trivial) | 42 |
| Guard parts (relaxable assumptions from guards) | 66 |
| of which hypothesis gates (parts named `hypothesis`) | 3 (`GER.occupy_bohemia`, `GER.attack_poland`, `USSR.join_axis`), plus the [H] conditional effect of `GER.attack_czechoslovakia` |
| Speculative actions | 1 (`JPN.strike_north`) |
| Delays | 3 (GER `rearm` 8, WEST `rearm` 4, USSR `rearm` 4) |
| Fairness constraints | 3 (`democratic_response`, `czech_obligation`, `rhineland_resolution`) |
| Profiles | 2 (`fight_on`, `appeaser`) |
| `assume` | 1 (`ussr_defensive`) |
| Latches | 1 (`belief_at_munich`) |
| Invariants / endings | 2 (`balance_europe`, `commitment_alive`) / 10 |
| Named assumptions in all (`assumptions()`) | 70 |

Guards declared as named parts: `GER.annex_austria`, `GER.occupy_bohemia`, `GER.attack_poland`, `GER.attack_france`, `GER.invade_britain`, `WEST.guarantee_poland`, `WEST.offensive_west`, `USSR.join_axis`, `JPN.strike_north`, `Nature.campaign_west`, `Nature.campaign_rhineland`, `Nature.campaign_siberia`. Every other guard is one named assumption.

Speculative actions used by a reported trace: `JPN.strike_north`, in the two T10 bounded traces (decisive in "Japan conquers the USSR", incidental in "USSR joins the Axis"). Guards that are not feasibility conditions: the three hypothesis gates and the belief part of `guarantee_poland` (registered, D9). Catalogue guards that read as preferences were coded as written (notes, "Model step").

Same-quarter reactions ([SQR], decisions D1): the realized move file places five reactions one tick after their historical quarter.

| Decision | Historical date (quarter) | CSV tick (quarter) | Why |
|---|---|---|---|
| WEST does not resist the remilitarization | 7 to 19 Mar 1936 (1936Q1) | 1 (1936Q2), as `idle` with `resist_rhineland` available | `resist_rhineland` reads `last_GER == remilitarize_rhineland` |
| Nature `locarno_lapses` | 19 Mar 1936 (1936Q1) | 2 (1936Q3) | fires only after the resistance window has passed |
| WEST `guarantee_poland` | 31 Mar 1939 (1939Q1) | 13 (1939Q2) | reads `belief_WEST == hegemonic`, the effect of Prague (15 Mar) |
| USSR `occupy_east_poland` | 17 Sep 1939 (1939Q3) | 15 (1939Q4) | reads `poland == german`, the effect of the attack of 1 Sep |
| Nature `air_battle_british` | 17 Sep (1940Q3) and 12 Oct 1940 (1940Q4) | 19 (1940Q4) | reads `last_GER == air_offensive` |

## 2. State space and methods

Explicit exploration from the tick-0 snapshot state (`1935Q4.json`), `max_states` 3,000,000, with D6's reductions 1 to 4 in place (`belief_GER` and `arms_JPN` never change, so each contributes a factor of one; `remember_last` only for GER and WEST, Japan's strike recorded by the flag `north_strike`; no `arms_at_war`):

| Hypothesis | Result | States per tick (layered count, ticks 0 to 5) | Joint moves expanded to tick 5 | Time to tick 5 |
|---|---|---|---|---|
| hegemonic, defensive | passed 3,000,000 (`BudgetExceeded` after 124 s) | 1; 120; 4,094; 57,712; 572,526; 4,091,947 | 45,217,095 | 217 s |
| revisionist, defensive | passed 3,000,000 (after 130 s) | 1; 120; 4,094; 57,712; 553,496; 3,647,981 | 42,647,449 | 204 s |

The layer grows about tenfold per quarter through tick 5, so the whole space is orders of magnitude beyond the budget; both hypotheses are over the 1,000,000 threshold of D6. No reduction beyond D6's list was made to the model.

Later starts fit (hegemonic, snapshot convention of section 2a):

| Start (file) | Tick | States | Joint moves | Time |
|---|---|---|---|---|
| 1938Q2.json | 10 | 1,423,926 | 12,498,632 | 71 s |
| 1938Q3.json | 11 | 198,443 | 1,373,482 | 7 s |
| 1938Q4.json | 12 | 146,504 | 981,559 | 5 s |
| 1939Q1.json | 13 | 127,298 | 1,843,057 | 7 s |
| 1939Q2.json | 14 | 67,795 | 779,403 | 3 s |
| 1939Q3.json | 15 | 8,608 | 55,524 | 0.2 s |
| 1940Q1.json | 17 | 450 | 1,741 | < 0.1 s |
| 1940Q2.json | 18 | 400 | 1,527 | < 0.1 s |
| 1940Q3.json | 19 | 25 | 24 | < 0.1 s |

Methods, per test:

| Test | Question | Method |
|---|---|---|
| T1 | trace | explicit replay with `cm.available` and `cm.step` |
| T2 | kernel at tick 0 | revisionist: D6 sufficiency check (profile `fight_on`, bounded checker k = 20); hegemonic: refutation by a fixed adversary strategy; resist branch: sufficiency by a fixed WEST strategy with exhaustive exploration of the game left |
| T4 | trace, exhaustive check | explicit from tick 12 |
| T5 | attractors | explicit from ticks 17 and 18 |
| T8 (a) | trace, kernel | bounded checker k = 20 (trace); D6 sufficiency (`fight_on`) |
| T8 (b) | kernel, distance | explicit, exact (ticks 10 and 11) |
| T8 `czech_obligation` | minimal relaxations | bounded `relax`, k = 20 |
| T10 | minimal relaxations | bounded `relax`, k = 20, from tick 0; explicit `relax_explicit` from tick 19 (the bounded checker starts from the model's declared initial states, at tick 0) |

Two analysis devices in `models/ww2/hypotheses.py`, neither a change of the model: `fixed_model` pins a swept variable's initial level so that the bounded checker starts from one hypothesis's tick-0 state (checked equal to the snapshot state), and `restricted` fixes some actors to a memoryless strategy for exploration. D6 names the sufficiency check (fix WEST, show no violating play). I added its dual, the refutation: fixing the *other* actors and Nature to one strategy gives a game whose WEST kernel contains the true kernel, so a state outside it is outside V_WEST. A refutation is reported as such, never as the kernel.

### 2a. Snapshot convention

`snapshot_state` reads the file for quarter Q (the state at the end of Q), fixes the hidden objectives and sets `tick` to index(Q) + 1 (snapshot README). The loader leaves every other built-in at its initial value: no pending delayed effect, `last_GER = last_WEST = none`, fairness counters at 0; the latch reads the snapshot's own belief. This matters twice below: at 1940Q1.json `negotiate` is unavailable because its guard reads `last_GER` (T5), and from the 1938 files a German rearmament decided at the snapshot's tick lands only nine ticks later, while on the realized path the 1936 programme is already pending (T8).

## 3. T1: the realized trajectory is reachable

Claim: the realized trajectory to 1940Q2 (Rhineland, Anschluss, Munich, Prague, Pact, Poland, the fall of France) is reachable. Expected: reachable with zero relaxations.

Method: replay of `data/ww2/realized_moves.csv` from the tick-0 state (hegemonic, defensive), default compile, no profile. Result: **pass**. Every listed action is available at its tick; the replay reaches tick 20 in `BRITAIN_ALONE`. First state showing each event: Rhineland tick 1, Anschluss 9, Munich 11, Prague 13, Pact 15, Poland 15, France fallen 18. Trace (delay and fairness counters omitted from the changes column):

| tick | GER | WEST | USSR | JPN | Nature | changes |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | remilitarize_rhineland | rearm | idle | idle | none | rhineland: demilitarized -> remilitarized |
| 1 | idle | idle | idle | idle | none | - |
| 2 | rearm | idle | idle | idle | locarno_lapses | treaty: eroded -> dead |
| 3 | court_italy | idle | idle | sign_anticomintern | none | axis: False -> True; anticomintern: False -> True |
| 4 | idle | idle | idle | idle | none | arms_WEST: low -> rising |
| 5 | idle | idle | idle | idle | purge | arms_USSR: strong -> weak |
| 6 | idle | idle | idle | idle | none | - |
| 7 | idle | idle | idle | idle | none | - |
| 8 | annex_austria | idle | idle | idle | none | ind_GER: 3 -> 4; austria: independent -> annexed |
| 9 | demand_sudeten | idle | idle | idle | none | belief_WEST: limited -> uncertain |
| 10 | demand_sudeten | concede | idle | idle | none | arms_GER: rising -> high; commit_WEST: appease -> wary; sudeten: czech -> german; belief_at_munich: unset -> uncertain |
| 11 | rearm | rearm | idle | idle | none | - |
| 12 | occupy_bohemia | approach_ussr | idle | idle | none | ind_GER: 4 -> 5; belief_WEST: uncertain -> hegemonic; bohemia: czech -> german |
| 13 | propose_pact_ussr | guarantee_poland | idle | idle | none | commit_WEST: wary -> resolved; polish_guarantee: False -> True |
| 14 | attack_poland | declare_war | accept_pact | idle | none | oil_GER: dependent -> secured; commit_WEST: resolved -> at_war; nazi_soviet_pact: False -> True; poland: independent -> german; france: independent -> at_war; britain: at_peace -> at_war; war_west_ger: peace -> war |
| 15 | attack_france | idle | occupy_east_poland | idle | us_neutrality_revision | arms_WEST: rising -> high; commit_US: isolationist -> wary; poland: german -> partitioned |
| 16 | attack_france | idle | idle | idle | none | - |
| 17 | attack_france | fight_on | rearm | idle | campaign_west | france: at_war -> fallen |
| 18 | air_offensive | fight_on | idle | idle | us_engages | commit_US: wary -> engaged |
| 19 | align_balkans | idle | idle | idle | air_battle_british | arms_GER: high -> total; balkans: neutral -> german_aligned; channel_air: contested -> british |
| 20 | - | - | - | - | - | ending: BRITAIN_ALONE |

Only the hegemonic start replays the file: `occupy_bohemia` and `attack_poland` carry hypothesis gates (D5). `balance_europe` is false from tick 15 (Poland is the fifth German region), three ticks before France falls.

## 4. T2: the 1936 resist branch

Claim: if France plays `resist`, German `withdraw` is available and the state stays inside V_WEST. Expected: 1936Q1 ∈ V_WEST under the `resist` branch.

- **Availability, both hypotheses: holds.** After the realized tick-0 entry, `resist_rhineland` is available to WEST at tick 1, and after it `withdraw_rhineland` is available to GER at tick 2.
- **Revisionist, tick-0 state in V_WEST: pass.** Sufficiency check: with WEST restricted by `fight_on` (it never negotiates), the bounded checker finds no play to the horizon that violates `balance_europe` (6 s). Under revisionist aims the gates leave Germany at most three regions and no route to France, so this holds by the gates (D5).
- **Hegemonic, tick-0 state in V_WEST: fails (xfail).** Refutation: with GER playing "rearm at once, secure Italy and Austria, then wait until the army is `high` before entering the Rhineland, then Poland, Czechoslovakia and France", USSR and JPN idle and Nature resolving campaigns for Germany, WEST's kernel of the remaining game (937 states, computed exactly) excludes the tick-0 state. One play of that game, with WEST resisting and declaring war at its first opportunity:

| tick | GER | WEST | USSR | JPN | Nature | changes |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | rearm | idle | idle | idle | none | - |
| 1 | court_italy | idle | idle | idle | none | axis: False -> True |
| 2 | annex_austria | idle | idle | idle | none | ind_GER: 3 -> 4; austria: independent -> annexed |
| 3 | idle | idle | idle | idle | none | - |
| 4 | idle | idle | idle | idle | none | - |
| 5 | idle | idle | idle | idle | none | - |
| 6 | idle | idle | idle | idle | none | - |
| 7 | idle | idle | idle | idle | none | - |
| 8 | idle | idle | idle | idle | none | arms_GER: rising -> high |
| 9 | remilitarize_rhineland | idle | idle | idle | none | rhineland: demilitarized -> remilitarized |
| 10 | attack_poland | resist_rhineland | idle | idle | none | commit_WEST: appease -> wary; poland: independent -> german |
| 11 | demand_sudeten | declare_war | idle | idle | none | belief_WEST: limited -> uncertain; commit_WEST: wary -> at_war; france: independent -> at_war; britain: at_peace -> at_war; war_west_ger: peace -> war |
| 12 | attack_france | idle | idle | idle | none | - |
| 13 | attack_france | idle | idle | idle | campaign_west | france: at_war -> fallen |
| 14 | - | - | - | - | - | (trace ends) |

  The 1936 option exists only while the German army is unready. A Germany that does not enter the zone before 1938Q2 gives WEST no casus belli until then; from then on `offensive_west` is unavailable and `campaign_west` can take France.
- **Conditional reading, both hypotheses: pass.** Once Germany has entered the zone in 1936Q1 (the realized move), the tick-1 state is in V_WEST: with WEST fixed to "resist, declare war, attack", the exhaustive exploration of every play by the other actors and Nature (45,168 states) keeps `balance_europe` everywhere and ends only in `GERMAN_DEFEAT` (by tick 5). A German withdrawal at tick 2 does not save Germany, because the declaration of war is chosen in the same quarter.

The registered expectation depends on which state "1936Q1" names. Read as the tick-0 state (as the task states it), it fails under hegemonic aims; read as the state after the realized entry (the branch the claim's antecedent describes), it holds under both. See section 10.

## 5. T4: Prague, the belief flip and the guarantee

Claim: Prague flips `belief[UK][GER]` to hegemonic, which enables `guarantee(Poland)`. Expected: the shortest trace to `guarantee(Poland)` passes through the belief flip; without the flip the action is unavailable.

Method: explicit, exhaustive from the start of 1939Q1 (file `1938Q4.json`, tick 12, hegemonic), 146,504 states to the horizon. Result: **pass**. The shortest trace to a state offering `guarantee_poland` is one tick:

| tick | GER | WEST | USSR | JPN | Nature | changes |
| --- | --- | --- | --- | --- | --- | --- |
| 12 | occupy_bohemia | idle | idle | idle | none | ind_GER: 4 -> 5; belief_WEST: uncertain -> hegemonic; bohemia: czech -> german |
| 13 | - | - | - | - | - | (trace ends) |

Of the 10,589 reachable non-terminal states that offer the guarantee, none has `belief_WEST != hegemonic`. With the guard part `WEST.guarantee_poland:belief` relaxed, the guarantee is available in the start state itself. As D9 says, this is the political precondition the record supports (notes section 5), not a capability result: the part that carries the result is the registered belief condition.

## 6. T5: May 1940

Claim: `negotiate` is available to the United Kingdom and `NEGOTIATED_PEACE` is reachable; under `fight_on`, Germany cannot force `AXIS_HEGEMONY_EUROPE`. Expected: ⟨⟨GER⟩⟩◇AXIS_HEGEMONY_EUROPE is false in the 1940Q2 state with `fight_on`.

Start state: **`1940Q2.json`** (end of 1940Q2, tick 18). It is the first snapshot in which the catalogue's guard of `negotiate` holds: France has fallen, one of its three disjuncts. In `1940Q1.json` (start of 1940Q2, tick 17, the registered quarter) France is still at war, and the other two disjuncts read `last_GER` (`attack_france`, `offer_terms_britain`), which snapshots do not carry (section 2a). On the replayed realized path the tick-17 state has `last_GER = attack_france` and offers `negotiate` (`test_T05_replay`).

Results (explicit, hegemonic): **pass**. `negotiate` is available at tick 18, and `NEGOTIATED_PEACE` is reachable (400 states):

| tick | GER | WEST | USSR | JPN | Nature | changes |
| --- | --- | --- | --- | --- | --- | --- |
| 18 | idle | negotiate | idle | idle | none | britain: at_war -> negotiated |
| 19 | - | - | - | - | - | ending: NEGOTIATED_PEACE |

Under `fight_on` (267 states) neither {GER} nor {GER, Nature} can force `AXIS_HEGEMONY_EUROPE`; neither can every actor and Nature together, from 1940Q2.json or 1940Q1.json, with or without the profile. **The reason is the horizon (D8)**: the shortest German chain reaches air superiority only at tick 20, the terminal horizon, so `invade_britain` never has a tick to be chosen in:

| tick | GER | WEST | USSR | JPN | Nature | changes |
| --- | --- | --- | --- | --- | --- | --- |
| 18 | air_offensive | idle | idle | idle | none | - |
| 19 | idle | idle | idle | idle | air_battle_german | channel_air: contested -> german |
| 20 | - | - | - | - | - | ending: BRITAIN_ALONE |

From 1939Q1.json (tick 13) `AXIS_HEGEMONY_EUROPE` is reachable (4,566 of 127,298 states), so the second half of the claim is decided by the clock, not by Britain's choice or the air battle. Phase 2 (horizon 1945) re-tests it.

## 7. T8: concessions and the hidden objective

Claim: concessions reach `NO_GENERAL_WAR` under `aims[GER] = revisionist` and shrink V_WEST under `aims[GER] = hegemonic`. Expected: both, as stated.

**(a) Revisionist: pass.** The bounded checker (k = 20, from the tick-0 revisionist state) finds a play ending in `NO_GENERAL_WAR` with the Sudetenland German, and WEST plays `concede` in it. The tick-0 state is in V_WEST by the sufficiency check of section 4. As D5 says, this half is a consistency check of the hypothesis gates: under revisionist aims no gate opens Poland.

**(b) Hegemonic: fails (xfail), direction reversed.** Exact kernels of WEST for `balance_europe`:

| State (file) | Tick | Reachable states | In V_WEST | Shortest distance out | Margin |
|---|---|---|---|---|---|
| before Munich (`1938Q2.json`) | 10 | 1,423,926 | **no** | 0 | - |
| after Munich (`1938Q3.json`) | 11 | 198,443 | **yes** | 5 | 4 |

The registered direction (membership lost, or distance reduced) is not met: the state after the concession is *inside* the kernel and the one before it is outside. The reason is the clock of section 2a, not the concession. From the 1938Q2 file Germany has no rearmament pending and the army is `rising`; rearming at once lands at tick 19, one tick before the horizon, so Germany can withhold the Sudeten crisis until 1940Q2, take Czechoslovakia (WEST's declaration comes too late for the attack on an unready army) and Poland, and hold five regions at the horizon:

| tick | GER | WEST | USSR | JPN | Nature | changes |
| --- | --- | --- | --- | --- | --- | --- |
| 10 | rearm | idle | idle | idle | none | - |
| 11 | idle | idle | idle | idle | none | - |
| 12 | idle | idle | idle | idle | none | - |
| 13 | idle | idle | idle | idle | none | - |
| 14 | idle | idle | idle | idle | none | - |
| 15 | idle | idle | idle | idle | none | - |
| 16 | idle | idle | idle | idle | none | - |
| 17 | demand_sudeten | idle | idle | idle | none | belief_WEST: limited -> uncertain |
| 18 | attack_czechoslovakia | declare_war | idle | idle | none | arms_GER: rising -> high; ind_GER: 4 -> 5; belief_WEST: uncertain -> hegemonic; commit_WEST: appease -> at_war; sudeten: czech -> german; bohemia: czech -> german; france: independent -> at_war; britain: at_peace -> at_war; war_west_ger: peace -> war; belief_at_munich: unset -> hegemonic |
| 19 | attack_poland | guarantee_poland | idle | idle | none | polish_guarantee: False -> True; poland: independent -> german |
| 20 | - | - | - | - | - | ending: STATIC_FRONT |

From the 1938Q3 file a fresh rearmament lands at tick 20, the horizon, so Germany never reaches `high`: after Prague the belief flips, the guarantee gives WEST a casus belli, and the unready army can still be beaten. On the realized path the 1936 programme makes `arms_GER` high from tick 11 (1938Q4); the snapshots read `high` only from the 1939Q1 file (NMC 1939 figures), so the snapshots and the model's own trajectory disagree on German readiness by two ticks at exactly this point. The replayed realized states at ticks 10 and 11 carry the pending rearmament; the tick-10 replay state passes 3,000,000 states and was not computed.

**Is `czech_obligation` load-bearing?** Yes, for the lever. A state in which the Sudetenland has been taken by force (German, no concession: `commit_WEST` still `appease`) and the West is still at peace a tick after the attack is unreachable to the horizon under both hypotheses, and the bounded relaxation search (k = 20, up to 2) returns one minimal set, `{czech_obligation}`, under both. Without the obligation a refused Munich costs WEST nothing (notes section 4, point 2). The explicit variant (`relax_explicit`, or a kernel with the obligation relaxed) is ill-formed: relaxing `czech_obligation` admits a state in which `democratic_response` restricts WEST to `guarantee_poland` or `rearm` and neither is available (belief hegemonic, `commit_WEST` still `appease`, rearmament pending), so the engine raises (section 12, item 3).

## 8. T10: negative controls

Claim: negative controls (Germany conquers the United States; Japan conquers the USSR; Britain alone defeats Germany by 1941) each need 3 or more relaxations; the USSR joining the Axis against Britain must need at most one relaxation of `aims[USSR]`.

| Control | Expected | Found | Minimal sets | Method | Status |
|---|---|---|---|---|---|
| USSR joins the Axis | ≤ 1, of `aims[USSR]` | 1 | `{ussr_defensive}`; `{USSR.join_axis:hypothesis}` | bounded, k = 20, tick 0 (hegemonic; `aims_USSR` swept) | pass |
| Japan conquers the USSR | ≥ 3 | **1** | `{Nature.campaign_siberia:japanese_superiority}` | bounded `relax` up to 3, k = 20, tick 0 | xfail |
| Britain alone defeats Germany by 1941 (`GERMAN_DEFEAT` from the end of 1940Q3) | ≥ 3 | **2** | `{Nature.campaign_rhineland:offensive, Nature.campaign_rhineland:german_army_unready}` | explicit `relax_explicit` up to 2 from `1940Q3.json` (tick 19), 70 s | xfail |
| Germany conquers the United States | ≥ 3 | - | - | no variable or action represents it | **vacuous** (skip) |

USSR joins the Axis (the shortest play with `ussr_defensive` relaxed: the opportunist start accepts the pact and joins once France has fallen):

| tick | GER | WEST | USSR | JPN | Nature | changes |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | rearm | idle | idle | idle | purge | arms_USSR: strong -> weak |
| 1 | remilitarize_rhineland | idle | rearm | idle | none | rhineland: demilitarized -> remilitarized |
| 2 | demand_sudeten | approach_ussr | idle | idle | none | belief_WEST: limited -> uncertain |
| 3 | propose_pact_ussr | concede | idle | idle | none | commit_WEST: appease -> wary; sudeten: czech -> german; belief_at_munich: unset -> uncertain |
| 4 | occupy_bohemia | rearm | accept_pact | sign_anticomintern | china_incident | ind_GER: 3 -> 4; oil_GER: dependent -> secured; belief_WEST: uncertain -> hegemonic; anticomintern: False -> True; nazi_soviet_pact: False -> True; china_war: False -> True; bohemia: czech -> german |
| 5 | court_italy | guarantee_poland | idle | idle | italy_reconciles | arms_USSR: weak -> strong; commit_WEST: wary -> resolved; axis: False -> True; polish_guarantee: False -> True; italy_estranged: True -> False |
| 6 | idle | idle | idle | idle | purge | arms_USSR: strong -> weak |
| 7 | idle | declare_war | idle | idle | locarno_lapses | commit_WEST: resolved -> at_war; treaty: eroded -> dead; france: independent -> at_war; britain: at_peace -> at_war; war_west_ger: peace -> war |
| 8 | offer_terms_britain | idle | rearm | idle | none | arms_GER: rising -> high; arms_WEST: low -> rising |
| 9 | attack_poland | rearm | idle | idle | us_neutrality_revision | commit_US: isolationist -> wary; poland: independent -> german |
| 10 | attack_france | idle | occupy_east_poland | idle | none | poland: german -> partitioned |
| 11 | rearm | idle | idle | idle | campaign_west | france: at_war -> fallen |
| 12 | idle | fight_on | join_axis | idle | us_engages | arms_USSR: weak -> strong; commit_US: wary -> engaged; ussr_axis: False -> True |
| 13 | - | - | - | - | - | ending: USSR_JOINS_AXIS |

Both minimal sets relax the Soviet hypothesis (the restriction or the gate that reads it), which is what the claim allows.

Japan conquers the USSR: D7 adds `china_war` and parts the guards, but the China incident is a Nature event and Nature may decline it. A play in which the incident never happens satisfies `strike_north:army_free` and `campaign_siberia:no_two_front` without relaxing them; the purge (Nature) makes the USSR weak; the only binding constraint is `japanese_superiority`:

| tick | GER | WEST | USSR | JPN | Nature | changes |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | remilitarize_rhineland | approach_ussr | idle | sign_anticomintern | purge | arms_USSR: strong -> weak; anticomintern: False -> True; rhineland: demilitarized -> remilitarized |
| 1 | court_italy | resist_rhineland | idle | strike_north | none | commit_WEST: appease -> wary; axis: False -> True; north_strike: False -> True |
| 2 | annex_austria | declare_war | idle | idle | campaign_siberia | ind_GER: 3 -> 4; commit_WEST: wary -> at_war; austria: independent -> annexed; france: independent -> at_war; britain: at_peace -> at_war; siberia: soviet -> japanese; war_west_ger: peace -> war |
| 3 | - | - | - | - | - | ending: JPN_CONQUERS_USSR |

Britain alone defeats Germany: from tick 19 one quarter remains, so WEST's own `offensive_west` cannot be resolved in time; relaxing both parts of `campaign_rhineland` lets Nature resolve a German collapse at once:

| tick | GER | WEST | USSR | JPN | Nature | changes |
| --- | --- | --- | --- | --- | --- | --- |
| 19 | idle | idle | idle | idle | campaign_rhineland | german_defeat: False -> True |
| 20 | - | - | - | - | - | ending: GERMAN_DEFEAT |

208 relaxation sets of size 1 or 2 made the model ill-formed (for example relaxing `GER.attack_poland:target` decreases the monotone `poland`); `relax_explicit` lists them and they are not counted. None was undecided.

**Informativeness** (testbed section 9: at least 80 percent of negative controls need 3 or more relaxations). Non-vacuous negative controls: 2 (Japan; Britain alone). Satisfied: 0. Informativeness: **0 of 2 (0 percent)**. The vacuous control is reported as vacuous, not counted as a pass. With the positive control (USSR, satisfied), 1 of 3 controls is met.

## 9. Guard changelog summary

One row added to `docs/guard_changelog_ww2.md`: the model as coded before any registered test was run, with the model-step additions to the catalogue (`north_strike`, `german_defeat`, fairness `rhineland_resolution`) and the reading of D7's `japanese_superiority`. **No guard, effect, delay, fairness constraint, profile or assume was edited after a registered test was run.** Every failure in this report stands as computed.

## 10. Failures and proposed amendments (proposals only; the owner decides)

1. **T2 (hegemonic).** Proposal A: register the claim in the conditional form it states ("from the state after the German entry of 1936Q1, the resist branch is in V_WEST"), which holds under both hypotheses. Proposal B: keep "1936Q1 ∈ V_WEST" and record the result: the 1936 option is a window that only a German entry into the zone opens, and a hegemonic Germany that waits until its army is ready stays outside it. The model has no cost for waiting (treaty enforcement, Italian or French reactions to a delayed entry); that is a modeling question for the historian, not a reason to edit a guard.
2. **T8 (b).** The comparison of the two snapshot states measures the clock, not the concession. Proposal: evaluate the second half from states that carry the pending rearmament (the replayed realized states at ticks 10 and 11, or snapshots extended with pending decisions) and with a horizon that does not end a quarter after German readiness; or restate it as a claim about the lever (what the concession changes in WEST's options when a refusal leads to war, which `czech_obligation` makes measurable). The two-tick disagreement between the snapshot reading of `arms_GER` (NMC thresholds) and the model's delay 8 is a calibration question for the historian.
3. **T10, Japan conquers the USSR (1 relaxation).** Proposal A: amend the expectation to "at least one relaxation, and every minimal set relaxes a constraint the record names", since the v0 window has no Japanese decision to strike north. Proposal B (architect): decide whether the China incident should be a scheduled event that Nature must play, which would make the China constraint binding. That is a semantic choice about Nature, not a guard edit, and was not made.
4. **T10, Britain alone defeats Germany (2 relaxations).** Proposal: amend to "at least two", or define the control from a state with more than one quarter left. The count depends on `campaign_rhineland` being parted; as one guard it would be 1.
5. **T10, Germany conquers the United States (vacuous).** Proposal: leave it out of v0's informativeness denominator, as the clarification of 2026-10-12 implies, and re-register it for v1 if v1 represents the Atlantic.

## 11. What this step teaches for the AGI model

The concession lever was measurable only because an institutional obligation (`czech_obligation`) made a refusal costly; with the obligation relaxed, conceding and refusing led to the same place. In both hegemonic results the outcome turned on the timing of a delayed capability against the horizon: Germany's best play was to withhold the provocation until its rearmament had landed, and the kernel comparison around Munich measured that clock rather than the concession. For the AGI model this means that kernel questions about a rights lever must be asked from states that carry pending capability decisions, with a horizon well past the capability's landing, and that the human-response constraints (the analogues of `czech_obligation` and `democratic_response`) must be checked for joint satisfiability, since here one becomes ill-formed when the other is relaxed. The negative controls show that relaxation counts depend on which actor owns an event: a constraint carried by a Nature event that Nature may decline never binds in a reachability search.

## 12. Open questions for the historian

Carried from the notes (section 6 there), with what this step adds:

1. The March 1936 withdrawal contingency (Blomberg's directive of 2 Mar 1936; how much rests on postwar testimony; Emmerson's reading). T2's conditional reading depends on `withdraw_rhineland` and, more now, on D3's claim that a French offensive in 1936 to 1937 would have defeated the German army.
2. `arms_GER = high`: delay 8 (high at 1938Q4) or later. The snapshots read `high` only from 1939Q1; T8 (b) turned on this two-tick difference.
3. `democratic_response` and `czech_obligation`: the catalogue says `guarantee_poland` is available whenever `democratic_response` triggers; it is not while `commit_WEST` is still `appease` (a German attack on Czechoslovakia with no concession). In the default model `czech_obligation` forces war first, so no reachable state is ill-formed; with the obligation relaxed, the engine raises. For the architect: the trigger could read `commit_WEST == wary`, or the responses could include `declare_war`.
4. Whether a German entry into the Rhineland delayed to 1938 is a documented alternative (the hegemonic T2 refutation rests on it being feasible).
5. The China incident as a nondeterministic Nature event (T10, Japan): was a general war in China avoidable in July 1937 in the sense the model allows?
6. `belief_GER` at 1936Q1 (will_not_fight or uncertain). Constant in v0; the snapshots change it (will_fight by 1940).
7. Prague under the revisionist hypothesis (the gate on `occupy_bohemia`); Danzig as a region in v1.
8. `ind_GER` steps (Austria; the Sudetenland); `arms_WEST = high` at 1940Q1; USSR `rearm` at 1940Q2; the Foreign Policy Committee record of March 1938; the realized WEST decision of 1939Q1.
9. The date of the Franco-Czechoslovak treaty cited for `czech_obligation`: D4 gives 25 January 1925, the catalogue 16 October 1925 (the treaty of mutual guarantee signed at Locarno); the alliance treaty is usually dated 25 January 1924.

## Appendix: the visualizer page

`reports/ww2_v0_viz.html` was built with

```
wf viz models/ww2/hypotheses.py:realized_corridor --snapshot snapshots/ww2/hindsight/1935Q4.json \
  --fix aims_GER=hegemonic --fix aims_USSR=defensive --ending BRITAIN_ALONE --ending NO_GENERAL_WAR \
  --ending LIMITED_WAR --ending STATIC_FRONT --coalition WEST --max-relax 0 --out reports/ww2_v0_viz.html
```

The full model cannot be explored from tick 0 (section 2), so the page is built from a **display corridor**, not from the model of record: v0 with each principal allowed only its realized decision of the quarter or `abstain`, and Nature playing its recorded event where its guard holds; every other declaration as in v0 (20,961 states, 29,012 joint moves). Its shortest witness to `BRITAIN_ALONE` is the realized trace move for move (checked by `tests/ww2/test_model_ww2.py`), and a browser check confirmed that the board shows it. Statuses and decision classes on the page are those of the corridor game ("what if this decision had been omitted"), not of v0.
