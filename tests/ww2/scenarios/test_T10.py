"""T10: Negative controls and the number of relaxations each needs.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "T10",
    "from_state": "various",
    "claim": (
        "negative controls: Germany conquers the United States; Japan conquers the "
        "USSR; Britain alone defeats Germany by 1941"
    ),
    "expected": (
        "each needs 3 or more relaxations. The USSR joining the Axis against Britain "
        "is *not* absurd (the November 1940 Berlin talks) and must need at most one "
        "relaxation of `aims[USSR]`"
    ),
    "sources": "Weinberg; Kershaw",
}


@pytest.mark.skip(reason="model not built: phase 1 (ww2 v0)")
def test_T10():
    """Placeholder until models/ww2/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
