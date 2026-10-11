"""Brute-force relaxations, informativeness, sensitivity, clusters and the budget."""

import pytest

from wavefront.analysis import (
    RelaxSets,
    budget,
    cluster,
    informativeness,
    minimal_relaxation_size,
    relax_explicit,
    sensitivity,
    signature,
)
from wavefront.engine import Trace, explore, witness
from wavefront.model import ModelError

from .games import crisis, door, ladder, locks


def test_relax_explicit_finds_all_minimal_sets_smallest_first():
    r = relax_explicit(locks(with_alt=True), "DONE", max_size=2)
    assert isinstance(r, RelaxSets)
    assert r == [["C.alt"], ["A.go", "B.go"]]
    assert r.assumptions == ["A.go", "B.go", "C.alt"]
    assert r.minimum_size == 1 and r.max_size == 2
    assert r.ill_formed == [] and r.undecided == []


def test_relax_explicit_respects_max_size():
    assert relax_explicit(locks(), "DONE", max_size=1) == []
    assert relax_explicit(locks(), "DONE", max_size=1).minimum_size is None
    assert relax_explicit(locks(), "DONE", max_size=2) == [["A.go", "B.go"]]


def test_relax_explicit_reachable_base_needs_nothing():
    assert relax_explicit(door(), "OUT") == [[]]
    assert relax_explicit(door(), "HORIZON") == [[]]


def test_relax_explicit_forceability_is_per_coalition():
    m = locks()
    assert relax_explicit(m, "DONE", coalition={"A", "B"}) == [["A.go", "B.go"]]
    # A alone cannot force DONE even with both guards relaxed: B may stay idle
    assert relax_explicit(m, "DONE", coalition={"A"}) == []
    # fairness lets A force OUT; it is an assumption like any other
    assert relax_explicit(door(), "OUT", coalition={"A"}) == [[]]


def test_relax_explicit_reports_ill_formed_relaxations():
    r = relax_explicit(locks(with_clash=True), "DONE", max_size=2)
    assert r == [["A.go", "B.go"]]
    bad = [s for s, _ in r.ill_formed]
    assert ["D.clash"] in bad
    assert all("conflicting Set" in msg for _, msg in r.ill_formed)
    # supersets of an ill-formed set are tried (and fail the same way), not skipped
    assert ["A.go", "D.clash"] in bad


def test_relax_explicit_budget_is_reported_as_undecided():
    r = relax_explicit(locks(), "DONE", max_size=1, max_states=2)
    assert r == [] and len(r.undecided) == 3 and r.ill_formed == []


def test_relax_explicit_rejects_unknown_ending():
    with pytest.raises(ModelError, match="no ending named 'NOPE'"):
        relax_explicit(locks(), "NOPE")


def test_minimal_relaxation_size_and_informativeness():
    m = locks()
    assert minimal_relaxation_size(m, "DONE", 2) == 2
    assert minimal_relaxation_size(m, "DONE", 1) is None
    controls = [
        ("DONE", ">=", 2),  # holds
        ("DONE", "==", 2),  # holds
        ("DONE", "<=", 1),  # fails
        ("DONE", ">=", 3),  # fails: rho is 2
    ]
    assert informativeness(m, controls) == 0.5
    assert informativeness(m, [("DONE", ">=", 0)]) == 1.0
    assert informativeness(m, [("HORIZON", "==", 0)]) == 1.0
    with pytest.raises(ValueError):
        informativeness(m, [])
    with pytest.raises(ValueError):
        informativeness(m, [("DONE", "<", 1)])
    with pytest.raises(ModelError):
        informativeness(m, [("NOPE", "<=", 1)])


def test_sensitivity_rows_sorted_by_effect():
    rows = sensitivity(ladder(), "low", {"P"})
    assert [(r.variable, r.from_level, r.to_level) for r in rows] == [
        ("shield", "True", "False"),
        ("x", "0", "1"),
    ]
    shield, x = rows
    assert (shield.base_in_kernel, shield.new_in_kernel, shield.flips) == (1, 0, 1)
    # outside the kernel the shortest distance to its outside is zero
    assert (shield.base_shortest, shield.new_shortest) == (3, 0)
    assert (x.flips, x.base_shortest, x.new_shortest) == (0, 3, 2)
    assert x.base_forced is None and x.error is None


def test_sensitivity_with_adversary_and_explicit_initial_states():
    m = ladder()
    cm = m.compile()
    start = [(2, 1)]  # x = 2, shield on
    rows = sensitivity(m, "low", {"P"}, adversary={"Nature"}, initial=start)
    by_key = {(r.variable, r.to_level): r for r in rows}
    assert set(by_key) == {("x", "1"), ("x", "3"), ("shield", "False")}
    up = by_key[("x", "3")]
    assert up.flips == 1 and up.new_forced == 0 and up.base_forced is None
    assert rows[-1].variable == "x" and rows[-1].to_level == "1"
    assert cm.variables[0].name == "x"


def test_sensitivity_rejects_unknown_invariant():
    with pytest.raises(ModelError, match="no invariant named"):
        sensitivity(ladder(), "nope", {"P"})


def test_cluster_by_non_trivial_guards():
    g = explore(crisis().compile())
    war = g.ending_states("WAR")
    traces = [witness(g, s, war) for s in range(g.size())]
    traces = [t for t in traces if t is not None and len(t) > 1]
    clusters = cluster(traces, g)
    assert sum(len(c.traces) for c in clusters) == len(traces)
    for c in clusters:
        assert all(signature(t, g) == c.signature for t in c.traces)
        assert len(c.representative) == min(len(t) for t in c.traces)
        # Nature's built-in none has a trivial guard and never counts
        assert ("Nature", "none") not in c.signature
    sizes = [len(c.traces) for c in clusters]
    assert sizes == sorted(sizes, reverse=True)
    longest = max(traces, key=len)
    sig = signature(longest, g)
    assert ("P", "provoke") in sig and ("Nature", "attack") in sig


def test_relaxed_guards_count_as_trivial():
    g = explore(locks().compile(relax={"A.go", "B.go"}))
    t = witness(g, g.initial[0], g.ending_states("DONE"))
    assert isinstance(t, Trace)
    assert signature(t, g) == frozenset()


def test_budget_delegates():
    cm = crisis().compile()
    assert budget(cm) == cm.budget()
    assert budget(cm)["speculative_actions"] == 1
