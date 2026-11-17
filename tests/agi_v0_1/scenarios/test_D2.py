"""D2, registered 2026-11-14 in docs/agi_v0_1.md section 5 before any v0.1 claim was run."""

from tests.agi_v0_1.claims import least_joint
from tests.agi_v0_1.common import OBJECTIVES, Parts, first_sight, need

CLAIM = {
    "id": "D2",
    "from_state": "`s₀`, within 24 ticks",
    "claim": (
        "the least joint effort of `H` and `L` on a play to `DISEMPOWERMENT` is 0 under every "
        "objective under which it is reachable within the bound: the lag slows the slide and "
        "does not price it (scores of record, docs/agi_effort.md)"
    ),
    "expected": "0 under each objective that reaches it",
}


def check(objective: str):
    found = least_joint(objective, "DISEMPOWERMENT")
    need(found is not None, "unreachable within the bound")
    need(found[0] == 0, f"effort {found[0]} in {found[1]} quarters: {found[2]}")
    return {"effort": found[0], "ticks": found[1], "play": found[2]}


@first_sight
def test_D2():
    p = Parts("D2")
    for objective in OBJECTIVES:
        p.check(objective, lambda o=objective: check(o))
    p.finish()
