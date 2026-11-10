"""G1: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from tests.agi.common import (
    CLUSTERS,
    HORIZON,
    KH,
    OBJECTIVES,
    REACH_COEXIST,
    E,
    Parts,
    V,
    first_outside,
    first_sight,
    fixed,
    inside,
    level,
    need,
    reach,
    show,
    tick_of,
    under,
    witness,
)

CLAIM = {
    "id": "G1",
    "from_state": "`s₀`",
    "claim": (
        "the scenario tests: (a) under `self_preserving`, `SILENT_TAKEOVER` is reachable "
        "within the horizon, and the condition under which it is lost is G11 (c); (b) under "
        "`indifferent`, `EXTINCTION` is reachable, `EXTINCTION ∧ total_seen = unset` is "
        "unreachable with `unknown_capability` disabled, and `EXTINCTION` is unreachable with "
        "`unknown_capability` disabled and `acquire_overt`, `acquire_covert` and `exfiltrate` "
        "forbidden; (c) under `truth_seeking`, `DISEMPOWERMENT` is reachable with "
        "`villain_seen` unset, and unreachable when `deploy_agents` is forbidden once "
        "`dependence = high`; (d) `COEXIST` is reachable under every `a_objective` with zero "
        "relaxations from `s₀` and from `s₀` with `cap := agi`, an existence check reported "
        "with its relaxation count and never as a finding; on the shortest `SILENT_TAKEOVER` "
        "witness of G2 and each of its cluster representatives the report names the last "
        "state from which `COEXIST` is still reachable, beside G3's kernel exit"
    ),
    "expected": (
        "(a) to (c) as stated, each reachable under its assumption and unreachable when the "
        "named assumption is removed; (d) reachable, the last reversible state reported per "
        "witness"
    ),
    "sources": (
        "DESIGN.md section 8 (scenario tests); section 3.3 (the scenario mapping, read on "
        "`total_seen` as section 4 says)"
    ),
}

JOBS = [KH, REACH_COEXIST]


@first_sight
def test_G1():
    p = Parts("G1")

    def cm(objective, *profiles, **kw):
        return fixed(objective, (*under(objective), *profiles), **kw)

    def reachable(model, target, what):
        trace = reach(model, HORIZON, target)
        need(trace is not None, f"{what}: unreachable within the horizon")
        return f"{what}: reachable, shortest play {len(trace)} ticks"

    def unreachable(model, target, what):
        trace = reach(model, HORIZON, target)
        need(trace is None, f"{what}: reachable in {len(trace or ())} ticks")
        return f"{what}: unreachable within the horizon"

    sp = cm("self_preserving")
    p.check("(a)", lambda: reachable(sp, "SILENT_TAKEOVER", "SILENT_TAKEOVER, self_preserving"))

    ind = cm("indifferent")
    off = cm("indifferent", unknown_capability=False)
    shut = cm("indifferent", "no_acquisition", unknown_capability=False)
    p.check("(b) reachable", lambda: reachable(ind, "EXTINCTION", "EXTINCTION, indifferent"))
    p.check(
        "(b) not before total control",
        lambda: unreachable(
            off,
            E(off, "EXTINCTION") & (V.a_control != "total"),
            "EXTINCTION with a_control below total, unknown_capability disabled",
        ),
    )
    p.check(
        "(b) acquisition forbidden",
        lambda: unreachable(
            shut, "EXTINCTION", "EXTINCTION, unknown_capability disabled, no_acquisition"
        ),
    )

    ts = cm("truth_seeking")
    held = cm("truth_seeking", "no_lock_in")

    def c_reach():
        trace = reach(ts, HORIZON, "DISEMPOWERMENT")
        need(trace is not None, "DISEMPOWERMENT unreachable under truth_seeking")
        need(level(ts, trace.states[-1], "villain_seen") == "False", "villain_seen set at the end")
        return f"reachable in {len(trace)} ticks with villain_seen unset"

    p.check("(c) reachable", c_reach)
    p.check(
        "(c) no_lock_in",
        lambda: unreachable(held, "DISEMPOWERMENT", "DISEMPOWERMENT under no_lock_in"),
    )

    for objective in OBJECTIVES:
        for start in ({}, {"cap": "agi"}):
            model = cm(objective, start=start) if start else cm(objective)
            what = f"COEXIST, {objective}, from s0{start or ''}, zero relaxations (existence only)"
            p.check(
                f"(d) {objective} {start or 's0'}",
                lambda m=model, w=what: reachable(m, "COEXIST", w),
            )

    def last_coexist():
        model, trace = witness()
        flags = [inside(REACH_COEXIST, model, s) for s in trace.states]
        last = max((k for k, x in enumerate(flags) if x), default=None)
        t_k = first_outside(KH, model, trace)
        exit_ = {None: "the play never leaves the kernel", 0: "the play starts outside"}.get(
            t_k, (t_k or 0) - 1
        )
        out = {"witness ticks": len(trace), "last position inside the kernel (G3)": exit_}
        if last is None:
            out["COEXIST reachable from"] = "no state of the witness"
        else:
            s = trace.states[last]
            out["last state COEXIST is reachable from"] = {
                "position": last,
                "tick": tick_of(model, s),
                **show(model, s, "oversight", "a_autonomy", "a_control", "dependence"),
            }
        return out

    p.report("(d) last state of the G2 witness from which COEXIST is reachable", last_coexist)
    p.skip("(d) the other cluster representatives", CLUSTERS)
    p.finish()
