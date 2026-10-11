"""Witness traces and their rendering."""

from wavefront.engine import Trace, explore, witness
from wavefront.model import Bump, Inc, Model, Set, V


def ladder():
    m = Model("ladder", horizon=6)
    m.var("level", levels=["ground", "first", "second", "roof"])
    m.flag("tired")
    p = m.actor("P", remember_last=True)
    p.action("climb", guard=V.tired == False, effect=Bump("level", 1))  # noqa: E712
    p.action("leap", guard=V.level == "first", effect=[Set("level", "roof"), Inc("n")])
    m.nature().event("wind", effect=Set("tired", True))
    m.counter("n", max=6)
    m.actor("Q").action("count", effect=Inc("n"))
    m.ending("TOP", V.level == "roof")
    return explore(m.compile())


def test_witness_is_shortest_and_valid():
    g = ladder()
    top = g.ending_states("TOP")
    w = witness(g, 0, top)
    assert isinstance(w, Trace)
    assert w[-1][1] is None and w[-1][0] in top
    assert len(w) - 1 == min(g.depth[t] for t in top) == 2  # climb, then leap
    for (s, jm), (t, _) in zip(w, w[1:], strict=False):
        assert g.states[t] == g.model.step(g.states[s], jm)
    assert w.state_ids[0] == 0 and len(w.joint_moves) == len(w) - 1


def test_witness_edge_cases():
    g = ladder()
    assert witness(g, 0, {0}) == Trace([(0, None)])
    assert witness(g, 0, set()) is None
    terminal = next(i for i, t in enumerate(g.terminal) if t)
    assert witness(g, terminal, {0}) is None


def test_render_shows_ticks_actions_and_changes():
    g = ladder()
    text = witness(g, 0, g.ending_states("TOP")).render(g)
    lines = text.splitlines()
    assert lines[0] == "| tick | P | Q | Nature | changes |"
    assert lines[2].startswith("| 0 | climb |")
    assert "level: ground -> first" in lines[2]
    assert "leap" in lines[3] and "level: first -> roof" in lines[3]
    assert "n: 0 -> 1" in lines[3]
    assert "last_P" not in text
    assert lines[-1] == "| 2 | - | - | - | ending: TOP |"
