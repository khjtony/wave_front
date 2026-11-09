#!/usr/bin/env python3
"""Print the Cold War v0 action tables of docs/actions_cw.md from the model.

``python scripts/cw_catalogue.py`` prints the tables; ``--check`` exits 1 if the document's
tables differ from the model (tests/coldwar/test_model_cw.py runs the same comparison).
``--v1`` does the same for the v1 tables (the coarse actions v1 adds or edits, and the two v1
sub-games; tests/coldwar_v1/test_model_cw_v1.py runs that comparison).
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
BEGIN_V1, END_V1 = "<!-- v1 tables:begin -->", "<!-- v1 tables:end -->"

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


def rows(m, keep=lambda actor, action: True) -> list[str]:
    out = ["| Actor | Action | Guard parts | Effect | Delay |", "|---|---|---|---|---|"]
    actors = list(m.actors) + [m.nature()]
    for a in actors:
        for x in a.actions:
            if not keep(a.name, x):
                continue
            guard = "; ".join(f"`{p}`: {expr(g)}" for p, g in x.guard_parts) or "none"
            eff = "; ".join(effect(e) for e in x.effects) or "none (crisis)"
            out.append(f"| {a.name} | `{x.name}` | {guard} | {eff} | {x.delay or ''} |")
    return out


def tables() -> str:
    parts = ["### The coarse game (`models/cw/v0.py`)", "", *rows(model)]
    for name, mod in SUBGAMES.items():
        parts += ["", f"### {name} (`models/cw/crises/{name}.py`)", "", *rows(mod.model)]
    return "\n".join(parts)


def tables_v1() -> str:
    """The coarse actions v1 adds or edits (guard parts, effects or delay differing from
    v0's action of the same actor and name), then the two sub-games v1 adds."""
    from models.cw import v1

    before = {
        (a.name, x.name): (repr(x.guard_parts), repr(x.effects), x.delay)
        for a in [*model.actors, model.nature()]
        for x in a.actions
    }

    def changed(actor: str, x) -> bool:
        return before.get((actor, x.name)) != (repr(x.guard_parts), repr(x.effects), x.delay)

    parts = ["### The coarse game, v1 additions and edits (`models/cw/v1.py`)", ""]
    parts += rows(v1.model, changed)
    for name in ("sino_soviet_1969", "alert_1973"):
        mod = v1.SUBGAMES[name]
        parts += ["", f"### {name} (`models/cw/crises/{name}.py`)", "", *rows(mod.model)]
    return "\n".join(parts)


def current(begin: str = BEGIN, end: str = END) -> str:
    text = DOC.read_text(encoding="utf-8")
    return text.split(begin, 1)[1].split(end, 1)[0].strip()


if __name__ == "__main__":
    v1_tables = "--v1" in sys.argv
    if "--check" in sys.argv:
        if v1_tables:
            sys.exit(0 if current(BEGIN_V1, END_V1) == tables_v1() else 1)
        sys.exit(0 if current() == tables() else 1)
    print(tables_v1() if v1_tables else tables())
