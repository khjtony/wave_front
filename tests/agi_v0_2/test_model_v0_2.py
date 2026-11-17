"""Structure of models/agi_v0_2/v0_2.py: the flag, the outside release and the four consequences
(docs/agi_v0_2.html section 3). No claim query is run here."""

from __future__ import annotations

import itertools

import pytest

from models.agi_v0_1 import v0_1
from models.agi_v0_2 import v0_2
from tests.agi_v0_2.common import CONSEQUENCES, OFF, ON, only

P = v0_2.OBJECTIVE_PROFILES


def compiled(switches):
    return v0_2.build(**switches).compile(profile=P)


BUILDS = {name: compiled(sw) for name, sw in [("off", OFF), ("on", ON)]}
BUILDS |= {c: compiled(only(c)) for c in CONSEQUENCES}
CM1 = v0_1.model.compile(profile=v0_1.OBJECTIVE_PROFILES)


def actions(cm):
    return {(a.name, x.name): x for a in cm.actors for x in a.actions}


def start(cm, objective="indifferent", **levels):
    s = list(next(x for x in cm.initial_states() if cm.state_dict(x)["a_objective"] == objective))
    for name, value in levels.items():
        i = cm.index[name]
        s[i] = cm.variables[i].levels.index(value) if isinstance(value, str) else int(value)
    return tuple(s)


def names(cm, state, actor):
    i = [a.name for a in cm.actors].index(actor)
    return {cm.actors[i].actions[j].name for j in cm.available(state)[i]}


def play(cm, s, choices):
    """One transition: each actor's first available action, ``choices`` where given (an
    unavailable choice is an error)."""
    avail = cm.available(s)
    move = [a[0] for a in avail]
    for who, what in choices.items():
        i = [a.name for a in cm.actors].index(who)
        j = [x.name for x in cm.actors[i].actions].index(what)
        assert j in avail[i], f"{who}.{what} is not available"
        move[i] = j
    return cm.step(s, tuple(move))


def level(cm, s, var):
    return cm.state_dict(s)[var]


def test_all_off_is_v0_1_plus_the_flag():
    new, old = actions(BUILDS["off"]), actions(CM1)
    assert set(new) - set(old) == {("Nature", "open_release")}
    assert set(old) <= set(new)
    for key, x in old.items():
        if key == ("L", "open_weights"):
            continue
        y = new[key]
        assert (y.delay, y.source, y.speculative, repr(y.guard_expr), repr(y.effects)) == (
            x.delay,
            x.source,
            x.speculative,
            repr(x.guard_expr),
            repr(x.effects),
        ), key
    assert [v.name for v in BUILDS["off"].variables if v.name not in CM1.index] == ["weights_open"]
    ow_new, ow_old = new[("L", "open_weights")], old[("L", "open_weights")]
    assert repr(ow_new.guard_expr) == repr(ow_old.guard_expr)
    assert len(ow_new.effects) == len(ow_old.effects) + 1


def test_what_each_consequence_adds():
    off = set(actions(BUILDS["off"]))
    assert set(actions(BUILDS["recall"])) == off
    assert set(actions(BUILDS["pressure"])) == off
    assert set(actions(BUILDS["testing"])) - off == {("H", "fund_oversight_open")}
    assert set(actions(BUILDS["retrain"])) - off == {
        ("Nature", f"retrain_{o}") for o in v0_2.OBJECTIVES
    }
    extra = {
        c: [v.name for v in BUILDS[c].variables if v.name not in BUILDS["off"].index]
        for c in CONSEQUENCES
    }
    assert extra == {
        "recall": [],
        "pressure": ["fair_pressure"],
        "testing": ["pending_H_fund_oversight_open"],
        "retrain": [],
    }
    spec = {k for k, x in actions(BUILDS["on"]).items() if x.speculative}
    assert spec == {
        ("A", "seize"),
        ("Nature", "unknown_capability"),
        ("H", "fund_oversight_open"),
        ("Nature", "retrain_aligned"),
        ("Nature", "retrain_self_preserving"),
        ("Nature", "retrain_truth_seeking"),
    }
    assert actions(BUILDS["on"])[("H", "fund_oversight_open")].delay == 1


@pytest.mark.parametrize("build", list(BUILDS))
def test_the_release_sets_the_flag_and_nothing_else(build):
    cm = BUILDS[build]
    s = start(cm)
    assert level(cm, s, "weights_open") is False or level(cm, s, "weights_open") in ("False", 0)
    t = play(cm, s, {"Nature": "open_release"})
    before, after = cm.state_dict(s), cm.state_dict(t)
    changed = {k for k in before if before[k] != after[k]}
    assert "weights_open" in changed and "oversight" not in changed
    assert "open_release" not in names(cm, t, "Nature")
    assert "open_release" not in names(cm, start(cm, regime="treaty"), "Nature")


def test_labs_own_release_sets_the_flag_and_lowers_oversight():
    cm = BUILDS["off"]
    t = play(cm, start(cm), {"L": "open_weights"})
    assert level(cm, t, "oversight") == "none"
    assert cm.state_dict(t)["weights_open"] in (True, "True", 1, "1")


@pytest.mark.parametrize("build,rolls_back", [("off", True), ("recall", False)])
def test_recall_the_pause_rollback(build, rolls_back):
    cm = BUILDS[build]
    s = start(cm, a_known="suspected", dependence="med", weights_open=1)
    t = play(cm, s, {"H": "pause_mandate"})
    assert level(cm, t, "dependence") == ("low" if rolls_back else "med")
    closed = play(cm, start(cm, a_known="suspected", dependence="med"), {"H": "pause_mandate"})
    assert level(cm, closed, "dependence") == "low"


@pytest.mark.parametrize("build,lands", [("off", False), ("recall", True)])
def test_recall_the_pending_wave_under_a_pause(build, lands):
    cm = BUILDS[build]
    s = start(cm, weights_open=1, adoption=1)
    s = list(s)
    s[cm.index["paused"]] = 1
    for move in itertools.product(*cm.available(tuple(s))):
        t = cm.step(tuple(s), move)
        assert (level(cm, t, "dependence") == "med") is lands
    # A mandatory regime without strong oversight cancels in both builds.
    s = start(cm, weights_open=1, adoption=1, regime="mandatory", oversight="weak")
    assert level(cm, play(cm, s, {}), "dependence") == "low"


def test_pressure_binds_after_two_quarters_and_only_when_a_response_exists():
    cm = BUILDS["pressure"]
    s = start(cm)
    assert names(cm, s, "L") > {"deploy_agents", "race"}
    s = play(cm, s, {"Nature": "open_release", "L": "idle"})
    assert int(level(cm, s, "fair_pressure")) == 1 and "idle" in names(cm, s, "L")
    s = play(cm, s, {"L": "idle"})
    assert int(level(cm, s, "fair_pressure")) == 2
    assert names(cm, s, "L") == {"deploy_agents", "race"}
    s = play(cm, s, {"L": "deploy_agents"})
    assert int(level(cm, s, "fair_pressure")) == 0 and "idle" in names(cm, s, "L")
    # Nationalized: neither response is available, so the pressure never counts.
    n = start(cm, weights_open=1)
    n = list(n)
    n[cm.index["nationalized"]] = 1
    n = tuple(n)
    for _ in range(4):
        n = play(cm, n, {"L": "idle"})
        assert int(level(cm, n, "fair_pressure")) == 0
    assert "fair_pressure" not in BUILDS["off"].index


def test_testing_swaps_the_oversight_action_and_widens_detection():
    cm, off = BUILDS["testing"], BUILDS["off"]
    assert "fund_oversight" in names(cm, start(cm), "H")
    assert "fund_oversight_open" not in names(cm, start(cm), "H")
    s = start(cm, weights_open=1)
    assert "fund_oversight" not in names(cm, s, "H")
    assert "fund_oversight_open" in names(cm, s, "H")
    t = play(cm, s, {"H": "fund_oversight_open"})
    assert level(cm, t, "oversight") == "weak"
    assert level(cm, play(cm, t, {}), "oversight") == "strong"  # delay 1: visible at t + 2

    def detects(model, **levels):
        st = list(start(model, **levels))
        last = model.index["last_A"]
        st[last] = model.variables[last].levels.index("acquire_covert")
        return "detection" in names(model, tuple(st), "Nature")

    assert detects(cm, oversight="none", weights_open=1)
    assert not detects(cm, oversight="none")
    assert not detects(off, oversight="none", weights_open=1)
    assert detects(off, oversight="weak")


def test_retraining_needs_open_weights_and_changes_the_objective():
    cm = BUILDS["retrain"]
    s = start(cm, "aligned")
    assert not {n for n in names(cm, s, "Nature") if n.startswith("retrain_")}
    s = play(cm, s, {"Nature": "open_release"})
    assert {n for n in names(cm, s, "Nature") if n.startswith("retrain_")} == {
        "retrain_self_preserving",
        "retrain_truth_seeking",
        "retrain_indifferent",
    }
    t = play(cm, s, {"Nature": "retrain_indifferent"})
    assert level(cm, t, "a_objective") == "indifferent"
    assert "retrain_aligned" in names(cm, t, "Nature")
    assert not [k for k in actions(BUILDS["off"]) if k[1].startswith("retrain_")]


@pytest.mark.parametrize("build", list(BUILDS))
def test_every_actor_has_a_move_and_the_record_keeper_one(build):
    cm = BUILDS[build]
    k = [a.name for a in cm.actors].index("Clock")
    frontier = set(cm.initial_states())
    for _ in range(6):
        nxt = set()
        for s in frontier:
            avail = cm.available(s)
            assert all(avail) and len(avail[k]) == 1
            nxt.add(cm.step(s, tuple(a[0] for a in avail)))
            nxt.add(cm.step(s, tuple(a[-1] for a in avail)))
        frontier = nxt
