# WW2 v0 hindsight snapshots, 1936Q1 to 1940Q4

Twenty-one snapshots, one per quarter from 1936Q1 to 1940Q4 plus the tick-0 file `1935Q4.json`,
in the format of `snapshots/schema.json`, for the model `ww2_v0`
([docs/ontology_ww2.md](../../../docs/ontology_ww2.md)). Each gives every ontology variable's
level at the **end** of the quarter (`date` is the quarter's last day), read with full
knowledge of the record, and the model's built-in variables at that point (section
"Built-ins" below). They are the comparison target for the blind replay
([docs/ww2_testbed.md](../../../docs/ww2_testbed.md) section 8), not a replay themselves.

Regenerate and check:

```
python3 -m wavefront.evidence.hindsight_ww2 --out snapshots/ww2/hindsight
python3 -m wavefront.evidence.hindsight_ww2 --out snapshots/ww2/hindsight --check
```

The builder (`wavefront/evidence/hindsight_ww2.py`) validates each file with
`validate_snapshot`, against the ontology's variable and level names and against the model's
built-in names, and checks the decision records against the realized moves; tests check that
its variable list matches the ontology tables, its built-in list matches the compiled model,
and the files are up to date.

## End of quarter, not the model's tick-0 state

The snapshot named `1936Q1` is the state on 31 March 1936, after the Rhineland: on the
realized path it is the model's state at tick 1. The model's tick-0 initial state is the
ontology's `Init` column, which is the state on 1 January 1936; `build("1936Q1", ..., at="start")`
reproduces it exactly (a test checks this). Use the `at="start"` reading when a snapshot is to
be loaded as the initial state of quarter T; with the decision records and the realized moves it
carries the built-ins of the end of the quarter before.

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
`"aims_GER": {"level": "hegemonic", "confidence": "assumed", "indicators": []}`
(`models/ww2/hypotheses.py`, `snapshot_state`).

## Confidence

- `high`: a dataset value or a dated legal, diplomatic or military event (a treaty, an
  annexation, a declaration of war), and the pre-event level of a structural variable.
- `medium`: a reading that depends on a threshold: the NMC thresholds above, `arms_USSR`,
  `arms_JPN`, and the event readings that are a judgment among candidate dates or documents
  (`belief_WEST`, `belief_GER`, `commit_WEST`, `oil_GER`, `balkans`, `channel_air`), including a
  pre-event level read from a later confirming document.
- `assumed`: no dated indicator; the rule then says what is missing. No variable of the 21
  files needs it; the fairness counters among the built-ins are `assumed` by decision F2.

## Rates

`rearm_delay_ticks` (4) with a provisional basis sentence, to be refined by the historian.

## Tick mapping for the model

Tick 0 of `models/ww2/v0.py` is the start of 1936Q1. A file named for quarter Q holds the levels in force at the *end* of Q, which is the model's state at tick index(Q) + 1 (1936Q1 is tick 1, 1940Q4 is tick 20, the horizon). The file `1935Q4.json` holds the levels in force at the end of 1935Q4 (1935 annual capability values, every event dated up to 31 December 1935), which is the model's tick-0 initial state; `build_all` generates it with the other twenty. When a registered test says "from the 1939Q1 state", it means the state at the start of 1939Q1, which is the `1938Q4.json` file.

## Built-ins

Since phase 2 (decision F2 of [docs/phase2_kickoff.md](../../../docs/phase2_kickoff.md)) each
file has a `builtins` section that sets the model's built-in variables, each entry with a
`value`, a `confidence`, `indicators` in the provenance shape of the variables, and the `rule`
that derives the value. The loader (`wavefront/evidence/snapshot.py`) fills them into the
state after the variables and refuses unknown names and values out of range.
`snapshot_state(cm, quarter, aims, builtins=True)` in `models/ww2/hypotheses.py` loads them;
its default (`builtins=False`) drops the section and keeps the phase 1 convention under which
T1 to T13 were run (reports/ww2_v0.md section 2a).

| Built-in | Read from | Rule | Confidence |
|---|---|---|---|
| `pending_GER_rearm`, `pending_WEST_rearm`, `pending_USSR_rearm` | `data/ww2/decisions_ww2.csv` | `max(0, d - (index(Q) - index(t)))` for the latest decision of quarter t at or before Q, with the model's delay d (8, 4, 4); the rule shows the arithmetic and the tick at which the effect lands | `medium` (the delay is a model parameter); `high` for 0 when no decision precedes Q |
| `last_GER`, `last_WEST` | `data/ww2/realized_moves.csv` | the actor's realized move of Q; `none` in `1935Q4.json` (tick 0) | `high`; `medium` for `idle` (a reading of the record) and for a move placed one quarter late [SQR] |
| `belief_at_munich` | `data/ww2/events_ww2.csv` | `unset` before the quarter of the Sudetenland cession (30 Sep 1938); from 1938Q3 on, the `belief_WEST` in force at the end of 1938Q3 (`uncertain`) | `high` while unset; `medium` after (the belief reading is a judgment) |
| `fair_democratic_response`, `fair_czech_obligation`, `fair_rhineland_resolution` | none | 0, by decision F2 | `assumed` |

The decision records (`data/ww2/decisions_ww2.csv`), one row per dated decision of a delayed
action in the realized record, sourced as the action catalogue and `realized_moves.csv`
source them:

| Date | Quarter (tick) | Decision | Delay | Pending at the end of each quarter |
|---|---|---|---|---|
| 3 Mar 1936 | 1936Q1 (0) | WEST `rearm`: Defence Requirements programme, Cmd. 5107 | 4 | 4, 3, 2, 1 in 1936Q1 to 1936Q4; lands at tick 5 |
| 24 Aug 1936 | 1936Q3 (2) | GER `rearm`: Four-Year Plan memorandum and army programme (Aug 1936) | 8 | 8 in 1936Q3 down to 1 in 1938Q2; lands at tick 11 (end of 1938Q3) |
| 14 Oct 1938 | 1938Q4 (11) | GER `rearm`: Goering's conference (1301-PS) | 8 | 8 in 1938Q4 down to 1 in 1940Q3; lands at tick 20 |
| 30 Nov 1938 (month precision) | 1938Q4 (11) | WEST `rearm`: post-Munich decisions and French decree-laws | 4 | 4 in 1938Q4 down to 1 in 1939Q3; lands at tick 16 |
| 7 May 1940 | 1940Q2 (17) | USSR `rearm`: Timoshenko's appointment after the Finnish-war conference | 4 | 4, 3, 2 in 1940Q2 to 1940Q4; lands after the horizon |

The builder refuses a decision taken while an earlier one of the same action is still pending
(the model makes the action unavailable then) and a decision row that is not a realized move
of its quarter, or the reverse.

## Replay against the snapshots

`tests/evidence/test_builtins_ww2.py` loads every file, with its built-ins and the hidden
objectives fixed, into `models/ww2/v0.py` under both hypotheses, and compares the loaded state,
variable by variable and built-in by built-in, with the state the model reaches at tick
index(Q) + 1 when `data/ww2/realized_moves.csv` is replayed with `cm.step` from the tick-0
state. Under hegemonic aims the replay runs to the horizon; under revisionist aims it stops at
tick 12, where `occupy_bohemia` is closed by its hypothesis gate, and the comparison covers the
files to `1938Q4.json`.

Every pending counter, last action and latch value agrees with the replay in every file. The
differences, each listed in the test with its reason, are:

| Variable | Files | Snapshot | Replay | Why |
|---|---|---|---|---|
| `treaty` | 1936Q1, 1936Q2 | dead | eroded | `locarno_lapses` is placed at tick 2 [SQR]; the record dates the lapse 7 to 19 Mar 1936 |
| `arms_WEST` | 1936Q3, 1936Q4 | rising | low | the NMC reading turns `rising` with the French programme (Sep 1936); the model's delay-4 effect of the Mar 1936 decision lands at tick 5 (1937Q1) |
| `china_war` | 1937Q3 to 1940Q4 | True | False | the China incident (7 Jul 1937) is not in the realized moves: Nature may decline it (owner's decision of 2026-10-12) and the file records `none` |
| `belief_WEST` | 1938Q2 | limited | uncertain | `demand_sudeten` is placed at tick 9 (Case Green, 30 May 1938) and raises the belief at once; the record moves the belief with the public demand of September (1938Q3) |
| `arms_GER` | 1938Q3 | rising | high | the 1936 programme lands at tick 11 under delay 8; the planning record reads `high` from 21 Oct 1938 (decisions D12), one tick later |
| `arms_USSR` | 1938Q4 to 1940Q4 | strong | weak | the record restores `strong` with the decree of Nov 1938; in the model only USSR `rearm` restores it, decided in 1940Q2 and landing after the horizon |
| `arms_WEST` | 1939Q1 to 1939Q3 | high | rising | NMC 1939 reads `high` from 1939Q1 (the 1939 figures include the wartime mobilization); the Oct to Nov 1938 decision lands at tick 16 (1939Q4) |
| `commit_WEST`, `polish_guarantee` | 1939Q1 | resolved, True | wary, False | `guarantee_poland` is placed at tick 13 [SQR]; the record dates it 31 Mar 1939 |
| `fair_democratic_response` | 1939Q1 | 0 | 1 | fairness counters are assumed 0 (F2); on the replay the trigger (belief hegemonic, `commit_WEST` wary, Poland independent) holds at tick 13 after a non-response (`approach_ussr`), so the counter is 1. The one built-in difference |
| `belief_GER` | 1939Q2 to 1940Q4 | uncertain, will_fight | will_not_fight | constant in v0 (decisions D6, reduction 1); the record moves it in 1939 |
| `oil_GER` | 1939Q3, 1939Q4 | dependent | secured | `accept_pact` secures oil at once (tick 15); the record reads `secured` from the economic agreement of Feb 1940 |
| `poland` | 1939Q3 | partitioned | german | `occupy_east_poland` is placed at tick 15 [SQR]; the record dates it 17 Sep 1939 |
| `balkans` | 1940Q3 | german_aligned | neutral | `align_balkans` is placed at tick 19; the record dates the alignment 30 Aug 1940 |
| `arms_GER` | 1940Q4 | high | total | the Oct 1938 programme lands at tick 20 under delay 8 and bumps `high` to `total`; the record reads no full war economy before 1941 |

None of these is a defect of the built-ins: the variable differences are the snapshot readings
and the model's placement of the realized moves disagreeing, as they did before phase 2 (the
built-ins did not change any variable level). The one at the 1938Q3 file matters for the
amended T8(b) (reports/ww2_v0.md section 14): the 1938Q3 file reads `arms_GER` `rising` and,
since the 1936 programme has landed by then, carries no pending German rearmament.
