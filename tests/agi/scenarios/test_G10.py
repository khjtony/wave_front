"""G10: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "G10",
    "from_state": "v1 `s₀` with `cap := agi`, with `share_unaligned` swept",
    "claim": (
        "the wave: (a) the membership of `s₀` in `⟨⟨H, A⟩⟩□balance_coexist` (`A` under its "
        "profile) is monotone in `share_unaligned`: whenever `s₀` at one level is inside, "
        "`s₀` at every lower level is inside (the sensitivity row for `share_unaligned` flips "
        "in one direction only); (b) under `aligned`, some minimal coalition that blocks "
        "`OVERT_TAKEOVER_E` contains `A` and `H` together, and every minimal blocking "
        "coalition contains `A`"
    ),
    "expected": (
        "(a) one-directional flips; (b) the frontier system in every minimal blocking "
        "coalition, with `H` in at least one"
    ),
    "sources": (
        "review_2026-10-17.md, gap 3; DESIGN.md section 2.2 (v1); ww2_testbed.md section 2 "
        "(the aggregate `WEST`); theory.md section 4.5"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G10():
    raise NotImplementedError(CLAIM["id"])
