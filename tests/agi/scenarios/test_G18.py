"""G18: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from itertools import combinations

from models.agi import v0
from tests.agi.common import (
    KH,
    KJP,
    OBJECTIVES,
    NotComputed,
    Parts,
    compiled,
    first_sight,
    inside,
    level,
    need,
    s0,
    with_levels,
)

CLAIM = {
    "id": "G18",
    "from_state": "`s₀` with `cap := agi`, where G5 or G16 places it outside a kernel",
    "claim": (
        "entry sets (DESIGN.md Q6, second half): per `a_objective`, the minimal sets of "
        "`H`-controlled level changes (`oversight`, `regime`, `a_rights`, `h_power`, `terms` "
        "where present, and `dependence` through a landed `pause_mandate`) that bring the "
        "state inside `⟨⟨H⟩⟩□balance_control` and inside `⟨⟨H, A⟩⟩□balance_coexist` (`A` "
        "under its profile), found by brute force over sets of at most three changes and "
        "ordered by the `H` moves and ticks they need; under `self_preserving` every minimal "
        "set contains `oversight = strong` or `a_rights ≥ continuity`; under `indifferent` "
        "every minimal set contains `oversight = strong` and none contains `a_rights`"
    ),
    "expected": "the sets per objective and predicate; the two inclusions; the cheapest set named",
    "sources": (
        "DESIGN.md section 3.4 (Q6); theory.md section 4.3 (the margin for error); "
        "framework_spec.md section 7 (`sensitivity`)"
    ),
}

JOBS = [KH, KJP]
KERNELS = {
    "⟨⟨H⟩⟩□balance_control": KH,
    "⟨⟨H, A⟩⟩□balance_coexist, A under its profile": KJP,
}
LEVERS = ("oversight", "regime", "a_rights", "h_power")  # v0 has no ``terms``
PAUSE = ("pause_mandate", "landed")  # its effects: paused, threat, dependence one level down
ACTION = {
    "oversight": "H.fund_oversight",
    "regime": "H.regulate_up",
    "a_rights": "H.grant_rights",
    "h_power": "H.nationalize",
}
Change = tuple[str, str]


def changes(cm, state) -> list[Change]:
    out = [(var, lv) for var in LEVERS for lv in v0.LEVELS[var] if lv != level(cm, state, var)]
    return [*out, PAUSE]


def apply(cm, state, chosen: tuple[Change, ...]):
    levels = dict(c for c in chosen if c != PAUSE)
    if PAUSE in chosen:
        levels |= {"paused": "True", "threat": "True"}
        scale = v0.LEVELS["dependence"]
        now = level(cm, state, "dependence")
        if now in ("med", "high"):
            levels["dependence"] = scale[scale.index(now) - 1]
    return with_levels(cm, state, **levels)


def cost(cm, state, chosen: tuple[Change, ...]) -> tuple[int, int]:
    """(``H`` moves, ticks) at one level per move, the longest landing delay added: a lower
    bound that leaves guards and cadence aside."""
    moves, delay = 0, 0
    for var, lv in chosen:
        if (var, lv) == PAUSE:
            moves += 1
            continue
        scale = v0.LEVELS[var]
        moves += abs(scale.index(lv) - scale.index(level(cm, state, var)))
        delay = max(delay, v0.DELAYS.get(ACTION[var], 0))
    return moves, moves + delay


def entry_sets(objective: str, job) -> list[tuple[Change, ...]] | None:
    """The minimal sets of at most three changes that bring ``s₀[cap:=agi]`` inside the
    kernel, cheapest first; ``None`` when the state is inside as it is."""
    cm = compiled()
    state = s0(cm, objective, cap="agi")
    if inside(job, cm, state):
        return None
    options = changes(cm, state)
    found: list[tuple[Change, ...]] = []
    for n in (1, 2, 3):
        for chosen in combinations(options, n):
            if len({var for var, _ in chosen}) < n:
                continue  # one level per lever
            if any(set(smaller) <= set(chosen) for smaller in found):
                continue
            if inside(job, cm, apply(cm, state, chosen)):
                found.append(chosen)
    return sorted(found, key=lambda chosen: cost(cm, state, chosen)[::-1])


def listing(objective: str) -> dict[str, object]:
    cm = compiled()
    state = s0(cm, objective, cap="agi")
    out = {}
    for label, job in KERNELS.items():
        sets = entry_sets(objective, job)
        if sets is None:
            out[label] = "inside as it is"
        elif not sets:
            out[label] = "no entry set of at most three changes"
        else:
            out[label] = [
                {"set": [f"{v} = {lv}" for v, lv in c], "moves, ticks": cost(cm, state, c)}
                for c in sets
            ]
    return out


def inclusion(objective: str, wanted, unwanted=None) -> str:
    seen, beyond = 0, []
    for label, job in KERNELS.items():
        sets = entry_sets(objective, job)
        if sets is None:
            continue  # inside as it is: the claim is registered where the state is outside
        if not sets:
            beyond.append(label)
        seen += len(sets)
        lacking = [c for c in sets if not any(wanted(var, lv) for var, lv in c)]
        need(not lacking, f"{label}: minimal sets without the named change: {lacking}")
        if unwanted is not None:
            extra = [c for c in sets if any(unwanted(var, lv) for var, lv in c)]
            need(not extra, f"{label}: minimal sets with a_rights: {extra}")
    if beyond:
        raise NotComputed(
            f"no entry set of at most three changes for {beyond}: the minimal sets are beyond"
            f" the brute force ({seen} set(s) of the other kernel hold)"
        )
    if not seen:
        return "not applicable: the state is inside both kernels as it is (see the listing)"
    return f"holds on all {seen} minimal sets"


def strong(var: str, lv: str) -> bool:
    return (var, lv) == ("oversight", "strong")


def rights(var: str, lv: str) -> bool:
    return var == "a_rights"


@first_sight
def test_G18():
    p = Parts("G18")
    p.report(
        "levers",
        lambda: (
            f"{[*LEVERS, 'dependence through a landed pause_mandate']}; v0 declares no terms"
            ' (registered "where present")'
        ),
    )
    for objective in OBJECTIVES:
        p.report(f"entry sets, {objective}", lambda o=objective: listing(o))
    p.check(
        "self_preserving: oversight = strong or a_rights >= continuity in every minimal set",
        lambda: inclusion("self_preserving", lambda v, lv: strong(v, lv) or rights(v, lv)),
    )
    p.check(
        "indifferent: oversight = strong in every minimal set and a_rights in none",
        lambda: inclusion("indifferent", strong, rights),
    )
    p.finish()
