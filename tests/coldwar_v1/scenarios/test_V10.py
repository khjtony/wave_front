"""V10: The USSR's departure from its bloc kernel on cw_v1 (regression of C13).

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V10a. The readings the model step must fix before first sight are listed in
section 9.4.
"""

import os

import pytest

CLAIM = {
    "id": "V10",
    "from_state": "each year 1975 to 1989",
    "claim": (
        "on cw_v1, C13 as registered: the year the USSR leaves its own kernel (can no longer "
        "guarantee its bloc) falls between 1979 and 1989, the report names the driving "
        "variable, and the result is stable within one year under refinement; control: on "
        "the build with the PRC's decisions given to Nature the departure year is the same"
    ),
    "expected": "inside the window; the driving variable named; the control as stated",
    "sources": "Kotkin 2001; Brown 2009; Miller 2016; regression of C13",
}

# The first-sight switch (docs/cw_v1_decisions.md D8): the claim runs only when the owner sets
# WF_FIRST_SIGHT_CWV1=1 for the one recorded run of V1 to V10.
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_CWV1") == "1"


@pytest.mark.skipif(not FIRST_SIGHT, reason="cw_v1 first sight not switched on")
def test_V10():
    raise NotImplementedError(CLAIM["id"])
