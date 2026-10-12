"""Readable text for guard and property expressions.

:func:`expr_text` walks an expression tree through the visitor protocol of
:mod:`wavefront.model.expr` and prints it the way a reader would write it::

    V.tension == "calm" and V.control < ite(V.aims == "hegemonic", 3, 1)
    not V.guarantee and V.belief != "hegemonic"
    V.belief in ["uncertain", "hegemonic"]

Level indices are printed as level names (quoted), counters as integers and flags as
``True``/``False``, resolved against the variable a literal is compared with, exactly as the
compiler resolves them. ``and``/``or``/``not`` replace the DSL's ``&``/``|``/``~``; ``min``,
``max`` and ``ite`` are calls; named invariants and endings print as ``invariant("name")``
and ``ending("name")``. Parentheses follow precedence, plus clarifying parentheses around an
``and`` inside an ``or`` and around anything but an atom under ``not``.

The formatter lives in :mod:`wavefront.viz`, not in the core: it is presentation only.
"""

from __future__ import annotations

from typing import Any

from ..model.compile import CompiledModel
from ..model.expr import (
    And,
    Arith,
    Cmp,
    Const,
    EndingRef,
    Expr,
    InSet,
    InvariantRef,
    Ite,
    Lit,
    Max,
    Min,
    Not,
    Or,
    VarRef,
)

__all__ = ["expr_text"]

# Precedence: higher binds tighter.
_OR, _AND, _NOT, _CMP, _ARITH, _ATOM = 1, 2, 3, 4, 5, 6
_NUMERIC_ORIGINS = ("tick", "pending", "fair")
_BOOL_NODES = (Const, Cmp, And, Or, Not, InSet, InvariantRef, EndingRef)


def _quote(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


class _Formatter:
    """Visitor returning ``(text, precedence)``; ``self.ctx`` is the variable index whose
    levels name the literals currently being printed (``None`` outside a comparison)."""

    def __init__(self, cm: CompiledModel | None) -> None:
        self.cm = cm
        self.ctx: int | None = None

    # -- driving -------------------------------------------------------------------------
    def fmt(self, node: Expr, ctx: int | None = None) -> tuple[str, int]:
        saved, self.ctx = self.ctx, ctx
        try:
            return node.accept(self)
        finally:
            self.ctx = saved

    def wrap(self, node: Expr, minimum: int, ctx: int | None = None) -> str:
        text, prec = self.fmt(node, ctx)
        return text if prec >= minimum else f"({text})"

    def var_index(self, name: str) -> int | None:
        if self.cm is None:
            return None
        return self.cm.index.get(name)

    def context_of(self, node: Expr) -> int | None:
        """The variable whose levels name literals compared with ``node`` (as the
        compiler's ``_CodeGen.ctx``)."""
        if isinstance(node, VarRef):
            return self.var_index(node.name)
        if isinstance(node, Arith | Min | Max | Ite):
            for child in node.children():
                if not isinstance(child, Lit) and not isinstance(child, _BOOL_NODES):
                    found = self.context_of(child)
                    if found is not None:
                        return found
        return None

    # -- atoms ---------------------------------------------------------------------------
    def visit_Const(self, node: Const) -> tuple[str, int]:
        return ("True" if node.value else "False"), _ATOM

    def visit_VarRef(self, node: VarRef) -> tuple[str, int]:
        name = node.name
        return (f"V.{name}" if name.isidentifier() else f"V[{_quote(name)}]"), _ATOM

    def literal(self, value: Any, ctx: int | None) -> str:
        spec = None if self.cm is None or ctx is None else self.cm.variables[ctx]
        if spec is None:
            if isinstance(value, str):
                return _quote(value)
            return repr(value)
        if spec.kind == "flag":
            if isinstance(value, bool | int) and value in (0, 1):
                return "True" if value else "False"
            return _quote(str(value))
        if spec.kind == "counter" or spec.origin in _NUMERIC_ORIGINS:
            return str(int(value)) if isinstance(value, bool | int) else str(value)
        if isinstance(value, bool | int) and not isinstance(value, bool):
            if 0 <= value < spec.size:
                return _quote(spec.levels[value])
            return str(value)
        if isinstance(value, bool):
            return _quote(spec.levels[int(value)]) if spec.size > int(value) else repr(value)
        return _quote(str(value))

    def visit_Lit(self, node: Lit) -> tuple[str, int]:
        return self.literal(node.value, self.ctx), _ATOM

    def visit_InvariantRef(self, node: InvariantRef) -> tuple[str, int]:
        return f"invariant({_quote(node.name)})", _ATOM

    def visit_EndingRef(self, node: EndingRef) -> tuple[str, int]:
        return f"ending({_quote(node.name)})", _ATOM

    # -- comparisons and sets --------------------------------------------------------------
    def visit_Cmp(self, node: Cmp) -> tuple[str, int]:
        ctx = self.context_of(node.left)
        if ctx is None:
            ctx = self.context_of(node.right)
        left = self.wrap(node.left, _ARITH, ctx)
        right = self.wrap(node.right, _ARITH, ctx)
        return f"{left} {node.op} {right}", _CMP

    def visit_InSet(self, node: InSet) -> tuple[str, int]:
        ctx = self.var_index(node.var.name)
        var = self.fmt(node.var)[0]
        items = ", ".join(self.literal(v, ctx) for v in node.values)
        return f"{var} in [{items}]", _CMP

    # -- connectives -----------------------------------------------------------------------
    @staticmethod
    def flatten(node: And | Or) -> list[Expr]:
        """The operands of a chain of the same connective (``(a & b) & c`` is one chain)."""
        out: list[Expr] = []
        for item in node.items:
            if type(item) is type(node):
                out.extend(_Formatter.flatten(item))  # type: ignore[arg-type]
            else:
                out.append(item)
        return out

    def visit_And(self, node: And) -> tuple[str, int]:
        return " and ".join(self.wrap(i, _AND + 1) for i in self.flatten(node)), _AND

    def visit_Or(self, node: Or) -> tuple[str, int]:
        # An ``and`` inside an ``or`` is parenthesized for the reader, not the parser.
        return " or ".join(self.wrap(i, _AND + 1) for i in self.flatten(node)), _OR

    def visit_Not(self, node: Not) -> tuple[str, int]:
        return f"not {self.wrap(node.item, _ATOM)}", _NOT

    # -- values ----------------------------------------------------------------------------
    def visit_Arith(self, node: Arith) -> tuple[str, int]:
        ctx = self.ctx if self.ctx is not None else self.context_of(node)
        left = self.wrap(node.left, _ARITH, ctx)
        right = self.wrap(node.right, _ATOM, ctx)
        return f"{left} {node.op} {right}", _ARITH

    def call(self, name: str, args: tuple[Expr, ...], node: Expr) -> tuple[str, int]:
        ctx = self.ctx if self.ctx is not None else self.context_of(node)
        return f"{name}({', '.join(self.fmt(a, ctx)[0] for a in args)})", _ATOM

    def visit_Min(self, node: Min) -> tuple[str, int]:
        return self.call("min", node.args, node)

    def visit_Max(self, node: Max) -> tuple[str, int]:
        return self.call("max", node.args, node)

    def visit_Ite(self, node: Ite) -> tuple[str, int]:
        ctx = self.ctx if self.ctx is not None else self.context_of(node)
        cond = self.fmt(node.cond)[0]
        then = self.fmt(node.then, ctx)[0]
        orelse = self.fmt(node.orelse, ctx)[0]
        return f"ite({cond}, {then}, {orelse})", _ATOM


def expr_text(expr: Expr, cm: CompiledModel | None = None) -> str:
    """``expr`` as readable text, with literals printed against ``cm``'s variables (level
    names for levels, integers for counters, ``True``/``False`` for flags). Without a
    compiled model literals are printed as written."""
    return _Formatter(cm).fmt(expr)[0]
