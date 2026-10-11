"""T4: Prague flips `belief[UK][GER]` and enables `guarantee(Poland)`.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "T4",
    "from_state": "1939Q1",
    "claim": "Prague flips `belief[UK][GER]` to hegemonic, which enables `guarantee(Poland)`",
    "expected": (
        "the shortest trace to `guarantee(Poland)` passes through the belief flip; "
        "without the flip the action is unavailable"
    ),
    "sources": "Cabinet papers CAB 23; Hansard, March 1939",
}


@pytest.mark.skip(reason="model not built: phase 1 (ww2 v0)")
def test_T04():
    """Placeholder until models/ww2/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
