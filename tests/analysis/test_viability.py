"""Kernels, point of no return, silent phase and distances on hand-built games."""

import math

import pytest

from wavefront.analysis import (
    Distance,
    distance,
    point_of_no_return,
    silent_phase,
    viability,
)
from wavefront.engine import Trace, explore, witness
from wavefront.model import ModelError

from .games import crisis, ladder, tug


def by(g, **values):
    """Id of the unique state with the given level names."""
    cm = g.model
    hits = [
        i
        for i, s in enumerate(g.states)
        if all(cm.level_name(k, s[cm.index[k]]) == str(v) for k, v in values.items())
    ]
    assert len(hits) == 1, hits
    return hits[0]


def literal_margin(g, kernel, s):
    """Stage index in M_0 = K, M_{i+1} = {s in M_i | every move stays in M_i}."""
    m = set(kernel)
    if s not in m:
        return None
    i = 0
    while True:
        nxt = {t for t in m if all(u in m for u in g.succ[t])}
        if s not in nxt:
            return i
        if nxt == m:
            return math.inf
        m, i = nxt, i + 1


def test_unilateral_kernel_and_empty_coalition():
    g = explore(ladder().compile())
    k = viability(g, {"P"}, "low")
    xs = {g.states[s][g.model.index["x"]] for s in k.kernel}
    assert xs == {0, 1, 2}
    assert viability(g, set(), "low").kernel == set()
    # the keeping strategy pulls wherever Nature could push x out
    pull = g.model.actors[0].action_index("pull")
    assert k.strategy[by(g, x=2)] == (pull,)


def test_viability_rejects_unknown_invariant_and_endings():
    g = explore(crisis().compile())
    with pytest.raises(ModelError, match="no invariant named 'WAR'"):
        viability(g, {"P"}, "WAR")


def test_distance_inside_and_outside_the_kernel():
    g = explore(ladder().compile())
    kernel = viability(g, {"P"}, "low").kernel
    d0 = distance(g, by(g, x=0), kernel, {"P"}, {"Nature"})
    # Lemma 5: the adversary cannot force leaving P's own kernel
    assert d0 == Distance(forced=None, shortest=3, margin=2)
    assert distance(g, by(g, x=2), kernel, {"P"}, {"Nature"}) == Distance(None, 1, 0)
    assert distance(g, by(g, x=3), kernel, {"P"}, {"Nature"}) == Distance(0, 0, None)
    for s in range(g.size()):
        assert distance(g, s, kernel, {"P"}, {"Nature"}).margin == literal_margin(g, kernel, s)


def test_margin_is_unbounded_when_no_play_leaves():
    g = explore(ladder().compile())
    kernel = viability(g, {"P"}, "always").kernel
    assert kernel == set(range(g.size()))
    assert distance(g, 0, kernel, {"P"}, {"Nature"}) == Distance(None, None, math.inf)


def test_joint_kernel_against_one_member():
    g = explore(tug().compile())
    joint = viability(g, {"A", "B"}, "low").kernel
    assert {g.states[s][0] for s in joint} == {0, 1, 2}
    assert viability(g, {"A"}, "low").kernel == set()
    # B defecting with Nature gains one level per tick against A
    assert distance(g, by(g, x=0), joint, {"A", "B"}, {"B", "Nature"}).forced == 3
    assert distance(g, by(g, x=2), joint, {"A", "B"}, {"B", "Nature"}).forced == 1
    assert distance(g, by(g, x=0), joint, {"A", "B"}, {"Nature"}).forced is None
    for s in range(g.size()):
        got = distance(g, s, joint, {"A", "B"}, {"Nature"}).margin
        assert got == literal_margin(g, joint, s)


def test_distance_validates_state_and_actors():
    g = explore(ladder().compile())
    with pytest.raises(ModelError, match="not in the graph"):
        distance(g, 99, set(), {"P"}, {"Nature"})
    with pytest.raises(ModelError, match="unknown actor"):
        distance(g, 0, set(), {"Q"}, {"Nature"})


def escalation_trace(g):
    """calm -> tense (provoke) -> mismatch -> crisis -> war."""
    cm = g.model
    p, n = cm.actors
    calm = by(g, pos="calm", pg="none", ng="none")
    tense = by(g, pos="tense", pg="none", ng="none")
    mism = by(g, pos="tense", pg="h", ng="t")
    cris = by(g, pos="crisis", pg="h", ng="t")
    war = by(g, pos="war", pg="h", ng="t")
    return Trace(
        [
            (calm, (p.action_index("provoke"), 0)),
            (tense, (p.action_index("guess_h"), n.action_index("guess_t"))),
            (mism, (p.action_index("wait"), n.action_index("escalate"))),
            (cris, (p.action_index("wait"), n.action_index("attack"))),
            (war, None),
        ]
    )


def test_silent_phase_indices():
    g = explore(crisis().compile())
    trace = escalation_trace(g)
    kernel = viability(g, {"P"}, "peace").kernel
    assert point_of_no_return(trace, kernel) == 1
    assert point_of_no_return(trace.state_ids, kernel) == 1
    sp = silent_phase(trace, g, {"P"}, "peace")
    assert (sp.t_K, sp.t_L, sp.t_phi) == (1, 2, 4)
    assert sp.silent == (1, 4)
    assert sp.contested_part == (1, 2)
    assert sp.lost_part == (2, 4)


def test_silent_phase_on_a_trace_that_stays_safe():
    g = explore(crisis().compile())
    calm = by(g, pos="calm", pg="none", ng="none")
    trace = Trace([(calm, None)])
    sp = silent_phase(trace, g, {"P"}, "peace")
    assert (sp.t_K, sp.t_L, sp.t_phi) == (None, None, None)
    assert sp.silent is None and sp.lost_part is None
    assert point_of_no_return(trace, viability(g, {"P"}, "peace").kernel) is None


def test_silent_phase_ordering_on_every_witness():
    g = explore(crisis().compile())
    for s in range(g.size()):
        trace = witness(g, s, g.ending_states("WAR"))
        if trace is None:
            continue
        sp = silent_phase(trace, g, {"P"}, "peace")
        assert sp.t_K is not None and sp.t_phi is not None
        assert sp.t_K <= sp.t_L <= sp.t_phi
