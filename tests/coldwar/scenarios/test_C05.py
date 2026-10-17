"""C5: Korea: `GENERAL_WAR` is blockable by the United States alone.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.

Reading (docs/cw_v0_decisions.md, R C5): the coarse game from the 1950 hindsight state,
per hypothesis. (a) a state with ``korea = armistice`` and ``no_war`` is reachable; (b) the
1950 state is in USA's kernel of "no GENERAL_WAR before 1 January 1954"; (c) the parts
``USA.nuclear_korea:total_commitment`` and ``:reading`` are reported with whether (b) holds
when each is relaxed. Holds iff (a) and (b) under ``opportunist``. H8: (b) is also reported at
the bound plus eight ticks (1 January 1962). Engine: explicit, cut at tick 7 (no sub-game
falls in 1950 to 1953).
"""

from wavefront.engine import safe

from ..common import HYPS, OPP, Timer, compiled, ending_ids, graph, hindsight

CLAIM = {
    "id": "C5",
    "from_state": "1950, June",
    "claim": (
        "a `LIMITED_WAR` in Korea is reachable and `GENERAL_WAR` is blockable by the "
        "United States alone, because nuclear use requires `commit = total` and "
        "`belief[USA][USSR].aims ≠ opportunist`"
    ),
    "expected": "`⟨⟨USA⟩⟩□¬GENERAL_WAR` true in the 1950 state under the documented guards",
    "sources": "FRUS 1950; Gaddis 1982 and 2005",
}

PARTS = ("USA.nuclear_korea:total_commitment", "USA.nuclear_korea:reading")


def us_blocks(aims, cut, relax=frozenset()):
    cm = compiled(aims, relax=relax)
    s = hindsight(1950, aims)
    g = graph(cm, s, cut=cut)
    gw = ending_ids(g, "GENERAL_WAR")
    keep = set(range(g.size())) - gw
    return g.index[s] in safe(g, ["USA"], keep).kernel, g


def test_C05():
    timer = Timer()
    print("\n[C5] engine: explicit coarse game from 1 Jan 1950, cut at 1 Jan 1954")
    results = {}
    for aims in HYPS:
        blocks, g = us_blocks(aims, 7)
        cm = compiled(aims)
        limited = [
            i
            for i in range(g.size())
            if cm.state_dict(g.states[i])["korea"] == "armistice"
            and cm.evaluate("no_war", g.states[i])
        ]
        war = any(cm.state_dict(s)["korea"] == "war" for s in g.states)
        print(f"[C5] aims_USSR={aims}: graph {g.size()} states; Korean war reachable {war}")
        print(
            f"[C5]   (a) limited war (armistice, no war between principals) "
            f"reachable: {bool(limited)}"
        )
        print(f"[C5]   (b) <<USA>>[]~GENERAL_WAR to 1954: {blocks}")
        for part in PARTS:
            relaxed, _ = us_blocks(aims, 7, frozenset({part}))
            print(f"[C5]   (c) with {part} relaxed: USA still blocks: {relaxed}")
        try:
            later, g2 = us_blocks(aims, 15)
            print(f"[C5]   H8: to 1962 (bound plus eight): {later} ({g2.size()} states)")
        except Exception as exc:  # reported, not asserted
            print(f"[C5]   H8: to 1962 not computed ({type(exc).__name__}: {exc})")
        results[aims] = (bool(limited), blocks)
        print(f"[C5] aims_USSR={aims}: (a) {bool(limited)}, (b) {blocks} ({timer})")
    assert all(results[OPP]), results
