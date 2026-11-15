"""D3, registered 2026-11-14 in docs/agi_v0_1.md section 5 before any v0.1 claim was run."""

from tests.agi_v0_1.claims import least_joint, shortest
from tests.agi_v0_1.common import Parts, first_sight, need

CLAIM = {
    "id": "D3",
    "from_state": "`s₀`, within 24 ticks, under `indifferent`",
    "claim": (
        "(a) the shortest play to `SILENT_TAKEOVER` under `indifferent` is longer than v0's "
        "(computed beside, 7 quarters on record); (b) its least joint effort of `H` and `L` "
        "is still 0"
    ),
    "expected": "(a) longer than v0's; (b) 0",
}


def longer():
    new = shortest("indifferent", "SILENT_TAKEOVER")
    old = shortest("indifferent", "SILENT_TAKEOVER", "v0")
    need(new is not None, "unreachable within the bound")
    need(old is not None, "v0: unreachable within the bound")
    need(new[0] > old[0], f"v0.1 {new[0]} against v0 {old[0]}: {new[1]}")
    return {"v0.1": new[0], "v0": old[0], "play": new[1]}


def free():
    found = least_joint("indifferent", "SILENT_TAKEOVER")
    need(found is not None, "unreachable within the bound")
    need(found[0] == 0, f"effort {found[0]}: {found[2]}")
    return {"effort": 0, "ticks": found[1], "play": found[2]}


@first_sight
def test_D3():
    p = Parts("D3")
    p.check("(a) longer than v0", longer)
    p.check("(b) still free for H and L", free)
    p.finish()
