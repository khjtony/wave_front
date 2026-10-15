"""K1: registered 2026-10-15 in docs/crisis_1939_testbed.md section 3.

The summer-1939 crisis sub-game of WW2 v1 (3-day ticks, 5 July to 3 September 1939), entered
from the 1939Q3 state. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "K1",
    "from_state": "tick 0",
    "claim": (
        "the realized sequence (military talks agreed, missions in Moscow, Voroshilov's "
        "question, the Polish refusal, the Soviet adjournment, the pact of 23 August, the "
        "attack order of 25 August and its cancellation, the re-order of 31 August, the "
        "attack of 1 September, the declarations of 3 September) is reachable with zero "
        "relaxations, and the exit state equals v1's realized 1939Q4 state"
    ),
    "expected": "reachable, zero relaxations; exit state matches",
    "sources": (
        "DBFP Third Series vols. VI and VII; DGFP Series D vol. VII; Halder's diary; Weinberg"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_K1():
    raise NotImplementedError(CLAIM["id"])
