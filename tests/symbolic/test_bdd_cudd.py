"""The CUDD core against the pure-Python reference (docs/engine_reordering_spike.md).

- With reordering off, the checks of ``test_bdd_differential.py``: random operation
  sequences side by side, every result equal as an edge after transfer in both directions,
  and ``node_count``, ``support``, ``count``, ``pick_one`` and ``top`` equal; the same with a
  collection at every step. ``simplify`` is the exception: its result is checked on the care
  set, then replaced by the reference's.
- With the order changed under the functions (a random shuffle or a sifting pass between
  steps, or CUDD's automatic reordering from a few nodes on): every result still equals the
  reference's after transfer in both directions, and ``support``, ``count``, ``pick_one`` and
  ``evaluate`` agree. This is the test of the stable variable identity: callers keep
  addressing variables by the level they were created at.
- Groups stay adjacent under sifting.
- The symbolic engine on random models under the CUDD core in each reordering mode: the
  fixpoints edge by edge against the reference, and the explicit cross-check.
- No reference is leaked: after ``close()`` CUDD counts no referenced node.

Skipped when the CUDD binding is not built.
"""

from __future__ import annotations

import random

import pytest
from bmc.rich_models import build_rich_model
from helpers.random_games import build_random_model
from hypothesis import given, settings
from hypothesis import strategies as st

from symbolic.crosscheck import check_model
from symbolic.test_bdd_differential import NVARS, OPS, Holder, _results, step
from wavefront.symbolic import attractor, encode, manager, reachable, safe
from wavefront.symbolic.bdd import FALSE, TRUE

try:
    from wavefront.symbolic.bdd_cudd import BDD as CuddBDD
except ImportError:
    CuddBDD = None

pytestmark = pytest.mark.skipif(CuddBDD is None, reason="CUDD binding not built")

MODES = ("off", "auto", "points")


def pair(nvars=NVARS, **kw):
    py, c = manager("python"), CuddBDD(**kw)
    for k in range(nvars):
        py.add_var(f"x{k}")
        c.add_var(f"x{k}")
    return py, c


def same_function(py, c, ep, ec, levels=range(NVARS)):
    """Equal functions, by edge after transfer in both directions and by the queries that
    do not depend on the order."""
    assert c.transfer(ec, py) == ep
    assert py.transfer(ep, c) == ec
    assert c.support(ec) == py.support(ep)
    assert c.count(ec, levels) == py.count(ep, levels)
    assert c.pick_one(ec, levels) == py.pick_one(ep, levels)


def same(py, c, ep, ec, levels=range(NVARS)):
    """:func:`same_function`, and the BDDs are the same graph (the orders are equal)."""
    same_function(py, c, ep, ec, levels)
    assert c.node_count(ec) == py.node_count(ep)
    assert c.top(ec) == py.top(ep)


def collect(py, c, pool):
    """A collection on both sides with the pool as roots three ways."""
    third = len(pool) // 3
    hp = Holder([e for e, _ in pool[third : 2 * third]])
    hc = Holder([e for _, e in pool[third : 2 * third]])
    py.register(hp)
    c.register(hc)
    with py.protecting(*(e for e, _ in pool[:third])):
        with c.protecting(*(e for _, e in pool[:third])):
            py.gc([e for e, _ in pool[2 * third :]])
            freed = c.gc([e for _, e in pool[2 * third :]])
    assert freed >= 0
    return freed


def run_sequence(seed, steps=40, gc_every_step=False, disturb=None, **kw):
    """Random operations on both managers. ``disturb(c, rnd)`` changes the order of the
    CUDD manager between steps; the comparison then leaves out what depends on the order."""
    rnd = random.Random(seed)
    py, c = pair(**kw)
    check = same if disturb is None and c.reorder_mode == "off" else same_function
    pool = [(TRUE, TRUE), (FALSE, FALSE)]
    for k in range(4):
        pool.append((py.var(k), c.var(k)))
    for _ in range(steps):
        peek = random.Random()
        peek.setstate(rnd.getstate())
        ep, ec = step(py, c, pool, rnd)
        if peek.choice(OPS) == "simplify":
            # only the care set is promised: the operator depends on the order, and CUDD's
            # keeps the smaller of its result and ``f`` (the reference differs on about one
            # call in a thousand even in the same order)
            peek.sample(range(NVARS), peek.randint(0, 4))
            (_, fc), (gp, gc) = pool[peek.randrange(len(pool))], pool[peek.randrange(len(pool))]
            if gp != FALSE:
                assert c.AND(ec, gc) == c.AND(fc, gc)
                ec = py.transfer(ep, c)
        check(py, c, ep, ec)
        pool.append((ep, ec))
        if len(pool) > 24:
            pool.pop(rnd.randrange(2, len(pool) - 1))
        if gc_every_step:
            collect(py, c, pool)
        if disturb is not None:
            disturb(c, rnd)
        if gc_every_step or disturb is not None:
            for ep, ec in pool:
                check(py, c, ep, ec)
    assert c.check()
    bits = [rnd.randint(0, 1) for _ in range(NVARS)]
    for ep, ec in pool:
        assert c.evaluate(ec, bits) == py.evaluate(ep, bits)
    order = c.order()
    assert c.close() == 0  # every reference given back
    return order


def shuffle(c, rnd):
    order = list(range(NVARS))
    rnd.shuffle(order)
    c.shuffle(order)
    assert c.order() == order


def sift(c, rnd):
    if rnd.random() < 0.3:
        c.reorder(rnd.choice(("sift", "group_sift", "sift_converge")))


@settings(max_examples=150, deadline=None)
@given(seed=st.integers(0, 2**32 - 1))
def test_static_order_equals_the_reference(seed):
    run_sequence(seed)


@settings(max_examples=40, deadline=None)
@given(seed=st.integers(0, 2**32 - 1))
def test_static_order_with_collection_at_every_step(seed):
    run_sequence(seed, steps=30, gc_every_step=True)


@settings(max_examples=100, deadline=None)
@given(seed=st.integers(0, 2**32 - 1))
def test_levels_keep_their_identity_under_shuffles(seed):
    run_sequence(seed, steps=30, disturb=shuffle)


@settings(max_examples=60, deadline=None)
@given(seed=st.integers(0, 2**32 - 1))
def test_levels_keep_their_identity_under_sifting_and_collection(seed):
    run_sequence(seed, steps=30, gc_every_step=True, disturb=sift)


def test_automatic_reordering_inside_operations(monkeypatch):
    """CUDD reorders in the middle of operations from 20 nodes on; the results are the
    reference's and some run really ends in another order."""
    monkeypatch.setenv("WAVEFRONT_CUDD_FIRST_REORDER", "20")
    moved = 0
    for seed in range(60):
        order = run_sequence(20_000 + seed, steps=60, reorder="auto")
        moved += order != list(range(NVARS))
    assert moved > 10


def test_pick_one_is_the_reference_pick_in_any_order():
    """The least assignment in level order, whatever the order of the BDD."""
    rnd = random.Random(11)
    for _ in range(30):
        py, c = pair()
        pool = [(py.var(k), c.var(k)) for k in range(NVARS)]
        for _ in range(12):
            pool.append(step(py, c, pool, rnd))
        for _ in range(8):
            shuffle(c, rnd)
            for ep, ec in pool:
                assert c.pick_one(ec, [1, 4]) == py.pick_one(ep, [1, 4])
                assert c.pick_one(ec) == py.pick_one(ep)


def test_groups_stay_adjacent_under_sifting():
    rnd = random.Random(5)
    for trial in range(20):
        py, c = pair(12)
        for k in range(0, 12, 2):
            assert c.group((k, k + 1))
        # a function whose good order is far from the given one: x_i <-> x_{i+6} pairs
        pool = [(py.var(k), c.var(k)) for k in range(12)]
        fp, fc = TRUE, TRUE
        for k in range(6):
            a, b = rnd.sample(range(12), 2)
            fp = py.AND(fp, py.IFF(py.var(a), py.var(b)) if k % 2 else py.OR(py.var(a), py.var(b)))
            fc = c.AND(fc, c.IFF(c.var(a), c.var(b)) if k % 2 else c.OR(c.var(a), c.var(b)))
        pool.append((fp, fc))
        for _ in range(10):
            pool.append(step(py, c, pool, rnd))
        keep = Holder([e for _, e in pool])
        c.register(keep)
        c.gc()
        c.reorder("group_sift")
        c.reorder("sift")
        for k in range(0, 12, 2):
            assert c.position(k + 1) == c.position(k) + 1, (trial, c.order())
        for ep, ec in pool:
            same_function(py, c, ep, ec, range(12))


def test_group_needs_adjacent_variables_and_can_be_switched_off():
    c = CuddBDD()
    for _ in range(4):
        c.add_var()
    with pytest.raises(ValueError):
        c.group((0, 2))
    off = CuddBDD(grouping=False)
    off.add_var()
    off.add_var()
    assert off.group((0, 1)) is False


def test_counts_past_64_bits():
    rnd = random.Random(3)
    n = 150
    py, c = pair(n)
    for _ in range(40):
        fp, fc = TRUE, TRUE
        for v in sorted(rnd.sample(range(n), 25), reverse=True):
            name = rnd.choice(("AND", "OR", "XOR"))
            lit_p, lit_c = py.var(v), c.var(v)
            if rnd.random() < 0.5:
                lit_p, lit_c = lit_p ^ 1, lit_c ^ 1
            fp = getattr(py, name)(lit_p, fp)
            fc = getattr(c, name)(lit_c, fc)
            if rnd.random() < 0.3:
                fp, fc = fp ^ 1, fc ^ 1
        levels = list(range(n)) + [n + 5, n + 9]  # extra levels count as free
        assert c.count(fc, levels) == py.count(fp, levels)
        assert c.count(fc ^ 1, levels) == py.count(fp ^ 1, levels)
        assert c.transfer(fc, py) == fp


def test_errors_match_the_reference():
    c = CuddBDD()
    for _ in range(3):
        c.add_var()
    with pytest.raises(ValueError):
        c.var(3)
    with pytest.raises(ValueError):
        c.simplify(c.var(0), FALSE)
    with pytest.raises(ValueError, match="depends on level 2"):
        c.count(c.var(2), [0, 1])
    with pytest.raises(ValueError):
        c.rename(c.var(0), {0: 5})
    with pytest.raises(IndexError):
        c.evaluate(c.var(2), [0, 1])
    assert c.pick_one(FALSE) is None
    assert c.pick_one(TRUE, [0, 2]) == {0: 0, 2: 0}
    assert c.count(TRUE, [0, 1, 7]) == 8
    with pytest.raises(ValueError):
        CuddBDD(reorder="sometimes")


def test_a_collected_edge_is_refused():
    c = CuddBDD()
    a, b = c.var(c.add_var()), c.var(c.add_var())
    f = c.AND(a, b)
    with c.protecting(a):
        c.gc()
        assert c.OR(a, a) == a
        with pytest.raises(ValueError, match="stale"):
            c.AND(f, a)


def _transferred(enc, seed, into):
    """The fixpoints of ``test_bdd_differential._results``, each copied into the manager
    ``into`` as soon as it is computed: the collections of the next one may release it."""
    rnd = random.Random(seed)
    names = enc.cm.actor_names
    move = lambda f: enc.mgr.transfer(f, into)  # noqa: E731
    reach = reachable(enc, check=False)
    out = [move(reach.states)]
    for target in [*enc.cm.model.endings, "HORIZON"]:
        coalition = tuple(rnd.sample(names, rnd.randint(0, len(names))))
        tb = enc.predicate(target)
        out.append(move(attractor(enc, coalition, tb).win))
        out.append(move(safe(enc, coalition, tb).kernel))
        out.append(move(safe(enc, coalition, tb, within=reach.states).kernel))
    return out


@pytest.mark.parametrize("mode", MODES)
def test_fixpoints_identical_edge_by_edge(mode, monkeypatch):
    """The encoding and the fixpoints under the CUDD core, in each reordering mode, give the
    reference's functions (compared in the reference manager)."""
    monkeypatch.setenv("WAVEFRONT_CUDD_FIRST_REORDER", "50")
    monkeypatch.setenv("WAVEFRONT_CUDD_RELEASE_MIN_NODES", "0")
    monkeypatch.setenv("WAVEFRONT_CUDD_REORDER_MIN_NODES", "0")
    reordered = 0
    for seed in range(25):
        cm = build_random_model(90_000 + seed).compile()
        ep = encode(cm, manager="python")
        ec = encode(cm, mgr=CuddBDD(reorder=mode))
        assert ec.mgr.core == "cudd"
        for c, n in ec.cur_to_next.items():  # the pairs the encoding grouped
            assert ec.mgr.position(n) == ec.mgr.position(c) + 1
        for name in ("dom", "term", "live", "initial", "error", "active"):
            assert ec.mgr.transfer(getattr(ec, name), ep.mgr) == getattr(ep, name)
        rp = _results(ep, seed)
        assert _transferred(ec, seed, ep.mgr) == rp
        if mode == "off":  # then once more, in the order a sifting pass leaves
            ec.mgr.gc()
            ec.mgr.reorder()
            assert _transferred(ec, seed, ep.mgr) == rp
        for c, n in ec.cur_to_next.items():
            assert ec.mgr.position(n) == ec.mgr.position(c) + 1
        reordered += ec.mgr.stats()["reorderings"] > 0
        assert ec.mgr.check()
    assert reordered >= 20


@pytest.mark.parametrize("mode", MODES)
def test_crosscheck_sweep_under_cudd(mode, monkeypatch):
    """The explicit cross-check (every coalition, strategies and witnesses included) with
    the CUDD core selected by the environment, in each reordering mode."""
    monkeypatch.setenv("WAVEFRONT_CUDD_REORDER", mode)
    monkeypatch.setenv("WAVEFRONT_CUDD_FIRST_REORDER", "50")
    monkeypatch.setenv("WAVEFRONT_CUDD_RELEASE_MIN_NODES", "0")
    monkeypatch.setenv("WAVEFRONT_CUDD_REORDER_MIN_NODES", "0")
    checked = 0
    for seed in range(15):
        assert check_model(
            build_random_model(80_000 + seed), seed=seed, every_coalition=True, manager="cudd"
        )
        model, profile = build_rich_model(130_000 + seed)
        checked += check_model(
            model, profile, seed, every_coalition=True, gc_always=True, manager="cudd"
        )
    assert checked >= 10


def test_selection_and_stats(monkeypatch):
    monkeypatch.setenv("WAVEFRONT_BDD", "cudd")
    monkeypatch.setenv("WAVEFRONT_CUDD_REORDER", "points")
    mgr = manager()
    assert mgr.core == "cudd" and mgr.reorder_mode == "points"
    assert manager("cudd").core == "cudd"
    cm = build_random_model(4).compile()
    enc = encode(cm, manager="cudd")
    res = reachable(enc, check=False)
    assert all(s["core"] == "cudd" for s in res.stats)
    assert {"live_nodes", "peak_nodes", "reorderings", "memory_bytes"} <= set(enc.mgr.stats())
