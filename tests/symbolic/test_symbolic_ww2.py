"""The symbolic engine against the explicit engine on WW2 v0 from hindsight snapshot
states whose exact kernels the explicit engine computes (decision F1): reachable-state
count, WEST's kernel for ``balance_europe`` (membership of the start state and size over the
reachable states, from the kernel restricted to the reachable set and from the kernel over
the whole state space), and the shortest distance out of the kernel."""

import pytest

from models.ww2.hypotheses import snapshot_state
from models.ww2.v0 import model
from wavefront.analysis import viability
from wavefront.analysis.viability import distance_table
from wavefront.engine import explore
from wavefront.symbolic import FALSE, attractor, encode, reachable, safe


def compare(quarter, expected_size=None, builtins=False, full=False):
    cm = model.compile()
    start = snapshot_state(cm, quarter, "hegemonic", builtins=builtins)
    g = explore(cm, initial=[start], max_states=3_000_000)
    if expected_size is not None:
        assert g.size() == expected_size
    kernel = viability(g, ["WEST"], "balance_europe").kernel
    s = g.initial[0]
    explicit_distance = distance_table(g, [s], kernel, ["WEST"], None)[s].shortest

    enc = encode(cm)
    reach = reachable(enc, enc.state_cube(start))
    assert reach.count() == g.size()
    phi = enc.predicate("balance_europe")
    res = safe(enc, ["WEST"], phi, within=reach.states)
    assert res.contains(start) == (s in kernel)
    assert res.count() == len(kernel)
    assert all(res.contains(g.states[i]) for i in kernel)
    if full:
        whole = safe(enc, ["WEST"], phi)
        assert whole.contains(start) == (s in kernel)
        assert whole.count(reach.states) == len(kernel)
    outside = enc.mgr.DIFF(reach.states, res.kernel)
    if outside != FALSE:
        everyone = cm.actor_names
        assert attractor(enc, everyone, outside).rank(start) == explicit_distance
    return s in kernel


def test_late_state_1939Q3():
    """8,608 states: quick enough for the default suite."""
    compare("1939Q3", 8_608, full=True)


@pytest.mark.slow
def test_after_munich_1938Q3():
    """198,443 states; the start state is in the kernel (reports/ww2_v0.md, T8)."""
    assert compare("1938Q3", 198_443)


@pytest.mark.slow
def test_after_munich_1938Q3_with_builtins():
    """601,353 states with the snapshot's built-ins: inside, shortest distance 3."""
    assert compare("1938Q3", 601_353, builtins=True)


@pytest.mark.slow
def test_before_munich_1938Q2():
    """1,423,926 states; the start state is outside the kernel (reports/ww2_v0.md, T8)."""
    assert not compare("1938Q2", 1_423_926)
