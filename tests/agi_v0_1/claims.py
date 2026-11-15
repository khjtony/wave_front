"""The bounded claims D1 to D4 of AGI v0.1 (docs/agi_v0_1.md section 5, part A).

Each query is one bounded check of at most ``K`` transitions from ``s₀`` on the build with the
objective fixed under its own profile, in a forked process with v0's budget
(``WF_AGI_BMC_MINUTES``, default 12 minutes per query). v0's value of the same query is
computed beside it the same way and reported, never checked.
"""

from __future__ import annotations

import z3

from tests.agi.collapse import play_moves
from tests.agi.effort import least_effort, scores_for
from tests.agi_v0_1.common import K, budgeted, fixed
from wavefront.bmc.encode import encode
from wavefront.bmc.queries import BmcTrace, reach
from wavefront.model import V

CANCEL = (V.adoption > 0) & (
    V.paused | (V.regime.is_in(["mandatory", "treaty"]) & (V.oversight != "strong"))
)


def shortest(objective: str, target, version: str = "v0.1") -> tuple[int, list[str]] | None:
    """``(ticks, play)`` of a shortest play to ``target``, or ``None``."""
    key = ("shortest", objective, str(target), version)

    def run():
        cm = fixed(objective, version)
        trace = reach(cm, K, target)
        return None if trace is None else (len(trace.moves), play_moves(cm, trace))

    return budgeted(key, run)


def least_joint(objective: str, target: str, version: str = "v0.1"):
    """``(effort, ticks, play)`` of the cheapest play to ``target`` for ``H`` with ``L``."""
    key = ("least", objective, target, version)

    def run():
        cm = fixed(objective, version)
        found = least_effort(cm, K, target, scores_for(objective, ("H", "L")))
        if found is None:
            return None
        cost, states, moves = found
        return cost, len(moves), play_moves(cm, BmcTrace(list(states), list(moves)))

    return budgeted(key, run)


def first_wave_cancelled(objective: str):
    """A play on which ``L`` starts a wave at tick 0 (``adoption = 3`` at tick 1) and
    ``dependence`` is still ``low`` at tick 4, the tick the wave would land; or ``None``."""
    key = ("first_wave", objective)

    def run():
        cm = fixed(objective)
        enc = encode(cm, 4)
        solver = enc.solver()
        solver.add(*enc.assume.values())
        # Every transition to tick 4 is enforced (``active[t]`` gates the transition into t;
        # the first sight asserted ``active[0..3]`` only and left tick 4 free: a defect).
        solver.add(*(enc.active[t] for t in range(1, 5)))
        solver.add(enc.condition(V.adoption == 3, 1), enc.condition(V.dependence == "low", 4))
        if solver.check() != z3.sat:
            return None
        states, moves = enc.decode(solver.model(), 4)
        return play_moves(cm, BmcTrace(list(states), list(moves)))

    return budgeted(key, run)
