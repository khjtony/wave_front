"""C13: The year the USSR leaves its own kernel falls between 1979 and 1989.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.

Reading (docs/cw_v0_decisions.md, R C13): for each year 1975 to 1989, the hindsight state
per hypothesis and K = safe({USSR}, bloc_intact) (symbolic). The departure year is the last
year inside followed by a year outside. (a) it falls between 1979 and 1989; (b) the driving
variable is reported: the variables whose one-level perturbation puts the first state outside
back inside, with the realized move of the departure year; (c) stability under refinement is
not tested at v0. Holds iff (a) and (b) under at least one hypothesis. Hold-out (decisions
D9). Engine: symbolic.
"""

from models.cw.v0 import REALIZED_MOVES
from models.ww2.hypotheses import realized_rows

from ..common import HYPS, Timer, compiled, hindsight, kernel

CLAIM = {
    "id": "C13",
    "from_state": "each year 1975 to 1989",
    "claim": (
        "the year the USSR leaves its own kernel (can no longer guarantee its bloc) "
        "falls between 1979 and 1989, the report names the driving variable, and the "
        "result is stable within one year under refinement"
    ),
    "expected": "inside the window; `refine at phase 3` for the driving variable",
    "sources": "Kotkin 2001; Brown 2009; Miller 2016",
}

YEARS = range(1975, 1991)


def test_C13():
    timer = Timer()
    print("\n[C13] engine: symbolic kernel of bloc_intact for USSR alone, hindsight states")
    rows = realized_rows(REALIZED_MOVES)
    results = {}
    for aims in HYPS:
        cm = compiled(aims)
        k = kernel(aims, ("USSR",), "bloc_intact")
        member = {y: k.contains(hindsight(y, aims)) for y in YEARS}
        print(f"[C13] aims_USSR={aims}: {member}")
        dep = next((y for y in YEARS[:-1] if member[y] and not member[y + 1]), None)
        before = all(not member[y] for y in YEARS if y <= 1979) and dep is None
        a = dep is not None and 1979 <= dep <= 1989
        drivers = []
        if dep is not None:
            s = hindsight(dep + 1, aims)
            for v in cm.variables:
                if v.origin != "var" or v.name == "aims_USSR":
                    continue
                i = cm.index[v.name]
                for d in (-1, 1):
                    j = s[i] + d
                    if 0 <= j < v.size and k.contains(s[:i] + (j,) + s[i + 1 :]):
                        drivers.append(f"{v.name} -> {v.levels[j]}")
            row = rows[dep - 1947]
            moves = {
                a: row[a]
                for a in ("USA", "USSR", "PRC", "Nature")
                if row[a] not in ("idle", "none")
            }
            print(
                f"[C13]   departure {dep}: realized moves {moves}; "
                f"restoring perturbations {drivers}"
            )
        elif before:
            print("[C13]   outside the kernel through the window from 1975")
        b = dep is not None and bool(drivers)
        print("[C13]   (c) stability under refinement: not tested at v0")
        results[aims] = (a, b)
        print(f"[C13] aims_USSR={aims}: (a) {a}, (b) {b} ({timer})")
    assert any(all(v) for v in results.values()), results
