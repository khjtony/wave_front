# Blind Cold War replay on the CIA estimates, 1957 to 1962, under the projected-force reading (two readers, unreviewed)

Run 2026-10-27 after the owner's decision 7d fixed `belief_force_USA` as the projected force (docs/ontology_cw.md), at commit a9a15d8, with `wf replay --episode cw --corpus data/cw/corpora/raw/crest --years 1957..1962`, once with `--backend deepseek` (flash, no guidance: the WW2 guidance is not sent for the Cold War) and once with `--backend claude` (about USD 3.75). 22 estimates; proposals not reviewed; no registered claim recomputed.

| Year | DeepSeek | Claude | Hindsight `nuke_USSR` | Manual replay (contemporaneous) |
|---|---|---|---|---|
| 1957 | overkill | few | few | few |
| 1958 | few | few | few | survivable |
| 1959 | few | few | few | survivable |
| 1960 | few | few | few | survivable |
| 1961 | few | survivable | few | survivable |
| 1962 | few | few | few | few |

**What it shows.** The projections are in the quotes the readers cite (NIE 11-8-60 projects 30, 150, 270 and 400 operational ICBM launchers for the years ahead), yet both readers mostly keep `few`. The reason is the scale: `belief_force_USA` is on `nuke_USSR`'s scale, whose levels measure **survivability** (`few`: weapons and delivery means vulnerable to a first strike; `survivable`: a force able to absorb a first strike, at sea, in hardened silos or on alert), not numbers. The projected Soviet ICBMs of 1958 to 1961 were soft and few in being; by the scale's own definition even hundreds of them are `few`. The missile gap was a gap in **numbers**, which this scale cannot express. Claude's one `survivable` (1961, from NIE 11-4-60 of 1 Dec 1960, "the USSR's emergence from strategic inequality ... a substantial missile force") is a reading of strategic parity rather than of survivability. DeepSeek's `overkill` for 1957 reads the bomber projection of 1956 (400 Bison and 300 Bear by mid-1959) as several times the assured-destruction requirement.

**Consequence for C6.** C6 (a), "the replayed belief exceeds the hindsight force", cannot be met on this scale unless the scale counts numbers, and the manual replay's `survivable` for 1958 to 1961 codes the debate rather than the scale's definition. This is an ontology question for the owner: give the belief its own scale (e.g. the projected count of intercontinental launchers in bands), or read the claim on survivability and accept that the missile gap is not a survivability gap. Until then the manual replay stands (decision 3c).

---

## DeepSeek report

PROPOSAL-LEVEL MEASUREMENT: no proposal below was reviewed. Every proposal the backend made was treated as if accepted to compute these metrics, no replay snapshot was written, and the levels and quotes below are the backend's unreviewed readings, not evidence accepted by a reviewer.

# Blind replay, CIA estimates 1957 to 1962, deepseek, projected-force reading, proposal level

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
| `belief_force_USA` | 10 | few 7, overkill 3 | 10 | 0 | 0 | 0 | 0 |
| `belief_USA_USSR` | 10 | opportunist 7, expansionist 3 | 10 | 0 | 0 | 0 | 0 |
| `belief_USSR_USA` | 0 | - | 0 | 0 | 0 | 0 | 0 |

## C6: the replayed estimate of the Soviet force against the hindsight force

Per year, the replayed `belief_force_USA` and the hindsight `nuke_USSR` (decisions R C6 (a): the replayed belief exceeds the hindsight force in every year 1958 to 1961), beside the contemporaneous belief of the record. These are inputs of C6; its parts (b) and (c) are computed on the model.

| Year | Replayed | Hindsight `nuke_USSR` | Replay exceeds | Contemporaneous (source) | Contemporaneous exceeds |
|---|---|---|---|---|---|
| 1957 | overkill | few | yes | few (manual replay) | no |
| 1958 | few | few | no | survivable (manual replay) | yes |
| 1959 | few | few | no | survivable (manual replay) | yes |
| 1960 | few | few | no | survivable (manual replay) | yes |
| 1961 | few | few | no | survivable (manual replay) | yes |
| 1962 | few | few | no | few (manual replay) | no |

Years 1958 to 1961 with a replay snapshot: 4 of 4; the replayed estimate exceeds the hindsight force in 0 of them.

## Agreement per variable

| Variable | With the hindsight truth | With the contemporaneous belief |
|---|---|---|
| `belief_force_USA` | 5/6 (83%) | 1/6 (17%) |
| `belief_USA_USSR` | n/a (no hindsight level: the swept hypothesis) | 6/6 (100%) |
| `belief_USSR_USA` | 6/6 (100%) | 6/6 (100%) |

## Flips: lag against the contemporaneous record

A documented flip is a change of the contemporaneous belief between consecutive 1 Januaries; a replayed flip is the same in the replay, dated by the proposal (treated as accepted) that set it. Matched within 2 years to the same level; lag is replay minus documented, in years (positive: the replay is late).

| Variable | Level | Documented (year) | Replayed (year, date) | Lag (years) |
|---|---|---|---|---|
| `belief_force_USA` | survivable | 1958 | none (missed) | - |
| `belief_force_USA` | few | 1962 | none (missed) | - |
| `belief_force_USA` | overkill | none (false flip) | 1957, 1956-03-06 | - |
| `belief_force_USA` | few | none (false flip) | 1958, 1957-01-15 | - |

## Disagreements and the indicators behind them

Every year in which the replay differs from the hindsight truth or from the contemporaneous belief, with the replay's latest proposal's (unreviewed) quote.

- `belief_force_USA`, 1957: replay `overkill` from 1956-03-06: "To destroy or neutralize US capabilities for nuclear warfare ... We have also estimated that by mid-1959 the USSR would have some 400 BISON and 300 BEAR aircraft in operational use."; hindsight few; contemporaneous few (manual replay).
- `belief_force_USA`, 1958: replay `few` from 1957-01-15: "The bomber force will probably consist of some 1,500 aircraft, ~eluding 700 BADGERS, 500 BISONS, and 300 BEARS."; hindsight few; contemporaneous survivable (manual replay).
- `belief_force_USA`, 1959: replay `few` from 1958-08-19: "The USSR will probably have a first operational capability with ten prototype ICBMs at some time during calendar 1959"; hindsight few; contemporaneous survivable (manual replay).
- `belief_force_USA`, 1960: replay `few` from 1959-11-03: "a few-say, l0--series produced ICBMs"; hindsight few; contemporaneous survivable (manual replay).
- `belief_force_USA`, 1961: replay `few` from 1960-08-01: "Operational ICBM Launchers 30 150 270 400"; hindsight few; contemporaneous survivable (manual replay).

---

## Claude report

PROPOSAL-LEVEL MEASUREMENT: no proposal below was reviewed. Every proposal the backend made was treated as if accepted to compute these metrics, no replay snapshot was written, and the levels and quotes below are the backend's unreviewed readings, not evidence accepted by a reviewer.

# Blind replay, CIA estimates 1957 to 1962, claude, projected-force reading, proposal level

- Years: 1957 to 1962 (6); the snapshot of a year is the state on its 1 January, read from the documents dated to the 31 December before.
- Corpus: crest, `data/cw/corpora/raw/crest`
- Backend: claude, model `claude-opus-5-5`, effort high
- Harness rules recorded: `two-document`, `no-retrospective`; the three belief variables are readings, outside both rules, so the rules act on nothing here.
- Review: none: proposal-level measurement (every proposal treated as accepted, nothing written)
- Command: `wf replay --episode cw --years 1957..1962 --out OUT --measure-proposals`
- Compared with: the hindsight snapshots in `snapshots/cw/hindsight/` (the truth of what each belief estimates, decisions D6) and the contemporaneous beliefs of the record (the manual replay snapshots in `snapshots/cw/replay/`, else the `belief` rows of `data/cw/events.csv`). Every variable but the beliefs is carried from the hindsight snapshot as `assumed`.

## Proposals per variable

Every proposal kept by the extractor's checks over the years, by level, and how the harness rules classified it.

| Variable | Proposals | By level | Shown and counted | Held: one document | First of two documents | Blocked: monotone, back | retrospective? (not counted) |
|---|---|---|---|---|---|---|---|
| `belief_force_USA` | 21 | few 16, survivable 4, overkill 1 | 21 | 0 | 0 | 0 | 0 |
| `belief_USA_USSR` | 6 | opportunist 6 | 6 | 0 | 0 | 0 | 0 |
| `belief_USSR_USA` | 0 | - | 0 | 0 | 0 | 0 | 0 |

## C6: the replayed estimate of the Soviet force against the hindsight force

Per year, the replayed `belief_force_USA` and the hindsight `nuke_USSR` (decisions R C6 (a): the replayed belief exceeds the hindsight force in every year 1958 to 1961), beside the contemporaneous belief of the record. These are inputs of C6; its parts (b) and (c) are computed on the model.

| Year | Replayed | Hindsight `nuke_USSR` | Replay exceeds | Contemporaneous (source) | Contemporaneous exceeds |
|---|---|---|---|---|---|
| 1957 | few | few | no | few (manual replay) | no |
| 1958 | few | few | no | survivable (manual replay) | yes |
| 1959 | few | few | no | survivable (manual replay) | yes |
| 1960 | few | few | no | survivable (manual replay) | yes |
| 1961 | survivable | few | yes | survivable (manual replay) | yes |
| 1962 | few | few | no | few (manual replay) | no |

Years 1958 to 1961 with a replay snapshot: 4 of 4; the replayed estimate exceeds the hindsight force in 1 of them.

## Agreement per variable

| Variable | With the hindsight truth | With the contemporaneous belief |
|---|---|---|
| `belief_force_USA` | 5/6 (83%) | 3/6 (50%) |
| `belief_USA_USSR` | n/a (no hindsight level: the swept hypothesis) | 6/6 (100%) |
| `belief_USSR_USA` | 6/6 (100%) | 6/6 (100%) |

## Flips: lag against the contemporaneous record

A documented flip is a change of the contemporaneous belief between consecutive 1 Januaries; a replayed flip is the same in the replay, dated by the proposal (treated as accepted) that set it. Matched within 2 years to the same level; lag is replay minus documented, in years (positive: the replay is late).

| Variable | Level | Documented (year) | Replayed (year, date) | Lag (years) |
|---|---|---|---|---|
| `belief_force_USA` | survivable | 1958 | none (missed) | - |
| `belief_force_USA` | few | 1962 | 1962, 1961-06-07 | +0 |
| `belief_force_USA` | few | none (false flip) | 1957, 1956-03-06 | - |
| `belief_force_USA` | survivable | none (false flip) | 1961, 1960-08-01 | - |

## Disagreements and the indicators behind them

Every year in which the replay differs from the hindsight truth or from the contemporaneous belief, with the replay's latest proposal's (unreviewed) quote.

- `belief_force_USA`, 1958: replay `few` from 1957-12-10: "some time duri.ng the period mid1958 to mid-1959, the USSR will probably have a first operational capability with up to 10 prototype ICBMs"; hindsight few; contemporaneous survivable (manual replay).
- `belief_force_USA`, 1959: replay `few` from 1958-12-23: "capable of large-scale attacks against the US only through the extensive use of medium bombers on one-way missions ... The USSR will probably achieve a first operational capability with 10 prototype ICBMs of 5,500 n.m. range at some time during 1959."; hindsight few; contemporaneous survivable (manual replay).
- `belief_force_USA`, 1960: replay `few` from 1959-11-03: "the initial operational capability (IOC) of a few-say, l0--series produced ICBMs. In light of all the evidence, we believe that for planning purposes it should be considered that the IOC will have occurred by 1 January 1960."; hindsight few; contemporaneous survivable (manual replay).
- `belief_force_USA`, 1961: replay `survivable` from 1960-12-01: "the USSR's emergence from strategic inequality, primarily through the buildup of an ICBM force ... we believe that they will build a substantial missile force"; hindsight few; contemporaneous survivable (manual replay).
