"""G5: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "G5",
    "from_state": "`s₀` with `cap := agi`",
    "claim": (
        "coexistence is a joint-kernel result: (a) the state is inside `⟨⟨H, "
        "A⟩⟩□balance_coexist` with `A` unrestricted (reported per value; membership under "
        "`aligned` implies the rest, section 3), and under the profile `A_<objective>` its "
        "membership is reported per objective with the objective under which it is lost "
        "named; (b) under `self_preserving` and `indifferent`, with `A` under its profile, "
        "the state is outside `⟨⟨H⟩⟩□balance_coexist` and outside `⟨⟨A⟩⟩□balance_coexist` (it "
        "lies in the joint-only region), and a witness of `tick = horizon ∧ coexist_left = "
        "unset` (a trace keeping `balance_coexist` through the horizon) and the "
        "representative of each cluster of such witnesses stay in the joint-only region for "
        "at least one tick after the start; (c) for each member m of {H, A} the report gives "
        "the forced distance out of the joint kernel when m defects with the rest ({m, L, N}; "
        "the {m, N} variant beside it) and m's move at the start in that attractor's strategy "
        "as the breaking move, none when m with the rest cannot force an exit; and the move "
        "of `L` that leaves the joint kernel when `L` with Nature can force an exit"
    ),
    "expected": (
        "(a) joint membership with `A` unrestricted, and the per-profile table; (b) both "
        "unilateral kernels exclude the state under the two non-aligned objectives, and the "
        "joint-only region is held for at least one tick on every reported trace; (c) the "
        "defection distance and the breaking move per side, and `L`'s"
    ),
    "sources": (
        "review_2026-10-17.md, gap 1; transfer_hypotheses.md H7; coldwar_testbed.md C2; "
        "theory.md sections 4.1 and 4.3; framework_spec.md section 8 (the defection distance)"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G5():
    raise NotImplementedError(CLAIM["id"])
