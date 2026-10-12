"""Relaxing a fairness constraint from an explicit initial state must not be ill-formed."""

from wavefront.analysis import relax_explicit
from wavefront.analysis._common import remap_states
from wavefront.model import Bump, Model, V, compile


def _model() -> Model:
    m = Model("remap", horizon=4)
    m.counter("x", max=3, init=0)
    a = m.actor("A")
    m.nature()
    a.action("up", guard=V.x < 2, effect=Bump("x", 1))
    a.action("jump", guard=V.x >= 2, effect=Bump("x", 1))
    m.fairness("move", actor="A", trigger=V.x < 3, within=1, responses=["up", "jump"])
    m.ending("TOP", V.x == 3)
    return m


def test_remap_drops_removed_counters_and_keeps_values():
    m = _model()
    base = compile(m)
    relaxed = compile(m, relax=frozenset({"move"}))
    assert len(relaxed.variables) == len(base.variables) - 1
    state = base.initial_states()[0]
    (mapped,) = remap_states(base, relaxed, [state])
    assert len(mapped) == len(relaxed.variables)
    assert mapped[relaxed.index["x"]] == state[base.index["x"]]


def test_relax_from_explicit_initial_state_tries_fairness_without_ill_formed():
    m = _model()
    base = compile(m)
    start = base.initial_states()[0]
    sets = relax_explicit(m, "TOP", max_size=1, initial=[start])
    assert sets.ill_formed == [], sets.ill_formed
    assert sets.minimum_size == 0  # TOP is reachable as declared
    # The fairness constraint is a candidate and is explored, not rejected.
    assert "move" in sets.assumptions
