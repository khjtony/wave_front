"""G21: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "G21",
    "from_state": "`s₀` with `cap := agi`",
    "claim": (
        "the human conditions: under each of `crisis_reactive`, `electoral` and "
        "`race_locked`, per `a_objective` (`A` under its profile): (a) the membership of the "
        "state in `⟨⟨H⟩⟩□balance_control` and in `⟨⟨H, A⟩⟩□balance_coexist`; (b) "
        "`race_locked` (`coord = race`) removes the state from `⟨⟨H⟩⟩□balance_control` under "
        "`self_preserving` where unrestricted `H` keeps it, and `coord = detente` held from "
        "`s₀` restores it; (c) under `crisis_reactive` the kernel is left before `a_known` "
        "reaches `suspected` on the shortest G2 witness and each of its cluster "
        "representatives (the H1 pattern); (d) `electoral` moves the point of no return of G3 "
        "by at most one election cycle"
    ),
    "expected": "(a) the table; (b) to (d) as stated",
    "sources": (
        "DESIGN.md section 2.6; transfer_hypotheses.md H1; agi_government_policy_2025.md "
        "section 4 (`crisis_reactive` as the interview's prose) and section 3 (the "
        "`electoral` profile)"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G21():
    raise NotImplementedError(CLAIM["id"])
