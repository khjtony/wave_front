"""Hand-built BMC tests: each construct of ``_successor`` with a known answer.

Most tests check both the BMC answer and, where it exists, the explicit engine's, and
replay every trace with ``cm.step``.
"""

import pytest
import z3

from bmc.rich_models import check_replay
from wavefront.bmc import BmcTrace, encode, reach, relax
from wavefront.engine import Trace, explore, witness
from wavefront.model import FALSE, Bump, Inc, Model, ModelError, Set, SetIf, V


def solve(enc, *extra):
    """A model of the encoding with ``extra`` constraints and every assumption asserted,
    or ``None``."""
    s = enc.solver()
    s.add(*enc.assume.values(), *extra)
    return s.model() if s.check() == z3.sat else None


def value(enc, model, name, t):
    return model.eval(enc.state[t][enc.cm.index[name]], model_completion=True).as_long()


def chosen(enc, actor, action, t):
    a = next(x for x in enc.cm.actors if x.name == actor)
    return enc.chosen[t][a.index] == a.action_index(action)


def replay(cm, trace, target):
    check_replay(cm, trace, lambda s: cm.evaluate(target, s))


# -- delays --------------------------------------------------------------------------------


def delayed(d):
    m = Model("delay", horizon=6)
    m.var("x", levels=["lo", "hi"])
    m.actor("A").action("fire", effect=Set("x", "hi"), delay=d)
    return m.compile()


@pytest.mark.parametrize("d", [1, 2])
def test_delay_timing(d):
    cm = delayed(d)
    enc = encode(cm, 5)
    model = solve(enc, enc.active[5], chosen(enc, "A", "fire", 0))
    # Chosen at tick 0: pending set to d at tick 1, effect visible at tick 1 + d.
    assert [value(enc, model, "pending_A_fire", t) for t in range(d + 2)] == [
        0,
        *range(d, -1, -1),
    ]
    assert [value(enc, model, "x", t) for t in range(d + 2)] == [0] * (d + 1) + [1]
    # Unavailable at ticks 1..d, available again at d + 1.
    for t in range(1, d + 1):
        assert (
            solve(enc, enc.active[5], chosen(enc, "A", "fire", 0), chosen(enc, "A", "fire", t))
            is None
        )
    assert (
        solve(enc, enc.active[5], chosen(enc, "A", "fire", 0), chosen(enc, "A", "fire", d + 1))
        is not None
    )
    trace = reach(cm, 5, V.x == "hi")
    assert len(trace) == d + 1
    replay(cm, trace, V.x == "hi")
    assert reach(cm, d, V.x == "hi") is None


def test_delayed_set_overrides_immediate_set_and_reads_pre_state():
    m = Model("override", horizon=4)
    m.var("x", levels=["lo", "mid", "hi"])
    m.counter("c", max=3)
    a = m.actor("A")
    a.action("late", effect=[Set("x", "hi"), SetIf(V.c == 0, "c", 3)], delay=1)
    a.action("bump_c", effect=Inc("c"))
    m.actor("B").action("now", effect=Set("x", "lo"))
    cm = m.compile()
    enc = encode(cm, 3)
    # late at 0; at tick 1 A bumps c and B sets lo: the delayed Set wins, and the SetIf
    # reads the pre-state (c == 0) although A's immediate Inc makes c 1.
    model = solve(
        enc,
        enc.active[2],
        chosen(enc, "A", "late", 0),
        chosen(enc, "B", "idle", 0),
        chosen(enc, "A", "bump_c", 1),
        chosen(enc, "B", "now", 1),
    )
    assert value(enc, model, "x", 2) == 2
    assert value(enc, model, "c", 2) == 3
    s0 = cm.initial_states()[0]
    s1 = cm.step(s0, (1, 0, 0))
    assert cm.step(s1, (2, 1, 0)) == tuple(value(enc, model, v.name, 2) for v in cm.variables)


# -- composition ---------------------------------------------------------------------------


def composition_model(strict):
    m = Model("compose", horizon=3)
    m.counter("n", max=2, init=1)
    m.counter("k", max=3)
    m.actor("A").action("push", effect=Bump("n", 1, strict=strict))
    m.actor("B").action("push", effect=Bump("n", 1))
    m.actor("C").action("set", effect=[Set("k", 2), Bump("k", 1)])
    m.actor("D").action("set", effect=Set("k", 2))
    m.actor("E").action("other", effect=Set("k", 1))
    return m.compile()


def test_bumps_sum_and_clamp_sets_win():
    cm = composition_model(strict=False)
    enc = encode(cm, 1)
    both = (chosen(enc, "A", "push", 0), chosen(enc, "B", "push", 0))
    model = solve(enc, enc.active[1], *both, chosen(enc, "C", "set", 0))
    assert value(enc, model, "n", 1) == 2  # 1 + 2 clamped to 2
    assert value(enc, model, "k", 1) == 3  # Set 2, then Bump 1
    # Agreeing Sets from two actors are fine; conflicting Sets are excluded.
    agree = (chosen(enc, "C", "set", 0), chosen(enc, "D", "set", 0))
    assert solve(enc, enc.active[1], *agree) is not None
    conflict = (chosen(enc, "D", "set", 0), chosen(enc, "E", "other", 0))
    assert solve(enc, enc.active[1], *conflict) is None
    assert value(enc, solve(enc, enc.active[1], conflict[1]), "k", 1) == 1


def test_strict_bump_out_of_range_is_excluded():
    cm = composition_model(strict=True)
    enc = encode(cm, 1)
    # n = 1: A's strict push alone is fine, with B's push it would reach 3 > 2.
    assert solve(enc, enc.active[1], chosen(enc, "A", "push", 0)) is not None
    both = (chosen(enc, "A", "push", 0), chosen(enc, "B", "push", 0))
    assert solve(enc, enc.active[1], *both) is None
    # B alone clamps (non-strict) even though A declared a strict bump.
    model = solve(enc, enc.active[1], chosen(enc, "B", "push", 0))
    assert value(enc, model, "n", 1) == 2
    m = Model("strict", horizon=2)
    m.counter("n", max=1)
    m.actor("A").action("push", effect=Bump("n", 1, strict=True))
    with pytest.raises(ModelError, match="strict Bump"):
        explore(m.compile())
    assert reach(m.compile(), 2, V.n == 1) is not None


def test_expression_set_is_clamped():
    m = Model("expr", horizon=2)
    m.counter("a", max=3, init=3)
    m.counter("b", max=2)
    m.actor("A").action("copy", effect=Set("b", V.a + 1))
    cm = m.compile()
    trace = reach(cm, 2, V.b == 2)
    assert len(trace) == 1
    replay(cm, trace, V.b == 2)


# -- latches, last actions, fairness, profiles, assumes ------------------------------------


def test_latch_freezes_first_value():
    m = Model("latch", horizon=5)
    m.counter("x", max=3)
    m.flag("go")
    a = m.actor("A", remember_last=True)
    a.action("inc", effect=Inc("x"))
    a.action("go", effect=Set("go", True))
    m.latch("x_at_go", of="x", when=V.go == True)  # noqa: E712
    cm = m.compile()
    # The latch copies x in the update after "go" is played, then stays.
    target = (V.x_at_go == "1") & (V.x == 3)
    trace = reach(cm, 5, target)
    assert len(trace) == 4
    replay(cm, trace, target)
    names = [cm.actors[0].actions[mv[0]].name for mv in trace.moves]
    assert names.count("go") == 1 and names.index("go") == 1
    assert reach(cm, 3, target) is None
    assert cm.level_name("last_A", trace.states[-1][cm.index["last_A"]]) == "inc"


def test_latch_set_in_initial_state():
    m = Model("latch0", horizon=2)
    m.var("x", levels=["a", "b"], init=None)
    m.latch("L", of="x", when=V.x == "b")
    cm = m.compile()
    enc = encode(cm, 0)
    s = enc.solver()
    s.add(enc.state[0][cm.index["x"]] == 1)
    assert s.check() == z3.sat
    assert s.model().eval(enc.state[0][cm.index["L"]]).as_long() == 2
    assert sorted(cm.initial_states()) == [(0, 0, 0), (0, 1, 2)]


def fairness_model():
    m = Model("fair", horizon=8)
    m.flag("alarm", init=True)
    m.counter("ignored", max=5)
    a = m.actor("A")
    a.action("ignore", effect=Inc("ignored"))
    a.action("respond")
    m.fairness("F", actor="A", trigger=V.alarm == True, within=2, responses=["respond"])  # noqa: E712
    return m


def test_fairness_forces_response_at_bound():
    m = fairness_model()
    cm = m.compile()
    target = V.ignored >= 3
    # Two unanswered ticks restrict A to "respond": three ignores need four ticks.
    assert reach(cm, 3, target) is None
    trace = reach(cm, 4, target)
    assert len(trace) == 4
    replay(cm, trace, target)
    names = [cm.actors[0].actions[mv[0]].name for mv in trace.moves]
    assert names.count("ignore") == 3 and names.index("respond") in (1, 2)
    enc = encode(cm, 3)
    assert solve(enc, enc.active[3], *(chosen(enc, "A", "ignore", t) for t in range(3))) is None
    # Relaxing F removes the restriction; the explicit engine agrees.
    result = relax(cm, 3, target)
    assert not result.reachable_as_is
    assert result.core == ["F"]
    assert result.minimum_size == 1 and result.minimal_sets == [["F"]]
    assert len(result.trace) == 3
    replay(m.compile(relax=["F"]), _drop_fair(cm, result.trace), target)


def _drop_fair(cm, trace):
    i = cm.index["fair_F"]
    states = [s[:i] + s[i + 1 :] for s in trace.states]
    return BmcTrace(states, trace.moves, trace.relaxed)


def profile_model():
    m = Model("profile", horizon=4)
    m.flag("provoked")
    m.flag("attacked")
    m.actor("A").action("attack", effect=Set("attacked", True))
    m.actor("B").action("provoke", effect=Set("provoked", True))
    m.profile("restrained", actor="A", forbid=["attack"], unless=V.provoked == True)  # noqa: E712
    return m


def test_profile_restricts_until_unless_holds():
    m = profile_model()
    target = V.attacked == True  # noqa: E712
    assert len(reach(m.compile(), 4, target)) == 1
    cm = m.compile(profile="restrained")
    trace = reach(cm, 4, target)
    assert len(trace) == 2
    replay(cm, trace, target)
    result = relax(cm, 1, target)
    assert result.minimal_sets == [["restrained"]] and result.core == ["restrained"]
    assert reach(cm, 1, target, relax=["restrained"]) is not None


def test_assume_restricts_initial_states():
    m = Model("assume", horizon=3)
    m.var("x", levels=["lo", "hi"], init=None)
    m.actor("A").action("lift", guard=V.x == "lo", effect=Set("x", "hi"))
    m.assume("starts_high", V.x == "hi")
    cm = m.compile()
    target = V.x == "lo"
    assert reach(cm, 3, target) is None
    trace = reach(cm, 3, target, relax=["starts_high"])
    assert len(trace) == 0
    result = relax(cm, 3, target)
    assert result.minimal_sets == [["starts_high"]] and result.minimum_size == 1
    # A guard relaxation is enumerated in the same way.
    assert relax(cm, 3, V.x == "hi").reachable_as_is
    assert cm.assumptions() == ["A.lift", "starts_high"]


def test_relax_minimum_two_and_bound():
    m = Model("two", horizon=3)
    m.flag("a")
    m.flag("b")
    m.actor("A").action("set_a", guard=FALSE, effect=Set("a", True))
    m.actor("B").action("set_b", guard=FALSE, effect=Set("b", True))
    m.actor("C").action("both", guard=FALSE, effect=[Set("a", True), Set("b", True)])
    m.actor("D").action("never", guard=FALSE)
    cm = m.compile()
    target = (V.a == True) & (V.b == True)  # noqa: E712
    result = relax(cm, 3, target)
    assert result.minimum_size == 1 and result.minimal_sets == [["C.both"]]
    assert set(result.core) == {"A.set_a", "C.both"} or set(result.core) == {
        "B.set_b",
        "C.both",
    }
    m2 = Model("two2", horizon=3)
    m2.flag("a")
    m2.flag("b")
    m2.actor("A").action("set_a", guard=FALSE, effect=Set("a", True))
    m2.actor("B").action("set_b", guard=FALSE, effect=Set("b", True))
    cm2 = m2.compile()
    result = relax(cm2, 3, target)
    assert result.minimum_size == 2 and result.minimal_sets == [["A.set_a", "B.set_b"]]
    assert relax(cm2, 3, target, max_relax=1).minimum_size is None
    assert relax(cm2, 0, target).minimum_size is None


# -- terminal states -----------------------------------------------------------------------


def test_terminal_states_are_frozen():
    m = Model("term", horizon=3)
    m.counter("x", max=3)
    m.actor("A").action("inc", effect=Inc("x"))
    m.ending("DONE", V.x == 2)
    cm = m.compile()
    enc = encode(cm, 6)
    model = solve(enc, enc.active[6], chosen(enc, "A", "inc", 0), chosen(enc, "A", "inc", 1))
    states = [tuple(value(enc, model, v.name, t) for v in cm.variables) for t in range(7)]
    assert states[2] == (2, 2) and all(s == states[2] for s in states[2:])
    # Without the ending, the horizon freezes the state at tick 3.
    model = solve(enc, enc.active[6], chosen(enc, "A", "idle", 0))
    states = [tuple(value(enc, model, v.name, t) for v in cm.variables) for t in range(7)]
    assert states[3][0] == 3 and all(s == states[3] for s in states[3:])
    # Nothing is reachable past an ending: x == 3 needs passing through DONE.
    assert reach(cm, 6, V.x == 3) is None
    assert len(reach(cm, 6, "DONE")) == 2
    assert reach(cm, 6, "HORIZON").states[-1][0] == 3


def test_untimed_model_with_cycle():
    m = Model("cycle", horizon=None)
    m.var("pos", levels=["a", "b", "c"])
    m.counter("laps", max=2)
    walker = m.actor("W", idle=False)
    walker.action("ab", guard=V.pos == "a", effect=Set("pos", "b"))
    walker.action("bc", guard=V.pos == "b", effect=Set("pos", "c"))
    walker.action("ca", guard=V.pos == "c", effect=[Set("pos", "a"), Inc("laps")])
    cm = m.compile()
    assert not cm.timed and "tick" not in cm.index
    enc = encode(cm, 12)
    assert solve(enc, enc.active[12]) is not None  # the cycle allows unbounded runs
    target = (V.laps == 2) & (V.pos == "b")
    assert reach(cm, 6, target) is None
    trace = reach(cm, 12, target)
    assert len(trace) == 7
    replay(cm, trace, target)
    g = explore(cm)
    assert g.size() == 9


# -- rendering -----------------------------------------------------------------------------


def test_render_matches_explicit_trace():
    m = Model("render", horizon=4)
    m.var("x", levels=["lo", "mid", "hi"])
    m.flag("f")
    a = m.actor("A", remember_last=True)
    a.action("up", effect=Bump("x", 1))
    a.action("slow", effect=Set("f", True), delay=1)
    m.nature().event("drop", guard=V.x == "hi", effect=Bump("x", -1))
    m.ending("TOP", (V.x == "hi") & (V.f == True))  # noqa: E712
    cm = m.compile()
    trace = reach(cm, 4, "TOP")
    g = explore(cm)
    explicit = Trace(
        [(g.index[s], mv) for s, mv in zip(trace.states, trace.moves, strict=False)]
        + [(g.index[trace.states[-1]], None)]
    )
    assert trace.render(cm) == explicit.render(g)
    assert "ending: TOP" in trace.render(cm)
    w = witness(g, g.initial[0], g.ending_states("TOP"))
    assert len(w) - 1 == len(trace)


def test_targets_by_name_and_errors():
    m = profile_model()
    m.invariant("calm", V.attacked == False)  # noqa: E712
    cm = m.compile()
    assert len(reach(cm, 2, "calm")) == 0
    assert reach(cm, 2, ~V.invariant("calm")) is not None
    with pytest.raises(ModelError):
        reach(cm, 2, "nope")
    with pytest.raises(ModelError):
        reach(cm, 2, V.attacked == "maybe")
    with pytest.raises(ModelError):
        reach(cm, 2, V.attacked == True, relax=["nope"])  # noqa: E712
    with pytest.raises(ValueError):
        encode(cm, -1)


def test_monotone_decrease_is_excluded():
    m = Model("monotone", horizon=3)
    m.var("g", levels=["g0", "g1", "g2"], init="g2", monotone=True)
    m.flag("moved")
    a = m.actor("A")
    a.action("drop", effect=[Set("g", "g1"), Set("moved", True)])
    a.action("mark", effect=Set("moved", True))
    cm = m.compile()
    with pytest.raises(ModelError, match="monotone"):
        explore(cm)
    assert reach(cm, 3, V.g == "g1") is None
    trace = reach(cm, 3, V.moved == True)  # noqa: E712
    assert [cm.actors[0].actions[mv[0]].name for mv in trace.moves] == ["mark"]


# -- cadence -------------------------------------------------------------------------------


def cadence_model(cadence):
    m = Model("cadence", horizon=8)
    m.counter("x", max=4)
    m.counter("y", max=4)
    m.flag("alarm")
    a = m.actor("A", cadence=cadence)
    a.action("push", effect=Bump("x", 1))
    a.action("raise_alarm", effect=Set("alarm", True))
    a.action("respond", guard=V.alarm, effect=[Set("alarm", False), Bump("y", 1)])
    m.fairness("F", actor="A", trigger=V.alarm, within=1, responses=["respond"])
    return m


@pytest.mark.parametrize("cadence, ticks", [(1, 2), (2, 3), (3, 4)])
def test_cadence_spaces_decisions(cadence, ticks):
    """Two pushes need k + 1 ticks with cadence k; BMC and the explicit engine agree."""
    cm = cadence_model(cadence).compile()
    target = V.x >= 2
    assert reach(cm, ticks - 1, target) is None
    trace = reach(cm, ticks, target)
    assert len(trace) == ticks
    replay(cm, trace, target)
    g = explore(cm)
    assert len(witness(g, g.initial[0], g.states_where(target))) == ticks + 1


def test_a_binding_fairness_restriction_overrides_the_cadence_in_bmc():
    """Alarm raised at tick 0, answered at tick 1 although the cadence counter is 2 there:
    y = 1 at tick 2. With F relaxed the answer waits for the counter: y = 1 at tick 4."""
    cm = cadence_model(3).compile()
    target = V.y >= 1
    trace = reach(cm, 8, target)
    assert [cm.actors[0].actions[mv[0]].name for mv in trace.moves] == ["raise_alarm", "respond"]
    replay(cm, trace, target)
    enc = encode(cm, 2)
    s = solve(enc, enc.active[2], chosen(enc, "A", "raise_alarm", 0))
    assert s is not None
    assert [value(enc, s, "cadence_A", t) for t in range(3)] == [0, 2, 2]
    result = relax(cm, 8, target)
    assert result.reachable_as_is and len(result.trace) == 2
    relaxed = reach(cm, 8, target, relax={"F"})
    assert [cm.actors[0].actions[mv[0]].name for mv in relaxed.moves] == [
        "raise_alarm",
        "idle",
        "idle",
        "respond",
    ]
