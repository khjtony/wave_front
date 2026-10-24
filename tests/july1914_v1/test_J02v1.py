"""J2v1: registered 2026-10-24 in docs/july1914_testbed.md section 8.3 (the 1914 v1
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
    "id": "J2v1",
    "from_state": "tick 32 (30 July)",
    "claim": (
        "**the timetable as point of no return (hold-out), J2 as amended, re-asked on v1.** The "
        "point of no return is Russia's last exit, 30 July: the state of that day is the last on "
        'the realized path from which the peace between Germany and Russia ("no war between Germany'
        ' and Russia") can still be kept, and only with Russia. Once Russian general mobilization '
        "is ordered (30 July), the kernel for it is left by every coalition that excludes Russia "
        "within two days, and the driving variable is the German plan's coupling of mobilization "
        "and war: with the coupling relaxed (an eastern-only deployment available, as it was not "
        "after 1913), the kernel is kept two days longer. Recorded beside the result: the departure"
        " along the realized path from 28 June of the kernel of the coalitions that exclude Russia,"
        " predicted not before Vienna's decision of 19 July on the note (Tisza's consent of 14 July"
        " does not by itself take the peace out of their hands)"
    ),
    "expected": (
        "departure inside ticks 31 to 34 with the coupling named as the driving variable; the "
        "relaxation of the coupling moves it by at least two days; Russia's last exit at tick 32 "
        "(the last realized state in the kernel of all five principals); recorded: the departure "
        "from tick 0 at tick 22 or later under `aims_RUS = fight`"
    ),
    "sources": "J2's sources; Albertini vol. II; Clark 2012 ch. 9 (the Council of 19 July)",
}


@pytest.mark.skipif(not V1.exists(), reason="1914 v1 not built")
def test_J2v1():
    raise NotImplementedError(CLAIM["id"])
