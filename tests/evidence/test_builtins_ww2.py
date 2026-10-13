"""Built-ins of the WW2 v0 hindsight snapshots (phase 2 decision F2).

The builder reads the pending counters from ``data/ww2/decisions_ww2.csv``, the last actions
from ``data/ww2/realized_moves.csv``, the latch from the events, and sets the fairness
counters to 0 (assumed). These tests check the decision records, the builder's arithmetic on
a tiny fixture, and the 21 committed files against the model: every file loads into
``models/ww2/v0.py`` under both hypotheses, and the loaded state is compared, variable by
variable and built-in by built-in, with the state the model itself reaches when the
realized moves are replayed from tick 0. Every difference is listed below with its reason;
``snapshots/ww2/hindsight/README.md`` explains each one.
"""

import json
from datetime import date
from pathlib import Path

import pytest

from models.ww2.hypotheses import (
    HYPOTHESES,
    fixed_model,
    quarter_tick,
    realized_moves,
    snapshot_state,
)
from models.ww2.v0 import model
from wavefront.evidence import hindsight_ww2 as h

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOTS = ROOT / "snapshots" / "ww2" / "hindsight"
FILES = [h.TICK0, *h.QUARTERS]
BUILTIN_ORIGINS = ("latch", "pending", "last", "fair")


@pytest.fixture(scope="module")
def cm():
    return model.compile()


@pytest.fixture(scope="module")
def committed():
    return {q: json.loads((SNAPSHOTS / f"{q}.json").read_text(encoding="utf-8")) for q in FILES}


# -- the builder's built-in list is the model's ------------------------------------------------


def test_builder_built_ins_are_the_models_in_state_order(cm):
    names = [v.name for v in cm.variables if v.origin in BUILTIN_ORIGINS]
    assert list(h.BUILTIN_NAMES) == names
    delays = {(a.name, x.name): x.delay for a in cm.actors for x in a.actions if x.delay}
    assert delays == h.DELAYED
    assert tuple(a.name for a in model.actors if a.remember_last) == h.REMEMBER_LAST
    assert tuple(f.name for f in model.fairness_constraints) == h.FAIRNESS
    (latch,) = model.latches
    of, var, level = h.LATCHES[latch.name]
    assert latch.of == of
    assert latch.when.free_vars() == frozenset({var})
    s = list(snapshot_state(cm, h.TICK0, "hegemonic"))
    assert not cm.evaluate(latch.when, s)
    s[cm.index[var]] = cm.variables[cm.index[var]].levels.index(level)
    assert cm.evaluate(latch.when, s)


# -- the decision records ----------------------------------------------------------------------


def test_the_decision_records():
    decisions = h.load_decisions()
    assert [(d.quarter, d.actor, d.action, d.delay) for d in decisions] == [
        ("1936Q1", "WEST", "rearm", 4),
        ("1936Q3", "GER", "rearm", 8),
        ("1938Q4", "GER", "rearm", 8),
        ("1938Q4", "WEST", "rearm", 4),
        ("1940Q2", "USSR", "rearm", 4),
    ]
    for d in decisions:
        assert d.source and d.note.startswith("realized_moves.csv tick")
    assert h.check_decisions_against_moves(decisions, h.load_moves()) == []


def test_decisions_and_moves_must_agree():
    decisions = h.load_decisions()
    moves = [dict(r) for r in h.load_moves()]
    moves[17]["USSR"] = "idle"
    moves[5]["WEST"] = "rearm"
    problems = h.check_decisions_against_moves(decisions, moves)
    assert problems == [
        "realized_moves.csv tick 5 (1937Q2): WEST rearm has no row in decisions_ww2.csv",
        "decisions_ww2.csv 1940-05-07 USSR rearm: the realized move of 1940Q2 is 'idle'",
    ]


HEADER = ",".join(h.DECISION_COLUMNS)


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        (["1936-03-03,1936Q1,WEST,resist_rhineland,0,s,"], "not a delayed action of v0"),
        (["1936-03-03,1936Q1,WEST,rearm,8,s,"], "delay_ticks 8 for WEST.rearm, but the model's"),
        (["1936-03-03,1936Q2,WEST,rearm,4,s,"], "does not match"),
        (["1936-03-03,1936Q1,WEST,rearm,4,,"], "source must not be empty"),
        (
            ["1936-03-03,1936Q1,WEST,rearm,4,s,", "1937-03-03,1937Q1,WEST,rearm,4,s,"],
            r"WEST.rearm decided at tick 4 \(1937Q1\) while the decision of tick 0 \(1936Q1\) "
            r"is still pending \(delay 4: unavailable at ticks 1 to 4\)",
        ),
    ],
)
def test_load_decisions_rejects_bad_rows(tmp_path, rows, message):
    path = tmp_path / "decisions.csv"
    path.write_text("# comment\n" + HEADER + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        h.load_decisions(path)


def test_a_decision_exactly_one_delay_later_is_allowed(tmp_path):
    path = tmp_path / "decisions.csv"
    rows = ["1936-03-03,1936Q1,WEST,rearm,4,s,", "1937-04-03,1937Q2,WEST,rearm,4,s,"]
    path.write_text(HEADER + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    assert len(h.load_decisions(path)) == 2


# -- the builder's arithmetic on a tiny fixture ---------------------------------------------------


def _event(day, variable, level):
    return h.Event(day, h.quarter_of(day), variable, level, f"{variable} {level}", "src", "")


def _decision(day, actor, action, delay):
    return h.Decision(day, h.quarter_of(day), actor, action, delay, f"src {actor}", "")


FIX_DECISIONS = [
    _decision(date(1936, 5, 1), "WEST", "rearm", 4),
    _decision(date(1936, 2, 1), "GER", "rearm", 8),
]
FIX_EVENTS = [
    _event(date(1936, 7, 1), "belief_WEST", "uncertain"),
    _event(date(1936, 8, 1), "sudeten", "german"),
    _event(date(1936, 11, 1), "belief_WEST", "hegemonic"),
]
FIX_MOVES = [
    {"tick": str(k), "quarter": h.quarter_name(k), "GER": g, "WEST": w, "source": f"row {k}"}
    for k, (g, w) in enumerate(
        [("rearm", "idle"), ("idle", "rearm"), ("idle", "idle"), ("court_italy", "idle")]
        + [("idle", "idle")] * 2
    )
]


def _fixture(quarter):
    return h.build_builtins(quarter, FIX_EVENTS, FIX_DECISIONS, FIX_MOVES)


def test_fixture_pending_counters_follow_the_formula():
    seq = {
        q: (_fixture(q)["pending_WEST_rearm"]["value"], _fixture(q)["pending_GER_rearm"]["value"])
        for q in ("1935Q4", "1936Q1", "1936Q2", "1936Q3", "1936Q4")
    }
    # WEST decided in 1936Q2 (index 1), delay 4; GER in 1936Q1 (index 0), delay 8.
    assert seq == {
        "1935Q4": (0, 0),
        "1936Q1": (0, 8),
        "1936Q2": (4, 7),
        "1936Q3": (3, 6),
        "1936Q4": (2, 5),
    }
    entry = _fixture("1936Q4")["pending_WEST_rearm"]
    assert entry["rule"].startswith(
        "pending_WEST_rearm = max(0, d - (index(Q) - index(t))) = max(0, 4 - (3 - 1)) = 2: "
        "WEST rearm decided 1936-05-01 (1936Q2, model tick 1) with delay d = 4, read at the end "
        "of Q = 1936Q4 (tick 4); the effect applies in the transition into tick 6 (the end of "
        "1937Q2)"
    )
    assert entry["confidence"] == "medium"
    assert entry["indicators"][0]["id"] == "decision_1936-05-01_WEST_rearm"
    assert entry["indicators"][0]["observed"] == "1936-05-01"
    assert entry["indicators"][0]["source"] == "src WEST"
    later = h.build_builtins("1937Q2", FIX_EVENTS, FIX_DECISIONS, FIX_MOVES)["pending_WEST_rearm"]
    assert later["value"] == 0
    assert "max(0, 4 - (5 - 1)) = 0" in later["rule"] and "so nothing is pending" in later["rule"]
    before = _fixture("1936Q1")["pending_WEST_rearm"]
    assert before["confidence"] == "high"
    assert (
        "no WEST rearm decision in data/ww2/decisions_ww2.csv at or before 1936Q1"
        in (before["rule"])
    )
    assert before["indicators"][0]["rule"].startswith("the first such decision, dated after")
    never = _fixture("1936Q4")["pending_USSR_rearm"]
    assert never["value"] == 0 and never["confidence"] == "assumed" and never["indicators"] == []


def test_fixture_last_actions_latch_and_fairness():
    tick0 = _fixture("1935Q4")
    assert tick0["last_GER"]["value"] == "none" and tick0["last_WEST"]["value"] == "none"
    q2 = _fixture("1936Q2")
    assert (q2["last_GER"]["value"], q2["last_WEST"]["value"]) == ("idle", "rearm")
    assert q2["last_GER"]["confidence"] == "medium" and q2["last_WEST"]["confidence"] == "high"
    assert q2["last_WEST"]["indicators"][0]["source"] == "row 1"
    assert q2["last_WEST"]["indicators"][0]["observed"] == "1936-06-30"
    assert _fixture("1936Q4")["last_GER"]["value"] == "court_italy"
    # The latch: unset before the cession quarter, then the belief at that quarter's end,
    # which a later belief change does not move.
    assert _fixture("1936Q2")["belief_at_munich"]["value"] == "unset"
    assert _fixture("1936Q3")["belief_at_munich"]["value"] == "uncertain"
    late = _fixture("1936Q4")["belief_at_munich"]
    assert late["value"] == "uncertain" and late["confidence"] == "medium"
    assert [i["observed"] for i in late["indicators"]] == ["1936-08-01", "1936-07-01"]
    for name in h.FAIRNESS:
        entry = _fixture("1936Q3")[f"fair_{name}"]
        assert entry["value"] == 0 and entry["confidence"] == "assumed"
        assert entry["indicators"] == [] and "assumed" in entry["rule"]
    assert list(_fixture("1936Q3")) == list(h.BUILTIN_NAMES)


def test_start_reading_takes_the_built_ins_of_the_quarter_before():
    from wavefront.evidence.datasets import nmc

    rows = nmc.load(ROOT / "data" / "ww2" / "nmc_1936_1940.csv")
    events = h.load_events()
    kw = {"decisions": h.load_decisions(), "moves": h.load_moves()}
    start = h.build("1938Q3", rows, events, at="start", **kw)
    end = h.build("1938Q2", rows, events, **kw)
    assert start["builtins"] == end["builtins"]
    with pytest.raises(ValueError, match="both the decisions and the realized moves"):
        h.build("1938Q3", rows, events, decisions=kw["decisions"])


# -- the committed files -----------------------------------------------------------------------


def test_committed_files_carry_every_built_in(committed):
    for quarter, snap in committed.items():
        assert list(snap["builtins"]) == list(h.BUILTIN_NAMES), quarter
        assert h.check_builtins(snap) == []
        for name, entry in snap["builtins"].items():
            assert entry["rule"], (quarter, name)
            if name.startswith("fair_"):
                assert (entry["value"], entry["confidence"]) == (0, "assumed")
            else:
                assert entry["indicators"], (quarter, name)


def test_committed_values_at_munich(committed):
    """The two states of the amended T8(b)."""
    before = {k: v["value"] for k, v in committed["1938Q2"]["builtins"].items()}
    after = {k: v["value"] for k, v in committed["1938Q3"]["builtins"].items()}
    assert before == {
        "belief_at_munich": "unset",
        "pending_GER_rearm": 1,  # the programme of Aug 1936 lands in the next transition
        "pending_WEST_rearm": 0,
        "pending_USSR_rearm": 0,
        "last_GER": "demand_sudeten",
        "last_WEST": "idle",
        "fair_democratic_response": 0,
        "fair_czech_obligation": 0,
        "fair_rhineland_resolution": 0,
    }
    assert after == before | {
        "belief_at_munich": "uncertain",
        "pending_GER_rearm": 0,
        "last_WEST": "concede",
    }


@pytest.mark.parametrize("aims", [hyp["aims_GER"] for hyp in HYPOTHESES])
def test_every_file_loads_with_its_built_ins_under_both_hypotheses(cm, committed, aims):
    for quarter, snap in committed.items():
        state = snapshot_state(cm, quarter, aims, builtins=True)
        named = cm.state_dict(state)
        assert int(named["tick"]) == quarter_tick(quarter)
        assert named["aims_GER"] == aims and named["aims_USSR"] == "defensive"
        for name, entry in snap["builtins"].items():
            assert named[name] == str(entry["value"]), (quarter, name)
        # the phase 1 convention is still available and differs only in the built-ins
        bare = snapshot_state(cm, quarter, aims)
        differ = {cm.variables[i].name for i, (a, b) in enumerate(zip(state, bare)) if a != b}
        assert all(cm.variables[cm.index[n]].origin in BUILTIN_ORIGINS for n in differ)


# -- replay against the snapshots ---------------------------------------------------------------

# Every (file, variable) on which the loaded snapshot state differs from the model's state
# after replaying data/ww2/realized_moves.csv from the tick-0 state, with its reason. The
# reasons are explained in snapshots/ww2/hindsight/README.md ("Replay against the snapshots").
REASONS = {
    "treaty": "locarno_lapses placed at tick 2 [SQR]; the record dates the lapse 7 to 19 Mar 1936",
    "arms_WEST_rising": "NMC reading with the French programme gate (Sep 1936) before the "
    "delay-4 effect of the Mar 1936 decision lands at tick 5",
    "china_war": "the China incident (7 Jul 1937) is not in the realized moves; Nature declines it",
    "belief_WEST": "demand_sudeten is placed at tick 9 (Case Green, May 1938) and raises the "
    "belief at once; the record has the belief move with the public demand of Sep 1938",
    "arms_GER_high": "the 1936 programme lands at tick 11 under delay 8; the planning record "
    "reads high from 21 Oct 1938 (decisions D12): one tick",
    "arms_USSR": "the record restores strong in Nov 1938; in the model only USSR rearm restores "
    "it, decided in 1940Q2 and landing after the horizon",
    "arms_WEST_high": "NMC 1939 reads high from 1939Q1; the Oct to Nov 1938 decision lands at "
    "tick 16 under delay 4",
    "guarantee": "guarantee_poland placed at tick 13 [SQR]; the record dates it 31 Mar 1939",
    "fair_democratic_response": "fairness counters are assumed 0 (F2); on the replay the "
    "trigger holds at tick 13 after a non-response (approach_ussr), so the counter is 1",
    "belief_GER": "constant in v0 (decisions D6, reduction 1); the record moves it in 1939",
    "oil_GER": "accept_pact secures oil at once (tick 15); the record dates it from the credit "
    "and economic agreements, read as secured from 1940Q1",
    "poland": "occupy_east_poland placed at tick 15 [SQR]; the record dates it 17 Sep 1939",
    "balkans": "align_balkans placed at tick 19; the record dates the alignment 30 Aug 1940",
    "arms_GER_total": "the Oct 1938 programme lands at tick 20 under delay 8 and bumps high to "
    "total; the record reads no total before 1941",
}


def _expected():
    out = {}

    def add(reason, variable, quarters):
        for q in quarters:
            out[(q, variable)] = reason

    add("treaty", "treaty", ["1936Q1", "1936Q2"])
    add("arms_WEST_rising", "arms_WEST", ["1936Q3", "1936Q4"])
    add("china_war", "china_war", [q for q in h.QUARTERS if q >= "1937Q3"])
    add("belief_WEST", "belief_WEST", ["1938Q2"])
    add("arms_GER_high", "arms_GER", ["1938Q3"])
    add("arms_USSR", "arms_USSR", [q for q in h.QUARTERS if q >= "1938Q4"])
    add("arms_WEST_high", "arms_WEST", ["1939Q1", "1939Q2", "1939Q3"])
    add("guarantee", "commit_WEST", ["1939Q1"])
    add("guarantee", "polish_guarantee", ["1939Q1"])
    add("fair_democratic_response", "fair_democratic_response", ["1939Q1"])
    add("belief_GER", "belief_GER", [q for q in h.QUARTERS if q >= "1939Q2"])
    add("oil_GER", "oil_GER", ["1939Q3", "1939Q4"])
    add("poland", "poland", ["1939Q3"])
    add("balkans", "balkans", ["1940Q3"])
    add("arms_GER_total", "arms_GER", ["1940Q4"])
    return out


EXPECTED = _expected()


def _replay(cm):
    """The realized states from tick 0, as far as every realized move is available."""
    state = cm.initial_states()[0]
    states, stopped = [state], None
    for tick, move in enumerate(realized_moves(cm)):
        avail = cm.available(state)
        bad = [
            f"{a.name}.{a.actions[j].name}"
            for a, j, ok in zip(cm.actors, move, avail, strict=True)
            if j not in ok
        ]
        if bad:
            stopped = (tick, bad)
            break
        state = cm.step(state, move)
        states.append(state)
    return states, stopped


@pytest.mark.parametrize("aims", [hyp["aims_GER"] for hyp in HYPOTHESES])
def test_loaded_snapshots_match_the_replayed_model_except_the_listed_differences(aims):
    fixed = fixed_model(model, aims_GER=aims).compile()
    states, stopped = _replay(fixed)
    if aims == "hegemonic":
        assert stopped is None and len(states) == model.horizon + 1
    else:
        # Prague is a hypothesis gate: under revisionist aims the realized path stops there.
        assert stopped == (12, ["GER.occupy_bohemia"])
    found = {}
    for quarter in FILES:
        tick = quarter_tick(quarter)
        if tick >= len(states):
            break
        loaded = snapshot_state(fixed, quarter, aims, builtins=True)
        for i, spec in enumerate(fixed.variables):
            if loaded[i] != states[tick][i]:
                found[(quarter, spec.name)] = (
                    spec.levels[loaded[i]] if spec.name != "tick" else loaded[i],
                    spec.levels[states[tick][i]] if spec.name != "tick" else states[tick][i],
                )
    compared = {q for q in FILES if quarter_tick(q) < len(states)}
    expected = {k for k in EXPECTED if k[0] in compared}
    unexpected = {
        f"{q} {v}: snapshot {a}, replay {b}"
        for (q, v), (a, b) in found.items()
        if (q, v) not in EXPECTED
    }
    missing = {f"{q} {v}: listed ({EXPECTED[(q, v)]}) but equal" for q, v in expected - set(found)}
    assert not unexpected and not missing, sorted(unexpected | missing)
    # No built-in differs except the assumed fairness counter.
    builtin_diffs = {
        k for k in found if fixed.variables[fixed.index[k[1]]].origin in BUILTIN_ORIGINS
    }
    assert builtin_diffs <= {("1939Q1", "fair_democratic_response")}
    assert set(REASONS) >= set(EXPECTED.values())
