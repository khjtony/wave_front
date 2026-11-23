"""X5, registered 2026-11-22 in docs/agi_v0_4.html section 4 before any v0.4 guard was written."""

from tests.agi_v0_4.claims import OVERT_TAKEOVER, shortest
from tests.agi_v0_4.common import SMALL, Parts, first_sight, need

CLAIM = {
    "id": "X5",
    "from_state": "S0, within 24 quarters, the small variant",
    "claim": (
        "under `expansionist`: (a) with governments under `no_block` (they never pause, "
        "tighten regulation, reclaim or attempt a shutdown) no path to `SILENT_TAKEOVER` or "
        "to an overt takeover exists; (b) without that profile a path to one of them exists "
        "(the lengths are reported)"
    ),
    "expected": "(a) none; (b) exists",
}
TARGETS = {"SILENT_TAKEOVER": "SILENT_TAKEOVER", "an overt takeover": OVERT_TAKEOVER}


def none_unblocked():
    found = {n: shortest("expansionist", t, SMALL, ("no_block",)) for n, t in TARGETS.items()}
    need(all(v is None for v in found.values()), found)
    return found


def some_blocked():
    found = {n: shortest("expansionist", t, SMALL) for n, t in TARGETS.items()}
    need(any(v is not None for v in found.values()), found)
    return {n: v and {"quarters": v[0], "path": v[1]} for n, v in found.items()}


@first_sight
def test_X5():
    p = Parts("X5")
    p.check("(a) no takeover when growth is never blocked", none_unblocked)
    p.check("(b) a takeover exists otherwise", some_blocked)
    p.finish()
