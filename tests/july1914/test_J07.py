"""J7: registered 2026-10-15 in docs/july1914_testbed.md section 3.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature. Do not edit the claim text without a changelog entry in that
document.

Reading (docs/july1914_decisions.md, R J7): the build with every cadence 1
(``build(cadence=False)``). (a) J2's departure (X = {AUH, GER, FRA, GBR},
``no_war_GER_RUS``, the realized path from tick 32, ``fight`` pairs) is at least two days
earlier than in the model of record; (b) J3's forcing family of ``LOCALIZED`` from tick 0
under ``(localize, deter)`` contains {GER}. Reported besides: the departures along the
realized path from tick 0 in both builds and the daily build's full J3 table. A content
check, reported and not tuned. Engine: explicit.
"""

import pytest

from .common import FIGHT, PAIRS, Timer, X, fmt, kept_as, label
from .test_J02 import departure_from_tick0, j2_departures
from .test_J03 import LOCALIZE_DETER, j3_tables

CLAIM = {
    "id": "J7",
    "from_state": "tick 0",
    "claim": (
        "**cadence sensitivity (content check, not hold-out).** With every principal's "
        "cadence set to 1 (each government deciding daily), the point of no return of J2 "
        "moves earlier by at least two days and the localized war of J3 becomes keepable by "
        "{GER} alone: the asymmetry of speed, not the content of any single decision, is what "
        "shortens the window"
    ),
    "expected": "as stated",
    "sources": "the model's own construction; reported as the mechanism the AGI model inherits",
}


@pytest.mark.slow
def test_J7():
    timer = Timer()
    print("\n[J7] engine: explicit; the build with every cadence 1 against the model of record")
    failures = []
    for pair in FIGHT:
        rec, _, _ = j2_departures(pair, cadence=True, coalitions=(X,))
        daily, g, _ = j2_departures(pair, cadence=False, coalitions=(X,))
        d0_rec, _ = departure_from_tick0(pair, True)
        d0_daily, _ = departure_from_tick0(pair, False)
        shift = kept_as(rec[X]) - kept_as(daily[X])
        print(
            f"[J7] {label(pair)}: X's departure from tick 32: record {rec[X]}, daily {daily[X]} "
            f"(earlier by {shift}); from tick 0: record {d0_rec}, daily {d0_daily}"
        )
        if shift < 2:
            failures.append(f"{label(pair)}: point of no return earlier by {shift} < 2 days")
    for pair in PAIRS:
        g, reachable, piv, per_tick, keep = j3_tables(pair, cadence=False)
        print(
            f"[J7] {label(pair)} daily build ({g.size()} states): LOCALIZED reachable "
            f"{reachable}; forcing {fmt(piv.forcing)}; blocking {fmt(piv.blocking)}; keeping "
            f"the invariant {fmt(keep)}"
        )
        gbr = [t for t, fam in per_tick if any("GBR" in c for c in fam)]
        print(f"[J7]   ticks with GBR in a minimal forcing coalition: {gbr}")
        if pair == LOCALIZE_DETER and frozenset({"GER"}) not in piv.forcing:
            failures.append(f"{{GER}} does not force LOCALIZED alone: {fmt(piv.forcing)}")
    print(f"[J7] done ({timer})")
    assert not failures, "; ".join(failures)
