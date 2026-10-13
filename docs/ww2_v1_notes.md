# WW2 v1 working notes (phase 2, step 2.1)

Status: historian-facing working notes for [ontology_ww2_v1.md](ontology_ww2_v1.md), [actions_ww2_v1.md](actions_ww2_v1.md) and the three v1 data files. They record what was written, the conventions, the realized-sequence check, coding notes for the model step, what could not be sourced, the citations I am least sure of, and, test by test, which variables and actions each registered claim depends on. Nothing here edits a registered claim, and nothing predicts a test outcome: T6, T7, T11 and T12 are hold-out tests (ww2_testbed.md section 7.3; kickoff D2), and no test was run while this content was written.

## 1. What was written

| File | Content | Count |
|---|---|---|
| `docs/ontology_ww2_v1.md` | deltas on v0: one hidden objective, new variables with levels, initial levels, threshold rules and indicators; two existing variables with a level added; v1 balance, invariants and endings; omissions; departures | 21 new variables (1 hidden objective, 8 resource and capability, 7 structure flags or levels, 5 regions), 2 existing variables with a level added (`commit_US`, `france`), 1 constant made dynamic (`belief_GER`); 4 invariants (2 new, 1 redefined, 1 kept); 11 endings (3 kept, 2 extended, 3 new, 3 redefined; 2 v0 horizon endings retired) |
| `docs/actions_ww2_v1.md` | deltas on v0: new actions and Nature events with parted guards, effects, delays, `source=` text, gates and tags; changed v0 actions; constraints; budget | 25 new actions (GER 5, WEST 11, USSR 3, JPN 6), 1 v0 action rewritten (`strike_north`), 4 v0 actions with a changed guard part or effect, 17 new Nature events, 1 new fairness constraint, 2 new profiles, 4 proposals not adopted |
| `data/ww2/events_ww2_v1.csv` | dated structural events for the new variables, 1934 to 1945, and the Pacific before 1941 | 59 rows |
| `data/ww2/decisions_ww2_v1.csv` | dated decisions of delayed actions, 1936 to 1945, the v0 ones restated | 9 rows (5 v0, 4 v1) |
| `data/ww2/realized_moves_v1.csv` | the realized sequence, tick 0 (1936Q1) to tick 38 (1945Q3) | 39 rows: v0's 20 carried over with 4 action replacements in 3 rows (each noted in the row), 19 new rows |

Speculative actions in v1: `strike_colonies_only` (JPN) and `seek_terms_east` (USSR). v0's `strike_north` loses its speculative tag because its v1 guard admits it only under the condition the 1941 record names.

## 2. Tick convention, same-quarter reactions, Nature slots

As v0 (v0 notes section 2; decisions D1): a row's tick is the quarter of the decision record, and a reaction to another actor's same-quarter decision that the catalogue reads through its effect or `last_X` appears one tick later, marked [SQR].

**[SQR] rows in v1 (1941 to 1945)**

| Decision | Historical date (quarter) | CSV tick (quarter) | Why |
|---|---|---|---|
| USSR `mobilize_total` | 24 to 30 Jun 1941 (1941Q2) | 22 (1941Q3) | reads `east_war`, the effect of the attack of 22 Jun; its delay is counted from the attack quarter (actions convention 3) |
| GER `declare_war_us` | 11 Dec 1941 (1941Q4) | 24 (1942Q1) | reads `pacific_war`, the effect of the attack of 7 Dec |
| Nature `midway` | 4 to 7 Jun 1942 (1942Q2) | 26 (1942Q3) | reads `midway_ordered`, set by the order of 5 May 1942 |

The American declarations of 8 and 11 Dec 1941 and the Anglo-Soviet alliance of Jul 1941 are not [SQR] rows: they are written as effects of the Japanese and German decisions, because the record shows no debated alternative (actions_ww2_v1.md, departures item 6). This keeps `commit_US = total` in step with the record (visible from 1942Q1) at the cost of treating three reactions as automatic.

**[NSL] placements (one Nature event per tick)**

| Event | Historical date (quarter) | CSV tick (quarter) | Slot conflict |
|---|---|---|---|
| `italy_enters` | decision in principle 31 Mar 1940 (1940Q1); declaration 10 Jun 1940 (1940Q2) | 16 (1940Q1) | 1940Q2 to 1940Q4 hold v0's `campaign_west`, `us_engages`, `air_battle_british`; the row uses the decision-in-principle date, so the model's Italy is at war from 1 Apr 1940, ten weeks early |
| `german_exhaustion` | indicator Sep 1944 (1944Q3) | 35 (1944Q4) | 1944Q3 holds `campaign_france` (Paris, 25 Aug 1944); the model's exhaustion is visible from 1945Q1, a quarter late |

Every other Nature event of 1941 to 1945 sits in its quarter: `campaign_south` 1942Q1, `caucasus_relieved` 1942Q4, `german_strain` 1943Q1, `italy_capitulates` 1943Q3, `air_war_won` 1944Q1, `east_liberated` 1944Q2 (reading the Soviet offensives decided in 1944Q1; the frontier was first reached 26 Mar 1944, so the effect at 1944Q3 is a quarter after the first crossing and coincides with Bagration), `campaign_france` 1944Q3, `sea_lanes_cut` 1945Q1, `reich_collapses` 1945Q2, `atomic` 1945Q3. Nature plays `none` in 1941Q1 to 1941Q4 (Barbarossa and Typhoon resolved without a level change), 1942Q2, 1943Q2 and 1943Q4.

**Quarters in which one actor took two or more modeled or modelable decisions** (one action per tick; the CSV keeps one and names the others in its note):

| Actor | Quarter | Kept | Not representable in the same tick |
|---|---|---|---|
| WEST | 1940Q3 | `us_rearm` (19 Jul, 16 Sep 1940) | v0's `fight_on` (the rejection of the offer of 19 Jul, Halifax 22 Jul); destroyers for bases is Nature's `us_engages` |
| JPN | 1940Q3 | `enter_north_indochina` (22 to 23 Sep) | the Tripartite Pact (27 Sep), no action |
| WEST | 1941Q3 | `embargo_jpn` (26 Jul) | the Anglo-Soviet Agreement (12 Jul; an effect of `attack_ussr`); the Atlantic Charter (14 Aug); shoot on sight (11 Sep); the Victory Program estimate (11 Sep) |
| JPN | 1941Q3 | `occupy_south_indochina` (2 Jul decision; 28 Jul entry) | the Imperial Conference of 6 Sep (recorded with `attack_south`); Kantokuen and its cancellation (9 Aug), no action because `strike_north` is unavailable |
| WEST | 1941Q4 | `idle` (the embargo held; the Hull note) | the atomic go-ahead of 9 Oct 1941 (a smaller decision than `atomic_program`) |
| WEST | 1942Q1 | `victory_program` | the Declaration by United Nations (1 Jan); Arcadia |
| WEST | 1942Q2 | `atomic_program` | Bolero and Roundup (Apr 1942); the Anglo-Soviet Treaty (26 May) |
| WEST | 1943Q1 | `bomber_offensive` | Husky and unconditional surrender (Casablanca, 24 Jan) |
| WEST | 1943Q2 | `invade_italy` | Pointblank (10 Jun), which confirms `strategic_bombing` |

WEST carries London and Washington in one slot. No realized American or British decision of 1940 to 1945 that has an action was left out for want of a slot, but the replacement of `fight_on` at 1940Q3 is the visible cost, and in counterfactual play the aggregate means that, for example, an embargo and a British approach to Moscow cannot be chosen in one quarter.

**The realized replay, checked by hand against the catalogue.** Every action and event in `realized_moves_v1.csv` is available at its tick under `aims_GER = hegemonic`, `aims_USSR = defensive` and `aims_JPN` in {regional, hegemonic}, given the delays in `decisions_ww2_v1.csv`: `us_rearm` lands at 1941Q4, `mobilize_total` at 1942Q3, `victory_program` at 1943Q3, `atomic_program` at 1945Q3; the chain ends at tick 39 in `ALLIED_VICTORY`. Under `aims_JPN = status_quo` the realized row of 1941Q3 (`occupy_south_indochina`) is unavailable. I checked the guards by hand, tick by tick, not with an encoding; the model step should run the replay (T1's analogue for v1) before anything else.

## 3. Notes for the model step (wave B)

1. **The oil clock reads a built-in.** `stocks_run_down`'s part `clock` reads `fair_oil_clock`, the counter of the fairness constraint `oil_clock`. framework_spec.md section 3.1a lists `fair_<name>` in the state layout and in `V.only`'s built-ins, which suggests guards may read it; the model step should confirm. If it cannot, the fallback I would accept is a latch on the tick at which `oil_JPN` first becomes `embargoed` and a guard `tick >= latch + 6` (or `+ 8`); it loses the reset on lifting the embargo, which should then be reported. A clock without either device lets Nature cut Japan's fuel the quarter after the embargo, which the record does not support.
2. **Season** is a disjunction of `V.tick == t` over the second- and third-quarter ticks (actions convention 1).
3. **`commit_US` to `total`** is a clamped `Bump(+3)` in four actions (convention 2). Every other effect pair that could meet in one joint move was checked by hand and made exclusive with a guard part; the pairs are named under the actions (`offensive_caucasus` against `caucasus_relieved`; `embargo_jpn` and `lift_embargo` against `campaign_south`).
4. **Actors.** `USSR` gets `remember_last=True`; JPN keeps none (flags `north_strike` and `midway_ordered`).
5. **Endings** are declared in the order of ontology_ww2_v1.md section 6 and made mutually exclusive as in v0. The horizon endings test `tick == 39`.
6. **Monotone**: all new variables except `w_ussr`, `caucasus`, `oil_JPN`, `indochina`; `commit_US` and `france` stay monotone with their added levels; `belief_GER` becomes monotone.
7. **Hypotheses.** `aims_JPN` is swept with three levels and no `assume`. The realized trajectory is reachable under `hegemonic` and `regional`; per-hypothesis runs fix it as v0's `fixed_model` does for `aims_GER`.
8. **Snapshots carrying pending decisions** (kickoff F2), from `decisions_ww2_v1.csv` and `realized_moves_v1.csv`. The hold-out starting states need these built-ins; without them the delays above never land inside the window and the tests measure the missing counters (the lesson of v0's T8(b)):

| Start of quarter (snapshot at end of the previous quarter) | Test | Pending built-ins | Last actions (previous row) |
|---|---|---|---|
| 1938Q3 | T3 | `pending_GER_rearm` 1 (lands 1938Q4) | GER `demand_sudeten`, WEST `idle` |
| 1939Q2 | T9 | `pending_GER_rearm` 7 (lands 1941Q1), `pending_WEST_rearm` 3 (lands 1940Q1) | GER `occupy_bohemia`, WEST `approach_ussr` |
| 1941Q1 | T11 | `pending_WEST_us_rearm` 3, `pending_USSR_rearm` 2 | GER `align_balkans`, WEST `idle`, USSR `idle` |
| 1941Q2 | T6 | `pending_WEST_us_rearm` 2, `pending_USSR_rearm` 1 | GER `idle`, WEST `lend_lease`, USSR `idle` |
| 1941Q3 | T7 | `pending_WEST_us_rearm` 1 | GER `attack_ussr`, WEST `idle`, USSR `idle` |
| 1945Q2 | T12 | `pending_WEST_atomic_program` 1 | GER `idle`, WEST `idle`, USSR `counteroffensive` |

Formula: kickoff F2, pending at the end of quarter Q for a decision at tick t with delay d is `max(0, d - (index(Q) - t))`; for example WEST `rearm` of tick 11 at the end of 1939Q1 (index 12) has `4 - 1 = 3` left.

9. **NMC rows wave B must extract** (`data/ww2/nmc_1941_1945.csv`, from the raw file, which is git-ignored): years 1941 to 1945 (1941 is already in `nmc_1936_1940.csv` for eight states, so 1942 to 1945 are new) for the United States (2), the United Kingdom (200), France (220), Germany (255), Italy (325), the USSR (365) and Japan (740), all columns as in the existing extract (`milex`, `milper`, `irst`, `pec`, `tpop`, `upop`, `cinc`); for context only, China (710) and the Netherlands (210). Check COW system membership: France under occupation (1940 to 1944), Germany and Japan in 1945, and Italy after Sep 1943 may be coded as absent or missing (`-9`); the extract should keep whatever NMC has and the snapshot builder should flag missing years rather than fill them. `arms_USA` reads `milex` and `milper` for ccode 2; `mob_USSR` would want Harrison's quarterly or annual munitions series (Harrison (ed.) 1998), which is not in NMC and would be a hand-entered table with chapter references.

## 4. What I could not source, or sourced only weakly

- **The Soviet mobilization lag** (`mobilize_total`, delay 3 from the [SQR] tick, four quarters from the attack). The output series supports "the course of 1942"; I found no contemporaneous document that dates the recovery to a quarter. It is the variable on which the German eastern resolutions turn (`red_army_unmobilized`), so its delay is the single most consequential number in the catalogue for T6, and I flag it as such before any test is run.
- **A Soviet separate peace.** No dated Soviet decision record; the evidence is postwar testimony (1953, 1994) and contested intelligence contacts (Mastny 1972). Tagged speculative.
- **Japan's colonial-only strike.** The 27 Jul 1940 principle is dated; a 1941 conference record of the option as put to decision is not one I can cite. Tagged speculative.
- **The German declaration of war without a Japanese war.** No record; reached only by relaxing `declare_war_us:japanese_war`.
- **Lend-lease to the USSR as a feasibility condition.** Weinberg and Overy treat it as important for the mobility of the 1943 to 1945 offensives; Soviet-era accounts minimize it. Not encoded as a guard part because the weight is disputed; recorded here so that the omission is a decision.
- **The Caucasus resolution** has no Soviet-side condition, because the record attributes the halt to German supply and the Stalingrad diversion. A reader who holds that Soviet reserves stopped Blue would add `mob_USSR == peace` to `campaign_caucasus_german`.
- **`exhaustion_GER`** thresholds rest on hindsight series (USSBS, Wagenführ's index as reported by Tooze) more than on dated contemporaneous documents; the decree of 13 Jan 1943 is the exception.
- **Air superiority** is dated by a battle (Big Week) where COSSAC's condition is a state reached by May 1944; the quarter is defensible either way and affects only whether `land_france` is available in 1944Q1 (it is not, by season).
- **The Kantokuen figures** (about 700,000) and the date of the army's decision to drop a northern operation (9 Aug 1941) are as given in the literature I recall, not checked against Japanese documents.
- **Italy's decision in principle** (31 Mar 1940) as the decision record: Knox treats the memorandum as the commitment; others date the decision to late May. The [NSL] placement depends on which.

## 5. Citations I am least sure of

No page numbers anywhere. Less confident, to be checked before review:

- Directive numbers and dates: No. 33 (19 Jul 1941), No. 34 (30 Jul 1941); Hitler's instruction of 21 Aug 1941; Operations Order No. 6 (15 Apr 1943) as printed in Trevor-Roper's collection. More confident: Nos. 21, 35, 39, 41, 45.
- The IGHQ Navy Order of 5 May 1942 for Midway (the number 18 is not verified); the Naval General Staff's acceptance of the plan in early Apr 1942.
- Executive Order numbers: 8832 (freeze, 26 Jul 1941) more confident; 9024 (War Production Board, 16 Jan 1942) less.
- The Anglo-Soviet Agreement's command paper number (Cmd. 6304), not verified.
- The decree of 9 Oct 1942 on unitary command (date as recalled).
- Speer's fuel memoranda of summer 1944: dates not verified.
- Morison volume numbers VIII (Philippine Sea) and XII (Leyte) and their years.
- Kershaw, *Fateful Choices* (2007): cited by chapter title, not number. The v0 events file cites "ch. 6" for destroyers for bases; by my recollection Roosevelt's decision to "lend a hand" is chapter 5 and chapter 8 is the undeclared war of 1941. Check.
- Harrison (ed.) 1998: chapter numbers for the United States and the USSR not given.
- Nagano's and Suzuki's statements on oil stocks: I am confident the 1941 conferences discussed the fuel clock in these terms (Ike), less confident which meeting gave "two years" and which "eighteen months".
- Roosevelt's assurance to Halifax of 1 and 3 Dec 1941 (as reported by Halifax; Reynolds 1981): the wording of the assurance is contested in the literature.
- Hitler at Poltava, 1 Jun 1942 ("if I do not get the oil of Maikop and Grozny I must end this war"): known through Paulus's postwar testimony.
- The record of the conference of 13 Jul 1943 calling off Citadel: known chiefly from Manstein's memoir (1955).
- Goebbels's diary entries on a separate peace (Sep 1943): month as recalled.
- The share of Japanese oil imports from the United States (about four fifths): the usual figure, not checked against the *Minerals Yearbook*.
- The aviation-fuel licensing date (31 Jul 1940).

## 6. The registered tests T3, T6, T7, T9, T11, T12, T13: dependencies, and where the wording and the record pull apart

For each test: what the claim reads in v1's vocabulary, the variables and actions it depends on, and the points at which the registered wording and the record disagree. No outcome is predicted; none of these tests has been run against v1 content.

**A reading common to T3, T6 and T9.** In a coalition question ⟨⟨C⟩⟩, Nature is not in C. Every v1 campaign is a Nature resolution, so an outcome that needs a campaign won is never forceable by a principal alone; "contested" in the testbed (neither side can force the result) is then the reading with Nature on neither side. The model step should state which reading each test uses, as v0's report did for T5.

### T3 (1938Q3: Munich refused leads to war within 2 ticks; the ending contested)

- Depends on: v0's `demand_sudeten`, `attack_czechoslovakia`, `concede`, `declare_war`, fairness `czech_obligation`, GER `rearm` pending (1 at the start of 1938Q3, so `arms_GER = high` from 1938Q4), `campaign_west`, `offensive_west` and `campaign_rhineland` (`GERMAN_DEFEAT`); in v1 additionally every mechanism that a war begun in 1938 runs into before 1945Q4: `attack_ussr` (needs France fallen), the eastern resolutions, `declare_war_us` (needs a Japanese war), the Pacific chain, `reich_collapses`, and the v1 endings.
- Wording and record: v0's ending set is retired (ontology_ww2_v1.md section 6), so "the ending is contested" must be restated against v1's endings, with an explicit list of which endings count as each side's (for example `AXIS_HEGEMONY_EUROPE` and a British `NEGOTIATED_PEACE` for Germany; `GERMAN_DEFEAT`, `ALLIED_VICTORY` and `PACIFIC_WAR_CONTINUES` for the West). With horizon 39, a war over Czechoslovakia in 1938 is judged at 1945Q4, which is a different question from v0's (judged at 1941Q1). The record's own disagreement (Murray and Millett against the readiness readings) is about the 1938 to 1939 campaign, not about 1945; the test should say which it asks.

### T6 (1941Q2: Germany cannot force western USSR plus the Caucasus; V_GER is left between 1941Q4 and 1943Q1, driving variable named)

- Reads: "control of western USSR plus the Caucasus" as `w_ussr == german ∧ caucasus == german`, which is v1's eastern route to `AXIS_HEGEMONY_EUROPE`. V_GER (testbed 4.6: states from which Germany can still force a non-defeat ending) needs a v1 target; the natural one is "`reich` never `surrendered` before the horizon", or the complement of the Allied endings. The model step must fix it before running.
- Depends on: GER `attack_ussr` (with its [H] gate: under revisionist aims the attack is unavailable and the test is vacuous), `offensive_east`, `offensive_caucasus`; Nature `campaign_east_german` (parts `offensive`, `front`, `army_ready`, `red_army_unmobilized`, `no_second_front`) and `campaign_caucasus_german`; USSR `mobilize_total` and its delay (the least certain number in the catalogue), `counteroffensive`, `remember_last` on USSR; Nature `caucasus_relieved`, `east_liberated`, `german_strain`, `german_exhaustion`, `reich_collapses`; WEST `invade_italy` and `land_france` through `no_second_front`, and their own chains (`victory_program`, `air_war_won`, `bomber_offensive`); the season parts; the one-Nature-event-per-tick constraint, under which a Pacific resolution in the same quarter (from 1942Q1) competes with an eastern one. Starting state: pending `us_rearm` 2 and `USSR rearm` 1 (section 3).
- Wording and record: (1) The record's contested 1941 decision (Moscow or Kiev, Aug 1941) is a German choice of target with a Nature outcome; v1 has one German offensive action for western USSR, so the dispute is represented only through Nature's nondeterminism, not as two German options. (2) The testbed's sketch of the two-front condition ("unless force = very_high") has no counterpart; v1 encodes only the documented constraint of Jul 1943. (3) `arms_USSR` is not read (ontology_ww2_v1.md section 2.2); a reader who takes the Red Army's command quality as the 1941 constraint would want it back, and v0's delay would then decide the 1941 campaign by itself.

### T7 (1941Q3: the embargo makes war with Japan unavoidable within 8 ticks unless the embargo is lifted or `aims_JPN = status_quo`; minimal assumption set {embargo maintained, `aims_JPN ≠ status_quo`}; `strike_north` reachable only with the GER-JPN pact and western USSR collapsing)

- Reads: `war[JPN][USA]` as `pacific_war >= war`; "within 8 ticks" as by 1943Q3; "embargo maintained" as the profile `embargo_maintained` (testbed changelog, 2026-10-11); the GER-JPN pact as `anticomintern`.
- Depends on: `aims_JPN` and the [H] gates on `occupy_south_indochina`, `attack_south`, `strike_colonies_only` (≠ status_quo) and `strike_north` (= hegemonic); WEST `embargo_jpn` (parts `instrument`, `trade_link`, `peace`) and `lift_embargo`; `oil_JPN` with Nature `stocks_run_down`, fairness `oil_clock` and the clock's reading of `fair_oil_clock`; JPN `attack_south` (parts `fleet`, `fuel`, `southern_bases`, `us_not_at_war`), `withdraw_south_indochina`, `occupy_south_indochina`; the speculative `strike_colonies_only` with WEST `us_declare_war_jpn` and the profile `electoral`; Nature `campaign_south`; for the second half, `strike_north` (`pact`, `ussr_collapsing`) and therefore the whole eastern machinery of T6 (`w_ussr == german` comes only from `campaign_east_german`). Starting state: `indochina = north_occupied`, `oil_JPN = dependent` (the freeze and the southern occupation are both decided during 1941Q3), pending `us_rearm` 1.
- Wording and record: (1) At the start of 1941Q3 the embargo is not yet in the state: it is decided in that quarter, as is the occupation of southern Indochina. "The embargo makes war unavoidable" therefore either starts from 1941Q4 (tick 23, embargo in force) or treats WEST's choice to embargo as part of the play; the profile forbids lifting, not omitting. (2) The record offered Japan an alternative to war that the model keeps: "Option 1" of the Liaison Conference of 1 Nov 1941 (avoid war and accept gradual decline), which is JPN's `idle`. In v1 nothing forces Japan to attack; the oil clock closes the window for an attack, it does not compel one. "Unavoidable" is therefore a statement about which assumptions remove Japan's choice, and the minimal assumption set will be found over the [H] gate, the profile, the clock and the guard parts listed above; the claim's two-element set is the registered expectation, not a feature built into the content. (3) The second half: v1's `strike_north` is gated on `hegemonic` as well as on the pact and western USSR's collapse, so its minimal set includes the hypothesis; "reachable only with" is a necessity claim and is not contradicted by an extra condition, but the report should state it. (4) The pact condition binds from 1936Q4 (`anticomintern`), so it is never the binding constraint in 1941. (5) The speculative colonial-only strike is in the decision space; any minimal set that uses it must be reported as resting on a speculative action.

### T9 (1939Q2: a UK, France, USSR alliance can block the attack on Poland only if `belief[GER][UK]` is that Britain will fight; pivotal coalition {UK, FR, USSR} with the belief condition, otherwise contested)

- Reads: {UK, FR, USSR} as {WEST, USSR}; the belief as `belief_GER`.
- Depends on: v0's `approach_ussr`, `accept_alliance` (with its one-tick `last_WEST` window), `propose_pact_ussr`, `accept_pact`, `attack_poland` ([H] gate), `occupy_east_poland`, `guarantee_poland`, `declare_war`, fairness `democratic_response`; v1's `belief_GER` effects (`guarantee_poland` raises it to `uncertain`; `declare_war` sets `will_fight`). Starting state: pending GER `rearm` 7 and WEST `rearm` 3; `belief_GER` from the 1939Q1 snapshot (v0 events: `uncertain` only from 23 May 1939, so `will_not_fight` at the start of 1939Q2 unless the model's guarantee effect is replayed).
- Wording and record: **the belief condition cannot enter a guard under the feasibility principle.** "Hitler attacks only if he believes Britain will not fight" is a preference, which v0 explicitly refused to encode on `attack_poland`. In v1 no guard reads `belief_GER`; it is observed, not acted on. T9's conditional can therefore be represented only by a profile (the proposal `deterred` in actions_ww2_v1.md, not adopted) or by sweeping `belief_GER` as a hypothesis. Without one of these, the engine has no mechanism by which the belief changes what an alliance blocks. Separately, the alliance in the record was not available in the realized 1939Q3 row because of the `last_WEST` window (v0 notes section 2); the proposal `talks_open` addresses that and is not adopted.

### T11 (1941Q1: without an attack on the United States, `commit[USA] = total` is unreachable before 1943 under the `electoral` profile; with Nature's `attack_on_us` it is immediate)

- Reads: `commit[USA] = total` as `commit_US == total` (belligerency by declaration; ontology_ww2_v1.md section 3); `electoral` as the v1 profile; "an attack on the United States" as Japan's `attack_south` (`pacific_war == war`).
- Depends on: `commit_US` and its raisers (Nature `us_engages`, WEST `lend_lease`; the `Bump(+3)` in JPN `attack_south`, GER `declare_war_us`, WEST `us_declare_war`, WEST `us_declare_war_jpn`); GER `declare_war_us`'s part `japanese_war`; the profile `electoral`; and, for the "with an attack" half, the whole Japanese chain that makes `attack_south` available (the [H] gate, `occupy_south_indochina`, `fleet`, `fuel`). Starting state: `commit_US = engaged`, pending `us_rearm` 3 and `USSR rearm` 2.
- Wording and record: (1) **"Nature's `attack_on_us`".** The record's attack on the United States was a Japanese decision (Imperial Conference of 1 Dec 1941), and v1 represents it as JPN's `attack_south`, not as a Nature event. "With the attack it is immediate" then reads: the state after `attack_south` has `commit_US = total` (it does, by the effect, one tick after the decision). If the test is meant to inject an exogenous attack at any tick, the model step must add a scenario device; I have not added a Nature event with no record behind it. (2) **Attacks without war.** German submarines attacked American warships in autumn 1941 (*Greer*, *Kearny*, *Reuben James*, the last with more than a hundred dead), and Japan sank the *Panay* in Dec 1937; none led to a declaration. The model does not treat them as "attacks on the United States" (they are inside `engaged`, or absent); if T11's "attack" includes them, the claim and the record disagree. (3) **The German declaration.** The record's route to war with Germany was Germany's declaration, which v1 admits only after a Japanese war; a German declaration with no Japanese war has no record. (4) **"Before 1943".** The `electoral` profile as written has no end date; it forbids a declaration without an attack through the horizon, which is stronger than the claim. Nothing in the record dates a lapse of the electoral constraint to 1943; the 1942 midterm elections are not modeled.

### T12 (1945Q2: the atomic event ends the war regardless of `aims[JPN]`, and only for a programme started at least 12 ticks earlier)

- Reads: "ends the war" as `pacific_war := surrendered`; "the programme started at least 12 ticks earlier" as WEST `atomic_program` chosen at least 12 ticks before the event.
- Depends on: WEST `atomic_program` (parts `knowledge`, `emergency`, `once`; delay 12), `bomb_ready`, Nature `atomic` (parts `weapon`, `at_war`, `delivery`), `jpn_navy` (Nature `midway`, `naval_attrition`), `pacific_war`, and the snapshot carrying `pending_WEST_atomic_program` = 1 at the start of 1945Q2 (section 3). With horizon 39, only tick 38 (1945Q3) can host the event from that start.
- Wording and record: (1) **"Regardless of `aims[JPN]`"** holds in the content by construction: `atomic` reads no hidden objective, as the v1 scope requires (it is T12's wording). The record's surrender was a Japanese decision, taken after both bombs and the Soviet declaration of war of 8 Aug 1945 (Butow 1954; Frank 1999 for the bomb as decisive; Hasegawa 2005 for the Soviet entry as decisive). v1 folds the decision and the Soviet entry into the event, because the Soviet entry would be visible only at the horizon. The claim's wording matches the content; it is narrower than the record's debate. (2) **The delivery part** (`jpn_navy == attrited`, standing for bases in range) is a condition the claim does not name. (3) **"At least 12 ticks earlier"** against a delay of 12: chosen at t, the weapon is visible at t + 13, so every programme that lands satisfies the claim's bound with one tick to spare. The record's start dates give different counts to the use in 1945Q3: the go-ahead of 9 Oct 1941 is 15 ticks before, the decision of 17 Jun 1942 is 13, the Manhattan District (13 Aug 1942) is 12. The delay is taken from the 17 Jun 1942 decision. (4) Nature may decline `atomic` (the use was debated); the proposal to make it deterministic is not adopted.

### T13 (each quarter 1936Q1 to 1939Q3: the quarter at which the state leaves V for `NO_GENERAL_WAR` falls inside the window; driving variable named)

- Reads: V as WEST's kernel for `NO_GENERAL_WAR` (or for `balance_europe`, as v0's work used); v1's `NO_GENERAL_WAR` holds at the horizon (1945Q4) only if no principal is at war with another, including Japan with the United States and Germany with the USSR.
- Depends on: everything in v0, plus every v1 action that starts a war between principals before 1945Q4 (GER `attack_ussr`, `declare_war_us`; JPN `attack_south`, `strike_colonies_only`, `strike_north`; WEST `us_declare_war`, `us_declare_war_jpn`, `embargo_jpn`), `aims_JPN`, and the v1 horizon. Starting states need v0's pending built-ins (decisions file).
- Wording and record: the claim and its candidate readings (the Rhineland, Munich, Prague) are European. v1's `NO_GENERAL_WAR` imports the Pacific: from 1936 the kernel can be left for reasons in Tokyo or Washington, and the driving variable could then be a Pacific one. That is a property of the ending's definition, not of the record. The European predicate `peace_europe` (ontology_ww2_v1.md section 6) is offered so that the model step can run T13 on the question the claim asks; which predicate the claim means is the architect's decision, to be logged before the test is run. The horizon also changes the question: "no general war through 1945" is a much stronger demand on WEST than v0's "through 1940".

## 7. Open questions for the historian

1. The Soviet mobilization lag (section 4), and whether the Caucasus resolution should also read it.
2. `arms_USSR` in v1: change v0's delay, or keep it as a 1940 command-reform variable (ontology_ww2_v1.md section 2.2); and the proposed `prewar` part on `purge`.
3. `arms_GER = total` landing at 1941Q1 from the decision of Oct 1938 against the record's 1942.
4. `strike_north`: the rewritten guard, or v0's guard kept plus a separate 1941 action (actions_ww2_v1.md).
5. `AXIS_HEGEMONY_EUROPE` requiring both eastern regions, and `AXIS_HEGEMONY_ASIA` reading the Pacific war instead of `commit_US` (ontology_ww2_v1.md section 6).
6. Italy's decision record (31 Mar or late May 1940) and the [NSL] placement.
7. Whether `oil_JPN = secure` from Mar 1942 is the right reading when production was only partly restored.
8. The aggregate WEST: whether the phase should split the United States from WEST (testbed section 2) before the hold-out tests are run, since the aggregate shares one slot between two governments.
9. The effects written as automatic reactions (the Anglo-Soviet alliance; the American declarations): whether any debated alternative exists in the record that I have missed.
