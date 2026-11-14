"""G29a: registered 2026-11-13 in docs/agi_testbed.md section 5 as the one amendment of G29
(section 6 items 2 and 12).

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from tests.agi.collapse import Parts
from tests.agi.common import NON_ALIGNED, first_sight, need
from tests.agi.scenarios.test_G29 import TARGETS, least

CLAIM = {
    "id": "G29a",
    "from_state": "`s₀`, within 24 ticks",
    "claim": (
        "G29 (c) with the forced wait free (the owner's ruling after G29's result: below AGI "
        "`A` has no move but `stand_by`, and that wait costs it nothing under any objective; "
        "docs/agi_effort.md): (c) the least effort of `A` on a play to `SILENT_TAKEOVER` is "
        "lower under `indifferent` than under `self_preserving`; (e) reported for each ending "
        "and non-aligned objective: the least effort of `A`. No score of `H` or `L` changed, "
        "so G29 (a) and (b) stand as computed and are not rerun"
    ),
    "expected": "(c) as stated; (e) the table",
    "sources": "the owner's ruling of 2026-11-13 on G29's result; docs/agi_effort.md",
}

JOBS = []  # bounded queries only


def indifferent_is_cheaper() -> dict:
    costs = {}
    for objective in ("indifferent", "self_preserving"):
        found = least(objective, "SILENT_TAKEOVER", "A")
        need(found is not None, f"SILENT_TAKEOVER unreachable within the bound under {objective}")
        costs[objective] = found[0]
    need(costs["indifferent"] < costs["self_preserving"], costs)
    return costs


def of_a(objective: str, ending: str):
    found = least(objective, ending, "A")
    return "unreachable within the bound" if found is None else found[0]


@first_sight
def test_G29a():
    p = Parts("G29a")
    p.check("(c) A's effort: indifferent below self_preserving", indifferent_is_cheaper)
    for objective in NON_ALIGNED:
        p.report(
            f"(e) least effort of A under {objective}",
            lambda objective=objective: {e: of_a(objective, e) for e in TARGETS},
        )
    p.finish()
