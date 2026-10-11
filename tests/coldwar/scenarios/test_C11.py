"""C11: Adding the PRC changes the pivotal coalition for `DETERRENCE_HOLDS`.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "C11",
    "from_state": "1969 to 1972",
    "claim": (
        "adding the PRC as a principal changes the pivotal coalition for "
        "`DETERRENCE_HOLDS` against the USSR from {USA} to {USA, PRC}"
    ),
    "expected": "as stated",
    "sources": "Westad 2017; FRUS 1969 to 1972",
}


@pytest.mark.skip(reason="model not built: phase 3 (cw v0)")
def test_C11():
    """Placeholder until models/cw/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
