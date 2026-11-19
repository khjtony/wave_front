"""F6, registered 2026-11-18 in docs/agi_v0_3.html section 5 before any v0.3 guard was written."""

from tests.agi_v0_3.common import DEFAULT, OBJECTIVES, Parts, first_sight, need
from tests.agi_v0_3.kernels import membership

CLAIM = {
    "id": "F6",
    "from_state": "`s₀`, the registered build; then the same under `no_nationalize`",
    "claim": (
        "(a) `s₀` is inside `⟨⟨H, L⟩⟩□balance_control` under every objective of `A`; (b) "
        "with governments never nationalizing it is outside under every objective (`A` "
        "under its profile)"
    ),
    "expected": "(a) inside under every objective; (b) outside under every objective",
}
JOINT = ("H", "L")


def inside(objective: str):
    found = membership(DEFAULT, JOINT, "balance_control")
    need(found["inside"][objective], found)
    return found


def outside(objective: str):
    found = membership(DEFAULT, JOINT, "balance_control", ("no_nationalize",))
    need(not found["inside"][objective], found)
    return found


@first_sight
def test_F6():
    p = Parts("F6")
    for o in OBJECTIVES:
        p.kernel(f"(a) s₀ is inside ⟨⟨H, L⟩⟩□balance_control, {o}", lambda o=o: inside(o))
    for o in OBJECTIVES:
        p.kernel(f"(b) outside it under no_nationalize, {o}", lambda o=o: outside(o))
    p.finish()
