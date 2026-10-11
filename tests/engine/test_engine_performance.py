"""Performance smoke test: about 1e5 reachable states with ~1e2 joint moves each."""

import time

import pytest

from wavefront.engine import explore
from wavefront.model import Bump, Inc, Model, Reset, Set, SetIf, V


def synthetic(horizon=6):
    """A model using every construct, sized to about 1.1e5 reachable states at horizon 6
    (4 actors with 4, 5, 4 and 4 actions)."""
    m = Model("perf", horizon=horizon)
    m.counter("a", max=4)
    m.counter("b", max=4)
    m.counter("c", max=3)
    m.var("d", levels=["lo", "mid", "hi"])
    m.flag("f")
    m.var("grow", levels=["g0", "g1", "g2", "g3"], monotone=True)
    p = m.actor("P", remember_last=True)
    q = m.actor("Q")
    r = m.actor("R")
    n = m.nature()
    p.action("up_a", guard=V.a < 4, effect=Inc("a"))
    p.action("down_a", guard=V.a > 0, effect=Bump("a", -1))
    p.action("set_d", guard=V.a >= 2, effect=Set("d", "hi"))
    p.action("slow", effect=Inc("c"), delay=2)
    q.action("up_b", guard=V.b < 4, effect=Inc("b"))
    q.action("down_b", effect=Bump("b", -1))
    q.action("lower_d", guard=V.d > "lo", effect=Bump("d", -1))
    q.action("toggle", effect=SetIf(V.f == False, "f", True))  # noqa: E712
    r.action("reset_c", guard=V.c > 0, effect=Reset("c"))
    r.action("grow", guard=V.b >= 2, effect=Bump("grow", 1))
    r.action("mix", effect=[Inc("a"), Bump("b", -1)])
    n.event("shock", effect=Bump("a", -1))
    n.event("drift", guard=V.d == "lo", effect=Bump("d", 1))
    n.event("boost", effect=Inc("c"))
    m.latch("d_at_grow", of="d", when=V.grow >= "g2")
    m.fairness("resp", actor="Q", trigger=V.a >= 3, within=2, responses=["down_b", "up_b"])
    m.ending("BOOM", (V.grow == "g3") & (V.c == 3))
    return m


@pytest.mark.slow
def test_explore_1e5_states_under_120_seconds():
    cm = synthetic().compile()
    start = time.perf_counter()
    g = explore(cm)
    elapsed = time.perf_counter() - start
    moves = sum(len(x) for x in g.moves)
    print(
        f"\nexplored {g.size()} states, {moves} joint moves "
        f"({moves / g.size():.1f} per state) in {elapsed:.1f} s "
        f"({elapsed / moves * 1e6:.2f} us per successor)"
    )
    assert 80_000 <= g.size() <= 150_000
    assert elapsed < 120
