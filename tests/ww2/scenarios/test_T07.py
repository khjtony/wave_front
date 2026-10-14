"""T7: The embargo makes war with Japan unavoidable within 8 ticks.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.

Reading (docs/ww2_v1_decisions.md E5, T7), on models/ww2/v1.py from the start of 1941Q3
(``1941Q2.json`` with its built-ins, tick 22), ``aims_GER = hegemonic``, ``aims_JPN``
swept:

- ``war[JPN][USA]`` := ``pacific_war >= war``; "embargo maintained" := the profile
  ``embargo_maintained``; WEST's move at tick 22 is fixed to ``embargo_jpn`` (the realized
  decision); "within 8 ticks" := a tick at most 30; the GER-JPN pact := ``anticomintern``.
- "Unavoidable unless the embargo is lifted or aims_JPN = status_quo": under the profile and
  ``aims_JPN`` in {regional, hegemonic}, no play keeps ``pacific_war == peace`` through tick
  30: the target ``tick == 30 and pacific_war == peace`` is unreachable (bounded checker). If
  it is reachable as is, the witness is the finding and the first half fails as registered.
- "The minimal assumption set is exactly {embargo maintained, aims_JPN != status_quo}": the
  minimal relaxation sets of the named assumptions that make "peace at tick 30" reachable,
  and their minimal hitting sets; the claim holds when the only minimal hitting set is
  {``embargo_maintained``, the ``hypothesis`` gates of the attack actions}. Reported per
  hypothesis, with and without the profile: <<JPN>> eventually war at each tick 22 to 31
  along the held-off path (the realized moves with Japan idle after its realized occupation
  of southern Indochina at tick 22, and no lifting), and the first tick at which
  ``attack_south`` is unavailable because ``oil_JPN == critical``.
- "strike_north reachable only with the pact and western USSR collapsing": (a)
  ``north_strike`` reachable from tick 22 under ``aims_JPN = hegemonic``; (b) unreachable
  with ``w_ussr == german`` excluded at every tick, and unreachable from the start state with
  ``anticomintern`` counterfactually unset. (b) holds by construction of the guard written
  from the 1941 record; the hypothesis gate is a third condition the claim does not name.

Engine: the bounded checker from the snapshot state (models/ww2/bounded.py). <<JPN>>
eventually war is decided by fixed strategies (decisions E6): forced when Japan playing
"occupy the south, then attack" leaves no play without war; not forced when the other
actors, fixed to "end the run in Europe or wait" (:data:`BLOCK`), keep the peace whatever
Japan does; otherwise undecided.
"""

import itertools

import pytest

from models.ww2 import bounded
from models.ww2.hypotheses import REALIZED_MOVES_V1, SNAPSHOTS_V1, realized_moves, snapshot_state
from models.ww2.v1 import model
from wavefront.model import V

CLAIM = {
    "id": "T7",
    "from_state": "1941Q3",
    "claim": (
        "the embargo makes war with Japan unavoidable within 8 ticks unless the "
        "embargo is lifted or `aims[JPN] = status_quo`"
    ),
    "expected": (
        "minimal assumption set for `war[JPN][USA]` is exactly {embargo maintained, "
        "`aims[JPN] ≠ status_quo`}; `strike_north` reachable only with GER-JPN pact "
        "and western USSR collapsing"
    ),
    "sources": "Ike 1967; Sagan 1988; Iriye 1987; Kershaw",
}

START = "1941Q2"  # the state at the start of 1941Q3 (tick 22)
PEACE_AT_30 = (V.tick == 30) & (V.pacific_war == "peace")
WAR = V.pacific_war >= "war"
GATES = {
    "JPN.attack_south:hypothesis",
    "JPN.strike_colonies_only:hypothesis",
    "JPN.occupy_south_indochina:hypothesis",
}
JPN_ATTACK = {"JPN": ["occupy_south_indochina", "attack_south"]}
BLOCK = {"GER": [], "WEST": ["negotiate"], "USSR": [], "Nature": []}


def start(cm, aims_JPN, **counterfactual):
    s = list(
        snapshot_state(
            cm, START, "hegemonic", builtins=True, snapshots=SNAPSHOTS_V1, aims_JPN=aims_JPN
        )
    )
    for name, level in counterfactual.items():
        i = cm.index[name]
        s[i] = cm.variables[i].levels.index(str(level))
    return tuple(s)


def embargo(enc):
    return bounded.fix(enc, 0, "WEST", "embargo_jpn")


@pytest.mark.slow
@pytest.mark.parametrize("aims_JPN", ["regional", "hegemonic"])
def test_T07_war_unavoidable_under_the_embargo(aims_JPN):
    """First half, as registered: under embargo_maintained, no play keeps peace through
    tick 30 (the witness is printed if there is one)."""
    cm = model.compile(profile="embargo_maintained")
    trace = bounded.reach_from(cm, start(cm, aims_JPN), 8, PEACE_AT_30, constrain=embargo)
    if trace is not None:
        print(f"\nT7 ({aims_JPN}): peace at tick 30 is reachable as is:")
        print(trace.render(cm))
    assert trace is None


@pytest.mark.slow
@pytest.mark.parametrize("aims_JPN", ["regional", "hegemonic"])
def test_T07_minimal_assumption_set(aims_JPN):
    """The minimal relaxation sets that make peace at tick 30 reachable, and their minimal
    hitting sets; the registered expectation is a single hitting set,
    {embargo_maintained, the hypothesis gates}."""
    cm = model.compile(profile="embargo_maintained")
    res = bounded.relax_from(
        cm, start(cm, aims_JPN), 8, PEACE_AT_30, max_relax=3, constrain=embargo
    )
    sets = [frozenset(s) for s in res.minimal_sets]
    hitting = minimal_hitting_sets(sets)
    print(
        f"\nT7 ({aims_JPN}): reachable as is {res.reachable_as_is}; minimal relaxation sets "
        f"{res.minimal_sets}; minimal hitting sets {[sorted(h) for h in hitting]}"
    )
    assert not res.reachable_as_is
    assert len(hitting) == 1
    (only,) = hitting
    assert "embargo_maintained" in only and only - {"embargo_maintained"} <= GATES


def minimal_hitting_sets(sets):
    """The inclusion-minimal sets meeting every set in ``sets`` (none when ``sets`` holds
    the empty set, i.e. when the target is reachable with nothing relaxed)."""
    if not sets or frozenset() in sets:
        return []
    universe = sorted(set().union(*sets))
    found = []
    for size in range(1, len(universe) + 1):
        for combo in itertools.combinations(universe, size):
            c = frozenset(combo)
            if all(c & s for s in sets) and not any(f <= c for f in found):
                found.append(c)
    return found


def held_off_path(cm, s):
    """The realized moves from tick 22 with Japan idle after its realized move of tick 22
    and Nature's or another actor's realized move replaced by its built-in action when it is
    not available; WEST never lifts the embargo (it does not in the record)."""
    moves = realized_moves(cm, REALIZED_MOVES_V1)
    states = [s]
    for t in range(22, 39):
        cur = states[-1]
        if cm.is_terminal(cur):
            break
        avail = cm.available(cur)
        move = []
        for a, j, acts in zip(cm.actors, moves[t], avail, strict=True):
            if a.name == "JPN" and t > 22:
                j = 0
            move.append(j if j in acts else acts[0])
        states.append(cm.step(cur, tuple(move)))
    return states


def japans_option(cm, s):
    forced, _ = bounded.forces(cm, s, WAR, JPN_ATTACK)
    if forced:
        return "yes"
    kept, _ = bounded.blocks(cm, s, WAR, BLOCK)
    return "no" if kept else "undecided"


@pytest.mark.slow
@pytest.mark.parametrize("profile", ["embargo_maintained", None])
@pytest.mark.parametrize("aims_JPN", ["status_quo", "regional", "hegemonic"])
def test_T07_japans_option_and_the_clock(aims_JPN, profile):
    """Reported (E5): <<JPN>> eventually war at each tick from 22 to 31 along the held-off
    path, and the first tick on it at which attack_south is unavailable because oil_JPN is
    critical. Asserted only what the reading makes structural: under status_quo Japan never
    has the option."""
    cm = model.compile(profile=profile)
    states = held_off_path(cm, start(cm, aims_JPN))
    jpn = next(a for a in cm.actors if a.name == "JPN")
    attack = jpn.action_index("attack_south")
    option = {}
    closed = None
    for st in states:
        t = st[cm.index["tick"]]
        if t > 31:
            break
        option[t] = japans_option(cm, st)
        if closed is None and cm.state_dict(st)["oil_JPN"] == "critical":
            if cm.is_terminal(st) or attack not in cm.available(st)[jpn.index]:
                closed = t
    print(
        f"\nT7 ({aims_JPN}, profile {profile}): <<JPN>> war by tick {option}; attack_south "
        f"closed by the oil clock at tick {closed}"
    )
    if aims_JPN == "status_quo":
        assert set(option.values()) <= {"no", "undecided"}


@pytest.mark.slow
def test_T07_strike_north_needs_the_pact_and_the_collapse():
    """Second half: (a) reachable under hegemonic aims; (b) unreachable with w_ussr german
    excluded at every tick, and unreachable with anticomintern counterfactually unset."""
    cm = model.compile()
    s = start(cm, "hegemonic")
    k = cm.horizon - 22
    target = V.north_strike
    a = bounded.reach_from(cm, s, k, target)
    assert a is not None
    print("\nT7 (a) strike_north witness:\n" + a.render(cm))
    no_collapse = bounded.reach_from(
        cm, s, k, target, constrain=bounded.avoid(V.w_ussr == "german")
    )
    assert no_collapse is None
    no_pact = bounded.reach_from(cm, start(cm, "hegemonic", anticomintern=False), k, target)
    if no_pact is not None:
        print("T7 (b) with anticomintern unset at tick 22:\n" + no_pact.render(cm))
    assert no_pact is None


@pytest.mark.slow
def test_T07_strike_north_guard_and_gate():
    """The guard written from the 1941 record: the pact and the collapse are parts of
    strike_north, with the hypothesis gate as a third condition the claim does not name;
    under regional aims the strike is unreachable (the gate)."""
    cm = model.compile()
    jpn = next(a for a in cm.actors if a.name == "JPN")
    x = jpn.actions[jpn.action_index("strike_north")]
    assert [p for p, _ in x.guard_parts] == ["hypothesis", "pact", "ussr_collapsing"]
    s = start(cm, "regional")
    assert bounded.reach_from(cm, s, cm.horizon - 22, V.north_strike) is None
