"""J1: registered 2026-10-15 in docs/july1914_testbed.md section 3.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "J1",
    "from_state": "tick 0",
    "claim": (
        "the realized sequence (the blank cheque of 5 to 6 July, the ultimatum of 23 July, "
        "the Serbian reply, the declaration of 28 July, the Russian partial then general "
        "mobilization, the German Kriegsgefahrzustand, the declarations of 1 and 3 August, "
        "the Belgian ultimatum and invasion, the British ultimatum) is reachable with zero "
        "relaxations, every action available at its tick"
    ),
    "expected": "reachable, zero relaxations",
    "sources": (
        "Geiss, July 1914 (the documents); Albertini; Clark, The Sleepwalkers; Otte, July Crisis"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_J1():
    raise NotImplementedError(CLAIM["id"])
