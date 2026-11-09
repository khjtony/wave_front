"""V2: Joint, not unilateral, US–Soviet balance every year from 1967 (C2, H7).

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V2a. The readings the model step must fix before first sight are listed in
section 9.4.

Reading (docs/cw_v1_decisions.md, R V2): for each year 1967 to 1991, per hypothesis, the
hindsight state; K_J, K_USA, K_USSR the kernels of ``balance_core`` through the horizon on the
flattened game (the sub-games active), by the composite engine for 1972 to 1983, the symbolic
engine from 1984 and the layered lifting for 1967 to 1971 (D7; each exact). Holds iff, under at
least one hypothesis, the state is in K_J every year and outside K_USA and K_USSR every year,
and the control holds under that hypothesis: on ``build(us_crisis_options=False)`` the state is
inside K_USSR in at least one year (same engines). Breaking moves (printed, not asserted): for
each year and unilateral kernel, the moves of the attractor strategy of the other principal
joined by Nature, the PRC idle, out of ``balance_core``, played from the state (the defender
idle) until the play leaves ``balance_core``, enters a crisis or ends; if that attractor does
not contain the state, the attractor of the other principal joined by the PRC and Nature (no
action forbidden), printed "with the PRC", else "not forced" (R notes of 2026-10-27, decision
2). Beside, not asserted: the fortune variants ({USA, Nature}, {USSR, Nature}), the kernels of
``balance_cw`` and ``balance_tri`` for the same coalitions (these by the layered lifting) and
the coarse kernels with the sub-games inert. Choices R left open: decisions section R notes.
"""

import os

import pytest

from ..common import (
    HYPS,
    Timer,
    compiled,
    composite_graph,
    composite_kernel,
    engine_for,
    hindsight,
    kernel,
    layered_kernel,
    lift_of,
    move_names,
    prc_idle,
)

CLAIM = {
    "id": "V2",
    "from_state": (
        "each year 1967 to 1991 (both principals at survivable second strike on the record; "
        "Podvig 2001)"
    ),
    "claim": (
        "with `balance_core := esc < conventional ∧ both_or_neither` (US–Soviet only; no "
        "clause on either bloc or on the PRC): the realized state is inside the joint kernel "
        "`⟨⟨USA, USSR⟩⟩□balance_core` every year and outside the unilateral kernels "
        "`⟨⟨USA⟩⟩□balance_core` and `⟨⟨USSR⟩⟩□balance_core` every year (H7); for each year "
        "and each unilateral kernel, the first moves of the other side's forcing strategy "
        "(with Nature) out of `balance_core` are named; control: on the analysis build "
        "without the American crisis-initiating options of the 1970s and 1980s, the state is "
        "inside `⟨⟨USSR⟩⟩□balance_core` in at least one year, so that the United States' "
        "ability to break the balance in the main result is owed to the added options"
    ),
    "expected": (
        "joint membership every year; non-membership of both unilateral kernels every year, "
        "each with its breaking moves named; the control as stated; the kernels of the "
        "registered `balance_cw` and of `balance_tri` reported beside, not asserted"
    ),
    "sources": (
        "Schelling 1960, 1966; Trachtenberg 1999; Sagan and Suri 2003; Blechman and Hart "
        "1982; Jones 2016; re-asks C2 as amended 2026-10-23"
    ),
}

# The first-sight switch (docs/cw_v1_decisions.md D8): the claim runs only when the owner sets
# WF_FIRST_SIGHT_CWV1=1 for the one recorded run of V1 to V10.
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_CWV1") == "1"

YEARS = range(1967, 1992)
P = "balance_core"
JOINT, US, SU = ("USA", "USSR"), ("USA",), ("USSR",)
COALITIONS = (JOINT, US, SU)
FORTUNE = (("USA", "Nature"), ("USSR", "Nature"))
BESIDE = ("balance_cw", "balance_tri")


def members(aims, year, coalitions, **build):
    """Membership of the year's hindsight state in each coalition's kernel of P, by the
    engine R assigns to the year, and the size of the explicit part (composite years)."""
    s = hindsight(year, aims, **build)
    engine = engine_for(year)
    if engine == "symbolic":
        return {c: kernel(aims, c, P, **build).contains(s) for c in coalitions}, engine
    if engine == "layered":
        return {c: layered_kernel(aims, c, P, **build).contains(s) for c in coalitions}, engine
    g = composite_graph(aims, [s], **build)
    start = g.index[s]
    out = {c: start in composite_kernel(g, aims, c, P, **build) for c in coalitions}
    return out, f"composite ({g.size()} states to 1984)"


def breaking_moves(aims, defender, state):
    """The attractor strategy of the other principal joined by Nature (the PRC idle) out of
    P, played from ``state`` with the defender idle, until the play leaves P, enters a
    crisis or ends (layered lifting, exact on the flattened game). If that attractor does not
    contain the state, the attractor of the other principal joined by the PRC and Nature (no
    action forbidden), its moves marked "with the PRC"; if neither contains it, "not forced"
    (the game is concurrent and not assumed determined). R notes of 2026-10-27, decision 2."""
    other = "USSR" if defender == US else "USA"
    played = _play(aims, (other, "Nature"), lift_of(aims, prc_idle(aims)), state)
    if played is not None:
        return played
    played = _play(aims, (other, "PRC", "Nature"), lift_of(aims), state)
    if played is not None:
        return f"with the PRC: {played}"
    return "not forced"


def _play(aims, attacker, lift, state):
    """The moves of ``attacker``'s attractor strategy out of P from ``state`` (the others
    idle), or None if the attractor does not contain the state."""
    cm = compiled(aims)
    enc = lift.enc
    res = lift.attractor(attacker, enc.mgr.DIFF(enc.dom, enc.predicate(P)))
    if not res.contains(state):
        return None
    idx = enc.actor_indices(attacker)
    plays, s = [], tuple(state)
    while cm.evaluate(P, s) and not cm.is_terminal(s):
        sub = lift.strategy_move(res, s)
        if sub is None:
            break
        move = [0] * len(cm.actors)
        for a, j in zip(idx, sub, strict=True):
            move[a] = j
        year = 1947 + s[cm.index["tick"]]
        crisis = lift.crisis_at(s)
        if crisis is not None and move[crisis.actor] == crisis.action:
            plays.append(f"{year}: enters {crisis.label} (forced through it)")
            break
        plays.append(f"{year}: {move_names(cm, move) or ['idle']}")
        s = cm.step(s, tuple(move))
    return "; ".join(plays) or "outside P already"


@pytest.mark.skipif(not FIRST_SIGHT, reason="cw_v1 first sight not switched on")
def test_V2():
    timer = Timer()
    print("\n[V2] engines: composite 1972-1983, symbolic from 1984, layered lifting 1967-1971")
    results = {}
    for aims in HYPS:
        cm = compiled(aims)
        main = True
        print(f"[V2] aims_USSR={aims}: year: {P}, K_J, K_USA, K_USSR (engine)")
        for y in YEARS:
            s = hindsight(y, aims)
            m, engine = members(aims, y, COALITIONS)
            ok = m[JOINT] and not m[US] and not m[SU]
            main = main and ok
            print(
                f"[V2]   {y}: {bool(cm.evaluate(P, s))}, {m[JOINT]}, {m[US]}, {m[SU]} ({engine})"
                f"{'' if ok else '  <- fails'}"
            )
            fortune = {c: layered_kernel(aims, c, P).contains(s) for c in FORTUNE}
            beside = {
                (inv, c): layered_kernel(aims, c, inv).contains(s)
                for inv in BESIDE
                for c in COALITIONS
            }
            inert = {c: kernel(aims, c, P).contains(s) for c in COALITIONS}
            print(
                f"[V2]     beside: fortune {fortune}; "
                + "; ".join(f"{inv} {[beside[(inv, c)] for c in COALITIONS]}" for inv in BESIDE)
                + f"; coarse inert {[inert[c] for c in COALITIONS]}"
            )
            for side in (US, SU):
                print(f"[V2]     breaking K_{side[0]}: {breaking_moves(aims, side, s)}")
        control = {}
        for y in YEARS:
            m, engine = members(aims, y, (SU,), us_crisis_options=False)
            control[y] = m[SU]
        c = any(control.values())
        print(f"[V2]   control (no American crisis options), K_USSR by year: {control}")
        results[aims] = (main, c)
        print(f"[V2] aims_USSR={aims}: main {main}, control {c} ({timer})")
    assert any(all(v) for v in results.values()), results
