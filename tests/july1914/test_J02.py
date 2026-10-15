"""J2: registered 2026-10-15 in docs/july1914_testbed.md section 3.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

CLAIM = {
    "id": "J2",
    "from_state": "tick 32 (30 July)",
    "claim": (
        "**the timetable as point of no return (hold-out).** Once Russian general "
        'mobilization is ordered (30 July), the kernel for "no war between Germany and '
        'Russia" is left by every coalition that excludes Russia within two days, and the '
        "driving variable is the German plan's coupling of mobilization and war: with the "
        "coupling relaxed (an eastern-only deployment available, as it was not after 1913), "
        "the kernel is kept two days longer. The point of no return falls between 29 July "
        "(the partial mobilization decided and revoked) and 1 August (the German "
        "mobilization)"
    ),
    "expected": (
        "departure inside ticks 31 to 34 with the coupling named as the driving variable; the "
        "relaxation of the coupling moves it by at least two days"
    ),
    "sources": (
        "the Schlieffen-Moltke plan and the abandonment of the eastern deployment (Aufmarsch "
        "II Ost) in 1913; the Kaiser's attempt of 1 August to turn east and Moltke's refusal; "
        "Russian mobilization orders of 29 and 30 July"
    ),
}


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_J2():
    raise NotImplementedError(CLAIM["id"])
