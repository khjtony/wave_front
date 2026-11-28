"""Y2, registered 2026-11-27 in docs/agi_v0_5.html section 8 before any v0.5 rule was written."""

from tests.agi_v0_5.claims import shortest
from tests.agi_v0_5.common import DEFAULT, OBJECTIVES, Parts, first_sight, need

CLAIM = {
    "id": "Y2",
    "from_state": "S0, within 36 steps, the registered build",
    "claim": (
        "on the two-month clock a shortest path to a takeover has at least as many steps as "
        "it had quarters and at most one and a half times as many, so it never arrives "
        "later in the calendar and may arrive up to a third sooner: `OPEN_TAKEOVER` in 10 "
        "to 15 steps under every goal; `SILENT_TAKEOVER` none under `aligned` and "
        "`truth_seeking`, 10 to 15 steps under `self_preserving` and `expansionist`, 7 to 11 "
        "under `indifferent`"
    ),
    "expected": "10 to 15 each; none, 10 to 15, none, 7 to 11, 10 to 15",
}
SILENT = {
    "aligned": None,
    "self_preserving": (10, 15),
    "truth_seeking": None,
    "indifferent": (7, 11),
    "expansionist": (10, 15),
}


def length(objective: str, ending: str, want):
    found = shortest(objective, ending, DEFAULT)
    got = None if found is None else found[0]
    ok = got is None if want is None else got is not None and want[0] <= got <= want[1]
    need(ok, f"{got} steps, predicted {want}: {found}")
    return {"steps": got, "months": None if got is None else 2 * got}


@first_sight
def test_Y2():
    p = Parts("Y2")
    for o in OBJECTIVES:
        p.check(
            f"shortest OPEN_TAKEOVER in 10 to 15 steps, {o}",
            lambda o=o: length(o, "OPEN_TAKEOVER", (10, 15)),
        )
        p.check(
            f"shortest SILENT_TAKEOVER, {o}", lambda o=o: length(o, "SILENT_TAKEOVER", SILENT[o])
        )
    p.finish()
