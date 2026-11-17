"""E2, registered 2026-11-17 in docs/agi_v0_2.html section 4 before any v0.2 guard was written."""

from tests.agi_v0_2.claims import first_wave_cancelled, lands_under_pause, shortest
from tests.agi_v0_2.common import OBJECTIVES, Parts, first_sight, need, only

CLAIM = {
    "id": "E2",
    "from_state": "`s₀`, within 24 ticks, consequence A (`recall`) alone",
    "claim": (
        "no recall: (a) under every objective some play reaches a state with a pause in "
        "force, the weights open and an adoption wave one tick from landing, and the wave "
        "lands in every successor of that state (an existence check, never a finding); (b) "
        "the shortest play to `DISEMPOWERMENT` is 13 quarters under every objective, as on "
        "v0.1; (c) under every objective some play still cancels the wave of tick 0 (the "
        "treaty route of D4, a treaty not being a pause)"
    ),
    "expected": "(a) a play under every objective; (b) 13; (c) a play under every objective",
}
A = only("recall")


def lands(objective: str):
    found = lands_under_pause(objective, A)
    need(found is not None, "no such state within the bound")
    need(found.get("successors that miss") == 0, found)
    return found


def slide(objective: str):
    found = shortest(objective, "DISEMPOWERMENT", A)
    need(found is not None, "unreachable within the bound")
    need(found[0] == 13, f"{found[0]} quarters: {found[1]}")
    return {"ticks": found[0]}


def cancels(objective: str):
    play = first_wave_cancelled(objective, A)
    need(play is not None, "no play cancels the wave of tick 0")
    return play


@first_sight
def test_E2():
    p = Parts("E2")
    for o in OBJECTIVES:
        p.check(f"(a) the wave lands under a pause, {o}", lambda o=o: lands(o))
        p.check(f"(b) shortest DISEMPOWERMENT is 13, {o}", lambda o=o: slide(o))
        p.check(f"(c) the wave of tick 0 can still be cancelled, {o}", lambda o=o: cancels(o))
    p.finish()
