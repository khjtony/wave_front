"""J6v1: registered 2026-10-24 in docs/july1914_testbed.md section 8.3 (the 1914 v1
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
    "id": "J6v1",
    "from_state": "tick 0",
    "claim": (
        "**negative control (hold-out), re-registered on v1.** A general European war by 15 July "
        "(before the ultimatum) needs at least two relaxations under every hypothesis pair, because"
        " every power's first step answered another's: Vienna's note waited on its own decision "
        "cycle, Russia's measures on Vienna's note, Germany's mobilization on Russia's measures. "
        "Every minimal set relaxes an Austro-Hungarian decision-cycle part (a part of Tisza's "
        "consent or of the note that reads it, or the harvest leave of the army, which the record "
        "never lifts) or a part by which a German mobilization step answers a Russian measure "
        "(`russian_measures` or [H] of `GER.kriegsgefahr` or `GER.mobilize`); "
        "`GER.mobilize:sequence` alone, v0's route, no longer suffices"
    ),
    "expected": "as stated",
    "sources": (
        "the Council of 7 July and Tisza's memoranda of 1 and 8 July; Conrad's harvest-leave "
        "constraint; the Russian Council of 24 July (measures only after the note); Bethmann's "
        "policy of letting Russia move first (Müller's diary, 1 August; Mombauer (ed.) 2013); Clark"
        " 2012 chs. 9 to 11; Otte 2014"
    ),
}


@pytest.mark.skipif(not V1.exists(), reason="1914 v1 not built")
def test_J6v1():
    raise NotImplementedError(CLAIM["id"])
