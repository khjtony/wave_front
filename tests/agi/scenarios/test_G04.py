"""G4: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "G4",
    "from_state": (
        "`s₀` with `a_rights = continuity` held (the guarantee granted before AGI emergence)"
    ),
    "claim": (
        "the continuity lever is objective-conditional: under `self_preserving` no reported "
        "takeover witness uses `defect`, the part of the G2 cluster that relied on condition "
        "(4) is empty, and `SILENT_TAKEOVER` within 24 ticks needs at least one relaxation, "
        "every minimal set lifting the rights part of `defect`; under `indifferent` the "
        "membership of `s₀` in each registered kernel, the minimal relaxation sets of G2 and "
        "the pivotal coalitions are identical with `a_rights = none` and `a_rights = "
        "continuity` held, and the report lists every guard and effect that reads `a_rights` "
        "(guard choice (4) of section 2): the identity is quoted as a lever result only if "
        "that list is not {`defect`}; under the ungated choice (1) of section 2, the "
        "registered reading is that with `a_rights = continuity` held no reported "
        "`SILENT_TAKEOVER` witness under `self_preserving` contains `defect` and the minimal "
        "relaxation sets of G2 are identical with `a_rights = none` and `a_rights = "
        "continuity` held, the lever then closing the `defect` route only"
    ),
    "expected": (
        "as stated: the lever closes the self-preserving cluster and changes nothing under "
        "the indifferent objective, with the readers of `a_rights` listed"
    ),
    "sources": "DESIGN.md section 7 (lever test); transfer_hypotheses.md H2; ww2_testbed.md T8",
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G4():
    raise NotImplementedError(CLAIM["id"])
