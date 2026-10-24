"""V10: The USSR's departure from its bloc kernel on cw_v1 (regression of C13).

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V10a. The readings the model step must fix before first sight are listed in
section 9.4.
"""

from pathlib import Path

import pytest

CLAIM = {
    "id": "V10",
    "from_state": "each year 1975 to 1989",
    "claim": (
        "on cw_v1, C13 as registered: the year the USSR leaves its own kernel (can no longer "
        "guarantee its bloc) falls between 1979 and 1989, the report names the driving "
        "variable, and the result is stable within one year under refinement; control: on "
        "the build with the PRC's decisions given to Nature the departure year is the same"
    ),
    "expected": "inside the window; the driving variable named; the control as stated",
    "sources": "Kotkin 2001; Brown 2009; Miller 2016; regression of C13",
}

BUILT = (Path(__file__).resolve().parents[3] / "models" / "cw" / "v1.py").exists()


@pytest.mark.skipif(not BUILT, reason="cw_v1 not built")
def test_V10():
    raise NotImplementedError(CLAIM["id"])
