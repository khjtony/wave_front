"""C8: Each verification regime raises `oversight` and the distance to the boundary.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.

Reading (docs/cw_v0_decisions.md, R C8): for each regime year Y in {1963, 1972, 1987},
per hypothesis: (a) the hindsight ``oversight`` of Y + 1 is above that of Y; (b) from the
hindsight state s of Y + 1 and s- (s with ``oversight`` at its level of Y), the shortest
distance out of K_J (symbolic) is larger from s, or s is inside and s- outside; (c) on the
analysis build ``frozen_oversight``, ``arms = reduced`` is unreachable from the 1962 hindsight
state, and reachable on the model. Holds iff (a), (b) for every Y, and (c), under at least one
hypothesis. Engine: symbolic.
"""

import pytest

from wavefront.model import V

from ..common import (
    HYPS,
    Timer,
    compiled,
    encoding,
    hindsight,
    kernel,
    level,
    shortest_out,
    with_level,
)

CLAIM = {
    "id": "C8",
    "from_state": "1963, 1972, 1987",
    "claim": (
        "each verification regime raises `oversight`; holding forces constant, the "
        "distance to the boundary increases; with `oversight` frozen at 1962 levels, "
        "the 1987 to 1991 drawdown is unreachable within the horizon"
    ),
    "expected": "as stated",
    "sources": "the treaty texts; Hoffman 2009",
}

REGIMES = (1963, 1972, 1987)


@pytest.mark.slow
def test_C08():
    from wavefront.symbolic import shortest

    timer = Timer()
    print("\n[C8] engine: symbolic (coarse game)")
    results = {}
    for aims in HYPS:
        cm = compiled(aims)
        kj = kernel(aims, ("USA", "USSR"))
        ab = True
        for y in REGIMES:
            before, after = (
                level(cm, hindsight(y, aims), "oversight"),
                level(cm, hindsight(y + 1, aims), "oversight"),
            )
            order = ["none", "test_ban", "ntm", "on_site"]
            a = order.index(after) > order.index(before)
            s = hindsight(y + 1, aims)
            sm = with_level(cm, s, "oversight", before)
            ins, insm = kj.contains(s), kj.contains(sm)
            ds, dm = shortest_out(kj, s), shortest_out(kj, sm)
            b = (ins and not insm) or (ins and insm and dm is not None and (ds is None or ds > dm))
            print(
                f"[C8]   aims_USSR={aims} {y}: oversight {before} -> {after} ({a}); "
                f"in K_J {ins} (lowered: {insm}); shortest out {ds} (lowered: {dm}): {b}"
            )
            ab = ab and a and b
        frozen = encoding(aims, frozen_oversight=True)
        start_f = hindsight(1962, aims, frozen=True)
        reduced_f = shortest(frozen, start_f, frozen.predicate(V.arms == "reduced"))
        enc = encoding(aims)
        reduced = shortest(enc, hindsight(1962, aims), enc.predicate(V.arms == "reduced"))
        c = reduced_f is None and reduced is not None
        print(f"[C8]   (c) arms = reduced from 1962: model in {reduced} ticks; frozen: {reduced_f}")
        results[aims] = ab and c
        print(f"[C8] aims_USSR={aims}: {results[aims]} ({timer})")
    assert any(results.values()), results
