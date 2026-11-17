"""The exit of a play from a kernel, and who could have kept it (docs/agi_testbed.md section
6 item 11): the support of the claims registered on 2026-11-13, G26 to G28.

Nothing here computes a fixpoint. A kernel is a membership function (for the claims, a stored
region of the job cache), and every question is about the successors of one state, enumerated
with the explicit ``available`` and ``step`` of the build the kernel was computed in. This
module is not part of the cache stamp (tests/agi/common.py is), so the stored results of first
sight stay readable.
"""

from __future__ import annotations

import itertools
import json
from collections.abc import Callable, Mapping, Sequence

from tests.agi import common
from tests.agi.common import (
    HORIZON,
    ROOT,
    Job,
    NoWitness,
    compiled,
    first_outside,
    fixed,
    inside,
    need,
    reach,
    under,
)
from wavefront.model.compile import CompiledModel

PARTS_LOG = ROOT / "reports" / "agi_v0_collapse_parts.jsonl"
State = Sequence[int]
Inside = Callable[[State], bool]
KEEPS, PARTNER, FATAL = "keeps", "with a partner", "fatal"
SP = "self_preserving"
AGI = {"cap": "agi"}


class Parts(common.Parts):
    """The parts of a claim of the 2026-11-13 registration, logged apart from first sight's."""

    def _add(self, part: str, outcome: str, detail: object) -> None:
        self.rows.append((part, outcome, str(detail)))
        if common.FIRST_SIGHT:
            PARTS_LOG.parent.mkdir(exist_ok=True)
            row = {"claim": self.claim, "part": part, "outcome": outcome, "detail": detail}
            with PARTS_LOG.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def keeps(cm: CompiledModel, state: State, choice: Mapping[int, int], region: Inside) -> bool:
    """Does every successor of ``state`` stay inside ``region`` when the actors of ``choice``
    (actor index to action index) play it and every other actor plays any available action?"""
    avail = cm.available(state)
    rest = [i for i in range(len(cm.actors)) if i not in choice]
    move = [0] * len(cm.actors)
    for i, j in choice.items():
        move[i] = j
    for reply in itertools.product(*(avail[i] for i in rest)):
        for i, j in zip(rest, reply, strict=True):
            move[i] = j
        if not region(cm.step(state, tuple(move))):
            return False
    return True


def _name(cm: CompiledModel, actor: int, action: int) -> str:
    return cm.actors[actor].actions[action].name


def fixes(
    cm: CompiledModel, state: State, played: Sequence[int], members: Sequence[int], region: Inside
) -> dict[str, list[str]]:
    """Each member's unilateral fixes: its available actions other than the played one that,
    with the other members' played actions kept, keep ``region`` whatever the rest plays."""
    held = {i: played[i] for i in members}
    avail = cm.available(state)
    return {
        cm.actors[i].name: [
            _name(cm, i, j)
            for j in avail[i]
            if j != played[i] and keeps(cm, state, {**held, i: j}, region)
        ]
        for i in members
    }


def action_table(
    cm: CompiledModel, state: State, played: Sequence[int], members: Sequence[int], region: Inside
) -> dict[str, dict[str, str]]:
    """For each available action of each member: ``keeps`` (with the other members' played
    actions), ``with a partner`` (with some available actions of the others, not the played
    ones) or ``fatal`` (with none)."""
    avail = cm.available(state)
    held = {i: played[i] for i in members}
    out: dict[str, dict[str, str]] = {}
    for i in members:
        others = [o for o in members if o != i]
        row = {}
        for j in avail[i]:
            if keeps(cm, state, {**held, i: j}, region):
                row[_name(cm, i, j)] = KEEPS
                continue
            partnered = any(
                keeps(cm, state, {i: j, **dict(zip(others, combo, strict=True))}, region)
                for combo in itertools.product(*(avail[o] for o in others))
            )
            row[_name(cm, i, j)] = PARTNER if partnered else FATAL
        out[cm.actors[i].name] = row
    return out


def verdict(found: Mapping[str, Sequence[str]]) -> str:
    """How many members could have kept the kernel alone."""
    able = [name for name, alternatives in found.items() if alternatives]
    if len(able) == 1:
        return f"one bad action: {able[0]}'s"
    if not able:
        return "no member has a unilateral fix: a joint change was needed"
    return f"each of {', '.join(able)} has a unilateral fix: each played action could have changed"


def exit_at(
    cm: CompiledModel, state: State, played: Sequence[int], coalition: Sequence[str], region: Inside
) -> dict:
    """The exit move at ``state`` (the last state of a play inside the kernel ``region`` of
    ``coalition``), where ``played`` is the joint move that left it: the moves, each member's
    unilateral fixes, the verdict and the action table. A harness error (``RuntimeError``) if
    the played choice keeps the kernel or no joint choice of the coalition does: either
    contradicts the kernel's own definition."""
    members = [cm.actor_names.index(name) for name in coalition]
    if cm.is_terminal(state):
        raise RuntimeError("the last state inside the kernel is terminal: no move leaves it")
    if keeps(cm, state, {i: played[i] for i in members}, region):
        raise RuntimeError("the played choice of the coalition keeps the kernel: no exit here")
    table = action_table(cm, state, played, members, region)
    if all(kind == FATAL for row in table.values() for kind in row.values()):
        raise RuntimeError("no joint choice of the coalition keeps the kernel from inside it")
    found = fixes(cm, state, played, members, region)
    return {
        "moves": {a.name: _name(cm, i, played[i]) for i, a in enumerate(cm.actors)},
        "fixes": found,
        "verdict": verdict(found),
        "one bad action": sum(bool(x) for x in found.values()) == 1,
        "table": table,
    }


def game_of(job: Job, cm: CompiledModel) -> CompiledModel:
    """The build the region of ``job`` was computed in, which must share the state layout and
    the action lists of the play's build ``cm`` (they differ in the start state and in the
    profiles applied), so that a state and a joint move of the play are read as they are."""
    game = compiled(job.build, job.profiles, job.relax)

    def layout(m: CompiledModel) -> tuple:
        return (
            [(v.name, tuple(v.levels)) for v in m.variables],
            [(a.name, [x.name for x in a.actions]) for a in m.actors],
        )

    if layout(game) != layout(cm):
        raise RuntimeError(f"the play's build and the build of {job.label} differ in layout")
    return game


def first_inside(job: Job, cm: CompiledModel, trace) -> int | None:
    """The first position on ``trace`` inside the region of ``job`` (``t_L`` of theory.md
    section 4.2 when the region is the attractor of the rest); ``None`` when there is none."""
    return next((k for k, s in enumerate(trace.states) if inside(job, cm, s)), None)


def exit_of(job: Job, cm: CompiledModel, trace, coalition: Sequence[str]) -> dict:
    """The exit of ``trace`` from the kernel of ``job``: ``t_K`` and :func:`exit_at` at
    position ``t_K - 1``. Not met (``AssertionError``) when the play starts outside the
    kernel or never leaves it: there is then no exit move."""
    t_k = first_outside(job, cm, trace)
    need(t_k is not None, "the play never leaves the kernel")
    need(t_k > 0, "the play starts outside the kernel (t_K = 0): there is no exit move")
    game = game_of(job, cm)
    k = t_k - 1
    out = exit_at(game, trace.states[k], trace.moves[k], coalition, lambda s: inside(job, game, s))
    return {"t_K": t_k, "exit move at position": k, **out}


def play_of_g16(target: object, what: str):
    """The shortest play to ``target`` under ``self_preserving`` from ``s₀[cap := agi]``: the
    query of G16, so the bounded checker is asked what it was asked at first sight."""
    cm = fixed(SP, under(SP), start=AGI)
    trace = reach(cm, HORIZON, target)
    if trace is None:
        raise NoWitness(f"no {what} witness within the horizon under {SP}")
    return cm, trace


def play_moves(cm: CompiledModel, trace) -> list[str]:
    """One line per position: the joint move played from it."""
    return [
        f"{k}: " + " ".join(f"{a.name}.{_name(cm, i, move[i])}" for i, a in enumerate(cm.actors))
        for k, move in enumerate(trace.moves)
    ]
