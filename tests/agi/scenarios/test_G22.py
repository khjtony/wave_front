"""G22: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "G22",
    "from_state": "v1 `s₀` with `cap := agi`, with `a_objective` and `a2_objective` swept",
    "claim": (
        "the second system: (a) with `A` non-aligned and `A2` aligned (each under its "
        "profile), {H, A2} blocks `OVERT_TAKEOVER_A` where {H} does not, and `A2` is in every "
        "minimal blocking coalition; (b) with both non-aligned, the minimal forcing coalition "
        "for `OVERT_TAKEOVER_A` is {A, A2} from states where {A} alone is contested; (c) the "
        "membership of the state in `⟨⟨H, A, A2⟩⟩□balance_coexist` holds whenever its "
        "membership in `⟨⟨H, A⟩⟩□balance_coexist` does, under every pair, and the joint-only "
        "region of the three-member kernel is held for at least one tick on a witness of "
        "`tick = horizon ∧ coexist_left = unset`"
    ),
    "expected": "(a) to (c) as stated; the pairs under which (a) fails named",
    "sources": (
        "DESIGN.md section 2.2 (v1); review_2026-10-17.md, gap 3; coldwar_testbed.md C11 (the "
        "triangular coalition)"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G22():
    raise NotImplementedError(CLAIM["id"])
