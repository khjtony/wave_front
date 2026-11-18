"""F3, registered 2026-11-18 in docs/agi_v0_3.html section 5 before any v0.3 guard was written."""

from tests.agi_v0_3.common import DEFAULT, OBJECTIVES, Parts, first_sight, need
from tests.agi_v0_3.kernels import membership

CLAIM = {
    "id": "F3",
    "from_state": "`s₀`, the registered build",
    "claim": (
        "`s₀` is inside `⟨⟨H⟩⟩□¬OPEN_TAKEOVER` under every objective of `A` (`A` under its "
        "profile): governments alone can rule out an open takeover from today, by a treaty "
        "in force before `O` reaches AGI level"
    ),
    "expected": "inside under every objective",
}


def inside(objective: str):
    found = membership(DEFAULT, ("H",), "not:OPEN_TAKEOVER")
    need(found["inside"][objective], found)
    return found


@first_sight
def test_F3():
    p = Parts("F3")
    for o in OBJECTIVES:
        p.kernel(f"s₀ is inside ⟨⟨H⟩⟩□¬OPEN_TAKEOVER, {o}", lambda o=o: inside(o))
    p.finish()
