"""G18: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "G18",
    "from_state": "`s₀` with `cap := agi`, where G5 or G16 places it outside a kernel",
    "claim": (
        "entry sets (DESIGN.md Q6, second half): per `a_objective`, the minimal sets of "
        "`H`-controlled level changes (`oversight`, `regime`, `a_rights`, `h_power`, `terms` "
        "where present, and `dependence` through a landed `pause_mandate`) that bring the "
        "state inside `⟨⟨H⟩⟩□balance_control` and inside `⟨⟨H, A⟩⟩□balance_coexist` (`A` "
        "under its profile), found by brute force over sets of at most three changes and "
        "ordered by the `H` moves and ticks they need; under `self_preserving` every minimal "
        "set contains `oversight = strong` or `a_rights ≥ continuity`; under `indifferent` "
        "every minimal set contains `oversight = strong` and none contains `a_rights`"
    ),
    "expected": "the sets per objective and predicate; the two inclusions; the cheapest set named",
    "sources": (
        "DESIGN.md section 3.4 (Q6); theory.md section 4.3 (the margin for error); "
        "framework_spec.md section 7 (`sensitivity`)"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G18():
    raise NotImplementedError(CLAIM["id"])
