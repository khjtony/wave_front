"""C13: The year the USSR leaves its own kernel falls between 1979 and 1989.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "C13",
    "from_state": "each year 1975 to 1989",
    "claim": (
        "the year the USSR leaves its own kernel (can no longer guarantee its bloc) "
        "falls between 1979 and 1989, the report names the driving variable, and the "
        "result is stable within one year under refinement"
    ),
    "expected": "inside the window; `refine at phase 3` for the driving variable",
    "sources": "Kotkin 2001; Brown 2009; Miller 2016",
}


@pytest.mark.skip(reason="model not built: phase 3 (cw v0)")
def test_C13():
    """Placeholder until models/cw/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
