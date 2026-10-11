"""Cross-check of ``reach`` against the explicit engine on random models (spec 6, 11).

For every target (each ending, ``HORIZON``, an invariant, a random condition) the BMC
answer at depth k (the horizon, or 4 for untimed models) must agree with
``explore`` + ``attractor(all actors incl. Nature, target)``: a trace exists iff some
initial state has rank <= k, and the trace found is shortest, so its length is the least
such rank. Every trace is replayed with ``cm.step`` and checked for availability.

Models come from the shared generator (:mod:`helpers.random_games`) and from the richer
generator in :mod:`bmc.rich_models` (delays, strict Bumps, SetIf, latches, fairness,
profiles, assumes); models on which the explicit engine raises ``ModelError`` are skipped.
Each check runs under hypothesis and over a fixed sweep of seeds.
"""

import random

from helpers.random_games import build_random_model
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from bmc.rich_models import (
    bound,
    build_rich_model,
    check_replay,
    explicit_distance,
    target_ids,
    targets,
    try_explore,
)
from wavefront.bmc import reach

SETTINGS = settings(
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
SWEEP = 200


def check_model(model, profile=None, seed=0):
    """Compare BMC and the explicit engine on every target; False if skipped."""
    cm = model.compile(profile=profile)
    g = try_explore(cm)
    if g is None:
        return False
    k = bound(cm)
    for target in targets(cm, random.Random(seed)):
        goal = target_ids(g, target)
        dist = explicit_distance(g, goal)
        expected = dist if dist is not None and dist <= k else None
        trace = reach(cm, k, target)
        got = None if trace is None else len(trace)
        assert got == expected, f"{model.name} target {target!r}: bmc {got}, explicit {expected}"
        if trace is not None:
            check_replay(cm, trace, lambda s: g.index.get(s) in goal)
    return True


@SETTINGS
@given(seed=st.integers(0, 2**32 - 1))
def test_reach_agrees_with_explicit_engine_shared_generator(seed):
    assert check_model(build_random_model(seed), seed=seed)


@SETTINGS
@given(seed=st.integers(0, 2**32 - 1))
def test_reach_agrees_with_explicit_engine_rich_generator(seed):
    model, profile = build_rich_model(seed)
    assume(check_model(model, profile, seed))


def test_reach_seed_sweep():
    """The same checks on a fixed set of seeds, with both generators."""
    checked = 0
    for seed in range(SWEEP):
        assert check_model(build_random_model(50_000 + seed), seed=seed)
        model, profile = build_rich_model(90_000 + seed)
        checked += check_model(model, profile, seed)
    assert checked >= SWEEP * 3 // 4
