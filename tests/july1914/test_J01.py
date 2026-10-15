"""J1: registered 2026-10-15 in docs/july1914_testbed.md section 3.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature. Do not edit the claim text without a changelog entry in that
document.

Reading (docs/july1914_decisions.md, R J1): under each hypothesis pair the realized moves
of data/july1914/realized_moves.csv are replayed from the tick-0 state with
``cm.available`` and ``cm.step`` (the explicit engine's semantics, zero relaxations); the
claim holds iff under at least one pair every row is available at its tick and the play ends
at tick 38 in ``GENERAL_WAR``. Engine: explicit replay.
"""

from models.july1914.v0 import REALIZED_MOVES
from models.ww2.hypotheses import realized_rows

from .common import PAIRS, Timer, compiled, label, replay

CLAIM = {
    "id": "J1",
    "from_state": "tick 0",
    "claim": (
        "the realized sequence (the blank cheque of 5 to 6 July, the ultimatum of 23 July, "
        "the Serbian reply, the declaration of 28 July, the Russian partial then general "
        "mobilization, the German Kriegsgefahrzustand, the declarations of 1 and 3 August, "
        "the Belgian ultimatum and invasion, the British ultimatum) is reachable with zero "
        "relaxations, every action available at its tick"
    ),
    "expected": "reachable, zero relaxations",
    "sources": (
        "Geiss, July 1914 (the documents); Albertini; Clark, The Sleepwalkers; Otte, July Crisis"
    ),
}


def test_J1():
    timer = Timer()
    rows = realized_rows(REALIZED_MOVES)
    ok = []
    print(f"\n[J1] engine: explicit replay ({len(rows)} rows)")
    for pair in PAIRS:
        cm = compiled(pair)
        states, stop = replay(pair)
        if stop is None:
            end = cm.ending_of(states[-1])
            tick = states[-1][cm.index["tick"]]
            print(f"[J1] {label(pair)}: every row available; tick {tick}, ending {end}")
            if tick == 38 and end == "GENERAL_WAR":
                ok.append(pair)
        else:
            print(f"[J1] {label(pair)}: stops at tick {stop[0]}: {stop[1]}.{stop[2]} unavailable")
    print(f"[J1] reachable with zero relaxations under: {ok} ({timer})")
    assert ok, "the realized sequence is not reachable under any hypothesis pair"
