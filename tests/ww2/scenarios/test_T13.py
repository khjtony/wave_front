"""T13: The state leaves V for `NO_GENERAL_WAR` inside 1936Q1 to 1939Q3.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.

Reading (docs/ww2_v1_decisions.md E5, T13):

- Primary, as registered, on **v0** (models/ww2/v0.py) with the symbolic engine: V :=
  ``safe({WEST}, no_general_war)`` with ``no_general_war := war_west_ger == peace and poland
  == independent`` (v0's NO_GENERAL_WAR kept through the horizon, tick 20; both conjuncts
  are monotone, so the ending at tick 20 is the invariant through tick 20). The quarter at
  which the realized path leaves V (the first replayed state of data/ww2/realized_moves.csv
  outside V, under each aims_GER), and the driving variable from a sensitivity sweep at that
  state (each variable, built-ins included, moved one level; membership looked up in the
  kernel, which the symbolic engine computes over the whole state domain).
- Refinement check on **v1**: the same question with ``european_peace := peace_europe and
  poland == independent`` through tick 20 (the invariant ``european_peace_t20``), along the
  v1 realized path. The claim's "stable within 2 quarters under refinement" is the v0-to-v1
  comparison of the departure quarters. On v1 the symbolic engine does not fit (the report's
  methods), so membership is decided by fixed strategies with the bounded checker (decisions
  E6): inside when WEST playing "concede when asked, respond, never declare"
  (:data:`KEEP_PEACE`) keeps the predicate against every play; outside when Germany playing
  "rearm, take Poland" (:data:`TAKE_POLAND`) breaks it against every play; otherwise
  undecided. The per-quarter memberships of the hindsight snapshots (with their built-ins)
  are printed beside the realized path's.
- Window: 1936Q1 (tick 0) to 1939Q3 (tick 14) inclusive.
"""

import pytest

from models.ww2 import bounded
from models.ww2.hypotheses import (
    REALIZED_MOVES_V1,
    SNAPSHOTS_V1,
    fixed_model,
    realized_moves,
    snapshot_state,
)
from models.ww2.v0 import model as v0_model
from models.ww2.v1 import model as v1_model
from wavefront.model import V
from wavefront.symbolic import encode, safe

CLAIM = {
    "id": "T13",
    "from_state": "each quarter 1936Q1 to 1939Q3",
    "claim": (
        "the quarter whose decisions leave V_WEST for `balance_europe` (the last quarter "
        "at which the realized state is inside the kernel, followed by a state outside "
        "it) falls inside the window, and the report names the driving variable"
    ),
    "expected": (
        "departure inside 1936Q1 to 1939Q3; stable within 2 quarters under refinement; "
        "recorded (symbolic engine, v0): 1936Q2 under hegemonic aims (the quarter in "
        "which the Rhineland was not resisted) and 1939Q3 under revisionist aims (the "
        "attack on Poland); the registered predicate `NO_GENERAL_WAR`, which forbids the "
        "West's own war, gave an empty kernel from 1936Q1 under hegemonic aims and is "
        "retired for this test"
    ),
    "sources": "the Rhineland, Munich and Prague readings; amended 2026-10-15",
}

WINDOW = range(0, 15)  # ticks 0 (1936Q1) to 14 (1939Q3)
# Amended 2026-10-15: V is WEST's kernel for balance_europe; the retired predicate is kept
# for the recorded degenerate result.
NO_GENERAL_WAR = (V.war_west_ger == "peace") & (V.poland == "independent")
FILES = [f"{y}Q{q}" for y in range(1936, 1940) for q in range(1, 5)][:14]  # to 1939Q2
FILES = ["1935Q4", *FILES]  # start of 1936Q1 to start of 1939Q3
KEEP_PEACE = {"WEST": ["concede", "guarantee_poland", "rearm"]}
TAKE_POLAND = {"GER": ["attack_poland", "rearm"]}


@pytest.fixture(scope="module")
def v0_kernel():
    """WEST's kernel for balance_europe over the whole v0 state space (about a minute)."""
    cm = v0_model.compile()
    enc = encode(cm)
    res = safe(enc, ["WEST"], enc.predicate("balance_europe"))
    return cm, res


@pytest.fixture(scope="module")
def v0_kernel_retired():
    """The retired predicate (no war with Germany and Poland independent), kept for the
    recorded degenerate result."""
    cm = v0_model.compile()
    enc = encode(cm)
    res = safe(enc, ["WEST"], enc.predicate(NO_GENERAL_WAR))
    return cm, res


def v0_path(cm, aims):
    s = snapshot_state(cm, "1935Q4", aims)
    out = [s]
    for move in realized_moves(cm):
        if cm.is_terminal(s):
            break
        if any(j not in a for j, a in zip(move, cm.available(s), strict=True)):
            break
        s = cm.step(s, move)
        out.append(s)
    return out


def departure(memberships):
    """The quarter whose decisions leave V (amended 2026-10-15): the last tick whose state
    is inside V and whose successor state is outside, given (tick, membership) pairs in
    order; None if no state is inside before the first outside one, if every state is
    inside, or if a membership is undecided before the departure."""
    prev = None
    for tick, m in memberships:
        if m == "undecided":
            return None
        if m == "out" and prev is not None and prev[1] == "in":
            return prev[0]
        prev = (tick, m)
    return None


def sensitivity(cm, res, state):
    """Each variable moved one level in ``state``: the moves that put it inside V."""
    rows = []
    for i, v in enumerate(cm.variables):
        if v.name == "tick":
            continue
        for d in (-1, 1):
            if 0 <= state[i] + d < v.size:
                t = list(state)
                t[i] += d
                if res.contains(tuple(t)):
                    rows.append((v.name, cm.level_name(i, t[i])))
    return rows


@pytest.mark.slow
@pytest.mark.parametrize("aims", ["revisionist", "hegemonic"])
def test_T13_v0_departure_inside_the_window(v0_kernel, aims):
    """Primary (v0, symbolic, amended 2026-10-15): the quarter whose decisions leave
    WEST's kernel for balance_europe along the realized path (the hindsight snapshot states
    with their built-ins), and the driving variable at the first state outside. Recorded:
    1936Q2 (tick 1) under hegemonic aims, 1939Q3 (tick 14) under revisionist aims. The
    realized path is read from the snapshot files because the model's own replay carries
    the built-ins only from tick 1 on."""
    cm, res = v0_kernel
    states = [(q, snapshot_state(cm, q, aims, builtins=True)) for q in [*FILES, "1939Q3"]]
    seen = [(st[cm.index["tick"]], "in" if res.contains(st) else "out") for _, st in states]
    t = departure(seen)
    first_out = None
    if t is not None:
        first_out = next((st for _, st in states if st[cm.index["tick"]] == t + 1), None)
    drivers = sensitivity(cm, res, first_out) if first_out is not None else []
    path = v0_path(cm, aims)
    replay = [(s[cm.index["tick"]], "in" if res.contains(s) else "out") for s in path[:16]]
    print(
        f"\nT13 v0 ({aims}): snapshot states {seen}; departure quarter tick {t}; driving "
        f"variables at the first state outside {drivers}; the model's own replay {replay}"
    )
    assert t is not None and t in WINDOW
    assert t == {"hegemonic": 1, "revisionist": 14}[aims]
    assert drivers


@pytest.mark.slow
@pytest.mark.parametrize("aims", ["revisionist", "hegemonic"])
def test_T13_retired_predicate_recorded(v0_kernel_retired, aims):
    """Recorded: under the retired predicate (no war with Germany and Poland independent),
    which forbids the West's own war, the kernel is empty along the path from 1936Q1 under
    hegemonic aims and never left under revisionist aims (reports/ww2_v1.md section 11)."""
    cm, res = v0_kernel_retired
    path = v0_path(cm, aims)
    seen = ["in" if res.contains(s) else "out" for s in path[:15]]
    if aims == "hegemonic":
        assert set(seen) == {"out"}
    else:
        assert set(seen) == {"in"}


def v1_membership(cm, s):
    """Membership of WEST's kernel for balance_europe through tick 20 on v1, by fixed
    strategies (amended 2026-10-15; before it, the European-peace predicate)."""
    k = 21 - s[cm.index["tick"]]
    if k <= 0:
        return "in"
    broken = ~V.invariant("balance_europe") & (V.tick <= 20)
    inside, _ = bounded.blocks(cm, s, broken, KEEP_PEACE, k=k)
    if inside:
        return "in"
    outside, _ = bounded.forces(cm, s, broken, TAKE_POLAND, k=k)
    return "out" if outside else "undecided"


def v1_path(aims):
    cm = fixed_model(v1_model, aims_GER=aims, aims_JPN="hegemonic").compile()
    (s,) = cm.initial_states()
    out = [s]
    for move in realized_moves(cm, REALIZED_MOVES_V1)[:15]:
        s = cm.step(s, move)
        out.append(s)
    return cm, out


@pytest.mark.slow
@pytest.mark.parametrize("aims", ["revisionist", "hegemonic"])
def test_T13_v1_refinement_is_stable_within_two_quarters(v0_kernel, aims):
    """Refinement (v1, bounded checker with fixed strategies): the departure along the v1
    snapshot states for balance_europe through tick 20, against v0's departure from the
    v0 snapshot states; asserted within two quarters when both depart."""
    cm0, res = v0_kernel
    seen0 = [
        (st[cm0.index["tick"]], "in" if res.contains(st) else "out")
        for st in (snapshot_state(cm0, q, aims, builtins=True) for q in [*FILES, "1939Q3"])
    ]
    t0 = departure(seen0)
    plain = v1_model.compile()
    seen = []
    for q in [*FILES, "1939Q3"]:
        st = snapshot_state(
            plain, q, aims, builtins=True, snapshots=SNAPSHOTS_V1, aims_JPN="hegemonic"
        )
        m = v1_membership(plain, st)
        seen.append((st[plain.index["tick"]], m))
        if m == "out" and len(seen) > 1 and seen[-2][1] == "in":
            break
    t1 = departure(seen)
    cm, path = v1_path(aims)
    replay = [(s[cm.index["tick"]], v1_membership(cm, s)) for s in path[:3]]
    print(
        f"\nT13 v1 ({aims}): snapshot states {seen}; departure quarter tick {t1} (v0: {t0}); "
        f"the model's own replay, first ticks: {replay}"
    )
    assert t0 is not None and t1 is not None and abs(t1 - t0) <= 2
