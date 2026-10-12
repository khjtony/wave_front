"""Structure of models/ww2/v0.py against docs/ontology_ww2.md, docs/actions_ww2.md and the
architect's decisions (docs/ww2_v0_decisions.md), and the helpers of models/ww2/hypotheses.py.

These are construction checks, not registered claims; the claims are in tests/ww2/scenarios.
"""

import itertools

import pytest

from models.ww2.hypotheses import (
    ROOT,
    SNAPSHOTS,
    fixed_model,
    quarter_tick,
    realized_corridor,
    realized_moves,
    realized_rows,
    snapshot_state,
)
from models.ww2.v0 import model
from wavefront.cli import main
from wavefront.engine import explore, witness
from wavefront.evidence.hindsight_ww2 import parse_ontology
from wavefront.model import ModelError

CM = model.compile()
DECLARED = {v.name: v for v in CM.variables if v.origin == "var"}
ADDED = {"north_strike", "german_defeat"}  # model-step additions (module docstring)


def test_every_ontology_variable_with_its_levels_order_and_init():
    onto = parse_ontology()
    assert set(DECLARED) == set(onto) | ADDED
    for name, spec in onto.items():
        v = DECLARED[name]
        if name == "ind_GER":  # counter 0..5 at 3 so the snapshot integers load as they are
            assert v.kind == "counter" and v.levels == tuple(str(i) for i in range(6))
            assert v.init == (3,)
            continue
        levels = tuple(str(x) for x in spec["levels"])
        assert v.levels == levels, name
        if spec["init"] is None:
            assert v.init == tuple(range(len(levels))), name
        else:
            assert v.init == (levels.index(str(spec["init"])),), name


def test_hidden_objectives_and_assumption():
    decl = {d.name: d for d in model.variables if hasattr(d, "hidden_from")}
    assert set(decl["aims_GER"].hidden_from) == {"WEST", "USSR", "JPN"}
    assert set(decl["aims_USSR"].hidden_from) == {"GER", "WEST", "JPN"}
    assert list(model.assumes) == ["ussr_defensive"]
    assert len(CM.initial_states()) == 2  # aims_GER swept; aims_USSR defensive


def test_d6_reductions():
    names = [v.name for v in CM.variables]
    assert "arms_at_war" not in names
    assert [n for n in names if n.startswith("last_")] == ["last_GER", "last_WEST"]
    # arms_JPN and belief_GER are constants: no effect ever targets them
    targets = {e.var for a in CM.actors for act in a.actions for e in act.effects}
    assert not targets & {"arms_JPN", "belief_GER"}
    assert {"china_war", "belief_at_munich"} <= set(names)


def test_sources_speculative_and_parts():
    for actor in CM.actors:
        for a in actor.actions:
            if not a.is_idle:
                assert a.source.strip(), f"{actor.name}.{a.name} has no source"
    spec = [f"{a.name}.{x.name}" for a in CM.actors for x in a.actions if x.speculative]
    assert spec == ["JPN.strike_north"]
    parted = {
        f"{d.actor}.{d.name}": [p for p, _ in d.guard_parts]
        for a in [*model.actors, model.nature()]
        for d in a.actions
        if d.guard_parts
    }
    for name in (
        "JPN.strike_north",
        "Nature.campaign_siberia",
        "WEST.offensive_west",
        "Nature.campaign_west",
        "GER.attack_france",
        "GER.attack_poland",
        "WEST.guarantee_poland",
        "GER.annex_austria",
        "GER.invade_britain",
    ):
        assert name in parted, name
    assert parted["JPN.strike_north"] == ["pact", "army_free", "ussr_weak"]
    assert parted["WEST.offensive_west"] == ["at_war", "german_army_unready"]
    assert {"no_two_front", "japanese_superiority"} <= set(parted["Nature.campaign_siberia"])
    for gated in ("GER.occupy_bohemia", "GER.attack_poland", "USSR.join_axis"):
        assert parted[gated][0] == "hypothesis"


def test_parameter_budget():
    b = CM.budget()
    assert {
        k: b[k]
        for k in (
            "variables",
            "actions",
            "guards",
            "guard_parts",
            "speculative_actions",
            "fairness_constraints",
            "delays",
            "latches",
            "invariants",
            "endings",
        )
    } == {
        "variables": 34,
        "actions": 42,
        "guards": 42,
        "guard_parts": 66,
        "speculative_actions": 1,
        "fairness_constraints": 3,
        "delays": 3,
        "latches": 1,
        "invariants": 2,
        "endings": 10,
    }
    assert [f.name for f in model.fairness_constraints] == [
        "democratic_response",
        "czech_obligation",
        "rhineland_resolution",
    ]
    assert [p.name for p in model.profiles] == ["fight_on", "appeaser"]
    assert list(model.invariants) == ["balance_europe", "commitment_alive"]


def test_endings_are_mutually_exclusive_on_every_state():
    """Every combination of the variables the endings read, at and before the horizon."""
    base = list(CM.initial_states()[0])
    axes = {
        "tick": [0, 19, 20],
        "german_defeat": [0, 1],
        "britain": range(4),
        "siberia": range(2),
        "ussr_axis": [0, 1],
        "war_west_ger": [0, 1],
        "poland": range(3),
        "france": range(3),
    }
    for values in itertools.product(*axes.values()):
        s = list(base)
        for name, value in zip(axes, values, strict=True):
            s[CM.index[name]] = value
        hits = [n for n in model.endings if CM.evaluate(n, s)]
        assert len(hits) <= 1, (values, hits)
        if values[0] == 20:
            assert len(hits) == 1, values  # every horizon state has a named ending


def test_tick0_snapshot_is_the_initial_state():
    for aims in ("revisionist", "hegemonic"):
        s = snapshot_state(CM, "1935Q4", aims)
        assert s in CM.initial_states()
        fixed = fixed_model(model, aims_GER=aims).compile()
        assert fixed.initial_states() == [s]


def test_every_hindsight_snapshot_loads_at_its_tick():
    files = sorted(p.stem for p in SNAPSHOTS.glob("*.json"))
    assert len(files) == 21
    for q in files:
        s = snapshot_state(CM, q, "hegemonic")
        assert s[CM.index["tick"]] == quarter_tick(q)
    assert quarter_tick("1935Q4") == 0 and quarter_tick("1940Q4") == 20
    with pytest.raises(ValueError):
        quarter_tick("1938Q5")
    with pytest.raises(ModelError):
        fixed_model(model, arms_GER="high")  # not swept


def test_realized_moves_cover_the_horizon():
    rows = realized_rows()
    moves = realized_moves(CM)
    assert len(rows) == len(moves) == model.horizon


def test_display_corridor_witness_is_the_realized_trace():
    """The visualizer's corridor (not a model of record): its shortest witness to
    BRITAIN_ALONE from the tick-0 hegemonic state is the realized trace, move for move."""
    corridor = realized_corridor()
    cm = corridor.compile()
    g = explore(cm, initial=[snapshot_state(cm, "1935Q4", "hegemonic")])
    trace = witness(g, g.initial[0], g.ending_states("BRITAIN_ALONE"))
    rows = realized_rows()
    for k, move in enumerate(trace.joint_moves):
        want = [rows[k][a] for a in ("GER", "WEST", "USSR", "JPN", "Nature")]
        want = ["abstain" if x == "idle" else x for x in want]
        assert g.move_names(move) == want, k
    assert model.name == "ww2_v0" and corridor.name == "ww2_v0_corridor"


def test_cli_viable_with_fixed_hypothesis(capsys):
    code = main(
        [
            "viable",
            str(ROOT / "models" / "ww2" / "v0.py"),
            "--coalition",
            "WEST",
            "--invariant",
            "balance_europe",
            "--snapshot",
            str(SNAPSHOTS / "1940Q3.json"),
            "--fix",
            "aims_GER=hegemonic",
            "--fix",
            "aims_USSR=defensive",
        ]
    )
    out, err = capsys.readouterr()
    assert code == 0, err
    assert "| #0 | no |" in out  # France has fallen: balance_europe is already false
