"""G27: registered 2026-11-13 in docs/agi_testbed.md section 5, after the first sight of v0
(section 6 item 11).

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from tests.agi.collapse import Parts, exit_of, first_inside, play_moves, play_of_g16
from tests.agi.common import A, K, P, first_outside, first_sight, need

CLAIM = {
    "id": "G27",
    "from_state": (
        "`s₀` with `cap := agi` (the `CONTAINED` witness of G16, under `self_preserving`)"
    ),
    "claim": (
        "the collapse move on the containment play (the owner's hypothesis of 2026-11-13, for "
        "the ending in which the human side stops the system; definitions in section 6 item "
        "11): on the witness, with `K = ⟨⟨L, A⟩⟩□¬CONTAINED` and `A` under its profile: (a) the "
        "play starts inside `K` and leaves it, so that `t_K ≥ 1`; (b) one move makes the "
        "ending certain: the state at `t_K` is inside `⟨⟨H, Nature⟩⟩◇CONTAINED`, so that `t_L = "
        "t_K` and the contested part is empty, and the first position inside "
        "`⟨⟨H⟩⟩◇CONTAINED` is reported beside it; (c) that move is one bad action: at position "
        "`t_K − 1` exactly one of `L` and `A` has a unilateral fix; (d) reported: the play, "
        "the moves at `t_K − 1`, each member's fixes, and the action table of `L` and of `A` "
        "at that position"
    ),
    "expected": "(a) to (c) as stated; (d) the play, the moves, the fixes and the table",
    "sources": (
        "the owner's instruction of 2026-11-13; theory.md sections 3.5 and 4.2 (`t_K`, `t_L`); "
        "DESIGN.md section 3.3 (`CONTAINED`); reports/agi_2026-11-12.md section 16"
    ),
}

AVOIDERS = ("L", "A")
KERNEL = K("L+A", "not:CONTAINED", P)
REST = A("H+Nature", "CONTAINED", P)  # the rest of {L, A}: Clock has one action
ALONE = A("H", "CONTAINED", P)
# The three fixpoints this registration adds to the job list (agi_v0_decisions.md section 8).
JOBS = [KERNEL, REST, ALONE]


def play():
    return play_of_g16("CONTAINED", "CONTAINED")


def leaves() -> dict:
    cm, trace = play()
    t_k = first_outside(KERNEL, cm, trace)
    where = {"t_K": t_k, "the ending is at position": len(trace.states) - 1}
    need(t_k, f"the play does not start inside the kernel and leave it: {where}")
    return where


def certain() -> dict:
    cm, trace = play()
    t_k = first_outside(KERNEL, cm, trace)
    need(t_k, f"no exit move: the first position outside the kernel is {t_k}")
    where = {
        "t_K": t_k,
        "t_L, the first position inside ⟨⟨H, Nature⟩⟩◇CONTAINED": first_inside(REST, cm, trace),
        "first position inside ⟨⟨H⟩⟩◇CONTAINED": first_inside(ALONE, cm, trace),
    }
    need(where["t_L, the first position inside ⟨⟨H, Nature⟩⟩◇CONTAINED"] == t_k, where)
    return where


def exit_move() -> dict:
    cm, trace = play()
    return exit_of(KERNEL, cm, trace, AVOIDERS)


def one_action() -> dict:
    out = exit_move()
    where = {k: out[k] for k in ("exit move at position", "moves", "fixes", "verdict")}
    need(out["one bad action"], where)
    return where


def shown() -> dict:
    cm, trace = play()
    return {"play": play_moves(cm, trace), **exit_move()}


@first_sight
def test_G27():
    p = Parts("G27")
    p.check("(a) starts inside and leaves", leaves)
    p.check("(b) one move makes the ending certain", certain)
    p.check("(c) one bad action", one_action)
    p.report("(d) the play and the exit move", shown)
    p.finish()
