"""The run_all orchestrator."""

import pytest

from wavefront.analysis import run_all
from wavefront.model import ModelError

from .games import coin, crisis, door, tug


def test_default_coalitions_and_kernels():
    a = run_all(tug())
    assert a.coalitions == [("A",), ("B",), ("A", "B")]
    entries = {e.coalition: e for e in a.kernels}
    assert entries[("A",)].in_kernel == {0: False}
    joint = entries[("A", "B")]
    assert joint.in_kernel == {0: True}
    assert joint.distances[0].shortest == 2 and joint.distances[0].forced is None
    assert joint.defection == {"A": {0: 3}, "B": {0: 3}}
    assert joint.uniformity is not None and joint.uniformity.uniform
    assert [n.kind for n in a.uniformity] == ["keep"]
    assert a.budget == a.cm.budget()


def test_endings_relaxations_pivotal_and_witnesses():
    a = run_all(crisis())
    assert a.endings == ["WAR"]
    (entry,) = a.contested
    assert entry.status == {0: "blocked"} and entry.rank == {}
    assert a.relaxations["WAR"] == [[]]
    assert a.pivotal["WAR"].blocking == [frozenset({"P"})]
    assert len(a.witnesses["WAR"]) == 5
    assert a.speculative == ["Nature.escalate"]
    assert list(a.sensitivity) == [("peace", ("P",))]


def test_horizon_is_an_ending_in_timed_models():
    a = run_all(door())
    assert a.endings == ["OUT", "HORIZON"]
    status = {e.ending: e.status[0] for e in a.contested}
    # A can walk out, or simply never walk and run out the clock
    assert status == {"OUT": "forced", "HORIZON": "forced"}


def test_explicit_initial_states_and_coalitions():
    cm = coin().compile()
    a = run_all(coin(), coalitions=[["P"]], initial=[cm.initial_states()[1]])
    assert a.explicit_initial and len(a.graph.initial) == 1
    assert [n.result.uniform for n in a.uniformity] == [True, True]
    with pytest.raises(ModelError, match="unknown actor"):
        run_all(coin(), coalitions=[{"Q"}])
