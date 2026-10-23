"""C1: Realized trajectory to 1991 is reachable at annual resolution.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.

Reading (docs/cw_v0_decisions.md, R C1): from the 1947 hindsight snapshot with its
built-ins, per hypothesis, the realized coarse moves and the realized moves of the three
sub-games are replayed on the flattened game (zero relaxations); the claim holds iff under at
least one hypothesis every move is available and the play reaches the horizon in
``CHALLENGER_EXHAUSTION``. Engine: explicit replay.
"""

from models.cw.v0 import HORIZON

from ..common import HYPS, Timer, flat_of, realized

CLAIM = {
    "id": "C1",
    "from_state": "1947 snapshot",
    "claim": "the realized trajectory to 1991 is reachable at annual resolution",
    "expected": "reachable with zero relaxations",
    "sources": "ICB; Gaddis 2005; Westad 2017",
}


def test_C01():
    timer = Timer()
    ok = []
    print("\n[C1] engine: explicit replay on the flattened game")
    for aims in HYPS:
        coarse, fine, stop = realized(aims)
        fm = flat_of(aims)
        if stop is None:
            end = fm.coarse.ending_of(coarse[-1])
            t = coarse[-1][fm.index["tick"]]
            print(
                f"[C1] aims_USSR={aims}: every move available; tick {t}, ending {end}; "
                f"crises played: {sorted(fine)} ({sum(len(v) for v in fine.values())} fine states)"
            )
            if t == HORIZON and end == "CHALLENGER_EXHAUSTION":
                ok.append(aims)
        else:
            year, crisis, step, actor, action = stop
            where = f"crisis {crisis} step {step}" if crisis else "coarse"
            print(f"[C1] aims_USSR={aims}: stops in {year} ({where}): {actor}.{action} unavailable")
    print(f"[C1] reachable with zero relaxations under: {ok} ({timer})")
    assert ok, "the realized trajectory is not reachable under any hypothesis"
