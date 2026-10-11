"""Attractors, safety kernels and contested regions (spec section 5.3).

Coalition semantics: for a coalition C (Nature may be a member) the controllable
predecessor of a set X is the set of non-terminal states with some C-move all of whose
completions by the other actors lead into X. A *cell* below is a pair (state, C-move);
its successors are the distinct states reached by the completions of that C-move.

- :func:`attractor` computes ``mu X. T | CPre_C(X)`` with the counter-based worklist
  algorithm: each cell counts its successors outside the current winning set; a state
  joins when one of its cells reaches zero.
- :func:`safe` computes ``nu X. phi & CPre_C(X)``: each cell counts its successors outside
  the current candidate set; a state leaves when none of its cells is at zero.

Terminal states have no cells: they are in an attractor iff they are in the target, and
in a safety kernel iff they satisfy ``phi``.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass
from operator import itemgetter
from typing import Literal

from ..model.model import ModelError
from .graph import Graph

__all__ = [
    "AttractorResult",
    "SafeResult",
    "ContestedResult",
    "attractor",
    "safe",
    "contested",
]

SubMove = tuple[int, ...]


@dataclass
class AttractorResult:
    """``win``: states from which the coalition can force the target. ``strategy[s]``: the
    coalition sub-move (action indices in actor order) that made ``s`` join; target states
    have no entry. ``rank[s]``: the iteration at which ``s`` joined (0 for the target), the
    number of ticks within which the coalition can force the target."""

    win: set[int]
    strategy: dict[int, SubMove]
    rank: dict[int, int]


@dataclass
class SafeResult:
    """``kernel``: states from which the coalition can keep ``phi`` forever (until a
    terminal state). ``strategy[s]``: a sub-move all of whose completions stay in the
    kernel (non-terminal kernel states only)."""

    kernel: set[int]
    strategy: dict[int, SubMove]


@dataclass
class ContestedResult:
    """``forced``: the coalition wins; ``blocked``: the rest of the actors (Nature included
    unless in the coalition) win the opposite objective; ``contested``: neither."""

    forced: set[int]
    blocked: set[int]
    contested: set[int]


@dataclass
class _Cells:
    state: list[int]
    sub: list[SubMove]
    succ: list[tuple[int, ...]]
    of_state: list[range]
    pred: list[list[int]]


def _projector(members: list[int]) -> Callable[[tuple[int, ...]], SubMove]:
    if not members:
        return lambda jm: ()
    if len(members) == 1:
        (only,) = members
        return lambda jm: (jm[only],)
    return itemgetter(*members)  # type: ignore[return-value]


def _cells(g: Graph, members: list[int]) -> _Cells:
    """Group every state's joint moves by the coalition's sub-move."""
    project = _projector(members)
    projected: dict[int, list[SubMove]] = {}
    state: list[int] = []
    sub: list[SubMove] = []
    succ: list[tuple[int, ...]] = []
    of_state: list[range] = []
    pred: list[list[int]] = [[] for _ in g.states]
    for s, moves in enumerate(g.moves):
        start = len(state)
        if moves:
            subs = projected.get(id(moves))
            if subs is None:
                subs = projected[id(moves)] = [project(jm) for jm in moves]
            groups: dict[SubMove, dict[int, None]] = {}
            for key, t in zip(subs, g.succ[s], strict=True):
                bucket = groups.get(key)
                if bucket is None:
                    groups[key] = {t: None}
                else:
                    bucket[t] = None
            for key, targets in groups.items():
                c = len(state)
                state.append(s)
                sub.append(key)
                succ.append(tuple(targets))
                for t in targets:
                    pred[t].append(c)
        of_state.append(range(start, len(state)))
    return _Cells(state, sub, succ, of_state, pred)


def _ids(g: Graph, states: Iterable[int]) -> set[int]:
    n = len(g.states)
    out = set(states)
    for s in out:
        if not 0 <= s < n:
            raise ModelError(f"state id {s} is not in the graph")
    return out


def attractor(g: Graph, coalition: Collection[str], target: Collection[int]) -> AttractorResult:
    """States from which ``coalition`` can force reaching ``target`` (``<<C>> F target``)."""
    cells = _cells(g, g.actor_indices(coalition))
    win = _ids(g, target)
    rank = dict.fromkeys(win, 0)
    strategy: dict[int, SubMove] = {}
    count = [len(ts) for ts in cells.succ]
    queue = deque(sorted(win))
    while queue:
        t = queue.popleft()
        r = rank[t] + 1
        for c in cells.pred[t]:
            count[c] -= 1
            if count[c] == 0:
                s = cells.state[c]
                if s not in win:
                    win.add(s)
                    rank[s] = r
                    strategy[s] = cells.sub[c]
                    queue.append(s)
    return AttractorResult(win, strategy, rank)


def safe(g: Graph, coalition: Collection[str], phi: Collection[int]) -> SafeResult:
    """States from which ``coalition`` can keep the play inside ``phi`` (``<<C>> G phi``)."""
    cells = _cells(g, g.actor_indices(coalition))
    inside = bytearray(len(g.states))
    for s in _ids(g, phi):
        inside[s] = 1
    count = [sum(1 for t in ts if not inside[t]) for ts in cells.succ]
    good = [sum(1 for c in cells.of_state[s] if count[c] == 0) for s in range(len(g.states))]
    queue = deque(
        s for s in range(len(g.states)) if inside[s] and not g.terminal[s] and good[s] == 0
    )
    for s in queue:
        inside[s] = 0
    while queue:
        t = queue.popleft()
        for c in cells.pred[t]:
            if count[c] == 0:
                s = cells.state[c]
                good[s] -= 1
                if good[s] == 0 and inside[s]:
                    inside[s] = 0
                    queue.append(s)
            count[c] += 1
    kernel = {s for s in range(len(g.states)) if inside[s]}
    strategy: dict[int, SubMove] = {}
    for s in kernel:
        for c in cells.of_state[s]:
            if count[c] == 0:
                strategy[s] = cells.sub[c]
                break
    return SafeResult(kernel, strategy)


def contested(
    g: Graph,
    coalition: Collection[str],
    target_or_phi: Collection[int],
    kind: Literal["reach", "keep"],
) -> ContestedResult:
    """Split the states into forced, blocked and contested for a reach or keep objective.

    ``reach``: forced is ``attractor(C, T).win``, blocked is ``safe(rest, not T).kernel``.
    ``keep``: forced is ``safe(C, phi).kernel``, blocked is ``attractor(rest, not phi).win``.
    ``rest`` is every actor, Nature included, that is not in the coalition.
    """
    members = set(g.actor_indices(coalition))
    rest = [a.name for a in g.model.actors if a.index not in members]
    goal = _ids(g, target_or_phi)
    everything = set(range(len(g.states)))
    if kind == "reach":
        forced = attractor(g, coalition, goal).win
        blocked = safe(g, rest, everything - goal).kernel
    elif kind == "keep":
        forced = safe(g, coalition, goal).kernel
        blocked = attractor(g, rest, everything - goal).win
    else:
        raise ValueError(f"kind must be 'reach' or 'keep', not {kind!r}")
    return ContestedResult(forced, blocked, everything - forced - blocked)
