"""C8: Each verification regime raises `oversight` and the distance to the boundary.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document. Part (b) amended 2026-10-23 on the owner's
decision 2n (oversight measured by its effect on reachability and on the unilateral kernels,
not on the joint kernel's distance); the previous wording is in git history and in
reports/cw_v0.md section 9.

Reading (docs/cw_v0_decisions.md, R C8, with the amendment A C8): for each regime year Y in
{1963, 1972, 1987}, per hypothesis: (a) the hindsight ``oversight`` of Y + 1 is above that of
Y; (b) amended: from the hindsight state s of Y + 1 and s- (s with ``oversight`` at its level
of Y), three distances to the boundary are taken: the shortest trace to GENERAL_WAR or
ACCIDENTAL_WAR, and the distance out of K_USA and of K_USSR, the unilateral kernels of
``balance_cw`` (0 when the state is outside; every distance the fewest transitions of
arbitrary play from the state, by forward images; never is infinitely far); (b)
holds iff at least one distance is larger from s and none is smaller. The registered (b),
the distance out of K_J, is printed beside it. (c) on the analysis build
``frozen_oversight``, ``arms = reduced`` is unreachable from the 1962 hindsight state, and
reachable on the model. Holds iff (a), (b) for every Y, and (c), under at least one
hypothesis. Engine: symbolic.
"""

import pytest

from wavefront.model import V

from ..common import (
    HYPS,
    Timer,
    compare,
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
        "distance to the boundary increases, measured on reachability and on the "
        "unilateral kernels: of the shortest trace to `GENERAL_WAR` or `ACCIDENTAL_WAR` "
        "and the distances out of `⟨⟨USA⟩⟩□balance_cw` and `⟨⟨USSR⟩⟩□balance_cw`, at "
        "least one is larger with the regime's `oversight` than with the level before "
        "it and none is smaller; with `oversight` frozen at 1962 levels, the 1987 to "
        "1991 drawdown is unreachable within the horizon"
    ),
    "expected": "as stated",
    "sources": "the treaty texts; Hoffman 2009; amended 2026-10-23",
}

REGIMES = (1963, 1972, 1987)


def measures(aims, state):
    """Distances to the boundary (amended (b), 2026-10-23): the shortest trace to the
    adverse endings and the distances out of the unilateral kernels of balance_cw, each
    by forward breadth-first images from ``state`` (as ``shortest_out``)."""
    from wavefront.symbolic import shortest

    enc = encoding(aims)
    return {
        "adverse": shortest(enc, state, enc.predicate(~V.invariant("no_general_war"))),
        "out K_USA": shortest_out(kernel(aims, ("USA",)), state),
        "out K_USSR": shortest_out(kernel(aims, ("USSR",)), state),
    }


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
            breg = (ins and not insm) or (
                ins and insm and dm is not None and (ds is None or ds > dm)
            )
            # Amended 2026-10-23 (decision 2n): reachability and the unilateral kernels.
            m_s, m_m = measures(aims, s), measures(aims, sm)
            some, none_back = compare(m_m, m_s)
            b = some and none_back
            print(
                f"[C8]   aims_USSR={aims} {y}: oversight {before} -> {after} ({a}); "
                f"in K_J {ins} (lowered: {insm}); shortest out {ds} (lowered: {dm}): "
                f"registered {breg}"
            )
            print(f"[C8]     distances {m_s} (lowered: {m_m}): amended {b}")
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
