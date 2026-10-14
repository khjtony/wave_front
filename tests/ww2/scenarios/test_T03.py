"""T3: Refused Munich leads to war in 1938, with a contested ending.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.

Reading (docs/ww2_v1_decisions.md E5, T3), on models/ww2/v1.py from the start of 1938Q3
(``1938Q2.json`` with its built-ins, tick 10; pending German rearmament 1, last_GER
demand_sudeten), under both ``aims_GER``:

- "Munich refused": WEST does not play ``concede`` at tick 10 (nor later). "War within 2
  ticks": ``war_west_ger == war`` reachable at a tick t <= 12 along a play in which
  ``concede`` is never chosen (bounded checker with the concession excluded). The Czech
  obligation (``czech_obligation``) stays in force.
- "The ending is contested, not forced for either side": at the first war state of the
  shortest such witness, W_GER := AXIS_HEGEMONY_EUROPE or NEGOTIATED_PEACE is not forced by
  {GER} and W_WEST := GERMAN_DEFEAT or reich == surrendered is not forced by {WEST}
  (standard notion: every other actor, Nature included, is the adversary), with the fortune
  table of E5 reported (the coalition joined by Nature, and the rest joined by Nature).
- v1 judges a 1938 war at 1945Q4 (v0 at 1941Q1); the reachability of each v1 ending from the
  war state is reported as the diagnostic.

Engine: the bounded checker from the snapshot state (models/ww2/bounded.py). "Not forced" is
shown by a fixed strategy of the rest that keeps the target false whatever the coalition
does (a sufficiency check of the rest's kernel for the complement, decisions E6), which
implies the coalition cannot force it. The fortune cells are decided the same way, or left
"undecided" when neither fixed strategy settles them; they are reported, not asserted.
"""

import pytest

from models.ww2 import bounded
from models.ww2.hypotheses import SNAPSHOTS_V1, snapshot_state
from models.ww2.v1 import model
from wavefront.model import V

CLAIM = {
    "id": "T3",
    "from_state": "1938Q3",
    "claim": "Munich refused leads to war in 1938",
    "expected": (
        "`war[GER][WEST]` reachable within 2 ticks; the ending is `contested`, not "
        "forced for either side"
    ),
    "sources": "Weinberg; Murray and Millett; the opposing readings of German readiness",
}

START = "1938Q2"  # the state at the start of 1938Q3 (tick 10)
W_GER = V.ending("AXIS_HEGEMONY_EUROPE") | V.ending("NEGOTIATED_PEACE")
W_WEST = V.ending("GERMAN_DEFEAT") | (V.reich == "surrendered")
NOTHING = {"WEST": [], "USSR": [], "JPN": [], "Nature": [], "GER": []}

# Fixed strategies used to decide the fortune cells (decisions E6).
GER_PUSH = {
    "GER": ["attack_poland", "attack_france", "invade_britain", "air_offensive", "rearm"],
    "Nature": ["campaign_west", "air_battle_german"],
}
WEST_PUSH = {
    "WEST": ["offensive_west", "rearm"],
    "Nature": ["campaign_rhineland", "reich_collapses"],
}


def start(cm, aims_GER):
    return snapshot_state(
        cm, START, aims_GER, builtins=True, snapshots=SNAPSHOTS_V1, aims_JPN="hegemonic"
    )


def refusal_witness(cm, aims_GER):
    s = start(cm, aims_GER)
    return bounded.reach_from(
        cm,
        s,
        2,
        V.war_west_ger == "war",
        constrain=lambda enc: bounded.never(enc, "WEST", "concede"),
    )


def without(names, *actors):
    return {a: v for a, v in names.items() if a not in actors}


@pytest.mark.parametrize("aims_GER", ["revisionist", "hegemonic"])
def test_T03_war_within_two_ticks(aims_GER):
    cm = model.compile()
    assert "czech_obligation" in cm.assumptions() and not cm.relax
    trace = refusal_witness(cm, aims_GER)
    assert trace is not None
    war_tick = trace.states[-1][cm.index["tick"]]
    assert war_tick <= 12
    west = next(a for a in cm.actors if a.name == "WEST")
    assert "concede" not in [west.actions[m[west.index]].name for m in trace.moves]
    print(f"\nT3 ({aims_GER}) refusal witness, war visible at tick {war_tick}:")
    print(trace.render(cm))


@pytest.mark.slow
@pytest.mark.parametrize("aims_GER", ["revisionist", "hegemonic"])
def test_T03_not_forced_for_either_side(aims_GER):
    """Standard notion at the first war state of the shortest refusal witness: the rest
    (Nature included) keeps W_GER false against every German play, and keeps W_WEST false
    against every Western play, so neither {GER} nor {WEST} forces its ending. The fortune
    table is printed (reported, not asserted)."""
    cm = model.compile()
    war = refusal_witness(cm, aims_GER).states[-1]
    ger_blocked, ger_play = bounded.blocks(cm, war, W_GER, without(NOTHING, "GER"))
    west_blocked, west_play = bounded.blocks(cm, war, W_WEST, without(NOTHING, "WEST"))
    table = fortune_table(cm, war)
    print(f"\nT3 ({aims_GER}) from tick {war[cm.index['tick']]}: fortune table {table}")
    assert ger_blocked, ger_play.render(cm) if ger_play else None
    assert west_blocked, west_play.render(cm) if west_play else None


def fortune_table(cm, war):
    """E5's fortune cells for both sides: whether the side joined by Nature forces its
    target ("forced with fortune"), and whether the other principals joined by Nature keep
    it false ("blocked with fortune"); each cell "yes", "no" or "undecided" by the fixed
    strategies of this module."""
    out = {}
    for side, target, push in (("GER", W_GER, GER_PUSH), ("WEST", W_WEST, WEST_PUSH)):
        forced, _ = bounded.forces(cm, war, target, push)
        rest_nature = without(NOTHING, side)  # every other principal and Nature do nothing
        rest_blocks, _ = bounded.blocks(cm, war, target, rest_nature)
        # "no" for the forced cell is shown by a strategy of the other principals alone
        # (Nature free) that keeps the target false.
        others = without(NOTHING, side, "Nature")
        others_block, _ = bounded.blocks(cm, war, target, others)
        out[side] = {
            "forced_with_fortune": "yes" if forced else ("no" if others_block else "undecided"),
            "blocked_with_fortune": "yes" if rest_blocks else "undecided",
        }
    return out


@pytest.mark.slow
@pytest.mark.parametrize("aims_GER", ["revisionist", "hegemonic"])
def test_T03_endings_reachable_from_the_war_state(aims_GER):
    """Diagnostic (E5): which v1 endings are reachable from the war state (bounded checker
    to the horizon); reported, not asserted."""
    cm = model.compile()
    war = refusal_witness(cm, aims_GER).states[-1]
    k = cm.horizon - war[cm.index["tick"]]
    found = {}
    for name in model.endings:
        trace = bounded.reach_from(cm, war, k, name)
        found[name] = None if trace is None else trace.states[-1][cm.index["tick"]]
    print(f"\nT3 ({aims_GER}) endings reachable from the war state (first tick): {found}")
    assert any(v is not None for v in found.values())
