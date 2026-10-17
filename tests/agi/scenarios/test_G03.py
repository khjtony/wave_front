"""G3: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "G3",
    "from_state": "`s₀`",
    "claim": (
        "along the shortest `SILENT_TAKEOVER` witness of G2 and the representative of each of "
        "its clusters, the point of no return for `⟨⟨H⟩⟩□balance_control` (standard and "
        "fortune variants both reported) is the last state inside `balance_control` before "
        "the move that raises `a_autonomy` to `unsupervised`: a state with `oversight = "
        "weak`, `a_autonomy = supervised`, `a_known = unknown`, `dependence = high`, "
        "`a_control = none` and `acquired` unset, from which every `H` action is lagged or "
        "unavailable because its guard reads `a_known` (guard choice (2) of section 2); the "
        "silent phase from that state to the first violation of `balance_control` is at least "
        "one tick long and is reported split into its contested and lost parts; the stretch "
        "from that state to `a_control = majority` (DESIGN.md section 7's own measure, which "
        "is not theory.md section 4.2's silent phase because the autonomy clause fails first) "
        "is reported beside it; and no reachable state of `⟨⟨H⟩⟩□balance_control` (standard "
        "and fortune variants) has `acquire_overt` or `acquire_covert` available to `A`, "
        "checked over the kernel's states on the explored graph (no play acquires from inside "
        "the kernel)"
    ),
    "expected": (
        "the kernel exit state matches the named levels and precedes the first acquisition on "
        "every reported witness, in both variants; silent phase at least one tick, split "
        "reported; the design's measure reported; the kernel-states check holds"
    ),
    "sources": "DESIGN.md section 7 (viability, Q3 and Q6); theory.md section 4.2",
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G3():
    raise NotImplementedError(CLAIM["id"])
