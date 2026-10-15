"""J7: registered 2026-10-15 in docs/july1914_testbed.md section 3.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "J7",
    "from_state": "tick 0",
    "claim": (
        "**cadence sensitivity (content check, not hold-out).** With every principal's "
        "cadence set to 1 (each government deciding daily), the point of no return of J2 "
        "moves earlier by at least two days and the localized war of J3 becomes keepable by "
        "{GER} alone: the asymmetry of speed, not the content of any single decision, is what "
        "shortens the window"
    ),
    "expected": "as stated",
    "sources": "the model's own construction; reported as the mechanism the AGI model inherits",
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_J7():
    raise NotImplementedError(CLAIM["id"])
