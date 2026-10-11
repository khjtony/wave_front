"""T2: French `resist` in 1936Q1 keeps the state inside V_WEST.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "T2",
    "from_state": "1936Q1",
    "claim": (
        "if France plays `resist`, German `withdraw` is available and the state stays inside V_WEST"
    ),
    "expected": "1936Q1 ∈ V_WEST under the `resist` branch",
    "sources": "Kershaw; Tooze",
}


@pytest.mark.skip(reason="model not built: phase 1 (ww2 v0)")
def test_T02():
    """Placeholder until models/ww2/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
