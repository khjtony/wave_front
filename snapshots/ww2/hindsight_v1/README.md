# WW2 v1 hindsight snapshots, 1936Q1 to 1945Q3

Forty snapshots in the format of `snapshots/schema.json` for the model `ww2_v1`
(`models/ww2/v1.py`; [docs/ontology_ww2_v1.md](../../../docs/ontology_ww2_v1.md) as deltas
on [docs/ontology_ww2.md](../../../docs/ontology_ww2.md)): the tick-0 file `1935Q4.json` and one
file per quarter from 1936Q1 to 1945Q3. Each gives every ontology variable's level at the
**end** of the quarter, read with full knowledge of the record, and the model's built-in
variables at that point. The file named for quarter Q is the model's state at tick
index(Q) + 1; "from state Q" in a registered test is the state at the start of Q, which is
the file of the quarter before (decisions E1).

Regenerate and check (the v0 files in `snapshots/ww2/hindsight/` are built by the v0 builder
and are unchanged):

```
python3 -m wavefront.evidence.hindsight_ww2_v1 --out snapshots/ww2/hindsight_v1
python3 -m wavefront.evidence.hindsight_ww2_v1 --out snapshots/ww2/hindsight_v1 --check
```

## Inputs

| Input | For |
|---|---|
| `data/ww2/nmc_1936_1940.csv` (years to 1940), `data/ww2/nmc_1941_1945.csv` (1941 to 1945; `scripts/fetch_ww2_data.py --extract v1`) | `arms_GER`, `arms_WEST`, `arms_USA` (rules below); `arms_USSR`, `arms_JPN`, `ind_GER` as supporting or context indicators |
| `data/ww2/events_ww2.csv`, `data/ww2/events_ww2_v1.csv` | every structural, region, belief and commitment variable, as in v0 |
| `data/ww2/decisions_ww2_v1.csv` | the pending counters (kickoff F2's formula); a row whose quarter is the one after its date's is accepted only when its note says `[SQR]`, and its quarter (the model tick) is used |
| `data/ww2/realized_moves_v1.csv` | `last_GER`, `last_WEST`, `last_USSR`; the flags `midway_ordered`, `east_feeler`, `east_peace`, which only a modeled decision sets and no event row carries |
| both ontology documents | checked against the builder's variable list (header-aware: bold level additions, `(v0)` labels) |

## Rules added for v1

| Variable | Rule |
|---|---|
| `arms_GER` | v0's rule, and `total` from the dated planning record (Speer's appointment, 8 Feb 1942), as v0 reads `high` (decisions D12) |
| `arms_WEST` | v0's rule. For 1943 NMC has no row for France: the United Kingdom's `milex` alone is a lower bound of the combined value and already meets the threshold, so the level is `high` without the missing value; the rule says so |
| `arms_USA` | **provisional, for the historian's review** (decisions E7): `high` if NMC `milper` (ccode 2) is at least 5,000 thousand; `rising` if the programme event of 19 Jul 1940 is in force and `milex` is above the previous year's; otherwise `low`. The planning date for `high` (1 Jul 1943) is shown as a cross-check |
| `mob_USSR`, `exhaustion_GER`, `oil_JPN`, `air_west` | events, confidence `medium` (the events file calls them threshold readings) |
| fairness counters | **computed** along the realized path (decisions E1): `min(previous + 1, within)` when the trigger holds on the snapshot's own end-of-quarter levels (with the quarter's last actions) and the actor's realized move is not a response, else 0. The oil clock reads 1 at the end of 1941Q3, 2 at the end of 1941Q4 and 0 from 1942Q1 |

## Gaps (flagged, not filled)

The builder reports the NMC gaps its readings met: France 1942 (`milper` missing) and France
1943 (no row: COW system membership gap during the occupation). The v1 extract's header lists
every gap of the extract (also the Netherlands 1941 to 1944, context only). Germany and Japan
have NMC rows for 1945 and Italy for 1943 to 1945, so no reading of the model's variables
needed them filled.

## Against the realized replay

`tests/ww2/test_model_ww2_v1.py` replays `data/ww2/realized_moves_v1.csv` from the tick-0 state
(aims_GER hegemonic, aims_JPN regional or hegemonic) and compares the state at the end of each
quarter with the file, built-ins included. The differences, each with its reason, are listed in
`EXPECTED_DIFFERENCES` there and tabulated in `reports/ww2_v1.md` section 3: the v0 ones
(one-tick [SQR] lags, the NMC readings of `arms_WEST`, the purge's end in Nov 1938), the
[NSL] placements (`italy` at 1940Q1, `exhaustion_GER` at 1944Q3), the two one-year
discrepancies of decisions E2 item 9 (`arms_GER` total from 1940Q4; `arms_USSR` strong in the
model only from 1941Q2), the American programme against the NMC annual figures (`arms_USA`),
the alliance written as an effect of the attack (`anglo_soviet_alliance` at 1941Q2), the
[SQR] German declaration and Midway, the Caucasus and the Prut by a quarter, the bomb ready
at the start of 1945Q3 against Trinity in July, and the democratic-response counter at 1939Q1
(the snapshot reads the guarantee of 31 Mar 1939; the replay has it a tick later). Pending
counters, last actions, the latch and the oil clock agree everywhere.

## The hidden objectives are not fixed

`aims_GER`, `aims_USSR` and `aims_JPN` are omitted, as in v0; `snapshot_state(cm, quarter,
aims_GER, snapshots=SNAPSHOTS_V1, aims_JPN=...)` in `models/ww2/hypotheses.py` adds them as
`assumed` entries per hypothesis.
