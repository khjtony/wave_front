"""K6: registered 2026-10-15 in docs/crisis_1939_testbed.md section 3.

The summer-1939 crisis sub-game of WW2 v1 (3-day ticks, 5 July to 3 September 1939), entered
from the 1939Q3 state. Do not edit the claim text without a changelog entry in that
document.

Reading (docs/crisis_1939_decisions.md R6). Reduced build.

- (a) From every realized state at ticks 0 to 14, ``german_approach == pact`` and
  ``alliance`` are each reachable (the attractor of every actor, Nature included) under
  ``documented_only``; ticks 15 and 16 printed.
- (b) Under ``no_german_proposal`` from the entry state (``aims_USSR == defensive``), the
  pact is unreachable and ``accept_pact`` is available in no reachable state; the minimal
  relaxation sets for the pact (``relax_explicit``, max_size 2) each name the German
  proposal (``no_german_proposal`` or ``USSR.accept_pact:proposal``), and so does the
  minimal assumption set (the minimal hitting set of the minimal relaxation sets).

Engine: the explicit engine (``attractor``, ``relax_explicit``).
"""

import time

import pytest

from models.ww2.crises import summer_1939 as crisis
from tests.ww2.crisis_1939 import common
from wavefront.analysis import relax_explicit
from wavefront.engine import attractor, explore
from wavefront.model import V

CLAIM = {
    "id": "K6",
    "from_state": "tick 0",
    "claim": (
        "the Soviet choice is open to both sides until 19 August: from every state up to tick "
        "14 both the pact and the alliance are reachable; under `aims_USSR = defensive` the "
        "pact needs Germany's proposal of a protocol (the German approach at "
        "`pact_proposed`), and without it the Soviet acceptance is unavailable"
    ),
    "expected": (
        "both targets reachable to tick 14; the pact's minimal assumption set names the "
        "German proposal"
    ),
    "sources": "Molotov to Schulenburg, 17 and 19 August; Stalin's reply, 21 August",
}

GERMAN_PROPOSAL = {"no_german_proposal", "USSR.accept_pact:proposal"}


def test_K6a_both_targets_reachable_to_tick_14(capsys):
    t0 = time.time()
    cm = common.compiled(inert=False, profile="documented_only")
    path = common.realized_states(cm)
    g = common.graph(cm, [common.entry(cm)])
    everyone = [a.name for a in cm.actors]
    pact = attractor(g, everyone, g.states_where(common.PACT)).win
    alliance = attractor(g, everyone, g.states_where(V.alliance)).win
    rows = [
        (t, common.sid(g, path[t]) in pact, common.sid(g, path[t]) in alliance) for t in range(17)
    ]
    with capsys.disabled():
        print(
            f"\nK6 reachability along the realized path (explicit engine, {g.size()} states, "
            f"{time.time() - t0:.1f} s): (tick, pact, alliance) {rows}"
        )
    assert all(p and a for t, p, a in rows if t <= 14)


@pytest.mark.slow
def test_K6b_the_pact_needs_the_german_proposal(capsys):
    t0 = time.time()
    cm = common.compiled(inert=False, profile="no_german_proposal")
    start = common.entry(cm)
    assert cm.state_dict(start)["aims_USSR"] == "defensive"
    g = explore(cm, initial=[start])
    assert not g.states_where(common.PACT)
    usr = [a.name for a in cm.actors].index("USSR")
    accept = cm.actors[usr].action_index("accept_pact")
    assert all(accept not in av[usr] for i, av in enumerate(g.avail) if not g.terminal[i])

    model = crisis.build(inert=False, target=("PACT", common.PACT))
    s0 = crisis.entry_state(model.compile(profile="no_german_proposal"), common.COARSE_Q2)
    sets = relax_explicit(model, "PACT", max_size=2, profile="no_german_proposal", initial=[s0])
    hitting = common.minimal_hitting_sets(sets)
    with capsys.disabled():
        print(
            f"\nK6 relax_explicit under no_german_proposal (explicit engine, "
            f"{time.time() - t0:.1f} s): minimal sets {list(sets)}; minimal assumption sets "
            f"(hitting sets) {[sorted(h) for h in hitting]}; ill-formed {len(sets.ill_formed)}; "
            f"undecided {len(sets.undecided)}"
        )
    assert sets and [] not in sets and not sets.undecided
    assert all(set(s) & GERMAN_PROPOSAL for s in sets)
    assert hitting and all(h & GERMAN_PROPOSAL for h in hitting)
