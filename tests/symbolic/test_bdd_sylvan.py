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
- The split step of this core (``compose_levels``, the nodes of a level in parallel) against
  the own core's present step, at the default, at 1 and at 8 threads, and as a soak at 12
  (docs/engine_multicore.md section 4); one manager per process; a full table is an error.

The Sylvan side runs on four worker threads unless ``WAVEFRONT_BDD_THREADS`` says otherwise,
so the parallel paths of the library are the ones compared. Skipped when either compiled
core is not built.
"""

from __future__ import annotations

import os
import random
import subprocess
import sys
from pathlib import Path

import pytest
from bmc.rich_models import build_rich_model
from helpers.random_games import build_random_model
from hypothesis import given, settings
from hypothesis import strategies as st

from symbolic.crosscheck import check_model, coalitions
from symbolic.test_bdd_differential import NVARS, Holder, _results, same, step
from wavefront.symbolic import c_available, cpre, encode, manager, reachable, sylvan_available
from wavefront.symbolic.bdd import FALSE, TRUE
from wavefront.symbolic.substitute import compose_by_levels

if sylvan_available():
    from wavefront.symbolic import bdd_sylvan

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
        c2 = manager("c")
        for k in range(NVARS):
            c2.add_var(f"x{k}")
        pool = [(c.var(k), s.var(k)) for k in range(NVARS)]
        for _ in range(15):
            pool.append(step(c, s, pool, rnd))
        perm = list(range(NVARS))
        rnd.shuffle(perm)
        mapping = dict(enumerate(perm))
        for ec, es in pool[-5:]:
            want = c.transfer(ec, c2, mapping)
            assert s.transfer(es, c2, mapping) == want
            assert c2.transfer(want, s) == s.transfer(es, s, mapping)  # within the one table
            assert c.transfer(ec, s, mapping) == s.transfer(es, s, mapping)
            assert s.transfer(es, s) == es
        s.close()


def test_one_manager_per_process():
    """A second live manager raises; a closed or unreferenced one does not count, and the
    next manager starts by collecting what it left."""
    s = manager("sylvan")
    s.add_var()
    with pytest.raises(RuntimeError, match="already live"):
        manager("sylvan")
    s.close()
    t = manager("sylvan")
    t.add_var()
    t.var(0)
    del t
    u = manager("sylvan")  # t is garbage: not live
    assert u.core == "sylvan"
    u.close()


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
        del rs
        es.mgr.close()


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


# -- the split step on this core (docs/engine_multicore.md section 4) -----------------------

SOAK = int(os.environ.get("WF_SYLVAN_SOAK", "0") or 0)


def test_split_step_against_the_own_core():
    """``cpre`` with the split step on this core (the C level loop, collecting before every
    level and after every quantification) against the own core's present step, edge by edge
    after a transfer: random targets of random models of both generators, every coalition;
    then the fixpoints (attractor stages, kernels by both methods and within a reachable set,
    contested regions)."""
    from symbolic.test_split_step import always_collect, fixpoints, models, random_target

    compared = 0
    for seed, (model, profile) in enumerate(models(range(20), 270_000)):
        cm = model.compile(profile=profile)
        ec, es = encode(cm, manager="c"), encode(cm, manager="sylvan")
        always_collect(es.mgr)
        bdd_sylvan.set_chunk(seed % 2)  # every other model: a collection after every node
        rnd = random.Random(seed)
        targets = [random_target(ec, rnd) for _ in range(3)]
        targets += [ec.predicate(name) for name in [*cm.model.endings, "HORIZON"]]
        targets += [ec.dom, FALSE, TRUE]
        for x in targets:
            xs = es.mgr.protect(ec.mgr.transfer(x, es.mgr))
            for coalition in coalitions(cm.actor_names):
                want = cpre(ec, coalition, x, step="compose")
                assert es.mgr.transfer(cpre(es, coalition, xs, step="split"), ec.mgr) == want
                compared += 1
            es.mgr.unprotect(xs)
        held_c, want = fixpoints(ec, seed, "compose")
        runs = es.mgr.gc_runs
        held_s, got = fixpoints(es, seed, "split")
        assert es.mgr.gc_runs > runs
        assert [es.mgr.transfer(e, ec.mgr) for e in got] == want
        compared += len(want)
        del held_c, held_s, got
        es.mgr.close()
    bdd_sylvan.set_chunk(0)
    assert compared > 1000


@pytest.mark.parametrize("threads", [1, 8])
def test_split_step_at_1_and_8_threads(threads):
    """The differential tests of the split step on this core (tests/symbolic/test_split_step.py
    and the test above) in a process of their own with ``threads`` workers: the thread count
    is fixed when the first manager of a process is made."""
    env = {**os.environ, "WAVEFRONT_BDD_THREADS": str(threads)}
    here = Path(__file__).resolve()
    args = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        str(here.parent / "test_split_step.py"),
        f"{here}::test_split_step_against_the_own_core",
        "-k",
        "sylvan or own_core",
    ]
    done = subprocess.run(args, env=env, capture_output=True, text=True, cwd=here.parents[2])
    assert done.returncode == 0, done.stdout[-3000:] + done.stderr[-3000:]
    assert " passed" in done.stdout and "failed" not in done.stdout


@pytest.mark.skipif(not SOAK, reason="a soak run: WF_SYLVAN_SOAK=<rounds>")
def test_soak():
    """The differential checks of the split step repeated ``WF_SYLVAN_SOAK`` times with new
    seeds, for races that show up rarely (run with WAVEFRONT_BDD_THREADS=12)."""
    from symbolic.test_split_step import always_collect, random_function, random_target

    rnd = random.Random(int(os.environ.get("WF_SYLVAN_SOAK_SEED", "1")))
    for k in range(SOAK):
        bdd_sylvan.set_chunk(k % 3)  # chunks of the default size, of 1 node, of 2 nodes
        s = manager("sylvan")
        levels = [s.add_var() for _ in range(14)]
        c = manager("c")
        for _ in levels:
            c.add_var()
        for _ in range(20):
            f = random_function(c, rnd, levels, 7)
            mapping = {v: random_function(c, rnd, levels, 4) for v in rnd.sample(levels, 9)}
            want = c.compose(f, mapping)
            fs = s.protect(c.transfer(f, s))
            ms = {v: c.transfer(g, s) for v, g in mapping.items()}
            always_collect(s)
            got = compose_by_levels(s, fs, ms, keep=list(ms.values()))
            assert s.transfer(got, c) == want, k
            assert compose_by_levels(s, fs, ms) == got, k  # no collection, same edge
            s.unprotect(fs)
        s.close()
        cm = build_random_model(500_000 + k).compile()
        ec, es = encode(cm, manager="c"), encode(cm, manager="sylvan")
        always_collect(es.mgr)
        for _ in range(3):
            x = random_target(ec, rnd)
            xs = es.mgr.protect(ec.mgr.transfer(x, es.mgr))
            for coalition in coalitions(cm.actor_names):
                want = cpre(ec, coalition, x, step="compose")
                assert es.mgr.transfer(cpre(es, coalition, xs, step="split"), ec.mgr) == want, k
            es.mgr.unprotect(xs)
        es.mgr.close()
    bdd_sylvan.set_chunk(0)


FULL_TABLE = """
import sys
from wavefront.symbolic import manager
s = manager("sylvan")
n = 22
xs = [s.add_var() for _ in range(n)]
ys = [s.add_var() for _ in range(n)]
eqs = [s.IFF(s.var(x), s.var(y)) for x, y in zip(xs, ys)]  # 2^22 nodes in this order
if sys.argv[1] == "midflight":
    f = s.and_all(eqs)  # one call that needs 64 times the table
else:  # many small calls, nothing collected: one is refused at its start
    for k in range(1 << 21):
        f = s.exists(s.cube({v: (k >> i) & 1 for i, v in enumerate(xs[:21])}), [xs[0]])
print("RESULT", s.node_count(f))
"""


def test_a_full_table_is_an_error_not_a_reading():
    """A table too small for the computation: an operation refused at its start raises
    MemoryError, and one that fills the table in mid-flight ends the process with the
    status and the message of the binding; never a result."""
    env = {**os.environ, "WAVEFRONT_SYLVAN_NODES_LOG2": "16", "WAVEFRONT_SYLVAN_CACHE_LOG2": "16"}
    root = Path(__file__).resolve().parents[2]

    def run(mode):
        cmd = [sys.executable, "-c", FULL_TABLE, mode]
        return subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=root)

    mid = run("midflight")
    assert mid.returncode == bdd_sylvan.TABLE_FULL_STATUS, mid.stderr[-2000:]
    assert bdd_sylvan.TABLE_FULL_MESSAGE in mid.stderr and "RESULT" not in mid.stdout
    steps = run("steps")
    assert "MemoryError" in steps.stderr and "RESULT" not in steps.stdout, steps.stderr[-2000:]


def test_table_sizes_follow_the_memory_limit():
    from wavefront.symbolic import _sylvan

    assert bdd_sylvan.table_sizes(12 << 30) == (28, 26)  # 6.4 GB of nodes, 2.4 GB of cache
    for gb in (8, 12, 26, 30, 85):
        limit = gb << 30
        nodes, cache = bdd_sylvan.table_sizes(limit)
        assert (1 << nodes) * 24 <= 0.62 * limit < (2 << nodes) * 24
        assert (1 << cache) * 36 <= 0.25 * limit < (2 << cache) * 36
    assert _sylvan.TABLE_FULL_STATUS == bdd_sylvan.TABLE_FULL_STATUS
    assert _sylvan.TABLE_FULL_MESSAGE == bdd_sylvan.TABLE_FULL_MESSAGE
