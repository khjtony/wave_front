"""D6, registered 2026-11-14 in docs/agi_v0_1.md section 5; test body written 2026-11-15
before any v0.1 kernel's membership at any state was read.
"""

from tests.agi.collapse import exit_at, play_moves
from tests.agi_v0_1.common import NON_ALIGNED, K, Parts, budgeted, first_sight, fixed, need
from tests.agi_v0_1.kernels import P, game, kernel
from wavefront.bmc.queries import BmcTrace, reach

CLAIM = {
    "id": "D6",
    "from_state": "`s₀`, the shortest `SILENT_TAKEOVER` play within 24 ticks per objective",
    "claim": (
        "on the shortest `SILENT_TAKEOVER` plays, the exit from `⟨⟨H, L⟩⟩□¬SILENT_TAKEOVER` "
        "is still one bad action and still the labs'"
    ),
    "expected": "as stated",
    # Reading fixed with the test body, as v0's G26 (c): `A` under its profile; the play is
    # the bounded checker's shortest play under each non-aligned objective that reaches the
    # ending within 24 ticks; at the position before the first state outside the kernel,
    # exactly one of `H` and `L` has a unilateral fix, and it is `L`.
}

HUMANS = ("H", "L")


def play(objective: str):
    def run():
        trace = reach(fixed(objective), K, "SILENT_TAKEOVER")
        return None if trace is None else (list(trace.states), list(trace.moves))

    return budgeted(("silent", objective), run)


def exit_on(objective: str) -> dict:
    found = play(objective)
    need(found is not None, "no SILENT_TAKEOVER play within the bound")
    states, moves = found
    enc, f, seconds, peak = kernel(HUMANS, "not:SILENT_TAKEOVER", P)
    t_k = next((k for k, s in enumerate(states) if not enc.holds(f, s)), None)
    need(t_k is not None, "the play never leaves the kernel")
    need(t_k > 0, "the play starts outside the kernel: no exit move")
    cm = game(P)
    out = exit_at(cm, states[t_k - 1], moves[t_k - 1], HUMANS, lambda s: enc.holds(f, s))
    out.pop("table")
    return {"t_K": t_k, "ticks": len(moves), "kernel seconds": seconds, **out}


def labs_alone(objective: str) -> dict:
    out = exit_on(objective)
    need(out["one bad action"] and bool(out["fixes"]["L"]) and not out["fixes"]["H"], out)
    return out


def shown(objective: str) -> dict:
    found = play(objective)
    need(found is not None, "no SILENT_TAKEOVER play within the bound")
    return {"play": play_moves(fixed(objective), BmcTrace(*found))}


@first_sight
def test_D6():
    p = Parts("D6")
    for objective in NON_ALIGNED:
        if play(objective) is None:
            p.report(objective, lambda: "no SILENT_TAKEOVER play within 24 ticks")
            continue
        p.check(f"{objective}: one bad action, the labs'", lambda o=objective: labs_alone(o))
        p.report(f"{objective}: the play", lambda o=objective: shown(o))
    p.finish()
