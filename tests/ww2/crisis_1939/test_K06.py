"""K6: registered 2026-10-15 in docs/crisis_1939_testbed.md section 3.

The summer-1939 crisis sub-game of WW2 v1 (3-day ticks, 5 July to 3 September 1939), entered
from the 1939Q3 state. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "K6",
    "from_state": "tick 0",
    "claim": (
        "the Soviet choice is open to both sides until 19 August: from every state up to tick "
        "14 both the pact and the alliance are reachable; under `aims_USSR = defensive` the "
        "pact needs Germany's proposal of a protocol (the German approach at "
        "`pact_proposed`), and without it the Soviet acceptance is unavailable"
    ),
    "expected": (
        "both targets reachable to tick 14; the pact's minimal assumption set names the "
        "German proposal"
    ),
    "sources": "Molotov to Schulenburg, 17 and 19 August; Stalin's reply, 21 August",
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_K6():
    raise NotImplementedError(CLAIM["id"])
