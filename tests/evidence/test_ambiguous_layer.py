"""The ambiguous layers of the WW2 hindsight snapshots (owner's decision 7j,
docs/owner_decisions_2026-10-23.md; docs/ambiguous_levels.md section 8), built by
scripts/build_ambiguous_layer.py from the canonical files and data/ambiguous_windows.csv:
they load with the set loaders, each file differs from its canonical counterpart only in its
windowed variables, the canonical files are unchanged, and the builder is idempotent."""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from models.ww2.hypotheses import snapshot_data
from models.ww2.v0 import model as v0_model
from models.ww2.v1 import model as v1_model
from wavefront.evidence import SnapshotError, snapshot_to_state, snapshot_to_states

ROOT = Path(__file__).resolve().parents[2]
PIN = ROOT / "tests" / "evidence" / "fixtures" / "snapshot_states_pin.json"
WW2 = ROOT / "snapshots" / "ww2"


def builder():
    name = "build_ambiguous_layer"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# the windows as applied: layer -> {file: {variable: levels}}
V0_WINDOWS = {
    "1938Q2": {"italy_estranged": (True, False), "belief_GER": ("will_not_fight", "will_fight")},
    "1938Q3": {"italy_estranged": (True, False), "belief_GER": ("will_not_fight", "will_fight")},
    "1938Q4": {"italy_estranged": (True, False), "belief_GER": ("will_not_fight", "will_fight")},
    "1939Q1": {"italy_estranged": (True, False)},
}
V1_WINDOWS = {
    **V0_WINDOWS,
    "1939Q3": {"oil_GER": ("dependent", "secured")},
    "1939Q4": {"oil_GER": ("dependent", "secured")},
}
LAYERS = [
    ("hindsight", "hindsight_ambiguous", V0_WINDOWS, v0_model, {}),
    ("hindsight_v1", "hindsight_v1_ambiguous", V1_WINDOWS, v1_model, {"aims_JPN": "hegemonic"}),
]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def compiled():
    return {id(m): m.compile() for m in (v0_model, v1_model)}


@pytest.mark.parametrize("canonical,layer,windows,model,hidden", LAYERS)
def test_the_layer_holds_exactly_the_window_files(canonical, layer, windows, model, hidden):
    assert sorted(p.stem for p in (WW2 / layer).glob("*.json")) == sorted(windows)
    assert not (ROOT / "snapshots" / "cw_v1" / "replay_ambiguous").exists()


@pytest.mark.parametrize("canonical,layer,windows,model,hidden", LAYERS)
def test_the_layer_loads_with_the_set_loaders(compiled, canonical, layer, windows, model, hidden):
    cm = compiled[id(model)]
    for quarter, sets in windows.items():
        for aims in ("revisionist", "hegemonic"):
            data = snapshot_data(
                quarter, snapshots=WW2 / layer, aims_GER=aims, aims_USSR="defensive", **hidden
            )
            res = snapshot_to_states(data, cm)
            assert res.is_set
            assert {k: set(v) for k, v in res.ambiguous} == {k: set(v) for k, v in sets.items()}
            n = 1
            for levels in sets.values():
                n *= len(levels)
            assert len(res) == n == len(set(res.states))
            for name, levels in sets.items():
                assert {m[name] for m in res.members} == set(levels)
            # the single-state loader refuses the set, naming the variables
            with pytest.raises(SnapshotError) as info:
                snapshot_to_state(data, cm)
            assert all(name in str(info.value) for name in sets)
            # every member differs from the canonical state only in the windowed variables
            base = snapshot_data(
                quarter, snapshots=WW2 / canonical, aims_GER=aims, aims_USSR="defensive", **hidden
            )
            want = snapshot_to_state(base, cm)
            free = {cm.index[name] for name in sets}
            assert want in res.states
            for s in res.states:
                assert all(a == b for i, (a, b) in enumerate(zip(s, want)) if i not in free)


@pytest.mark.parametrize("canonical,layer,windows,model,hidden", LAYERS)
def test_each_file_differs_from_its_canonical_file_only_in_the_windowed_variable(
    canonical, layer, windows, model, hidden
):
    for quarter, sets in windows.items():
        new = read(WW2 / layer / f"{quarter}.json")
        old = read(WW2 / canonical / f"{quarter}.json")
        assert set(new) == set(old)
        assert {k: v for k, v in new.items() if k != "variables"} == {
            k: v for k, v in old.items() if k != "variables"
        }
        assert set(new["variables"]) == set(old["variables"])
        for name, entry in new["variables"].items():
            if name not in sets:
                assert entry == old["variables"][name], (quarter, name)
                continue
            assert "level" not in entry and entry["ambiguity"].strip()
            assert "owner's decision 7j" in entry["ambiguity"]
            assert [m["level"] for m in entry["levels"]] == list(sets[name])
            # the canonical member is the canonical entry, provenance included
            same = [m for m in entry["levels"] if m["level"] == old["variables"][name]["level"]]
            assert same == [old["variables"][name]]
            for m in entry["levels"]:
                assert m["indicators"] and m["confidence"] != "assumed"


def test_the_ambiguity_texts_cite_the_two_readers_and_the_review_sample():
    for layer in ("hindsight_ambiguous", "hindsight_v1_ambiguous"):
        for path in (WW2 / layer).glob("193[8]Q*.json"):
            for name in ("italy_estranged", "belief_GER"):
                text = read(path)["variables"][name]["ambiguity"]
                for cited in (
                    "reports/replay_ww2_frus_claude/",
                    "reports/replay_ww2_frus_deepseek/",
                    "review_sample.csv",
                ):
                    assert cited in text, (path, name, cited)


def test_the_secured_member_does_not_rest_on_the_credit_agreement():
    """Owner's decision 5c: the German-Soviet credit agreement of 19 Aug 1939 is not a
    source. The secured member rests on v1's clock (accept_pact) and the later deliveries;
    the ambiguity text says so."""
    for quarter in ("1939Q3", "1939Q4"):
        entry = read(WW2 / "hindsight_v1_ambiguous" / f"{quarter}.json")["variables"]["oil_GER"]
        assert "decision 5c" in entry["ambiguity"] and "accept_pact" in entry["ambiguity"]
        (secured,) = [m for m in entry["levels"] if m["level"] == "secured"]
        ids = [i["id"] for i in secured["indicators"]]
        assert ids == ["move_1939Q3_USSR_accept_pact", "event_1940-02-11_oil_GER"]
        for ind in secured["indicators"]:
            for field in ("value", "source", "observed"):
                assert "credit" not in str(ind[field]).lower()
                assert "1939-08-19" not in str(ind[field])


def test_the_canonical_window_files_are_unchanged():
    """The canonical files the layer copies are those of the pin taken before sets existed
    (tests/evidence/test_ambiguous_levels.py pins every committed snapshot's state), so the
    registered claims' start states are unchanged."""
    pin = json.loads(PIN.read_text(encoding="utf-8"))["snapshots"]
    for canonical, _, windows, _, _ in LAYERS:
        for quarter in windows:
            rel = f"snapshots/ww2/{canonical}/{quarter}.json"
            data = (ROOT / rel).read_bytes()
            assert hashlib.sha256(data).hexdigest()[:16] == pin[rel]["file"], rel
            assert not any("levels" in e for e in json.loads(data)["variables"].values())
    assert not any("_ambiguous/" in rel for rel in pin)


def test_the_builder_is_idempotent_and_the_layer_up_to_date(tmp_path):
    b = builder()
    first = b.build_all()
    assert first == b.build_all()
    assert b.stale(first) == []
    # writing twice into a fresh directory gives the same bytes, and a stale file is removed
    moved = {tmp_path / layer.name: texts for layer, texts in first.items()}
    (tmp_path / "hindsight_ambiguous").mkdir()
    (tmp_path / "hindsight_ambiguous" / "1937Q1.json").write_text("{}", encoding="utf-8")
    b.write(moved)
    once = {p: p.read_bytes() for p in sorted(tmp_path.rglob("*.json"))}
    b.write(moved)
    assert once == {p: p.read_bytes() for p in sorted(tmp_path.rglob("*.json"))}
    assert b.stale(moved) == []
    assert not (tmp_path / "hindsight_ambiguous" / "1937Q1.json").exists()


def test_the_cold_war_window_is_recorded_but_not_built():
    b = builder()
    (cw,) = [w for w in b.read_windows() if w.episode == "cw_v1_replay"]
    assert cw.variable == "belief_force_USA" and (cw.first, cw.last) == ("1958", "1961")
    assert not cw.built and "after cw_v1's replay coding is final" in cw.status
    assert all(layer.name != "replay_ambiguous" for layer in b.build_all())
