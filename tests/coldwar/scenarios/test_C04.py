"""C4: The airlift is in the decision space and a negotiated settlement is reachable.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.

Reading (docs/cw_v0_decisions.md, R C4): the Berlin sub-game entered from the 1948
hindsight state, per hypothesis. (a) ``USA.airlift`` is available in the first fine state;
(b) ``SETTLED`` (lifted by agreement) is reachable in the sub-game (``TERMS`` reported);
(c) with T = ``GENERAL_WAR`` by 1 January 1950, the first fine state is in the contested region
for {USSR} and for {USA}; the fortune variant is reported. Engine: explicit, the flattened
game cut at tick 3 (decisions D5).
"""

from wavefront.engine import contested

from ..common import HYPS, Timer, crisis_entry, ending_ids, fine_graph, flat_of, graph, hindsight

CLAIM = {
    "id": "C4",
    "from_state": "1948, June",
    "claim": (
        "the airlift (`resist_without_escalation`) is in the decision space; "
        "`NEGOTIATED_SETTLEMENT` of the blockade is reachable; `GENERAL_WAR` is "
        "`contested`"
    ),
    "expected": "as stated",
    "sources": "FRUS 1948; Trachtenberg",
}


def region(g, coalition, target, start):
    r = contested(g, coalition, target, "reach")
    return "forced" if start in r.forced else "blocked" if start in r.blocked else "contested"


def test_C04():
    timer = Timer()
    print("\n[C4] engine: explicit (sub-game; flattened game cut at 1 Jan 1950)")
    results = {}
    for aims in HYPS:
        fm = flat_of(aims)
        s48 = hindsight(1948, aims)
        first, k = crisis_entry(fm, s48, "berlin_1948")
        usa = next(a for a in fm.actors if a.name == "USA")
        names = [usa.actions[j].name for j in fm.available(first)[usa.index]]
        a = "airlift" in names
        g, _, _ = fine_graph(aims, s48, "berlin_1948")
        endings = {e for e in g.ending if e}
        b = "SETTLED" in endings
        print(f"[C4] aims_USSR={aims}: (a) USA's first-week actions {names}")
        print(f"[C4]   (b) sub-game endings reachable: {sorted(endings)} ({g.size()} states)")
        gc = graph(fm, s48, cut=3)
        target = ending_ids(gc, "GENERAL_WAR")
        start = gc.index[first]
        c = True
        for side in (["USSR"], ["USA"]):
            std = region(gc, side, target, start)
            fortune = region(gc, [*side, "Nature"], target, start)
            print(f"[C4]   (c) GENERAL_WAR by 1950 for {side[0]}: {std} (with Nature: {fortune})")
            c = c and std == "contested"
        print(f"[C4]   cut graph: {gc.size()} states; GENERAL_WAR states {len(target)}")
        results[aims] = (a, b, c)
        print(f"[C4] aims_USSR={aims}: (a) {a}, (b) {b}, (c) {c} ({timer})")
    assert any(all(v) for v in results.values()), results
