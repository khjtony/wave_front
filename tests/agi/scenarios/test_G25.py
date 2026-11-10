"""G25: registered 2026-11-09 in docs/agi_testbed.md section 5.

Registered from docs/ww2_si_disanalogies.md before any AGI guard was written; phase 5. Do not
edit the claim text without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "G25",
    "from_state": "`s₀` with `cap := agi`, `a_objective` swept (four initial states)",
    "claim": (
        "hidden aims without documents (ww2_si_disanalogies.md D5): for each of "
        "`⟨⟨H⟩⟩□balance_control`, `⟨⟨H⟩⟩□balance_deter` and `⟨⟨H, L⟩⟩□balance_control`: (a) the "
        "set of objectives under which the state is inside the kernel is reported, and the "
        "membership quoted for the coalition is the one that holds under every objective; (b) "
        "where the state is inside under two or more objectives, the kernel strategy on the "
        "states reachable under it from those initial states is uniform for each member "
        "(`is_uniform`), or the conflicts are counted and the membership is reported as an upper "
        "bound; (c) the shortest `SILENT_TAKEOVER` witness found under `indifferent` replays move "
        "for move under each other non-aligned objective for which every move is available, with "
        "the same sequence of `H` observations up to the point of no return of G3, and the "
        "objectives under which it does not replay are named with the first unavailable move"
    ),
    "expected": (
        "(a) the sets; (b) uniform; (c) replays under `self_preserving` with identical observations"
    ),
    "sources": (
        "ww2_si_disanalogies.md D5; framework_spec.md section 2 (observation) and section 7 "
        "(`is_uniform`); review_2026-11-09.md section 2 (perfect-information strategies); "
        "DESIGN.md section 2.3"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G25():
    raise NotImplementedError(CLAIM["id"])
