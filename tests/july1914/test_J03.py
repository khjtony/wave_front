"""J3: registered 2026-10-15 in docs/july1914_testbed.md section 3.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature. Do not edit the claim text without a changelog entry in that
document.

Reading (docs/july1914_decisions.md, R J3), on the explicit graph from tick 0 per
hypothesis pair: (a) ``LOCALIZED`` reachable from the tick-0 state (attractor of every actor
with Nature) under ``(localize, deter)`` and unreachable under the other three pairs;
(b) ``pivotal(g, "LOCALIZED", initial=[s0])`` under ``(localize, deter)``: {GER, RUS} is a
minimal forcing coalition and neither {GER} nor {RUS} forces; (c) along the realized prefix
under ``(localize, deter)`` (ticks 0 to 32), GBR belongs to no minimal forcing coalition at
any tick up to 30 and to one at tick 31. Reported besides: the blocking families, the
per-tick table under every pair, and the minimal coalitions whose kernel for the invariant
``localized`` contains the tick-0 state. Engine: explicit (``wavefront.analysis.pivotal``;
per-tick families from one attractor per coalition on the same graph).
"""

import itertools

import pytest

from models.july1914.v0 import PRINCIPALS
from wavefront.analysis import pivotal, viability
from wavefront.engine import attractor

from .common import (
    PAIRS,
    Timer,
    all_attractors,
    fmt,
    forcing_family,
    graph0,
    label,
    replay,
)

CLAIM = {
    "id": "J3",
    "from_state": "tick 0 to 30 (28 July)",
    "claim": (
        "**localization (hold-out).** A localized Austro-Serbian war (AUH at war with Serbia, "
        "no great-power mobilization) is reachable to the horizon only under `aims_GER = "
        "localize` with Russia at `deter`, and the pivotal coalition for keeping it localized "
        "is {GER, RUS} jointly; neither alone keeps it, and GBR is not pivotal before 29 July"
    ),
    "expected": (
        "pivotal coalition {GER, RUS}; under `continental` aims the localized ending is "
        "unreachable; GBR's membership in a pivotal coalition appears only from tick 31"
    ),
    "sources": (
        "the \"Halt in Belgrade\" of 28 July; Sazonov's partial-mobilization scheme; Grey's "
        "mediation proposals of 24 to 29 July"
    ),
}


LOCALIZE_DETER = ("localize", "deter")


def keeping_family(g, s0, invariant="localized"):
    found = []
    for n in range(len(PRINCIPALS) + 1):
        for c in itertools.combinations(PRINCIPALS, n):
            c = frozenset(c)
            if any(m <= c for m in found):
                continue
            if s0 in viability(g, list(c), invariant).kernel:
                found.append(c)
    return found


def j3_tables(pair, cadence=True):
    """(s0 reachability, pivotal result at s0, per-tick forcing families along the realized
    prefix, the keeping family of the invariant) for one pair and build."""
    g = graph0(pair, cadence)
    (s0,) = g.initial
    target = g.ending_states("LOCALIZED")
    everyone = [a.name for a in g.model.actors]
    reachable = s0 in attractor(g, everyone, target).win
    piv = pivotal(g, "LOCALIZED", initial=[s0])
    wins = all_attractors(g, target)
    states, _ = replay(pair, cadence)
    per_tick = [(t, forcing_family(wins, g.index[s])) for t, s in enumerate(states)]
    return g, reachable, piv, per_tick, keeping_family(g, s0)


@pytest.mark.slow
def test_J3():
    timer = Timer()
    print("\n[J3] engine: explicit, graph from tick 0 per pair; wavefront.analysis.pivotal")
    failures = []
    for pair in PAIRS:
        g, reachable, piv, per_tick, keep = j3_tables(pair)
        print(
            f"[J3] {label(pair)}: {g.size()} states; LOCALIZED reachable from tick 0: {reachable}"
        )
        print(f"[J3]   pivotal at tick 0: forcing {fmt(piv.forcing)}; blocking {fmt(piv.blocking)}")
        print(f"[J3]   minimal coalitions keeping the invariant localized: {fmt(keep)}")
        gbr_ticks = [t for t, fam in per_tick if any("GBR" in c for c in fam)]
        print(f"[J3]   ticks with GBR in a minimal forcing coalition: {gbr_ticks}")
        changes, last = [], None
        for t, fam in per_tick:
            if fam != last:
                changes.append(f"t{t}: {fmt(fam)}")
                last = fam
        print(f"[J3]   forcing families along the realized prefix: {'; '.join(changes)}")
        want = pair == LOCALIZE_DETER
        if reachable != want:
            failures.append(f"{label(pair)}: LOCALIZED reachable {reachable}, claim {want}")
        if pair == LOCALIZE_DETER:
            if frozenset({"GER", "RUS"}) not in piv.forcing:
                failures.append(f"{{GER, RUS}} not a minimal forcing coalition: {fmt(piv.forcing)}")
            for single in ("GER", "RUS"):
                if any(c <= frozenset({single}) for c in piv.forcing):
                    failures.append(f"{{{single}}} forces LOCALIZED alone")
            early = [t for t in gbr_ticks if t <= 30]
            if early:
                failures.append(f"GBR pivotal before tick 31: {early}")
            if 31 not in gbr_ticks:
                failures.append("GBR not in a minimal forcing coalition at tick 31")
    print(f"[J3] done ({timer})")
    assert not failures, "; ".join(failures)
