"""T5: `negotiate` is available and Germany cannot force `AXIS_HEGEMONY_EUROPE`.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "T5",
    "from_state": "1940Q2",
    "claim": (
        "`negotiate` is available to the United Kingdom and `NEGOTIATED_PEACE` is "
        "reachable; under `fight_on`, Germany cannot force `AXIS_HEGEMONY_EUROPE`"
    ),
    "expected": "`⟨⟨GER⟩⟩◇AXIS_HEGEMONY_EUROPE` is false in the 1940Q2 state with `fight_on`",
    "sources": "Lukacs 1999; Overy 1995",
}


@pytest.mark.skip(reason="model not built: phase 1 (ww2 v0)")
def test_T05():
    """Placeholder until models/ww2/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
