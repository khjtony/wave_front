"""J1v1: registered 2026-10-24 in docs/july1914_testbed.md section 8.3 (the 1914 v1
registration, owner's decision 2h of 2026-10-23), before any v1 guard.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature, in the v1 content of section 8.2. Do not edit the claim text
without a changelog entry in that document. Skipped until ``models/july1914/v1.py`` exists
and the owner gives the go for the first sight by setting ``WF_FIRST_SIGHT_1914V1=1`` (the
skip condition was "v1.py exists" until the model step built it; changed then so that the
first sight is held, docs/july1914_v1_decisions.md V9). The body is the reading of
docs/july1914_v1_decisions.md section R (J1v1), written before that go.
"""

import os
from pathlib import Path

import pytest

from models.july1914.v1 import REALIZED_MOVES
from models.ww2.hypotheses import realized_rows

from .common import PAIRS, Timer, compiled, label, replay

V1 = Path(__file__).resolve().parents[2] / "models" / "july1914" / "v1.py"
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_1914V1") == "1"

CLAIM = {
    "id": "J1v1",
    "from_state": "tick 0",
    "claim": (
        "**regression.** The realized sequence of J1, with Tisza's consent of 14 July added, is "
        "reachable in v1 with zero relaxations, every action available at its tick; in particular "
        "the German mobilization of 1 August is available under its new Russian-measures and [H] "
        "parts, after the Russian general mobilization order of 30 July"
    ),
    "expected": (
        "reachable, zero relaxations, under at least one hypothesis pair, ending in `GENERAL_WAR` "
        "at the horizon"
    ),
    "sources": (
        "J1's sources; Berchtold's report to Franz Joseph of 14 July; the German ultimatum to "
        "Russia of 31 July and the mobilization order of 1 August (Geiss; Mombauer (ed.) 2013)"
    ),
}


@pytest.mark.skipif(
    not (V1.exists() and FIRST_SIGHT),
    reason="1914 v1 first sight held for the owner's go (WF_FIRST_SIGHT_1914V1=1)",
)
def test_J1v1():
    timer = Timer()
    rows = realized_rows(REALIZED_MOVES)
    ok = []
    print(f"\n[J1v1] engine: explicit replay ({len(rows)} rows)")
    for pair in PAIRS:
        cm = compiled(pair)
        states, stop = replay(pair)
        if stop is None:
            end = cm.ending_of(states[-1])
            tick = states[-1][cm.index["tick"]]
            print(f"[J1v1] {label(pair)}: every row available; tick {tick}, ending {end}")
            ger = next(a for a in cm.actors if a.name == "GER")
            mob = ger.action_index("mobilize") in cm.available(states[34])[ger.index]
            rus = cm.state_dict(states[34])["mob_RUS"]
            print(f"[J1v1]   GER.mobilize available at tick 34: {mob}; mob_RUS at 34: {rus}")
            if tick == 38 and end == "GENERAL_WAR" and mob and rus == "general":
                ok.append(pair)
        else:
            print(f"[J1v1] {label(pair)}: stops at tick {stop[0]}: {stop[1]}.{stop[2]} unavailable")
    print(f"[J1v1] reachable with zero relaxations under: {ok} ({timer})")
    assert ok, "the realized sequence is not reachable under any hypothesis pair"
