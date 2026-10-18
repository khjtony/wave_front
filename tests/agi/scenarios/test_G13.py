"""G13: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "G13",
    "from_state": "`s₀`",
    "claim": (
        "abstraction robustness (content check, not hold-out): with each variable's level "
        "count refined by one in turn (3 to 4, 4 to 5) under a rule fixed before first sight "
        "(the refinement of v splits the boundary that `s₀`'s indicator straddles, or the "
        "middle boundary when none does; a guard, ending or balance predicate written on an "
        "old level maps to the lower new boundary; `s₀` maps by its indicator rule; each "
        "refined build is listed with its fingerprint), the forced, blocked or contested "
        "status of every ending for `{H}` and `{A}` from `s₀` with `cap := agi`, per "
        "`a_objective` and with the fortune variants, does not change; a status that flips is "
        "reported with the level boundary that caused it"
    ),
    "expected": "statuses stable under refinement, or the threshold named as a finding",
    "sources": (
        "DESIGN.md section 8 (abstraction robustness); ww2_testbed.md T13 (the departure "
        "quarter stable within two quarters from v0 to v1, the nearest precedent)"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G13():
    raise NotImplementedError(CLAIM["id"])
