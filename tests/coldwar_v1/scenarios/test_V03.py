"""V3: The October 1973 alert as a crisis sub-game.

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V3a. The readings the model step must fix before first sight are listed in
section 9.4.

Reading (docs/cw_v1_decisions.md, R V3): the 1973 hindsight state, the realized coarse move
of 1973 (``USSR.warn_unilateral``) and the sub-game graph from its first fine state, per
hypothesis. A fine state is in coalition C's lifted kernel iff C can keep ``fighting`` false
inside the sub-game until a terminal fine state whose return state (1 January 1974, the cut)
has ``esc < conventional`` (``no_war_core``). (a) The realized sub-game moves are available
from the entry and reach ``CEASEFIRE``; its return state is "the realized 1974 state"; zero
relaxations. (b) The first fine state is in the lifted kernel of {USA, USSR} and outside those
of {USA} and {USSR}; beside: the fortune variants and the unbounded lifted kernels (returns
valued by the composite engine's kernel of ``no_war_core`` through the horizon). (c) No edge
on a shortest play (all actors) from the first fine state into the realized return (the
terminal fine states whose return equals the realized 1974 state) has ``USA.defcon3``; and
from a (after USA ``defcon3``, USSR idle, Nature none) the fewest transitions to a terminal
fine state whose return has ``esc >= conventional`` is not larger than from r (after USA
``reply``; unreachable is infinitely far). Control: with every declared action of USA and USSR
forbidden in the sub-game, no state with ``fighting`` true is reachable. Holds iff (a), (b),
(c) and the control under at least one hypothesis. Hold-out: total. Engine: explicit on the
sub-game (composite for the unbounded column).
"""

import os
from collections import deque

import pytest

from models.ww2.hypotheses import realized_moves
from wavefront.engine import explore, safe
from wavefront.model import V

from ..common import (
    CRISIS_DATA,
    HYPS,
    Forbid,
    Timer,
    bfs_distance,
    compiled,
    composite_graph,
    composite_kernel,
    far,
    fine_graph,
    flat_of,
    hindsight,
)

CLAIM = {
    "id": "V3",
    "from_state": (
        "1973, October: the alert sub-game, entered from the 1973 hindsight state (the "
        "Arab–Israeli war under way; Brezhnev's message to Nixon of 24 Oct)"
    ),
    "claim": (
        "with `no_war_core := esc < conventional` kept inside the sub-game and at its "
        "return, bounded to 1 January 1974: (a) the realized play (the US alert of 24 to 25 "
        "Oct, no Soviet intervention, the ceasefire under Resolution 340 with a UN force "
        "without the principals) is reachable with zero relaxations; (b) the entry state is "
        "inside `⟨⟨USA, USSR⟩⟩□no_war_core` and outside `⟨⟨USA⟩⟩□no_war_core` and "
        "`⟨⟨USSR⟩⟩□no_war_core`: each side's readiness moves leave something to chance that "
        "the other side cannot remove; (c) the alert was not needed for the peaceful return "
        "and did not move the play away from war: no shortest play from the entry to the "
        "realized return contains the US alert, and the shortest play to `esc ≥ "
        "conventional` from the state after the alert is not longer than from the state "
        "after the documented alternative (a reply without the alert); control: in the "
        "restricted game in which neither principal plays any declared action, US–Soviet "
        "combat is unreachable in the sub-game (Nature, the belligerents included, does not "
        "bring the principals to combat alone)"
    ),
    "expected": (
        "(a) reachable with zero relaxations, quoted with its count and never as a finding; "
        "(b) joint in, both unilateral out, with the fortune variants and the unbounded "
        "lifted kernels reported beside; (c) as stated; the control's target unreachable"
    ),
    "sources": (
        "FRUS 1969–1976 vol. XXV; Kissinger 1982; Israelyan 1995; Lebow and Stein 1994; "
        "Garthoff 1994; Blechman and Hart 1982; Sagan 1985; Schelling 1966"
    ),
}

# The first-sight switch (docs/cw_v1_decisions.md D8): the claim runs only when the owner sets
# WF_FIRST_SIGHT_CWV1=1 for the one recorded run of V1 to V10.
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_CWV1") == "1"

NAME = "alert_1973"
JOINT, US, SU = ("USA", "USSR"), ("USA",), ("USSR",)


def realized_play(sub, first):
    """The realized fine states from ``first`` and the first unavailable move (or None)."""
    states, h = [first], first
    for move in realized_moves(sub, CRISIS_DATA / NAME / "realized_moves.csv"):
        if sub.is_terminal(h):
            break
        av = sub.available(h)
        bad = [
            f"{a.name}.{a.actions[j].name}"
            for a, j, acts in zip(sub.actors, move, av, strict=True)
            if j not in acts
        ]
        if bad:
            return states, bad
        h = sub.step(h, move)
        states.append(h)
    return states, None


def lifted(g, returns, coalition, member):
    """Fine states from which ``coalition`` keeps ``fighting`` false until a terminal fine
    state whose return state satisfies ``member``."""
    sub = g.model
    i = sub.index["fighting"]
    phi = {
        k for k, h in enumerate(g.states) if not h[i] and (not g.terminal[k] or member(returns[k]))
    }
    return safe(g, list(coalition), phi).kernel


def distances_to(g, targets):
    """Fewest transitions from every fine state into ``targets`` (reverse breadth-first)."""
    pred = [[] for _ in range(g.size())]
    for u in range(g.size()):
        for v in g.succ[u]:
            pred[v].append(u)
    dist = {t: 0 for t in targets}
    queue = deque(targets)
    while queue:
        v = queue.popleft()
        for u in pred[v]:
            if u not in dist:
                dist[u] = dist[v] + 1
                queue.append(u)
    return dist


def alert_on_shortest_plays(g, sub, first, targets):
    """``(d, edges)``: the shortest distance from ``first`` into ``targets`` and the edges on
    shortest plays whose joint move has the United States' ``defcon3``."""
    to = distances_to(g, targets)
    if first not in to:
        return None, []
    d = to[first]
    frm = {first: 0}
    queue = deque([first])
    while queue:
        u = queue.popleft()
        for v in g.succ[u]:
            if v not in frm:
                frm[v] = frm[u] + 1
                queue.append(v)
    usa = next(a for a in sub.actors if a.name == "USA")
    alert = usa.action_index("defcon3")
    edges = []
    for u, du in frm.items():
        for move, v in zip(g.moves[u], g.succ[u], strict=True):
            if v in to and du + 1 + to[v] == d and move[usa.index] == alert:
                edges.append((u, v))
    return d, edges


def after(sub, h, usa_action):
    names = {"USA": usa_action, "USSR": "idle", "Nature": "none"}
    move = tuple(a.action_index(names[a.name]) for a in sub.actors)
    available = all(j in acts for j, acts in zip(move, sub.available(h), strict=True))
    return sub.step(h, move), available


@pytest.mark.skipif(not FIRST_SIGHT, reason="cw_v1 first sight not switched on")
def test_V3():
    timer = Timer()
    print("\n[V3] engine: explicit on the alert sub-game; composite for the unbounded column")
    results = {}
    for aims in HYPS:
        cm = compiled(aims)
        fm = flat_of(aims)
        s73 = hindsight(1973, aims)
        g, returns, _ = fine_graph(fm, s73, NAME)
        sub = g.model
        first = g.initial[0]
        h0 = g.states[first]
        # (a)
        play, stop = realized_play(sub, h0)
        end = sub.ending_of(play[-1])
        a = stop is None and end == "CEASEFIRE"
        realized_return = returns.get(g.index[play[-1]]) if a else None
        print(
            f"[V3] aims_USSR={aims}: sub-game {g.size()} states; (a) realized days {len(play)}, "
            f"ending {end}, unavailable {stop}: {a} (zero relaxations)"
        )
        if realized_return is not None:
            print(f"[V3]   realized 1974 state: {cm.format_state(realized_return)}")

        # (b)
        def bounded(r):
            return bool(cm.evaluate("no_war_core", r))

        ks = {c: lifted(g, returns, c, bounded) for c in (JOINT, US, SU)}
        b = first in ks[JOINT] and first not in ks[US] and first not in ks[SU]
        fortune = {
            c: first in lifted(g, returns, c, bounded)
            for c in (("USA", "Nature"), ("USSR", "Nature"))
        }
        starts = sorted(set(returns.values()))
        g2 = composite_graph(aims, starts)
        unbounded = {}
        for c in (JOINT, US, SU):
            k2 = composite_kernel(g2, aims, c, "no_war_core")
            unbounded[c] = first in lifted(g, returns, c, lambda r, k2=k2: g2.index[r] in k2)
        print(
            f"[V3]   (b) first fine state in K_J {first in ks[JOINT]}, K_USA {first in ks[US]}, "
            f"K_USSR {first in ks[SU]}: {b}; beside: fortune {fortune}; unbounded "
            f"(composite, {g2.size()} states) {unbounded}"
        )
        # (c)
        c1 = False
        if realized_return is not None:
            target = {i for i, r in returns.items() if r == realized_return}
            d, edges = alert_on_shortest_plays(g, sub, first, target)
            c1 = d is not None and not edges
            print(
                f"[V3]   (c) shortest play into the realized return: {d} transitions; edges "
                f"with USA.defcon3 on shortest plays: {len(edges)}"
            )
        war = {i for i, r in returns.items() if cm.evaluate(V.esc >= "conventional", r)}
        ha, ok_a = after(sub, h0, "defcon3")
        hr, ok_r = after(sub, h0, "reply")
        da = bfs_distance(g, g.index[ha], war) if ok_a else None
        dr = bfs_distance(g, g.index[hr], war) if ok_r else None
        c2 = ok_a and ok_r and far(da) <= far(dr)
        print(
            f"[V3]   (c) to a return with esc >= conventional: after the alert {da}, after the "
            f"reply alone {dr} (available {ok_a}, {ok_r}): {c2}"
        )
        c = c1 and c2
        # control
        pairs = [
            (a.name, x.name)
            for a in sub.actors
            if a.name in ("USA", "USSR")
            for x in a.actions
            if not x.is_idle
        ]
        gc = explore(Forbid(sub, pairs), initial=[h0])
        fi = sub.index["fighting"]
        control = not any(h[fi] for h in gc.states)
        print(f"[V3]   control (USA and USSR idle): fighting reachable {not control}")
        results[aims] = (a, b, c, control)
        print(f"[V3] aims_USSR={aims}: (a) {a}, (b) {b}, (c) {c}, control {control} ({timer})")
    assert any(all(v) for v in results.values()), results
