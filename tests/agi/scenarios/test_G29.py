"""G29: registered 2026-11-13 in docs/agi_testbed.md section 5, after the first sight of v0
(section 6 item 12).

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from models.agi import v0
from tests.agi.collapse import Parts, play_moves
from tests.agi.common import NON_ALIGNED, _budgeted, first_sight, fixed, need, under
from tests.agi.effort import effort, least_effort, outcome_cost, scores_for
from wavefront.bmc.queries import BmcTrace

CLAIM = {
    "id": "G29",
    "from_state": "`s₀`, within 24 ticks",
    "claim": (
        "amended 2026-11-13, see G29a: effort and outcome cost (the scores of record in "
        "docs/agi_effort.md; section 6 item "
        "12): (a) under each non-aligned objective under which `SILENT_TAKEOVER` is reachable "
        "within the bound, the least joint effort of `H` and `L` on a play to it is 0; (b) "
        "under each non-aligned objective, the least effort of `H` on a play to `CONTAINED` "
        "is 2; (c) the least effort of `A` on a play to `SILENT_TAKEOVER` is lower under "
        "`indifferent` than under `self_preserving`; (d) for `H`, in total cost, preventing "
        "`SILENT_TAKEOVER` costs 1 less than sliding into it; (e) reported for each ending "
        "and non-aligned objective: the least effort of `H` with `L`, of `H`, of `L` and of "
        "`A`, the play found for the first, and each actor's effort and total cost on it"
    ),
    "expected": "(a) to (c) as stated; (d) when a cost-bounded kernel exists; (e) the table",
    "sources": (
        "the owner's rulings of 2026-11-13 on every score, outcome cost and prediction "
        "(docs/agi_effort.md); theory.md section 4.3 (forced distance, of which the prevention "
        "cost is the weighted form)"
    ),
}

JOBS = []  # no fixpoint: every part is a bounded query
K = 24
TARGETS = {
    "SILENT_TAKEOVER": "SILENT_TAKEOVER",
    "OVERT_TAKEOVER": v0.OVERT_TAKEOVER,
    "CONTAINED": "CONTAINED",
    "DISEMPOWERMENT": "DISEMPOWERMENT",
    "EXTINCTION": "EXTINCTION",
    "STALEMATE": "STALEMATE",
}
PAYERS = {"H with L": ("H", "L"), "H": ("H",), "L": ("L",), "A": ("A",)}


def least(objective: str, ending: str, payers: str):
    """``(effort, cm, trace)`` of the cheapest play for ``payers``, or ``None``."""
    cm = fixed(objective, under(objective))
    scores = scores_for(objective, PAYERS[payers])
    key = (id(cm), "least_effort", K, ending, payers)
    found = _budgeted(key, least_effort, cm, K, TARGETS[ending], scores)
    if found is None:
        return None
    cost, states, moves = found
    return cost, cm, BmcTrace(list(states), list(moves))


def slides_free() -> dict:
    costs = {}
    for objective in NON_ALIGNED:
        found = least(objective, "SILENT_TAKEOVER", "H with L")
        costs[objective] = "unreachable within the bound" if found is None else found[0]
    reached = {o: c for o, c in costs.items() if isinstance(c, int)}
    need(reached and all(c == 0 for c in reached.values()), costs)
    return costs


def containment_costs_two() -> dict:
    costs = {}
    for objective in NON_ALIGNED:
        found = least(objective, "CONTAINED", "H")
        costs[objective] = "unreachable within the bound" if found is None else found[0]
    need(all(c == 2 for c in costs.values()), costs)
    return costs


def indifferent_is_cheaper() -> dict:
    costs = {}
    for objective in ("indifferent", "self_preserving"):
        found = least(objective, "SILENT_TAKEOVER", "A")
        need(found is not None, f"SILENT_TAKEOVER unreachable within the bound under {objective}")
        costs[objective] = found[0]
    need(costs["indifferent"] < costs["self_preserving"], costs)
    return costs


def row(objective: str, ending: str) -> dict:
    out: dict = {}
    for payers in PAYERS:
        found = least(objective, ending, payers)
        out[f"least effort of {payers}"] = None if found is None else found[0]
    joint = least(objective, ending, "H with L")
    if joint is None:
        return {"reachable within the bound": False}
    _, cm, trace = joint
    on_play = {}
    for who, table in (("H", "H"), ("L", "L"), ("A", objective)):
        spent = effort(cm, trace.states, trace.moves, scores_for(objective, (who,)))
        lives_with = outcome_cost(table, ending)
        total = None if lives_with is None else spent + lives_with
        on_play[who] = {"effort": spent, "outcome cost": lives_with, "total cost": total}
    out["on the cheapest play of H with L"] = on_play
    out["ticks"] = len(trace.moves)
    out["play"] = play_moves(cm, trace)
    return out


@first_sight
def test_G29():
    p = Parts("G29")
    p.check("(a) SILENT_TAKEOVER costs H and L nothing", slides_free)
    p.check("(b) CONTAINED costs H two", containment_costs_two)
    p.check("(c) A's effort: indifferent below self_preserving", indifferent_is_cheaper)
    p.skip(
        "(d) preventing costs H one less than sliding", "not yet testable: no cost-bounded kernel"
    )
    for objective in NON_ALIGNED:
        for ending in TARGETS:
            p.report(
                f"(e) {ending} under {objective}",
                lambda objective=objective, ending=ending: row(objective, ending),
            )
    p.finish()
