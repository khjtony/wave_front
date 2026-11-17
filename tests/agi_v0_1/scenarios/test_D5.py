"""D5, registered 2026-11-14 in docs/agi_v0_1.md section 5; test body written 2026-11-15
before the kernel's membership at any state was read (the probe printed time and memory only).
"""

from tests.agi_v0_1.common import OBJECTIVES, Parts, first_sight, need
from tests.agi_v0_1.kernels import P, U, game, kernel, start

CLAIM = {
    "id": "D5",
    "from_state": "`s₀`",
    "claim": (
        "`s₀` is inside `⟨⟨H⟩⟩□balance_control` under at least one objective, where v0 has "
        "it outside under all four"
    ),
    "expected": "as stated",
    # Reading fixed with the test body (docs/agi_v0_1.md section 5): checked with `A` under
    # its profile (P, the objective's own restraint), the reading most favourable to `H`;
    # `A` unrestricted within its guards (U, v0's first-sight finding 1) reported beside.
}


def membership(profiles) -> dict:
    enc, f, seconds, peak = kernel(("H",), "balance_control", profiles)
    cm = game(profiles)
    out = {o: enc.holds(f, start(cm, o)) for o in OBJECTIVES}
    return {"inside": out, "seconds": seconds, "peak nodes": peak}


def check() -> dict:
    found = membership(P)
    need(any(found["inside"].values()), found)
    return found


@first_sight
def test_D5():
    p = Parts("D5")
    p.check("s₀ inside ⟨⟨H⟩⟩□balance_control under some objective, A under its profile", check)
    p.report("the same, A unrestricted", lambda: membership(U))
    p.finish()
