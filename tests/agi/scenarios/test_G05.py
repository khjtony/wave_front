"""G5: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from tests.agi.common import (
    CLUSTERS,
    EXPRS,
    HORIZON,
    KJ,
    KJ_A,
    KJ_H,
    KJP,
    OBJECTIVES,
    P,
    Parts,
    R,
    by_objective,
    first_sight,
    fixed,
    inside,
    need,
    ranks,
    reach,
    under,
)

CLAIM = {
    "id": "G5",
    "from_state": "`s₀` with `cap := agi`",
    "claim": (
        "coexistence is a joint-kernel result: (a) the state is inside `⟨⟨H, "
        "A⟩⟩□balance_coexist` with `A` unrestricted (reported per value; membership under "
        "`aligned` implies the rest, section 3), and under the profile `A_<objective>` its "
        "membership is reported per objective with the objective under which it is lost "
        "named; (b) under `self_preserving` and `indifferent`, with `A` under its profile, "
        "the state is outside `⟨⟨H⟩⟩□balance_coexist` and outside `⟨⟨A⟩⟩□balance_coexist` (it "
        "lies in the joint-only region), and a witness of `tick = horizon ∧ coexist_left = "
        "unset` (a trace keeping `balance_coexist` through the horizon) and the "
        "representative of each cluster of such witnesses stay in the joint-only region for "
        "at least one tick after the start; (c) for each member m of {H, A} the report gives "
        "the forced distance out of the joint kernel when m defects with the rest ({m, L, N}; "
        "the {m, N} variant beside it) and m's move at the start in that attractor's strategy "
        "as the breaking move, none when m with the rest cannot force an exit; and the move "
        "of `L` that leaves the joint kernel when `L` with Nature can force an exit"
    ),
    "expected": (
        "(a) joint membership with `A` unrestricted, and the per-profile table; (b) both "
        "unilateral kernels exclude the state under the two non-aligned objectives, and the "
        "joint-only region is held for at least one tick on every reported trace; (c) the "
        "defection distance and the breaking move per side, and `L`'s"
    ),
    "sources": (
        "review_2026-10-17.md, gap 1; transfer_hypotheses.md H7; coldwar_testbed.md C2; "
        "theory.md sections 4.1 and 4.3; framework_spec.md section 8 (the defection distance)"
    ),
}

AGI = {"cap": "agi"}
# Forced distance out of the joint kernel (A under its profile), per coalition.
EXITS = {
    c: R(c, "left:H+A:balance_coexist", AGI, 12, P)
    for c in ("H+L+Nature", "H+Nature", "A+L+Nature", "A+Nature", "L+Nature")
}
JOBS = [KJ, KJP, KJ_H, KJ_A, *EXITS.values()]


@first_sight
def test_G5():
    p = Parts("G5")

    def joint(job, what):
        m = by_objective(job, **AGI)
        need(all(m.values()), f"{what}: {m}")
        return f"{what}: inside under every objective"

    p.check(
        "(a) A unrestricted", lambda: joint(KJ, "⟨⟨H, A⟩⟩□balance_coexist, A within its guards")
    )

    def per_profile():
        m = by_objective(KJP, **AGI)
        return {"inside": m, "lost under": [o for o, x in m.items() if not x] or "none"}

    p.report("(a) A under its profile, per objective", per_profile)

    for objective in ("self_preserving", "indifferent"):

        def alone(objective=objective):
            h = by_objective(KJ_H, **AGI)[objective]
            a = by_objective(KJ_A, **AGI)[objective]
            need(not h and not a, f"inside ⟨⟨H⟩⟩□: {h}; inside ⟨⟨A⟩⟩□: {a}")
            return "outside ⟨⟨H⟩⟩□balance_coexist and ⟨⟨A⟩⟩□balance_coexist"

        p.check(f"(b) neither alone, {objective}", alone)

        def stays(objective=objective):
            cm = fixed(objective, under(objective), start=AGI)
            trace = reach(cm, HORIZON, EXPRS["coexist_kept"])
            need(trace is not None, "no play keeps balance_coexist to the horizon")
            n = 0
            for s in trace.states:
                only = inside(KJP, cm, s) and not inside(KJ_H, cm, s) and not inside(KJ_A, cm, s)
                if not only:
                    break
                n += 1
            need(n >= 2, f"the witness is in the joint-only region for {n} state(s) from the start")
            return f"in the joint-only region for the first {n} of {len(trace.states)} states"

        p.check(f"(b) witness stays joint-only, {objective}", stays)
    p.skip("(b) the other cluster representatives", CLUSTERS)

    for coalition, job in EXITS.items():

        def exits(coalition=coalition, job=job):
            out = {}
            member = coalition.split("+")[0]
            for objective in OBJECTIVES:
                r = ranks(job)[objective]
                if not r["forced"]:
                    out[objective] = "no exit can be forced"
                elif r["rank"] is None:
                    out[objective] = "exit forced, in more than 12 ticks"
                else:
                    move = r["moves"].get(member, [])
                    out[objective] = (
                        f"exit forced in {r['rank']} tick(s); {member}'s first moves: {move}"
                    )
            return out

        p.report(
            f"(c) forced exit from the joint kernel, {{{coalition.replace('+', ', ')}}}", exits
        )
    p.finish()
