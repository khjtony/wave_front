"""Strategy uniformity and pivotal coalitions."""

import pytest

from wavefront.analysis import is_uniform, pivotal, strategy_closure, viability
from wavefront.engine import attractor, explore
from wavefront.model import ModelError

from .games import coin, crisis, locks, relay, tug


def test_perfect_information_strategy_is_not_uniform_under_a_hidden_coin():
    g = explore(coin(hidden=True).compile())
    win = attractor(g, {"P"}, g.ending_states("WIN"))
    assert set(g.initial) <= win.win
    res = is_uniform(g, {"P"}, win.strategy)
    assert not res.uniform and not res
    assert res.conflicts == [("P", *sorted(g.initial))]
    assert not res.jointly_uniform
    assert res.joint_conflicts == [tuple(sorted(g.initial))]


def test_strategy_is_uniform_when_the_coin_is_observed():
    g = explore(coin(hidden=False).compile())
    win = attractor(g, {"P"}, g.ending_states("WIN"))
    res = is_uniform(g, {"P"}, win.strategy)
    assert res.uniform and res.conflicts == []
    assert res.jointly_uniform and res.joint_conflicts == []
    # Nature observes everything, so any coalition with Nature is uniform
    assert is_uniform(g, {"P", "Nature"}, {s: (0, 0) for s in g.initial}).uniform


def test_joint_check_passes_but_a_blind_member_conflicts():
    g = explore(relay().compile())
    win = attractor(g, {"A", "B"}, g.ending_states("WIN"))
    assert set(g.initial) <= win.win
    used = {s: win.strategy[s] for s in g.initial}
    # B's call depends on the coin, which only A sees
    assert used[g.initial[0]][1] != used[g.initial[1]][1]
    res = is_uniform(g, {"A", "B"}, used)
    assert res.jointly_uniform and res.joint_conflicts == []
    assert not res.uniform
    assert res.conflicts == [("B", *sorted(g.initial))]
    # A's own component (idle in both states) is fine
    assert all(member == "B" for member, _, _ in res.conflicts)


def test_strategy_closure_follows_the_strategy_only():
    g = explore(crisis().compile())
    k = viability(g, {"P"}, "peace")
    calm = g.initial[0]
    used = strategy_closure(g, {"P"}, k.strategy, [calm])
    # P waits in calm forever: only the calm state is used
    assert used == {calm: k.strategy[calm]}


def test_pivotal_antichains():
    g = explore(crisis().compile())
    r = pivotal(g, "WAR")
    assert r.forcing == []
    assert r.blocking == [frozenset({"P"})]
    r = pivotal(g, "WAR", include_nature=True)
    assert r.forcing == [frozenset({"P", "Nature"})]
    assert r.blocking == [frozenset({"P"}), frozenset({"Nature"})]


def test_pivotal_needs_both_members():
    g = explore(locks().compile(relax={"A.go", "B.go"}))
    r = pivotal(g, "DONE")
    assert r.forcing == [frozenset({"A", "B"})]
    assert r.blocking == [frozenset({"A"}), frozenset({"B"})]


def test_pivotal_rejects_unknown_ending():
    g = explore(tug().compile())
    with pytest.raises(ModelError, match="no ending named 'X'"):
        pivotal(g, "X")
    with pytest.raises(ModelError, match="no ending named 'HORIZON'"):
        pivotal(g, "HORIZON")  # untimed


def test_pivotal_with_restricted_initial_states_and_actors():
    g = explore(coin(hidden=True).compile())
    r = pivotal(g, "WIN")
    assert r.forcing == [frozenset({"P"})]  # perfect-information upper bound
    assert r.blocking == [frozenset({"P"})]
    r = pivotal(g, "WIN", actors=[], include_nature=True)
    assert r.forcing == [] and r.blocking == []
    r = pivotal(g, "WIN", initial=[])
    assert r.forcing == [frozenset()] and r.blocking == [frozenset()]
    r = pivotal(g, "HORIZON")
    assert r.forcing == [] and r.blocking == [frozenset()]
