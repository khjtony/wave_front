# Cold War v0 snapshots

Built by `models/cw/snapshots.py` from `data/cw/events.csv` and `data/cw/decisions.csv`, in the format of `snapshots/schema.json`, for the model `cw_v0` ([docs/ontology_cw.md](../../docs/ontology_cw.md); decisions D6 and D7 of [docs/cw_v0_decisions.md](../../docs/cw_v0_decisions.md)).

```
python -m models.cw.snapshots --out snapshots/cw
python -m models.cw.snapshots --out snapshots/cw --check
```

- **`hindsight/<year>.json`, 1947 to 1992.** The state on **1 January** of the year: the model's state at tick `year - 1947` (`1947.json` is tick 0, `1992.json` the horizon). Every declared variable at the level of the record, with its indicator; the belief variables at the hindsight truth of what they estimate (D6); `aims_USSR` and `belief_USA_USSR` left out and fixed per hypothesis by `snapshot_state`. Built-ins: the pending delayed decisions (on 1 January 1947, `pending_USSR_build_bomb = 3`, the Soviet decision of 1945).
- **`replay/<year>.json`, 1957 to 1962 and 1983.** The manual replay (D7): the beliefs and the contemporaneous estimate of the Soviet force from documents dated before the snapshot's date; every other variable carried from the hindsight snapshot as `assumed`. Not the blind pipeline: its corpora are not reachable from the development environment (data/cw/README.md).

The hindsight snapshots and the model's realized path agree on every variable except the belief variables in the years of a documented belief error (1951 to 1953, 1958 to 1961, 1983 onwards); tests/coldwar/test_model_cw.py checks this.
