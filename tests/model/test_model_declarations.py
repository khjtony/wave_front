"""DSL construction and compile-time errors."""

import pytest

from wavefront.model import TRUE, Bump, Ite, Model, ModelError, Set, SetIf, V, compile


def base(horizon=3):
    m = Model("m", horizon=horizon)
    m.var("cap", levels=["low", "mid", "high"], init="low")
    m.counter("stock", max=3, init=1)
    m.flag("rights")
    return m


# -- declarations ----------------------------------------------------------------------


def test_declarations_are_recorded():
    m = base()
    a = m.actor("A")
    act = a.action("grow", guard=V.cap < "high", effect=Bump("cap", 1), source="s", delay=1)
    assert act.effects[0].var == "cap" and act.delay == 1 and act.source == "s"
    assert act.guard is not None
    assert m.nature() is m.nature()
    assert m.actor_named("Nature").is_nature
    assert [d.name for d in m.variables] == ["cap", "stock", "rights"]


def test_horizon_must_be_positive_or_none():
    with pytest.raises(ModelError):
        Model("m", horizon=0)
    assert not Model("m", horizon=None).timed


@pytest.mark.parametrize(
    "declare",
    [
        lambda m: m.var("cap", levels=["a", "b"]),
        lambda m: m.counter("cap", max=2),
        lambda m: m.actor("cap"),
        lambda m: m.invariant("stock", TRUE),
        lambda m: m.ending("rights", TRUE),
        lambda m: m.latch("cap", of="stock", when=TRUE),
        lambda m: m.assume("cap", TRUE),
    ],
)
def test_duplicate_names_are_rejected(declare):
    m = base()
    with pytest.raises(ModelError, match="duplicate name"):
        declare(m)


@pytest.mark.parametrize(
    "name", ["tick", "last_x", "pending_a_b", "fair_x", "Nature", "all", "only", "not ok", "if"]
)
def test_reserved_and_invalid_names_are_rejected(name):
    m = Model("m", horizon=2)
    with pytest.raises(ModelError):
        m.var(name, levels=["a", "b"])


def test_duplicate_and_reserved_action_names():
    m = base()
    a = m.actor("A")
    a.action("x")
    with pytest.raises(ModelError, match="duplicate action"):
        a.action("x")
    with pytest.raises(ModelError, match="reserved"):
        a.action("idle")
    with pytest.raises(ModelError, match="reserved"):
        m.nature().event("none")
    # Different actors may reuse an action name.
    m.actor("B").action("x")


def test_level_and_init_validation():
    m = Model("m", horizon=2)
    with pytest.raises(ModelError, match="at least two levels"):
        m.var("v", levels=["a"])
    with pytest.raises(ModelError, match="duplicate levels"):
        m.var("v", levels=["a", "a"])
    with pytest.raises(ModelError, match="has no level 'z'"):
        m.var("v", levels=["a", "b"], init="z")
    with pytest.raises(ModelError):
        m.counter("c", max=2, init=3)
    with pytest.raises(ModelError):
        m.flag("f", init="yes")
    assert m.var("w", levels=["a", "b"]).init == 0  # defaults to the first level
    assert m.var("u", levels=["a", "b"], init=None).init is None


def test_bad_action_arguments():
    m = base()
    a = m.actor("A")
    with pytest.raises(ModelError, match="delay"):
        a.action("x", delay=-1)
    with pytest.raises(ModelError, match="not an effect"):
        a.action("y", effect=["cap"])
    with pytest.raises(ModelError, match="within"):
        m.fairness("f", actor="A", trigger=TRUE, within=0, responses=["idle"])


# -- compile errors --------------------------------------------------------------------


def test_unknown_level_names_variable_and_level():
    m = base()
    m.actor("A").action("x", guard=V.cap == "huge")
    with pytest.raises(ModelError, match=r"variable 'cap' has no level 'huge'"):
        m.compile()


def test_unknown_level_in_effect_and_ending():
    m = base()
    m.actor("A").action("x", effect=Set("cap", "huge"))
    with pytest.raises(ModelError, match="'cap' has no level 'huge'"):
        m.compile()
    m = base()
    m.ending("E", V.cap.is_in(["low", "nope"]))
    with pytest.raises(ModelError, match="no level 'nope'"):
        m.compile()


def test_unknown_variable_and_named_predicate():
    m = base()
    m.actor("A").action("x", guard=V.missing == 1)
    with pytest.raises(ModelError, match="unknown variable 'missing'"):
        m.compile()
    m = base()
    m.ending("E", V.invariant("nope"))
    with pytest.raises(ModelError, match="unknown invariant 'nope'"):
        m.compile()


def test_unresolvable_level_name_and_non_condition():
    m = base()
    m.ending("E", V.stock + 1 == "high")
    with pytest.raises(ModelError, match="'stock' has no level 'high'"):
        m.compile()
    m = base()
    m.ending("E", Ite(TRUE, 1, 2) == "high")
    with pytest.raises(ModelError, match="cannot be resolved"):
        m.compile()
    m2 = base()
    m2.ending("E", V.stock)  # a counter used as a condition
    with pytest.raises(ModelError, match="used as a condition"):
        m2.compile()


def test_effect_errors():
    m = base()
    m.actor("A").action("x", effect=Set("tick", 1))
    with pytest.raises(ModelError, match="built-in variable 'tick'"):
        m.compile()
    m = base()
    m.actor("A").action("x", effect=Set("stock", 7))
    with pytest.raises(ModelError, match="out of range"):
        m.compile()
    m = base()
    m.actor("A").action("x", effect=[Set("cap", "mid"), Set("cap", "high")])
    with pytest.raises(ModelError, match="two Sets"):
        m.compile()


def test_monotone_static_checks():
    m = Model("m", horizon=2)
    m.var("cap", levels=["low", "mid", "high"], monotone=True)
    m.actor("A").action("x", effect=Bump("cap", -1))
    with pytest.raises(ModelError, match="decreases monotone"):
        m.compile()
    m = Model("m", horizon=2)
    m.var("cap", levels=["low", "mid", "high"], monotone=True)
    m.actor("A").action("x", effect=SetIf(V.cap == "high", "cap", "low"))
    with pytest.raises(ModelError, match="lowest level"):
        m.compile()
    m = Model("m", horizon=2)
    m.var("cap", levels=["low", "mid", "high"], monotone=True)
    m.actor("A").action("x", effect=[Bump("cap", 1), Set("cap", "mid")])
    m.compile()  # not statically decreasing; checked at explore time


def test_observation_violation_in_guard():
    m = base()
    m.var("aims", levels=["limited", "hegemonic"], hidden_from=["A"])
    a = m.actor("A")
    a.action("x", guard=V.aims == "limited")
    with pytest.raises(ModelError, match=r"A\.x references variable 'aims'.*actor A"):
        m.compile()


def test_observation_violation_through_named_invariant():
    m = base()
    m.invariant("ok", V.stock >= 1)
    m.actor("A", observes=V.all_except("stock")).action("x", guard=V.invariant("ok"))
    with pytest.raises(ModelError, match="'stock'"):
        m.compile()


def test_observation_only_includes_own_builtins():
    m = base()
    a = m.actor("A", observes=V.only("cap"), remember_last=True)
    a.action("x", guard=(V.cap < "high") & (V.tick < 2) & (V.last_A == "idle"))
    a.action("y", delay=1)
    a.action("z", guard=V.pending_A_y == 0)
    cm = m.compile()
    assert cm.actors[0].observes == frozenset({"cap", "tick", "last_A", "pending_A_y"})
    m.actor("B").action("w", guard=V.stock > 0)
    a.action("bad", guard=V.stock > 0)
    with pytest.raises(ModelError, match="A.bad references variable 'stock'"):
        m.compile()


def test_observation_check_covers_fairness_triggers_and_profiles():
    m = base()
    m.var("h", levels=["a", "b"], hidden_from=["A"])
    m.actor("A").action("x")
    m.fairness("resp", actor="A", trigger=V.h == "b", within=1, responses=["x"])
    with pytest.raises(ModelError, match="trigger of fairness constraint 'resp'.*'h'"):
        m.compile()
    m = base()
    m.var("h", levels=["a", "b"], hidden_from=["A"])
    m.actor("A").action("x")
    m.profile("p", actor="A", forbid=["x"], unless=V.h == "b")
    with pytest.raises(ModelError, match="unless condition of profile 'p'.*'h'"):
        m.compile()
    # Nature observes everything.
    m = base()
    m.var("h", levels=["a", "b"], hidden_from=["A"])
    m.actor("A")
    m.nature().event("e", guard=V.h == "b")
    m.compile()


def test_hidden_from_and_observes_must_name_known_things():
    m = base()
    m.var("h", levels=["a", "b"], hidden_from=["Ghost"])
    with pytest.raises(ModelError, match="unknown actor 'Ghost'"):
        m.compile()
    m = base()
    m.actor("A", observes=V.only("ghost"))
    with pytest.raises(ModelError, match="unknown variable 'ghost'"):
        m.compile()


def test_profiles_and_fairness_are_validated():
    m = base()
    m.actor("A").action("x")
    m.profile("p", actor="A", forbid=["nope"])
    with pytest.raises(ModelError, match="no action 'nope'"):
        m.compile()
    m = base()
    m.actor("A").action("x")
    m.fairness("f", actor="B", trigger=TRUE, within=1, responses=["x"])
    with pytest.raises(ModelError, match="unknown actor 'B'"):
        m.compile()
    m = base()
    m.actor("A").action("x")
    with pytest.raises(ModelError, match="no profile 'p'"):
        compile(m, profile="p")


def test_untimed_model_has_no_tick():
    m = Model("m", horizon=None)
    m.counter("x", max=2)
    m.actor("A").action("a", guard=V.tick < 2)
    with pytest.raises(ModelError, match="untimed model has no variable 'tick'"):
        m.compile()
    m = Model("m", horizon=None)
    m.counter("x", max=2)
    cm = m.compile()
    assert "tick" not in cm.index and not cm.timed
    assert cm.initial_states() == [(0,)]
    assert not cm.is_terminal((2,)) and cm.ending_of((2,)) is None


def test_actor_without_actions():
    m = base()
    m.actor("A", idle=False)
    with pytest.raises(ModelError, match="no actions"):
        m.compile()
