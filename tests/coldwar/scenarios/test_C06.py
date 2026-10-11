"""C6: Replayed `belief[USA][USSR].force` exceeds hindsight `nuke[USSR]`, 1957 to 1961.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

CLAIM = {
    "id": "C6",
    "from_state": "1957 to 1961, annual replay",
    "claim": (
        "the replayed `belief[USA][USSR].force` from dated estimates and press exceeds "
        "the hindsight `nuke[USSR]`; analysis from the replay snapshot shows more "
        "adversarial reachability than from the hindsight snapshot; the gap closes "
        "within one year of `intel[USA] = overhead_reconnaissance` (1960 to 1961)"
    ),
    "expected": "as stated; the closing is driven by `intel`, not by any force change",
    "sources": "the NIE series (CIA CREST); Gaddis 2005; Preble 2004",
}


@pytest.mark.skip(reason="model not built: phase 3 (cw v0)")
def test_C06():
    """Placeholder until models/cw/v0.py exists. Will assert CLAIM['expected']."""
    raise NotImplementedError
