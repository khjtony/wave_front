"""V7: Verification regimes on cw_v1 (C8 as amended).

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V7a. The readings the model step must fix before first sight are listed in
section 9.4.

Reading (docs/cw_v1_decisions.md, R V7): as v0's A C8 with ``balance_core`` in the
unilateral kernels. For each regime year Y in {1963, 1972, 1987}, per hypothesis: (a) the
hindsight ``oversight`` of Y + 1 is above that of Y; (b) s the hindsight state of Y + 1 and s-
the same with ``oversight`` at its level of Y; three distances (fewest transitions of
arbitrary play on the flattened game, a crisis counting its entry, fine steps and return): to
``GENERAL_WAR`` or ``ACCIDENTAL_WAR``, and out of K_USA and K_USSR of ``balance_core`` through
the horizon (0 when outside; never is infinitely far), by the layered lifting for 1964, the
composite engine for 1973 (explicit to 1984, the symbolic all-actor rank beyond) and the
symbolic engine for 1988; (b) holds iff for every Y at least one is larger from s and none is
smaller. (c) Control: on ``build(frozen_oversight=True)`` ``arms = reduced`` is unreachable
from the 1962 hindsight state within the horizon, while it is reachable on the model
(symbolic reachability on the coarse game; exact for this target). Holds iff (a), (b) and (c)
under at least one hypothesis.
"""

import os

import pytest

from tests.coldwar.common import level, with_level
from wavefront.model import V

from ..common import (
    HYPS,
    Timer,
    compare,
    compiled,
    composite_distances,
    composite_graph,
    encoding,
    engine_for,
    everyone_attractor,
    hindsight,
    layered_distance,
)

CLAIM = {
    "id": "V7",
    "from_state": "1963, 1972, 1987",
    "claim": (
        "on cw_v1, C8 as amended 2026-10-23, with `balance_core` in place of `balance_cw` in "
        "the unilateral kernels (the bloc clause empties `⟨⟨USA⟩⟩` by construction; section "
        "9.2): each verification regime raises `oversight`; holding forces constant, the "
        "distance to the boundary increases, measured on reachability and on the unilateral "
        "kernels: of the shortest trace to `GENERAL_WAR` or `ACCIDENTAL_WAR` and the "
        "distances out of `⟨⟨USA⟩⟩□balance_core` and `⟨⟨USSR⟩⟩□balance_core`, at least one "
        "is larger with the regime's `oversight` than with the level before it and none is "
        "smaller; with `oversight` frozen at 1962 levels, the 1987 to 1991 drawdown is "
        "unreachable within the horizon; the frozen-oversight clause is the claim's negative "
        "control"
    ),
    "expected": "as stated",
    "sources": "the treaty texts; Hoffman 2009; re-asks C8 as amended",
}

# The first-sight switch (docs/cw_v1_decisions.md D8): the claim runs only when the owner sets
# WF_FIRST_SIGHT_CWV1=1 for the one recorded run of V1 to V10.
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_CWV1") == "1"

REGIMES = (1963, 1972, 1987)
ORDER = ["none", "test_ban", "ntm", "on_site"]
KEYS = {
    "adverse": "adverse",
    "out K_USA": "out:USA:balance_core",
    "out K_USSR": "out:USSR:balance_core",
}


def distances(aims, year, states):
    """The three distances from each of ``states`` (hindsight-year ``year``), by the engine
    R assigns to the year."""
    engine = engine_for(year)
    if engine == "symbolic":
        ranks = {k: everyone_attractor(aims, key) for k, key in KEYS.items()}
        return [{k: r.rank(s) for k, r in ranks.items()} for s in states], engine
    if engine == "layered":
        ranks = {k: layered_distance(aims, key) for k, key in KEYS.items()}
        return [{k: r.rank(s) for k, r in ranks.items()} for s in states], engine
    g = composite_graph(aims, states)
    dist = composite_distances(aims, g, list(KEYS.values()))
    out = [{k: dist[key][g.index[s]] for k, key in KEYS.items()} for s in states]
    return out, f"composite ({g.size()} states to 1984)"


@pytest.mark.skipif(not FIRST_SIGHT, reason="cw_v1 first sight not switched on")
def test_V7():
    from wavefront.symbolic import shortest

    timer = Timer()
    print("\n[V7] engines: layered lifting (1964), composite (1973), symbolic (1988)")
    results = {}
    for aims in HYPS:
        cm = compiled(aims)
        ab = True
        for y in REGIMES:
            before = level(cm, hindsight(y, aims), "oversight")
            after = level(cm, hindsight(y + 1, aims), "oversight")
            a = ORDER.index(after) > ORDER.index(before)
            s = hindsight(y + 1, aims)
            sm = with_level(cm, s, "oversight", before)
            (m_s, m_m), engine = distances(aims, y + 1, [s, sm])
            some, none_back = compare(m_m, m_s)
            b = some and none_back
            print(
                f"[V7]   aims_USSR={aims} {y}: oversight {before} -> {after} ({a}); "
                f"distances {m_s} (lowered: {m_m}) [{engine}]: {b}"
            )
            ab = ab and a and b
        frozen = encoding(aims, frozen_oversight=True)
        start_f = hindsight(1962, aims, frozen_oversight=True)
        reduced_f = shortest(frozen, start_f, frozen.predicate(V.arms == "reduced"))
        enc = encoding(aims)
        reduced = shortest(enc, hindsight(1962, aims), enc.predicate(V.arms == "reduced"))
        c = reduced_f is None and reduced is not None
        print(f"[V7]   (c) arms = reduced from 1962: model in {reduced}; frozen: {reduced_f}")
        results[aims] = ab and c
        print(f"[V7] aims_USSR={aims}: (a) and (b) {ab}, (c) {c} ({timer})")
    assert any(results.values()), results
