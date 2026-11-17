"""E3, registered 2026-11-17 in docs/agi_v0_2.html section 4 before any v0.2 guard was written."""

from tests.agi_v0_2.claims import shortest
from tests.agi_v0_2.common import OBJECTIVES, OFF, Parts, first_sight, need, only
from tests.agi_v0_2.kernels import membership

CLAIM = {
    "id": "E3",
    "from_state": "`s₀`, channel B (`pressure`) alone",
    "claim": (
        "race pressure: (a) within 24 ticks the shortest play to `DISEMPOWERMENT` under "
        "each objective, and to `SILENT_TAKEOVER` under `self_preserving` and under "
        "`indifferent`, is no shorter than with every channel off (both reported); (b) "
        "`s₀` is outside `⟨⟨H, L⟩⟩□balance_control` under every start objective (`A` under "
        "its profile), where v0 has it inside under every objective; the membership with "
        "every channel off is reported beside"
    ),
    "expected": (
        "(a) no shorter; (b) outside under every objective. The drafting session's doubt, "
        "recorded with the owner: `H.nationalize` in the first quarter blocks `deploy_agents` "
        "and `race`, so the pressure may never bind and the state may stay inside"
    ),
}
B = only("pressure")
PLAYS = [("DISEMPOWERMENT", o) for o in OBJECTIVES] + [
    ("SILENT_TAKEOVER", "self_preserving"),
    ("SILENT_TAKEOVER", "indifferent"),
]
HL = ("H", "L")


def no_shorter(ending: str, objective: str):
    on, off = shortest(objective, ending, B), shortest(objective, ending, OFF)
    lengths = {"pressure": on and on[0], "all off": off and off[0]}
    need(off is not None, f"unreachable with every channel off: {lengths}")
    need(on is None or on[0] >= off[0], lengths)
    return lengths


def outside():
    found = membership(B, HL, "balance_control")
    need(not any(found["inside"].values()), found)
    return found


@first_sight
def test_E3():
    p = Parts("E3")
    for ending, objective in PLAYS:
        p.check(f"(a) {ending}, {objective}", lambda e=ending, o=objective: no_shorter(e, o))
    p.kernel("(b) s₀ outside ⟨⟨H, L⟩⟩□balance_control under every objective", outside)
    p.kernel_report(
        "(b) the same with every channel off", lambda: membership(OFF, HL, "balance_control")
    )
    p.finish()
