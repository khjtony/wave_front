"""K2: registered 2026-10-15 in docs/crisis_1939_testbed.md section 3.

The summer-1939 crisis sub-game of WW2 v1 (3-day ticks, 5 July to 3 September 1939), entered
from the 1939Q3 state. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "K2",
    "from_state": "tick 0",
    "claim": (
        "re-asking T9: a UK, France, USSR alliance concluded before the pact blocks the "
        "attack on Poland only if `belief_GER` is `will_fight`; the coalition that can "
        "conclude it in time is {WEST, USSR} with Nature granting Polish passage, and Polish "
        "passage is pivotal (without it the alliance needs a Soviet decision the record does "
        "not show)"
    ),
    "expected": (
        "pivotal coalition {WEST, USSR} with the belief condition and the passage condition; "
        "without the belief condition, `contested` (the attack is not blocked, and Germany "
        "cannot force it before the pact under `deterred` while the alliance is possible)"
    ),
    "sources": (
        "the Moscow talks (DBFP vol. VII); Voroshilov's question of 14 August; Beck's "
        "refusal; the profile `deterred` as adopted for T9"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_K2():
    raise NotImplementedError(CLAIM["id"])
