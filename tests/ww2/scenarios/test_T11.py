"""T11: No `commit[USA] = total` before 1943 without an attack on the United States.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "T11",
    "from_state": "1941Q1",
    "claim": (
        "without an attack on the United States, `commit[USA] = total` is unreachable "
        "before 1943 under the `electoral` profile; with Nature's `attack_on_us` it is "
        "immediate"
    ),
    "expected": "as stated",
    "sources": "Gallup series; Kershaw",
}


@pytest.mark.skip(reason="model not built: phase 1 (ww2 v0)")
def test_T11():
    """Placeholder until models/ww2/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
