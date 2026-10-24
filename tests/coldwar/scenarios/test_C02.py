"""C2: Joint kernel membership and unilateral non-membership every year from 1965.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document. Amended 2026-10-23 on the owner's decision 2o:
asked with the balance predicate without the clause on the opponent's bloc (review of
2026-10-18, section 2; the T13 precedent), beside the registered predicate; the previous
wording is in git history and in reports/cw_v0.md section 3.

Reading (docs/cw_v0_decisions.md, R C2, with the amendment A C2): for each year from 1965 to
1991, the hindsight state per hypothesis; K_J = safe({USA, USSR}, P), K_USA, K_USSR the
unilateral kernels (symbolic, coarse game; exact by decisions D5), for P the amended predicate
``balance_nobloc := no_war ∧ both_or_neither`` (``balance_cw`` without ``bloc_intact``) and,
beside it, the registered ``balance_cw``. Holds iff, under at least one hypothesis, the state
is in K_J every year and outside K_USA and K_USSR every year, for ``balance_nobloc`` (the
amended claim); the registered predicate's result is printed and not asserted. What each side
could do to break it is reported for both predicates: the first move of the other side's
(with Nature) forcing strategy out of P, where it has one. Engine: symbolic.
"""

from wavefront.model import V

from ..common import HYPS, PRINCIPALS, Timer, compiled, encoding, hindsight

CLAIM = {
    "id": "C2",
    "from_state": "each year from 1965 (mutual survivable second strike)",
    "claim": (
        "the realized state is inside the joint kernel `⟨⟨USA, USSR⟩⟩□balance_nobloc` "
        "every year, and outside the unilateral kernels `⟨⟨USA⟩⟩□balance_nobloc` and "
        "`⟨⟨USSR⟩⟩□balance_nobloc`, where `balance_nobloc` is `balance_cw` without the "
        "clause on the blocs (both principals retain survivable second strike or neither "
        "has it, and esc < conventional between principals)"
    ),
    "expected": (
        "joint membership every year; unilateral non-membership every year; the report "
        "names what each side could do to break it; the kernels of the registered "
        "`balance_cw` are reported beside"
    ),
    "sources": "Schelling 1960, 1966; Trachtenberg 1999; amended 2026-10-23",
}

YEARS = range(1965, 1992)
BOTH = ((V.nuke_USA >= "survivable") & (V.nuke_USSR >= "survivable")) | (
    (V.nuke_USA < "survivable") & (V.nuke_USSR < "survivable")
)
# Amended 2026-10-23 (decision 2o): balance_cw without the clause on the blocs.
PREDICATES = {
    "balance_nobloc": V.invariant("no_war") & BOTH,
    "balance_cw": V.invariant("balance_cw"),
}


def kernels(aims, name):
    from wavefront.symbolic import safe

    enc = encoding(aims)
    phi = enc.predicate(PREDICATES[name])
    return {c: safe(enc, list(c), phi) for c in (("USA", "USSR"), ("USA",), ("USSR",))}


def breaker(aims, name, defender, state):
    """The first move of the rest's (Nature included) forcing strategy out of predicate
    ``name`` from ``state``, as names, or None if the rest cannot force it."""
    from wavefront.symbolic import attractor

    enc = encoding(aims)
    cm = compiled(aims)
    rest = [a for a in (*PRINCIPALS, "Nature") if a not in defender]
    out = enc.mgr.DIFF(enc.dom, enc.predicate(PREDICATES[name]))
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
    print("\n[C2] engine: symbolic kernels (coarse game), hindsight snapshots")
    passed = []
    for aims in HYPS:
        cm = compiled(aims)
        verdict = {}
        for name in PREDICATES:
            ks = kernels(aims, name)
            kj, ku, kr = ks[("USA", "USSR")], ks[("USA",)], ks[("USSR",)]
            ok = True
            print(f"[C2] aims_USSR={aims} [{name}]: year: predicate, joint, USA, USSR")
            for y in YEARS:
                s = hindsight(y, aims)
                j, u, r = kj.contains(s), ku.contains(s), kr.contains(s)
                holds = bool(cm.evaluate(PREDICATES[name], s))
                print(f"[C2]   {y}: {holds}, {j}, {u}, {r}")
                ok = ok and j and not u and not r
            for y in (1965, 1970, 1975, 1980, 1985, 1990):
                s = hindsight(y, aims)
                for side in (("USA",), ("USSR",)):
                    try:
                        note = breaker(aims, name, side, s)
                    except Exception as exc:  # reported, not asserted
                        note = f"not computed ({type(exc).__name__})"
                    print(f"[C2]   {y}: against {side[0]} alone: {note}")
            verdict[name] = ok
            print(
                f"[C2] aims_USSR={aims} [{name}]: claim {'holds' if ok else 'does not hold'} "
                f"({timer})"
            )
        print(
            f"[C2] aims_USSR={aims}: amended (balance_nobloc) {verdict['balance_nobloc']}; "
            f"registered (balance_cw) {verdict['balance_cw']}"
        )
        if verdict["balance_nobloc"]:
            passed.append(aims)
    assert passed, "joint membership with unilateral non-membership fails every year set"
