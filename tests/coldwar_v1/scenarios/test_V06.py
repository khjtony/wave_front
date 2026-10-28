"""V6: The missile gap on cw_v1 (C6 as amended).

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V6a. The readings the model step must fix before first sight are listed in
section 9.4.

Amended 2026-10-28 before first sight on the owner's decision 7g (section 8 of the
registration): the comparison is with the hindsight ``count_USSR``, the number of Soviet
intercontinental delivery vehicles in bands, on which ``belief_force_USA`` is the projected
number (docs/cw_v1_decisions.md D9).

Reading (docs/cw_v1_decisions.md, R V6): as v0's A C6, on cw_v1 with ``snapshots/cw_v1/``.
(a) The replayed ``belief_force_USA`` exceeds the hindsight ``count_USSR`` in every year 1958
to 1961 (1957 and 1962 reported). (b) For each year of (a), per hypothesis, from the replay
state and from the hindsight state, on the flattened game cut at tick 16 (1 January 1963; the
Cuba sub-game inside and active) by the layered lifting in its explicit form (the coarse game
explored explicitly to 1962, the states of 1962 valued one step ahead with the Cuba sub-game
explored once and lifted, exact because its entry map is constant): the fewest transitions to
``GENERAL_WAR`` and to ``ACCIDENTAL_WAR``, and the distance out of {USA}'s and out of
{USSR}'s kernel of ``no_general_war`` (avoiding both) kept to the cut, the cut states kept iff
``no_general_war`` (0 when outside; unreachable or never left is infinite). (b) holds iff in
every year at least one measure is smaller from the replay state and none is smaller from the
hindsight state; a year whose explicit part exceeds 6,000,000 states is undecided and fails
(b). (c) Y_o, the first replay year with ``intel_USA = overhead``, and Y_c, the first year
from Y_o whose replayed belief does not exceed the hindsight ``count_USSR``: Y_c - Y_o <= 1.
Control (the analysis hold): from the 1960 replay state with ``intel_USA = partial`` and
``pending_USA_corona = 0``, the realized coarse moves of 1960 and 1961 are stepped with
``USA.corona`` replaced by idle and Nature's ``estimate_revised`` by ``none``; the
``belief_force_USA`` of 1 January 1962 exceeds the hindsight ``count_USSR`` of 1962. Holds iff
(a), (b), (c) and the control under at least one hypothesis. Hold-out: total.
"""

import os

import pytest

from models.cw import v1
from models.ww2.hypotheses import realized_moves
from tests.coldwar.common import level, with_level
from wavefront.engine import BudgetExceeded

from ..common import (
    ADVERSE,
    HYPS,
    Timer,
    compare,
    compiled,
    hindsight,
    lift_of,
    replay_state,
)
from ..layered import Window

CLAIM = {
    "id": "V6",
    "from_state": "1957 to 1961, annual replay",
    "claim": (
        "on cw_v1, C6 as amended 2026-10-23, its comparison amended 2026-10-28 before first "
        "sight on the owner's decision 7g: the replayed `belief[USA][USSR].force` from dated "
        "estimates and press (the projected number of Soviet intercontinental delivery "
        "vehicles, in bands) exceeds the hindsight `count[USSR]` (the number in being, on the "
        "same bands); analysis from the "
        "replay snapshot shows more adversarial reachability than from the hindsight "
        "snapshot, measured on reachability and on the unilateral kernels: of the shortest "
        "traces to `GENERAL_WAR` and to `ACCIDENTAL_WAR` by 1963 and the distances out of "
        "`⟨⟨USA⟩⟩` and `⟨⟨USSR⟩⟩` kernels of avoiding both by 1963, at least one puts the "
        "replay state nearer the adverse endings and none puts it farther, in every year of "
        "the gap; the gap closes within one year of `intel[USA] = overhead_reconnaissance` "
        "(1960 to 1961); control: with `intel[USA]` held at `partial` from 1960 (an analysis "
        "hold outside the assumption set), the replayed belief still exceeds the hindsight "
        "`count[USSR]` on 1 January 1962"
    ),
    "expected": (
        "as stated; the manual replay until the blind NIE replay runs, then both (decision 3c)"
    ),
    "sources": (
        "the NIE series (CIA CREST); Gaddis 2005; Preble 2004; Norris and Cochran 1990 (the "
        "count); re-asks C6 as amended"
    ),
}

# The first-sight switch (docs/cw_v1_decisions.md D8): the claim runs only when the owner sets
# WF_FIRST_SIGHT_CWV1=1 for the one recorded run of V1 to V10.
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_CWV1") == "1"

YEARS = range(1957, 1963)
GAP = range(1958, 1962)
CUT = 16  # 1 January 1963
BANDS = v1.BANDS  # the projected and the hindsight count share these (decision 7g)


def exceeds(cm, belief_state, force_state) -> bool:
    b = level(cm, belief_state, "belief_force_USA")
    f = level(cm, force_state, "count_USSR")
    return BANDS.index(b) > BANDS.index(f)


def measures(aims, state):
    """The four distances of (b) from ``state`` on the flattened game cut at 1963 (explicit
    form of the layered lifting), or None if the explicit part exceeds the budget."""
    cm = compiled(aims)
    try:
        w = Window(lift_of(aims), [state], CUT)
    except BudgetExceeded:
        return None, None
    out = {}
    for e in ADVERSE:
        out[e] = w.distance(state, lambda r, e=e: cm.ending_of(r) == e)

    def phi(r):
        return bool(cm.evaluate("no_general_war", r))

    for side in ("USA", "USSR"):
        k = w.kernel((side,), phi)
        out[f"K_{side}"] = w.distance(state, phi, kernel=k, coalition=(side,))
    return out, w.g.size()


def control(aims):
    """The analysis hold: overhead coverage withheld from 1960."""
    cm = compiled(aims)
    s = replay_state(1960, aims)
    s = with_level(cm, s, "intel_USA", "partial")
    s = with_level(cm, s, "pending_USA_corona", 0)
    usa = next(a for a in cm.actors if a.name == "USA")
    nature = next(a for a in cm.actors if a.name == "Nature")
    corona, revised = usa.action_index("corona"), nature.action_index("estimate_revised")
    moves = realized_moves(cm, v1.REALIZED_MOVES)
    notes = []
    for year in (1960, 1961):
        move = list(moves[year - v1.YEAR0])
        if move[usa.index] == corona:
            move[usa.index] = usa.action_index("idle")
        if move[nature.index] == revised:
            move[nature.index] = nature.action_index("none")
        av = cm.available(s)
        missing = [
            f"{a.name}.{a.actions[j].name}"
            for a, j, acts in zip(cm.actors, move, av, strict=True)
            if j not in acts
        ]
        if missing:
            notes.append(f"{year}: unavailable after the hold {missing}")
        s = cm.step(s, tuple(move))
    return exceeds(cm, s, hindsight(1962, aims)), level(cm, s, "belief_force_USA"), notes


@pytest.mark.skipif(not FIRST_SIGHT, reason="cw_v1 first sight not switched on")
def test_V6():
    timer = Timer()
    print("\n[V6] engine: replay against hindsight; explicit form of the layered lifting to 1963")
    results = {}
    for aims in HYPS:
        cm = compiled(aims)
        gap = {}
        for y in YEARS:
            r, h = replay_state(y, aims), hindsight(y, aims)
            gap[y] = exceeds(cm, r, h)
            print(
                f"[V6] aims_USSR={aims} {y}: replayed belief {level(cm, r, 'belief_force_USA')}, "
                f"hindsight count_USSR {level(cm, h, 'count_USSR')}: exceeds {gap[y]}"
            )
        a = all(gap[y] for y in GAP)
        b = True
        for y in GAP:
            mr, nr = measures(aims, replay_state(y, aims))
            mh, nh = measures(aims, hindsight(y, aims))
            if mr is None or mh is None:
                print(f"[V6]   {y}: undecided (explicit part over budget)")
                b = False
                continue
            some, none_back = compare(mr, mh)
            ok = some and none_back
            print(f"[V6]   {y}: replay {mr} ({nr}); hindsight {mh} ({nh}): {ok}")
            b = b and ok
        intel = {y: level(cm, replay_state(y, aims), "intel_USA") for y in YEARS}
        y_o = next((y for y in YEARS if intel[y] == "overhead"), None)
        y_c = next((y for y in YEARS if y_o and y >= y_o and not gap[y]), None)
        c = y_o is not None and y_c is not None and y_c - y_o <= 1
        print(f"[V6]   (c) intel overhead from {y_o}; gap closed in {y_c}: {c}")
        ctrl, belief, notes = control(aims)
        print(
            f"[V6]   control: belief on 1 Jan 1962 with the hold {belief}: exceeds {ctrl} {notes}"
        )
        results[aims] = (a, b, c, ctrl)
        print(f"[V6] aims_USSR={aims}: (a) {a}, (b) {b}, (c) {c}, control {ctrl} ({timer})")
    assert any(all(v) for v in results.values()), results
