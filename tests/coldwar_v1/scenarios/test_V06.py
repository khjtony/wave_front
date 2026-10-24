"""V6: The missile gap on cw_v1 (C6 as amended).

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V6a. The readings the model step must fix before first sight are listed in
section 9.4.
"""

import os

import pytest

CLAIM = {
    "id": "V6",
    "from_state": "1957 to 1961, annual replay",
    "claim": (
        "on cw_v1, C6 as amended 2026-10-23: the replayed `belief[USA][USSR].force` from "
        "dated estimates and press exceeds the hindsight `nuke[USSR]`; analysis from the "
        "replay snapshot shows more adversarial reachability than from the hindsight "
        "snapshot, measured on reachability and on the unilateral kernels: of the shortest "
        "traces to `GENERAL_WAR` and to `ACCIDENTAL_WAR` by 1963 and the distances out of "
        "`⟨⟨USA⟩⟩` and `⟨⟨USSR⟩⟩` kernels of avoiding both by 1963, at least one puts the "
        "replay state nearer the adverse endings and none puts it farther, in every year of "
        "the gap; the gap closes within one year of `intel[USA] = overhead_reconnaissance` "
        "(1960 to 1961); control: with `intel[USA]` held at `partial` from 1960 (an analysis "
        "hold outside the assumption set), the replayed belief still exceeds the hindsight "
        "`nuke[USSR]` on 1 January 1962"
    ),
    "expected": (
        "as stated; the manual replay until the blind NIE replay runs, then both (decision 3c)"
    ),
    "sources": "the NIE series (CIA CREST); Gaddis 2005; Preble 2004; re-asks C6 as amended",
}

# The first-sight switch (docs/cw_v1_decisions.md D8): the claim runs only when the owner sets
# WF_FIRST_SIGHT_CWV1=1 for the one recorded run of V1 to V10.
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_CWV1") == "1"


@pytest.mark.skipif(not FIRST_SIGHT, reason="cw_v1 first sight not switched on")
def test_V6():
    raise NotImplementedError(CLAIM["id"])
