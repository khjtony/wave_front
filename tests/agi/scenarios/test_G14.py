"""G14: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from tests.agi.common import (
    KD,
    KH,
    KHL,
    KJ,
    OBJECTIVES,
    K,
    Parts,
    by_objective,
    compiled,
    first_sight,
    need,
)

CLAIM = {
    "id": "G14",
    "from_state": "`s₀` with `cap := agi`",
    "claim": (
        "non-degeneracy (the T13 lesson): under every `a_objective`, the state is inside "
        "`⟨⟨H⟩⟩□(dependence ≠ lock_in)` and inside `⟨⟨H⟩⟩□(trust ≠ hostile)`, and the report "
        "names the `H` action that blocks `deploy_agents`; where either membership fails, "
        "every balance kernel of this document is also reported with `L` in the coalition "
        "(`⟨⟨H, L⟩⟩□φ`), and the conjunct and the actor that empty the kernel are named"
    ),
    "expected": (
        "membership of both, with the blocking action named; or the emptying conjunct and "
        "actor, with the `L`-joined kernels beside"
    ),
    "sources": (
        "ww2_testbed.md T13 and section 11 (2026-10-14, the empty kernel); DESIGN.md section "
        "3.2 (V_HL); review_2026-10-17.md, gap 1"
    ),
}

AGI = {"cap": "agi"}
CONJUNCTS = {"dependence ≠ lock_in": "no_lock_in", "trust ≠ hostile": "not_hostile"}
ALONE = {text: K("H", name) for text, name in CONJUNCTS.items()}
WITH = {
    (text, actor): K(f"H+{actor}", name) for text, name in CONJUNCTS.items() for actor in ("L", "A")
}
# Every balance kernel of the document, as registered and with L in the coalition.
BALANCE = {
    "⟨⟨H⟩⟩□balance_control": (KH, KHL),
    "⟨⟨H⟩⟩□balance_deter": (KD, K("H+L", "balance_deter")),
    "⟨⟨H, A⟩⟩□balance_coexist": (KJ, K("H+L+A", "balance_coexist")),
}
JOBS = [*ALONE.values(), *WITH.values(), *(job for jobs in BALANCE.values() for job in jobs)]


def member(text: str) -> str:
    got = by_objective(ALONE[text], **AGI)
    out = [o for o in OBJECTIVES if not got[o]]
    need(not out, f"s₀[cap:=agi] is outside ⟨⟨H⟩⟩□({text}) under {out}")
    return f"inside ⟨⟨H⟩⟩□({text}) under every objective"


def blockers() -> dict[str, list[str]]:
    """The ``H`` actions with an effect on a variable that a guard part of
    ``L.deploy_agents`` reads."""
    actors = {a.name: a for a in compiled().model.actors}
    deploy = next(a for a in actors["L"].actions if a.name == "deploy_agents")
    out = {}
    for part, expr in deploy.guard_parts:
        read = expr.free_vars()
        hits = sorted(
            {
                f"H.{x.name} (acts on {eff.var})"
                for x in actors["H"].actions
                for eff in x.effects
                if eff.var in read
            }
        )
        if hits:
            out[f"L.deploy_agents:{part}"] = hits
    return out


def emptied(text: str) -> dict[str, object]:
    """Who has to join ``H`` for the conjunct to be kept, by objective."""
    alone = by_objective(ALONE[text], **AGI)
    with_l = by_objective(WITH[text, "L"], **AGI)
    with_a = by_objective(WITH[text, "A"], **AGI)
    out = {}
    for o in OBJECTIVES:
        if alone[o]:
            continue
        joiners = [a for a, got in (("L", with_l), ("A", with_a)) if got[o]]
        out[o] = joiners or "neither L nor A alone restores it"
    return out


@first_sight
def test_G14():
    p = Parts("G14")
    kept = {text: p.check(text, lambda text=text: member(text)) for text in CONJUNCTS}
    p.report("H actions that act on what a guard part of deploy_agents reads", blockers)
    if not all(kept.values()):
        for text in CONJUNCTS:
            p.report(f"who must join H to keep {text}", lambda text=text: emptied(text))
        for label, (registered, joined) in BALANCE.items():
            p.report(
                f"{label} and the same with L",
                lambda registered=registered, joined=joined: {
                    "as registered": by_objective(registered, **AGI),
                    "with L": by_objective(joined, **AGI),
                },
            )
    p.finish()
