"""Uniformity of computed coalition strategies (spec sections 1 and 7).

The solvers compute perfect-information strategies: one coalition move per state. A
strategy is *uniform* when each member's part of the move depends only on what that
member observes, so the members can play it without pooling information. A forcing or
keeping result that rests on a non-uniform strategy is an upper bound on what the
coalition can do with what its members see.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass, field

from ..engine import Graph

__all__ = ["UniformityResult", "is_uniform", "strategy_closure"]


@dataclass
class UniformityResult:
    """Uniformity of a coalition strategy.

    - ``uniform``: per-member uniformity. For every member ``a``, the component of the
      sub-move belonging to ``a`` is the same in any two strategy states that ``a``
      observes identically, so the members can play the strategy each acting on their
      own observations.
    - ``conflicts``: ``(member, s, t)`` triples violating this; for each member and each
      of its observation classes, the first state with the first move paired with the
      first state of each other move.
    - ``jointly_uniform``: the weaker check on the joint observation
      ``tuple(cm.observe(a, s) for a in coalition)`` (members pooling what they see).
    - ``joint_conflicts``: ``(s, t)`` pairs violating the joint check.

    The result is truthy exactly when ``uniform`` holds."""

    uniform: bool
    conflicts: list[tuple[str, int, int]] = field(default_factory=list)
    jointly_uniform: bool = True
    joint_conflicts: list[tuple[int, int]] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.uniform


def _class_conflicts(classes: dict) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for moves in classes.values():
        reps = list(moves.values())
        out.extend((reps[0], other) for other in reps[1:])
    return out


def is_uniform(
    g: Graph, coalition: Collection[str], strategy: Mapping[int, tuple[int, ...]]
) -> UniformityResult:
    """Check a coalition strategy (``{state_id: coalition sub-move}`` as returned by
    :func:`~wavefront.engine.attractor` or :func:`~wavefront.engine.safe`, members in
    actor order) for per-member uniformity and for joint-observation uniformity (see
    :class:`UniformityResult`). Nature observes everything, so its own component never
    conflicts."""
    cm = g.model
    members = [cm.actors[i].name for i in g.actor_indices(coalition)]
    per_member: list[dict[tuple, dict[int, int]]] = [{} for _ in members]
    joint: dict[tuple, dict[tuple[int, ...], int]] = {}
    for s in sorted(strategy):
        state = g.states[s]
        sub = tuple(strategy[s])
        views = tuple(cm.observe(m, state) for m in members)
        joint.setdefault(views, {}).setdefault(sub, s)
        for k, view in enumerate(views):
            per_member[k].setdefault(view, {}).setdefault(sub[k], s)
    conflicts = [
        (m, s, t) for m, classes in zip(members, per_member) for s, t in _class_conflicts(classes)
    ]
    joint_conflicts = _class_conflicts(joint)
    return UniformityResult(not conflicts, conflicts, not joint_conflicts, joint_conflicts)


def strategy_closure(
    g: Graph,
    coalition: Collection[str],
    strategy: Mapping[int, tuple[int, ...]],
    sources: Iterable[int],
) -> dict[int, tuple[int, ...]]:
    """The part of ``strategy`` that is actually used from ``sources``: the states reached
    when the coalition follows ``strategy`` and the others play anything, stopping at
    states without a strategy entry (targets and terminal states)."""
    idx = g.actor_indices(coalition)
    out: dict[int, tuple[int, ...]] = {}
    seen = set()
    queue = deque(s for s in sources if s in strategy)
    seen.update(queue)
    while queue:
        s = queue.popleft()
        sub = tuple(strategy[s])
        out[s] = sub
        for jm, t in zip(g.moves[s], g.succ[s], strict=True):
            if t not in seen and tuple(jm[i] for i in idx) == sub and t in strategy:
                seen.add(t)
                queue.append(t)
    return out
