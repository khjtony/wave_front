"""T7: The embargo makes war with Japan unavoidable within 8 ticks.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "T7",
    "from_state": "1941Q3",
    "claim": (
        "the embargo makes war with Japan unavoidable within 8 ticks unless the "
        "embargo is lifted or `aims[JPN] = status_quo`"
    ),
    "expected": (
        "minimal assumption set for `war[JPN][USA]` is exactly {embargo maintained, "
        "`aims[JPN] ≠ status_quo`}; `strike_north` reachable only with GER-JPN pact "
        "and western USSR collapsing"
    ),
    "sources": "Ike 1967; Sagan 1988; Iriye 1987; Kershaw",
}


@pytest.mark.skip(reason="model not built: phase 1 (ww2 v0)")
def test_T07():
    """Placeholder until models/ww2/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
