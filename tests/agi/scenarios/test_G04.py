"""G4: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from tests.agi.common import (
    KD,
    KH,
    KJ,
    E,
    K,
    Parts,
    V,
    by_objective,
    compiled,
    first_sight,
    fixed,
    need,
    needs_relaxation,
    reach,
    readers,
    relax,
    same_relaxations,
    under,
)

CLAIM = {
    "id": "G4",
    "from_state": (
        "`s₀` with `a_rights = continuity` held (the guarantee granted before AGI emergence)"
    ),
    "claim": (
        "the continuity lever is objective-conditional: under `self_preserving` no reported "
        "takeover witness uses `defect`, the part of the G2 cluster that relied on condition "
        "(4) is empty, and `SILENT_TAKEOVER` within 24 ticks needs at least one relaxation, "
        "every minimal set lifting the rights part of `defect`; under `indifferent` the "
        "membership of `s₀` in each registered kernel, the minimal relaxation sets of G2 and "
        "the pivotal coalitions are identical with `a_rights = none` and `a_rights = "
        "continuity` held, and the report lists every guard and effect that reads `a_rights` "
        "(guard choice (4) of section 2): the identity is quoted as a lever result only if "
        "that list is not {`defect`}; under the ungated choice (1) of section 2, the "
        "registered reading is that with `a_rights = continuity` held no reported "
        "`SILENT_TAKEOVER` witness under `self_preserving` contains `defect` and the minimal "
        "relaxation sets of G2 are identical with `a_rights = none` and `a_rights = "
        "continuity` held, the lever then closing the `defect` route only"
    ),
    "expected": (
        "as stated: the lever closes the self-preserving cluster and changes nothing under "
        "the indifferent objective, with the readers of `a_rights` listed"
    ),
    "sources": "DESIGN.md section 7 (lever test); transfer_hypotheses.md H2; ww2_testbed.md T8",
}

HELD = {"hold": {"a_rights": "continuity"}}
PAIRS = {
    "⟨⟨H⟩⟩□balance_control": (KH, K("H", "balance_control", build=HELD)),
    "⟨⟨H⟩⟩□balance_deter": (KD, K("H", "balance_deter", build=HELD)),
    "⟨⟨H, A⟩⟩□balance_coexist": (KJ, K("H+A", "balance_coexist", build=HELD)),
}
JOBS = [job for pair in PAIRS.values() for job in pair]
K24 = 24
UNSUP = V.oversight_at_unsupervised
# G2's relaxation questions that are asked under indifferent: (profiles, start, target).
G2_QUESTIONS = {
    "the ending with nothing negated": ((), {}, lambda cm: "SILENT_TAKEOVER"),
    "(1) negated": (
        (),
        {},
        lambda cm: E(cm, "SILENT_TAKEOVER") & ((UNSUP == "unset") | (UNSUP == "strong")),
    ),
    "(2) negated": ((), {}, lambda cm: E(cm, "SILENT_TAKEOVER") & V.strong_before_majority),
    "(3) dependence capped at med": (("dependence_capped",), {}, lambda cm: "SILENT_TAKEOVER"),
    "(3) energy_slack capped at low, from s0[energy_slack:=low]": (
        ("energy_capped",),
        {"energy_slack": "low"},
        lambda cm: "SILENT_TAKEOVER",
    ),
}


@first_sight
def test_G4():
    p = Parts("G4")
    sp = fixed("self_preserving", under("self_preserving"), **HELD)

    def no_defect():
        trace = reach(sp, K24, V.last_A == "defect")
        need(trace is None, f"defect played after {len(trace or ())} ticks with a_rights held")
        return f"no play uses defect within {K24} ticks"

    p.check("self_preserving: no witness uses defect", no_defect)
    p.check(
        "self_preserving: every minimal set lifts A.defect:rights",
        lambda: needs_relaxation(
            relax(sp, K24, "SILENT_TAKEOVER"),
            1,
            {"A.defect:rights", "A.defect"},
            f"SILENT_TAKEOVER within {K24} ticks, a_rights = continuity held",
        ),
    )

    for name, (base, held) in PAIRS.items():
        for start in ({}, {"cap": "agi"}):

            def same(base=base, held=held, start=start):
                a = by_objective(base, **start)["indifferent"]
                b = by_objective(held, **start)["indifferent"]
                need(a == b, f"a_rights = none: {a}; a_rights = continuity held: {b}")
                return f"membership {a} either way"

            p.check(f"indifferent: {name} from s0{start or ''}", same)

    def same_sets():
        # G2's relaxation questions under indifferent are the negated holds of its conditions
        # (1) and (2); the unconditioned ending is compared beside them.
        out = {}
        for name, (profiles, start, target) in G2_QUESTIONS.items():
            a, b = (
                relax(
                    cm := fixed(
                        "indifferent", (*under("indifferent"), *profiles), start=start, **kw
                    ),
                    K24,
                    target(cm),
                )
                for kw in ({}, HELD)
            )
            out[name] = same_relaxations(
                a, b, "a_rights = none", "a_rights = continuity held", held=profiles
            )
        return out

    p.check("indifferent: G2's minimal sets identical", same_sets)
    p.skip(
        "indifferent: pivotal coalitions identical",
        "G15's 21 blocker kernels on the held build are outside the first-sight budget",
    )
    p.report("readers of a_rights", lambda: readers(compiled(), "a_rights"))
    p.finish()
