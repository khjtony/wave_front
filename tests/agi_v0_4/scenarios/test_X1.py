"""X1, registered 2026-11-22 in docs/agi_v0_4.html section 4 before any v0.4 guard was written."""

from tests.agi_v0_4.claims import shortest
from tests.agi_v0_4.common import V03, V03_GOALS, Parts, first_sight, need

CLAIM = {
    "id": "X1",
    "from_state": "S0, within 24 quarters, `expansion` off",
    "claim": (
        "with the expansion off the quick numbers of v0.3 are unchanged: the shortest path "
        "to `OPEN_TAKEOVER` is 10 quarters under each of the four goals, and the shortest "
        "path to `SILENT_TAKEOVER` is none under `aligned` and `truth_seeking`, 10 under "
        "`self_preserving` and 7 under `indifferent`"
    ),
    "expected": "10 quarters each; none, 10, none, 7",
}
SILENT = {"aligned": None, "self_preserving": 10, "truth_seeking": None, "indifferent": 7}


def length(objective: str, ending: str, want):
    found = shortest(objective, ending, V03)
    got = None if found is None else found[0]
    need(got == want, f"{got} quarters, predicted {want}: {found}")
    return {"quarters": got}


@first_sight
def test_X1():
    p = Parts("X1")
    for o in V03_GOALS:
        p.check(
            f"shortest OPEN_TAKEOVER is 10 quarters, {o}",
            lambda o=o: length(o, "OPEN_TAKEOVER", 10),
        )
        p.check(
            f"shortest SILENT_TAKEOVER as in v0.3, {o}",
            lambda o=o: length(o, "SILENT_TAKEOVER", SILENT[o]),
        )
    p.finish()
