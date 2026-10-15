"""K1: registered 2026-10-15 in docs/crisis_1939_testbed.md section 3.

The summer-1939 crisis sub-game of WW2 v1 (3-day ticks, 5 July to 3 September 1939), entered
from the 1939Q3 state. Do not edit the claim text without a changelog entry in that
document.

Reading (docs/crisis_1939_decisions.md R1), from the entry state (``1939Q2.json`` with its
built-ins, ``aims_GER = hegemonic``, ``aims_USSR = defensive``), full build, nothing relaxed:

- "reachable with zero relaxations": every realized move of
  ``data/ww2/crises/1939/realized_moves.csv`` is available at its tick, with no profile and
  with ``deterred``; the play ends at tick 20 in ``ATTACK_LAUNCHED``; the terminal state is
  in the graph explored from the entry state; the claim's sequence is at its ticks
  (decisions C1 to C4).
- "the exit state equals v1's realized 1939Q4 state": the exit of the terminal state equals
  v1's own realized transition of 1939Q3 on the nine exit variables, and every difference
  from ``1939Q3.json`` is one that v1's transition shows too (C12); the same through the
  flattened game. The literal comparison with ``1939Q3.json`` is printed.

Engine: the explicit engine (replay, ``explore``) and ``wavefront.engine.flatten``.
"""

import time

import pytest

from models.ww2.crises import summer_1939 as crisis
from tests.ww2.crisis_1939 import common

CLAIM = {
    "id": "K1",
    "from_state": "tick 0",
    "claim": (
        "the realized sequence (military talks agreed, missions in Moscow, Voroshilov's "
        "question, the Polish refusal, the Soviet adjournment, the pact of 23 August, the "
        "attack order of 25 August and its cancellation, the re-order of 31 August, the "
        "attack of 1 September, the declarations of 3 September) is reachable with zero "
        "relaxations, and the exit state equals v1's realized 1939Q4 state"
    ),
    "expected": "reachable, zero relaxations; exit state matches",
    "sources": (
        "DBFP Third Series vols. VI and VII; DGFP Series D vol. VII; Halder's diary; Weinberg"
    ),
}


@pytest.mark.parametrize("profile", [None, "deterred"])
def test_K1(profile, capsys):
    t0 = time.time()
    cm = common.compiled(inert=True, profile=profile)
    rows = crisis.realized_rows()
    moves = crisis.realized_moves(cm)
    states = crisis.replay(cm, common.entry(cm), moves)  # raises on an unavailable move
    assert cm.assumptions() and not cm.relax  # nothing relaxed
    final = states[-1]
    assert cm.state_dict(final)["tick"] == "20"
    assert cm.ending_of(final) == "ATTACK_LAUNCHED"
    g = common.graph(cm, [common.entry(cm)])
    assert all(tuple(s) in g.index for s in states)

    # the claim's sequence, at the ticks of decisions C1 to C4
    played = {(k, a.name): r[a.name] for k, r in enumerate(rows) for a in cm.actors}
    d = [cm.state_dict(s) for s in states]
    assert played[(6, "WEST")] == "send_missions" and d[12]["talks"] == "military"
    assert played[(13, "USSR")] == "ask_passage"
    assert played[(14, "USSR")] == "adjourn_talks"
    assert played[(15, "Nature")] == "passage_refused"
    assert d[16]["german_approach"] == "pact" and d[15]["german_approach"] != "pact"
    assert d[17]["attack_order"] == "ordered" and played[(17, "GER")] == "cancel_attack"
    assert played[(19, "GER")] == "attack_poland" and d[20]["attack_order"] == "launched"

    # the exit state
    out = common.exit_applied(final, cm)
    v1q3 = common.v1_realized_q3()
    snap = common.snapshot_q3()
    literal = {k: (out[k], snap[k]) for k in crisis.EXIT_VARIABLES if out[k] != snap[k]}
    v1_own = {k for k in crisis.EXIT_VARIABLES if v1q3[k] != snap[k]}
    with capsys.disabled():
        print(
            f"\nK1 [{profile}] explicit engine, {g.size()} states, {time.time() - t0:.1f} s; "
            f"exit {out}; literal differences from 1939Q3.json {literal}; "
            f"v1's own differences {sorted(v1_own)}"
        )
    assert out == {k: v1q3[k] for k in crisis.EXIT_VARIABLES}
    assert set(literal) <= v1_own

    # the same through the flattened game (v1 with a crisis action)
    fm, sub = common.flattened_v1()
    back = _through_the_flattened_game(fm, sub)
    assert {k: back[k] for k in crisis.EXIT_VARIABLES} == {
        k: v1q3[k] for k in crisis.EXIT_VARIABLES
    }


def _through_the_flattened_game(fm, sub):
    s = common.COARSE_Q2_STATE
    names = [a.name for a in fm.actors]
    avail = fm.available(s)
    move = [a[0] for a in avail]
    ger = names.index("GER")
    move[ger] = next(k for k in avail[ger] if fm.actors[ger].actions[k].name == "crisis_1939")
    state = fm.step(s, tuple(move))
    for fine_move in crisis.realized_moves(sub):
        chosen = {fa.name: fa.actions[j].name for fa, j in zip(sub.actors, fine_move, strict=True)}
        avail = fm.available(state)
        flat = []
        for i, a in enumerate(fm.actors):
            want = chosen.get(a.name)
            opts = [k for k in avail[i] if want is None or a.actions[k].name == want]
            assert opts, (a.name, want)
            flat.append(opts[0])
        state = fm.step(state, tuple(flat))
    back = fm.step(state, tuple(a[0] for a in fm.available(state)))
    assert not fm.is_fine(back)
    return fm.state_dict(back)
