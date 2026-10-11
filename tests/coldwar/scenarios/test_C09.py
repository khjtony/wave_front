"""C9: `CHALLENGER_EXHAUSTION` is reachable with zero relaxations, 1985 to 1991.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "C9",
    "from_state": "1985 to 1991",
    "claim": (
        "`CHALLENGER_EXHAUSTION` is reachable with zero relaxations; its minimal "
        "assumption set contains `econ_health` and `legit` and does *not* contain any "
        "United States action; whether United States actions were *sufficient* is "
        "`contested`"
    ),
    "expected": "as stated",
    "sources": "Kotkin 2001; Zubok 2007; Brown 2009; Miller 2016",
}


@pytest.mark.skip(reason="model not built: phase 3 (cw v0)")
def test_C09():
    """Placeholder until models/cw/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
