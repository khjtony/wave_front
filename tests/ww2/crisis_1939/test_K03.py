"""K3: registered 2026-10-15 in docs/crisis_1939_testbed.md section 3.

The summer-1939 crisis sub-game of WW2 v1 (3-day ticks, 5 July to 3 September 1939), entered
from the 1939Q3 state. Do not edit the claim text without a changelog entry in that
document.

Reading (docs/crisis_1939_decisions.md R3). Reduced build, Nature free, profile
``documented_only``. The kernel for "no pact and the alliance still possible" is
``viability(g, {WEST, USSR, Nature}, "alliance_race")`` ({WEST, USSR} with Nature granting
Polish passage, the fortune sense of ww2_testbed.md section 4.6, because the realized path
exists only in the free model). The departure tick d is the last realized tick inside the
kernel followed by a realized state outside it; t_K = d + 1 (``point_of_no_return``). The
claim holds for the tick when the realized states 0 to d are inside and 13 <= d <= 15. The
driving variables are those of the top-ranked rows of ``sensitivity`` from the realized
state at d (coalition {WEST, USSR, Nature}, adversary {GER}); the claim holds for the
variable when every top-ranked variable is ``passage`` or ``talks``. Diagnostics: the
standard kernel of {WEST, USSR} (Nature adversarial), documented and with the speculative
action.

Engine: the explicit engine (``viability``, ``point_of_no_return``, ``sensitivity``).
"""

import functools
import time

from models.ww2.crises import summer_1939 as crisis
from tests.ww2.crisis_1939 import common
from wavefront.analysis import point_of_no_return, sensitivity, viability

CLAIM = {
    "id": "K3",
    "from_state": "ticks 0 to 15",
    "claim": (
        'the tick at which {WEST, USSR} leave the kernel for "no pact and the alliance still '
        "possible\" falls between 14 August (Voroshilov's question, tick 13) and 21 August "
        "(the Soviet break-off, tick 15), and the driving variable is Polish passage or the "
        "pace of the talks"
    ),
    "expected": "point of no return inside ticks 13 to 15, with the driving variable named",
    "sources": (
        "the military missions' record; the Schulenburg-Molotov exchanges of 15 to 19 August"
    ),
}

FORTUNE = {"WEST", "USSR", "Nature"}


@functools.lru_cache(maxsize=None)
def departure(coalition: frozenset, documented: bool = True) -> dict:
    t0 = time.time()
    cm = common.compiled(inert=False, profile="documented_only" if documented else None)
    path = common.realized_states(cm)
    g = common.graph(cm, [common.entry(cm)])
    kernel = viability(g, coalition, "alliance_race").kernel
    ids = [common.sid(g, s) for s in path]
    inside = [i in kernel for i in ids]
    t_k = point_of_no_return(ids, kernel)
    d = None if t_k is None or t_k == 0 else t_k - 1
    return {
        "inside": inside,
        "t_K": t_k,
        "d": d,
        "path": path,
        "cm": cm,
        "seconds": round(time.time() - t0, 2),
        "states": g.size(),
    }


@functools.lru_cache(maxsize=None)
def driving() -> tuple:
    r = departure(frozenset(FORTUNE))
    t0 = time.time()
    rows = sensitivity(
        crisis.build(inert=False),
        "alliance_race",
        FORTUNE,
        adversary={"GER"},
        profile="documented_only",
        initial=[r["path"][r["d"]]],
    )
    top = max(row.effect for row in rows)
    return rows, sorted({row.variable for row in rows if row.effect == top}), time.time() - t0


def test_K3_departure_tick(capsys):
    r = departure(frozenset(FORTUNE))
    diag = {
        "{WEST, USSR} documented": departure(frozenset({"WEST", "USSR"}), True),
        "{WEST, USSR} with speculative": departure(frozenset({"WEST", "USSR"}), False),
    }
    with capsys.disabled():
        print(
            f"\nK3 fortune kernel {{WEST, USSR, Nature}} (explicit engine, {r['states']} "
            f"states, {r['seconds']} s): inside along the realized path "
            f"{''.join('1' if x else '0' for x in r['inside'])}; t_K = {r['t_K']}, "
            f"departure tick d = {r['d']}"
        )
        for name, x in diag.items():
            print(
                f"K3 diagnostic, standard kernel {name}: inside "
                f"{''.join('1' if y else '0' for y in x['inside'])}; t_K = {x['t_K']}"
            )
    assert r["d"] is not None
    assert all(r["inside"][: r["d"] + 1])
    assert 13 <= r["d"] <= 15


def test_K3_driving_variable(capsys):
    rows, top, seconds = driving()
    with capsys.disabled():
        print(f"\nK3 sensitivity from the realized state at d (explicit engine, {seconds:.1f} s):")
        print(
            "| variable | from | to | in kernel before | after | flips | shortest before | after |"
        )
        print("|---|---|---|---|---|---|---|---|")
        for row in rows:
            print(
                f"| {row.variable} | {row.from_level} | {row.to_level} | {row.base_in_kernel} | "
                f"{row.new_in_kernel} | {row.flips} | {row.base_shortest} | {row.new_shortest} |"
            )
        print(f"K3 top-ranked (driving) variables: {top}")
    assert top and set(top) <= {"passage", "talks"}
