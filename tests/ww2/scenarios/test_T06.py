"""T6: Germany cannot force the 1941 campaign; V_GER exit falls in 1941Q4 to 1943Q1.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.

Reading (docs/ww2_v1_decisions.md E5, T6), on models/ww2/v1.py from the start of 1941Q2
(``1941Q1.json`` with its built-ins, tick 21), ``aims_GER = hegemonic``, ``aims_USSR =
defensive``, ``aims_JPN`` swept:

- X := ``w_ussr == german and caucasus == german``. "Germany cannot force": not
  <<GER>> eventually X (standard notion: every other actor, Nature included, is the
  adversary), with the fortune table. "Contested for the 1941 campaign": the standard
  contested region of ``contested(kind='reach')`` for {GER} and X (not forced by {GER} and
  not blocked by the rest), as E5 asserts it, with the fortune variant reported.
- V_GER := ``safe({GER}, undefeated)``, ``undefeated := reich == fighting and not
  german_defeat`` (keeping it through the horizon is reaching a non-defeat ending).
- "The quarter at which V_GER is left": the point of no return t_K along the realized path
  from tick 21 (the first realized state outside V_GER), with the loss point and the
  visible-failure tick, and the driving variable from a sensitivity sweep (each declared
  variable moved one level in the state before t_K, the realized move replayed, membership
  of the successor rechecked). Window: 1941Q4 to 1943Q1 inclusive (ticks 23 to 28).
  Computed without a WEST profile; ``electoral`` is a sensitivity run.

Engine (decisions E6): the symbolic engine does not fit v1 (reports/ww2_v1.md, methods), so
kernel membership is decided by fixed strategies with the bounded checker
(models/ww2/bounded.py): inside V_GER when GER playing ``idle`` throughout keeps
``undefeated`` against every play of the others (sufficiency); outside when the others,
fixed to the collapse strategy :data:`COLLAPSE`, leave GER no play that keeps it
(refutation). A state settled by neither is "undecided" and reported so. Every result is
"by fixed strategy", never the kernel itself.
"""

import pytest

from models.ww2 import bounded
from models.ww2.hypotheses import REALIZED_MOVES_V1, SNAPSHOTS_V1, realized_moves, snapshot_state
from models.ww2.v1 import model
from wavefront.model import V

CLAIM = {
    "id": "T6",
    "from_state": "1941Q2",
    "claim": (
        "Germany cannot force control of western USSR plus the Caucasus; the quarter "
        "at which V_GER is left falls between 1941Q4 and 1943Q1"
    ),
    "expected": (
        "`contested` for the 1941 campaign; point of no return inside the window, with "
        "the driving variable named"
    ),
    "sources": "Tooze; Overy; Kershaw",
}

START = "1941Q1"  # the state at the start of 1941Q2 (tick 21)
WINDOW = range(23, 29)  # 1941Q4 to 1943Q1
X = (V.w_ussr == "german") & (V.caucasus == "german")
DEFEATED = ~V.invariant("undefeated")
IDLE = {"GER": []}
NOTHING = {"WEST": [], "USSR": [], "JPN": [], "Nature": []}
# The adversaries' collapse strategy for the refutation of V_GER membership.
COLLAPSE = {
    "WEST": ["us_declare_war", "victory_program", "bomber_offensive", "land_france"],
    "USSR": ["mobilize_total", "counteroffensive"],
    "JPN": ["occupy_south_indochina", "attack_south"],
    "Nature": [
        "reich_collapses",
        "campaign_france",
        "german_exhaustion",
        "air_war_won",
        "german_strain",
        "east_liberated",
    ],
}
# Germany with fortune: attack, take western USSR, then the Caucasus; Nature resolves for
# Germany and takes Italy out of the war (which removes the West's second front).
GER_PUSH = {
    "GER": ["attack_ussr", "offensive_caucasus", "offensive_east"],
    "Nature": ["campaign_east_german", "campaign_caucasus_german", "italy_capitulates"],
}
# The other principals keeping a second front open against Germany with fortune.
SECOND_FRONT = {
    "WEST": ["us_declare_war", "invade_italy", "land_france"],
    "USSR": [],
    "JPN": [],
}


def start(cm, aims_JPN):
    return snapshot_state(
        cm, START, "hegemonic", builtins=True, snapshots=SNAPSHOTS_V1, aims_JPN=aims_JPN
    )


def membership(cm, s):
    """ "in", "out" or "undecided" for V_GER, by the two fixed strategies."""
    inside, _ = bounded.blocks(cm, s, DEFEATED, IDLE)
    if inside:
        return "in"
    outside, _ = bounded.forces(cm, s, DEFEATED, COLLAPSE)
    return "out" if outside else "undecided"


def realized_path(cm, s):
    """The realized states from ``s`` (tick 21) while the realized moves are available."""
    moves = realized_moves(cm, REALIZED_MOVES_V1)
    states = [s]
    for move in moves[21:]:
        cur = states[-1]
        if cm.is_terminal(cur):
            break
        avail = cm.available(cur)
        if any(j not in a for j, a in zip(move, avail, strict=True)):
            break
        states.append(cm.step(cur, move))
    return states


def point_of_no_return(cm, states):
    """(t_K, memberships): the first state outside V_GER along ``states``."""
    seen = []
    for s in states:
        m = membership(cm, s)
        seen.append((s[cm.index["tick"]], m))
        if m == "out":
            return s[cm.index["tick"]], seen
        if m == "undecided":
            return None, seen
    return None, seen


@pytest.mark.slow
@pytest.mark.parametrize("aims_JPN", ["status_quo", "regional", "hegemonic"])
def test_T06_germany_cannot_force_the_campaign(aims_JPN):
    """Standard notion: the rest (every other actor, Nature included) keeps X false
    whatever Germany does, so {GER} cannot force X; and E5's contested region, which is
    asserted as registered (contested: not forced and not blocked). The fortune table is
    printed."""
    cm = model.compile()
    s = start(cm, aims_JPN)
    blocked, play = bounded.blocks(cm, s, X, NOTHING)
    fortune_forced, _ = bounded.forces(cm, s, X, GER_PUSH)
    others_block, _ = bounded.blocks(cm, s, X, SECOND_FRONT)
    table = {
        "GER with fortune forces X": "yes"
        if fortune_forced
        else ("no" if others_block else "undecided"),
        "rest with fortune keeps not-X": "yes" if blocked else "undecided",
    }
    region = "blocked" if blocked else "undecided"
    print(f"\nT6 ({aims_JPN}): standard region {region}; fortune table {table}")
    assert blocked, play.render(cm) if play else None  # Germany cannot force X
    assert region == "contested"  # E5: the standard contested region, as registered


@pytest.mark.slow
@pytest.mark.parametrize("profile", [None, "electoral"])
@pytest.mark.parametrize("aims_JPN", ["status_quo", "regional", "hegemonic"])
def test_T06_point_of_no_return_in_the_window(aims_JPN, profile):
    """t_K along the realized path from tick 21, with the visible-failure tick; asserted
    inside the window (ticks 23 to 28) for the run without a profile, as registered; the
    ``electoral`` run is a sensitivity run (printed, not asserted)."""
    cm = model.compile(profile=profile)
    states = realized_path(cm, start(cm, aims_JPN))
    t_k, seen = point_of_no_return(cm, states)
    visible = next((s[cm.index["tick"]] for s in states if not cm.evaluate("undefeated", s)), None)
    print(
        f"\nT6 ({aims_JPN}, profile {profile}): memberships {seen}; t_K {t_k}; "
        f"realized path to tick {states[-1][cm.index['tick']]}; visible failure {visible}"
    )
    if profile is None:
        assert t_k is not None and t_k in WINDOW


def perturbations(cm, s):
    """One-level moves of each declared variable of ``s`` (tick and built-ins excepted)."""
    for i, v in enumerate(cm.variables):
        if v.origin != "var":
            continue
        for d in (-1, 1):
            if 0 <= s[i] + d < v.size:
                t = list(s)
                t[i] += d
                yield v.name, cm.level_name(i, t[i]), tuple(t)


@pytest.mark.slow
def test_T06_driving_variable():
    """Sensitivity at t_K (aims_JPN hegemonic, no profile): every declared variable moved
    one level in the realized state before t_K, the realized move of that tick replayed
    when it is still available, and the successor's V_GER membership rechecked. The
    variables whose move restores membership (or makes the realized move unavailable) are
    the driving variables; the test asserts that one exists and prints them."""
    cm = model.compile()
    states = realized_path(cm, start(cm, "hegemonic"))
    t_k, _ = point_of_no_return(cm, states)
    assert t_k is not None
    before = states[t_k - 21 - 1]
    move = realized_moves(cm, REALIZED_MOVES_V1)[t_k - 1]
    rows = []
    for name, level, p in perturbations(cm, before):
        avail = cm.available(p) if not cm.is_terminal(p) else None
        if avail is None or any(j not in a for j, a in zip(move, avail, strict=True)):
            rows.append((name, level, "realized move unavailable"))
            continue
        nxt = cm.step(p, move)
        inside, _ = bounded.blocks(cm, nxt, DEFEATED, IDLE)
        if inside:
            rows.append((name, level, "restores membership"))
    print(f"\nT6 driving variables at the state before t_K = {t_k}: {rows}")
    assert rows
