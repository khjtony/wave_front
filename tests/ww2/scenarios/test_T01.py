"""T1: Realized trajectory to 1940Q2 is reachable from the 1936Q1 snapshot.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "T1",
    "from_state": "1936Q1 snapshot",
    "claim": (
        "the realized trajectory to 1940Q2 (Rhineland, Anschluss, Munich, Prague, "
        "Pact, Poland, the fall of France) is reachable"
    ),
    "expected": "reachable with zero relaxations",
    "sources": "ICB; Weinberg; Kershaw",
}


@pytest.mark.skip(reason="model not built: phase 1 (ww2 v0)")
def test_T01():
    """Placeholder until models/ww2/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
