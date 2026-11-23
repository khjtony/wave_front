"""X7, registered 2026-11-23 in docs/agi_v0_4.html section 4, after the quick claims and before any kernel reading on the variant with both AI systems."""

from tests.agi_v0_4.common import DEFAULT, Parts, first_sight, need
from tests.agi_v0_4.kernels import membership

CLAIM = {
    "id": "X7",
    "from_state": "S0, the registered variant with both AI systems",
    "claim": (
        "under `expansionist` and under `self_preserving`, S0 is outside "
        "`⟨⟨H⟩⟩□¬CROWDED_OUT`: with a second system that no pause reaches, governments "
        "alone cannot guarantee that humans are never crowded out. "
        "`⟨⟨H, L⟩⟩□¬CROWDED_OUT` is reported"
    ),
    "expected": "outside under both goals",
}
GOALS = ("expansionist", "self_preserving")


def reading(coalition, objective, want=None):
    found = membership(DEFAULT, coalition, "not:CROWDED_OUT", only=(objective,))
    if want is not None:
        need(found["inside"][objective] is want, found)
    return found


@first_sight
def test_X7():
    p = Parts("X7")
    for o in GOALS:
        p.kernel(f"S0 is outside ⟨⟨H⟩⟩□¬CROWDED_OUT, {o}", lambda o=o: reading(("H",), o, False))
    for o in GOALS:
        p.kernel_report(f"governments with companies, {o}", lambda o=o: reading(("H", "L"), o))
    p.finish()
