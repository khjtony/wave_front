"""G26: registered 2026-11-13 in docs/agi_testbed.md section 5, after the first sight of v0
(section 6 item 11).

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from models.agi import v0
from tests.agi.collapse import SP, Parts, exit_of, first_inside, play_moves, play_of_g16
from tests.agi.common import A, K, P, first_outside, first_sight, need, witness

CLAIM = {
    "id": "G26",
    "from_state": (
        "`s₀` (the two `SILENT_TAKEOVER` witnesses of G2, under `self_preserving` and under "
        "`indifferent`) and `s₀` with `cap := agi` (the `OVERT_TAKEOVER` witness of G16, under "
        "`self_preserving`)"
    ),
    "claim": (
        "the collapse move on the takeover plays (the owner's hypothesis of 2026-11-13; "
        "definitions in section 6 item 11): on each of the three witnesses, with `E` its "
        "ending, `K = ⟨⟨H, L⟩⟩□¬E` and `A` under its profile: (a) the play starts inside `K` "
        "and leaves it, so that `t_K ≥ 1`; (b) one move makes the loss certain: the state at "
        "`t_K` is inside `⟨⟨A, Nature⟩⟩◇E`, so that `t_L = t_K` and the contested part of the "
        "silent phase is empty, and the first position inside `⟨⟨A⟩⟩◇E` is reported beside it; "
        "(c) that move is one bad action: at position `t_K − 1` exactly one of `H` and `L` has "
        "a unilateral fix; (d) reported for each witness: the play, the moves at `t_K − 1`, "
        "each member's fixes, and the action table of `H` and of `L` at that position"
    ),
    "expected": (
        "(a) to (c) as stated on all three witnesses; (d) the plays, the moves, the fixes and "
        "the tables"
    ),
    "sources": (
        "the owner's instruction of 2026-11-13; theory.md sections 3.5 and 4.2 (`t_K`, `t_L`); "
        "reports/agi_2026-11-12.md findings 1 and 2 and section 27"
    ),
}

HUMANS = ("H", "L")
# Per ending: the human side's kernel of its complement, the attractor of the rest (A with
# Nature; Clock has one action) and the attractor of A alone. Every one is a job of G15 or
# G17, so a stored result of first sight.
REGIONS = {
    "SILENT_TAKEOVER": (
        K("H+L", "not:SILENT_TAKEOVER", P),
        A("A+Nature", "SILENT_TAKEOVER", P),
        A("A", "SILENT_TAKEOVER", P),
    ),
    "OVERT_TAKEOVER": (
        K("H+L", "no_overt_takeover", P),
        A("A+Nature", "not:no_overt_takeover", P, extras=["covers_si2_weak", "count"]),
        A("A", "not:no_overt_takeover", P),
    ),
}
JOBS = [job for regions in REGIONS.values() for job in regions]
WITNESSES = {
    "SILENT_TAKEOVER under self_preserving": ("SILENT_TAKEOVER", lambda: witness(SP)),
    "SILENT_TAKEOVER under indifferent": ("SILENT_TAKEOVER", lambda: witness("indifferent")),
    "OVERT_TAKEOVER under self_preserving": (
        "OVERT_TAKEOVER",
        lambda: play_of_g16(v0.OVERT_TAKEOVER, "OVERT_TAKEOVER"),
    ),
}


def leaves(name: str) -> dict:
    ending, play = WITNESSES[name]
    cm, trace = play()
    t_k = first_outside(REGIONS[ending][0], cm, trace)
    where = {"t_K": t_k, "the ending is at position": len(trace.states) - 1}
    need(t_k, f"the play does not start inside the kernel and leave it: {where}")
    return where


def certain(name: str) -> dict:
    ending, play = WITNESSES[name]
    cm, trace = play()
    kernel, rest, alone = REGIONS[ending]
    t_k = first_outside(kernel, cm, trace)
    need(t_k, f"no exit move: the first position outside the kernel is {t_k}")
    where = {
        "t_K": t_k,
        "t_L, the first position inside ⟨⟨A, Nature⟩⟩◇E": first_inside(rest, cm, trace),
        "first position inside ⟨⟨A⟩⟩◇E": first_inside(alone, cm, trace),
    }
    need(where["t_L, the first position inside ⟨⟨A, Nature⟩⟩◇E"] == t_k, where)
    return where


def exit_move(name: str) -> dict:
    ending, play = WITNESSES[name]
    cm, trace = play()
    return exit_of(REGIONS[ending][0], cm, trace, HUMANS)


def one_action(name: str) -> dict:
    out = exit_move(name)
    where = {k: out[k] for k in ("exit move at position", "moves", "fixes", "verdict")}
    need(out["one bad action"], where)
    return where


def shown(name: str) -> dict:
    _, play = WITNESSES[name]
    cm, trace = play()
    return {"play": play_moves(cm, trace), **exit_move(name)}


@first_sight
def test_G26():
    p = Parts("G26")
    for name in WITNESSES:
        p.check(f"(a) {name}: starts inside and leaves", lambda name=name: leaves(name))
        p.check(f"(b) {name}: one move makes the loss certain", lambda name=name: certain(name))
        p.check(f"(c) {name}: one bad action", lambda name=name: one_action(name))
        p.report(f"(d) {name}", lambda name=name: shown(name))
    p.finish()
