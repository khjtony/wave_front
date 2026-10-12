# WW2 v0 working notes (phase 1, steps 1.1 and 1.2)

Status: historian-facing working notes for the draft of [ontology_ww2.md](ontology_ww2.md), [actions_ww2.md](actions_ww2.md) and `data/ww2/realized_moves.csv`. They record the conventions used, a check of the draft catalogue against the realized sequence, what the catalogue implies for the registered tests, open questions, and the citations least certain. Nothing here edits a registered claim ([ww2_testbed.md](ww2_testbed.md) section 5).

## 1. What was filled

- ontology_ww2.md: threshold rules with indicators for every variable, the 1936Q1 initial levels with dated evidence (section 2a), the hypothesis-space sources for both hidden objectives, section 7 extended with the omissions that touch T1, T2, T4, T5, T8 and T10, and a list of departures (section 9).
- actions_ww2.md: every guard in the DSL's vocabulary, effects, delays with reasons, `source=` text for every action and event, speculative tags, constraints, a parameter budget and a list of departures.
- realized_moves.csv: one row per tick 0 to 19, with dates and sources.

## 2. Tick convention and same-quarter reactions

The state at tick t is the start of quarter t; the row at tick t holds what each actor decided during quarter t; effects are visible at t + 1. A row's tick is the quarter of the **decision record** (a directive, a Cabinet conclusion, a signature), not of the execution when the two differ. Two consequences:

1. Where the decision and the execution fall in different quarters the CSV uses the decision. `demand_sudeten` is at 1938Q2 (Case Green directive, 30 May 1938) and again at 1938Q3 (the cession demand); `attack_france` is at 1939Q4 (Directive No. 6), 1940Q1 (the revised plan) and 1940Q2 (the launch).
2. **Same-quarter reaction [SQR].** When an actor reacted within a quarter to another actor's decision of the same quarter, and the catalogue reads the first decision through its effect or through `last_X`, the reaction cannot be available until the next tick. Those rows are placed at the next tick and marked [SQR] in the CSV note with the historical date. This is a mechanical rule, applied so that T1's replay can run; it is a departure from the instruction to place every decision in its historical quarter, and the strict variant is given below.

| Decision | Historical date (quarter) | CSV tick (quarter) | Why |
|---|---|---|---|
| WEST does not resist the remilitarization | 7 to 19 Mar 1936 (1936Q1) | 1 (1936Q2), as `idle` with `resist_rhineland` available | `resist_rhineland` reads `last_GER == remilitarize_rhineland` |
| Nature `locarno_lapses` | 19 Mar 1936 (1936Q1) | 2 (1936Q3) | fires only after the resistance window has passed |
| WEST `guarantee_poland` | 31 Mar 1939 (1939Q1) | 13 (1939Q2) | reads `belief_WEST == hegemonic`, the effect of Prague (15 Mar) |
| USSR `occupy_east_poland` | 17 Sep 1939 (1939Q3) | 15 (1939Q4) | reads `poland == german`, the effect of the attack of 1 Sep; also the second Soviet decision of 1939Q3 |
| Nature `air_battle_british` | 17 Sep (1940Q3) and 12 Oct 1940 (1940Q4) | 19 (1940Q4) | reads `last_GER == air_offensive` (Directive No. 17, 1 Aug 1940); the 12 Oct postponement is in the tick's quarter, the 17 Sep one is not |

**Strict variant.** Placing the guarantee at tick 12 (its quarter) and the four-power proposal of 20 Mar 1939 nowhere, the replay stops at tick 12: `guarantee_poland` is unavailable because `belief_WEST` is still `uncertain` at the start of 1939Q1. Under the strict rule the non-resistance and `locarno_lapses` would also sit in tick 0, where neither is available. The registered claims T1 and T4 are both about sequence, not about exact ticks, so the SQR rule loses nothing they assert; but it does put the hindsight snapshots and the model's trajectory out of step at three points: `treaty` (dead from 1936Q2 in the record, from 1936Q4 in the model), `polish_guarantee` (true at the start of 1939Q2 in the record, from 1939Q3 in the model) and `poland` (partitioned at the start of 1939Q4 in the record, from 1940Q1 in the model). The replay metrics of section 9 of the testbed should allow for these, or the architect should consider a finer tick for 1936Q1, 1939Q1 and 1939Q3 (the nested crisis sub-games planned for phase 2).

**Quarters in which one actor took two or more decisions** (one action per tick; the CSV keeps the decisive one and names the others in its note):

| Actor | Quarter | Kept | Not representable in the same tick |
|---|---|---|---|
| WEST | 1936Q1 | `rearm` (3 Mar 1936) | the decision not to resist (7 to 19 Mar), moved to tick 1 |
| GER | 1938Q4 | `rearm` (14 Oct 1938) | directive on the remainder of Czechoslovakia (21 Oct); the Danzig proposal to Lipski (24 Oct) |
| GER | 1939Q1 | `occupy_bohemia` | Memel (22 to 23 Mar) |
| WEST | 1939Q1 | `approach_ussr` (20 Mar) | the guarantee (31 Mar), moved to tick 13; the doubling of the Territorial Army (29 Mar) |
| GER | 1939Q2 | `propose_pact_ussr` (30 May) | Case White directive (3 Apr); renunciation of the German-Polish declaration (28 Apr); Pact of Steel (22 May) |
| WEST | 1939Q2 | `guarantee_poland` (moved) | conscription (26 Apr); guarantees to Romania and Greece (13 Apr); the decision to negotiate an alliance with Moscow (24 May) |
| GER | 1939Q3 | `attack_poland` | Hitler's telegram to Stalin (20 Aug), the GER side of the pact |
| WEST | 1939Q3 | `declare_war` | the military mission to Moscow (11 to 21 Aug) |
| USSR | 1939Q3 | `accept_pact` | the invasion of eastern Poland (17 Sep), moved to tick 15 |
| GER | 1939Q4 | `attack_france` (9 Oct) | the Reichstag offer of 6 Oct (`offer_terms_britain`) |
| GER | 1940Q3 | `air_offensive` | the Reichstag offer of 19 Jul; the Second Vienna Award (30 Aug) |
| USSR | 1940Q2 | `rearm` | the Baltic occupation and Bessarabia (not modeled) |

The consequence that matters most: because WEST's 1939Q2 slot goes to the moved guarantee, `last_WEST` at 1939Q3 is `guarantee_poland`, so in the replay the USSR's August 1939 choice is offered `accept_pact` but not `accept_alliance`. The engine still explores paths where both are offered (WEST approaches in 1939Q2), but the realized row does not show the choice Stalin actually had. A `talks_open` state variable in v1 would represent the April to August talks as a standing offer.

## 3. Check of the draft catalogue on a scratch encoding

To make sure the tables are directly codable, I encoded the catalogue in the DSL in a scratch file outside the repository (not a deliverable; step 1.5 writes the model). Results:

- **Codable.** Every guard and effect compiles, including the latch comparison `arms_at_war >= high` and the conditional increment `SetIf(cond, "ind_GER", V.ind_GER + 1)` on a counter.
- **Replay.** `realized_moves.csv`, replayed from the hegemonic 1936Q1 initial state, has every action available at its tick and ends at tick 20 in `BRITAIN_ALONE`, with zero relaxations.
- **A composition error in the skeleton.** `invade_britain` (`britain := invaded`) and `negotiate` (`britain := negotiated`) can be chosen in the same joint move, which the engine rejects as conflicting `Set`s. The catalogue writes both as `Bump`s (+2 and +1), so the invasion prevails when clamped. No other pair of conflicting `Set`s exists (each was checked for mutually exclusive guards).
- **Size.** Exploration from the two default initial states passed 3 x 10^6 states (about 100 seconds) without finishing. The testbed's target is 10^6 or fewer. Contributors: the delay counter of GER `rearm` (0 to 8), the `last_*` variables (GER has 15 actions), four actors that can idle at every tick, and `belief_GER`, which no v0 action changes and which could be dropped from the v0 state. Step 1.5 should reduce the state or use the bounded path.
- **T4**, from the realized 1939Q1 state (45,333 reachable states): the shortest trace to a state where `guarantee_poland` is available is one tick, through `occupy_bohemia` and the belief flip; no reachable state offers the guarantee without `belief_WEST == hegemonic`.
- **T5**, from the realized 1940Q2 state (1,105 states): `negotiate` is available to WEST at 1940Q2; `NEGOTIATED_PEACE` is reachable; under the profile `fight_on`, `AXIS_HEGEMONY_EUROPE` is unreachable, so neither GER nor GER with Nature can force it (section 4).
- **T2 counterexample without the `campaign_west` condition.** GER remilitarizes (1936Q1), rearms while WEST resists (1936Q2), holds; WEST declares war (1936Q3). GER reaches `high` at 1938Q3, attacks Poland, then France; `campaign_west` takes France at 1939Q2 and `balance_europe` fails. With the `arms_at_war >= high` condition the same branch blocks `campaign_west` (`arms_at_war` is `rising`).
- **T10**: with only `Nature.campaign_siberia` relaxed, `JPN_CONQUERS_USSR` is reached (strike north from 1939Q4 on the realized path). With only `ussr_defensive` relaxed, `join_axis` is available at 1940Q3 and `USSR_JOINS_AXIS` is reached at 1940Q4.
- **Not computed**: the full viability kernel V_WEST from 1936Q1 (T2, T8), because the state space exceeds the budget. Those statements below are by hand analysis.

## 4. The registered tests against this catalogue

**T1 (realized trajectory reachable with zero relaxations).** Supported under the SQR rule (section 2), from the hegemonic start only, since `occupy_bohemia` and `attack_poland` are gated on `aims_GER == hegemonic`; the 1936Q1 snapshot sweeps `aims_GER`, so the hegemonic start is one of its initial states. A strict replay with every decision in its historical quarter fails at the guarantee.

**T2 (French `resist` keeps 1936Q1 in V_WEST).** Supported by hand analysis, given two changes to the skeleton, both in the catalogue: (a) the treaty regime lapses through Nature's `locarno_lapses`, not on the tick of the remilitarization (otherwise `balance_europe` is false before WEST can move); (b) `campaign_west` requires `arms_at_war >= high`. With them, under the resist branch: if GER withdraws, the treaty is `enforced` and the zone demilitarized, and GER cannot reach five regions or start a war in the West; if GER holds, WEST can declare war, `balance_europe` holds through the war clause, France cannot fall, and GER's regions stay at or below three (Rhineland, Austria, Poland; the Sudetenland needs peace with the West). This holds for both `aims_GER` starts. Caveats: (i) the resist branch runs over three ticks (entry 1936Q1, resistance 1936Q2, withdrawal 1936Q3) where the record had a week, so T2's trace will read as a slow crisis; (ii) I chose condition (b) after seeing the counterexample in section 3, so it should be judged on the record alone (Beck's memoranda of 1938, the March 1936 withdrawal contingency) before the guard is written; (iii) the kernel was not computed.

**T3 (phase 2; Munich refused leads to war, ending contested).** The added `attack_czechoslovakia` gives the branch a German move, and `declare_war` is available while the demand is open. Under GER `rearm` delay 8 the decision of 1936Q3 makes `arms_GER = high` visible at 1938Q4, so a war declared at Munich (1938Q3) latches `arms_at_war = high` and France can fall; a war begun earlier latches `rising` and France cannot. The boundary therefore falls between Munich and the earlier crises, which keeps T3's case contested; Beck's own 1938 view would put it later. The delay and the latch together take a position on German readiness that bears on T3, and the historian should look at both together.

**T4 (Prague flips the belief and enables the guarantee).** Computed and supported (section 3), with the one-tick lag of section 2. The guard is kept as registered; whether it is feasibility or preference is discussed in section 5.

**T5 (`negotiate` available at 1940Q2; under `fight_on` Germany cannot force `AXIS_HEGEMONY_EUROPE`).** Computed and supported, but the second half holds for a reason worth stating: from 1940Q2 the chain France's fall (resolved in 1940Q2), air offensive (1940Q3), air battle (1940Q4), invasion (1941Q1 = the horizon, terminal) does not fit inside the horizon, so the invasion ending is unreachable even with Nature's help. The claim passes on the horizon, not on Britain's choice or on the air battle. The real Sea Lion target was September 1940; the model's chain is one or two ticks longer because each Nature resolution comes one tick after the German decision. The first half needs the departure on `negotiate`: under the skeleton's guard (`france == fallen and last_GER == offer_terms_britain`) `negotiate` is unavailable at 1940Q2, when the War Cabinet actually debated it.

**T8 (concessions reach `NO_GENERAL_WAR` under revisionist and shrink V_WEST under hegemonic).** Three problems, none fixed in the catalogue because each needs an architect's decision:

1. The skeleton had no guard that read `aims_GER`, so the hypotheses could not differ. The catalogue adds hypothesis gates on `occupy_bohemia` and `attack_poland`. With them, WEST can force `NO_GENERAL_WAR` under the revisionist start and cannot under the hegemonic start, but that result follows directly from the gate on `attack_poland`, so it is put in, not found.
2. Concessions are not pivotal. Under the revisionist start WEST forces `NO_GENERAL_WAR` whether or not it concedes: after a refusal, `attack_czechoslovakia` takes only the Sudetenland and WEST may stand aside. The "rights lever" bites only if a refusal leads to war, which is what the proposed (not adopted) fairness `czech_obligation` in actions_ww2.md would encode.
3. The last clause of `balance_europe` makes every realized state from 1936Q4 to the guarantee fall outside `balance_europe`, under both hypotheses (ontology_ww2.md section 6). After a concession, V_WEST is therefore empty under both starts, and the "shrink V_WEST under hegemonic" half cannot show a contrast. If T8 is evaluated as kernel membership after concessions, the balance definition decides the answer.

**T9 (phase 2).** `belief_GER` is never updated in v0, and the alliance window issue of section 2 removes `accept_alliance` from the realized 1939Q3 row. Both need work in v1. The two-front feasibility condition the testbed mentions ("no second active front unless force = very_high") is not in v0.

**T10 (negative controls).**

- USSR joins the Axis: one relaxation (`ussr_defensive`). Supported.
- Japan conquers the USSR: **one** relaxation (`Nature.campaign_siberia`), not three or more. `strike_north` is feasible from mid-1937 (Anti-Comintern Pact plus the purge), because the China war, the main constraint, is not modeled. A methodological point for the architect: a guard is one named assumption whatever its conjuncts, so relaxation counts depend on how the constraints are packaged. "Three or more" is reachable only if the absurdity rests on three separately named assumptions (for example a JPN China-war variable with its own guard, the strike-north guard, and the campaign guard).
- Germany conquers the United States; Britain alone defeats Germany by 1941: no v0 variable or action represents either, so no relaxation set reaches them. Whether `informativeness` counts an unreachable ending as satisfying "three or more" depends on the implementation; it should be reported as vacuous rather than as a pass.

**T13 (phase 2).** Under the balance clause, the realized trajectory leaves the balance in 1936Q4, the earliest edge of T13's window, for a reason fixed by definition (the treaty regime's death) rather than computed. The driving variable will be `treaty`.

## 5. Guards that are preferences in disguise, and other guard notes

1. **`guarantee_poland`, `belief_WEST == hegemonic` (kept; T4).** My assessment: closer to a belief-conditioned preference than to a capability constraint. The institutional reading is real (a British government could not commit to war for an East European state without a Cabinet and Commons majority and the Dominions' acquiescence, and the record of March 1938 shows the option judged undeliverable then), but the reasons given in March 1938 were partly military (no means to help directly), and those had not changed by March 1939. What changed was the governing coalition's reading of German aims. The registered claim is consistent with the record; it should be reported as the political precondition the record supports, not as a capability result.
2. **Hypothesis gates** on `occupy_bohemia`, `attack_poland`, `join_axis` and the hegemonic part of `attack_czechoslovakia`'s effect: preferences by design, declared and counted separately.
3. **Skeleton sketches that encoded a motive or a sequence, replaced:** `strike_north` used `war_west_ger == war` (an opportunity motive, not a Japanese capability); `approach_ussr` required the guarantee (the four-power proposal came first); `negotiate` required a German offer and France's fall (the May 1940 debate had neither); `offer_terms_britain` required France's fall (the October 1939 offer); `align_balkans` allowed the pact as a prior condition (no record of a German alignment attempt before France fell); `demand_sudeten` required a capability level that, under its own rule, Germany reached only after Munich.
4. **`declare_war`'s guarantee disjunct** admits a declaration under the guarantee before any German attack, a branch with no record; it is the price of letting the declaration of 3 Sep 1939 share a quarter with the attack of 1 Sep.
5. **`campaign_west`'s `arms_at_war` condition** is capability, but it was chosen with T2 in view (section 4).

## 6. Open questions for the historian

1. The March 1936 withdrawal contingency: what Blomberg's directive of 2 March 1936 provided; how much of the "withdraw if France moves" account rests on postwar testimony (Jodl, Schmidt, Hitler's later remarks); Emmerson's reading. T2 depends on `withdraw_rhineland` being a documented alternative.
2. `arms_GER = high`: the size of the mobilizable German field army in September 1938 and in spring 1939, and whether delay 8 (high at 1938Q4) or 10 (1939Q2) fits the rule better. The choice also moves the T3 boundary (section 4).
3. `belief_GER` at 1936Q1: Hitler's calculation (will_not_fight) or the military's (uncertain)?
4. `ind_GER`: whether the Austrian step is justified by reserves and ore rather than steel, and whether the Sudetenland should count.
5. Prague under the revisionist hypothesis: is excluding it (the gate) a fair encoding of the Taylor reading, which treats Prague as improvisation?
6. Danzig: should v1 carry a Danzig region so that the revisionist hypothesis can pursue its stated claim short of war?
7. `arms_WEST = high` at 1940Q1 from the post-Munich decisions: defensible, or should French mobilization (Sep 1939) set it?
8. USSR `rearm` at 1940Q2: is the Winter War conference and Timoshenko's appointment the right decision record?
9. Whether the Foreign Policy Committee record of 18 to 22 March 1938 gives the grounds for rejecting a Czech guarantee as I summarize them (military inability, the Dominions, no majority).
10. Whether the realized WEST decision of 1939Q1 should be the four-power proposal (20 Mar) or the guarantee (31 Mar) if the architect adopts a strict replay.

## 7. Citations I am least sure of

No page numbers are given anywhere. The following are cited from memory with less confidence and should be checked before review:

- Nuremberg document numbers C-102 (Case Otto, 11 Mar 1938), C-136 (directive of 21 Oct 1938), C-175 (directive of 24 Jun 1937) and 1301-PS (Goering's conference of 14 Oct 1938). More confident: 386-PS (Hossbach), 388-PS (Case Green), C-120 (Case White), L-79 (23 May 1939), 798-PS and 1014-PS (22 Aug 1939).
- DGFP, DBFP and DDF volume numbers attached to particular documents (Series C vol. V for March 1936; Series D vols. I, II, IV, VI, VII, XI; DBFP Third Series vols. V to VII for the 1939 Moscow talks).
- Treue's edition of the Four-Year Plan memorandum (Vierteljahrshefte für Zeitgeschichte, 1955); Jacobsen, *Dokumente zur Vorgeschichte des Westfeldzuges* (1956); K.-J. Müller, *General Ludwig Beck* (1980) as the edition of the Beck memoranda.
- Emmerson 1977's position that the withdrawal story is overstated (I recall the argument, not its exact form).
- Kershaw, *Hubris* (1998): the Rhineland is treated in the closing chapter (chapter number not given).
- The Rhine Pact's provision for immediate action in a flagrant breach (article 4).
- Wording: Chamberlain at Birmingham, 17 Mar 1939, "a step in the direction of an attempt to dominate the world by force"; Sarraut's broadcast of 8 Mar 1936 (quoted in translation).
- Dates: the British Cabinet's approval of the Defence Requirements programme (February 1936, day not given); the decision on a continental field force (February 1939); the air expansion scheme approved in November 1938; the German-Romanian oil agreement of May 1940; Ribbentrop's letter to Stalin of 13 Oct 1940; Weizsäcker's instruction of 30 May 1939.
- Jodl's postwar account of the western front in September 1938 is paraphrased, not quoted.
- The characterizations of Raack (1995) and Tucker (1990) as the opportunist reading are fair summaries in my judgement but compress both authors.

## Model step (1.5 to 1.7)

Added with `models/ww2/v0.py`, `models/ww2/hypotheses.py`, the six scenario tests and [reports/ww2_v0.md](../reports/ww2_v0.md). Every point below was decided while coding, before any registered test was run against the model; none is a guard edit made in response to a test (docs/guard_changelog_ww2.md has the one row for this step).

### Coding choices the documents left open

1. **Constants.** `arms_JPN` and `belief_GER` are declared with their ontology levels and initial levels, and no effect changes them, so each contributes a factor of one to the reachable count (D6 reductions 1 and 3). They are declared because the hindsight snapshots contain them and the loader refuses unknown variables. The snapshots do change `belief_GER` (`will_fight` by 1940); a state loaded from them carries that value unchanged.
2. **`ind_GER`** is a counter 0..5 with initial value 3, so the snapshot integers 3 to 5 load directly; 0 to 2 are never reached. The catalogue's conditional increment is `SetIf(cond, "ind_GER", V.ind_GER + 1)`; the unconditional ones are `Inc`.
3. **`last_JPN` replaced by a flag.** JPN has no `remember_last` (D6 reduction 2). `strike_north` sets the new flag `north_strike`, and `campaign_siberia` reads it (part `strike`). A strike therefore stays on record, where `last_JPN` would have held it for one quarter.
4. **`german_defeat`** (new flag) is set by Nature's `campaign_rhineland` and defines `GERMAN_DEFEAT` (D3 names the ending but no variable).
5. **Determinism of `campaign_rhineland`** (D3: "resolves, deterministically"). Nature always has `none`, so the only way to make it deterministic in the DSL is a fairness constraint on Nature: `rhineland_resolution`, trigger `last_WEST == offensive_west and arms_GER <= rising`, within 1, response `campaign_rhineland`. It is a third fairness constraint beyond the two the catalogue and D4 name, and a relaxable assumption.
6. **`campaign_siberia`'s parts**: `strike` (`north_strike`), `ussr_weak` (catalogue), `no_two_front` (`not china_war`, D7) and `japanese_superiority` (D7), written as the constant `FALSE`. I read D7's `japanese_superiority` as the catalogue's `ussr_at_war_in_europe` term renamed: both are the constant `FALSE` and cite the same record (Nomonhan, 1939). Keeping both would have added a second never-satisfied part.
7. **`china_incident`** has the guard `not china_war` and no date: like `purge`, Nature may play it in any quarter or never. This decides T10's Japanese control (report section 8).
8. **Parted guards**, beyond the list required: `GER.occupy_bohemia` and `USSR.join_axis` (they carry hypothesis gates, named `hypothesis`), `Nature.campaign_rhineland` (`offensive`, `german_army_unready`, the two constraints D3 joins). Part names elsewhere: `annex_austria` (`target`, `italian_acquiescence`, `army`), `attack_poland` (`hypothesis`, `target`, `army_ready`), `attack_france` (`at_war`, `polish_front_closed`, `army_ready`), `invade_britain` (`air_superiority`, `france_fallen`, `britain_at_war`), `guarantee_poland` (`target`, `once`, `belief`, `commitment`), `offensive_west` and `strike_north` as in D3 and D7, `campaign_west` (`offensive`, `france_in_field`, `army_ready`), `join_axis` (`hypothesis`, `pact`, `france_fallen`, `once`). `demand_sudeten`, `declare_war` and the remaining guards are single assumptions. Relaxation counts in T10 depend on this packaging (report section 10).
9. **Endings** are made mutually exclusive on every state by declaring them in the ontology's order and conjoining each with the negation of every earlier one; the horizon endings test `tick == 20`. A test checks every combination of the variables they read.
10. **Monotone variables**: the regions except the Rhineland, the pact flags, `china_war`, `north_strike`, `german_defeat`, `arms_GER`, `arms_WEST`, `ind_GER`, `oil_GER`, `belief_WEST`, `commit_WEST`, `commit_US`. Not monotone: `treaty`, `rhineland`, `arms_USSR`, `italy_estranged`.
11. **Snapshot states.** `snapshot_state` sets `tick` to index(Q) + 1 and leaves every other built-in at its initial value, as the loader does: no pending delayed effect, no last action, fairness counters at zero. I did not fill the built-ins from the realized move file, because that would mix the replayed trajectory into the hindsight state. Consequences: T5 is run from `1940Q2.json` (the first snapshot whose state alone satisfies `negotiate`'s guard), and the 1938 snapshots carry no pending German rearmament, which decides T8 (b) (report section 7).
12. **Bounded checker from one hypothesis.** The bounded checker starts from the model's declared initial states, so `fixed_model` pins `aims_GER` in a copy of the model; T10 keeps `aims_USSR` swept so that `ussr_defensive` can be relaxed. Mid-trajectory starts (T10 from 1940Q3) use the explicit engine.
13. **Refutation of kernel membership.** D6 gives a sufficiency check for membership. To show non-membership (T2 hegemonic) I fixed the other actors and Nature to one memoryless strategy (`restricted`) and computed WEST's kernel of that smaller game exactly; the true kernel is contained in it.
14. **T2 has two readings**: the tick-0 state in V_WEST (fails under hegemonic aims), and the state after the realized German entry of 1936Q1 in V_WEST (holds under both). Both are tests; only the first carries the xfail.
15. **CLI `--fix`** is on `viable` and `viz`. The task named `report` as well, but `report` has no `--snapshot` option, and adding one would change the CLI beyond `--fix`, so it was not added.
16. **The visualizer page** cannot be built from v0 at tick 0 (the graph passes 3,000,000 states). It is built from `realized_corridor()`, a display device in `hypotheses.py` (v0 restricted to the realized decisions or abstention, Nature playing its recorded events where it can), whose shortest witness to `BRITAIN_ALONE` is the realized trace. No registered test uses it.

### Catalogue guards kept as written although they read as preferences or sequence conditions

- `guarantee_poland:belief` (registered T4; D9).
- `declare_war`'s `polish_guarantee` disjunct admits a preventive declaration under the guarantee, a branch with no record (section 5, point 4).
- `withdraw_rhineland` and `resist_rhineland` read `last_*` windows, sequence conditions imposed by the quarterly tick.
- `remilitarize_rhineland` stays available after a withdrawal (its guard has no one-shot condition). This is what lets a hegemonic Germany withdraw in 1936 and re-enter once ready (report section 4); whether a second entry was a documented alternative is for the historian.

### Problems found in the catalogue (not fixed; for the architect)

- **`democratic_response` can leave WEST without a response.** The catalogue states that `guarantee_poland` is available whenever the trigger holds. It is not when `commit_WEST` is still `appease` (belief hegemonic after a German attack on Czechoslovakia with no concession), and `rearm` may be pending or exhausted. In the default model `czech_obligation` forces war first, so no reachable state is ill-formed (1.4 million states from 1938Q2 explored without error); with `czech_obligation` relaxed the engine raises. Options: trigger `commit_WEST == wary`, or `declare_war` among the responses.
- **`appeaser` and `czech_obligation` conflict.** Under the profile `appeaser`, a German attack on Czechoslovakia that leaves `belief_WEST` below hegemonic (revisionist aims) restricts WEST to `declare_war` (forbidden by the profile) or `concede` (unavailable once the Sudetenland is German), so the engine raises. No test selects `appeaser`.
- **Treaty date.** D4 cites the Franco-Czechoslovak treaty of 25 January 1925; the catalogue cites 16 October 1925 (the treaty of mutual guarantee signed at Locarno). The alliance treaty is usually dated 25 January 1924.
- **Readiness clock.** The model's German `rearm` (delay 8, decided 1936Q3) gives `arms_GER = high` from 1938Q4; the snapshots' NMC reading gives it from 1939Q1. The two-tick difference decides T8 (b).
