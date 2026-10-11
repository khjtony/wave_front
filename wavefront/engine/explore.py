"""Breadth-first exploration of a compiled model (spec section 5.2)."""

from __future__ import annotations

import itertools
from collections.abc import Callable, Iterable, Sequence

from ..model.compile import CompiledModel
from ..model.model import ModelError
from .graph import Graph

__all__ = ["explore", "BudgetExceeded"]

PROGRESS_EVERY = 10_000


class BudgetExceeded(RuntimeError):
    """Exploration found more states than ``max_states``."""


def _initial_states(cm: CompiledModel, initial: Iterable[Sequence[int]] | None) -> list[tuple]:
    if initial is None:
        return cm.initial_states()
    out = []
    for state in initial:
        state = tuple(state)
        if len(state) != len(cm.variables) or any(
            not isinstance(x, int) or not 0 <= x < v.size
            for x, v in zip(state, cm.variables, strict=False)
        ):
            raise ModelError(f"initial state {state} does not match the model's variables")
        out.append(state)
    return list(dict.fromkeys(out))


def explore(
    cm: CompiledModel,
    initial: Iterable[Sequence[int]] | None = None,
    max_states: int = 1_000_000,
    on_progress: Callable[[int, int], None] | None = None,
) -> Graph:
    """Explore every state reachable from ``initial`` (default: the model's initial
    states) breadth-first.

    Raises :class:`ModelError` when an actor has no available action, two Sets conflict,
    endings overlap or a monotone variable decreases, and :class:`BudgetExceeded` when more
    than ``max_states`` states are found. ``on_progress(expanded, discovered)`` is called
    every 10 000 expanded states and once at the end.
    """
    states = _initial_states(cm, initial)
    if len(states) > max_states:
        raise BudgetExceeded(f"{len(states)} initial states exceed max_states={max_states}")
    n_initial = len(states)
    index = {s: i for i, s in enumerate(states)}
    depth = [0] * len(states)
    moves: list[list[tuple[int, ...]]] = []
    succ: list[list[int]] = []
    avail: list[list[list[int]]] = []
    terminal: list[bool] = []
    ending: list[str | None] = []
    no_moves: list[tuple[int, ...]] = []
    no_avail: list[list[int]] = [[] for _ in cm.actors]
    cache: dict[tuple, tuple[list[list[int]], list[tuple[int, ...]]]] = {}
    successors = cm.successors
    i = 0
    while i < len(states):
        s = states[i]
        e = cm.ending_of(s)
        ending.append(e)
        terminal.append(e is not None)
        if e is not None:
            moves.append(no_moves)
            succ.append([])
            avail.append(no_avail)
        else:
            av = cm.available(s)
            key = tuple(map(tuple, av))
            hit = cache.get(key)
            if hit is None:
                hit = cache[key] = (av, list(itertools.product(*av)))
            av, mv = hit
            ids = []
            d = depth[i] + 1
            for t in successors(s, av, mv):
                j = index.get(t)
                if j is None:
                    j = len(states)
                    if j >= max_states:
                        raise BudgetExceeded(
                            f"exploration of {cm.name!r} passed max_states={max_states}"
                        )
                    index[t] = j
                    states.append(t)
                    depth.append(d)
                ids.append(j)
            moves.append(mv)
            succ.append(ids)
            avail.append(av)
        i += 1
        if on_progress is not None and i % PROGRESS_EVERY == 0:
            on_progress(i, len(states))
    if on_progress is not None:
        on_progress(i, len(states))
    return Graph(
        model=cm,
        states=states,
        index=index,
        initial=list(range(n_initial)),
        moves=moves,
        succ=succ,
        avail=avail,
        depth=depth,
        terminal=terminal,
        ending=ending,
    )
