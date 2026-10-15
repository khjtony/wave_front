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
        "interim, at quarterly resolution: from the 1939Q2 state with the alliance "
        "counterfactually concluded, {WEST, USSR} keeps Poland independent through 1940Q4 "
        "under `deterred` iff the belief is `will_fight`, and the attack is forced "
        "otherwise (recorded: at quarterly resolution the alliance of summer 1939 cannot "
        "form before the attack, so the registered race is invisible); the registered "
        "question is re-asked at 3-day resolution in the summer-1939 crisis sub-game "
        "(docs/crisis_1939_testbed.md), where the alliance race and the attack are decided"
    ),
    "sources": "the 1939 Anglo-Soviet talks; Weinberg; amended 2026-10-15",
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


def start(cm, belief, alliance=True):
    """The 1939Q2 start state with belief_GER set to ``belief`` and, by default, the
    Anglo-Soviet alliance counterfactually concluded (the interim reading of the amended
    claim, 2026-10-15); ``alliance=False`` is the state as the record has it."""
    s = list(
        snapshot_state(
            cm, START, "hegemonic", builtins=True, snapshots=SNAPSHOTS_V1, aims_JPN="hegemonic"
        )
    )
    i = cm.index["belief_GER"]
    s[i] = cm.variables[i].levels.index(belief)
    if alliance:
        s[cm.index["anglo_soviet_alliance"]] = 1
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
    """Interim reading (amended 2026-10-15): from the start state with the alliance
    concluded, under deterred, {WEST, USSR} keeps poland_blocked iff belief_GER is
    will_fight; without the alliance (the record's state) nothing blocks under any belief,
    which is the recorded quarterly result; the run without the profile is printed."""
    cm = model.compile(profile="deterred")
    s = start(cm, belief)
    joint = membership(cm, s, ["WEST", "USSR"])
    west = membership(cm, s, ["WEST"])
    ussr = membership(cm, s, ["USSR"])
    record = membership(cm, start(cm, belief, alliance=False), ["WEST", "USSR"])
    plain = model.compile()
    without = membership(plain, start(plain, belief), ["WEST", "USSR"])
    print(
        f"\nT9 belief_GER {belief}: alliance concluded: {{WEST, USSR}} {joint}, {{WEST}} "
        f"{west}, {{USSR}} {ussr}; as the record has it (no alliance): {record}; "
        f"{{WEST, USSR}} without the profile deterred: {without}"
    )
    assert record == "out"  # the recorded quarterly result: the race is invisible
    if belief == "will_fight":
        assert joint == "in"
    else:
        assert joint == "out"


@pytest.mark.slow
@pytest.mark.parametrize("belief", ["will_not_fight", "uncertain"])
def test_T09_otherwise_contested(belief):
    """Recorded (amended 2026-10-15): without the belief condition the attack on Poland is
    *forced* by Germany at quarterly resolution (the army is ready and no campaign is
    involved, so the standard region applies and nothing restrains the attack); the
    registered "otherwise contested" is re-asked in the crisis sub-game."""
    cm = model.compile(profile="deterred")
    s = start(cm, belief)
    forced, _ = bounded.forces(cm, s, X, TAKE)
    rest = {"WEST": KEEP["WEST"], "USSR": KEEP["USSR"], "JPN": [], "Nature": []}
    blocked, _ = bounded.blocks(cm, s, X, rest)
    region = "forced" if forced else ("blocked" if blocked else "undecided")
    print(f"\nT9 belief_GER {belief}: region for {{GER}} and Poland taken: {region}")
    assert region == "forced"


@pytest.mark.slow
def test_T09_can_the_west_bring_will_fight_about_before_the_attack():
    """Reported (E5): in v1 only declare_war sets will_fight; the earliest tick at which
    WEST can make it hold, and whether Germany can take Poland by then."""
    cm = model.compile(profile="deterred")
    s = start(cm, "will_not_fight", alliance=False)
    resolve = bounded.reach_from(cm, s, 7, V.belief_GER == "will_fight")
    taken = bounded.reach_from(cm, s, 7, X)
    t_resolve = resolve.states[-1][cm.index["tick"]]
    t_taken = taken.states[-1][cm.index["tick"]]
    print(f"\nT9: will_fight first at tick {t_resolve}; Poland first taken at tick {t_taken}")
    assert t_resolve >= 14 and t_taken >= 14
