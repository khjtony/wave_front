PROPOSAL-LEVEL MEASUREMENT: no proposal below was reviewed. Every proposal the backend made was treated as if accepted to compute these metrics, no replay snapshot was written, and the levels and quotes below are the backend's unreviewed readings, not evidence accepted by a reviewer.

# Replay metrics, Cold War 1957 to 1962

- Years: 1957 to 1962 (6); the snapshot of a year is the state on its 1 January, read from the documents dated to the 31 December before.
- Corpus: crest, `/home/khjtony/workspace/wave_front/data/cw/corpora/raw/crest`
- Backend: claude, model `claude-opus-5-5`, effort high
- Harness rules recorded: `two-document`, `no-retrospective`; the three belief variables are readings, outside both rules, so the rules act on nothing here.
- Review: none: proposal-level measurement (every proposal treated as accepted, nothing written)
- Command: `wf replay --episode cw --years 1957..1962 --out OUT --corpus /home/khjtony/workspace/wave_front/data/cw/corpora/raw/crest --backend claude --measure-proposals`
- Compared with: the hindsight snapshots in `snapshots/cw/hindsight/` (the truth of what each belief estimates, decisions D6) and the contemporaneous beliefs of the record (the manual replay snapshots in `snapshots/cw/replay/`, else the `belief` rows of `data/cw/events.csv`). Every variable but the beliefs is carried from the hindsight snapshot as `assumed`.

## Date filtering

| Year | Documents dated before its 1 January | Read this year | Proposals | Discarded by the checks |
|---|---|---|---|---|
| 1957 | 1 | 1 | 1 | 0 |
| 1958 | 5 | 4 | 3 | 1 |
| 1959 | 9 | 4 | 4 | 2 |
| 1960 | 10 | 1 | 0 | 0 |
| 1961 | 16 | 6 | 6 | 1 |
| 1962 | 22 | 6 | 3 | 1 |

## Proposals per variable

Every proposal kept by the extractor's checks over the years, by level, and how the harness rules classified it.

| Variable | Proposals | By level | Shown and counted | Held: one document | First of two documents | Blocked: monotone, back | retrospective? (not counted) |
|---|---|---|---|---|---|---|---|
| `belief_force_USA` | 14 | under_1000 13, under_200 1 | 14 | 0 | 0 | 0 | 0 |
| `belief_USA_USSR` | 3 | opportunist 3 | 3 | 0 | 0 | 0 | 0 |
| `belief_USSR_USA` | 0 | - | 0 | 0 | 0 | 0 | 0 |

## C6: the replayed estimate of the Soviet force against the hindsight force

Per year, the replayed `belief_force_USA` and the hindsight `count_USSR`, the number of Soviet intercontinental delivery vehicles in being, in the same bands (the owner's decision 7g; cw_v1 decisions R V6 (a), v0's C6 as amended: the replayed belief exceeds the hindsight count, a higher band, in every year 1958 to 1961), beside the contemporaneous belief of the record. These are inputs of C6; its parts (b) and (c) are computed on the model.

| Year | Replayed | Hindsight `count_USSR` | Replay exceeds | Contemporaneous (source) | Contemporaneous exceeds |
|---|---|---|---|---|---|
| 1957 | under_1000 | under_200 | yes | under_1000 (manual replay) | yes |
| 1958 | under_1000 | under_200 | yes | under_1000 (manual replay) | yes |
| 1959 | under_1000 | under_200 | yes | under_1000 (manual replay) | yes |
| 1960 | under_1000 | under_200 | yes | under_1000 (manual replay) | yes |
| 1961 | under_1000 | under_200 | yes | under_1000 (manual replay) | yes |
| 1962 | under_1000 | under_200 | yes | under_1000 (manual replay) | yes |

Years 1958 to 1961 with a replay snapshot: 4 of 4; the replayed estimate exceeds the hindsight force in 4 of them.

## Agreement per variable

| Variable | With the hindsight truth | With the contemporaneous belief |
|---|---|---|
| `belief_force_USA` | 0/6 (0%) | 6/6 (100%) |
| `belief_USA_USSR` | n/a (no hindsight level: the swept hypothesis) | 6/6 (100%) |
| `belief_USSR_USA` | 6/6 (100%) | 6/6 (100%) |

## Flips: lag against the contemporaneous record

A documented flip is a change of the contemporaneous belief between consecutive 1 Januaries; a replayed flip is the same in the replay, dated by the proposal (treated as accepted) that set it. Matched within 2 years to the same level; lag is replay minus documented, in years (positive: the replay is late).

| Variable | Level | Documented (year) | Replayed (year, date) | Lag (years) |
|---|---|---|---|---|
| `belief_force_USA` | under_1000 | 1957 | 1957, 1956-03-06 | +0 |

## Disagreements and the indicators behind them

Every year in which the replay differs from the hindsight truth or from the contemporaneous belief, with the replay's latest proposal's (unreviewed) quote.

- `belief_force_USA`, 1957: replay `under_1000` from 1956-03-06: "We have also estimated that by mid-1959 the USSR would have some 400 BISON and 300 BEAR aircraft in operational use."; hindsight under_200; contemporaneous under_1000 (manual replay).
- `belief_force_USA`, 1958: replay `under_1000` from 1957-11-12: "we estimate that the Soviets may by mid-1960 have about 400-600 heavy bombers and tankers of jet and turboprop types"; hindsight under_200; contemporaneous under_1000 (manual replay).
- `belief_force_USA`, 1959: replay `under_1000` from 1958-12-23: "we therefore believe that a capability with 500 ICBMs could be achieved some time in 1962"; hindsight under_200; contemporaneous under_1000 (manual replay).
- `belief_force_USA`, 1960: replay `under_1000` from 1958-12-23: "we therefore believe that a capability with 500 ICBMs could be achieved some time in 1962"; hindsight under_200; contemporaneous under_1000 (manual replay).
- `belief_force_USA`, 1961: replay `under_1000` from 1960-08-01: "The Director of Central Intelligence considers that program "A" should be regarded as the nearest approximation of the actual Soviet program."; hindsight under_200; contemporaneous under_1000 (manual replay).
- `belief_force_USA`, 1962: replay `under_1000` from 1961-06-07: "100200 operational launchers in mid-1962, 150300 in mid-1963, and 200--400 in .mid-1964"; hindsight under_200; contemporaneous under_1000 (manual replay).
