"""J2: registered 2026-10-15 in docs/july1914_testbed.md section 3.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature. Do not edit the claim text without a changelog entry in that
document.

Reading (docs/july1914_decisions.md, R J2): under the pairs whose realized path reaches
tick 38 (``aims_RUS = fight``), on the explicit graph from the realized state at tick 32:
(a) for every coalition C excluding RUS, ``viability(g, C, "no_war_GER_RUS")`` and the
departure along the realized path from 32; holds iff every departure is at most 34; (b) the
same for X = {AUH, GER, FRA, GBR} with ``GER.mobilize_east:coupling`` relaxed (recompiled and
re-explored from the same state): the shift (a kernel kept to the end counting as 39) is at
least 2; (c) the named assumptions whose single relaxation puts X's departure state back in
X's kernel include the coupling. Reported besides: Russia's forced days to war at the
departure state, the state-perturbation sensitivity at tick 32, the departure along the
realized path from tick 0, and the ``deter`` pairs. Engine: explicit
(``wavefront.engine.explore``, ``wavefront.analysis.viability``,
``point_of_no_return``-style departure, ``sensitivity``).
"""

import pytest

from models.july1914.v0 import build
from wavefront.analysis import sensitivity, viability
from wavefront.analysis._common import remap_states
from wavefront.engine import attractor
from wavefront.model import ModelError

from .common import (
    COALITIONS_WITHOUT_RUS,
    COUPLING,
    FIGHT,
    PAIRS,
    Timer,
    X,
    compiled,
    departure,
    graph0,
    graph_from,
    kept_as,
    label,
    path_ids,
    replay,
)

CLAIM = {
    "id": "J2",
    "from_state": "tick 32 (30 July)",
    "claim": (
        "**the timetable as point of no return (hold-out).** Once Russian general "
        'mobilization is ordered (30 July), the kernel for "no war between Germany and '
        'Russia" is left by every coalition that excludes Russia within two days, and the '
        "driving variable is the German plan's coupling of mobilization and war: with the "
        "coupling relaxed (an eastern-only deployment available, as it was not after 1913), "
        "the kernel is kept two days longer. The point of no return falls between 29 July "
        "(the partial mobilization decided and revoked) and 1 August (the German "
        "mobilization)"
    ),
    "expected": (
        "departure inside ticks 31 to 34 with the coupling named as the driving variable; the "
        "relaxation of the coupling moves it by at least two days"
    ),
    "sources": (
        "the Schlieffen-Moltke plan and the abandonment of the eastern deployment (Aufmarsch "
        "II Ost) in 1913; the Kaiser's attempt of 1 August to turn east and Moltke's refusal; "
        "Russian mobilization orders of 29 and 30 July"
    ),
}


def j2_departures(pair, cadence=True, relax=frozenset(), coalitions=COALITIONS_WITHOUT_RUS):
    """Departure along the realized path from tick 32, per coalition excluding RUS."""
    g = graph_from(pair, 32, cadence, relax)
    ids = path_ids(g, pair, 32, cadence, relax)
    out = {}
    for c in coalitions:
        kernel = viability(g, list(c), "no_war_GER_RUS").kernel
        out[c] = departure(ids, kernel, 32)
    return out, g, ids


def departure_from_tick0(pair, cadence=True):
    g = graph0(pair, cadence)
    states, _ = replay(pair, cadence)
    ids = [g.index[s] for s in states]
    kernel = viability(g, list(X), "no_war_GER_RUS").kernel
    return departure(ids, kernel, 0), [t for t, s in enumerate(ids) if s in kernel]


@pytest.mark.slow
def test_J2():
    timer = Timer()
    print("\n[J2] engine: explicit, graph from the realized state at tick 32")
    failures = []
    for pair in PAIRS:
        states, stop = replay(pair)
        if stop is not None and stop[0] <= 32:
            # the state at 32 exists, the realized move at 32 does not
            g = graph_from(pair, 32)
            kernel = viability(g, list(X), "no_war_GER_RUS").kernel
            s32 = g.index[states[32]]
            print(
                f"[J2] {label(pair)}: realized path stops at tick {stop[0]} "
                f"({stop[1]}.{stop[2]}); state at 32 in X's kernel: {s32 in kernel}"
            )
            continue
        deps, g, ids = j2_departures(pair)
        print(f"[J2] {label(pair)}: graph from tick 32: {g.size()} states")
        for c, d in deps.items():
            print(f"[J2]   C={{{', '.join(c)}}}: departure {d}")
        bad = {c: d for c, d in deps.items() if kept_as(d) > 34}
        if bad:
            failures.append(f"{label(pair)}: departures after tick 34: {bad}")
        dep_x = deps[X]
        # Russia (with Nature) forcing war from the departure state, in days
        if dep_x is not None:
            war = {
                s for s in range(g.size()) if not g.model.evaluate("no_war_GER_RUS", g.states[s])
            }
            rank = attractor(g, ["RUS", "Nature"], war).rank.get(ids[dep_x - 32])
            print(f"[J2]   X's departure state: RUS with Nature forces war within {rank} days")
        # (b) the coupling relaxed
        relaxed = frozenset({COUPLING})
        deps_r, g_r, _ = j2_departures(pair, relax=relaxed, coalitions=(X,))
        shift = kept_as(deps_r[X]) - kept_as(dep_x)
        print(
            f"[J2]   coupling relaxed: X's departure {deps_r[X]} (graph {g_r.size()} states); "
            f"shift {shift} days"
        )
        if shift < 2:
            failures.append(f"{label(pair)}: coupling shift {shift} < 2")
        # (c) which single relaxations restore X's kernel at the departure state
        restoring, ill_formed = [], []
        base = compiled(pair)
        if dep_x is not None:
            for a in base.assumptions():
                try:
                    g_a = graph_from(pair, 32, True, frozenset({a}))
                except ModelError as exc:
                    ill_formed.append((a, str(exc).splitlines()[0][:80]))
                    continue
                cm_a = compiled(pair, True, frozenset({a}))
                (s_dep,) = remap_states(base, cm_a, [states[dep_x]])
                k_a = viability(g_a, list(X), "no_war_GER_RUS").kernel
                if g_a.index[s_dep] in k_a:
                    restoring.append(a)
        print(f"[J2]   relaxations whose model is ill-formed from tick 32: {ill_formed}")
        print(f"[J2]   single relaxations restoring X's kernel at tick {dep_x}: {restoring}")
        if dep_x is not None and COUPLING not in restoring:
            failures.append(f"{label(pair)}: the coupling does not restore the kernel")
        # reported besides: sensitivity at tick 32, departure from tick 0
        rows = sensitivity(
            build(), "no_war_GER_RUS", list(X), adversary=["RUS", "Nature"], initial=[states[32]]
        )
        flips = [
            f"{r.variable} {r.from_level}->{r.to_level}" for r in rows if r.flips and not r.error
        ]
        print(f"[J2]   sensitivity at tick 32 (membership flips): {flips or 'none'}")
        d0, inside = departure_from_tick0(pair)
        print(
            f"[J2]   departure of X's kernel along the realized path from tick 0: {d0} "
            f"(realized states inside: ticks {inside[:1]}..{inside[-1:]})"
        )
    print(f"[J2] done ({timer})")
    assert not failures, "; ".join(failures)
    assert FIGHT
