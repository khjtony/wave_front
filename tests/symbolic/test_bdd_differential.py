"""The compiled BDD core against the pure-Python reference (docs/engine_scaling.md section 7).

- Random operation sequences run on both managers side by side; after every step the C
  result, transferred into the reference manager, is the reference's own result as an edge
  (canonical form: equal edges iff equal functions), and the canonical-form queries
  (``node_count``, ``support``, ``count``, ``pick_one``, ``top``) agree.
- The same with a collection at every step on both sides (the pool of live results as
  roots, some protected, some held by a registered holder): nothing in use is freed, and
  the computed-table entries the C collector keeps are still right.
- Transfers between managers with a variable permutation, both directions.
- The symbolic engine on random models (both generators of the cross-checks) under both
  cores: the full explicit cross-check, and the fixpoints' results compared edge by edge.
- The selection rule of :func:`wavefront.symbolic.manager`.

Skipped when the compiled core is not built.
"""

from __future__ import annotations

import random

import pytest
from bmc.rich_models import build_rich_model
from helpers.random_games import build_random_model
from hypothesis import given, settings
from hypothesis import strategies as st

from symbolic.crosscheck import check_model
from wavefront.symbolic import (
    attractor,
    c_available,
    encode,
    manager,
    reachable,
    safe,
)
from wavefront.symbolic.bdd import FALSE, TRUE

pytestmark = pytest.mark.skipif(not c_available(), reason="C core not built")

NVARS = 10
STEPS = 40
OPS = (
    "and",
    "or",
    "xor",
    "iff",
    "implies",
    "diff",
    "not",
    "ite",
    "exists",
    "forall",
    "and_exists",
    "restrict",
    "simplify",
    "compose",
    "rename",
    "and_all",
    "or_all",
    "cube",
    "var",
)


def pair(nvars=NVARS):
    py, c = manager("python"), manager("c")
    for k in range(nvars):
        py.add_var(f"x{k}")
        c.add_var(f"x{k}")
    return py, c


def same(py, c, ep, ec, levels=range(NVARS)):
    """``ec`` (in ``c``) and ``ep`` (in ``py``) are the same function, by edge after
    transfer in both directions, and by every canonical-form query."""
    assert c.transfer(ec, py) == ep
    assert py.transfer(ep, c) == ec
    assert c.node_count(ec) == py.node_count(ep)
    assert c.support(ec) == py.support(ep)
    assert c.count(ec, levels) == py.count(ep, levels)
    assert c.pick_one(ec, levels) == py.pick_one(ep, levels)
    assert c.top(ec) == py.top(ep)


def step(py, c, pool, rnd):
    """Apply one random operation to both managers; return the two results."""
    op = rnd.choice(OPS)
    pick = lambda: rnd.randrange(len(pool))  # noqa: E731
    levels = rnd.sample(range(NVARS), rnd.randint(0, 4))
    if op == "var":
        k = rnd.randrange(NVARS)
        return py.var(k), c.var(k)
    if op == "cube":
        assign = {v: rnd.randint(0, 1) for v in levels}
        return py.cube(assign), c.cube(assign)
    i = pick()
    fp, fc = pool[i]
    if op == "not":
        return py.NOT(fp), c.NOT(fc)
    if op in ("exists", "forall"):
        return getattr(py, op)(fp, levels), getattr(c, op)(fc, levels)
    if op == "restrict":
        assign = {v: rnd.randint(0, 1) for v in levels}
        return py.restrict(fp, assign), c.restrict(fc, assign)
    if op == "rename":
        perm = list(range(NVARS))
        if rnd.random() < 0.5:
            rnd.shuffle(perm)  # any permutation: the slow path
        else:
            shift = rnd.randint(0, 2)  # order-preserving onto higher levels: the fast path
            perm = [min(v + shift, NVARS - 1) if v < NVARS - 3 else v for v in perm]
            perm = list(dict.fromkeys(perm)) + [v for v in range(NVARS) if v not in perm]
        mapping = {v: perm[v] for v in levels}
        if len(set(mapping.values())) < len(mapping):
            mapping = {v: v for v in levels}
        return py.rename(fp, mapping), c.rename(fc, mapping)
    if op == "compose":
        mp, mc = {}, {}
        for v in levels:
            gp, gc = pool[pick()]
            mp[v], mc[v] = gp, gc
        return py.compose(fp, mp), c.compose(fc, mc)
    if op in ("and_all", "or_all"):
        idx = [pick() for _ in range(rnd.randint(0, 5))]
        return (
            getattr(py, op)(pool[j][0] for j in idx),
            getattr(c, op)(pool[j][1] for j in idx),
        )
    gp, gc = pool[pick()]
    if op == "simplify":
        if gp == FALSE:
            return py.NOT(fp), c.NOT(fc)
        return py.simplify(fp, gp), c.simplify(fc, gc)
    if op == "and_exists":
        return py.and_exists(fp, gp, levels), c.and_exists(fc, gc, levels)
    if op == "ite":
        hp, hc = pool[pick()]
        return py.ITE(fp, gp, hp), c.ITE(fc, gc, hc)
    name = {"and": "AND", "or": "OR", "xor": "XOR", "iff": "IFF"}.get(op, op.upper())
    return getattr(py, name)(fp, gp), getattr(c, name)(fc, gc)


class Holder:
    def __init__(self, edges):
        self.edges = edges

    def bdd_roots(self):
        return list(self.edges)


def run_sequence(seed, steps=STEPS, gc_every_step=False):
    rnd = random.Random(seed)
    py, c = pair()
    pool = [(TRUE, TRUE), (FALSE, FALSE)]
    for k in range(4):
        pool.append((py.var(k), c.var(k)))
    freed = 0
    for _ in range(steps):
        ep, ec = step(py, c, pool, rnd)
        same(py, c, ep, ec)
        pool.append((ep, ec))
        if len(pool) > 24:  # drop a random old result: garbage for the collector
            pool.pop(rnd.randrange(2, len(pool) - 1))
        if gc_every_step:
            # roots three ways: passed, protected, and held by a registered holder
            third = len(pool) // 3
            hp = Holder([e for e, _ in pool[third : 2 * third]])
            hc = Holder([e for _, e in pool[third : 2 * third]])
            py.register(hp)
            c.register(hc)
            with py.protecting(*(e for e, _ in pool[:third])):
                with c.protecting(*(e for _, e in pool[:third])):
                    fp = py.gc([e for e, _ in pool[2 * third :]])
                    fc = c.gc([e for _, e in pool[2 * third :]])
            freed += fc
            assert fp >= 0 and fc >= 0
            assert py.live_nodes == c.live_nodes  # what survives is the same DAG
            del hp, hc
            for ep, ec in pool:
                same(py, c, ep, ec)
    return freed


@settings(max_examples=300, deadline=None)
@given(seed=st.integers(0, 2**32 - 1))
def test_random_operation_sequences(seed):
    run_sequence(seed)


@settings(max_examples=60, deadline=None)
@given(seed=st.integers(0, 2**32 - 1))
def test_random_sequences_with_collection_at_every_step(seed):
    run_sequence(seed, steps=30, gc_every_step=True)


def test_collection_reuses_nodes_and_keeps_results():
    """Long sequences with a collection at every step; freed nodes are reused and the cache
    entries that survive a collection stay correct."""
    freed = sum(run_sequence(10_000 + seed, steps=60, gc_every_step=True) for seed in range(20))
    assert freed > 1000


def test_transfer_with_permutation_both_directions():
    rnd = random.Random(7)
    for _ in range(50):
        py, c = pair()
        c2 = manager("c")
        py2 = manager("python")
        for k in range(NVARS):
            c2.add_var()
            py2.add_var()
        pool = [(py.var(k), c.var(k)) for k in range(NVARS)]
        for _ in range(15):
            pool.append(step(py, c, pool, rnd))
        perm = list(range(NVARS))
        rnd.shuffle(perm)
        mapping = dict(enumerate(perm))
        for ep, ec in pool[-5:]:
            want = py.transfer(ep, py2, mapping)
            assert c.transfer(ec, c2, mapping) == py2.transfer(want, c2)
            assert c.transfer(ec, py2, mapping) == want
            assert py.transfer(ep, c2, mapping) == c.transfer(ec, c2, mapping)


def test_counts_past_64_bits():
    """Exact counts over 150 levels (five 32-bit limbs) with complemented edges at every
    depth, against the reference's Python integers."""
    rnd = random.Random(3)
    n = 150
    py, c = pair(n)
    for _ in range(40):
        fp, fc = TRUE, TRUE
        for v in sorted(rnd.sample(range(n), 25), reverse=True):
            op = rnd.choice(("and", "or", "xor"))
            name = {"and": "AND", "or": "OR", "xor": "XOR"}[op]
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
        assert c.count(fc, levels) + c.count(fc ^ 1, levels) == 2 ** len(levels)
        assert c.transfer(fc, py) == fp


def test_errors_match_the_reference():
    py, c = pair(3)
    for mgr in (py, c):
        with pytest.raises(ValueError):
            mgr.var(3)
        with pytest.raises(ValueError):
            mgr.simplify(mgr.var(0), FALSE)
        with pytest.raises(ValueError, match="depends on level 2"):
            mgr.count(mgr.var(2), [0, 1])
        with pytest.raises(ValueError):
            mgr.rename(mgr.var(0), {0: 5})
        assert mgr.pick_one(FALSE) is None
        assert mgr.pick_one(TRUE, [0, 2]) == {0: 0, 2: 0}
        assert mgr.count(TRUE, [0, 1, 7]) == 8


def _results(enc, core_seed):
    """Fixpoint results of one encoding, as edges."""
    rnd = random.Random(core_seed)
    names = enc.cm.actor_names
    out = []
    reach = reachable(enc, check=False)
    out.append(reach.states)
    for target in [*enc.cm.model.endings, "HORIZON"]:
        coalition = tuple(rnd.sample(names, rnd.randint(0, len(names))))
        tb = enc.predicate(target)
        out.append(attractor(enc, coalition, tb).win)
        out.append(safe(enc, coalition, tb).kernel)
        out.append(safe(enc, coalition, tb, within=reach.states).kernel)
    return out


def test_fixpoints_identical_edge_by_edge():
    """The encoding and the fixpoints under both cores give the same functions."""
    compared = 0
    for seed in range(40):
        model = build_random_model(90_000 + seed)
        cm = model.compile()
        ep = encode(cm, manager="python")
        ec = encode(cm, manager="c")
        assert ec.mgr.core == "c" and ep.mgr.core == "python"
        for name in ("dom", "term", "live", "initial", "error", "active"):
            assert ec.mgr.transfer(getattr(ec, name), ep.mgr) == getattr(ep, name)
        rp = _results(ep, seed)
        rc = _results(ec, seed)
        assert len(rp) == len(rc)
        for a, b in zip(rp, rc, strict=True):
            assert ec.mgr.transfer(b, ep.mgr) == a
        compared += 1
    assert compared == 40


@pytest.mark.parametrize("core", ["python", "c"])
def test_crosscheck_sweep_under_each_core(core):
    """The explicit cross-check (every coalition) on seeded models of both generators,
    once per core."""
    checked = 0
    for seed in range(30):
        assert check_model(
            build_random_model(80_000 + seed), seed=seed, every_coalition=True, manager=core
        )
        model, profile = build_rich_model(130_000 + seed)
        checked += check_model(model, profile, seed, every_coalition=True, manager=core)
    assert checked >= 20


def test_crosscheck_with_collection_at_every_step_c():
    checked = 0
    for seed in range(20):
        model, profile = build_rich_model(160_000 + seed)
        checked += check_model(model, profile, seed, gc_always=True, manager="c")
    assert checked >= 14


def test_selection_rule(monkeypatch):
    monkeypatch.delenv("WAVEFRONT_BDD", raising=False)
    assert manager().core == "c"
    monkeypatch.setenv("WAVEFRONT_BDD", "c")
    assert manager().core == "c"
    monkeypatch.setenv("WAVEFRONT_BDD", "python")
    assert manager().core == "python"
    assert manager("c").core == "c"  # an explicit choice wins
    monkeypatch.setenv("WAVEFRONT_BDD", "rust")
    with pytest.raises(ValueError):
        manager()


def test_stats_report_the_core():
    cm = build_random_model(4).compile()
    for core in ("python", "c"):
        enc = encode(cm, manager=core)
        res = reachable(enc, check=False)
        assert all(s["core"] == core for s in res.stats)
