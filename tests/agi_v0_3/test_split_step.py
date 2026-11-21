"""The split steps on AGI v0.1 (docs/engine_split_step.md): ``cpre`` with ``step="split"``
and with ``step="moves"`` returns the edge of the present ``cpre`` on random targets and on
the first layers of the kernels the claims compute, for three coalitions, with and without a
selected profile; and (marked ``slow``, about a minute) the two whole kernels of the
benchmark have the recorded numbers of states under each split step, with none of the
initial states inside."""

from __future__ import annotations

import random

import pytest

from tests.agi.common import target_bdd
from tests.agi_v0_3.bench_reorder import ORDERS, ordered_encoding
from tests.agi_v0_3.common import V01, compiled, key
from wavefront.model import V
from wavefront.symbolic import c_available, cpre, safe
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
