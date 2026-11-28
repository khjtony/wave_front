"""Y4, registered 2026-11-27 in docs/agi_v0_5.html section 8 before any v0.5 rule was written."""

from tests.agi_v0_5.claims import shortest
from tests.agi_v0_5.common import DEFAULT, OBJECTIVES, Parts, first_sight, need

CLAIM = {
    "id": "Y4",
    "from_state": "S0, within 36 steps, the registered build",
    "claim": (
        "the shorter study still has its good ending: under `aligned` a path reaches "
        "`COEXIST` at the last step, the end of 2032. Whether one exists under each other "
        "goal is reported"
    ),
    "expected": "reachable under `aligned`, at step 36",
}


def coexist(objective: str, must: bool):
    found = shortest(objective, "COEXIST", DEFAULT)
    if must:
        need(found is not None and found[0] == 36, f"predicted a path of 36 steps: {found}")
    return {"steps": None if found is None else found[0]}


@first_sight
def test_Y4():
    p = Parts("Y4")
    p.check("COEXIST is reached at step 36, aligned", lambda: coexist("aligned", True))
    for o in OBJECTIVES[1:]:
        p.report(f"COEXIST, {o}", lambda o=o: coexist(o, False))
    p.finish()
