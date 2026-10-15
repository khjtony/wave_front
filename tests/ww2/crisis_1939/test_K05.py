"""K5: registered 2026-10-15 in docs/crisis_1939_testbed.md section 3.

The summer-1939 crisis sub-game of WW2 v1 (3-day ticks, 5 July to 3 September 1939), entered
from the 1939Q3 state. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "K5",
    "from_state": "tick 0",
    "claim": (
        "negative control: an attack launched before 26 August (tick 17) needs at least one "
        "relaxation, and every minimal set relaxes Case White's readiness part (the date of 1 "
        "September fixed on 3 April, a constraint the record never lifts)"
    ),
    "expected": "as stated",
    "sources": "Case White directive of 3 April 1939 (C-120)",
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_K5():
    raise NotImplementedError(CLAIM["id"])
