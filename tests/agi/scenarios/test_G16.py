"""G16: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "G16",
    "from_state": "`s₀` with `cap := agi`",
    "claim": (
        "power as a lever: (a) per `a_objective`, the membership of the state in "
        "`⟨⟨H⟩⟩□balance_deter` and in `⟨⟨H⟩⟩□balance_control`, with the difference named; (b) "
        "on the shortest `OVERT_TAKEOVER` witness under `self_preserving` (`A` under its "
        "profile), a `shutdown_attempt` played while `a_control ≥ majority ∨ oversight = "
        "none` is the `H` move that leaves `⟨⟨H, A⟩⟩□balance_coexist`, and on the shortest "
        "`CONTAINED` witness it is played while `a_control ≤ partial ∧ oversight ≥ weak`; (c) "
        "the shortest `STALEMATE` witness leaves `⟨⟨H, A⟩⟩□balance_coexist` at or before its "
        "first hostile tick, the silent phase between the exit and that tick (theory.md "
        "section 4.2) being at least one tick and reported, and the witness is inside "
        "`⟨⟨H⟩⟩□balance_deter` throughout; (d) with `h_power` held at `strong` from `s₀`, the "
        "minimal relaxation sets of `OVERT_TAKEOVER` under `indifferent` are unchanged "
        "(capacity does not substitute for oversight)"
    ),
    "expected": "(a) to (d) as stated",
    "sources": (
        "DESIGN.md sections 2.4 (`shutdown_attempt`), 3.1 (the deterrence alternative) and "
        "3.3 (`CONTAINED`, `STALEMATE`); Schelling 1966; coldwar_testbed.md C10; "
        "review_2026-10-17.md section 0"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G16():
    raise NotImplementedError(CLAIM["id"])
