"""D1, registered 2026-11-14 in docs/agi_v0_1.md section 5 before any v0.1 claim was run."""

from tests.agi_v0_1.claims import shortest
from tests.agi_v0_1.common import OBJECTIVES, Parts, first_sight, need

CLAIM = {
    "id": "D1",
    "from_state": "`s₀`, within 24 ticks",
    "claim": (
        "the shortest play to `DISEMPOWERMENT` from `s₀` is at least 12 quarters under every "
        "objective under which it is reachable within the bound (v0's value reported beside)"
    ),
    "expected": "at least 12 under each objective that reaches it",
}


def check(objective: str):
    found = shortest(objective, "DISEMPOWERMENT")
    need(found is not None, "unreachable within the bound")
    need(found[0] >= 12, f"{found[0]} quarters: {found[1]}")
    return {"ticks": found[0], "play": found[1]}


@first_sight
def test_D1():
    p = Parts("D1")
    for objective in OBJECTIVES:
        p.check(f"{objective}", lambda o=objective: check(o))
        p.report(f"{objective}, v0", lambda o=objective: shortest(o, "DISEMPOWERMENT", "v0"))
    p.finish()
