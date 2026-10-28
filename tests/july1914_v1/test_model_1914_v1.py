"""Structure of models/july1914/v1.py against docs/july1914_testbed.md section 8.2 and
docs/july1914_v1_decisions.md: the change from v0 is exactly the registered scope, sources and
hypothesis gates, the budget and the fingerprints, the cadences with the new realized decision
of 14 July, the realized moves against the dated decisions and events, the realized replay
move by move under each hypothesis pair, well-formedness from tick 0, v0 unaffected, and the
hold of the first sight.

These are construction checks, not registered claims; the claims are test_J01v1 to test_J09v1,
skipped until the owner sets ``WF_FIRST_SIGHT_1914V1=1`` (decisions V9). The replay below is
the model step's availability check (decisions V8), not J1v1: it asserts where each pair's
replay stops and what the play ends in, and reports no kernel, coalition or relaxation set.
"""

import csv
import hashlib
import re
from collections import defaultdict

import pytest

from models.july1914 import v0
from models.july1914.v1 import (
    CADENCE,
    CADENCE_SOURCES,
    DATA,
    HORIZON,
    PRINCIPALS,
    REALIZED_MOVES,
    V0_DATA,
    build,
    model,
)
from models.ww2.hypotheses import realized_rows
from wavefront.analysis import fingerprint
from wavefront.engine import explore

from .common import PAIRS, compiled, label, replay

CM = model.compile()
ROOT = V0_DATA.parents[1]
CHANGELOG = ROOT / "docs" / "guard_changelog_1914.md"

# The commit at which J1v1 to J9v1 are first run, in one go, with the working tree
# uncommitted (testbed section 8.6; decisions V9). None until the owner's go.
FIRST_SIGHT_COMMIT = "c0c44601aec10cdfb82272a3b77e0a22793277c6"

LEVELS = {
    "aims_GER": ("localize", "continental"),
    "aims_RUS": ("deter", "fight"),
    "blank_cheque": (False, True),
    "ultimatum": ("none", "resolved", "delivered", "rejected"),
    "halt_in_belgrade": ("none", "proposed", "accepted"),
    "war_AUH_SER": ("peace", "war"),
    "tisza": ("opposed", "consented"),
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

# Testbed section 8.2, and 8.5 as resolved by the owner's decision 7e(a): the guard parts of
# the actions v1 changes or adds; every other action is v0's, guard, effect, delay and source
# alike.
V1_PARTS = {
    "AUH.tisza_consent": ["council", "once"],
    "AUH.ultimatum": ["resolved", "tisza"],
    "GER.mobilize": ["hypothesis", "russian_measures", "sequence"],
    "GER.mobilize_east": ["hypothesis", "russian_measures", "sequence", "coupling"],
    "RUS.mobilize_general": ["hypothesis", "austrian_measures", "prepared", "level"],
}

# v0 as committed (e082977): the model file and its data, byte for byte (sha256, 16 hex).
V0_FILES = {
    "models/july1914/v0.py": "fe31f17c97b1f7b7",
    "data/july1914/realized_moves.csv": "cde3029961ffe265",
    "data/july1914/decisions.csv": "5a119af225735e3d",
    "data/july1914/events.csv": "79c6f24afcae13a0",
}


def actions_of(m):
    return {f"{a.name}.{x.name}": x for a in [*m.actors, m.nature()] for x in a.actions}


def decl(name):
    return next(v for v in model.variables if v.name == name)


def test_variables_levels_and_inits_as_v0_plus_tisza():
    declared = {v.name: v for v in CM.variables if v.origin == "var"}
    assert list(declared) == list(LEVELS)
    for name, levels in LEVELS.items():
        v = declared[name]
        assert tuple(v.levels) == tuple(str(x) for x in levels) or v.kind == "flag", name
    assert decl("tisza").init == 0 and decl("tisza").monotone
    assert decl("aims_GER").init is None and decl("aims_RUS").init is None
    assert set(decl("aims_GER").hidden_from) == {"AUH", "RUS", "FRA", "GBR"}
    assert set(decl("aims_RUS").hidden_from) == {"AUH", "GER"}
    assert not model.assumes and not model.profiles
    assert CM.horizon == HORIZON == 38
    assert [a.name for a in CM.actors] == [*PRINCIPALS, "Nature"]


def test_the_change_from_v0_is_exactly_the_registered_scope():
    a0, a1 = actions_of(v0.model), actions_of(model)
    assert set(a1) - set(a0) == {"AUH.tisza_consent"} and set(a0) <= set(a1)
    changed = sorted(k for k in a0 if repr(a0[k]) != repr(a1[k]))
    assert changed == ["AUH.ultimatum", "GER.mobilize", "GER.mobilize_east", "RUS.mobilize_general"]
    for key, parts in V1_PARTS.items():
        assert [p for p, _ in a1[key].guard_parts] == parts, key
    for key in changed:  # effects and delays as v0's
        assert repr(a1[key].effects) == repr(a0[key].effects), key
        assert a1[key].delay == a0[key].delay, key
    ger0, ger1 = (dict(a["GER.kriegsgefahr"].guard_parts) for a in (a0, a1))
    for key in ("GER.mobilize", "GER.mobilize_east"):
        parts = dict(a1[key].guard_parts)
        for p in ("hypothesis", "russian_measures"):
            assert repr(parts[p]) == repr(ger0[p]) == repr(ger1[p]), (key, p)
    # decision 7e(a): the Russian general order takes the partial order's occasion; its other
    # parts are v0's
    rus0, rus1 = (
        dict(a0["RUS.mobilize_general"].guard_parts),
        dict(a1["RUS.mobilize_general"].guard_parts),
    )
    occasion = dict(a1["RUS.mobilize_partial"].guard_parts)["occasion"]
    assert repr(rus1.pop("austrian_measures")) == repr(occasion)
    assert repr(rus1) == repr(rus0)
    assert "AUH.ultimatum:council" not in CM.assumptions()
    assert "AUH.ultimatum:tisza" in CM.assumptions()
    assert repr(model.fairness_constraints) == repr(v0.model.fairness_constraints)
    assert repr(sorted(model.invariants.items())) == repr(sorted(v0.model.invariants.items()))
    assert repr(sorted(model.endings.items())) == repr(sorted(v0.model.endings.items()))
    assert {a.name: a.cadence for a in model.actors} == {a.name: a.cadence for a in v0.model.actors}


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
                if expr.free_vars() & {"aims_GER", "aims_RUS"}:
                    gated[f"{a.name}.{x.name}"] = part
    assert gated == {
        "GER.kriegsgefahr": "hypothesis",
        "GER.mobilize": "hypothesis",
        "GER.mobilize_east": "hypothesis",
        "RUS.mobilize_general": "hypothesis",
    }


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
        "variables": 16,
        "levels": 44,
        "actors": 6,
        "actions": 27,
        "guards": 27,
        "guard_parts": 61,
        "speculative_actions": 0,
        "fairness_constraints": 4,
        "delays": 1,
        "cadence": 2,
        "latches": 0,
        "invariants": 2,
        "endings": 4,
        "builtin_variables": 8,
    }
    assert {k: b[k] for k in expected} == expected
    assert build(False).compile().budget()["cadence"] == 0
    assert fingerprint(model) == "c0548a4c25db"
    assert fingerprint(build(False)) == "a979eb052d20"


def test_v0_is_unaffected():
    assert fingerprint(v0.model) == "368d154000b2"
    assert fingerprint(v0.build(False)) == "f63b4510ab6a"
    for path, digest in V0_FILES.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest()[:16] == digest, path


def realized_decisions():
    with open(DATA / "decisions.csv", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_cadences_are_the_smallest_gaps_of_the_record():
    ticks = defaultdict(list)
    for row in realized_decisions():
        ticks[row["actor"]].append(int(row["tick"]))
    assert sorted(ticks["AUH"]) == [9, 16, 21, 27, 30, 33]
    for actor in PRINCIPALS:
        t = sorted(ticks[actor])
        gap = min(b - a for a, b in zip(t, t[1:], strict=False))
        assert CADENCE[actor] == gap, actor
        assert CADENCE_SOURCES[actor], actor
    assert "14 Jul" in CADENCE_SOURCES["AUH"]
    assert {a.name: a.cadence for a in model.actors} == CADENCE
    assert all(a.cadence == 1 for a in build(False).actors)


def test_realized_moves_are_the_dated_decisions_and_v0s_plus_the_consent():
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
    rows0 = realized_rows(v0.REALIZED_MOVES)
    moves = [tuple(r[a] for a in [*PRINCIPALS, "Nature"]) for r in rows]
    moves0 = [tuple(r[a] for a in [*PRINCIPALS, "Nature"]) for r in rows0]
    diff = [t for t, (m1, m0) in enumerate(zip(moves, moves0, strict=True)) if m1 != m0]
    assert diff == [16] and rows[16]["AUH"] == "tisza_consent"


@pytest.mark.parametrize("cadence", [True, False], ids=["record", "daily"])
@pytest.mark.parametrize("pair", PAIRS, ids=label)
def test_realized_replay_move_by_move(pair, cadence):
    cm = compiled(pair, cadence)
    states, stop = replay(pair, cadence)
    if pair[1] == "fight":
        assert stop is None
        assert len(states) == HORIZON + 1
        assert cm.ending_of(states[-1]) == "GENERAL_WAR"
        for s in states[:-1]:
            assert not cm.is_terminal(s)
    else:  # the [H] gate of RUS.mobilize_general, as in v0 (decisions D8)
        assert stop == (32, "RUS", "mobilize_general")
    assert cm.state_dict(states[16])["tisza"] == "opposed"
    assert cm.state_dict(states[17])["tisza"] == "consented"


def test_dated_events_are_visible_on_the_replay():
    cm = compiled(("continental", "fight"))
    states, _ = replay(("continental", "fight"))
    rows = []
    for path in (V0_DATA / "events.csv", DATA / "events.csv"):
        with open(path, newline="", encoding="utf-8") as fh:
            rows += list(csv.DictReader(line for line in fh if not line.startswith("#")))
    assert any(r["variable"] == "tisza" for r in rows)
    for row in rows:
        t = int(row["visible_tick"])
        value = cm.state_dict(states[t])[row["variable"]]
        assert str(value) == row["level"], (row["date"], row["variable"], value)


@pytest.mark.parametrize("cadence", [True, False], ids=["record", "daily"])
def test_well_formed_from_tick_0_under_every_pair(cadence):
    g = explore(build(cadence).compile(), max_states=3_000_000)
    assert len(g.initial) == 4
    assert g.size() == (93_003 if cadence else 50_813)


def test_the_model_step_is_logged_and_the_first_sight_is_held():
    text = CHANGELOG.read_text(encoding="utf-8")
    rows = [line for line in text.splitlines() if line.startswith("| 2026")]
    step = [r for r in rows if "v1 model step" in r]
    assert len(step) == 1 and "before any of J1v1 to J9v1 was run" in step[0]
    amendment = [r for r in rows if "model step amendment on the owner's decision 7e(a)" in r]
    assert len(amendment) == 1 and "before any of J1v1 to J9v1 was run" in amendment[0]
    assert "c0548a4c25db" in amendment[0] and "a979eb052d20" in amendment[0]
    sight = [r for r in rows if "first sight of J1v1" in r]
    if FIRST_SIGHT_COMMIT is None:
        assert not sight, "a v1 first-sight row without FIRST_SIGHT_COMMIT"
    else:
        assert len(sight) == 1 and FIRST_SIGHT_COMMIT in sight[0]
    for f in sorted((ROOT / "tests" / "july1914_v1").glob("test_J*v1.py")):
        assert "WF_FIRST_SIGHT_1914V1" in f.read_text(encoding="utf-8"), f.name
