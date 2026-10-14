"""T11: No `commit[USA] = total` before 1943 without an attack on the United States.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.

Reading (docs/ww2_v1_decisions.md E5, T11), on models/ww2/v1.py from the start of 1941Q1
(``1940Q4.json`` with its built-ins, tick 20), ``aims_GER = hegemonic``, ``aims_JPN`` swept,
under the profile ``electoral``:

- ``commit[USA] = total`` := ``commit_US == total``; "before 1943" := at a tick t < 28; "an
  attack on the United States" := JPN ``attack_south`` (the Imperial Conference decision of
  1 Dec 1941; there is no Nature event ``attack_on_us`` in the record, and none is added).
- "Unreachable without an attack": under ``electoral``, ``commit_US == total`` at a tick
  below 28 is unreachable in every play in which JPN never plays ``attack_south`` (bounded
  checker with the constraint). The minimal relaxation sets that make it reachable are
  reported (expected to name ``electoral`` or ``GER.declare_war_us:japanese_war``; not
  asserted).
- "With the attack it is immediate": in every reachable state at a tick t <= 26 in which
  ``attack_south`` is chosen, ``commit_US == total`` at t + 1 (a bounded search for a
  counterexample over every such play), and the shortest trace to ``total`` from the start
  state is reported.

Engine: the bounded checker from the snapshot state (models/ww2/bounded.py).
"""

import pytest
import z3

from models.ww2 import bounded
from models.ww2.hypotheses import SNAPSHOTS_V1, snapshot_state
from models.ww2.v1 import model
from wavefront.model import V

CLAIM = {
    "id": "T11",
    "from_state": "1941Q1",
    "claim": (
        "without an attack on the United States, `commit[USA] = total` is unreachable "
        "before 1943 under the `electoral` profile; with Nature's `attack_on_us` it is "
        "immediate"
    ),
    "expected": "as stated",
    "sources": "Gallup series; Kershaw",
}

START = "1940Q4"  # the state at the start of 1941Q1 (tick 20)
TOTAL_BEFORE_1943 = (V.commit_US == "total") & (V.tick < 28)


def start(cm, aims_JPN):
    return snapshot_state(
        cm, START, "hegemonic", builtins=True, snapshots=SNAPSHOTS_V1, aims_JPN=aims_JPN
    )


def no_attack(enc):
    return bounded.never(enc, "JPN", "attack_south")


@pytest.mark.slow
@pytest.mark.parametrize("aims_JPN", ["status_quo", "regional", "hegemonic"])
def test_T11_unreachable_without_an_attack(aims_JPN):
    cm = model.compile(profile="electoral")
    s = start(cm, aims_JPN)
    trace = bounded.reach_from(cm, s, 7, TOTAL_BEFORE_1943, constrain=no_attack)
    if trace is not None:
        print(f"\nT11 ({aims_JPN}) total without an attack:\n" + trace.render(cm))
    assert trace is None
    res = bounded.relax_from(cm, s, 7, TOTAL_BEFORE_1943, max_relax=2, constrain=no_attack)
    print(
        f"\nT11 ({aims_JPN}) minimal relaxation sets for total before 1943 without an "
        f"attack: {res.minimal_sets} (minimum {res.minimum_size})"
    )
    if res.trace is not None:
        print(res.trace.render(cm))


@pytest.mark.slow
@pytest.mark.parametrize("aims_JPN", ["status_quo", "regional", "hegemonic"])
def test_T11_with_the_attack_it_is_immediate(aims_JPN):
    """No play from the start state chooses attack_south at a tick t <= 26 and lacks
    commit_US == total at t + 1 (under status_quo the attack is never available: the
    hypothesis gate); the shortest trace to total is printed, not asserted."""
    cm = model.compile(profile="electoral")
    s = start(cm, aims_JPN)
    jpn = next(a for a in cm.actors if a.name == "JPN")
    attack = jpn.action_index("attack_south")
    total = cm.variables[cm.index["commit_US"]].levels.index("total")

    def counterexample(enc):
        cases = []
        for t in range(0, 26 - 20 + 1):
            cases.append(
                z3.And(
                    enc.active[t + 1],
                    z3.Not(enc.terminal[t]),
                    enc.chosen[t][jpn.index] == attack,
                    enc.state[t + 1][cm.index["commit_US"]] != total,
                )
            )
        return z3.Or(*cases)

    assert bounded.exists_from(cm, s, 7, counterexample) is None
    shortest = bounded.reach_from(cm, s, 19, V.commit_US == "total")
    shown = "none to the horizon" if shortest is None else "\n" + shortest.render(cm)
    print(f"\nT11 ({aims_JPN}) shortest trace to total: {shown}")
