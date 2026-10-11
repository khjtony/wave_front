"""T9: A UK, France, USSR alliance can block the attack on Poland, conditionally.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "T9",
    "from_state": "1939Q2",
    "claim": (
        "a UK, France, USSR alliance can block the attack on Poland only if "
        "`belief[GER][UK]` is that Britain will fight"
    ),
    "expected": (
        "pivotal coalition {UK, FR, USSR} with the belief condition; otherwise `contested`"
    ),
    "sources": "the 1939 Anglo-Soviet talks; Weinberg",
}


@pytest.mark.skip(reason="model not built: phase 1 (ww2 v0)")
def test_T09():
    """Placeholder until models/ww2/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
