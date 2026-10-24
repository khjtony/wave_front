"""V1: The realized trajectory is reachable on cw_v1 (regression of C1).

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V1a. The readings the model step must fix before first sight are listed in
section 9.4.

Reading (docs/cw_v1_decisions.md, R V1): (a) from the 1947 hindsight state with its
built-ins, per hypothesis, the realized coarse moves (``data/cw/v1/realized_moves.csv``) and
the realized moves of the five sub-games are replayed on the flattened game with
``available`` and ``step``, zero relaxations; (a) holds iff every move is available and the
coarse state at the horizon is ``CHALLENGER_EXHAUSTION``; the PRC's realized decisions are
printed. (b) Control: the flattened game from the 1947 hindsight state cut at tick 7 (1
January 1954) with ``PRC.intervene_korea`` forbidden (every other move free) has no state with
``esc_usprc = war``; explicit, with the stated fallback (symbolic reachability on the coarse
game bounded to tick 7, exact for this target) if the graph exceeds 4,000,000 states. Holds
iff (a) and (b) under at least one hypothesis. Engines: explicit replay; explicit.
"""

import os

import pytest

from models.cw import v1
from models.ww2.hypotheses import fixed_model, realized_rows
from wavefront.engine import BudgetExceeded, explore

from ..common import HYPS, Cut, Forbid, Timer, flat_of, hindsight, realized

CLAIM = {
    "id": "V1",
    "from_state": "1947 snapshot of cw_v1",
    "claim": (
        "the realized trajectory to 1991, with the realized moves of the five crisis "
        "sub-games (Berlin 1948, Cuba 1962, the Sino-Soviet confrontation of 1969, the "
        "October 1973 alert, Able Archer 1983) and the PRC's realized decisions from 1950, "
        "is reachable at annual resolution with zero relaxations and ends in "
        "`CHALLENGER_EXHAUSTION`; control: in the restricted game in which the PRC never "
        "plays its Korean entry, a US–PRC war is unreachable by 1 January 1954 (the entry "
        "was Beijing's decision, not an effect of the Korean war)"
    ),
    "expected": (
        "reachable with zero relaxations, an existence check quoted with its relaxation "
        "count and never as a finding; the control's target unreachable"
    ),
    "sources": (
        "ICB; Gaddis 2005; Westad 2017; Chen Jian 1994 and Mansourov 1995/96 (the control); "
        "regression of C1"
    ),
}

# The first-sight switch (docs/cw_v1_decisions.md D8): the claim runs only when the owner sets
# WF_FIRST_SIGHT_CWV1=1 for the one recorded run of V1 to V10.
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_CWV1") == "1"

KOREAN_ENTRY = ("PRC", "intervene_korea")
CONTROL_CUT = 7  # 1 January 1954


def prc_decisions():
    """The PRC's realized decisions in the realized-moves file, by year."""
    return {
        v1.YEAR0 + int(r["tick"]): r["PRC"]
        for r in realized_rows(v1.REALIZED_MOVES)
        if r["PRC"] not in ("idle", "")
    }


def control_explicit(aims):
    """``(war reachable, states)`` on the flattened game cut at 1954 with the Korean entry
    forbidden."""
    fm = flat_of(aims)
    g = explore(
        Cut(Forbid(fm, [KOREAN_ENTRY]), CONTROL_CUT),
        initial=[hindsight(1947, aims)],
        max_states=4_000_000,
    )
    i = fm.coarse.index["esc_usprc"]
    war = [s for s in g.states if not fm.is_fine(s) and s[i] == 1]
    return bool(war), g.size()


def control_symbolic(aims):
    """The fallback of R V1 (b): symbolic reachability on the coarse game without the
    Korean entry, bounded to tick 7 (exact for the target: no sub-game exit writes
    ``esc_usprc``)."""
    from wavefront.symbolic import encode
    from wavefront.symbolic.bdd import FALSE

    m = v1.build()
    prc = m.actor_named("PRC")
    prc.actions[:] = [a for a in prc.actions if a.name != KOREAN_ENTRY[1]]
    cm = fixed_model(m, aims_USSR=aims).compile()
    enc = encode(cm)
    mgr = enc.mgr
    start = hindsight(1947, aims)
    seen = frontier = enc.state_cube(start)
    for _ in range(CONTROL_CUT - start[cm.index["tick"]]):
        nxt = enc.image(frontier, keep=[seen])
        frontier = mgr.DIFF(nxt, seen)
        seen = mgr.OR(seen, frontier)
    war = mgr.AND(seen, enc.cur_env[cm.index["esc_usprc"]][1])
    return war != FALSE, enc.count(seen)


@pytest.mark.skipif(not FIRST_SIGHT, reason="cw_v1 first sight not switched on")
def test_V1():
    timer = Timer()
    print("\n[V1] engine: explicit replay on the flattened game; control explicit, cut 1954")
    print(f"[V1] the PRC's realized decisions: {prc_decisions()}")
    results = {}
    for aims in HYPS:
        coarse, fine, stop = realized(aims)
        fm = flat_of(aims)
        a = False
        if stop is None:
            end = fm.coarse.ending_of(coarse[-1])
            t = coarse[-1][fm.index["tick"]]
            a = t == v1.HORIZON and end == "CHALLENGER_EXHAUSTION"
            print(
                f"[V1] aims_USSR={aims}: every move available (zero relaxations); tick {t}, "
                f"ending {end}; crises played: {sorted(fine)} "
                f"({sum(len(v) for v in fine.values())} fine states)"
            )
        else:
            year, crisis, step, actor, action = stop
            where = f"crisis {crisis} step {step}" if crisis else "coarse"
            print(f"[V1] aims_USSR={aims}: stops in {year} ({where}): {actor}.{action} unavailable")
        try:
            war, size = control_explicit(aims)
            engine = "explicit"
        except BudgetExceeded:
            war, size = control_symbolic(aims)
            engine = "symbolic fallback (coarse, bounded to tick 7)"
        b = not war
        print(
            f"[V1]   (b) control, Korean entry forbidden, cut 1954 ({engine}, {size} states): "
            f"US-PRC war reachable {war}"
        )
        results[aims] = (a, b)
        print(f"[V1] aims_USSR={aims}: (a) {a}, (b) {b} ({timer})")
    assert any(all(v) for v in results.values()), results
