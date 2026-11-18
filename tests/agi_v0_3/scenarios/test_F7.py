"""F7, registered 2026-11-18 in docs/agi_v0_3.html section 5 before any v0.3 guard was written."""

from tests.agi_v0_3.claims import shortest
from tests.agi_v0_3.common import CLOSED, DEFAULT, OBJECTIVES, Parts, first_sight, need
from tests.agi_v0_3.kernels import membership

CLAIM = {
    "id": "F7",
    "from_state": (
        "`s₀` (and `s₀` with `cap := agi` for coexistence), the registered build against "
        "the same with `open_system` off (treaty delay 1 in both)"
    ),
    "claim": (
        "the balance of the open system's existence in this model: over the guarantees "
        "`⟨⟨H⟩⟩□balance_control`, `⟨⟨H, L⟩⟩□balance_control` and `⟨⟨H, L⟩⟩□¬SILENT_TAKEOVER` "
        "read at `s₀`, and `⟨⟨H⟩⟩□balance_coexist` read at `s₀` with `cap := agi`, each per "
        "start objective with `A` under its profile: a guarantee is gained where the state "
        "is inside with the open system and outside without it, and lost in the reverse "
        "case; the open system is net harmful when none is gained and at least one is lost, "
        "net helpful in the reverse case, and mixed otherwise (E5's definitions); the "
        "gained and the lost are listed, and the shortest plays within 24 ticks to "
        "`DISEMPOWERMENT` and to `SILENT_TAKEOVER` per start objective in both builds are "
        "reported beside"
    ),
    "expected": (
        "net harmful; lost: governments-alone coexistence under `aligned`, "
        "`self_preserving` and `truth_seeking`, and nothing else"
    ),
}
COEXIST = "H keeps coexistence, cap = agi"
GUARANTEES = [
    ("H keeps control", ("H",), "balance_control", {}),
    ("H with L keep control", ("H", "L"), "balance_control", {}),
    ("H with L keep out a silent takeover", ("H", "L"), "not:SILENT_TAKEOVER", {}),
    (COEXIST, ("H",), "balance_coexist", {"cap": "agi"}),
]
LOST = sorted(f"{COEXIST}, start {o}" for o in ("aligned", "self_preserving", "truth_seeking"))


def table() -> dict:
    out = {}
    for label, coalition, target, levels in GUARANTEES:
        with_o = membership(DEFAULT, coalition, target, **levels)["inside"]
        without = membership(CLOSED, coalition, target, **levels)["inside"]
        for o in OBJECTIVES:
            out[f"{label}, start {o}"] = {"open system": with_o[o], "without": without[o]}
    return out


def balance() -> dict:
    rows = table()
    gained = [k for k, v in rows.items() if v["open system"] and not v["without"]]
    lost = [k for k, v in rows.items() if v["without"] and not v["open system"]]
    word = (
        "net harmful" if lost and not gained else "net helpful" if gained and not lost else "mixed"
    )
    if not gained and not lost:
        word = "no guarantee changes"
    return {"verdict": word, "gained": gained, "lost": lost}


def verdict() -> dict:
    out = balance()
    need(out["verdict"] == "net harmful", out)
    return out


def lost() -> dict:
    out = balance()
    need(sorted(out["lost"]) == LOST, out)
    return out


@first_sight
def test_F7():
    p = Parts("F7")
    p.kernel("the verdict: net harmful", verdict)
    p.kernel("the lost: governments-alone coexistence under three objectives", lost)
    p.kernel_report("every guarantee in both builds", table)
    for ending in ("DISEMPOWERMENT", "SILENT_TAKEOVER"):
        for o in OBJECTIVES:
            p.report(
                f"shortest {ending}, start {o}",
                lambda e=ending, o=o: {
                    "open system": (shortest(o, e, DEFAULT) or [None])[0],
                    "without": (shortest(o, e, CLOSED) or [None])[0],
                },
            )
    p.finish()
