"""J3v1: registered 2026-10-24 in docs/july1914_testbed.md section 8.3 (the 1914 v1
registration, owner's decision 2h of 2026-10-23), before any v1 guard.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature, in the v1 content of section 8.2. Do not edit the claim text
without a changelog entry in that document. Skipped until ``models/july1914/v1.py`` exists;
the model step replaces the body with the reading of the v1 decisions document.
"""

from pathlib import Path

import pytest

V1 = Path(__file__).resolve().parents[2] / "models" / "july1914" / "v1.py"

CLAIM = {
    "id": "J3v1",
    "from_state": "tick 0 to 30 (28 July)",
    "claim": (
        "**localization (hold-out), J3 as amended, re-asked on v1 unreworded (decision 5b).** A "
        "localized Austro-Serbian war (AUH at war with Serbia, no great-power mobilization) can be "
        "forced to the horizon only under `aims_GER = localize` with Russia at `deter`; read with "
        "the declaration of war required by 3 August, the pivotal coalition for keeping it "
        "localized is {GER, RUS} jointly, neither alone keeps it, and GBR is not pivotal at any "
        "tick (the model's result, registered: no British action reaches the Austro-Serbian dyad)"
    ),
    "expected": (
        "forceable from tick 0 under (localize, deter) only; pivotal coalition {GER, RUS} with the "
        "declaration by 3 August; GBR in no minimal forcing coalition at any tick"
    ),
    "sources": "J3's sources; amended 2026-10-23; re-asked on v1 2026-10-24",
}


@pytest.mark.skipif(not V1.exists(), reason="1914 v1 not built")
def test_J3v1():
    raise NotImplementedError(CLAIM["id"])
