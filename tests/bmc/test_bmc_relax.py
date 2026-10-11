"""Cross-check of ``relax`` against brute-force relaxation with the explicit engine.

For random models with at most 6 named assumptions (guards, fairness, a selected profile,
``assume`` restrictions), the brute force compiles ``compile(model, profile, relax=S)``
for every subset S of ``cm.assumptions()``, explores it and asks whether a target state
is within k transitions of an initial state, for every target (each ending,
``HORIZON``, the invariant, a random condition). ``relax`` must report the same minimum size
and exactly the same minimum-size sets. The unsat core must be a real core: asserting
only the core assumptions keeps the target unreachable. The trace returned for the first
set is replayed on the model compiled with that set relaxed.
"""

import itertools
import random

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from bmc.rich_models import bound, build_rich_model, check_replay, target_ids, targets, try_explore
from wavefront.bmc import reach, relax

MAX_ASSUMPTIONS = 6
SETTINGS = settings(
    max_examples=120,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
SWEEP = 120


def brute_force(model, profile, names, target_list, k):
    """``{subset: [reachable per target]}`` for every subset, or ``None`` if some subset's
    explicit exploration raises ``ModelError``."""
    out = {}
    for size in range(len(names) + 1):
        for subset in itertools.combinations(names, size):
            g = try_explore(model.compile(profile=profile, relax=subset))
            if g is None:
                return None
            out[subset] = [
                any(g.depth[i] <= k for i in target_ids(g, target)) for target in target_list
            ]
    return out


def check_model(model, profile, seed, stats=None):
    """Compare ``relax`` with the brute force on every target; False if skipped."""
    cm = model.compile(profile=profile)
    names = cm.assumptions()
    if len(names) > MAX_ASSUMPTIONS:
        return False
    target_list = targets(cm, random.Random(seed))
    k = bound(cm)
    table = brute_force(model, profile, names, target_list, k)
    if table is None:
        return False
    for n, target in enumerate(target_list):
        working = [list(s) for s, ok in table.items() if ok[n]]
        minimum = min((len(s) for s in working), default=None)
        expected = sorted(s for s in working if len(s) == minimum)
        check_target(model, profile, cm, k, target, minimum, expected)
        if stats is not None:
            stats[minimum] = stats.get(minimum, 0) + 1
    return True


def check_target(model, profile, cm, k, target, minimum, expected_sets):
    names = cm.assumptions()
    result = relax(cm, k, target, max_relax=len(names), max_sets=100)
    assert result.minimum_size == minimum, f"{model.name} {target!r}: {result}"
    assert result.reachable_as_is == (minimum == 0)
    if minimum is None:
        assert result.minimal_sets == [] and result.trace is None
    else:
        assert sorted(result.minimal_sets) == expected_sets
        relaxed = model.compile(profile=profile, relax=result.minimal_sets[0])
        g = try_explore(relaxed)
        goal = target_ids(g, target)
        check_replay(relaxed, _project(cm, relaxed, result.trace), lambda s: g.index[s] in goal)
    if minimum != 0:
        assert set(result.core) <= set(names)
        assert reach(cm, k, target, relax=set(names) - set(result.core)) is None
    if minimum is not None and minimum >= 2:
        assert relax(cm, k, target, max_relax=minimum - 1).minimum_size is None


def _project(cm, relaxed, trace):
    """The trace on the layout of ``relaxed`` (a relaxed fairness constraint drops its
    counter from the state)."""
    keep = [cm.index[v.name] for v in relaxed.variables]
    states = [tuple(s[i] for i in keep) for s in trace.states]
    return type(trace)(states, trace.moves, trace.relaxed)


@SETTINGS
@given(seed=st.integers(0, 2**32 - 1))
def test_relax_agrees_with_brute_force(seed):
    model, profile = build_rich_model(seed)
    assume(check_model(model, profile, seed))


def test_relax_seed_sweep():
    checked = 0
    stats: dict = {}
    for seed in range(SWEEP):
        model, profile = build_rich_model(70_000 + seed)
        checked += check_model(model, profile, seed, stats)
    assert checked >= SWEEP // 2
    # The sweep must exercise non-trivial relaxations, not only reachable-as-is targets.
    assert stats.get(1, 0) >= 20 and stats.get(2, 0) >= 5
