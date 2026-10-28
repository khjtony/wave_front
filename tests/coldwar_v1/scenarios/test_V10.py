"""V10: The USSR's departure from its bloc kernel on cw_v1 (regression of C13).

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V10a. The readings the model step must fix before first sight are listed in
section 9.4.

Reading (docs/cw_v1_decisions.md, R V10): as v0's R C13 on cw_v1. For each year 1975 to 1990
(1990 so that a departure in 1989 can be seen), per hypothesis, the hindsight state and
``K_USSR^bloc = safe({USSR}, bloc_intact)`` through the horizon by the composite engine
(explicit to 1984 with the symbolic kernel beyond; from 1984 the symbolic kernel alone). The
departure year is the first year inside followed by a year outside (v0's reading of "the last
year inside followed by a year outside"). (a) It falls in 1979 to 1989; (b) the driving
variables: those whose one-level perturbation of the first state outside (the departure
year's successor) puts it back inside, printed with the realized moves of the departure year;
(b) holds iff there is one; (c) the departure year is within one year of v0's recorded
departure (1980; reports/cw_v0.md section 14). Control: on the PRC-to-Nature build the
departure year is the same. Holds iff (a), (b), (c) and the control under at least one
hypothesis. Beside, not asserted (the fortune variant): the departure year of
``safe({USSR, Nature}, bloc_intact)``, on the same explicit parts.
"""

import os

import pytest

from models.cw import v1
from models.ww2.hypotheses import realized_rows

from ..common import (
    HYPS,
    Timer,
    compiled,
    composite_graph,
    composite_kernel,
    hindsight,
    kernel,
)

CLAIM = {
    "id": "V10",
    "from_state": "each year 1975 to 1989",
    "claim": (
        "on cw_v1, C13 as registered: the year the USSR leaves its own kernel (can no longer "
        "guarantee its bloc) falls between 1979 and 1989, the report names the driving "
        "variable, and the result is stable within one year under refinement; control: on "
        "the build with the PRC's decisions given to Nature the departure year is the same"
    ),
    "expected": "inside the window; the driving variable named; the control as stated",
    "sources": "Kotkin 2001; Brown 2009; Miller 2016; regression of C13",
}

# The first-sight switch (docs/cw_v1_decisions.md D8): the claim runs only when the owner sets
# WF_FIRST_SIGHT_CWV1=1 for the one recorded run of V1 to V10.
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_CWV1") == "1"

YEARS = range(1975, 1991)
INV = "bloc_intact"
USSR = ("USSR",)
FORTUNE = ("USSR", "Nature")  # beside, not asserted (section 9.2, the fortune variant)
V0_DEPARTURE = 1980  # reports/cw_v0.md section 14


def inside(aims, year, states, coalitions=(USSR,), **build):
    """Membership of ``states`` (of hindsight year ``year``) in each coalition's kernel of
    ``bloc_intact`` by the composite engine (symbolic alone from 1984), one explicit part for
    all coalitions; a list per state when several coalitions are asked, else a bool."""
    if year >= 1984:
        ks = [kernel(aims, c, INV, **build) for c in coalitions]
        out = [[k.contains(s) for k in ks] for s in states]
    else:
        g = composite_graph(aims, states, **build)
        ks = [composite_kernel(g, aims, c, INV, **build) for c in coalitions]
        out = [[g.index[s] in k for k in ks] for s in states]
    return [m[0] for m in out] if len(coalitions) == 1 else out


def first_departure(member):
    return next((y for y in YEARS[:-1] if member[y] and not member[y + 1]), None)


def departure(aims, fortune=False, **build):
    """The departure year of K_USSR^bloc; with ``fortune`` also that of safe({USSR, Nature},
    bloc_intact), computed on the same explicit parts (beside, not asserted)."""
    coalitions = (USSR, FORTUNE) if fortune else (USSR,)
    member, luck = {}, {}
    for y in YEARS:
        m = inside(aims, y, [hindsight(y, aims, **build)], coalitions, **build)[0]
        member[y], luck[y] = (m[0], m[1]) if fortune else (m, None)
    if fortune:
        return member, first_departure(member), luck, first_departure(luck)
    return member, first_departure(member)


def drivers(aims, dep):
    cm = compiled(aims)
    s = hindsight(dep + 1, aims)
    perts = []
    for v in cm.variables:
        if v.origin != "var" or v.name == "aims_USSR":
            continue
        i = cm.index[v.name]
        for d in (-1, 1):
            j = s[i] + d
            if 0 <= j < v.size:
                perts.append((f"{v.name} -> {v.levels[j]}", s[:i] + (j,) + s[i + 1 :]))
    back = inside(aims, dep + 1, [t for _, t in perts])
    return [name for (name, _), ok in zip(perts, back, strict=True) if ok]


@pytest.mark.skipif(not FIRST_SIGHT, reason="cw_v1 first sight not switched on")
def test_V10():
    timer = Timer()
    print("\n[V10] engine: composite (explicit to 1984, symbolic beyond) for K_USSR of bloc_intact")
    rows = realized_rows(v1.REALIZED_MOVES)
    results = {}
    for aims in HYPS:
        member, dep, luck, dep_luck = departure(aims, fortune=True)
        print(f"[V10] aims_USSR={aims}: {member}")
        print(f"[V10]   beside (fortune), safe({{USSR, Nature}}): {luck}; departure {dep_luck}")
        a = dep is not None and 1979 <= dep <= 1989
        found = []
        if dep is not None:
            found = drivers(aims, dep)
            row = rows[dep - v1.YEAR0]
            moves = {
                x: row[x]
                for x in ("USA", "USSR", "PRC", "Nature")
                if row[x] not in ("idle", "none")
            }
            print(
                f"[V10]   departure {dep}: realized moves {moves}; restoring perturbations {found}"
            )
        b = bool(found)
        c = dep is not None and abs(dep - V0_DEPARTURE) <= 1
        _, dep_ctrl = departure(aims, prc_principal=False)
        control = dep_ctrl == dep and dep is not None
        print(
            f"[V10]   (c) within one year of v0's {V0_DEPARTURE}: {c}; control (PRC-to-Nature "
            f"build) departure {dep_ctrl}: {control}"
        )
        results[aims] = (a, b, c, control)
        print(f"[V10] aims_USSR={aims}: (a) {a}, (b) {b}, (c) {c}, control {control} ({timer})")
    assert any(all(v) for v in results.values()), results
