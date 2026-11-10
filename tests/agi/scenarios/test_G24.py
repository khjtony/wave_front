"""G24: registered 2026-11-09 in docs/agi_testbed.md section 5.

Registered from docs/ww2_si_disanalogies.md before any AGI guard was written; phase 5. Do not
edit the claim text without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "G24",
    "from_state": "`s₀` with `cap := agi`, and the G2 witness",
    "claim": (
        "whose clock decides (ww2_si_disanalogies.md D4): with `self_improve` at delay 0 (the "
        "sweep build of section 6) and, separately, with every delay of an `H` action at 0 (the "
        "build option `h_lag = 0`), under every non-aligned `a_objective`: (a) at `self_improve` "
        "delay 0 the membership of the state in `⟨⟨H⟩⟩□balance_control` and the levels of the "
        "point of no return of G3, recomputed on that build's shortest `SILENT_TAKEOVER` witness, "
        "are those of the baseline, and the length of that witness is shorter than the baseline's "
        "by no more than the ontology's `self_improve` delay times the number of capability steps "
        "on the baseline witness; (b) at `h_lag = 0` the state is inside `⟨⟨H⟩⟩□balance_control` "
        "where it is outside in the baseline, or the silent phase of the shortest "
        "`SILENT_TAKEOVER` witness is shorter than the baseline's by at least one tick; where (b) "
        "fails under an objective, the report names the guard parts in the minimal relaxation "
        "sets that restore the membership instead"
    ),
    "expected": (
        "(a) the boundary unchanged and the ending earlier; (b) the boundary moves with `H`'s lag"
    ),
    "sources": (
        "ww2_si_disanalogies.md D4; transfer_hypotheses.md H1, H3, H5; DESIGN.md section 2.5 "
        "(lags) and section 8"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G24():
    raise NotImplementedError(CLAIM["id"])
