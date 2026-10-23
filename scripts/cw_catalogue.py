#!/usr/bin/env python3
"""Print the Cold War v0 action tables of docs/actions_cw.md from the model.

``python scripts/cw_catalogue.py`` prints the tables; ``--check`` exits 1 if the document's
tables differ from the model (tests/coldwar/test_model_cw.py runs the same comparison).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.cw.crises import SUBGAMES  # noqa: E402
from models.cw.v0 import model  # noqa: E402
from wavefront.model.effects import Bump, Set, SetIf  # noqa: E402

DOC = ROOT / "docs" / "actions_cw.md"
BEGIN, END = "<!-- tables:begin -->", "<!-- tables:end -->"

OPS = {"==": "=", "!=": "≠", "<=": "≤", ">=": "≥", "<": "<", ">": ">"}


def expr(e) -> str:
    name = type(e).__name__
    if name == "Cmp":
        return f"{expr(e.left)} {OPS[e.op]} {expr(e.right)}"
    if name == "VarRef":
        return e.name
    if name == "Lit":
        return str(e.value)
    if name in ("And", "Or"):
        sep = " ∧ " if name == "And" else " ∨ "
        return "(" + sep.join(expr(x) for x in e.items) + ")"
    if name == "Not":
        return "¬" + expr(e.item)
    if name == "Const":
        return "TRUE" if e.value else "FALSE"
    if name == "InSet":
        return f"{expr(e.var)} ∈ {{{', '.join(map(str, e.values))}}}"
    return str(e)


def effect(x) -> str:
    if isinstance(x, SetIf):
        return f"{x.var} := {x.value} if {expr(x.cond)}"
    if isinstance(x, Set):
        v = expr(x.value) if hasattr(x.value, "free_vars") else x.value
        return f"{x.var} := {v}"
    if isinstance(x, Bump):
        return f"{x.var} {x.amount:+d}"
    return str(x)


def rows(m) -> list[str]:
    out = ["| Actor | Action | Guard parts | Effect | Delay |", "|---|---|---|---|---|"]
    actors = list(m.actors) + [m.nature()]
    for a in actors:
        for x in a.actions:
            guard = "; ".join(f"`{p}`: {expr(g)}" for p, g in x.guard_parts) or "none"
            eff = "; ".join(effect(e) for e in x.effects) or "none (crisis)"
            out.append(f"| {a.name} | `{x.name}` | {guard} | {eff} | {x.delay or ''} |")
    return out


def tables() -> str:
    parts = ["### The coarse game (`models/cw/v0.py`)", "", *rows(model)]
    for name, mod in SUBGAMES.items():
        parts += ["", f"### {name} (`models/cw/crises/{name}.py`)", "", *rows(mod.model)]
    return "\n".join(parts)


def current() -> str:
    text = DOC.read_text(encoding="utf-8")
    return text.split(BEGIN, 1)[1].split(END, 1)[0].strip()


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(0 if current() == tables() else 1)
    print(tables())
