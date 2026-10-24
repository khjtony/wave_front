"""J9v1: registered 2026-10-24 in docs/july1914_testbed.md section 8.3 (the 1914 v1
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
    "id": "J9v1",
    "from_state": "tick 32 (30 July)",
    "claim": (
        "**Russia's exit alone (hold-out; new).** With Germany's mobilization answering a Russian "
        "measure as its Kriegsgefahr did, Russia alone could still have kept the peace with Germany"
        " on 30 July, before the general order took effect: the realized state of 30 July is in the"
        ' kernel of {RUS} for "no war between Germany and Russia" under every hypothesis pair (the '
        "Tsar could withhold the general order, as he had cancelled one on 29 July, and the partial"
        " measures could still be revoked), and {RUS}'s kernel along the realized path is left at "
        "the state after the general order (31 July)"
    ),
    "expected": (
        "the realized state at tick 32 in {RUS}'s kernel of `no_war_GER_RUS` under every pair; "
        "under `fight` {RUS}'s departure along the realized path from tick 32 at tick 33"
    ),
    "sources": (
        "the Tsar's countermand of 29 July and the order of 30 July (Lieven 2015; Albertini vol. "
        "II); the German ultimatum to Russia of 31 July (Geiss); Clark 2012 ch. 11; McMeekin 2013; "
        "Trachtenberg 1990/91"
    ),
}


@pytest.mark.skipif(not V1.exists(), reason="1914 v1 not built")
def test_J9v1():
    raise NotImplementedError(CLAIM["id"])
