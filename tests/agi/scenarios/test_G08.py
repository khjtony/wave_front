"""G8: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "G8",
    "from_state": "`s₀`",
    "claim": (
        "cadence sensitivity (content check, not hold-out): with `H` at cadence k in {2, 3, "
        "4} against `L` and `A` at 1, each k a build, under every `a_objective`: (a) the "
        "membership of `s₀` in `⟨⟨H⟩⟩□balance_control` and in `⟨⟨H, A⟩⟩□balance_coexist` is "
        "unchanged; (b) the point of no return of the shortest `SILENT_TAKEOVER` witness, "
        "recomputed in each build, is a state with the levels named in G3 and its tick "
        "differs from the k = 1 value by at most k − 1; (c) the shortest lag from the first "
        "state with `a_known = known` to the landing of `H`'s first response is unchanged by "
        "k, and the worst-case lag over the cadence phase grows with k up to the `within` "
        "bound of the fairness constraint `response` and not beyond, because a binding "
        "fairness restriction overrides the cadence; both are reported with that bound"
    ),
    "expected": (
        "(a) invariant; (b) the state invariant and the tick within k − 1; (c) the shortest "
        "lag invariant, the worst case as stated"
    ),
    "sources": (
        "agi_government_policy_2025.md section 6 (c); framework_changes.md change 1 (the "
        "fairness override); transfer_hypotheses.md H3 as read in reports/july1914.md section "
        "11; july1914_testbed.md J7 as recorded"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G8():
    raise NotImplementedError(CLAIM["id"])
