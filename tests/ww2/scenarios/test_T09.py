"""T9: A UK, France, USSR alliance can block the attack on Poland, conditionally.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.

Reading (docs/ww2_v1_decisions.md E5, T9), on models/ww2/v1.py from the start of 1939Q2
(``1939Q1.json`` with its built-ins, tick 13), ``aims_GER = hegemonic``:

- {UK, FR, USSR} := {WEST, USSR}; ``belief[GER][UK]`` := ``belief_GER``; "the attack on
  Poland" := GER ``attack_poland``; "block" := keep ``poland_blocked`` (``poland ==
  independent or tick > 20``): the kernel ``safe(C, poland_blocked)``.
- The belief condition enters as the profile ``deterred`` on GER (forbids
  ``attack_poland`` while ``belief_GER == will_fight and anglo_soviet_alliance``), a named,
  relaxable behavioural assumption; ``belief_GER`` at the start state is swept over its three
  levels as counterfactual initial states. Expected as registered: under ``deterred`` and
  ``will_fight``, {WEST, USSR} is a minimal coalition that keeps ``poland_blocked`` (neither
  {WEST} nor {USSR} alone does); under the other two levels nothing blocks the attack.
- "Otherwise contested": the standard contested region for X := ``poland != independent``
  and the coalition {GER}, with the fortune variant reported.

Engine (decisions E6): the bounded checker with fixed strategies (models/ww2/bounded.py).
Membership of a coalition's kernel is shown by a fixed strategy of the coalition that keeps
Poland independent through tick 20 against every play of the others (sufficiency), and
refuted by a fixed German strategy that takes Poland whatever the coalition does; a state
settled by neither is "undecided". ``aims_JPN`` is fixed to hegemonic (Japan has no move
that bears on Poland before 1941).
"""

import pytest

from models.ww2 import bounded
from models.ww2.hypotheses import SNAPSHOTS_V1, snapshot_state
from models.ww2.v1 import model
from wavefront.model import V

CLAIM = {
    "id": "T9",
    "from_state": "1939Q2",
    "claim": (
        "a UK, France, USSR alliance can block the attack on Poland only if "
        "`belief[GER][UK]` is that Britain will fight"
    ),
    "expected": (
        "pivotal coalition {UK, FR, USSR} with the belief condition; otherwise `contested`"
    ),
    "sources": "the 1939 Anglo-Soviet talks; Weinberg",
}

START = "1939Q1"  # the state at the start of 1939Q2 (tick 13)
TAKEN = ~V.invariant("poland_blocked")  # Poland taken at a tick <= 20
X = V.poland != "independent"
BELIEFS = ["will_not_fight", "uncertain", "will_fight"]
# The coalition's strategies: conclude the alliance and declare (resolve observed).
KEEP = {
    "WEST": ["approach_ussr", "declare_war", "guarantee_poland"],
    "USSR": ["accept_alliance"],
}
TAKE = {"GER": ["attack_poland"]}


def start(cm, belief):
    s = list(
        snapshot_state(
            cm, START, "hegemonic", builtins=True, snapshots=SNAPSHOTS_V1, aims_JPN="hegemonic"
        )
    )
    i = cm.index["belief_GER"]
    s[i] = cm.variables[i].levels.index(belief)
    return tuple(s)


def membership(cm, s, coalition):
    k = 21 - s[cm.index["tick"]]
    keep = {a: KEEP.get(a, []) for a in coalition}
    inside, _ = bounded.blocks(cm, s, TAKEN, keep, k=k)
    if inside:
        return "in"
    outside, _ = bounded.forces(cm, s, TAKEN, TAKE, k=k)
    return "out" if outside else "undecided"


@pytest.mark.slow
@pytest.mark.parametrize("belief", BELIEFS)
def test_T09_pivotal_coalition_with_the_belief_condition(belief):
    """Under deterred: {WEST, USSR} keeps poland_blocked iff belief_GER is will_fight, and
    neither alone does; printed with the run without the profile."""
    cm = model.compile(profile="deterred")
    s = start(cm, belief)
    joint = membership(cm, s, ["WEST", "USSR"])
    west = membership(cm, s, ["WEST"])
    ussr = membership(cm, s, ["USSR"])
    plain = model.compile()
    without = membership(plain, start(plain, belief), ["WEST", "USSR"])
    print(
        f"\nT9 belief_GER {belief}: {{WEST, USSR}} {joint}, {{WEST}} {west}, {{USSR}} {ussr}; "
        f"{{WEST, USSR}} without the profile deterred: {without}"
    )
    if belief == "will_fight":
        assert (joint, west, ussr) == ("in", "out", "out")
    else:
        assert joint == "out"


@pytest.mark.slow
@pytest.mark.parametrize("belief", ["will_not_fight", "uncertain"])
def test_T09_otherwise_contested(belief):
    """Without the belief condition the attack is contested: the standard contested region
    for {GER} and Poland taken (not forced by Germany, not blocked by the rest). The fortune
    variant is printed."""
    cm = model.compile(profile="deterred")
    s = start(cm, belief)
    forced, _ = bounded.forces(cm, s, X, TAKE)
    rest = {"WEST": KEEP["WEST"], "USSR": KEEP["USSR"], "JPN": [], "Nature": []}
    blocked, _ = bounded.blocks(cm, s, X, rest)
    region = "forced" if forced else ("blocked" if blocked else "undecided")
    # Fortune variant: Germany alone already decides X when it forces it; Nature joining
    # either side changes nothing then.
    print(f"\nT9 belief_GER {belief}: region for {{GER}} and Poland taken: {region}")
    assert region == "contested"


@pytest.mark.slow
def test_T09_can_the_west_bring_will_fight_about_before_the_attack():
    """Reported (E5): in v1 only declare_war sets will_fight; the earliest tick at which
    WEST can make it hold, and whether Germany can take Poland by then."""
    cm = model.compile(profile="deterred")
    s = start(cm, "will_not_fight")
    resolve = bounded.reach_from(cm, s, 7, V.belief_GER == "will_fight")
    taken = bounded.reach_from(cm, s, 7, X)
    t_resolve = resolve.states[-1][cm.index["tick"]]
    t_taken = taken.states[-1][cm.index["tick"]]
    print(f"\nT9: will_fight first at tick {t_resolve}; Poland first taken at tick {t_taken}")
    assert t_resolve >= 14 and t_taken >= 14
