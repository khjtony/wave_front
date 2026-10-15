"""K4: registered 2026-10-15 in docs/crisis_1939_testbed.md section 3.

The summer-1939 crisis sub-game of WW2 v1 (3-day ticks, 5 July to 3 September 1939), entered
from the 1939Q3 state. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "K4",
    "from_state": "tick 17 (25 August)",
    "claim": (
        "after the pact, no coalition blocks the attack under any belief: the Anglo-Polish "
        "treaty of 25 August and Chamberlain's letter of 22 August flip `belief_GER` to "
        "`will_fight` and the attack is cancelled for a documented reason (Italy's "
        "non-readiness and the treaty), but it is re-ordered and launched by 1 September "
        "whatever WEST does; the cancellation of 25 August delays the attack by at most two "
        "ticks"
    ),
    "expected": (
        "from the state of 25 August the attack is forced by Germany by tick 19 under every "
        "belief; the shortest trace shows the cancellation and the re-order"
    ),
    "sources": (
        "DGFP Series D vol. VII (the order of 25 August, 15:02; the cancellation; the order "
        "of 31 August); Halder's diary 25 to 31 August; Ciano's diary"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_K4():
    raise NotImplementedError(CLAIM["id"])
