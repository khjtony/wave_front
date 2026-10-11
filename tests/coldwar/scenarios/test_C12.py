"""C12: Negative controls and the number of relaxations each needs.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "C12",
    "from_state": "various",
    "claim": (
        "negative controls: a United States preventive strike in the early 1950s needs "
        "exactly one relaxation (it was debated and rejected, so it is not absurd); a "
        "Soviet conventional invasion of Western Europe in the 1980s needs 2 or more; "
        "a negotiated merger of the blocs needs 3 or more; `ACCIDENTAL_WAR` is "
        "reachable with zero relaxations and forceable by no coalition"
    ),
    "expected": "as stated",
    "sources": "Trachtenberg 1999; Sagan 1993",
}


@pytest.mark.skip(reason="model not built: phase 3 (cw v0)")
def test_C12():
    """Placeholder until models/cw/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
