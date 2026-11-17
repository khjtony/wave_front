"""The bounded queries of the v0.2 claims (docs/agi_v0_2.html section 4): each is one bounded
check of at most ``K`` transitions from ``s₀`` on a build named by its switches, in a forked
process with v0's budget (``WF_AGI_BMC_MINUTES``, default 12 minutes a query)."""

from __future__ import annotations

import itertools
from collections.abc import Mapping

import z3

from tests.agi.collapse import play_moves
from tests.agi.effort import least_effort, scores_for
from tests.agi_v0_2.common import K, budgeted, fixed, key
from wavefront.bmc.encode import encode
from wavefront.bmc.queries import BmcTrace, reach
from wavefront.model import V

LICENSE_FAILS = V.regime.is_in(["mandatory", "treaty"]) & (V.oversight != "strong")
# A pending wave at a state that cancels it in the all-off build (v0.1's ``CANCEL``).
CANCEL = (V.adoption > 0) & (V.paused | LICENSE_FAILS)
# The last state before a landing, under a pause, with the weights open and the licence good.
PAUSED_OPEN_WAVE = (
    V.paused & V.weights_open & (V.adoption == 1) & ~LICENSE_FAILS & (V.dependence != "lock_in")
)


def shortest(objective: str, target, switches: Mapping[str, bool]):
    """``(ticks, play)`` of a shortest play to ``target``, or ``None``."""

    def run():
        cm = fixed(objective, switches)
        trace = reach(cm, K, target)
        return None if trace is None else (len(trace.moves), play_moves(cm, trace))

    return budgeted(("shortest", objective, str(target), key(switches)), run)


def least_joint(objective: str, target: str, switches: Mapping[str, bool]):
    """``(effort, ticks, play)`` of the cheapest play to ``target`` for ``H`` with ``L``."""

    def run():
        cm = fixed(objective, switches)
        found = least_effort(cm, K, target, scores_for(objective, ("H", "L")))
        if found is None:
            return None
        cost, states, moves = found
        return cost, len(moves), play_moves(cm, BmcTrace(list(states), list(moves)))

    return budgeted(("least", objective, target, key(switches)), run)


def first_wave_cancelled(objective: str, switches: Mapping[str, bool]):
    """A play on which a wave is started at tick 0 (``adoption = 3`` at tick 1) and
    ``dependence`` is still ``low`` at tick 4, the tick it would land; or ``None``. Every
    transition to tick 4 is enforced (the corrected query of v0.1's D4 (a))."""

    def run():
        cm = fixed(objective, switches)
        enc = encode(cm, 4)
        solver = enc.solver()
        solver.add(*enc.assume.values())
        solver.add(*(enc.active[t] for t in range(1, 5)))
        solver.add(enc.condition(V.adoption == 3, 1), enc.condition(V.dependence == "low", 4))
        if solver.check() != z3.sat:
            return None
        states, moves = enc.decode(solver.model(), 4)
        return play_moves(cm, BmcTrace(list(states), list(moves)))

    return budgeted(("first_wave", objective, key(switches)), run)


def lands_under_pause(objective: str, switches: Mapping[str, bool]):
    """A shortest play to a state with a pause in force, the weights open and a wave one tick
    from landing, such that ``dependence`` is one level higher in every successor of that
    state (checked on the explicit model over every available joint move): the wave lands
    whatever anyone plays. ``None`` when no such state is reached within the bound;
    ``AssertionError`` text when it is reached and some successor does not land the wave."""

    def run():
        cm = fixed(objective, switches)
        trace = reach(cm, K, PAUSED_OPEN_WAVE)
        if trace is None:
            return None
        state = tuple(trace.states[-1])
        if cm.is_terminal(state):
            return {"error": "the state found is terminal"}
        i = cm.index["dependence"]
        misses = 0
        for move in itertools.product(*cm.available(state)):
            misses += cm.step(state, move)[i] != state[i] + 1
        return {
            "ticks": len(trace.moves),
            "successors that miss": misses,
            "play": play_moves(cm, trace),
        }

    return budgeted(("lands_under_pause", objective, key(switches)), run)
