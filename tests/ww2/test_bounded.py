"""The bounded helpers of models/ww2/bounded.py against the explicit engine, on WW2 v0 states
small enough to explore whole (no registered claim is evaluated here)."""

import pytest

from models.ww2 import bounded
from models.ww2.hypotheses import snapshot_state
from models.ww2.v0 import model
from wavefront.engine import attractor, explore, safe, witness
from wavefront.model import V

CM = model.compile()


@pytest.fixture(scope="module")
def late():
    """The 1940Q1 file (tick 17) with its built-ins, hegemonic: a few hundred states."""
    s = snapshot_state(CM, "1940Q1", "hegemonic", builtins=True)
    return s, explore(CM, initial=[s])


def test_reach_from_matches_the_explicit_shortest_witness(late):
    s, g = late
    for target in ("NEGOTIATED_PEACE", "BRITAIN_ALONE", V.channel_air == "german"):
        trace = bounded.reach_from(CM, s, 3, target)
        goal = (
            g.ending_states(target)
            if isinstance(target, str)
            else {i for i, x in enumerate(g.states) if CM.evaluate(target, x)}
        )
        w = witness(g, g.initial[0], goal)
        assert (trace is None) == (w is None), target
        if trace is not None:
            assert len(trace) == len(w.joint_moves)
            assert bounded.replay(CM, s, trace.moves)[-1] == trace.states[-1]


def test_fixed_strategies_are_sound_against_the_exact_fixpoints(late):
    """A result of ``forces`` or ``blocks`` never contradicts the exact attractor or kernel:
    a coalition shown to force a target by a fixed strategy is in the attractor, and the
    rest shown to block it is outside."""
    s, g = late
    for target, coalition, strategy, rest in [
        (
            "NEGOTIATED_PEACE",
            ["WEST"],
            {"WEST": ["negotiate"]},
            {"GER": [], "USSR": [], "JPN": [], "Nature": []},
        ),
        (
            V.channel_air == "german",
            ["GER", "Nature"],
            {"GER": ["air_offensive"], "Nature": ["campaign_west", "air_battle_german"]},
            {"WEST": ["negotiate"], "USSR": [], "JPN": []},
        ),
    ]:
        goal = (
            g.ending_states(target)
            if isinstance(target, str)
            else {i for i, x in enumerate(g.states) if CM.evaluate(target, x)}
        )
        exact = g.initial[0] in attractor(g, coalition, goal).win
        forced, _ = bounded.forces(CM, s, target, strategy)
        if forced:
            assert exact, target
        blocked, _ = bounded.blocks(CM, s, target, rest)
        if blocked:
            assert not exact, target
        assert forced or blocked  # each pair decides these two questions
        everyone = [a.name for a in CM.actors]
        complement = set(range(len(g.states))) - goal
        rest = [n for n in everyone if n not in coalition]
        assert (g.initial[0] in safe(g, rest, complement).kernel) == blocked


def test_play_is_total_under_a_fairness_restriction():
    """In the 1939Q1 file the democratic response may restrict WEST to its responses; a
    strategy listing none of them still has a move (the fallback order)."""
    s = snapshot_state(CM, "1939Q1", "hegemonic", builtins=True)
    trace = bounded.reach_from(
        CM, s, 4, V.tick == 17, constrain=bounded.strategies({"WEST": ["approach_ussr"]})
    )
    assert trace is not None


def test_wellformed_from_finds_nothing_on_v0_late_states():
    s = snapshot_state(CM, "1939Q3", "hegemonic", builtins=True)
    assert bounded.wellformed_from(CM, s) == []


def test_exists_from_and_fix():
    s = snapshot_state(CM, "1940Q1", "hegemonic", builtins=True)
    west = next(a for a in CM.actors if a.name == "WEST")
    trace = bounded.exists_from(
        CM,
        s,
        2,
        lambda enc: enc.state[2][CM.index["britain"]] == 2,
        constrain=lambda enc: bounded.fix(enc, 1, "WEST", "negotiate"),
    )
    assert trace is not None and trace.moves[1][west.index] == west.action_index("negotiate")
    none = bounded.exists_from(
        CM, s, 1, lambda enc: enc.state[1][CM.index["britain"]] == 3
    )  # invaded in one quarter: impossible
    assert none is None
