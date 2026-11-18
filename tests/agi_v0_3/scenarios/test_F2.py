"""F2, registered 2026-11-18 in docs/agi_v0_3.html section 5 before any v0.3 guard was written."""

from tests.agi_v0_1 import claims as v01
from tests.agi_v0_3.claims import shortest
from tests.agi_v0_3.common import DEFAULT, OBJECTIVES, Parts, first_sight, need

CLAIM = {
    "id": "F2",
    "from_state": "`s₀`, within 24 ticks, the registered build",
    "claim": (
        "(a) under every objective of `A` a play to `OPEN_TAKEOVER` exists and the shortest "
        "is 10 quarters; (b) the shortest play to `SILENT_TAKEOVER` per objective is "
        "v0.1's: none under `aligned` and `truth_seeking`, 10 quarters under "
        "`self_preserving`, 7 under `indifferent` (v0.1's own, computed beside, is reported)"
    ),
    "expected": "(a) 10 quarters under every objective; (b) none, none, 10 and 7",
}
OPEN_QUARTERS = 10
SILENT = {"aligned": None, "truth_seeking": None, "self_preserving": 10, "indifferent": 7}


def open_takeover(objective: str):
    found = shortest(objective, "OPEN_TAKEOVER", DEFAULT)
    need(found is not None, "no OPEN_TAKEOVER play within the bound")
    need(found[0] == OPEN_QUARTERS, f"{found[0]} quarters: {found[1]}")
    return {"ticks": found[0], "play": found[1]}


def silent_takeover(objective: str):
    found = shortest(objective, "SILENT_TAKEOVER", DEFAULT)
    ticks = None if found is None else found[0]
    need(ticks == SILENT[objective], f"{ticks} quarters, expected {SILENT[objective]}: {found}")
    return {"ticks": ticks, "play": found and found[1]}


@first_sight
def test_F2():
    p = Parts("F2")
    for o in OBJECTIVES:
        p.check(f"(a) shortest OPEN_TAKEOVER is 10 quarters, {o}", lambda o=o: open_takeover(o))
    for o in OBJECTIVES:
        p.check(f"(b) shortest SILENT_TAKEOVER as v0.1's, {o}", lambda o=o: silent_takeover(o))
        p.report(
            f"(b) v0.1's shortest SILENT_TAKEOVER, {o}",
            lambda o=o: (v01.shortest(o, "SILENT_TAKEOVER") or [None])[0],
        )
    p.finish()
