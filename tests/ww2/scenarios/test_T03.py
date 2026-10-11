"""T3: Refused Munich leads to war in 1938, with a contested ending.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "T3",
    "from_state": "1938Q3",
    "claim": "Munich refused leads to war in 1938",
    "expected": (
        "`war[GER][WEST]` reachable within 2 ticks; the ending is `contested`, not "
        "forced for either side"
    ),
    "sources": "Weinberg; Murray and Millett; the opposing readings of German readiness",
}


@pytest.mark.skip(reason="model not built: phase 1 (ww2 v0)")
def test_T03():
    """Placeholder until models/ww2/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
