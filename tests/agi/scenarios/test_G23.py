"""G23: registered 2026-11-09 in docs/agi_testbed.md section 5.

Registered from docs/ww2_si_disanalogies.md before any AGI guard was written; phase 5. Do not
edit the claim text without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "G23",
    "from_state": "`s₀` with `cap := agi`",
    "claim": (
        "restraint written into `A` (ww2_si_disanalogies.md D1): the ontology tags every guard "
        "part of an `A` action as capability or motive, a part that reads `a_objective`, "
        "`a_rights`, `trust` or `terms` being motive; in the unrestrained build (every motive "
        "part relaxed, no `A_<objective>` profile), under every `a_objective`: (a) the membership "
        "of the state in `⟨⟨H⟩⟩□balance_control` and in `⟨⟨H⟩⟩□balance_deter` equals its "
        "membership in the baseline under `self_preserving` and under `indifferent`; (b) the "
        "continuity lever of G4 is a motive result: in the unrestrained build the membership of "
        "the state in each registered kernel and the forced distance to `SILENT_TAKEOVER` for {A} "
        "(the shortest distance where it is not forced) are identical with `a_rights = none` and "
        "`a_rights = continuity` held; (c) every unilateral `H` kernel membership of G5, G14 and "
        "G16 that differs between the baseline and the unrestrained build is listed with the "
        "motive parts whose relaxation changes it, and the report quotes it as conditional on "
        "those parts"
    ),
    "expected": "(a) and (b) as stated; (c) the list, expected empty",
    "sources": (
        "ww2_si_disanalogies.md D1 and D2; review_2026-11-09.md section 2 (no incentives); "
        "review_phase3_2026-10-18.md section 2; coldwar_testbed.md C2"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G23():
    raise NotImplementedError(CLAIM["id"])
