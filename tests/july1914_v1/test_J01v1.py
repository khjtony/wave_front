"""J1v1: registered 2026-10-24 in docs/july1914_testbed.md section 8.3 (the 1914 v1
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
    "id": "J1v1",
    "from_state": "tick 0",
    "claim": (
        "**regression.** The realized sequence of J1, with Tisza's consent of 14 July added, is "
        "reachable in v1 with zero relaxations, every action available at its tick; in particular "
        "the German mobilization of 1 August is available under its new Russian-measures and [H] "
        "parts, after the Russian general mobilization order of 30 July"
    ),
    "expected": (
        "reachable, zero relaxations, under at least one hypothesis pair, ending in `GENERAL_WAR` "
        "at the horizon"
    ),
    "sources": (
        "J1's sources; Berchtold's report to Franz Joseph of 14 July; the German ultimatum to "
        "Russia of 31 July and the mobilization order of 1 August (Geiss; Mombauer (ed.) 2013)"
    ),
}


@pytest.mark.skipif(not V1.exists(), reason="1914 v1 not built")
def test_J1v1():
    raise NotImplementedError(CLAIM["id"])
