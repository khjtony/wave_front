"""Brute-force cross-checks of attractor, safe, contested and witness on random models.

Two references:

1. Enumeration of every memoryless per-state coalition strategy (one sub-move per state)
   on tiny models: a state is winning iff some strategy wins from it. This is exactly what
   the fixpoints compute (spec 11).
2. The layered Kleene iteration straight from the definitions, on models up to the bounds
   of spec 11, which also checks ranks as stage indices and the strategies returned.

Each check runs under hypothesis (models built from a drawn seed) and over a fixed sweep of
seeds, because hypothesis favours very small seeds and therefore very small games.
"""

import random

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st
from wf_random_games import (
    build_random_model,
    enumerate_strategies,
    kleene_attractor,
    kleene_safe,
    random_models,
    strategy_count,
    strategy_keeps,
    strategy_reaches,
    sub_successors,
)

from wavefront.engine import attractor, contested, explore, safe, witness

MAX_STRATEGIES = 4096
SMALL = {"max_vars": 3, "max_horizon": 3, "max_actors": 2}
SWEEP = 300

SETTINGS = settings(
    max_examples=300,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)


def random_case(model, rnd):
    """Explore ``model`` and pick a random coalition and goal set."""
    g = explore(model.compile(), max_states=5000)
    coalition = {name for name in g.model.actor_names if rnd.random() < 0.6}
    p = rnd.choice((0.1, 0.3, 0.6))
    goal = {i for i in range(g.size()) if rnd.random() < p}
    return g, coalition, goal


def check_enumeration(g, coalition, goal):
    reach_bf: set[int] = set()
    keep_bf: set[int] = set()
    for sigma in enumerate_strategies(g, coalition):
        reach_bf |= strategy_reaches(g, sigma, goal)
        keep_bf |= strategy_keeps(g, sigma, goal)
    assert attractor(g, coalition, goal).win == reach_bf
    assert safe(g, coalition, goal).kernel == keep_bf


def check_layered(g, coalition, goal):
    table = sub_successors(g, coalition)

    r = attractor(g, coalition, goal)
    win, rank = kleene_attractor(g, coalition, goal)
    assert r.win == win
    assert r.rank == rank
    assert set(r.strategy) == win - goal
    for s, sub in r.strategy.items():
        # The strategy's completions all lead to states that joined strictly earlier.
        assert all(r.rank[t] < r.rank[s] for t in table[s][sub])

    k = safe(g, coalition, goal)
    assert k.kernel == kleene_safe(g, coalition, goal)
    assert set(k.strategy) == {s for s in k.kernel if not g.terminal[s]}
    for s, sub in k.strategy.items():
        assert table[s][sub] <= k.kernel

    for kind in ("reach", "keep"):
        c = contested(g, coalition, goal, kind)
        assert not c.forced & c.blocked
        assert c.forced | c.blocked | c.contested == set(range(g.size()))
        assert not c.contested & (c.forced | c.blocked)


def check_witness(g, rnd):
    targets = {i for i in range(g.size()) if rnd.random() < 0.1}
    source = rnd.randrange(g.size())
    # With every actor (Nature included) in the coalition, the attractor is plain
    # reachability and the rank is the length of a shortest path.
    win, rank = kleene_attractor(g, g.model.actor_names, targets)
    w = witness(g, source, targets)
    if source not in win:
        assert w is None
        return
    assert w is not None
    assert len(w) - 1 == rank[source]
    assert w[0][0] == source and w[-1][0] in targets and w[-1][1] is None
    for (s, jm), (t, _) in zip(w, w[1:], strict=False):
        assert g.succ[s][g.moves[s].index(jm)] == t


@SETTINGS
@given(model=random_models(**SMALL), seed=st.integers(0, 2**16))
def test_fixpoints_equal_strategy_enumeration(model, seed):
    g, coalition, goal = random_case(model, random.Random(seed))
    assume(strategy_count(g, coalition) <= MAX_STRATEGIES)
    check_enumeration(g, coalition, goal)


@SETTINGS
@given(model=random_models(), seed=st.integers(0, 2**16))
def test_fixpoints_equal_layered_definition(model, seed):
    check_layered(*random_case(model, random.Random(seed)))


@SETTINGS
@given(model=random_models(), seed=st.integers(0, 2**16))
def test_witness_is_shortest(model, seed):
    g = explore(model.compile(), max_states=5000)
    check_witness(g, random.Random(seed))


def test_seed_sweep():
    """The same checks on a fixed, evenly spread set of seeds."""
    enumerated = 0
    for seed in range(SWEEP):
        rnd = random.Random(seed)
        g, coalition, goal = random_case(build_random_model(seed, **SMALL), rnd)
        if strategy_count(g, coalition) <= MAX_STRATEGIES:
            check_enumeration(g, coalition, goal)
            enumerated += 1
        g, coalition, goal = random_case(build_random_model(10_000 + seed), rnd)
        check_layered(g, coalition, goal)
        check_witness(g, rnd)
    assert enumerated >= SWEEP // 2
