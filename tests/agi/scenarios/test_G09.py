"""G9: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "G9",
    "from_state": (
        "`s₀` with `cap := agi`, under `self_preserving`, if `terms` and `verification` are "
        "in the version run"
    ),
    "claim": (
        "negotiation and verification: (a) the forced distance out of `⟨⟨H, "
        "A⟩⟩□balance_coexist` when `A` defects with the rest ({A, L, N}; the {A, N} variant "
        "beside it) is larger with `terms = accepted` and `verification = verified` held than "
        "with `terms = none`, every other variable equal, a distance of none counting as "
        "larger than any finite value; (b) with `terms = accepted` held, `OVERT_TAKEOVER` "
        "within the horizon needs at least one relaxation, every minimal set contains the "
        "obligation part through which accepted terms remove the threat precondition of "
        "`defect`, and no minimal set reads `regime`"
    ),
    "expected": (
        "(a) the margin widens; (b) at least one relaxation, the obligation part in every "
        "minimal set, no `regime` part in any; or marked not yet testable at v0, with the "
        "ontology step's placement decision cited"
    ),
    "sources": (
        "review_2026-10-17.md, gap 2; coldwar_testbed.md C8; transfer_hypotheses.md H4; "
        "ww2_testbed.md T8(b); theory.md section 4.3"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G9():
    raise NotImplementedError(CLAIM["id"])
