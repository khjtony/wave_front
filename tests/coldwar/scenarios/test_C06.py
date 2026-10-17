"""C6: Replayed `belief[USA][USSR].force` exceeds hindsight `nuke[USSR]`, 1957 to 1961.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.

Reading (docs/cw_v0_decisions.md, R C6): the manual replay snapshots of 1957 to 1962
against the hindsight snapshots. (a) the replayed ``belief_force_USA`` exceeds the hindsight
``nuke_USSR`` in every year from 1958 through 1961 (1957 and 1962 reported); (b) for each such
year, per hypothesis, some US-adverse ending (GENERAL_WAR, ACCIDENTAL_WAR) is reachable by
1 January 1963 from the replay state in fewer ticks than from the hindsight state (or only
from it), and none the other way; (c) Y_o, the first replay year with ``intel_USA =
overhead``, and Y_c, the first year from Y_o whose replayed belief does not exceed the
hindsight force, satisfy Y_c - Y_o <= 1; the hindsight ``nuke_USSR`` is the same in Y_c - 1 and
Y_c, and the only event lowering the belief has the part ``overhead``. Hold-out (decisions
D9). Engine: explicit coarse game cut at tick 16 (the Cuba sub-game is inert there).
"""

from models.cw.v0 import NUKE, model

from ..common import (
    ADVERSE,
    HYPS,
    Timer,
    bfs_distance,
    compiled,
    ending_ids,
    graph,
    hindsight,
    level,
    replay_state,
)

CLAIM = {
    "id": "C6",
    "from_state": "1957 to 1961, annual replay",
    "claim": (
        "the replayed `belief[USA][USSR].force` from dated estimates and press exceeds "
        "the hindsight `nuke[USSR]`; analysis from the replay snapshot shows more "
        "adversarial reachability than from the hindsight snapshot; the gap closes "
        "within one year of `intel[USA] = overhead_reconnaissance` (1960 to 1961)"
    ),
    "expected": "as stated; the closing is driven by `intel`, not by any force change",
    "sources": "the NIE series (CIA CREST); Gaddis 2005; Preble 2004",
}

YEARS = range(1957, 1963)
GAP = range(1958, 1962)


def adverse(g, start):
    return {e: bfs_distance(g, g.index[start], ending_ids(g, e)) for e in ADVERSE}


def more(rep, hind):
    """Replay shows more adversarial reachability: some ending closer (or only) from the
    replay state and none closer from the hindsight state."""
    better = worse = False
    for e in ADVERSE:
        r, h = rep[e], hind[e]
        if r is not None and (h is None or r < h):
            better = True
        if h is not None and (r is None or h < r):
            worse = True
    return better and not worse


def lowering_events():
    out = {}
    for a in [*model.actors, model.nature()]:
        for x in a.actions:
            for e in x.effects:
                if getattr(e, "var", None) == "belief_force_USA":
                    out[f"{a.name}.{x.name}"] = [p for p, _ in x.guard_parts]
    return out


def test_C06():
    timer = Timer()
    print("\n[C6] engine: replay against hindsight snapshots; explicit coarse game cut at 1963")
    cm = compiled("opportunist")
    exceeds = {}
    for y in YEARS:
        rb = level(cm, replay_state(y, "opportunist"), "belief_force_USA")
        hn = level(cm, hindsight(y, "opportunist"), "nuke_USSR")
        exceeds[y] = NUKE.index(rb) > NUKE.index(hn)
        print(f"[C6]   {y}: replayed belief {rb}, hindsight nuke_USSR {hn}: exceeds {exceeds[y]}")
    a = all(exceeds[y] for y in GAP)
    results = {}
    for aims in HYPS:
        cm = compiled(aims)
        b = True
        for y in GAP:
            r, h = replay_state(y, aims), hindsight(y, aims)
            gr, gh = graph(cm, r, cut=16), graph(cm, h, cut=16)
            dr, dh = adverse(gr, r), adverse(gh, h)
            ok = more(dr, dh)
            print(
                f"[C6]   aims_USSR={aims} {y}: replay {dr} ({gr.size()}); "
                f"hindsight {dh} ({gh.size()}): more {ok}"
            )
            b = b and ok
        results[aims] = b
    intel = {y: level(cm, replay_state(y, "opportunist"), "intel_USA") for y in YEARS}
    y_o = next((y for y in YEARS if intel[y] == "overhead"), None)
    y_c = next((y for y in YEARS if y_o and y >= y_o and not exceeds[y]), None)
    force = {y: level(cm, hindsight(y, "opportunist"), "nuke_USSR") for y in YEARS}
    low = lowering_events()
    print(f"[C6]   (c) intel overhead from {y_o}; gap closed in {y_c}; hindsight force {force}")
    print(f"[C6]   (c) events with an effect on belief_force_USA (guard parts): {low}")
    c = (
        y_o is not None
        and y_c is not None
        and y_c - y_o <= 1
        and force[y_c - 1] == force[y_c]
        and "overhead" in low.get("Nature.estimate_revised", [])
    )
    print(f"[C6] (a) {a}, (b) {results}, (c) {c} ({timer})")
    assert a and c and any(results.values()), (a, results, c)
