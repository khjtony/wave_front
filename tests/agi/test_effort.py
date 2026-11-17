"""tests/agi/effort.py: the least-effort search against brute force on a model read by hand,
and the score tables against the actions of models/agi/v0.py. Construction checks: no effort
of the AGI model is computed here."""

import itertools

import pytest

from models.agi import v0
from tests.agi.effort import (
    A_SCORES,
    ALARM,
    BELOW_AGI,
    H_SCORES,
    L_SCORES,
    OUTCOME,
    effort,
    least_effort,
    shifted,
)
from wavefront.model import Model, Set, V

CM = v0.model.compile()


def errand() -> Model:
    """``P`` reaches ``done`` by a dear direct step or by two cheap ones; ``Q`` can spoil the
    cheap road once, and an alarm (``opinion`` in backlash) changes what waiting costs."""
    m = Model("errand", horizon=4)
    m.var("at", ["home", "half", "done"], init="home")
    m.var("a_known", ["unknown", "suspected"], init="unknown")
    m.var("opinion", ["mixed", "backlash"], init="mixed")
    p = m.actor("P")
    p.action("leap", guard=V.at == "home", effect=[Set("at", "done")], source="test")
    p.action("walk", guard=V.at != "done", effect=[Set("at", V.at + 1)], source="test")
    q = m.actor("Q")
    q.action("shout", guard=V.opinion == "mixed", effect=[Set("opinion", "backlash")], source="t")
    return m


SCORES = {"P": {"idle": (ALARM, 5, 0), "leap": 4, "walk": 1}, "Q": {"idle": 0, "shout": 2}}


def brute(cm, k, target, scores):
    best = None
    frontier = [(s, 0) for s in cm.initial_states()]
    for _ in range(k + 1):
        nxt = []
        for state, cost in frontier:
            if cm.evaluate(target, state):
                best = cost if best is None else min(best, cost)
                continue
            if cm.is_terminal(state):
                continue
            for move in itertools.product(*cm.available(state)):
                nxt.append((cm.step(state, move), cost + effort(cm, [state], [move], scores)))
        frontier = nxt
    return best


@pytest.mark.parametrize("who", [("P",), ("Q",), ("P", "Q")])
@pytest.mark.parametrize("k", [1, 2, 3])
def test_least_effort_equals_brute_force(who, k):
    cm = errand().compile()
    scores = {name: SCORES[name] for name in who}
    target = V.at == "done"
    found = least_effort(cm, k, target, scores)
    assert found is not None
    cost, states, moves = found
    assert cost == brute(cm, k, target, scores)
    assert cm.evaluate(target, states[-1]) and len(moves) == len(states) - 1


def test_the_cheap_road_and_the_alarm_price():
    cm = errand().compile()
    assert least_effort(cm, 1, V.at == "done", {"P": SCORES["P"]})[0] == 4  # the leap
    assert least_effort(cm, 2, V.at == "done", {"P": SCORES["P"]})[0] == 2  # two walks
    assert least_effort(cm, 0, V.at == "done", SCORES) is None
    # waiting a quarter under alarm costs P five: found only when the target needs the wait
    late = (V.at == "done") & (V.tick == 3)
    assert least_effort(cm, 3, late, {"P": SCORES["P"]})[0] == 2


def test_every_scored_action_is_an_action_of_v0_and_none_is_left_out():
    def names(actor):
        return {x.name for x in CM.actors[CM.actor_names.index(actor)].actions}

    assert set(H_SCORES) == names("H")
    assert set(L_SCORES) == names("L")
    for objective, table in A_SCORES.items():
        assert objective in v0.OBJECTIVES and set(table) <= names("A")
    assert set(A_SCORES) == set(v0.OBJECTIVES)
    endings = set(v0.model.endings) | {"OVERT_TAKEOVER"}
    for who, row in OUTCOME.items():
        assert set(row) == endings, who


def test_waiting_below_agi_is_free_and_a_shift_moves_every_state():
    for objective in ("truth_seeking", "indifferent"):
        assert A_SCORES[objective]["stand_by"] == (BELOW_AGI, 0, 2)
    assert shifted(2, -1) == 1 and shifted(0, -1) == 0
    assert shifted((ALARM, 0, 1), 1) == (ALARM, 1, 2)
    assert shifted((ALARM, 0, 1), -1) == (ALARM, 0, 0)
