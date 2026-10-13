"""The ``builtins`` section of a snapshot (phase 2 decision F2): schema, validator, loader.

A snapshot may set the built-in variables of a model (pending delayed decisions, last
actions, latches, fairness counters), each with a value, a confidence, indicators and the
rule that derives the value. These tests cover what loads, what is refused and that the
validator agrees with ``snapshots/schema.json`` on the new section.
"""

import copy
import json
import re
from pathlib import Path

import pytest

from wavefront.engine import explore
from wavefront.evidence import SnapshotError, load_snapshot, snapshot_to_state, validate_snapshot
from wavefront.model import Bump, Model, V

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "snapshots" / "schema.json"


def mini():
    """One built-in of each family: a latch, a pending counter (delay 2), a last action, a
    fairness counter (within 2); plus a flag latch and a swept variable."""
    m = Model("mini_b", horizon=6)
    m.var("cap", levels=["low", "mid", "high"], init="low")
    m.counter("stock", max=3, init=1)
    m.flag("rights")
    m.var("pick", levels=["a", "b"], init=None)
    m.latch("cap_when_rich", of="cap", when=V.stock >= 2)
    m.latch("rights_when_high", of="rights", when=V.cap == "high")
    p = m.actor("P", remember_last=True)
    p.action("build", guard=V.cap < "high", effect=Bump("cap", 1), delay=2)
    p.action("save", effect=Bump("stock", 1))
    m.fairness("f", actor="P", trigger=V.rights, within=2, responses=["save"])
    return m.compile()


LAYOUT = [
    "tick",
    "cap",
    "stock",
    "rights",
    "pick",
    "cap_when_rich",
    "rights_when_high",
    "pending_P_build",
    "last_P",
    "fair_f",
]


def indicator(**over):
    out = {
        "id": "i",
        "value": "v",
        "source": "https://example.org/s",
        "observed": "2026-09-30",
        "rule": "r",
    }
    out.update(over)
    return out


def entry(value, confidence="high", indicators=None, rule="derived from i"):
    return {
        "value": value,
        "confidence": confidence,
        "indicators": [indicator()] if indicators is None else indicators,
        "rule": rule,
    }


def snapshot(builtins=None, **levels):
    levels.setdefault("pick", "a")
    data = {
        "date": "2026-10-11",
        "model": "mini_b",
        "variables": {
            name: {"level": level, "confidence": "high", "indicators": [indicator()]}
            for name, level in levels.items()
        },
    }
    if builtins is not None:
        data["builtins"] = {
            name: value if isinstance(value, dict) else entry(value)
            for name, value in builtins.items()
        }
    return data


def as_dict(state):
    return dict(zip(LAYOUT, state, strict=True))


def refused(data, cm=None):
    with pytest.raises(SnapshotError) as info:
        snapshot_to_state(data, cm or mini())
    return info.value


# -- what loads --------------------------------------------------------------------------


def test_layout():
    assert [v.name for v in mini().variables] == LAYOUT


def test_every_family_is_filled_into_the_state_after_the_variables():
    cm = mini()
    data = snapshot(
        {
            "cap_when_rich": "mid",
            "rights_when_high": True,
            "pending_P_build": 2,
            "last_P": "save",
            "fair_f": 1,
        },
        cap="high",
        stock=2,
        rights=True,
    )
    state = snapshot_to_state(data, cm)
    assert as_dict(state) == {
        "tick": 0,
        "cap": 2,
        "stock": 2,
        "rights": 1,
        "pick": 0,
        "cap_when_rich": 2,  # 'mid' as given, not the loaded cap (the loader does not override)
        "rights_when_high": 2,  # True
        "pending_P_build": 2,
        "last_P": 3,  # none, idle, build, save
        "fair_f": 1,
    }
    assert cm.format_state(state) == (
        "{tick=0, cap=high, stock=2, rights=True, pick=a, cap_when_rich=mid, "
        "rights_when_high=True, pending_P_build=2, last_P=save, fair_f=1}"
    )


def test_omitted_built_ins_keep_their_initial_values_and_omitted_latches_are_set_as_before():
    state = snapshot_to_state(snapshot({"pending_P_build": 1}, cap="mid", stock=3), mini())
    assert as_dict(state) == {
        "tick": 0,
        "cap": 1,
        "stock": 3,
        "rights": 0,
        "pick": 0,
        "cap_when_rich": 2,  # the condition holds, so the loader sets it to cap + 1
        "rights_when_high": 0,
        "pending_P_build": 1,
        "last_P": 0,
        "fair_f": 0,
    }


def test_last_action_none_idle_and_unset_latch_and_zero_counters_load():
    state = snapshot_to_state(
        snapshot({"last_P": "none", "cap_when_rich": "unset", "pending_P_build": 0, "fair_f": 0}),
        mini(),
    )
    assert as_dict(state)["last_P"] == 0 and as_dict(state)["cap_when_rich"] == 0
    idle = snapshot_to_state(snapshot({"last_P": "idle"}), mini())
    assert as_dict(idle)["last_P"] == 1


def test_an_integral_float_counts_as_an_integer():
    state = snapshot_to_state(snapshot({"pending_P_build": 2.0}), mini())
    assert as_dict(state)["pending_P_build"] == 2


def test_an_assumed_built_in_needs_no_indicator_but_a_rule():
    data = snapshot({"fair_f": entry(0, "assumed", [], "assumed: no record observes it")})
    assert validate_snapshot(data) == []
    assert as_dict(snapshot_to_state(data, mini()))["fair_f"] == 0


def test_a_loaded_pending_counter_behaves_as_the_models_own():
    """The engine takes the counter as given: the action is unavailable while it runs, and
    the effect lands when it reaches 0 (framework_spec.md section 3.1)."""
    cm = mini()
    state = snapshot_to_state(snapshot({"pending_P_build": 2}), cm)
    p = cm.actors[0]
    build = p.action_index("build")
    assert build not in cm.available(state)[0]
    idle = tuple(0 for _ in cm.actors)
    s1 = cm.step(state, idle)
    assert as_dict(s1)["pending_P_build"] == 1 and as_dict(s1)["cap"] == 0
    assert build not in cm.available(s1)[0]
    s2 = cm.step(s1, idle)
    assert as_dict(s2)["pending_P_build"] == 0 and as_dict(s2)["cap"] == 1
    assert build in cm.available(s2)[0]
    assert explore(cm, initial=[state]).states[0] == state


def test_a_file_with_built_ins_loads_like_its_data(tmp_path):
    cm = mini()
    data = snapshot({"pending_P_build": 1, "last_P": "build"})
    path = tmp_path / "b.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert load_snapshot(path, cm) == snapshot_to_state(data, cm)


# -- what is refused ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("builtins", "message"),
    [
        (
            {"pending_P_save": 0},
            r"snapshot built-in 'pending_P_save' \(value 0\): not a built-in of model 'mini_b' "
            r"\(built-ins: cap_when_rich, rights_when_high, pending_P_build, last_P, fair_f\)",
        ),
        ({"last_Q": "x"}, r"snapshot built-in 'last_Q' \(value 'x'\): not a built-in"),
        ({"tick": 3}, r"snapshot built-in 'tick' \(value 3\): it is not settable"),
        ({"cap": "high"}, r"snapshot built-in 'cap' \(value 'high'\): it is a declared variable"),
        (
            {"pending_P_build": 3},
            r"built-in 'pending_P_build' is 3, outside 0\.\.2 \(the delay of P\.build is 2\)",
        ),
        ({"pending_P_build": "1"}, r"'pending_P_build' is a pending counter, so '1' is not an"),
        ({"pending_P_build": True}, r"'pending_P_build' is a pending counter, so True is not"),
        ({"fair_f": 3}, r"built-in 'fair_f' is 3, outside 0\.\.2 \(its 'within' is 2\)"),
        (
            {"last_P": "rebuild"},
            r"built-in 'last_P' has no action 'rebuild' \(levels: none, idle, build, save\)",
        ),
        (
            {"cap_when_rich": "medium"},
            r"built-in 'cap_when_rich' \(a latch of 'cap'\) has no level 'medium'",
        ),
        ({"cap_when_rich": 1}, r"built-in 'cap_when_rich' \(a latch of 'cap'\) has no level 1"),
        (
            {"rights_when_high": "True"},
            r"built-in 'rights_when_high' \(a latch of 'rights'\) has no level 'True'",
        ),
    ],
)
def test_unknown_names_and_values_out_of_range_are_refused_naming_the_built_in(builtins, message):
    error = refused(snapshot(builtins))
    assert re.search(message, str(error)), str(error)


def test_a_built_in_in_variables_is_refused_with_a_pointer_to_the_section():
    data = snapshot(pending_P_build=1)
    error = refused(data)
    assert "snapshot variable 'pending_P_build' (level 1) is a built-in of model" in str(error)
    assert "built-ins go in its builtins section" in str(error)


def test_an_unset_latch_whose_condition_holds_is_refused():
    error = refused(snapshot({"cap_when_rich": "unset"}, stock=2))
    assert "built-in 'cap_when_rich' is given as 'unset', but its condition already holds" in (
        str(error)
    )


def test_all_built_in_problems_are_reported_together():
    error = refused(snapshot({"pending_P_build": 9, "fair_f": 9, "last_P": "x", "nope": 1}))
    assert len(error.problems) == 4
    for name in ("pending_P_build", "fair_f", "last_P", "nope"):
        assert any(name in p for p in error.problems), name


# -- structure: validator and schema ---------------------------------------------------------


def broken(mutate):
    data = snapshot({"pending_P_build": 1})
    mutate(data)
    return data


def _b(d):
    return d["builtins"]["pending_P_build"]


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (broken(lambda d: d.update(builtins=[])), r"^builtins: must be an object"),
        (broken(lambda d: d["builtins"].update(x=None)), r"builtins\.x: must be an object"),
        (
            broken(lambda d: d["builtins"].update({"bad name": entry(0)})),
            r"builtins: 'bad name' is not a valid built-in name",
        ),
        (broken(lambda d: _b(d).pop("rule")), r"builtins\.pending_P_build: missing required field"),
        (broken(lambda d: _b(d).pop("value")), r"missing required field 'value'"),
        (broken(lambda d: _b(d).pop("confidence")), r"missing required field 'confidence'"),
        (broken(lambda d: _b(d).pop("indicators")), r"missing required field 'indicators'"),
        (broken(lambda d: _b(d).update(level=1)), r"unexpected field 'level'"),
        (broken(lambda d: _b(d).update(rule="")), r"\.rule: must be a non-empty string"),
        (broken(lambda d: _b(d).update(value=-1)), r"\.value: must not be negative"),
        (broken(lambda d: _b(d).update(value=1.5)), r"\.value: must be a non-negative integer"),
        (broken(lambda d: _b(d).update(value=None)), r"\.value: must be a non-negative integer"),
        (broken(lambda d: _b(d).update(value="")), r"\.value: must not be an empty string"),
        (broken(lambda d: _b(d).update(confidence="sure")), r"\.confidence: 'sure' is not one"),
        (broken(lambda d: _b(d).update(indicators={})), r"\.indicators: must be an array"),
        (
            broken(lambda d: _b(d).update(indicators=[])),
            r"builtins\.pending_P_build: no indicators, and only confidence 'assumed'",
        ),
        (
            broken(lambda d: _b(d)["indicators"][0].pop("source")),
            r"builtins\.pending_P_build\.indicators\[0\]: missing required field 'source'",
        ),
    ],
)
def test_structural_problems_in_builtins_are_reported_with_their_path(data, message):
    problems = validate_snapshot(data)
    assert any(re.search(message, p) for p in problems), problems


def test_the_schema_file_declares_the_section():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert "builtins" in schema["properties"]
    assert schema["$defs"]["builtin"]["required"] == ["value", "confidence", "indicators", "rule"]


def _mutations(base):
    values = [None, True, False, 0, -1, 2.0, 1.5, "", "x", "assumed", [], {}, {"a": 1}]
    yield base
    section = base["builtins"]
    for name in list(section):
        for field in list(section[name]):
            out = copy.deepcopy(base)
            del out["builtins"][name][field]
            yield out
            for value in values:
                out = copy.deepcopy(base)
                out["builtins"][name][field] = value
                yield out
        for value in values:
            out = copy.deepcopy(base)
            out["builtins"][name] = value
            yield out
        out = copy.deepcopy(base)
        out["builtins"][name]["extra"] = 1
        yield out
        out = copy.deepcopy(base)
        out["builtins"]["not a name"] = out["builtins"].pop(name)
        yield out
        for k, ind in enumerate(section[name]["indicators"]):
            for field in ind:
                out = copy.deepcopy(base)
                del out["builtins"][name]["indicators"][k][field]
                yield out
    for value in values:
        out = copy.deepcopy(base)
        out["builtins"] = value
        yield out


def test_the_validator_agrees_with_the_schema_file_on_builtins():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    bases = [
        snapshot({"pending_P_build": 1, "last_P": "save", "rights_when_high": True}),
        snapshot({"fair_f": entry(0, "assumed", [], "assumed")}),
    ]
    valid = invalid = 0
    for base in bases:
        for candidate in _mutations(base):
            theirs = [e.message for e in validator.iter_errors(candidate)]
            mine = validate_snapshot(candidate)
            assert bool(mine) == bool(theirs), (candidate, mine, theirs)
            valid, invalid = valid + (not mine), invalid + bool(mine)
    assert valid >= 15 and invalid >= 150, (valid, invalid)
