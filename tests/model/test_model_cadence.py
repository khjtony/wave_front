"""Decision cadence (spec 3.1, 3.1a): ``m.actor(name, cadence=k)``.

With ``k >= 2`` the compiler adds ``cadence_<actor>`` in ``0..k-1`` (last in the state);
the actor's declared actions are available only while it is 0, its built-in ``idle``
always; choosing a declared action sets it to ``k - 1``, anything else decrements it to 0.
A binding fairness restriction overrides the counter. ``k == 1`` adds nothing.
"""

import pytest

from wavefront.analysis import fingerprint
from wavefront.engine import explore
from wavefront.evidence import SnapshotError, snapshot_to_state
from wavefront.model import Bump, Model, ModelError, Set, V


def move(cm, **chosen):
    """A joint move by action names; unnamed actors play their built-in action."""
    return tuple(
        actor.action_index(chosen[actor.name]) if actor.name in chosen else 0 for actor in cm.actors
    )


def names(cm, avail, actor):
    a = next(x for x in cm.actors if x.name == actor)
    return [a.actions[j].name for j in avail[a.index]]


def with_counter(cm, state, actor, value):
    s = list(state)
    s[cm.index[f"cadence_{actor}"]] = value
    return tuple(s)


def model(cadence=3, horizon=8):
    """A (fast or slow) pusher A and a puller B; ``cadence=None`` leaves the argument out."""
    m = Model("cad", horizon=horizon)
    m.counter("x", max=8)
    m.counter("y", max=8)
    a = m.actor("A") if cadence is None else m.actor("A", cadence=cadence)
    a.action("push", effect=Bump("x", 1), source="test")
    a.action("hold", guard=V.x < 8, source="test")
    b = m.actor("B")
    b.action("pull", effect=Bump("y", 1), source="test")
    return m


# -- layout --------------------------------------------------------------------------------


def test_counter_is_added_last_with_k_levels():
    m = model(cadence=3)
    m.fairness("f", actor="B", trigger=V.y >= 1, within=1, responses=["pull"])
    cm = m.compile()
    spec = cm.variables[-1]
    assert [v.name for v in cm.variables] == ["tick", "x", "y", "fair_f", "cadence_A"]
    assert (spec.kind, spec.origin, spec.levels, spec.init) == (
        "builtin",
        "cadence",
        ("0", "1", "2"),
        (0,),
    )
    a = cm.actors[0]
    assert (a.period, a.cadence) == (3, cm.index["cadence_A"])
    assert cm.actors[1].cadence is None and cm.actors[1].period == 1


def test_cadence_one_adds_nothing():
    one, plain = model(cadence=1).compile(), model(cadence=None).compile()
    assert [v.name for v in one.variables] == ["tick", "x", "y"]
    assert [v.name for v in one.variables] == [v.name for v in plain.variables]
    assert one.budget() == plain.budget()
    g1, g2 = explore(one), explore(plain)
    assert (g1.states, g1.moves, g1.succ, g1.avail) == (g2.states, g2.moves, g2.succ, g2.avail)


# -- availability, reset and decrement -----------------------------------------------------


def test_declared_actions_only_when_the_counter_is_zero():
    cm = model(cadence=3).compile()
    s0 = cm.initial_states()[0]
    assert names(cm, cm.available(s0), "A") == ["idle", "push", "hold"]
    for c in (1, 2):
        assert names(cm, cm.available(with_counter(cm, s0, "A", c)), "A") == ["idle"]
        # the other actors are unaffected
        assert names(cm, cm.available(with_counter(cm, s0, "A", c)), "B") == ["idle", "pull"]


def test_a_declared_action_resets_and_anything_else_decrements_to_zero():
    cm = model(cadence=3).compile()
    i = cm.index["cadence_A"]
    s0 = cm.initial_states()[0]
    s1 = cm.step(s0, move(cm, A="push"))
    assert s1[i] == 2 and s1[cm.index["x"]] == 1
    s2 = cm.step(s1, move(cm, B="pull"))  # A idles (its only option); B's move is irrelevant
    assert s2[i] == 1
    s3 = cm.step(s2, move(cm))
    assert s3[i] == 0
    assert cm.step(s3, move(cm))[i] == 0  # idle at 0 stays 0
    assert cm.step(s3, move(cm, A="hold"))[i] == 2  # an effectless declared action counts


def test_an_actor_with_cadence_k_decides_at_most_once_every_k_ticks():
    """Along every play, two declared actions of A are at least k ticks apart, and A can
    decide at ticks 0, k, 2k, ..."""
    for k in (2, 3):
        cm = model(cadence=k, horizon=7).compile()
        g = explore(cm)
        a = cm.actors[0]
        tick = cm.index["tick"]

        def decisions(sid, last):
            """Walk every play (the graph is small), checking spacing."""
            if g.terminal[sid]:
                return
            for jm, t in zip(g.moves[sid], g.succ[sid], strict=True):
                now = g.states[sid][tick]
                if jm[a.index]:
                    assert last is None or now - last >= k
                    decisions(t, now)
                else:
                    decisions(t, last)

        for s in g.initial:
            decisions(s, None)
        x = cm.index["x"]
        assert max(s[x] for s in g.states) == len(range(0, 7, k))  # pushes at 0, k, 2k, ...


def test_idle_is_always_available_and_delays_and_profiles_are_unchanged():
    m = Model("cad", horizon=6)
    m.counter("x", max=4)
    a = m.actor("A", cadence=2)
    a.action("slow", effect=Bump("x", 1), delay=2, source="test")
    a.action("fast", effect=Bump("x", 1), source="test")
    m.profile("calm", actor="A", forbid=["fast"], unless=V.x >= 2)
    cm = m.compile()
    s0 = cm.initial_states()[0]
    s1 = cm.step(s0, move(cm, A="slow"))
    assert s1[cm.index["pending_A_slow"]] == 2 and s1[cm.index["cadence_A"]] == 1
    assert names(cm, cm.available(s1), "A") == ["idle"]
    s2 = cm.step(s1, move(cm))
    # the cadence counter is back at 0, but slow is still pending
    assert s2[cm.index["cadence_A"]] == 0 and s2[cm.index["pending_A_slow"]] == 1
    assert names(cm, cm.available(s2), "A") == ["idle", "fast"]
    calm = m.compile(profile="calm")
    assert names(calm, calm.available(s2), "A") == ["idle"]


# -- fairness ------------------------------------------------------------------------------


def fair_model(responses):
    m = Model("cadfair", horizon=6)
    m.flag("alarm")
    m.counter("x", max=6)
    a = m.actor("A", cadence=3)
    a.action("raise_alarm", effect=Set("alarm", True), source="test")
    a.action("respond", guard=V.alarm, effect=[Set("alarm", False), Bump("x", 1)], source="test")
    a.action("other", source="test")
    m.fairness("f", actor="A", trigger=V.alarm, within=1, responses=responses)
    return m.compile()


def test_a_binding_fairness_restriction_overrides_the_cadence_counter():
    cm = fair_model(["respond"])
    i, f = cm.index["cadence_A"], cm.index["fair_f"]
    s1 = cm.step(cm.initial_states()[0], move(cm, A="raise_alarm"))
    assert (s1[i], s1[f]) == (2, 1)  # cadence counter above 0, fairness binds
    assert names(cm, cm.available(s1), "A") == ["respond"]
    s2 = cm.step(s1, move(cm, A="respond"))
    assert (s2[i], s2[f]) == (2, 0)  # the response resets the cadence counter
    assert names(cm, cm.available(s2), "A") == ["idle"]


def test_an_idle_response_under_a_binding_restriction_decrements_the_counter():
    cm = fair_model(["idle", "respond"])
    i = cm.index["cadence_A"]
    s1 = cm.step(cm.initial_states()[0], move(cm, A="raise_alarm"))
    assert names(cm, cm.available(s1), "A") == ["idle", "respond"]
    assert cm.step(s1, move(cm))[i] == 1


def test_a_relaxed_fairness_constraint_no_longer_overrides():
    cm = fair_model(["respond"])
    s1 = cm.step(cm.initial_states()[0], move(cm, A="raise_alarm"))
    relaxed = cm.model.compile(relax=["f"])
    s1r = tuple(x for n, x in zip([v.name for v in cm.variables], s1, strict=True) if n != "fair_f")
    assert names(relaxed, relaxed.available(s1r), "A") == ["idle"]


# -- observation ---------------------------------------------------------------------------


def test_only_observation_includes_the_actors_own_cadence_counter():
    m = Model("obs", horizon=4)
    m.counter("x", max=3)
    a = m.actor("A", observes=V.only("x"), cadence=2)
    a.action("go", guard=V["cadence_B"] == 0, source="test")
    b = m.actor("B", observes=V.only("x"), cadence=2)
    b.action("go", guard=V["cadence_B"] == 0, source="test")
    with pytest.raises(ModelError, match="cadence_B"):
        m.compile()
    m2 = Model("obs", horizon=4)
    m2.counter("x", max=3)
    a = m2.actor("A", observes=V.only("x"), cadence=2)
    b = m2.actor("B", observes=V.only("x"), cadence=2)
    b.action("go", guard=V["cadence_B"] == 0, source="test")
    cm = m2.compile()
    assert "cadence_A" in cm.actors[0].observes and "cadence_B" not in cm.actors[0].observes
    assert "cadence_B" in cm.actors[1].observes


# -- snapshots -----------------------------------------------------------------------------


def snapshot(value):
    return {
        "date": "2026-10-15",
        "model": "cad",
        "variables": {},
        "builtins": {
            "cadence_A": {
                "value": value,
                "confidence": "assumed",
                "indicators": [],
                "rule": "A last decided one tick before the snapshot",
            }
        },
    }


def test_a_snapshot_may_set_the_cadence_counter():
    cm = model(cadence=3).compile()
    state = snapshot_to_state(snapshot(2), cm)
    assert state[cm.index["cadence_A"]] == 2
    assert names(cm, cm.available(state), "A") == ["idle"]
    assert snapshot_to_state(snapshot(0), cm) == cm.initial_states()[0]


@pytest.mark.parametrize(
    "value, message",
    [
        (3, r"'cadence_A' is 3, outside 0\.\.2 \(the cadence of A is 3\)"),
        ("idle", r"'cadence_A' is a cadence counter, so 'idle' is not an integer"),
        (True, r"cadence counter"),
    ],
)
def test_a_cadence_counter_out_of_range_is_refused(value, message):
    with pytest.raises(SnapshotError, match=message):
        snapshot_to_state(snapshot(value), model(cadence=3).compile())


def test_a_snapshot_cannot_set_a_cadence_counter_the_model_lacks():
    with pytest.raises(SnapshotError, match="not a built-in of model"):
        snapshot_to_state(snapshot(0), model(cadence=1).compile())


# -- budget and fingerprint ----------------------------------------------------------------


def test_budget_counts_actors_with_a_cadence():
    assert model(cadence=1).compile().budget()["cadence"] == 0
    m = model(cadence=2)
    m.actor("C", cadence=3)
    b = m.compile().budget()
    assert b["cadence"] == 2
    assert b["builtin_variables"] == 3  # tick and two cadence counters


def test_fingerprint_changes_only_when_a_cadence_is_used():
    m0 = model(cadence=None)
    assert fingerprint(model(cadence=1)) == fingerprint(m0)
    assert fingerprint(model(cadence=2)) != fingerprint(m0)
    assert fingerprint(model(cadence=2)) != fingerprint(model(cadence=3))


# -- errors --------------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [0, -1, 1.5, True, "2", None])
def test_cadence_must_be_an_int_at_least_one(bad):
    with pytest.raises(ModelError, match="cadence must be an int >= 1"):
        Model("m", horizon=2).actor("A", cadence=bad)


def test_cadence_needs_the_builtin_idle():
    with pytest.raises(ModelError, match="needs the built-in idle"):
        Model("m", horizon=2).actor("A", idle=False, cadence=2)
    Model("m", horizon=2).actor("A", idle=False, cadence=1)  # fine


def test_an_assigned_cadence_is_checked_at_compile():
    m = model(cadence=1)
    m.actors[0].cadence = 0
    with pytest.raises(ModelError, match="cadence must be an int >= 1"):
        m.compile()
    m = model(cadence=1)
    m.nature().cadence = 2
    with pytest.raises(ModelError, match="Nature has no cadence"):
        m.compile()


@pytest.mark.parametrize("name", ["cadence_A", "cadence_x"])
def test_the_cadence_prefix_is_reserved(name):
    m = Model("m", horizon=2)
    with pytest.raises(ModelError, match="reserved"):
        m.counter(name, max=2)
    with pytest.raises(ModelError, match="reserved"):
        m.actor(name)
