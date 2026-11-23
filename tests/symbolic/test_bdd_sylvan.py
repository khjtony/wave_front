"""The multi-core BDD core on Sylvan against the compiled core
(docs/engine_multicore_spike.md), with the checks of ``test_bdd_differential.py``:

- Random operation sequences on both managers side by side; after every step the two
  results are the same function (equal edges after a transfer in each direction) and the
  canonical-form queries agree.
- The same with a collection at every step of the Sylvan side: what the roots reach, and
  nothing else, is left in the table, and every live result still agrees.
- Exact counts past 64 bits, transfers under a permutation, the reference's errors.
- The encoding and the fixpoints on random models, edge by edge, and the explicit
  cross-check, also with a collection at every opportunity.

The Sylvan side runs on four worker threads unless ``WAVEFRONT_BDD_THREADS`` says otherwise,
so the parallel paths of the library are the ones compared. Skipped when either compiled
core is not built.
"""

from __future__ import annotations

import os
import random

import pytest
from bmc.rich_models import build_rich_model
from helpers.random_games import build_random_model
from hypothesis import given, settings
from hypothesis import strategies as st

from symbolic.crosscheck import check_model
from symbolic.test_bdd_differential import NVARS, Holder, _results, same, step
from wavefront.symbolic import c_available, encode, manager, reachable, sylvan_available
from wavefront.symbolic.bdd import FALSE, TRUE

pytestmark = pytest.mark.skipif(
    not (c_available() and sylvan_available()), reason="C or Sylvan core not built"
)

os.environ.setdefault("WAVEFRONT_BDD_THREADS", "4")


def pair(nvars=NVARS):
    c, s = manager("c"), manager("sylvan")
    for k in range(nvars):
        c.add_var(f"x{k}")
        s.add_var(f"x{k}")
    return c, s


def left_by_collection(s, roots):
    """The live nodes a collection must leave: what the roots of the call and of every live
    Sylvan manager reach. The table counts two reserved entries where ``node_count`` counts
    one constant."""
    from wavefront.symbolic.bdd_sylvan import _managers

    return s.node_count([*roots, *(e for m in _managers for e in m._roots())]) + 1


def run_sequence(seed, steps=40, gc_every_step=False):
    rnd = random.Random(seed)
    c, s = pair()
    pool = [(TRUE, TRUE), (FALSE, FALSE)]
    for k in range(4):
        pool.append((c.var(k), s.var(k)))
    freed = 0
    for _ in range(steps):
        ec, es = step(c, s, pool, rnd)
        same(c, s, ec, es)
        pool.append((ec, es))
        if len(pool) > 24:
            pool.pop(rnd.randrange(2, len(pool) - 1))
        if gc_every_step:
            third = len(pool) // 3
            holder = Holder([e for _, e in pool[third : 2 * third]])
            s.register(holder)
            with s.protecting(*(e for _, e in pool[:third])):
                freed += s.gc([e for _, e in pool[2 * third :]])
                assert s.live_nodes == left_by_collection(s, [e for _, e in pool[2 * third :]])
            del holder
            for ec, es in pool:
                same(c, s, ec, es)
    return freed


@settings(max_examples=300, deadline=None)
@given(seed=st.integers(0, 2**32 - 1))
def test_random_operation_sequences(seed):
    run_sequence(seed)


@settings(max_examples=60, deadline=None)
@given(seed=st.integers(0, 2**32 - 1))
def test_random_sequences_with_collection_at_every_step(seed):
    run_sequence(seed, steps=30, gc_every_step=True)


def test_collection_frees_nodes_and_keeps_results():
    freed = sum(run_sequence(10_000 + seed, steps=60, gc_every_step=True) for seed in range(20))
    assert freed > 1000


def test_transfer_with_permutation_both_directions():
    rnd = random.Random(7)
    for _ in range(50):
        c, s = pair()
        c2, s2 = pair()
        pool = [(c.var(k), s.var(k)) for k in range(NVARS)]
        for _ in range(15):
            pool.append(step(c, s, pool, rnd))
        perm = list(range(NVARS))
        rnd.shuffle(perm)
        mapping = dict(enumerate(perm))
        for ec, es in pool[-5:]:
            want = c.transfer(ec, c2, mapping)
            assert s.transfer(es, c2, mapping) == want
            assert s.transfer(es, s2, mapping) == c2.transfer(want, s2)
            assert c.transfer(ec, s2, mapping) == s.transfer(es, s2, mapping)
            assert s.transfer(es, s2) == es  # one table: the same level is the same edge


def test_counts_past_64_bits():
    rnd = random.Random(3)
    n = 150
    c, s = pair(n)
    for _ in range(40):
        fc, fs = TRUE, TRUE
        for v in sorted(rnd.sample(range(n), 25), reverse=True):
            name = rnd.choice(("AND", "OR", "XOR"))
            lit_c, lit_s = c.var(v), s.var(v)
            if rnd.random() < 0.5:
                lit_c, lit_s = lit_c ^ 1, lit_s ^ 1
            fc = getattr(c, name)(lit_c, fc)
            fs = getattr(s, name)(lit_s, fs)
            if rnd.random() < 0.3:
                fc, fs = fc ^ 1, fs ^ 1
        levels = list(range(n)) + [n + 5, n + 9]  # extra levels count as free
        assert s.count(fs, levels) == c.count(fc, levels)
        assert s.count(fs ^ 1, levels) == c.count(fc ^ 1, levels)
        assert s.count(fs, levels) + s.count(fs ^ 1, levels) == 2 ** len(levels)
        assert s.transfer(fs, c) == fc


def test_errors_match_the_reference():
    _, s = pair(3)
    with pytest.raises(ValueError):
        s.var(3)
    with pytest.raises(ValueError):
        s.simplify(s.var(0), FALSE)
    with pytest.raises(ValueError, match="depends on level 2"):
        s.count(s.var(2), [0, 1])
    with pytest.raises(ValueError):
        s.rename(s.var(0), {0: 5})
    assert s.pick_one(FALSE) is None
    assert s.pick_one(TRUE, [0, 2]) == {0: 0, 2: 0}
    assert s.count(TRUE, [0, 1, 7]) == 8


def test_fixpoints_identical_edge_by_edge():
    """The encoding and the fixpoints under both cores give the same functions."""
    for seed in range(40):
        cm = build_random_model(90_000 + seed).compile()
        ec = encode(cm, manager="c")
        es = encode(cm, manager="sylvan")
        assert es.mgr.core == "sylvan" and es.mgr.workers >= 1
        for name in ("dom", "term", "live", "initial", "error", "active"):
            assert es.mgr.transfer(getattr(es, name), ec.mgr) == getattr(ec, name)
        rc = _results(ec, seed)
        rs = _results(es, seed)
        assert len(rc) == len(rs)
        for a, b in zip(rc, rs, strict=True):
            assert es.mgr.transfer(b, ec.mgr) == a


def test_crosscheck_sweep():
    """The explicit cross-check (every coalition) on seeded models of both generators."""
    checked = 0
    for seed in range(30):
        assert check_model(
            build_random_model(80_000 + seed), seed=seed, every_coalition=True, manager="sylvan"
        )
        model, profile = build_rich_model(130_000 + seed)
        checked += check_model(model, profile, seed, every_coalition=True, manager="sylvan")
    assert checked >= 20


def test_crosscheck_with_collection_at_every_step():
    checked = 0
    for seed in range(20):
        model, profile = build_rich_model(160_000 + seed)
        checked += check_model(model, profile, seed, gc_always=True, manager="sylvan")
    assert checked >= 14


def test_selection_and_stats(monkeypatch):
    monkeypatch.setenv("WAVEFRONT_BDD", "sylvan")
    assert manager().core == "sylvan"
    assert manager("c").core == "c"  # an explicit choice wins
    enc = encode(build_random_model(4).compile())
    res = reachable(enc, check=False)
    assert all(st["core"] == "sylvan" for st in res.stats)
    stats = enc.mgr.stats()
    assert stats["workers"] == enc.mgr.workers and stats["peak_nodes"] >= stats["live_nodes"]
