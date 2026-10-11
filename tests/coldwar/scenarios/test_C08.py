"""C8: Each verification regime raises `oversight` and the distance to the boundary.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "C8",
    "from_state": "1963, 1972, 1987",
    "claim": (
        "each verification regime raises `oversight`; holding forces constant, the "
        "distance to the boundary increases; with `oversight` frozen at 1962 levels, "
        "the 1987 to 1991 drawdown is unreachable within the horizon"
    ),
    "expected": "as stated",
    "sources": "the treaty texts; Hoffman 2009",
}


@pytest.mark.skip(reason="model not built: phase 3 (cw v0)")
def test_C08():
    """Placeholder until models/cw/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
