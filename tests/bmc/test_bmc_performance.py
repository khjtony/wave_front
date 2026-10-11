"""Performance smoke test: ``reach`` on a 17-variable model unrolled to k = 30."""

import time

import pytest

from wavefront.bmc import reach, relax
from wavefront.model import Bump, Inc, Model, Reset, Set, SetIf, V


def synthetic(horizon=30):
    """Six counters, three leveled variables, three flags, two delayed actions, two
    latches, a fairness constraint and two endings (17 state variables with built-ins)."""
    m = Model("bmc_perf", horizon=horizon)
    m.counter("a", max=6)
    m.counter("b", max=6)
    m.counter("c", max=4)
    m.var("d", levels=["lo", "mid", "hi"])
    m.flag("f")
    m.var("grow", levels=["g0", "g1", "g2", "g3"], monotone=True)
    m.counter("stock", max=5, init=2)
    m.var("mood", levels=["calm", "tense", "angry"])
    m.flag("alarm")
    m.counter("debt", max=4)
    p = m.actor("P", remember_last=True)
    q = m.actor("Q")
    r = m.actor("R")
    n = m.nature()
    p.action("up_a", guard=V.a < 6, effect=Inc("a"))
    p.action("down_a", guard=V.a > 0, effect=Bump("a", -1))
    p.action("set_d", guard=V.a >= 2, effect=Set("d", "hi"))
    p.action("slow", effect=Inc("c"), delay=2)
    p.action("spend", guard=V.stock > 0, effect=[Bump("stock", -1), Inc("debt")])
    q.action("up_b", guard=V.b < 6, effect=Inc("b"))
    q.action("down_b", effect=Bump("b", -1))
    q.action("lower_d", guard=V.d > "lo", effect=Bump("d", -1))
    q.action("toggle", effect=SetIf(V.f == False, "f", True))  # noqa: E712
    q.action("calm", guard=V.mood > "calm", effect=Bump("mood", -1))
    r.action("reset_c", guard=V.c > 0, effect=Reset("c"))
    no_alarm = V.alarm == False  # noqa: E712
    r.action("grow", guard=(V.b >= 3) & no_alarm, effect=Bump("grow", 1))
    r.action("mix", effect=[Inc("a"), Bump("b", -1)])
    r.action("provoke", effect=Bump("mood", 1), delay=1)
    n.event("shock", effect=Bump("a", -1))
    n.event("drift", guard=V.d == "lo", effect=Bump("d", 1))
    n.event("boost", effect=Inc("c"))
    n.event("ring", guard=V.mood == "angry", effect=Set("alarm", True))
    n.event("restock", guard=V.stock < 5, effect=Inc("stock"))
    m.latch("d_at_grow", of="d", when=V.grow >= "g2")
    m.latch("mood_at_debt", of="mood", when=V.debt >= 3)
    m.fairness("resp", actor="Q", trigger=V.a >= 4, within=2, responses=["down_b", "up_b"])
    m.ending("BOOM", (V.grow == "g3") & (V.c == 4) & (V.debt >= 4))
    m.ending("CRISIS", (V.alarm == True) & (V.grow <= "g1"))  # noqa: E712
    return m


def timed(fn, *args, **kwargs):
    start = time.perf_counter()
    out = fn(*args, **kwargs)
    return out, time.perf_counter() - start


@pytest.mark.slow
def test_reach_k30_under_60_seconds():
    cm = synthetic().compile()
    assert len(cm.variables) == 17
    report = []
    for name, target, length in [
        ("BOOM", "BOOM", 6),
        ("CRISIS", "CRISIS", 5),
        ("deep", (V.grow == "g3") & (V.a == 6) & (V.b == 0) & (V.debt == 4) & (V.stock == 5), 8),
        ("unreachable", (V.alarm == True) & (V.tick <= 4), None),  # noqa: E712
    ]:
        trace, elapsed = timed(reach, cm, 30, target)
        report.append(f"{name}: {elapsed:.1f} s")
        assert (None if trace is None else len(trace)) == length
        assert elapsed < 60
    # The unreachable target needs one relaxed guard (Nature.ring).
    result, elapsed = timed(relax, cm, 30, (V.alarm == True) & (V.tick <= 4))  # noqa: E712
    report.append(f"relax: {elapsed:.1f} s")
    assert result.minimal_sets == [["Nature.ring"]]
    assert elapsed < 120
    print("\n" + "; ".join(report))
