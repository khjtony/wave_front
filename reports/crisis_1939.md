# The summer-1939 crisis sub-game: report on K1 to K6

> Every result is conditional on the model version and the entry state; no bare reachability result is a finding. The deliverables below are kernels and their departure ticks, pivotal coalitions, contested regions and minimal relaxation sets, each with the engine that computed it.

Model `crisis_1939` (`models/ww2/crises/summer_1939.py`), fingerprint `8eb17771ce24` (full build) and `e1a188144a02` (reduced build, `build(inert=False)`). Entry state: v1's state at the start of 1939Q3 (`snapshots/ww2/hindsight_v1/1939Q2.json` with its built-ins, tick 14) under `aims_GER = hegemonic`, `aims_USSR = defensive` (`aims_JPN = hegemonic`, not read). Registered claims: [docs/crisis_1939_testbed.md](../docs/crisis_1939_testbed.md) section 3, unedited; readings: [docs/crisis_1939_decisions.md](../docs/crisis_1939_decisions.md) section R, written before the first run. Content: [docs/ontology_crisis_1939.md](../docs/ontology_crisis_1939.md), [docs/actions_crisis_1939.md](../docs/actions_crisis_1939.md), `data/ww2/crises/1939/`.

**Hold-out record.** The content, the model edits, the data files, the decisions with the readings and all test files were written first. The construction tests (`test_model_crisis_1939.py`: well-formedness, budget, the realized replay, the exit check) and then K1 alone were run as the first checks (A9). Then the whole directory, K1 to K6 in one go, was run once: `python -m pytest tests/ww2/crisis_1939 -q -s -rA`, 2026-10-15 01:50 to 02:10 UTC, 19 min 18 s, at commit **`f00e5be3d27c578d009383bb81fdcd7d3ea6a6de`** with the working tree uncommitted (f00e5be already held the draft module of the interrupted attempt; nothing of it had been run as a registered test). Result: **47 passed, 3 failed**. No guard, effect, delay, fairness constraint or profile changed after that run; the only edits afterwards were the first-run constant in the construction test, the changelog's first-run row, this report and the visualizer page. The guard changelog (docs/guard_changelog_ww2.md) has the model-step row and the first-run row, nothing after. The whole directory was rerun with no model change on 2026-10-15/16 (23:43 to 00:05 UTC, 21 min 59 s, with the tree at the WIP snapshots 9ad5a5e and 689c5d5 plus uncommitted work of other steps): **47 passed, 3 failed**, the same three registered clauses (run without `-s`, so the diagnostic tables were not printed again).

## Outcome

| Claim | Result | Engine | Time (first run) | Key numbers | § |
|---|---|---|---|---|---|
| realized replay, well-formedness, bisimulation | pass | explicit | 160 s (all construction tests) | 20 realized moves available; `ATTACK_LAUNCHED` at tick 20; no model error from the entry state under 6 profile sets and both scenarios | 2 |
| K1 reachable with zero relaxations, exit matches v1 | **pass** (as read, R1) | explicit replay and `explore` (80,956 states); `flatten` | 6.3 s per profile | exit equals v1's realized 1939Q3 transition on all 9 variables; against `1939Q3.json` literally 7 of 9 (`poland`, `oil_GER` are v1's own clock differences) | 3 |
| K2 (a) {WEST, USSR} pivotal with the belief and passage conditions | pass | explicit (`pivotal`, `attractor`) | 6.4 s | minimal blocking [{WEST, USSR}] in all 4 granted rows with the belief condition; minimal coalition forcing the alliance by tick 17 [{WEST, USSR}] | 4 |
| K2 (b) only if `will_fight` | pass | explicit | (in a) | no blocking coalition with the belief below `will_fight` and no raise | 4 |
| K2 (c) Polish passage pivotal | pass | explicit | 14.8 s | refused, documented: nothing blocks; refused with the speculative action: {WEST, USSR} blocks | 4 |
| K2 (d) without the belief condition, contested | **fail** | explicit (`contested`) | 0.0 s (cached) | **forced** by Germany in all 4 rows | 4 |
| K3 departure tick in 13 to 15 | pass | explicit (`viability`, `point_of_no_return`) | 1.5 s | d = 15 (19 to 21 Aug), t_K = 16 | 5 |
| K3 driving variable passage or pace of the talks | **fail** | explicit (`sensitivity`) | 0.4 s | three-way tie: `talks`, `passage`, `german_approach` | 5 |
| K4 (a, b) forced by Germany, no coalition blocks, every belief | pass | explicit (`attractor`, `safe`), 57 states | 0.0 s | rank 1 from tick 17 under every belief, with and without `deterred` | 6 |
| K4 (c, d) the treaty flips the belief; the halt documented | pass | explicit replay | 0.0 s | `belief_GER` uncertain at 17, will_fight at 18 (`sign_treaty`); the letter changes nothing | 6 |
| K4 (e, f) re-ordered within two ticks whatever WEST does | pass | explicit | 0.0 s | rank 1 from the tick-18 state; realized delay 2 ticks | 6 |
| K4 (g) the shortest trace shows the cancellation and the re-order | **fail** | explicit (`witness`) | 0.0 s | the shortest trace is the attack at tick 17 itself | 6 |
| K5 every minimal set relaxes readiness | pass | explicit (`relax_explicit`, max size 2) | 527 s | minimal sets [[`GER.attack_poland:readiness`]]; 201 ill-formed relaxations | 7 |
| K6 (a) both targets reachable to tick 14 | pass | explicit (`attractor` of everyone) | 0.4 s | both reachable at ticks 0 to 15; the alliance not from 16 | 8 |
| K6 (b) the pact's minimal assumption set names the German proposal | pass | explicit (`relax_explicit`, max size 2) | 334 s | minimal sets [[`no_german_proposal`]]; hitting set {`no_german_proposal`} | 8 |

## 1. The model and the parameter budget

Four principals' worth of the summer of 1939 in 20 three-day ticks: `GER`, `WEST`, `USSR` and Nature (Poland and Italy), thirteen declared variables, everything structural frozen at the entry values. The content is the historian's (ontology and catalogue); the coding choices C1 to C12 are in the decisions document. The draft module of the interrupted attempt was reviewed against the record and the architect's decisions and kept; this step changed its documentation, the entry map (`talks` broken when the coarse pact holds), `tick_of`'s range check, the E501 line and added the data-file constants.

| Item | Full build | Reduced build | Note |
|---|---|---|---|
| Declared variables / levels | 13 / 37 | 11 / 32 | the reduced build drops `mobilization_POL`, `italy_ready` |
| Built-in variables | 3 | 3 | `tick`, `pending_WEST_send_missions`, `fair_polish_obligation` |
| Actions (GER, WEST, USSR, Nature) | 21 (5, 5, 6, 5) | 18 | |
| Guards / guard parts | 21 / 39 | 18 / 36 | one [H] gate, one date part (`attack_poland:readiness`) |
| Speculative actions | 1 | 1 | `USSR.conclude_without_passage` |
| Delayed actions | 1 | 1 | `WEST.send_missions`, 5 ticks |
| Fairness | 1 | 1 | `polish_obligation`; `scenario_passage` only in the two scenario builds |
| Profiles | 4 | 4 | `deterred` (behaviour, v1's); `documented_only`, `no_belief_raise`, `no_german_proposal` (analysis devices) |
| Cadence / latches / assumes | 0 / 0 / 0 | | no documented decision period |
| Invariants / endings | 3 / 2 | | `no_attack`, `no_pact`, `alliance_race`; `ATTACK_LAUNCHED`, `NO_ATTACK` |
| States from the entry state | 80,956 | 13,504 | explicit engine, 6.5 s and 0.7 s |

## 2. Engines and well-formedness

Every result is the explicit engine's (`wavefront.engine`) and the analysis layer's (`wavefront.analysis`): exact kernels, attractors, contested regions, pivotal coalitions, sensitivity and brute-force relaxation sets. No bounded or fixed-strategy check was needed. The flattened game of framework_spec.md section 14 is used for K1's exit check (a copy of v1 with a GER action `crisis_1939`, the sub-game attached with `crisis()`; one coarse step in, twenty fine steps, the return).

Well-formedness, before any claim: the full build explores from the entry state and its two counterfactual belief levels without a model error under no profile, `deterred`, `deterred + documented_only`, with `no_belief_raise`, and `no_german_proposal`, and in both passage scenarios under five profile sets; every terminal state is in exactly one ending. The reduced build is bisimilar to the full build under the projection that drops the two inert variables and reads the three inert events as `none` (checked state by state and move by move on the whole reachable graph, with and without profiles), so every analysis on the reduced build holds for the full one.

## 3. The realized replay and K1

**Claim (K1).** The realized sequence is reachable with zero relaxations and the exit state equals v1's realized 1939Q4 state. **Reading (R1)** as in the decisions. **Engine:** explicit replay and exploration; `flatten`.

The realized moves (`data/ww2/crises/1939/realized_moves.csv`), every one available at its tick with nothing relaxed, with no profile and with `deterred`:

| Tick (days) | GER | WEST | USSR | Nature | Visible at t + 1 |
|---|---|---|---|---|---|
| 0 to 5 (5 to 22 Jul) | idle | idle | idle | none | political talks deadlocked; Molotov's condition of 17 Jul |
| 6 (23 to 25 Jul) | idle | `send_missions` | idle | none | pending 5 ticks |
| 7 (26 to 28 Jul) | `open_approach` | idle | idle | none | `german_approach` opened (Schnurre and Astakhov, 26 Jul) |
| 8 to 11 (29 Jul to 9 Aug) | idle | idle | idle | none | missions sail 5 Aug |
| 12 (10 to 12 Aug) | idle | idle | idle | none | talks military from tick 12 (12 Aug) |
| 13 (13 to 15 Aug) | `propose_pact` | idle | `ask_passage` | none | Voroshilov's question; Ribbentrop's telegram |
| 14 (16 to 18 Aug) | idle | idle | `adjourn_talks` | none | adjourned (17 Aug) |
| 15 (19 to 21 Aug) | idle | `authorize_convention` | `accept_pact` | `passage_refused` | refused; powers; the pact decision |
| 16 (22 to 24 Aug) | `order_attack` | `warn_germany` | `break_talks` | `mobilize_partial` | pact signed (23 Aug) visible at 16; talks broken at 17 |
| 17 (25 to 27 Aug) | `cancel_attack` | `sign_treaty` | idle | `italy_declines` | cancelled; treaty; `belief_GER` will_fight at 18 |
| 18 (28 to 30 Aug) | idle | idle | idle | `mobilize_general` | |
| 19 (31 Aug to 2 Sep) | `attack_poland` | idle [SQR] | idle | none | launched at tick 20 |
| 20 (3 Sep) | horizon | | | | the declarations, applied on return (C3) |

[SQR] and [NSL] notes. WEST's declarations react to the attack of tick 19 and fall at tick 20, the terminal horizon: the obligation `polish_obligation` is due in the terminal state (`fair_polish_obligation == 1`) and the exit map applies `declare_war`'s effects (C3). The halt of 25 Aug reacts to two moves of the same tick (the treaty, Mussolini's letter) but its guard does not read them, so it sits at its date. Two decisions of one actor in one tick were separated (C2): the USSR's adjournment sine die of 21 Aug sits at tick 16 with Voroshilov's statement of 22 Aug (tick 15 keeps the pact decision); GER's 15:02 order of 25 Aug is the confirmation of the Y-day order of 23 Aug at tick 16 (tick 17 keeps the halt). No [NSL] placement: the four realized Nature events fall in four ticks.

**Result: pass.** The play ends at tick 20 in `ATTACK_LAUNCHED`; its terminal state is in the explored graph (80,956 states). The exit, applied to the entry coarse state:

| Variable | Exit | v1's own realized 1939Q3 transition | `1939Q3.json` |
|---|---|---|---|
| `poland` | german | german | **partitioned** (17 Sep, after the horizon; v1's `occupy_east_poland` at v1 tick 15 [SQR]) |
| `war_west_ger` | war | war | war |
| `france`, `britain` | at_war | at_war | at_war |
| `commit_WEST` | at_war | at_war | at_war |
| `nazi_soviet_pact` | True | True | True |
| `anglo_soviet_alliance` | False | False | False |
| `belief_GER` | will_fight | will_fight | will_fight |
| `oil_GER` | secured | secured | **dependent** (the snapshot keeps the 1936 reading; v1's `accept_pact` sets secured) |

The exit equals v1's own realized transition on all nine variables, and through the flattened game the return transition gives the same nine levels (tick 15, `last_GER == crisis_1939`, the coarse delay counters decremented as by v1's own step). Against `1939Q3.json` literally, 7 of 9 match; both differences are differences between v1's model clock and its hindsight snapshot that v1's own transition shows (C12), not differences of the sub-game. **If the owner reads K1 as the literal comparison with `1939Q3.json`, K1 fails on `poland` and `oil_GER` by construction of v1**; the proposed amendment is in section 11.

## 4. K2: the alliance and the attack (the hold-out claim)

**Claim.** A UK, France, USSR alliance concluded before the pact blocks the attack only if `belief_GER` is `will_fight`; the coalition that can conclude it in time is {WEST, USSR} with Nature granting Polish passage, and passage is pivotal. **Expected:** pivotal {WEST, USSR} with the belief and passage conditions; without the belief condition, `contested`. **Reading (R2):** passage scenarios granted and refused; entry belief swept; raises allowed or forbidden (`no_belief_raise`); `deterred` and `documented_only`. **Engine:** explicit (`pivotal`, `attractor`, `safe`, `contested`), 11,583 to 26,444 states per cell, 2 to 11 s per cell.

Under `deterred` (minimal blocking coalitions drawn from {WEST}, {USSR}, {WEST, USSR}; "status" is the standard region for {GER} reaching `ATTACK_LAUNCHED`):

| Passage | Decision space | Belief raises | Entry belief | Blocking | GER forces | Status | Forcing the alliance by tick 17 |
|---|---|---|---|---|---|---|---|
| granted | documented | allowed | any of the three | [{WEST, USSR}] | no | blocked | [{WEST, USSR}] |
| granted | documented | forbidden | will_not_fight, uncertain | [] | **yes** | **forced** | [{WEST, USSR}] |
| granted | documented | forbidden | will_fight | [{WEST, USSR}] | no | blocked | [{WEST, USSR}] |
| refused | documented | allowed or forbidden | any | [] | yes | forced | [] |
| refused | with speculative | allowed | any | [{WEST, USSR}] | no | blocked | [{WEST, USSR}] |
| refused | with speculative | forbidden | will_not_fight, uncertain / will_fight | [] / [{WEST, USSR}] | yes / no | forced / blocked | [{WEST, USSR}] |
| free (Nature not fixed) | documented | allowed | any | [] | no | blocked (by the rest with Nature) | [] |
| free | documented | forbidden | will_not_fight, uncertain / will_fight | [] | yes / no | forced / blocked | [] |
| free | with speculative | as the refused rows | | | | | |

(The granted rows with the speculative action available equal the documented ones.) **Without `deterred`, nothing blocks in any cell and Germany forces the attack in every cell**: the whole result rests on the behavioural profile.

- **(a) pass.** With Nature granting passage and the belief condition met (entry `will_fight`, or the West's treaty available), the only minimal blocking coalition is {WEST, USSR}; neither alone. The shortest play to the alliance in the granted scenario sends the missions at tick 0, has them in session at tick 5 (the delay of 5), the question at 6, the Polish consent and the Western powers at 7, and the convention at 8: alliance from tick 9, eight ticks before the attack is first feasible. {WEST, USSR} is also the only minimal coalition that can force the alliance by tick 17.
- **(b) pass.** With the belief below `will_fight` and no Western signal, no coalition over {WEST, USSR} blocks, even with passage granted: `deterred` never binds.
- **(c) pass.** With passage refused, no documented coalition blocks; {WEST, USSR} blocks only through the speculative `conclude_without_passage` (no Soviet record). Passage is pivotal.
- **(d) fail.** Where the belief condition fails, the attack is **forced** by Germany (order, then attack at tick 17), not contested. The claim's parenthetical ("Germany cannot force it ... while the alliance is possible") is true only where the belief can still become `will_fight`, i.e. where the belief condition holds. The cells that match the parenthetical are the free-Nature ones with the West's raises available: Germany cannot force the attack, {WEST, USSR} cannot block it, and the rest with Nature can keep it out. Diagnostic computed after the run (no model change), fortune table for those cells (testbed section 4.6, owner's decision 2): {GER, Nature} forces the attack (Nature refuses passage) and {WEST, USSR, Nature} keeps it out (Nature grants), for every entry level, so the free model is **contested in the fortune sense**; with raises forbidden and the belief below `will_fight` it is forced by Germany even without Nature's help.

Along the realized path (diagnostic, `deterred + documented_only`, free model): the fortune kernel of {WEST, USSR, Nature} for `no_attack` contains the realized states of ticks 0 to 15 and none from 16 (t_K = 16, departure tick 15, 19 to 21 Aug); the standard kernel of {WEST, USSR} contains none of them (Nature may refuse).

## 5. K3: when the alliance stopped being possible

**Claim.** {WEST, USSR} leave the kernel for "no pact and the alliance still possible" between tick 13 and tick 15, the driving variable being Polish passage or the pace of the talks. **Reading (R3):** the kernel of {WEST, USSR, Nature} for `alliance_race` (fortune reading of the passage condition), documented decision space, free model; the departure tick d and t_K = d + 1; the driving variables are the top-ranked rows of `sensitivity` at d. **Engine:** explicit (`viability`, `point_of_no_return`, `sensitivity`), 11,938 states.

- **Departure: pass.** Kernel membership along the realized path, ticks 0 to 20: `111111111111111100000`. d = **15** (19 to 21 Aug), t_K = 16. Diagnostics: the standard kernel of {WEST, USSR} (Nature adversarial) is empty along the whole path under `documented_only` (t_K = 0: without Nature's consent nothing is forceable), and in the full decision space (with the speculative conclusion) it gives the same departure, d = 15.
- **Driving variable: fail.** Sensitivity from the realized state at tick 15 (talks adjourned, passage asked, powers not yet given, the German proposal before Moscow):

| Variable | From | To | In kernel before / after | Shortest before / after |
|---|---|---|---|---|
| `talks` | adjourned | broken | 1 / 0 | 1 / 0 |
| `passage` | asked | unasked | 1 / 0 | 1 / 0 |
| `passage` | asked | refused | 1 / 0 | 1 / 0 |
| `german_approach` | pact_proposed | pact | 1 / 0 | 1 / 0 |
| every other variable | ±1 level | | 1 / 1 | 1 / 1 or none |

The top rank is a three-way tie: `talks`, `passage` and `german_approach`. The realized departure is overdetermined: in the one tick 19 to 21 Aug, Poland refused passage (Nature) and the Soviet government decided for the pact (the USSR, a coalition member), and either alone takes the state out of the kernel. The claim names two of the three; it does not name the pact. (`passage` has two flipping rows, but each row is one perturbed state; the ranking counts flips per row, so the tie stands.)

## 6. K4: from 25 August

**Claim.** After the pact no coalition blocks the attack under any belief; the treaty and the letter flip the belief; the attack is cancelled for a documented reason, re-ordered and launched by 1 Sep whatever WEST does; the cancellation delays it by at most two ticks. **Expected:** forced by Germany by tick 19 under every belief; the shortest trace shows the cancellation and the re-order. **Reading (R4).** **Engine:** explicit, 57 states from the six start states.

- **(a, b) pass.** From the realized state at tick 17, under each of the three belief levels, with and without `deterred`, Germany forces the attack with rank 1 (attack at tick 17, 26 Aug), and {WEST, USSR, Nature} cannot keep it out: after the pact the alliance is impossible, so `deterred` never binds.
- **(c, d) pass.** `belief_GER` is `uncertain` at ticks 16 and 17 and `will_fight` from 18; the raise is the treaty's (`sign_treaty`, tick 17); Chamberlain's letter (tick 16) changes nothing from `uncertain`, as coded (C8). The realized GER move of tick 17 is `cancel_attack`, whose source cites Mussolini's letter and the treaty, beside WEST's `sign_treaty` and Nature's `italy_declines`.
- **(e, f) pass.** From the realized state after the halt (tick 18), Germany forces the attack with rank 1 under every belief (attack at tick 18 at the earliest); the realized attack (tick 19) is two ticks after the first feasible one (tick 17).
- **(g) fail.** The engine's shortest trace from the state of 25 Aug is one step, the attack at tick 17:

| tick | GER | WEST | USSR | Nature | changes |
| --- | --- | --- | --- | --- | --- |
| 17 | attack_poland | idle | idle | none | attack_order: ordered -> launched; fair_polish_obligation: 0 -> 1 |
| 18 | - | - | - | - | (trace ends) |

It does not show the cancellation: the halt was a choice, not a feasibility constraint, and the attack of 26 Aug was feasible (Case White's readiness part allows tick 17). The shortest trace through the realized halt (from tick 18) is the re-order and launch at tick 18, one tick earlier than the record.

## 7. K5: the negative control

**Claim.** An attack before 26 Aug (tick 17) needs at least one relaxation, and every minimal set relaxes Case White's readiness part. **Reading (R5):** target `EARLY_ATTACK` (launched by tick 17), `relax_explicit` up to size 2 from the entry state, no profile. **Engine:** explicit brute force, 527 s.

**Result: pass.** Unreachable as is; the only minimal set is [`GER.attack_poland:readiness`] (minimum size 1; 37 named assumptions searched). 201 relaxations up to size 2 are ill-formed (`ill_formed`, not results): relaxing a part that keeps a monotone variable from being set lower (`open_approach:first`, `propose_pact:opened`, `ask_passage:first`, the two `question` parts of Nature's answers) or keeps two `Set`s apart (`accept_pact:proposal` with `open_approach` at `none`) produces a model error, and so does every pair containing one of them. None of them could hide a set without the readiness part: only `attack_poland` launches, and its readiness part stays in force unless relaxed. Informativeness of this control: the minimum is 1, below the testbed's "3 or more" target for negative controls (ww2_testbed.md section 9), as for v1's Japan control; K5 asks for a content control (the named constraint), which it is.

## 8. K6: the Soviet choice

**Claim.** The choice is open to both sides until 19 Aug; under `aims_USSR = defensive` the pact needs Germany's proposal. **Reading (R6).** **Engine:** explicit.

- **(a) pass** (0.4 s, 11,938 states). Both the pact and the alliance are reachable (every actor and Nature, documented decision space) from every realized state at ticks 0 to 15; from tick 16 (the pact signed) the alliance is not. The choice was open through the tick that ends on 21 Aug, one tick longer than the claim's "until 19 August".
- **(b) pass** (334 s). Under `no_german_proposal` the pact is unreachable and `accept_pact` is available in no reachable state. The only minimal relaxation set is [`no_german_proposal`]; the minimal assumption set (hitting set) is {`no_german_proposal`}: it names the German proposal. Relaxing the guard part `USSR.accept_pact:proposal` instead is ill-formed, not a result: with the part relaxed, Germany's `open_approach` and the Soviet acceptance can both set `german_approach` in one joint move. The claim's second half ("without it the Soviet acceptance is unavailable") holds by the guard written from Molotov's replies of 15, 17 and 19 Aug, which answered German proposals.

## 9. Minimal assumption sets, kernels and pivotal coalitions in one place

| Question | Kernel / coalition / set | Engine |
|---|---|---|
| Who can block the attack (granted, belief met, `deterred`) | {WEST, USSR}, minimal and unique | explicit `pivotal` |
| Who can block it (refused, documented) | nobody | explicit `pivotal` |
| Who can conclude the alliance by tick 17 (granted) | {WEST, USSR} | explicit `attractor` |
| The alliance's kernel along the realized path (fortune) | ticks 0 to 15; departure 19 to 21 Aug | explicit `viability` |
| No attack, fortune kernel of {WEST, USSR, Nature} along the realized path | ticks 0 to 15 | explicit `viability` |
| Early attack | {`GER.attack_poland:readiness`} | explicit `relax_explicit` |
| The pact without a German proposal | {`no_german_proposal`} | explicit `relax_explicit` |
| Speculative actions used by a reported result | `USSR.conclude_without_passage` in K2 (c) and the "with speculative" cells only | |

## 10. What K2 says for T9

T9 asked whether a UK, France, USSR alliance could have blocked the attack on Poland, and under what belief in Berlin. At three-day resolution, from the state of 5 July 1939, under the record's decision space:

1. **The race was winnable, but only with Polish consent.** With passage granted, {WEST, USSR} could conclude the convention eight ticks before Case White's earliest day even at the realized pace of the missions' dispatch (after the realized dispatch of 23 to 25 Jul the convention stayed possible, with Nature's consent, until the decisions of 19 to 21 Aug); neither power alone could. With passage refused, as Beck refused it on 19 Aug, no documented coalition could; only a Soviet decision to conclude without consent, for which there is no record, would.
2. **The alliance blocks only through the belief, and the belief is the West's to raise.** Under `deterred`, the alliance blocks the attack only when Berlin believes the West will fight; the treaty with Poland, which the record shows could have been signed any time after April, suffices to make it so. Without that signal and with Berlin's belief below `will_fight`, Germany forces the attack whatever the alliance.
3. **Everything rests on `deterred`.** Without the profile, Germany forces the attack in every cell. The sub-game therefore says that the alliance could have deterred Hitler only if the behavioural assumption of T9 holds; it does not test that assumption.
4. **When it was lost.** Along the realized path, the alliance's kernel (with Nature's favour) and the no-attack kernel are both left by the decisions of 19 to 21 Aug, when Poland refused and the Soviet government chose the pact in the same tick; neither alone is the driving variable.

For the T9 row of ww2_testbed.md section 5 ("re-asked in the crisis sub-game"): K2's first clause holds; its "contested" clause does not as read (forced where the belief condition fails; contested in the fortune sense only when Polish consent is left open and the West may raise the belief).

## 11. Failures and proposed amendments (proposals only; the owner decides)

1. **K2 (d).** As read, "without the belief condition" the attack is forced by Germany, not contested. Proposed amendment: "without the belief condition the attack is forced by Germany; with Polish passage left open (Nature free) and the West's raises available, the attack is contested in the fortune sense (section 4.6): Germany with Nature's refusal forces it, {WEST, USSR} with Nature's consent keeps it out."
2. **K3, driving variable.** The departure tick holds; the driving variable is a three-way tie of Polish passage, the talks and the German approach, because Poland's refusal and the Soviet pact decision fall in one tick. Proposed amendment: "the driving variables are Polish passage, the state of the talks and the German approach (the pact decision), which the record places in the same days (19 to 21 Aug)." An alternative, if the owner wants the claim to separate them: re-ask at daily resolution in that week (Beck 19 Aug; the Soviet draft 19 Aug; Stalin's reply 21 Aug), which three-day ticks cannot do.
3. **K4 (g).** The shortest trace is the attack of 26 Aug, which the readiness part allows; the halt was a choice. Proposed amendment: "the shortest trace through the realized cancellation of 25 Aug shows the re-order and the attack within two ticks" (which holds: one tick).
4. **K1, if read literally against `1939Q3.json`.** Two exit variables differ from the snapshot by v1's own construction (`poland`: the Soviet entry of 17 Sep after the horizon; `oil_GER`: the snapshot's 1936 reading against v1's `accept_pact`). Proposed amendment: "the exit state equals v1's realized transition of 1939Q3; differences between that transition and the hindsight snapshot are v1's and are tabulated" (the reading R1 used). Separately, for v1's owner: `oil_GER` in the v1 snapshots stays `dependent` while v1's `accept_pact` sets `secured`; one of the two should move.

## 12. Omissions and limitations

- Three-day ticks put Poland's refusal and the Soviet pact decision in one tick (K3) and the order of 25 Aug with its halt in one tick (C2); the realized file keeps one decision per actor per tick and notes the other.
- The declarations of 3 Sep sit at the horizon and are applied on return (C3); inside the sub-game WEST's declaration is reachable only after an attack decided by tick 18.
- `belief_GER` is monotone: the Obersalzberg dip of 22 Aug is not modeled, so a belief raised before 22 Aug cannot fall back. The `will_fight` reading of the halt of 25 Aug is contested by Directive No. 1 (31 Aug), which provides for both cases.
- `send_missions`' delay of 5 is the realized pace, not the fastest feasible one; a faster mission is a counterfactual on the pace this model does not represent.
- `west_powers` (C9) is a condition the architect's decision does not name; it adds one Western decision to the alliance's path and does not change any timing on the record (the powers came on 21 Aug, the same tick as the refusal).
- Romania's consent, the political treaty text and the Henderson-Dahlerus exchanges are not modeled (ontology section 7).
- Several sources are marked "(not verified)": the Y-day decision of 23 Aug (Halder), Daladier's instruction and the British powers of 21 Aug, Doumenc's report of 22 Aug, Hitler's stop of the economic talks in late June, the Polish mobilization records.
- `aims_USSR` is read by no guard; K6's "under `aims_USSR = defensive`" is the entry value, not a gate.
- The sub-game is not attached to v1 (v1 has no crisis action and was not edited); the flattened check uses a copy.

## 13. Files, tests and the visualizer

Files of this step: `docs/ontology_crisis_1939.md`, `docs/actions_crisis_1939.md`, `docs/crisis_1939_decisions.md`, `data/ww2/crises/1939/events.csv`, `decisions.csv`, `realized_moves.csv`, `models/ww2/crises/summer_1939.py` (edited), `tests/ww2/crisis_1939/common.py`, `test_model_crisis_1939.py`, `test_K01.py` to `test_K06.py` (un-skipped, CLAIM dicts verbatim), `docs/guard_changelog_ww2.md` (two rows), this report and `reports/crisis_1939_viz.html`.

**The visualizer page.** Built with `wavefront.viz.bundle.bundle` and `wavefront.viz.render.render_html` (the functions behind `wf viz`; the CLI cannot load the entry state) on the reduced build under `deterred + documented_only`, from the entry state with the three belief levels as hypotheses, coalitions {GER}, {WEST, USSR} and {WEST, USSR, Nature}, endings `ATTACK_LAUNCHED` and `NO_ATTACK`, `max_relax` 0. 13,504 states, 5.1 MB, built in 144 s. The traces on the page are the engine's shortest witnesses, not the realized path (section 3 has the realized path); statuses are the model's (the free model, so the {WEST, USSR} column shows the standard kernel and the {WEST, USSR, Nature} column the fortune kernel).
