"""Clustering of traces by the non-trivial guards they rely on (spec section 7)."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from ..engine import Graph, Trace
from ._common import is_trivial_guard

__all__ = ["Cluster", "cluster", "signature"]

Signature = frozenset[tuple[str, str]]


@dataclass
class Cluster:
    """Traces sharing one ``signature``: the set of ``(actor, action)`` pairs whose guard
    is not the constant ``TRUE`` and that were chosen somewhere along the trace (so their
    guard was satisfied there). ``representative`` is the shortest trace (the first one
    on ties)."""

    signature: Signature
    traces: list[Trace] = field(default_factory=list)

    @property
    def representative(self) -> Trace:
        """The shortest trace of the cluster."""
        return min(self.traces, key=len)


def signature(trace: Trace, g: Graph) -> Signature:
    """The ``(actor, action)`` pairs with a non-trivial guard used along ``trace``. Guards
    relaxed in the compiled model count as trivial."""
    out = set()
    actors = g.model.actors
    for move in trace.joint_moves:
        for actor, j in zip(actors, move, strict=True):
            action = actor.actions[j]
            if not is_trivial_guard(action):
                out.add((actor.name, action.name))
    return frozenset(out)


def cluster(traces: Iterable[Trace], g: Graph) -> list[Cluster]:
    """Group ``traces`` by :func:`signature`. Clusters are ordered by decreasing size, then
    by first appearance; traces keep their input order within a cluster."""
    groups: dict[Signature, Cluster] = {}
    for trace in traces:
        sig = signature(trace, g)
        groups.setdefault(sig, Cluster(sig)).traces.append(trace)
    order = list(groups.values())
    return sorted(order, key=lambda c: -len(c.traces))
