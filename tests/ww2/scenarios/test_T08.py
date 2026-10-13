"""T8: Concessions reach `NO_GENERAL_WAR` or shrink V_WEST, depending on German aims.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest
import z3

from models.ww2.hypotheses import fixed_model, snapshot_state
from models.ww2.v0 import model
from wavefront import bmc
from wavefront.analysis import distance_table, viability
from wavefront.bmc.queries import _Query
from wavefront.engine import explore
from wavefront.model import V

CLAIM = {
    "id": "T8",
    "from_state": ("1936Q1"),
    "claim": (
        "(a) concessions reach `NO_GENERAL_WAR` under `aims[GER] = revisionist` "
        "and the tick-0 state is in V_WEST; (b) under `aims[GER] = hegemonic` "
        "with the Czech obligation in force, refusing the Sudeten demand leads to "
        "war within one tick and `czech_obligation` is the only minimal "
        "relaxation that lets a refusal stay at peace (the lever is measurable); "
        "the kernel comparison before and after the concession is evaluated from "
        "states that carry the pending rearmament, in phase 2"
    ),
    "expected": (
        "(a) as stated; (b) the load-bearing result in phase 1, the kernel "
        "comparison deferred to phase 2; this is the historical calibration of "
        "the AGI model's rights lever"
    ),
    "sources": ("Taylor 1961 against Weinberg 1994 and Kershaw; amended 2026-10-12"),
}

# Decisions D5: the first half (revisionist) is a consistency check of the hypothesis gates;
# the finding, if any, is the second half (what the Munich concession does to WEST's kernel
# under hegemonic aims). Methods: decisions D6 (the tick-0 state passes 3,000,000 states);
# the 1938 states fit the explicit engine and are computed exactly.


def test_T08_revisionist():
    """(a) Under revisionist aims, NO_GENERAL_WAR is reachable along a path that includes
    WEST's concede (bounded checker, k = 20, from the tick-0 state), and the tick-0 state is
    in V_WEST (sufficiency check: WEST fixed by the profile fight_on, no play to the horizon
    violates balance_europe)."""
    m = fixed_model(model, aims_GER="revisionist")
    cm = m.compile()
    assert cm.initial_states() == [snapshot_state(cm, "1935Q4", "revisionist")]
    # The claim is about a play in which WEST concedes, so the concession is part of the
    # query: a plain shortest trace to the target could just as well come from a limited
    # German attack under revisionist aims, and which witness z3 returns is not fixed.
    west = next(a for a in cm.actors if a.name == "WEST")
    concede = west.action_index("concede")
    query = _Query(cm, 20, V.ending("NO_GENERAL_WAR") & (V.sudeten == "german"))
    solver = query.solver()
    solver.add(z3.Or([query.enc.chosen[t][west.index] == concede for t in range(20)]))
    trace = query.shortest(solver, query.literals(frozenset()), [])
    assert trace is not None
    assert "concede" in [west.actions[mv[west.index]].name for mv in trace.moves]
    assert cm.ending_of(trace.states[-1]) == "NO_GENERAL_WAR"
    assert bmc.reach(m.compile(profile="fight_on"), 20, ~V.invariant("balance_europe")) is None


def kernel_entry(quarter, max_states=3_000_000):
    """WEST's kernel for balance_europe from the snapshot of ``quarter`` with its built-ins
    (pending decisions, last actions, the latch, fairness counters; phase 2 decision F2)
    under hegemonic aims: (reachable states, membership, shortest distance out)."""
    cm = model.compile()
    start = snapshot_state(cm, quarter, "hegemonic", builtins=True)
    g = explore(cm, initial=[start], max_states=max_states)
    kernel = viability(g, ["WEST"], "balance_europe").kernel
    s = g.initial[0]
    d = distance_table(g, [s], kernel, ["WEST"], None)[s]
    return g.size(), s in kernel, d.shortest


@pytest.mark.slow
@pytest.mark.skip(
    reason="phase 2 evaluation blocked by the explicit engine's budget: from the 1938Q2 file with "
    "its built-ins (GER rearmament pending 1 tick, last_GER demand_sudeten) the exploration passes "
    "3,000,000 states and, on the one retry the protocol allows, 5,000,000 states (343 s); the "
    "symbolic engine (phase 2 decision F1) is needed. The 1938Q3 half is computed below. See "
    "reports/ww2_v0.md section 14"
)
def test_T08_hegemonic():
    """(b) Under hegemonic aims, the Munich concession shrinks V_WEST: compare the state
    before it (1938Q2.json, start of 1938Q3, tick 10) with the state after it (1938Q3.json,
    tick 11), both with the built-ins of decision F2. Registered direction: membership lost,
    or (both inside) the shortest distance out of the kernel reduced. The phase 1 comparison
    without built-ins (before outside, after inside at distance 5) measured the rearmament
    clock; with the built-ins the before state carries the 1936 programme one tick from
    landing."""
    n_before, in_before, short_before = kernel_entry("1938Q2", max_states=5_000_000)
    n_after, in_after, short_after = kernel_entry("1938Q3")
    shrinks = (in_before and not in_after) or (
        in_before and in_after and short_after < short_before
    )
    assert shrinks


@pytest.mark.slow
def test_T08_hegemonic_after_concession_recorded():
    """The half of the amended T8(b) the explicit engine computes, recorded for section 14 of
    the report, not a verdict on the claim: from 1938Q3.json with its built-ins (no rearmament
    pending, last_GER demand_sudeten, last_WEST concede, belief_at_munich uncertain) the
    reachable set has 601,353 states and the state is in V_WEST for balance_europe with
    shortest distance 3 out of the kernel (phase 1, without built-ins: 198,443 states,
    inside, distance 5)."""
    assert kernel_entry("1938Q3") == (601_353, True, 3)


@pytest.mark.slow
@pytest.mark.parametrize("aims", ["revisionist", "hegemonic"])
def test_T08_czech_obligation_is_load_bearing(aims):
    """The rights lever bites only if a refused concession leads to war. A state in which
    the Sudetenland was taken by force (German, with no concession: commit_WEST still
    appease) and the West is still at peace a tick after the attack is unreachable to the
    horizon, and the only minimal relaxation that reaches it is the fairness constraint
    czech_obligation (decisions D4)."""
    cm = fixed_model(model, aims_GER=aims).compile()
    target = (
        (V.sudeten == "german")
        & (V.commit_WEST == "appease")
        & (V.war_west_ger == "peace")
        & (V.last_GER != "attack_czechoslovakia")
    )
    res = bmc.relax(cm, 20, target, max_relax=2)
    assert not res.reachable_as_is
    assert res.minimal_sets == [["czech_obligation"]]
