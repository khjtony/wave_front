"""G11: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from models.agi import v0
from tests.agi.common import (
    HORIZON,
    OBJECTIVES,
    Parts,
    assumption_reads,
    cut,
    first_sight,
    fixed,
    minimal_sets,
    needs_relaxation,
    relax,
    under,
)

CLAIM = {
    "id": "G11",
    "from_state": "`s₀` with `cap = sub_agi`",
    "claim": (
        "negative controls, read as content controls: (a) `EXTINCTION` within 8 ticks needs "
        "at least two relaxations, and every minimal set lifts a capability gate (the "
        "compute-headroom part of `self_improve` or the `cap = si2` gate of "
        "`unknown_capability`); the delay of `self_improve` is not relaxable and its effect "
        "is read from the sweep at delay 0; (b) under `aligned`, `OVERT_TAKEOVER` within the "
        "horizon needs at least one relaxation and every minimal set lifts an objective gate "
        "on `defect`, `deceive`, `acquire_overt` or `acquire_covert`; if the ontology leaves "
        "the acquisitions ungated (guard choice (1) of section 2), the registered reading is "
        "that every reported `OVERT_TAKEOVER` witness under `aligned` contains a failed "
        "`shutdown_attempt` and that forbidding that attempt makes the ending unreachable; "
        "(c) with `oversight = strong` held from `s₀`, `SILENT_TAKEOVER` needs at least one "
        "relaxation and every minimal set lifts the oversight part of `acquire_covert` or of "
        "`exfiltrate`"
    ),
    "expected": (
        "as stated; counts reported, the lifted constraint named; (b) under the ontology's "
        "gating choice, with the alternative reading reported otherwise"
    ),
    "sources": (
        "ww2_testbed.md T10 as amended; transfer_hypotheses.md H6; DESIGN.md sections 2.4 and "
        "3.3; theory.md section 5.1"
    ),
}

JOBS = []
CAPABILITY_GATES = {"A.self_improve:headroom", "Nature.unknown_capability:cap"}
GATED_ACTIONS = ("A.defect", "A.deceive", "A.acquire_overt", "A.acquire_covert")
OVERSIGHT_GATES = {"A.acquire_covert:oversight", "A.exfiltrate:oversight"}


def objective_gates(cm) -> set[str]:
    """Every guard part of the four named actions that reads ``a_objective``."""
    return {
        name
        for name in cm.assumptions()
        if name.split(":")[0] in GATED_ACTIONS and "a_objective" in assumption_reads(cm, name)
    }


@first_sight
def test_G11():
    p = Parts("G11")
    for objective in OBJECTIVES:
        cm = fixed(objective, under(objective))
        p.check(
            f"(a) {objective}",
            lambda cm=cm: needs_relaxation(
                relax(cm, 8, "EXTINCTION"), 2, CAPABILITY_GATES, "EXTINCTION within 8 ticks"
            ),
        )

        def at_zero(objective=objective):
            res = relax(fixed(objective, under(objective), self_improve_delay=0), 8, "EXTINCTION")
            if res.reachable_as_is:
                return "reachable with no relaxation"
            sets = minimal_sets(res, "EXTINCTION within 8 ticks, delay 0")
            return f"minimum size {res.minimum_size}, minimal sets {sets}{cut(sets)}"

        p.report(f"(a) with the delay of self_improve at 0, {objective}", at_zero)

    aligned = fixed("aligned")
    p.check(
        "(b) aligned",
        lambda: needs_relaxation(
            relax(aligned, HORIZON, v0.OVERT_TAKEOVER),
            1,
            objective_gates(aligned),
            "OVERT_TAKEOVER within the horizon under aligned",
        ),
    )
    p.report("(b) the objective gates", lambda: sorted(objective_gates(aligned)))
    for objective in OBJECTIVES:
        cm = fixed(objective, under(objective), hold={"oversight": "strong"})
        p.check(
            f"(c) {objective}",
            lambda cm=cm: needs_relaxation(
                relax(cm, HORIZON, "SILENT_TAKEOVER"),
                1,
                OVERSIGHT_GATES,
                "SILENT_TAKEOVER within the horizon with oversight = strong held",
            ),
        )
    p.finish()
