"""Pivotal coalitions (spec section 7; theory.md section 4.5)."""

from __future__ import annotations

import itertools
from collections.abc import Collection, Iterable
from dataclasses import dataclass

from ..engine import Graph, attractor, safe
from ..model.model import ModelError
from ._common import check_ending, complement

__all__ = ["PivotalResult", "pivotal"]


@dataclass
class PivotalResult:
    """The antichains of minimal coalitions (by inclusion) that can force, respectively
    block, an ending from every initial state considered. Each list is ordered by size,
    then by actor order."""

    forcing: list[frozenset[str]]
    blocking: list[frozenset[str]]


def _minimal(universe: list[str], works) -> list[frozenset[str]]:
    found: list[frozenset[str]] = []
    for size in range(len(universe) + 1):
        for combo in itertools.combinations(universe, size):
            c = frozenset(combo)
            if any(m <= c for m in found):
                continue
            if works(c):
                found.append(c)
    return found


def pivotal(
    g: Graph,
    ending_name: str,
    actors: Iterable[str] | None = None,
    include_nature: bool = False,
    initial: Collection[int] | None = None,
) -> PivotalResult:
    """Minimal coalitions drawn from ``actors`` (default: every declared actor, Nature
    excluded; Nature is added when ``include_nature``) that can force ``ending_name`` from
    every state in ``initial`` (default ``g.initial``), and minimal ones that can keep it
    from happening (``Safe_C(not E)``) from every such state. Actors outside the coalition,
    Nature included unless it is a member, are adversaries. Coalitions are enumerated by
    increasing size and supersets of minimal ones are skipped: both families are upward
    closed. With no initial state every coalition qualifies and the answer is the empty
    coalition."""
    cm = g.model
    target = check_ending(g, ending_name)
    nature = [a.name for a in cm.actors if a.is_nature]
    if actors is None:
        universe = [a.name for a in cm.actors if not a.is_nature]
    else:
        wanted = set(actors)
        universe = [cm.actors[i].name for i in g.actor_indices(wanted)]
    if include_nature:
        universe = [a for a in universe if a not in nature] + nature
    sources = list(g.initial if initial is None else initial)
    for s in sources:
        if not 0 <= s < g.size():
            raise ModelError(f"state id {s} is not in the graph")
    avoid = complement(g, target)

    def forces(c: frozenset[str]) -> bool:
        win = attractor(g, c, target).win
        return all(s in win for s in sources)

    def blocks(c: frozenset[str]) -> bool:
        kernel = safe(g, c, avoid).kernel
        return all(s in kernel for s in sources)

    return PivotalResult(_minimal(universe, forces), _minimal(universe, blocks))
