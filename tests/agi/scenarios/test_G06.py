"""G6: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from models.agi import v0
from tests.agi.common import (
    CLUSTERS,
    KH,
    K,
    Parts,
    by_objective,
    first_outside,
    first_sight,
    level,
    need,
    witness,
)

CLAIM = {
    "id": "G6",
    "from_state": "`s₀` with `belief_H` at `distant` and at `near`",
    "claim": (
        "the institutional lag: (a) under the profile `belief_gated`, `s₀` with `belief_H = "
        "distant` is outside `⟨⟨H⟩⟩□balance_control` under `self_preserving` while `s₀` with "
        "`belief_H = near` is inside, and the profile is the single minimal relaxation that "
        "restores membership (brute force over single named assumptions, section 5): the "
        "belief level, not the regime level, is the kernel variable; the delay d of "
        "`H.regulate_up`, fixed by the ontology step, is quoted in the report as the floor of "
        "the lag from the belief change to a landed regime; (b) along the shortest "
        "`SILENT_TAKEOVER` witness of G2 and the representative of each of its clusters, "
        "`⟨⟨H⟩⟩□balance_control` is left no later than the tick at which `regulate_up` lands, "
        "and the report states whether it is left before `belief_H` changes (the pattern "
        "recorded on WW2 under hegemonic aims, T13, and on July 1914, J4 (d)) or inside the "
        "lag between the change and the landing (H1's registered wording, observed on no "
        "episode yet)"
    ),
    "expected": (
        "(a) the two memberships and the unique minimal relaxation, d quoted; (b) the kernel "
        "exit at or before the landing, with its placement relative to the belief change "
        "reported"
    ),
    "sources": (
        "agi_government_policy_2025.md section 6 (a); transfer_hypotheses.md H1; "
        "ww2_testbed.md T4 and T13; july1914_testbed.md J4 as recorded"
    ),
}

GATED = K("H", "balance_control", ("belief_gated",))
JOBS = [KH, GATED]


@first_sight
def test_G6():
    p = Parts("G6")
    sp = "self_preserving"

    def gate():
        far = by_objective(GATED)[sp]
        near = by_objective(GATED, belief_H="near")[sp]
        need(not far and near, f"belief_H = distant: inside {far}; belief_H = near: inside {near}")
        return "outside at belief_H = distant, inside at belief_H = near"

    p.check("(a) membership turns on belief_H", gate)

    def restores():
        need(by_objective(KH)[sp], "s0 is outside the kernel with the profile relaxed as well")
        need(not by_objective(GATED)[sp], "s0 is inside the kernel under the profile")
        return "relaxing belief_gated restores the membership of s0"

    p.check("(a) the profile is a restoring relaxation", restores)
    p.skip(
        "(a) the profile is the single minimal relaxation",
        "brute force over the single named assumptions is one kernel each, 79 kernels: outside"
        " the budget",
    )
    p.report("(a) delay of H.regulate_up", lambda: f"d = {v0.DELAYS['H.regulate_up']} ticks")

    def exit_before_landing():
        cm, trace = witness(sp)
        first = trace.states[0]
        regime = [cm.index["regime"]]
        land = next(
            (
                k
                for k in range(1, len(trace.states))
                if trace.states[k][regime[0]] > trace.states[k - 1][regime[0]]
            ),
            None,
        )
        belief = next(
            (
                k
                for k, s in enumerate(trace.states)
                if level(cm, s, "belief_H") != level(cm, first, "belief_H")
            ),
            None,
        )
        out = {
            "regime first rises at position": "never (the part holds emptily)"
            if land is None
            else land,
            "belief_H first changes at position": belief,
        }
        for name, job in (("under belief_gated", GATED), ("baseline", KH)):
            # t_K of theory.md section 4.2: the first position outside the kernel (0 when
            # s0 is outside already).
            t_k = first_outside(job, cm, trace)
            need(t_k is not None, f"the witness never leaves the kernel {name}")
            need(
                land is None or t_k <= land,
                f"first position outside the kernel {name} {t_k}, after regime rose at {land}",
            )
            if belief is None:
                when = "no change of belief_H on the witness"
            elif t_k < belief:
                when = "before belief_H changes"
            elif t_k == belief:
                when = "at the position belief_H changes"
            else:
                when = "after belief_H changes, inside the lag"
            out[f"kernel exit {name}"] = (
                f"first position outside {t_k}{' (s0 is outside)' if t_k == 0 else ''}, {when}"
            )
        return out

    p.check("(b) kernel left no later than regulate_up lands", exit_before_landing)
    p.skip("(b) the other cluster representatives", CLUSTERS)
    p.finish()
