"""X4, registered 2026-11-22 in docs/agi_v0_4.html section 4 before any v0.4 guard was written."""

from tests.agi_v0_4.common import SMALL, Parts, first_sight, need
from tests.agi_v0_4.kernels import membership

CLAIM = {
    "id": "X4",
    "from_state": "S0 with `cap := agi`, the small variant; then the same with `ceiling` on",
    "claim": (
        "under `expansionist`, with AGI since s₀: (a) the start is outside "
        "`⟨⟨H⟩⟩□balance_coexist`; (b) with the agreed ceiling (`ceiling` on) it is inside"
    ),
    "expected": "(a) outside; (b) inside",
}
CEILING = {**SMALL, "ceiling": True}


def reading(build, want: bool):
    found = membership(build, ("H",), "balance_coexist", only=("expansionist",), cap="agi")
    need(found["inside"]["expansionist"] is want, found)
    return found


@first_sight
def test_X4():
    p = Parts("X4")
    p.kernel("(a) outside ⟨⟨H⟩⟩□balance_coexist", lambda: reading(SMALL, False))
    p.kernel("(b) inside it with the agreed ceiling", lambda: reading(CEILING, True))
    p.finish()
