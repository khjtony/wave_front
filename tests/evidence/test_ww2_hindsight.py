"""The WW2 v0 hindsight snapshots: the events file, the builder and the 20 committed files."""

import copy
import json
import re
from pathlib import Path

import pytest

from wavefront.evidence import hindsight_ww2 as h
from wavefront.evidence import validate_snapshot
from wavefront.evidence.datasets import nmc

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOTS = ROOT / "snapshots" / "ww2" / "hindsight"
SCHEMA = ROOT / "snapshots" / "schema.json"
ONTOLOGY = ROOT / "docs" / "ontology_ww2.md"
EVENTS = ROOT / "data" / "ww2" / "events_ww2.csv"


@pytest.fixture(scope="module")
def nmc_rows():
    return nmc.load(ROOT / "data" / "ww2" / "nmc_1936_1940.csv")


@pytest.fixture(scope="module")
def events():
    return h.load_events(EVENTS)


@pytest.fixture(scope="module")
def committed():
    return {
        q: json.loads((SNAPSHOTS / f"{q}.json").read_text(encoding="utf-8")) for q in h.QUARTERS
    }


# -- the ontology ----------------------------------------------------------------------------


def test_builder_variables_match_the_ontology_tables():
    assert h.ontology_mismatches(ONTOLOGY) == []
    doc = h.parse_ontology(ONTOLOGY)
    assert set(doc) == {v.name for v in h.VARIABLES} | set(h.HIDDEN)


def test_start_of_1936q1_is_the_ontology_initial_state(nmc_rows, events):
    snap = h.build("1936Q1", nmc_rows, events, at="start")
    assert snap["date"] == "1936-01-01"
    assert {k: v["level"] for k, v in snap["variables"].items()} == {
        v.name: v.init for v in h.VARIABLES
    }


# -- the events file -------------------------------------------------------------------------

# (date, variable, level) for the events every snapshot series must carry.
REQUIRED_EVENTS = [
    ("1936-03-07", "rhineland", "remilitarized"),
    ("1936-10-23", "axis", True),
    ("1936-11-25", "anticomintern", True),
    ("1937-06-11", "arms_USSR", "weak"),
    ("1938-03-12", "austria", "annexed"),
    ("1938-05-20", "belief_WEST", "limited"),
    ("1938-09-12", "belief_WEST", "uncertain"),
    ("1938-09-30", "sudeten", "german"),
    ("1939-03-15", "bohemia", "german"),
    ("1939-03-17", "belief_WEST", "hegemonic"),
    ("1939-03-31", "polish_guarantee", True),
    ("1939-04-26", "commit_WEST", "resolved"),
    ("1939-05-22", "axis", True),
    ("1939-08-23", "nazi_soviet_pact", True),
    ("1939-09-01", "poland", "independent"),
    ("1939-09-03", "war_west_ger", "war"),
    ("1939-09-17", "poland", "partitioned"),
    ("1939-11-04", "commit_US", "wary"),
    ("1940-05-10", "france", "at_war"),
    ("1940-05-28", "britain", "at_war"),
    ("1940-06-22", "france", "fallen"),
    ("1940-07-10", "channel_air", "contested"),
    ("1940-08-30", "balkans", "german_aligned"),
    ("1940-09-02", "commit_US", "engaged"),
    ("1940-09-27", "axis", True),
    ("1940-10-31", "channel_air", "british"),
    ("1940-11-13", "ussr_axis", False),
]


def test_events_cover_the_required_list(events):
    present = {(e.date.isoformat(), e.variable, e.level) for e in events}
    assert [r for r in REQUIRED_EVENTS if r not in present] == []


def test_events_are_well_formed(events):
    assert [e.date for e in events] == sorted(e.date for e in events)
    for e in events:
        assert 1935 <= e.date.year <= 1940
        assert e.quarter == h.quarter_of(e.date)
        assert e.level in h.BY_NAME[e.variable].levels
        if e.uncertain:
            assert e.note, f"{e.date} {e.variable}: a '?' source needs a note"
    text = EVENTS.read_text(encoding="utf-8")
    assert not re.search(r"\bpp?\.\s*\d", text), "no page numbers in event sources"


def test_every_event_read_variable_has_a_row(events):
    derived = {"arms_JPN", "ind_GER"}
    have = {e.variable for e in events}
    assert [v.name for v in h.VARIABLES if v.name not in derived and v.name not in have] == []


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ("1936-03-07,1936Q1,nonesuch,x,e,s,", "not a WW2 v0 ontology variable"),
        ("1936-03-07,1936Q1,rhineland,occupied,e,s,", "not one of"),
        ("1936-03-07,1936Q2,rhineland,remilitarized,e,s,", "does not match"),
        ("1936-03-07,1936Q1,axis,yes,e,s,", "True or False"),
        ("1936-03-07,1936Q1,rhineland,remilitarized,e,,", "must not be empty"),
    ],
)
def test_load_events_rejects_bad_rows(tmp_path, row, message):
    path = tmp_path / "events.csv"
    path.write_text(",".join(h.EVENT_COLUMNS) + "\n" + row + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        h.load_events(path)


def test_quarter_bounds():
    assert [d.isoformat() for d in h.quarter_bounds("1936Q1")] == ["1936-01-01", "1936-03-31"]
    assert [d.isoformat() for d in h.quarter_bounds("1940Q4")] == ["1940-10-01", "1940-12-31"]
    with pytest.raises(ValueError):
        h.quarter_bounds("1936Q5")


# -- the committed snapshots -----------------------------------------------------------------


def test_twenty_snapshots_and_nothing_else():
    assert sorted(p.stem for p in SNAPSHOTS.glob("*.json")) == list(h.QUARTERS)
    assert len(h.QUARTERS) == 20


def test_committed_snapshots_are_up_to_date(nmc_rows, events, committed):
    assert h.build_all(nmc_rows, events) == committed


def test_committed_snapshots_are_valid(committed):
    for quarter, snap in committed.items():
        assert validate_snapshot(snap) == [], quarter
        assert h.check_against_ontology(snap) == [], quarter
        assert snap["model"] == "ww2_v0"
        assert snap["date"] == h.quarter_bounds(quarter)[1].isoformat()
        assert not any(name.startswith("aims_") for name in snap["variables"])
        assert set(snap["rates"]) == {"rearm_delay_ticks"}
        assert snap["rates"]["rearm_delay_ticks"]["basis"]


def test_committed_snapshots_satisfy_the_json_schema(committed):
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    for snap in committed.values():
        jsonschema.Draft202012Validator(schema).validate(snap)


def test_nmc_indicators_are_flagged_as_interpolated(committed):
    seen = 0
    for quarter, snap in committed.items():
        for entry in snap["variables"].values():
            for ind in entry["indicators"]:
                if ind["id"].startswith("nmc_"):
                    seen += 1
                    assert h.INTERPOLATED in ind["rule"]
                    assert isinstance(ind["value"], int)
                    assert ind["observed"] == f"{quarter[:4]}-12-31"
                    assert "version 7.0" in ind["source"]
    assert seen >= 20 * 8


def test_confidence_policy(committed):
    for snap in committed.values():
        for name, entry in snap["variables"].items():
            assert entry["indicators"], name
            if entry["confidence"] == "assumed":
                assert any("Missing:" in i["rule"] for i in entry["indicators"]), name
            if name in ("arms_GER", "arms_WEST"):
                assert entry["confidence"] == "medium"


def test_aims_are_left_to_the_analysis(committed):
    snap = copy.deepcopy(committed["1938Q3"])
    snap["variables"]["aims_GER"] = {
        "level": "hegemonic",
        "confidence": "assumed",
        "indicators": [],
    }
    assert validate_snapshot(snap) == []
    assert h.check_against_ontology(snap) == [
        "aims_GER is swept by the model and must not be fixed"
    ]


# The realized path as read from the record (levels at each quarter's end).
REALIZED = {
    "1936Q1": {"rhineland": "remilitarized", "treaty": "dead", "arms_WEST": "low", "ind_GER": 3},
    "1936Q3": {"arms_WEST": "rising", "axis": False},
    "1936Q4": {"axis": True, "anticomintern": True, "arms_USSR": "strong"},
    "1937Q2": {"arms_USSR": "weak"},
    "1938Q1": {"austria": "annexed", "ind_GER": 4, "belief_WEST": "limited"},
    "1938Q3": {"sudeten": "german", "belief_WEST": "uncertain", "commit_WEST": "wary"},
    "1939Q1": {
        "bohemia": "german",
        "ind_GER": 5,
        "belief_WEST": "hegemonic",
        "polish_guarantee": True,
        "commit_WEST": "resolved",
        "arms_GER": "high",
    },
    "1939Q3": {
        "nazi_soviet_pact": True,
        "poland": "partitioned",
        "war_west_ger": "war",
        "france": "at_war",
        "britain": "at_war",
        "commit_WEST": "at_war",
        "anglo_soviet_alliance": False,
    },
    "1939Q4": {"commit_US": "wary"},
    "1940Q1": {"oil_GER": "secured"},
    "1940Q2": {"france": "fallen", "britain": "at_war", "channel_air": "contested"},
    "1940Q3": {"balkans": "german_aligned", "commit_US": "engaged"},
    "1940Q4": {"channel_air": "british", "ussr_axis": False, "siberia": "soviet"},
}


@pytest.mark.parametrize("quarter", sorted(REALIZED))
def test_realized_levels(committed, quarter):
    levels = {k: v["level"] for k, v in committed[quarter]["variables"].items()}
    assert {k: levels[k] for k in REALIZED[quarter]} == REALIZED[quarter]


# -- the NMC threshold rules -----------------------------------------------------------------


def test_arms_thresholds_follow_the_rules(nmc_rows, events):
    def level(quarter, var, rules=h.ONTOLOGY_RULES, rows=nmc_rows):
        return h.build(quarter, rows, events, rules)["variables"][var]["level"]

    assert [level(f"{y}Q4", "arms_GER") for y in range(1936, 1941)] == [
        "rising",
        "rising",
        "rising",
        "high",
        "high",
    ]
    assert [level(f"{y}Q4", "arms_WEST") for y in range(1936, 1941)] == [
        "rising",
        "rising",
        "rising",
        "high",
        "high",
    ]
    # The western gate: the French programme of September 1936.
    assert level("1936Q2", "arms_WEST") == "low"
    # A lower personnel threshold moves the German reading; the rule, not the date, decides.
    lower = copy.deepcopy(h.ONTOLOGY_RULES)
    lower["arms_GER"]["high_milper_min"] = 700
    assert level("1938Q4", "arms_GER", lower) == "high"
    # Falling expenditure with conscription in force reads low.
    falling = [dict(r) for r in nmc_rows]
    for r in falling:
        if r["ccode"] == 255 and r["year"] == 1937:
            r["milex"] = 1
    assert level("1937Q4", "arms_GER", rows=falling) == "low"


def test_missing_nmc_year_is_an_error(nmc_rows, events):
    rows = [r for r in nmc_rows if not (r["ccode"] == 255 and r["year"] == 1937)]
    with pytest.raises(ValueError, match="no row for ccode 255, year 1937"):
        h.build("1937Q1", rows, events)


# -- the command line ------------------------------------------------------------------------


def test_cli_check_passes_on_the_committed_files(capsys):
    assert h.main(["--out", str(SNAPSHOTS), "--check"]) == 0
    assert "checked 20 snapshots" in capsys.readouterr().out


def test_cli_writes_and_detects_stale_files(tmp_path, capsys):
    assert h.main(["--out", str(tmp_path)]) == 0
    assert sorted(p.stem for p in tmp_path.glob("*.json")) == list(h.QUARTERS)
    (tmp_path / "1937Q1.json").write_text("{}", encoding="utf-8")
    assert h.main(["--out", str(tmp_path), "--check"]) == 1
    assert "1937Q1.json" in capsys.readouterr().err
