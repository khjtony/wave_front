"""Witness traces (spec section 5.4)."""

from __future__ import annotations

from collections import deque
from collections.abc import Collection

from ..model.model import ModelError
from .graph import Graph

__all__ = ["Trace", "witness"]


class Trace(list[tuple[int, tuple[int, ...] | None]]):
    """A play as a list of ``(state_id, joint_move)`` pairs; the last pair has the move
    ``None`` (its state is where the trace stops)."""

    @property
    def state_ids(self) -> list[int]:
        """The state ids along the trace."""
        return [s for s, _ in self]

    @property
    def joint_moves(self) -> list[tuple[int, ...]]:
        """The joint moves along the trace (one fewer than the states)."""
        return [m for _, m in self if m is not None]

    def render(self, g: Graph) -> str:
        """A Markdown table: tick, each actor's action, and the variables that changed
        (level names; ``tick`` and ``last_*`` are omitted as redundant). In an untimed
        model the first column is the step number. A model that defines
        ``trace_tick(state, step)`` and ``trace_changes(state, next_state)`` (the flattened
        multi-resolution model of :mod:`wavefront.engine.multires`) supplies those two
        columns itself."""
        cm = g.model
        tick_of = getattr(cm, "trace_tick", None)
        changes_of = getattr(cm, "trace_changes", None)
        names = cm.actor_names
        header = ["tick" if cm.timed else "step", *names, "changes"]
        rows = [header, ["---"] * len(header)]
        shown = [i for i, v in enumerate(cm.variables) if v.origin not in ("tick", "last")]
        for k, (sid, move) in enumerate(self):
            state = g.states[sid]
            if tick_of is not None:
                tick = tick_of(state, k)
            else:
                tick = str(state[cm.index["tick"]]) if cm.timed else str(k)
            if move is None:
                end = g.ending[sid]
                note = f"ending: {end}" if end is not None else "(trace ends)"
                rows.append([tick, *(["-"] * len(names)), note])
                continue
            nxt = g.states[self[k + 1][0]]
            if changes_of is not None:
                changes = changes_of(state, nxt)
            else:
                changes = [
                    f"{cm.variables[i].name}: {cm.level_name(i, state[i])} -> "
                    f"{cm.level_name(i, nxt[i])}"
                    for i in shown
                    if state[i] != nxt[i]
                ]
            rows.append([tick, *g.move_names(move), "; ".join(changes) or "-"])
        return "\n".join("| " + " | ".join(row) + " |" for row in rows)


def witness(g: Graph, source: int, targets: Collection[int]) -> Trace | None:
    """A shortest trace from ``source`` to a state in ``targets`` (breadth-first), or
    ``None`` if no target is reachable. Among equally short traces the one using the
    lowest move indices is returned."""
    n = len(g.states)
    if not 0 <= source < n:
        raise ModelError(f"state id {source} is not in the graph")
    goal = set(targets)
    parent: dict[int, tuple[int, int] | None] = {source: None}
    queue = deque([source])
    found = source if source in goal else None
    while queue and found is None:
        s = queue.popleft()
        for k, t in enumerate(g.succ[s]):
            if t not in parent:
                parent[t] = (s, k)
                if t in goal:
                    found = t
                    break
                queue.append(t)
    if found is None:
        return None
    steps: list[tuple[int, tuple[int, ...] | None]] = [(found, None)]
    link = parent[found]
    while link is not None:
        s, k = link
        steps.append((s, g.moves[s][k]))
        link = parent[s]
    steps.reverse()
    return Trace(steps)
