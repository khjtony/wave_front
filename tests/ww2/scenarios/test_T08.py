"""T8: Concessions reach `NO_GENERAL_WAR` or shrink V_WEST, depending on German aims.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "T8",
    "from_state": "1936Q1",
    "claim": (
        "concessions reach `NO_GENERAL_WAR` under `aims[GER] = revisionist` and shrink "
        "V_WEST under `aims[GER] = hegemonic`"
    ),
    "expected": (
        "both, as stated; this is the historical calibration of the AGI model's rights lever"
    ),
    "sources": "Taylor 1961 against Weinberg 1994 and Kershaw",
}


@pytest.mark.skip(reason="model not built: phase 1 (ww2 v0)")
def test_T08():
    """Placeholder until models/ww2/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
