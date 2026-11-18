"""E4, registered 2026-11-17 in docs/agi_v0_2.html section 4 before any v0.2 guard was written."""

from tests.agi_v0_2.common import (
    NON_ALIGNED,
    K,
    Parts,
    budgeted,
    first_sight,
    fixed,
    key,
    need,
    only,
)
from tests.agi_v0_2.kernels import exit_of, membership
from wavefront.bmc.queries import reach

CLAIM = {
    "id": "E4",
    "from_state": "`s₀`, consequence C (`testing`) alone",
    "claim": (
        "outside testing: (a) on the bounded checker's shortest `SILENT_TAKEOVER` play "
        "within 24 ticks under each non-aligned objective that has one, the exit from "
        "`⟨⟨H, L⟩⟩□¬SILENT_TAKEOVER` (`A` under its profile) is one bad action and the "
        "labs', as D6 found on v0.1; (b) `s₀` is outside `⟨⟨H⟩⟩□balance_control` under every "
        "start objective (`A` under its profile), as D5 found"
    ),
    "expected": "(a) one bad action, the labs', on each play; (b) outside under every objective",
}
C = only("testing")
HL = ("H", "L")


def play(objective: str):
    def run():
        trace = reach(fixed(objective, C), K, "SILENT_TAKEOVER")
        return None if trace is None else (list(trace.states), list(trace.moves))

    return budgeted(("silent", objective, key(C)), run)


def labs_alone(objective: str):
    states, moves = play(objective)
    out = exit_of(C, HL, "not:SILENT_TAKEOVER", states, moves)
    need(out["t_K"], f"no exit move: the first position outside the kernel is {out['t_K']}")
    need(out["one bad action"] and bool(out["fixes"]["L"]) and not out["fixes"]["H"], out)
    return out


def outside():
    found = membership(C, ("H",), "balance_control")
    need(not any(found["inside"].values()), found)
    return found


@first_sight
def test_E4():
    p = Parts("E4")
    for objective in NON_ALIGNED:
        if play(objective) is None:
            p.report(f"(a) {objective}", lambda: "no SILENT_TAKEOVER play within 24 ticks")
            continue
        p.kernel(f"(a) {objective}: one bad action, the labs'", lambda o=objective: labs_alone(o))
    p.kernel("(b) s₀ outside ⟨⟨H⟩⟩□balance_control under every objective", outside)
    p.finish()
