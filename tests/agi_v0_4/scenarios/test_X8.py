"""X8, registered 2026-11-23 in docs/agi_v0_4.html section 4, after the quick claims and before any kernel reading on the variant with both AI systems."""

from tests.agi_v0_4.common import DEFAULT, Parts, first_sight, need
from tests.agi_v0_4.kernels import membership

CLAIM = {
    "id": "X8",
    "from_state": "S0 with `cap := agi`, the registered variant with both AI systems",
    "claim": (
        "under `expansionist` and under `self_preserving`, with AGI since s₀, the start is "
        "outside `⟨⟨H⟩⟩□balance_coexist`"
    ),
    "expected": "outside under both goals",
}


def reading(objective):
    found = membership(DEFAULT, ("H",), "balance_coexist", only=(objective,), cap="agi")
    need(not found["inside"][objective], found)
    return found


@first_sight
def test_X8():
    p = Parts("X8")
    for o in ("expansionist", "self_preserving"):
        p.kernel(f"outside ⟨⟨H⟩⟩□balance_coexist, {o}", lambda o=o: reading(o))
    p.finish()
