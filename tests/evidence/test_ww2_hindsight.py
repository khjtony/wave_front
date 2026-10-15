"""The WW2 v0 hindsight snapshots: the events file, the builder and the 21 committed files.

The built-ins section (phase 2 decision F2) is tested in tests/evidence/test_builtins_ww2.py."""

import copy
import json
import re
from datetime import date
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
        q: json.loads((SNAPSHOTS / f"{q}.json").read_text(encoding="utf-8"))
        for q in [h.TICK0, *h.QUARTERS]
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


def test_twenty_one_snapshots_and_nothing_else():
    assert sorted(p.stem for p in SNAPSHOTS.glob("*.json")) == sorted([h.TICK0, *h.QUARTERS])
    assert len(h.QUARTERS) == 20


def test_committed_snapshots_are_up_to_date(nmc_rows, events, committed):
    built = h.build_all(nmc_rows, events, decisions=h.load_decisions(), moves=h.load_moves())
    assert built == committed


# The clock-consistency pass (owner's decision 7 of 2026-10-15) on the v0 series.
CLOCK_CHANGES = [
    ("1938Q2", "belief_WEST", "limited", "uncertain", "b"),  # demand_sudeten; record Sep 1938
    ("1938Q3", "arms_GER", "rising", "high", "a"),  # the programme of Aug 1936; record Oct 1938
]


def test_the_variables_depend_on_the_built_ins_only_through_the_clock_pass(
    nmc_rows, events, committed
):
    """The built-ins are an added section, and the decision records and realized moves move
    a variable only through the clock-consistency pass: every other level, confidence and
    indicator is what the builder gives without them; each changed entry names its case and
    keeps the event-dated reading it overrides in its provenance."""
    bare = h.build_all(nmc_rows, events)
    changes = []
    built = h.build_all(
        nmc_rows, events, decisions=h.load_decisions(), moves=h.load_moves(), changes=changes
    )
    assert built == committed
    assert [
        (c["quarter"], c["variable"], c["before"], c["after"], c["case"]) for c in changes
    ] == CLOCK_CHANGES
    changed = {(c[0], c[1]) for c in CLOCK_CHANGES}
    for quarter, snap in committed.items():
        assert "builtins" not in bare[quarter]
        for name, entry in snap["variables"].items():
            if (quarter, name) in changed:
                ind = entry["indicators"][0]
                assert ind["id"] == f"clock_{quarter}_{name}"
                assert "overrides the event-dated reading" in ind["rule"]
                old = bare[quarter]["variables"][name]
                assert entry["level"] != old["level"]
                assert len(entry["indicators"]) == len(old["indicators"]) + 2
            else:
                assert entry == bare[quarter]["variables"][name], (quarter, name)
    rule = committed["1938Q3"]["variables"]["arms_GER"]["indicators"][0]["rule"]
    assert "case (a)" in rule and "1938-10-21" in rule and "tick 11" in rule


# -- the clock-consistency pass on a small fixture ---------------------------------------------


def _toy_clock():
    from wavefront.model import Bump, Model, Set, V

    m = Model("toy_clock", horizon=6)
    m.var("arms", levels=["low", "rising", "high"], init="low", monotone=True)
    m.flag("pact", init=False, monotone=True)
    a = m.actor("A", observes=V.all())
    b = m.actor("B", observes=V.all())
    m.nature()
    a.action("build", guard=V.arms < "high", effect=Bump("arms", 1), delay=1, source="s")
    b.action("sign", effect=Set("pact", True), source="s")
    return h.Clock(m.compile(), {})


TOY_VARIABLES = {
    "arms": h.Variable("arms", "level", ("low", "rising", "high"), "low", "2"),
    "pact": h.Variable("pact", "flag", (False, True), False, "4"),
}
TOY_QUARTERS = ["1935Q4", "1936Q1", "1936Q2", "1936Q3", "1936Q4"]


def _toy_series(arms, pact, pending):
    out = {}
    for q, x, f, p in zip(TOY_QUARTERS, arms, pact, pending, strict=True):
        day = h.quarter_bounds(q)[1].isoformat()

        def entry(name, level, day=day):
            ind = {"id": f"event_{day}_{name}", "value": f"{name} event", "source": "src"}
            ind |= {"observed": day, "rule": f"{name} read from the event"}
            return {"level": level, "confidence": "high", "indicators": [ind]}

        out[q] = {
            "date": day,
            "model": "toy_clock",
            "variables": {"arms": entry("arms", x), "pact": entry("pact", f)},
            "builtins": {
                "pending_A_build": {
                    "value": p,
                    "confidence": "assumed",
                    "indicators": [],
                    "rule": "fixture",
                }
            },
        }
    return out


def _toy_moves(sign_note=""):
    plays = [("build", "idle"), ("idle", "idle"), ("idle", "sign"), ("idle", "idle")]
    return [
        {"tick": str(k), "quarter": h.quarter_name(k), "A": x, "B": y, "Nature": "none"}
        | {"source": f"row {k}", "note": sign_note if y == "sign" else ""}
        for k, (x, y) in enumerate(plays)
    ]


TOY_DECISIONS = [h.Decision(date(1936, 2, 1), "1936Q1", "A", "build", 1, "src A", "")]


def test_fixture_clock_pass_both_cases():
    """Case (a): A's build of 1936Q1 with delay 1 lands in the transition into tick 2 (the
    end of 1936Q2), where the record still reads low and reads rising one quarter later.
    Case (b): B's sign of 1936Q3 sets the pact at once, where the record reads it from
    1936Q4. Both entries take the model's value; nothing else changes."""
    series = _toy_series(
        ["low", "low", "low", "rising", "rising"],
        [False, False, False, False, True],
        [0, 1, 0, 0, 0],
    )
    out, changes = h.clock_consistency(
        series, TOY_DECISIONS, _toy_moves(), _toy_clock(), TOY_VARIABLES
    )
    assert [(c["quarter"], c["variable"], c["before"], c["after"], c["case"]) for c in changes] == [
        ("1936Q2", "arms", "low", "rising", "a"),
        ("1936Q3", "pact", False, True, "b"),
    ]
    a = out["1936Q2"]["variables"]["arms"]
    assert (a["level"], a["confidence"]) == ("rising", "medium")
    assert a["indicators"][0]["id"] == "clock_1936Q2_arms"
    assert (
        a["indicators"][0]["observed"] == "1936-02-01" and a["indicators"][0]["source"] == "src A"
    )
    assert "case (a)" in a["indicators"][0]["rule"]
    assert (
        "overrides the event-dated reading arms = low at the end of 1936Q2"
        in (a["indicators"][0]["rule"])
    )
    assert "the record reaches rising on 1936-09-30" in a["indicators"][0]["rule"]
    assert a["indicators"][1]["id"] == "event_1936-09-30_arms"
    assert a["indicators"][2]["rule"].startswith("event-dated reading overridden")
    b = out["1936Q3"]["variables"]["pact"]
    assert b["level"] is True and "case (b)" in b["indicators"][0]["rule"]
    assert b["indicators"][0]["source"] == "row 2"
    for q in TOY_QUARTERS:
        for name in TOY_VARIABLES:
            if (q, name) not in {("1936Q2", "arms"), ("1936Q3", "pact")}:
                assert out[q]["variables"][name] == series[q]["variables"][name]


def test_fixture_clock_pass_exclusions():
    """Rule (c): a lag of two ticks, a record that leads the model, an [NSL] placement and
    the last quarter of a series (no next reading) stay as the record reads them."""
    clock = _toy_clock()
    two_ticks = _toy_series(["low", "low", "low", "low", "rising"], [False] * 5, [0, 1, 0, 0, 0])
    _, changes = h.clock_consistency(two_ticks, TOY_DECISIONS, _toy_moves(), clock, TOY_VARIABLES)
    assert changes == []
    leads = _toy_series(
        ["low", "rising", "rising", "rising", "rising"], [False] * 5, [0, 1, 0, 0, 0]
    )
    _, changes = h.clock_consistency(leads, TOY_DECISIONS, _toy_moves(), clock, TOY_VARIABLES)
    assert changes == []
    pact = _toy_series(
        ["low", "low", "rising", "rising", "rising"],
        [False, False, False, False, True],
        [0, 1, 0, 0, 0],
    )
    _, changes = h.clock_consistency(
        pact, TOY_DECISIONS, _toy_moves("sign [NSL]"), clock, TOY_VARIABLES
    )
    assert changes == []
    short = {q: pact[q] for q in TOY_QUARTERS[:4]}  # 1936Q3 is now the last quarter
    _, changes = h.clock_consistency(short, TOY_DECISIONS, _toy_moves(), clock, TOY_VARIABLES)
    assert changes == []


def test_committed_snapshots_are_valid(committed):
    for quarter, snap in committed.items():
        assert validate_snapshot(snap) == [], quarter
        assert h.check_against_ontology(snap) == [], quarter
        assert h.check_builtins(snap) == [], quarter
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
        "high",  # the planning-record definition, from the Oct 1938 directives (D12)
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
    assert "checked 21 snapshots" in capsys.readouterr().out


def test_cli_writes_and_detects_stale_files(tmp_path, capsys):
    assert h.main(["--out", str(tmp_path)]) == 0
    assert sorted(p.stem for p in tmp_path.glob("*.json")) == sorted([h.TICK0, *h.QUARTERS])
    (tmp_path / "1937Q1.json").write_text("{}", encoding="utf-8")
    assert h.main(["--out", str(tmp_path), "--check"]) == 1
    assert "1937Q1.json" in capsys.readouterr().err
