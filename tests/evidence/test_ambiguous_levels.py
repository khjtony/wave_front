"""Snapshots with a set of levels over a contested window (docs/ambiguous_levels.md): the
schema and the validator, the loader's product set of states, the unchanged loading of every
existing snapshot, and the replay metrics against a set-valued hindsight level."""

import copy
import hashlib
import importlib
import json
import shutil
from pathlib import Path

import pytest

from wavefront.analysis import fingerprint
from wavefront.evidence import (
    SnapshotError,
    level_set,
    load_snapshot,
    load_snapshot_states,
    read_snapshot,
    snapshot_to_state,
    snapshot_to_states,
    validate_snapshot,
)
from wavefront.evidence.extract import TEXT_VARIABLES
from wavefront.evidence.replay import compare, parse_quarters, quarter_end, render_report
from wavefront.model import Model, V

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "snapshots" / "schema.json"
PIN = ROOT / "tests" / "evidence" / "fixtures" / "snapshot_states_pin.json"
HINDSIGHT = ROOT / "snapshots" / "ww2" / "hindsight"
QUARTERS = parse_quarters("1936Q1..1940Q4")


def indicator(rule="r"):
    return {
        "id": "i",
        "value": "v",
        "source": "https://example.org/s",
        "observed": "2026-09-30",
        "rule": rule,
    }


def member(level, confidence="medium"):
    return {"level": level, "confidence": confidence, "indicators": [indicator()]}


def level_set_entry(*levels):
    return {"levels": [member(lv) for lv in levels], "ambiguity": "the crossing is a judgement"}


def doc(**variables):
    """A snapshot of the mini model; a tuple value is a set of levels."""
    out = {
        name: level_set_entry(*value) if isinstance(value, tuple) else member(value)
        for name, value in variables.items()
    }
    return {"date": "2026-10-11", "model": "mini", "variables": out}


def mini():
    m = Model("mini", horizon=4)
    m.var("cap", levels=["low", "mid", "high"], init="mid")
    m.counter("stock", max=3, init=1)
    m.flag("rights")
    m.var("pick", levels=["a", "b"], init="a")
    m.latch("cap_when_rich", of="cap", when=V.stock >= 2)
    m.actor("P")
    return m.compile()


# -- schema and validator ----------------------------------------------------------------------


def test_a_set_of_levels_is_valid_and_each_member_carries_its_provenance():
    assert validate_snapshot(doc(cap=("low", "mid"))) == []
    assert validate_snapshot(doc(rights=(True, False), stock=(0, 2, 3))) == []
    assumed = doc(cap=("low", "mid"))
    assumed["variables"]["cap"]["levels"][0] = {
        "level": "low",
        "confidence": "assumed",
        "indicators": [],
    }
    assert validate_snapshot(assumed) == []


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda e: e.update(level="low"), "unexpected field 'level'"),
        (lambda e: e.update(confidence="high"), "unexpected field 'confidence'"),
        (lambda e: e.pop("ambiguity"), "missing required field 'ambiguity'"),
        (lambda e: e.update(ambiguity=""), "ambiguity: must be a non-empty string"),
        (lambda e: e.update(levels=[member("low")]), "at least two members"),
        (lambda e: e.update(levels="low"), "levels: must be an array"),
        (lambda e: e["levels"][1].pop("indicators"), "levels[1]: missing required field"),
        (
            lambda e: e["levels"][0].update(indicators=[]),
            "levels[0]: no indicators, and only confidence 'assumed'",
        ),
        (lambda e: e["levels"][0].update(level=""), "levels[0].level: must not be an empty"),
    ],
)
def test_malformed_sets_are_refused_with_their_path(mutate, message):
    data = doc(cap=("low", "mid"))
    mutate(data["variables"]["cap"])
    problems = validate_snapshot(data)
    assert any(message in p for p in problems), problems


def test_the_validator_agrees_with_the_schema_file_on_set_valued_snapshots():
    jsonschema = pytest.importorskip("jsonschema")
    from tests.evidence.test_snapshot_schema import REPLACEMENTS, at, dropped, paths, replaced

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    base = doc(cap=("low", "mid"), rights=True)
    corpus = [base]
    for path in paths(base):
        if not path:
            continue
        corpus.append(dropped(base, path))
        corpus += [replaced(base, path, value) for value in REPLACEMENTS]
        if isinstance(at(base, path), dict):
            corpus.append(replaced(base, (*path, "extra"), 1))
    both = copy.deepcopy(base)
    both["variables"]["cap"]["level"] = "low"
    corpus.append(both)
    valid = invalid = 0
    for candidate in corpus:
        theirs = list(validator.iter_errors(candidate))
        mine = validate_snapshot(candidate)
        assert bool(mine) == bool(theirs), (candidate, mine, [e.message for e in theirs])
        valid, invalid = valid + (not mine), invalid + bool(mine)
    assert valid >= 10 and invalid >= 100, (valid, invalid)


# -- the loader --------------------------------------------------------------------------------


def test_the_loader_returns_the_product_set_in_declaration_order():
    cm = mini()
    res = snapshot_to_states(doc(pick=("b", "a"), cap=("high", "low"), stock=0), cm)
    assert res.ambiguous == (("cap", ("low", "high")), ("pick", ("a", "b")))
    assert len(res) == 4 and len(set(res.states)) == 4
    shown = [(cm.level_name("cap", s[cm.index["cap"]]), s[cm.index["pick"]]) for s in res.states]
    assert shown == [("low", 0), ("low", 1), ("high", 0), ("high", 1)]
    assert res.members[1] == {"cap": "low", "pick": "b"}
    assert res.label(1) == "cap=low, pick=b"
    # every member agrees off the set-valued variables
    assert {s[cm.index["stock"]] for s in res.states} == {0}


def test_a_snapshot_without_a_set_is_one_state_as_before():
    cm = mini()
    data = doc(cap="high", stock=2)
    res = snapshot_to_states(data, cm)
    assert not res.is_set and res.states == (snapshot_to_state(data, cm),)
    assert res.members == ({},)


def test_latches_are_filled_per_member():
    cm = mini()
    res = snapshot_to_states(doc(stock=(1, 2), cap="high"), cm)
    latch = [s[cm.index["cap_when_rich"]] for s in res.states]
    assert latch == [0, cm.variables[cm.index["cap"]].levels.index("high") + 1]
    data = doc(stock=(1, 2))
    data["builtins"] = {
        "cap_when_rich": {
            "value": "unset",
            "confidence": "high",
            "indicators": [indicator()],
            "rule": "not yet rich",
        }
    }
    with pytest.raises(SnapshotError, match=r"in the member stock=2"):
        snapshot_to_states(data, cm)


def test_the_single_state_loader_refuses_a_set_and_names_the_variables(tmp_path):
    cm = mini()
    data = doc(cap=("low", "mid"), rights=(True, False))
    with pytest.raises(SnapshotError, match=r"set of levels for 'cap', 'rights'.*4 states"):
        snapshot_to_state(data, cm)
    path = tmp_path / "s.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(SnapshotError, match="snapshot_to_states"):
        load_snapshot(path, cm)
    assert len(load_snapshot_states(path, cm)) == 4


@pytest.mark.parametrize(
    "variables, message",
    [
        ({"cap": ("low", "low")}, "gives level 'low' twice"),
        ({"cap": ("low", "medium")}, "has no level 'medium'"),
        ({"stock": (1, 9)}, "counter 0..3"),
        ({"nope": ("a", "b")}, "'nope' (levels ['a', 'b']) is not a variable"),
    ],
)
def test_bad_members_are_refused(variables, message):
    with pytest.raises(SnapshotError) as info:
        snapshot_to_states(doc(**variables), mini())
    assert any(message in p for p in info.value.problems), info.value.problems


def test_level_set_reads_both_forms():
    assert level_set(member("low")) == ("low",)
    assert level_set(level_set_entry(True, False)) == (True, False)


def test_every_existing_snapshot_loads_to_exactly_one_state_as_before():
    """The states of the committed snapshots, pinned with the loader before sets existed
    (swept variables fixed to their first level). A file or model changed since the pin is
    skipped; enough must remain for the check to mean something."""
    pin = json.loads(PIN.read_text(encoding="utf-8"))
    import sys

    sys.path.insert(0, str(ROOT))
    cache = {}
    checked = 0
    for rel, want in pin["snapshots"].items():
        path = ROOT / rel
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()[:16] != want["file"]:
            continue
        data = read_snapshot(path)
        name = data["model"]
        if name not in cache:
            model = importlib.import_module(pin["models"][name]).model
            cache[name] = (model.compile(), fingerprint(model))
        cm, fp = cache[name]
        if fp != want["model"]:
            continue
        assert not any("levels" in e for e in data["variables"].values()), rel
        for spec in cm.variables:
            if spec.origin == "var" and len(spec.init) > 1 and spec.name not in data["variables"]:
                lv = spec.levels[0] if spec.kind == "level" else (spec.kind != "flag" and 0)
                data["variables"][spec.name] = {
                    "level": lv,
                    "confidence": "assumed",
                    "indicators": [],
                }
        res = snapshot_to_states(data, cm)
        assert not res.is_set and len(res) == 1, rel
        assert res.states[0] == snapshot_to_state(data, cm)
        assert hashlib.sha256(repr(res.states[0]).encode()).hexdigest()[:16] == want["state"], rel
        checked += 1
    assert checked >= 100, checked


# -- replay metrics against a set-valued hindsight level ----------------------------------------


def _copy(src, dst):
    dst.mkdir()
    for q in ["1935Q4", *QUARTERS]:
        shutil.copy(src / f"{q}.json", dst / f"{q}.json")
    return dst


def _edit(directory, quarter, name, entry):
    path = directory / f"{quarter}.json"
    snap = json.loads(path.read_text())
    snap["variables"][name] = entry
    path.write_text(json.dumps(snap))


def _concrete(level, quarter):
    return {
        "level": level,
        "confidence": "medium",
        "indicators": [indicator() | {"observed": quarter_end(quarter).isoformat()}],
    }


WINDOW = parse_quarters("1938Q2..1939Q2")


def test_a_replayed_level_in_the_hindsight_set_agrees_and_is_counted_separately(tmp_path):
    hind = _copy(HINDSIGHT, tmp_path / "hind")
    rep = _copy(HINDSIGHT, tmp_path / "rep")
    for q in WINDOW:
        _edit(hind, q, "italy_estranged", level_set_entry(True, False))
        assert validate_snapshot(json.loads((hind / f"{q}.json").read_text())) == []
    # the replay reads Italy reconciled from 1938Q2 to 1939Q1, estranged again from 1939Q2
    for q in WINDOW[:-1]:
        _edit(rep, q, "italy_estranged", _concrete(False, q))
    plain = compare(rep, QUARTERS, HINDSIGHT)
    assert plain.agreement["italy_estranged"] == (16, 20)
    assert len(plain.false_flips("italy_estranged")) == 2
    m = compare(rep, QUARTERS, hind)
    assert m.agreement["italy_estranged"] == (20, 20)
    assert m.ambiguous == {"italy_estranged": (5, 5)}
    assert m.false_flips("italy_estranged") == []
    assert [f.quarter for f in m.window_flips("italy_estranged")] == ["1938Q2", "1939Q2"]
    assert m.unread["italy_estranged"] == (20, 20)  # the initial level is in every set
    text = render_report(m, title="t", corpus={"source": "s"}, backend={"name": "b"}, command="c")
    assert "Set-valued hindsight levels" in text and "`italy_estranged` 5/5 (100%)" in text
    assert "Replayed flips inside a window, not counted as false: 2." in text
    # identical series: nothing else moves
    same = compare(_copy(HINDSIGHT, tmp_path / "same"), QUARTERS, hind)
    assert same.agreement["italy_estranged"] == (20, 20)
    assert same.ambiguous == {"italy_estranged": (5, 5)}
    assert all(same.false_flips(v) == [] for v in TEXT_VARIABLES)


def test_a_replayed_level_outside_the_set_disagrees(tmp_path):
    hind = _copy(HINDSIGHT, tmp_path / "hind")
    rep = _copy(HINDSIGHT, tmp_path / "rep")
    _edit(hind, "1938Q2", "belief_WEST", level_set_entry("limited", "uncertain"))
    _edit(rep, "1938Q2", "belief_WEST", _concrete("hegemonic", "1938Q2"))
    m = compare(rep, QUARTERS, hind)
    assert m.ambiguous["belief_WEST"] == (0, 1)
    assert "1938Q2" in m.details["belief_WEST"]
    text = render_report(m, title="t", corpus={"source": "s"}, backend={"name": "b"}, command="c")
    assert "1938Q2 ({limited, uncertain} / hegemonic)" in text
    assert "a set over a contested window: the crossing is a judgement" in text


def test_a_documented_flip_across_a_window_is_dated_by_the_window(tmp_path):
    """belief_WEST goes limited -> uncertain in 1938Q2 in the record; with 1938Q2 set-valued
    the flip may fall anywhere from 1938Q2 to 1938Q3, so a replay flipping in 1938Q3 has lag 0
    (one quarter late against the concrete record)."""
    hind = _copy(HINDSIGHT, tmp_path / "hind")
    rep = _copy(HINDSIGHT, tmp_path / "rep")
    _edit(hind, "1938Q2", "belief_WEST", level_set_entry("limited", "uncertain"))
    _edit(rep, "1938Q2", "belief_WEST", _concrete("limited", "1938Q2"))
    late = [x for x in compare(rep, QUARTERS, HINDSIGHT).matched("belief_WEST")]
    assert [x.lag_quarters for x in late if x.documented.after == "uncertain"] == [1]
    m = compare(rep, QUARTERS, hind)
    windowed = [x for x in m.matched("belief_WEST") if x.documented.after == "uncertain"]
    assert len(windowed) == 1
    d = windowed[0].documented
    assert (d.quarter, d.window_end, d.before) == ("1938Q2", "1938Q3", "limited")
    assert windowed[0].lag_quarters == 0 and windowed[0].lag_days is None
    assert m.false_flips("belief_WEST") == [] and m.missed_flips("belief_WEST") == []
    text = render_report(m, title="t", corpus={"source": "s"}, backend={"name": "b"}, command="c")
    assert "1938Q2 to 1938Q3 (ambiguous window)" in text


def test_the_cold_war_metrics_take_a_set_valued_hindsight_level():
    from wavefront.evidence.replay_cw import YearMetrics

    m = YearMetrics(years=["1960"], missing_replay=[])
    m.replay["belief_force_USA"] = {"1960": "under_200"}
    m.hindsight["belief_force_USA"] = {"1960": ("none", "under_200")}
    assert m.agreement("belief_force_USA", "hindsight") == (1, 1)
    assert m.exceeds("1960") is None  # exceeds one member, not the other: fragile
    m.hindsight["belief_force_USA"] = {"1960": ("under_200", "under_1000")}
    assert m.agreement("belief_force_USA", "hindsight") == (1, 1)
    assert m.exceeds("1960") is False
    m.replay["belief_force_USA"] = {"1960": "over_1000"}
    assert m.exceeds("1960") is True
    assert m.agreement("belief_force_USA", "hindsight") == (0, 1)
