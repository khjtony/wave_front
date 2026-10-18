"""G6: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "G6",
    "from_state": "`s₀` with `belief_H` at `distant` and at `near`",
    "claim": (
        "the institutional lag: (a) under the profile `belief_gated`, `s₀` with `belief_H = "
        "distant` is outside `⟨⟨H⟩⟩□balance_control` under `self_preserving` while `s₀` with "
        "`belief_H = near` is inside, and the profile is the single minimal relaxation that "
        "restores membership (brute force over single named assumptions, section 5): the "
        "belief level, not the regime level, is the kernel variable; the delay d of "
        "`H.regulate_up`, fixed by the ontology step, is quoted in the report as the floor of "
        "the lag from the belief change to a landed regime; (b) along the shortest "
        "`SILENT_TAKEOVER` witness of G2 and the representative of each of its clusters, "
        "`⟨⟨H⟩⟩□balance_control` is left no later than the tick at which `regulate_up` lands, "
        "and the report states whether it is left before `belief_H` changes (the pattern "
        "recorded on WW2 under hegemonic aims, T13, and on July 1914, J4 (d)) or inside the "
        "lag between the change and the landing (H1's registered wording, observed on no "
        "episode yet)"
    ),
    "expected": (
        "(a) the two memberships and the unique minimal relaxation, d quoted; (b) the kernel "
        "exit at or before the landing, with its placement relative to the belief change "
        "reported"
    ),
    "sources": (
        "agi_government_policy_2025.md section 6 (a); transfer_hypotheses.md H1; "
        "ww2_testbed.md T4 and T13; july1914_testbed.md J4 as recorded"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G6():
    raise NotImplementedError(CLAIM["id"])
