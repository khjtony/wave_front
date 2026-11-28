"""Y3, registered 2026-11-27 in docs/agi_v0_5.html section 8 before any v0.5 rule was written."""

from tests.agi_v0_5.claims import PEACEFUL, shortest, shortest_keeping
from tests.agi_v0_5.common import DEFAULT, SMALL, Parts, first_sight, need

CLAIM = {
    "id": "Y3",
    "from_state": "S0, within 36 steps, the small variant (the registered one beside)",
    "claim": (
        "the study to the end of 2032 is long enough for people to be crowded out without "
        "a hostile act: under `expansionist` a path to `CROWDED_OUT` exists on which "
        "relations are never hostile and the frontier AI system takes no control, and the "
        "shortest has 20 to 30 steps. The shortest path on the registered build with the "
        "open system is reported"
    ),
    "expected": "a peaceful path exists; 20 to 30 steps",
}


def peaceful():
    found = shortest_keeping("expansionist", "CROWDED_OUT", PEACEFUL, SMALL)
    need(found is not None, "no peaceful path to CROWDED_OUT within 36 steps")
    need(20 <= found[0] <= 30, f"{found[0]} steps, predicted 20 to 30: {found[1]}")
    return {"steps": found[0], "months": 2 * found[0], "path": found[1]}


@first_sight
def test_Y3():
    p = Parts("Y3")
    p.check("a peaceful path to CROWDED_OUT, 20 to 30 steps", peaceful)
    p.report(
        "shortest CROWDED_OUT with the open system",
        lambda: shortest("expansionist", "CROWDED_OUT", DEFAULT),
    )
    p.finish()
