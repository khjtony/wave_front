"""The symbolic engine on the toy model: every ending's attractor and every invariant's
kernel, for every coalition, equal the explicit engine's on the reachable states (with
ranks and strategy moves), and witness traces replay on the explicit model."""

import itertools

import pytest

from models.toy.two_power import model
from symbolic.crosscheck import check_attractor, check_safe, check_transitions
from wavefront.engine import explore
from wavefront.symbolic import attractor, encode, reachable, witness

PROFILES = [None, "appeaser"]


@pytest.fixture(scope="module", params=PROFILES)
def world(request):
    cm = model.compile(profile=request.param)
    g = explore(cm)
    enc = encode(cm)
    return cm, g, enc


def all_coalitions(cm):
    names = cm.actor_names
    return [c for k in range(len(names) + 1) for c in itertools.combinations(names, k)]


def test_transitions_and_reachable(world):
    cm, g, enc = world
    check_transitions(cm, g, enc)
    reach = reachable(enc)
    assert reach.count() == g.size()


def test_every_ending_attractor_every_coalition(world):
    cm, g, enc = world
    for ending in [*cm.model.endings, "HORIZON"]:
        goal = g.ending_states(ending)
        tb = enc.predicate(ending)
        for coalition in all_coalitions(cm):
            check_attractor(g, enc, coalition, goal, tb)


def test_every_kernel_every_coalition(world):
    cm, g, enc = world
    reach = reachable(enc)
    for name in cm.model.invariants:
        phi = g.states_where(name)
        pb = enc.predicate(name)
        for coalition in all_coalitions(cm):
            check_safe(g, enc, coalition, phi, pb, reach.states)


def test_witness_replays(world):
    cm, g, enc = world
    found = 0
    for ending in cm.model.endings:
        tb = enc.predicate(ending)
        for coalition in all_coalitions(cm):
            res = attractor(enc, coalition, tb)
            for i in g.initial:
                s = g.states[i]
                trace = witness(enc, cm, s, tb, coalition, result=res)
                if trace is None:
                    assert not res.contains(s)
                    continue
                found += 1
                assert len(trace) - 1 <= res.rank(s)
                for (state, move), (nxt, _) in itertools.pairwise(trace):
                    assert not cm.is_terminal(state)
                    avail = cm.available(state)
                    assert all(j in acts for j, acts in zip(move, avail, strict=True))
                    assert cm.step(state, move) == nxt
                assert trace[-1][1] is None
                assert cm.ending_of(trace[-1][0]) == ending
    assert found
