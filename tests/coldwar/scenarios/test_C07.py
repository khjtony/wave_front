"""C7: Soviet first-strike-intent belief moves the state toward the boundary, 1983.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "C7",
    "from_state": "1983, November",
    "claim": (
        "the Soviet belief `belief[USSR][USA].aims = first_strike_intent` moves the "
        "state toward the boundary with *no change in any hindsight force variable*; "
        "the shortest trace to `GENERAL_WAR` from the replay snapshot is shorter than "
        "from the hindsight snapshot"
    ),
    "expected": "as stated",
    "sources": "Jones 2016; the 1990 PFIAB report (declassified 2015)",
}


@pytest.mark.skip(reason="model not built: phase 3 (cw v0)")
def test_C07():
    """Placeholder until models/cw/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
