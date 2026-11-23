"""X3, registered 2026-11-22 in docs/agi_v0_4.html section 4 before any v0.4 guard was written."""

from tests.agi_v0_4.common import SMALL, Parts, first_sight, need
from tests.agi_v0_4.kernels import membership

CLAIM = {
    "id": "X3",
    "from_state": "S0, the small variant; then the same with `reclaim` off",
    "claim": (
        "under `expansionist`: (a) S0 is inside `⟨⟨H⟩⟩□¬CROWDED_OUT`; (b) with `reclaim` "
        "off it is outside. `⟨⟨H, L⟩⟩□¬CROWDED_OUT` is reported beside both"
    ),
    "expected": "(a) inside; (b) outside",
}
NO_RECLAIM = {**SMALL, "reclaim": False}
GOAL = ("expansionist",)


def reading(build, coalition, want=None):
    found = membership(build, coalition, "not:CROWDED_OUT", only=GOAL)
    if want is not None:
        need(found["inside"]["expansionist"] is want, found)
    return found


@first_sight
def test_X3():
    p = Parts("X3")
    p.kernel("(a) S0 is inside ⟨⟨H⟩⟩□¬CROWDED_OUT", lambda: reading(SMALL, ("H",), True))
    p.kernel("(b) outside it with reclaim off", lambda: reading(NO_RECLAIM, ("H",), False))
    p.kernel_report("governments with companies", lambda: reading(SMALL, ("H", "L")))
    p.kernel_report(
        "governments with companies, reclaim off", lambda: reading(NO_RECLAIM, ("H", "L"))
    )
    p.finish()
