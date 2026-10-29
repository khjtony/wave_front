"""V6: The missile gap on cw_v1 (C6 as amended).

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V6a. The readings the model step must fix before first sight are listed in
section 9.4.

Amended 2026-10-28 before first sight on the owner's decision 7g (section 8 of the
registration): the comparison is with the hindsight ``count_USSR``, the number of Soviet
intercontinental delivery vehicles in bands, on which ``belief_force_USA`` is the projected
number (docs/cw_v1_decisions.md D9). Amended again 2026-10-28 before first sight on the
owner's decision 7i: the comparison is with ``count_USSR`` at the date the estimate projects
for, read from the hindsight snapshot of the latest 1 January not after that date.

Input (the owner's decision 7k, R V6): the replay is the blind replay at proposal level, run
at the first-sight commit with ``wf replay --episode cw --years 1957..1962 --corpus
data/cw/corpora/raw/crest --source crest --backend claude --measure-proposals --out DIR``, its
directory given in ``WF_CWV1_BLIND_REPLAY``; V6 is asserted on it, its projected dates by the
rule of 7k (the estimate's date plus 30 months). The manual replay (snapshots/cw_v1/replay) is
computed and printed beside, on the same rule and on its recorded projected dates, and is not
asserted.

Reading (docs/cw_v1_decisions.md, R V6): as v0's A C6, on cw_v1 with ``snapshots/cw_v1/``. (a)
The replayed ``belief_force_USA`` exceeds the hindsight ``count_USSR`` at its projected date in
every year 1958 to 1961 (1957 and 1962 reported). (b) For each year of (a), per hypothesis, from
the replay state and from the hindsight state, on the flattened game cut at tick 16 (1 January
1963; the Cuba sub-game inside and active) by the layered lifting in its explicit form (the
coarse game explored explicitly to 1962, the states of 1962 valued one step ahead with the Cuba
sub-game explored once and lifted, exact because its entry map is constant): the fewest
transitions to ``GENERAL_WAR`` and to ``ACCIDENTAL_WAR``, and the distance out of {USA}'s and
out of {USSR}'s kernel of ``no_general_war`` (avoiding both) kept to the cut, the cut states
kept iff ``no_general_war`` (0 when outside; unreachable or never left is infinite). (b) holds
iff in every year at least one measure is smaller from the replay state and none is smaller from
the hindsight state; a year whose explicit part exceeds 6,000,000 states is undecided and fails
(b). (c) Y_o, the first replay year with ``intel_USA = overhead``, and Y_c, the first year from
Y_o whose replayed belief does not exceed the hindsight ``count_USSR`` at its projected date:
Y_c - Y_o <= 1. Control (the analysis hold): from the 1960 replay state with ``intel_USA =
partial`` and ``pending_USA_corona = 0``, the realized coarse moves of 1960 and 1961 are stepped
with ``USA.corona`` replaced by idle and Nature's ``estimate_revised`` by ``none``; the
``belief_force_USA`` of 1 January 1962 exceeds the hindsight ``count_USSR`` at the projected
date of the same series' replay of 1962. Holds iff (a), (b), (c) and the control under at least
one hypothesis, on the blind series. Hold-out: total.
"""

import json
import os
from pathlib import Path

import pytest

from models.cw import v1
from models.cw.snapshots_v1 import (
    BLIND_REPLAY_ENV,
    SNAPSHOTS,
    blind_snapshots,
    projected_year,
    rule_year,
    snapshot_state,
)
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
)
from ..layered import Window

CLAIM = {
    "id": "V6",
    "from_state": "1957 to 1961, annual replay",
    "claim": (
        "on cw_v1, C6 as amended 2026-10-23, its comparison amended 2026-10-28 before first "
        "sight on the owner's decisions 7g and 7i: the replayed `belief[USA][USSR].force` "
        "from dated estimates and press (the projected number of Soviet intercontinental delivery "
        "vehicles, in bands) exceeds the hindsight `count[USSR]` at the date the estimate "
        "projects (the number in being at that date, about two to three years after the "
        "estimate's own date, as the replay row records it, on the same bands); analysis from the "
        "replay snapshot shows more adversarial reachability than from the hindsight "
        "snapshot, measured on reachability and on the unilateral kernels: of the shortest "
        "traces to `GENERAL_WAR` and to `ACCIDENTAL_WAR` by 1963 and the distances out of "
        "`⟨⟨USA⟩⟩` and `⟨⟨USSR⟩⟩` kernels of avoiding both by 1963, at least one puts the "
        "replay state nearer the adverse endings and none puts it farther, in every year of "
        "the gap; the gap closes within one year of `intel[USA] = overhead_reconnaissance` "
        "(1960 to 1961); control: with `intel[USA]` held at `partial` from 1960 (an analysis "
        "hold outside the assumption set), the replayed belief of 1 January 1962 still exceeds "
        "the hindsight `count[USSR]` at the date it projects"
    ),
    "expected": (
        "as stated; the manual replay until the blind NIE replay runs, then both (decision 3c)"
    ),
    "sources": (
        "the NIE series (CIA CREST); Gaddis 2005; Preble 2004; Norris and Cochran 1990, NRDC "
        "Working Paper 90-1, Table 2 (the count; the 1997 revision not used); re-asks C6 as "
        "amended"
    ),
}

# The first-sight switch (docs/cw_v1_decisions.md D8): the claim runs only when the owner sets
# WF_FIRST_SIGHT_CWV1=1 for the one recorded run of V1 to V10.
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_CWV1") == "1"

YEARS = range(1957, 1963)
GAP = range(1958, 1962)
CUT = 16  # 1 January 1963
BANDS = v1.BANDS  # the projected and the hindsight count share these (decision 7g)


def blind_dir() -> Path:
    """The blind replay directory of decision 7k; fails clearly when it is not given or holds
    no proposals (no fallback to the manual replay)."""
    given = os.environ.get(BLIND_REPLAY_ENV)
    if not given:
        raise RuntimeError(
            f"V6 reads the blind replay (decision 7k): set {BLIND_REPLAY_ENV} to the --out "
            "directory of wf replay --episode cw --years 1957..1962 --measure-proposals"
        )
    path = Path(given)
    if not (path / "proposals").is_dir():
        raise RuntimeError(f"{BLIND_REPLAY_ENV}={given}: no proposals/ in it (decision 7k)")
    return path


def manual_snapshots() -> dict[int, dict]:
    return {
        y: json.loads((SNAPSHOTS / "replay" / f"{y}.json").read_text(encoding="utf-8"))
        for y in YEARS
    }


def read_years(snaps: dict[int, dict], recorded: bool = False) -> dict[int, int]:
    """Per replay year, the hindsight snapshot whose ``count_USSR`` the belief is set against:
    by the rule of decision 7k (the estimate's date plus 30 months), or with ``recorded`` on
    the manual replay's recorded projected date (decision 7i); either way the latest 1 January
    not after the date."""
    if recorded:
        return {y: projected_year(y) for y in snaps}
    return {y: rule_year(y, snaps[y]["variables"]["belief_force_USA"]) for y in snaps}


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


def control(aims, start, read_year):
    """The analysis hold: overhead coverage withheld from 1960, from the series' 1960 state;
    the belief of 1 January 1962 against the count of ``read_year``."""
    cm = compiled(aims)
    s = with_level(cm, start, "intel_USA", "partial")
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
    return exceeds(cm, s, hindsight(read_year, aims)), level(cm, s, "belief_force_USA"), notes


def gap_and_closing(cm, aims, states, reads, tag):
    """(a), (c) and the control of one series on one reading of the projected dates."""
    gap = {}
    for y in YEARS:
        h = hindsight(reads[y], aims)
        gap[y] = exceeds(cm, states[y], h)
        print(
            f"[V6] {tag} aims_USSR={aims} {y}: replayed belief "
            f"{level(cm, states[y], 'belief_force_USA')}, hindsight count_USSR of 1 Jan "
            f"{reads[y]} {level(cm, h, 'count_USSR')}: exceeds {gap[y]}"
        )
    a = all(gap[y] for y in GAP)
    intel = {y: level(cm, states[y], "intel_USA") for y in YEARS}
    y_o = next((y for y in YEARS if intel[y] == "overhead"), None)
    y_c = next((y for y in YEARS if y_o and y >= y_o and not gap[y]), None)
    c = y_o is not None and y_c is not None and y_c - y_o <= 1
    print(f"[V6] {tag}   (c) intel overhead from {y_o}; gap closed in {y_c}: {c}")
    ctrl, belief, notes = control(aims, states[1960], reads[1962])
    print(
        f"[V6] {tag}   control: belief on 1 Jan 1962 with the hold {belief}, against the count "
        f"of 1 Jan {reads[1962]}: exceeds {ctrl} {notes}"
    )
    return a, c, ctrl


def run_series(aims, tag, snaps, readings, hindsight_measures):
    """V6 on one replay series: (b) once, (a), (c) and the control on each reading."""
    cm = compiled(aims)
    states = {y: snapshot_state(cm, y, aims, "replay", snaps[y]) for y in YEARS}
    b = True
    for y in GAP:
        mr, nr = measures(aims, states[y])
        if (aims, y) not in hindsight_measures:
            hindsight_measures[aims, y] = measures(aims, hindsight(y, aims))
        mh, nh = hindsight_measures[aims, y]
        if mr is None or mh is None:
            print(f"[V6] {tag}   {y}: undecided (explicit part over budget)")
            b = False
            continue
        some, none_back = compare(mr, mh)
        ok = some and none_back
        print(f"[V6] {tag}   {y}: replay {mr} ({nr}); hindsight {mh} ({nh}): {ok}")
        b = b and ok
    out = {}
    for name, reads in readings.items():
        a, c, ctrl = gap_and_closing(cm, aims, states, reads, f"{tag}/{name}")
        out[name] = (a, b, c, ctrl)
        print(f"[V6] {tag}/{name} aims_USSR={aims}: (a) {a}, (b) {b}, (c) {c}, control {ctrl}")
    return out


@pytest.mark.skipif(not FIRST_SIGHT, reason="cw_v1 first sight not switched on")
def test_V6():
    timer = Timer()
    blind = blind_snapshots(blind_dir(), YEARS)
    manual = manual_snapshots()
    print("\n[V6] engine: replay against hindsight; explicit form of the layered lifting to 1963")
    print("[V6] asserted: the blind replay at proposal level (decision 7k), dates by the rule")
    print("[V6] printed, not asserted: the manual replay, by the rule and on its recorded dates")
    results, beside = {}, {}
    hindsight_measures = {}
    for aims in HYPS:
        results[aims] = run_series(
            aims, "blind", blind, {"rule": read_years(blind)}, hindsight_measures
        )["rule"]
        beside[aims] = run_series(
            aims,
            "manual",
            manual,
            {"rule": read_years(manual), "recorded": read_years(manual, recorded=True)},
            hindsight_measures,
        )
        print(f"[V6] aims_USSR={aims}: blind {results[aims]}; manual {beside[aims]} ({timer})")
    assert any(all(v) for v in results.values()), results
