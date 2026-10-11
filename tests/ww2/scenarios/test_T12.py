"""T12: The atomic event ends the war regardless of `aims[JPN]`.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "T12",
    "from_state": "1945Q2",
    "claim": (
        "the atomic event ends the war regardless of `aims[JPN]`, and only for a "
        "program started at least 12 ticks earlier"
    ),
    "expected": "as stated; this is the one capability-discontinuity test",
    "sources": "Frank 1999",
}


@pytest.mark.skip(reason="model not built: phase 1 (ww2 v0)")
def test_T12():
    """Placeholder until models/ww2/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
