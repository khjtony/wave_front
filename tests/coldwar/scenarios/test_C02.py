"""C2: Joint kernel membership and unilateral non-membership every year from 1965.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.

Reading (docs/cw_v0_decisions.md, R C2): for each year from 1965 to 1991, the hindsight
state per hypothesis; K_J = safe({USA, USSR}, balance_cw), K_USA, K_USSR the unilateral
kernels (symbolic, coarse game; exact by decisions D5). Holds iff, under at least one
hypothesis, the state is in K_J every year and outside K_USA and K_USSR every year. What each
side could do to break it is reported: the first move of the other side's (with Nature)
forcing strategy out of balance, where it has one. Engine: symbolic.
"""

from ..common import HYPS, PRINCIPALS, Timer, compiled, encoding, hindsight, kernel

CLAIM = {
    "id": "C2",
    "from_state": "each year from 1965 (mutual survivable second strike)",
    "claim": (
        "the realized state is inside the joint kernel `⟨⟨USA, USSR⟩⟩□balance_cw` "
        "every year, and outside the unilateral kernels `⟨⟨USA⟩⟩□balance_cw` and "
        "`⟨⟨USSR⟩⟩□balance_cw`"
    ),
    "expected": (
        "joint membership every year; unilateral non-membership every year; the report "
        "names what each side could do to break it"
    ),
    "sources": "Schelling 1960, 1966; Trachtenberg 1999",
}

YEARS = range(1965, 1992)


def breaker(aims, defender, state):
    """The first move of the rest's (Nature included) forcing strategy out of balance_cw
    from ``state``, as names, or None if the rest cannot force it."""
    from wavefront.symbolic import attractor

    enc = encoding(aims)
    cm = compiled(aims)
    rest = [a for a in (*PRINCIPALS, "Nature") if a not in defender]
    out = enc.mgr.DIFF(enc.dom, enc.predicate("balance_cw"))
    res = attractor(enc, rest, out)
    if not res.contains(state):
        return None
    move = res.strategy_move(state)
    idx = enc.actor_indices(rest)
    names = []
    for i, j in zip(idx, move or (), strict=False):
        x = cm.actors[i].actions[j]
        if not x.is_idle:
            names.append(f"{cm.actors[i].name}.{x.name}")
    return f"forced in {res.rank(state)} ticks, first move {names or ['idle']}"


def test_C02():
    timer = Timer()
    print("\n[C2] engine: symbolic kernels of balance_cw (coarse game), hindsight snapshots")
    passed = []
    for aims in HYPS:
        cm = compiled(aims)
        kj = kernel(aims, ("USA", "USSR"))
        ku = kernel(aims, ("USA",))
        ks = kernel(aims, ("USSR",))
        ok = True
        print(f"[C2] aims_USSR={aims}: year: balance, joint, USA, USSR")
        for y in YEARS:
            s = hindsight(y, aims)
            j, u, r = kj.contains(s), ku.contains(s), ks.contains(s)
            bal = bool(cm.evaluate("balance_cw", s))
            print(f"[C2]   {y}: {bal}, {j}, {u}, {r}")
            ok = ok and j and not u and not r
        for y in (1965, 1970, 1975, 1980, 1985, 1990):
            s = hindsight(y, aims)
            for side in (("USA",), ("USSR",)):
                try:
                    note = breaker(aims, side, s)
                except Exception as exc:  # reported, not asserted
                    note = f"not computed ({type(exc).__name__})"
                print(f"[C2]   {y}: against {side[0]} alone: {note}")
        print(f"[C2] aims_USSR={aims}: claim {'holds' if ok else 'does not hold'} ({timer})")
        if ok:
            passed.append(aims)
    assert passed, "joint membership with unilateral non-membership fails every year set"
