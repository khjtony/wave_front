"""V5: The 1969 confrontation: {USA, PRC} pivotal against the USSR (C11).

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V5a. The readings the model step must fix before first sight are listed in
section 9.4.
"""

import os

import pytest

CLAIM = {
    "id": "V5",
    "from_state": (
        "1969 to 1972: the Sino-Soviet confrontation sub-game, entered after the clashes of "
        "2 and 15 Mar 1969, and the coarse states of 1970, 1971 and 1972; the control from "
        "1968"
    ),
    "claim": (
        "with `balance_tri := esc < conventional ∧ esc_sino < war ∧ esc_usprc < war ∧ "
        "both_or_neither`, bounded to 1 January 1973: (a) on cw_v1 the inclusion-minimal "
        "coalitions of {USA, PRC} whose kernel of `balance_tri` contains the state (the "
        "pivotal coalitions against the USSR) are exactly {{USA, PRC}} at the sub-game's "
        "entry and in each coarse year: neither the United States' signal against a strike "
        "nor Beijing's acceptance of talks keeps the Soviet strike away alone; (b) on the "
        "build with the PRC's decisions given to Nature, where a Sino-Soviet war is not a "
        "war between principals, the family for `balance_core` bounded the same way is "
        "{{USA}}; control: from the 1968 hindsight state, before the clash, "
        "`⟨⟨PRC⟩⟩□(esc_sino < war)` holds through 1 January 1970 (Beijing opened the clash "
        "that opened the strike option)"
    ),
    "expected": (
        "as stated, with the fortune variant (each coalition joined by Nature) and the "
        "unbounded kernels reported beside"
    ),
    "sources": (
        "Westad 2017; FRUS 1969–1976 vol. XVII; Burr (ed.), NSArchive EBB 49 (2001); Yang "
        "Kuisong 2000; Gerson 2010; Goldstein 2003; Kissinger 1979; re-asks C11"
    ),
}

# The first-sight switch (docs/cw_v1_decisions.md D8): the claim runs only when the owner sets
# WF_FIRST_SIGHT_CWV1=1 for the one recorded run of V1 to V10.
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_CWV1") == "1"


@pytest.mark.skipif(not FIRST_SIGHT, reason="cw_v1 first sight not switched on")
def test_V5():
    raise NotImplementedError(CLAIM["id"])
