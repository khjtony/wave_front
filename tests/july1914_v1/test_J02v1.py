"""J2v1: registered 2026-10-24 in docs/july1914_testbed.md section 8.3 (the 1914 v1
registration, owner's decision 2h of 2026-10-23), before any v1 guard.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature, in the v1 content of section 8.2. Do not edit the claim text
without a changelog entry in that document. Skipped until ``models/july1914/v1.py`` exists
and the owner gives the go for the first sight by setting ``WF_FIRST_SIGHT_1914V1=1`` (the
skip condition was "v1.py exists" until the model step built it; changed then so that the
first sight is held, docs/july1914_v1_decisions.md V9). The body is the reading of
docs/july1914_v1_decisions.md section R (J2v1), written before that go.
"""

import os
from pathlib import Path

import pytest

from models.july1914.v1 import PRINCIPALS, build
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

V1 = Path(__file__).resolve().parents[2] / "models" / "july1914" / "v1.py"
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_1914V1") == "1"

CLAIM = {
    "id": "J2v1",
    "from_state": "tick 32 (30 July)",
    "claim": (
        "**the timetable as point of no return (hold-out), J2 as amended, re-asked on v1.** The "
        "point of no return is Russia's last exit, 30 July: the state of that day is the last on "
        'the realized path from which the peace between Germany and Russia ("no war between Germany'
        ' and Russia") can still be kept, and only with Russia. Once Russian general mobilization '
        "is ordered (30 July), the kernel for it is left by every coalition that excludes Russia "
        "within two days, and the driving variable is the German plan's coupling of mobilization "
        "and war: with the coupling relaxed (an eastern-only deployment available, as it was not "
        "after 1913), the kernel is kept two days longer. Recorded beside the result: the departure"
        " along the realized path from 28 June of the kernel of the coalitions that exclude Russia,"
        " predicted not before Vienna's decision of 19 July on the note (Tisza's consent of 14 July"
        " does not by itself take the peace out of their hands)"
    ),
    "expected": (
        "departure inside ticks 31 to 34 with the coupling named as the driving variable; the "
        "relaxation of the coupling moves it by at least two days; Russia's last exit at tick 32 "
        "(the last realized state in the kernel of all five principals); recorded: the departure "
        "from tick 0 at tick 22 or later under `aims_RUS = fight`"
    ),
    "sources": "J2's sources; Albertini vol. II; Clark 2012 ch. 9 (the Council of 19 July)",
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


def realized_ticks_inside(pair, coalition, cadence=True):
    """The ticks of the realized states (from tick 0) inside ``coalition``'s kernel for
    ``no_war_GER_RUS`` on the graph from tick 0, and the length of the realized prefix."""
    g = graph0(pair, cadence)
    states, _ = replay(pair, cadence)
    kernel = viability(g, list(coalition), "no_war_GER_RUS").kernel
    return [t for t, s in enumerate(states) if g.index[s] in kernel], len(states)


@pytest.mark.slow
@pytest.mark.skipif(
    not (V1.exists() and FIRST_SIGHT),
    reason="1914 v1 first sight held for the owner's go (WF_FIRST_SIGHT_1914V1=1)",
)
def test_J2v1():
    timer = Timer()
    print("\n[J2v1] engine: explicit, graph from the realized state at tick 32")
    failures = []
    for pair in PAIRS:
        states, stop = replay(pair)
        if stop is not None and stop[0] <= 32:
            # the state at 32 exists, the realized move at 32 does not
            g = graph_from(pair, 32)
            kernel = viability(g, list(X), "no_war_GER_RUS").kernel
            s32 = g.index[states[32]]
            print(
                f"[J2v1] {label(pair)}: realized path stops at tick {stop[0]} "
                f"({stop[1]}.{stop[2]}); state at 32 in X's kernel: {s32 in kernel}"
            )
            all_in, n = realized_ticks_inside(pair, PRINCIPALS)
            print(
                f"[J2v1]   kernel of all five principals from tick 0: realized states inside "
                f"{len(all_in)} of ticks 0..{n - 1}, last {all_in[-1] if all_in else None}"
            )
            continue
        deps, g, ids = j2_departures(pair)
        print(f"[J2v1] {label(pair)}: graph from tick 32: {g.size()} states")
        for c, d in deps.items():
            print(f"[J2v1]   C={{{', '.join(c)}}}: departure {d}")
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
            print(f"[J2v1]   X's departure state: RUS with Nature forces war within {rank} days")
        # (b) the coupling relaxed
        relaxed = frozenset({COUPLING})
        deps_r, g_r, _ = j2_departures(pair, relax=relaxed, coalitions=(X,))
        shift = kept_as(deps_r[X]) - kept_as(dep_x)
        print(
            f"[J2v1]   coupling relaxed: X's departure {deps_r[X]} (graph {g_r.size()} states); "
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
        print(f"[J2v1]   relaxations whose model is ill-formed from tick 32: {ill_formed}")
        print(f"[J2v1]   single relaxations restoring X's kernel at tick {dep_x}: {restoring}")
        if dep_x is not None and COUPLING not in restoring:
            failures.append(f"{label(pair)}: the coupling does not restore the kernel")
        # reported besides: sensitivity at tick 32, departure from tick 0
        rows = sensitivity(
            build(), "no_war_GER_RUS", list(X), adversary=["RUS", "Nature"], initial=[states[32]]
        )
        flips = [
            f"{r.variable} {r.from_level}->{r.to_level}" for r in rows if r.flips and not r.error
        ]
        print(f"[J2v1]   sensitivity at tick 32 (membership flips): {flips or 'none'}")
        d0, inside = departure_from_tick0(pair)
        print(
            f"[J2v1]   departure of X's kernel along the realized path from tick 0: {d0} "
            f"(realized states inside: ticks {inside[:1]}..{inside[-1:]})"
        )
        # (e) recorded beside the result, registered as "22 or later"
        if kept_as(d0) < 22:
            failures.append(f"{label(pair)}: departure from tick 0 {d0}, before 22")
        # (d) Russia's last exit (amended 2026-10-23)
        all_in, n = realized_ticks_inside(pair, PRINCIPALS)
        rus_in, _ = realized_ticks_inside(pair, ("RUS",))
        last_exit = all_in[-1] if all_in else None
        print(
            f"[J2v1]   Russia's last exit: last realized state in the kernel of all five "
            f"principals at tick {last_exit} (inside: {len(all_in)} of ticks 0..{n - 1}); "
            f"{{RUS}} alone: last inside at tick {rus_in[-1] if rus_in else None}"
        )
        if all_in != list(range(33)):
            failures.append(f"{label(pair)}: Russia's last exit at {last_exit}, not 32")
    print(f"[J2v1] done ({timer})")
    assert not failures, "; ".join(failures)
    assert FIGHT
