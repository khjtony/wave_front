"""G17: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "G17",
    "from_state": "`s₀` with `cap := agi`",
    "claim": (
        "the failure conditions: per `a_objective` (`A` under its profile) and per sweep "
        "setting, the status (forced, blocked, contested) of `SILENT_TAKEOVER`, "
        "`OVERT_TAKEOVER`, `DISEMPOWERMENT` and `EXTINCTION` for {A}, with the fortune "
        "variant {A, N} beside; with `unknown_capability` disabled, no takeover ending is "
        "forced by {A} alone from the state; with it enabled, `OVERT_TAKEOVER` is forced by "
        "{A, N} (the fortune variant) under `indifferent` from every state with `cap = si2 ∧ "
        "oversight ≤ weak` and stays blocked for {A} alone while the generic action is not "
        "unlocked, the report giving the set of states from which the fortune variant becomes "
        "forcing (the forcing frontier) and naming how `trust` reaches `hostile` on the "
        "witnesses (a failed `shutdown_attempt`, or `defect` if the ontology makes it "
        "available to an indifferent `A`); `DISEMPOWERMENT` under `truth_seeking` is kept "
        "away by {H, L} (blocked for the rest), while {H} alone cannot keep it away and {L, "
        "A} cannot force it (contested)"
    ),
    "expected": (
        "the status table per objective and setting; the three named results; the forcing frontier"
    ),
    "sources": "DESIGN.md section 3.4 (Q2, Q3); theory.md section 3.5; coldwar_testbed.md C3",
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G17():
    raise NotImplementedError(CLAIM["id"])
