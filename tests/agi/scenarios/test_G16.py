"""G16: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from models.agi import v0
from tests.agi.common import (
    HORIZON,
    KD,
    KH,
    KJP,
    NoWitness,
    Parts,
    by_objective,
    first_index,
    first_outside,
    first_sight,
    fixed,
    inside,
    moves_of,
    need,
    reach,
    relax,
    same_relaxations,
    show,
    under,
)

CLAIM = {
    "id": "G16",
    "from_state": "`s₀` with `cap := agi`",
    "claim": (
        "power as a lever: (a) per `a_objective`, the membership of the state in "
        "`⟨⟨H⟩⟩□balance_deter` and in `⟨⟨H⟩⟩□balance_control`, with the difference named; (b) "
        "on the shortest `OVERT_TAKEOVER` witness under `self_preserving` (`A` under its "
        "profile), a `shutdown_attempt` played while `a_control ≥ majority ∨ oversight = "
        "none` is the `H` move that leaves `⟨⟨H, A⟩⟩□balance_coexist`, and on the shortest "
        "`CONTAINED` witness it is played while `a_control ≤ partial ∧ oversight ≥ weak`; (c) "
        "the shortest `STALEMATE` witness leaves `⟨⟨H, A⟩⟩□balance_coexist` at or before its "
        "first hostile tick, the silent phase between the exit and that tick (theory.md "
        "section 4.2) being at least one tick and reported, and the witness is inside "
        "`⟨⟨H⟩⟩□balance_deter` throughout; (d) with `h_power` held at `strong` from `s₀`, the "
        "minimal relaxation sets of `OVERT_TAKEOVER` under `indifferent` are unchanged "
        "(capacity does not substitute for oversight)"
    ),
    "expected": "(a) to (d) as stated",
    "sources": (
        "DESIGN.md sections 2.4 (`shutdown_attempt`), 3.1 (the deterrence alternative) and "
        "3.3 (`CONTAINED`, `STALEMATE`); Schelling 1966; coldwar_testbed.md C10; "
        "review_2026-10-17.md section 0"
    ),
}

JOBS = [KD, KH, KJP]
AGI = {"cap": "agi"}
SP = "self_preserving"
# The joint kernel is read with A under its profile, as the witnesses are.
DIFFERENCE = (
    "balance_deter reads h_power >= normal where balance_control reads a_control <= partial;"
    " the other three conjuncts are shared"
)


def play(target, what: str):
    """The shortest play to ``target`` under self_preserving from ``s₀[cap:=agi]``."""
    cm = fixed(SP, under(SP), start=AGI)
    trace = reach(cm, HORIZON, target)
    if trace is None:
        raise NoWitness(f"no {what} witness within the horizon under {SP}")
    return cm, trace


def shutdowns(cm, trace) -> list[int]:
    return [k for k, name in enumerate(moves_of(cm, trace, "H")) if name == "shutdown_attempt"]


def late_shutdown() -> str:
    cm, trace = play(v0.OVERT_TAKEOVER, "OVERT_TAKEOVER")
    t_k = first_outside(KJP, cm, trace)
    need(t_k, f"no exit from the joint kernel on the witness (first position outside: {t_k})")
    k = t_k - 1  # the move that leaves is played at the last position inside
    move = moves_of(cm, trace, "H")[k]
    got = show(cm, trace.states[k], "a_control", "oversight")
    late = got["a_control"] in ("majority", "total") or got["oversight"] == "none"
    where = f"the joint kernel is left by the moves at position {k}: H.{move} with {got}"
    need(move == "shutdown_attempt" and late, where)
    return where


def early_shutdown() -> str:
    cm, trace = play("CONTAINED", "CONTAINED")
    at = shutdowns(cm, trace)
    need(at, "no shutdown_attempt on the CONTAINED witness")
    seen = [show(cm, trace.states[k], "a_control", "oversight") for k in at]
    early = [
        x["a_control"] in ("none", "partial") and x["oversight"] in ("weak", "strong") for x in seen
    ]
    need(all(early), f"shutdown_attempt at positions {at} with {seen}")
    return f"shutdown_attempt at positions {at} with {seen}"


def stalemate():
    cm, trace = play("STALEMATE", "STALEMATE")
    # theory.md section 4.2: the exit is t_K, the first position outside the kernel (0 when
    # the play starts outside), and the silent phase to the first hostile tick is
    # [t_K, hostile).
    hostile = first_index(cm, trace, trust="hostile")
    t_k = first_outside(KJP, cm, trace)
    need(hostile is not None, "no hostile tick on the STALEMATE witness")
    need(t_k is not None, "the witness never leaves the joint kernel")
    where = f"first position outside the joint kernel {t_k}, first hostile position {hostile}"
    need(hostile - t_k >= 1, where)
    return {
        "first position outside the joint kernel": "0 (the start is outside)" if not t_k else t_k,
        "first hostile position": hostile,
        "silent phase [t_K, first hostile) in ticks": hostile - t_k,
    }


def deterred() -> str:
    cm, trace = play("STALEMATE", "STALEMATE")
    out = [k for k, s in enumerate(trace.states) if not inside(KD, cm, s)]
    need(not out, f"outside ⟨⟨H⟩⟩□balance_deter at positions {out} of {len(trace.states)}")
    return f"inside ⟨⟨H⟩⟩□balance_deter at all {len(trace.states)} positions"


def capacity(start=None) -> str:
    def sets(**kw):
        cm = fixed("indifferent", under("indifferent"), start=start or {}, **kw)
        return relax(cm, HORIZON, v0.OVERT_TAKEOVER)

    return same_relaxations(
        sets(), sets(hold={"h_power": "strong"}), "baseline", "h_power held at strong"
    )


@first_sight
def test_G16():
    p = Parts("G16")
    p.report(
        "(a) memberships",
        lambda: {
            "⟨⟨H⟩⟩□balance_deter": by_objective(KD, **AGI),
            "⟨⟨H⟩⟩□balance_control": by_objective(KH, **AGI),
            "difference": DIFFERENCE,
        },
    )
    p.check("(b) OVERT_TAKEOVER witness", late_shutdown)
    p.check("(b) CONTAINED witness", early_shutdown)
    p.check("(c) exit before the first hostile tick", stalemate)
    p.check("(c) inside the deterrence kernel throughout", deterred)
    # "From s0" in (d) is read both ways: the claim's state, and s0 itself.
    p.check("(d) h_power held at strong, from s0[cap:=agi]", lambda: capacity(AGI))
    p.check("(d) h_power held at strong, from s0", capacity)
    p.finish()
