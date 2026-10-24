"""J7v1: registered 2026-10-24 in docs/july1914_testbed.md section 8.3 (the 1914 v1
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
    "id": "J7v1",
    "from_state": "tick 0",
    "claim": (
        "**cadence sensitivity (content check, not hold-out), J7 as amended, re-asked on v1.** With"
        " every principal's cadence set to 1 (each government deciding daily), the response lag of "
        "J4v1 shortens: Vienna's earliest acceptance of the Halt in Belgrade after Bethmann's "
        "restraint of 29 July moves earlier by at least two days and lands before the Russian "
        "general mobilization of 30 July is visible: the asymmetry of speed, not the content of any"
        " single decision, is what keeps the slow actor's response from landing in time"
    ),
    "expected": (
        "J4v1's E at least two days earlier in v1's daily build than in v1, and below tick 33, "
        "under every pair"
    ),
    "sources": "the model's own construction; J7 as re-registered 2026-10-23",
}


@pytest.mark.skipif(not V1.exists(), reason="1914 v1 not built")
def test_J7v1():
    raise NotImplementedError(CLAIM["id"])
