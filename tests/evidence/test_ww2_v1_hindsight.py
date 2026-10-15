"""The WW2 v1 hindsight snapshots (decisions E1 and E7): the builder
(wavefront/evidence/hindsight_ww2_v1.py), its inputs and the 40 committed files.

The comparison of the files with the model's realized replay is in
tests/ww2/test_model_ww2_v1.py (it needs the model); here the builder is checked against its
documents and data, and its arithmetic on small fixtures."""

import json
from datetime import date
from pathlib import Path

import pytest

from wavefront.evidence import hindsight_ww2 as h0
from wavefront.evidence import hindsight_ww2_v1 as h
from wavefront.evidence import validate_snapshot
from wavefront.evidence.datasets import nmc

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOTS = ROOT / "snapshots" / "ww2" / "hindsight_v1"
FILES = [h.TICK0, *h.QUARTERS]


@pytest.fixture(scope="module")
def inputs():
    return {
        "nmc_rows": h.load_nmc(),
        "events": h.load_events(),
        "decisions": h.load_decisions(),
        "moves": h.load_moves(),
    }


@pytest.fixture(scope="module")
def built(inputs):
    return h.build_all(**inputs)


@pytest.fixture(scope="module")
def committed():
    return {q: json.loads((SNAPSHOTS / f"{q}.json").read_text(encoding="utf-8")) for q in FILES}


# -- documents and inputs --------------------------------------------------------------------


def test_builder_variables_match_both_ontology_documents():
    """Header-aware: the v1 document's bold level additions and (v0) labels are read."""
    assert h.ontology_mismatches() == []
    doc = h.parse_ontology()
    assert doc["commit_US"]["levels"] == ("isolationist", "wary", "engaged", "total")
    assert doc["france"]["levels"] == ("independent", "at_war", "fallen", "liberated")
    assert doc["bomb_ready"]["levels"] == (False, True) and doc["bomb_ready"]["init"] is False
    assert doc["aims_JPN"]["init"] is None
    assert set(doc) == {v.name for v in h.VARIABLES} | set(h.HIDDEN)
    # the 22 new ontology variables (east_offer added 2026-10-15) less the swept aims_JPN
    assert len(h.NEW) == 21


def test_quarters_and_ticks():
    assert len(h.QUARTERS) == 39 and h.QUARTERS[0] == "1936Q1" and h.QUARTERS[-1] == "1945Q3"
    assert h0.quarter_index("1945Q3") == 38


def test_inputs_load(inputs):
    assert len(inputs["moves"]) == 39
    assert [(d.quarter, d.actor, d.action) for d in inputs["decisions"]] == [
        ("1936Q1", "WEST", "rearm"),
        ("1936Q3", "GER", "rearm"),
        ("1938Q4", "GER", "rearm"),
        ("1938Q4", "WEST", "rearm"),
        ("1940Q2", "USSR", "rearm"),
        ("1940Q3", "WEST", "us_rearm"),
        ("1941Q3", "USSR", "mobilize_total"),
        ("1942Q1", "WEST", "victory_program"),
        ("1942Q2", "WEST", "atomic_program"),
    ]
    assert h.check_decisions_against_moves(inputs["decisions"], inputs["moves"]) == []
    years = {(r["ccode"], r["year"]) for r in inputs["nmc_rows"]}
    assert (2, 1945) in years and (220, 1943) not in years  # France 1943: COW gap
    v1 = [r for r in inputs["nmc_rows"] if r["year"] >= 1941]
    assert {r["extract"] for r in v1} == {"data/ww2/nmc_1941_1945.csv"}


def test_sqr_decision_rows_take_the_model_quarter(tmp_path):
    """A decision whose quarter is the one after its date's is accepted only when its note
    says [SQR]; the model quarter enters the arithmetic."""
    head = ",".join(h0.DECISION_COLUMNS)
    good = tmp_path / "good.csv"
    good.write_text(
        head + "\n1941-06-30,1941Q3,USSR,mobilize_total,3,s,[SQR] reaction\n", encoding="utf-8"
    )
    (d,) = h.load_decisions(good)
    assert d.quarter == "1941Q3" and d.date == date(1941, 6, 30)
    bad = tmp_path / "bad.csv"
    bad.write_text(head + "\n1941-06-30,1941Q3,USSR,mobilize_total,3,s,no mark\n", "utf-8")
    with pytest.raises(ValueError, match="does not match"):
        h.load_decisions(bad)
    far = tmp_path / "far.csv"
    far.write_text(head + "\n1941-03-30,1941Q3,USSR,mobilize_total,3,s,[SQR]\n", "utf-8")
    with pytest.raises(ValueError, match="does not match"):
        h.load_decisions(far)
    other = tmp_path / "other.csv"
    other.write_text(head + "\n1941-07-30,1941Q3,USSR,purge,3,s,\n", "utf-8")
    with pytest.raises(ValueError, match="not a delayed action of v1"):
        h.load_decisions(other)


def test_overlapping_nmc_rows_must_agree(tmp_path):
    src = ROOT / "data" / "ww2" / "nmc_1941_1945.csv"
    lines = src.read_text(encoding="utf-8").splitlines()
    changed = [ln.replace("USA,2,1941,75150", "USA,2,1941,75151") for ln in lines]
    bad = tmp_path / "nmc_bad.csv"
    bad.write_text("\n".join(changed) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="differs"):
        h.load_nmc([ROOT / "data" / "ww2" / "nmc_1936_1940.csv", bad])


# -- the committed files ---------------------------------------------------------------------


def test_forty_snapshots_and_nothing_else():
    names = sorted(p.name for p in SNAPSHOTS.iterdir())
    assert names == sorted([f"{q}.json" for q in FILES] + ["README.md"])


def test_committed_snapshots_are_up_to_date(built, committed):
    snaps, gaps = built
    assert set(snaps) == set(committed)
    for q in FILES:
        assert snaps[q] == committed[q], q
    assert gaps == ["FRN 1942: milper missing", "FRN 1943: no NMC row"]


def test_committed_snapshots_are_valid(committed):
    for q, snap in committed.items():
        assert validate_snapshot(snap) == [], q
        assert h.check_against_ontology(snap) == [], q
        assert h.check_builtins(snap) == [], q
        assert snap["model"] == "ww2_v1"
        assert list(snap["builtins"]) == list(h.BUILTIN_NAMES)
        for name in h.HIDDEN:
            assert name not in snap["variables"]


def test_nmc_gaps_are_flagged_not_filled(committed):
    """France 1943 has no NMC row: arms_WEST is decided by the United Kingdom's milex as a
    lower bound, the rule says so, and no France 1943 value appears anywhere."""
    for q in ("1943Q1", "1943Q2", "1943Q3", "1943Q4"):
        entry = committed[q]["variables"]["arms_WEST"]
        assert entry["level"] == "high"
        rule = entry["indicators"][0]["rule"]
        assert "NMC has no milex for FRN 1943" in rule and "lower bound" in rule
        assert not any(i["id"].startswith("nmc_FRN_1943") for i in entry["indicators"])
    entry = committed["1942Q2"]["variables"]["arms_WEST"]
    assert not any(i["id"] == "nmc_FRN_1942_milper" for i in entry["indicators"])
    for q in FILES:
        for name, entry in committed[q]["variables"].items():
            for ind in entry["indicators"]:
                if ind["id"].startswith("nmc_"):
                    assert ind["value"] is not None, (q, name)


def test_built_ins_at_the_test_start_states(committed):
    """Notes section 3 item 8: the pending counters and last actions of the start states."""

    def nonzero(q):
        b = committed[q]["builtins"]
        return {k: v["value"] for k, v in b.items() if v["value"] not in (0, "unset")}

    assert nonzero("1938Q2") == {
        "pending_GER_rearm": 1,
        "last_GER": "demand_sudeten",
        "last_WEST": "idle",
        "last_USSR": "idle",
    }
    assert nonzero("1939Q1") == {
        "belief_at_munich": "uncertain",
        "pending_GER_rearm": 7,
        "pending_WEST_rearm": 3,
        "last_GER": "occupy_bohemia",
        "last_WEST": "approach_ussr",
        "last_USSR": "idle",
    }
    assert nonzero("1940Q4")["pending_WEST_us_rearm"] == 3
    assert nonzero("1940Q4")["pending_USSR_rearm"] == 2
    assert nonzero("1941Q1")["pending_WEST_us_rearm"] == 2
    assert nonzero("1941Q1")["last_WEST"] == "lend_lease"
    assert nonzero("1941Q2")["pending_WEST_us_rearm"] == 1
    assert nonzero("1941Q2")["last_GER"] == "attack_ussr"
    assert nonzero("1945Q1")["pending_WEST_atomic_program"] == 1
    assert nonzero("1945Q1")["last_USSR"] == "counteroffensive"


def test_fairness_counters_are_computed_along_the_realized_path(committed):
    """E1: the oil clock is 1 at the end of 1941Q3, 2 at the end of 1941Q4 and 0 from the
    end of 1942Q1 (the oil secure); no counter is assumed."""
    clock = {q: committed[q]["builtins"]["fair_oil_clock"]["value"] for q in FILES}
    assert clock["1941Q3"] == 1 and clock["1941Q4"] == 2
    assert all(clock[q] == 0 for q in FILES if q not in ("1941Q3", "1941Q4"))
    for q in FILES:
        for f in h.FAIRNESS:
            entry = committed[q]["builtins"][f"fair_{f.name}"]
            assert entry["confidence"] != "assumed" and entry["indicators"], (q, f.name)
    rule = committed["1941Q4"]["builtins"]["fair_oil_clock"]["rule"]
    assert rule.startswith("fair_oil_clock = min(1 + 1, 8) = 2: computed along the realized path")


def test_move_flags(committed):
    assert committed["1942Q1"]["variables"]["midway_ordered"]["level"] is False
    assert committed["1942Q2"]["variables"]["midway_ordered"]["level"] is True
    for q in FILES:
        assert committed[q]["variables"]["east_feeler"]["level"] is False
        assert committed[q]["variables"]["east_peace"]["level"] is False
        offer = committed[q]["variables"]["east_offer"]
        assert offer["level"] is False and offer["confidence"] == "medium"


# The clock-consistency pass (owner's decision 7 of 2026-10-15): (quarter, variable, before,
# after, case) for every change it makes to the event-dated readings of the v1 series.
CLOCK_CHANGES = [
    ("1938Q2", "belief_WEST", "limited", "uncertain", "b"),  # demand_sudeten; record Sep 1938
    ("1938Q3", "arms_GER", "rising", "high", "a"),  # the programme of Aug 1936; record Oct 1938
    ("1941Q2", "anglo_soviet_alliance", False, True, "b"),  # attack_ussr; record 12 Jul 1941
    ("1942Q2", "caucasus", "soviet", "contested", "b"),  # offensive_caucasus; record Jul 1942
    ("1945Q2", "bomb_ready", False, True, "a"),  # atomic_program of Jun 1942; Trinity Jul 1945
]


def test_clock_consistency_pass_changes(inputs, committed):
    changes = []
    snaps, _ = h.build_all(**inputs, changes=changes)
    found = [(c["quarter"], c["variable"], c["before"], c["after"], c["case"]) for c in changes]
    assert found == CLOCK_CHANGES
    bare, _ = h.build_all(**inputs, clock=False)
    for q in FILES:
        for name, entry in committed[q]["variables"].items():
            if (q, name) in {(c[0], c[1]) for c in CLOCK_CHANGES}:
                assert entry["indicators"][0]["id"] == f"clock_{q}_{name}"
                assert "overrides the event-dated reading" in entry["indicators"][0]["rule"]
                assert entry["confidence"] == "medium"
                assert bare[q]["variables"][name]["level"] != entry["level"]
            else:
                assert bare[q]["variables"][name] == entry, (q, name)
    rule = committed["1941Q2"]["variables"]["anglo_soviet_alliance"]["indicators"][0]["rule"]
    assert "case (b)" in rule and "GER attack_ussr" in rule and "1941-07-12" in rule


def test_clock_pass_keeps_the_nsl_placement_and_the_one_year_discrepancies(inputs):
    """Rule (c): italy at 1940Q1 is a one-tick lag in form but an [NSL] placement, kept; it
    would change if the move were not marked [NSL]. The one-year discrepancies of decisions
    E2 item 9 (arms_GER total from 1940Q4) are not one-tick lags and are kept."""
    moves = [dict(r, note=r["note"].replace("[NSL", "[nsl")) for r in inputs["moves"]]
    changes = []
    h.build_all(**{**inputs, "moves": moves}, changes=changes)
    extra = {(c["quarter"], c["variable"]) for c in changes} - {c[:2] for c in CLOCK_CHANGES}
    assert extra == {("1940Q1", "italy")}
    snaps, _ = h.build_all(**inputs)
    assert snaps["1940Q4"]["variables"]["arms_GER"]["level"] == "high"


def test_start_of_1936q1_is_the_ontology_initial_state(inputs):
    levels = h.start_levels("1936Q1", inputs["nmc_rows"], inputs["events"], inputs["moves"])
    assert levels == {v.name: v.init for v in h.VARIABLES}


# -- the builder's arithmetic on a fixture ---------------------------------------------------


def _entry(level, confidence="high"):
    return {"level": level, "confidence": confidence, "indicators": []}


def _levels(**over):
    base = {v.name: v.init for v in h.VARIABLES}
    base.update(over)
    return {k: _entry(v) for k, v in base.items()}


def test_fixture_fairness_series_follows_the_system_update():
    moves = [
        {
            "tick": str(k),
            "quarter": h0.quarter_name(k),
            "GER": "idle",
            "WEST": w,
            "USSR": "idle",
            "JPN": "idle",
            "Nature": n,
            "source": f"row {k}",
            "note": "",
        }
        for k, (w, n) in enumerate(
            [("idle", "none")] * 3 + [("idle", "stocks_run_down"), ("idle", "none")]
        )
    ]
    levels = {
        h.TICK0: _levels(),
        "1936Q1": _levels(oil_JPN="embargoed"),
        "1936Q2": _levels(oil_JPN="embargoed", poland="german"),
        "1936Q3": _levels(oil_JPN="embargoed"),
        "1936Q4": _levels(oil_JPN="critical"),
        "1937Q1": _levels(oil_JPN="embargoed"),
    }
    series = h.fairness_series(levels, moves)
    assert [series[q]["fair_oil_clock"]["value"] for q in levels] == [0, 1, 2, 3, 0, 1]
    # A response resets the counter even when the trigger holds: 1937Q1's move is "none",
    # 1936Q4's is the response stocks_run_down with the oil critical.
    assert series["1936Q4"]["fair_oil_clock"]["rule"].startswith("fair_oil_clock = 0")
    assert series[h.TICK0]["fair_oil_clock"]["rule"].startswith("fair_oil_clock = 0")
    # democratic_response never triggers here (belief limited).
    assert all(series[q]["fair_democratic_response"]["value"] == 0 for q in levels)
    # The trigger indicator records whether it held.
    assert series["1936Q2"]["fair_oil_clock"]["indicators"][0]["value"] is True


def test_fixture_counter_caps_at_within():
    moves = [
        {
            "tick": str(k),
            "quarter": h0.quarter_name(k),
            "GER": "idle",
            "WEST": "idle",
            "USSR": "idle",
            "JPN": "idle",
            "Nature": "none",
            "source": "s",
            "note": "",
        }
        for k in range(4)
    ]
    hegemonic = _levels(belief_WEST="hegemonic", commit_WEST="wary")
    levels = {h.TICK0: _levels(), **{h0.quarter_name(k): hegemonic for k in range(4)}}
    series = h.fairness_series(levels, moves)
    assert [series[q]["fair_democratic_response"]["value"] for q in levels] == [0, 1, 2, 2, 2]


def test_cli_check_passes_on_the_committed_files(capsys):
    assert h.main(["--out", str(SNAPSHOTS), "--check"]) == 0
    assert "checked 40 snapshots" in capsys.readouterr().out


def test_cli_detects_stale_files(tmp_path, capsys):
    assert h.main(["--out", str(tmp_path)]) == 0
    (tmp_path / "1941Q3.json").write_text("{}\n", encoding="utf-8")
    assert h.main(["--out", str(tmp_path), "--check"]) == 1
    assert "1941Q3.json" in capsys.readouterr().err


def test_v0_snapshots_are_unchanged(capsys):
    """The v0 builder's 21 files still check byte for byte."""
    assert h0.main(["--out", str(ROOT / "snapshots" / "ww2" / "hindsight"), "--check"]) == 0


def test_nmc_extract_v1_header_flags_the_gaps():
    path = ROOT / "data" / "ww2" / "nmc_1941_1945.csv"
    head = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.startswith("#")]
    gaps = next(ln for ln in head if ln.startswith("# Gaps"))
    assert "FRN (220) has no row for 1943" in gaps
    assert "NTH (210) has no row for 1941, 1942, 1943, 1944" in gaps
    rows = nmc.load(path)
    assert len(rows) == 40
    assert {r["ccode"] for r in rows} == {2, 200, 210, 220, 255, 325, 365, 710, 740}
