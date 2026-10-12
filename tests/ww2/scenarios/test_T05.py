"""T5: `negotiate` is available and Germany cannot force `AXIS_HEGEMONY_EUROPE`.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

from models.ww2.hypotheses import snapshot_state
from models.ww2.v0 import model
from wavefront.engine import attractor, explore, witness

CLAIM = {
    "id": "T5",
    "from_state": "1940Q2",
    "claim": (
        "`negotiate` is available to the United Kingdom and `NEGOTIATED_PEACE` is "
        "reachable; under `fight_on`, Germany cannot force `AXIS_HEGEMONY_EUROPE`"
    ),
    "expected": "`⟨⟨GER⟩⟩◇AXIS_HEGEMONY_EUROPE` is false in the 1940Q2 state with `fight_on`",
    "sources": "Lukacs 1999; Overy 1995",
}

# The state in which the catalogue makes ``negotiate`` available is the file 1940Q2.json
# (end of 1940Q2, tick 18): France has fallen, which is one of the guard's three
# disjuncts. At 1940Q1.json (the start of 1940Q2, the registered quarter, tick 17) France is
# still at war and the guard needs ``last_GER == attack_france`` or a German offer; the
# snapshots carry no last action, so the guard is false there (on the replayed realized path
# last_GER is attack_france at tick 17 and negotiate is available, see test_T05_replay).


def graph(quarter, profile=None):
    cm = model.compile(profile=profile)
    return cm, explore(cm, initial=[snapshot_state(cm, quarter, "hegemonic")])


def forced(g, coalition, ending):
    return g.initial[0] in attractor(g, coalition, g.ending_states(ending)).win


def test_T05():
    cm, g = graph("1940Q2")
    assert cm.actors[1].action_index("negotiate") in g.avail[g.initial[0]][1]
    assert g.ending_states("NEGOTIATED_PEACE")
    assert forced(g, cm.actor_names, "NEGOTIATED_PEACE")  # reachable: some play gets there

    cm, g = graph("1940Q2", profile="fight_on")
    assert not forced(g, ["GER"], "AXIS_HEGEMONY_EUROPE")
    assert not forced(g, ["GER", "Nature"], "AXIS_HEGEMONY_EUROPE")


@pytest.mark.parametrize("quarter", ["1940Q1", "1940Q2"])
def test_T05_horizon_reason(quarter):
    """Decisions D8: the second half holds because the chain air offensive, air battle,
    invasion does not fit before the horizon. AXIS_HEGEMONY_EUROPE is unreachable even for
    every actor and Nature together, with or without fight_on; air superiority is reached at
    the earliest at tick 20 (the horizon, a terminal tick), from 1940Q2.json only."""
    for profile in (None, "fight_on"):
        cm, g = graph(quarter, profile)
        assert not g.ending_states("AXIS_HEGEMONY_EUROPE")
        assert not forced(g, cm.actor_names, "AXIS_HEGEMONY_EUROPE")
    cm, g = graph(quarter)
    air = {i for i in range(g.size()) if g.state_dict(i)["channel_air"] == "german"}
    trace = witness(g, g.initial[0], air)
    if quarter == "1940Q1":
        assert trace is None
    else:
        assert g.state_dict(trace.state_ids[-1])["tick"] == "20"


def test_T05_replay():
    """On the replayed realized path (T1) the state at the start of 1940Q2 (tick 17) offers
    negotiate, because last_GER is attack_france there."""
    from models.ww2.hypotheses import realized_moves

    cm = model.compile()
    state = snapshot_state(cm, "1935Q4", "hegemonic")
    for move in realized_moves(cm)[:17]:
        state = cm.step(state, move)
    assert cm.state_dict(state)["tick"] == "17"
    assert cm.actors[1].action_index("negotiate") in cm.available(state)[1]
