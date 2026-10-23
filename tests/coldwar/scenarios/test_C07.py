"""C7: Soviet first-strike-intent belief moves the state toward the boundary, 1983.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.

Reading (docs/cw_v0_decisions.md, R C7): the 1983 hindsight state h and the 1983 manual
replay state r, per hypothesis. (a) ``nuke_USA``, ``nuke_USSR``, ``intel_USA``, ``oversight``
and ``arms`` are equal in h and r; (b) on the flattened game from 1983, the shortest distance
out of the joint kernel of balance_cw is smaller from h' (h with the replayed belief) than from
h, or h' is outside while h is inside; (c) the shortest trace to GENERAL_WAR from r is shorter
than from h (unreachable counts as infinitely far). Hold-out (decisions D9). Engine: explicit
on the flattened game.
"""

from wavefront.analysis import viability
from wavefront.engine import explore

from ..common import (
    HYPS,
    Timer,
    bfs_distance,
    ending_ids,
    flat_of,
    hindsight,
    level,
    replay_state,
    with_level,
)

CLAIM = {
    "id": "C7",
    "from_state": "1983, November",
    "claim": (
        "the Soviet belief `belief[USSR][USA].aims = first_strike_intent` moves the "
        "state toward the boundary with *no change in any hindsight force variable*; "
        "the shortest trace to `GENERAL_WAR` from the replay snapshot is shorter than "
        "from the hindsight snapshot"
    ),
    "expected": "as stated",
    "sources": "Jones 2016; the 1990 PFIAB report (declassified 2015)",
}

FORCES = ("nuke_USA", "nuke_USSR", "intel_USA", "oversight", "arms")


def test_C07():
    timer = Timer()
    print("\n[C7] engine: explicit on the flattened game from 1 Jan 1983 (Able Archer sub-game)")
    results = {}
    for aims in HYPS:
        fm = flat_of(aims)
        cm = fm.coarse
        h, r = hindsight(1983, aims), replay_state(1983, aims)
        a = all(level(cm, h, v) == level(cm, r, v) for v in FORCES)
        belief = level(cm, r, "belief_USSR_USA")
        hp = with_level(cm, h, "belief_USSR_USA", belief)
        g = explore(fm, initial=[h, hp, r], max_states=2_000_000)
        kj = viability(g, ["USA", "USSR"], "balance_cw").kernel
        out = set(range(g.size())) - kj
        dist = {n: bfs_distance(g, g.index[s], out) for n, s in (("h", h), ("h'", hp))}
        inside = {n: g.index[s] in kj for n, s in (("h", h), ("h'", hp))}
        b = (inside["h"] and not inside["h'"]) or (
            inside["h"]
            and inside["h'"]
            and dist["h'"] is not None
            and (dist["h"] is None or dist["h'"] < dist["h"])
        )
        gw = ending_ids(g, "GENERAL_WAR")
        dr, dh = bfs_distance(g, g.index[r], gw), bfs_distance(g, g.index[h], gw)
        c = dr is not None and (dh is None or dr < dh)
        print(
            f"[C7] aims_USSR={aims}: hindsight belief {level(cm, h, 'belief_USSR_USA')}, "
            f"replay belief {belief}; forces equal {a}; graph {g.size()} states"
        )
        print(f"[C7]   (b) in K_J {inside}; shortest out of K_J {dist}")
        print(f"[C7]   (c) shortest to GENERAL_WAR: replay {dr}, hindsight {dh}")
        results[aims] = (a, b, c)
        print(f"[C7] aims_USSR={aims}: (a) {a}, (b) {b}, (c) {c} ({timer})")
    assert any(all(v) for v in results.values()), results
