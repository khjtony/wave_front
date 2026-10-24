"""Diagnostic for the Cold War v0 review (docs/review_phase3_2026-10-18.md), not a
registered claim: for each clause of ``balance_cw`` and each of the joint and unilateral
coalitions, the years 1965 to 1991 whose hindsight state is inside the kernel.

Needs the Cold War v0 branch (``models/cw``, ``tests/coldwar``). Run from the repository
root:  python scripts/cw_balance_clauses.py opportunist
"""

import sys

sys.path.insert(0, ".")
from tests.coldwar.common import encoding, hindsight  # noqa: E402
from wavefront.model import V  # noqa: E402
from wavefront.symbolic import safe  # noqa: E402

aims = sys.argv[1]
enc = encoding(aims)
BOTH = ((V.nuke_USA >= "survivable") & (V.nuke_USSR >= "survivable")) | (
    (V.nuke_USA < "survivable") & (V.nuke_USSR < "survivable")
)


def phi(name):
    if name == "no_war & both_or_neither":
        return enc.predicate(V.invariant("no_war") & BOTH)
    if name == "no_general_war & both_or_neither":
        return enc.predicate(V.invariant("no_general_war") & BOTH)
    return enc.predicate(name)


states = {y: hindsight(y, aims) for y in range(1965, 1992)}
for name in (
    "balance_cw",
    "bloc_intact",
    "no_war",
    "no_general_war",
    "no_war & both_or_neither",
    "no_general_war & both_or_neither",
):
    row = []
    for coal in (("USA", "USSR"), ("USA",), ("USSR",)):
        k = safe(enc, list(coal), phi(name))
        ys = [y for y, s in states.items() if k.contains(s)]
        row.append(f"{'+'.join(coal)}: {len(ys)}/27" + (f" ({ys[0]}-{ys[-1]})" if ys else ""))
    print(f"{aims:11s} {name:34s} " + " | ".join(row), flush=True)
