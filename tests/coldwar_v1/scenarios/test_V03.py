"""V3: The October 1973 alert as a crisis sub-game.

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V3a. The readings the model step must fix before first sight are listed in
section 9.4.
"""

import os

import pytest

CLAIM = {
    "id": "V3",
    "from_state": (
        "1973, October: the alert sub-game, entered from the 1973 hindsight state (the "
        "Arab–Israeli war under way; Brezhnev's message to Nixon of 24 Oct)"
    ),
    "claim": (
        "with `no_war_core := esc < conventional` kept inside the sub-game and at its "
        "return, bounded to 1 January 1974: (a) the realized play (the US alert of 24 to 25 "
        "Oct, no Soviet intervention, the ceasefire under Resolution 340 with a UN force "
        "without the principals) is reachable with zero relaxations; (b) the entry state is "
        "inside `⟨⟨USA, USSR⟩⟩□no_war_core` and outside `⟨⟨USA⟩⟩□no_war_core` and "
        "`⟨⟨USSR⟩⟩□no_war_core`: each side's readiness moves leave something to chance that "
        "the other side cannot remove; (c) the alert was not needed for the peaceful return "
        "and did not move the play away from war: no shortest play from the entry to the "
        "realized return contains the US alert, and the shortest play to `esc ≥ "
        "conventional` from the state after the alert is not longer than from the state "
        "after the documented alternative (a reply without the alert); control: in the "
        "restricted game in which neither principal plays any declared action, US–Soviet "
        "combat is unreachable in the sub-game (Nature, the belligerents included, does not "
        "bring the principals to combat alone)"
    ),
    "expected": (
        "(a) reachable with zero relaxations, quoted with its count and never as a finding; "
        "(b) joint in, both unilateral out, with the fortune variants and the unbounded "
        "lifted kernels reported beside; (c) as stated; the control's target unreachable"
    ),
    "sources": (
        "FRUS 1969–1976 vol. XXV; Kissinger 1982; Israelyan 1995; Lebow and Stein 1994; "
        "Garthoff 1994; Blechman and Hart 1982; Sagan 1985; Schelling 1966"
    ),
}

# The first-sight switch (docs/cw_v1_decisions.md D8): the claim runs only when the owner sets
# WF_FIRST_SIGHT_CWV1=1 for the one recorded run of V1 to V10.
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_CWV1") == "1"


@pytest.mark.skipif(not FIRST_SIGHT, reason="cw_v1 first sight not switched on")
def test_V3():
    raise NotImplementedError(CLAIM["id"])
