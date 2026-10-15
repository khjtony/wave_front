"""Structure of models/july1914/v0.py against docs/ontology_1914.md, docs/actions_1914.md and
docs/july1914_decisions.md: variables and levels, sources, hypothesis gates, the belief rule,
the budget, the cadences with their record, the realized moves against the dated decisions
and events, the realized replay under each hypothesis pair, well-formedness from tick 0, and
the hold-out guard on docs/guard_changelog_1914.md.

These are construction checks, not registered claims; the claims are test_J01 to test_J07.
"""

import csv
import re
from collections import defaultdict

import pytest

from models.july1914.v0 import (
    CADENCE,
    CADENCE_SOURCES,
    DATA,
    HORIZON,
    PRINCIPALS,
    REALIZED_MOVES,
    build,
    model,
)
from models.ww2.hypotheses import realized_rows
from wavefront.analysis import fingerprint
from wavefront.engine import explore

from .common import PAIRS, compiled, label, replay

CM = model.compile()
ROOT = DATA.parents[1]

# The commit at which J1 to J7 were first run, in one go, with the working tree uncommitted
# (docs/july1914_decisions.md D9; the first-sight row of docs/guard_changelog_1914.md).
FIRST_SIGHT_COMMIT = "f00e5be3d27c578d009383bb81fdcd7d3ea6a6de"

LEVELS = {
    "aims_GER": ("localize", "continental"),
    "aims_RUS": ("deter", "fight"),
    "blank_cheque": (False, True),
    "ultimatum": ("none", "resolved", "delivered", "rejected"),
    "halt_in_belgrade": ("none", "proposed", "accepted"),
    "war_AUH_SER": ("peace", "war"),
    "mob_AUH": ("none", "partial", "general"),
    "mob_RUS": ("none", "pre_mobilization", "partial", "general"),
    "mob_GER": ("none", "kriegsgefahr", "general"),
    "mob_FRA": ("none", "covering_troops", "general"),
    "war_GER_RUS": ("peace", "war"),
    "war_GER_FRA": ("peace", "war"),
    "belgium": ("neutral", "demanded", "invaded"),
    "belief_GER_GBR": ("stays_out", "uncertain", "fights"),
    "commitment_GBR": ("none", "naval_assurance", "belgian_guarantee", "war"),
}


def decl(name):
    return next(v for v in model.variables if v.name == name)


def test_variables_levels_and_inits_as_the_ontology():
    declared = {v.name: v for v in CM.variables if v.origin == "var"}
    assert list(declared) == list(LEVELS)
    for name, levels in LEVELS.items():
        v = declared[name]
        assert tuple(v.levels) == tuple(str(x) for x in levels) or v.kind == "flag", name
    assert decl("aims_GER").init is None and decl("aims_RUS").init is None
    assert set(decl("aims_GER").hidden_from) == {"AUH", "RUS", "FRA", "GBR"}
    assert set(decl("aims_RUS").hidden_from) == {"AUH", "GER"}
    assert not model.assumes and not model.profiles
    assert CM.horizon == HORIZON == 38
    assert [a.name for a in CM.actors] == [*PRINCIPALS, "Nature"]


def test_every_action_has_a_dated_source_and_none_is_speculative():
    for a in CM.actors:
        for x in a.actions:
            if x.is_idle:
                continue
            assert len(x.source) > 40, (a.name, x.name)
            assert re.search(r"1914|1913|1912", x.source), (a.name, x.name)
            assert not x.speculative, (a.name, x.name)


def test_hypothesis_gates_are_the_only_readers_of_the_aims():
    gated = {}
    for a in model.actors + [model.nature()]:
        for x in a.actions:
            for part, expr in x.guard_parts:
                names = expr.free_vars()
                if names & {"aims_GER", "aims_RUS"}:
                    gated[f"{a.name}.{x.name}"] = part
    assert gated == {"GER.kriegsgefahr": "hypothesis", "RUS.mobilize_general": "hypothesis"}


def test_the_belief_is_read_by_no_guard_fairness_or_profile():
    for a in model.actors + [model.nature()]:
        for x in a.actions:
            assert "belief_GER_GBR" not in x.guard.free_vars(), x.name
    for f in model.fairness_constraints:
        assert "belief_GER_GBR" not in f.trigger.free_vars()
    assert not model.profiles


def test_budget_as_catalogued():
    b = CM.budget()
    expected = {
        "variables": 15,
        "levels": 42,
        "actors": 6,
        "actions": 26,
        "guards": 26,
        "guard_parts": 54,
        "speculative_actions": 0,
        "fairness_constraints": 4,
        "delays": 1,
        "cadence": 2,
        "invariants": 2,
        "endings": 4,
    }
    assert {k: b[k] for k in expected} == expected
    assert build(False).compile().budget()["cadence"] == 0
    assert fingerprint(model) == "368d154000b2"
    assert fingerprint(build(False)) == "f63b4510ab6a"


def test_the_coupling_and_the_timetable_as_decided():
    ger = next(a for a in CM.actors if a.name == "GER")
    east = ger.actions[ger.action_index("mobilize_east")]
    assert [p for p, _ in east.guard_parts] == ["sequence", "coupling"]
    assert "GER.mobilize_east:coupling" in CM.assumptions()
    fair = {f.name: (f.actor, f.within, f.responses) for f in model.fairness_constraints}
    assert fair == {
        "reply_deadline": ("Nature", 2, ("serbian_reply",)),
        "mobilization_race": ("GER", 1, ("kriegsgefahr", "mobilize", "mobilize_east")),
        "western_timetable": ("GER", 1, ("ultimatum_belgium", "declare_war_FRA")),
        "liege": ("Nature", 1, ("invade_belgium",)),
    }
    delays = {f"{a.name}.{x.name}": x.delay for a in CM.actors for x in a.actions if x.delay}
    assert delays == {"AUH.ultimatum": 4}


def realized_decisions():
    with open(DATA / "decisions.csv", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_cadences_are_the_smallest_gaps_of_the_record():
    ticks = defaultdict(list)
    for row in realized_decisions():
        ticks[row["actor"]].append(int(row["tick"]))
    for actor in PRINCIPALS:
        t = sorted(ticks[actor])
        gap = min(b - a for a, b in zip(t, t[1:], strict=False))
        assert CADENCE[actor] == gap, actor
        assert CADENCE_SOURCES[actor], actor
    cadenced = [v.name for v in CM.variables if v.name.startswith("cadence_")]
    assert cadenced == ["cadence_AUH", "cadence_FRA"]
    assert {a.name: a.cadence for a in model.actors} == CADENCE
    assert all(a.cadence == 1 for a in build(False).actors)


def test_realized_moves_are_the_dated_decisions():
    rows = realized_rows(REALIZED_MOVES)
    assert len(rows) == HORIZON
    played = {(int(r["tick"]), a, r[a]) for r in rows for a in PRINCIPALS if r[a] != "idle"}
    recorded = {(int(d["tick"]), d["actor"], d["action"]) for d in realized_decisions()}
    assert played == recorded
    for d in realized_decisions():
        a = next(x for x in CM.actors if x.name == d["actor"])
        assert int(d["delay_days"]) == a.actions[a.action_index(d["action"])].delay
    for r in rows:
        assert r["date"] and (r["note"] or all(r[a] in ("idle", "none") for a in PRINCIPALS))


@pytest.mark.parametrize("pair", PAIRS, ids=label)
def test_realized_replay_per_hypothesis_pair(pair):
    cm = compiled(pair)
    states, stop = replay(pair)
    if pair[1] == "fight":
        assert stop is None
        assert len(states) == HORIZON + 1
        assert cm.ending_of(states[-1]) == "GENERAL_WAR"
        for s in states[:-1]:
            assert not cm.is_terminal(s)
    else:
        assert stop == (32, "RUS", "mobilize_general")


def test_dated_events_are_visible_on_the_replay():
    cm = compiled(("continental", "fight"))
    states, _ = replay(("continental", "fight"))
    with open(DATA / "events.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(line for line in fh if not line.startswith("#")))
    assert rows
    for row in rows:
        t = int(row["visible_tick"])
        value = cm.state_dict(states[t])[row["variable"]]
        assert str(value) == row["level"], (row["date"], row["variable"], value)


@pytest.mark.parametrize("cadence", [True, False], ids=["record", "daily"])
def test_well_formed_from_tick_0_under_every_pair(cadence):
    g = explore(build(cadence).compile(), max_states=2_000_000)
    assert len(g.initial) == 4
    assert g.size() == (181_913 if cadence else 73_937)


def test_hold_out_rows_after_first_sight_name_a_source_and_spare_the_hold_out():
    text = (ROOT / "docs" / "guard_changelog_1914.md").read_text(encoding="utf-8")
    rows = [line for line in text.splitlines() if line.startswith("| 2026")]
    marks = [k for k, line in enumerate(rows) if "first sight" in line]
    assert marks, "no first-sight row"
    assert FIRST_SIGHT_COMMIT in rows[marks[0]]
    for line in rows[marks[0] + 1 :]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        claim, source, rerun = cells[1], cells[3], cells[5]
        assert source and source != "n/a", line
        assert rerun.startswith("yes"), line
        assert not re.search(r"\bJ[2-6]\b", claim), "J2 to J6 are under a total hold-out"
