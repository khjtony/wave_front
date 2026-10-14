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
        "the quarter at which the state leaves V for `NO_GENERAL_WAR` falls inside the "
        "window, and the report names the driving variable"
    ),
    "expected": "departure inside 1936Q1 to 1939Q3; stable within 2 quarters under refinement",
    "sources": "the Rhineland, Munich and Prague readings",
}

WINDOW = range(0, 15)  # ticks 0 (1936Q1) to 14 (1939Q3)
NO_GENERAL_WAR = (V.war_west_ger == "peace") & (V.poland == "independent")
FILES = [f"{y}Q{q}" for y in range(1936, 1940) for q in range(1, 5)][:14]  # to 1939Q2
FILES = ["1935Q4", *FILES]  # start of 1936Q1 to start of 1939Q3
KEEP_PEACE = {"WEST": ["concede", "guarantee_poland", "rearm"]}
TAKE_POLAND = {"GER": ["attack_poland", "rearm"]}


@pytest.fixture(scope="module")
def v0_kernel():
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
    """The first tick whose state is outside V, given (tick, membership) pairs in order;
    None if every state is inside or a membership is undecided before any is outside."""
    for tick, m in memberships:
        if m == "out":
            return tick
        if m == "undecided":
            return None
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


@pytest.mark.parametrize("aims", ["revisionist", "hegemonic"])
def test_T13_v0_departure_inside_the_window(v0_kernel, aims):
    """Primary (v0, symbolic): the realized path's departure from V and the driving
    variable; the snapshot files (with built-ins) printed beside it. Under revisionist aims
    the path may never leave V (no German attack on Poland in the hypothesis), which is
    printed; the registered window is asserted for the hypothesis under which the path leaves
    V."""
    cm, res = v0_kernel
    path = v0_path(cm, aims)
    seen = [(s[cm.index["tick"]], "in" if res.contains(s) else "out") for s in path[:15]]
    files = {q: res.contains(snapshot_state(cm, q, aims, builtins=True)) for q in FILES}
    t = departure(seen)
    drivers = sensitivity(cm, res, path[t]) if t is not None else []
    print(
        f"\nT13 v0 ({aims}): realized path {seen}; departure tick {t}; driving variables "
        f"{drivers}; snapshot files in V {files}"
    )
    if aims == "hegemonic":
        assert t is not None and t in WINDOW
        assert drivers


def v1_membership(cm, s):
    k = 21 - s[cm.index["tick"]]
    if k <= 0:
        return "in"
    broken = ~V.invariant("european_peace_t20")
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
    realized path for european_peace_t20, against v0's departure; asserted within two
    quarters when both depart."""
    cm0, res = v0_kernel
    seen0 = [(s[cm0.index["tick"]], "in" if res.contains(s) else "out") for s in v0_path(cm0, aims)]
    t0 = departure(seen0[:15])
    cm, path = v1_path(aims)
    seen = []
    for s in path[:15]:
        m = v1_membership(cm, s)
        seen.append((s[cm.index["tick"]], m))
        if m != "in":
            break
    t1 = departure(seen)
    files = {}
    plain = v1_model.compile()
    for q in FILES:
        s = snapshot_state(
            plain, q, aims, builtins=True, snapshots=SNAPSHOTS_V1, aims_JPN="hegemonic"
        )
        files[q] = v1_membership(plain, s)
        if files[q] != "in":
            break
    print(
        f"\nT13 v1 ({aims}): realized path {seen}; departure tick {t1} (v0: {t0}); "
        f"snapshot files {files}"
    )
    if t0 is not None or t1 is not None:
        assert t0 is not None and t1 is not None and abs(t1 - t0) <= 2
