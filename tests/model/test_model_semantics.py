"""Compiled-model semantics: layout, evaluation, composition and system updates."""

import itertools

import pytest

from wavefront.engine import explore
from wavefront.model import (
    FALSE,
    TRUE,
    Bump,
    Inc,
    Ite,
    Max,
    Min,
    Model,
    ModelError,
    Reset,
    Set,
    SetIf,
    V,
)


def move(cm, **chosen):
    """A joint move by action names; unnamed actors play their first (built-in) action."""
    return tuple(
        actor.action_index(chosen[actor.name]) if actor.name in chosen else 0 for actor in cm.actors
    )


def val(cm, state, name):
    return cm.level_name(name, state[cm.index[name]])


def at(cm, **values):
    """A state with the given variables (level names or ints); others take their init."""
    s = list(cm.initial_states()[0])
    for name, v in values.items():
        spec = cm.variables[cm.index[name]]
        s[cm.index[name]] = spec.levels.index(v) if isinstance(v, str) else int(v)
    return tuple(s)


def simple():
    m = Model("m", horizon=5)
    m.var("cap", levels=["low", "mid", "high"])
    m.counter("stock", max=3, init=1)
    m.flag("rights")
    return m


# -- layout and evaluation -------------------------------------------------------------


def test_state_layout_and_actor_order():
    m = simple()
    m.latch("cap_at_rights", of="cap", when=V.rights == True)  # noqa: E712
    a = m.actor("A", remember_last=True)
    a.action("slow", delay=2)
    m.actor("B", idle=False).action("only")
    m.fairness("f", actor="B", trigger=FALSE, within=2, responses=["only"])
    cm = m.compile()
    names = [v.name for v in cm.variables]
    assert names == [
        "tick",
        "cap",
        "stock",
        "rights",
        "cap_at_rights",
        "pending_A_slow",
        "last_A",
        "fair_f",
    ]
    kinds = [v.kind for v in cm.variables]
    assert kinds == ["builtin", "level", "counter", "flag"] + ["builtin"] * 4
    assert cm.variables[cm.index["cap_at_rights"]].levels == ("unset", "low", "mid", "high")
    assert cm.variables[cm.index["last_A"]].levels == ("none", "idle", "slow")
    assert cm.actor_names == ["A", "B", "Nature"]
    assert [a.name for a in cm.actors[0].actions] == ["idle", "slow"]
    assert [a.name for a in cm.actors[1].actions] == ["only"]
    assert [a.name for a in cm.actors[2].actions] == ["none"]
    assert cm.actors[0].actions[0].is_idle and not cm.actors[0].actions[1].is_idle


def test_initial_states_are_the_product_of_inits():
    m = Model("m", horizon=2)
    m.var("a", levels=["x", "y", "z"], init=None)
    m.flag("f", init=None)
    m.counter("c", max=2, init=1)
    cm = m.compile()
    states = cm.initial_states()
    assert len(states) == 6
    assert set(states) == {(0, a, f, 1) for a in range(3) for f in range(2)}


def test_generated_guards_match_hand_evaluation():
    m = Model("m", horizon=4)
    m.var("cap", levels=["low", "mid", "high"])
    m.counter("stock", max=3)
    m.flag("f")
    cm = m.compile()
    exprs = {
        "cmp": lambda c, s, f: c < 2,
        "and": lambda c, s, f: c >= 1 and s != 2,
        "or": lambda c, s, f: c == 0 or f == 1,
        "not": lambda c, s, f: not (c <= 1),
        "in": lambda c, s, f: c in (0, 2),
        "imp": lambda c, s, f: (not f == 1) or s > 0,
        "arith": lambda c, s, f: s + 1 >= c - 1,
        "minmax": lambda c, s, f: min(c, s) < max(s, 2),
        "ite": lambda c, s, f: (s if f == 1 else c) == 2,
        "flag": lambda c, s, f: f == 1,
        "var": lambda c, s, f: c > s,
        "const": lambda c, s, f: True,
    }
    built = {
        "cmp": V.cap < "high",
        "and": (V.cap >= "mid") & (V.stock != 2),
        "or": (V.cap == "low") | (V.f == True),  # noqa: E712
        "not": ~(V.cap <= 1),
        "in": V.cap.is_in(["low", "high"]),
        "imp": (V.f == True).implies(V.stock > 0),  # noqa: E712
        "arith": V.stock + 1 >= V.cap - 1,
        "minmax": Min(V.cap, V.stock) < Max(V.stock, 2),
        "ite": Ite(V.f, V.stock, V.cap) == 2,
        "flag": V.f,
        "var": V.cap > V.stock,
        "const": TRUE,
    }
    for c, s, f in itertools.product(range(3), range(4), range(2)):
        state = (0, c, s, f)
        for key, expected in exprs.items():
            assert cm.evaluate(built[key], state) == expected(c, s, f), key
    assert cm.evaluate(V.stock + 2, (0, 0, 1, 0)) == 3
    assert (V.cap < "high").to_python(cm)((0, 1, 0, 0)) is True
    assert cm.evaluate(Ite(V.f, 1, 0), (0, 0, 0, 1)) == 1


def test_evaluate_named_predicates_and_references():
    m = simple()
    m.invariant("ok", V.stock >= 1)
    m.ending("WIN", V.invariant("ok") & (V.cap == "high"))
    m.ending("LOSE", ~V.ending("WIN") & (V.stock == 0))
    cm = m.compile()
    s = at(cm, cap="high", stock=2)
    assert cm.evaluate("ok", s) is True
    assert cm.evaluate("WIN", s) is True
    assert cm.evaluate("LOSE", s) is False
    with pytest.raises(ModelError):
        cm.evaluate("nothing", s)


def test_recursive_named_predicate_is_an_error():
    m = simple()
    m.invariant("a", V.invariant("a"))
    with pytest.raises(ModelError, match="refers to itself"):
        m.compile()


def test_format_state_uses_level_names():
    cm = simple().compile()
    s = at(cm, cap="mid", rights=1)
    assert cm.format_state(s) == "{tick=0, cap=mid, stock=1, rights=True}"
    assert cm.state_dict(s)["cap"] == "mid"


def test_budget_counts():
    m = simple()
    a = m.actor("A")
    a.action("x", guard=V.cap < "high", effect=Bump("cap", 1), speculative=True)
    a.action("y", delay=2)
    m.latch("l", of="cap", when=TRUE)
    m.fairness("f", actor="A", trigger=FALSE, within=1, responses=["x"])
    b = m.compile().budget()
    assert b["variables"] == 3
    assert b["levels"] == 3 + 4 + 2
    assert b["actions"] == 2
    assert b["guards"] == 1
    assert b["speculative_actions"] == 1
    assert b["delays"] == 1
    assert b["latches"] == 1
    assert b["fairness_constraints"] == 1


# -- effect composition ------------------------------------------------------------------


def test_effects_are_evaluated_on_the_pre_state():
    m = Model("m", horizon=3)
    m.var("a", levels=["x", "y"])
    m.var("b", levels=["x", "y"], init="y")
    p = m.actor("P")
    p.action("swap", effect=[Set("a", V.b), Set("b", V.a)])
    cm = m.compile()
    s = cm.step(cm.initial_states()[0], move(cm, P="swap"))
    assert val(cm, s, "a") == "y" and val(cm, s, "b") == "x"


def test_set_then_summed_bumps_then_clamp():
    m = simple()
    m.actor("A").action("set", effect=Set("stock", 1))
    m.actor("B").action("up", effect=Bump("stock", 2))
    m.actor("C").action("up", effect=Inc("stock"))
    cm = m.compile()
    s0 = at(cm, stock=0)
    s = cm.step(s0, move(cm, A="set", B="up", C="up"))
    assert s[cm.index["stock"]] == 3  # 1 + 2 + 1 = 4, clamped to 3
    s = cm.step(s0, move(cm, A="set", B="up"))
    assert s[cm.index["stock"]] == 3
    s = cm.step(s0, move(cm, A="set"))
    assert s[cm.index["stock"]] == 1
    s = cm.step(s0, move(cm, C="up"))
    assert s[cm.index["stock"]] == 1
    assert s[cm.index["tick"]] == 1


def test_negative_bumps_clamp_at_zero_and_strict_raises():
    m = simple()
    m.actor("A").action("down", effect=Bump("stock", -5))
    m.actor("B").action("down", effect=Bump("stock", -1, strict=True))
    cm = m.compile()
    s0 = at(cm, stock=1)
    assert cm.step(s0, move(cm, A="down"))[cm.index["stock"]] == 0
    assert cm.step(s0, move(cm, B="down"))[cm.index["stock"]] == 0
    with pytest.raises(ModelError, match="strict Bump.*'stock'"):
        cm.step(at(cm, stock=0), move(cm, B="down"))


def test_set_if_and_reset_and_expression_values():
    m = simple()
    a = m.actor("A")
    a.action("cond", effect=SetIf(V.cap == "high", "rights", True))
    a.action("reset", effect=Reset("stock"))
    a.action("copy", effect=Set("stock", V.cap + 2))
    cm = m.compile()
    assert cm.step(at(cm, cap="low"), move(cm, A="cond"))[cm.index["rights"]] == 0
    assert cm.step(at(cm, cap="high"), move(cm, A="cond"))[cm.index["rights"]] == 1
    assert cm.step(at(cm, stock=3), move(cm, A="reset"))[cm.index["stock"]] == 0
    assert cm.step(at(cm, cap="mid"), move(cm, A="copy"))[cm.index["stock"]] == 3
    assert cm.step(at(cm, cap="high"), move(cm, A="copy"))[cm.index["stock"]] == 3  # clamped


def test_equal_sets_do_not_conflict_but_different_ones_do_at_explore_time():
    m = simple()
    m.actor("A").action("hi", effect=Set("cap", "high"))
    m.actor("B").action("hi", effect=Set("cap", "high"))
    m.actor("C").action("mid", effect=Set("cap", "mid"))
    cm = m.compile()
    s0 = cm.initial_states()[0]
    assert val(cm, cm.step(s0, move(cm, A="hi", B="hi")), "cap") == "high"
    with pytest.raises(
        ModelError, match=r"conflicting Set on 'cap' in state \{tick=0.*sets high; C\.mid sets mid"
    ):
        explore(cm)
    with pytest.raises(ModelError, match="C.mid sets mid"):
        cm.step(s0, move(cm, A="hi", C="mid"))


# -- delays ----------------------------------------------------------------------------


def test_delay_one_timing():
    """d=1: chosen at t, unavailable at t+1, effect visible at t+2."""
    m = Model("m", horizon=6)
    m.counter("x", max=5)
    a = m.actor("A")
    a.action("act", effect=Inc("x"), delay=1)
    cm = m.compile()
    act = cm.actors[0].action_index("act")
    s0 = cm.initial_states()[0]
    assert act in cm.available(s0)[0]
    s1 = cm.step(s0, move(cm, A="act"))  # chosen at t=0
    assert s1[cm.index["x"]] == 0 and s1[cm.index["pending_A_act"]] == 1
    assert act not in cm.available(s1)[0]  # unavailable at t+1
    s2 = cm.step(s1, move(cm))
    assert s2[cm.index["tick"]] == 2 and s2[cm.index["x"]] == 1  # visible at t+2
    assert s2[cm.index["pending_A_act"]] == 0 and act in cm.available(s2)[0]


def test_delay_two_timing_and_composition_after_immediate_effects():
    m = Model("m", horizon=6)
    m.counter("x", max=5)
    a = m.actor("A")
    a.action("late", effect=Set("x", 4), delay=2)
    b = m.actor("B")
    b.action("now", effect=Inc("x"))
    cm = m.compile()
    late = cm.actors[0].action_index("late")
    s = cm.initial_states()[0]
    s = cm.step(s, move(cm, A="late"))
    seen = []
    for _ in range(3):
        seen.append((s[cm.index["x"]], late in cm.available(s)[0]))
        s = cm.step(s, move(cm, B="now"))
    # ticks 1, 2 unavailable; the Set lands in the transition 2 -> 3 after B's Bump.
    assert seen == [(0, False), (1, False), (4, True)]


# -- last action, latches, fairness, profiles -----------------------------------------------


def test_last_action_variable():
    m = simple()
    a = m.actor("A", remember_last=True)
    a.action("x")
    cm = m.compile()
    s0 = cm.initial_states()[0]
    assert val(cm, s0, "last_A") == "none"
    assert val(cm, cm.step(s0, move(cm, A="x")), "last_A") == "x"
    assert val(cm, cm.step(s0, move(cm)), "last_A") == "idle"


def test_latch_captures_value_once():
    m = simple()
    m.latch("cap_at", of="cap", when=V.stock >= 2)
    a = m.actor("A")
    a.action("up", effect=Inc("stock"))
    a.action("grow", effect=Bump("cap", 1))
    a.action("both", effect=[Inc("stock"), Bump("cap", 1)])
    cm = m.compile()
    s = cm.initial_states()[0]
    assert val(cm, s, "cap_at") == "unset"
    s = cm.step(s, move(cm, A="grow"))
    assert val(cm, s, "cap_at") == "unset"
    s = cm.step(s, move(cm, A="both"))  # stock 2, cap high: latch sees the new state
    assert val(cm, s, "cap_at") == "high"
    s = cm.step(s, move(cm, A="up"))
    assert val(cm, s, "cap_at") == "high"


def test_latch_set_in_initial_state_when_condition_holds():
    m = simple()
    m.latch("cap_at", of="cap", when=V.stock >= 1)
    cm = m.compile()
    assert val(cm, cm.initial_states()[0], "cap_at") == "low"


def test_fairness_counter_and_restriction():
    m = simple()
    a = m.actor("A")
    a.action("respond", guard=V.stock >= 1)
    a.action("other")
    m.nature().event("alarm", effect=Set("rights", True))
    m.fairness("f", actor="A", trigger=V.rights == True, within=2, responses=["respond"])  # noqa: E712
    cm = m.compile()
    f = cm.index["fair_f"]
    s = cm.initial_states()[0]
    s = cm.step(s, move(cm, Nature="alarm"))
    assert s[f] == 1 and len(cm.available(s)[0]) == 3
    s2 = cm.step(s, move(cm, A="other"))
    assert s2[f] == 2
    assert cm.available(s2)[0] == [cm.actors[0].action_index("respond")]
    assert cm.step(s2, move(cm, A="other", Nature="alarm"))[f] == 2  # min(counter + 1, within)
    assert cm.step(s, move(cm, A="respond", Nature="alarm"))[f] == 0  # responded
    quiet = at(cm, rights=0, fair_f=1)
    assert cm.step(quiet, move(cm, A="other"))[f] == 0  # trigger off
    starved = at(cm, stock=0, rights=1, fair_f=2)
    with pytest.raises(ModelError, match="fairness constraint 'f' restricts actor A"):
        cm.available(starved)


def test_profiles_are_inert_unless_selected():
    m = simple()
    a = m.actor("A")
    a.action("strike")
    m.profile("calm", actor="A", forbid=["strike"], unless=V.cap == "high")
    strike = 1
    assert strike in m.compile().available(at(m.compile(), cap="low"))[0]
    cm = m.compile(profile="calm")
    assert strike not in cm.available(at(cm, cap="low"))[0]
    assert strike in cm.available(at(cm, cap="high"))[0]
    cm = m.compile(profile=["calm"], relax={"calm"})
    assert strike in cm.available(at(cm, cap="low"))[0]


def test_monotone_violation_at_explore_time():
    m = Model("m", horizon=3)
    m.var("cap", levels=["low", "mid", "high"], monotone=True, init="mid")
    m.actor("A").action("set_mid", effect=Set("cap", "mid"))
    m.actor("B").action("grow", effect=Bump("cap", 1))
    cm = m.compile()
    with pytest.raises(ModelError, match=r"monotone variable 'cap' decreases from high to mid"):
        explore(cm)


def test_no_available_action_names_state_and_actor():
    m = simple()
    m.actor("A", idle=False).action("x", guard=V.stock >= 1, effect=Reset("stock"))
    cm = m.compile()
    with pytest.raises(ModelError, match=r"actor A has no available action in state \{tick=1"):
        explore(cm)


def test_endings_must_be_exclusive():
    m = simple()
    m.actor("A").action("up", effect=Inc("stock"))
    m.ending("ONE", V.stock >= 2)
    m.ending("TWO", (V.stock >= 2) & (V.cap == "low"))
    cm = m.compile()
    with pytest.raises(ModelError, match="endings ONE, TWO hold together"):
        explore(cm)


def test_terminal_states_and_horizon():
    m = simple()
    m.ending("FULL", V.stock == 3)
    cm = m.compile()
    assert cm.ending_of(at(cm, stock=3)) == "FULL"
    assert cm.is_terminal(at(cm, stock=3))
    assert cm.ending_of(at(cm, tick=5)) == "HORIZON"
    assert cm.ending_of(at(cm, tick=4)) is None and not cm.is_terminal(at(cm, tick=4))


# -- assumptions and relaxation ----------------------------------------------------------------


def relaxable():
    m = simple()
    a = m.actor("A")
    a.action("grow", guard=V.stock >= 2, effect=Bump("cap", 1))
    a.action("free")
    a.action("strike")
    m.nature().event("e", guard=V.cap == "high")
    m.fairness("f", actor="A", trigger=FALSE, within=1, responses=["grow"])
    m.profile("calm", actor="A", forbid=["strike"])
    m.profile("other", actor="A", forbid=["free"])
    m.assume("rich", V.stock >= 1)
    m.var("pick", levels=["a", "b"], init=None)
    return m


def test_assumptions_are_listed():
    m = relaxable()
    assert m.compile().assumptions() == ["A.grow", "Nature.e", "f", "rich"]
    assert m.compile(profile="calm").assumptions() == ["A.grow", "Nature.e", "f", "calm", "rich"]
    assert m.compile(relax={"f", "A.grow"}).assumptions() == m.compile().assumptions()


def test_relaxing_guards_fairness_assumes():
    m = relaxable()
    cm = m.compile()
    grow = cm.actors[0].action_index("grow")
    assert grow not in cm.available(at(cm, stock=1))[0]
    cm = m.compile(relax=["A.grow"])
    assert grow in cm.available(at(cm, stock=1))[0]
    assert "fair_f" in m.compile().index and "fair_f" not in m.compile(relax={"f"}).index
    m2 = Model("m", horizon=2)
    m2.counter("c", max=2, init=None)
    m2.assume("pos", V.c >= 1)
    assert m2.compile().initial_states() == [(0, 1), (0, 2)]
    assert len(m2.compile(relax={"pos"}).initial_states()) == 3
    m.compile(relax={"A.free"})  # a TRUE guard: accepted, no effect
    with pytest.raises(ModelError, match="unknown assumption"):
        m.compile(relax={"A.nothing"})


def test_observe_projects_onto_observed_variables():
    m = simple()
    m.var("h", levels=["a", "b"], hidden_from=["A"])
    m.actor("A", observes=V.all_except("stock"))
    cm = m.compile()
    s = at(cm, cap="mid", stock=2, rights=1, h="b")
    assert cm.observe("A", s) == (0, 1, 1)  # tick, cap, rights
    assert cm.observe("Nature", s) == s
