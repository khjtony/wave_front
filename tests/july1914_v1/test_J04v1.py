"""J4v1: registered 2026-10-24 in docs/july1914_testbed.md section 8.3 (the 1914 v1
registration, owner's decision 2h of 2026-10-23), before any v1 guard.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature, in the v1 content of section 8.2. Do not edit the claim text
without a changelog entry in that document. Skipped until ``models/july1914/v1.py`` exists
and the owner gives the go for the first sight by setting ``WF_FIRST_SIGHT_1914V1=1`` (the
skip condition was "v1.py exists" until the model step built it; changed then so that the
first sight is held, docs/july1914_v1_decisions.md V9). The body is the reading of
docs/july1914_v1_decisions.md section R (J4v1), written before that go.
"""

import itertools
import os
from pathlib import Path

import pytest

from wavefront.analysis import viability
from wavefront.engine import explore

from .common import (
    FIGHT,
    PAIRS,
    Timer,
    X,
    compiled,
    departure,
    graph_from,
    label,
    path_ids,
    replay,
)
from .test_J02v1 import departure_from_tick0

V1 = Path(__file__).resolve().parents[2] / "models" / "july1914" / "v1.py"
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_1914V1") == "1"

CLAIM = {
    "id": "J4v1",
    "from_state": "tick 31 (29 July)",
    "claim": (
        "**belief lag under a fast adversary (hold-out), J4 as amended, re-asked on v1.** Berlin's "
        "reading of Britain flips to `fights` on Lichnowsky's telegram of 29 July, and Bethmann's "
        "attempt to restrain Vienna that night is in the decision space; but by the cadence of the "
        "Austro-Hungarian decisions and the Russian general mobilization of the next day, the "
        "restraint cannot land before the mobilization orders: the belief change precedes the "
        "response by an institutional lag of at least one day, and the point of no return (J2v1) "
        "precedes the belief change"
    ),
    "expected": (
        "the restraint action available at tick 31 with its effect visible at tick 33 or later; the"
        " kernel already left at tick 31, before the belief change is visible"
    ),
    "sources": "J4's sources; amended 2026-10-23; re-asked on v1 2026-10-24",
}


def earliest_acceptance(pair, cadence=True):
    """E: the earliest tick with the Halt accepted over the plays from the realized state at
    31 in which GER plays restrain_vienna at 31 (None if no such play reaches it)."""
    cm = compiled(pair, cadence)
    states, _ = replay(pair, cadence)
    s31 = states[31]
    ger = next(a for a in cm.actors if a.name == "GER")
    j = ger.action_index("restrain_vienna")
    avail = cm.available(s31)
    if j not in avail[ger.index]:
        return None, False
    succ = set()
    for move in itertools.product(*avail):
        if move[ger.index] == j:
            succ.add(cm.step(s31, move))
    g = explore(cm, initial=sorted(succ), max_states=2_000_000)
    ticks = [
        s[cm.index["tick"]] for s in g.states if cm.state_dict(s)["halt_in_belgrade"] == "accepted"
    ]
    return (min(ticks) if ticks else None), True


@pytest.mark.slow
@pytest.mark.skipif(
    not (V1.exists() and FIRST_SIGHT),
    reason="1914 v1 first sight held for the owner's go (WF_FIRST_SIGHT_1914V1=1)",
)
def test_J4v1():
    timer = Timer()
    print("\n[J4v1] engine: explicit, from the realized state at tick 31")
    failures = []
    for pair in PAIRS:
        cm = compiled(pair)
        states, stop = replay(pair)
        flip = cm.state_dict(states[32])["belief_GER_GBR"]
        before = cm.state_dict(states[31])["belief_GER_GBR"]
        e, available = earliest_acceptance(pair)
        g = graph_from(pair, 31)
        ids = path_ids(g, pair, 31)
        kernel = viability(g, list(X), "no_war_GER_RUS").kernel
        dep = departure(ids, kernel, 31)
        last = 31 + len(ids) - 1
        print(
            f"[J4v1] {label(pair)}: restrain_vienna available at 31: {available}; belief at 31 "
            f"{before}, at 32 {flip}; earliest Halt accepted E = {E_str(e)} (lag after the "
            f"visible belief {lag(e)}); X's kernel left at {dep} (realized path to tick {last}"
            f"{'' if stop is None else f', stops at {stop[0]}'})"
        )
        if not available:
            failures.append(f"{label(pair)}: restrain_vienna unavailable at 31")
        if flip != "fights" or before == "fights":
            failures.append(f"{label(pair)}: no belief flip on 29 July")
        if e is not None and e < 33:
            failures.append(f"{label(pair)}: restraint lands at {e} < 33")
        d0, _ = departure_from_tick0(pair)
        print(
            f"[J4v1]   (d) amended: X's kernel along the realized path from tick 0 left at {d0}; "
            f"registered 2026-10-15 (kernel left at 32 or 33): {dep in (32, 33)}"
        )
        if pair in FIGHT:
            if dep != 31:
                failures.append(f"{label(pair)}: the state at 31 is inside X's kernel ({dep})")
            if d0 is None or d0 > 31:
                failures.append(f"{label(pair)}: from tick 0 the kernel is left at {d0}, not <= 31")
    print(f"[J4v1] done ({timer})")
    assert not failures, "; ".join(failures)


def E_str(e):
    return "never" if e is None else str(e)


def lag(e):
    return "none (never lands)" if e is None else f"{e - 32} days"
