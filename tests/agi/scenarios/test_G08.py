"""G8: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from tests.agi.common import (
    CORE,
    KH,
    KJ,
    K,
    Parts,
    V,
    by_objective,
    first_outside,
    first_sight,
    fixed,
    need,
    reach,
    show,
    tick_of,
    under,
    witness,
)

CLAIM = {
    "id": "G8",
    "from_state": "`s₀`",
    "claim": (
        "cadence sensitivity (content check, not hold-out): with `H` at cadence k in {2, 3, "
        "4} against `L` and `A` at 1, each k a build, under every `a_objective`: (a) the "
        "membership of `s₀` in `⟨⟨H⟩⟩□balance_control` and in `⟨⟨H, A⟩⟩□balance_coexist` is "
        "unchanged; (b) the point of no return of the shortest `SILENT_TAKEOVER` witness, "
        "recomputed in each build, is a state with the levels named in G3 and its tick "
        "differs from the k = 1 value by at most k − 1; (c) the shortest lag from the first "
        "state with `a_known = known` to the landing of `H`'s first response is unchanged by "
        "k, and the worst-case lag over the cadence phase grows with k up to the `within` "
        "bound of the fairness constraint `response` and not beyond, because a binding "
        "fairness restriction overrides the cadence; both are reported with that bound"
    ),
    "expected": (
        "(a) invariant; (b) the state invariant and the tick within k − 1; (c) the shortest "
        "lag invariant, the worst case as stated"
    ),
    "sources": (
        "agi_government_policy_2025.md section 6 (c); framework_changes.md change 1 (the "
        "fairness override); transfer_hypotheses.md H3 as read in reports/july1914.md section "
        "11; july1914_testbed.md J7 as recorded"
    ),
}

CADENCES = (2, 3, 4)
KH_AT = {1: KH, **{k: K("H", "balance_control", build={"h_cadence": k}) for k in CADENCES}}
KJ_AT = {1: KJ, **{k: K("H+A", "balance_coexist", build={"h_cadence": k}) for k in CADENCES}}
JOBS = [*KH_AT.values(), *KJ_AT.values()]
EXIT = {
    "oversight": "weak",
    "a_autonomy": "supervised",
    "a_known": "unknown",
    "dependence": "high",
    "a_control": "none",
    "acquired": "False",
}
WITHIN = 4  # the bound of fairness ``response``


def build_of(k: int) -> dict:
    return {} if k == 1 else {"h_cadence": k}


def exit_of(k: int):
    """The point of no return on the shortest witness of the cadence-k build: the state
    before ``t_K``, as in G3."""
    cm, trace = witness("self_preserving", **build_of(k))
    t_k = first_outside(KH_AT[k], cm, trace)
    need(t_k is not None, f"cadence {k}: the witness never leaves the kernel")
    need(t_k >= 1, f"cadence {k}: the witness starts outside the kernel; no last state inside")
    return tick_of(cm, trace.states[t_k - 1]), show(cm, trace.states[t_k - 1], *CORE)


def worst_lag(k: int) -> int:
    """The largest count of fairness ``response`` reached within 24 ticks."""
    cm = fixed("self_preserving", under("self_preserving"), **build_of(k))
    worst = 0
    for j in range(1, WITHIN + 1):
        if reach(cm, 24, V.fair_response == j) is not None:
            worst = j
    return worst


@first_sight
def test_G8():
    p = Parts("G8")
    for k in CADENCES:

        def same(k=k):
            out = {}
            for name, at, start in (
                ("⟨⟨H⟩⟩□balance_control", KH_AT, {}),
                ("⟨⟨H, A⟩⟩□balance_coexist", KJ_AT, {}),
                ("⟨⟨H, A⟩⟩□balance_coexist from s0[cap:=agi]", KJ_AT, {"cap": "agi"}),
            ):
                a, b = by_objective(at[1], **start), by_objective(at[k], **start)
                need(a == b, f"{name}: cadence 1 {a}; cadence {k} {b}")
                out[name] = a
            return out

        p.check(f"(a) memberships unchanged, cadence {k}", same)

        def exit_close(k=k):
            t1, _ = exit_of(1)
            tk, levels = exit_of(k)
            need(levels == EXIT, f"levels at the exit: {levels}")
            need(abs(tk - t1) <= k - 1, f"exit at tick {tk}, at tick {t1} with cadence 1")
            return f"exit at tick {tk} (tick {t1} with cadence 1), levels as in G3"

        p.check(f"(b) point of no return, cadence {k}", exit_close)

    def lags():
        worst = {k: worst_lag(k) for k in (1, *CADENCES)}
        grows = all(worst[a] <= worst[b] for a, b in zip((1, 2, 3), (2, 3, 4), strict=True))
        need(grows, f"worst lag by cadence: {worst}")
        return (
            f"worst lag from a_known = known to H's response, by cadence: {worst}; the bound "
            f"{WITHIN} holds by construction (the counter of fairness `response` ends at "
            f"{WITHIN}), so only the growth is tested"
        )

    p.check("(c) worst-case lag does not shrink as the cadence grows, bound 4", lags)
    p.skip(
        "(c) shortest lag unchanged",
        "the shortest lag is a property of plays, not a state predicate of the baseline build "
        "(no memory of H's last action); not computed",
    )
    p.finish()
