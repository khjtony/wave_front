"""G12: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "G12",
    "from_state": "`s₀`",
    "claim": (
        "narrative reproduction (content check, not hold-out): each storyline is an ordered "
        "list of waypoint state facts, and a storyline exists as a trace when there is a "
        "chain of shortest witnesses through its waypoints in order under a profile that "
        "forbids every speculative action, under some `a_objective`; the storylines: the AI "
        "2027 race branch (`last_L = race`; `cap ≥ si1` with `oversight ≤ weak`; `a_control = "
        "total`), the AI 2027 slowdown branch (`last_L = race`; `a_known ≥ suspected`; "
        "`regime = treaty ∧ oversight = strong`), and the typical Intelligence Rising plot "
        "(`last_L = race`; an `accident` event; `last_H` in {`fund_oversight`, `regulate_up`, "
        "`pause_mandate`}; then `regime = treaty` or a takeover ending); where a chain "
        "breaks, the minimal relaxation set of the first unreachable waypoint names the "
        "missing guard, and a missing action is the modeler's note"
    ),
    "expected": (
        "each chain exists, or the first unreachable waypoint with its minimal relaxation "
        "sets is reported"
    ),
    "sources": (
        "DESIGN.md section 8 (narrative reproduction); AI 2027; Intelligence Rising; "
        "framework_spec.md sections 5.4 and 6"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G12():
    raise NotImplementedError(CLAIM["id"])
