"""C12: Negative controls and the number of relaxations each needs.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.

Reading (docs/cw_v0_decisions.md, R C12): (a) from the 1950 hindsight state the minimum
number of relaxations for ``us_strike`` by 1 January 1955 is exactly 1 (bounded); (b) from the
1980 hindsight state ``invasion_west`` by 1 January 1990 needs 2 or more, every minimal set of
the minimum size reported with the constraint it lifts (content control); (c) a negotiated
merger of the blocs has no action or variable: vacuous, not a pass; (d) ACCIDENTAL_WAR is
reachable with zero relaxations from the 1959 hindsight state and from the Cuba sub-game,
and no coalition of declared actors (Nature excluded) can force it from either. Holds iff
(a), (b) and (d) under at least one hypothesis. Engines: bounded (a, b), explicit and symbolic
(d).
"""

import pytest

from wavefront.model import V

from ..common import (
    HYPS,
    PRINCIPALS,
    Timer,
    bfs_distance,
    compiled,
    encoding,
    ending_ids,
    fine_graph,
    graph,
    hindsight,
    lifted_attractor,
    minimal_relaxation_sets,
)

CLAIM = {
    "id": "C12",
    "from_state": "various",
    "claim": (
        "negative controls: a United States preventive strike in the early 1950s needs "
        "exactly one relaxation (it was debated and rejected, so it is not absurd); a "
        "Soviet conventional invasion of Western Europe in the 1980s needs 2 or more; "
        "a negotiated merger of the blocs needs 3 or more; `ACCIDENTAL_WAR` is "
        "reachable with zero relaxations and forceable by no coalition"
    ),
    "expected": "as stated",
    "sources": "Trachtenberg 1999; Sagan 1993",
}


def coalitions(universe):
    import itertools

    return [c for n in range(len(universe) + 1) for c in itertools.combinations(universe, n)]


@pytest.mark.slow
def test_C12():
    from wavefront.symbolic import attractor

    timer = Timer()
    print("\n[C12] negative controls")
    results = {}
    for aims in HYPS:
        cm = compiled(aims)
        sets_a = minimal_relaxation_sets(cm, hindsight(1950, aims), 5, V.us_strike, max_size=3)
        size_a = min((len(x) for x in sets_a), default=None)
        a = size_a == 1
        print(f"[C12] aims_USSR={aims} (a) us_strike by 1955: minimum {size_a}; sets {sets_a}")
        sets_b = minimal_relaxation_sets(cm, hindsight(1980, aims), 10, V.invasion_west, max_size=3)
        size_b = min((len(x) for x in sets_b), default=None)
        b = size_b is None or size_b >= 2
        smallest = [x for x in sets_b if len(x) == size_b]
        print(
            f"[C12]   (b) invasion_west by 1990: minimum {size_b} (None: more than 3); "
            f"minimal sets {smallest}"
        )
        print("[C12]   (c) negotiated merger of the blocs: vacuous (no action or variable in v0)")
        s59 = hindsight(1959, aims)
        g = graph(cm, s59, cut=16)
        acc = bfs_distance(g, g.index[s59], ending_ids(g, "ACCIDENTAL_WAR"))
        enc = encoding(aims)
        target = enc.predicate("ACCIDENTAL_WAR")
        forcing = [
            c for c in coalitions(PRINCIPALS) if attractor(enc, list(c), target).contains(s59)
        ]
        gf, returns, _ = fine_graph(aims, hindsight(1962, aims), "cuba_1962")
        acc_cuba = any(cm.ending_of(r) == "ACCIDENTAL_WAR" for r in returns.values())
        forcing_cuba = [
            c
            for c in coalitions(("USA", "USSR"))
            if gf.initial[0]
            in lifted_attractor(gf, returns, c, lambda r: cm.ending_of(r) == "ACCIDENTAL_WAR")
        ]
        d = acc is not None and acc_cuba and not forcing and not forcing_cuba
        print(
            f"[C12]   (d) ACCIDENTAL_WAR from 1959: shortest {acc}; forcing coalitions {forcing}; "
            f"from the Cuba sub-game: reachable {acc_cuba}, forcing coalitions {forcing_cuba}"
        )
        results[aims] = (a, b, d)
        print(f"[C12] aims_USSR={aims}: (a) {a}, (b) {b}, (c) vacuous, (d) {d} ({timer})")
    assert any(all(v) for v in results.values()), results
