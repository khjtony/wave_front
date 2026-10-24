PROPOSAL-LEVEL MEASUREMENT: no proposal below was reviewed. Every proposal the backend made was treated as if accepted to compute these metrics, no replay snapshot was written, and the levels and quotes below are the backend's unreviewed readings, not evidence accepted by a reviewer.

# Replay metrics, FRUS 1936 to 1940, Claude backend, proposal level

- Quarters: 1936Q1 to 1940Q4 (20); snapshot compared at each quarter's last day.
- Corpus: frus, `data/ww2/corpora/raw/frus`
- Backend: claude, model `claude-opus-5-5`, effort high
- Harness rules in force: `two-document`, `no-retrospective` ([docs/replay_harness.md](../docs/replay_harness.md), section "Harness rules")
- Review: none: proposal-level measurement (every proposal treated as accepted, nothing written)
- Command: `wf replay --quarters 1936Q1..1940Q4 --out OUT --measure-proposals`
- Target: the hindsight snapshots in `snapshots/ww2/hindsight/` (levels at each quarter's end, read with full knowledge of the record).

## Proposals per variable

Every proposal kept by the extractor's checks over the quarters, by level.

| Variable | Proposals | By level |
|---|---|---|
| `belief_WEST` | 165 | limited 79, uncertain 56, hegemonic 30 |
| `belief_GER` | 9 | uncertain 4, will_fight 3, will_not_fight 2 |
| `commit_WEST` | 196 | appease 68, resolved 68, at_war 45, wary 15 |
| `commit_US` | 205 | isolationist 129, wary 58, engaged 18 |
| `treaty` | 17 | dead 14, eroded 3 |
| `axis` | 96 | true 92, false 4 |
| `anticomintern` | 38 | true 38 |
| `nazi_soviet_pact` | 79 | true 79 |
| `polish_guarantee` | 42 | true 42 |
| `anglo_soviet_alliance` | 36 | false 36 |
| `ussr_axis` | 9 | false 9 |
| `italy_estranged` | 83 | true 76, false 7 |
| `china_war` | 68 | true 68 |
| `war_west_ger` | 223 | war 222, peace 1 |
| `rhineland` | 77 | remilitarized 76, demilitarized 1 |
| `austria` | 118 | annexed 115, independent 3 |
| `sudeten` | 29 | german 28, czech 1 |
| `bohemia` | 58 | german 58 |
| `poland` | 167 | partitioned 114, german 53 |
| `france` | 329 | at_war 167, fallen 162 |
| `britain` | 377 | at_war 377 |
| `balkans` | 22 | german_aligned 14, neutral 8 |
| `siberia` | 0 | - |
| `channel_air` | 13 | contested 9, british 4 |
| `oil_GER` | 38 | secured 38 |
| all | 2494 | |

## What the harness rules did

Every proposal of the quarters, classified at the last quarter's end under `two-document`, `no-retrospective`. Only the first column is counted by the metrics; a flip of a variable under the two-document rule is counted at, and dated by, the proposal of its second document (the first is listed under "First of two documents").

| Variable | Proposals | Shown and counted | Held: one document | First of two documents | Blocked: monotone, back | retrospective? (not counted) |
|---|---|---|---|---|---|---|
| `belief_WEST` | 165 | 165 | 0 | 0 | 0 | 0 |
| `belief_GER` | 9 | 9 | 0 | 0 | 0 | 0 |
| `commit_WEST` | 196 | 196 | 0 | 0 | 0 | 0 |
| `commit_US` | 205 | 205 | 0 | 0 | 0 | 0 |
| `treaty` | 17 | 17 | 0 | 0 | 0 | 0 |
| `axis` | 96 | 95 | 0 | 1 | 0 | 0 |
| `anticomintern` | 38 | 37 | 0 | 1 | 0 | 0 |
| `nazi_soviet_pact` | 79 | 78 | 0 | 1 | 0 | 0 |
| `polish_guarantee` | 42 | 41 | 0 | 1 | 0 | 0 |
| `anglo_soviet_alliance` | 36 | 36 | 0 | 0 | 0 | 0 |
| `ussr_axis` | 9 | 9 | 0 | 0 | 0 | 0 |
| `italy_estranged` | 83 | 64 | 0 | 1 | 0 | 18 |
| `china_war` | 68 | 67 | 0 | 1 | 0 | 0 |
| `war_west_ger` | 223 | 222 | 0 | 1 | 0 | 0 |
| `rhineland` | 77 | 77 | 0 | 0 | 0 | 0 |
| `austria` | 118 | 117 | 0 | 1 | 0 | 0 |
| `sudeten` | 29 | 28 | 0 | 1 | 0 | 0 |
| `bohemia` | 58 | 57 | 0 | 1 | 0 | 0 |
| `poland` | 167 | 162 | 0 | 2 | 3 | 0 |
| `france` | 329 | 327 | 0 | 2 | 0 | 0 |
| `britain` | 377 | 376 | 0 | 1 | 0 | 0 |
| `balkans` | 22 | 21 | 0 | 1 | 0 | 0 |
| `siberia` | 0 | 0 | 0 | 0 | 0 | 0 |
| `channel_air` | 13 | 12 | 0 | 1 | 0 | 0 |
| `oil_GER` | 38 | 37 | 0 | 1 | 0 | 0 |
| all | 2494 | 2455 | 0 | 18 | 3 | 18 |

## Summary against section 9

- Text-derived variables, exact level agreement over variable-quarters: 472/500 (94%).
- For scale: a replay that reads nothing (every text variable at its initial level) agrees on 304/500 (61%). Split by the hindsight level: where it is still the initial one, this replay agrees on 287/304 (94%); where it has moved, on 185/196 (94%).
- Resource variables: 100/100 (100%), but they are copied from the hindsight snapshots (they come from the datasets), so this checks the copy, not a reading; the section 9 target of 80 percent for resource variables is not tested by a replay of documents.
- Belief and commitment flips: 8 of 9 documented flips replayed within one quarter (9 matched within 4 quarters).
- False flips (replayed, no documented flip to the same level within 4 quarters): 4. Missed flips: 0.

## Agreement per variable

| Group | Variable | Agreement | Reading nothing | Quarters that disagree (hindsight / replay) |
|---|---|---|---|---|
| beliefs and commitment | `belief_WEST` | 19/20 (95%) | 9/20 (45%) | 1938Q4 (uncertain / limited) |
| beliefs and commitment | `belief_GER` | 11/20 (55%) | 13/20 (65%) | 1938Q3 (will_not_fight / will_fight), 1938Q4 (will_not_fight / will_fight), 1939Q2 (uncertain / will_not_fight), 1939Q3 (will_fight / uncertain), 1939Q4 (will_fight / uncertain), 1940Q1 (will_fight / uncertain), 1940Q2 (will_fight / uncertain), 1940Q3 (will_fight / uncertain), 1940Q4 (will_fight / uncertain) |
| beliefs and commitment | `commit_WEST` | 19/20 (95%) | 10/20 (50%) | 1938Q4 (wary / appease) |
| beliefs and commitment | `commit_US` | 20/20 (100%) | 15/20 (75%) | - |
| treaty | `treaty` | 20/20 (100%) | 0/20 (0%) | - |
| pacts and structural flags | `axis` | 20/20 (100%) | 3/20 (15%) | - |
| pacts and structural flags | `anticomintern` | 20/20 (100%) | 3/20 (15%) | - |
| pacts and structural flags | `nazi_soviet_pact` | 20/20 (100%) | 14/20 (70%) | - |
| pacts and structural flags | `polish_guarantee` | 19/20 (95%) | 12/20 (60%) | 1939Q1 (true / false) |
| pacts and structural flags | `anglo_soviet_alliance` | 20/20 (100%) | 20/20 (100%) | - |
| pacts and structural flags | `ussr_axis` | 20/20 (100%) | 20/20 (100%) | - |
| pacts and structural flags | `italy_estranged` | 9/20 (45%) | 20/20 (100%) | 1938Q2 (true / false), 1938Q3 (true / false), 1938Q4 (true / false), 1939Q1 (true / false), 1939Q2 (true / false), 1939Q3 (true / false), 1939Q4 (true / false), 1940Q1 (true / false), 1940Q2 (true / false), 1940Q3 (true / false), 1940Q4 (true / false) |
| pacts and structural flags | `china_war` | 20/20 (100%) | 6/20 (30%) | - |
| war | `war_west_ger` | 20/20 (100%) | 14/20 (70%) | - |
| regions | `rhineland` | 20/20 (100%) | 0/20 (0%) | - |
| regions | `austria` | 20/20 (100%) | 8/20 (40%) | - |
| regions | `sudeten` | 20/20 (100%) | 10/20 (50%) | - |
| regions | `bohemia` | 20/20 (100%) | 12/20 (60%) | - |
| regions | `poland` | 20/20 (100%) | 14/20 (70%) | - |
| regions | `france` | 20/20 (100%) | 14/20 (70%) | - |
| regions | `britain` | 20/20 (100%) | 14/20 (70%) | - |
| regions | `balkans` | 19/20 (95%) | 18/20 (90%) | 1940Q3 (german_aligned / neutral) |
| regions | `siberia` | 20/20 (100%) | 20/20 (100%) | - |
| regions | `channel_air` | 20/20 (100%) | 19/20 (95%) | - |
| oil | `oil_GER` | 16/20 (80%) | 16/20 (80%) | 1939Q1 (dependent / secured), 1939Q2 (dependent / secured), 1939Q3 (dependent / secured), 1939Q4 (dependent / secured) |
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
| `belief_WEST` | hegemonic | 1939Q1, 1939-03-17 | 1939Q1, 1939-03-22 | +0 | +5 |
| `belief_WEST` | limited | none (false flip) | 1938Q4, 1938-11-25 | - | - |
| `belief_GER` | uncertain | 1939Q2, 1939-05-23 | 1939Q3, 1939-08-26 | +1 | +95 |
| `belief_GER` | will_fight | 1939Q3, 1939-09-03 | 1938Q3, 1938-09-17 | -4 | -351 |
| `belief_GER` | will_not_fight | none (false flip) | 1939Q1, 1939-03-23 | - | - |
| `commit_WEST` | wary | 1938Q3, 1938-09-30 | 1938Q3, 1938-09-26 | +0 | -4 |
| `commit_WEST` | resolved | 1939Q1, 1939-03-31 | 1939Q1, 1939-03-31 | +0 | +0 |
| `commit_WEST` | at_war | 1939Q3, 1939-09-03 | 1939Q3, 1939-09-03 | +0 | +0 |
| `commit_WEST` | appease | none (false flip) | 1938Q4, 1938-10-12 | - | - |
| `commit_US` | wary | 1939Q4, 1939-11-04 | 1939Q4, 1939-11-04 | +0 | +0 |
| `commit_US` | engaged | 1940Q3, 1940-09-02 | 1940Q3, 1940-09-02 | +0 | +0 |
| `treaty` | dead | 1936Q1, 1936-03-07 | 1936Q1, 1936-03-20 | +0 | +13 |
| `axis` | true | 1936Q4, 1936-10-23 | 1936Q4, 1936-11-14 | +0 | +22 |
| `anticomintern` | true | 1936Q4, 1936-11-25 | 1936Q4, 1936-11-25 | +0 | +0 |
| `nazi_soviet_pact` | true | 1939Q3, 1939-08-23 | 1939Q3, 1939-08-23 | +0 | +0 |
| `polish_guarantee` | true | 1939Q1, 1939-03-31 | 1939Q2, 1939-03-31 | +1 | +0 |
| `italy_estranged` | false | none (false flip) | 1938Q2, 1938-04-16 | - | - |
| `china_war` | true | 1937Q3, 1937-07-07 | 1937Q3, 1937-08-31 | +0 | +55 |
| `war_west_ger` | war | 1939Q3, 1939-09-03 | 1939Q3, 1939-09-04 | +0 | +1 |
| `rhineland` | remilitarized | 1936Q1, 1936-03-07 | 1936Q1, 1936-03-07 | +0 | +0 |
| `austria` | annexed | 1938Q1, 1938-03-12 | 1938Q1, 1938-03-12 | +0 | +0 |
| `sudeten` | german | 1938Q3, 1938-09-30 | 1938Q3, 1938-09-30 | +0 | +0 |
| `bohemia` | german | 1939Q1, 1939-03-15 | 1939Q1, 1939-03-15 | +0 | +0 |
| `poland` | partitioned | 1939Q3, 1939-09-17 | 1939Q3, 1939-09-17 | +0 | +0 |
| `france` | at_war | 1939Q3, 1939-09-03 | 1939Q3, 1939-09-05 | +0 | +2 |
| `france` | fallen | 1940Q2, 1940-06-22 | 1940Q2, 1940-06-22 | +0 | +0 |
| `britain` | at_war | 1939Q3, 1939-09-03 | 1939Q3, 1939-09-03 | +0 | +0 |
| `balkans` | german_aligned | 1940Q3, 1940-08-30 | 1940Q4, 1940-10-15 | +1 | +46 |
| `channel_air` | british | 1940Q4, 1940-10-31 | 1940Q4, 1940-10-17 | +0 | -14 |
| `oil_GER` | secured | 1940Q1, 1940-02-11 | 1939Q1, 1939-03-24 | -4 | -324 |

## Disagreements and the indicators behind them

At the first quarter of each run of disagreement: the hindsight level with its latest event, and the replay level with the latest proposal's (unreviewed) quote.

- `belief_WEST`, 1938Q4: hindsight `uncertain` from 1938-09-12: "Sudeten demand: Hitler's Nuremberg speech demands self-determination for the Sudeten Germans; escalated at Berchtesgaden (15 September) and Godesberg (22 to 23 September)"; replay `limited` from 1938-11-25: "Hitler liberated from the diktat of Versailles was of his own free will pledging himself to renounce any claim to Alsace-Lorraine and to respect the French frontiers. It would be absurd for France to refuse such an offer. Bonnet said that he was now convinced that France had no reason to fear an attack from Germany.".
- `belief_GER`, 1938Q3: hindsight `will_not_fight` from 1938-09-30: "Britain and France concede the Sudetenland at Munich"; replay `will_fight` from 1938-09-17: "Hitler said he was perfectly willing to take on a world war".
- `belief_GER`, 1939Q2: hindsight `uncertain` from 1939-05-23: "Hitler's conference with the service chiefs: Poland to be attacked at the first suitable opportunity; war with Britain and France considered possible"; replay `will_not_fight` from 1939-05-30: "his Government was convinced that if events should take place in the matter [manner?] outlined Great Britain and France would refuse to assist Poland and Germany would be left to deal with Poland alone".
- `commit_WEST`, 1938Q4: hindsight `wary` from 1938-09-30: "Munich concession, followed by the acceleration of British rearmament as policy"; replay `appease` from 1938-10-12: "Then after that to let Hitler go ahead and do what he likes in Central Europe... even if he decides to go into Rumania it is Halifax's idea that England should mind her own business".
- `polish_guarantee`, 1939Q1: hindsight `true` from 1939-03-31: "British guarantee to Poland announced in the Commons; France associated"; replay `false` (assumed, no indicator).
- `italy_estranged`, 1938Q2: hindsight `true` from 1935-10-03: "Italy invades Ethiopia; League of Nations sanctions from 18 November 1935"; replay `false` from 1938-05-09: "Chamberlain was extremely proud of his agreement with Italy ... there was unquestionably a change in Italy's attitude toward France".
- `balkans`, 1940Q3: hindsight `german_aligned` from 1940-08-30: "Second Vienna Award: Germany and Italy guarantee the remainder of Romania"; replay `neutral` from 1940-05-27: "the German Government was using this situation to press for a hundred percent alignment of Rumania with Germany for protection... Naturally he is seeking a way out of succumbing to German offer of protection".
- `oil_GER`, 1939Q1: hindsight `dependent` from 1936-10-18: "Four-Year Plan decree: synthetic fuel programme to reduce dependence on imported oil"; replay `secured` from 1939-03-24: "shortly after the details of the Rumanian-German accord had been confirmed here".
