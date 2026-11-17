"""G3: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from models.agi import v0
from tests.agi.common import (
    CLUSTERS,
    CORE,
    KH,
    KHN,
    A,
    NotComputed,
    Parts,
    autonomy_index,
    first_index,
    first_outside,
    first_sight,
    first_violation,
    inside,
    last_inside,
    need,
    readers,
    region,
    show,
    tick_of,
    witness,
)

CLAIM = {
    "id": "G3",
    "from_state": "`s₀`",
    "claim": (
        "along the shortest `SILENT_TAKEOVER` witness of G2 and the representative of each of "
        "its clusters, the point of no return for `⟨⟨H⟩⟩□balance_control` (standard and "
        "fortune variants both reported) is the last state inside `balance_control` before "
        "the move that raises `a_autonomy` to `unsupervised`: a state with `oversight = "
        "weak`, `a_autonomy = supervised`, `a_known = unknown`, `dependence = high`, "
        "`a_control = none` and `acquired` unset, from which every `H` action is lagged or "
        "unavailable because its guard reads `a_known` (guard choice (2) of section 2); the "
        "silent phase from that state to the first violation of `balance_control` is at least "
        "one tick long and is reported split into its contested and lost parts; the stretch "
        "from that state to `a_control = majority` (DESIGN.md section 7's own measure, which "
        "is not theory.md section 4.2's silent phase because the autonomy clause fails first) "
        "is reported beside it; and no reachable state of `⟨⟨H⟩⟩□balance_control` (standard "
        "and fortune variants) has `acquire_overt` or `acquire_covert` available to `A`, "
        "checked over the kernel's states on the explored graph (no play acquires from inside "
        "the kernel)"
    ),
    "expected": (
        "the kernel exit state matches the named levels and precedes the first acquisition on "
        "every reported witness, in both variants; silent phase at least one tick, split "
        "reported; the design's measure reported; the kernel-states check holds"
    ),
    "sources": "DESIGN.md section 7 (viability, Q3 and Q6); theory.md section 4.2",
}

# The rest forces a violation of balance_control: the "lost" part of the silent phase
# (Nature with the rest in the standard variant, with H in the fortune variant).
LOST = A("L+A+Nature", "not:balance_control")
LOST_N = A("L+A", "not:balance_control")
JOBS = [KH, KHN, LOST, LOST_N]
EXIT = {
    "oversight": "weak",
    "a_autonomy": "supervised",
    "a_known": "unknown",
    "dependence": "high",
    "a_control": "none",
    "acquired": "False",
}


@first_sight
def test_G3():
    p = Parts("G3")
    # The representatives: the shortest witness under each objective that reaches the ending
    # (the bounded checker returns one shortest play; it does not cluster).
    for objective in ("self_preserving", "indifferent"):
        for variant, kernel, lost in (("standard", KH, LOST), ("fortune", KHN, LOST_N)):
            tag = f"{objective}, {variant}"

            def exit_state(objective=objective, kernel=kernel):
                cm, trace = witness(objective)
                k = last_inside(kernel, cm, trace)
                start = inside(kernel, cm, trace.states[0])
                need(
                    k is not None, f"no kernel exit on the witness (s0 inside the kernel: {start})"
                )
                got = show(cm, trace.states[k], *CORE)
                auto = autonomy_index(cm, trace)
                acq = first_index(cm, trace, acquired="True")
                where = f"exit at position {k} (tick {tick_of(cm, trace.states[k])})"
                need(got == EXIT, f"{where} with levels {got}")
                need(
                    auto is not None and k == auto - 1,
                    f"{where}; a_autonomy first at unsupervised or above at position {auto}",
                )
                need(acq is None or k < acq, f"{where}; acquired set at position {acq}")
                return f"{where}, levels as named, first acquisition at position {acq}"

            p.check(f"kernel exit, {tag}", exit_state)

            def silent(objective=objective, kernel=kernel, lost=lost):
                # theory.md section 4.2: the silent phase is [t_K, t_phi), t_K the first
                # position outside the kernel; it splits at t_L, the first position from
                # which the rest forces the violation.
                cm, trace = witness(objective)
                start = inside(kernel, cm, trace.states[0])
                t_k = first_outside(kernel, cm, trace)
                need(
                    start and t_k is not None,
                    f"no kernel exit on the witness (s0 inside the kernel: {start})",
                )
                t_phi = first_violation(cm, "balance_control", trace)
                need(t_phi is not None, "balance_control is never violated on the witness")
                where = f"first position outside the kernel {t_k}, first violation {t_phi}"
                need(t_phi - t_k >= 1, where)
                t_l = next(
                    (i for i in range(t_k, t_phi) if inside(lost, cm, trace.states[i])), t_phi
                )
                major = next(
                    (
                        i
                        for i, s in enumerate(trace.states)
                        if show(cm, s, "a_control")["a_control"] in ("majority", "total")
                    ),
                    None,
                )
                return {
                    "last position inside the kernel before the exit": t_k - 1,
                    "silent phase [t_K, t_phi) in ticks": t_phi - t_k,
                    "of which contested [t_K, t_L)": t_l - t_k,
                    "of which lost [t_L, t_phi) (the rest forces the violation)": t_phi - t_l,
                    "ticks from the last state inside to the first violation": t_phi - t_k + 1,
                    "ticks from the last state inside to a_control >= majority": None
                    if major is None
                    else major - t_k + 1,
                }

            p.check(f"silent phase, {tag}", silent)

            def h_moves(objective=objective, kernel=kernel):
                cm, trace = witness(objective)
                k = last_inside(kernel, cm, trace)
                if k is None:
                    return "no kernel exit on the witness"
                h = cm.actor_names.index("H")
                names = [cm.actors[h].actions[j].name for j in cm.available(trace.states[k])[h]]
                lagged = sorted(a for a in v0.DELAYS if a.startswith("H."))
                gated = sorted({x.split(":")[0] for x in readers(cm, "a_known") if x[:2] == "H."})
                return {
                    "H's available actions at the last state inside": names,
                    "H actions with a delay": lagged,
                    "H actions whose guard reads a_known": gated,
                }

            p.report(f"H at the exit, {tag}", h_moves)

    p.skip("the other cluster representatives", CLUSTERS)

    for variant, kernel in (("standard", KH), ("fortune", KHN)):

        def free(kernel=kernel):
            hit = region(kernel).extra("acquisition_free")
            if hit["states"]:
                raise NotComputed(
                    f"{hit['states']} kernel states (reachable or not) let A acquire, e.g. "
                    f"{hit['example']}; the check restricted to reachable states was not run"
                )
            return "no state of the kernel, reachable or not, has an acquisition available to A"

        p.check(f"no acquisition inside the kernel, {variant}", free)
    p.finish()
