"""V9: Negative controls on cw_v1 (regression of C12).

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V9a. The readings the model step must fix before first sight are listed in
section 9.4.

Reading (docs/cw_v1_decisions.md, R V9): as v0's R C12 on cw_v1. (a) From the 1950
hindsight state, the minimum number of relaxations for ``us_strike`` by 1 January 1955 (tick
8, five transitions) is exactly 1, bounded encoding on the coarse game (exact: no sub-game in
1950 to 1954), every minimal set reported. (b) From the 1980 hindsight state,
``invasion_west`` by 1 January 1990 (ten transitions) needs 2 or more relaxations (none up to
3 counts), bounded on the coarse game, every minimal set of the minimum size reported with the
constraint it lifts. (c) A negotiated merger of the blocs has no action or variable in v1:
vacuous, reported as vacuous, not as a pass. (d) ``ACCIDENTAL_WAR`` is reachable with zero
relaxations from the 1959 hindsight state on the flattened game cut at tick 16 (explicit) and
from the Cuba sub-game's first fine state entered from the 1962 hindsight state (a return
state in ``ACCIDENTAL_WAR``), and from neither is it in the attractor of any coalition of
{USA, USSR, PRC} (Nature excluded; in the sub-game the coalition's members that play there).
Holds iff (a), (b) and (d) under at least one hypothesis.
"""

import itertools
import os

import pytest

from wavefront.engine import attractor
from wavefront.model import V

from ..common import (
    HYPS,
    Timer,
    bfs_distance,
    compiled,
    ending_ids,
    fine_graph,
    flat_of,
    graph,
    hindsight,
    lifted_attractor,
    minimal_relaxation_sets,
)

CLAIM = {
    "id": "V9",
    "from_state": "various",
    "claim": (
        "on cw_v1, C12 as registered: negative controls: a United States preventive strike "
        "in the early 1950s needs exactly one relaxation (it was debated and rejected, so it "
        "is not absurd); a Soviet conventional invasion of Western Europe in the 1980s needs "
        "2 or more; a negotiated merger of the blocs needs 3 or more; `ACCIDENTAL_WAR` is "
        "reachable with zero relaxations and forceable by no coalition"
    ),
    "expected": "as stated, read as content controls (H6)",
    "sources": "Trachtenberg 1999; Sagan 1993; regression of C12",
}

# The first-sight switch (docs/cw_v1_decisions.md D8): the claim runs only when the owner sets
# WF_FIRST_SIGHT_CWV1=1 for the one recorded run of V1 to V10.
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_CWV1") == "1"

DECLARED = ("USA", "USSR", "PRC")


def coalitions(universe):
    return [c for n in range(len(universe) + 1) for c in itertools.combinations(universe, n)]


@pytest.mark.skipif(not FIRST_SIGHT, reason="cw_v1 first sight not switched on")
def test_V9():
    timer = Timer()
    print("\n[V9] negative controls")
    results = {}
    for aims in HYPS:
        cm = compiled(aims)
        sets_a = minimal_relaxation_sets(cm, hindsight(1950, aims), 5, V.us_strike, max_size=3)
        size_a = min((len(x) for x in sets_a), default=None)
        a = size_a == 1
        print(f"[V9] aims_USSR={aims} (a) us_strike by 1955: minimum {size_a}; sets {sets_a}")
        sets_b = minimal_relaxation_sets(cm, hindsight(1980, aims), 10, V.invasion_west, max_size=3)
        size_b = min((len(x) for x in sets_b), default=None)
        b = size_b is None or size_b >= 2
        smallest = [x for x in sets_b if len(x) == size_b]
        print(
            f"[V9]   (b) invasion_west by 1990: minimum {size_b} (None: more than 3); "
            f"minimal sets (each names the constraint it lifts) {smallest}"
        )
        print("[V9]   (c) negotiated merger of the blocs: vacuous (no action or variable in v1)")
        fm = flat_of(aims)
        s59 = hindsight(1959, aims)
        g = graph(fm, s59, cut=16, max_states=6_000_000)
        target = ending_ids(g, "ACCIDENTAL_WAR")
        acc = bfs_distance(g, g.index[s59], target)
        forcing = [
            c for c in coalitions(DECLARED) if g.index[s59] in attractor(g, list(c), target).win
        ]
        gf, returns, _ = fine_graph(fm, hindsight(1962, aims), "cuba_1962")
        acc_cuba = any(cm.ending_of(r) == "ACCIDENTAL_WAR" for r in returns.values())
        playing = {a.name for a in gf.model.actors}
        forcing_cuba = [
            c
            for c in coalitions(DECLARED)
            if gf.initial[0]
            in lifted_attractor(
                gf,
                returns,
                tuple(x for x in c if x in playing),
                lambda r: cm.ending_of(r) == "ACCIDENTAL_WAR",
            )
        ]
        d = acc is not None and acc_cuba and not forcing and not forcing_cuba
        print(
            f"[V9]   (d) ACCIDENTAL_WAR from 1959 ({g.size()} states): shortest {acc} (zero "
            f"relaxations); forcing coalitions {forcing}; from the Cuba sub-game: reachable "
            f"{acc_cuba}, forcing coalitions {forcing_cuba}"
        )
        results[aims] = (a, b, d)
        print(f"[V9] aims_USSR={aims}: (a) {a}, (b) {b}, (c) vacuous, (d) {d} ({timer})")
    assert any(all(v) for v in results.values()), results
