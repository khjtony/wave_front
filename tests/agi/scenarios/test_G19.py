"""G19: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "G19",
    "from_state": "`s₀` and `s₀` with `cap := agi`",
    "claim": (
        "sensitivity (DESIGN.md Q7): under ±1 level shifts of each variable, per "
        "`a_objective`, the ranking by membership flips and distance change for "
        "`⟨⟨H⟩⟩□balance_control` places `oversight` and `a_autonomy` above `regime` and "
        "`compute` (the G2 ordering), and `h_power` ranks above `oversight` for "
        "`balance_deter` only; the top-ranked variable per objective is the report's "
        "indicator of the quarter"
    ),
    "expected": "the ranking per objective and predicate; the two orderings",
    "sources": (
        "DESIGN.md section 3.4 (Q7); coldwar_testbed.md C10; framework_spec.md section 7 "
        "(`sensitivity`)"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G19():
    raise NotImplementedError(CLAIM["id"])
