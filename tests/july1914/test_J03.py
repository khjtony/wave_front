"""J3: registered 2026-10-15 in docs/july1914_testbed.md section 3.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "J3",
    "from_state": "tick 0 to 30 (28 July)",
    "claim": (
        "**localization (hold-out).** A localized Austro-Serbian war (AUH at war with Serbia, "
        "no great-power mobilization) is reachable to the horizon only under `aims_GER = "
        "localize` with Russia at `deter`, and the pivotal coalition for keeping it localized "
        "is {GER, RUS} jointly; neither alone keeps it, and GBR is not pivotal before 29 July"
    ),
    "expected": (
        "pivotal coalition {GER, RUS}; under `continental` aims the localized ending is "
        "unreachable; GBR's membership in a pivotal coalition appears only from tick 31"
    ),
    "sources": (
        "the \"Halt in Belgrade\" of 28 July; Sazonov's partial-mobilization scheme; Grey's "
        "mediation proposals of 24 to 29 July"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_J3():
    raise NotImplementedError(CLAIM["id"])
