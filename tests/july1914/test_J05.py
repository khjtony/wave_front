"""J5: registered 2026-10-15 in docs/july1914_testbed.md section 3.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "J5",
    "from_state": "tick 35 (2 August)",
    "claim": (
        "**the Belgian route as the British trigger (hold-out).** From the state of 2 August, "
        "British entry into the war is forced by the German ultimatum to Belgium: with "
        "Belgium `demanded`, GBR's war declaration becomes available and the Cabinet's "
        "commitment reaches `war` within two days whatever Germany does; without the Belgian "
        "ultimatum (a German choice the plan made unavoidable only through the coupling of "
        "J2), British entry by 4 August needs at least one relaxation, and every minimal set "
        "relaxes either the Belgian route or the naval assurance of 2 August"
    ),
    "expected": "as stated",
    "sources": (
        "the British Cabinet of 2 to 3 August; Grey's statement of 3 August; the ultimatum of "
        "4 August; the German ultimatum to Belgium of 2 August"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_J5():
    raise NotImplementedError(CLAIM["id"])
