"""C10: After 1965, further increases in `nuke` do not change kernel membership.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "C10",
    "from_state": "each year from 1965",
    "claim": (
        "once both principals hold survivable second strike, further increases in "
        "`nuke` do not change kernel membership; `oversight` and `belief` do"
    ),
    "expected": (
        "the sensitivity report (Q7) ranks `nuke` below `oversight` and `belief` after "
        "1965 and above them before"
    ),
    "sources": "Schelling 1966; Kristensen and Norris series",
}


@pytest.mark.skip(reason="model not built: phase 3 (cw v0)")
def test_C10():
    """Placeholder until models/cw/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
