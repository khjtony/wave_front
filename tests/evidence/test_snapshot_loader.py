"""Mapping snapshots onto compiled models: states, defaults and every refusal path."""

import copy
import json
import re
from pathlib import Path

import pytest

from models.toy.two_power import model as toy
from wavefront.cli import main
from wavefront.engine import attractor, explore, safe
from wavefront.evidence import (
    SnapshotError,
    load_snapshot,
    read_snapshot,
    snapshot_to_state,
    validate_snapshot,
)
from wavefront.model import Model, ModelError, V

EXAMPLE_PATH = Path(__file__).resolve().parents[2] / "snapshots" / "toy" / "example.json"


def mini():
    """One variable of each kind, a swept one, a latch and the three built-in families."""
    m = Model("mini", horizon=4)
    m.var("cap", levels=["low", "mid", "high"], init="mid")
    m.counter("stock", max=3, init=1)
    m.flag("rights")
    m.var("pick", levels=["a", "b", "c"], init=None, hidden_from=["P"])
    m.latch("cap_when_rich", of="cap", when=V.stock >= 2)
    p = m.actor("P", remember_last=True)
    p.action("slow", delay=1)
    m.fairness("f", actor="P", trigger=V.rights, within=2, responses=["slow"])
    return m.compile()


MINI_LAYOUT = [
    "tick",
    "cap",
    "stock",
    "rights",
    "pick",
    "cap_when_rich",
    "pending_P_slow",
    "last_P",
    "fair_f",
]


def indicator():
    return {
        "id": "i",
        "value": "v",
        "source": "https://example.org/s",
        "observed": "2026-09-30",
        "rule": "r",
    }


def snapshot(**levels):
    """A valid snapshot of the mini model with provenance for each variable given."""
    return {
        "date": "2026-10-11",
        "model": "mini",
        "variables": {
            name: {"level": level, "confidence": "high", "indicators": [indicator()]}
            for name, level in levels.items()
        },
    }


def refused(data, cm=None):
    """The SnapshotError raised for ``data``."""
    with pytest.raises(SnapshotError) as info:
        snapshot_to_state(data, cm or mini())
    return info.value


# -- what loads --------------------------------------------------------------------------


def test_the_mini_model_has_the_expected_layout():
    assert [v.name for v in mini().variables] == MINI_LAYOUT


def test_a_valid_snapshot_maps_names_integers_and_booleans_to_a_state():
    cm = mini()
    state = snapshot_to_state(snapshot(cap="high", stock=2, rights=True, pick="b"), cm)
    assert isinstance(state, tuple) and all(type(x) is int for x in state)
    assert dict(zip(MINI_LAYOUT, state, strict=True)) == {
        "tick": 0,
        "cap": 2,  # level name -> index in declaration order
        "stock": 2,  # counter value
        "rights": 1,  # flag
        "pick": 1,
        "cap_when_rich": 3,  # latch: stock >= 2 already holds, so it holds cap (2) + 1
        "pending_P_slow": 0,
        "last_P": 0,
        "fair_f": 0,
    }
    assert cm.format_state(state) == (
        "{tick=0, cap=high, stock=2, rights=True, pick=b, cap_when_rich=high, "
        "pending_P_slow=0, last_P=none, fair_f=0}"
    )


def test_variables_the_snapshot_omits_take_their_declared_initial_values():
    cm = mini()
    state = snapshot_to_state(snapshot(pick="c"), cm)
    assert dict(zip(MINI_LAYOUT, state, strict=True)) == {
        "tick": 0,
        "cap": 1,  # declared init "mid"
        "stock": 1,  # declared init 1
        "rights": 0,  # flag default
        "pick": 2,
        "cap_when_rich": 0,  # stock < 2: the latch stays unset
        "pending_P_slow": 0,
        "last_P": 0,
        "fair_f": 0,
    }


def test_the_state_is_a_start_the_engine_accepts():
    cm = mini()
    state = snapshot_to_state(snapshot(pick="a"), cm)
    assert state in cm.initial_states()
    assert explore(cm, initial=[state]).states[0] == state


def test_counters_accept_integral_floats_and_flags_accept_both_booleans():
    cm = mini()
    assert snapshot_to_state(snapshot(stock=3.0, rights=False, pick="a"), cm)[2] == 3
    assert snapshot_to_state(snapshot(rights=False, pick="a"), cm)[3] == 0


def test_the_snapshot_is_not_modified_and_the_result_does_not_alias_it():
    data = snapshot(cap="low", pick="a")
    before = copy.deepcopy(data)
    first = snapshot_to_state(data, mini())
    assert data == before
    assert snapshot_to_state(data, mini()) == first


def test_a_file_loads_to_the_same_state_as_its_data(tmp_path):
    cm = mini()
    data = snapshot(cap="high", pick="b")
    path = tmp_path / "s.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert load_snapshot(path, cm) == snapshot_to_state(data, cm)
    assert load_snapshot(str(path), cm) == snapshot_to_state(data, cm)
    assert read_snapshot(path) == data


def test_an_assumed_variable_needs_no_indicators_to_load():
    data = snapshot(cap="low", pick="a")
    data["variables"]["pick"].update(confidence="assumed", indicators=[])
    assert validate_snapshot(data) == []
    assert snapshot_to_state(data, mini())[4] == 0


# -- what is refused ---------------------------------------------------------------------


def test_an_unknown_variable_is_refused_naming_the_variable_and_the_level():
    error = refused(snapshot(pick="a", colour="red"))
    assert re.search(
        r"variable 'colour' \(level 'red'\) is not a variable of model 'mini'", str(error)
    )
    assert "variables: cap, stock, rights, pick" in str(error)


def test_an_unknown_level_is_refused_naming_the_variable_and_the_level():
    error = refused(snapshot(cap="medium", pick="a"))
    assert str(error) == "variable 'cap' has no level 'medium' (levels: low, mid, high)"


@pytest.mark.parametrize(
    ("levels", "message"),
    [
        # a level variable is given by name, not by number or flag
        ({"cap": 1}, r"variable 'cap' has no level 1 \(levels: low, mid, high\)"),
        ({"cap": True}, r"variable 'cap' has no level True"),
        # a counter is given by an integer in range
        ({"stock": 4}, r"variable 'stock' is a counter 0\.\.3, so level 4 is not an integer"),
        ({"stock": -1}, r"variable 'stock' is a counter 0\.\.3, so level -1 is not an integer"),
        ({"stock": "2"}, r"variable 'stock' is a counter 0\.\.3, so level '2' is not an integer"),
        # a non-integral number is not a level at all: the schema layer refuses it first
        ({"stock": 1.5}, r"variables\.stock\.level: must be a level name, an integer or a boolean"),
        ({"stock": True}, r"variable 'stock' is a counter 0\.\.3, so level True is not an integer"),
        # a flag is given by a boolean
        ({"rights": 1}, r"variable 'rights' is a flag, so level 1 is not true or false"),
        ({"rights": "yes"}, r"variable 'rights' is a flag, so level 'yes' is not true or false"),
    ],
)
def test_a_level_of_the_wrong_kind_is_refused(levels, message):
    error = refused(snapshot(pick="a", **levels))
    assert re.search(message, str(error)), str(error)


@pytest.mark.parametrize("name", ["tick", "cap_when_rich", "pending_P_slow", "last_P", "fair_f"])
def test_built_in_variables_cannot_be_set_by_a_snapshot(name):
    error = refused(snapshot(pick="a", **{name: 0}))
    assert f"snapshot variable {name!r} (level 0) is a built-in of model 'mini'" in str(error)


def test_a_swept_variable_must_be_fixed_by_the_snapshot():
    error = refused(snapshot(cap="low"))
    assert re.search(r"variable 'pick' has no declared initial value", str(error))
    assert "(it is swept over every level: a, b, c)" in str(error)
    assert str(error).endswith("so the snapshot must fix it")


def test_a_variable_with_no_indicators_is_refused_unless_assumed():
    data = snapshot(cap="low", pick="a")
    data["variables"]["cap"]["indicators"] = []
    error = refused(data)
    assert "variables.cap: no indicators, and only confidence 'assumed' may omit them" in str(error)
    data["variables"]["cap"]["confidence"] = "assumed"
    assert snapshot_to_state(data, mini())[1] == 0


def test_missing_provenance_fields_are_refused():
    data = snapshot(cap="low", pick="a")
    del data["variables"]["cap"]["indicators"][0]["source"]
    assert "variables.cap.indicators[0]: missing required field 'source'" in str(refused(data))
    data = snapshot(cap="low", pick="a")
    del data["variables"]["cap"]["confidence"]
    assert "variables.cap: missing required field 'confidence'" in str(refused(data))


def test_a_bad_date_is_refused():
    data = snapshot(pick="a")
    data["date"] = "October 2026"
    assert "date: 'October 2026' is not a date" in str(refused(data))


def test_all_problems_are_reported_together_and_kept_on_the_error():
    error = refused(snapshot(cap="medium", stock=9, colour="red"))
    assert len(error.problems) == 4  # cap, stock, colour, and the swept pick left unfixed
    for fragment in ("'cap'", "'stock'", "'colour'", "'pick'"):
        assert any(fragment in p for p in error.problems), fragment
    assert str(error) == "; ".join(error.problems)


def test_a_snapshot_error_is_a_value_error_and_a_model_error():
    """A ValueError as specified; also a ModelError, so ``wf`` reports it with exit code 2."""
    assert issubclass(SnapshotError, ValueError)
    assert issubclass(SnapshotError, ModelError)
    with pytest.raises(ValueError):
        snapshot_to_state({}, mini())


def test_files_that_are_not_snapshots_are_refused(tmp_path):
    cm = mini()
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{not json", encoding="utf-8")
    with pytest.raises(SnapshotError, match=r"bad\.json: not valid JSON"):
        load_snapshot(bad_json, cm)
    not_an_object = tmp_path / "list.json"
    not_an_object.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(
        SnapshotError, match=r"list\.json: invalid snapshot: snapshot: must be an obj"
    ):
        read_snapshot(not_an_object)
    duplicated = tmp_path / "twice.json"
    duplicated.write_text(
        '{"date": "2026-10-11", "model": "mini", "variables": {'
        '"cap": {"level": "low", "confidence": "assumed", "indicators": []}, '
        '"cap": {"level": "high", "confidence": "assumed", "indicators": []}}}',
        encoding="utf-8",
    )
    with pytest.raises(SnapshotError, match=r"twice\.json: duplicate key 'cap'"):
        load_snapshot(duplicated, cm)
    wrong_level = tmp_path / "level.json"
    wrong_level.write_text(json.dumps(snapshot(cap="medium", pick="a")), encoding="utf-8")
    with pytest.raises(SnapshotError, match=r"level\.json: variable 'cap' has no level 'medium'"):
        load_snapshot(wrong_level, cm)
    with pytest.raises(FileNotFoundError):
        load_snapshot(tmp_path / "missing.json", cm)


# -- the toy example, end to end -------------------------------------------------------------


def toy_data(**levels):
    data = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    for name, level in levels.items():
        data["variables"][name]["level"] = level
    return data


def test_the_example_snapshot_loads_to_the_toy_models_hegemonic_start():
    cm = toy.compile()
    state = load_snapshot(EXAMPLE_PATH, cm)
    assert state in cm.initial_states()
    assert cm.level_name("aims", state[cm.index["aims"]]) == "hegemonic"
    assert state == snapshot_to_state(toy_data(), cm)
    limited = snapshot_to_state(toy_data(aims="limited"), cm)
    assert limited in cm.initial_states() and limited != state
    assert {state, limited} == set(cm.initial_states())


def test_a_snapshot_may_lie_outside_the_models_assumptions_and_still_sets_the_latch():
    cm = toy.compile()
    crisis = snapshot_to_state(toy_data(tension="crisis"), cm)
    assert crisis not in cm.initial_states()  # calm_start would exclude it
    assert explore(cm, initial=[crisis]).states[0] == crisis  # ... but the engine takes it as given
    ahead = snapshot_to_state(toy_data(control=2, belief="hegemonic"), cm)
    assert cm.level_name("belief_at_majority", ahead[cm.index["belief_at_majority"]]) == "hegemonic"
    behind = snapshot_to_state(toy_data(control=1), cm)
    assert cm.level_name("belief_at_majority", behind[cm.index["belief_at_majority"]]) == "unset"


def test_the_toy_refuses_what_the_loader_should_refuse():
    cm = toy.compile()
    with pytest.raises(SnapshotError, match="variable 'oversight' has no level 'medium'"):
        snapshot_to_state(toy_data(oversight="medium"), cm)
    with pytest.raises(SnapshotError, match="variable 'control' is a counter 0..3"):
        snapshot_to_state(toy_data(control=4), cm)
    with pytest.raises(SnapshotError, match="variable 'guarantee' is a flag"):
        snapshot_to_state(toy_data(guarantee="no"), cm)
    data = toy_data()
    del data["variables"]["aims"]
    with pytest.raises(SnapshotError, match="variable 'aims' has no declared initial value"):
        snapshot_to_state(data, cm)
    data = toy_data()
    data["variables"]["aims"]["confidence"] = "high"
    data["variables"]["aims"]["indicators"] = []
    with pytest.raises(SnapshotError, match="variables.aims: no indicators"):
        snapshot_to_state(data, cm)


def test_snapshots_move_the_verdict_through_the_engine():
    """Evidence about the starting state changes what the engine says: the same hegemonic
    hypothesis with a guarantee in force keeps INC's balance kernel; with INC lulled it does
    not even keep the takeover blocked. A demonstration of the path snapshot -> state ->
    analysis, not a finding."""
    cm = toy.compile()

    def verdict(**levels):
        state = snapshot_to_state(toy_data(**levels), cm)
        g = explore(cm, initial=[state])
        takeover = g.ending_states("TAKEOVER")
        balance = safe(g, {"INC"}, g.states_where("balance")).kernel
        blocked = safe(g, {"INC"}, set(range(g.size())) - takeover).kernel
        forced = attractor(g, {"CH"}, takeover).win
        return {
            "balance": 0 in balance,
            "blocks takeover": 0 in blocked,
            "ch forces takeover": 0 in forced,
        }

    assert verdict() == {"balance": False, "blocks takeover": True, "ch forces takeover": False}
    assert verdict(guarantee=True) == {
        "balance": True,
        "blocks takeover": True,
        "ch forces takeover": False,
    }
    assert verdict(belief="limited") == {
        "balance": False,
        "blocks takeover": False,
        "ch forces takeover": True,
    }
    assert verdict(aims="limited") == {
        "balance": True,
        "blocks takeover": True,
        "ch forces takeover": False,
    }


def test_wf_viable_takes_a_snapshot_and_reports_a_bad_one_as_a_user_error(capsys, tmp_path):
    """The command line path: a good snapshot is analysed, a bad one is refused with exit
    code 2 and a message naming the file, the variable and the level (no traceback)."""
    model_ref = str(EXAMPLE_PATH.parents[2] / "models" / "toy" / "two_power.py")
    args = ["viable", model_ref, "--coalition", "INC", "--invariant", "balance"]
    assert main([*args, "--snapshot", str(EXAMPLE_PATH)]) == 0
    out = capsys.readouterr().out
    assert "balance" in out

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(toy_data(oversight="medium")), encoding="utf-8")
    assert main([*args, "--snapshot", str(bad)]) == 2
    err = capsys.readouterr().err
    assert "bad.json" in err and "variable 'oversight' has no level 'medium'" in err
