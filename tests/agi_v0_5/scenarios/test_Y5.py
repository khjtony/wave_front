"""Y5, registered 2026-11-27 in docs/agi_v0_5.html section 8 before any v0.5 rule was written."""

from tests.agi_v0_5.common import SMALL, Parts, first_sight, need
from tests.agi_v0_5.kernels import membership

CLAIM = {
    "id": "Y5",
    "from_state": "S0, the small variant",
    "claim": (
        "under `aligned` the two readings of v0.4's small variant are unchanged on the new "
        "clock: S0 is outside `⟨⟨H⟩⟩□balance_control` and inside "
        "`⟨⟨H, L⟩⟩□balance_control`. Whether either zone can be computed on this clock is "
        "part of what is learned: the countdowns are longer"
    ),
    "expected": "outside; inside",
}


def reading(coalition, want):
    found = membership(SMALL, coalition, "balance_control", only=("aligned",))
    need(found["inside"]["aligned"] is want, found)
    return found


@first_sight
def test_Y5():
    p = Parts("Y5")
    p.kernel("governments alone keep control: outside, aligned", lambda: reading(("H",), False))
    p.kernel(
        "governments with companies keep control: inside, aligned",
        lambda: reading(("H", "L"), True),
    )
    p.finish()
