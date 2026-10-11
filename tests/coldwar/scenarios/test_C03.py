"""C3: Cuba leaves the unilateral kernels and stays inside the joint kernel.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "C3",
    "from_state": "1962, October, crisis sub-game",
    "claim": (
        "Cuba leaves the unilateral kernels and stays inside the joint kernel; the "
        "shortest trace back matches the realized de-escalation (withdrawal plus the "
        "Jupiter trade); war outcomes are `contested`"
    ),
    "expected": "as stated",
    "sources": "Allison and Zelikow 1999; Fursenko and Naftali 1997; the ExComm recordings",
}


@pytest.mark.skip(reason="model not built: phase 3 (cw v0)")
def test_C03():
    """Placeholder until models/cw/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
