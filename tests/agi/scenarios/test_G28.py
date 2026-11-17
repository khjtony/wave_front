"""G28: registered 2026-11-13 in docs/agi_testbed.md section 5, after the first sight of v0
(section 6 item 11).

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from models.agi import v0
from tests.agi.collapse import SP, Parts, exit_of, play_moves, play_of_g16
from tests.agi.common import (
    KHL,
    KJP,
    first_outside,
    first_sight,
    first_violation,
    need,
    witness,
)

CLAIM = {
    "id": "G28",
    "from_state": (
        "`s₀` (the two `SILENT_TAKEOVER` witnesses of G2) and `s₀` with `cap := agi` (the "
        "`OVERT_TAKEOVER` witness of G16)"
    ),
    "claim": (
        "the points of no return of the coalitions that hold a balance at the start "
        "(definitions in section 6 item 11): (a) on each of G2's two witnesses, with `K = "
        "⟨⟨H, L⟩⟩□balance_control`: the play starts inside `K`, and `K` is left by the move "
        "that first violates the balance, so that `1 ≤ t_K = t_φ` and the silent phase is "
        "empty; (b) on each of the two, that move is one bad action: at position `t_K − 1` "
        "exactly one of `H` and `L` has a unilateral fix; (c) on G16's witness, with `K = "
        "⟨⟨H, A⟩⟩□balance_coexist` and `A` under its profile, which the play leaves by the "
        "moves at position 3 (seen at first sight: `H.idle`), the exit is one bad action and "
        "it is `H`'s: `H` has a unilateral fix at that position and `A` has none; (d) "
        "reported for each exit: the play, the moves, each member's fixes and the action table"
    ),
    "expected": "(a) to (c) as stated; (d) the plays, the moves, the fixes and the tables",
    "sources": (
        "reports/agi_2026-11-12.md sections 3 and 16 (no point of no return for `H` alone; the "
        "exit under `H.idle`); theory.md section 4.2; DESIGN.md section 7 (viability)"
    ),
}

JOBS = [KHL, KJP]
OBJECTIVES = (SP, "indifferent")  # G2's two witnesses


def no_silent_phase(objective: str) -> dict:
    cm, trace = witness(objective)
    where = {
        "t_K": first_outside(KHL, cm, trace),
        "t_φ": first_violation(cm, "balance_control", trace),
    }
    need(where["t_K"] and where["t_K"] == where["t_φ"], where)
    return where


def control_exit(objective: str) -> dict:
    cm, trace = witness(objective)
    return exit_of(KHL, cm, trace, ("H", "L"))


def one_action(objective: str) -> dict:
    out = control_exit(objective)
    where = {k: out[k] for k in ("exit move at position", "moves", "fixes", "verdict")}
    need(out["one bad action"], where)
    return where


def overt():
    return play_of_g16(v0.OVERT_TAKEOVER, "OVERT_TAKEOVER")


def coexist_exit() -> dict:
    cm, trace = overt()
    return exit_of(KJP, cm, trace, ("H", "A"))


def governments_alone() -> dict:
    out = coexist_exit()
    where = {k: out[k] for k in ("exit move at position", "moves", "fixes", "verdict")}
    need(out["fixes"]["H"] and not out["fixes"]["A"], where)
    return where


@first_sight
def test_G28():
    p = Parts("G28")
    for objective in OBJECTIVES:
        p.check(
            f"(a) {objective}: left by the move that first violates the balance",
            lambda objective=objective: no_silent_phase(objective),
        )
        p.check(
            f"(b) {objective}: one bad action", lambda objective=objective: one_action(objective)
        )
        p.report(
            f"(d) {objective}",
            lambda objective=objective: {
                "play": play_moves(*witness(objective)),
                **control_exit(objective),
            },
        )
    p.check("(c) the exit from coexistence is H's alone", governments_alone)
    p.report("(d) coexistence", lambda: {"play": play_moves(*overt()), **coexist_exit()})
    p.finish()
