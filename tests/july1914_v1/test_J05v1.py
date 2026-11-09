"""J5v1: registered 2026-10-24 in docs/july1914_testbed.md section 8.3 (the 1914 v1
registration, owner's decision 2h of 2026-10-23), before any v1 guard.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature, in the v1 content of section 8.2. Do not edit the claim text
without a changelog entry in that document. Skipped until ``models/july1914/v1.py`` exists
and the owner gives the go for the first sight by setting ``WF_FIRST_SIGHT_1914V1=1`` (the
skip condition was "v1.py exists" until the model step built it; changed then so that the
first sight is held, docs/july1914_v1_decisions.md V9). The body is the reading of
docs/july1914_v1_decisions.md section R (J5v1), written before that go.
"""

import os
from pathlib import Path

import pytest

from models.ww2 import bounded
from wavefront.engine import attractor, explore
from wavefront.model import V

from .common import FIGHT, Timer, compiled, label, minimal_relaxation_sets, replay

V1 = Path(__file__).resolve().parents[2] / "models" / "july1914" / "v1.py"
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_1914V1") == "1"

CLAIM = {
    "id": "J5v1",
    "from_state": "tick 35 (2 August)",
    "claim": (
        "**the Belgian route as the British trigger (hold-out), J5 re-asked on v1.** From the state"
        " of 2 August, British entry into the war is forced by the German ultimatum to Belgium: "
        "with Belgium `demanded`, GBR's war declaration becomes available and the Cabinet's "
        "commitment reaches `war` within two days whatever Germany does; without the Belgian "
        "ultimatum (a German choice the plan made unavoidable only through the coupling of J2v1), "
        "British entry by 4 August needs at least one relaxation, and every minimal set relaxes "
        "either the Belgian route or the naval assurance of 2 August"
    ),
    "expected": "as stated",
    "sources": "J5's sources",
}


BELGIAN_ROUTE = (
    "GBR.ultimatum_GER:belgian_route",
    "GER.ultimatum_belgium:",
    "Nature.invade_belgium:",
)
NAVAL = ("GBR.naval_assurance:",)


def touches(relaxation, prefixes):
    return any(any(a == p or a.startswith(p) for p in prefixes) for a in relaxation)


@pytest.mark.slow
@pytest.mark.skipif(
    not (V1.exists() and FIRST_SIGHT),
    reason="1914 v1 first sight held for the owner's go (WF_FIRST_SIGHT_1914V1=1)",
)
def test_J5v1():
    timer = Timer()
    print("\n[J5v1] engines: explicit for (a) and (b); bounded checker from the state for (c)")
    failures = []
    war = V.commitment_GBR == "war"
    for pair in FIGHT:
        cm = compiled(pair)
        states, _ = replay(pair)
        s35 = list(states[35])
        s35[cm.index["belgium"]] = cm.variables[cm.index["belgium"]].levels.index("demanded")
        start = tuple(s35)
        g = explore(cm, initial=[start])
        (s0,) = g.initial
        gbr = next(a for a in cm.actors if a.name == "GBR")
        j = gbr.action_index("ultimatum_GER")
        avail_ticks = [
            g.states[i][cm.index["tick"]]
            for i in range(g.size())
            if not g.terminal[i] and j in g.avail[i][gbr.index]
        ]
        first = min(avail_ticks) if avail_ticks else None
        target = g.states_where(war)
        by_gbr = attractor(g, ["GBR"], target)
        by_none = attractor(g, [], target)
        rank = by_gbr.rank.get(s0)
        print(
            f"[J5v1] {label(pair)}: from tick 35 with Belgium demanded ({g.size()} states): "
            f"ultimatum_GER first available at tick {first}; GBR forces war within {rank} days; "
            f"inevitable (coalition {{}}): {s0 in by_none.win}"
        )
        if first is None or first > 36:
            failures.append(f"{label(pair)}: ultimatum_GER not available by 36 ({first})")
        if rank is None or rank > 2:
            failures.append(f"{label(pair)}: GBR forces war in {rank} days, not within 2")
        # (c) without the Belgian ultimatum, from the realized state at 35
        never = lambda enc: bounded.never(enc, "GER", "ultimatum_belgium")  # noqa: E731
        avoid_play = bounded.exists_from(
            cm, states[35], 3, lambda enc: enc.active[3], constrain=never
        )
        print(
            f"[J5v1]   a play to tick 38 without the Belgian note, nothing relaxed: "
            f"{'yes' if avoid_play else 'none (the western_timetable forces it)'}"
        )
        sets = minimal_relaxation_sets(cm, states[35], 3, war, max_size=3, constrain=never)
        print(f"[J5v1]   minimal relaxation sets for war by 4 Aug without the note: {sets}")
        if sets and sets[0]:
            trace = bounded.reach_from(cm, states[35], 3, war, relax=sets[0], constrain=never)
            print(trace.render(cm) if trace else "(no trace)")
        if sets == [[]]:
            failures.append(f"{label(pair)}: British entry reachable as is without the note")
        for s in sets:
            if s and not (touches(s, BELGIAN_ROUTE) or touches(s, NAVAL)):
                failures.append(f"{label(pair)}: minimal set {s} relaxes neither route")
        if not sets:
            failures.append(f"{label(pair)}: no relaxation set up to size 3")
    print(f"[J5v1] done ({timer})")
    assert not failures, "; ".join(failures)
