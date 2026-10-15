SYNTHETIC RUN: the corpus is a fixture written for pipeline tests, every proposal was auto-accepted without review, and nothing below is evidence about 1936 to 1940. It measures the mechanics of the harness only.

# Replay metrics on the synthetic fixture corpus, WW2 1936Q1 to 1940Q4

- Quarters: 1936Q1 to 1940Q4 (20); snapshot compared at each quarter's last day.
- Corpus: local, `tests/evidence/fixtures/corpus_synthetic` (synthetic fixtures)
- Backend: rules
- Harness rules in force: none (every proposal is shown and counted as the backend made it) ([docs/replay_harness.md](../docs/replay_harness.md), section "Harness rules")
- Review: auto-accepted (synthetic run only)
- Command: `wf replay --quarters 1936Q1..1940Q4 --out OUT --corpus tests/evidence/fixtures/corpus_synthetic --rules none --auto-accept`
- Target: the hindsight snapshots in `snapshots/ww2/hindsight/` (levels at each quarter's end, read with full knowledge of the record).

What this run shows: that the harness filters each quarter's corpus by document date, extracts proposals in the fixed schema, checks them, turns accepted proposals into schema-valid snapshots with their quotes and rules, and computes the agreement, lag and false-flip metrics against the hindsight snapshots. What it does not show: anything about extraction quality on real documents. The fixtures summarize the same dated events the hindsight snapshots are built from, and the rule backend's keywords were written alongside them, so high agreement is expected; the disagreements that remain are listed at the end with the indicators behind them.

## Date filtering

| Quarter | Documents dated at or before its end | Read this quarter | Proposals | Discarded by the checks |
|---|---|---|---|---|
| 1936Q1 | 2 | 2 | 4 | 0 |
| 1936Q2 | 2 | 0 | 0 | 0 |
| 1936Q3 | 3 | 1 | 0 | 0 |
| 1936Q4 | 6 | 3 | 4 | 0 |
| 1937Q1 | 6 | 0 | 0 | 0 |
| 1937Q2 | 7 | 1 | 0 | 0 |
| 1937Q3 | 8 | 1 | 1 | 0 |
| 1937Q4 | 8 | 0 | 0 | 0 |
| 1938Q1 | 9 | 1 | 1 | 0 |
| 1938Q2 | 10 | 1 | 1 | 0 |
| 1938Q3 | 12 | 2 | 3 | 0 |
| 1938Q4 | 14 | 2 | 0 | 0 |
| 1939Q1 | 17 | 3 | 4 | 0 |
| 1939Q2 | 20 | 3 | 3 | 0 |
| 1939Q3 | 27 | 7 | 11 | 0 |
| 1939Q4 | 28 | 1 | 1 | 0 |
| 1940Q1 | 29 | 1 | 1 | 0 |
| 1940Q2 | 33 | 4 | 3 | 0 |
| 1940Q3 | 37 | 4 | 6 | 0 |
| 1940Q4 | 40 | 3 | 3 | 0 |

## Summary against section 9

- Text-derived variables, exact level agreement over variable-quarters: 488/500 (98%).
- For scale: a replay that reads nothing (every text variable at its initial level) agrees on 305/500 (61%). Split by the hindsight level: where it is still the initial one, this replay agrees on 305/305 (100%); where it has moved, on 183/195 (94%).
- Resource variables: 100/100 (100%), but they are copied from the hindsight snapshots (they come from the datasets), so this checks the copy, not a reading; the section 9 target of 80 percent for resource variables is not tested by a replay of documents.
- Belief and commitment flips: 8 of 9 documented flips replayed within one quarter (8 matched within 4 quarters).
- False flips (replayed, no documented flip to the same level within 4 quarters): 2. Missed flips: 1.

## Agreement per variable

| Group | Variable | Agreement | Reading nothing | Quarters that disagree (hindsight / replay) |
|---|---|---|---|---|
| beliefs and commitment | `belief_WEST` | 14/20 (70%) | 10/20 (50%) | 1939Q3 (hegemonic / uncertain), 1939Q4 (hegemonic / uncertain), 1940Q1 (hegemonic / uncertain), 1940Q2 (hegemonic / uncertain), 1940Q3 (hegemonic / uncertain), 1940Q4 (hegemonic / uncertain) |
| beliefs and commitment | `belief_GER` | 14/20 (70%) | 13/20 (65%) | 1939Q3 (will_fight / will_not_fight), 1939Q4 (will_fight / will_not_fight), 1940Q1 (will_fight / will_not_fight), 1940Q2 (will_fight / will_not_fight), 1940Q3 (will_fight / will_not_fight), 1940Q4 (will_fight / will_not_fight) |
| beliefs and commitment | `commit_WEST` | 20/20 (100%) | 10/20 (50%) | - |
| beliefs and commitment | `commit_US` | 20/20 (100%) | 15/20 (75%) | - |
| treaty | `treaty` | 20/20 (100%) | 0/20 (0%) | - |
| pacts and structural flags | `axis` | 20/20 (100%) | 3/20 (15%) | - |
| pacts and structural flags | `anticomintern` | 20/20 (100%) | 3/20 (15%) | - |
| pacts and structural flags | `nazi_soviet_pact` | 20/20 (100%) | 14/20 (70%) | - |
| pacts and structural flags | `polish_guarantee` | 20/20 (100%) | 12/20 (60%) | - |
| pacts and structural flags | `anglo_soviet_alliance` | 20/20 (100%) | 20/20 (100%) | - |
| pacts and structural flags | `ussr_axis` | 20/20 (100%) | 20/20 (100%) | - |
| pacts and structural flags | `italy_estranged` | 20/20 (100%) | 20/20 (100%) | - |
| pacts and structural flags | `china_war` | 20/20 (100%) | 6/20 (30%) | - |
| war | `war_west_ger` | 20/20 (100%) | 14/20 (70%) | - |
| regions | `rhineland` | 20/20 (100%) | 0/20 (0%) | - |
| regions | `austria` | 20/20 (100%) | 8/20 (40%) | - |
| regions | `sudeten` | 20/20 (100%) | 10/20 (50%) | - |
| regions | `bohemia` | 20/20 (100%) | 12/20 (60%) | - |
| regions | `poland` | 20/20 (100%) | 14/20 (70%) | - |
| regions | `france` | 20/20 (100%) | 14/20 (70%) | - |
| regions | `britain` | 20/20 (100%) | 14/20 (70%) | - |
| regions | `balkans` | 20/20 (100%) | 18/20 (90%) | - |
| regions | `siberia` | 20/20 (100%) | 20/20 (100%) | - |
| regions | `channel_air` | 20/20 (100%) | 19/20 (95%) | - |
| oil | `oil_GER` | 20/20 (100%) | 16/20 (80%) | - |
| resources (copied) | `arms_GER` | 20/20 (100%) | - | - |
| resources (copied) | `arms_WEST` | 20/20 (100%) | - | - |
| resources (copied) | `arms_USSR` | 20/20 (100%) | - | - |
| resources (copied) | `arms_JPN` | 20/20 (100%) | - | - |
| resources (copied) | `ind_GER` | 20/20 (100%) | - | - |

## Flips: lag against the documented date

A documented flip is a change of level between consecutive hindsight snapshots, dated by the event that set the new level; a replayed flip is the same in the replay snapshots, dated by the accepted proposal that set it. Lag is replay minus documented (positive: the replay is late).

| Variable | Level | Documented (quarter, date) | Replayed (quarter, date) | Lag (quarters) | Lag (days) |
|---|---|---|---|---|---|
| `belief_WEST` | uncertain | 1938Q3, 1938-09-12 | 1938Q3, 1938-09-12 | +0 | +0 |
| `belief_WEST` | hegemonic | 1939Q1, 1939-03-17 | 1939Q1, 1939-03-17 | +0 | +0 |
| `belief_WEST` | uncertain | none (false flip) | 1939Q3, 1939-09-01 | - | - |
| `belief_GER` | uncertain | 1939Q2, 1939-05-23 | 1939Q2, 1939-05-23 | +0 | +0 |
| `belief_GER` | will_fight | 1939Q3, 1939-09-03 | none (missed) | - | - |
| `belief_GER` | will_not_fight | none (false flip) | 1939Q3, 1939-08-22 | - | - |
| `commit_WEST` | wary | 1938Q3, 1938-09-30 | 1938Q3, 1938-09-30 | +0 | +0 |
| `commit_WEST` | resolved | 1939Q1, 1939-03-31 | 1939Q1, 1939-03-31 | +0 | +0 |
| `commit_WEST` | at_war | 1939Q3, 1939-09-03 | 1939Q3, 1939-09-03 | +0 | +0 |
| `commit_US` | wary | 1939Q4, 1939-11-04 | 1939Q4, 1939-11-04 | +0 | +0 |
| `commit_US` | engaged | 1940Q3, 1940-09-02 | 1940Q3, 1940-09-02 | +0 | +0 |
| `treaty` | dead | 1936Q1, 1936-03-07 | 1936Q1, 1936-03-07 | +0 | +0 |
| `axis` | true | 1936Q4, 1936-10-23 | 1936Q4, 1936-10-23 | +0 | +0 |
| `anticomintern` | true | 1936Q4, 1936-11-25 | 1936Q4, 1936-11-25 | +0 | +0 |
| `nazi_soviet_pact` | true | 1939Q3, 1939-08-23 | 1939Q3, 1939-08-23 | +0 | +0 |
| `polish_guarantee` | true | 1939Q1, 1939-03-31 | 1939Q1, 1939-03-31 | +0 | +0 |
| `china_war` | true | 1937Q3, 1937-07-07 | 1937Q3, 1937-07-07 | +0 | +0 |
| `war_west_ger` | war | 1939Q3, 1939-09-03 | 1939Q3, 1939-09-03 | +0 | +0 |
| `rhineland` | remilitarized | 1936Q1, 1936-03-07 | 1936Q1, 1936-03-07 | +0 | +0 |
| `austria` | annexed | 1938Q1, 1938-03-12 | 1938Q1, 1938-03-12 | +0 | +0 |
| `sudeten` | german | 1938Q3, 1938-09-30 | 1938Q3, 1938-09-30 | +0 | +0 |
| `bohemia` | german | 1939Q1, 1939-03-15 | 1939Q1, 1939-03-15 | +0 | +0 |
| `poland` | partitioned | 1939Q3, 1939-09-17 | 1939Q3, 1939-09-17 | +0 | +0 |
| `france` | at_war | 1939Q3, 1939-09-03 | 1939Q3, 1939-09-03 | +0 | +0 |
| `france` | fallen | 1940Q2, 1940-06-22 | 1940Q2, 1940-06-22 | +0 | +0 |
| `britain` | at_war | 1939Q3, 1939-09-03 | 1939Q3, 1939-09-03 | +0 | +0 |
| `balkans` | german_aligned | 1940Q3, 1940-08-30 | 1940Q3, 1940-08-30 | +0 | +0 |
| `channel_air` | british | 1940Q4, 1940-10-31 | 1940Q4, 1940-10-31 | +0 | +0 |
| `oil_GER` | secured | 1940Q1, 1940-02-11 | 1940Q1, 1940-02-11 | +0 | +0 |

## Disagreements and the indicators behind them

At the first quarter of each run of disagreement: the hindsight level with its latest event, and the replay level with the latest accepted quote.

- `belief_WEST`, 1939Q3: hindsight `hegemonic` from 1939-03-17: "Chamberlain's Birmingham speech asks whether Germany is attempting to dominate the world by force"; replay `uncertain` from 1939-09-01: "In London and Paris general mobilization has been ordered, and the British and French Ambassadors have presented warnings in Berlin.".
- `belief_GER`, 1939Q3: hindsight `will_fight` from 1939-09-03: "The declarations of war disprove the expectation of 22 August"; replay `will_not_fight` from 1939-08-22: "Our enemies are little worms; I saw them at Munich.".
