# WW2 v0 hindsight snapshots, 1936Q1 to 1940Q4

Twenty snapshots, one per quarter, in the format of `snapshots/schema.json`, for the model
`ww2_v0` ([docs/ontology_ww2.md](../../../docs/ontology_ww2.md)). Each gives every ontology
variable's level at the **end** of the quarter (`date` is the quarter's last day), read with
full knowledge of the record. They are the comparison target for the blind replay
([docs/ww2_testbed.md](../../../docs/ww2_testbed.md) section 8), not a replay themselves.

Regenerate and check:

```
python3 -m wavefront.evidence.hindsight_ww2 --out snapshots/ww2/hindsight
python3 -m wavefront.evidence.hindsight_ww2 --out snapshots/ww2/hindsight --check
```

The builder (`wavefront/evidence/hindsight_ww2.py`) validates each file with
`validate_snapshot` and against the ontology's variable and level names; a test checks that
its variable list matches the ontology tables and that the files are up to date.

## End of quarter, not the model's tick-0 state

The snapshot named `1936Q1` is the state on 31 March 1936, after the Rhineland: on the
realized path it is the model's state at tick 1. The model's tick-0 initial state is the
ontology's `Init` column, which is the state on 1 January 1936; `build("1936Q1", ..., at="start")`
reproduces it exactly (a test checks this). Use the `at="start"` reading when a snapshot is to
be loaded as the initial state of quarter T.

## Provenance

- **Resource variables** (`arms_GER`, `arms_WEST`, `arms_JPN`; `arms_USSR` and `ind_GER` as
  supporting or cross-check indicators) come from `data/ww2/nmc_1936_1940.csv`, Correlates of
  War NMC version 7.0, obtained through the `peacesciencer` mirror (see
  `data/ww2/README.md`). NMC is annual. **Every NMC indicator is interpolated: the year's
  value is carried to each of its quarters, and its `rule` ends with
  `interpolated: annual value carried to the quarter`.** Its `observed` date is 31 December of
  that year, which is later than the snapshot date for the first three quarters: the reading
  uses the whole year's figure. The 1939 figures in particular include the wartime
  mobilization from September, so the 1939Q1 and 1939Q2 readings of `arms_GER` and `arms_WEST`
  (`high`) anticipate it.
- **Structural, region, pact, belief and commitment variables** come from
  `data/ww2/events_ww2.csv`: the level set by the latest dated event at or before the quarter's
  end, with the event and its source as the indicator (and the later confirming event, if
  any). Before a variable's first event the level is the ontology's initial level, cited with
  the first dated event that changes or confirms it.
- **`ind_GER`** is 3 + 1 with Austria annexed + 1 with Bohemia german (ontology section 2),
  with the two region events as indicators and NMC `irst` as a cross-check. It is written as
  an integer.

The provisional thresholds (not part of the ontology; listed in `ONTOLOGY_RULES` for the
historian's review):

| Variable | Rule |
|---|---|
| `arms_GER` | `high` if NMC `milper` >= 1000 thousand; `rising` if conscription is in force (16 March 1935) and `milex` is above the previous year's; otherwise `low`; `total` is never read from NMC |
| `arms_WEST` | `high` if UK + France `milex` >= 3 times its 1935 value; `rising` if both rearmament programmes are in force (French programme, September 1936) and the combined `milex` is above the previous year's; otherwise `low` |
| `arms_USSR` | `weak` from the Tukhachevsky trial (June 1937) to the decree ending the mass operations (November 1938); `strong` otherwise (a literal reading of the ontology; NMC `milper` shown as context) |
| `arms_JPN` | fixed at `high` in v0 |

## The hidden objectives are not fixed

`aims_GER` and `aims_USSR` are swept by the model (ontology section 1) and are omitted. A
snapshot that fixed them would assert a historiographical hypothesis as an observation.
Per-hypothesis analysis fixes them by adding one entry with `confidence: "assumed"` to a copy
of the snapshot, for example
`"aims_GER": {"level": "hegemonic", "confidence": "assumed", "indicators": []}`. The latches
(`belief_at_munich`, `arms_at_war`) are built-ins set by the loader.

## Confidence

- `high`: a dataset value or a dated legal, diplomatic or military event (a treaty, an
  annexation, a declaration of war), and the pre-event level of a structural variable.
- `medium`: a reading that depends on a threshold: the NMC thresholds above, `arms_USSR`,
  `arms_JPN`, and the event readings that are a judgment among candidate dates or documents
  (`belief_WEST`, `belief_GER`, `commit_WEST`, `oil_GER`, `balkans`, `channel_air`), including a
  pre-event level read from a later confirming document.
- `assumed`: no dated indicator; the rule then says what is missing. None of the current 20
  files needs it.

## Rates

`rearm_delay_ticks` (4) with a provisional basis sentence, to be refined by the historian.

## Tick mapping for the model

Tick 0 of `models/ww2/v0.py` is the start of 1936Q1. A file named for quarter Q holds the levels in force at the *end* of Q, which is the model's state at tick index(Q) + 1 (1936Q1 is tick 1, 1940Q4 is tick 20, the horizon). The file `1935Q4.json` holds the levels in force at the end of 1935Q4 (1935 annual capability values, every event dated up to 31 December 1935), which is the model's tick-0 initial state; `build_all` generates it with the other twenty. When a registered test says "from the 1939Q1 state", it means the state at the start of 1939Q1, which is the `1938Q4.json` file.
