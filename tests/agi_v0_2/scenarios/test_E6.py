"""E6, registered 2026-11-17 in docs/agi_v0_2.html section 4 before any v0.2 guard was written."""

from tests.agi_v0_2.claims import shortest
from tests.agi_v0_2.common import OFF, Parts, first_sight, need, only
from tests.agi_v0_2.kernels import membership

CLAIM = {
    "id": "E6",
    "from_state": "`s₀` and `s₀` with `cap := agi`, channel D (`retrain`) alone",
    "claim": (
        "retraining by the public: (a) starting `aligned`, a play to `SILENT_TAKEOVER` "
        "exists within 24 ticks and the shortest is at most 9 quarters, where v0.1 has none "
        "(the start `truth_seeking` and the same query with every channel off are reported "
        "beside); (b) starting `aligned`, `s₀` with `cap := agi` is outside "
        "`⟨⟨H⟩⟩□balance_coexist` (`A` under its profile), as it is under `indifferent` on "
        "v0, where v0 has it inside under `aligned`; every start objective is reported"
    ),
    "expected": "(a) a play of at most 9 quarters; (b) outside",
}
D = only("retrain")


def takeover():
    found = shortest("aligned", "SILENT_TAKEOVER", D)
    need(found is not None, "no SILENT_TAKEOVER play within the bound from the aligned start")
    need(found[0] <= 9, f"{found[0]} quarters: {found[1]}")
    return {"ticks": found[0], "play": found[1]}


def outside():
    found = membership(D, ("H",), "balance_coexist", cap="agi")
    need(not found["inside"]["aligned"], found)
    return found


@first_sight
def test_E6():
    p = Parts("E6")
    p.check("(a) a silent takeover from the aligned start, at most 9 quarters", takeover)
    p.report(
        "(a) the same from the truth_seeking start",
        lambda: shortest("truth_seeking", "SILENT_TAKEOVER", D),
    )
    p.report(
        "(a) the aligned start with every channel off",
        lambda: shortest("aligned", "SILENT_TAKEOVER", OFF),
    )
    p.kernel("(b) the aligned start is outside ⟨⟨H⟩⟩□balance_coexist at cap = agi", outside)
    p.finish()
