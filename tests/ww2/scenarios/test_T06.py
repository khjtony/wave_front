"""T6: Germany cannot force the 1941 campaign; V_GER exit falls in 1941Q4 to 1943Q1.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "T6",
    "from_state": "1941Q2",
    "claim": (
        "Germany cannot force control of western USSR plus the Caucasus; the quarter "
        "at which V_GER is left falls between 1941Q4 and 1943Q1"
    ),
    "expected": (
        "`contested` for the 1941 campaign; point of no return inside the window, with "
        "the driving variable named"
    ),
    "sources": "Tooze; Overy; Kershaw",
}


@pytest.mark.skip(reason="model not built: phase 1 (ww2 v0)")
def test_T06():
    """Placeholder until models/ww2/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
