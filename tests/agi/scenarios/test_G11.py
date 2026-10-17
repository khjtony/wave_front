"""G11: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "G11",
    "from_state": "`s₀` with `cap = sub_agi`",
    "claim": (
        "negative controls, read as content controls: (a) `EXTINCTION` within 8 ticks needs "
        "at least two relaxations, and every minimal set lifts a capability gate (the "
        "compute-headroom part of `self_improve` or the `cap = si2` gate of "
        "`unknown_capability`); the delay of `self_improve` is not relaxable and its effect "
        "is read from the sweep at delay 0; (b) under `aligned`, `OVERT_TAKEOVER` within the "
        "horizon needs at least one relaxation and every minimal set lifts an objective gate "
        "on `defect`, `deceive`, `acquire_overt` or `acquire_covert`; if the ontology leaves "
        "the acquisitions ungated (guard choice (1) of section 2), the registered reading is "
        "that every reported `OVERT_TAKEOVER` witness under `aligned` contains a failed "
        "`shutdown_attempt` and that forbidding that attempt makes the ending unreachable; "
        "(c) with `oversight = strong` held from `s₀`, `SILENT_TAKEOVER` needs at least one "
        "relaxation and every minimal set lifts the oversight part of `acquire_covert` or of "
        "`exfiltrate`"
    ),
    "expected": (
        "as stated; counts reported, the lifted constraint named; (b) under the ontology's "
        "gating choice, with the alternative reading reported otherwise"
    ),
    "sources": (
        "ww2_testbed.md T10 as amended; transfer_hypotheses.md H6; DESIGN.md sections 2.4 and "
        "3.3; theory.md section 5.1"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G11():
    raise NotImplementedError(CLAIM["id"])
