"""The split steps against the present one (docs/engine_split_step.md).

``step="split"`` substitutes the next-state functions one node of the target at a time and
releases every sub-result after its last use; ``step="moves"`` does that once per joint move
of the coalition; ``step="compose"`` substitutes in one manager call. All must return the
same edge:

- :func:`compose_by_levels` against :meth:`BDD.compose` on random functions and random
  substitutions, on both cores, with and without a collection after every node;
- ``cpre`` on random targets of random models of both generators, every coalition, profiles
  included (the rich generator selects them);
- the fixpoints (attractor stages, kernels by both methods and within a reachable set,
  contested regions) edge by edge, the split run collecting at every opportunity;
- the explicit cross-check with each split step selected by the environment variable.
"""

from __future__ import annotations

import os
import random
import sys
from contextlib import contextmanager

import pytest
from bmc.rich_models import build_rich_model
from helpers.random_games import build_random_model
from hypothesis import given, settings
from hypothesis import strategies as st

from symbolic.crosscheck import check_model, coalitions
from wavefront.symbolic import (
    attractor,
    c_available,
    contested,
    cpre,
    encode,
    manager,
    reachable,
    safe,
    solve,
    substitute,
    sylvan_available,
)
from wavefront.symbolic.bdd import FALSE, TRUE
from wavefront.symbolic.solve import STEP_ENV
from wavefront.symbolic.substitute import compose_by_levels

# The Sylvan core runs the split step in C, the nodes of a level in parallel
# (docs/engine_multicore.md); its worker threads follow WAVEFRONT_BDD_THREADS (default 1:
# tests/symbolic/test_bdd_sylvan.py repeats these checks at 1 and 8 threads).
# The default Sylvan tables whatever the cap of the run, as in test_bdd_sylvan.py.
os.environ.setdefault("WAVEFRONT_SYLVAN_NODES_LOG2", "24")
os.environ.setdefault("WAVEFRONT_SYLVAN_CACHE_LOG2", "23")
CORES = [
    "python",
    *(["c"] if c_available() else []),
    *(["sylvan"] if sylvan_available() else []),
]
SPLIT_STEPS = ["split", "moves"]
NVARS = 12


def random_function(mgr, rnd, levels, depth=4):
    if depth == 0 or rnd.random() < 0.15:
        return rnd.choice([mgr.var(rnd.choice(levels)), mgr.nvar(rnd.choice(levels)), TRUE, FALSE])
    a = random_function(mgr, rnd, levels, depth - 1)
    b = random_function(mgr, rnd, levels, depth - 1)
    op = rnd.choice(["and", "or", "xor", "ite"])
    if op == "ite":
        return mgr.ITE(a, b, random_function(mgr, rnd, levels, depth - 1))
    return {"and": mgr.AND, "or": mgr.OR, "xor": mgr.XOR}[op](a, b)


def fresh(core):
    """A new manager of NVARS variables."""
    mgr = manager(core)
    for _ in range(NVARS):
        mgr.add_var()
    return mgr


def close(enc):
    """End a Sylvan manager before the next one is made (a no-op on the other cores)."""
    getattr(enc.mgr, "close", lambda: None)()


@pytest.fixture
def every_node(monkeypatch):
    """Look at the node table after every node, not every 256th (on the Sylvan core: chunks
    of one node)."""
    monkeypatch.setattr(substitute, "_CHECK_EVERY", 1)
    with one_node_chunks():
        yield


@contextmanager
def one_node_chunks():
    if not sylvan_available():
        yield
        return
    from wavefront.symbolic import bdd_sylvan

    bdd_sylvan.set_chunk(1, policy_inside=True)
    try:
        yield
    finally:
        bdd_sylvan.set_chunk(0)


def always_collect(mgr):
    mgr.gc_min_nodes = 0
    mgr.gc_factor = 0.0


@pytest.mark.parametrize("core", CORES)
@settings(max_examples=150, deadline=None)
@given(seed=st.integers(0, 2**32 - 1))
def test_compose_by_levels_is_compose(core, seed):
    rnd = random.Random(seed)
    mgr = fresh(core)
    levels = list(range(NVARS))
    f = random_function(mgr, rnd, levels, 6)
    mapping = {
        v: random_function(mgr, rnd, levels, 3) for v in rnd.sample(levels, rnd.randint(0, NVARS))
    }
    want = mgr.compose(f, mapping)
    stats: dict = {}
    assert compose_by_levels(mgr, f, mapping, stats=stats) == want
    if mapping and f > 1 and mgr.top(f) <= max(mapping):
        assert 1 <= stats["held"] <= stats["nodes"] <= mgr.node_count(f)


@pytest.mark.parametrize("core", CORES)
@settings(max_examples=100, deadline=None)
@given(seed=st.integers(0, 2**32 - 1))
def test_compose_by_levels_collecting_after_every_node(core, seed):
    """Nothing still needed is freed: the sub-results in use, the target, the substituted
    functions and the caller's edges survive a collection after every node."""
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(substitute, "_CHECK_EVERY", 1)
        with one_node_chunks():
            _collecting_after_every_node(core, seed)


def _collecting_after_every_node(core, seed):
    rnd = random.Random(seed)
    mgr = fresh(core)
    levels = list(range(NVARS))
    f = random_function(mgr, rnd, levels, 6)
    mapping = {
        v: random_function(mgr, rnd, levels, 3) for v in rnd.sample(levels, rnd.randint(1, NVARS))
    }
    other = random_function(mgr, rnd, levels, 5)
    want = mgr.compose(f, mapping)
    size = mgr.node_count(other)
    mgr.protect(want)  # the reference's result, to compare with after the collections
    always_collect(mgr)
    runs = mgr.gc_runs
    got = compose_by_levels(mgr, f, mapping, keep=[other])
    assert got == want
    assert mgr.node_count(other) == size
    assert mgr.compose(f, mapping) == want  # f and the mapping are intact
    if f > 1 and mgr.top(f) <= max(mapping):
        assert mgr.gc_runs > runs


def random_target(enc, rnd):
    """A random state predicate: a union of conjunctions of ``variable == value`` and
    ``variable != value`` conditions."""
    mgr = enc.mgr
    out = FALSE
    for _ in range(rnd.randint(1, 4)):
        term = TRUE
        for i in rnd.sample(range(len(enc.cur_env)), rnd.randint(1, min(3, len(enc.cur_env)))):
            c = rnd.choice(list(enc.cur_env[i].values()))
            term = mgr.AND(term, c if rnd.random() < 0.6 else c ^ 1)
        out = mgr.OR(out, term)
    return out


def models(seeds, base=0):
    for seed in seeds:
        yield build_random_model(base + seed), None
        yield build_rich_model(base + 40_000 + seed)


@pytest.mark.parametrize("core", CORES)
def test_cpre_split_is_cpre(core):
    """Random targets, every coalition (the empty one and all actors included)."""
    compared = 0
    for model, profile in models(range(40), 210_000):
        cm = model.compile(profile=profile)
        enc = encode(cm, manager=core)
        mgr = enc.mgr
        rnd = random.Random(compared)
        targets = [random_target(enc, rnd) for _ in range(3)]
        targets += [enc.predicate(name) for name in [*cm.model.endings, "HORIZON"]]
        targets += [enc.dom, FALSE, TRUE]
        for x in targets:
            for coalition in coalitions(cm.actor_names):
                want = cpre(enc, coalition, x, step="compose")
                assert cpre(enc, coalition, x, step="split") == want
                assert cpre(enc, coalition, x, step="moves") == want
                assert mgr.AND(want, enc.active) == want
                compared += 1
        close(enc)
    assert compared > 2000


def fixpoints(enc, seed, step):
    """The fixpoint results of one encoding (kept alive by the returned objects)."""
    rnd = random.Random(seed)
    names = enc.cm.actor_names
    reach = reachable(enc, check=False)
    held: list = [reach]
    edges = [reach.states]
    for target in [*enc.cm.model.endings, "HORIZON"]:
        coalition = tuple(rnd.sample(names, rnd.randint(0, len(names))))
        tb = enc.predicate(target)
        a = attractor(enc, coalition, tb, step=step)
        kernels = [safe(enc, coalition, tb, method=m, step=step) for m in ("auto", "iterate")]
        kernels.append(safe(enc, coalition, tb, within=reach.states, step=step))
        c = contested(enc, coalition, tb, "reach", step=step)
        held += [a, *kernels, c]
        edges += [a.win, *a.layers, *(k.kernel for k in kernels), c.forced, c.blocked]
    return held, edges


@pytest.mark.parametrize("step", SPLIT_STEPS)
@pytest.mark.parametrize("core", CORES)
def test_fixpoints_identical_edge_by_edge(core, step, every_node):
    """The split run collects after every node of every substitution and after every
    quantification; the present run's results are held by their result objects."""
    compared = 0
    for seed, (model, profile) in enumerate(models(range(25), 250_000)):
        enc = encode(model.compile(profile=profile), manager=core)
        held, want = fixpoints(enc, seed, "compose")
        always_collect(enc.mgr)
        runs = enc.mgr.gc_runs
        held2, got = fixpoints(enc, seed, step)
        assert got == want
        assert enc.mgr.gc_runs > runs
        compared += len(want)
        del held, held2
        close(enc)
    assert compared > 500


@pytest.mark.parametrize("step", SPLIT_STEPS)
def test_crosscheck_with_the_split_step(step, monkeypatch, every_node):
    """The explicit cross-check (every coalition) with the split step selected by the
    environment, collecting at every opportunity."""
    monkeypatch.setenv(STEP_ENV, step)
    checked = 0
    for seed in range(15):
        assert check_model(build_random_model(230_000 + seed), seed=seed, every_coalition=True)
        model, profile = build_rich_model(240_000 + seed)
        checked += check_model(model, profile, seed, every_coalition=True, gc_always=True)
    assert checked >= 10


def test_step_selection(monkeypatch):
    cm = build_random_model(7).compile()
    enc = encode(cm)
    x = enc.predicate("HORIZON")
    calls = []
    real = substitute.compose_by_levels

    def spy(*args, **kwargs):
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(sys.modules["wavefront.symbolic.encode"], "compose_by_levels", spy)
    names = cm.actor_names[:1]
    monkeypatch.delenv(STEP_ENV, raising=False)
    want = cpre(enc, names, x)
    assert not calls  # the default is the present step
    monkeypatch.setenv(STEP_ENV, "split")
    assert cpre(enc, names, x) == want and len(calls) == 1
    assert cpre(enc, names, x, step="compose") == want and len(calls) == 1  # an argument wins
    monkeypatch.setenv(STEP_ENV, "compose")
    assert cpre(enc, names, x, step="split") == want and len(calls) == 2
    # "moves": one substitution per joint move of the coalition that is available somewhere
    spied = []
    monkeypatch.setattr(
        solve, "compose_by_levels", lambda *a, **k: spied.append(1) or real(*a, **k)
    )
    assert cpre(enc, names, x, step="moves") == want
    assert 1 <= len(spied) <= len(cm.actors[enc.actor_indices(names)[0]].actions)
    assert cpre(enc, [], x, step="moves") == cpre(enc, [], x, step="compose")
    assert len(calls) == 3  # no member: the plain split step
    monkeypatch.setattr(solve, "MOVES_LIMIT", 0)
    assert cpre(enc, names, x, step="moves") == want and len(calls) == 4  # too many moves
    monkeypatch.setenv(STEP_ENV, "relational")
    with pytest.raises(ValueError):
        cpre(enc, names, x)
    with pytest.raises(ValueError):
        safe(enc, names, x, step="relational")
