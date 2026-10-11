"""T13: The state leaves V for `NO_GENERAL_WAR` inside 1936Q1 to 1939Q3.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "T13",
    "from_state": "each quarter 1936Q1 to 1939Q3",
    "claim": (
        "the quarter at which the state leaves V for `NO_GENERAL_WAR` falls inside the "
        "window, and the report names the driving variable"
    ),
    "expected": "departure inside 1936Q1 to 1939Q3; stable within 2 quarters under refinement",
    "sources": "the Rhineland, Munich and Prague readings",
}


@pytest.mark.skip(reason="model not built: phase 1 (ww2 v0)")
def test_T13():
    """Placeholder until models/ww2/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
