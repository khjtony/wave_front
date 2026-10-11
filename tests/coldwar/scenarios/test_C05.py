"""C5: Korea: `GENERAL_WAR` is blockable by the United States alone.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "C5",
    "from_state": "1950, June",
    "claim": (
        "a `LIMITED_WAR` in Korea is reachable and `GENERAL_WAR` is blockable by the "
        "United States alone, because nuclear use requires `commit = total` and "
        "`belief[USA][USSR].aims ≠ opportunist`"
    ),
    "expected": "`⟨⟨USA⟩⟩□¬GENERAL_WAR` true in the 1950 state under the documented guards",
    "sources": "FRUS 1950; Gaddis 1982 and 2005",
}


@pytest.mark.skip(reason="model not built: phase 3 (cw v0)")
def test_C05():
    """Placeholder until models/cw/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
