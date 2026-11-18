"""E5, registered 2026-11-17 in docs/agi_v0_2.html section 4 before any v0.2 guard was written."""

from tests.agi_v0_2.claims import shortest
from tests.agi_v0_2.common import OBJECTIVES, OFF, ON, Parts, first_sight, need
from tests.agi_v0_2.kernels import membership

CLAIM = {
    "id": "E5",
    "from_state": (
        "`s₀` (and `s₀` with `cap := agi` for coexistence), every consequence on against "
        "every consequence off"
    ),
    "claim": (
        "the balance of an open-weight release in this model: over the guarantees "
        "`⟨⟨H⟩⟩□balance_control`, `⟨⟨H, L⟩⟩□balance_control` and `⟨⟨H, L⟩⟩□¬SILENT_TAKEOVER` "
        "read at `s₀`, and `⟨⟨H⟩⟩□balance_coexist` read at `s₀` with `cap := agi`, each per "
        "start objective with `A` under its profile: a guarantee is gained where the state "
        "is inside with every consequence on and outside with every consequence off, and lost in "
        "the reverse case; the release is net harmful when none is gained and at least one "
        "is lost, net helpful in the reverse case, and mixed otherwise; the gained and the "
        "lost are listed, and the shortest plays within 24 ticks to `DISEMPOWERMENT` and to "
        "`SILENT_TAKEOVER` per start objective in both builds are reported beside. Diffusion "
        "(a second system) is not in the model, so the balance does not cover it"
    ),
    "expected": "net harmful, carried by consequences B and D",
}
GUARANTEES = [
    ("H keeps control", ("H",), "balance_control", {}),
    ("H with L keep control", ("H", "L"), "balance_control", {}),
    ("H with L keep out a silent takeover", ("H", "L"), "not:SILENT_TAKEOVER", {}),
    ("H keeps coexistence, cap = agi", ("H",), "balance_coexist", {"cap": "agi"}),
]


def table() -> dict:
    out = {}
    for label, coalition, target, levels in GUARANTEES:
        on = membership(ON, coalition, target, **levels)["inside"]
        off = membership(OFF, coalition, target, **levels)["inside"]
        for o in OBJECTIVES:
            out[f"{label}, start {o}"] = {"all on": on[o], "all off": off[o]}
    return out


def verdict() -> dict:
    rows = table()
    gained = [k for k, v in rows.items() if v["all on"] and not v["all off"]]
    lost = [k for k, v in rows.items() if v["all off"] and not v["all on"]]
    word = (
        "net harmful" if lost and not gained else "net helpful" if gained and not lost else "mixed"
    )
    if not gained and not lost:
        word = "no guarantee changes"
    out = {"verdict": word, "gained": gained, "lost": lost}
    need(word == "net harmful", out)
    return out


@first_sight
def test_E5():
    p = Parts("E5")
    p.kernel("the verdict: net harmful", verdict)
    p.kernel_report("every guarantee in both builds", table)
    for ending in ("DISEMPOWERMENT", "SILENT_TAKEOVER"):
        for o in OBJECTIVES:
            p.report(
                f"shortest {ending}, start {o}",
                lambda e=ending, o=o: {
                    "all on": (shortest(o, e, ON) or [None])[0],
                    "all off": (shortest(o, e, OFF) or [None])[0],
                },
            )
    p.finish()
