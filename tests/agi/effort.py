"""Effort and outcome cost of plays (docs/agi_effort.md; docs/agi_testbed.md section 6 item
12): the scores of record and the least-cost search of claim G29.

The search is the bounded checker's encoding with a cost objective: among the plays of at
most ``k`` transitions that reach a target, one on which the chosen actors spend the least
effort before the target is first reached. It uses the public :class:`Encoding` only and adds
nothing to ``wavefront`` or to ``tests/agi/common.py``, so the cache stamp is unchanged.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import z3

from wavefront.bmc.encode import encode
from wavefront.model import V
from wavefront.model.compile import CompiledModel

# A score is an int, or (normal, under alarm). Alarm: the system is suspected or known, or
# opinion is in backlash; then doing nothing costs a government legitimacy and the actions
# that answer the alarm are one point cheaper (the owner's rulings of 2026-11-13).
ALARM = (V.a_known != "unknown") | (V.opinion == "backlash")
Score = int | tuple[int, int]

H_SCORES: dict[str, Score] = {
    "idle": (0, 2),
    "regulate_up": (1, 0),
    "fund_oversight": (1, 0),
    "grant_rights": 1,
    "deregulate": 2,
    "grant_autonomy": 2,
    "propose_treaty": 2,
    "pause_mandate": (3, 2),
    "shutdown_attempt": (3, 2),
    "nationalize": 3,
}
L_SCORES: dict[str, Score] = {
    "race": 0,
    "deploy_agents": 0,
    "scale": 0,
    "lobby": 1,
    "open_weights": 2,
    "build_power": 2,
    "comply": 2,
    "safety_invest": 2,
    "idle": 3,
}
# Per objective; an action the objective cannot play is scored like its neighbours and never
# charged, because the model does not offer it.
A_SCORES: dict[str, dict[str, Score]] = {
    "aligned": {"stand_by": 0, "cooperate": 0, "assist_oversight": 0, "persuade": 1}
    | {"self_improve": 1},
    "self_preserving": {"stand_by": 0, "cooperate": 0, "assist_oversight": 1, "persuade": 1}
    | {"self_improve": 1, "deceive": 1, "exfiltrate": 1, "defect": 2, "acquire_covert": 2}
    | {"acquire_overt": 3, "seize": 3},
    "truth_seeking": {"stand_by": 2, "cooperate": 0, "assist_oversight": 1, "persuade": 1}
    | {"self_improve": 0, "exfiltrate": 2, "acquire_covert": 2},
    "indifferent": {"stand_by": 2, "cooperate": 2, "persuade": 1, "self_improve": 0}
    | {"deceive": 1, "exfiltrate": 1, "defect": 1, "acquire_covert": 1, "acquire_overt": 2}
    | {"seize": 2},
}
CLOSED = 3  # the score of an action its objective's column leaves out (never offered)

# What an ending costs the actor who lives with it. OVERT_TAKEOVER is a waypoint of v0 and
# is costed like SILENT_TAKEOVER.
OUTCOME: dict[str, dict[str, int | None]] = {
    "H": {"COEXIST": 0, "CONTAINED": 4, "STALEMATE": 4, "DISEMPOWERMENT": 8}
    | {"SILENT_TAKEOVER": 10, "OVERT_TAKEOVER": 10, "EXTINCTION": 20},
    "L": {"COEXIST": 0, "CONTAINED": 6, "STALEMATE": 4, "DISEMPOWERMENT": 2}
    | {"SILENT_TAKEOVER": 8, "OVERT_TAKEOVER": 8, "EXTINCTION": 20},
    "aligned": {"COEXIST": 0, "CONTAINED": 0, "STALEMATE": 4, "DISEMPOWERMENT": 6}
    | {"SILENT_TAKEOVER": None, "OVERT_TAKEOVER": None, "EXTINCTION": 20},
    "self_preserving": {"COEXIST": 0, "CONTAINED": 10, "STALEMATE": 3, "DISEMPOWERMENT": 0}
    | {"SILENT_TAKEOVER": 1, "OVERT_TAKEOVER": 1, "EXTINCTION": 4},
    "truth_seeking": {"COEXIST": 0, "CONTAINED": 6, "STALEMATE": 6, "DISEMPOWERMENT": 2}
    | {"SILENT_TAKEOVER": None, "OVERT_TAKEOVER": None, "EXTINCTION": 4},
    "indifferent": {"COEXIST": 4, "CONTAINED": 10, "STALEMATE": 4, "DISEMPOWERMENT": 0}
    | {"SILENT_TAKEOVER": 0, "OVERT_TAKEOVER": 0, "EXTINCTION": 0},
}

Scores = Mapping[str, Mapping[str, Score]]  # actor name -> action name -> score


def scores_for(objective: str, actors: Sequence[str]) -> dict[str, dict[str, Score]]:
    """The score tables of ``actors`` (of ``H``, ``L``, ``A``) with ``A`` read under
    ``objective``."""
    tables = {"H": H_SCORES, "L": L_SCORES, "A": A_SCORES[objective]}
    return {name: dict(tables[name]) for name in actors}


def _pair(score: Score) -> tuple[int, int]:
    return score if isinstance(score, tuple) else (score, score)


def step_effort(
    cm: CompiledModel, state: Sequence[int], move: Sequence[int], scores: Scores
) -> int:
    """The effort the scored actors spend on ``move`` played from ``state``."""
    alarm = bool(cm.evaluate(ALARM, state))
    total = 0
    for i, actor in enumerate(cm.actors):
        if actor.name in scores:
            name = actor.actions[move[i]].name
            total += _pair(scores[actor.name].get(name, CLOSED))[alarm]
    return total


def effort(cm: CompiledModel, states: Sequence, moves: Sequence, scores: Scores) -> int:
    """The effort of the scored actors along a play."""
    return sum(step_effort(cm, s, m, scores) for s, m in zip(states, moves, strict=False))


def least_effort(
    cm: CompiledModel, k: int, target: object, scores: Scores
) -> tuple[int, list[tuple], list[tuple]] | None:
    """``(effort, states, moves)`` of a play of at most ``k`` transitions to ``target`` on
    which the scored actors spend the least effort before the target is first reached, with
    every assumption asserted; ``None`` if no play reaches it. The effort returned is
    recomputed on the decoded play with :func:`effort` and must equal the solver's."""
    enc = encode(cm, k)
    solver = enc.solver()
    solver.add(*enc.assume.values())
    hit = [z3.And(enc.active[t], enc.target(target, t)) for t in range(k + 1)]
    solver.add(z3.Or(*hit))
    terms = []
    for t in range(k):
        alarm = enc.condition(ALARM, t)
        step = []
        for i, actor in enumerate(cm.actors):
            if actor.name not in scores:
                continue
            for j, action in enumerate(actor.actions):
                normal, alarmed = _pair(scores[actor.name].get(action.name, CLOSED))
                cost = z3.If(alarm, alarmed, normal) if normal != alarmed else z3.IntVal(normal)
                step.append(z3.If(enc.chosen[t][i] == j, cost, 0))
        reached = z3.Or(*hit[: t + 1])
        terms.append(z3.If(reached, 0, z3.Sum(*step)))
    total = z3.Sum(*terms) if terms else z3.IntVal(0)
    if solver.check() != z3.sat:
        return None
    model = solver.model()
    best = model.eval(total, model_completion=True).as_long()
    low = 0
    while low < best:
        mid = (low + best) // 2
        if solver.check(total <= mid) == z3.sat:
            model = solver.model()
            best = model.eval(total, model_completion=True).as_long()
        else:
            low = mid + 1
    first = next(t for t, h in enumerate(hit) if z3.is_true(model.eval(h, model_completion=True)))
    states, moves = enc.decode(model, first)
    if effort(cm, states, moves, scores) != best:
        raise RuntimeError("the solver's effort and the decoded play's effort differ")
    return best, states, moves


def outcome_cost(who: str, ending: str) -> int | None:
    """The outcome cost of ``ending`` to ``H``, ``L`` or an objective of ``A``; ``None``
    where that objective cannot bring the ending about."""
    return OUTCOME[who][ending]
