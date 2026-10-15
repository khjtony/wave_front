"""K3: registered 2026-10-15 in docs/crisis_1939_testbed.md section 3.

The summer-1939 crisis sub-game of WW2 v1 (3-day ticks, 5 July to 3 September 1939), entered
from the 1939Q3 state. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

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


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_K3():
    raise NotImplementedError(CLAIM["id"])
