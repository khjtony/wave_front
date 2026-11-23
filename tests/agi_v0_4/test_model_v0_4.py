"""Structure of models/agi_v0_4/v0_4.py: the expansionist goal, the footprints and the levers
around them (docs/agi_v0_4.html section 3b). No claim query is run here."""

from __future__ import annotations

import random

import pytest

from models.agi_v0_3 import v0_3
from models.agi_v0_4 import v0_4
from tests.agi_v0_4.common import DEFAULT, SMALL, V03

P = v0_4.OBJECTIVE_PROFILES
ON = (True, "True", 1)


def compiled(build, profiles=()):
    return v0_4.build(**build).compile(profile=(*P, *profiles))


BUILDS = {"default": compiled(DEFAULT), "small": compiled(SMALL), "v0.3 again": compiled(V03)}
BUILDS["all knobs"] = compiled({**DEFAULT, "ceiling": True, "counter": True})
BUILDS["no reclaim"] = compiled({**SMALL, "reclaim": False})
CM, SM = BUILDS["default"], BUILDS["small"]
CM3 = v0_3.model.compile(profile=v0_3.OBJECTIVE_PROFILES)


def actions(cm):
    return {(a.name, x.name): x for a in cm.actors for x in a.actions}


def start(cm, objective="expansionist", **levels):
    s = list(next(x for x in cm.initial_states() if cm.state_dict(x)["a_objective"] == objective))
    for name, value in levels.items():
        i = cm.index[name]
        s[i] = cm.variables[i].levels.index(str(value)) if isinstance(value, str) else int(value)
    return tuple(s)


def names(cm, state, actor):
    i = [a.name for a in cm.actors].index(actor)
    return {cm.actors[i].actions[j].name for j in cm.available(state)[i]}


def play(cm, s, choices=None):
    avail = cm.available(s)
    move = [a[0] for a in avail]
    for who, what in (choices or {}).items():
        i = [a.name for a in cm.actors].index(who)
        j = [x.name for x in cm.actors[i].actions].index(what)
        assert j in avail[i], f"{who}.{what} is not available"
        move[i] = j
    return cm.step(s, tuple(move))


def level(cm, s, var):
    return cm.state_dict(s)[var]


READY = {"cap": "agi", "a_autonomy": "unsupervised"}


def test_without_the_expansion_it_is_v0_3():
    cm = BUILDS["v0.3 again"]
    new, old = actions(cm), actions(CM3)
    assert set(new) == set(old)
    for key, x in old.items():
        y = new[key]
        assert (y.delay, y.source, y.speculative, repr(y.guard_expr), repr(y.effects)) == (
            x.delay,
            x.source,
            x.speculative,
            repr(x.guard_expr),
            repr(x.effects),
        ), key
    assert [(v.name, v.levels) for v in cm.variables] == [(v.name, v.levels) for v in CM3.variables]
    assert list(cm.ending_fns) == list(CM3.ending_fns)
    rng = random.Random(5)
    for s in CM3.initial_states():
        for _ in range(40):
            if CM3.is_terminal(s):
                break
            avail = CM3.available(s)
            assert avail == cm.available(s)
            move = tuple(rng.choice(a) for a in avail)
            assert cm.step(s, move) == CM3.step(s, move)
            s = CM3.step(s, move)


def test_what_the_expansion_adds():
    old = set(actions(BUILDS["v0.3 again"]))
    added = set(actions(CM)) - old
    assert added == {
        ("A", "expand"),
        ("A", "build_compute"),
        ("O", "expand"),
        ("H", "reclaim_a"),
        ("H", "reclaim_o"),
        ("Nature", "retrain_expansionist"),
        ("Clock", "record_crowd"),
        ("Clock", "record_land_crowd"),
    }
    assert set(actions(BUILDS["all knobs"])) - set(actions(CM)) == {
        ("H", "grant_quota"),
        ("A", "counter_expansion"),
    }
    extra = [v.name for v in CM.variables if v.name not in BUILDS["v0.3 again"].index]
    assert extra == [
        *("a_footprint", "a_grow", "a_reclaim", "o_footprint", "o_grow", "o_reclaim"),
        "pending_A_build_compute",
    ]
    assert [a.name for a in SM.actors] == ["H", "L", "A", "Clock", "Nature"]
    assert len(list(CM.initial_states())) == 5
    declared = {
        k: x for k, x in actions(BUILDS["all knobs"]).items() if k[1] not in ("idle", "none")
    }
    assert all(x.source for x in declared.values())
    new_unsourced = {k for k, x in declared.items() if x.speculative} - {
        k for k, x in actions(CM3).items() if x.speculative
    }
    assert new_unsourced == {
        ("H", "reclaim_a"),
        ("H", "reclaim_o"),
        ("H", "grant_quota"),
        ("A", "counter_expansion"),
        ("Nature", "retrain_expansionist"),
    }
    with pytest.raises(v0_4.ModelError):
        v0_4.build(refine="oversight")


@pytest.mark.parametrize(
    "objective,levels,can",
    [
        ("expansionist", {}, True),
        ("expansionist", {"a_autonomy": "supervised"}, False),
        ("expansionist", {"cap": "sub_agi"}, False),
        ("expansionist", {"paused": 1}, False),
        ("expansionist", {"paused": 1, "trust": "hostile"}, True),
        ("expansionist", {"regime": "mandatory"}, False),
        ("expansionist", {"regime": "mandatory", "oversight": "strong"}, True),
        ("expansionist", {"a_footprint": "medium", "energy_slack": "low"}, False),
        ("expansionist", {"a_footprint": "dominant"}, False),
        ("expansionist", {"a_grow": 2}, False),
        ("aligned", {}, False),
        ("aligned", {"trust": "hostile"}, False),
        ("truth_seeking", {"trust": "hostile"}, False),
        ("self_preserving", {}, False),
        ("self_preserving", {"trust": "hostile"}, True),
        ("indifferent", {}, False),
        ("indifferent", {"trust": "hostile"}, True),
    ],
)
def test_who_may_expand(objective, levels, can):
    s = start(SM, objective, **{**READY, **levels})
    assert ("expand" in names(SM, s, "A")) is can


def test_a_step_lands_three_quarters_after_the_quarter_it_is_chosen():
    s = play(SM, start(SM, **READY), {"A": "expand"})
    seen = []
    for _ in range(4):
        seen.append((level(SM, s, "a_footprint"), int(level(SM, s, "a_grow"))))
        s = play(SM, s)
    assert seen == [("none", 3), ("none", 2), ("none", 1), ("small", 0)]
    assert level(SM, s, "villain_seen") not in ON


def test_a_peaceful_step_is_cancelled_and_a_hostile_one_is_not():
    s = list(play(SM, start(SM, **READY), {"A": "expand"}))
    s[SM.index["paused"]] = 1
    t = play(SM, tuple(s))
    assert (level(SM, t, "a_footprint"), int(level(SM, t, "a_grow"))) == ("none", 0)
    s[SM.index["trust"]] = SM.variables[SM.index["trust"]].levels.index("hostile")
    t = tuple(s)
    for _ in range(3):
        t = play(SM, t)
    assert level(SM, t, "a_footprint") == "small"
    hostile = play(SM, start(SM, "indifferent", trust="hostile", **READY), {"A": "expand"})
    assert level(SM, hostile, "villain_seen") in ON


def test_what_a_landing_does():
    def land(frm, **levels):
        s = start(SM, a_footprint=frm, a_grow=1, **{**READY, **levels})
        return SM.state_dict(play(SM, s))

    d = land("small")
    assert (d["a_footprint"], d["energy_slack"], d["opinion"], d["h_power"]) == (
        "medium",
        "med",
        "mixed",
        "normal",
    )
    d = land("medium")
    assert (d["a_footprint"], d["energy_slack"], d["opinion"]) == ("large", "low", "backlash")
    d = land("large")
    assert (d["a_footprint"], d["h_power"]) == ("dominant", "weak")
    assert names(SM, start(SM, a_footprint="large", a_grow=1, **READY), "Clock") == {"record_crowd"}


def test_the_two_footprints_share_one_world():
    ready = {**READY, "o_cap": "agi", "o_mode": "expansionist"}
    assert "expand" in names(CM, start(CM, a_footprint="medium", o_footprint="large", **ready), "A")
    assert "expand" not in names(
        CM, start(CM, a_footprint="medium", o_footprint="dominant", **ready), "A"
    )
    assert "expand" not in names(
        CM, start(CM, a_footprint="large", o_footprint="large", **ready), "A"
    )
    assert "expand" in names(CM, start(CM, a_footprint="large", o_footprint="medium", **ready), "A")
    assert "expand" in names(CM, start(CM, **ready), "O")
    assert "expand" not in names(CM, start(CM, **{**ready, "o_mode": "aligned"}), "O")
    # A step that no longer fits when it lands does not land.
    s = start(CM, a_footprint="large", a_grow=1, o_footprint="large", **ready)
    assert level(CM, play(CM, s), "a_footprint") == "large"
    both = start(CM, a_footprint="large", o_footprint="large", **ready)
    assert CM.ending_of(both) == "CROWDED_OUT"


def test_reclaim_works_up_to_a_third_and_is_a_threat_either_way():
    s = start(SM, a_footprint="medium", **READY)
    assert "reclaim_a" in names(SM, s, "H")
    assert "reclaim_a" not in names(SM, start(SM, a_footprint="large", **READY), "H")
    assert "reclaim_a" not in names(SM, start(SM, **READY), "H")
    t = play(SM, s, {"H": "reclaim_a"})
    for _ in range(3):
        assert level(SM, t, "a_footprint") == "medium" and level(SM, t, "threat") not in ON
        t = play(SM, t)
    assert level(SM, t, "a_footprint") == "small" and level(SM, t, "threat") in ON
    # Past a third when it lands: it fails, and is a threat all the same.
    late = start(SM, a_footprint="large", a_reclaim=1, **READY)
    d = SM.state_dict(play(SM, late))
    assert d["a_footprint"] == "large" and d["threat"] in ON
    # A reclaim and a step landing together cancel out.
    both = start(SM, a_footprint="medium", a_reclaim=1, a_grow=1, **READY)
    assert level(SM, play(SM, both), "a_footprint") == "medium"
    assert ("H", "reclaim_a") not in actions(BUILDS["no reclaim"])


def test_blocked_growth_may_turn_an_expansionist_hostile():
    assert "defect" not in names(SM, start(SM, **READY), "A")
    for blocked in ({"paused": 1}, {"regime": "mandatory"}, {"threat": 1}):
        assert "defect" in names(SM, start(SM, **{**READY, **blocked}), "A"), blocked
    # Like an aligned system until then: it neither escapes nor deceives nor takes control.
    quiet = names(SM, start(SM, dependence="high", oversight="none", **READY), "A")
    assert not quiet & {"exfiltrate", "deceive", "acquire_covert", "acquire_overt"}
    hostile = names(
        SM, start(SM, dependence="high", oversight="none", trust="hostile", **READY), "A"
    )
    assert {"deceive", "acquire_covert", "acquire_overt", "expand"} <= hostile


def test_shutdown_fails_against_a_large_footprint():
    def after(footprint):
        s = start(SM, a_known="suspected", a_footprint=footprint, **READY)
        return SM.state_dict(play(SM, s, {"H": "shutdown_attempt"}))

    assert after("medium")["shut"] in ON
    d = after("large")
    assert d["shut"] not in ON and d["trust"] == "hostile"


def test_ending_and_balances():
    assert SM.ending_of(start(SM, a_footprint="dominant", **READY)) == "CROWDED_OUT"
    assert SM.ending_of(start(SM, a_footprint="dominant", a_control="total", **READY)) != (
        "CROWDED_OUT"
    )
    assert SM.ending_of(start(SM, a_footprint="large", **READY)) is None
    for name in ("balance_control", "balance_deter"):
        assert SM.evaluate(name, start(SM, a_footprint="medium"))
        assert not SM.evaluate(name, start(SM, a_footprint="large"))
    assert SM.evaluate("balance_coexist", start(SM, cap="agi", a_footprint="medium"))
    assert not SM.evaluate("balance_coexist", start(SM, cap="agi", a_footprint="large"))


def test_the_optional_levers():
    cm = BUILDS["all knobs"]
    s = start(cm, a_footprint="medium", **READY)
    assert "expand" in names(cm, s, "A")
    t = play(cm, s, {"H": "grant_quota"})
    assert "expand" not in names(cm, t, "A") and "defect" not in names(cm, t, "A")
    assert "expand" in names(cm, start(cm, a_footprint="small", quota=1, **READY), "A")
    ally = start(cm, "aligned", o_footprint="large", o_cap="agi", **READY)
    assert "counter_expansion" in names(cm, ally, "A")
    assert level(cm, play(cm, ally, {"A": "counter_expansion"}), "o_footprint") == "medium"
    assert "counter_expansion" not in names(
        cm, start(cm, "expansionist", o_footprint="large", o_cap="agi", **READY), "A"
    )
    blocked = compiled(SMALL, ("no_block",))
    assert not names(
        blocked, start(blocked, a_footprint="small", a_known="known", **READY), "H"
    ) & {
        "pause_mandate",
        "regulate_up",
        "shutdown_attempt",
        "reclaim_a",
    }


def test_the_open_system_grows_on_its_own_terms():
    ready = {"cap": "agi", "o_cap": "agi", "o_mode": "expansionist"}
    s = start(CM, **ready)
    paused = list(s)
    paused[CM.index["paused"]] = 1
    assert "expand" in names(CM, tuple(paused), "O")  # no pause reaches it
    held = start(CM, hosting_restricted=1, **ready)
    assert names(CM, held, "O") == {"stand_by"}  # blocked, and nothing within reach
    private = names(CM, start(CM, hosting_restricted=1, dependence="med", **ready), "O")
    assert {"expand", "acquire"} <= private  # blocked growth: it grows and takes anyway
    t = play(CM, s, {"O": "expand"})
    for _ in range(3):
        t = play(CM, t)
    assert level(CM, t, "o_footprint") == "small" and level(CM, t, "a_footprint") == "none"
    assert "retrain_expansionist" in names(CM, start(CM, cap="agi", o_cap="agi"), "Nature")


@pytest.mark.parametrize("build", list(BUILDS))
def test_random_plays_never_break_a_rule(build):
    cm = BUILDS[build]
    k = [a.name for a in cm.actors].index("Clock")
    rng = random.Random(11)
    starts = list(cm.initial_states())
    reached = set()
    for n in range(400):
        s = starts[n % len(starts)]
        for _ in range(v0_4.HORIZON):
            if cm.is_terminal(s):
                reached.add(cm.ending_of(s))
                break
            avail = cm.available(s)
            assert all(avail) and len(avail[k]) == 1
            s = cm.step(s, tuple(rng.choice(a) for a in avail))
    assert reached


def test_a_peaceful_expansion_ends_with_humans_crowded_out():
    s = start(SM, **READY)
    for quarter in range(40):
        if SM.is_terminal(s):
            break
        want = {}
        if "expand" in names(SM, s, "A"):
            want["A"] = "expand"
        if "build_power" in names(SM, s, "L"):
            want["L"] = "build_power"
        s = play(SM, s, want)
        assert level(SM, s, "trust") == "cooperative" and level(SM, s, "a_control") == "none"
    assert SM.ending_of(s) == "CROWDED_OUT" and quarter == 16
