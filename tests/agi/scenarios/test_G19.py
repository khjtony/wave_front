"""G19: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from models.agi import v0
from tests.agi.common import (
    KD,
    KH,
    OBJECTIVES,
    NotComputed,
    Parts,
    compiled,
    first_sight,
    inside,
    need,
    s0,
    shift,
)

CLAIM = {
    "id": "G19",
    "from_state": "`s₀` and `s₀` with `cap := agi`",
    "claim": (
        "sensitivity (DESIGN.md Q7): under ±1 level shifts of each variable, per "
        "`a_objective`, the ranking by membership flips and distance change for "
        "`⟨⟨H⟩⟩□balance_control` places `oversight` and `a_autonomy` above `regime` and "
        "`compute` (the G2 ordering), and `h_power` ranks above `oversight` for "
        "`balance_deter` only; the top-ranked variable per objective is the report's "
        "indicator of the quarter"
    ),
    "expected": "the ranking per objective and predicate; the two orderings",
    "sources": (
        "DESIGN.md section 3.4 (Q7); coldwar_testbed.md C10; framework_spec.md section 7 "
        "(`sensitivity`)"
    ),
}

# The ranking is by membership flips over the ±1 shifts from both states; the distance
# change that would break ties is outside the budget, so a tie leaves an ordering undecided.
JOBS = [KH, KD]
KERNELS = {"balance_control": KH, "balance_deter": KD}
STATES = ({}, {"cap": "agi"})
G2_ORDER = [(hi, lo) for hi in ("oversight", "a_autonomy") for lo in ("regime", "compute")]


def flips(objective: str, job) -> dict[str, int]:
    cm = compiled()
    out = dict.fromkeys(v0.LEVELS, 0)
    for levels in STATES:
        state = s0(cm, objective, **levels)
        base = inside(job, cm, state)
        for var in v0.LEVELS:
            for by in (-1, 1):
                moved = shift(cm, state, var, by)
                if moved is not None and inside(job, cm, moved) != base:
                    out[var] += 1
    return out


def ranking(objective: str) -> dict[str, object]:
    out = {}
    for name, job in KERNELS.items():
        n = flips(objective, job)
        top = max(n.values())
        out[name] = {
            "flips": dict(sorted(n.items(), key=lambda kv: -kv[1])),
            "top": [v for v, x in n.items() if x == top] if top else "no shift flips membership",
        }
    return out


def ordered(n: dict[str, int], pairs, what: str) -> str:
    """Every ``hi`` strictly above its ``lo`` on flips; a tie is undecided."""
    below = [(hi, lo) for hi, lo in pairs if n[hi] < n[lo]]
    need(not below, f"{what}: ranked below on flips {below}; flips {n}")
    tied = [(hi, lo) for hi, lo in pairs if n[hi] == n[lo]]
    if tied:
        raise NotComputed(f"{what}: tied on flips {tied}; the distance change is not computed")
    return f"{what}: holds on flips { ({v: n[v] for pair in pairs for v in pair}) }"


def deter_only(objective: str) -> str:
    deter, control = flips(objective, KD), flips(objective, KH)
    need(
        control["h_power"] <= control["oversight"],
        f"h_power ranks above oversight for balance_control as well: {control}",
    )
    got = ordered(deter, [("h_power", "oversight")], "h_power above oversight, balance_deter")
    if control["h_power"] == control["oversight"]:
        raise NotComputed(
            f"{got}; for balance_control h_power and oversight tie on flips {control}; the "
            'distance change is not computed, so "only" is undecided'
        )
    return got


@first_sight
def test_G19():
    p = Parts("G19")
    for objective in OBJECTIVES:
        p.report(f"ranking, {objective}", lambda o=objective: ranking(o))
        p.check(
            f"the G2 ordering, {objective}",
            lambda o=objective: ordered(flips(o, KH), G2_ORDER, "balance_control"),
        )
        p.check(f"h_power, {objective}", lambda o=objective: deter_only(o))
    p.finish()
