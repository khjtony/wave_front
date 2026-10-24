"""V8: Force past survivability on cw_v1 (C10 as amended).

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V8a. The readings the model step must fix before first sight are listed in
section 9.4.
"""

import os

import pytest

CLAIM = {
    "id": "V8",
    "from_state": "each year from 1965",
    "claim": (
        "on cw_v1, C10 as amended 2026-10-23, with `balance_core` in place of `balance_cw` "
        "in the unilateral kernels (the bloc clause empties `⟨⟨USA⟩⟩` by construction; "
        "section 9.2): once both principals hold survivable second strike, further increases "
        "in `nuke` do not change kernel membership; `oversight` and `belief` do change the "
        "state's membership in the unilateral kernels `⟨⟨USA⟩⟩□balance_core` and "
        "`⟨⟨USSR⟩⟩□balance_core` or its shortest trace to `GENERAL_WAR` or `ACCIDENTAL_WAR`; "
        "the ranking before 1965, `nuke` above `oversight` and `belief`, is the claim's "
        "negative control"
    ),
    "expected": (
        "the sensitivity report (Q7), scoring a variable by the one-level perturbations that "
        "change unilateral-kernel membership or the shortest trace to the adverse endings, "
        "ranks `nuke` below `oversight` and `belief` after 1965 and above them before"
    ),
    "sources": "Schelling 1966; Kristensen and Norris series; re-asks C10 as amended",
}

# The first-sight switch (docs/cw_v1_decisions.md D8): the claim runs only when the owner sets
# WF_FIRST_SIGHT_CWV1=1 for the one recorded run of V1 to V10.
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_CWV1") == "1"


@pytest.mark.skipif(not FIRST_SIGHT, reason="cw_v1 first sight not switched on")
def test_V8():
    raise NotImplementedError(CLAIM["id"])
