"""T2: French `resist` in 1936Q1 keeps the state inside V_WEST.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

from models.ww2.hypotheses import (
    first_available,
    fixed_model,
    realized_moves,
    restricted,
    snapshot_state,
)
from models.ww2.v0 import model
from wavefront import bmc
from wavefront.analysis import viability
from wavefront.engine import explore
from wavefront.model import V

CLAIM = {
    "id": "T2",
    "from_state": ("1936Q1, after the German entry"),
    "claim": (
        "if France plays `resist`, German `withdraw` is available and the state "
        "after the entry stays inside V_WEST; from the tick-0 state a hegemonic "
        "Germany that delays its entry until its army is ready keeps the state "
        "outside V_WEST (recorded result)"
    ),
    "expected": (
        "the tick-1 state (after the realized entry) ∈ V_WEST under the `resist` "
        "branch for both hypotheses, with `resist` then `withdraw` available; the "
        "tick-0 state ∉ V_WEST under hegemonic aims"
    ),
    "sources": ("Kershaw; Tooze; amended 2026-10-12"),
}

# Methods (decisions D6). From tick 0 neither hypothesis fits the explicit budget (both pass
# 3,000,000 states), so kernel membership is never computed whole here:
# - membership is shown by a sufficiency check: WEST's strategy is fixed (by a profile,
#   checked with the bounded checker to the horizon; or by a memoryless strategy, checked by
#   exhaustive exploration of the game left), and no play violates balance_europe;
# - non-membership is shown by a refutation: the other actors and Nature are fixed to one
#   memoryless strategy and WEST's kernel of that smaller game, computed exactly, excludes
#   the state. The true kernel is contained in it, so the state is outside the true kernel.


def tick0(cm, aims):
    return snapshot_state(cm, "1935Q4", aims)


def german_wait_strategy(state, names):
    """GER: rearm at once; withdraw from a resisted Rhineland while the army is unready;
    secure Italy and Austria; then wait until the army is ready (arms_GER high) before
    remilitarizing, attacking Poland and France, and taking Czechoslovakia."""
    rising = state["arms_GER"] == "rising"
    if rising and "withdraw_rhineland" in names:
        return "withdraw_rhineland"
    if rising and "rearm" in names:
        return "rearm"
    for a in ("court_italy", "annex_austria"):
        if a in names:
            return a
    if rising:
        return "idle"
    for a in (
        "remilitarize_rhineland",
        "attack_france",
        "attack_poland",
        "align_balkans",
        "occupy_bohemia",
        "attack_czechoslovakia",
        "demand_sudeten",
    ):
        if a in names:
            return a
    return "idle"


ADVERSARY = {
    "GER": german_wait_strategy,
    "USSR": first_available(),
    "JPN": first_available(),
    "Nature": first_available("campaign_west", "air_battle_german", "campaign_rhineland"),
}
# WEST in the resist branch: resist, declare war, attack while the army is unready.
RESIST_AND_STRIKE = first_available("resist_rhineland", "declare_war", "offensive_west")


def test_T02_revisionist():
    """1936Q1 is in V_WEST under revisionist aims: sufficiency check with WEST fixed by the
    profile fight_on (never negotiate); the bounded checker finds no play to the horizon
    that violates balance_europe. Resist and withdraw are available in the resist branch."""
    cm = fixed_model(model, aims_GER="revisionist").compile(profile="fight_on")
    assert cm.initial_states() == [tick0(cm, "revisionist")]
    assert bmc.reach(cm, 20, ~V.invariant("balance_europe")) is None
    assert_resist_then_withdraw("revisionist")


def test_T02_hegemonic():
    """The recorded result registered in the amended claim (2026-10-12): the tick-0 state is
    NOT in V_WEST under hegemonic aims. Shown through a necessary condition for membership:
    the state is outside WEST's kernel of the game in which GER, USSR, JPN and Nature play
    the fixed strategy ADVERSARY (Germany rearms at once, does not enter the Rhineland until
    its army is ready, and WEST never gets a casus belli while the 1936 army could still be
    beaten). Resist and withdraw are available in the resist branch after the entry."""
    assert_resist_then_withdraw("hegemonic")
    cm = model.compile()
    g = explore(restricted(cm, ADVERSARY), initial=[tick0(cm, "hegemonic")])
    kernel = viability(g, ["WEST"], "balance_europe").kernel
    assert g.initial[0] not in kernel


def assert_resist_then_withdraw(aims):
    cm = model.compile()
    ger, west = cm.actors[0], cm.actors[1]
    resist = west.action_index("resist_rhineland")
    withdraw = ger.action_index("withdraw_rhineland")
    s1 = cm.step(tick0(cm, aims), realized_moves(cm)[0])  # GER enters the zone, 1936Q1
    assert resist in cm.available(s1)[1]
    s2 = cm.step(s1, (0, resist, 0, 0, 0))
    assert withdraw in cm.available(s2)[0]


@pytest.mark.parametrize("aims", ["revisionist", "hegemonic"])
def test_T02_resist_branch(aims):
    """The conditional reading of the claim: once Germany has entered the zone (the realized
    1936Q1 move), the state in which France may resist is in V_WEST under both hypotheses.
    Sufficiency check with WEST fixed to RESIST_AND_STRIKE (resist, declare war, attack the
    unready army): every play of the other actors and Nature, explored exhaustively, keeps
    balance_europe, and every terminal state is GERMAN_DEFEAT."""
    cm = model.compile()
    s1 = cm.step(tick0(cm, aims), realized_moves(cm)[0])
    g = explore(restricted(cm, {"WEST": RESIST_AND_STRIKE}), initial=[s1])
    assert all(cm.evaluate("balance_europe", s) for s in g.states)
    assert {e for e in g.ending if e is not None} == {"GERMAN_DEFEAT"}
    assert g.size() == 45168
