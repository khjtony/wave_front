"""C4: The airlift is in the decision space and a negotiated settlement is reachable.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "C4",
    "from_state": "1948, June",
    "claim": (
        "the airlift (`resist_without_escalation`) is in the decision space; "
        "`NEGOTIATED_SETTLEMENT` of the blockade is reachable; `GENERAL_WAR` is "
        "`contested`"
    ),
    "expected": "as stated",
    "sources": "FRUS 1948; Trachtenberg",
}


@pytest.mark.skip(reason="model not built: phase 3 (cw v0)")
def test_C04():
    """Placeholder until models/cw/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
