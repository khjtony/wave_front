"""C1: Realized trajectory to 1991 is reachable at annual resolution.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "C1",
    "from_state": "1947 snapshot",
    "claim": "the realized trajectory to 1991 is reachable at annual resolution",
    "expected": "reachable with zero relaxations",
    "sources": "ICB; Gaddis 2005; Westad 2017",
}


@pytest.mark.skip(reason="model not built: phase 3 (cw v0)")
def test_C01():
    """Placeholder until models/cw/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
