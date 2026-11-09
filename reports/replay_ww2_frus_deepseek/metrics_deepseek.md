PROPOSAL-LEVEL MEASUREMENT: no proposal below was reviewed. Every proposal the backend made was treated as if accepted to compute these metrics, no replay snapshot was written, and the levels and quotes below are the backend's unreviewed readings, not evidence accepted by a reviewer.

# Replay metrics, FRUS 1936 to 1940, DeepSeek flash with guidance g2, proposal level

- Quarters: 1936Q1 to 1940Q4 (20); snapshot compared at each quarter's last day.
- Corpus: frus, `data/ww2/corpora/raw/frus`
- Backend: deepseek, model `deepseek-flash`
- Harness rules in force: `two-document`, `no-retrospective` ([docs/replay_harness.md](../docs/replay_harness.md), section "Harness rules")
- Review: none: proposal-level measurement (every proposal treated as accepted, nothing written)
- Command: `wf replay --quarters 1936Q1..1940Q4 --out OUT --measure-proposals`
- Target: the hindsight snapshots in `snapshots/ww2/hindsight/` (levels at each quarter's end, read with full knowledge of the record).

## Proposals per variable

Every proposal kept by the extractor's checks over the quarters, by level.

| Variable | Proposals | By level |
|---|---|---|
| `belief_WEST` | 241 | limited 125, uncertain 77, hegemonic 39 |
| `belief_GER` | 28 | uncertain 11, will_not_fight 11, will_fight 6 |
| `commit_WEST` | 356 | appease 138, resolved 101, at_war 97, wary 20 |
| `commit_US` | 234 | isolationist 164, wary 47, engaged 23 |
| `treaty` | 25 | dead 16, eroded 9 |
| `axis` | 140 | true 139, false 1 |
| `anticomintern` | 31 | true 31 |
| `nazi_soviet_pact` | 82 | true 81, false 1 |
| `polish_guarantee` | 45 | true 45 |
| `anglo_soviet_alliance` | 18 | false 18 |
| `ussr_axis` | 2 | false 2 |
| `italy_estranged` | 209 | true 205, false 4 |
| `china_war` | 46 | true 46 |
| `war_west_ger` | 197 | war 193, peace 4 |
| `rhineland` | 62 | remilitarized 62 |
| `austria` | 67 | annexed 65, independent 2 |
| `sudeten` | 30 | german 23, czech 7 |
| `bohemia` | 46 | german 46 |
| `poland` | 138 | partitioned 76, german 59, independent 3 |
| `france` | 282 | at_war 170, fallen 105, independent 7 |
| `britain` | 303 | at_war 300, at_peace 3 |
| `balkans` | 25 | german_aligned 13, neutral 12 |
| `siberia` | 1 | soviet 1 |
| `channel_air` | 7 | contested 5, british 2 |
| `oil_GER` | 45 | secured 44, dependent 1 |
| all | 2660 | |

## What the harness rules did

Every proposal of the quarters, classified at the last quarter's end under `two-document`, `no-retrospective`. Only the first column is counted by the metrics; a flip of a variable under the two-document rule is counted at, and dated by, the proposal of its second document (the first is listed under "First of two documents").

| Variable | Proposals | Shown and counted | Held: one document | First of two documents | Blocked: monotone, back | retrospective? (not counted) |
|---|---|---|---|---|---|---|
| `belief_WEST` | 241 | 241 | 0 | 0 | 0 | 0 |
| `belief_GER` | 28 | 28 | 0 | 0 | 0 | 0 |
| `commit_WEST` | 356 | 356 | 0 | 0 | 0 | 0 |
| `commit_US` | 234 | 234 | 0 | 0 | 0 | 0 |
| `treaty` | 25 | 20 | 0 | 0 | 0 | 5 |
| `axis` | 140 | 139 | 0 | 1 | 0 | 0 |
| `anticomintern` | 31 | 30 | 0 | 1 | 0 | 0 |
| `nazi_soviet_pact` | 82 | 80 | 0 | 1 | 1 | 0 |
| `polish_guarantee` | 45 | 44 | 0 | 1 | 0 | 0 |
| `anglo_soviet_alliance` | 18 | 18 | 0 | 0 | 0 | 0 |
| `ussr_axis` | 2 | 2 | 0 | 0 | 0 | 0 |
| `italy_estranged` | 209 | 107 | 0 | 1 | 0 | 101 |
| `china_war` | 46 | 45 | 0 | 1 | 0 | 0 |
| `war_west_ger` | 197 | 196 | 0 | 1 | 0 | 0 |
| `rhineland` | 62 | 62 | 0 | 0 | 0 | 0 |
| `austria` | 67 | 66 | 0 | 1 | 0 | 0 |
| `sudeten` | 30 | 29 | 0 | 1 | 0 | 0 |
| `bohemia` | 46 | 45 | 0 | 1 | 0 | 0 |
| `poland` | 138 | 120 | 0 | 2 | 16 | 0 |
| `france` | 282 | 279 | 0 | 2 | 1 | 0 |
| `britain` | 303 | 302 | 0 | 1 | 0 | 0 |
| `balkans` | 25 | 21 | 0 | 1 | 3 | 0 |
| `siberia` | 1 | 1 | 0 | 0 | 0 | 0 |
| `channel_air` | 7 | 6 | 0 | 1 | 0 | 0 |
| `oil_GER` | 45 | 43 | 0 | 1 | 1 | 0 |
| all | 2660 | 2514 | 0 | 18 | 22 | 106 |

## Summary against section 9

- Text-derived variables, exact level agreement over variable-quarters: 465/500 (93%).
- For scale: a replay that reads nothing (every text variable at its initial level) agrees on 304/500 (61%). Split by the hindsight level: where it is still the initial one, this replay agrees on 281/304 (92%); where it has moved, on 184/196 (94%).
- Resource variables: 100/100 (100%), but they are copied from the hindsight snapshots (they come from the datasets), so this checks the copy, not a reading; the section 9 target of 80 percent for resource variables is not tested by a replay of documents.
- Belief and commitment flips: 7 of 9 documented flips replayed within one quarter (8 matched within 4 quarters).
- False flips (replayed, no documented flip to the same level within 4 quarters): 9. Missed flips: 1.

## Agreement per variable

| Group | Variable | Agreement | Reading nothing | Quarters that disagree (hindsight / replay) |
|---|---|---|---|---|
| beliefs and commitment | `belief_WEST` | 16/20 (80%) | 9/20 (45%) | 1938Q3 (uncertain / limited), 1938Q4 (uncertain / limited), 1939Q1 (hegemonic / uncertain), 1940Q3 (hegemonic / limited) |
| beliefs and commitment | `belief_GER` | 9/20 (45%) | 13/20 (65%) | 1936Q2 (will_not_fight / uncertain), 1936Q3 (will_not_fight / uncertain), 1936Q4 (will_not_fight / uncertain), 1937Q1 (will_not_fight / uncertain), 1937Q2 (will_not_fight / uncertain), 1937Q3 (will_not_fight / uncertain), 1937Q4 (will_not_fight / uncertain), 1938Q2 (will_not_fight / will_fight), 1939Q2 (uncertain / will_not_fight), 1939Q3 (will_fight / uncertain), 1939Q4 (will_fight / uncertain) |
| beliefs and commitment | `commit_WEST` | 18/20 (90%) | 10/20 (50%) | 1938Q3 (wary / appease), 1938Q4 (wary / appease) |
| beliefs and commitment | `commit_US` | 20/20 (100%) | 15/20 (75%) | - |
| treaty | `treaty` | 20/20 (100%) | 0/20 (0%) | - |
| pacts and structural flags | `axis` | 20/20 (100%) | 3/20 (15%) | - |
| pacts and structural flags | `anticomintern` | 20/20 (100%) | 3/20 (15%) | - |
| pacts and structural flags | `nazi_soviet_pact` | 20/20 (100%) | 14/20 (70%) | - |
| pacts and structural flags | `polish_guarantee` | 19/20 (95%) | 12/20 (60%) | 1939Q1 (true / false) |
| pacts and structural flags | `anglo_soviet_alliance` | 20/20 (100%) | 20/20 (100%) | - |
| pacts and structural flags | `ussr_axis` | 20/20 (100%) | 20/20 (100%) | - |
| pacts and structural flags | `italy_estranged` | 8/20 (40%) | 20/20 (100%) | 1938Q1 (true / false), 1938Q2 (true / false), 1938Q3 (true / false), 1938Q4 (true / false), 1939Q1 (true / false), 1939Q2 (true / false), 1939Q3 (true / false), 1939Q4 (true / false), 1940Q1 (true / false), 1940Q2 (true / false), 1940Q3 (true / false), 1940Q4 (true / false) |
| pacts and structural flags | `china_war` | 20/20 (100%) | 6/20 (30%) | - |
| war | `war_west_ger` | 20/20 (100%) | 14/20 (70%) | - |
| regions | `rhineland` | 20/20 (100%) | 0/20 (0%) | - |
| regions | `austria` | 20/20 (100%) | 8/20 (40%) | - |
| regions | `sudeten` | 19/20 (95%) | 10/20 (50%) | 1938Q3 (german / czech) |
| regions | `bohemia` | 20/20 (100%) | 12/20 (60%) | - |
| regions | `poland` | 20/20 (100%) | 14/20 (70%) | - |
| regions | `france` | 20/20 (100%) | 14/20 (70%) | - |
| regions | `britain` | 20/20 (100%) | 14/20 (70%) | - |
| regions | `balkans` | 19/20 (95%) | 18/20 (90%) | 1940Q3 (german_aligned / neutral) |
| regions | `siberia` | 20/20 (100%) | 20/20 (100%) | - |
| regions | `channel_air` | 20/20 (100%) | 19/20 (95%) | - |
| oil | `oil_GER` | 17/20 (85%) | 16/20 (80%) | 1939Q2 (dependent / secured), 1939Q3 (dependent / secured), 1939Q4 (dependent / secured) |
| resources (copied) | `arms_GER` | 20/20 (100%) | - | - |
| resources (copied) | `arms_WEST` | 20/20 (100%) | - | - |
| resources (copied) | `arms_USSR` | 20/20 (100%) | - | - |
| resources (copied) | `arms_JPN` | 20/20 (100%) | - | - |
| resources (copied) | `ind_GER` | 20/20 (100%) | - | - |

## Flips: lag against the documented date

A documented flip is a change of level between consecutive hindsight snapshots, dated by the event that set the new level; a replayed flip is the same in the replay snapshots, dated by the proposal (treated as accepted) that set it. Lag is replay minus documented (positive: the replay is late).

| Variable | Level | Documented (quarter, date) | Replayed (quarter, date) | Lag (quarters) | Lag (days) |
|---|---|---|---|---|---|
| `belief_WEST` | uncertain | 1938Q2, 1938-06-30 | 1938Q2, 1938-06-22 | +0 | -8 |
| `belief_WEST` | hegemonic | 1939Q1, 1939-03-17 | 1939Q2, 1939-06-28 | +1 | +103 |
| `belief_WEST` | limited | none (false flip) | 1938Q3, 1938-09-28 | - | - |
| `belief_WEST` | uncertain | none (false flip) | 1939Q1, 1939-03-18 | - | - |
| `belief_WEST` | limited | none (false flip) | 1940Q3, 1940-07-29 | - | - |
| `belief_WEST` | hegemonic | none (false flip) | 1940Q4, 1940-12-28 | - | - |
| `belief_GER` | uncertain | 1939Q2, 1939-05-23 | 1939Q3, 1939-08-26 | +1 | +95 |
| `belief_GER` | will_fight | 1939Q3, 1939-09-03 | 1940Q1, 1940-02-26 | +2 | +176 |
| `belief_GER` | uncertain | none (false flip) | 1936Q2, 1936-05-18 | - | - |
| `belief_GER` | will_not_fight | none (false flip) | 1938Q1, 1938-02-17 | - | - |
| `belief_GER` | will_fight | none (false flip) | 1938Q2, 1938-05-22 | - | - |
| `belief_GER` | will_not_fight | none (false flip) | 1938Q3, 1938-08-30 | - | - |
| `commit_WEST` | wary | 1938Q3, 1938-09-30 | none (missed) | - | - |
| `commit_WEST` | resolved | 1939Q1, 1939-03-31 | 1939Q1, 1939-03-31 | +0 | +0 |
| `commit_WEST` | at_war | 1939Q3, 1939-09-03 | 1939Q3, 1939-09-03 | +0 | +0 |
| `commit_US` | wary | 1939Q4, 1939-11-04 | 1939Q4, 1939-11-10 | +0 | +6 |
| `commit_US` | engaged | 1940Q3, 1940-09-02 | 1940Q3, 1940-09-25 | +0 | +23 |
| `treaty` | dead | 1936Q1, 1936-03-07 | 1936Q1, 1936-03-07 | +0 | +0 |
| `axis` | true | 1936Q4, 1936-10-23 | 1936Q4, 1936-11-09 | +0 | +17 |
| `anticomintern` | true | 1936Q4, 1936-11-25 | 1936Q4, 1936-11-25 | +0 | +0 |
| `nazi_soviet_pact` | true | 1939Q3, 1939-08-23 | 1939Q3, 1939-08-23 | +0 | +0 |
| `polish_guarantee` | true | 1939Q1, 1939-03-31 | 1939Q2, 1939-03-31 | +1 | +0 |
| `italy_estranged` | false | none (false flip) | 1938Q1, 1938-02-17 | - | - |
| `china_war` | true | 1937Q3, 1937-07-07 | 1937Q3, 1937-08-11 | +0 | +35 |
| `war_west_ger` | war | 1939Q3, 1939-09-03 | 1939Q3, 1939-09-03 | +0 | +0 |
| `rhineland` | remilitarized | 1936Q1, 1936-03-07 | 1936Q1, 1936-03-07 | +0 | +0 |
| `austria` | annexed | 1938Q1, 1938-03-12 | 1938Q1, 1938-03-12 | +0 | +0 |
| `sudeten` | german | 1938Q3, 1938-09-30 | 1938Q4, 1938-10-03 | +1 | +3 |
| `bohemia` | german | 1939Q1, 1939-03-15 | 1939Q1, 1939-03-15 | +0 | +0 |
| `poland` | partitioned | 1939Q3, 1939-09-17 | 1939Q3, 1939-09-17 | +0 | +0 |
| `france` | at_war | 1939Q3, 1939-09-03 | 1939Q3, 1939-09-03 | +0 | +0 |
| `france` | fallen | 1940Q2, 1940-06-22 | 1940Q2, 1940-06-24 | +0 | +2 |
| `britain` | at_war | 1939Q3, 1939-09-03 | 1939Q3, 1939-09-03 | +0 | +0 |
| `balkans` | german_aligned | 1940Q3, 1940-08-30 | 1940Q4, 1940-10-02 | +1 | +33 |
| `channel_air` | british | 1940Q4, 1940-10-31 | 1940Q4, 1940-12-12 | +0 | +42 |
| `oil_GER` | secured | 1940Q1, 1940-02-11 | 1939Q2, 1939-04-12 | -3 | -305 |

## Disagreements and the indicators behind them

At the first quarter of each run of disagreement: the hindsight level with its latest event, and the replay level with the latest proposal's (unreviewed) quote.

- `belief_WEST`, 1938Q3: hindsight `uncertain` from 1938-09-12: "Sudeten demand: Hitler's Nuremberg speech demands self-determination for the Sudeten Germans; escalated at Berchtesgaden (15 September) and Godesberg (22 to 23 September)"; replay `limited` from 1938-09-29: "upon the emphatic advice of England and France".
- `belief_WEST`, 1940Q3: hindsight `hegemonic` from 1939-03-17: "Chamberlain's Birmingham speech asks whether Germany is attempting to dominate the world by force"; replay `limited` from 1940-07-29: "Laval is convinced that Germany has no intention to crush France ... their plan contemplates a European federation of states in which France will play an important role compatible with its dignity and tradition".
- `belief_GER`, 1936Q2: hindsight `will_not_fight` from 1938-09-30: "Britain and France concede the Sudetenland at Munich"; replay `uncertain` from 1936-05-18: "until the German fortifications had been constructed on the French border an involvement of Germany in war with Italy might lead to a French attack on Germany".
- `belief_GER`, 1938Q2: hindsight `will_not_fight` from 1938-09-30: "Britain and France concede the Sudetenland at Munich"; replay `will_fight` from 1938-05-22: "even though England were to take the course outlined in the British Government’s memorandum, Germany would not hesitate to make war any more than she had hesitated in 1914".
- `belief_GER`, 1939Q2: hindsight `uncertain` from 1939-05-23: "Hitler's conference with the service chiefs: Poland to be attacked at the first suitable opportunity; war with Britain and France considered possible"; replay `will_not_fight` from 1939-05-30: "his Government was convinced that if events should take place in the matter [manner?] outlined Great Britain and France would refuse to assist Poland and Germany would be left to deal with Poland alone.".
- `commit_WEST`, 1938Q3: hindsight `wary` from 1938-09-30: "Munich concession, followed by the acceleration of British rearmament as policy"; replay `appease` from 1938-09-30: "the British Minister appeared at 10 a.m. in Praha and told them that an answer to the proposal must be received from the Czech Government by 12 o’clock.".
- `polish_guarantee`, 1939Q1: hindsight `true` from 1939-03-31: "British guarantee to Poland announced in the Commons; France associated"; replay `false` (assumed, no indicator).
- `italy_estranged`, 1938Q1: hindsight `true` from 1935-10-03: "Italy invades Ethiopia; League of Nations sanctions from 18 November 1935"; replay `false` from 1938-02-17: "Italy being now on Germany's side".
- `sudeten`, 1938Q3: hindsight `german` from 1938-09-30: "Munich Agreement (signed in the early hours of 30 September, dated 29 September); occupation 1 to 10 October 1938"; replay `czech` from 1938-09-28: "the Sudeten problem would never have become a menace to world peace or even the cause of an internal conflict in this country".
- `balkans`, 1940Q3: hindsight `german_aligned` from 1940-08-30: "Second Vienna Award: Germany and Italy guarantee the remainder of Romania"; replay `neutral` from 1940-09-19: "this gratitude will not change Bulgaria’s policy of neutrality".
- `oil_GER`, 1939Q2: hindsight `dependent` from 1936-10-18: "Four-Year Plan decree: synthetic fuel programme to reduce dependence on imported oil"; replay `secured` from 1939-05-24: "the recently signed German-Rumanian economic agreement".
