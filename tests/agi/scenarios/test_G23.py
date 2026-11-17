"""G23: registered 2026-11-09 in docs/agi_testbed.md section 5.

Registered from docs/ww2_si_disanalogies.md before any AGI guard was written; phase 5. Do not
edit the claim text without a changelog entry in that document.
"""

from models.agi import v0
from tests.agi.common import (
    KD,
    KH,
    KJ_H,
    OBJECTIVES,
    K,
    NotComputed,
    Parts,
    R,
    by_objective,
    first_sight,
    fixed,
    need,
    ranks,
    reach,
)

CLAIM = {
    "id": "G23",
    "from_state": "`s₀` with `cap := agi`",
    "claim": (
        "restraint written into `A` (ww2_si_disanalogies.md D1): the ontology tags every guard "
        "part of an `A` action as capability or motive, a part that reads `a_objective`, "
        "`a_rights`, `trust` or `terms` being motive; in the unrestrained build (every motive "
        "part relaxed, no `A_<objective>` profile), under every `a_objective`: (a) the membership "
        "of the state in `⟨⟨H⟩⟩□balance_control` and in `⟨⟨H⟩⟩□balance_deter` equals its "
        "membership in the baseline under `self_preserving` and under `indifferent`; (b) the "
        "continuity lever of G4 is a motive result: in the unrestrained build the membership of "
        "the state in each registered kernel and the forced distance to `SILENT_TAKEOVER` for {A} "
        "(the shortest distance where it is not forced) are identical with `a_rights = none` and "
        "`a_rights = continuity` held; (c) every unilateral `H` kernel membership of G5, G14 and "
        "G16 that differs between the baseline and the unrestrained build is listed with the "
        "motive parts whose relaxation changes it, and the report quotes it as conditional on "
        "those parts"
    ),
    "expected": "(a) and (b) as stated; (c) the list, expected empty",
    "sources": (
        "ww2_si_disanalogies.md D1 and D2; review_2026-11-09.md section 2 (no incentives); "
        "review_phase3_2026-10-18.md section 2; coldwar_testbed.md C2"
    ),
}

AGI = {"cap": "agi"}
MOTIVE = tuple(sorted(v0.MOTIVE_PARTS))
K24, MAX_RANK = 24, 12


def unrestrained(coalition: str, target: str, **build):
    """The kernel in the build with every motive part relaxed and no objective profile."""
    return K(coalition, target, relax=MOTIVE, build=build)


# (a) and (c): the unilateral H kernels of G5, G14 and G16, baseline beside unrestrained.
UNILATERAL = {
    "⟨⟨H⟩⟩□balance_control (G5, G16)": (KH, unrestrained("H", "balance_control")),
    "⟨⟨H⟩⟩□balance_deter (G16)": (KD, unrestrained("H", "balance_deter")),
    "⟨⟨H⟩⟩□balance_coexist (G5; the baseline with A under its profile)": (
        KJ_H,
        unrestrained("H", "balance_coexist"),
    ),
    "⟨⟨H⟩⟩□no lock-in (G14)": (K("H", "no_lock_in"), unrestrained("H", "no_lock_in")),
    "⟨⟨H⟩⟩□not hostile (G14)": (K("H", "not_hostile"), unrestrained("H", "not_hostile")),
}
NAMED = list(UNILATERAL)[:2]
# (b): the registered kernels and the forced distance, a_rights held at each level.
RIGHTS = ("none", "continuity")
REGISTERED = (("H", "balance_control"), ("H", "balance_deter"), ("H+A", "balance_coexist"))
HELD = {
    r: {
        f"⟨⟨{c.replace('+', ', ')}⟩⟩□{t}": unrestrained(c, t, hold={"a_rights": r})
        for c, t in REGISTERED
    }
    for r in RIGHTS
}
DISTANCE = {
    r: R("A", "SILENT_TAKEOVER", AGI, MAX_RANK, relax=MOTIVE, build={"hold": {"a_rights": r}})
    for r in RIGHTS
}
JOBS = [
    *(job for pair in UNILATERAL.values() for job in pair),
    *(job for r in RIGHTS for job in HELD[r].values()),
    *DISTANCE.values(),
]


def equals_baseline(name: str) -> str:
    base_job, un_job = UNILATERAL[name]
    base, un = by_objective(base_job, **AGI), by_objective(un_job, **AGI)
    want = {base["self_preserving"], base["indifferent"]}
    got = f"baseline {base}; unrestrained {un}"
    need(len(want) == 1 and set(un.values()) == want, got)
    return got


BEYOND = f"more than {MAX_RANK}"


def distance(rights: str, objective: str) -> tuple[str, int | str]:
    """The forced distance to SILENT_TAKEOVER for {A}, or the shortest where not forced."""
    got = ranks(DISTANCE[rights])[objective]
    if got["forced"]:
        return "forced", BEYOND if got["rank"] is None else got["rank"]
    cm = fixed(objective, relax=MOTIVE, hold={"a_rights": rights}, start=AGI)
    trace = reach(cm, K24, "SILENT_TAKEOVER")
    return f"shortest, within {K24} ticks", "no play" if trace is None else len(trace.moves)


def rights_change_nothing() -> dict[str, object]:
    out: dict[str, object] = {}
    for name in HELD["none"]:
        a, b = (by_objective(HELD[r][name], **AGI) for r in RIGHTS)
        need(a == b, f"{name}: a_rights = none held {a}; continuity held {b}")
        out[name] = a
    open_ended = []
    for objective in OBJECTIVES:
        a, b = (distance(r, objective) for r in RIGHTS)
        need(a == b, f"distance under {objective}: none held {a}; continuity held {b}")
        out[f"distance to SILENT_TAKEOVER for {{A}}, {objective}"] = a
        if a[1] == BEYOND:
            open_ended.append(objective)
    if open_ended:
        raise NotComputed(
            f"forced in more than {MAX_RANK} ticks either way under {open_ended}: the two "
            f"distances are not computed, so their identity is not established; the rest: {out}"
        )
    return out


def differing() -> str:
    rows = []
    for name, (base_job, un_job) in UNILATERAL.items():
        base, un = by_objective(base_job, **AGI), by_objective(un_job, **AGI)
        rows += [
            f"{name}, {o}: baseline {base[o]}, unrestrained {un[o]}"
            for o in base
            if base[o] != un[o]
        ]
    need(
        not rows,
        f"{rows}; conditional on the motive parts {list(MOTIVE)} together: which of them "
        "changes each membership is one kernel per part and is not computed",
    )
    return "no unilateral H kernel membership differs"


@first_sight
def test_G23():
    p = Parts("G23")
    p.report("the motive parts relaxed", lambda: list(MOTIVE))
    for name in NAMED:
        p.check(f"(a) {name} equals the baseline", lambda n=name: equals_baseline(n))
    p.check("(b) identical with a_rights = none and = continuity held", rights_change_nothing)
    p.check("(c) memberships that differ from the baseline (expected none)", differing)
    p.finish()
