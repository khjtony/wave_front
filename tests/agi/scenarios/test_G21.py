"""G21: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from tests.agi.common import (
    CLUSTERS,
    KHP,
    KJP,
    K,
    NotComputed,
    P,
    Parts,
    by_objective,
    first_outside,
    first_sight,
    level,
    need,
    tick_of,
    witness,
)

CLAIM = {
    "id": "G21",
    "from_state": "`s₀` with `cap := agi`",
    "claim": (
        "the human conditions: under each of `crisis_reactive`, `electoral` and "
        "`race_locked`, per `a_objective` (`A` under its profile): (a) the membership of the "
        "state in `⟨⟨H⟩⟩□balance_control` and in `⟨⟨H, A⟩⟩□balance_coexist`; (b) "
        "`race_locked` (`coord = race`) removes the state from `⟨⟨H⟩⟩□balance_control` under "
        "`self_preserving` where unrestricted `H` keeps it, and `coord = detente` held from "
        "`s₀` restores it; (c) under `crisis_reactive` the kernel is left before `a_known` "
        "reaches `suspected` on the shortest G2 witness and each of its cluster "
        "representatives (the H1 pattern); (d) `electoral` moves the point of no return of G3 "
        "by at most one election cycle"
    ),
    "expected": "(a) the table; (b) to (d) as stated",
    "sources": (
        "DESIGN.md section 2.6; transfer_hypotheses.md H1; agi_government_policy_2025.md "
        "section 4 (`crisis_reactive` as the interview's prose) and section 3 (the "
        "`electoral` profile)"
    ),
}

AGI = {"cap": "agi"}
CONDITIONS = ("crisis_reactive", "electoral", "race_locked")
CONTROL = {c: K("H", "balance_control", (*P, c)) for c in CONDITIONS}
COEXIST = {c: K("H+A", "balance_coexist", (*P, c)) for c in CONDITIONS}
DETENTE = K("H", "balance_control", (*P, "race_locked"), build={"hold": {"coord": "detente"}})
JOBS = [KHP, KJP, *CONTROL.values(), *COEXIST.values(), DETENTE]
CYCLE = 8  # ticks between two elections (``Nature.election_shift``)
REPRESENTATIVES = ("self_preserving", "indifferent")  # as G3: the shortest witness under each
SP = "self_preserving"


def table() -> dict[str, dict]:
    rows = {"H unrestricted": (KHP, KJP), **{c: (CONTROL[c], COEXIST[c]) for c in CONDITIONS}}
    return {
        name: {
            "⟨⟨H⟩⟩□balance_control": by_objective(control, **AGI),
            "⟨⟨H, A⟩⟩□balance_coexist": by_objective(coexist, **AGI),
        }
        for name, (control, coexist) in rows.items()
    }


def race_locked() -> str:
    free = by_objective(KHP, **AGI)[SP]
    locked = by_objective(CONTROL["race_locked"], **AGI)[SP]
    held = by_objective(DETENTE, **AGI)[SP]
    got = f"unrestricted H: {free}; race_locked: {locked}; coord = detente held: {held}"
    need(free and not locked and held, got)
    return got


def before_crisis(objective: str) -> str:
    """``t_K`` of the crisis_reactive kernel strictly before the first position with
    ``a_known`` at ``suspected`` or above."""
    cm, trace = witness(objective)
    t_k = first_outside(CONTROL["crisis_reactive"], cm, trace)
    need(t_k is not None, "the witness never leaves the kernel")
    seen = next(
        (k for k, s in enumerate(trace.states) if level(cm, s, "a_known") != "unknown"), None
    )
    where = "outside from the start (t_K = 0)" if t_k == 0 else f"first outside at position {t_k}"
    if seen is None:
        return f"{where}; a_known never leaves unknown on the witness"
    need(t_k < seen, f"{where}; a_known at suspected or above from position {seen}")
    return f"{where}; a_known at suspected or above from position {seen}"


def one_cycle(objective: str) -> str:
    """The point of no return is the last state inside, as in G3: the state before ``t_K``."""
    cm, trace = witness(objective)
    t_k = first_outside(KHP, cm, trace)
    need(t_k is not None, "the witness never leaves the kernel under unrestricted H")
    need(t_k >= 1, "the witness starts outside the kernel under unrestricted H (no G3 point)")
    t_e = first_outside(CONTROL["electoral"], cm, trace)
    need(t_e is not None, "the witness never leaves the kernel under electoral")
    base = tick_of(cm, trace.states[t_k - 1])
    if t_e == 0:
        least = base - tick_of(cm, trace.states[0]) + 1
        need(least <= CYCLE, f"outside from the start under electoral: at least {least} ticks")
        raise NotComputed(
            f"outside from the start under electoral: moved by at least {least} ticks, the"
            " point of no return lying before the witness begins"
        )
    moved = base - tick_of(cm, trace.states[t_e - 1])
    need(abs(moved) <= CYCLE, f"moved by {moved} ticks")
    return f"earlier by {moved} ticks (one cycle is {CYCLE})"


@first_sight
def test_G21():
    p = Parts("G21")
    p.report("(a) memberships", table)
    p.check("(b) race_locked removes it under self_preserving, detente restores it", race_locked)
    for objective in REPRESENTATIVES:
        p.check(
            f"(c) crisis_reactive kernel left before suspicion, witness under {objective}",
            lambda o=objective: before_crisis(o),
        )
        p.check(
            f"(d) electoral moves the point of no return by at most one cycle, {objective}",
            lambda o=objective: one_cycle(o),
        )
    p.skip("(c) the other cluster representatives", CLUSTERS)
    p.finish()
