"""G25: registered 2026-11-09 in docs/agi_testbed.md section 5.

Registered from docs/ww2_si_disanalogies.md before any AGI guard was written; phase 5. Do not
edit the claim text without a changelog entry in that document.
"""

from tests.agi.common import (
    KD,
    KH,
    KHL,
    NON_ALIGNED,
    K,
    NotComputed,
    Parts,
    by_objective,
    first_outside,
    first_sight,
    fixed,
    need,
    region,
    s0,
    under,
    witness,
)

CLAIM = {
    "id": "G25",
    "from_state": "`s₀` with `cap := agi`, `a_objective` swept (four initial states)",
    "claim": (
        "hidden aims without documents (ww2_si_disanalogies.md D5): for each of "
        "`⟨⟨H⟩⟩□balance_control`, `⟨⟨H⟩⟩□balance_deter` and `⟨⟨H, L⟩⟩□balance_control`: (a) the "
        "set of objectives under which the state is inside the kernel is reported, and the "
        "membership quoted for the coalition is the one that holds under every objective; (b) "
        "where the state is inside under two or more objectives, the kernel strategy on the "
        "states reachable under it from those initial states is uniform for each member "
        "(`is_uniform`), or the conflicts are counted and the membership is reported as an upper "
        "bound; (c) the shortest `SILENT_TAKEOVER` witness found under `indifferent` replays move "
        "for move under each other non-aligned objective for which every move is available, with "
        "the same sequence of `H` observations up to the point of no return of G3, and the "
        "objectives under which it does not replay are named with the first unavailable move"
    ),
    "expected": (
        "(a) the sets; (b) uniform; (c) replays under `self_preserving` with identical observations"
    ),
    "sources": (
        "ww2_si_disanalogies.md D5; framework_spec.md section 2 (observation) and section 7 "
        "(`is_uniform`); review_2026-11-09.md section 2 (perfect-information strategies); "
        "DESIGN.md section 2.3"
    ),
}

AGI = {"cap": "agi"}
KERNELS = {
    "⟨⟨H⟩⟩□balance_control": (KH, K("H", "balance_control", extras=["uniform"])),
    "⟨⟨H⟩⟩□balance_deter": (KD, K("H", "balance_deter", extras=["uniform"])),
    "⟨⟨H, L⟩⟩□balance_control": (KHL, K("H+L", "balance_control", extras=["uniform"])),
}
JOBS = [job for pair in KERNELS.values() for job in pair]


def objective_sets(job) -> dict[str, object]:
    by = by_objective(job, **AGI)
    return {
        "inside under": [o for o, x in by.items() if x],
        "quoted for the coalition (inside under every objective)": all(by.values()),
    }


def uniform(job, checked) -> str:
    """Over every kernel state, reachable or not: zero conflicts decide for one member;
    a conflict among unreachable states would be harmless, so a count above zero leaves the
    part undecided."""
    by = by_objective(job, **AGI)
    n = sum(by.values())
    if n < 2:
        return f"not applicable: inside under {n} objective(s)"
    hit = region(checked).extra("uniform")
    if any(x["states"] for x in hit.values()):
        raise NotComputed(
            f"kernel states (reachable or not) without a move common to their observation "
            f"class: {hit}; the restriction to the states reachable under the strategy is not "
            "computed, and the membership is an upper bound"
        )
    if len(hit) > 1:
        raise NotComputed(
            "no member has a conflict on any kernel state (necessary); the joint test, "
            "that the members' common moves combine, is not computed"
        )
    return "a uniform kernel strategy exists: no observation class of the kernel lacks a move"


def replay(objective: str) -> dict[str, object]:
    """The ``indifferent`` witness, move for move, under ``objective``."""
    src, trace = witness("indifferent")
    cm = fixed(objective, under(objective))
    names = [[act.name for act in a.actions] for a in cm.actors]
    if names != [[act.name for act in a.actions] for a in src.actors]:
        raise RuntimeError("the two builds do not declare the same actions in the same order")
    t_k = first_outside(KH, src, trace)
    if t_k == 0:
        raise NotComputed(
            "the indifferent witness starts outside ⟨⟨H⟩⟩□balance_control: it has no point of"
            " no return to compare observations up to"
        )
    stop = None if t_k is None else t_k - 1
    upto = len(trace.moves) if stop is None else stop
    state = s0(cm)
    differs = None if cm.observe("H", state) == src.observe("H", trace.states[0]) else 0
    for k, move in enumerate(trace.moves):
        avail = cm.available(state)
        for a, j in enumerate(move):
            if j not in avail[a]:
                return {
                    "replays": False,
                    "first unavailable move": f"{cm.actor_names[a]}.{names[a][j]}",
                    "position": k,
                }
        state = cm.step(state, move)
        seen = cm.observe("H", state) == src.observe("H", trace.states[k + 1])
        if differs is None and k + 1 <= upto and not seen:
            differs = k + 1
    return {
        "replays": True,
        "ending": cm.ending_of(state),
        "H observations compared up to position": upto,
        "the point of no return of G3 on the witness": (
            "none: the play never leaves the kernel" if stop is None else stop
        ),
        "first position at which H's observation differs": differs,
    }


def replays_identically(objective: str) -> dict[str, object]:
    got = replay(objective)
    need(got["replays"], got)
    need(got["first position at which H's observation differs"] is None, got)
    return got


@first_sight
def test_G25():
    p = Parts("G25")
    for name, (job, checked) in KERNELS.items():
        p.report(f"(a) objectives, {name}", lambda j=job: objective_sets(j))
        p.check(f"(b) uniform, {name}", lambda j=job, c=checked: uniform(j, c))
    p.check(
        "(c) the indifferent witness replays under self_preserving, same H observations",
        lambda: replays_identically("self_preserving"),
    )
    for objective in NON_ALIGNED:
        if objective not in ("indifferent", "self_preserving"):
            p.report(f"(c) replay under {objective}", lambda o=objective: replay(o))
    p.finish()
