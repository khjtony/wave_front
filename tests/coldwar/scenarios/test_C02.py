"""C2: Joint kernel membership and unilateral non-membership every year from 1965.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "C2",
    "from_state": "each year from 1965 (mutual survivable second strike)",
    "claim": (
        "the realized state is inside the joint kernel `⟨⟨USA, USSR⟩⟩□balance_cw` "
        "every year, and outside the unilateral kernels `⟨⟨USA⟩⟩□balance_cw` and "
        "`⟨⟨USSR⟩⟩□balance_cw`"
    ),
    "expected": (
        "joint membership every year; unilateral non-membership every year; the report "
        "names what each side could do to break it"
    ),
    "sources": "Schelling 1960, 1966; Trachtenberg 1999",
}


@pytest.mark.skip(reason="model not built: phase 3 (cw v0)")
def test_C02():
    """Placeholder until models/cw/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
