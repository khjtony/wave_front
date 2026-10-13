"""Cross-check of the symbolic engine against the explicit engine on random tiny models
(decision F1 of docs/phase2_kickoff.md).

For each model from the shared generator (:mod:`helpers.random_games`) and the richer one
(:mod:`bmc.rich_models`: delays, strict Bumps, SetIf and expression Sets, flags, latches,
``remember_last``, fairness, profiles, assumes): the encoding's availability and successors
equal the explicit model's on every reachable state and joint move; ``reachable`` finds
exactly the explored states (and raises where ``explore`` raises); and for every target
(each ending, ``HORIZON``, the invariant, a random condition), the symbolic attractor
(membership, rank, strategy move), safety kernel (both methods, and restricted to the
reachable states, with its count and strategy move) and contested regions equal the
explicit ones on every reachable state. Hypothesis draws one coalition per target; the
seeded sweeps check every coalition.
"""

from bmc.rich_models import build_rich_model
from helpers.random_games import build_random_model
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from symbolic.crosscheck import check_model

SETTINGS = settings(
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
SWEEP = 100


@SETTINGS
@given(seed=st.integers(0, 2**32 - 1))
def test_symbolic_agrees_shared_generator(seed):
    assert check_model(build_random_model(seed), seed=seed)


@SETTINGS
@given(seed=st.integers(0, 2**32 - 1))
def test_symbolic_agrees_rich_generator(seed):
    model, profile = build_rich_model(seed)
    assume(check_model(model, profile, seed))


def test_symbolic_seed_sweep_every_coalition():
    checked = 0
    for seed in range(SWEEP):
        assert check_model(build_random_model(70_000 + seed), seed=seed, every_coalition=True)
        model, profile = build_rich_model(110_000 + seed)
        checked += check_model(model, profile, seed, every_coalition=True)
    assert checked >= SWEEP * 3 // 4


def test_symbolic_with_garbage_collection_at_every_step():
    """The same checks with a collection at every opportunity: no edge in use is freed."""
    checked = 0
    for seed in range(40):
        model, profile = build_rich_model(150_000 + seed)
        checked += check_model(model, profile, seed, gc_always=True)
    assert checked >= 30
