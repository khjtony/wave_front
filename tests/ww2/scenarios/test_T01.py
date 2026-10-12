"""T1: Realized trajectory to 1940Q2 is reachable from the 1936Q1 snapshot.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

from models.ww2.hypotheses import realized_moves, snapshot_state
from models.ww2.v0 import model

CLAIM = {
    "id": "T1",
    "from_state": "1936Q1 snapshot",
    "claim": (
        "the realized trajectory to 1940Q2 (Rhineland, Anschluss, Munich, Prague, "
        "Pact, Poland, the fall of France) is reachable"
    ),
    "expected": "reachable with zero relaxations",
    "sources": "ICB; Weinberg; Kershaw",
}


def test_T01():
    """Replay data/ww2/realized_moves.csv from the tick-0 state (aims_GER hegemonic,
    aims_USSR defensive) with the default compile: no relaxation, no profile. Every listed
    action must be available at its tick (``cm.available``), the replay must reach the
    horizon, and the ending must be BRITAIN_ALONE (the realized 1940Q4 state)."""
    cm = model.compile()
    assert cm.relax == frozenset()  # zero relaxations
    state = snapshot_state(cm, "1935Q4", "hegemonic")
    assert state in cm.initial_states()
    seen = {}
    for tick, move in enumerate(realized_moves(cm)):
        assert cm.state_dict(state)["tick"] == str(tick)
        avail = cm.available(state)
        for actor, j, acts in zip(cm.actors, move, avail, strict=True):
            assert j in acts, f"tick {tick}: {actor.name}.{actor.actions[j].name} unavailable"
        state = cm.step(state, move)
        d = cm.state_dict(state)
        for var, level in (
            ("rhineland", "remilitarized"),
            ("austria", "annexed"),
            ("sudeten", "german"),
            ("bohemia", "german"),
            ("nazi_soviet_pact", "True"),
            ("poland", "german"),
            ("france", "fallen"),
        ):
            if d[var] == level:
                seen.setdefault(var, tick + 1)
    assert cm.state_dict(state)["tick"] == "20"
    assert cm.ending_of(state) == "BRITAIN_ALONE"
    # Rhineland, Anschluss, Munich, Prague, Pact, Poland, the fall of France, in order
    # (ticks of the first state showing each; [SQR] rows lag their quarter by one tick).
    assert seen == {
        "rhineland": 1,
        "austria": 9,
        "sudeten": 11,
        "bohemia": 13,
        "nazi_soviet_pact": 15,
        "poland": 15,
        "france": 18,
    }
