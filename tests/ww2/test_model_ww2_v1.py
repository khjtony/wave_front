"""Structure of models/ww2/v1.py against docs/ontology_ww2_v1.md, docs/actions_ww2_v1.md and the
architect's decisions E1 to E8 (docs/ww2_v1_decisions.md); the realized replay of E4; the
transcription-drift check against v0; well-formedness from the test start states; and the
hold-out guard on docs/guard_changelog_ww2.md.

These are construction checks, not registered claims; the claims are in tests/ww2/scenarios.
"""

import itertools
import re

import pytest
import z3

from models.ww2 import bounded
from models.ww2.hypotheses import (
    REALIZED_MOVES_V1,
    ROOT,
    SNAPSHOTS_V1,
    fixed_model,
    quarter_tick,
    realized_moves,
    realized_rows,
    snapshot_state,
)
from models.ww2.v0 import model as v0_model
from models.ww2.v1 import SEASON_TICKS, model
from wavefront.bmc.encode import _Translator
from wavefront.evidence import hindsight_ww2_v1 as h1
from wavefront.model import ModelError
from wavefront.model.effects import Bump, Set, SetIf
from wavefront.model.expr import Expr
from wavefront.viz.format import expr_text, guard_text

CM = model.compile()
CM0 = v0_model.compile()
DECLARED = {v.name: v for v in CM.variables if v.origin == "var"}
ADDED = {"north_strike", "german_defeat"}  # v0 model-step additions, kept

# The commit at which the v1 suite was first run whole ("first sight" of the hold-out tests
# T6, T7, T11 and T12; decisions E8). The working tree was uncommitted at that moment: the
# architect's last commit is the base. Every docs/guard_changelog_ww2.md row after the
# first-sight row must name a contemporaneous source and a full rerun.
FIRST_SIGHT_COMMIT = "3d5c55ec8b76c0ad9458a44c5ca96bdc9b1511c6"


def actor(cm, name):
    return next(a for a in cm.actors if a.name == name)


def action(cm, actor_name, name):
    a = actor(cm, actor_name)
    return a.actions[a.action_index(name)]


def declared(m):
    return {(d.actor, d.name): d for a in [*m.actors, m.nature()] for d in a.actions}


# -- variables, actors, sources -------------------------------------------------------------


def test_every_ontology_variable_with_its_levels_order_and_init():
    """The v0 ontology overlaid with the v1 deltas (header-aware: bold level additions, (v0)
    row labels): every variable, level and initial level is declared as written."""
    onto = h1.parse_ontology()
    assert set(DECLARED) == set(onto) | ADDED
    for name, spec in onto.items():
        v = DECLARED[name]
        if name == "ind_GER":  # counter 0..5 at 3, as v0
            assert v.kind == "counter" and v.init == (3,)
            continue
        levels = tuple(str(x) for x in spec["levels"])
        assert v.levels == levels, name
        if spec["init"] is None:
            assert v.init == tuple(range(len(levels))), name
        else:
            assert v.init == (levels.index(str(spec["init"])),), name


def test_monotone_variables():
    """Notes section 3 item 6: every new variable is monotone except w_ussr, caucasus,
    oil_JPN and indochina; commit_US and france stay monotone; belief_GER becomes monotone.
    The 21 include east_offer, added 2026-10-15 on the owner's decision 1."""
    new = set(DECLARED) - {v.name for v in CM0.variables} - {"aims_JPN"}
    assert len(new) == 21 and "east_offer" in new
    not_monotone = {n for n in new if not DECLARED[n].monotone}
    assert not_monotone == {"w_ussr", "caucasus", "oil_JPN", "indochina"}
    for name in ("commit_US", "france", "belief_GER"):
        assert DECLARED[name].monotone
    assert DECLARED["commit_US"].levels[-1] == "total"
    assert DECLARED["france"].levels[-1] == "liberated"


def test_hidden_objectives_actors_and_assumption():
    decl = {d.name: d for d in model.variables if hasattr(d, "hidden_from")}
    assert set(decl["aims_JPN"].hidden_from) == {"GER", "WEST", "USSR"}
    assert decl["aims_JPN"].levels == ("status_quo", "regional", "hegemonic")
    assert list(model.assumes) == ["ussr_defensive"]
    assert len(CM.initial_states()) == 6  # aims_GER x aims_JPN; aims_USSR defensive
    names = [v.name for v in CM.variables]
    assert [n for n in names if n.startswith("last_")] == ["last_GER", "last_WEST", "last_USSR"]
    assert [a.name for a in CM.actors] == ["GER", "WEST", "USSR", "JPN", "Nature"]
    assert model.horizon == 39


def test_sources_speculative_and_hypothesis_gates():
    for a in CM.actors:
        for x in a.actions:
            if not x.is_idle:
                assert x.source.strip(), f"{a.name}.{x.name} has no source"
    spec = sorted(f"{a.name}.{x.name}" for a in CM.actors for x in a.actions if x.speculative)
    # USSR.accept_terms_east: added 2026-10-15 on the owner's decision 1 (speculative).
    assert spec == ["JPN.strike_colonies_only", "USSR.accept_terms_east", "USSR.seek_terms_east"]
    gated = sorted(
        f"{d.actor}.{d.name}"
        for d in declared(model).values()
        if d.guard_parts and d.guard_parts[0][0] == "hypothesis"
    )
    assert gated == sorted(
        [
            "GER.occupy_bohemia",
            "GER.attack_poland",
            "USSR.join_axis",
            "GER.attack_ussr",
            "JPN.occupy_south_indochina",
            "JPN.attack_south",
            "JPN.strike_colonies_only",
            "JPN.strike_north",
        ]
    )
    for d in declared(model).values():  # a hypothesis part is always written first
        assert "hypothesis" not in [p for p, _ in d.guard_parts[1:]]


# The part names of the catalogue (docs/actions_ww2_v1.md), in its order, and the two parts
# the model step had to name (decisions E2 item 10, E3; the module docstring).
PARTS = {
    ("GER", "attack_ussr"): ["hypothesis", "peace", "west_closed", "army_ready", "season"],
    ("GER", "offensive_east"): ["at_war", "front", "army_ready", "season", "reserves"],
    ("GER", "offensive_caucasus"): [
        "at_war",
        "target",
        "flank",
        "army_ready",
        "season",
        "reserves",
    ],
    ("GER", "declare_war_us"): ["not_yet", "japanese_war"],
    ("GER", "negotiate_east"): ["at_war", "feeler"],
    ("GER", "offer_terms_east"): ["at_war", "once"],  # owner's decision 1, 2026-10-15
    ("WEST", "lend_lease"): ["us_policy", "belligerent"],
    ("WEST", "embargo_jpn"): ["instrument", "trade_link", "peace"],
    ("WEST", "lift_embargo"): ["in_force", "peace", "before_clock"],
    ("WEST", "victory_program"): ["programme", "belligerent"],
    ("WEST", "atomic_program"): ["knowledge", "emergency", "once"],
    ("WEST", "bomber_offensive"): ["us_at_war", "us_arms", "once"],
    ("WEST", "invade_italy"): ["target", "us_at_war", "us_arms"],
    ("WEST", "land_france"): [
        "at_war",
        "us_at_war",
        "us_arms",
        "air_superiority",
        "season",
        "france_occupied",
    ],
    ("WEST", "us_declare_war"): ["not_yet", "engaged"],
    ("WEST", "us_declare_war_jpn"): ["colonial_war"],
    ("WEST", "negotiate"): ["occasion", "no_separate_peace"],
    ("WEST", "fight_on"): ["occasion", "no_separate_peace"],
    ("USSR", "mobilize_total"): ["at_war", "once"],
    ("USSR", "counteroffensive"): ["at_war"],
    ("USSR", "seek_terms_east"): ["at_war", "no_separate_peace", "once"],
    ("USSR", "accept_terms_east"): ["offer", "no_separate_peace"],  # owner's decision 1
    ("JPN", "enter_north_indochina"): ["target", "vichy_weak"],
    ("JPN", "occupy_south_indochina"): ["hypothesis", "north_held", "vichy_weak"],
    ("JPN", "withdraw_south_indochina"): ["held", "peace"],
    ("JPN", "attack_south"): ["hypothesis", "us_not_at_war", "fleet", "fuel", "southern_bases"],
    ("JPN", "strike_colonies_only"): ["hypothesis", "peace", "fleet", "fuel", "southern_bases"],
    ("JPN", "offensive_midway"): ["at_war", "first_stage_done", "fleet", "once"],
    ("JPN", "strike_north"): ["hypothesis", "pact", "ussr_collapsing"],
    ("Nature", "purge"): ["officer_corps", "prewar"],
    ("Nature", "italy_enters"): ["axis", "war", "nonbelligerent"],
    ("Nature", "campaign_east_german"): [
        "offensive",
        "front",
        "army_ready",
        "red_army_unmobilized",
        "no_second_front",
    ],
    ("Nature", "campaign_caucasus_german"): ["offensive", "front", "army_ready", "no_second_front"],
    ("Nature", "caucasus_relieved"): ["offensive", "front", "mobilized"],
    ("Nature", "east_liberated"): ["offensive", "front", "mobilized", "german_strain"],
    ("Nature", "german_strain"): ["two_fronts", "soviet_mobilized", "level"],
    ("Nature", "german_exhaustion"): ["strained", "bombing", "two_fronts", "territory_lost"],
    ("Nature", "air_war_won"): ["bombing", "us_arms", "level"],
    ("Nature", "italy_capitulates"): ["landing", "at_war"],
    ("Nature", "campaign_france"): [
        "landing",
        "france_occupied",
        "air_superiority",
        "reserves_bound",
    ],
    ("Nature", "reich_collapses"): ["exhausted", "east", "west", "level"],
    ("Nature", "campaign_south"): ["at_war", "target", "fleet"],
    ("Nature", "midway"): ["operation", "fleet", "at_war"],
    ("Nature", "naval_attrition"): ["at_war", "fleet", "us_arms"],
    ("Nature", "stocks_run_down"): ["embargo", "clock"],
    ("Nature", "sea_lanes_cut"): ["at_war", "fleet", "us_arms", "supply"],
    ("Nature", "atomic"): ["weapon", "at_war", "delivery"],
}
DELAYS = {
    ("GER", "rearm"): 8,
    ("WEST", "rearm"): 4,
    ("USSR", "rearm"): 4,
    ("WEST", "us_rearm"): 4,
    ("WEST", "victory_program"): 5,
    ("WEST", "atomic_program"): 12,
    ("USSR", "mobilize_total"): 3,
}


def test_guard_parts_delays_and_the_oil_clock():
    decl = declared(model)
    for key, parts in PARTS.items():
        assert [p for p, _ in decl[key].guard_parts] == parts, key
    assert {k: d.delay for k, d in decl.items() if d.delay} == DELAYS
    assert not decl[("WEST", "us_rearm")].guard_parts  # catalogue: one unnamed condition
    # E3: the clock part reads the built-in fairness counter of oil_clock.
    clock = dict(decl[("Nature", "stocks_run_down")].guard_parts)["clock"]
    assert "fair_oil_clock" in clock.free_vars()
    (f,) = [f for f in model.fairness_constraints if f.name == "oil_clock"]
    assert (f.actor, f.within, f.responses) == (
        "Nature",
        8,
        ("stocks_run_down", "campaign_rhineland"),
    )
    assert expr_text(f.trigger, CM) == 'V.oil_JPN == "embargoed"'
    # E2 item 4: every raise of commit_US to total is a clamped Bump(+3).
    raisers = sorted(
        f"{d.actor}.{d.name}"
        for d in decl.values()
        for e in d.effects
        if isinstance(e, Bump) and e.var == "commit_US"
    )
    assert raisers == [
        "GER.declare_war_us",
        "JPN.attack_south",
        "WEST.us_declare_war",
        "WEST.us_declare_war_jpn",
    ]
    for d in decl.values():
        for e in d.effects:
            if isinstance(e, Bump) and e.var == "commit_US":
                assert (e.amount, e.strict) == (3, False)
    assert SEASON_TICKS == tuple(t for t in range(39) if t % 4 in (1, 2))
    assert SEASON_TICKS[:4] == (1, 2, 5, 6) and SEASON_TICKS[-1] == 38


def test_owners_decision_1_the_german_offer_in_the_east():
    """The two actions of the content decision of docs/german_exit_1941_1945.md (owner's
    decision 1, 2026-10-15, an edit after first sight): a documented, refused German offer
    and a speculative Soviet acceptance, the latter closed by the alliance that the attack
    sets, so from the T7 start state (alliance set) it is unavailable whatever is offered."""
    decl = declared(model)
    offer, accept = decl[("GER", "offer_terms_east")], decl[("USSR", "accept_terms_east")]
    assert [(p, expr_text(e, CM)) for p, e in offer.guard_parts] == [
        ("at_war", "V.east_war"),
        ("once", "not V.east_offer"),
    ]
    assert [(p, expr_text(e, CM)) for p, e in accept.guard_parts] == [
        ("offer", "V.east_offer"),
        ("no_separate_peace", "not V.anglo_soviet_alliance"),
    ]
    assert [effect_text(e, CM) for e in offer.effects] == ["Set(east_offer, True)"]
    assert [effect_text(e, CM) for e in accept.effects] == ["Set(east_peace, True)"]
    assert not offer.speculative and accept.speculative
    assert not offer.delay and not accept.delay
    for text in ("Ribbentrop", "Oshima, 29 Jul 1943", "Goebbels's diary, Sep 1943"):
        assert text in offer.source
    for text in ("No Soviet decision record", "Stockholm", "Koch", "Mastny"):
        assert text in accept.source
    assert DECLARED["east_offer"].monotone and DECLARED["east_offer"].init == (0,)
    s = list(
        snapshot_state(
            CM, "1941Q2", "hegemonic", builtins=True, snapshots=SNAPSHOTS_V1, aims_JPN="hegemonic"
        )
    )
    s[CM.index["east_offer"]] = 1
    ussr = actor(CM, "USSR")
    assert ussr.action_index("accept_terms_east") not in CM.available(tuple(s))[ussr.index]


def test_constraints_profiles_invariants():
    assert [f.name for f in model.fairness_constraints] == [
        "democratic_response",
        "czech_obligation",
        "rhineland_resolution",
        "oil_clock",
    ]
    profiles = {p.name: p for p in model.profiles}
    assert list(profiles) == ["fight_on", "appeaser", "electoral", "embargo_maintained", "deterred"]
    assert profiles["electoral"].forbid == ("us_declare_war", "us_declare_war_jpn")
    assert expr_text(profiles["electoral"].unless, CM) == 'V.pacific_war in ["war", "surrendered"]'
    assert profiles["embargo_maintained"].forbid == ("lift_embargo",)
    assert profiles["deterred"].actor == "GER" and profiles["deterred"].forbid == ("attack_poland",)
    assert list(model.invariants) == [
        "balance_europe",
        "balance_asia",
        "commitment_alive",
        "peace_europe",
        "undefeated",
        "poland_blocked",
        "european_peace",
        "european_peace_t20",
    ]
    assert list(model.endings) == [
        "GERMAN_DEFEAT",
        "NEGOTIATED_PEACE",
        "AXIS_HEGEMONY_EUROPE",
        "JPN_CONQUERS_USSR",
        "USSR_JOINS_AXIS",
        "ALLIED_VICTORY",
        "AXIS_HEGEMONY_ASIA",
        "PACIFIC_WAR_CONTINUES",
        "NO_GENERAL_WAR",
        "LIMITED_WAR",
        "WAR_UNRESOLVED",
    ]


# The catalogue's parameter budget (docs/actions_ww2_v1.md, "Parameter budget (v1 draft)")
# and what budget() reports. Differences from the catalogue are reported, not tuned: one
# profile more (deterred, adopted for T9 by decisions E5 after the catalogue was written).
CATALOGUE = {
    "actions_by_actor": {"GER": 20, "WEST": 20, "USSR": 8, "JPN": 8},
    "nature_events": 28,
    "speculative": 2,
    "hypothesis_gates": 8,
    "delays": 7,
    "fairness": 4,
    "profiles": 4,
    "assume": 1,
    "variables_added": 21,
}
# Added after first sight on the owner's decision 1 of 2026-10-15 (docs/german_exit_1941_1945.md;
# docs/guard_changelog_ww2.md): GER offer_terms_east, USSR accept_terms_east (speculative) and
# the flag east_offer. Before: actions 84, guards 84, guard_parts 202, speculative 2,
# variables 55, levels 141, assumptions 207.
DECISION_1 = {
    "actions_by_actor": {"GER": 1, "USSR": 1},
    "speculative": 1,
    "variables_added": 1,
}


def test_parameter_budget(capsys):
    b = CM.budget()
    with capsys.disabled():
        print("\nWW2 v1 budget():", {k: v for k, v in b.items() if k != "state_space_bound"})
    by_actor = {a.name: len(a.actions) - 1 for a in CM.actors}
    expected = {
        k: n + DECISION_1["actions_by_actor"].get(k, 0)
        for k, n in CATALOGUE["actions_by_actor"].items()
    }
    assert by_actor == {**expected, "Nature": CATALOGUE["nature_events"]}
    assert b["actions"] == 56 + 2 + 28
    assert b["speculative_actions"] == CATALOGUE["speculative"] + DECISION_1["speculative"]
    assert b["delays"] == CATALOGUE["delays"]
    assert b["fairness_constraints"] == CATALOGUE["fairness"]
    assert len(model.assumes) == CATALOGUE["assume"]
    assert len(model.profiles) == CATALOGUE["profiles"] + 1  # + deterred (decisions E5)
    added = CATALOGUE["variables_added"] + DECISION_1["variables_added"]
    assert b["variables"] - 34 == added  # v0 declares 34
    assert {
        k: b[k]
        for k in (
            "variables",
            "levels",
            "actions",
            "guards",
            "guard_parts",
            "latches",
            "invariants",
            "endings",
            "builtin_variables",
        )
    } == {
        "variables": 56,
        "levels": 143,
        "actions": 86,
        "guards": 86,
        "guard_parts": 206,
        "latches": 1,
        "invariants": 8,
        "endings": 11,
        "builtin_variables": 16,
    }
    assert len(CM.assumptions()) == 211


# -- transcription drift against v0 ----------------------------------------------------------


def effect_text(e, cm):
    def value(v):
        return expr_text(v, cm) if isinstance(v, Expr) else repr(v)

    if isinstance(e, SetIf):
        return f"SetIf({expr_text(e.cond, cm)}, {e.var}, {value(e.value)})"
    if isinstance(e, Set):
        return f"Set({e.var}, {value(e.value)})"
    if isinstance(e, Bump):
        return f"Bump({e.var}, {e.amount}, strict={e.strict})"
    raise AssertionError(type(e))


def spec_of(cm, a, x):
    return {
        "guard": guard_text(x, cm),
        "effects": [effect_text(e, cm) for e in x.effects],
        "delay": x.delay,
        "source": x.source,
        "speculative": x.speculative,
    }


# Changed v0 actions (docs/actions_ww2_v1.md, "Changed v0 actions"; decisions E2 item 10).
CHANGED = {
    ("WEST", "negotiate"),
    ("WEST", "fight_on"),
    ("WEST", "guarantee_poland"),
    ("WEST", "declare_war"),
    ("JPN", "strike_north"),
    ("Nature", "purge"),
}


def test_shared_actions_are_v0_verbatim_except_the_changed_ones():
    """Every action and event v1 shares with v0 has the same guard text, effects, delay,
    source and speculative tag, except the six the catalogue changes; for those, exactly the
    documented change."""
    shared = 0
    for a0 in CM0.actors:
        a1 = actor(CM, a0.name)
        for x0 in a0.actions:
            if x0.is_idle:
                continue
            x1 = a1.actions[a1.action_index(x0.name)]
            s0, s1 = spec_of(CM0, a0, x0), spec_of(CM, a1, x1)
            shared += 1
            if (a0.name, x0.name) not in CHANGED:
                assert s1 == s0, (a0.name, x0.name)
                continue
            parts0 = dict(x0.guard_parts)
            parts1 = dict(x1.guard_parts)
            if x0.name in ("negotiate", "fight_on"):
                assert expr_text(parts1["occasion"], CM) == s0["guard"]
                assert expr_text(parts1["no_separate_peace"], CM) == (
                    "not (V.anglo_soviet_alliance and V.east_war)"
                )
                assert {k: s1[k] for k in ("effects", "delay", "source", "speculative")} == {
                    k: s0[k] for k in ("effects", "delay", "source", "speculative")
                }
            elif x0.name == "guarantee_poland":
                assert s1["guard"] == s0["guard"]
                assert s1["effects"] == [
                    *s0["effects"],
                    "SetIf(V.belief_GER < \"uncertain\", belief_GER, 'uncertain')",
                ]
                assert s1["source"] == s0["source"]
            elif x0.name == "declare_war":
                assert s1["guard"] == s0["guard"]
                assert s1["effects"] == [*s0["effects"], "Set(belief_GER, 'will_fight')"]
                assert s1["source"] == s0["source"]
            elif x0.name == "strike_north":
                assert list(parts0) == ["pact", "army_free", "ussr_weak"]
                assert expr_text(parts1["pact"], CM) == expr_text(parts0["pact"], CM0)
                assert expr_text(parts1["ussr_collapsing"], CM) == 'V.w_ussr == "german"'
                assert s1["effects"] == s0["effects"]
                assert s0["speculative"] and not s1["speculative"]
            elif x0.name == "purge":
                assert expr_text(parts1["officer_corps"], CM) == s0["guard"]
                assert expr_text(parts1["prewar"], CM) == "not V.east_war"
                assert {k: s1[k] for k in ("effects", "delay", "source")} == {
                    k: s0[k] for k in ("effects", "delay", "source")
                }
    assert shared == 42


def test_shared_constraints_latch_and_invariant_are_v0_verbatim():
    f0 = {f.name: f for f in v0_model.fairness_constraints}
    for f in model.fairness_constraints:
        if f.name in f0:
            g = f0[f.name]
            assert (f.actor, f.within, f.responses) == (g.actor, g.within, g.responses)
            assert expr_text(f.trigger, CM) == expr_text(g.trigger, CM0)
    p0 = {p.name: p for p in v0_model.profiles}
    for p in model.profiles:
        if p.name in p0:
            q = p0[p.name]
            assert (p.actor, p.forbid) == (q.actor, q.forbid)
            assert expr_text(p.unless, CM) == expr_text(q.unless, CM0)
    assert expr_text(model.assumes["ussr_defensive"], CM) == expr_text(
        v0_model.assumes["ussr_defensive"], CM0
    )
    assert expr_text(model.invariants["commitment_alive"], CM) == expr_text(
        v0_model.invariants["commitment_alive"], CM0
    )
    (l1,), (l0,) = model.latches, v0_model.latches
    assert (l1.name, l1.of, expr_text(l1.when, CM)) == (l0.name, l0.of, expr_text(l0.when, CM0))


# -- endings ---------------------------------------------------------------------------------


def test_endings_are_mutually_exclusive_and_cover_the_horizon():
    """For every pair of endings, no state satisfies both (Z3 over the whole state domain);
    every state at the horizon satisfies one."""
    tr = _Translator(CM)
    s = [z3.Int(v.name) for v in CM.variables]
    dom = [z3.And(x >= 0, x < v.size) for x, v in zip(s, CM.variables, strict=True)]
    ends = {n: tr.boolean(e, s) for n, e in model.endings.items()}
    solver = z3.Solver()
    solver.add(*dom)
    for a, b in itertools.combinations(ends, 2):
        assert solver.check(ends[a], ends[b]) == z3.unsat, (a, b)
    solver.add(s[CM.index["tick"]] == 39)
    assert solver.check(z3.Not(z3.Or(*ends.values()))) == z3.unsat
    # Before the horizon only the absorbing endings can hold.
    early = z3.Solver()
    early.add(*dom, s[CM.index["tick"]] < 39)
    for name in ("AXIS_HEGEMONY_ASIA", "PACIFIC_WAR_CONTINUES", "NO_GENERAL_WAR"):
        assert early.check(ends[name]) == z3.unsat
    for name in ("LIMITED_WAR", "WAR_UNRESOLVED"):
        assert early.check(ends[name]) == z3.unsat


# -- snapshots and the realized replay (decisions E4) ----------------------------------------


@pytest.mark.parametrize("aims_JPN", ["status_quo", "regional", "hegemonic"])
def test_tick0_snapshot_is_the_initial_state(aims_JPN):
    for aims in ("revisionist", "hegemonic"):
        s = snapshot_state(CM, "1935Q4", aims, snapshots=SNAPSHOTS_V1, aims_JPN=aims_JPN)
        assert s in CM.initial_states()
        fixed = fixed_model(model, aims_GER=aims, aims_JPN=aims_JPN).compile()
        assert fixed.initial_states() == [s]


def test_every_v1_snapshot_loads_at_its_tick_with_its_built_ins():
    files = sorted(p.stem for p in SNAPSHOTS_V1.glob("*.json"))
    assert len(files) == 40 and files[0] == "1935Q4" and files[-1] == "1945Q3"
    for q in files:
        s = snapshot_state(
            CM, q, "hegemonic", builtins=True, snapshots=SNAPSHOTS_V1, aims_JPN="hegemonic"
        )
        assert s[CM.index["tick"]] == quarter_tick(q)
    assert quarter_tick("1945Q3") == 39
    with pytest.raises(ModelError):
        fixed_model(model, arms_USA="high")  # not swept


def replay(aims_JPN):
    cm = fixed_model(model, aims_GER="hegemonic", aims_JPN=aims_JPN).compile()
    (s,) = cm.initial_states()
    return cm, bounded.replay(cm, s, realized_moves(cm, REALIZED_MOVES_V1))


@pytest.mark.parametrize("aims_JPN", ["regional", "hegemonic"])
def test_realized_replay_reaches_allied_victory(aims_JPN):
    """E4: every row of realized_moves_v1.csv is available at its tick from the tick-0 state
    (aims_GER hegemonic, aims_USSR defensive), with no relaxation and no profile, and the
    chain ends at tick 39 in ALLIED_VICTORY."""
    cm, states = replay(aims_JPN)
    assert len(states) == 40 == len(realized_rows(REALIZED_MOVES_V1)) + 1
    assert cm.state_dict(states[-1])["tick"] == "39"
    assert cm.ending_of(states[-1]) == "ALLIED_VICTORY"
    assert all(cm.ending_of(s) is None for s in states[:-1])


def test_realized_replay_under_status_quo_stops_at_the_southern_occupation():
    """E4: under aims_JPN = status_quo the realized row of 1941Q3 (occupy_south_indochina) is
    unavailable: the hypothesis's content."""
    with pytest.raises(ValueError, match="tick 22: JPN.occupy_south_indochina unavailable"):
        replay("status_quo")


# Differences between the v1 hindsight snapshots (with built-ins) and the realized replay,
# variable by variable at the end of each quarter, with the reason (reports/ww2_v1.md
# section 3 tabulates them; snapshots/ww2/hindsight_v1/README.md explains each). The five
# one-tick lags of the record behind the model's clock (belief_WEST 1938Q2, arms_GER 1938Q3,
# anglo_soviet_alliance 1941Q2, caucasus 1942Q2, bomb_ready 1945Q2) are gone since the
# clock-consistency pass of the builder (owner's decision 7 of 2026-10-15); italy at 1940Q1
# is an [NSL] placement and stays. oil_GER at 1939Q3 and 1939Q4 (accept_pact against the
# record's deliveries of Feb 1940) left the list on 2026-10-23: the v1 series dates secured from
# the credit agreement of 19 Aug 1939 (owner's decision 2d; docs/guard_changelog_ww2.md).
EXPECTED_DIFFERENCES = {
    "treaty": ({"1936Q1", "1936Q2"}, "[SQR] locarno_lapses at tick 2 (v0)"),
    "arms_WEST": (
        {"1936Q3", "1936Q4", "1939Q1", "1939Q2", "1939Q3"},
        "NMC reading against the delay-4 programme (v0)",
    ),
    "arms_GER": (
        {"1940Q4", "1941Q1", "1941Q2", "1941Q3", "1941Q4"},
        "total lands at tick 20 against the record's 1942 (E2 item 9); not a one-tick lag",
    ),
    "arms_USSR": (
        {f"{y}Q{q}" for y in (1939, 1940) for q in range(1, 5)} | {"1938Q4", "1941Q1"},
        "the record's Nov 1938 against the model's rearm of 1940Q2 landing at tick 22 (v0)",
    ),
    "commit_WEST": ({"1939Q1"}, "[SQR] guarantee_poland (v0)"),
    "polish_guarantee": ({"1939Q1"}, "[SQR] guarantee_poland (v0)"),
    "fair_democratic_response": (
        {"1939Q1"},
        "E1 counts on the snapshot's levels (commit_WEST resolved, 31 Mar 1939); the replay "
        "has the guarantee one tick later",
    ),
    "poland": ({"1939Q3"}, "[SQR] occupy_east_poland (v0)"),
    "italy": ({"1940Q1"}, "[NSL] italy_enters at the decision in principle (31 Mar 1940)"),
    "arms_USA": (
        {"1940Q3", "1940Q4", "1941Q1", "1941Q2", "1943Q1"},
        "NMC annual reading against the delay-4 and delay-5 programmes",
    ),
    "balkans": ({"1940Q3"}, "align_balkans at tick 19 (v0)"),
    "war_us_ger": ({"1941Q4"}, "[SQR] declare_war_us"),
    "jpn_navy": ({"1942Q2"}, "[SQR] midway"),
    "w_ussr": ({"1944Q1"}, "east_liberated placed at 1944Q2; the Prut reached 26 Mar 1944"),
    "exhaustion_GER": ({"1944Q3"}, "[NSL] german_exhaustion"),
}


def replay_differences(aims_JPN):
    cm, states = replay(aims_JPN)
    out = {}
    for q in [h1.TICK0, *h1.QUARTERS]:
        loaded = snapshot_state(
            cm, q, "hegemonic", builtins=True, snapshots=SNAPSHOTS_V1, aims_JPN=aims_JPN
        )
        rep = states[quarter_tick(q)]
        for i, v in enumerate(cm.variables):
            if loaded[i] != rep[i]:
                out.setdefault(v.name, []).append(
                    (q, cm.level_name(i, loaded[i]), cm.level_name(i, rep[i]))
                )
    return out


@pytest.mark.parametrize("aims_JPN", ["regional", "hegemonic"])
def test_replay_against_the_v1_snapshots(aims_JPN):
    """E4: the replayed state at the end of each quarter against the v1 snapshot loaded with
    its built-ins; every difference is one of EXPECTED_DIFFERENCES. Pending counters, last
    actions, the latch and the oil clock agree everywhere."""
    diffs = replay_differences(aims_JPN)
    assert {k: {q for q, _, _ in v} for k, v in diffs.items()} == {
        k: quarters for k, (quarters, _) in EXPECTED_DIFFERENCES.items()
    }
    builtin = {v.name for v in CM.variables if v.origin in ("latch", "pending", "last", "fair")}
    assert set(diffs) & builtin == {"fair_democratic_response"}


# -- well-formedness (decisions E3) ----------------------------------------------------------

STARTS = [
    ("1945Q1", "hegemonic"),  # T12
    ("1941Q2", "hegemonic"),  # T7
    ("1941Q1", "hegemonic"),  # T6
    ("1940Q4", "hegemonic"),  # T11
    ("1939Q1", "hegemonic"),  # T9
    ("1938Q2", "hegemonic"),  # T3
    ("1938Q2", "revisionist"),  # T3
    ("1935Q4", "hegemonic"),  # tick 0
    ("1935Q4", "revisionist"),  # tick 0
]


def wellformed(quarter, aims_GER, aims_JPN):
    s = snapshot_state(
        CM, quarter, aims_GER, builtins=True, snapshots=SNAPSHOTS_V1, aims_JPN=aims_JPN
    )
    return [name for name, _ in bounded.wellformed_from(CM, s)]


def test_wellformed_from_the_t12_start():
    """No state reachable from the T12 start (1945Q1.json, tick 37) has a joint move on
    which the explicit engine would raise (bounded check to the horizon)."""
    for aims_JPN in ("status_quo", "regional", "hegemonic"):
        assert wellformed("1945Q1", "hegemonic", aims_JPN) == []


@pytest.mark.slow
@pytest.mark.parametrize(("quarter", "aims_GER"), STARTS[1:])
@pytest.mark.parametrize("aims_JPN", ["status_quo", "regional", "hegemonic"])
def test_wellformed_from_every_test_start(quarter, aims_GER, aims_JPN):
    """As above from every v1 test start state and from tick 0, to the horizon: no actor
    without an available action, no two different Sets of one variable in one joint move, no
    monotone decrease (the bounded hazard check of models/ww2/bounded.py)."""
    assert wellformed(quarter, aims_GER, aims_JPN) == []


def test_the_e3_conflict_is_found_without_the_edit():
    """The hazard check finds the conflict that decisions E3 removed: with the part
    lift_embargo:before_clock relaxed, lift_embargo and the forced stocks_run_down set oil_JPN
    differently in one joint move."""
    cm = model.compile(relax={"WEST.lift_embargo:before_clock"})
    s = snapshot_state(
        CM, "1941Q2", "hegemonic", builtins=True, snapshots=SNAPSHOTS_V1, aims_JPN="hegemonic"
    )
    found = [name for name, _ in bounded.wellformed_from(cm, s)]
    assert found == ["WEST.lift_embargo and Nature.stocks_run_down set oil_JPN differently"]


# -- the snapshot builder's built-ins are the model's ----------------------------------------


def test_builder_built_ins_and_triggers_are_the_models():
    names = [v.name for v in CM.variables if v.origin in ("latch", "pending", "last", "fair")]
    assert list(h1.BUILTIN_NAMES) == names
    assert {(a.name, x.name): x.delay for a in CM.actors for x in a.actions if x.delay} == (
        h1.DELAYED
    )
    assert tuple(a.name for a in model.actors if a.remember_last) == h1.REMEMBER_LAST
    for f, g in zip(model.fairness_constraints, h1.FAIRNESS, strict=True):
        assert (f.name, f.actor, f.within, f.responses) == (g.name, g.actor, g.within, g.responses)
        words = expr_text(f.trigger, CM).replace("V.", "").replace('"', "")
        assert words == g.trigger_text, f.name
    # The builder's triggers agree with the model's compiled triggers on every snapshot.
    for q in [h1.TICK0, *h1.QUARTERS]:
        s = snapshot_state(
            CM, q, "hegemonic", builtins=True, snapshots=SNAPSHOTS_V1, aims_JPN="hegemonic"
        )
        d = CM.state_dict(s)
        levels = {v.name: _level(v.name, d[v.name]) for v in h1.VARIABLES}
        last = {a: d.get(f"last_{a}", "none") for a in ("GER", "WEST", "USSR")}
        for f, g in zip(model.fairness_constraints, h1.FAIRNESS, strict=True):
            assert bool(CM.evaluate(f.trigger, s)) == g.trigger(levels, last), (q, f.name)


def _level(name, text):
    var = h1.BY_NAME[name]
    if var.kind == "flag":
        return text == "True"
    if var.kind == "integer":
        return int(text)
    return text


# -- the hold-out record (decisions E8) ------------------------------------------------------

CHANGELOG = ROOT / "docs" / "guard_changelog_ww2.md"


def changelog_rows():
    rows = []
    for line in CHANGELOG.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| 20"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(dict(zip(["date", "test", "change", "source", "budget", "rerun"], cells)))
    return rows


def test_hold_out_rows_after_first_sight_name_a_source():
    """Every guard-changelog row after the first-sight row (the row that records the commit
    of the first whole run of the v1 suite) names a contemporaneous source and a rerun of the
    whole suite; the first-sight row names FIRST_SIGHT_COMMIT."""
    rows = changelog_rows()
    marks = [k for k, r in enumerate(rows) if "first sight" in r["test"].lower()]
    assert len(marks) == 1, "exactly one first-sight row"
    mark = rows[marks[0]]
    assert re.search(r"\b[0-9a-f]{7,40}\b", mark["change"])
    assert FIRST_SIGHT_COMMIT[:7] in mark["change"]
    for r in rows[marks[0] + 1 :]:
        assert r["source"] and r["source"].lower() not in ("n/a", "(none)", "none", "-"), r
        assert r["rerun"].lower().startswith("yes"), r
