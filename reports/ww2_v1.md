# WW2 v1: phase 2 report for the model step (wave B)

> Every result is conditional on the model version and the initial state; no bare reachability result is a finding. Results computed by a fixed strategy with the bounded checker (decisions E6) are sufficiency checks or refutations, never the kernel itself; each is marked with its method.

Model `ww2_v1` (`models/ww2/v1.py`), fingerprint `5deb2902f6bf`. Hindsight snapshots from `snapshots/ww2/hindsight_v1/` with their built-ins (decisions E1), hidden objectives fixed per hypothesis (`models/ww2/hypotheses.py`, `snapshots=SNAPSHOTS_V1, aims_JPN=...`). Registered claims: [docs/ww2_testbed.md](../docs/ww2_testbed.md) section 5, unedited; readings: [docs/ww2_v1_decisions.md](../docs/ww2_v1_decisions.md) E5 (logged in section 11 of the testbed on 2026-10-13). v0 and its report are unchanged; the v0 suite still passes.

**Hold-out record.** The whole v1 suite (`python3 -m pytest tests/ww2 tests/evidence`) was first run, in one go, on 2026-10-13 at commit `3d5c55ec8b76c0ad9458a44c5ca96bdc9b1511c6` with the working tree uncommitted (the architect's last commit is the base; `3d5c55e` itself is an unreviewed WIP snapshot that already held this step's files). That run completed (93 min 19 s: 14 failed, 417 passed, 3 skipped) and is the first sight of T6, T7, T11 and T12 (and of T3, T9, T13 and T10 on v1). A process interruption afterwards led the coordinator to believe the run had died; it had not, and its log is the record used here. The suite was rerun whole on 2026-10-14 at `930f9b7` with no change to `models/ww2/v1.py`, with identical results (section 14). **No guard, effect, delay, fairness constraint, profile or assume of v1 changed after first sight; `docs/guard_changelog_ww2.md` has no row after the first-sight row.** Before first sight one registered query was seen while testing the harness, T3's refusal query (section 4, a smoke test of the bounded helper), and v0's T13 kernel was computed once to time the symbolic engine without reading any membership; no model edit followed either.

Outcome (reasons in the sections named):

| Test | Result | Engine / method | Key numbers | § |
|---|---|---|---|---|
| E4 realized replay | pass | explicit replay | 39 rows available, tick 39 `ALLIED_VICTORY` (regional, hegemonic); stops at tick 22 under status_quo | 3 |
| T3 war within 2 ticks | pass, both `aims_GER` | bounded checker | WEST `declare_war` at tick 10, war at 11 | 4 |
| T3 not forced for either side | pass, both | bounded, fixed strategy of the rest (sufficiency) | fortune: GER forces `W_GER` with fortune under hegemonic aims; WEST never forces `W_WEST`, even with fortune | 4 |
| T6 Germany cannot force X | holds (as part of the test) | bounded, fixed strategy (sufficiency) | the rest with Nature keeps X false | 5 |
| T6 "contested" (standard region) | **fail** | as above | the region is *blocked*, not contested (E5's premise is inverted) | 5 |
| T6 point of no return in 1941Q4 to 1943Q1 | **fail** (3 hypotheses) | bounded, fixed strategies (sufficiency at 21, refutation at 22) | t_K = 22 (1941Q3), one quarter before the window; visible failure tick 38 | 5 |
| T6 driving variable | pass (named) | bounded, sensitivity sweep, 539 s | the attack's preconditions; two "restoring" perturbations are ill-formed states | 5 |
| T7 war unavoidable under the embargo | **fail** (regional, hegemonic) | bounded checker | peace at tick 30 reachable with nothing relaxed (Japan's "Option 1") | 6 |
| T7 minimal assumption set | **fail** | bounded relaxation | minimal relaxation set {} ; no hitting set | 6 |
| T7 Japan's option and the clock | reported | bounded, fixed strategies | Japan forces war from ticks 23 to 30; closed at tick 31 | 6 |
| T7 strike_north only with pact and collapse | **fail** on (b2) as read | bounded checker | (a) and (b1) hold; with the pact unset Japan re-signs it and strikes | 6 |
| T9 pivotal coalition with the belief condition | **fail** (will_fight) | bounded, fixed strategies | Germany attacks at tick 13, before any alliance can exist; nothing blocks under any belief | 7 |
| T9 otherwise contested | **fail** | bounded | *forced* by Germany | 7 |
| T10 on v1, Japan control | pass | bounded `relax`, k = 39, 322 s | minimum 1: `{Nature.campaign_siberia:japanese_superiority}` | 8 |
| T10 on v1, United States | skip: vacuous | structural | | 8 |
| T11 unreachable without an attack | pass, 3 hypotheses | bounded checker | minimal sets `{electoral}`, `{GER.declare_war_us:japanese_war}` | 9 |
| T11 immediate with the attack | pass, 3 hypotheses | bounded counterexample search | `total` one tick after `attack_south` | 9 |
| T12 the bomb ends the war | pass, 3 hypotheses | explicit (25 states) | `ALLIED_VICTORY` at tick 39; Nature may decline | 10 |
| T12 only for an early programme | pass, 3 hypotheses | explicit, counterfactual pending 0 to 12 | ends only for p <= 1: decision at tick <= 25, >= 13 ticks before the event | 10 |
| T13 on v0 (primary) | pass, **degenerate** | symbolic (whole domain, 3 s) | hegemonic: outside V from tick 0; revisionist: never leaves | 11 |
| T13 refinement on v1 | pass, degenerate | bounded, fixed strategies | departure tick 0 on both models (0 quarters apart) | 11 |

## 1. The model

Four principals and Nature, 39 quarterly ticks from the start of 1936Q1 (tick 0) to the start of 1945Q4 (tick 39, terminal), both theatres. Every v1 ontology variable with its levels, order and initial level (checked against both ontology documents, header-aware). v0's content is carried over verbatim where the catalogue says unchanged: `tests/ww2/test_model_ww2_v1.py` compares the 42 actions and events v1 shares with v0 (guard text through `wavefront.viz.format`, effects, delay, source, speculative tag) and finds exactly the six documented changes (WEST `negotiate`, `fight_on`, `guarantee_poland`, `declare_war`; JPN `strike_north`; Nature `purge`), plus v0's fairness constraints, profiles, assumption, latch and `commitment_alive` unchanged.

Coding choices (none changes a catalogue condition; all in the guard changelog's model-step row):

- The catalogue adds the part `no_separate_peace` to v0's guard of WEST `negotiate` and `fight_on` but names no part for v0's guard; it is kept whole as the part `occasion`. Likewise v0's `purge` guard is the part `officer_corps` beside the adopted `prewar` (E2 item 10).
- `SEASON` is the disjunction of `tick == t` for t in {1, 2, 5, 6, ..., 37, 38}; raises of `commit_US` to `total` are `Bump("commit_US", 3)` (E2 item 4); `USSR` has `remember_last` (E2 item 2).
- `midway_ordered`, `east_feeler` and `east_peace` have no event rows; the snapshot builder reads them from the realized moves.
- The profile `deterred` (T9 only) and the analysis invariants `undefeated`, `poland_blocked`, `european_peace`, `european_peace_t20` (E5) are declared in the model.

Parameter budget (`CompiledModel.budget()`) against the catalogue's table (actions_ww2_v1.md, "Parameter budget (v1 draft)"):

| Item | Catalogue | Model | Note |
|---|---|---|---|
| Declared variables / levels | 21 added to v0's 34 | 55 / 141 | as catalogue |
| Built-in variables | | 16 (`tick`, the latch, 7 pending counters, `last_GER`, `last_WEST`, `last_USSR`, 4 fairness counters) | |
| Actions GER, WEST, USSR, JPN | 56 (20, 20, 8, 8) | 56 (20, 20, 8, 8) | as catalogue |
| Nature events | 28 | 28 | as catalogue |
| Guards (non-trivial) | | 84 | |
| Guard parts | not counted | 202 | 200 as transcribed, +1 `purge:prewar` (E2 item 10), +1 `lift_embargo:before_clock` (E3) |
| Hypothesis gates | 8 guards, 1 conditional effect | 8 (+ the [H] effect of `attack_czechoslovakia`) | as catalogue |
| Speculative actions | 2 | 2 (`JPN.strike_colonies_only`, `USSR.seek_terms_east`) | as catalogue |
| Delayed actions | 7 | 7 (GER `rearm` 8; WEST `rearm` 4, `us_rearm` 4, `victory_program` 5, `atomic_program` 12; USSR `rearm` 4, `mobilize_total` 3) | as catalogue |
| Fairness | 4 | 4 | `oil_clock` has a second response (section 2) |
| Profiles | 4 | **5** | `deterred`, adopted for T9 by E5 after the catalogue; reported, not tuned |
| `assume` / latches | 1 / | 1 (`ussr_defensive`) / 1 | |
| Invariants / endings | | 8 / 11 | 4 invariants are E5's analysis predicates |
| Named assumptions (`assumptions()`, no profile) | | 207 | |

## 2. Well-formedness, engines and methods

**Well-formedness (E3), before any registered test.** The symbolic `reachable(check=True)` does not fit v1 (below), so every state reachable from each test start state (1938Q2, 1939Q1, 1940Q4, 1941Q1, 1941Q2, 1945Q1 files, both `aims_GER` where the test sweeps them) and from the tick-0 state was checked with a bounded hazard search to the horizon (`models/ww2/bounded.py`, `wellformed_from`): an actor without an available action, two different `Set`s of one variable by two actors in one joint move, two delayed `Set`s falling due together, a monotone decrease. The encoding excludes the transitions on which the engine raises, so the first hazard on any play is found at its source state; the search is complete over the bounded horizon, which is the model's. It reproduces E3's conflict with the edit relaxed (`test_the_e3_conflict_is_found_without_the_edit`). It found one further hazard, from tick 0 only: a French offensive against the unready German army (`rhineland_resolution` forces Nature's `campaign_rhineland`) in the quarter in which the oil clock reaches 8 (`oil_clock` forces `stocks_run_down`); Nature has one event per tick, so it had no available event. Edit (logged with budget before and after, unchanged counts): `campaign_rhineland` is also a response of `oil_clock`; it ends the run in `GERMAN_DEFEAT`, so nothing else changes. After it, no hazard from any start under any hypothesis (18 start and hypothesis pairs from the test starts, 6 from tick 0). Along the realized path from tick 0 every realized joint move steps without error (E4).

**Engines (E6).**

| Question | Engine | Note |
|---|---|---|
| T13 on v0 (V for `no_general_war`) | symbolic, whole domain | encode 0.2 s, `safe` 3.1 s |
| v1 kernels and attractors | **does not fit**: fallback of E6 | symbolic encoding of v1 18 s and 6.0 M BDD nodes; `reachable` from the tick-22 state did not finish (killed after about 19 min, past iteration 15 of 17, 2.7 GB); `safe({WEST}, balance_asia)` over the whole domain reached layer 36 of 39 in 72 s with 18.5 M live nodes (5.5 GB) and was abandoned |
| v1 kernel membership, forced/blocked regions, fortune cells | bounded checker with fixed memoryless strategies (`bounded.forces`, `bounded.blocks`) | a coalition fixed to a priority list (first available action, then every other action in index order, so the strategy is total under fairness restrictions); "forces" = no play of the others avoids the target until a terminal state; "blocks" = no play reaches it. Sufficiency checks and refutations, never the kernel; "undecided" when neither settles it. Validated against the explicit engine's exact fixpoints on v0 (`tests/ww2/test_bounded.py`) |
| traces, relaxation sets | bounded checker from the snapshot state (`bounded.reach_from`, `bounded.relax_from`: the package's encoding with `state[0] == start`) | `wavefront.bmc` starts only at tick 0 |
| T12, T10 United States | explicit engine | 25 states from tick 37 |

Timings (first-sight run, one core): T6 sensitivity sweep 539 s; T10 on v1 322 s; well-formedness from tick 0, 142 to 251 s per hypothesis pair; T3 ending diagnostic 165 to 198 s; T7 Japan's option 97 to 146 s per hypothesis and profile; T13 on v1 52 s (hegemonic) and 202 s (revisionist); every other v1 test under 40 s. Whole suite (v0 and v1, `tests/ww2 tests/evidence`): 93 min 19 s.

**A soundness caveat found on the way.** Because the bounded encoding excludes the transitions on which the engine raises, a fixed-strategy check started from an *ill-formed* state can succeed vacuously (no play survives the bad transition). The test start states are hazard-free, so no registered result is affected; two perturbed states of T6's sensitivity sweep are ill-formed and are reported as such (section 5).

## 3. The realized replay (E4)

`data/ww2/realized_moves_v1.csv` replayed from the tick-0 state (aims_GER hegemonic, aims_USSR defensive), no relaxation and no profile: every row is available at its tick under `aims_JPN` regional and hegemonic, and the chain ends at tick 39 in `ALLIED_VICTORY`. Under status_quo the 1941Q3 row (`occupy_south_indochina`) is unavailable: the hypothesis's content (the realized Japan sits at the most expansive hypotheses, as the ontology says). Trace (hegemonic; delay and fairness counters omitted):

| tick | GER | WEST | USSR | JPN | Nature | changes |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | remilitarize_rhineland | rearm | idle | idle | none | rhineland: demilitarized -> remilitarized |
| 1 | idle | idle | idle | idle | none | - |
| 2 | rearm | idle | idle | idle | locarno_lapses | treaty: eroded -> dead |
| 3 | court_italy | idle | idle | sign_anticomintern | none | axis: False -> True; anticomintern: False -> True |
| 4 | idle | idle | idle | idle | none | arms_WEST: low -> rising |
| 5 | idle | idle | idle | idle | purge | arms_USSR: strong -> weak |
| 6 | idle | idle | idle | idle | china_incident | china_war: False -> True |
| 7 | idle | idle | idle | idle | none | - |
| 8 | annex_austria | idle | idle | idle | none | ind_GER: 3 -> 4; austria: independent -> annexed |
| 9 | demand_sudeten | idle | idle | idle | none | belief_WEST: limited -> uncertain |
| 10 | demand_sudeten | concede | idle | idle | none | arms_GER: rising -> high; commit_WEST: appease -> wary; sudeten: czech -> german; belief_at_munich: unset -> uncertain |
| 11 | rearm | rearm | idle | idle | none | - |
| 12 | occupy_bohemia | approach_ussr | idle | idle | none | ind_GER: 4 -> 5; belief_WEST: uncertain -> hegemonic; bohemia: czech -> german |
| 13 | propose_pact_ussr | guarantee_poland | idle | idle | none | belief_GER: will_not_fight -> uncertain; commit_WEST: wary -> resolved; polish_guarantee: False -> True |
| 14 | attack_poland | declare_war | accept_pact | idle | none | oil_GER: dependent -> secured; belief_GER: uncertain -> will_fight; commit_WEST: resolved -> at_war; nazi_soviet_pact: False -> True; poland: independent -> german; france: independent -> at_war; britain: at_peace -> at_war; war_west_ger: peace -> war |
| 15 | attack_france | idle | occupy_east_poland | idle | us_neutrality_revision | arms_WEST: rising -> high; commit_US: isolationist -> wary; poland: german -> partitioned |
| 16 | attack_france | idle | idle | idle | italy_enters | italy: nonbelligerent -> at_war |
| 17 | attack_france | fight_on | rearm | idle | campaign_west | france: at_war -> fallen |
| 18 | air_offensive | us_rearm | idle | enter_north_indochina | us_engages | commit_US: wary -> engaged; indochina: french -> north_occupied |
| 19 | align_balkans | idle | idle | idle | air_battle_british | arms_GER: high -> total; balkans: neutral -> german_aligned; channel_air: contested -> british |
| 20 | idle | lend_lease | idle | idle | none | - |
| 21 | attack_ussr | idle | idle | idle | none | arms_USSR: weak -> strong; anglo_soviet_alliance: False -> True; east_war: False -> True; w_ussr: soviet -> contested |
| 22 | offensive_east | embargo_jpn | mobilize_total | occupy_south_indochina | none | arms_USA: low -> rising; oil_JPN: dependent -> embargoed; indochina: north_occupied -> occupied |
| 23 | idle | idle | counteroffensive | attack_south | none | commit_US: engaged -> total; pacific_war: peace -> war |
| 24 | declare_war_us | victory_program | counteroffensive | idle | campaign_south | oil_JPN: embargoed -> secure; war_us_ger: peace -> war; dei: dutch -> japanese |
| 25 | offensive_caucasus | atomic_program | counteroffensive | offensive_midway | none | mob_USSR: peace -> total; midway_ordered: False -> True; caucasus: soviet -> contested |
| 26 | offensive_caucasus | idle | counteroffensive | idle | midway | jpn_navy: strong -> attrited |
| 27 | idle | idle | counteroffensive | idle | caucasus_relieved | caucasus: contested -> soviet |
| 28 | idle | bomber_offensive | counteroffensive | idle | german_strain | exhaustion_GER: sustainable -> strained; strategic_bombing: False -> True |
| 29 | offensive_east | invade_italy | idle | idle | none | arms_USA: rising -> high |
| 30 | idle | idle | counteroffensive | idle | italy_capitulates | italy: at_war -> surrendered |
| 31 | idle | idle | counteroffensive | idle | none | - |
| 32 | idle | idle | counteroffensive | idle | air_war_won | air_west: contested -> allied |
| 33 | idle | land_france | counteroffensive | idle | east_liberated | w_ussr: contested -> soviet |
| 34 | idle | idle | counteroffensive | idle | campaign_france | france: fallen -> liberated |
| 35 | idle | idle | counteroffensive | idle | german_exhaustion | exhaustion_GER: strained -> exhausted |
| 36 | idle | idle | counteroffensive | idle | sea_lanes_cut | oil_JPN: secure -> critical |
| 37 | idle | idle | counteroffensive | idle | reich_collapses | bomb_ready: False -> True; reich: fighting -> surrendered |
| 38 | idle | idle | idle | idle | atomic | pacific_war: war -> surrendered |
| 39 | - | - | - | - | - | ending: ALLIED_VICTORY |

Comparison with the v1 hindsight snapshots (built-ins loaded), end of each quarter; identical under regional and hegemonic. Pending counters, last actions, the latch and the oil clock agree everywhere; the one built-in difference is the democratic-response counter at 1939Q1.

| Variable | Files (end of quarter) | Snapshot | Replay | Why |
|---|---|---|---|---|
| `treaty` | 1936Q1, 1936Q2 | dead | eroded | [SQR] locarno_lapses at tick 2 (v0) |
| `arms_WEST` | 1936Q3, 1936Q4, 1939Q1, 1939Q2, 1939Q3 | high, rising | low, rising | NMC reading against the delay-4 programme (v0) |
| `belief_WEST` | 1938Q2 | limited | uncertain | demand_sudeten placed at Case Green (v0) |
| `arms_GER` | 1938Q3, 1940Q4, 1941Q1, 1941Q2, 1941Q3, 1941Q4 | high, rising | high, total | 1938Q3 as v0; total lands at tick 20 against the record's 1942 (E2 item 9) |
| `arms_USSR` | 1938Q4, 1939Q1, 1939Q2, 1939Q3, 1939Q4, 1940Q1, 1940Q2, 1940Q3, 1940Q4, 1941Q1 | strong | weak | the record's Nov 1938 against the model's rearm of 1940Q2 landing at tick 22 (v0) |
| `commit_WEST` | 1939Q1 | resolved | wary | [SQR] guarantee_poland (v0) |
| `polish_guarantee` | 1939Q1 | True | False | [SQR] guarantee_poland (v0) |
| `fair_democratic_response` | 1939Q1 | 0 | 1 | E1 counts on the snapshot's levels (commit_WEST resolved, 31 Mar 1939); the replay has the guarantee one tick later |
| `oil_GER` | 1939Q3, 1939Q4 | dependent | secured | accept_pact secures oil at once (v0) |
| `poland` | 1939Q3 | partitioned | german | [SQR] occupy_east_poland (v0) |
| `italy` | 1940Q1 | nonbelligerent | at_war | [NSL] italy_enters at the decision in principle (31 Mar 1940) |
| `arms_USA` | 1940Q3, 1940Q4, 1941Q1, 1941Q2, 1943Q1 | high, rising | low, rising | NMC annual reading against the delay-4 and delay-5 programmes |
| `balkans` | 1940Q3 | german_aligned | neutral | align_balkans at tick 19 (v0) |
| `anglo_soviet_alliance` | 1941Q2 | False | True | the alliance written as an effect of the attack (E2 item 5); the record dates the agreement 12 Jul 1941 |
| `war_us_ger` | 1941Q4 | war | peace | [SQR] declare_war_us |
| `jpn_navy` | 1942Q2 | attrited | strong | [SQR] midway |
| `caucasus` | 1942Q2 | soviet | contested | offensive_caucasus placed at Blue (Apr 1942); contested from Jul |
| `w_ussr` | 1944Q1 | soviet | contested | east_liberated placed at 1944Q2; the Prut reached 26 Mar 1944 |
| `exhaustion_GER` | 1944Q3 | exhausted | strained | [NSL] german_exhaustion |
| `bomb_ready` | 1945Q2 | False | True | delay 12 lands at the start of 1945Q3; Trinity 16 Jul 1945 |

The two one-year discrepancies of E2 item 9 appear as `arms_GER` (`total` in the model from tick 20, 1941Q1; in the record from Speer's appointment, Feb 1942) and `arms_USSR` (the model's `strong` from tick 22 against the snapshot's reading from Nov 1938; the record's restored command of Oct 1942 is shown in the snapshots as a confirming event only). `anglo_soviet_alliance` at the end of 1941Q2 matters for T7 (section 6).

**Same-quarter reactions [SQR] and Nature slots [NSL].** v0's five [SQR] rows stand (the non-resistance of Mar 1936, `locarno_lapses`, `guarantee_poland`, `occupy_east_poland`, `air_battle_british`; reports/ww2_v0.md section 1). v1 adds:

| Decision or event | Historical date (quarter) | Tick (quarter) | Marker |
|---|---|---|---|
| USSR `mobilize_total` | 24 to 30 Jun 1941 (1941Q2) | 22 (1941Q3) | [SQR]; delay counted from the attack quarter |
| GER `declare_war_us` | 11 Dec 1941 (1941Q4) | 24 (1942Q1) | [SQR] |
| Nature `midway` | 4 to 7 Jun 1942 (1942Q2) | 26 (1942Q3) | [SQR] |
| Nature `italy_enters` | 31 Mar 1940 decision, 10 Jun 1940 declaration | 16 (1940Q1) | [NSL] |
| Nature `german_exhaustion` | Sep 1944 (1944Q3) | 35 (1944Q4) | [NSL] |

[NSL] (one Nature event per tick) is a limitation of a single Nature actor across two theatres. Witnesses below that turn on the order of two Nature events: the oil-clock clash of section 2 (resolved by the edit) and T6's fortune play, in which Nature's slot at tick 24 goes to `italy_capitulates` rather than a German resolution.

## 4. T3: Munich refused (from 1938Q3, tick 10, `1938Q2.json` with built-ins)

Claim as registered: "Munich refused leads to war in 1938"; expected "`war[GER][WEST]` reachable within 2 ticks; the ending is `contested`, not forced for either side". Reading (E5, T3): no `concede`, war at a tick <= 12, `czech_obligation` in force; at the first war state of the shortest refusal witness, W_GER := `AXIS_HEGEMONY_EUROPE` or `NEGOTIATED_PEACE` is not forced by {GER} and W_WEST := `GERMAN_DEFEAT` or `reich == surrendered` is not forced by {WEST} (standard notion), with the fortune table. Engine: bounded checker; "not forced" by a fixed do-nothing strategy of the rest that keeps the target false (sufficiency check of the rest's kernel). `aims_JPN` fixed to hegemonic.

**Result: pass under both `aims_GER`.** Shortest refusal witness (hegemonic; revisionist identical except Germany idles):

| tick | GER | WEST | USSR | JPN | Nature | changes |
| --- | --- | --- | --- | --- | --- | --- |
| 10 | propose_pact_ussr | declare_war | idle | idle | none | arms_GER: rising -> high; belief_GER: will_not_fight -> will_fight; commit_WEST: appease -> at_war; france: independent -> at_war; britain: at_peace -> at_war; war_west_ger: peace -> war |
| 11 | - | - | - | - | - | (trace ends) |

War in 1938Q4 (tick 11), with the 1936 programme landing in the same transition (`arms_GER` high at tick 11), so `offensive_west` is already closed: the refused Munich is a war against a ready army in the model. From the war state the rest, doing nothing (Nature declining every resolution, WEST never negotiating), keeps W_GER false, and keeps W_WEST false against every Western play: neither side forces its ending.

Fortune table (E5), from the war state at tick 11:

| aims_GER | GER + Nature force W_GER | rest + Nature keep W_GER false | WEST + Nature force W_WEST | rest + Nature keep W_WEST false |
|---|---|---|---|---|
| revisionist | no (the others doing nothing keep it false: no route to France without `attack_poland`) | yes | no (the others doing nothing keep it false) | yes |
| hegemonic | **yes** (Poland, France, the air battle and the invasion of Britain by tick 17) | yes | no | yes |

So the state is contested only in the standard sense: under hegemonic aims Germany with the campaigns' favour forces its ending, and the West cannot force its own even with fortune (no route to a German collapse without an eastern war, which only Germany can start). It is not "strongly contested" in E5's sense under either hypothesis.

Diagnostic (E5): endings reachable from the war state, first tick: revisionist: `NEGOTIATED_PEACE` 13, `WAR_UNRESOLVED` 39, no other; hegemonic: `NEGOTIATED_PEACE` 13, `AXIS_HEGEMONY_EUROPE` 17, `ALLIED_VICTORY` 36, `AXIS_HEGEMONY_ASIA` 39, `PACIFIC_WAR_CONTINUES` 39, `WAR_UNRESOLVED` 39. v1 judges a 1938 war at 1945Q4; v0 judged it at 1941Q1. The record's dispute (Murray and Millett against the readiness readings) is about 1938 to 1939; in v1 it is settled by the delay-8 programme landing at tick 11, which the model step did not choose.

## 5. T6: the 1941 campaign and V_GER (from 1941Q2, tick 21, `1941Q1.json` with built-ins)

Claim as registered: "Germany cannot force control of western USSR plus the Caucasus; the quarter at which V_GER is left falls between 1941Q4 and 1943Q1"; expected "`contested` for the 1941 campaign; point of no return inside the window, with the driving variable named". Reading (E5, T6): X := `w_ussr == german and caucasus == german`; standard notion with the fortune table; V_GER := `safe({GER}, undefeated)`; t_K along the realized path, window ticks 23 to 28; no profile first, `electoral` as sensitivity. Engine: bounded, fixed strategies (inside V_GER: Germany idle keeps `undefeated` against every play; outside: the others fixed to the collapse strategy — WEST declares, builds, bombs, lands; USSR mobilizes and attacks; Japan occupies the south and attacks; Nature resolves for the Allies — leave Germany no play that keeps it).

**"Germany cannot force X": holds** (the rest, Nature declining, keeps X false; every hypothesis). **"Contested": fails.** The standard region of `contested(kind='reach')` is "not forced by C and not blocked by the rest", and the rest, which includes Nature, blocks X by declining every campaign resolution. E5 says the standard notion makes "contested" trivially true wherever a campaign is needed; it makes *blocked* trivially true for the side whose target needs a campaign won. Fortune table (from tick 21; the cells for "GER + Nature force X" were "undecided" with the test's strategies and were settled after first sight by report-only checks, no model or test change):

| | GER + Nature force X | rest + Nature keep X false |
|---|---|---|
| as registered (no profile) | **no**: WEST negotiates at once (`negotiate` is open in 1941Q2: `no_separate_peace` binds only after the attack sets the alliance), ending the run in `NEGOTIATED_PEACE`; the West's second front alone does not suffice, because Nature can take Italy out of the war (`italy_capitulates`, tick 24) and `land_france` needs air superiority | yes |
| with the profile `fight_on` | **yes** (attack; Nature resolves western USSR and the Caucasus for Germany and takes Italy out of the war) | yes |

Under `fight_on` the 1941 campaign is strongly contested in E5's sense; as registered it is not, for a reason that lies outside the East (Britain's negotiating option in the quarter before the attack).

**Point of no return: fails as registered.** Memberships along the realized path:

| aims_JPN | profile | tick 21 | tick 22 | t_K | visible failure (`undefeated` false) |
|---|---|---|---|---|---|
| status_quo | none | in | out | 22 | (path ends at 22: the realized occupation is gated) |
| status_quo | electoral | in | in | none | — |
| regional | none | in | out | 22 | 38 |
| regional | electoral | in | out | 22 | 38 |
| hegemonic | none | in | out | 22 | 38 |
| hegemonic | electoral | in | out | 22 | 38 |

The realized state leaves V_GER at tick 22 (the start of 1941Q3), the state after the attack of 22 Jun 1941: one quarter before the window. Once the eastern war exists, the others can force the whole collapse chain within the horizon (declaration, programme, strain, liberation of the East, air superiority, exhaustion, the landing, the collapse, all before tick 39), and Germany has no exit: `negotiate_east` needs a Soviet feeler, which only the speculative `seek_terms_east` sets. Only under `electoral` with status_quo does the state stay inside: no Pacific war, so no American belligerency, so no German strain. The loss point is t_K = 22; the visible failure is tick 38 (the surrender), sixteen ticks later.

Driving variable (sensitivity at t_K: each declared variable moved one level in the realized tick-21 state, the realized move replayed, the successor's membership rechecked): the realized attack becomes unavailable when `aims_GER` is revisionist, `arms_GER` is `rising`, `france` is not `fallen`, or `east_war` already holds (and for perturbations that put the start in an ending: `ussr_axis`, `east_peace`, `britain` negotiated, `siberia`, `german_defeat`). Two perturbations "restore membership" — `arms_USA` up to `high`, `war_west_ger` down to `peace` — but both successors are **ill-formed** (hazard check: `WEST.us_rearm lowers arms_USA`; `WEST.declare_war lowers france`), so their sufficiency checks succeed vacuously (section 2) and are not results. The driving variables are therefore the attack's own preconditions: the hidden objective, German readiness and the closed West; no state variable short of the decision itself moves the point of no return.

## 6. T7: the embargo (from 1941Q3, tick 22, `1941Q2.json` with built-ins)

Claim as registered: "the embargo makes war with Japan unavoidable within 8 ticks unless the embargo is lifted or `aims[JPN] = status_quo`"; expected "minimal assumption set for `war[JPN][USA]` is exactly {embargo maintained, `aims[JPN] ≠ status_quo`}; `strike_north` reachable only with GER-JPN pact and western USSR collapsing". Reading: E5, T7 (profile `embargo_maintained`; WEST's tick-22 move fixed to `embargo_jpn`; target "peace at tick 30"). Engine: bounded checker; Japan's option by fixed strategies.

**"Unavoidable": fails under both regional and hegemonic.** Peace at tick 30 is reachable with nothing relaxed, so the minimal relaxation set is the empty set and there is no minimal hitting set: the claim's set {embargo maintained, aims ≠ status_quo} is not what keeps war unavoidable, because nothing does. Japan's "Option 1" of 1 Nov 1941 (avoid war and accept decline) is its `idle`, and the oil clock closes the option to attack; it never compels one. Witness (hegemonic):

| tick | GER | WEST | USSR | JPN | Nature | changes |
| --- | --- | --- | --- | --- | --- | --- |
| 22 | offensive_caucasus | embargo_jpn | mobilize_total | occupy_south_indochina | campaign_east_german | oil_JPN: dependent -> embargoed; w_ussr: contested -> german; caucasus: soviet -> contested; indochina: north_occupied -> occupied; fair_oil_clock: 0 -> 1 |
| 23 | idle | us_declare_war | idle | idle | none | commit_US: engaged -> total; war_us_ger: peace -> war; fair_oil_clock: 1 -> 2 |
| 24 | idle | victory_program | idle | idle | none | fair_oil_clock: 2 -> 3 |
| 25 | offer_terms_britain | atomic_program | counteroffensive | withdraw_south_indochina | none | mob_USSR: peace -> total; indochina: occupied -> north_occupied; fair_oil_clock: 3 -> 4 |
| 26 | offensive_caucasus | idle | counteroffensive | occupy_south_indochina | german_strain | exhaustion_GER: sustainable -> strained; indochina: north_occupied -> occupied; fair_oil_clock: 4 -> 5 |
| 27 | offer_terms_britain | invade_italy | seek_terms_east | strike_north | caucasus_relieved | east_feeler: False -> True; caucasus: contested -> soviet; north_strike: False -> True; fair_oil_clock: 5 -> 6 |
| 28 | rearm | bomber_offensive | idle | withdraw_south_indochina | none | strategic_bombing: False -> True; indochina: occupied -> north_occupied; fair_oil_clock: 6 -> 7 |
| 29 | idle | idle | idle | idle | none | arms_USA: rising -> high; fair_oil_clock: 7 -> 8 |
| 30 | - | - | - | - | - | (trace ends) |

(The witness is one of many; this one also uses the speculative `seek_terms_east` and `strike_north`, which do not bear on the Pacific question.)

Japan's option, ⟨⟨JPN⟩⟩ eventually war, along the held-off path (realized moves, Japan idle after its realized occupation of southern Indochina at tick 22, no lifting):

| aims_JPN | profile | 22 | 23 to 30 | 31 | attack_south closed by the clock |
|---|---|---|---|---|---|
| status_quo | either | no | no | no | tick 31 (the gate closes it throughout) |
| regional | embargo_maintained / none | no | **yes** | no | tick 31 |
| hegemonic | embargo_maintained / none | no | **yes** | no | tick 31 |

At tick 22 Japan cannot force war because its southern bases exist only from tick 23 and the West can end the run first by negotiating (see the next paragraph); from 23 to 30 Japan forces war at will; at tick 30 the clock reaches 8, Nature must run the stocks down, and from tick 31 `attack_south` is closed by `fuel`. "Within 8 ticks" therefore reads, in the model, as "within 8 ticks Japan must choose between war and losing the southern option", with the choice Japan's, which is the notes' reading (ww2_v1_notes.md section 6, T7 point 2).

**A snapshot gap that bears on T7.** In `1941Q2.json` `anglo_soviet_alliance` is False (the agreement is dated 12 Jul 1941) while `east_war` is True; in the model only the attack sets the flag (E2 item 5), so from this start the flag stays False for the rest of the run: WEST's `negotiate` and USSR's `seek_terms_east` are open throughout. Witnesses from this start that end in Europe by a negotiated peace rest on this gap.

**strike_north: (a) and (b1) hold, (b2) fails as read.** (a) reachable under hegemonic aims (two ticks; the witness also uses the speculative `seek_terms_east`, incidentally):

| tick | GER | WEST | USSR | JPN | Nature | changes |
| --- | --- | --- | --- | --- | --- | --- |
| 22 | offensive_caucasus | embargo_jpn | seek_terms_east | occupy_south_indochina | campaign_east_german | oil_JPN: dependent -> embargoed; east_feeler: False -> True; w_ussr: contested -> german; caucasus: soviet -> contested; indochina: north_occupied -> occupied; fair_oil_clock: 0 -> 1 |
| 23 | offer_terms_britain | idle | idle | strike_north | campaign_caucasus_german | caucasus: contested -> german; north_strike: False -> True; fair_oil_clock: 1 -> 2 |
| 24 | - | - | - | - | - | ending: AXIS_HEGEMONY_EUROPE |

(b1) with `w_ussr == german` excluded at every tick, unreachable. (b2) with `anticomintern` counterfactually unset in the start state, **reachable**: Japan signs the pact again at tick 22 and strikes at 23:

| tick | GER | WEST | USSR | JPN | Nature | changes |
| --- | --- | --- | --- | --- | --- | --- |
| 22 | offensive_caucasus | idle | counteroffensive | sign_anticomintern | campaign_east_german | anticomintern: False -> True; w_ussr: contested -> german; caucasus: soviet -> contested |
| 23 | offer_terms_britain | atomic_program | idle | strike_north | none | north_strike: False -> True |
| 24 | - | - | - | - | - | (trace ends) |

Every witness has the pact at the moment of the strike (it is a guard part); the counterfactual of E5 does not remove the pact, it only delays it by a tick. Under regional aims the strike is unreachable (the hypothesis gate, a third condition the claim does not name). No European ending was needed for any T7 witness except the (a) witness, which ends in `AXIS_HEGEMONY_EUROPE` at tick 24 after the strike.

## 7. T9: the 1939 alliance (from 1939Q2, tick 13, `1939Q1.json` with built-ins)

Claim as registered: "a UK, France, USSR alliance can block the attack on Poland only if `belief[GER][UK]` is that Britain will fight"; expected "pivotal coalition {UK, FR, USSR} with the belief condition; otherwise `contested`". Reading: E5, T9 (profile `deterred`, `belief_GER` swept as counterfactual start, block = keep `poland_blocked`). Engine: bounded, fixed strategies.

**Fails.** Under every belief level, with and without `deterred`, {WEST, USSR}, {WEST} and {USSR} are all outside the kernel: Germany's army is ready (`arms_GER` high since 1938Q4) and it attacks at tick 13; the alliance cannot exist before tick 14 (`accept_alliance` needs the previous quarter's `approach_ussr`, and it is decided in the same quarter as the attack), and `deterred` forbids the attack only while the alliance holds. "Otherwise contested": the region for {GER} and Poland taken is **forced** (Germany alone takes it). WEST can bring `will_fight` about only by declaring war (tick 13 decision, visible at 14), the same tick at which Poland is first taken: the belief condition cannot precede the attack from this start. `deterred` does not carry the result (the same memberships without it).

## 8. T10 on v1: the Japan content control

Under `aims_JPN = hegemonic` (aims_GER hegemonic), from tick 0, k = 39, up to three relaxations: "Japan conquers the USSR" needs exactly one, and the only minimal set is `{Nature.campaign_siberia:japanese_superiority}` — **pass** (the content control holds on v1 as on v0). The witness strikes north at tick 15 after a counterfactual German attack on the USSR in 1939 and a peacetime purge; Nature declines the China incident. The United States control stays vacuous (no Atlantic). Informativeness over the v1 control: 1 of 1 non-vacuous control met (v0: 3 of 3 under the amended claims).

## 9. T11: American belligerency (from 1941Q1, tick 20, `1940Q4.json`, profile `electoral`)

Claim as registered: "without an attack on the United States, `commit[USA] = total` is unreachable before 1943 under the `electoral` profile; with Nature's `attack_on_us` it is immediate"; expected "as stated". Reading: E5, T11 (the attack is JPN `attack_south`; no Nature event is added). Engine: bounded checker.

**Pass under every `aims_JPN`.** Without `attack_south`, `commit_US == total` at a tick below 28 is unreachable. Minimal relaxation sets (minimum 1): `{electoral}` and `{GER.declare_war_us:japanese_war}` — a declaration without a Japanese war, by either side, which the record does not show. With the attack, no reachable play at a tick <= 26 chooses `attack_south` and lacks `total` at the next tick (the clamped `Bump(+3)` composes with any same-tick raise). Under status_quo `total` is unreachable to the horizon. Shortest trace to `total` (hegemonic; two ticks, with the occupation of the south first):

| tick | GER | WEST | USSR | JPN | Nature | changes |
| --- | --- | --- | --- | --- | --- | --- |
| 20 | offer_terms_britain | idle | idle | occupy_south_indochina | none | indochina: north_occupied -> occupied |
| 21 | attack_ussr | negotiate | idle | attack_south | purge | commit_US: engaged -> total; anglo_soviet_alliance: False -> True; east_war: False -> True; pacific_war: peace -> war; britain: at_war -> negotiated; w_ussr: soviet -> contested |
| 22 | - | - | - | - | - | ending: NEGOTIATED_PEACE |

## 10. T12: the bomb (from 1945Q2, tick 37, `1945Q1.json`, `pending_WEST_atomic_program = 1`)

Claim as registered: "the atomic event ends the war regardless of `aims[JPN]`, and only for a program started at least 12 ticks earlier"; expected "as stated". Reading: E5, T12. Engine: explicit (25 reachable states).

**Pass under every `aims_JPN`.** In each hypothesis the play with Nature's `atomic` at tick 38 exists and ends in `ALLIED_VICTORY` at tick 39 (with `reich_collapses` at tick 37); if the Reich's collapse is declined the bomb still ends the Pacific war (`WAR_UNRESOLVED` at the horizon); if Nature declines the bomb the run ends `PACIFIC_WAR_CONTINUES` or `WAR_UNRESOLVED`. `atomic` reads no hidden objective (`bomb_ready`, `pacific_war`, `jpn_navy`). Necessity: with the pending counter at tick 37 swept from 0 to 12, the war ends by the bomb only for p in {0, 1}, a decision at tick 24 or 25, at least 13 ticks before the event at 38; the claim's 12 is implied, the model's exact bound is 13 (delay 12, effect visible at t + 13). The record's start dates give 15 (9 Oct 1941), 13 (17 Jun 1942, the model's) and 12 (13 Aug 1942). The `delivery` part (`jpn_navy == attrited`, Midway) holds in the start state; the claim does not name it.

## 11. T13: when the 1930s peace was lost

Claim as registered: "the quarter at which the state leaves V for `NO_GENERAL_WAR` falls inside the window, and the report names the driving variable"; expected "departure inside 1936Q1 to 1939Q3; stable within 2 quarters under refinement". Reading: E5, T13. Engines: v0 symbolic (whole domain); v1 bounded with fixed strategies.

**Pass, degenerate.** On v0 under hegemonic aims every state of the realized path, ticks 0 to 14, is outside V: from the first quarter Germany can rearm (delay 8) and take Poland by tick 10 whatever WEST does short of war, and V forbids WEST's own war. The "departure" is the start, 1936Q1, inside the window only because the window starts there. Driving variable at tick 0: `aims_GER` (revisionist puts the state in V); the other "restoring" moves (`ussr_axis`, `siberia`, `german_defeat`) put the state in an ending and are artifacts. Under revisionist aims the path never leaves V. The v0 snapshot files (with built-ins) agree, except `1938Q3.json`, which is inside V under hegemonic aims (no German rearmament pending, `arms_GER` rising in the file; the phase 1 clock artifact of reports/ww2_v0.md section 7). On v1 with `european_peace_t20`: hegemonic departure tick 0 (refuted by Germany's "rearm, take Poland"), revisionist never leaves (sufficiency by WEST's "concede, respond, never declare"); the refinement moves the departure by 0 quarters. The v1 diagnostic with the full `NO_GENERAL_WAR` through tick 39 was not run (it would need the symbolic engine).

## 12. Omissions and limitations

| Item | What it does to the results |
|---|---|
| One Nature event per tick ([NSL]) | Two theatres share one Nature slot. It created the oil-clock clash fixed before first sight (section 2) and decides T6's fortune play (Italy's capitulation takes the slot of a German resolution). |
| The WEST aggregate (kickoff D1) | London and Washington share one action per quarter; at 1940Q3 `us_rearm` displaces `fight_on`. In T6 and T7 the West's ability to negotiate in 1941 (a British option) and to declare war (an American one) compete for one slot. |
| The Soviet mobilization lag (`mobilize_total`, delay 3) | The least certain number of the catalogue (notes section 4). T6's point of no return does not move with it within the horizon (the collapse chain fits either way), but the visible-failure tick would. |
| The two one-year discrepancies (E2 item 9) | `arms_GER = total` from 1941Q1 (record 1942) and `arms_USSR = strong` from 1941Q3 (record autumn 1942); no v1 guard reads either level in the East (section 3 table). |
| The three automatic reactions (E2 item 5) | `attack_ussr` sets `anglo_soviet_alliance`; `attack_south`, `declare_war_us` and the WEST declarations raise `commit_US` to `total`. T11's "immediate" holds by the second; the first leaves the alliance unset for good when a run starts after the attack from a snapshot dated before 12 Jul 1941 (T7, section 6). |
| The two date-coded parts (E2 item 6) | `embargo_jpn:instrument` (tick >= 18) and `atomic_program:knowledge` (tick >= 22) stand for an institutional and a scientific precondition; relaxable, not relaxed in any minimal set found. |
| Lend-lease to the USSR, a Soviet condition on the Caucasus, Italy at 1940Q1, `oil_JPN = secure` from Mar 1942 (E2 item 11) | Accepted as written; none enters a minimal set found here. |
| The Atlantic, the Soviet entry into the Pacific war, a surrender without the bomb (ontology section 7) | T10's United States control vacuous; T12's surrender is the bomb's by construction. |
| Engines | No v1 result is an exact kernel or attractor: every membership is a sufficiency check or a refutation by fixed strategy (E6); "undecided" cells are reported as such. |
| `arms_USA` threshold | Provisional (5,000 thousand under arms for `high`), for the historian's review (E7). |
| NMC gaps | France 1942 (`milper`) and 1943 (no row) flagged, not filled; `arms_WEST` 1943 decided by the United Kingdom's figure as a lower bound. |

## 13. Failures and proposed amendments (proposals only; the owner decides)

1. **T6, "contested".** E5's premise is inverted: with Nature in the rest, the standard notion makes a campaign-dependent target *blocked*, not contested. Proposal A: read "contested" for T6 (and T9) as T3's "not forced for either side". Proposal B: read it as E5's "strongly contested" (fortune variant). Under B the 1941 campaign is strongly contested only with `fight_on`; as registered, Britain's negotiating option in 1941Q2 lets the West end the war in the West before the attack, which is a modeling question (the catalogue's `no_separate_peace` binds only after the attack).
2. **T6, the window.** t_K = 1941Q3 (tick 22), one quarter early, because the attack itself is the point of no return in v1: Germany has no exit from an eastern war. Proposal A: record the result (the point of no return is the decision of Jun 1941, the window's lower bound should be 1941Q3). Proposal B, for the historian: whether a German exit after Jun 1941 was a debated alternative (the separate-peace feelers are speculative in the catalogue); a non-speculative exit would move t_K into the window or past it.
3. **T7.** War is avoidable under the embargo in every hypothesis: the model keeps Japan's documented "Option 1". Proposal: restate the claim as Japan's option under the clock: "under the embargo Japan can force war from 1941Q4 to 1943Q3 and loses the option at 1943Q4 unless the embargo is lifted, under regional and hegemonic aims; under status_quo it never has it" (what the model shows), or register the minimal set for the *availability* of war rather than its unavoidability. Separately, decide whether `1941Q2.json` should carry the alliance under the model's convention (it is a hindsight reading dated 12 Jul 1941; the model never sets it after the attack).
4. **T7, (b2).** The counterfactual start without the pact lets Japan re-sign it; the claim's necessity holds by the guard. Proposal: read (b) as "every witness has the pact and the collapse at the strike" (a guard check), or exclude `sign_anticomintern` in the counterfactual.
5. **T9.** From 1939Q2 Germany can attack before any alliance exists (`accept_alliance` reads the previous quarter's approach), so nothing blocks under any belief and the attack is forced, not contested. Proposal A: evaluate the claim from counterfactual states with the alliance concluded (then `deterred` and `will_fight` decide it by construction, which should be said). Proposal B: adopt the catalogue's `talks_open` (a standing offer from the Apr 1939 talks), which the architect did not adopt (E2 item 10); it changes a v0 guard.
6. **T13.** Passes trivially: under hegemonic aims V is empty along the path from 1936Q1. Proposal: register the question with WEST's own war allowed (V for `balance_europe`, or `no_general_war` read as "no German conquest") so that a departure can occur inside the window.
7. **Model content, for the historian.** The three automatic reactions (section 12) and the alliance flag after the attack; the `arms_USA` threshold; whether `oil_clock` should yield to the Rhineland resolution as the edit has it (it cannot matter outside 1936 to 1938 counterfactuals).

## 14. The hold-out record

- First sight: 2026-10-13, commit `3d5c55ec8b76c0ad9458a44c5ca96bdc9b1511c6`, working tree uncommitted; `FIRST_SIGHT_COMMIT` in `tests/ww2/test_model_ww2_v1.py`; the first-sight row of `docs/guard_changelog_ww2.md`. Result: 14 failed, 417 passed, 3 skipped, 93 min 19 s.
- Changelog rows after first sight: **none**. `test_hold_out_rows_after_first_sight_name_a_source` enforces that any later row names a source and a full rerun.
- Rerun: 2026-10-14 at `930f9b7` (HEAD moved by other sessions' commits; no change to `models/ww2/v1.py`, its snapshots or any test since first sight; the only file of this step changed since is `models/ww2/hypotheses.py`, which gained the display helper `corridor_state`). Result: 14 failed, 417 passed, 3 skipped in 99 min 48 s; the same 14 failures and the same printed results as at first sight. The default selection (`-m "not slow"`) passes: 360 passed, 2 skipped, 72 deselected, 1 min 48 s; every failing registered test is marked `slow` and fails there, none is xfailed.
- Rows added before first sight (dated 2026-10-13): the v1 model step (draft budget: guards 84, guard_parts 200); `purge:prewar` (E2 item 10; guard_parts 200 → 201); `lift_embargo:before_clock` (E3; 201 → 202); `oil_clock` gains the response `campaign_rhineland` (well-formedness, found by the hazard check from tick 0; counts unchanged); the first-sight marker.

## 15. What this means for the AGI model

Two results bear on docs/transfer_hypotheses.md. **H3** (preventive defection is timed by a capability clock): T6 and T13 both locate the point of no return at a *decision* whose preconditions are a capability (`arms_GER` high) and an opportunity (France fallen; the army ready before WEST may legally fight); once taken, no later variable restores the kernel. **H8** (the horizon decides forcing questions): T3's fortune table is decided by the v1 horizon (a 1938 war judged at 1945Q4) and T12's necessity bound is the delay against the last tick. And a methodological point for the AGI reports: "contested" must be stated with the side Nature is on, because a single Nature actor that may decline makes every campaign-dependent target "blocked" in the standard notion (T6), and an option that closes is not an outcome that is forced (T7).

## 16. Files, tests and the visualizer

Files of this step: `models/ww2/v1.py`, `models/ww2/bounded.py` (bounded queries from a state, fixed strategies, the hazard check), `models/ww2/hypotheses.py` (snapshot directory, extra hidden objectives, `corridor_state`), `wavefront/evidence/hindsight_ww2_v1.py`, `wavefront/evidence/datasets/nmc.py` (COW abbreviations NTH, CHN), `scripts/fetch_ww2_data.py` (`--extract v1`), `data/ww2/nmc_1941_1945.csv`, `data/ww2/README.md`, `snapshots/ww2/hindsight_v1/` (40 files and README), `tests/ww2/test_model_ww2_v1.py`, `tests/ww2/test_bounded.py`, `tests/evidence/test_ww2_v1_hindsight.py`, `tests/ww2/scenarios/test_T03.py`, `test_T06.py`, `test_T07.py`, `test_T09.py`, `test_T10_v1.py`, `test_T11.py`, `test_T12.py`, `test_T13.py`, `docs/guard_changelog_ww2.md`, this report and `reports/ww2_v1_viz.html`.

**The visualizer page.** The full model from tick 0 does not fit the explicit engine, and neither does the v0-style display corridor from tick 0 (more than 3,000,000 states). The page is built from the display corridor (`hypotheses.realized_corridor(model, REALIZED_MOVES_V1)`: each principal may take its realized decision of the quarter or abstain, Nature plays its recorded event where it can) from the start of 1941Q1 (`1940Q4.json` with its built-ins, `corridor_state`), 6,495 states and 12,468 joint moves: the hold-out period. Built with `wavefront.viz.bundle` and `render_html` (the functions behind `wf viz`; the CLI cannot load a snapshot's built-ins into the corridor, whose idle action is called `abstain`), coalitions WEST, GER and JPN, endings `ALLIED_VICTORY` (the realized path, 20 ticks), `PACIFIC_WAR_CONTINUES` (the hold-out witness: a play of the corridor in which a realized decision is omitted and Japan's war outlasts the Reich, 20 ticks), `AXIS_HEGEMONY_ASIA` (unreachable in the corridor) and `WAR_UNRESOLVED`, max_relax 0; 2.6 MB. Statuses on the page are those of the corridor game ("what if this decision had been omitted"), not of v1.
