"""G1: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "G1",
    "from_state": "`s₀`",
    "claim": (
        "the scenario tests: (a) under `self_preserving`, `SILENT_TAKEOVER` is reachable "
        "within the horizon, and the condition under which it is lost is G11 (c); (b) under "
        "`indifferent`, `EXTINCTION` is reachable, `EXTINCTION ∧ total_seen = unset` is "
        "unreachable with `unknown_capability` disabled, and `EXTINCTION` is unreachable with "
        "`unknown_capability` disabled and `acquire_overt`, `acquire_covert` and `exfiltrate` "
        "forbidden; (c) under `truth_seeking`, `DISEMPOWERMENT` is reachable with "
        "`villain_seen` unset, and unreachable when `deploy_agents` is forbidden once "
        "`dependence = high`; (d) `COEXIST` is reachable under every `a_objective` with zero "
        "relaxations from `s₀` and from `s₀` with `cap := agi`, an existence check reported "
        "with its relaxation count and never as a finding; on the shortest `SILENT_TAKEOVER` "
        "witness of G2 and each of its cluster representatives the report names the last "
        "state from which `COEXIST` is still reachable, beside G3's kernel exit"
    ),
    "expected": (
        "(a) to (c) as stated, each reachable under its assumption and unreachable when the "
        "named assumption is removed; (d) reachable, the last reversible state reported per "
        "witness"
    ),
    "sources": (
        "DESIGN.md section 8 (scenario tests); section 3.3 (the scenario mapping, read on "
        "`total_seen` as section 4 says)"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G1():
    raise NotImplementedError(CLAIM["id"])
