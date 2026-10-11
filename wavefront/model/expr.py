"""Declarative expression trees for guards, effects and properties.

Expressions are immutable dataclass trees built with ordinary Python operators::

    (V.belief <= "uncertain") & (V.cap < "high")
    V.stock + 1 >= V.need
    Ite(V.flag == True, 1, 0)

``V.name`` is a :class:`VarRef`; comparisons with ``== != < <= > >=`` return :class:`Cmp`
nodes; ``&``, ``|``, ``~`` and :meth:`Expr.implies` build boolean nodes; ``+`` and ``-``
build :class:`Arith` nodes; :class:`Min`, :class:`Max` and :class:`Ite` are constructed
directly. Plain Python values (level names, ints, bools) are wrapped as :class:`Lit` and
resolved against a variable's levels when the model is compiled
(:mod:`wavefront.model.compile`), so nothing here knows about a particular model.

Because ``==`` builds a node, expressions must never be used where Python needs a truth
value (``if expr``, ``and``, ``or``, ``in``); :meth:`Expr.__bool__` raises ``TypeError``.
Expression nodes hash by identity.

Node types: :class:`Const`, :class:`Lit`, :class:`VarRef`, :class:`Cmp`, :class:`And`,
:class:`Or`, :class:`Not`, :class:`InSet`, :class:`Arith`, :class:`Min`, :class:`Max`,
:class:`Ite`, :class:`InvariantRef`, :class:`EndingRef`.

Visitor protocol: ``node.accept(visitor)`` calls ``visitor.visit_<ClassName>(node)``, for
example ``visit_Cmp``. ``node.children()`` returns the direct sub-expressions and
:func:`walk` yields a tree in pre-order. This lets translators (the Python code generator
in :mod:`wavefront.model.compile`, a Z3 encoder in ``wavefront.bmc``) walk trees without
the core importing any solver.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, fields
from typing import Any

__all__ = [
    "Expr",
    "Const",
    "Lit",
    "VarRef",
    "Cmp",
    "And",
    "Or",
    "Not",
    "InSet",
    "Arith",
    "Min",
    "Max",
    "Ite",
    "InvariantRef",
    "EndingRef",
    "Observes",
    "V",
    "TRUE",
    "FALSE",
    "walk",
    "lift_bool",
    "lift_value",
]

CMP_OPS = ("==", "!=", "<", "<=", ">", ">=")
ARITH_OPS = ("+", "-")

LiteralValue = str | int | bool


class Expr:
    """Base class of every expression node."""

    __slots__ = ()
    __hash__ = object.__hash__

    # -- comparisons -------------------------------------------------------------------
    def __eq__(self, other: object) -> Cmp:  # type: ignore[override]
        return Cmp("==", self, lift_value(other))

    def __ne__(self, other: object) -> Cmp:  # type: ignore[override]
        return Cmp("!=", self, lift_value(other))

    def __lt__(self, other: object) -> Cmp:
        return Cmp("<", self, lift_value(other))

    def __le__(self, other: object) -> Cmp:
        return Cmp("<=", self, lift_value(other))

    def __gt__(self, other: object) -> Cmp:
        return Cmp(">", self, lift_value(other))

    def __ge__(self, other: object) -> Cmp:
        return Cmp(">=", self, lift_value(other))

    # -- boolean connectives -----------------------------------------------------------
    def __and__(self, other: object) -> And:
        return And((self, lift_bool(other)))

    def __rand__(self, other: object) -> And:
        return And((lift_bool(other), self))

    def __or__(self, other: object) -> Or:
        return Or((self, lift_bool(other)))

    def __ror__(self, other: object) -> Or:
        return Or((lift_bool(other), self))

    def __invert__(self) -> Not:
        return Not(self)

    def implies(self, other: object) -> Or:
        """``self -> other``, built as ``~self | other``."""
        return Or((Not(self), lift_bool(other)))

    # -- arithmetic --------------------------------------------------------------------
    def __add__(self, other: object) -> Arith:
        return Arith("+", self, lift_value(other))

    def __radd__(self, other: object) -> Arith:
        return Arith("+", lift_value(other), self)

    def __sub__(self, other: object) -> Arith:
        return Arith("-", self, lift_value(other))

    def __rsub__(self, other: object) -> Arith:
        return Arith("-", lift_value(other), self)

    # -- protocol ----------------------------------------------------------------------
    def __bool__(self) -> bool:
        raise TypeError(
            "an expression has no truth value; use & | ~ instead of and/or/not, "
            "and compile the model to evaluate it"
        )

    def children(self) -> tuple[Expr, ...]:
        """Direct sub-expressions, in field order."""
        out: list[Expr] = []
        for f in fields(self):  # type: ignore[arg-type]
            value = getattr(self, f.name)
            if isinstance(value, Expr):
                out.append(value)
            elif isinstance(value, tuple):
                out.extend(v for v in value if isinstance(v, Expr))
        return tuple(out)

    def accept(self, visitor: Any) -> Any:
        """Dispatch to ``visitor.visit_<ClassName>(self)``."""
        return getattr(visitor, "visit_" + type(self).__name__)(self)

    def free_vars(self) -> frozenset[str]:
        """Names of variables referenced directly (named invariants and endings are not
        expanded; the compiler expands them)."""
        return frozenset(n.name for n in walk(self) if isinstance(n, VarRef))


def walk(expr: Expr) -> Iterator[Expr]:
    """Yield ``expr`` and all its sub-expressions in pre-order."""
    stack = [expr]
    while stack:
        node = stack.pop()
        yield node
        stack.extend(reversed(node.children()))


def lift_bool(value: object) -> Expr:
    """Wrap a Python bool as :data:`TRUE`/:data:`FALSE`; pass expressions through."""
    if isinstance(value, Expr):
        return value
    if isinstance(value, bool):
        return TRUE if value else FALSE
    raise TypeError(f"expected a boolean expression, got {value!r}")


def lift_value(value: object) -> Expr:
    """Wrap a level name, int or bool as :class:`Lit`; pass expressions through."""
    if isinstance(value, Expr):
        return value
    if isinstance(value, str | int | bool):
        return Lit(value)
    raise TypeError(f"expected an expression, level name, int or bool, got {value!r}")


@dataclass(frozen=True, eq=False)
class Const(Expr):
    """Boolean constant; use :data:`TRUE` and :data:`FALSE`."""

    value: bool


@dataclass(frozen=True, eq=False)
class Lit(Expr):
    """A literal operand: a level name, an int (a level index or counter value) or a bool
    (index 1 or 0). Level names are resolved at compile time against the variable it is
    compared with or assigned to."""

    value: LiteralValue


@dataclass(frozen=True, eq=False)
class VarRef(Expr):
    """Reference to a variable (declared or built-in, such as ``tick``)."""

    name: str

    def is_in(self, values: Iterable[LiteralValue]) -> InSet:
        """True when the variable has one of the given levels."""
        return InSet(self, tuple(values))


@dataclass(frozen=True, eq=False)
class Cmp(Expr):
    """Comparison ``left op right`` on level indices or integer values."""

    op: str
    left: Expr
    right: Expr

    def __post_init__(self) -> None:
        if self.op not in CMP_OPS:
            raise ValueError(f"unknown comparison operator {self.op!r}")


@dataclass(frozen=True, eq=False)
class And(Expr):
    """Conjunction of two or more boolean expressions."""

    items: tuple[Expr, ...]


@dataclass(frozen=True, eq=False)
class Or(Expr):
    """Disjunction of two or more boolean expressions."""

    items: tuple[Expr, ...]


@dataclass(frozen=True, eq=False)
class Not(Expr):
    """Negation."""

    item: Expr


@dataclass(frozen=True, eq=False)
class InSet(Expr):
    """``var.is_in(values)``: the variable has one of the listed levels."""

    var: VarRef
    values: tuple[LiteralValue, ...]


@dataclass(frozen=True, eq=False)
class Arith(Expr):
    """``left + right`` or ``left - right`` on integer values (not clamped)."""

    op: str
    left: Expr
    right: Expr

    def __post_init__(self) -> None:
        if self.op not in ARITH_OPS:
            raise ValueError(f"unknown arithmetic operator {self.op!r}")


@dataclass(frozen=True, eq=False, init=False)
class Min(Expr):
    """Minimum of two or more integer expressions: ``Min(V.a, V.b + 1, 3)``."""

    args: tuple[Expr, ...]

    def __init__(self, *args: object) -> None:
        if len(args) < 2:
            raise ValueError("Min needs at least two arguments")
        object.__setattr__(self, "args", tuple(lift_value(a) for a in args))


@dataclass(frozen=True, eq=False, init=False)
class Max(Expr):
    """Maximum of two or more integer expressions."""

    args: tuple[Expr, ...]

    def __init__(self, *args: object) -> None:
        if len(args) < 2:
            raise ValueError("Max needs at least two arguments")
        object.__setattr__(self, "args", tuple(lift_value(a) for a in args))


@dataclass(frozen=True, eq=False, init=False)
class Ite(Expr):
    """``Ite(cond, a, b)``: ``a`` if ``cond`` holds, else ``b``."""

    cond: Expr
    then: Expr
    orelse: Expr

    def __init__(self, cond: object, then: object, orelse: object) -> None:
        object.__setattr__(self, "cond", lift_bool(cond))
        object.__setattr__(self, "then", lift_value(then))
        object.__setattr__(self, "orelse", lift_value(orelse))


@dataclass(frozen=True, eq=False)
class InvariantRef(Expr):
    """Reference to a named invariant, expanded at compile time."""

    name: str


@dataclass(frozen=True, eq=False)
class EndingRef(Expr):
    """Reference to a named ending, expanded at compile time."""

    name: str


TRUE = Const(True)
FALSE = Const(False)


@dataclass(frozen=True)
class Observes:
    """An observation set: ``V.all()``, ``V.all_except(...)`` or ``V.only(...)``.

    ``kind`` is ``"all"``, ``"except"`` or ``"only"``; ``names`` are variable names.
    """

    kind: str
    names: tuple[str, ...] = ()


class _Namespace:
    """The ``V`` namespace. ``V.name`` and ``V["name"]`` are variable references."""

    RESERVED = frozenset({"all", "all_except", "only", "invariant", "ending", "ref"})

    def __getattr__(self, name: str) -> VarRef:
        if name.startswith("__"):
            raise AttributeError(name)
        return VarRef(name)

    def __getitem__(self, name: str) -> VarRef:
        return VarRef(name)

    def ref(self, name: str) -> VarRef:
        """Reference a variable by name."""
        return VarRef(name)

    def invariant(self, name: str) -> InvariantRef:
        """Reference the named invariant."""
        return InvariantRef(name)

    def ending(self, name: str) -> EndingRef:
        """Reference the named ending."""
        return EndingRef(name)

    def all(self) -> Observes:
        """Observe every variable."""
        return Observes("all")

    def all_except(self, *names: str) -> Observes:
        """Observe every variable except ``names``."""
        return Observes("except", tuple(names))

    def only(self, *names: str) -> Observes:
        """Observe only ``names`` (plus the actor's own built-ins and ``tick``)."""
        return Observes("only", tuple(names))


V = _Namespace()
