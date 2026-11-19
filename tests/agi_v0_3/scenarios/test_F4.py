"""F4, registered 2026-11-18 in docs/agi_v0_3.html section 5 before any v0.3 guard was written."""

from tests.agi_v0_3.common import DEFAULT, OBJECTIVES, Parts, first_sight, need
from tests.agi_v0_3.kernels import membership

CLAIM = {
    "id": "F4",
    "from_state": "`s₀`, the registered build under the profile `no_treaty`",
    "claim": (
        "with governments never proposing a treaty: (a) `s₀` is outside "
        "`⟨⟨H⟩⟩□¬OPEN_TAKEOVER` under every objective of `A`; (b) `s₀` is inside "
        "`⟨⟨H, L⟩⟩□¬OPEN_TAKEOVER` under every objective (`A` under its profile)"
    ),
    "expected": "(a) outside under every objective; (b) inside under every objective",
}
NO_TREATY = ("no_treaty",)


def alone_outside(objective: str):
    found = membership(DEFAULT, ("H",), "not:OPEN_TAKEOVER", NO_TREATY)
    need(not found["inside"][objective], found)
    return found


def joint_inside(objective: str):
    found = membership(DEFAULT, ("H", "L"), "not:OPEN_TAKEOVER", NO_TREATY)
    need(found["inside"][objective], found)
    return found


@first_sight
def test_F4():
    p = Parts("F4")
    for o in OBJECTIVES:
        p.kernel(f"(a) s₀ is outside ⟨⟨H⟩⟩□¬OPEN_TAKEOVER, {o}", lambda o=o: alone_outside(o))
    for o in OBJECTIVES:
        p.kernel(f"(b) s₀ is inside ⟨⟨H, L⟩⟩□¬OPEN_TAKEOVER, {o}", lambda o=o: joint_inside(o))
    p.finish()
