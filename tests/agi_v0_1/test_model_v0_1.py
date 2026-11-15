"""Structure of models/agi_v0_1/v0_1.py: the one change from v0 (docs/agi_v0_1.md section 2)."""

from __future__ import annotations

from models.agi import v0
from models.agi_v0_1 import v0_1

CM = v0_1.model.compile()
CM0 = v0.model.compile()


def actions(cm):
    return {(a.name, x.name): x for a in cm.actors for x in a.actions}


def start(cm, objective="indifferent", **levels):
    s = next(x for x in cm.initial_states() if cm.state_dict(x)["a_objective"] == objective)
    s = list(s)
    for name, value in levels.items():
        i = cm.index[name]
        s[i] = cm.variables[i].levels.index(value) if isinstance(value, str) else int(value)
    return tuple(s)


def play(cm, s, choices, n):
    """``n`` transitions with each actor's first available action, ``choices`` (actor name to
    action name) where available."""
    names = [a.name for a in cm.actors]
    out = [s]
    for _ in range(n):
        avail = cm.available(s)
        move = [a[0] for a in avail]
        for who, what in choices.items():
            i = names.index(who)
            j = [x.name for x in cm.actors[i].actions].index(what)
            if j in avail[i]:
                move[i] = j
        s = cm.step(s, tuple(move))
        out.append(s)
    return out


def test_only_deploy_agents_and_the_record_keeper_differ():
    new, old = actions(CM), actions(CM0)
    assert set(new) - set(old) == {("Clock", "record_land")}
    assert set(old) <= set(new)
    for key, x in old.items():
        if key in {("L", "deploy_agents"), ("Clock", "record")}:
            continue
        y = new[key]
        assert (y.delay, y.source, y.speculative, repr(y.guard_expr), repr(y.effects)) == (
            x.delay,
            x.source,
            x.speculative,
            repr(x.guard_expr),
            repr(x.effects),
        ), key
    deploy = ("L", "deploy_agents")
    assert repr(new[deploy].guard_expr) == repr(old[deploy].guard_expr)
    assert new[("L", "deploy_agents")].delay == 0
    assert "L.deploy_agents" not in v0_1.LAGS_NOT_CARRIED
    assert [v.name for v in CM.variables if v.name not in CM0.index] == ["adoption"]


def test_autonomy_at_once_dependence_after_the_lag():
    trace = play(CM, start(CM), {"L": "deploy_agents"}, 1 + v0_1.ADOPTION_LAG)
    rows = [CM.state_dict(s) for s in trace]
    assert rows[1]["a_autonomy"] == "unsupervised"
    assert [r["dependence"] for r in rows] == ["low"] * (1 + v0_1.ADOPTION_LAG) + ["med"]
    assert [int(r["adoption"]) for r in rows] == [0, 3, 2, 1, 0]


def test_one_wave_at_a_time():
    s = start(CM, cap="agi")
    trace = play(CM, s, {"L": "deploy_agents"}, 8)
    deps = [CM.state_dict(x)["dependence"] for x in trace]
    assert deps == ["low"] * 4 + ["med"] * 4 + ["high"]


def test_a_pause_cancels_a_pending_wave():
    s = start(CM, a_known="suspected")
    trace = play(CM, s, {"L": "deploy_agents"}, 1)
    trace += play(CM, trace[-1], {"H": "pause_mandate"}, 1)[1:]
    trace += play(CM, trace[-1], {}, 4)[1:]
    rows = [CM.state_dict(x) for x in trace]
    assert rows[2]["paused"] is True or rows[2]["paused"] in ("True", 1, "1")
    assert all(r["dependence"] == "low" for r in rows)
    assert int(rows[3]["adoption"]) == 0


def test_a_mandatory_regime_without_strong_oversight_cancels():
    s = start(CM, regime="mandatory", oversight="weak")
    # licence fails, so the deployment is not available; start the wave by hand
    s = list(s)
    s[CM.index["adoption"]] = 2
    trace = play(CM, tuple(s), {}, 3)
    assert [CM.state_dict(x)["dependence"] for x in trace] == ["low"] * 4
    assert int(CM.state_dict(trace[1])["adoption"]) == 0


def test_the_record_keeper_has_one_move_in_every_state_reached():
    k = [a.name for a in CM.actors].index("Clock")
    frontier = set(CM.initial_states())
    for _ in range(5):
        nxt = set()
        for s in frontier:
            avail = CM.available(s)
            assert len(avail[k]) == 1
            move = tuple(a[-1] for a in avail)
            nxt.add(CM.step(s, move))
            nxt.add(CM.step(s, tuple(a[0] for a in avail)))
        frontier = nxt
