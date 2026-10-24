"""V2: Joint, not unilateral, US–Soviet balance every year from 1967 (C2, H7).

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V2a. The readings the model step must fix before first sight are listed in
section 9.4.
"""

import os

import pytest

CLAIM = {
    "id": "V2",
    "from_state": (
        "each year 1967 to 1991 (both principals at survivable second strike on the record; "
        "Podvig 2001)"
    ),
    "claim": (
        "with `balance_core := esc < conventional ∧ both_or_neither` (US–Soviet only; no "
        "clause on either bloc or on the PRC): the realized state is inside the joint kernel "
        "`⟨⟨USA, USSR⟩⟩□balance_core` every year and outside the unilateral kernels "
        "`⟨⟨USA⟩⟩□balance_core` and `⟨⟨USSR⟩⟩□balance_core` every year (H7); for each year "
        "and each unilateral kernel, the first moves of the other side's forcing strategy "
        "(with Nature) out of `balance_core` are named; control: on the analysis build "
        "without the American crisis-initiating options of the 1970s and 1980s, the state is "
        "inside `⟨⟨USSR⟩⟩□balance_core` in at least one year, so that the United States' "
        "ability to break the balance in the main result is owed to the added options"
    ),
    "expected": (
        "joint membership every year; non-membership of both unilateral kernels every year, "
        "each with its breaking moves named; the control as stated; the kernels of the "
        "registered `balance_cw` and of `balance_tri` reported beside, not asserted"
    ),
    "sources": (
        "Schelling 1960, 1966; Trachtenberg 1999; Sagan and Suri 2003; Blechman and Hart "
        "1982; Jones 2016; re-asks C2 as amended 2026-10-23"
    ),
}

# The first-sight switch (docs/cw_v1_decisions.md D8): the claim runs only when the owner sets
# WF_FIRST_SIGHT_CWV1=1 for the one recorded run of V1 to V10.
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_CWV1") == "1"


@pytest.mark.skipif(not FIRST_SIGHT, reason="cw_v1 first sight not switched on")
def test_V2():
    raise NotImplementedError(CLAIM["id"])
