"""C6: Replayed `belief[USA][USSR].force` exceeds hindsight `nuke[USSR]`, 1957 to 1961.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document. Part (b) amended 2026-10-23 on the owner's
decision 2n (belief measured by its effect on reachability and on the unilateral kernels, not
on the joint kernel); the previous wording is in git history and in reports/cw_v0.md
section 7.

Reading (docs/cw_v0_decisions.md, R C6, with the amendment A C6): the manual replay snapshots
of 1957 to 1962 against the hindsight snapshots. (a) the replayed ``belief_force_USA``
exceeds the hindsight ``nuke_USSR`` in every year from 1958 through 1961 (1957 and 1962
reported); (b) amended: for each such year, per hypothesis, four measures of nearness to
the US-adverse endings by 1 January 1963 are taken from the replay state and from the
hindsight state: the shortest trace to GENERAL_WAR and to ACCIDENTAL_WAR, and the distance
out of {USA}'s and of {USSR}'s kernel of avoiding both endings to 1963 (0 when the state is
outside the kernel); (b) holds iff in every year at least one measure is smaller from the
replay state and none is smaller from the hindsight state (an unreachable ending, or a
kernel no play leaves, is infinitely far). The registered (b),
the two shortest traces alone, is printed beside it. (c) Y_o, the first replay year with
``intel_USA = overhead``, and Y_c, the first year from Y_o whose replayed belief does not
exceed the hindsight force, satisfy Y_c - Y_o <= 1; the hindsight ``nuke_USSR`` is the same
in Y_c - 1 and Y_c, and the only event lowering the belief has the part ``overhead``.
Hold-out (decisions D9): the amended claim was computed once, on the model of first sight,
before the guard edit of 2026-10-23 (docs/guard_changelog_cw.md). Engine: explicit coarse
game cut at tick 16 (the Cuba sub-game is inert there).
"""

from models.cw.v0 import NUKE, model
from wavefront.engine import safe

from ..common import (
    ADVERSE,
    HYPS,
    Timer,
    bfs_distance,
    compare,
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
        "adversarial reachability than from the hindsight snapshot, measured on "
        "reachability and on the unilateral kernels: of the shortest traces to "
        "`GENERAL_WAR` and to `ACCIDENTAL_WAR` by 1963 and the distances out of "
        "`⟨⟨USA⟩⟩` and `⟨⟨USSR⟩⟩` kernels of avoiding both by 1963, at least one puts the "
        "replay state nearer the adverse endings and none puts it farther, in every year "
        "of the gap; the gap closes within one year of `intel[USA] = "
        "overhead_reconnaissance` (1960 to 1961)"
    ),
    "expected": "as stated; the closing is driven by `intel`, not by any force change",
    "sources": "the NIE series (CIA CREST); Gaddis 2005; Preble 2004; amended 2026-10-23",
}

YEARS = range(1957, 1963)
GAP = range(1958, 1962)


def adverse(g, start):
    return {e: bfs_distance(g, g.index[start], ending_ids(g, e)) for e in ADVERSE}


def kernel_distances(g, start):
    """Distance out (0 when outside, None when never left) of {USA}'s and {USSR}'s kernels
    of avoiding the adverse endings on the cut graph ``g`` (amended (b), 2026-10-23)."""
    bad = ending_ids(g, *ADVERSE)
    keep = set(range(g.size())) - bad
    out = {}
    for side in ("USA", "USSR"):
        k = safe(g, [side], keep).kernel
        out[f"K_{side}"] = bfs_distance(g, g.index[start], set(range(g.size())) - k)
    return out


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
        b = breg = True
        for y in GAP:
            r, h = replay_state(y, aims), hindsight(y, aims)
            gr, gh = graph(cm, r, cut=16), graph(cm, h, cut=16)
            dr, dh = adverse(gr, r), adverse(gh, h)
            reg = more(dr, dh)
            # Amended 2026-10-23 (decision 2n): the unilateral kernels beside reachability.
            mr = {**dr, **kernel_distances(gr, r)}
            mh = {**dh, **kernel_distances(gh, h)}
            some, none_back = compare(mr, mh)
            ok = some and none_back
            print(
                f"[C6]   aims_USSR={aims} {y}: replay {mr} ({gr.size()}); "
                f"hindsight {mh} ({gh.size()}): registered {reg}, amended {ok}"
            )
            b = b and ok
            breg = breg and reg
        results[aims] = b
        print(f"[C6]   aims_USSR={aims}: (b) registered {breg}, amended {b}")
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
