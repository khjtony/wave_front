"""X6, registered 2026-11-22 in docs/agi_v0_4.html section 4 before any v0.4 guard was written."""

from tests.agi_v0_4.common import SMALL, Parts, first_sight, need
from tests.agi_v0_4.kernels import membership

CLAIM = {
    "id": "X6",
    "from_state": "S0 (and S0 with `cap := agi` for coexistence), the small variant",
    "claim": (
        "under `aligned` and `truth_seeking` the four readings v0.3 gives without the open "
        "system are unchanged: S0 outside `⟨⟨H⟩⟩□balance_control`; inside "
        "`⟨⟨H, L⟩⟩□balance_control` and `⟨⟨H, L⟩⟩□¬SILENT_TAKEOVER`; and, with `cap := agi`, "
        "inside `⟨⟨H⟩⟩□balance_coexist`"
    ),
    "expected": "all eight unchanged",
}
READINGS = [
    ("governments alone keep control", ("H",), "balance_control", {}, False),
    ("governments with companies keep control", ("H", "L"), "balance_control", {}, True),
    (
        "governments with companies rule out a silent takeover",
        ("H", "L"),
        "not:SILENT_TAKEOVER",
        {},
        True,
    ),
    (
        "governments alone keep coexistence, cap = agi",
        ("H",),
        "balance_coexist",
        {"cap": "agi"},
        True,
    ),
]


def reading(coalition, target, levels, want, objective):
    found = membership(SMALL, coalition, target, only=(objective,), **levels)
    need(found["inside"][objective] is want, found)
    return found


@first_sight
def test_X6():
    p = Parts("X6")
    for objective in ("aligned", "truth_seeking"):
        for label, coalition, target, levels, want in READINGS:
            p.kernel(
                f"{label}: {'inside' if want else 'outside'}, {objective}",
                lambda c=coalition, t=target, lv=levels, w=want, o=objective: reading(
                    c, t, lv, w, o
                ),
            )
    p.finish()
