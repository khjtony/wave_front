"""The split steps on AGI v0.1 (docs/engine_split_step.md): ``cpre`` with ``step="split"``
and with ``step="moves"`` returns the edge of the present ``cpre`` on random targets and on
the first layers of the kernels the claims compute, for three coalitions, with and without a
selected profile; and (marked ``slow``, about a minute) the two whole kernels of the
benchmark have the recorded numbers of states under each split step, with none of the
initial states inside. The same on the multi-core core with its split step: ``cpre`` against
the own core's edge by edge, the two kernels at 1 and 12 threads, and one kernel edge by edge
(docs/engine_multicore.md)."""

from __future__ import annotations

import json
import os
import random
import subprocess
import sys
from pathlib import Path

import pytest

from tests.agi.common import target_bdd
from tests.agi_v0_3.bench_reorder import ORDERS, ordered_encoding
from tests.agi_v0_3.common import V01, compiled, key
from wavefront.model import V
from wavefront.symbolic import c_available, cpre, safe, sylvan_available
from wavefront.symbolic.bdd import FALSE, TRUE

pytestmark = pytest.mark.skipif(not c_available(), reason="C core not built")

COALITIONS = (["H"], ["H", "L"], ["A"])
ORDER = ORDERS / "v01_indifferent.json"
# docs/engine_reordering_spike.md section 4: the kernels of balance_control at one objective
KERNEL_STATES = {
    "aligned": 302461218730668589056,
    "indifferent": 196126762366467883008,
}
LAYERS = 6  # kernel layers used as targets (ticks horizon to horizon - 5)


def random_target(enc, rnd):
    """A union of conjunctions of ``variable == value`` and ``variable != value``."""
    mgr = enc.mgr
    out = FALSE
    for _ in range(rnd.randint(1, 4)):
        term = TRUE
        for i in rnd.sample(range(len(enc.cur_env)), rnd.randint(1, 4)):
            c = rnd.choice(list(enc.cur_env[i].values()))
            term = mgr.AND(term, c if rnd.random() < 0.6 else c ^ 1)
        out = mgr.OR(out, term)
    return mgr.protect(out)


def kernel_layers(enc, coalition, goal):
    """The first tick layers of ``safe(enc, coalition, goal)``, by the present step."""
    seen = []

    class Enough(Exception):
        pass

    def on_iteration(st):
        if len(seen) >= LAYERS:
            raise Enough

    def stat(enc_, k, t0, x, **extra):
        seen.append(enc.mgr.protect(x))
        return real(enc_, k, t0, x, **extra)

    import wavefront.symbolic.solve as solve

    real = solve._stat
    solve._stat = stat
    try:
        safe(enc, coalition, goal, on_iteration=on_iteration, step="compose")
    except Enough:
        pass
    finally:
        solve._stat = real
    return seen


@pytest.mark.parametrize("profiles", [(), ("no_treaty",)], ids=["no profile", "no_treaty"])
def test_cpre_split_is_cpre_on_v01(profiles):
    cm = compiled(key(V01, profiles))
    enc = ordered_encoding(cm, ORDER)
    mgr = enc.mgr
    rnd = random.Random(20261120)
    targets = [random_target(enc, rnd) for _ in range(12)]
    targets += [enc.predicate(name) for name in cm.model.endings]
    targets.append(target_bdd(enc, "balance_control"))
    for goal_name in KERNEL_STATES:
        goal = mgr.AND(
            target_bdd(enc, "balance_control"), enc.predicate(V.a_objective == goal_name)
        )
        mgr.protect(goal)
        for coalition in COALITIONS:
            targets += kernel_layers(enc, coalition, goal)
    compared = distinct = 0
    for x in targets:
        for coalition in COALITIONS:
            want = mgr.protect(cpre(enc, coalition, x, step="compose"))
            assert cpre(enc, coalition, x, step="split") == want
            assert cpre(enc, coalition, x, step="moves") == want
            mgr.unprotect(want)
            compared += 1
            distinct += want not in (FALSE, TRUE)
            mgr.maybe_gc()
    assert compared == 3 * (12 + len(cm.model.endings) + 1 + 2 * 3 * LAYERS)
    assert distinct > compared // 2


@pytest.mark.slow
@pytest.mark.parametrize("step", ["split", "moves"])
@pytest.mark.parametrize("goal_name", list(KERNEL_STATES))
def test_whole_kernel_with_the_split_step(goal_name, step):
    cm = compiled(key(V01, ()))
    enc = ordered_encoding(cm, ORDER)
    mgr = enc.mgr
    goal = mgr.AND(target_bdd(enc, "balance_control"), enc.predicate(V.a_objective == goal_name))
    mgr.protect(goal)
    res = safe(enc, ["H"], goal, step=step)
    assert enc.count(res.kernel) == KERNEL_STATES[goal_name]
    starts = cm.initial_states()
    assert len(starts) == 4
    assert not any(res.contains(s) for s in starts)


# -- the split step on the multi-core core (docs/engine_multicore.md section 4) ------------

needs_sylvan = pytest.mark.skipif(not sylvan_available(), reason="Sylvan core not built")


@needs_sylvan
@pytest.mark.parametrize("profiles", [(), ("no_treaty",)], ids=["no profile", "no_treaty"])
def test_sylvan_split_step_is_the_own_cores_cpre_on_v01(profiles):
    """``cpre`` with the split step on the Sylvan core equals the own core's present step,
    edge by edge after a transfer, on the targets of the test above."""
    cm = compiled(key(V01, profiles))
    ec = ordered_encoding(cm, ORDER, manager="c")
    es = ordered_encoding(cm, ORDER, manager="sylvan")
    assert es.mgr.names == ec.mgr.names
    mgr = ec.mgr
    rnd = random.Random(20261123)
    targets = [random_target(ec, rnd) for _ in range(12)]
    targets += [ec.predicate(name) for name in cm.model.endings]
    targets.append(target_bdd(ec, "balance_control"))
    for goal_name in KERNEL_STATES:
        goal = mgr.AND(target_bdd(ec, "balance_control"), ec.predicate(V.a_objective == goal_name))
        mgr.protect(goal)
        for coalition in COALITIONS:
            targets += kernel_layers(ec, coalition, goal)
    compared = 0
    for x in targets:
        xs = es.mgr.protect(mgr.transfer(x, es.mgr))
        for coalition in COALITIONS:
            want = cpre(ec, coalition, x, step="compose")
            got = cpre(es, coalition, xs, step="split")
            assert es.mgr.transfer(got, mgr) == want
            compared += 1
            mgr.maybe_gc()
            es.mgr.maybe_gc()
        es.mgr.unprotect(xs)
    es.mgr.close()
    assert compared == 3 * (12 + len(cm.model.endings) + 1 + 2 * 3 * LAYERS)


KERNEL_RUN = """
import json, sys
from tests.agi.common import target_bdd
from tests.agi_v0_3.bench_reorder import ORDERS, ordered_encoding
from tests.agi_v0_3.common import V01, compiled, key
from wavefront.model import V
from wavefront.symbolic import safe
cm = compiled(key(V01, ()))
enc = ordered_encoding(cm, ORDERS / "v01_indifferent.json", manager="sylvan")
mgr = enc.mgr
out = {"workers": mgr.workers}
for name in sys.argv[1:]:
    goal = mgr.AND(target_bdd(enc, "balance_control"), enc.predicate(V.a_objective == name))
    mgr.protect(goal)
    res = safe(enc, ["H"], goal, step="split")
    out[name] = [str(enc.count(res.kernel)), [res.contains(s) for s in cm.initial_states()]]
    mgr.unprotect(goal)
    del res
print("KERNELS", json.dumps(out))
"""


@needs_sylvan
@pytest.mark.slow
@pytest.mark.parametrize("threads", [1, 12])
def test_whole_kernels_on_sylvan_with_the_split_step(threads):
    """The two kernels of the benchmark on the Sylvan core with the split step, at 1 and 12
    worker threads (a process of their own each): the recorded numbers of states, none of the
    four initial states inside."""
    root = Path(__file__).resolve().parents[2]
    env = {**os.environ, "WAVEFRONT_BDD_THREADS": str(threads)}
    cmd = [sys.executable, "-c", KERNEL_RUN, *KERNEL_STATES]
    done = subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=root)
    assert done.returncode == 0, done.stderr[-3000:]
    line = next(x for x in done.stdout.splitlines() if x.startswith("KERNELS "))
    got = json.loads(line.removeprefix("KERNELS "))
    assert got["workers"] == threads
    for name, states in KERNEL_STATES.items():
        assert got[name] == [str(states), [False] * 4]


@needs_sylvan
@pytest.mark.slow
def test_whole_aligned_kernel_on_sylvan_is_the_own_cores():
    """The kernel itself, edge by edge after a transfer, against the own core's present
    step (``aligned``: the smaller of the two)."""
    cm = compiled(key(V01, ()))
    ec = ordered_encoding(cm, ORDER, manager="c")
    es = ordered_encoding(cm, ORDER, manager="sylvan")
    kernels = []
    for enc, step in ((ec, "compose"), (es, "split")):
        goal = enc.mgr.AND(
            target_bdd(enc, "balance_control"), enc.predicate(V.a_objective == "aligned")
        )
        enc.mgr.protect(goal)
        kernels.append(enc.mgr.protect(safe(enc, ["H"], goal, step=step).kernel))
    assert es.mgr.transfer(kernels[1], ec.mgr) == kernels[0]
    es.mgr.close()


FULL_TABLE_RUN = """
from tests.agi.common import NotComputed
from tests.agi_v0_3 import kernels
from tests.agi_v0_3.common import V01
try:
    kernels.membership(V01, ["H"], "balance_control", only=["indifferent"])
except NotComputed as exc:
    print("NOT COMPUTED", exc)
"""


@needs_sylvan
def test_a_full_table_reads_not_computed(tmp_path):
    """A kernel job of the harness on the Sylvan core with a table far too small: the part
    reads "not computed" (the table refused an operation, or filled in mid-flight and the
    child's exit status and message say so), and no reading is saved as computed."""
    root = Path(__file__).resolve().parents[2]
    readings = tmp_path / "readings.jsonl"
    env = {
        **os.environ,
        "WF_V03_CORE": "sylvan",
        "WF_V03_THREADS": "4",
        "WF_V03_MEMORY_GB": "4",
        "WF_V03_READINGS": str(readings),
        "WAVEFRONT_SYLVAN_NODES_LOG2": "20",
        "WAVEFRONT_SYLVAN_CACHE_LOG2": "18",
    }
    done = subprocess.run(
        [sys.executable, "-c", FULL_TABLE_RUN], env=env, capture_output=True, text=True, cwd=root
    )
    assert done.returncode == 0, done.stderr[-3000:]
    assert "NOT COMPUTED" in done.stdout and "node table" in done.stdout, done.stdout
    rows = [json.loads(line) for line in readings.read_text().splitlines()]
    assert rows and all(r["kind"] == "over" and r["core"] == "sylvan" for r in rows)
