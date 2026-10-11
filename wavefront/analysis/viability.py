"""Viability kernels, the point of no return, the silent phase and distances
(spec section 7; theory.md sections 4.1 to 4.3)."""

from __future__ import annotations

import math
from collections.abc import Collection, Sequence
from dataclasses import dataclass

from ..engine import Graph, SafeResult, attractor, safe
from ..model.model import ModelError
from ._common import check_invariant, complement, everyone, rest_of, trace_state_ids

__all__ = [
    "viability",
    "point_of_no_return",
    "SilentPhase",
    "silent_phase",
    "Distance",
    "distance",
    "distance_table",
]


def viability(g: Graph, coalition: Collection[str], invariant_name: str) -> SafeResult:
    """The viability kernel ``K_C(phi) = Safe_C(phi)`` of a named invariant: the states from
    which ``coalition`` can keep the invariant until a terminal state (forever in an untimed
    model) whatever the other actors and Nature do. ``strategy`` gives a keeping move for
    each non-terminal kernel state."""
    return safe(g, coalition, check_invariant(g, invariant_name))


def point_of_no_return(trace: Sequence, kernel: Collection[int]) -> int | None:
    """Index of the first state of ``trace`` outside ``kernel`` (``t_K`` of theory.md 4.2),
    or ``None`` if the whole trace stays inside. ``trace`` is a
    :class:`~wavefront.engine.Trace` or a sequence of state ids."""
    for i, s in enumerate(trace_state_ids(trace)):
        if s not in kernel:
            return i
    return None


@dataclass(frozen=True)
class SilentPhase:
    """The three indices of theory.md section 4.2 along one trace (``None`` if the event
    never happens): ``t_K`` the point of no return (first state outside ``K_C(phi)``),
    ``t_L`` the first state from which the rest can force ``not phi``, and ``t_phi`` the
    first state violating ``phi``. ``t_K <= t_L <= t_phi`` whenever they are defined."""

    t_K: int | None
    t_L: int | None
    t_phi: int | None

    @property
    def silent(self) -> tuple[int, int | None] | None:
        """The silent phase ``[t_K, t_phi)`` as a half-open index range (end ``None``: to
        the end of the trace), or ``None`` if the trace never leaves the kernel."""
        return None if self.t_K is None else (self.t_K, self.t_phi)

    @property
    def contested_part(self) -> tuple[int, int | None] | None:
        """``[t_K, t_L)``: the outcome is out of the coalition's hands but not yet lost."""
        return None if self.t_K is None else (self.t_K, self.t_L)

    @property
    def lost_part(self) -> tuple[int, int | None] | None:
        """``[t_L, t_phi)``: the rest can force the visible failure."""
        return None if self.t_L is None else (self.t_L, self.t_phi)


def _first(ids: list[int], inside: Collection[int], want_inside: bool) -> int | None:
    for i, s in enumerate(ids):
        if (s in inside) == want_inside:
            return i
    return None


def silent_phase(
    trace: Sequence, g: Graph, coalition: Collection[str], invariant_name: str
) -> SilentPhase:
    """``t_K``, ``t_L`` and ``t_phi`` of theory.md section 4.2 for ``trace`` and the
    kernel of ``coalition`` for the named invariant. ``t_L`` uses the attractor of every
    actor not in the coalition, Nature included, to the states violating the invariant."""
    phi = check_invariant(g, invariant_name)
    kernel = safe(g, coalition, phi).kernel
    lost = attractor(g, rest_of(g, coalition), complement(g, phi)).win
    ids = trace_state_ids(trace)
    return SilentPhase(
        t_K=_first(ids, kernel, False),
        t_L=_first(ids, lost, True),
        t_phi=_first(ids, phi, False),
    )


@dataclass(frozen=True)
class Distance:
    """Distances of one state to the outside of a kernel ``K`` (spec section 7).

    - ``forced``: the rank of the state in ``attractor(adversary, S - K)``, the number of
      ticks within which the adversary can force leaving ``K``; ``None`` if it cannot.
    - ``shortest``: the rank in the attractor of every actor and Nature, the fewest steps
      of some play that leave ``K``; ``None`` if no play leaves it (0 outside ``K``).
    - ``margin``: the stage index of the state in ``M_0 = K``,
      ``M_{i+1} = {s in M_i | every joint move from s stays in M_i}``, i.e. the number of
      consecutive ticks of arbitrary play that certainly stay inside ``K``. ``None`` for a
      state outside ``K``; ``math.inf`` when no play ever leaves ``K``.
    """

    forced: int | None
    shortest: int | None
    margin: int | float | None


def _margin_stages(g: Graph, kernel: Collection[int]) -> dict[int, int | float]:
    """Stage index of every kernel state in the ``M_i`` sequence of :class:`Distance`.

    ``s`` drops out of ``M_{i+1}`` exactly when some move leads to a state that dropped
    out by stage ``i``, so the stage is computed by a backward breadth-first sweep from
    the complement: a state first removed at stage ``i + 1`` has margin ``i``.
    """
    inside = set(kernel)
    removed: dict[int, int] = {s: 0 for s in range(g.size()) if s not in inside}
    frontier = list(removed)
    pred: list[list[int]] = [[] for _ in range(g.size())]
    for s, ts in enumerate(g.succ):
        if s in inside:
            for t in set(ts):
                pred[t].append(s)
    stage = 0
    while frontier:
        stage += 1
        nxt = []
        for t in frontier:
            for s in pred[t]:
                if s not in removed:
                    removed[s] = stage
                    nxt.append(s)
        frontier = nxt
    return {s: (removed[s] - 1 if s in removed else math.inf) for s in inside}


def distance(
    g: Graph,
    state_id: int,
    kernel: Collection[int],
    coalition: Collection[str],
    adversary: Collection[str],
) -> Distance:
    """The forced, shortest and margin distances of ``state_id`` to ``S - kernel`` (see
    :class:`Distance`). ``coalition`` is the kernel's owner; it is validated but enters the
    numbers only through ``kernel``. By Lemma 5 of theory.md, ``forced`` is ``None`` inside
    the coalition's own kernel whenever ``adversary`` is disjoint from ``coalition``; the
    informative uses are a joint kernel against one member, and states outside the
    kernel."""
    return distance_table(g, [state_id], kernel, coalition, adversary)[state_id]


def distance_table(
    g: Graph,
    state_ids: Collection[int],
    kernel: Collection[int],
    coalition: Collection[str],
    adversary: Collection[str] | None,
) -> dict[int, Distance]:
    """:func:`distance` for several states at once (each fixpoint is computed once).
    With ``adversary=None`` the ``forced`` entries are ``None``."""
    for s in state_ids:
        if not 0 <= s < g.size():
            raise ModelError(f"state id {s} is not in the graph")
    g.actor_indices(coalition)
    kernel = set(kernel)
    outside = complement(g, kernel)
    forced = attractor(g, adversary, outside).rank if adversary is not None else {}
    shortest = attractor(g, everyone(g), outside).rank
    margins = _margin_stages(g, kernel)
    return {
        s: Distance(forced.get(s), shortest.get(s), margins.get(s) if s in kernel else None)
        for s in state_ids
    }
