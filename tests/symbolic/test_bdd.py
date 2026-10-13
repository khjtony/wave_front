"""The BDD manager against truth tables on random functions of a few variables."""

import itertools
import random

from hypothesis import given, settings
from hypothesis import strategies as st

from wavefront.symbolic.bdd import BDD, FALSE, TRUE

N = 6
ROWS = list(itertools.product((0, 1), repeat=N))  # row r assigns level k to ROWS[r][k]
FULL = (1 << len(ROWS)) - 1


def table(mgr, f):
    """The truth table of ``f`` as an int with bit r set when row r satisfies f."""
    return sum(1 << r for r, row in enumerate(ROWS) if mgr.evaluate(f, row))


def random_function(mgr, rnd, depth=4):
    """A random function and its truth table built from literals and connectives."""
    if depth == 0 or rnd.random() < 0.2:
        k = rnd.randrange(N)
        t = sum(1 << r for r, row in enumerate(ROWS) if row[k])
        if rnd.random() < 0.5:
            return mgr.var(k), t
        return mgr.nvar(k), FULL ^ t
    op = rnd.choice(("and", "or", "xor", "not", "ite", "imp"))
    a, ta = random_function(mgr, rnd, depth - 1)
    if op == "not":
        return mgr.NOT(a), FULL ^ ta
    b, tb = random_function(mgr, rnd, depth - 1)
    if op == "and":
        return mgr.AND(a, b), ta & tb
    if op == "or":
        return mgr.OR(a, b), ta | tb
    if op == "xor":
        return mgr.XOR(a, b), ta ^ tb
    if op == "imp":
        return mgr.IMPLIES(a, b), (FULL ^ ta) | tb
    c, tc = random_function(mgr, rnd, depth - 1)
    return mgr.ITE(a, b, c), (ta & tb) | ((FULL ^ ta) & tc)


def manager():
    mgr = BDD()
    for k in range(N):
        mgr.add_var(f"x{k}")
    return mgr


def exists_table(t, levels):
    out = 0
    for r, row in enumerate(ROWS):
        for bits in itertools.product((0, 1), repeat=len(levels)):
            other = list(row)
            for v, b in zip(levels, bits, strict=True):
                other[v] = b
            if t >> ROWS.index(tuple(other)) & 1:
                out |= 1 << r
                break
    return out


@settings(max_examples=150, deadline=None)
@given(seed=st.integers(0, 2**32 - 1))
def test_operations_match_truth_tables(seed):
    rnd = random.Random(seed)
    mgr = manager()
    f, tf = random_function(mgr, rnd)
    g, tg = random_function(mgr, rnd)
    assert table(mgr, f) == tf
    assert table(mgr, g) == tg
    # canonicity: equal functions are equal edges
    assert (f == g) == (tf == tg)
    assert mgr.AND(f, g) == mgr.NOT(mgr.OR(mgr.NOT(f), mgr.NOT(g)))
    levels = sorted(rnd.sample(range(N), rnd.randint(1, 3)))
    assert table(mgr, mgr.exists(f, levels)) == exists_table(tf, levels)
    assert table(mgr, mgr.forall(f, levels)) == FULL ^ exists_table(FULL ^ tf, levels)
    assert table(mgr, mgr.and_exists(f, g, levels)) == exists_table(tf & tg, levels)
    # restrict
    assign = {v: rnd.randint(0, 1) for v in rnd.sample(range(N), 2)}
    rf = mgr.restrict(f, assign)
    for r, row in enumerate(ROWS):
        other = list(row)
        for v, b in assign.items():
            other[v] = b
        assert mgr.evaluate(rf, row) == bool(tf >> ROWS.index(tuple(other)) & 1)
    # compose: substitute g for one variable and h for another
    h, th = random_function(mgr, rnd, 2)
    a, b = rnd.sample(range(N), 2)
    cf = mgr.compose(f, {a: g, b: h})
    for row in ROWS:
        other = list(row)
        other[a] = int(mgr.evaluate(g, row))
        other[b] = int(mgr.evaluate(h, row))
        assert mgr.evaluate(cf, row) == mgr.evaluate(f, other)
    # rename: a permutation of the variables
    perm = list(range(N))
    rnd.shuffle(perm)
    nf = mgr.rename(f, dict(enumerate(perm)))
    for row in ROWS:
        other = [row[perm[k]] for k in range(N)]
        assert mgr.evaluate(nf, row) == mgr.evaluate(f, other)
    # simplify agrees on the care set
    if g != FALSE:
        sf = mgr.simplify(f, g)
        for r, row in enumerate(ROWS):
            if tg >> r & 1:
                assert mgr.evaluate(sf, row) == bool(tf >> r & 1)
    # count and pick_one
    assert mgr.count(f, range(N)) == bin(tf).count("1")
    pick = mgr.pick_one(f, range(N))
    if tf == 0:
        assert pick is None
    else:
        assert mgr.evaluate(f, pick)
        assert len(pick) == N
    # count over a superset of the support with an extra variable
    assert mgr.count(TRUE, range(3)) == 8
    assert mgr.count(FALSE, range(3)) == 0


def test_gc_keeps_roots_and_reuses_nodes():
    rnd = random.Random(1)
    mgr = manager()
    keep, tk = random_function(mgr, rnd, 5)
    for _ in range(20):
        random_function(mgr, rnd, 5)
    before = mgr.live_nodes
    freed = mgr.gc([keep])
    assert freed > 0
    assert mgr.live_nodes == before - freed
    assert table(mgr, keep) == tk
    again, ta = random_function(mgr, rnd, 5)
    assert table(mgr, again) == ta
    assert table(mgr, keep) == tk


def test_protect_and_register():
    mgr = manager()
    f = mgr.AND(mgr.var(0), mgr.var(3))
    mgr.protect(f)

    class Holder:
        def __init__(self, e):
            self.e = e

        def bdd_roots(self):
            return [self.e]

    g = mgr.XOR(mgr.var(1), mgr.var(5))
    h = Holder(g)
    mgr.register(h)
    mgr.gc()
    assert mgr.evaluate(f, [1, 0, 0, 1, 0, 0])
    assert mgr.evaluate(g, [0, 1, 0, 0, 0, 0])
    mgr.unprotect(f)
    del h
    mgr.gc()
    assert mgr.live_nodes == 1


def test_deep_order():
    """Hundreds of variables: no recursion trouble, counts as big ints."""
    mgr = BDD()
    levels = [mgr.add_var() for _ in range(600)]
    f = TRUE
    for v in reversed(levels):
        f = mgr.OR(mgr.var(v), f) if v % 2 else mgr.AND(mgr.var(v), f)
    g = mgr.XOR(f, mgr.var(0))
    assert mgr.count(mgr.or_all(mgr.var(v) for v in levels), levels) == 2**600 - 1
    assert mgr.exists(g, levels) == TRUE
    assert mgr.node_count(f) <= 601
