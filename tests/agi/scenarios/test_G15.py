"""G15: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "G15",
    "from_state": "`s₀` with `cap := agi`",
    "claim": (
        "the labs as a principal: (a) per `a_objective`, the minimal blocking coalitions over "
        "{H, L, A} (Nature in the rest, the fortune variant beside) for `SILENT_TAKEOVER`, "
        "`OVERT_TAKEOVER` and `DISEMPOWERMENT`; (b) under `truth_seeking`, every minimal "
        "coalition that blocks `DISEMPOWERMENT` contains `L` unless `nationalize` has landed; "
        "(c) under `self_preserving`, {H, L} blocks `SILENT_TAKEOVER` where {H} alone does "
        "not, and the `L` guard parts (on `deploy_agents` and `safety_invest`) that carry the "
        "difference are named"
    ),
    "expected": (
        "(a) the antichains per ending and objective; (b) `L` in every minimal blocker of "
        "`DISEMPOWERMENT` without `nationalize`; (c) the difference and its parts"
    ),
    "sources": (
        "DESIGN.md sections 3.2 (V_HL) and 3.4 (Q5); theory.md section 4.5; "
        "agi_government_policy_2025.md section 3 (`nationalize`)"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G15():
    raise NotImplementedError(CLAIM["id"])
