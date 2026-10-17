"""G20: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "G20",
    "from_state": (
        "the first two dated AGI snapshots (phase 6), or the first snapshot and a 2025Q1 "
        "back-reading built from agi_government_policy_2025.md once its quotations are "
        "verified"
    ),
    "claim": (
        "drift (DESIGN.md Q8): the change in the membership of `⟨⟨H⟩⟩□balance_control` and in "
        "the shortest distance to its boundary between the two readings is reported per "
        "`a_objective` with the variable whose level change accounts for it; a drift carried "
        "by `regime` alone (the revocation of the executive order read as `deregulate`) "
        "changes no membership (G2, G7); a drift carried by `dependence` or `a_autonomy` does"
    ),
    "expected": "the per-variable attribution; the regime-only null result",
    "sources": (
        "DESIGN.md sections 1.2 (item 6), 3.4 (Q8) and 6.3 (`wf drift`); "
        "agi_government_policy_2025.md sections 5 and 6"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G20():
    raise NotImplementedError(CLAIM["id"])
