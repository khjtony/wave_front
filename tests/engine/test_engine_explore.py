"""Breadth-first exploration and the Graph helpers."""

import pytest

from wavefront.engine import BudgetExceeded, Graph, explore
from wavefront.model import Bump, Inc, Model, ModelError, Set, V


def counter_game(horizon=3):
    m = Model("counter", horizon=horizon)
    m.counter("x", max=3)
    p = m.actor("P")
    p.action("up", effect=Inc("x"))
    m.nature().event("down", guard=V.x > 0, effect=Bump("x", -1))
    m.ending("TOP", V.x == 3)
    return m


def test_graph_shape_and_alignment():
    cm = counter_game().compile()
    g = explore(cm)
    assert isinstance(g, Graph)
    assert g.initial == [0] and g.states[0] == (0, 0) and g.depth[0] == 0
    for i, s in enumerate(g.states):
        assert g.index[s] == i
        assert len(g.moves[i]) == len(g.succ[i])
        assert g.terminal[i] == (g.ending[i] is not None)
        if g.terminal[i]:
            assert g.moves[i] == [] and g.succ[i] == []
        else:
            assert g.avail[i] == cm.available(s)
            for jm, t in zip(g.moves[i], g.succ[i], strict=True):
                assert g.states[t] == cm.step(s, jm)
                assert g.depth[t] <= g.depth[i] + 1
    # Ids are assigned breadth-first.
    assert g.depth == sorted(g.depth)
    assert g.ending_states("TOP") == {i for i, s in enumerate(g.states) if s[1] == 3}
    assert all(g.states[i][0] == 3 for i in g.ending_states("HORIZON"))


def test_states_where_variants():
    m = counter_game()
    m.invariant("low", V.x <= 1)
    g = explore(m.compile())
    by_expr = g.states_where(V.x <= 1)
    assert by_expr == g.states_where("low")
    assert by_expr == g.states_where(lambda s: s[1] <= 1)
    assert g.states_where("TOP") == g.ending_states("TOP")
    with pytest.raises(ModelError):
        g.states_where("nothing")
    assert g.size() == len(g.states)


def test_explicit_initial_states_and_validation():
    cm = counter_game().compile()
    g = explore(cm, initial=[(0, 2)])
    assert g.states[0] == (0, 2)
    assert min(s[0] for s in g.states) == 0
    with pytest.raises(ModelError):
        explore(cm, initial=[(0, 9)])
    with pytest.raises(ModelError):
        explore(cm, initial=[(0,)])


def test_budget_exceeded_and_progress():
    cm = counter_game(horizon=6).compile()
    full = explore(cm)
    with pytest.raises(BudgetExceeded):
        explore(cm, max_states=full.size() - 1)
    assert explore(cm, max_states=full.size()).size() == full.size()
    calls = []
    explore(cm, on_progress=lambda done, found: calls.append((done, found)))
    assert calls[-1] == (full.size(), full.size())


def test_moves_are_the_product_of_available_actions():
    m = Model("m", horizon=2)
    m.var("a", levels=["x", "y"])
    p = m.actor("P")
    p.action("one", effect=Set("a", "y"))
    p.action("two", guard=V.a == "y")
    q = m.actor("Q")
    q.action("three")
    g = explore(m.compile())
    assert g.moves[0] == [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 0)]
    assert g.avail[0] == [[0, 1], [0, 1], [0]]


def test_untimed_model_with_cycles():
    m = Model("cycle", horizon=None)
    m.var("pos", levels=["a", "b", "c"])
    p = m.actor("P", idle=False)
    p.action("next", effect=Bump("pos", 1), guard=V.pos != "c")
    p.action("back", effect=Set("pos", "a"), guard=V.pos == "c")
    g = explore(m.compile())
    assert g.size() == 3
    assert g.succ == [[1], [2], [0]]
    assert not any(g.terminal)
    assert g.depth == [0, 1, 2]
