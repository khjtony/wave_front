"""J4v1: registered 2026-10-24 in docs/july1914_testbed.md section 8.3 (the 1914 v1
registration, owner's decision 2h of 2026-10-23), before any v1 guard.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature, in the v1 content of section 8.2. Do not edit the claim text
without a changelog entry in that document. Skipped until ``models/july1914/v1.py`` exists;
the model step replaces the body with the reading of the v1 decisions document.
"""

from pathlib import Path

import pytest

V1 = Path(__file__).resolve().parents[2] / "models" / "july1914" / "v1.py"

CLAIM = {
    "id": "J4v1",
    "from_state": "tick 31 (29 July)",
    "claim": (
        "**belief lag under a fast adversary (hold-out), J4 as amended, re-asked on v1.** Berlin's "
        "reading of Britain flips to `fights` on Lichnowsky's telegram of 29 July, and Bethmann's "
        "attempt to restrain Vienna that night is in the decision space; but by the cadence of the "
        "Austro-Hungarian decisions and the Russian general mobilization of the next day, the "
        "restraint cannot land before the mobilization orders: the belief change precedes the "
        "response by an institutional lag of at least one day, and the point of no return (J2v1) "
        "precedes the belief change"
    ),
    "expected": (
        "the restraint action available at tick 31 with its effect visible at tick 33 or later; the"
        " kernel already left at tick 31, before the belief change is visible"
    ),
    "sources": "J4's sources; amended 2026-10-23; re-asked on v1 2026-10-24",
}


@pytest.mark.skipif(not V1.exists(), reason="1914 v1 not built")
def test_J4v1():
    raise NotImplementedError(CLAIM["id"])
