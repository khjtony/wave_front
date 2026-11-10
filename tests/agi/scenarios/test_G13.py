"""G13: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from models.agi import v0
from tests.agi.common import (
    OBJECTIVES,
    A,
    K,
    NotComputed,
    P,
    Parts,
    compiled,
    first_sight,
    s0,
    status,
)
from wavefront.analysis import fingerprint

CLAIM = {
    "id": "G13",
    "from_state": "`s₀`",
    "claim": (
        "abstraction robustness (content check, not hold-out): with each variable's level "
        "count refined by one in turn (3 to 4, 4 to 5) under a rule fixed before first sight "
        "(the refinement of v splits the boundary that `s₀`'s indicator straddles, or the "
        "middle boundary when none does; a guard, ending or balance predicate written on an "
        "old level maps to the lower new boundary; `s₀` maps by its indicator rule; each "
        "refined build is listed with its fingerprint), the forced, blocked or contested "
        "status of every ending for `{H}` and `{A}` from `s₀` with `cap := agi`, per "
        "`a_objective` and with the fortune variants, does not change; a status that flips is "
        "reported with the level boundary that caused it"
    ),
    "expected": "statuses stable under refinement, or the threshold named as a finding",
    "sources": (
        "DESIGN.md section 8 (abstraction robustness); ww2_testbed.md T13 (the departure "
        "quarter stable within two quarters from v0 to v1, the nearest precedent)"
    ),
}

# The budget carries one status per build: SILENT_TAKEOVER for {A} (forced by {A}, kept
# away by everyone else, or contested), A under its profile. The other endings, {H} and
# the fortune variants are not computed.
ENDING = "SILENT_TAKEOVER"
REST = "H+L+Clock+Nature"


def pair(**build):
    return A("A", ENDING, P, build=build), K(REST, f"not:{ENDING}", P, build=build)


BASELINE = pair()
REFINED = {var: pair(refine=var) for var in sorted(v0.REFINE)}
JOBS = [*BASELINE, *(job for jobs in REFINED.values() for job in jobs)]


def statuses(jobs) -> dict[str, str]:
    forced, blocked = jobs
    cm = compiled(forced.build)
    return {o: status(forced, blocked, cm, s0(cm, o, cap="agi")) for o in OBJECTIVES}


def refinement(p: Parts, var: str) -> None:
    """The registered expectation is "stable, or the threshold named as a finding": an
    unchanged status is a part met, a flip is reported with its boundary and fails nothing."""
    try:
        base, refined = statuses(BASELINE), statuses(REFINED[var])
    except NotComputed as exc:
        p.skip(f"refine {var}", str(exc))
        return
    upper = v0.REFINE[var]
    if refined == base:
        p.check(f"refine {var}: status unchanged", lambda: f"{ENDING} for {{A}}: {base}")
    else:
        p.report(
            f"refine {var}: the status flips (finding)",
            lambda: (
                f"{ENDING} for {{A}} changes when {var} gains {upper}_lo below {upper}:"
                f" baseline {base}, refined {refined}"
            ),
        )


def builds() -> dict[str, dict[str, str]]:
    out = {"baseline": {"fingerprint": fingerprint(v0.build())}}
    for var in REFINED:
        upper = v0.REFINE[var]
        out[var] = {
            "new level": f"{upper}_lo below {upper}",
            "fingerprint": fingerprint(v0.build(refine=var)),
        }
    return out


@first_sight
def test_G13():
    p = Parts("G13")
    p.report("refined builds", builds)
    for var in REFINED:
        refinement(p, var)
    p.skip(
        "the other five endings, {H} and the fortune variants",
        "16 builds × 6 endings × 2 actors × 2 variants × 2 fixpoints is 768 fixpoints;"
        " the budget of this run carries 32",
    )
    p.finish()
