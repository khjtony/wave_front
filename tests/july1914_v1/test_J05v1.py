"""J5v1: registered 2026-10-24 in docs/july1914_testbed.md section 8.3 (the 1914 v1
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
    "id": "J5v1",
    "from_state": "tick 35 (2 August)",
    "claim": (
        "**the Belgian route as the British trigger (hold-out), J5 re-asked on v1.** From the state"
        " of 2 August, British entry into the war is forced by the German ultimatum to Belgium: "
        "with Belgium `demanded`, GBR's war declaration becomes available and the Cabinet's "
        "commitment reaches `war` within two days whatever Germany does; without the Belgian "
        "ultimatum (a German choice the plan made unavoidable only through the coupling of J2v1), "
        "British entry by 4 August needs at least one relaxation, and every minimal set relaxes "
        "either the Belgian route or the naval assurance of 2 August"
    ),
    "expected": "as stated",
    "sources": "J5's sources",
}


@pytest.mark.skipif(not V1.exists(), reason="1914 v1 not built")
def test_J5v1():
    raise NotImplementedError(CLAIM["id"])
