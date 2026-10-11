"""The explored game graph (spec section 5.1)."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

from ..model.compile import CompiledModel
from ..model.expr import Expr
from ..model.model import ModelError

__all__ = ["Graph"]


@dataclass
class Graph:
    """Reachable states of a compiled model and their joint moves.

    State ids are assigned in breadth-first order. ``moves[i]`` and ``succ[i]`` are
    aligned: ``succ[i][k]`` is the id reached from state ``i`` under ``moves[i][k]``.
    Terminal states have no moves. Lists in ``moves`` and ``avail`` may be shared between
    states with the same available actions; treat them as read-only.
    """

    model: CompiledModel
    states: list[tuple[int, ...]]
    index: dict[tuple[int, ...], int]
    initial: list[int]
    moves: list[list[tuple[int, ...]]]
    succ: list[list[int]]
    avail: list[list[list[int]]]
    depth: list[int]
    terminal: list[bool]
    ending: list[str | None]

    def size(self) -> int:
        """Number of states."""
        return len(self.states)

    def states_where(self, pred: Expr | str | Callable[[tuple[int, ...]], object]) -> set[int]:
        """Ids of states satisfying an expression, a named invariant or ending, or a Python
        predicate on the state tuple."""
        if isinstance(pred, Expr):
            fn = self.model.compile_expr(pred)
        elif isinstance(pred, str):
            cm = self.model
            fns = {**cm.invariant_fns, **cm.ending_fns}
            if pred not in fns:
                raise ModelError(f"no invariant or ending named {pred!r}")
            fn = fns[pred]
        elif callable(pred):
            fn = pred
        else:
            raise TypeError(f"cannot use {pred!r} as a state predicate")
        return {i for i, s in enumerate(self.states) if fn(s)}

    def ending_states(self, name: str) -> set[int]:
        """Ids of terminal states whose ending is ``name`` (``"HORIZON"`` included)."""
        return {i for i, e in enumerate(self.ending) if e == name}

    def actor_indices(self, names: Iterable[str]) -> list[int]:
        """Sorted actor indices of a coalition given by actor names."""
        known = {a.name: a.index for a in self.model.actors}
        out = set()
        for name in names:
            if name not in known:
                raise ModelError(f"unknown actor {name!r} (actors: {', '.join(known)})")
            out.add(known[name])
        return sorted(out)

    def state_dict(self, state_id: int) -> dict[str, str]:
        """``{variable: level name}`` for a state id."""
        return self.model.state_dict(self.states[state_id])

    def format_state(self, state_id: int) -> str:
        """A state id rendered with level names."""
        return self.model.format_state(self.states[state_id])

    def move_names(self, joint_move: Sequence[int]) -> list[str]:
        """Action names of a joint move, in actor order."""
        return [a.actions[j].name for a, j in zip(self.model.actors, joint_move, strict=True)]
