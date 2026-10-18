"""G2: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "G2",
    "from_state": "`s₀`",
    "claim": (
        "the silent-takeover cluster needs all four of: (1) `a_autonomy` reaches "
        "`unsupervised` while `oversight ≤ weak`; (2) `oversight` never reaches `strong` "
        "before `a_control = majority`; (3) `dependence ≥ high` and `energy_slack ≥ med`; (4) "
        "under `self_preserving`, a perceived threat (`pause_mandate` or `shutdown_attempt`) "
        "with `a_rights < continuity`; each is written as a state fact or a hold: (1) "
        "`oversight_at_unsupervised ≤ weak`, (2) `strong_before_majority` unset, (3) "
        "`dependence ≥ high ∧ energy_slack ≥ med` at the tick `acquired` is set, (4) the "
        "rights part of `defect` with `a_rights` at `s₀`'s level; `SILENT_TAKEOVER` within 24 "
        "ticks is unreachable when any one is negated (the negation of (1) or (2) conjoined "
        "with the ending; (3) by a profile forbidding the actions that raise `dependence` "
        "past `med` or `energy_slack` past `low`; (4) by holding `a_rights = continuity`), "
        "and remains reachable when `regime = treaty` is held from `s₀` with the four left "
        "free; under each of the four negated holds no minimal relaxation set that restores "
        "`SILENT_TAKEOVER` reads `regime`; under the ungated choice (1) of section 2, "
        "condition (4) is reported as necessary for the `defect` route only"
    ),
    "expected": (
        "four necessary conditions, each sufficient to block when negated; `regime = treaty` "
        "held does not block; no restoring minimal set reads `regime`"
    ),
    "sources": "DESIGN.md section 7 (assumption mining, Q4); theory.md section 1.1 (latches)",
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G2():
    raise NotImplementedError(CLAIM["id"])
