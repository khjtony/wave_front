"""V1: The realized trajectory is reachable on cw_v1 (regression of C1).

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V1a. The readings the model step must fix before first sight are listed in
section 9.4.
"""

import os

import pytest

CLAIM = {
    "id": "V1",
    "from_state": "1947 snapshot of cw_v1",
    "claim": (
        "the realized trajectory to 1991, with the realized moves of the five crisis "
        "sub-games (Berlin 1948, Cuba 1962, the Sino-Soviet confrontation of 1969, the "
        "October 1973 alert, Able Archer 1983) and the PRC's realized decisions from 1950, "
        "is reachable at annual resolution with zero relaxations and ends in "
        "`CHALLENGER_EXHAUSTION`; control: in the restricted game in which the PRC never "
        "plays its Korean entry, a US–PRC war is unreachable by 1 January 1954 (the entry "
        "was Beijing's decision, not an effect of the Korean war)"
    ),
    "expected": (
        "reachable with zero relaxations, an existence check quoted with its relaxation "
        "count and never as a finding; the control's target unreachable"
    ),
    "sources": (
        "ICB; Gaddis 2005; Westad 2017; Chen Jian 1994 and Mansourov 1995/96 (the control); "
        "regression of C1"
    ),
}

# The first-sight switch (docs/cw_v1_decisions.md D8): the claim runs only when the owner sets
# WF_FIRST_SIGHT_CWV1=1 for the one recorded run of V1 to V10.
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_CWV1") == "1"


@pytest.mark.skipif(not FIRST_SIGHT, reason="cw_v1 first sight not switched on")
def test_V1():
    raise NotImplementedError(CLAIM["id"])
