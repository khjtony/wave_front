"""D4, registered 2026-11-14 in docs/agi_v0_1.md section 5 before any v0.1 claim was run."""

from tests.agi_v0_1.claims import CANCEL, first_wave_cancelled, shortest
from tests.agi_v0_1.common import OBJECTIVES, Parts, first_sight, need

CLAIM = {
    "id": "D4",
    "from_state": "`s₀`, within 24 ticks",
    "claim": (
        "cancellation, existence checks under each objective (never findings): (a) no play "
        "cancels a wave the labs start at tick 0 before it lands at tick 4, because a pause "
        "needs an alarm and a mandatory regime takes 7 quarters; (b) some play within the "
        "bound reaches a state at which a pending wave is cancelled"
    ),
    "expected": "(a) and (b) under every objective",
}


def first(objective: str):
    play = first_wave_cancelled(objective)
    need(play is None, f"a play cancels the wave of tick 0: {play}")
    return "no such play within 4 ticks"


def some(objective: str):
    found = shortest(objective, CANCEL)
    need(found is not None, "no cancellation within the bound")
    return {"tick": found[0], "play": found[1]}


@first_sight
def test_D4():
    p = Parts("D4")
    for objective in OBJECTIVES:
        p.check(f"(a) {objective}", lambda o=objective: first(o))
        p.check(f"(b) {objective}", lambda o=objective: some(o))
    p.finish()
