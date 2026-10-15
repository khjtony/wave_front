"""Engine demonstrations on the cadence toy ``models/toy/cadence.py``.

These are demonstrations, not findings: what the decision cadence (spec 3.1) changes in a
fast-against-slow game. The same SLOW that blocks ``OVERRUN`` alone when it decides every
tick cannot prevent it when it decides at most once every three ticks, and FAST then forces
it. If the toy is edited the answers here are expected to change with it.
"""

import pytest

from models.toy.cadence import build, model
from wavefront.analysis import fingerprint, viability
from wavefront.bmc import reach
from wavefront.engine import attractor, contested, explore, witness
from wavefront.symbolic import attractor as s_attractor
from wavefront.symbolic import encode
from wavefront.symbolic import safe as s_safe


def status(g, coalition, ending):
    (s,) = g.initial
    r = contested(g, coalition, g.ending_states(ending), "reach")
    return "forced" if s in r.forced else "blocked" if s in r.blocked else "contested"


def test_the_default_toy_is_the_slow_version_with_one_cadence_counter():
    cm = model.compile()
    assert [v.name for v in cm.variables] == ["tick", "exposure", "cadence_SLOW"]
    assert cm.budget()["cadence"] == 1
    fast = build(1).compile()
    assert [v.name for v in fast.variables] == ["tick", "exposure"]
    assert fast.budget()["cadence"] == 0
    assert fingerprint(build(1)) != fingerprint(build(3))


def test_at_cadence_one_slow_blocks_the_overrun_alone():
    g = explore(build(1).compile())
    (s0,) = g.initial
    assert status(g, ["FAST"], "OVERRUN") == "blocked"
    assert s0 in viability(g, ["SLOW"], "contained").kernel


def test_at_cadence_three_fast_forces_the_overrun_slow_cannot_prevent():
    cm = build(3).compile()
    g = explore(cm)
    (s0,) = g.initial
    assert status(g, ["FAST"], "OVERRUN") == "forced"
    assert s0 not in viability(g, ["SLOW"], "contained").kernel
    win = attractor(g, ["FAST"], g.ending_states("OVERRUN"))
    assert win.rank[s0] == 4
    # FAST's forcing strategy is simply to advance every tick.
    advance = cm.actors[0].action_index("advance")
    assert set(win.strategy.values()) == {(advance,)}
    # Unopposed, three ticks suffice; against SLOW's best play, four (rank above).
    trace = witness(g, s0, g.ending_states("OVERRUN"))
    assert len(trace) == 4  # four states, three moves


@pytest.mark.parametrize("k, rank", [(1, None), (2, 5), (3, 4), (4, 4)])
def test_the_slower_slow_is_the_sooner_fast_forces(k, rank):
    g = explore(build(k).compile())
    (s0,) = g.initial
    assert attractor(g, ["FAST"], g.ending_states("OVERRUN")).rank.get(s0) == rank


@pytest.mark.parametrize("k", [1, 3])
def test_the_symbolic_and_bounded_engines_agree(k):
    cm = build(k).compile()
    g = explore(cm)
    (s0,) = g.initial
    enc = encode(cm)
    forced = s_attractor(enc, ["FAST"], enc.predicate("OVERRUN"))
    kept = s_safe(enc, ["SLOW"], enc.predicate("contained"))
    explicit = attractor(g, ["FAST"], g.ending_states("OVERRUN"))
    assert forced.contains(g.states[s0]) == (s0 in explicit.win)
    assert kept.contains(g.states[s0]) == (k == 1)
    trace = reach(cm, cm.horizon, "OVERRUN")
    assert trace is not None and len(trace) == 3  # reachable either way with SLOW idle
