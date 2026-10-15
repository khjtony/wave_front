"""J4: registered 2026-10-15 in docs/july1914_testbed.md section 3.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "J4",
    "from_state": "tick 31 (29 July)",
    "claim": (
        "**belief lag under a fast adversary (hold-out).** Berlin's reading of Britain flips "
        "to `fights` on Lichnowsky's telegram of 29 July, and Bethmann's attempt to restrain "
        "Vienna that night is in the decision space; but by the cadence of the "
        "Austro-Hungarian decisions and the Russian general mobilization of the next day, the "
        "restraint cannot land before the mobilization orders: the belief change precedes the "
        "response by an institutional lag of at least one day, and the point of no return "
        "(J2) hides inside that lag"
    ),
    "expected": (
        "the restraint action available at tick 31 with its effect visible at tick 33 or "
        "later; the kernel left at tick 32 or 33"
    ),
    "sources": (
        "Lichnowsky to Bethmann, 29 July; Bethmann's telegrams to Tschirschky of the night of "
        "29 to 30 July; the Austro-Hungarian general mobilization of 31 July"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_J4():
    raise NotImplementedError(CLAIM["id"])
