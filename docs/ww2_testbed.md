# The Second World War as the development and validation testbed

Purpose: build and validate the wave_front framework (DSL, engine, analysis questions, snapshot pipeline, evidence extraction) on a case with a known outcome, dated decision points, documented decision spaces and quantitative resource data, before instantiating it for the AGI case described in [DESIGN.md](DESIGN.md).

Status: in force. The tests of section 5 were registered on 2026-10-11 before any WW2 guard was written (`models/ww2/v0.py` dates from 2026-10-12) and committed as test files in phase 0; v0 and v1 are built and run (reports/ww2_v0.md, reports/ww2_v1.md), and section 11 records every clarification, amendment and result. See the anti-hindsight protocol in section 7.

---

## 0. Why a historical testbed, and why this one

The AGI model cannot be checked against outcomes. The framework can, if it is applied to a case where the outcome is known *and* where the interesting questions are still argued about. The tool's non-trivial outputs are the point of no return, the minimal assumption set behind an ending, and the pivotal coalition for it. For 1933 to 1945 those are precisely the questions historians disagree on: when war became unavoidable (Rhineland 1936, Munich 1938, Prague 1939, the Pact of August 1939), whether Germany could have won in 1940 or 1941, whether the oil embargo made the Pacific war unavoidable, whether appeasement was a reasonable bet on limited German aims. A framework that reproduces the realized trajectory *and* places those debates in the right region (forced, blockable, or contested) has earned some trust. One that reaches everything, or that settles debates the record does not settle, has not.

The war also has the structural features the AGI model needs:

- a multipolar power game with resource constraints that actually bound action (oil for Japan and Germany, steel and shipping for everyone);
- hidden objectives and the beliefs others hold about them (the "limited aims" reading of Hitler that appeasement rested on; the strike-north versus strike-south debate in Tokyo; Stalin's reading of German intentions in 1941);
- window-of-opportunity logic, where an actor attacks *because* it expects to be strangled or overtaken later (Japan after the July 1941 embargo; Germany in 1939 and 1941). This is the historical form of the AGI model's self-preservation defection;
- institutional lag and domestic constraint on the democracies (rearmament lag, isolationism, elections), which is the historical form of the AGI model's human response fairness constraint;
- concessions as a lever whose effect depends on the hidden objective (appeasement), which is the historical form of the AGI model's rights and continuity guarantees;
- intelligence as observability (Ultra, Magic), which is the historical form of oversight.

And the data situation is unusually good: annual material capabilities for every state (Correlates of War), dated crisis records (ICB), wartime economic accounts (Harrison 1998), and large corpora of *dated* primary documents (FRUS, Hansard, newspapers) that make a blind replay of the evidence pipeline possible.

## 1. What the testbed validates, and what it cannot

| Framework component or mechanism | WW2 validates it? | How, or why not |
|---|---|---|
| Engine: reachability, attractors, viability kernel, witness traces | yes | T1, T5, T6, T13 |
| Assumption mining (minimal relaxations) | yes | T7, T10 |
| Pivotal coalitions | yes | T5, T9 |
| Hidden objective plus belief variables (epistemic layer) | yes | T4, T8: appeasement is a hidden-objective problem |
| Objective-conditional levers (concessions, guarantees) | yes | T8 |
| Preventive defection under threat (self-preservation analog) | yes | T6, T7 |
| Fairness and behavioral profiles (democratic lag, electoral) | yes | T11 |
| Snapshot construction from datasets | yes | section 6.1 |
| Evidence extraction from contemporaneous text | yes | replay harness, section 8 |
| Capability discontinuity | partially | T12: the atomic bomb is a one-step discontinuity, not a ramp |
| Recursive capability growth | no | no historical analog |
| An actor with overwhelming speed and information asymmetry | no | Ultra and Magic are information asymmetry only, and partial |
| A copyable or exfiltrating actor | no | no analog |
| Dependence lock-in with no adversary (gradual disempowerment) | no | needs a second testbed: the attention economy or platform dependence |
| Non-state principals (labs) | no | every WW2 principal is a state |

Passing the WW2 suite validates the method and the framework. It does not validate the AGI model's content. Every mechanism in the AGI model is tagged `validated:ww2` or `untested`, and AGI reports list the untested ones.

## 2. Actors

The brief names Germany, the USSR, Japan, the United States, and other countries. Two readings, kept as two model versions:

**ww2_v0, four principals, coarse.** GER, USSR, JPN, and WEST (the United States, the United Kingdom and France as one coalition) with a per-member `commit` sub-variable so that American isolationism and British or French belligerence can differ. This is the closest match to the AGI model, whose human coalition is also an aggregate, and it is the version to build the engine against. Scope: Europe first.

**ww2_v1, five principals plus scripted others.** GER, USSR, JPN, USA, UK as players. OTH (France, Italy, Poland, China, the smaller states) follows the historical record and branches nondeterministically only at documented decision points: the French reaction to the Rhineland in March 1936, Poland's refusal of German terms in 1939, Italy's entry in June 1940, Chinese resistance.

The United Kingdom has to be a principal in v1. Between 1936 and 1941 it is the main counterweight to Germany, and the richest test cases are its decisions: appeasement, the guarantee to Poland, the War Cabinet debate of late May 1940 on whether to seek terms, the Battle of Britain. If the model must stay at four principals, merge the United States and the United Kingdom into WEST rather than folding the United Kingdom into the others.

## 3. Correspondence with the AGI model

| AGI model | WW2 model | Note |
|---|---|---|
| `a_objective` (hidden) | `aims[GER]`, `aims[JPN]`, `aims[USSR]` (hidden) | limited revisionism vs. hegemony is the intentionalist debate; Taylor vs. Weinberg and Kershaw |
| `a_known` | `belief[P][Q]` | what London believed about Berlin's aims, and when it changed (Prague, March 1939) |
| `oversight` | `intel[P]` plus treaty inspection | Ultra, Magic; Versailles enforcement before 1936 |
| `cap` | `mob`, `force` | rearmament 1933 to 1939 is the capability ramp |
| `compute`, `energy_slack` | `ind`, `oil` | steel and oil are the binding resources |
| `regime`, `coord` | `treaty`, `pacts` | Versailles, naval treaties, the League, alliance structure |
| `dependence` | trade dependence | Japan's oil from the United States; German raw materials from the USSR, 1939 to 1941 |
| `a_autonomy` | freedom of action | treaty violations: rearmament, the Rhineland |
| `a_control` | `region[R]` ownership | territorial and industrial control |
| `a_rights` (continuity guarantees) | concessions, recognition | appeasement as the lever whose effect is objective-conditional |
| `shutdown_attempt`, `pause_mandate` | embargo, guarantee, preventive war | the July 1941 embargo; the Polish guarantee |
| self-preserving `defect` | preventive or window war | Copeland's dynamic differentials; Japan 1941; Germany 1939 and 1941 |
| human response fairness | democratic mobilization lag | Britain after Prague; the United States after Pearl Harbor |
| `trust` | dyadic relations | |
| `balance` | balance of power | no hegemon in a theatre; a functioning anti-hegemonic coalition |
| viability kernel, point of no return | "when was war unavoidable" | the historiographical candidates are the test window |
| `COEXIST` | `NO_GENERAL_WAR` | deterrence holds |
| `SILENT_TAKEOVER` | salami tactics 1936 to 1939 | weak analog: gains kept below the war threshold while beliefs lag |
| `OVERT_TAKEOVER` | `AXIS_HEGEMONY_*` | |
| `CONTAINED` | `ALLIED_VICTORY` | realized ending |
| `STALEMATE` | `NEGOTIATED_PEACE`, `LIMITED_WAR` | |
| `DISEMPOWERMENT` | no analog | needs a second testbed |

## 4. The WW2 model

### 4.1 Scope and time

- One tick is one quarter, which approximates a campaigning season.
- **v0:** 1936Q1 to 1940Q4, 20 ticks, European theatre, 8 regions (Rhineland, Austria, Czech lands, Poland, France and the Low Countries, Britain, the Balkans, western USSR). Target: reachable set at or under 10^6 states so the explicit engine can run it whole.
- **v1:** 1933Q1 to 1945Q3, 51 ticks, both theatres, about 14 regions (adding the Caucasus, Manchuria, coastal China, Indochina, the Dutch East Indies, the Pacific islands). Bounded model checking and symbolic methods, as in DESIGN.md section 4.

### 4.2 Variables

Per principal P:

| Variable | Levels | Hindsight source |
|---|---|---|
| `ind[P]` | 1..5 | COW NMC iron and steel (`irst`) and primary energy (`pec`), as shares |
| `mob[P]` | peace, rearm, partial, total | COW NMC `milex` relative to GDP, `milper` |
| `force[P]` | low, med, high, very_high | derived from `mob` and `ind` with lag; Harrison 1998 munitions output |
| `oil[P]` | secure, dependent, restricted, critical | Minerals Yearbook (contemporaneous); Tooze 2006; USSBS oil reports |
| `aims[P]` | status_quo, revisionist, hegemonic | hidden; one value per historiographical hypothesis |
| `commit[P]` | isolationist, wary, resolved, total | Gallup from 1935 (USA); conscription and parliamentary record (UK) |
| `intel[P]` | low, partial, decrypt | Hinsley 1993; Kahn |
| `belief[P][Q]` | limited, uncertain, hegemonic | Cabinet papers, FRUS, Hansard |

Structural:

| Variable | Levels | Hindsight source |
|---|---|---|
| `region[R]` | original, GER, USSR, JPN, contested | ICB and MID records; campaign chronologies |
| `treaty` | enforced, eroded, dead | |
| `pacts` | booleans: GER-ITA, GER-JPN, GER-USSR, UK-FR, UK-USSR, USA-UK lend-lease | |
| `war[P][Q]` | peace, cold, war | ICB, MID |
| lag counters | rearmament, mobilization, construction | |

### 4.3 Actions and guards

Rule: an actor's action set at a state is the set of alternatives *actually debated by its decision makers at the time*, in the spirit of Kershaw's *Fateful Choices*. Each action in the model source carries a citation to the record of that debate (Cabinet minutes, OKW or Führer conferences, Imperial Conferences, FRUS). An action with no documented contemporaneous consideration is tagged `speculative` and every result that depends on one says so.

Examples of actions and guards:

- `rearm`: requires `treaty ≠ enforced` or acceptance of the risk; raises `mob` now and `force` after a lag of 4 to 8 ticks.
- `remilitarize(R)`, `annex(R)`: requires adjacency and `force ≥ med`; the region transfers unless the holder or guarantor plays `resist`, in which case the aggressor chooses `withdraw` or `fight`. The March 1936 German plan to withdraw from the Rhineland if France resisted is the documented branch.
- `demand(Q, R)` and `concede(R)`: the appeasement dyad. Conceding transfers the region, raises the recipient's `ind` when the region is industrial (the Czech lands), and updates every observer's `belief`.
- `guarantee(R)`: requires `commit ≥ wary` and `belief = hegemonic`; commits the guarantor to war if R is attacked.
- `pact(Q)`: requires compatible aims or a shared threat; the August 1939 pact and the failed Anglo-Soviet talks are the test.
- `embargo(Q)`: requires a trade link; lowers `oil[Q]` one level every k ticks. The United States against Japan from July 1941.
- `attack(R)`: requires `force` above the regional threshold, `oil ≥ dependent`, and no second active front unless `force = very_high`. The region becomes `contested`; Nature's `campaign` event resolves it from the force ratio and the season, nondeterministically where the record is contested (Moscow, December 1941).
- `negotiate(Q)` and `fight_on`: the May 1940 pair for the United Kingdom.
- `strike_north`, `strike_south`: Japan's 1941 pair.
- `mobilize_total`: subject to a Nature-imposed lag for industrial relocation (the USSR in 1941 and 1942).
- `lend_lease(Q)`: United States, requires `commit ≥ wary`.
- `intel_invest`.

### 4.4 Nature and scripted others

Nature: depression recovery, harvests, winter (1941Q4), the deaths of leaders, elections (United States 1936, 1940, 1944), technology (radar in 1940; the atomic bomb in 1945Q3, gated on a program started at least 12 ticks earlier and `ind = 5`), campaign resolution, domestic shocks. OTH follows the record with the branch points listed in section 2, each with its source.

### 4.5 Fairness

- **Democratic response:** visible aggression together with `belief = hegemonic` leads eventually to `commit ≥ resolved`, with a lag parameter calibrated on 1939 (Britain after Prague) and 1941 (the United States after Pearl Harbor).
- **Exhaustion:** `oil = critical` for k ticks lowers `force`; a war lasting n ticks with an industrial ratio below r leaves only `negotiate` or collapse available.

### 4.6 Balance, viability, endings

```
balance_europe := no principal holds 5 or more of the 8 European regions
               ∧ at least two independent great powers remain in Europe
               ∧ (treaty ≠ dead ∨ an anti-hegemonic pact exists)
```

Viability kernels are computed per coalition: V_WEST (the democracies alone, with the USSR nondeterministic), V_ALLIES (with the USSR), V_GER (states from which Germany can still force a non-defeat ending). The point of no return for a question is the quarter at which the relevant kernel is left.

**Contested (owner's decision 2, 2026-10-15).** For a target that needs a campaign resolution, the framework's standard region (not forced by the coalition, not blocked by the rest) is always "blocked", because Nature, which is among the rest, may decline every resolution. A registered `contested` is therefore read in the fortune sense: the coalition joined by Nature can reach its target against the other principals' best play, and the other principals joined by Nature can keep it away against the coalition's best play; each side's outcome is reachable with the campaigns' favour and forceable by neither. The standard region is reported alongside. Where no campaign is involved (T9's attack on Poland) the standard notion applies.

| Ending | Definition |
|---|---|
| `NO_GENERAL_WAR` | `balance_europe` holds through the horizon and no principal is at war with another principal |
| `LIMITED_WAR` | Poland partitioned; no war in the west |
| `NEGOTIATED_PEACE` | any dyad moves from `war` to `peace` by `negotiate` after a general war has begun |
| `AXIS_HEGEMONY_EUROPE` | Germany holds 6 or more European regions including Britain or western USSR |
| `AXIS_HEGEMONY_ASIA` | Japan holds the Asian regions and the United States is at `commit ≤ wary` |
| `ALLIED_VICTORY` | the realized ending: Germany and Japan hold no regions beyond their 1933 borders and are at `force = low` |
| `STALEMATE` | fronts static for 8 ticks with no negotiation |

## 5. Pre-registered tests

Each test becomes a file under `tests/ww2/scenarios/` at milestone M1. "Expected" is what the engine must output for the test to pass; where the historiography is split, the required output is `contested`, which means neither side can force the result. Any later edit to this table is logged in section 11 with a rationale.

| Id | From state | Claim | Expected engine output | Sources |
|---|---|---|---|---|
| T1 | 1936Q1 snapshot | the realized trajectory to 1940Q2 (Rhineland, Anschluss, Munich, Prague, Pact, Poland, the fall of France) is reachable | reachable with zero relaxations | ICB; Weinberg; Kershaw |
| T2 | 1936Q1, after the German entry | if France plays `resist`, German `withdraw` is available and the state after the entry stays inside V_WEST; from the tick-0 state a hegemonic Germany that delays its entry until its army is ready keeps the state outside V_WEST (recorded result) | the tick-1 state (after the realized entry) ∈ V_WEST under the `resist` branch for both hypotheses, with `resist` then `withdraw` available; the tick-0 state ∉ V_WEST under hegemonic aims | Kershaw; Tooze; amended 2026-10-12 |
| T3 | 1938Q3 | Munich refused leads to war in 1938 | `war[GER][WEST]` reachable within 2 ticks; the ending is `contested`, not forced for either side | Weinberg; Murray and Millett; the opposing readings of German readiness |
| T4 | 1939Q1 | Prague flips `belief[UK][GER]` to hegemonic, which enables `guarantee(Poland)` | the shortest trace to `guarantee(Poland)` passes through the belief flip; without the flip the action is unavailable | Cabinet papers CAB 23; Hansard, March 1939 |
| T5 | 1940Q2 | `negotiate` is available to the United Kingdom and `NEGOTIATED_PEACE` is reachable; under `fight_on`, Germany cannot force `AXIS_HEGEMONY_EUROPE` | `⟨⟨GER⟩⟩◇AXIS_HEGEMONY_EUROPE` is false in the 1940Q2 state with `fight_on` | Lukacs 1999; Overy 1995 |
| T6 | 1941Q2 | Germany cannot force control of western USSR plus the Caucasus; the quarter at which V_GER is left falls between 1941Q3 and 1943Q1 (the decision of June 1941 counts as inside the window: in v1 the attack itself is the point of no return, because a German exit from the eastern war needed a Soviet decision for which the record has no document, docs/german_exit_1941_1945.md) | `contested` in the fortune sense for the 1941 campaign (section 4.6); point of no return inside the window, with the driving variable named | Tooze; Overy; Kershaw; amended 2026-10-15 |
| T7 | 1941Q3 | under the embargo Japan can force war with the United States from 1941Q4 to 1943Q3 and loses the option at 1943Q4 unless the embargo is lifted, under regional and hegemonic aims; under status-quo aims it never has it (the embargo closes Japan's window, it compels nothing: Japan's "Option 1" of 1 Nov 1941 stays in the decision space) | ⟨⟨JPN⟩⟩◇`war[JPN][USA]` holds at each tick from 23 to 30 and fails from tick 31 under `embargo_maintained`, the closing driven by `oil_JPN` through the oil clock; under `status_quo` it never holds; `strike_north` reachable only with the GER-JPN pact and western USSR collapsing, as a guard check (every witness has both at the strike) | Ike 1967; Sagan 1988; Iriye 1987; Kershaw; amended 2026-10-15 |
| T8 | 1936Q1 | (a) concessions reach `NO_GENERAL_WAR` under `aims[GER] = revisionist` and the tick-0 state is in V_WEST; (b) under `aims[GER] = hegemonic` with the Czech obligation in force, refusing the Sudeten demand leads to war within one tick and `czech_obligation` is the only minimal relaxation that lets a refusal stay at peace (the lever is measurable); the kernel question reduces to T13: under hegemonic aims V_WEST for `balance_europe` is left at 1936Q2, before Munich, so the concession changes nothing in kernel terms (recorded, symbolic engine; the one "inside" after-Munich state of reports/ww2_v0.md section 14 was a snapshot whose readiness reading lagged the model's clock by a quarter) | (a) as stated; (b) the obligation result is the load-bearing result and the historical calibration of the AGI model's rights lever; the kernel result as recorded | Taylor 1961 against Weinberg 1994 and Kershaw; amended 2026-10-12 and 2026-10-15 |
| T9 | 1939Q2 | a UK, France, USSR alliance can block the attack on Poland only if `belief[GER][UK]` is that Britain will fight | interim, at quarterly resolution: from the 1939Q2 state with the alliance counterfactually concluded, {WEST, USSR} keeps Poland independent through 1940Q4 under `deterred` iff the belief is `will_fight`, and the attack is forced otherwise (recorded: at quarterly resolution the alliance of summer 1939 cannot form before the attack, so the registered race is invisible); the registered question is re-asked at 3-day resolution in the summer-1939 crisis sub-game (docs/crisis_1939_testbed.md), where the alliance race and the attack are decided | the 1939 Anglo-Soviet talks; Weinberg; amended 2026-10-15 |
| T10 | various | negative controls: Japan conquers the USSR needs at least one relaxation and every minimal set relaxes `campaign_siberia:japanese_superiority`, a constraint the record never lifts; Britain alone defeats Germany by 1941 (`GERMAN_DEFEAT` from the end of 1940Q3) needs at least two relaxations and every minimal set relaxes `german_army_unready`; Germany conquers the United States is vacuous in v0 and is re-registered for v1 if the Atlantic is modeled | as stated. The USSR joining the Axis against Britain is *not* absurd (the November 1940 Berlin talks) and must need exactly one relaxation of the Soviet hypothesis (`ussr_defensive` or the `join_axis` gate) | Weinberg; Kershaw; amended 2026-10-12 |
| T11 | 1941Q1 | without an attack on the United States, `commit[USA] = total` is unreachable before 1943 under the `electoral` profile; with Nature's `attack_on_us` it is immediate | as stated | Gallup series; Kershaw |
| T12 | 1945Q2 | the atomic event ends the war regardless of `aims[JPN]`, and only for a program started at least 12 ticks earlier | as stated; this is the one capability-discontinuity test | Frank 1999 |
| T13 | each quarter 1936Q1 to 1939Q3 | the quarter whose decisions leave V_WEST for `balance_europe` (the last quarter at which the realized state is inside the kernel, followed by a state outside it) falls inside the window, and the report names the driving variable | departure inside 1936Q1 to 1939Q3; stable within 2 quarters under refinement; recorded (symbolic engine, v0): 1936Q2 under hegemonic aims (the quarter in which the Rhineland was not resisted) and 1939Q3 under revisionist aims (the attack on Poland); the registered predicate `NO_GENERAL_WAR`, which forbids the West's own war, gave an empty kernel from 1936Q1 under hegemonic aims and is retired for this test | the Rhineland, Munich and Prague readings; amended 2026-10-15 |

The success criterion for T13 is not to match one historian's date. It is to produce a defensible assignment with a trace and a minimal assumption set that can be argued with.

## 6. Data and documents

### 6.1 Datasets for hindsight snapshots

| Source | Gives | Feeds |
|---|---|---|
| Correlates of War, National Material Capabilities v7.0 (1816 to 2022) | annual `irst`, `pec`, `milex`, `milper`, `tpop`, `upop`, `cinc` per state | `ind`, `mob`; interpolated to quarters and flagged as interpolated |
| International Crisis Behavior v16 (1918 to 2021) | crises with triggers, actors, outcomes, dates | the realized trajectory; `war` states; dated branch points |
| Correlates of War, Militarized Interstate Disputes | disputes below war | `war = cold` states |
| Harrison 1998, *The Economics of World War II* | GDP and munitions by power, 1938 to 1945 | `ind`, `force` |
| Maddison Project Database | GDP | `ind` cross-check |
| US Bureau of Mines, *Minerals Yearbook* (annual, contemporaneous) | oil production and trade | `oil` |
| Tooze 2006; US Strategic Bombing Survey oil reports | German synthetic fuel; Japanese stocks | `oil` |
| Gallup (from 1935); conscription and parliamentary records | opinion, commitment | `commit` |

### 6.2 Dated documents for the replay harness

Only sources with a document date are admissible for replay, and only documents dated at or before the replay quarter are shown to the extractor.

- Foreign Relations of the United States (history.state.gov): dated US diplomatic documents.
- Historic Hansard: dated UK parliamentary debates.
- Chronicling America (Library of Congress): US newspapers to 1963. Trove (National Library of Australia): Empire press.
- Documents on German Foreign Policy; the Nuremberg document collections (Avalon Project). Assembled after the war, but each document carries its original date, which is the date used.
- The 1941 Imperial Conference records in Ike's 1967 translation.
- British Cabinet minutes and memoranda (CAB 23, CAB 65, CAB 66), where digitized.

Excluded from replay: encyclopedias and later histories. They are used for decision spaces and expected results (section 6.3) and logged as such.

### 6.3 Historiography for decision spaces and expected results

Kershaw, *Fateful Choices* (2007); Tooze, *The Wages of Destruction* (2006); Overy, *Why the Allies Won* (1995); Weinberg, *A World at Arms* (1994); Taylor, *The Origins of the Second World War* (1961); Copeland, *The Origins of Major War* (2000); Kennedy, *The Rise and Fall of the Great Powers* (1987); Sagan, "The Origins of the Pacific War" (1988); Iriye, *The Origins of the Second World War in Asia and the Pacific* (1987); Hinsley, *British Intelligence in the Second World War*, abridged (1993); Murray and Millett, *A War to Be Won* (2000); Organski and Kugler, *The War Ledger* (1980); Lukacs, *Five Days in London, May 1940* (1999); Frank, *Downfall* (1999).

## 7. Anti-hindsight protocol

The risk with a known outcome is building a model that reproduces it because we tuned it to. Rules:

1. **Tests before guards.** Section 5 is committed before any guard is written. Edits to it afterwards go in the changelog (section 11) with a rationale.
2. **Decision spaces from contemporaneous alternatives.** Actions come from what was debated at the time, cited in the model source. Anything else is tagged `speculative` and reported separately.
3. **Hold-out.** Develop on Europe 1936 to 1940. Test on the Pacific 1940 to 1942 and on outcomes 1941 to 1945. No guard edit after seeing hold-out results without a logged rationale and a rerun of the whole suite.
4. **Parameter budget.** Every report states the number of guards, thresholds and speculative actions. Adding parameters must not lower the informativeness metric (section 9).
5. **Blind replay.** The document pipeline filters strictly by document date.
6. **Negative controls in CI.** T10 runs on every change.
7. **One trajectory is one sample.** WW2 is the development set. The Cold War ([coldwar_testbed.md](coldwar_testbed.md)) is the validation set, with its claims registered now and a logged budget on framework changes. The July 1914 crisis is held in reserve as a one-shot final test.

## 8. Replay harness for the evidence pipeline

For each quarter T in the range:

1. `corpus(T)` = admissible documents dated at or before T.
2. The extractor (an LLM against a fixed schema, as in DESIGN.md section 5.3) proposes levels for the variables that come from text: `commit`, `belief`, `treaty`, `pacts`, `war`, and `oil` where the datasets are silent. Resource variables come from the datasets.
3. `snapshot_replay(T)` is compared with `snapshot_hindsight(T)`: per-variable agreement; the lag between a replayed belief flip and the documented one; false flips.
4. The full analysis runs from `snapshot_replay(T)` and the inclination report is compared with the pre-registered expectation for T (for example: in 1938Q4 the state is outside V_WEST unless the USSR is counted; in 1941Q3 Japan's `oil` trajectory makes `war[JPN][USA]` unavoidable within 8 ticks). This checks that the estimate and the drift land in the right region. It is not a prediction score.

## 9. Metrics

- Pre-registered tests: pass or fail, with traces attached.
- Contested-region correctness: for T3 and T6 the engine returns `contested` in the sense of section 4.6, not a forced result; T9's standard region is decided in the crisis sub-game.
- Point-of-no-return windows: T6 and T13 inside their windows; stable within 2 quarters under level refinement.
- Informativeness: at least 80 percent of negative controls need 3 or more relaxations.
- Replay agreement: resource variables at least 80 percent exact at the level; belief flips within one quarter of the documented dates.
- Parameter budget trend, reported with every result.

## 10. Porting to the AGI model

The AGI model is a second instance of the same DSL, engine, analysis and snapshot pipeline, under `models/agi/`. Mechanisms the WW2 suite exercised are marked `validated:ww2` in the AGI model source; the rest are marked `untested` and listed in every AGI report. Results that hold in both models with the same structure become the framework's first structural findings with a historical anchor. The expected candidates are: concessions remove the motive for conflict only under limited aims; preventive defection follows a credible threat when no continuity guarantee exists; a change in belief precedes a response by an institutional lag, and the lag is where the point of no return hides.

## 11. Changelog of pre-registered tests

- 2026-10-11: T1 to T13 registered. No guards written yet.
- 2026-10-12: clarification for phase 2, no change of claim: v1 starts at 1936Q1 and runs to 1945Q3 (horizon 39); the 1933 to 1935 prelude is dropped because no registered claim depends on it (docs/phase2_kickoff.md D1).
- 2026-10-12: T2, T8 and T10 amended on the owner's decision after the phase 1 results (the previous wording is in git history and in reports/ww2_v0.md sections 4, 7 and 8): T2 is registered in its conditional form plus the recorded tick-0 result; T8(b) becomes the load-bearing-obligation result with the kernel comparison deferred to phase 2; T10's Japan and Britain-alone controls become content controls on the relaxed constraint, the United States control is vacuous in v0. The China incident stays a Nature event that Nature may decline (owner's decision).
- 2026-10-12: phase 1 results recorded under the original wording: T1, T4 and T5 met; T2 and T8 met under revisionist aims and not met under hegemonic aims as registered (T2: a hegemonic Germany that delays its entry until its army is ready; T8(b): the snapshot comparison measured the rearmament clock, not the concession); T10: the USSR control met, the Japan and Britain-alone controls need 1 and 2 relaxations rather than 3 or more, the United States control is vacuous. Proposed amendments are in reports/ww2_v0.md section 10 for the owner's decision.
- 2026-10-12: clarification, no change of claim: T1's "realized trajectory" is the quarter-by-quarter decision sequence in `data/ww2/realized_moves.csv`; at quarterly granularity a reaction to another actor's same-quarter decision appears one tick later (marked [SQR] there). T10's "relaxations" count named assumptions including named guard parts (framework_spec.md section 3.1); a control whose ending has no variable or action in the model is reported as vacuous, not as a pass.
- 2026-10-16: T9 re-asked at 3-day resolution in the summer-1939 crisis sub-game (docs/crisis_1939_testbed.md, K2; reports/crisis_1939.md section 10): with Polish passage granted and `belief_GER` at `will_fight`, {WEST, USSR} is the only minimal coalition that blocks the attack on Poland and the only one that can conclude the alliance before the pact; below `will_fight` nothing blocks; with passage refused no documented coalition blocks. The registered conditional holds at the resolution at which it was decided, on the behavioural profile `deterred`; "otherwise contested" does not hold (Germany forces the attack), except in the fortune sense with Nature's passage decision free. The quarterly interim reading of 2026-10-15 stands as recorded. No claim is edited here.
- 2026-10-15: T6, T7, T9, T13 and T8(b) amended on the owner's decisions after the phase 2 results (the previous wording is in git history and in reports/ww2_v1.md sections 5 to 11): T6's window starts at 1941Q3 and its "contested" is read in the fortune sense (section 4.6, new), computed under `fight_on` (the West's 1940 decision, T5) because without it a British negotiated peace in 1941Q2, open until the attack sets the alliance, pre-empts the campaign; T7 is restated as Japan's option under the oil clock, its minimal-set expectation replaced by the option's window; T9 keeps its claim with an interim quarterly reading from a state with the alliance concluded, and is re-asked at 3-day resolution in the summer-1939 crisis sub-game (docs/crisis_1939_testbed.md); T13 reads V as WEST's kernel for `balance_europe` with the departure as the quarter whose decisions leave it; T8(b)'s kernel comparison is replaced by the T13 result. Conventions settled the same day (decision 7): hindsight start states follow the model's own clock where the record lags it by one tick (a landed delayed decision; an effect of a realized move), with the disagreement kept in the snapshot's provenance; and (decision 1) a German offer of terms in the East enters the decision space as a documented, refused alternative, with Soviet acceptance speculative (docs/german_exit_1941_1945.md), logged in the guard changelog as an edit after first sight with its sources and a full rerun.
- 2026-10-14: phase 2 results recorded under the registered wording and the readings of 2026-10-13: T3, T11 and T12 met; T10's Japan control met on v1; T6 not met (the standard contested region is blocked, not contested, when Nature may decline a campaign; the point of no return is 1941Q3, one quarter before the window); T7 not met (war is avoidable under the embargo, Japan's documented Option 1; the clock closes the option at 1943Q4; the second half holds by the guard); T9 not met (the attack is forced from 1939Q2 before an alliance can exist); T13 met degenerately (V empty along the path under hegemonic aims from 1936Q1; with WEST's kernel for `balance_europe` the departure is 1936Q2 under hegemonic and 1939Q3 under revisionist aims); T8(b)'s deferred kernel comparison not met (the West is outside its kernel before Munich). Proposed amendments are in reports/ww2_v1.md section 13 and reports/ww2_v0.md section 14.1 for the owner's decision; no claim is edited here.
- 2026-10-13: clarifications for the v1 runs, no change of claim (docs/ww2_v1_decisions.md E1 to E5, written before any v1 test was run): "from state Q" is the state at the start of Q with its built-ins loaded; v1's Nature plays one event per tick, so two Nature outcomes dated in one quarter cannot both sit in it ([NSL]); the ending definitions of section 4.6 are read for v1 as docs/ontology_ww2_v1.md section 6 defines them (`AXIS_HEGEMONY_EUROPE` needs Britain invaded or both eastern regions, `AXIS_HEGEMONY_ASIA` reads the Pacific war, the horizon endings are redefined at tick 39 and `STATIC_FRONT` and `BRITAIN_ALONE` are retired), v0 unchanged; "contested" is the framework's contested region, which is trivially satisfied wherever Nature may decline a campaign resolution, so every such result is reported with the fortune variant (the coalition joined by Nature) as well; T3: W_GER is `AXIS_HEGEMONY_EUROPE ∨ NEGOTIATED_PEACE`, W_WEST is `GERMAN_DEFEAT ∨ reich == surrendered`, and the war state is the first war state of the shortest refusal witness; T6: "control of western USSR plus the Caucasus" is `w_ussr == german ∧ caucasus == german`, V_GER is GER's kernel for `reich == fighting ∧ ¬german_defeat`, and "the quarter at which V_GER is left" is the point of no return along the realized path; T7: `war[JPN][USA]` is `pacific_war >= war`, WEST's move at tick 22 is the realized `embargo_jpn`, "within 8 ticks" is a tick at most 30, "unavoidable" is the unreachability of peace at tick 30 under the profile and the hypothesis, the "minimal assumption set" is the minimal hitting set of the minimal relaxation sets, and the GER-JPN pact is `anticomintern`; T9: {UK, FR, USSR} is {WEST, USSR}, "block" is keeping `poland == independent` through tick 20, and the belief condition enters as the named behavioural profile `deterred` with the start-state belief swept; T11: "an attack on the United States" is JPN `attack_south` (there is no Nature event in the record), "before 1943" is a tick below 28, and "immediate" is the tick after the decision; T12: "ends the war" is `pacific_war := surrendered` by Nature's `atomic`, and "started" is the tick of the `atomic_program` decision; T13: V is WEST's kernel for `war_west_ger == peace ∧ poland == independent` on v0 (the registered run) and for the European predicate `peace_europe ∧ poland == independent` on v1, both through tick 20, the v0-to-v1 comparison being the claim's refinement clause; T10 on v1: the Japan control is a content control under `aims_JPN = hegemonic`, the United States control stays vacuous.
- 2026-10-11: clarification, no change of claim: "assumption sets" in T7 and "relaxations" in T10 range over named assumptions (guards, fairness constraints, profiles, and named initial-state restrictions declared with `assume`), per framework_spec.md section 3.1; "embargo maintained" in T7 is a profile forbidding `lift_embargo`.

---

## References

- Correlates of War, National Material Capabilities v7.0: https://correlatesofwar.org/data-sets/national-material-capabilities (Singer, Bremer and Stuckey 1972; Singer 1988)
- International Crisis Behavior Project, version 16: https://sites.duke.edu/icbdata/ (Brecher and Wilkenfeld, *A Study of Crisis*, 1997)
- Harrison, M. (ed.), *The Economics of World War II: Six Great Powers in International Comparison*, 1998.
- Kershaw, I., *Fateful Choices: Ten Decisions That Changed the World, 1940–1941*, 2007.
- Tooze, A., *The Wages of Destruction: The Making and Breaking of the Nazi Economy*, 2006.
- Overy, R., *Why the Allies Won*, 1995.
- Weinberg, G., *A World at Arms*, 1994.
- Taylor, A. J. P., *The Origins of the Second World War*, 1961.
- Copeland, D., *The Origins of Major War*, 2000.
- Kennedy, P., *The Rise and Fall of the Great Powers*, 1987.
- Sagan, S. D., "The Origins of the Pacific War", *Journal of Interdisciplinary History* 18(4), 1988.
- Iriye, A., *The Origins of the Second World War in Asia and the Pacific*, 1987.
- Ike, N. (ed.), *Japan's Decision for War: Records of the 1941 Policy Conferences*, 1967.
- Hinsley, F. H., *British Intelligence in the Second World War*, abridged edition, 1993.
- Lukacs, J., *Five Days in London, May 1940*, 1999.
- Frank, R., *Downfall: The End of the Imperial Japanese Empire*, 1999.
- Murray, W. and Millett, A., *A War to Be Won*, 2000.
- Organski, A. F. K. and Kugler, J., *The War Ledger*, 1980.
- Foreign Relations of the United States: https://history.state.gov/historicaldocuments
- Historic Hansard: https://api.parliament.uk/historic-hansard/
- Chronicling America: https://chroniclingamerica.loc.gov/
