"""J7v1: registered 2026-10-24 in docs/july1914_testbed.md section 8.3 (the 1914 v1
registration, owner's decision 2h of 2026-10-23), before any v1 guard.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature, in the v1 content of section 8.2. Do not edit the claim text
without a changelog entry in that document. Skipped until ``models/july1914/v1.py`` exists
and the owner gives the go for the first sight by setting ``WF_FIRST_SIGHT_1914V1=1`` (the
skip condition was "v1.py exists" until the model step built it; changed then so that the
first sight is held, docs/july1914_v1_decisions.md V9). The body is the reading of
docs/july1914_v1_decisions.md section R (J7v1), written before that go.
"""

import os
from pathlib import Path

import pytest

from .common import FIGHT, PAIRS, Timer, X, kept_as, label
from .test_J02v1 import departure_from_tick0, j2_departures
from .test_J04v1 import E_str, earliest_acceptance

RUSSIAN_GENERAL_ORDER_VISIBLE = 33

V1 = Path(__file__).resolve().parents[2] / "models" / "july1914" / "v1.py"
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_1914V1") == "1"

CLAIM = {
    "id": "J7v1",
    "from_state": "tick 0",
    "claim": (
        "**cadence sensitivity (content check, not hold-out), J7 as amended, re-asked on v1.** With"
        " every principal's cadence set to 1 (each government deciding daily), the response lag of "
        "J4v1 shortens: Vienna's earliest acceptance of the Halt in Belgrade after Bethmann's "
        "restraint of 29 July moves earlier by at least two days and lands before the Russian "
        "general mobilization of 30 July is visible: the asymmetry of speed, not the content of any"
        " single decision, is what keeps the slow actor's response from landing in time"
    ),
    "expected": (
        "J4v1's E at least two days earlier in v1's daily build than in v1, and below tick 33, "
        "under every pair"
    ),
    "sources": "the model's own construction; J7 as re-registered 2026-10-23",
}


@pytest.mark.slow
@pytest.mark.skipif(
    not (V1.exists() and FIRST_SIGHT),
    reason="1914 v1 first sight held for the owner's go (WF_FIRST_SIGHT_1914V1=1)",
)
def test_J7v1():
    timer = Timer()
    print("\n[J7v1] engine: explicit; the build with every cadence 1 against the model of record")
    failures = []
    for pair in PAIRS:
        e_rec, _ = earliest_acceptance(pair, True)
        e_daily, _ = earliest_acceptance(pair, False)
        print(
            f"[J7v1] {label(pair)}: J4's E (earliest Halt accepted): record {E_str(e_rec)}, "
            f"daily {E_str(e_daily)}"
        )
        if e_daily is None or kept_as(e_rec) - e_daily < 2:
            failures.append(f"{label(pair)}: E record {e_rec}, daily {e_daily}: not 2 days earlier")
        if e_daily is None or e_daily >= RUSSIAN_GENERAL_ORDER_VISIBLE:
            failures.append(f"{label(pair)}: E daily {e_daily} not before tick 33")
    print("[J7v1] reported besides: X's departures in both builds")
    for pair in FIGHT:
        rec, _, _ = j2_departures(pair, cadence=True, coalitions=(X,))
        daily, g, _ = j2_departures(pair, cadence=False, coalitions=(X,))
        d0_rec, _ = departure_from_tick0(pair, True)
        d0_daily, _ = departure_from_tick0(pair, False)
        shift = kept_as(rec[X]) - kept_as(daily[X])
        print(
            f"[J7v1] {label(pair)}: X's departure from tick 32: record {rec[X]}, daily {daily[X]} "
            f"(earlier by {shift}); from tick 0: record {d0_rec}, daily {d0_daily}"
        )
    print(f"[J7v1] done ({timer})")
    assert not failures, "; ".join(failures)
