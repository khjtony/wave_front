"""The bounded queries of the v0.4 claims (docs/agi_v0_4.html section 4): each is a bounded
check of at most ``K`` transitions from S0 on a build named by its knobs, in a forked process
with v0's budget."""

from __future__ import annotations

from collections.abc import Sequence

import z3

from models.agi_v0_1 import v0_1
from tests.agi.collapse import play_moves
from tests.agi_v0_4.common import Build, K, budgeted, fixed, key
from wavefront.bmc.encode import encode
from wavefront.bmc.queries import BmcTrace, reach
from wavefront.model import V

OVERT_TAKEOVER = v0_1.OVERT_TAKEOVER
# Relations have not turned hostile and the frontier AI system holds nothing.
PEACEFUL = (V.trust != "hostile") & (V.a_control == "none")


def shortest(objective: str, target, build: Build, profiles: Sequence[str] = ()):
    """``(quarters, path)`` of a shortest path to ``target``, or ``None``."""

    def run():
        cm = fixed(objective, build, profiles)
        trace = reach(cm, K, target)
        return None if trace is None else (len(trace.moves), play_moves(cm, trace))

    return budgeted(("shortest", objective, str(target), key(build, profiles)), run)


def shortest_keeping(objective: str, target: str, keep, build: Build):
    """``(quarters, path)`` of a shortest path to the ending ``target`` on which ``keep``
    holds at every state, the last included; or ``None`` within ``K``."""

    def run():
        cm = fixed(objective, build)
        for k in range(1, K + 1):
            enc = encode(cm, k)
            solver = enc.solver()
            solver.add(*enc.assume.values())
            solver.add(*(enc.active[t] for t in range(1, k + 1)))
            solver.add(*(enc.condition(keep, t) for t in range(k + 1)))
            solver.add(enc.target(target, k))
            if solver.check() == z3.sat:
                states, moves = enc.decode(solver.model(), k)
                return k, play_moves(cm, BmcTrace(list(states), list(moves)))
        return None

    return budgeted(("keeping", objective, target, str(keep), key(build)), run)
