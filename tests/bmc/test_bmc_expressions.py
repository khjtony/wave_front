"""Expression translation: every node kind, in boolean and integer position.

1. The Z3 translation of each expression equals ``cm.evaluate`` on every state of a small
   model (all variable values, not only reachable ones).
2. Each condition is used as an action guard and as an ending, and each value expression
   as a ``Set`` value; ``reach`` must then agree with the explicit engine on every target
   and its traces must replay with ``cm.step``.

Node kinds covered: Const, Lit, VarRef (a flag used directly as a condition, levels and
counters in comparisons and arithmetic, ``tick``), Cmp (with literals and VarRef vs
VarRef), And, Or, Not (and ``implies``), InSet, Arith (+, -), Min, Max, Ite (condition and
integer branches), InvariantRef and EndingRef.
"""

import itertools

import pytest
import z3

from bmc.rich_models import check_replay, explicit_distance, target_ids
from wavefront.bmc import encode, reach, relax
from wavefront.engine import explore
from wavefront.model import FALSE, TRUE, Bump, Inc, Ite, Max, Min, Model, Set, V
from wavefront.model.compile import is_condition
from wavefront.model.expr import VarRef

CONDITIONS = {
    "const_true": TRUE,
    "const_false": FALSE,
    "flag": V.deal,
    "not_flag": ~V.deal,
    "flag_and_flag": V.deal & V.f2,
    "flag_or_cmp": V.deal | (V.cnt >= 2),
    "flag_eq_true": V.deal == True,  # noqa: E712
    "flag_ne_false": V.f2 != False,  # noqa: E712
    "implies": V.deal.implies(V.f2),
    "level_eq": V.lvl == "mid",
    "level_ne": V.lvl != "lo",
    "level_lt_counter": V.lvl < V.cnt2,
    "counter_eq_counter": V.cnt == V.cnt2,
    "level_gt_counter": V.lvl > V.cnt,
    "inset": V.lvl.is_in(["lo", "hi"]),
    "inset_empty": V.lvl.is_in([]),
    "arith_min": V.cnt + 1 >= Min(V.cnt2, 2),
    "arith_max": Max(V.cnt, V.cnt2) - 1 == 1,
    "arith_sub": V.cnt - V.cnt2 < 0,
    "lit_left": Ite(V.deal, 1, 2) == V.cnt2,
    "ite_conditions": Ite(V.deal, V.cnt >= 2, V.lvl == "hi"),
    "ite_flags": Ite(V.f2, V.deal, ~V.deal),
    "ite_const": Ite(V.deal, TRUE, V.f2),
    "ite_integer": Ite(V.lvl >= "mid", 2, V.cnt) <= V.cnt2,
    "flag_sum": V.deal + V.f2 == 1,
    "bool_in_arith": (V.cnt >= 1) + 1 == 2,
    "invariant": V.invariant("low_count"),
    "not_invariant": ~V.invariant("low_count") & V.deal,
    "tick": V.tick >= 2,
}

VALUES = {
    "counter": V.cnt,
    "sum": V.cnt + V.cnt2,
    "clamp_low": V.cnt - 2,
    "clamp_high": V.cnt + 5,
    "min_level": Min(V.cnt, V.lvl),
    "max3": Max(V.cnt2, V.lvl, 1),
    "ite_arith": Ite(V.deal, V.cnt + 1, 0),
    "ite_level_lit": Ite(V.lvl > "lo", V.cnt, V.cnt2),
    "flag": V.deal,
    "flag_sum": V.deal + V.f2,
    "bool_node": (V.cnt >= 2) + V.deal,
    "level": V.lvl,
    "ite_invariant": Ite(V.invariant("low_count"), 3, 1),
    "ite_ending": Ite(V.ending("STOP"), 0, 2),
    "ite_bool_lits": Ite(V.f2, True, False),
    "tick": V.tick - 1,
}


def base_model(name):
    m = Model(name, horizon=3)
    m.flag("deal")
    m.flag("f2", init=None)
    m.var("lvl", levels=["lo", "mid", "hi"])
    m.counter("cnt", max=3)
    m.counter("cnt2", max=2, init=None)
    m.counter("out", max=3)
    m.flag("marker")
    a = m.actor("A")
    a.action("seal", effect=Set("deal", True))
    a.action("up", effect=Inc("cnt"))
    a.action("lift", effect=Bump("lvl", 1))
    n = m.nature()
    n.event("tick2", effect=Inc("cnt2"))
    n.event("flip", effect=Set("f2", True))
    m.invariant("low_count", V.cnt <= 1)
    return m


# -- 1. translation equals evaluation on every state ---------------------------------------


def all_states(cm):
    return itertools.product(*(range(v.size) for v in cm.variables))


def test_translation_equals_evaluation_on_every_state():
    m = base_model("eval")
    m.ending("STOP", (V.cnt == 3) & V.deal)
    cm = m.compile()
    enc = encode(cm, 0)
    exprs = {**CONDITIONS, **{f"v_{k}": v for k, v in VALUES.items()}}
    exprs["ending_ref"] = V.ending("STOP") | V.f2
    translated = {k: enc.expr(e, 0) for k, e in exprs.items()}
    conditions = {k: enc.condition(e, 0) for k, e in exprs.items()}
    checked = 0
    for state in all_states(cm):
        sub = [(x, z3.IntVal(v)) for x, v in zip(enc.state[0], state, strict=True)]
        for key, e in exprs.items():
            expected = cm.evaluate(e, state)
            got = z3.simplify(z3.substitute(translated[key], *sub))
            if z3.is_bool(got):
                assert z3.is_true(got) == bool(expected), (key, state)
                assert is_condition(e) or isinstance(e, VarRef)  # a bare flag
            else:
                assert got.as_long() == expected, (key, state)
            cond = z3.simplify(z3.substitute(conditions[key], *sub))
            assert z3.is_true(cond) == bool(expected), (key, state)
            checked += 1
    assert checked == len(exprs) * 4 * 2 * 2 * 3 * 4 * 3 * 4 * 2


# -- 2. the same expressions inside a model -------------------------------------------------


def cross_check(m, extra_targets=()):
    cm = m.compile()
    g = explore(cm)
    for target in [*m.endings, "HORIZON", V.marker, *extra_targets]:
        goal = target_ids(g, target)
        dist = explicit_distance(g, goal)
        expected = dist if dist is not None and dist <= 3 else None
        trace = reach(cm, 3, target)
        assert (None if trace is None else len(trace)) == expected, target
        if trace is not None:
            check_replay(cm, trace, lambda s: g.index.get(s) in goal)
    return cm


@pytest.mark.parametrize("key", list(CONDITIONS))
def test_condition_as_guard(key):
    m = base_model(f"guard_{key}")
    m.ending("STOP", (V.cnt == 3) & V.deal)
    m.actor("B").action("act", guard=CONDITIONS[key], effect=Set("marker", True))
    cm = cross_check(m)
    if key not in ("const_true",):
        assert "B.act" in cm.assumptions()


@pytest.mark.parametrize("key", list(CONDITIONS))
def test_condition_as_ending(key):
    m = base_model(f"ending_{key}")
    m.ending("E", CONDITIONS[key])
    cm = cross_check(m)
    result = relax(cm, 3, "E")
    assert result.reachable_as_is == (reach(cm, 3, "E") is not None)


@pytest.mark.parametrize("key", list(VALUES))
def test_value_as_set_value(key):
    m = base_model(f"value_{key}")
    m.ending("STOP", (V.cnt == 3) & V.deal)
    m.actor("B").action("assign", effect=[Set("out", VALUES[key]), Set("marker", True)])
    cross_check(m, [V.out == n for n in range(4)])


def test_ending_reference_in_guard():
    m = base_model("ending_ref_guard")
    m.ending("STOP", (V.cnt == 3) & V.deal)
    m.ending("OTHER", V.marker & ~V.ending("STOP"))
    m.actor("B").action("act", guard=~V.ending("STOP") & V.deal, effect=Set("marker", True))
    cross_check(m)


def test_bare_flag_ending_in_relax():
    """Regression: an ending that is a flag used directly (``V.deal``) crashed ``relax``
    with a Z3 sort mismatch."""
    m = Model("standoff", horizon=4)
    m.counter("tension", max=3)
    m.flag("deal")
    m.actor("A").action("provoke", effect=Bump("tension", 1))
    m.actor("B").action("sign", guard=V.tension >= 2, effect=Set("deal", True))
    m.ending("WAR", V.tension == 3)
    m.ending("DEAL", V.deal)
    cm = m.compile()
    result = relax(cm, 4, "DEAL")
    assert result.reachable_as_is and len(result.trace) == 3
    result = relax(cm, 2, "DEAL")
    assert result.minimum_size == 1 and result.minimal_sets == [["B.sign"]]
    assert len(reach(cm, 4, V.deal)) == 3
    assert len(reach(cm, 4, ~V.deal & (V.tension == 3))) == 3
    assert reach(cm, 4, "HORIZON") is not None
