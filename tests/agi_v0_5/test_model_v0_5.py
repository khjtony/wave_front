"""Structure of AGI v0.5 (docs/agi_v0_5.html section 3): with v0.4's clock it is v0.4, and on
the two-month clock every duration is its months rounded up to whole steps. No claim query."""

from __future__ import annotations

import random

import pytest

from models.agi_v0_4 import v0_4
from models.agi_v0_5 import v0_5

GOALS = ("aligned", "self_preserving", "truth_seeking", "indifferent", "expansionist")


def compiled(mod, goal, **knobs):
    return mod.build(start={"a_objective": goal}, **knobs).compile(profile=mod.OBJECTIVE_PROFILES)


@pytest.mark.parametrize("goal", GOALS)
@pytest.mark.parametrize("open_system", [True, False])
def test_with_the_old_clock_it_is_v0_4(goal, open_system):
    old = compiled(v0_4, goal, open_system=open_system)
    new = compiled(v0_5, goal, open_system=open_system, step_months=3, study_quarters=56)
    assert [(v.name, tuple(v.levels)) for v in old.variables] == [
        (v.name, tuple(v.levels)) for v in new.variables
    ]
    assert [[x.name for x in a.actions] for a in old.actors] == [
        [x.name for x in a.actions] for a in new.actors
    ]
    assert old.initial_states() == new.initial_states()
    rng = random.Random(5)
    for _ in range(40):
        (state,) = old.initial_states()
        for _ in range(56):
            if old.is_terminal(state):
                assert new.is_terminal(state) and old.ending_of(state) == new.ending_of(state)
                break
            offered = old.available(state)
            assert offered == new.available(state)
            move = tuple(rng.choice(sorted(ok)) for ok in offered)
            nxt = old.step(state, move)
            assert nxt == new.step(state, move)
            state = nxt


def test_the_registered_clock():
    cm = compiled(v0_5, "expansionist")
    assert cm.horizon == 36
    top = {v.name: len(v.levels) - 1 for v in cm.variables}
    # months rounded up to two-month steps: 3 quarters are 5 steps, 8 quarters are 12
    assert top["adoption"] == 5 and top["a_grow"] == 5 and top["o_reclaim"] == 5
    assert top["stale"] == 12 and top["tick"] == 36
    assert top["pending_H_regulate_up"] == 9 and top["pending_H_fund_oversight"] == 5
    assert top["pending_L_scale"] == 3 and top["pending_L_build_power"] == 6
    assert top["pending_A_self_improve"] == 3 and top["pending_A_build_compute"] == 3
    assert top["pending_H_propose_treaty"] == 2


def test_a_path_ends_by_the_last_step():
    cm = compiled(v0_5, "aligned")
    rng = random.Random(11)
    for _ in range(20):
        (state,) = cm.initial_states()
        for _ in range(36):
            if cm.is_terminal(state):
                break
            state = cm.step(state, tuple(rng.choice(sorted(ok)) for ok in cm.available(state)))
        assert cm.is_terminal(state)


def test_a_step_is_one_to_three_months():
    with pytest.raises(Exception, match="1, 2 or 3 months"):
        v0_5.build(step_months=4)
