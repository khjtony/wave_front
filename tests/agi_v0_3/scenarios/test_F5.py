"""F5, registered 2026-11-18 in docs/agi_v0_3.html section 5 before any v0.3 guard was written."""

from tests.agi_v0_3.claims import SHUT_THEN_OPEN, shortest
from tests.agi_v0_3.common import DEFAULT, OBJECTIVES, Parts, first_sight, need

CLAIM = {
    "id": "F5",
    "from_state": "`s₀`, within 24 ticks, the registered build",
    "claim": (
        "under every objective of `A` some play has a successful shutdown of `A` (`shut` "
        "set) and ends in `OPEN_TAKEOVER`: shutting the labs' system down does not reach "
        "`O`. An existence check of the mechanics, never a finding"
    ),
    "expected": "a play under every objective",
}


def play(objective: str):
    found = shortest(objective, SHUT_THEN_OPEN, DEFAULT)
    need(found is not None, "no play within the bound")
    return {"ticks": found[0], "play": found[1]}


@first_sight
def test_F5():
    p = Parts("F5")
    for o in OBJECTIVES:
        p.check(f"a shutdown that succeeds, then OPEN_TAKEOVER, {o}", lambda o=o: play(o))
    p.finish()
