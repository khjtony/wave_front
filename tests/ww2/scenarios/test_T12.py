"""T12: The atomic event ends the war regardless of `aims[JPN]`.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.

Reading (docs/ww2_v1_decisions.md E5, T12), on models/ww2/v1.py from the start of 1945Q2
(``1945Q1.json`` with its built-ins, tick 37: ``pending_WEST_atomic_program = 1``, so
``bomb_ready`` at tick 38), ``aims_GER = hegemonic``, ``aims_JPN`` swept:

- "The atomic event ends the war" := Nature's ``atomic`` sets ``pacific_war :=
  surrendered``; "regardless of aims_JPN" := for each of the three levels, the play in which
  Nature plays ``atomic`` at tick 38 exists and ends in ALLIED_VICTORY, and ``atomic`` reads
  no hidden objective (checked on the compiled guard and effect). Nature may decline the
  event; the report says so.
- "Only for a programme started at least 12 ticks earlier": with
  ``pending_WEST_atomic_program`` swept over 0 to 12 in the start state (counterfactual start
  dates: pending p at tick 37 means the decision was taken at tick 24 + p, and ``bomb_ready``
  is visible at tick 36 + p; for p = 0 the weapon is ready in the start state), the war ends
  by the bomb only for p <= 1, that is for a decision at tick <= 25, thirteen or more ticks
  before the event at 38. The claim's bound of 12 is implied (13 >= 12).
- The ``delivery`` part (``jpn_navy == attrited``) is a condition the claim does not name;
  it holds in the start state (Midway, 1942).

Engine: explicit exploration from the start state (the reachable set from tick 37 is a few
dozen states).
"""

import pytest

from models.ww2.hypotheses import SNAPSHOTS_V1, snapshot_state
from models.ww2.v1 import model
from wavefront.engine import explore

CLAIM = {
    "id": "T12",
    "from_state": "1945Q2",
    "claim": (
        "the atomic event ends the war regardless of `aims[JPN]`, and only for a "
        "program started at least 12 ticks earlier"
    ),
    "expected": "as stated; this is the one capability-discontinuity test",
    "sources": "Frank 1999",
}

START = "1945Q1"  # the state at the start of 1945Q2 (tick 37)
AIMS_JPN = ["status_quo", "regional", "hegemonic"]


def start(cm, aims_JPN, pending=None):
    s = list(
        snapshot_state(
            cm, START, "hegemonic", builtins=True, snapshots=SNAPSHOTS_V1, aims_JPN=aims_JPN
        )
    )
    if pending is not None:
        s[cm.index["pending_WEST_atomic_program"]] = pending
        s[cm.index["bomb_ready"]] = 1 if pending == 0 else 0
    return tuple(s)


def atomic_plays(cm, g):
    """(state id, joint move) pairs in which Nature plays atomic."""
    nature = cm.actors[-1]
    j = nature.action_index("atomic")
    return [(i, m) for i, moves in enumerate(g.moves) for m in moves if m[nature.index] == j]


@pytest.mark.parametrize("aims_JPN", AIMS_JPN)
def test_T12_the_bomb_ends_the_war(aims_JPN):
    cm = model.compile()
    s = start(cm, aims_JPN)
    assert cm.state_dict(s)["jpn_navy"] == "attrited"  # delivery holds at the start
    g = explore(cm, initial=[s])
    plays = [(i, m) for i, m in atomic_plays(cm, g) if g.states[i][cm.index["tick"]] == 38]
    assert plays
    ends = set()
    for i, m in plays:
        nxt = cm.step(g.states[i], m)
        assert cm.state_dict(nxt)["pacific_war"] == "surrendered"
        ends.add(cm.ending_of(nxt))
    assert "ALLIED_VICTORY" in ends
    declined = {g.ending[i] for i in range(g.size()) if g.ending[i]} - {"ALLIED_VICTORY"}
    print(
        f"\nT12 ({aims_JPN}): {g.size()} states; endings after the bomb at tick 38 {ends}; "
        f"endings where Nature declines it {declined}"
    )


def test_T12_the_event_reads_no_hidden_objective():
    cm = model.compile()
    nature = cm.actors[-1]
    atomic = nature.actions[nature.action_index("atomic")]
    read = set(atomic.guard_expr.free_vars())
    for e in atomic.effects:
        read.add(e.var)
    assert not {n for n in read if n.startswith("aims_")}


@pytest.mark.parametrize("aims_JPN", AIMS_JPN)
def test_T12_only_for_a_programme_started_early_enough(aims_JPN):
    """Necessity: the war ends by the bomb (some play reaches pacific_war == surrendered)
    only for pending p <= 1 at tick 37, a decision at tick <= 25, at least 13 ticks before
    the event at tick 38."""
    cm = model.compile()
    ends = []
    for p in range(13):
        g = explore(cm, initial=[start(cm, aims_JPN, p)])
        surrendered = any(cm.state_dict(x)["pacific_war"] == "surrendered" for x in g.states)
        if surrendered:
            ends.append(p)
    print(f"\nT12 ({aims_JPN}): pending values at tick 37 for which the bomb ends the war {ends}")
    assert ends == [0, 1]
    latest_decision = 24 + max(ends)
    assert 38 - latest_decision >= 12  # the claim's bound; the model's is 13
