"""Attractors, safety kernels and contested regions on hand-built games."""

import pytest

from wavefront.engine import attractor, contested, explore, safe
from wavefront.model import Bump, Model, ModelError, Set, V


def sid(g, **values):
    """Id of the unique state with the given level names."""
    cm = g.model
    hits = [
        i
        for i, s in enumerate(g.states)
        if all(cm.level_name(k, s[cm.index[k]]) == str(v) for k, v in values.items())
    ]
    assert len(hits) == 1, hits
    return hits[0]


def pennies():
    """Matching pennies: A wins on a match, B on a mismatch; one simultaneous round."""
    m = Model("pennies", horizon=1)
    m.var("a", levels=["unset", "h", "t"])
    m.var("b", levels=["unset", "h", "t"])
    a = m.actor("A", idle=False)
    b = m.actor("B", idle=False)
    for side in ("h", "t"):
        a.action(side, effect=Set("a", side))
        b.action(side, effect=Set("b", side))
    m.ending("MATCH", (V.a == V.b) & (V.a != "unset"))
    m.ending("MISMATCH", (V.a != V.b) & (V.a != "unset") & (V.b != "unset"))
    return explore(m.compile())


def test_matching_pennies_is_contested():
    g = pennies()
    match = g.ending_states("MATCH")
    r = contested(g, {"A"}, match, "reach")
    assert 0 in r.contested
    assert 0 not in r.forced and 0 not in r.blocked
    assert r.forced == match and r.blocked == g.ending_states("MISMATCH")
    # B cannot keep "no match" and A plus Nature cannot force a match either.
    k = contested(g, {"B"}, set(range(g.size())) - match, "keep")
    assert 0 in k.contested
    # Together the two players can force a match; the empty coalition cannot.
    joint = attractor(g, {"A", "B"}, match)
    assert 0 in joint.win and joint.rank[0] == 1
    assert g.move_names((*joint.strategy[0], 0))[0] == g.move_names((*joint.strategy[0], 0))[1]
    assert 0 not in attractor(g, set(), match).win
    assert 0 in attractor(g, {"A", "B", "Nature"}, match).win


def chain():
    """c -> b; b -> a or b -> t0 directly; a -> t1. Targets t0 and t1."""
    m = Model("chain", horizon=None)
    m.var("pos", levels=["c", "b", "a", "t0", "t1"])
    p = m.actor("P", idle=False)
    p.action("c_to_b", guard=V.pos == "c", effect=Set("pos", "b"))
    p.action("b_to_a", guard=V.pos == "b", effect=Set("pos", "a"))
    p.action("b_to_t0", guard=V.pos == "b", effect=Set("pos", "t0"))
    p.action("a_to_t1", guard=V.pos == "a", effect=Set("pos", "t1"))
    m.ending("T0", V.pos == "t0")
    m.ending("T1", V.pos == "t1")
    return explore(m.compile())


def test_rank_is_the_stage_index_on_a_chain():
    g = chain()
    target = g.ending_states("T0") | g.ending_states("T1")
    r = attractor(g, {"P"}, target)
    ranks = {g.model.level_name("pos", g.states[s][0]): k for s, k in r.rank.items()}
    # b reaches t0 in one step even though the route via a is found from t1 as well.
    assert ranks == {"t0": 0, "t1": 0, "a": 1, "b": 1, "c": 2}
    b = sid(g, pos="b")
    assert g.model.actors[0].actions[r.strategy[b][0]].name == "b_to_t0"


def keep_game():
    """P keeps x <= 2 against Nature: inc adds 1, jump sets 3 at x == 2; dec subtracts 1."""
    m = Model("keep", horizon=None)
    m.counter("x", max=3)
    m.actor("P").action("dec", effect=Bump("x", -1))
    n = m.nature()
    n.event("inc", effect=Bump("x", 1))
    n.event("jump", guard=V.x == 2, effect=Set("x", 3))
    return explore(m.compile())


def test_safety_kernel_and_strategy():
    g = keep_game()
    phi = g.states_where(V.x <= 2)
    k = safe(g, {"P"}, phi)
    assert k.kernel == phi
    x2 = sid(g, x=2)
    assert g.model.actors[0].actions[k.strategy[x2][0]].name == "dec"
    # Without P, Nature alone keeps nothing safe from x == 2.
    assert x2 not in safe(g, set(), phi).kernel
    # Nature cannot force leaving phi; P keeps it: nothing is contested.
    r = contested(g, {"P"}, phi, "keep")
    assert r.forced == phi and r.blocked == g.states_where(V.x == 3) and not r.contested
    # Nature with P's help can force x == 3.
    assert x2 in attractor(g, {"P", "Nature"}, g.states_where(V.x == 3)).win


def test_terminal_states_in_fixpoints():
    m = Model("term", horizon=2)
    m.var("v", levels=["ok", "bad", "end"])
    p = m.actor("P")
    p.action("finish", effect=Set("v", "end"))
    p.action("spoil", effect=Set("v", "bad"))
    m.ending("END", V.v == "end")
    m.ending("BAD", V.v == "bad")
    g = explore(m.compile())
    end, bad = g.states_where(V.v == "end"), g.states_where(V.v == "bad")
    phi = g.states_where(V.v != "bad")
    k = safe(g, {"P"}, phi)
    assert end <= k.kernel and not bad & k.kernel and 0 in k.kernel
    # HORIZON states satisfying phi are in the kernel.
    assert all(i in k.kernel for i in g.ending_states("HORIZON"))
    # A terminal state is in an attractor iff it is in the target.
    r = attractor(g, {"P"}, end)
    assert not bad & r.win and end <= r.win and r.rank[0] == 1


def test_nature_in_the_coalition():
    m = Model("weather", horizon=1)
    m.var("sky", levels=["grey", "sun", "rain"])
    n = m.nature()
    n.event("sun", effect=Set("sky", "sun"))
    n.event("rain", effect=Set("sky", "rain"))
    m.actor("P")
    m.ending("SUN", V.sky == "sun")
    g = explore(m.compile())
    sun = g.ending_states("SUN")
    assert 0 in attractor(g, {"Nature"}, sun).win
    assert 0 not in attractor(g, {"P"}, sun).win
    r = attractor(g, {"Nature", "P"}, sun)
    assert len(r.strategy[0]) == 2  # sub-move over (P, Nature) in actor order


def test_unknown_actor_and_bad_kind():
    g = pennies()
    with pytest.raises(ModelError, match="unknown actor 'Z'"):
        attractor(g, {"Z"}, set())
    with pytest.raises(ValueError):
        contested(g, {"A"}, set(), "maybe")  # type: ignore[arg-type]
    with pytest.raises(ModelError):
        safe(g, {"A"}, {10_000})
