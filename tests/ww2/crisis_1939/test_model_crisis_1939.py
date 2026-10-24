"""Structure of models/ww2/crises/summer_1939.py against docs/ontology_crisis_1939.md,
docs/actions_crisis_1939.md and docs/crisis_1939_decisions.md; well-formedness from the entry
state; the parameter budget; the realized replay; the exit check against v1; the
bisimulation of the full and reduced builds; and the hold-out guard on
docs/guard_changelog_ww2.md.

These are construction checks, not registered claims; the claims are test_K01 to test_K06.
"""

import csv
import datetime
import re

import pytest

from models.ww2.crises import summer_1939 as crisis
from tests.ww2.crisis_1939 import common
from wavefront.engine import explore
from wavefront.model import ModelError
from wavefront.model.effects import SetIf

FULL = crisis.build().compile()
REDUCED = crisis.build(inert=False).compile()

# The commit at which tests/ww2/crisis_1939 was first run whole (K1 to K6 in one go; the
# working tree uncommitted, so the commit is the base the run's files sat on). Every
# docs/guard_changelog_ww2.md row after the crisis first-run row names a source and a rerun.
FIRST_RUN_COMMIT = "f00e5be3d27c578d009383bb81fdcd7d3ea6a6de"


def act(cm, actor, name):
    a = next(x for x in cm.actors if x.name == actor)
    return a.actions[a.action_index(name)]


# -- calendar, variables, actions ----------------------------------------------------------


def test_calendar():
    d = datetime.date
    assert crisis.tick_of(d(1939, 7, 5)) == 0
    assert crisis.tick_of(d(1939, 8, 14)) == 13  # Voroshilov's question
    assert crisis.tick_of(d(1939, 8, 21)) == 15  # the break-off
    assert crisis.tick_of(d(1939, 8, 23)) == 16  # the pact
    assert crisis.tick_of(d(1939, 8, 25)) == 17  # order, halt, treaty, Mussolini
    assert crisis.tick_of(d(1939, 8, 26)) == 17  # Y-day
    assert crisis.tick_of(d(1939, 9, 1)) == 19  # the attack
    assert crisis.tick_of(d(1939, 9, 3)) == 20 == crisis.HORIZON
    assert crisis.tick_days(17) == (d(1939, 8, 25), d(1939, 8, 27))
    with pytest.raises(ValueError):
        crisis.tick_of(d(1939, 9, 4))


def test_variables_levels_and_initial_values():
    expected = {
        "aims_GER": (["revisionist", "hegemonic"], None),
        "aims_USSR": (["defensive", "opportunist"], None),
        "talks": (["political", "military", "adjourned", "broken"], "political"),
        "passage": (["unasked", "asked", "refused", "granted"], "unasked"),
        "west_powers": (["False", "True"], "False"),
        "alliance": (["False", "True"], "False"),
        "german_approach": (["none", "opened", "pact_proposed", "pact"], "none"),
        "attack_order": (["none", "ordered", "cancelled", "launched"], "none"),
        "british_treaty": (["none", "guarantee", "treaty"], "guarantee"),
        "belief_GER": (["will_not_fight", "uncertain", "will_fight"], "uncertain"),
        "war_declared": (["False", "True"], "False"),
        "mobilization_POL": (["none", "partial", "general"], "none"),
        "italy_ready": (["unknown", "not_ready"], "unknown"),
    }
    declared = {v.name: v for v in FULL.variables if v.origin == "var"}
    assert list(declared) == list(expected)
    for name, (levels, init) in expected.items():
        v = declared[name]
        assert [str(x) for x in v.levels] == levels, name
        if init is None:
            assert len(v.init) == len(levels), name
        else:
            assert [str(v.levels[i]) for i in v.init] == [init], name
    monotone = {v.name for v in declared.values() if v.monotone}
    assert monotone == {
        "passage",
        "west_powers",
        "alliance",
        "german_approach",
        "british_treaty",
        "belief_GER",
        "war_declared",
        "mobilization_POL",
        "italy_ready",
    }
    assert {v.name for v in REDUCED.variables if v.origin == "var"} == set(declared) - {
        "mobilization_POL",
        "italy_ready",
    }


CATALOGUE = {
    ("GER", "open_approach"): ["first", "free"],
    ("GER", "propose_pact"): ["opened", "free"],
    ("GER", "order_attack"): ["standing"],
    ("GER", "cancel_attack"): ["standing"],
    ("GER", "attack_poland"): ["hypothesis", "order", "readiness"],
    ("WEST", "send_missions"): ["political"],
    ("WEST", "authorize_convention"): ["in_session", "once"],
    ("WEST", "warn_germany"): ["guarantee"],
    ("WEST", "sign_treaty"): ["once"],
    ("WEST", "declare_war"): ["attack", "guarantee", "once"],
    ("USSR", "ask_passage"): ["in_session", "first"],
    ("USSR", "adjourn_talks"): ["in_session"],
    ("USSR", "break_talks"): ["open", "no_alliance"],
    ("USSR", "accept_pact"): ["proposal", "free"],
    ("USSR", "conclude_alliance"): ["no_pact", "in_session", "powers", "passage", "once"],
    ("USSR", "conclude_without_passage"): [
        "no_pact",
        "in_session",
        "powers",
        "no_consent",
        "once",
    ],
    ("Nature", "passage_refused"): ["question"],
    ("Nature", "passage_granted"): ["question"],
    ("Nature", "mobilize_partial"): ["first"],
    ("Nature", "mobilize_general"): ["partial"],
    ("Nature", "italy_declines"): ["first"],
}


def test_actions_parts_sources_delays_and_speculative_tag():
    found = {(a.name, x.name): x for a in FULL.actors for x in a.actions if not x.is_idle}
    assert set(found) == set(CATALOGUE)
    for key, parts in CATALOGUE.items():
        x = found[key]
        assert [p for p, _ in x.guard_parts] == parts, key
        assert x.source and len(x.source) > 40, key
        assert x.speculative == (key == ("USSR", "conclude_without_passage")), key
        assert x.delay == (5 if key == ("WEST", "send_missions") else 0), key
    # the hypothesis gate is v1's, and only on the attack
    gated = [
        k
        for k, x in found.items()
        if "aims_GER" in str(x.guard_expr) or "aims_USSR" in str(x.guard_expr)
    ]
    assert gated == [("GER", "attack_poland")]
    assert isinstance(act(FULL, "WEST", "send_missions").effects[0], SetIf)
    # the delay is the one of data/ww2/crises/1939/decisions.csv
    with open(crisis.DECISIONS, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert [(r["actor"], r["action"], int(r["delay_ticks"]), int(r["tick"])) for r in rows] == [
        ("WEST", "send_missions", 5, 6)
    ]
    assert crisis.tick_of(datetime.date.fromisoformat(rows[0]["date"])) == 6


def test_constraints_and_profiles():
    m = crisis.build()
    assert [(f.name, f.actor, f.within, list(f.responses)) for f in m.fairness_constraints] == [
        ("polish_obligation", "WEST", 1, ["declare_war"])
    ]
    assert [p.name for p in m.profiles] == [
        "deterred",
        "documented_only",
        "no_belief_raise",
        "no_german_proposal",
    ]
    for passage in ("granted", "refused"):
        ms = crisis.build(passage=passage)
        assert [f.name for f in ms.fairness_constraints] == [
            "polish_obligation",
            "scenario_passage",
        ]
        cm = ms.compile()
        nature = next(a for a in cm.actors if a.is_nature)
        names = {x.name for x in nature.actions}
        assert ("passage_granted" in names) == (passage == "granted")
        assert ("passage_refused" in names) == (passage == "refused")
    with pytest.raises(ModelError):
        crisis.build(passage="maybe")


def test_parameter_budget(capsys):
    b = FULL.budget()
    assert {
        k: b[k]
        for k in (
            "variables",
            "levels",
            "actors",
            "actions",
            "guards",
            "guard_parts",
            "speculative_actions",
            "fairness_constraints",
            "delays",
            "cadence",
            "latches",
            "invariants",
            "endings",
            "builtin_variables",
        )
    } == {
        "variables": 13,
        "levels": 37,
        "actors": 4,
        "actions": 21,
        "guards": 21,
        "guard_parts": 39,
        "speculative_actions": 1,
        "fairness_constraints": 1,
        "delays": 1,
        "cadence": 0,
        "latches": 0,
        "invariants": 3,
        "endings": 2,
        "builtin_variables": 3,
    }
    r = REDUCED.budget()
    assert (r["variables"], r["actions"], r["guards"], r["guard_parts"]) == (11, 18, 18, 36)
    with capsys.disabled():
        print(f"\nbudget (full build): {b}\nbudget (reduced build): {r}")


# -- entry, data files ----------------------------------------------------------------------


def test_entry_state_from_1939q2():
    cm = FULL
    s = cm.state_dict(common.entry(cm))
    assert {
        k: s[k]
        for k in (
            "tick",
            "aims_GER",
            "aims_USSR",
            "talks",
            "passage",
            "west_powers",
            "alliance",
            "german_approach",
            "attack_order",
            "british_treaty",
            "belief_GER",
            "war_declared",
            "mobilization_POL",
            "italy_ready",
        )
    } == {
        "tick": "0",
        "aims_GER": "hegemonic",
        "aims_USSR": "defensive",
        "talks": "political",
        "passage": "unasked",
        "west_powers": "False",
        "alliance": "False",
        "german_approach": "none",
        "attack_order": "none",
        "british_treaty": "guarantee",
        "belief_GER": "uncertain",
        "war_declared": "False",
        "mobilization_POL": "none",
        "italy_ready": "unknown",
    }
    # the coarse entry state is the one A2 names
    c = common.COARSE_Q2
    assert (c["tick"], c["arms_GER"], c["polish_guarantee"], c["nazi_soviet_pact"]) == (
        "14",
        "high",
        "True",
        "False",
    )
    assert (c["anglo_soviet_alliance"], c["belief_GER"], c["poland"]) == (
        "False",
        "uncertain",
        "independent",
    )
    # from a state after the crisis (1939Q3), the entry map gives the settled values
    q3 = dict(common.COARSE_Q2)
    q3.update(nazi_soviet_pact="True", poland="german", war_west_ger="war", belief_GER="will_fight")
    e = crisis.entry(q3)
    assert (e["german_approach"], e["talks"], e["attack_order"], e["war_declared"]) == (
        "pact",
        "broken",
        "launched",
        True,
    )


def test_data_files_are_consistent_with_the_calendar_and_the_model():
    rows = crisis.realized_rows()
    assert len(rows) == crisis.HORIZON
    for k, row in enumerate(rows):
        first, last = crisis.tick_days(k)
        assert (row["first_day"], row["last_day"]) == (first.isoformat(), last.isoformat())
        for a in FULL.actors:
            a.action_index(row[a.name])  # raises if unknown
        assert row["source"], k
    with open(crisis.EVENTS, newline="", encoding="utf-8") as fh:
        events = list(csv.DictReader(line for line in fh if not line.startswith("#")))
    levels = {v.name: [str(x) for x in v.levels] for v in FULL.variables}
    for e in events:
        day = datetime.date.fromisoformat(e["date"])
        if day < crisis.TICK0:
            assert e["tick"] == "", e
        else:
            assert int(e["tick"]) == crisis.tick_of(day), e
        assert e["level"] in levels[e["variable"]], e
        assert e["source"], e


# -- well-formedness ------------------------------------------------------------------------

PROFILES = [
    None,
    "deterred",
    ("deterred", "documented_only"),
    ("deterred", "documented_only", "no_belief_raise"),
    ("deterred", "no_belief_raise"),
    "no_german_proposal",
]


@pytest.mark.parametrize("profile", PROFILES)
def test_wellformed_from_the_entry_state_full_build(profile):
    """Every state reachable from the entry state (and from the two counterfactual entry
    levels of belief_GER) explores without a model error: an actor always has an action,
    no two different Sets on one variable, no monotone decrease, endings exclusive."""
    cm = common.compiled(inert=True, profile=profile)
    g = explore(cm, initial=[common.entry(cm, b) for b in common.BELIEFS])
    assert g.size() > 0
    assert all(
        g.ending[i] in ("ATTACK_LAUNCHED", "NO_ATTACK") for i in range(g.size()) if g.terminal[i]
    )


@pytest.mark.parametrize("passage", ["granted", "refused"])
@pytest.mark.parametrize("profile", PROFILES[:5])
def test_wellformed_in_the_passage_scenarios(passage, profile):
    cm = common.compiled(inert=True, passage=passage, profile=profile)
    explore(cm, initial=[common.entry(cm, b) for b in common.BELIEFS])


def test_the_two_builds_are_bisimilar():
    """The reduced build is the full build with the two inert variables projected away and
    the three inert events read as Nature's none: from every reachable full state the
    projected available moves and successors are the reduced build's (so every fixpoint,
    rank and pivotal coalition that does not mention the inert variables agrees)."""
    for profile in (None, ("deterred", "documented_only")):
        full = common.compiled(inert=True, profile=profile)
        red = common.compiled(inert=False, profile=profile)
        keep = [full.index[v.name] for v in red.variables]
        nat_full = next(a for a in full.actors if a.is_nature)
        nat_red = next(a for a in red.actors if a.is_nature)
        to_red = []
        for x in nat_full.actions:
            to_red.append(0 if x.name in crisis.INERT_EVENTS else nat_red.action_index(x.name))
        g = explore(full, initial=[common.entry(full)])
        red_states = set()
        for i, s in enumerate(g.states):
            p = tuple(s[k] for k in keep)
            red_states.add(p)
            if g.terminal[i]:
                assert red.is_terminal(p)
                continue
            mapped = {}
            for jm, t in zip(g.moves[i], g.succ[i], strict=True):
                pm = (*jm[:-1], to_red[jm[-1]])
                pt = tuple(g.states[t][k] for k in keep)
                mapped.setdefault(pm, set()).add(pt)
            want = {}
            for jm, t in zip(*_moves_and_succ(red, p), strict=True):
                want.setdefault(jm, set()).add(t)
            assert mapped == want, red.format_state(p)
        assert red_states == set(explore(red, initial=[common.entry(red)]).states)


def _moves_and_succ(cm, s):
    import itertools

    avail = cm.available(s)
    moves = list(itertools.product(*avail))
    return moves, [cm.step(s, m) for m in moves]


# -- the realized replay (K1's sequence; decisions R1) --------------------------------------


@pytest.mark.parametrize("inert", [True, False])
@pytest.mark.parametrize("profile", [None, "deterred"])
def test_realized_replay(inert, profile):
    cm = common.compiled(inert=inert, profile=profile)
    states = common.realized_states(cm)
    assert len(states) == crisis.HORIZON + 1
    d = [cm.state_dict(s) for s in states]
    assert d[-1]["tick"] == "20" and cm.ending_of(states[-1]) == "ATTACK_LAUNCHED"
    assert [x["talks"] for x in d[11:18]] == [
        "political",
        "military",
        "military",
        "military",
        "adjourned",
        "adjourned",
        "broken",
    ]
    assert [x["passage"] for x in d[13:17]] == ["unasked", "asked", "asked", "refused"]
    assert [x["german_approach"] for x in (d[7], d[8], d[14], d[15], d[16])] == [
        "none",
        "opened",
        "pact_proposed",
        "pact_proposed",
        "pact",
    ]
    assert [x["attack_order"] for x in d[16:21]] == [
        "none",
        "ordered",
        "cancelled",
        "cancelled",
        "launched",
    ]
    assert [x["belief_GER"] for x in d[16:19]] == ["uncertain", "uncertain", "will_fight"]
    assert d[17]["west_powers"] == "True" and d[17]["alliance"] == "False"
    assert d[18]["british_treaty"] == "treaty" and d[20]["war_declared"] == "False"
    assert d[20]["fair_polish_obligation"] == "1"  # due on return (decisions C3)
    if inert:
        assert [x["mobilization_POL"] for x in (d[16], d[17], d[19])] == [
            "none",
            "partial",
            "general",
        ]
        assert d[18]["italy_ready"] == "not_ready"
    g = common.graph(cm, [common.entry(cm)])
    assert all(tuple(s) in g.index for s in states)


def test_exit_check_against_v1():
    """The exit of the realized terminal state against v1's own realized transition of
    1939Q3 and against 1939Q3.json (decisions R1 and C12)."""
    cm = FULL
    final = common.realized_states(cm)[-1]
    out = common.exit_applied(final, cm)
    v1q3 = common.v1_realized_q3()
    snap = common.snapshot_q3()
    assert out == {k: v1q3[k] for k in crisis.EXIT_VARIABLES}
    diff_snapshot = {k for k in crisis.EXIT_VARIABLES if out[k] != snap[k]}
    diff_v1 = {k for k in crisis.EXIT_VARIABLES if v1q3[k] != snap[k]}
    # oil_GER left the differences on 2026-10-23: the v1 snapshots date secured from the credit
    # agreement of 19 Aug 1939, following v1's accept_pact (owner's decision 2d; first run:
    # {"poland", "oil_GER"}, with the snapshot's oil_GER dependent).
    assert diff_snapshot == diff_v1 == {"poland"}
    assert (out["poland"], snap["poland"]) == ("german", "partitioned")
    assert (out["oil_GER"], snap["oil_GER"]) == ("secured", "secured")
    assert {k: out[k] for k in crisis.EXIT_VARIABLES if k not in diff_v1} == {
        "war_west_ger": "war",
        "france": "at_war",
        "britain": "at_war",
        "commit_WEST": "at_war",
        "nazi_soviet_pact": "True",
        "anglo_soviet_alliance": "False",
        "belief_GER": "will_fight",
        "oil_GER": "secured",
    }


def test_exit_without_the_obligation_and_with_a_declaration_inside():
    cm = FULL
    final = cm.state_dict(common.realized_states(cm)[-1])
    out = crisis.make_exit(obligation=False)(final, dict(common.COARSE_Q2))
    assert "war_west_ger" not in out and out["poland"] == "german"
    declared = dict(final, war_declared="True")
    assert crisis.exit(declared, dict(common.COARSE_Q2))["war_west_ger"] == "war"


def test_flattened_game_returns_v1s_realized_q3():
    fm, sub = common.flattened_v1()
    s = common.COARSE_Q2_STATE
    ger = next(i for i, a in enumerate(fm.actors) if a.name == "GER")
    avail = fm.available(s)
    j = next(k for k in avail[ger] if fm.actors[ger].actions[k].name == "crisis_1939")
    move = [a[0] for a in avail]
    move[ger] = j
    state = fm.step(s, tuple(move))
    assert fm.is_fine(state)
    for fine_move in crisis.realized_moves(sub):
        avail = fm.available(state)
        flat_move = []
        for i, a in enumerate(fm.actors):
            name = None
            for fa, fj in zip(sub.actors, fine_move, strict=True):
                if fa.name == a.name:
                    name = fa.actions[fj].name
            options = [k for k in avail[i] if name is None or a.actions[k].name == name]
            assert options, (a.name, name)
            flat_move.append(options[0])
        state = fm.step(state, tuple(flat_move))
    avail = fm.available(state)
    back = fm.step(state, tuple(a[0] for a in avail))
    assert not fm.is_fine(back)
    got = fm.state_dict(back)
    v1q3 = common.v1_realized_q3()
    assert got["tick"] == "15"
    assert {k: got[k] for k in crisis.EXIT_VARIABLES} == {k: v1q3[k] for k in crisis.EXIT_VARIABLES}
    assert got["last_GER"] == "crisis_1939"
    assert got["pending_GER_rearm"] == v1q3["pending_GER_rearm"]


# -- the hold-out guard ---------------------------------------------------------------------


def _changelog_rows():
    rows = []
    for line in (crisis.ROOT / "docs" / "guard_changelog_ww2.md").read_text().splitlines():
        if line.startswith("| 20"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append(dict(zip(["date", "test", "change", "source", "budget", "rerun"], cells)))
    return rows


def test_crisis_changelog_rows_after_the_first_run_name_a_source():
    """The model-step row of the sub-game exists; after the row recording the first run of
    K1 to K6, every row about the sub-game names a source and a full rerun."""
    rows = _changelog_rows()
    step = [r for r in rows if "summer_1939" in r["change"] and "model step" in r["test"]]
    assert len(step) == 1
    marks = [k for k, r in enumerate(rows) if r["test"].startswith("crisis 1939: first run")]
    if FIRST_RUN_COMMIT is None:
        assert not marks
        return
    assert len(marks) == 1
    assert FIRST_RUN_COMMIT[:7] in rows[marks[0]]["change"]
    assert re.search(r"\b[0-9a-f]{7,40}\b", rows[marks[0]]["change"])
    for r in rows[marks[0] + 1 :]:
        assert r["source"] and r["source"].lower() not in ("n/a", "(none)", "none", "-"), r
        assert r["rerun"].lower().startswith("yes"), r
