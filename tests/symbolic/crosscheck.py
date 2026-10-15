"""Shared checks of the symbolic engine against the explicit engine (spec 5.3, F1)."""

from __future__ import annotations

import itertools
import random

from bmc.rich_models import target_ids, targets, try_explore

from wavefront.engine import attractor as x_attractor
from wavefront.engine import contested as x_contested
from wavefront.engine import safe as x_safe
from wavefront.model import ModelError
from wavefront.symbolic import (
    attractor,
    contested,
    encode,
    reachable,
    safe,
    shortest,
    witness,
)


def coalitions(names, rnd=None):
    """Every coalition, or one random coalition when ``rnd`` is given."""
    if rnd is not None:
        return [tuple(rnd.sample(names, rnd.randint(0, len(names))))]
    return [c for k in range(len(names) + 1) for c in itertools.combinations(names, k)]


def check_transitions(cm, g, enc):
    """The encoding's availability and next-state functions equal the explicit model's on
    every reachable state and joint move."""
    for i, s in enumerate(g.states):
        assert enc.holds(enc.dom, s)
        assert enc.holds(enc.term, s) == g.terminal[i]
        if g.terminal[i]:
            continue
        assert enc.available(s) == g.avail[i]
        for jm, t in zip(g.moves[i], g.succ[i], strict=True):
            assert enc.successor(s, jm) == g.states[t]
            assert not enc.is_error(s, jm)
    assert enc.count(enc.initial) == len(cm.initial_states())


def _sub(jm, members):
    return tuple(jm[i] for i in members)


def check_attractor(g, enc, coalition, goal, tb, strategy_every=1):
    """Membership and rank on every reachable state; the strategy move on every
    ``strategy_every``-th state."""
    xa = x_attractor(g, coalition, goal)
    sa = attractor(enc, coalition, tb)
    members = g.actor_indices(coalition)
    for i, s in enumerate(g.states):
        assert sa.contains(s) == (i in xa.win), (coalition, g.model.format_state(s))
        if i not in xa.win:
            if i % strategy_every == 0:
                assert sa.strategy_move(s) is None
            continue
        assert sa.rank(s) == xa.rank[i]
        if i % strategy_every:
            continue
        move = sa.strategy_move(s)
        if xa.rank[i] == 0:
            assert move is None
            continue
        followers = [
            t for jm, t in zip(g.moves[i], g.succ[i], strict=True) if _sub(jm, members) == move
        ]
        assert followers, "the strategy move is available"
        assert all(xa.rank.get(t, -1) in range(xa.rank[i]) for t in followers)
    for i in g.initial:
        check_witness(g.model, enc, sa, g.states[i], i in xa.win)
    return sa


def check_witness(cm, enc, res, state, winning):
    """The witness from ``state`` replays on the explicit model and ends in the target
    within the state's rank."""
    trace = witness(enc, cm, state, res.target, res.coalition, result=res)
    if not winning:
        assert trace is None
        return
    assert trace is not None and len(trace) - 1 <= res.rank(state)
    for (s, move), (nxt, _) in itertools.pairwise(trace):
        assert not cm.is_terminal(s)
        assert all(j in acts for j, acts in zip(move, cm.available(s), strict=True))
        assert cm.step(s, move) == nxt
    assert trace[-1][1] is None and enc.holds(res.target, trace[-1][0])


def check_safe(g, enc, coalition, phi, pb, within=None, strategy_every=1):
    xs = x_safe(g, coalition, phi)
    members = g.actor_indices(coalition)
    results = [safe(enc, coalition, pb, method=m) for m in ("auto", "iterate")]
    if within is not None:
        results.append(safe(enc, coalition, pb, within=within))
    for res in results:
        for i, s in enumerate(g.states):
            assert res.contains(s) == (i in xs.kernel), (coalition, g.model.format_state(s))
    ss = results[0]
    assert ss.count(within) == len(xs.kernel) if within is not None else True
    for i in xs.kernel:
        if i % strategy_every:
            continue
        s = g.states[i]
        move = ss.strategy_move(s)
        if g.terminal[i]:
            assert move is None
            continue
        followers = [
            t for jm, t in zip(g.moves[i], g.succ[i], strict=True) if _sub(jm, members) == move
        ]
        assert followers, "the strategy move is available"
        assert all(t in xs.kernel for t in followers)


def check_contested(g, enc, coalition, goal, tb):
    for kind in ("reach", "keep"):
        xc = x_contested(g, coalition, goal, kind)
        sc = contested(enc, coalition, tb, kind)
        for i, s in enumerate(g.states):
            want = "forced" if i in xc.forced else "blocked" if i in xc.blocked else "contested"
            assert sc.region(s) == want


def check_model(model, profile=None, seed=0, every_coalition=False, gc_always=False, manager=None):
    """All checks on one model; ``False`` if the explicit engine rejects it (then the
    symbolic ``reachable`` must reject it too). ``gc_always`` makes the manager collect
    garbage at every opportunity; ``manager`` picks the BDD core (default: the selected
    one, see :func:`wavefront.symbolic.manager`)."""
    cm = model.compile(profile=profile)
    g = try_explore(cm)
    enc = encode(cm, manager=manager)
    if gc_always:
        enc.mgr.gc_min_nodes = 0
        enc.mgr.gc_factor = 0.0
    if g is None:
        try:
            reachable(enc)
        except ModelError:
            return False
        raise AssertionError(f"{model.name}: explore raised but reachable did not")
    check_transitions(cm, g, enc)
    reach = reachable(enc)
    assert reach.count() == g.size()
    assert all(reach.contains(s) for s in g.states)
    rnd = random.Random(seed)
    names = cm.actor_names
    for target in targets(cm, rnd):
        goal = target_ids(g, target)
        tb = enc.predicate(target)
        assert {i for i, s in enumerate(g.states) if enc.holds(tb, s)} == goal
        ranks = x_attractor(g, names, goal).rank
        for i in g.initial:
            assert shortest(enc, g.states[i], tb) == ranks.get(i)
        for coalition in coalitions(names, None if every_coalition else rnd):
            check_attractor(g, enc, coalition, goal, tb)
            check_safe(g, enc, coalition, goal, tb, reach.states)
            check_contested(g, enc, coalition, goal, tb)
    return True
