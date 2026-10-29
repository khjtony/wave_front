"""Construction checks of models/cw/v1.py and the two v1 sub-games against
docs/ontology_cw.md section 12, docs/actions_cw.md section 6 and docs/cw_v1_decisions.md:
v0 unchanged, variables, sources, hypothesis gates, the PRC's scope and the analysis builds,
the budget and fingerprints, the generated catalogue, the realized moves against the dated
decisions and events, the realized moves available step by step on the flattened game, the
sub-games' realized days, the snapshot convention, well-formedness from the claims' start
states and the sizes recorded in decisions section S.

These are construction checks, not registered claims: nothing here computes a quantity of V1
to V10 (in particular no kernel membership, no forcing region, no relaxation count and no
ending of the realized path). The claims are tests/coldwar_v1/scenarios/test_V01.py to
test_V10.py, which run only under the owner's first-sight switch (decisions D8).
"""

import csv
import re
import subprocess
import sys

import pytest

from models.cw import v0, v1
from models.cw.crises import alert_1973, sino_soviet_1969
from models.cw.snapshots_v1 import SNAPSHOTS, events, write
from models.ww2.hypotheses import realized_moves, realized_rows
from wavefront.analysis import fingerprint
from wavefront.engine import explore
from wavefront.model import V

from .common import CRISIS_DATA, HYPS, compiled, fine_graph, flat_of, graph, hindsight, realized
from .common import tick as tick_of

CM = v1.model.compile()
NEW_SUBGAMES = {"sino_soviet_1969": sino_soviet_1969, "alert_1973": alert_1973}
BELIEFS = ("belief_force_USA", "belief_USA_USSR", "belief_USSR_USA")

# The commit at which V1 to V10 are first run, in one go (decisions D8): None until the
# owner's first sight.
FIRST_SIGHT_COMMIT_V1 = "1663c43ac4b5f3c33ebd60a0f3c2130550104194"


def all_actions(m):
    return [(a, x) for a in [*m.actors, m.nature()] for x in a.actions]


# -- v0 unchanged ---------------------------------------------------------------------------
def test_v0_is_unchanged():
    assert fingerprint(v0.model) == "527d0f540ac6"
    assert fingerprint(v0.build(prc_principal=False)) == "08da3b3a28da"
    assert fingerprint(v0.build(frozen_oversight=True)) == "424bd3cc6e65"
    from models.cw import crises

    assert list(crises.SUBGAMES) == ["berlin_1948", "cuba_1962", "able_archer_1983"]
    assert {n: fingerprint(s.model) for n, s in crises.SUBGAMES.items()} == {
        "berlin_1948": "c7b956d15290",
        "cuba_1962": "2abcb5e9c735",
        "able_archer_1983": "abcf2dea1928",
    }


# -- declarations ---------------------------------------------------------------------------
def test_variables_are_v0s_plus_the_us_prc_war_the_talks_and_the_count():
    v0_vars = [v.name for v in v0.model.compile().variables if v.origin == "var"]
    v1_vars = [v.name for v in CM.variables if v.origin == "var"]
    assert v1_vars == [*v0_vars, "esc_usprc", "sino_soviet_talks", "count_USSR"]
    assert tuple(CM.variables[CM.index["esc_usprc"]].levels) == ("peace", "war")
    # the owner's decision 7g: belief_force_USA on the bands of count_USSR (decisions D9)
    bands = ("none", "under_200", "under_1000", "over_1000")
    assert tuple(v1.BANDS) == bands
    for name in ("count_USSR", "belief_force_USA"):
        assert tuple(CM.variables[CM.index[name]].levels) == bands, name
    count = next(v for v in v1.model.variables if v.name == "count_USSR")
    belief = next(v for v in v1.model.variables if v.name == "belief_force_USA")
    assert count.monotone and count.init == 0 and not belief.monotone and belief.init == 0
    talks = next(v for v in v1.model.variables if v.name == "sino_soviet_talks")
    assert talks.monotone and talks.init is not None and not talks.init
    assert CM.horizon == v1.HORIZON == 45
    assert [a.name for a in CM.actors] == ["USA", "USSR", "PRC", "Nature"]
    aims = next(v for v in v1.model.variables if v.name == "aims_USSR")
    assert aims.init is None and set(aims.hidden_from) == {"USA", "PRC"}
    assert not v1.model.assumes and not v1.model.profiles and not v1.model.fairness_constraints


@pytest.mark.parametrize(
    "m",
    [
        v1.model,
        v1.build(prc_principal=False),
        sino_soviet_1969.model,
        sino_soviet_1969.model_prc_scripted,
        alert_1973.model,
    ],
    ids=lambda m: m.name,
)
def test_every_action_has_a_dated_source_and_none_is_speculative(m):
    for a, x in all_actions(m):
        assert len(x.source) > 40, (a.name, x.name)
        assert re.search(r"19[2-9]\d", x.source), (a.name, x.name)
        assert not x.speculative, (a.name, x.name)


def test_every_v1_edit_of_a_v0_action_carries_its_own_source():
    before = {(a.name, x.name): x for a, x in all_actions(v0.model)}
    for a, x in all_actions(v1.model):
        old = before.get((a.name, x.name))
        if old is None:
            continue
        same = (repr(old.guard_parts), repr(old.effects), old.delay) == (
            repr(x.guard_parts),
            repr(x.effects),
            x.delay,
        )
        if same:
            assert x.source == old.source, (a.name, x.name)
        else:
            assert x.source.startswith(old.source) and " v1: " in x.source, (a.name, x.name)
            assert re.search(r"19[2-9]\d", x.source.split(" v1: ", 1)[1]), (a.name, x.name)


def test_hypothesis_gates_are_the_only_readers_of_the_aims():
    gated = {
        f"{a.name}.{x.name}": part
        for a, x in all_actions(v1.model)
        for part, expr in x.guard_parts
        if "aims_USSR" in expr.free_vars()
    }
    assert gated == {
        "USSR.approve_korea": "hypothesis",
        "USSR.enter_korea": "hypothesis",
        "USSR.invade_west": "hypothesis",
    }


def test_the_prc_is_a_principal_from_1950_and_the_builds():
    prc = next(a for a in v1.model.actors if a.name == "PRC")
    assert [x.name for x in prc.actions] == [
        "border_clash",
        "rapprochement",
        "normalize",
        "intervene_korea",
    ]
    for x in prc.actions:
        name, expr = x.guard_parts[0]
        assert name == "principal" and repr(expr) == repr(V.tick >= 3)
    scripted = v1.build(prc_principal=False)
    assert [a.name for a in scripted.actors] == ["USA", "USSR"]
    nature = {x.name for x in scripted.nature().actions}
    assert {"border_clash", "rapprochement", "normalize", "intervene_korea"} <= nature
    no_options = v1.build(us_crisis_options=False)
    usa = {x.name for x in no_options.actor_named("USA").actions}
    assert usa == {x.name for x in v1.model.actor_named("USA").actions} - set(v1.US_CRISIS_OPTIONS)
    for name in v1.US_CRISIS_OPTIONS:
        x = next(x for x in v1.model.actor_named("USA").actions if x.name == name)
        assert [p for p, _ in x.guard_parts] == ["occasion", "level"]


def test_crisis_actions_have_no_effect_and_a_dated_occasion():
    fm = flat_of("opportunist")
    assert [c.crisis.label for c in fm._compiled] == list(v1.SUBGAMES)
    for comp in fm._compiled:
        actor = fm.coarse.actors[comp.actor]
        spec = actor.actions[comp.action]
        assert not spec.effects and not spec.delay
        assert "occasion" in dict(spec.guard_parts), spec.name


def test_the_frozen_oversight_build_only_drops_the_oversight_effects():
    frozen = v1.build(frozen_oversight=True)
    for (a, x), (b, y) in zip(all_actions(v1.model), all_actions(frozen), strict=True):
        assert (a.name, x.name, repr(x.guard_parts)) == (b.name, y.name, repr(y.guard_parts))
        kept = [e for e in x.effects if getattr(e, "var", None) != "oversight"]
        assert repr(list(y.effects)) == repr(kept)


def test_budget_and_fingerprints_as_catalogued():
    b = CM.budget()
    expected = {
        "variables": 29,
        "levels": 86,
        "actors": 4,
        "actions": 68,
        "guards": 68,
        "guard_parts": 137,
        "speculative_actions": 0,
        "fairness_constraints": 0,
        "delays": 8,
        "cadence": 0,
        "invariants": 9,
        "endings": 5,
    }
    assert {k: b[k] for k in expected} == expected
    # before the owner's decision 7g (2026-10-28): 151787621ce1, a21bc2f7c046, a2c78d3a609d,
    # 736ac7362625, with 28 variables, 82 levels, 64 actions, 127 guard parts and 7 delays
    assert fingerprint(v1.model) == "6cbb54f105b1"
    assert fingerprint(v1.build(prc_principal=False)) == "8eb285056b15"
    assert fingerprint(v1.build(us_crisis_options=False)) == "9780a34b6304"
    assert fingerprint(v1.build(frozen_oversight=True)) == "6b7059a046d4"
    assert fingerprint(sino_soviet_1969.model) == "ac9a1b01ddaa"
    assert fingerprint(sino_soviet_1969.model_prc_scripted) == "6df79b14f313"
    assert fingerprint(alert_1973.model) == "6e4f5e7c5efe"
    fb = flat_of("opportunist").budget()
    assert fb["crises"] == 5
    assert (fb["crisis_variables"], fb["crisis_actions"], fb["crisis_speculative_actions"]) == (
        32,
        50,
        0,
    )


def test_the_v1_actions_catalogue_is_generated_from_the_model():
    script = v1.ROOT / "scripts" / "cw_catalogue.py"
    done = subprocess.run([sys.executable, str(script), "--v1", "--check"], capture_output=True)
    assert done.returncode == 0, "docs/actions_cw.md section 6 is out of date"


def test_the_registered_predicates_are_declared():
    names = set(v1.model.invariants)
    assert {"no_war_core", "both_or_neither", "balance_core", "balance_tri"} <= names
    assert {"balance_cw", "no_war", "no_general_war", "bloc_intact"} <= names
    assert "no_general_war_core" in names
    assert set(v1.model.endings) == set(v0.model.endings)


@pytest.mark.parametrize("prc_principal", [True, False])
def test_the_1969_exit_carries_the_talks_into_the_coarse_game(prc_principal):
    """The owner's decision 7f(a): agreed talks without a strike set ``sino_soviet_talks``;
    a strike sets the Sino-Soviet war and not the flag; the flag closes ``strike_china``."""
    sub = sub_of("sino_soviet_1969", prc_principal)
    g = explore(sub, max_states=1_000_000)
    seen = set()
    for i in range(g.size()):
        if not g.terminal[i]:
            continue
        week = {k: str(v) for k, v in sub.state_dict(g.states[i]).items()}
        out = sino_soviet_1969.exit_map(week, {})
        if week["strike"] == "True":
            assert out == {"esc_sino": "war"}
        elif week["talks"] == "agreed":
            assert out == {"esc_sino": "clash", "sino_soviet_talks": True}
        else:
            assert out == {"esc_sino": "clash"}
        seen.add(tuple(sorted(out)))
    assert seen == {("esc_sino",), ("esc_sino", "sino_soviet_talks")}
    strike = next(x for x in v1.model.actor_named("USSR").actions if x.name == "strike_china")
    assert repr(dict(strike.guard_parts)["talks"]) == repr(~V.sino_soviet_talks)


# -- data -----------------------------------------------------------------------------------
def decisions():
    rows = []
    for path in (v1.DATA / "decisions.csv", v1.DATA_V1 / "decisions.csv"):
        with open(path, newline="", encoding="utf-8") as fh:
            rows += list(csv.DictReader(fh))
    return rows


def test_realized_moves_are_the_dated_decisions():
    rows = realized_rows(v1.REALIZED_MOVES)
    assert len(rows) == v1.HORIZON
    actors = ("USA", "USSR", "PRC")
    played = {(int(r["tick"]), a, r[a]) for r in rows for a in actors if r[a] != "idle"}
    recorded = {(int(d["tick"]), d["actor"], d["action"]) for d in decisions()}
    assert played == recorded - {(-2, "USSR", "build_bomb")}
    for d in decisions():
        a = next(x for x in CM.actors if x.name == d["actor"])
        assert int(d["delay_years"]) == a.actions[a.action_index(d["action"])].delay
    v0_rows = realized_rows(v0.REALIZED_MOVES)
    changed = {
        int(r["tick"])
        for r, s in zip(rows, v0_rows, strict=True)
        if any(r[a] != s[a] for a in (*actors, "Nature"))
    }
    # 1956, 1959, 1968: the Soviet deployments of the count and the bomber gap (decision 7g)
    assert changed == {tick_of(y) for y in (1951, 1956, 1959, 1968, 1973)}


@pytest.mark.parametrize("aims", HYPS)
def test_the_realized_moves_are_available_step_by_step(aims):
    """A construction check of the realized moves file, not claim V1: every recorded move is
    available where the file places it; the ending is not read here."""
    coarse, fine, stop = realized(aims)
    if aims == "opportunist":
        assert stop is None
        assert len(coarse) == v1.HORIZON + 1
        assert set(fine) == set(v1.SUBGAMES)
    else:  # the war in Korea needs the opportunist reading of Stalin's approval (v0's D3)
        assert stop == (1950, None, 0, "USSR", "approve_korea")


def sub_of(name, prc_principal=True):
    if name == "sino_soviet_1969":
        return sino_soviet_1969.build(prc_principal).compile()
    return NEW_SUBGAMES[name].model.compile()


@pytest.mark.parametrize("name", list(NEW_SUBGAMES))
def test_each_new_sub_game_replays_its_realized_days(name):
    sub = sub_of(name)
    (s,) = sub.initial_states()
    path = CRISIS_DATA / name / "realized_moves.csv"
    for move in realized_moves(sub, path):
        if sub.is_terminal(s):
            break
        av = sub.available(s)
        assert all(j in acts for j, acts in zip(move, av, strict=True))
        s = sub.step(s, move)
    assert sub.ending_of(s) == {"sino_soviet_1969": "HORIZON", "alert_1973": "CEASEFIRE"}[name]


def test_dated_events_are_visible_on_the_realized_path():
    """Every record row of a non-belief variable and every belief row is the level on the
    realized path at its visible tick; a row marked [SQR] one tick later (decisions R V1)."""
    coarse, _, _ = realized("opportunist")
    cm = flat_of("opportunist").coarse
    checked = 0
    for row in events():
        if row["series"] == "replay" or (row["series"] == "record" and row["variable"] in BELIEFS):
            continue
        t = int(row["visible_tick"]) + (1 if row["note"].startswith("[SQR]") else 0)
        assert cm.state_dict(coarse[t])[row["variable"]] == row["level"], row
        checked += 1
    assert checked > 60


def test_the_realized_path_reproduces_the_count_at_each_1_january():
    """The owner's decision 7g: count_USSR on the realized path is, on every 1 January from
    1947 to 1992, the band of the record's count of Soviet intercontinental delivery vehicles
    at the end of the year before (data/cw/v1/strategic_launchers.csv), set by the Soviet
    deployments (USSR.heavy_bombers, first_icbms, icbm_buildup, icbm_parity)."""
    coarse, _, _ = realized("opportunist")
    cm = flat_of("opportunist").coarse
    with open(v1.DATA_V1 / "strategic_launchers.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(line for line in fh if not line.startswith("#")))
    assert [int(r["visible_year"]) for r in rows] == list(range(1947, 1993))
    for r in rows:
        if r["total"]:
            total = int(r["total"])
            assert total == int(r["icbm"]) + int(r["slbm"]) + int(r["bombers"]), r["year"]
            assert r["band"] == v1.BANDS[(total > 0) + (total >= 200) + (total >= 1000)]
        else:
            assert r["mark"] == "[U]" and r["band"] == "over_1000", r["year"]
        t = int(r["visible_year"]) - v1.YEAR0
        assert cm.state_dict(coarse[t])["count_USSR"] == r["band"], r["year"]


def test_snapshots_are_up_to_date():
    assert write(SNAPSHOTS, check=True) == []


@pytest.mark.parametrize("aims", HYPS)
def test_hindsight_differs_from_the_realized_path_only_in_the_belief_errors(aims):
    """v0's decisions D6, and the one [SQR] placement of v1: the US-PRC war is on the record
    on 1 Jan 1951 and on the model's path from 1952 (decisions R V1)."""
    coarse, _, _ = realized("opportunist")
    cm = compiled(aims)
    errors = {}
    for year in range(1947, 1993):
        h = cm.state_dict(hindsight(year, aims))
        p = cm.state_dict(coarse[year - 1947])
        diff = {k for k in h if h[k] != p[k] and k != "aims_USSR"}
        if diff:
            errors[year] = diff
    expected = {
        # the projected count above the count in being (decisions D9): the bomber and missile
        # gaps, 1957 to 1962, and the buildup projected past 1,000 before it got there
        **{y: {"belief_force_USA"} for y in [*range(1957, 1963), 1967, 1968]},
        **{y: {"belief_USSR_USA"} for y in [*range(1983, 1986), *range(1988, 1993)]},
    }
    usa_reading = range(1951, 1954) if aims == "opportunist" else range(1947, 1993)
    for y in usa_reading:
        expected[y] = expected.get(y, set()) | {"belief_USA_USSR"}
    expected[1951] = expected.get(1951, set()) | {"esc_usprc"}
    assert errors == expected


# -- well-formedness and sizes (decisions section S) ----------------------------------------
@pytest.mark.parametrize(
    "name,prc_principal,size",
    [("sino_soviet_1969", True, 975), ("sino_soviet_1969", False, 975), ("alert_1973", True, 197)],
)
def test_each_new_sub_game_is_well_formed_from_its_entry(name, prc_principal, size):
    sub = sub_of(name, prc_principal)
    g = explore(sub, max_states=1_000_000)
    assert g.size() == size


@pytest.mark.parametrize("aims", HYPS)
@pytest.mark.parametrize(
    "build", [{}, {"prc_principal": False}, {"us_crisis_options": False}], ids=str
)
def test_every_return_of_every_sub_game_is_a_valid_coarse_transition(aims, build):
    """Each sub-game explored from its entry in the hindsight state of its year, and every
    terminal fine state returned to the coarse game (the exit maps checked as applied)."""
    fm = flat_of(aims, **build)
    years = {
        "berlin_1948": 1948,
        "cuba_1962": 1962,
        "sino_soviet_1969": 1969,
        "alert_1973": 1973,
        "able_archer_1983": 1983,
    }
    for name, year in years.items():
        g, returns, _ = fine_graph(fm, hindsight(year, aims, **build), name)
        assert returns and all(r[fm.index["tick"]] == tick_of(year) + 1 for r in returns.values())


# Explicit state counts of the flattened game from the claims' start states (decisions
# section S), opportunist; each exploration also checks well-formedness (explore raises
# ModelError on an actor without a move, overlapping endings, conflicting Sets, a monotone
# decrease or a bad exit map).
SIZES = [
    ("V3", 1973, 1974, 209),
    ("V5", 1970, 1973, 11407),  # 16274 before the talks flag (decision 7f(a), 2026-10-27)
    ("V5 control", 1968, 1970, 47619),  # 35600 before the talks flag, 35636 before 7g
    ("V2 from 1984", 1984, None, 3440),
    ("V2 from 1983", 1983, None, 4143),
]


@pytest.mark.parametrize("label,year,cut,size", SIZES, ids=[s[0] for s in SIZES])
def test_sizes_of_the_flattened_game_from_the_start_states(label, year, cut, size):
    fm = flat_of("opportunist")
    g = graph(fm, hindsight(year, "opportunist"), None if cut is None else tick_of(cut))
    assert g.size() == size


@pytest.mark.slow
@pytest.mark.parametrize("aims", HYPS)
def test_well_formed_from_1950_to_1954_flattened(aims):
    fm = flat_of(aims)
    g = graph(fm, hindsight(1950, aims), tick_of(1954))
    assert g.size() == {"opportunist": 129549, "status_quo": 18941}[aims]


def test_hold_out_rows_for_v1_spare_the_hold_out():
    """The v1 rows of docs/guard_changelog_cw.md: the model-step row exists; no first-sight
    row exists while FIRST_SIGHT_COMMIT_V1 is None; after it, no row may serve V3, V5 or V6
    (total hold-out, decisions D8)."""
    text = (v1.ROOT / "docs" / "guard_changelog_cw.md").read_text(encoding="utf-8")
    rows = [line for line in text.splitlines() if line.startswith("| 2026")]
    assert any("model step, coded before any of V1 to V10 was run" in r for r in rows)
    marks = [k for k, r in enumerate(rows) if "first sight of V1 to V10" in r]
    if FIRST_SIGHT_COMMIT_V1 is None:
        assert not marks
        return
    assert FIRST_SIGHT_COMMIT_V1 in rows[marks[0]]
    for line in rows[marks[0] + 1 :]:
        claim = line.strip("|").split("|")[1]
        assert not re.search(r"\bV(3|5|6)\b", claim), "V3, V5, V6: total hold-out"
