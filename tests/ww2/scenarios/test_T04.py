"""T4: Prague flips `belief[UK][GER]` and enables `guarantee(Poland)`.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

from models.ww2.hypotheses import snapshot_state
from models.ww2.v0 import model
from wavefront.engine import explore, witness
from wavefront.model.compile import compile as compile_model

CLAIM = {
    "id": "T4",
    "from_state": "1939Q1",
    "claim": "Prague flips `belief[UK][GER]` to hegemonic, which enables `guarantee(Poland)`",
    "expected": (
        "the shortest trace to `guarantee(Poland)` passes through the belief flip; "
        "without the flip the action is unavailable"
    ),
    "sources": "Cabinet papers CAB 23; Hansard, March 1939",
}


def test_T04():
    """From the state at the start of 1939Q1 (file 1938Q4.json, tick 12; hegemonic aims),
    explored exhaustively to the horizon (146,504 states): the shortest trace to a state in
    which WEST's guarantee_poland is available passes through occupy_bohemia and the flip of
    belief_WEST to hegemonic, and no reachable state offers the guarantee with another
    belief. With the guard part ``belief`` relaxed the guarantee is available at once, so
    the belief condition is what withholds it (decisions D9: a political precondition the
    record supports, not a capability result)."""
    cm = model.compile()
    start = snapshot_state(cm, "1938Q4", "hegemonic")
    g = explore(cm, initial=[start], max_states=3_000_000)
    assert g.size() == 146_504
    gi = cm.actors[1].action_index("guarantee_poland")
    offers = {i for i in range(g.size()) if not g.terminal[i] and gi in g.avail[i][1]}
    assert offers and gi not in g.avail[g.initial[0]][1]
    assert all(g.state_dict(i)["belief_WEST"] == "hegemonic" for i in offers)

    trace = witness(g, g.initial[0], offers)
    assert len(trace) - 1 == 1
    ger_moves = [g.move_names(m)[0] for m in trace.joint_moves]
    assert "occupy_bohemia" in ger_moves
    beliefs = [g.state_dict(s)["belief_WEST"] for s in trace.state_ids]
    assert beliefs[0] == "uncertain" and beliefs[-1] == "hegemonic"

    relaxed = compile_model(model, relax={"WEST.guarantee_poland:belief"})
    assert gi in relaxed.available(snapshot_state(relaxed, "1938Q4", "hegemonic"))[1]
