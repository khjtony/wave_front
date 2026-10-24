"""V9: Negative controls on cw_v1 (regression of C12).

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V9a. The readings the model step must fix before first sight are listed in
section 9.4.
"""

from pathlib import Path

import pytest

CLAIM = {
    "id": "V9",
    "from_state": "various",
    "claim": (
        "on cw_v1, C12 as registered: negative controls: a United States preventive strike "
        "in the early 1950s needs exactly one relaxation (it was debated and rejected, so it "
        "is not absurd); a Soviet conventional invasion of Western Europe in the 1980s needs "
        "2 or more; a negotiated merger of the blocs needs 3 or more; `ACCIDENTAL_WAR` is "
        "reachable with zero relaxations and forceable by no coalition"
    ),
    "expected": "as stated, read as content controls (H6)",
    "sources": "Trachtenberg 1999; Sagan 1993; regression of C12",
}

BUILT = (Path(__file__).resolve().parents[3] / "models" / "cw" / "v1.py").exists()


@pytest.mark.skipif(not BUILT, reason="cw_v1 not built")
def test_V9():
    raise NotImplementedError(CLAIM["id"])
