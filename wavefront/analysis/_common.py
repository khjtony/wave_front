"""Small helpers shared by the analysis modules."""

from __future__ import annotations

from collections import deque
from collections.abc import Collection, Iterable, Sequence

from ..engine import Graph
from ..model.expr import Const
from ..model.model import ModelError

__all__ = [
    "check_invariant",
    "check_ending",
    "complement",
    "everyone",
    "rest_of",
    "nearest_source",
    "is_trivial_guard",
    "trace_state_ids",
]


def check_invariant(g: Graph, name: str) -> set[int]:
    """States satisfying the named invariant; :class:`ModelError` if there is none."""
    if name not in g.model.invariant_fns:
        known = ", ".join(g.model.invariant_fns) or "none declared"
        raise ModelError(f"no invariant named {name!r} (invariants: {known})")
    return g.states_where(name)


def check_ending(g: Graph, name: str) -> set[int]:
    """Terminal states of the named ending (``"HORIZON"`` allowed in timed models)."""
    cm = g.model
    if name not in cm.ending_fns and not (name == "HORIZON" and cm.timed):
        known = ", ".join([*cm.ending_fns, *(["HORIZON"] if cm.timed else [])]) or "none"
        raise ModelError(f"no ending named {name!r} (endings: {known})")
    return g.ending_states(name)


def complement(g: Graph, states: Collection[int]) -> set[int]:
    """All state ids of ``g`` not in ``states``."""
    return set(range(g.size())) - set(states)


def everyone(g: Graph) -> list[str]:
    """Every actor of the graph's model, Nature included."""
    return list(g.model.actor_names)


def rest_of(g: Graph, coalition: Iterable[str]) -> list[str]:
    """Every actor, Nature included, that is not in ``coalition``."""
    members = set(g.actor_indices(coalition))
    return [a.name for a in g.model.actors if a.index not in members]


def nearest_source(g: Graph, sources: Iterable[int], targets: Collection[int]) -> int | None:
    """The source with the fewest steps to ``targets`` (first in ``sources`` order on
    ties), found by one backward breadth-first search; ``None`` if no source reaches."""
    sources = list(sources)
    goal = set(targets)
    if not goal or not sources:
        return None
    pred: list[list[int]] = [[] for _ in range(g.size())]
    for s, ts in enumerate(g.succ):
        for t in set(ts):
            pred[t].append(s)
    dist = dict.fromkeys(goal, 0)
    queue = deque(goal)
    while queue:
        t = queue.popleft()
        for s in pred[t]:
            if s not in dist:
                dist[s] = dist[t] + 1
                queue.append(s)
    reachable = [s for s in sources if s in dist]
    if not reachable:
        return None
    return min(reachable, key=lambda s: dist[s])


def is_trivial_guard(action: object) -> bool:
    """True for an action whose (compiled, possibly relaxed) guard is the constant TRUE."""
    expr = getattr(action, "guard_expr", None)
    return isinstance(expr, Const) and bool(expr.value)


def trace_state_ids(trace: Sequence) -> list[int]:
    """State ids of a :class:`~wavefront.engine.Trace` or of a plain sequence of ids."""
    return [step[0] if isinstance(step, tuple) else step for step in trace]
