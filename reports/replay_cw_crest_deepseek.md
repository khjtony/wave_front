# Blind Cold War replay on the CIA estimates, 1957 to 1962 (DeepSeek flash, unreviewed)

Run 2026-10-24 on the owner's decision 3c (the blind replay is to replace the manual one for C6 and C7 when it can run), with `wf replay --episode cw --corpus data/cw/corpora/raw/crest --years 1957..1962 --backend deepseek --model deepseek-flash` (no guidance file) at the commit in the run's `commit.txt` (a6e8fa0), then the proposal-level measurement below. 22 estimates; the proposals were not reviewed. Not a registered claim's computation: C6's parts (b) and (c) are not recomputed here.

**What it shows.** The replayed `belief_force_USA` is `few` in every year, equal to the hindsight `nuke_USSR`, and below the manual replay's `survivable` for 1958 to 1961. The quotes are the estimates' statements of the *current* Soviet force (about ten prototype ICBMs, an initial operational capability). The missile gap of the record lies in the estimates' *projections* (hundreds of ICBMs by 1961 to 1962) and in the political debate, which the manual replay coded as the belief. Whether `belief_force_USA` is Washington's estimate of the force at the date or its projection is a reading of the ontology (docs/ontology_cw.md) that the owner decides before this replay can stand in for the manual one; until then the manual replay stands (decision 3c).

---

PROPOSAL-LEVEL MEASUREMENT: no proposal below was reviewed. Every proposal the backend made was treated as if accepted to compute these metrics, no replay snapshot was written, and the levels and quotes below are the backend's unreviewed readings, not evidence accepted by a reviewer.

# Blind replay, CIA estimates 1957 to 1962, DeepSeek flash, proposal level

- Years: 1957 to 1962 (6); the snapshot of a year is the state on its 1 January, read from the documents dated to the 31 December before.
- Corpus: crest, `data/cw/corpora/raw/crest`
- Backend: deepseek, model `deepseek-flash`
- Harness rules recorded: `two-document`, `no-retrospective`; the three belief variables are readings, outside both rules, so the rules act on nothing here.
- Review: none: proposal-level measurement (every proposal treated as accepted, nothing written)
- Command: `wf replay --episode cw --years 1957..1962 --out OUT --measure-proposals`
- Compared with: the hindsight snapshots in `snapshots/cw/hindsight/` (the truth of what each belief estimates, decisions D6) and the contemporaneous beliefs of the record (the manual replay snapshots in `snapshots/cw/replay/`, else the `belief` rows of `data/cw/events.csv`). Every variable but the beliefs is carried from the hindsight snapshot as `assumed`.

## Proposals per variable

Every proposal kept by the extractor's checks over the years, by level, and how the harness rules classified it.

| Variable | Proposals | By level | Shown and counted | Held: one document | First of two documents | Blocked: monotone, back | retrospective? (not counted) |
|---|---|---|---|---|---|---|---|
| `belief_force_USA` | 17 | few 17 | 17 | 0 | 0 | 0 | 0 |
| `belief_USA_USSR` | 8 | opportunist 7, expansionist 1 | 8 | 0 | 0 | 0 | 0 |
| `belief_USSR_USA` | 0 | - | 0 | 0 | 0 | 0 | 0 |

## C6: the replayed estimate of the Soviet force against the hindsight force

Per year, the replayed `belief_force_USA` and the hindsight `nuke_USSR` (decisions R C6 (a): the replayed belief exceeds the hindsight force in every year 1958 to 1961), beside the contemporaneous belief of the record. These are inputs of C6; its parts (b) and (c) are computed on the model.

| Year | Replayed | Hindsight `nuke_USSR` | Replay exceeds | Contemporaneous (source) | Contemporaneous exceeds |
|---|---|---|---|---|---|
| 1957 | few | few | no | few (manual replay) | no |
| 1958 | few | few | no | survivable (manual replay) | yes |
| 1959 | few | few | no | survivable (manual replay) | yes |
| 1960 | few | few | no | survivable (manual replay) | yes |
| 1961 | few | few | no | survivable (manual replay) | yes |
| 1962 | few | few | no | few (manual replay) | no |

Years 1958 to 1961 with a replay snapshot: 4 of 4; the replayed estimate exceeds the hindsight force in 0 of them.

## Agreement per variable

| Variable | With the hindsight truth | With the contemporaneous belief |
|---|---|---|
| `belief_force_USA` | 6/6 (100%) | 2/6 (33%) |
| `belief_USA_USSR` | n/a (no hindsight level: the swept hypothesis) | 6/6 (100%) |
| `belief_USSR_USA` | 6/6 (100%) | 6/6 (100%) |

## Flips: lag against the contemporaneous record

A documented flip is a change of the contemporaneous belief between consecutive 1 Januaries; a replayed flip is the same in the replay, dated by the proposal (treated as accepted) that set it. Matched within 2 years to the same level; lag is replay minus documented, in years (positive: the replay is late).

| Variable | Level | Documented (year) | Replayed (year, date) | Lag (years) |
|---|---|---|---|---|
| `belief_force_USA` | survivable | 1958 | none (missed) | - |
| `belief_force_USA` | few | 1962 | none (missed) | - |
| `belief_force_USA` | few | none (false flip) | 1957, 1956-03-06 | - |

## Disagreements and the indicators behind them

Every year in which the replay differs from the hindsight truth or from the contemporaneous belief, with the replay's latest proposal's (unreviewed) quote.

- `belief_force_USA`, 1958: replay `few` from 1957-12-10: "the USSR will probably have a first operational capability with up to 10 prototype ICBMs"; hindsight few; contemporaneous survivable (manual replay).
- `belief_force_USA`, 1959: replay `few` from 1958-08-19: "The USSR will probably have a first operational capability with ten prototype ICBMs at some time during calendar 1959"; hindsight few; contemporaneous survivable (manual replay).
- `belief_force_USA`, 1960: replay `few` from 1959-11-03: "We cannot state with certainty the precise timing of the initial operational capability (IOC) of a few-say, l0--series produced ICBMs."; hindsight few; contemporaneous survivable (manual replay).
- `belief_force_USA`, 1961: replay `few` from 1960-02-09: "The Soviet rulers probably regard their present strategic attack forces as capable of devastating US and Allied copcentrations of population and industry, but incapable of preventing, by military action, the nuclear devastation of the USSR."; hindsight few; contemporaneous survivable (manual replay).
