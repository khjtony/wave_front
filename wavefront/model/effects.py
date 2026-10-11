"""Effect objects attached to actions.

Effects are evaluated against the pre-state of a transition and composed per variable as
in spec section 3.4: a ``Set`` value is taken if any ``Set`` targets the variable (two
``Set`` effects with different values in one joint move are an error), then all ``Bump``
amounts are added, then the result is clamped to the variable's range (or ``strict`` raises).

- :class:`Set` assigns a level name, a counter value, a flag value or an integer
  expression (an expression result is clamped to the variable's range).
- :class:`Bump` adds ``amount`` to the level index or counter value.
- :func:`Inc` and :func:`Reset` are sugar for counters.
- :class:`SetIf` is a ``Set`` that applies only if ``cond`` holds in the pre-state.
"""

from __future__ import annotations

from dataclasses import dataclass

from .expr import Expr, lift_bool

__all__ = ["Effect", "Set", "Bump", "Inc", "Reset", "SetIf"]


@dataclass(frozen=True, eq=False)
class Set:
    """Assign ``value`` (a level name, int, bool, or integer expression) to ``var``."""

    var: str
    value: str | int | bool | Expr


@dataclass(frozen=True)
class Bump:
    """Add ``amount`` to the index of ``var``; clamp to its range unless ``strict``."""

    var: str
    amount: int
    strict: bool = False

    def __post_init__(self) -> None:
        if isinstance(self.amount, bool) or not isinstance(self.amount, int):
            raise TypeError(f"Bump amount must be an int, got {self.amount!r}")


@dataclass(frozen=True, eq=False)
class SetIf:
    """Assign ``value`` to ``var`` if ``cond`` holds in the pre-state."""

    cond: Expr
    var: str
    value: str | int | bool | Expr

    def __post_init__(self) -> None:
        object.__setattr__(self, "cond", lift_bool(self.cond))


Effect = Set | Bump | SetIf


def Inc(counter: str, amount: int = 1) -> Bump:
    """Increment a counter: ``Bump(counter, amount)``."""
    return Bump(counter, amount)


def Reset(counter: str) -> Set:
    """Reset a counter to zero: ``Set(counter, 0)``."""
    return Set(counter, 0)
