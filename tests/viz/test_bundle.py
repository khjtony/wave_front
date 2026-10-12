"""The visualizer's data bundle (docs/visualizer.md sections 1, 5 and 8)."""

import json

import pytest
from hypothesis import HealthCheck, given, settings

from models.toy.two_power import model as toy
from tests.analysis.games import coin, crisis, ladder, tug
from tests.helpers.random_games import random_models
from wavefront.analysis import point_of_no_return, silent_phase, viability
from wavefront.engine import attractor, contested, explore, safe
from wavefront.model import Model, Set, V
from wavefront.viz import bundle, decision_classes, replay, status_codes
from wavefront.viz.bundle import DECISION_NAMES, STATUS_NAMES

KEPT, CONTESTED, LOST, FAILED = range(4)
SAFE, RISKY, LOSING, ENDS = range(4)


# -- helpers ---------------------------------------------------------------------------------


def reference_codes(g, coalition, phi):
    """Status codes from the engine's own ``contested`` and ``safe``."""
    res = contested(g, coalition, phi, "keep")
    kernel = safe(g, coalition, phi).kernel
    assert kernel == res.forced
    out = []
    for s in range(g.size()):
        if s not in phi:
            out.append(FAILED)
        elif s in res.forced:
            out.append(KEPT)
        elif s in res.blocked:
            out.append(LOST)
        else:
            assert s in res.contested
            out.append(CONTESTED)
    return out


def direct_classes(g, codes, s):
    """Decision classes straight from the definition in the task: for actor X and action a,
    over all joint moves where X plays a."""
    out = []
    for i, avail in enumerate(g.avail[s]):
        row = []
        for a in avail:
            succ = [t for m, t in zip(g.moves[s], g.succ[s], strict=True) if m[i] == a]
            if all(codes[t] == KEPT for t in succ):
                cls = SAFE
            elif all(g.terminal[t] for t in succ):
                cls = ENDS
            elif not any(codes[t] == KEPT for t in succ):
                cls = LOSING
            else:
                cls = RISKY
            row.append([a, cls])
        out.append(row)
    return out


def codes_of(b, p, c):
    return [int(ch) for ch in b["states"]["status"][p][c]]


def trace(b, hyp, ending):
    (t,) = [t for t in b["traces"] if t["hypothesis"] == hyp and t["ending"] == ending]
    return t


def hyp_index(b, **values):
    (k,) = [
        i
        for i, it in enumerate(b["hypotheses"]["items"])
        if all(it["values"][n] == v for n, v in values.items())
    ]
    return k


# -- status codes ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("game", "coalition", "invariant"),
    [
        (ladder(), ["P"], "low"),
        (ladder(shielded=False), ["P"], "low"),
        (tug(), ["A"], "low"),
        (tug(), ["A", "B"], "low"),
        (crisis(), ["P"], "peace"),
        (crisis(), ["P", "Nature"], "peace"),
    ],
)
def test_status_codes_agree_with_contested_and_safe(game, coalition, invariant):
    g = explore(game.compile())
    phi = g.states_where(invariant)
    assert status_codes(g, coalition, phi) == reference_codes(g, coalition, phi)


def test_the_crisis_game_has_every_status():
    """Matching pennies makes the tense states contested for P: neither side can force."""
    g = explore(crisis().compile())
    codes = status_codes(g, ["P"], g.states_where("peace"))
    assert set(codes) == {KEPT, CONTESTED, LOST, FAILED}


@settings(max_examples=25, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(random_models())
def test_status_codes_agree_on_random_models(m):
    g = explore(m.compile())
    everyone = set(range(g.size()))
    players = [a.name for a in g.model.actors if not a.is_nature]
    for e in m.endings:
        phi = everyone - g.ending_states(e)
        for coalition in ([], players[:1], players):
            assert status_codes(g, coalition, phi) == reference_codes(g, coalition, phi)


def test_bundle_statuses_match_the_engine_for_every_property_and_coalition():
    m = crisis()
    b = bundle(m, max_relax=0)
    g = explore(m.compile())
    everyone = set(range(g.size()))
    assert [p["id"] for p in b["properties"]] == ["avoid:WAR", "invariant:peace"]
    phis = [everyone - g.ending_states("WAR"), g.states_where("peace")]
    for p, phi in enumerate(phis):
        for c, coal in enumerate(b["coalitions"]):
            assert codes_of(b, p, c) == reference_codes(g, coal["members"], phi)


# -- decision classes ---------------------------------------------------------------------------


@settings(max_examples=25, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(random_models())
def test_decision_classes_agree_with_their_definition(m):
    g = explore(m.compile())
    everyone = set(range(g.size()))
    players = [a.name for a in g.model.actors if not a.is_nature]
    for e in m.endings:
        codes = status_codes(g, players[:1], everyone - g.ending_states(e))
        for s in range(g.size()):
            if g.terminal[s]:
                assert decision_classes(g, codes, s) == [[] for _ in g.model.actors]
            else:
                assert decision_classes(g, codes, s) == direct_classes(g, codes, s)


def test_bundle_classes_along_every_trace_agree_with_their_definition(toy_bundle):
    b = toy_bundle
    g = explore(toy.compile())
    for t in b["traces"]:
        if t["states"] is None:
            continue
        for p in range(len(b["properties"])):
            for c in range(len(b["coalitions"])):
                codes = codes_of(b, p, c)
                for k, s in enumerate(t["states"][:-1]):
                    assert t["classes"][p][c][k] == direct_classes(g, codes, s)


# -- the toy, docs/visualizer.md section 9 -------------------------------------------------------


def test_toy_hypotheses_and_defaults(toy_bundle):
    b = toy_bundle
    hyp = b["hypotheses"]
    assert hyp["variables"] == ["aims"]
    assert hyp["values"] == {"aims": ["limited", "hegemonic"]}
    assert [it["label"] for it in hyp["items"]] == ["aims = limited", "aims = hegemonic"]
    # INC cannot tell the two initial states apart; CH can
    assert all(it["identical_to"] == ["INC"] for it in hyp["items"])
    # TAKEOVER is reachable only under hegemonic aims, so the page opens there
    assert b["meta"]["default"] == {
        "hypothesis": hyp_index(b, aims="hegemonic"),
        "coalition": 0,
        "ending": 0,
    }
    assert b["coalitions"][0] == {"name": "{INC}", "members": ["INC"]}
    aims = next(v for v in b["variables"] if v["name"] == "aims")
    assert aims["hidden_from"] == ["INC"] and aims["swept"]
    assert [a["color_slot"] for a in b["actors"]] == [1, 2, None]


def test_toy_status_band_markers(toy_bundle):
    """On the shortest takeover trace for {INC}: the point of no return at tick 1 and the
    takeover at tick 3 (tests/toy). For the property "not TAKEOVER" the rest can force the
    takeover from tick 1 already (t_L = 1); the balance invariant is visibly lost at tick 2,
    which is the "loss at tick 2" of tests/toy."""
    b = toy_bundle
    t = trace(b, hyp_index(b, aims="hegemonic"), "TAKEOVER")
    assert len(t["states"]) == 4
    names = [a["actions"] for a in b["actors"]]
    assert [names[0][m[0]]["name"] for m in t["moves"]] == ["expand"] * 3
    assert [names[1][m[1]]["name"] for m in t["moves"]] == ["idle"] * 3
    p_avoid = [p["id"] for p in b["properties"]].index("avoid:TAKEOVER")
    p_bal = [p["id"] for p in b["properties"]].index("invariant:balance")
    assert t["phases"][p_avoid][0] == {"t_K": 1, "t_L": 1, "t_phi": 3}
    assert t["phases"][p_bal][0] == {"t_K": 0, "t_L": 0, "t_phi": 2}
    ticks = [b["states"]["tick"][s] for s in t["states"]]
    assert ticks == [0, 1, 2, 3]
    assert b["all_endings"][b["states"]["ending"][t["states"][-1]]] == "TAKEOVER"


def test_toy_phases_agree_with_the_analysis_layer(toy_bundle):
    b = toy_bundle
    g = explore(toy.compile())
    p_bal = [p["id"] for p in b["properties"]].index("invariant:balance")
    everyone = set(range(g.size()))
    for t in b["traces"]:
        if t["states"] is None:
            continue
        for c, coal in enumerate(b["coalitions"]):
            sp = silent_phase(t["states"], g, coal["members"], "balance")
            assert t["phases"][p_bal][c] == {"t_K": sp.t_K, "t_L": sp.t_L, "t_phi": sp.t_phi}
            kernel = safe(g, coal["members"], everyone - g.ending_states("TAKEOVER")).kernel
            p_avoid = [p["id"] for p in b["properties"]].index("avoid:TAKEOVER")
            assert t["phases"][p_avoid][c]["t_K"] == point_of_no_return(t["states"], kernel)
            k_bal = viability(g, coal["members"], "balance").kernel
            assert t["phases"][p_bal][c]["t_K"] == point_of_no_return(t["states"], k_bal)


def test_toy_decision_tree_at_tick_zero(toy_bundle):
    """resist is INC's only safe first move against a hegemonic CH (tests/toy). idle and
    concede are risky, not losing: if CH also idles, the play stays in INC's kernel."""
    b = toy_bundle
    t = trace(b, hyp_index(b, aims="hegemonic"), "TAKEOVER")
    p = [p["id"] for p in b["properties"]].index("avoid:TAKEOVER")
    inc = b["actors"][1]
    classes = {inc["actions"][a]["name"]: DECISION_NAMES[c] for a, c in t["classes"][p][0][0][1]}
    assert classes == {
        "idle": "risky",
        "concede": "risky",
        "resist": "safe",
        "fund_oversight": "risky",
    }


def test_toy_replay_under_limited_aims_stops_where_expand_is_unavailable(toy_bundle):
    b = toy_bundle
    t = trace(b, hyp_index(b, aims="hegemonic"), "TAKEOVER")
    (r,) = t["replays"]
    assert r["hypothesis"] == hyp_index(b, aims="limited")
    assert r["stop"] == {"index": 1, "reason": "unavailable", "actor": 0, "action": 1}
    assert b["actors"][0]["actions"][1]["name"] == "expand"
    assert len(r["states"]) == 2 and r["moves"] == t["moves"][:1]
    # the states agree on every variable but the hypothesis up to the stop
    aims = [v["name"] for v in b["variables"]].index("aims")
    for a, c in zip(t["states"], r["states"], strict=False):
        va = [col[a] for i, col in enumerate(b["states"]["values"]) if i != aims]
        vc = [col[c] for i, col in enumerate(b["states"]["values"]) if i != aims]
        assert va == vc


def test_toy_landscape_kept_region_shrinks_with_control(toy_bundle):
    """Among the live (non-terminal) states of the hegemonic hypothesis the kept share falls
    as control rises, and kept gives way to lost between control 1 and 2; at control 3
    everything has failed. (Terminal states at the horizon satisfy "not TAKEOVER" and are
    kept whatever the control.)"""
    b = toy_bundle
    h = hyp_index(b, aims="hegemonic")
    p = [p["id"] for p in b["properties"]].index("avoid:TAKEOVER")
    codes = codes_of(b, p, 0)
    control = b["states"]["values"][[v["name"] for v in b["variables"]].index("control")]
    depth = b["states"]["depth"][h]
    terminal = b["states"]["terminal"]
    live = {}
    for lv in range(3):
        ids = [
            s for s in range(len(depth)) if depth[s] >= 0 and control[s] == lv and not terminal[s]
        ]
        live[lv] = [sum(codes[s] == k for s in ids) / len(ids) for k in range(4)]
    assert live[0][KEPT] > live[1][KEPT] > live[2][KEPT]
    assert live[1][KEPT] > live[1][LOST] and live[2][LOST] > live[2][KEPT]
    top = [s for s in range(len(depth)) if depth[s] >= 0 and control[s] == 3]
    assert top and all(codes[s] == FAILED for s in top)


def test_toy_card_and_tables(toy_bundle):
    b = toy_bundle
    heg = b["hypotheses"]["items"][hyp_index(b, aims="hegemonic")]
    lim = b["hypotheses"]["items"][hyp_index(b, aims="limited")]
    p = [p["id"] for p in b["properties"]].index("avoid:TAKEOVER")
    p_bal = [p["id"] for p in b["properties"]].index("invariant:balance")
    assert heg["card"]["status"][p][0] == KEPT  # INC can block the takeover (tests/toy)
    assert heg["card"]["status"][p_bal][0] != KEPT and lim["card"]["status"][p_bal][0] == KEPT
    assert heg["card"]["endings"]["TAKEOVER"] == 3 and lim["card"]["endings"]["TAKEOVER"] is None
    piv = {r["ending"]: r for r in heg["tables"]["pivotal"]}
    assert piv["TAKEOVER"]["forcing"] == [["CH", "INC"]]
    assert piv["TAKEOVER"]["blocking"] == [["CH"], ["INC"]]
    relax = {r["ending"]: r for r in lim["tables"]["relaxations"]}
    assert relax["TAKEOVER"]["minimum_size"] == 1
    assert {tuple(s) for s in relax["TAKEOVER"]["sets"]} == {("CH.expand",), ("CH.defect",)}
    assert heg["reachable"] + lim["reachable"] == b["states"]["count"]


# -- backward ranks ------------------------------------------------------------------------------


def test_backward_ranks_agree_with_attractor(toy_bundle):
    b = toy_bundle
    g = explore(toy.compile())
    groups = [c["members"] for c in b["coalitions"]] + [list(g.model.actor_names)]
    for e, name in enumerate(b["endings"]):
        for c, coal in enumerate(groups):
            rank = attractor(g, coal, g.ending_states(name)).rank
            assert b["states"]["rank"][e][c] == [rank.get(s, -1) for s in range(g.size())]


# -- replays ----------------------------------------------------------------------------------


def gate():
    """``kind`` is swept: only a ``strong`` A may ``jump``; ``step`` is always available.
    Replaying a strong trace under ``weak`` stops at the first jump."""
    m = Model("gate", horizon=3)
    m.var("kind", levels=["weak", "strong"], init=None)
    m.counter("pos", max=3, init=0)
    a = m.actor("A")
    a.action("step", effect=Set("pos", 1), source="test")
    a.action("jump", guard=V.kind == "strong", effect=Set("pos", 3), source="test")
    m.ending("FAR", V.pos == 3)
    return m


def test_replay_stops_where_an_action_becomes_unavailable():
    cm = gate().compile()
    g = explore(cm)
    weak, strong = g.initial
    a = cm.actors[0]
    moves = [(a.action_index("step"), 0), (a.action_index("jump"), 0)]
    r = replay(cm, g, weak, moves)
    assert r["stop"] == {"index": 1, "reason": "unavailable", "actor": 0, "action": 2}
    assert len(r["states"]) == 2 and r["moves"] == [list(moves[0])]
    full = replay(cm, g, strong, moves)
    assert full["stop"] is None and len(full["states"]) == 3
    assert g.ending[full["states"][-1]] == "FAR"
    # a replay that reaches a terminal state before the moves run out stops there
    early = replay(cm, g, strong, [moves[1], moves[0]])
    assert early["stop"]["reason"] == "terminal" and early["stop"]["index"] == 1


def test_bundle_replays_every_reference_trace_under_every_other_hypothesis():
    b = bundle(gate(), endings=["FAR"], max_relax=0)
    (t,) = [t for t in b["traces"] if t["states"] is not None]
    assert b["hypotheses"]["items"][t["hypothesis"]]["values"] == {"kind": "strong"}
    (r,) = t["replays"]
    assert b["hypotheses"]["items"][r["hypothesis"]]["values"] == {"kind": "weak"}
    assert r["stop"]["reason"] == "unavailable" and r["stop"]["index"] == 0
    # a replay that stays available runs to the end
    b2 = bundle(coin(), max_relax=0)
    for t in b2["traces"]:
        for r in t["replays"]:
            assert r["stop"] is None and len(r["states"]) == len(t["states"])


# -- size policy and serialization -----------------------------------------------------------------


def test_moves_table_matches_the_graph(toy_bundle):
    import itertools

    b = toy_bundle
    g = explore(toy.compile())
    mv = b["moves"]
    assert mv["complete"]
    for s in range(0, g.size(), 37):
        if g.terminal[s]:
            assert mv["avail"][s] == -1
            continue
        avail = mv["avail_table"][mv["avail"][s]]
        assert avail == [list(a) for a in g.avail[s]]
        n = len(g.moves[s])
        assert [tuple(m) for m in g.moves[s]] == list(itertools.product(*avail))
        assert mv["succ"][mv["offset"][s] : mv["offset"][s] + n] == g.succ[s]


def test_size_policy_switches_at_max_moves():
    m = crisis()
    g = explore(m.compile())
    total = sum(len(x) for x in g.moves)
    full = bundle(m, max_moves=total, max_relax=0)
    assert full["moves"]["complete"] and full["meta"]["counts"]["moves_included"] == total
    part = bundle(m, max_moves=total - 1, max_relax=0)
    assert not part["moves"]["complete"]
    included = {s for s, k in enumerate(part["moves"]["avail"]) if k >= 0}
    shown = set()
    for t in part["traces"]:
        for ids in [t["states"] or []] + [r["states"] for r in t["replays"]]:
            shown.update(ids)
    hood = set(shown)
    frontier = set(shown)
    for _ in range(2):
        frontier = {u for s in frontier for u in g.succ[s]} - hood
        hood |= frontier
    assert included == {s for s in hood if not g.terminal[s]}
    assert part["meta"]["counts"]["moves_included"] == sum(len(g.moves[s]) for s in included)


def test_size_policy_on_the_toy_keeps_the_trace_neighborhood():
    b = bundle(toy, coalitions=[["INC"]], endings=["TAKEOVER"], max_moves=1000, max_relax=0)
    assert not b["moves"]["complete"]
    included = {s for s, k in enumerate(b["moves"]["avail"]) if k >= 0}
    assert 0 < len(included) < b["states"]["count"] // 4
    for t in b["traces"]:
        for s in t["states"] or []:
            assert s in included or b["states"]["terminal"][s]


def test_bundle_is_json_serializable_and_round_trips(toy_bundle):
    text = json.dumps(toy_bundle, allow_nan=False)
    assert json.loads(text) == toy_bundle


def test_status_and_class_names():
    assert STATUS_NAMES == ("kept", "contested", "lost", "failed")
    assert DECISION_NAMES == ("safe", "risky", "losing", "ends")


# -- inputs ------------------------------------------------------------------------------------


def test_snapshot_bundle_has_one_hypothesis_and_provenance():
    b = bundle(toy, snapshot="snapshots/toy/example.json", coalitions=[["INC"]], max_relax=0)
    assert b["meta"]["initial_source"] == "snapshot"
    assert b["hypotheses"]["variables"] == []
    assert [it["label"] for it in b["hypotheses"]["items"]] == ["snapshot"]
    snap = b["snapshot"]
    assert snap["date"] and "oversight" in snap["variables"]
    assert snap["variables"]["aims"]["confidence"] == "assumed"
    assert json.loads(json.dumps(b)) == b


def test_explicit_initial_states_and_unknown_endings():
    from wavefront.model import ModelError

    cm = gate().compile()
    weak = cm.initial_states()[0]
    b = bundle(gate(), initial=[weak], max_relax=0)
    assert b["meta"]["initial_source"] == "explicit"
    assert len(b["hypotheses"]["items"]) == 1
    with pytest.raises(ModelError, match="no ending named 'NOPE'"):
        bundle(gate(), endings=["NOPE"], max_relax=0)
    with pytest.raises(ValueError, match="either initial states or a snapshot"):
        bundle(gate(), initial=[weak], snapshot={}, max_relax=0)


def test_untimed_model_uses_depth_for_ticks():
    b = bundle(ladder(), max_relax=0)
    assert b["meta"]["timed"] is False
    g = explore(ladder().compile())
    assert b["states"]["tick"] == g.depth
    assert b["endings"] == [] and b["traces"] == []
    assert [p["id"] for p in b["properties"]] == ["invariant:low", "invariant:always"]
