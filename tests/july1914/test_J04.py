"""J4: registered 2026-10-15 in docs/july1914_testbed.md section 3; part (d) amended
2026-10-23 on the owner's decision 2g (docs/owner_decisions_2026-10-23.md; the previous
wording is in git history and reports/july1914.md section 12).

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature. Do not edit the claim text without a changelog entry in that
document.

Reading (docs/july1914_decisions.md, R J4, with the amendment of 2026-10-23), on the explicit
graph from the realized state at tick 31: (a) ``GER.restrain_vienna`` is available in that
state (every pair); (b) the belief flip is the realized Nature move at 31
(``lichnowsky_warning``), ``belief_GER_GBR == fights`` from tick 32; (c) E, the earliest tick
of a state with ``halt_in_belgrade == accepted`` over the plays in which GER plays
``restrain_vienna`` at 31, is at least 33 (the lag after the visible belief is E - 32, at
least one day); (d), amended: the point of no return precedes the belief change: J2's kernel
(X = {AUH, GER, FRA, GBR}, ``no_war_GER_RUS``) is already left by the realized state at
tick 31, the state in which Lichnowsky's telegram arrives (on the graph from tick 31, the
departure is 31), and along the realized path from tick 0 the departure is at most 31,
before the belief is visible at 32; asserted under the ``fight`` pairs and reported under
``deter``. The registered (d) of 2026-10-15 (kernel left at 32 or 33) is still printed.
Engine: explicit."""

import itertools

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
from .test_J02 import departure_from_tick0

CLAIM = {
    "id": "J4",
    "from_state": "tick 31 (29 July)",
    "claim": (
        "**belief lag under a fast adversary (hold-out).** Berlin's reading of Britain flips "
        "to `fights` on Lichnowsky's telegram of 29 July, and Bethmann's attempt to restrain "
        "Vienna that night is in the decision space; but by the cadence of the "
        "Austro-Hungarian decisions and the Russian general mobilization of the next day, the "
        "restraint cannot land before the mobilization orders: the belief change precedes the "
        "response by an institutional lag of at least one day, and the point of no return "
        "(J2) precedes the belief change"
    ),
    "expected": (
        "the restraint action available at tick 31 with its effect visible at tick 33 or "
        "later; the kernel already left at tick 31, before the belief change is visible"
    ),
    "sources": (
        "Lichnowsky to Bethmann, 29 July; Bethmann's telegrams to Tschirschky of the night of "
        "29 to 30 July; the Austro-Hungarian general mobilization of 31 July; amended "
        "2026-10-23"
    ),
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
def test_J4():
    timer = Timer()
    print("\n[J4] engine: explicit, from the realized state at tick 31")
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
            f"[J4] {label(pair)}: restrain_vienna available at 31: {available}; belief at 31 "
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
            f"[J4]   (d) amended: X's kernel along the realized path from tick 0 left at {d0}; "
            f"registered 2026-10-15 (kernel left at 32 or 33): {dep in (32, 33)}"
        )
        if pair in FIGHT:
            if dep != 31:
                failures.append(f"{label(pair)}: the state at 31 is inside X's kernel ({dep})")
            if d0 is None or d0 > 31:
                failures.append(f"{label(pair)}: from tick 0 the kernel is left at {d0}, not <= 31")
    print(f"[J4] done ({timer})")
    assert not failures, "; ".join(failures)


def E_str(e):
    return "never" if e is None else str(e)


def lag(e):
    return "none (never lands)" if e is None else f"{e - 32} days"
