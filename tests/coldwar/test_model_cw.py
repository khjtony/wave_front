"""Structure of models/cw/v0.py and models/cw/crises against docs/ontology_cw.md,
docs/actions_cw.md and docs/cw_v0_decisions.md: variables and levels, sources, hypothesis
gates, the PRC's scope, the budget, the generated catalogue, the realized moves against the
dated decisions and events, the realized replays of the coarse game, the sub-games and the
flattened game, the snapshot convention, well-formedness, and the hold-out rule on
docs/guard_changelog_cw.md.

These are construction checks, not registered claims; the claims are
tests/coldwar/scenarios/test_C01.py to test_C13.py.
"""

import csv
import re
import subprocess
import sys

import pytest

from models.cw import crises
from models.cw.snapshots import SNAPSHOTS, write
from models.cw.v0 import DATA, HORIZON, REALIZED_MOVES, ROOT, build, model
from models.ww2.hypotheses import realized_moves, realized_rows
from wavefront.analysis import fingerprint
from wavefront.engine import explore

from .common import HYPS, compiled, flat_of, hindsight, realized

CM = model.compile()

# The commit at which C1 to C13 were first run, in one go (decisions D9; the first-sight
# row of docs/guard_changelog_cw.md).
FIRST_SIGHT_COMMIT = "6b87af9d5790094c4f2af12bae31a813b03bcc6f"

LEVELS = {
    "aims_USSR": ("status_quo", "opportunist"),
    "nuke_USA": ("none", "few", "survivable", "overkill"),
    "nuke_USSR": ("none", "few", "survivable", "overkill"),
    "intel_USA": ("low", "partial", "overhead"),
    "belief_force_USA": ("none", "few", "survivable", "overkill"),
    "belief_USA_USSR": ("status_quo", "opportunist", "expansionist"),
    "belief_USSR_USA": ("status_quo", "hostile", "first_strike_intent"),
    "offer": ("none", "test_ban", "limits", "reductions"),
    "oversight": ("none", "test_ban", "ntm", "on_site"),
    "arms": ("race", "capped", "reduced"),
    "buildup": (False, True),
    "esc": ("peace", "crisis", "conventional", "tactical_nuclear", "strategic"),
    "accidental": (False, True),
    "us_strike": (False, True),
    "berlin_wall": (False, True),
    "invasion_west": (False, True),
    "korea": ("peace", "war", "armistice"),
    "afghan": ("none", "war", "withdrawn"),
    "econ_USSR": ("growing", "stagnant", "declining", "failing"),
    "legit_USSR": ("secure", "contested", "failing"),
    "perestroika": (False, True),
    "bloc_USSR": ("intact", "contested", "released", "dissolved"),
    "align_PRC": ("soviet_ally", "split", "us_aligned"),
    "china_opening": (False, True),
    "esc_sino": ("peace", "clash", "war"),
}
BELIEFS = ("belief_force_USA", "belief_USA_USSR", "belief_USSR_USA")


def test_variables_levels_and_inits_as_the_ontology():
    declared = {v.name: v for v in CM.variables if v.origin == "var"}
    assert list(declared) == list(LEVELS)
    for name, levels in LEVELS.items():
        assert tuple(declared[name].levels) == tuple(str(x) for x in levels) or (
            declared[name].kind == "flag"
        ), name
    aims = next(v for v in model.variables if v.name == "aims_USSR")
    assert aims.init is None and set(aims.hidden_from) == {"USA", "PRC"}
    assert not model.assumes and not model.profiles and not model.fairness_constraints
    assert CM.horizon == HORIZON == 45
    assert [a.name for a in CM.actors] == ["USA", "USSR", "PRC", "Nature"]


def all_actions(m):
    return [(a, x) for a in [*m.actors, m.nature()] for x in a.actions]


@pytest.mark.parametrize(
    "m", [model, *(s.model for s in crises.SUBGAMES.values())], ids=lambda m: m.name
)
def test_every_action_has_a_dated_source_and_none_is_speculative(m):
    for a, x in all_actions(m):
        assert len(x.source) > 40, (a.name, x.name)
        assert re.search(r"19[2-9]\d", x.source), (a.name, x.name)
        assert not x.speculative, (a.name, x.name)


def test_hypothesis_gates_are_the_only_readers_of_the_aims():
    gated = {}
    for a, x in all_actions(model):
        for part, expr in x.guard_parts:
            if "aims_USSR" in expr.free_vars():
                gated[f"{a.name}.{x.name}"] = part
    assert gated == {
        "USSR.approve_korea": "hypothesis",
        "USSR.enter_korea": "hypothesis",
        "USSR.invade_west": "hypothesis",
    }


def test_the_prc_is_a_principal_from_1969_and_nature_carries_it_in_the_scripted_build():
    prc = next(a for a in model.actors if a.name == "PRC")
    assert [x.name for x in prc.actions] == ["border_clash", "rapprochement", "normalize"]
    for x in prc.actions:
        assert x.guard_parts[0][0] == "principal"
    scripted = build(prc_principal=False)
    assert [a.name for a in scripted.actors] == ["USA", "USSR"]
    nature = [x.name for x in scripted.nature().actions]
    assert {"border_clash", "rapprochement", "normalize"} <= set(nature)
    assert "PRC" not in next(v for v in scripted.variables if v.name == "aims_USSR").hidden_from


def test_budget_and_fingerprints_as_catalogued():
    b = CM.budget()
    expected = {
        "variables": 25,
        "levels": 76,
        "actors": 4,
        "actions": 58,
        "guards": 58,
        "guard_parts": 110,
        "speculative_actions": 0,
        "fairness_constraints": 0,
        "delays": 7,
        "cadence": 0,
        "invariants": 4,
        "endings": 5,
    }
    assert {k: b[k] for k in expected} == expected
    assert fingerprint(model) == "430d7ac3cdbb"
    assert fingerprint(build(prc_principal=False)) == "29bf5b8cf12d"
    assert fingerprint(build(frozen_oversight=True)) == "d68077ee7e9e"
    subs = {n: fingerprint(s.model) for n, s in crises.SUBGAMES.items()}
    assert subs == {
        "berlin_1948": "c7b956d15290",
        "cuba_1962": "2abcb5e9c735",
        "able_archer_1983": "abcf2dea1928",
    }


def test_the_actions_catalogue_is_generated_from_the_model():
    script = ROOT / "scripts" / "cw_catalogue.py"
    done = subprocess.run([sys.executable, str(script), "--check"], capture_output=True)
    assert done.returncode == 0, "docs/actions_cw.md is out of date: run scripts/cw_catalogue.py"


def test_the_frozen_oversight_build_only_drops_the_oversight_effects():
    frozen = build(frozen_oversight=True)
    for (a, x), (b, y) in zip(all_actions(model), all_actions(frozen), strict=True):
        assert (a.name, x.name, repr(x.guard_parts)) == (b.name, y.name, repr(y.guard_parts))
        kept = [e for e in x.effects if getattr(e, "var", None) != "oversight"]
        assert repr(list(y.effects)) == repr(kept)


def decisions():
    with open(DATA / "decisions.csv", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_realized_moves_are_the_dated_decisions():
    rows = realized_rows(REALIZED_MOVES)
    assert len(rows) == HORIZON
    actors = ("USA", "USSR", "PRC")
    played = {(int(r["tick"]), a, r[a]) for r in rows for a in actors if r[a] != "idle"}
    recorded = {(int(d["tick"]), d["actor"], d["action"]) for d in decisions()}
    assert played == recorded - {(-2, "USSR", "build_bomb")}
    for d in decisions():
        a = next(x for x in CM.actors if x.name == d["actor"])
        assert int(d["delay_years"]) == a.actions[a.action_index(d["action"])].delay
    for r in rows:
        assert r["year"] == str(1947 + int(r["tick"]))
        moved = any(r[a] not in ("idle", "none") for a in (*actors, "Nature"))
        assert not moved or r["note"], r["year"]


@pytest.mark.parametrize("aims", HYPS)
def test_realized_replay_on_the_flattened_game(aims):
    coarse, fine, stop = realized(aims)
    fm = flat_of(aims)
    if aims == "opportunist":
        assert stop is None
        assert len(coarse) == HORIZON + 1
        assert fm.coarse.ending_of(coarse[-1]) == "CHALLENGER_EXHAUSTION"
        assert all(not fm.coarse.is_terminal(s) for s in coarse[:-1])
        ends = {}
        for name, states in fine.items():
            sub = crises.SUBGAMES[name].model.compile()
            ends[name] = sub.ending_of(fm.split(states[-1])[2])
        assert ends == {
            "berlin_1948": "SETTLED",
            "cuba_1962": "WITHDRAWAL",
            "able_archer_1983": "HORIZON",
        }
    else:
        assert stop == (1950, None, 0, "USSR", "approve_korea")


@pytest.mark.parametrize("name", list(crises.SUBGAMES))
def test_each_sub_game_replays_its_realized_days(name):
    sub = crises.SUBGAMES[name].model.compile()
    init = {"able_archer_1983": {"belief": "first_strike_intent"}}.get(name, {})
    (s,) = [
        x for x in sub.initial_states() if all(sub.state_dict(x)[k] == v for k, v in init.items())
    ]
    path = DATA / "crises" / name / "realized_moves.csv"
    for move in realized_moves(sub, path):
        if sub.is_terminal(s):
            break
        av = sub.available(s)
        assert all(j in acts for j, acts in zip(move, av, strict=True))
        s = sub.step(s, move)
    expected = {"berlin_1948": "SETTLED", "cuba_1962": "WITHDRAWAL", "able_archer_1983": "HORIZON"}
    assert sub.ending_of(s) == expected[name]


def events():
    with open(DATA / "events.csv", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(line for line in fh if not line.startswith("#")))


def test_dated_events_are_visible_on_the_realized_path():
    coarse, _, _ = realized("opportunist")
    cm = flat_of("opportunist").coarse
    rows = events()
    assert {r["series"] for r in rows} == {"record", "belief", "replay"}
    checked = 0
    for row in rows:
        if row["series"] == "replay" or (row["series"] == "record" and row["variable"] in BELIEFS):
            continue
        value = cm.state_dict(coarse[int(row["visible_tick"])])[row["variable"]]
        assert value == row["level"], (row["visible_year"], row["variable"], value)
        checked += 1
    assert checked > 60


def test_snapshots_are_up_to_date():
    assert write(SNAPSHOTS, check=True) == []


@pytest.mark.parametrize("aims", HYPS)
def test_hindsight_differs_from_the_realized_path_only_in_the_belief_errors(aims):
    """Decisions D6: the hindsight snapshots carry each belief's hindsight truth."""
    coarse, _, _ = realized("opportunist")
    cm = compiled(aims)
    errors = {}
    for year in range(1947, 1993):
        h = cm.state_dict(hindsight(year, aims))
        p = cm.state_dict(coarse[year - 1947])
        diff = {k for k in h if h[k] != p[k] and k != "aims_USSR"}
        if diff:
            errors[year] = diff
    beliefs = {
        **{y: {"belief_force_USA"} for y in range(1958, 1962)},
        **{y: {"belief_USSR_USA"} for y in [*range(1983, 1986), *range(1988, 1993)]},
    }
    # belief_USA_USSR's hindsight truth is the hypothesis's own level (the path is opportunist)
    usa_reading = range(1951, 1954) if aims == "opportunist" else range(1947, 1993)
    for y in usa_reading:
        beliefs[y] = beliefs.get(y, set()) | {"belief_USA_USSR"}
    assert errors == beliefs


@pytest.mark.parametrize("aims", HYPS)
def test_well_formed_from_1975_and_on_the_flattened_game_from_1983(aims):
    g = explore(compiled(aims), initial=[hindsight(1975, aims)], max_states=1_000_000)
    assert g.size() > 1000
    fm = flat_of(aims)
    g = explore(fm, initial=[hindsight(1983, aims)], max_states=1_000_000)
    assert any(fm.is_fine(s) for s in g.states)


@pytest.mark.parametrize("name", list(crises.SUBGAMES))
def test_each_sub_game_is_well_formed_from_its_entry(name):
    sub = crises.SUBGAMES[name].model.compile()
    g = explore(sub, max_states=1_000_000)
    assert g.size() > 10


def test_hold_out_rows_after_first_sight_name_a_source_and_spare_the_hold_out():
    text = (ROOT / "docs" / "guard_changelog_cw.md").read_text(encoding="utf-8")
    rows = [line for line in text.splitlines() if line.startswith("| 2026")]
    marks = [k for k, line in enumerate(rows) if "first sight" in line and "C1 to C13" in line]
    if FIRST_SIGHT_COMMIT is None:
        assert not marks, "a first-sight row without FIRST_SIGHT_COMMIT"
        return
    assert marks, "no first-sight row"
    assert FIRST_SIGHT_COMMIT in rows[marks[0]]
    for line in rows[marks[0] + 1 :]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        claim, source, rerun = cells[1], cells[3], cells[5]
        assert source and source != "n/a", line
        assert rerun.startswith("yes"), line
        assert not re.search(r"\bC(3|6|7|13)\b", claim), "C3, C6, C7, C13: total hold-out"
