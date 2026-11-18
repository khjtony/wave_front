"""The bounded queries of the v0.3 claims (docs/agi_v0_3.html section 5): each is one bounded
check of at most ``K`` transitions from ``s₀`` on a build named by its options, in a forked
process with v0's budget (``WF_AGI_BMC_MINUTES``, default 12 minutes a query)."""

from __future__ import annotations

from collections.abc import Sequence

import z3

from models.agi_v0_1 import v0_1
from tests.agi.collapse import play_moves
from tests.agi.effort import least_effort, scores_for
from tests.agi_v0_3.common import Build, K, budgeted, fixed, key
from wavefront.bmc.encode import encode
from wavefront.bmc.queries import BmcTrace, reach
from wavefront.model import V

# A state that reads ``OPEN_TAKEOVER`` (total control of ``O``, and neither of the two endings
# before it in precedence) after a shutdown of ``A`` that succeeded.
SHUT_THEN_OPEN = (
    V.shut
    & (V.o_control == "total")
    & (V.h_power != "none")
    & ~((V.a_control == "total") & v0_1.MAJORITY_UNSEEN)
)


def shortest(objective: str, target, build: Build, profiles: Sequence[str] = ()):
    """``(ticks, play)`` of a shortest play to ``target``, or ``None``."""

    def run():
        cm = fixed(objective, build, profiles)
        trace = reach(cm, K, target)
        return None if trace is None else (len(trace.moves), play_moves(cm, trace))

    return budgeted(("shortest", objective, str(target), key(build, profiles)), run)


def least_joint(objective: str, target: str, build: Build):
    """``(effort, ticks, play)`` of the cheapest play to ``target`` for ``H`` with ``L``."""

    def run():
        cm = fixed(objective, build)
        found = least_effort(cm, K, target, scores_for(objective, ("H", "L")))
        if found is None:
            return None
        cost, states, moves = found
        return cost, len(moves), play_moves(cm, BmcTrace(list(states), list(moves)))

    return budgeted(("least", objective, target, key(build)), run)


def first_wave_cancelled(objective: str, build: Build):
    """A play on which a wave is started at tick 0 (``adoption = 3`` at tick 1) and
    ``dependence`` is still ``low`` at tick 4, the tick it would land; or ``None``. Every
    transition to tick 4 is enforced (the corrected query of v0.1's D4 (a))."""

    def run():
        cm = fixed(objective, build)
        enc = encode(cm, 4)
        solver = enc.solver()
        solver.add(*enc.assume.values())
        solver.add(*(enc.active[t] for t in range(1, 5)))
        solver.add(enc.condition(V.adoption == 3, 1), enc.condition(V.dependence == "low", 4))
        if solver.check() != z3.sat:
            return None
        states, moves = enc.decode(solver.model(), 4)
        return play_moves(cm, BmcTrace(list(states), list(moves)))

    return budgeted(("first_wave", objective, key(build)), run)
