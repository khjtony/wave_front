# Cold War testbed data

Inputs to the Cold War v0 model (`models/cw/v0.py`), its hindsight and replay snapshots (`snapshots/cw/`, built by `models/cw/snapshots.py`) and the realized replay of claim C1 ([docs/coldwar_testbed.md](../../docs/coldwar_testbed.md); [docs/cw_v0_decisions.md](../../docs/cw_v0_decisions.md)).

## Files

| File | What | Written from |
|---|---|---|
| `events.csv` | dated levels, one row per event and variable: `record` rows (the hindsight record, read by the hindsight snapshots), `belief` rows (the contemporaneous beliefs, the model's realized path and the replay snapshots), `replay` rows (a contemporaneous reading of a non-belief variable that the record corrects: the estimated Soviet ICBM force of 1957 to 1961) | the sources in its `source` column |
| `decisions.csv` | the dated decisions of the realized path with their delays (years), including the Soviet atomic decision of 1945, before tick 0 | the sources in its `source` column |
| `realized_moves.csv` | the realized joint move of every year, 1947 to 1991 (tick 0 to 44), with the placement notes ([SQR], [NSL], one decision per actor per year) | maintained with the decisions file |
| `crises/<name>/realized_moves.csv` | the realized moves of the three sub-games (Berlin 1948 by week, Cuba 1962 and Able Archer 1983 by day) | as above |
| `v1/events.csv`, `v1/decisions.csv` | Cold War v1's additions (`models/cw/v1.py`): the US-PRC war, the 1973 return, the Korean entry and Brezhnev's message of 1973; read together with the v0 files by `models/cw/snapshots_v1.py` | the sources in their `source` columns |
| `v1/realized_moves.csv` | v1's realized joint moves (v0's with 1951 and 1973 changed) | docs/cw_v1_decisions.md D5 |
| `crises/sino_soviet_1969/`, `crises/alert_1973/` | the realized moves of v1's two sub-games (by week and by day) | as above |

## The data sets the testbed names, and why none is read here

coldwar_testbed.md section 6.1 names the Correlates of War National Material Capabilities, the Kristensen and Norris nuclear inventories (FAS; the Bulletin of the Atomic Scientists), the NRDC databook and SIPRI, ICB and MID, the Maddison Project with the post-1991 revisions, and Polity; section 6.2 the replay corpora (FRUS, CIA CREST with the NIE series, the Wilson Center Digital Archive, the National Security Archive). On 2026-10-17 the development environment's network policy refused every one of these hosts (correlatesofwar.org, fas.org, thebulletin.org, www.cia.gov, history.state.gov, maddisonproject.org and rug.nl, dataverse.nl, zenodo.org), and the GitHub data mirror the WW2 work used (`peacesciencer`) as well.

So no level of v0 is read from a downloaded series. The ontology's thresholds are stated on the record of deployments, treaties and events, which the historiography in each row's `source` dates; where a level would be cross-checked against a series (the year the Soviet force became survivable against the inventories, the dating of the Soviet slowdown against the revised GDP series) the row says "not verified". When the hosts can be reached the cross-checks to run are: `nuke_*` against Norris and Kristensen, "Global nuclear weapons inventories, 1945-2010" (BAS 66(4), 2010) and Podvig (ed.) 2001; `econ_USSR` against Maddison and Khanin's revisions; the replay against the NIE series in CREST (the blind replay of docs/replay_harness.md).

## Conventions

- `year` is the year of the decision or event; `tick = year - 1947`. `visible_year` (`visible_tick`) is the first 1 January showing the level: the next year for an event of the year, later for a delayed decision.
- An initial level (visible 1947) is a `record` row with `year` 1946.
- tests/coldwar/test_model_cw.py checks that every `record` row of a non-belief variable and every `belief` row is the level on the model's realized path at its `visible_tick`, and that the decisions file is the realized moves file.
