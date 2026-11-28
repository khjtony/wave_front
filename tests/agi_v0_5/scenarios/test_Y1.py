"""Y1, registered 2026-11-27 in docs/agi_v0_5.html section 8 before any v0.5 rule was written."""

from tests.agi_v0_5.claims import PEACEFUL, shortest, shortest_keeping
from tests.agi_v0_5.common import (
    K_V04,
    V03_GOALS,
    V04_NO_EXPANSION,
    V04_SMALL,
    Parts,
    first_sight,
    need,
)

CLAIM = {
    "id": "Y1",
    "from_state": "S0, within 24 quarters, v0.4's clock (`step_months=3`, `study_quarters=56`)",
    "claim": (
        "with v0.4's clock the quick numbers of v0.4 are unchanged: with the expansion off "
        "the shortest path to `OPEN_TAKEOVER` is 10 quarters under each of the four goals "
        "and the shortest path to `SILENT_TAKEOVER` is none under `aligned` and "
        "`truth_seeking`, 10 under `self_preserving` and 7 under `indifferent`; with the "
        "expansion on and no open system, the shortest peaceful path to `CROWDED_OUT` under "
        "`expansionist` is 20 quarters. A wiring check of the new clock"
    ),
    "expected": "10 quarters each; none, 10, none, 7; 20",
}
SILENT = {"aligned": None, "self_preserving": 10, "truth_seeking": None, "indifferent": 7}


def length(objective: str, ending: str, want):
    found = shortest(objective, ending, V04_NO_EXPANSION, K_V04)
    got = None if found is None else found[0]
    need(got == want, f"{got} quarters, predicted {want}: {found}")
    return {"quarters": got}


def peaceful():
    found = shortest_keeping("expansionist", "CROWDED_OUT", PEACEFUL, V04_SMALL, K_V04)
    need(found is not None and found[0] == 20, f"predicted 20 quarters: {found}")
    return {"quarters": found[0]}


@first_sight
def test_Y1():
    p = Parts("Y1")
    for o in V03_GOALS:
        p.check(
            f"shortest OPEN_TAKEOVER is 10 quarters, {o}",
            lambda o=o: length(o, "OPEN_TAKEOVER", 10),
        )
        p.check(
            f"shortest SILENT_TAKEOVER as in v0.4, {o}",
            lambda o=o: length(o, "SILENT_TAKEOVER", SILENT[o]),
        )
    p.check("a peaceful path to CROWDED_OUT, 20 quarters", peaceful)
    p.finish()
