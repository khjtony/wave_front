"""X2, registered 2026-11-22 in docs/agi_v0_4.html section 4 before any v0.4 guard was written."""

from tests.agi_v0_4.claims import PEACEFUL, shortest, shortest_keeping
from tests.agi_v0_4.common import DEFAULT, SMALL, Parts, first_sight, need

CLAIM = {
    "id": "X2",
    "from_state": "S0, within 24 quarters, the small variant (the registered one beside)",
    "claim": (
        "under `expansionist` a path to `CROWDED_OUT` exists on which relations are never "
        "hostile and the frontier AI system takes no control, and the shortest such path "
        "is 20 quarters; the shortest path to `CROWDED_OUT` on the registered variant with "
        "the open system is reported. A wiring check, never a finding"
    ),
    "expected": "a peaceful path exists; 20 quarters",
}


def peaceful():
    found = shortest_keeping("expansionist", "CROWDED_OUT", PEACEFUL, SMALL)
    need(found is not None, "no peaceful path to CROWDED_OUT within 24 quarters")
    need(found[0] == 20, f"{found[0]} quarters, predicted 20: {found[1]}")
    return {"quarters": found[0], "path": found[1]}


@first_sight
def test_X2():
    p = Parts("X2")
    p.check("a peaceful path to CROWDED_OUT, 20 quarters", peaceful)
    p.report(
        "shortest CROWDED_OUT, any path, small variant",
        lambda: shortest("expansionist", "CROWDED_OUT", SMALL),
    )
    p.report(
        "shortest CROWDED_OUT with the open system",
        lambda: shortest("expansionist", "CROWDED_OUT", DEFAULT),
    )
    p.finish()
