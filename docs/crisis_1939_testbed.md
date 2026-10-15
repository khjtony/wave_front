# The summer-1939 crisis sub-game: registered claims (3-day ticks, 5 July to 3 September 1939)

Status: claims registered 2026-10-15 by the architect on the owner's decisions 4 and 10 of 2026-10-15, **before any guard, action, variable or data row of the sub-game is written**. The same protocol as ww2_testbed.md section 7 applies: a later edit to this table goes in the changelog (section 7) with a rationale; guards come from contemporaneous alternatives with dated sources; guard edits after a failing test are logged in docs/guard_changelog_ww2.md; the claims are run once, in one go, and the commit of first sight is recorded.

## 0. Why this sub-game

T9 asks whether an Anglo-French-Soviet alliance could have blocked the attack on Poland, and under what belief in Berlin. At quarterly resolution the question is invisible: the alliance needs two quarters to form and the attack one, so Germany attacks first by construction (reports/ww2_v1.md section 7). The record's race ran in weeks: the Moscow political talks of June and July, the military missions of 12 to 21 August, the German approach to Moscow of 26 July to 23 August, the attack order of 25 August and its cancellation, the attack of 1 September. This sub-game asks T9's question at the resolution at which it was decided, using the crisis machinery of framework_spec.md section 14: it is entered from WW2 v1's state at the start of 1939Q3 (tick 14) and returns a 1939Q4 state.

## 1. Scope and time

- One tick is three days. Tick 0 is 5 July 1939; tick 20 is 3 September 1939 (the British and French declarations), the horizon. Sixty days, twenty ticks.
- Entry: v1's state at the start of 1939Q3 (`1939Q2.json` with its built-ins, under `aims_GER = hegemonic`): the army `high`, Bohemia German, the Polish guarantee given, `belief_GER` `uncertain` (the conference of 23 May), no pact, no alliance, WEST's approach to Moscow standing (`last_WEST == approach_ussr` from 1939Q1 and the talks under way).
- Exit: the coarse variables the crisis can change: `poland` (independent or german), `war_west_ger`, `france`, `britain`, `commit_WEST`, `nazi_soviet_pact`, `anglo_soviet_alliance`, `belief_GER`, `oil_GER`.
- Actors: `GER`, `WEST`, `USSR` and `Nature` (the coarse actors the sub-game needs; `JPN` does not take part). Poland's and Italy's decisions are Nature's, as Italy's are in v1: Nature carries the Polish refusal of Soviet passage (Beck, 19 to 20 August) and Mussolini's letter of 25 August.
- Everything structural is frozen at the entry values (the coarse rule of spec section 14): armaments, regions, the China war. What moves is diplomacy, military conversations, orders and beliefs.

## 2. Variables the claims refer to (names fixed here; levels and thresholds come with the ontology)

| Variable | Meaning | Record |
|---|---|---|
| `talks` | the Anglo-French-Soviet negotiation: political, military, adjourned, broken | political talks to mid-July; military talks agreed 23 to 25 July; missions in Moscow 12 to 17 August; adjourned 17 August; broken off 21 August |
| `passage` | Polish consent to Soviet passage: refused, granted | Voroshilov's question of 14 August; Beck's refusal 19 to 20 August; Daladier's unauthorized assurance 21 August |
| `german_approach` | the German approach to Moscow: none, opened, pact_proposed, pact | Schnurre and Astakhov 26 July; Schulenburg's instructions 3 August; Molotov's reply 17 August; Hitler's telegram 20 August; Stalin's reply 21 August; the pact signed 23 to 24 August |
| `attack_order` | Case White: none, ordered, cancelled, launched | ordered 25 August for 26 August; cancelled the same evening; re-ordered 31 August; launched 1 September |
| `british_treaty` | the Anglo-Polish agreement of 25 August: guarantee only, treaty signed | signed 25 August |
| `belief_GER` | as v1: will_not_fight, uncertain, will_fight | the conference of 22 August ("our enemies are small worms"); Chamberlain's letter of 22 August; the shock of 25 August; the declarations of 3 September |
| `mobilization_POL` | none, partial, general | partial 23 August; general ordered 29 August, suspended, re-ordered 30 August |
| `italy_ready` | flag | Mussolini's letter of 25 August: Italy not ready |

The alliance exists when `talks` reach a concluded military convention with `passage` granted (the Soviet condition of 14 August), or by a Soviet decision to conclude without it (a documented alternative only if the historian finds a Soviet record; otherwise speculative). The pact exists when `german_approach == pact`.

## 3. Registered claims

"Expected" is what the engine must output. Where the record is split, the expected output is `contested` in the sense of ww2_testbed.md section 4.6. "Blocks the attack" means keeping `attack_order != launched` to the horizon (the sub-game's kernel question); "the alliance" means the alliance variable set before the pact.

| Id | From | Claim | Expected engine output | Sources |
|---|---|---|---|---|
| K1 | tick 0 | the realized sequence (military talks agreed, missions in Moscow, Voroshilov's question, the Polish refusal, the Soviet adjournment, the pact of 23 August, the attack order of 25 August and its cancellation, the re-order of 31 August, the attack of 1 September, the declarations of 3 September) is reachable with zero relaxations, and the exit state equals v1's realized 1939Q4 state | reachable, zero relaxations; exit state matches | DBFP Third Series vols. VI and VII; DGFP Series D vol. VII; Halder's diary; Weinberg |
| K2 | tick 0 | re-asking T9: a UK, France, USSR alliance concluded before the pact blocks the attack on Poland only if `belief_GER` is `will_fight`; the coalition that can conclude it in time is {WEST, USSR} with Nature granting Polish passage, and Polish passage is pivotal (without it the alliance needs a Soviet decision the record does not show) | pivotal coalition {WEST, USSR} with the belief condition and the passage condition; without the belief condition, `contested` (the attack is not blocked, and Germany cannot force it before the pact under `deterred` while the alliance is possible) | the Moscow talks (DBFP vol. VII); Voroshilov's question of 14 August; Beck's refusal; the profile `deterred` as adopted for T9 |
| K3 | ticks 0 to 15 | the tick at which {WEST, USSR} leave the kernel for "no pact and the alliance still possible" falls between 14 August (Voroshilov's question, tick 13) and 21 August (the Soviet break-off, tick 15), and the driving variable is Polish passage or the pace of the talks | point of no return inside ticks 13 to 15, with the driving variable named | the military missions' record; the Schulenburg-Molotov exchanges of 15 to 19 August |
| K4 | tick 17 (25 August) | after the pact, no coalition blocks the attack under any belief: the Anglo-Polish treaty of 25 August and Chamberlain's letter of 22 August flip `belief_GER` to `will_fight` and the attack is cancelled for a documented reason (Italy's non-readiness and the treaty), but it is re-ordered and launched by 1 September whatever WEST does; the cancellation of 25 August delays the attack by at most two ticks | from the state of 25 August the attack is forced by Germany by tick 19 under every belief; the shortest trace shows the cancellation and the re-order | DGFP Series D vol. VII (the order of 25 August, 15:02; the cancellation; the order of 31 August); Halder's diary 25 to 31 August; Ciano's diary |
| K5 | tick 0 | negative control: an attack launched before 26 August (tick 17) needs at least one relaxation, and every minimal set relaxes Case White's readiness part (the date of 1 September fixed on 3 April, a constraint the record never lifts) | as stated | Case White directive of 3 April 1939 (C-120) |
| K6 | tick 0 | the Soviet choice is open to both sides until 19 August: from every state up to tick 14 both the pact and the alliance are reachable; under `aims_USSR = defensive` the pact needs Germany's proposal of a protocol (the German approach at `pact_proposed`), and without it the Soviet acceptance is unavailable | both targets reachable to tick 14; the pact's minimal assumption set names the German proposal | Molotov to Schulenburg, 17 and 19 August; Stalin's reply, 21 August |

Departures from v1's conventions, stated now: the sub-game has no hidden objective of its own (`aims_GER` hegemonic and `aims_USSR` defensive enter from the coarse state); `belief_GER` is read and raised by documented events at daily resolution (Chamberlain's letter, the treaty), not only by `declare_war`; Nature's one-event-per-tick rule applies, and at three-day ticks two Nature events in one tick are marked [NSL] as in v1.

## 4. Data and documents

- British Documents on Foreign Policy, Third Series, vols. VI and VII (the Moscow talks, the military missions, 22 to 31 August).
- Documents on German Foreign Policy, Series D, vols. VI and VII (the German approach to Moscow; the orders of 25 and 31 August; the Henderson exchanges).
- Halder's war diary (July to September 1939); Ciano's diary (August 1939).
- Nazi-Soviet Relations 1939-1941 (the State Department collection of the German documents on the pact).
- Weinberg, The Foreign Policy of Hitler's Germany: Starting World War II (1980); Watt, How War Came (1989), the chapters on the Moscow talks and the last week; Roberts, The Unholy Alliance (1989) for the Soviet side.
- The FRUS 1939 volumes (already fetched) for the replay harness at 3-day resolution, if the replay is run on the sub-game.

## 5. Protocol

As ww2_testbed.md section 7. The sub-game's catalogue (variables, actions with dated sources, Nature events, delays in ticks) is written from the record by the historian agent after this file is committed; the model step follows docs/ww2_v1_decisions.md E-style decisions written by the architect; the claims are run once, in one go, and the commit of first sight is recorded in the report. K2 is the hold-out claim of this sub-game.

## 6. Metrics

K1 pass; K2 and K3 as the method-reliability results (B3, B8, B10 in docs/validity.md); K5 informativeness; K4 and K6 as content checks. The result for T9 is K2's, reported in the T9 row of ww2_testbed.md section 5 as "re-asked in the crisis sub-game".

## 7. Changelog

- 2026-10-15: K1 to K6 registered. No guard written yet.
