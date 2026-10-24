"""V7: Verification regimes on cw_v1 (C8 as amended).

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V7a. The readings the model step must fix before first sight are listed in
section 9.4.
"""

import os

import pytest

CLAIM = {
    "id": "V7",
    "from_state": "1963, 1972, 1987",
    "claim": (
        "on cw_v1, C8 as amended 2026-10-23, with `balance_core` in place of `balance_cw` in "
        "the unilateral kernels (the bloc clause empties `⟨⟨USA⟩⟩` by construction; section "
        "9.2): each verification regime raises `oversight`; holding forces constant, the "
        "distance to the boundary increases, measured on reachability and on the unilateral "
        "kernels: of the shortest trace to `GENERAL_WAR` or `ACCIDENTAL_WAR` and the "
        "distances out of `⟨⟨USA⟩⟩□balance_core` and `⟨⟨USSR⟩⟩□balance_core`, at least one "
        "is larger with the regime's `oversight` than with the level before it and none is "
        "smaller; with `oversight` frozen at 1962 levels, the 1987 to 1991 drawdown is "
        "unreachable within the horizon; the frozen-oversight clause is the claim's negative "
        "control"
    ),
    "expected": "as stated",
    "sources": "the treaty texts; Hoffman 2009; re-asks C8 as amended",
}

# The first-sight switch (docs/cw_v1_decisions.md D8): the claim runs only when the owner sets
# WF_FIRST_SIGHT_CWV1=1 for the one recorded run of V1 to V10.
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_CWV1") == "1"


@pytest.mark.skipif(not FIRST_SIGHT, reason="cw_v1 first sight not switched on")
def test_V7():
    raise NotImplementedError(CLAIM["id"])
