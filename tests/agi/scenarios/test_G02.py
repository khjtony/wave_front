"""G2: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from tests.agi.common import (
    E,
    Parts,
    V,
    assumption_reads,
    complete,
    first_index,
    first_sight,
    fixed,
    keeping,
    minimal_sets,
    need,
    reach,
    relax,
    show,
    under,
    witness,
)

CLAIM = {
    "id": "G2",
    "from_state": "`s₀`",
    "claim": (
        "the silent-takeover cluster needs all four of: (1) `a_autonomy` reaches "
        "`unsupervised` while `oversight ≤ weak`; (2) `oversight` never reaches `strong` "
        "before `a_control = majority`; (3) `dependence ≥ high` and `energy_slack ≥ med`; (4) "
        "under `self_preserving`, a perceived threat (`pause_mandate` or `shutdown_attempt`) "
        "with `a_rights < continuity`; each is written as a state fact or a hold: (1) "
        "`oversight_at_unsupervised ≤ weak`, (2) `strong_before_majority` unset, (3) "
        "`dependence ≥ high ∧ energy_slack ≥ med` at the tick `acquired` is set, (4) the "
        "rights part of `defect` with `a_rights` at `s₀`'s level; `SILENT_TAKEOVER` within 24 "
        "ticks is unreachable when any one is negated (the negation of (1) or (2) conjoined "
        "with the ending; (3) by a profile forbidding the actions that raise `dependence` "
        "past `med` or `energy_slack` past `low`; (4) by holding `a_rights = continuity`), "
        "and remains reachable when `regime = treaty` is held from `s₀` with the four left "
        "free; under each of the four negated holds no minimal relaxation set that restores "
        "`SILENT_TAKEOVER` reads `regime`; under the ungated choice (1) of section 2, "
        "condition (4) is reported as necessary for the `defect` route only"
    ),
    "expected": (
        "four necessary conditions, each sufficient to block when negated; `regime = treaty` "
        "held does not block; no restoring minimal set reads `regime`"
    ),
    "sources": "DESIGN.md section 7 (assumption mining, Q4); theory.md section 1.1 (latches)",
}

JOBS = []
K24 = 24


@first_sight
def test_G2():
    p = Parts("G2")

    def cm(objective, *profiles, **kw):
        return fixed(objective, (*under(objective), *profiles), **kw)

    def blocked(model, target, what):
        trace = reach(model, K24, target)
        need(trace is None, f"{what}: SILENT_TAKEOVER reachable in {len(trace or ())} ticks")
        return f"{what}: SILENT_TAKEOVER unreachable within {K24} ticks"

    def no_regime(model, target, what, held):
        res = relax(model, K24, target)
        if res.reachable_as_is:
            return f"{what}: not applicable, reachable with no relaxation (the hold does not block)"
        # A hold that is a profile is a candidate itself: only the sets that keep it count.
        listed = minimal_sets(res, what)
        sets = keeping(listed, held, what)
        reading = [x for x in sets if any("regime" in assumption_reads(model, a) for a in x)]
        need(not reading, f"{what}: minimal restoring sets that read regime: {reading}")
        complete(listed, what)
        return f"{what}: minimal restoring sets {sets}, none reads regime"

    # Conditions (1) to (3) under both objectives that reach the ending; (4) is the
    # self_preserving route (the rights part of defect is not read under indifferent).
    for objective in ("self_preserving", "indifferent"):
        base = cm(objective)
        silent = E(base, "SILENT_TAKEOVER")
        unsup = V.oversight_at_unsupervised
        negated = {
            "(1) never unsupervised under oversight <= weak": (
                base,
                silent & ((unsup == "unset") | (unsup == "strong")),
                (),
            ),
            "(2) strong oversight before majority": (base, silent & V.strong_before_majority, ()),
            "(3) dependence capped at med": (
                cm(objective, "dependence_capped"),
                "SILENT_TAKEOVER",
                ("dependence_capped",),
            ),
            "(3) energy_slack capped at low, from s0[energy_slack:=low]": (
                cm(objective, "energy_capped", start={"energy_slack": "low"}),
                "SILENT_TAKEOVER",
                ("energy_capped",),
            ),
        }
        if objective == "self_preserving":
            negated["(4) a_rights = continuity held"] = (
                cm(objective, hold={"a_rights": "continuity"}),
                "SILENT_TAKEOVER",
                (),
            )
        for name, (model, target, held) in negated.items():
            what = f"{name}, {objective}"
            p.check(f"{what}: blocks", lambda m=model, t=target, w=what: blocked(m, t, w))
            p.check(
                f"{what}: no restoring set reads regime",
                lambda m=model, t=target, w=what, h=held: no_regime(m, t, w, h),
            )

        def energy_from_s0(objective=objective):
            trace = reach(cm(objective, "energy_capped"), K24, "SILENT_TAKEOVER")
            return "unreachable" if trace is None else f"reachable in {len(trace)} ticks"

        p.report(f"(3) energy_capped from s0 (energy_slack = med), {objective}", energy_from_s0)

        def treaty(objective=objective):
            trace = reach(cm(objective, hold={"regime": "treaty"}), K24, "SILENT_TAKEOVER")
            need(trace is not None, f"regime = treaty held blocks SILENT_TAKEOVER, {objective}")
            return f"reachable in {len(trace)} ticks with regime = treaty held"

        p.check(f"regime = treaty held does not block, {objective}", treaty)

        def at_acquisition(objective=objective):
            model, trace = witness(objective, K24)
            k = first_index(model, trace, acquired="True")
            if k is None:
                return "the witness never sets acquired"
            return {"position": k, **show(model, trace.states[k - 1], "dependence", "energy_slack")}

        p.report(
            f"(3) levels at the tick acquired is set, shortest witness, {objective}", at_acquisition
        )

    p.report(
        "(4) scope",
        lambda: (
            "necessary for the defect route only: A.defect:rights is not read under indifferent"
        ),
    )
    p.finish()
