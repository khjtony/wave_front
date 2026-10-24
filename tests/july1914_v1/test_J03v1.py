"""J3v1: registered 2026-10-24 in docs/july1914_testbed.md section 8.3 (the 1914 v1
registration, owner's decision 2h of 2026-10-23), before any v1 guard.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature, in the v1 content of section 8.2. Do not edit the claim text
without a changelog entry in that document. Skipped until ``models/july1914/v1.py`` exists
and the owner gives the go for the first sight by setting ``WF_FIRST_SIGHT_1914V1=1`` (the
skip condition was "v1.py exists" until the model step built it; changed then so that the
first sight is held, docs/july1914_v1_decisions.md V9). The body is the reading of
docs/july1914_v1_decisions.md section R (J3v1), written before that go.
"""

import itertools
import os
from pathlib import Path

import pytest

from models.july1914.v1 import PRINCIPALS
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

V1 = Path(__file__).resolve().parents[2] / "models" / "july1914" / "v1.py"
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_1914V1") == "1"

CLAIM = {
    "id": "J3v1",
    "from_state": "tick 0 to 30 (28 July)",
    "claim": (
        "**localization (hold-out), J3 as amended, re-asked on v1 unreworded (decision 5b).** A "
        "localized Austro-Serbian war (AUH at war with Serbia, no great-power mobilization) can be "
        "forced to the horizon only under `aims_GER = localize` with Russia at `deter`; read with "
        "the declaration of war required by 3 August, the pivotal coalition for keeping it "
        "localized is {GER, RUS} jointly, neither alone keeps it, and GBR is not pivotal at any "
        "tick (the model's result, registered: no British action reaches the Austro-Serbian dyad)"
    ),
    "expected": (
        "forceable from tick 0 under (localize, deter) only; pivotal coalition {GER, RUS} with the "
        "declaration by 3 August; GBR in no minimal forcing coalition at any tick"
    ),
    "sources": "J3's sources; amended 2026-10-23; re-asked on v1 2026-10-24",
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
@pytest.mark.skipif(
    not (V1.exists() and FIRST_SIGHT),
    reason="1914 v1 first sight held for the owner's go (WF_FIRST_SIGHT_1914V1=1)",
)
def test_J3v1():
    timer = Timer()
    print("\n[J3v1] engine: explicit, graph from tick 0 per pair; wavefront.analysis.pivotal")
    failures = []
    for pair in PAIRS:
        g, reachable, piv, per_tick, keep = j3_tables(pair)
        forceable = bool(piv.forcing)
        print(
            f"[J3v1] {label(pair)}: {g.size()} states; LOCALIZED forceable from tick 0 (amended "
            f"(a)): {forceable}; reachable (registered 2026-10-15): {reachable}"
        )
        print(
            f"[J3v1]   pivotal at tick 0: forcing {fmt(piv.forcing)}; blocking {fmt(piv.blocking)}"
        )
        print(f"[J3v1]   minimal coalitions keeping the invariant localized: {fmt(keep)}")
        gbr_ticks = [t for t, fam in per_tick if any("GBR" in c for c in fam)]
        print(
            f"[J3v1]   registered reading (ending at the horizon): ticks with GBR in a minimal "
            f"forcing coalition: {gbr_ticks}; forcing families along the realized prefix: "
            f"{changes_of(per_tick)}"
        )
        fam0, per_tick3 = j3_by_3_august(pair)
        gbr3 = [t for t, fam in per_tick3 if any("GBR" in c for c in fam)]
        print(
            f"[J3v1]   declaration by 3 August (amended (b), (c)): forcing at tick 0 {fmt(fam0)}; "
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
    print(f"[J3v1] done ({timer})")
    assert not failures, "; ".join(failures)
