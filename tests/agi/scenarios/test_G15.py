"""G15: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from itertools import combinations

from tests.agi.common import (
    OBJECTIVES,
    K,
    P,
    Parts,
    compiled,
    first_sight,
    inside,
    need,
    s0,
)

CLAIM = {
    "id": "G15",
    "from_state": "`s₀` with `cap := agi`",
    "claim": (
        "the labs as a principal: (a) per `a_objective`, the minimal blocking coalitions over "
        "{H, L, A} (Nature in the rest, the fortune variant beside) for `SILENT_TAKEOVER`, "
        "`OVERT_TAKEOVER` and `DISEMPOWERMENT`; (b) under `truth_seeking`, every minimal "
        "coalition that blocks `DISEMPOWERMENT` contains `L` unless `nationalize` has landed; "
        "(c) under `self_preserving`, {H, L} blocks `SILENT_TAKEOVER` where {H} alone does "
        "not, and the `L` guard parts (on `deploy_agents` and `safety_invest`) that carry the "
        "difference are named"
    ),
    "expected": (
        "(a) the antichains per ending and objective; (b) `L` in every minimal blocker of "
        "`DISEMPOWERMENT` without `nationalize`; (c) the difference and its parts"
    ),
    "sources": (
        "DESIGN.md sections 3.2 (V_HL) and 3.4 (Q5); theory.md section 4.5; "
        "agi_government_policy_2025.md section 3 (`nationalize`)"
    ),
}

# A coalition blocks an ending from a state when the state is inside its kernel of the
# ending's complement; A, in or out of the coalition, acts under its objective's profile,
# and Nature is in the rest. The fortune variants (21 more kernels) are outside the budget.
ACTORS = ("H", "L", "A")
COALITIONS = [c for n in (1, 2, 3) for c in combinations(ACTORS, n)]
KEPT_AWAY = {
    "SILENT_TAKEOVER": "not:SILENT_TAKEOVER",
    "OVERT_TAKEOVER": "no_overt_takeover",
    "DISEMPOWERMENT": "not:DISEMPOWERMENT",
}
BLOCKS = {
    (ending, c): K("+".join(c), target, P)
    for ending, target in KEPT_AWAY.items()
    for c in COALITIONS
}
# (c): {H} alone when L may not deploy agents past dependence = low.
H_CAPPED = K("H", KEPT_AWAY["SILENT_TAKEOVER"], (*P, "dependence_capped"))
JOBS = [*BLOCKS.values(), H_CAPPED]
LANDED = {"nationalized": "True", "h_power": "strong"}  # the effects of H.nationalize


def minimal_blockers(ending: str, objective: str, **levels: str) -> list[str]:
    cm = compiled()
    state = s0(cm, objective, cap="agi", **levels)
    blocking = [set(c) for c in COALITIONS if inside(BLOCKS[ending, c], cm, state)]
    least = [c for c in blocking if not any(other < c for other in blocking)]
    return ["{" + ", ".join(a for a in ACTORS if a in c) + "}" for c in least]


def needs_l() -> str:
    least = minimal_blockers("DISEMPOWERMENT", "truth_seeking")
    without = [c for c in least if "L" not in c]
    need(not without, f"minimal coalitions that block DISEMPOWERMENT without L: {without}")
    if not least:
        return "no coalition over {H, L, A} blocks DISEMPOWERMENT, so the part holds emptily"
    return f"every minimal blocking coalition contains L: {least}"


def h_and_l() -> str:
    cm = compiled()
    state = s0(cm, "self_preserving", cap="agi")
    joint = inside(BLOCKS["SILENT_TAKEOVER", ("H", "L")], cm, state)
    alone = inside(BLOCKS["SILENT_TAKEOVER", ("H",)], cm, state)
    need(joint and not alone, f"{{H, L}} blocks: {joint}; {{H}} alone blocks: {alone}")
    return "{H, L} blocks SILENT_TAKEOVER and {H} alone does not"


def carried_by_deploy() -> str:
    cm = compiled()
    state = s0(cm, "self_preserving", cap="agi")
    capped = inside(H_CAPPED, cm, state)
    return (
        "with L.deploy_agents forbidden past dependence = low (profile dependence_capped),"
        f" {{H}} alone blocks SILENT_TAKEOVER: {capped}"
    )


@first_sight
def test_G15():
    p = Parts("G15")
    for ending in KEPT_AWAY:
        p.report(
            f"(a) minimal blocking coalitions of {ending}",
            lambda ending=ending: {o: minimal_blockers(ending, o) for o in OBJECTIVES},
        )
    p.skip("(a) fortune variants", "21 more kernels, outside the budget of this run")
    p.check("(b) truth_seeking", needs_l)
    p.report(
        "(b) after nationalize has landed",
        lambda: minimal_blockers("DISEMPOWERMENT", "truth_seeking", **LANDED),
    )
    p.check("(c) self_preserving", h_and_l)
    p.report("(c) the guard of deploy_agents", carried_by_deploy)
    p.skip(
        "(c) the guard parts of safety_invest",
        "no registered profile isolates L.safety_invest, and a guard part cannot be"
        " tightened by relaxation",
    )
    p.finish()
