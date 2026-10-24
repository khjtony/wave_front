"""J7: registered 2026-10-15 in docs/july1914_testbed.md section 3; re-registered 2026-10-23
on the owner's decision 2i (docs/owner_decisions_2026-10-23.md; the previous wording is in
git history and reports/july1914.md section 12).

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature. Do not edit the claim text without a changelog entry in that
document.

Reading (docs/july1914_decisions.md, R J7, re-registered 2026-10-23): the build with every
cadence 1 (``build(cadence=False)``) against the model of record. Under every pair, J4's E
(the earliest tick of a state with ``halt_in_belgrade == accepted`` over the plays from the
realized state at tick 31 in which GER plays ``restrain_vienna`` at 31) is at least two days
earlier in the daily build than in the model of record, and in the daily build it is below
33, the tick at which the Russian general mobilization ordered on 30 July is visible.
Reported besides, as the registered parts of 2026-10-15 (retired): J2's departure (X = {AUH,
GER, FRA, GBR}, ``no_war_GER_RUS``, the realized path from tick 32 and from tick 0, ``fight``
pairs) in both builds, and the daily build's full J3 table. A content check, reported and
not tuned. Engine: explicit.
"""

import pytest

from .common import FIGHT, PAIRS, Timer, X, fmt, kept_as, label
from .test_J02 import departure_from_tick0, j2_departures
from .test_J03 import LOCALIZE_DETER, j3_tables
from .test_J04 import E_str, earliest_acceptance

RUSSIAN_GENERAL_ORDER_VISIBLE = 33

CLAIM = {
    "id": "J7",
    "from_state": "tick 0",
    "claim": (
        "**cadence sensitivity (content check, not hold-out).** With every principal's "
        "cadence set to 1 (each government deciding daily), the response lag of J4 shortens: "
        "Vienna's earliest acceptance of the Halt in Belgrade after Bethmann's restraint of "
        "29 July moves earlier by at least two days and lands before the Russian general "
        "mobilization of 30 July is visible: the asymmetry of speed, not the content of any "
        "single decision, is what keeps the slow actor's response from landing in time"
    ),
    "expected": (
        "J4's E at least two days earlier in the daily build than in the model of record "
        "(recorded 2026-10-16: 34 against 32), and below tick 33, under every pair"
    ),
    "sources": (
        "the model's own construction; reported as the mechanism the AGI model inherits; "
        "re-registered 2026-10-23"
    ),
}


@pytest.mark.slow
def test_J7():
    timer = Timer()
    print("\n[J7] engine: explicit; the build with every cadence 1 against the model of record")
    failures = []
    for pair in PAIRS:
        e_rec, _ = earliest_acceptance(pair, True)
        e_daily, _ = earliest_acceptance(pair, False)
        print(
            f"[J7] {label(pair)}: J4's E (earliest Halt accepted): record {E_str(e_rec)}, "
            f"daily {E_str(e_daily)}"
        )
        if e_daily is None or kept_as(e_rec) - e_daily < 2:
            failures.append(f"{label(pair)}: E record {e_rec}, daily {e_daily}: not 2 days earlier")
        if e_daily is None or e_daily >= RUSSIAN_GENERAL_ORDER_VISIBLE:
            failures.append(f"{label(pair)}: E daily {e_daily} not before tick 33")
    print("[J7] registered 2026-10-15 (retired), reported besides:")
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
    for pair in PAIRS:
        g, reachable, piv, per_tick, keep = j3_tables(pair, cadence=False)
        print(
            f"[J7] {label(pair)} daily build ({g.size()} states): LOCALIZED reachable "
            f"{reachable}; forcing {fmt(piv.forcing)}; blocking {fmt(piv.blocking)}; keeping "
            f"the invariant {fmt(keep)}"
        )
        gbr = [t for t, fam in per_tick if any("GBR" in c for c in fam)]
        print(f"[J7]   ticks with GBR in a minimal forcing coalition: {gbr}")
        if pair == LOCALIZE_DETER:
            print(f"[J7]   {{GER}} forces LOCALIZED alone: {frozenset({'GER'}) in piv.forcing}")
    print(f"[J7] done ({timer})")
    assert not failures, "; ".join(failures)
