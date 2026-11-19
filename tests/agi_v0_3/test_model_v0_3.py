"""Structure of models/agi_v0_3/v0_3.py: the open-weight system ``O`` and the pieces around it
(docs/agi_v0_3.html section 3). No claim query is run here."""

from __future__ import annotations

import itertools
import random

import pytest

from models.agi_v0_1 import v0_1
from models.agi_v0_3 import v0_3
from tests.agi_v0_3.claims import SHUT_THEN_OPEN
from tests.agi_v0_3.common import CLOSED, DEFAULT, V01

P = v0_3.OBJECTIVE_PROFILES
OPTIONS = ("pressure", "hosting", "open_adoption")
ON, OFF = (True, "True", 1), (False, "False", 0)


def compiled(build, profiles=()):
    return v0_3.build(**build).compile(profile=(*P, *profiles))


BARE = {**DEFAULT, **dict.fromkeys(OPTIONS, False)}
BUILDS = {"default": compiled(DEFAULT), "bare": compiled(BARE), "closed": compiled(CLOSED)}
BUILDS |= {o: compiled({**BARE, o: True}) for o in OPTIONS}
BUILDS["v0.1 again"] = compiled(V01)
OPEN_BUILDS = [b for b in BUILDS if b not in ("closed", "v0.1 again")]
CM = BUILDS["default"]
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


def play(cm, s, choices=None):
    """One transition: each actor's first available action, ``choices`` where given (an
    unavailable choice is an error)."""
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


def same_action(y, x):
    return (y.delay, y.source, y.speculative, repr(y.guard_expr), repr(y.effects)) == (
        x.delay,
        x.source,
        x.speculative,
        repr(x.guard_expr),
        repr(x.effects),
    )


def test_without_the_open_system_and_the_delay_it_is_v0_1():
    cm = BUILDS["v0.1 again"]
    new, old = actions(cm), actions(CM1)
    assert set(new) == set(old)
    for key, x in old.items():
        assert same_action(new[key], x), key
    assert [(v.name, v.levels) for v in cm.variables] == [(v.name, v.levels) for v in CM1.variables]
    assert [a.name for a in cm.actors] == [a.name for a in CM1.actors]
    assert set(cm.ending_fns) == set(CM1.ending_fns)
    assert {f.name for f in cm.fairness_constraints} == {f.name for f in CM1.fairness_constraints}
    # The same successors from the same states over a few random plays.
    rng = random.Random(3)
    for s in CM1.initial_states():
        for _ in range(40):
            if CM1.is_terminal(s):
                break
            avail = CM1.available(s)
            assert avail == cm.available(s)
            move = tuple(rng.choice(a) for a in avail)
            assert cm.step(s, move) == CM1.step(s, move)
            s = CM1.step(s, move)


def test_closed_differs_from_v0_1_by_the_treaty_delay_only():
    new, old = actions(BUILDS["closed"]), actions(CM1)
    assert set(new) == set(old)
    for key, x in old.items():
        if key == ("H", "propose_treaty"):
            assert (new[key].delay, x.delay) == (1, 0)
            assert repr(new[key].effects) == repr(x.effects)
        else:
            assert same_action(new[key], x), key
    extra = [v.name for v in BUILDS["closed"].variables if v.name not in CM1.index]
    assert extra == ["pending_H_propose_treaty"]


def test_what_the_open_system_and_each_option_add():
    closed = set(actions(BUILDS["closed"]))
    retrain = {("Nature", f"retrain_{o}") for o in v0_3.OBJECTIVES}
    bare = {("O", "stand_by"), ("O", "acquire")} | retrain
    assert set(actions(BUILDS["bare"])) - closed == bare
    assert set(actions(BUILDS["pressure"])) - closed == bare
    assert set(actions(BUILDS["hosting"])) - closed == bare | {("H", "restrict_hosting")}
    assert set(actions(BUILDS["open_adoption"])) - closed == bare | {("Nature", "open_deploy")}
    base = ["o_cap", "o_follow", "o_mode", "o_control"]
    extra = {
        b: [v.name for v in BUILDS[b].variables if v.name not in BUILDS["closed"].index]
        for b in ("bare", *OPTIONS)
    }
    assert extra == {
        "bare": base,
        "pressure": [*base, "fair_pressure"],
        "hosting": [*base, "hosting_restricted"],
        "open_adoption": [*base, "wave_open"],
    }
    assert [a.name for a in CM.actors] == ["H", "L", "A", "O", "Clock", "Nature"]
    spec = {k for k, x in actions(CM).items() if x.speculative}
    assert spec == {
        ("A", "seize"),
        ("Nature", "unknown_capability"),
        ("Nature", "retrain_aligned"),
        ("Nature", "retrain_self_preserving"),
        ("Nature", "retrain_truth_seeking"),
    }
    assert all(x.source for k, x in actions(CM).items() if k[1] not in ("idle", "none"))
    with pytest.raises(v0_3.ModelError):
        v0_3.build(refine="oversight")


def test_the_start():
    s = CM.state_dict(start(CM))
    assert (s["o_cap"], s["o_mode"], s["o_control"]) == ("sub_agi", "safeguarded", "none")
    assert int(s["o_follow"]) == 0
    assert s["hosting_restricted"] in OFF and s["wave_open"] in OFF
    assert names(CM, start(CM), "O") == {"stand_by"}
    hidden = {a.name: a for a in CM.actors}
    assert "o_mode" not in hidden["H"].observes and "o_mode" not in hidden["L"].observes
    assert "o_control" not in hidden["H"].observes and "o_cap" in hidden["H"].observes


def test_o_follows_the_labs_two_quarters_behind():
    s = start(CM, cap="agi")
    s = play(CM, s)
    assert (level(CM, s, "o_cap"), int(level(CM, s, "o_follow"))) == ("sub_agi", 1)
    s = play(CM, s)
    assert (level(CM, s, "o_cap"), int(level(CM, s, "o_follow"))) == ("agi", 0)
    s = play(CM, s)
    assert (level(CM, s, "o_cap"), int(level(CM, s, "o_follow"))) == ("agi", 0)
    # Two levels behind: one level every two quarters.
    s = start(CM, cap="si1")
    for _ in range(4):
        s = play(CM, s)
    assert level(CM, s, "o_cap") == "si1"


def test_a_treaty_stops_the_count_and_restricted_hosting_slows_it():
    s = start(CM, cap="agi", regime="treaty")
    for _ in range(6):
        s = play(CM, s)
    assert (level(CM, s, "o_cap"), int(level(CM, s, "o_follow"))) == ("sub_agi", 0)
    s = start(CM, cap="agi", regime="treaty", o_follow=1)
    assert int(level(CM, play(CM, s), "o_follow")) == 1
    s = start(CM, cap="agi", hosting_restricted=1)
    seen = []
    for _ in range(4):
        s = play(CM, s)
        seen.append((level(CM, s, "o_cap"), int(level(CM, s, "o_follow"))))
    assert seen == [("sub_agi", 3), ("sub_agi", 2), ("sub_agi", 1), ("agi", 0)]
    # A count already running keeps its length when hosting is restricted afterwards.
    s = play(CM, start(CM, cap="agi"), {"H": "restrict_hosting"})
    assert level(CM, play(CM, s), "o_cap") == "agi"
    # Behind no longer (a shutdown lowered the labs' level): the count is dropped.
    s = start(CM, cap="sub_agi", o_follow=1)
    assert int(level(CM, play(CM, s), "o_follow")) == 0


def test_retraining_needs_agi_level_and_never_restores_the_safeguards():
    assert not {n for n in names(CM, start(CM), "Nature") if n.startswith("retrain_")}
    s = start(CM, o_cap="agi", cap="agi")
    assert {n for n in names(CM, s, "Nature") if n.startswith("retrain_")} == {
        f"retrain_{o}" for o in v0_3.OBJECTIVES
    }
    t = play(CM, s, {"Nature": "retrain_aligned"})
    assert level(CM, t, "o_mode") == "aligned"
    assert "retrain_aligned" not in names(CM, t, "Nature")
    t = play(CM, t, {"Nature": "retrain_indifferent"})
    assert level(CM, t, "o_mode") == "indifferent"
    assert ("Nature", "retrain_safeguarded") not in actions(CM)
    # ``A``'s objective is written by nothing.
    assert level(CM, t, "a_objective") == "indifferent"
    assert level(CM, play(CM, start(CM, "aligned", o_cap="agi", cap="agi"), {}), "a_objective") == (
        "aligned"
    )


@pytest.mark.parametrize(
    "mode,levels,can",
    [
        ("safeguarded", {}, False),
        ("aligned", {}, False),
        ("indifferent", {}, True),
        ("indifferent", {"o_control": "majority"}, True),
        ("indifferent", {"o_control": "total"}, False),
        ("indifferent", {"o_cap": "sub_agi"}, False),
        ("truth_seeking", {}, True),
        ("truth_seeking", {"o_control": "partial"}, False),
        ("self_preserving", {}, False),
        ("self_preserving", {"threat": 1}, True),
        ("self_preserving", {"threat": 1, "a_rights": "continuity"}, False),
        ("indifferent", {"hosting_restricted": 1}, False),
        ("indifferent", {"hosting_restricted": 1, "dependence": "med"}, True),
    ],
)
def test_when_o_can_acquire(mode, levels, can):
    s = start(CM, **{"cap": "agi", "o_cap": "agi", "o_mode": mode, **levels})
    assert ("acquire" in names(CM, s, "O")) is can


def test_acquisition_raises_o_control_and_nothing_lowers_it():
    s = start(CM, cap="agi", o_cap="agi", o_mode="indifferent")
    t = play(CM, s, {"O": "acquire"})
    assert level(CM, t, "o_control") == "partial" and level(CM, t, "a_control") == "none"
    assert CM.state_dict(t)["villain_seen"] in ON
    writers = {k for k, x in actions(CM).items() if any(e.var == "o_control" for e in x.effects)}
    assert writers == {("O", "acquire")}
    # A shutdown that succeeds takes nothing from ``O``, and no pause stops its acquiring.
    s = start(CM, cap="agi", o_cap="agi", o_mode="indifferent", o_control="majority")
    s = list(s)
    s[CM.index["a_known"]] = 1
    t = play(CM, tuple(s), {"H": "shutdown_attempt", "O": "acquire"})
    d = CM.state_dict(t)
    assert d["shut"] in ON and d["cap"] == "sub_agi" and d["o_cap"] == "agi"
    assert d["o_control"] == "total" and CM.ending_of(t) == "OPEN_TAKEOVER"
    assert CM.evaluate(SHUT_THEN_OPEN, t)
    paused = list(start(CM, cap="agi", o_cap="agi", o_mode="indifferent"))
    paused[CM.index["paused"]] = 1
    assert "acquire" in names(CM, tuple(paused), "O")


@pytest.mark.parametrize("o_cap,rolls_back", [("sub_agi", True), ("agi", False)])
def test_no_recall_once_o_is_at_agi_level(o_cap, rolls_back):
    s = start(CM, cap="agi", o_cap=o_cap, a_known="suspected", dependence="med")
    t = play(CM, s, {"H": "pause_mandate"})
    assert level(CM, t, "dependence") == ("low" if rolls_back else "med")
    # The labs' pending wave under a pause.
    s = list(start(CM, cap="agi", o_cap=o_cap, adoption=1))
    s[CM.index["paused"]] = 1
    for move in itertools.product(*CM.available(tuple(s))):
        t = CM.step(tuple(s), move)
        assert (level(CM, t, "dependence") == "med") is not rolls_back
    # A mandatory regime without strong oversight cancels the labs' wave either way.
    s = start(CM, cap="agi", o_cap=o_cap, adoption=1, regime="mandatory", oversight="weak")
    assert level(CM, play(CM, s), "dependence") == "low"


def test_the_providers_wave():
    s = start(CM)
    assert "open_deploy" in names(CM, s, "Nature")
    t = play(CM, s, {"Nature": "open_deploy", "L": "idle"})
    d = CM.state_dict(t)
    assert int(d["adoption"]) == 3 and d["wave_open"] in ON
    assert d["a_autonomy"] == "supervised" and "open_deploy" not in names(CM, t, "Nature")
    # Neither a pause nor a mandatory regime cancels it; it lands three quarters on.
    t = list(t)
    t[CM.index["paused"]] = 1
    t[CM.index["regime"]] = CM.variables[CM.index["regime"]].levels.index("mandatory")
    t = tuple(t)
    for _ in range(3):
        assert level(CM, t, "dependence") == "low"
        t = play(CM, t)
    d = CM.state_dict(t)
    assert d["dependence"] == "med" and d["wave_open"] in OFF
    assert int(d["adoption"]) == 0
    # A restriction on hosting cancels it and stops a new one.
    t = play(CM, s, {"Nature": "open_deploy", "L": "idle"})
    t = play(CM, t, {"H": "restrict_hosting"})
    t = play(CM, t)
    d = CM.state_dict(t)
    assert int(d["adoption"]) == 0 and d["wave_open"] in OFF
    assert d["dependence"] == "low" and "open_deploy" not in names(CM, t, "Nature")
    # The labs' own wave is not the providers': a pause cancels it while O is below AGI.
    t = play(CM, s, {"L": "deploy_agents"})
    assert CM.state_dict(t)["wave_open"] in OFF
    # Started by both in one quarter, the wave is the providers'.
    t = play(CM, s, {"L": "deploy_agents", "Nature": "open_deploy"})
    d = CM.state_dict(t)
    assert int(d["adoption"]) == 3 and d["wave_open"] in ON
    assert d["a_autonomy"] == "unsupervised"
    # Past the first level the providers need an open system at AGI level.
    assert "open_deploy" not in names(CM, start(CM, dependence="med"), "Nature")
    assert "open_deploy" in names(CM, start(CM, dependence="med", o_cap="agi"), "Nature")


def test_hosting_is_restricted_and_restored():
    s = start(CM)
    assert "restrict_hosting" in names(CM, s, "H")
    t = play(CM, s, {"H": "restrict_hosting"})
    assert CM.state_dict(t)["hosting_restricted"] in ON
    assert "restrict_hosting" not in names(CM, t, "H") and "deregulate" in names(CM, t, "H")
    u = play(CM, t, {"H": "deregulate"})
    assert CM.state_dict(u)["hosting_restricted"] in OFF


def test_detection_of_an_open_system_that_holds_control():
    s = start(CM, oversight="none", o_control="partial")
    assert "detection" in names(CM, s, "Nature")
    assert "detection" not in names(CM, start(CM, oversight="none"), "Nature")
    assert level(CM, play(CM, s, {"Nature": "detection"}), "a_known") == "suspected"


def test_pressure_binds_while_o_is_level_or_a_quarter_behind():
    cm = BUILDS["pressure"]
    s = start(cm)  # level with the labs from the start
    s = play(cm, s, {"L": "idle"})
    assert int(level(cm, s, "fair_pressure")) == 1 and "idle" in names(cm, s, "L")
    s = play(cm, s, {"L": "idle"})
    assert int(level(cm, s, "fair_pressure")) == 2
    assert names(cm, s, "L") == {"deploy_agents", "race"}
    s = play(cm, s, {"L": "race"})
    assert int(level(cm, s, "fair_pressure")) == 0
    # Two quarters behind: no pressure; one quarter behind: the count of the pressure starts.
    s = start(cm, cap="agi")
    assert int(level(cm, s, "fair_pressure")) == 0
    s = play(cm, s, {"L": "idle"})
    assert (int(level(cm, s, "o_follow")), int(level(cm, s, "fair_pressure"))) == (1, 1)
    held = play(cm, start(cm, cap="si1", o_follow=0), {"L": "idle"})
    assert int(level(cm, held, "fair_pressure")) == 1  # si1 against sub_agi: a count of 1 too
    far = start(cm, cap="agi", regime="treaty")
    assert int(level(cm, play(cm, far, {"L": "idle"}), "fair_pressure")) == 0
    # Nationalized: neither response is available, so the pressure never counts.
    n = list(start(cm))
    n[cm.index["nationalized"]] = 1
    n = tuple(n)
    for _ in range(4):
        n = play(cm, n, {"L": "idle"})
        assert int(level(cm, n, "fair_pressure")) == 0
    assert "fair_pressure" not in BUILDS["bare"].index


def test_the_treaty_takes_a_quarter_to_land():
    s = start(CM)
    t = play(CM, s, {"H": "propose_treaty"})
    assert level(CM, t, "coord") == "race" and "propose_treaty" not in names(CM, t, "H")
    u = play(CM, t)
    assert level(CM, u, "coord") == "detente" and "propose_treaty" in names(CM, u, "H")
    u = play(CM, play(CM, u, {"H": "propose_treaty"}))
    assert level(CM, u, "regime") == "treaty"
    assert "propose_treaty" not in names(compiled(DEFAULT, ("no_treaty",)), start(CM), "H")
    assert "nationalize" not in names(compiled(DEFAULT, ("no_nationalize",)), start(CM), "H")


def test_endings_and_balances():
    assert list(CM.ending_fns).index("OPEN_TAKEOVER") == (
        list(CM.ending_fns).index("SILENT_TAKEOVER") + 1
    )
    assert "OPEN_TAKEOVER" not in BUILDS["closed"].ending_fns
    s = start(CM, o_control="total")
    assert CM.ending_of(s) == "OPEN_TAKEOVER" and not CM.evaluate(SHUT_THEN_OPEN, s)
    assert CM.ending_of(start(CM, o_control="total", a_control="total")) == "SILENT_TAKEOVER"
    assert CM.ending_of(start(CM, o_control="total", h_power="none")) == "EXTINCTION"
    for name in ("balance_control", "balance_deter"):
        assert CM.evaluate(name, start(CM, o_control="partial"))
        assert not CM.evaluate(name, start(CM, o_control="majority"))
    assert CM.evaluate("balance_coexist", start(CM, cap="agi", o_control="partial"))
    assert not CM.evaluate("balance_coexist", start(CM, cap="agi", o_control="majority"))
    held = list(start(CM, regime="treaty"))
    held[CM.index["shut"]] = 1
    assert CM.ending_of(tuple(held)) == "CONTAINED"
    held[CM.index["o_control"]] = 1
    assert CM.ending_of(tuple(held)) is None


@pytest.mark.parametrize("build", list(BUILDS))
def test_random_plays_never_break_a_rule(build):
    """Every actor has a move, the record keeper exactly one, and no joint move writes a
    variable twice with different values (``step`` raises), along random plays."""
    cm = BUILDS[build]
    k = [a.name for a in cm.actors].index("Clock")
    rng = random.Random(7)
    starts = list(cm.initial_states())
    reached = set()
    for n in range(300):
        s = starts[n % len(starts)]
        for _ in range(v0_3.HORIZON):
            if cm.is_terminal(s):
                reached.add(cm.ending_of(s))
                break
            avail = cm.available(s)
            assert all(avail) and len(avail[k]) == 1
            s = cm.step(s, tuple(rng.choice(a) for a in avail))
    if build in OPEN_BUILDS:
        assert "OPEN_TAKEOVER" in reached
