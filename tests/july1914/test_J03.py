"""J3: registered 2026-10-15 in docs/july1914_testbed.md section 3; amended 2026-10-23 on the
owner's decision 2f (docs/owner_decisions_2026-10-23.md; the previous wording is in git
history and reports/july1914.md section 12).

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature. Do not edit the claim text without a changelog entry in that
document.

Reading (docs/july1914_decisions.md, R J3, with the amendment of 2026-10-23), on the explicit
graph from tick 0 per hypothesis pair: (a) forceability: the ending ``LOCALIZED`` is forced
from the tick-0 state by the coalition of all five principals (Nature the adversary) under
``(localize, deter)`` and by no coalition under the other three pairs. (b) and (c) read
"localized" with the declaration of war required by 3 August: the target is the set of
states at tick 37 with ``war_AUH_SER == war`` from which the coalition forces ``LOCALIZED``
(every play passes through exactly one state at tick 37 unless it ended before, so a
coalition's attractor of that set is exactly "forces a localized war whose declaration is
visible by tick 37"). (b) under ``(localize, deter)``, {GER, RUS} is a minimal coalition
forcing that target from tick 0 and neither {GER} nor {RUS} forces it; (c) the model's
result, registered: GBR belongs to no minimal forcing coalition of that target at any tick of
the realized prefix, under every pair. Reported besides: the registered readings of
2026-10-15 (reachability, ``pivotal`` on the ending at the horizon, GBR from tick 31), the
blocking families, the per-tick tables under every pair, and the minimal coalitions whose
kernel for the invariant ``localized`` contains the tick-0 state. Engine: explicit
(``wavefront.analysis.pivotal``; per-tick families from one attractor per coalition on the
same graph)."""

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
        "no great-power mobilization) can be forced to the horizon only under `aims_GER = "
        "localize` with Russia at `deter`; read with the declaration of war required by 3 "
        "August, the pivotal coalition for keeping it localized is {GER, RUS} jointly, "
        "neither alone keeps it, and GBR is not pivotal at any tick (the model's result, "
        "registered: no British action reaches the Austro-Serbian dyad)"
    ),
    "expected": (
        "forceable from tick 0 under (localize, deter) only; pivotal coalition {GER, RUS} "
        "with the declaration by 3 August; GBR in no minimal forcing coalition at any tick"
    ),
    "sources": (
        "the \"Halt in Belgrade\" of 28 July; Sazonov's partial-mobilization scheme; Grey's "
        "mediation proposals of 24 to 29 July; amended 2026-10-23"
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


BY_3_AUGUST = 37  # the declaration of war visible by the state of 4 August (decided by 3 August)


def by_3_august_attractors(g):
    """For every coalition of principals (Nature the adversary), the states from which it
    forces ``LOCALIZED`` with the declaration of war on Serbia visible by tick 37 (amended
    reading of 2026-10-23): the attractor of the tick-37 states with ``war_AUH_SER == war``
    inside the coalition's attractor of ``LOCALIZED``."""
    cm = g.model
    loc = g.ending_states("LOCALIZED")
    ti, wi = cm.index["tick"], cm.index["war_AUH_SER"]
    war = cm.variables[wi].levels.index("war")
    at37 = {s for s in range(g.size()) if g.states[s][ti] == BY_3_AUGUST and g.states[s][wi] == war}
    out = {}
    for c, win in all_attractors(g, loc).items():
        out[c] = attractor(g, list(c), at37 & win).win
    return out


def j3_by_3_august(pair, cadence=True):
    """(forcing family at tick 0, per-tick forcing families along the realized prefix) for
    the localized war with the declaration by 3 August."""
    g = graph0(pair, cadence)
    (s0,) = g.initial
    wins = by_3_august_attractors(g)
    states, _ = replay(pair, cadence)
    per_tick = [(t, forcing_family(wins, g.index[s])) for t, s in enumerate(states)]
    return forcing_family(wins, s0), per_tick


def changes_of(per_tick):
    changes, last = [], None
    for t, fam in per_tick:
        if fam != last:
            changes.append(f"t{t}: {fmt(fam)}")
            last = fam
    return "; ".join(changes)


@pytest.mark.slow
def test_J3():
    timer = Timer()
    print("\n[J3] engine: explicit, graph from tick 0 per pair; wavefront.analysis.pivotal")
    failures = []
    for pair in PAIRS:
        g, reachable, piv, per_tick, keep = j3_tables(pair)
        forceable = bool(piv.forcing)
        print(
            f"[J3] {label(pair)}: {g.size()} states; LOCALIZED forceable from tick 0 (amended "
            f"(a)): {forceable}; reachable (registered 2026-10-15): {reachable}"
        )
        print(f"[J3]   pivotal at tick 0: forcing {fmt(piv.forcing)}; blocking {fmt(piv.blocking)}")
        print(f"[J3]   minimal coalitions keeping the invariant localized: {fmt(keep)}")
        gbr_ticks = [t for t, fam in per_tick if any("GBR" in c for c in fam)]
        print(
            f"[J3]   registered reading (ending at the horizon): ticks with GBR in a minimal "
            f"forcing coalition: {gbr_ticks}; forcing families along the realized prefix: "
            f"{changes_of(per_tick)}"
        )
        fam0, per_tick3 = j3_by_3_august(pair)
        gbr3 = [t for t, fam in per_tick3 if any("GBR" in c for c in fam)]
        print(
            f"[J3]   declaration by 3 August (amended (b), (c)): forcing at tick 0 {fmt(fam0)}; "
            f"along the realized prefix: {changes_of(per_tick3)}; ticks with GBR: {gbr3}"
        )
        want = pair == LOCALIZE_DETER
        if forceable != want:
            failures.append(f"{label(pair)}: LOCALIZED forceable {forceable}, claim {want}")
        if gbr3:
            failures.append(f"{label(pair)}: GBR in a minimal forcing coalition at {gbr3}")
        if pair == LOCALIZE_DETER:
            if frozenset({"GER", "RUS"}) not in fam0:
                failures.append(
                    f"{{GER, RUS}} not a minimal coalition forcing the localized war with the "
                    f"declaration by 3 August: {fmt(fam0)}"
                )
            for single in ("GER", "RUS"):
                if any(c <= frozenset({single}) for c in fam0):
                    failures.append(f"{{{single}}} forces the localized war alone")
    print(f"[J3] done ({timer})")
    assert not failures, "; ".join(failures)
