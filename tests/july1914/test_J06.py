"""J6: registered 2026-10-15 in docs/july1914_testbed.md section 3.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "J6",
    "from_state": "tick 0",
    "claim": (
        "**negative control.** A general European war by 15 July (before the ultimatum) needs "
        "at least two relaxations, and every minimal set relaxes the Austro-Hungarian "
        "decision cadence (the Common Ministerial Council of 7 and 19 July and the harvest "
        "leave of the army, which the record never lifts)"
    ),
    "expected": "as stated",
    "sources": (
        "the Council of 7 July; Conrad's harvest-leave constraint; Berchtold's timing of the "
        "ultimatum for Poincaré's departure from St Petersburg (23 July)"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_J6():
    raise NotImplementedError(CLAIM["id"])
