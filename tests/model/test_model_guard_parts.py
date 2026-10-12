"""Guards declared as named parts: declaration, assumptions, relaxation, availability and
the observation check (spec 3.1, 4)."""

import pytest

from wavefront.model import TRUE, Model, ModelError, Set, V
from wavefront.model.expr import And, Const


def parted(form="dict"):
    """``A.strike`` needs three conditions, declared as named parts; ``A.wait`` has a plain
    guard; ``A.free`` none."""
    m = Model("m", horizon=3)
    m.flag("war")
    m.var("arms", levels=["weak", "strong"], init="strong")
    m.flag("pact")
    m.flag("struck")
    a = m.actor("A")
    a.action("wait", guard=~V.struck, source="test")
    parts = {"quiet": ~V.war, "weak": V.arms == "weak", "pact": V.pact}
    guard = parts if form == "dict" else list(parts.items())
    a.action("strike", guard=guard, effect=Set("struck", True), source="test")
    a.action("free", source="test")
    m.nature().event("start", guard=~V.war, effect=Set("war", True), source="test")
    m.ending("STRUCK", V.struck)
    return m


def strike_available(cm, **values):
    s = list(cm.initial_states()[0])
    for name, v in values.items():
        spec = cm.variables[cm.index[name]]
        s[cm.index[name]] = spec.levels.index(v) if isinstance(v, str) else int(v)
    a = cm.actors[0]
    return a.action_index("strike") in cm.available(tuple(s))[0]


# -- declaration -------------------------------------------------------------------------


@pytest.mark.parametrize("form", ["dict", "list"])
def test_parts_are_recorded_in_order_with_their_conjunction(form):
    m = parted(form)
    decl = m.actors[0].actions[1]
    assert [n for n, _ in decl.guard_parts] == ["quiet", "weak", "pact"]
    assert isinstance(decl.guard, And) and len(decl.guard.items) == 3
    assert decl.assumption == "A.strike" and decl.part_assumption("pact") == "A.strike:pact"
    assert m.actors[0].actions[0].guard_parts == ()


def test_a_list_of_pairs_accepts_bools_and_a_single_part():
    m = Model("m", horizon=2)
    a = m.actor("A")
    one = a.action("one", guard=[("only", V.tick < 1)])
    assert one.guard is one.guard_parts[0][1]
    trivial = a.action("trivial", guard={"always": True, "never": False})
    assert trivial.guard_parts[0][1] is TRUE
    assert isinstance(trivial.guard, Const) and not trivial.guard.value  # TRUE parts dropped


@pytest.mark.parametrize(
    ("guard", "match"),
    [
        ([("p", V.tick < 1), ("p", V.tick < 2)], "duplicate guard part name 'p'"),
        ({"not ok": V.tick < 1}, "not a Python identifier"),
        ({"if": V.tick < 1}, "not a Python identifier"),
        ([(3, V.tick < 1)], "not a Python identifier"),
        ({"": V.tick < 1}, "not a Python identifier"),
        ([("p", V.tick < 1, "extra")], r"not a \(name, expr\) pair"),
        (["p"], r"not a \(name, expr\) pair"),
        ({}, "at least one part"),
        ({"p": "weak"}, "not a boolean expression"),
        (5, "is not an expression"),
    ],
)
def test_bad_parted_guards_are_rejected(guard, match):
    a = Model("m", horizon=2).actor("A")
    with pytest.raises(ModelError, match=match):
        a.action("x", guard=guard)


# -- assumptions and relaxation ------------------------------------------------------------


def test_assumptions_list_parts_in_place_of_the_guard():
    m = parted()
    expected = ["A.wait", "A.strike:quiet", "A.strike:weak", "A.strike:pact", "Nature.start"]
    assert m.compile().assumptions() == expected
    assert m.compile(relax={"A.strike:weak"}).assumptions() == expected
    assert m.compile(relax={"A.strike"}).assumptions() == expected
    # trivial parts are omitted, as trivial guards are
    m2 = Model("m", horizon=2)
    m2.actor("A").action("x", guard={"always": TRUE, "late": V.tick >= 1})
    assert m2.compile().assumptions() == ["A.x:late"]


def test_availability_needs_every_part():
    cm = parted().compile()
    assert strike_available(cm, war=0, arms="weak", pact=1)
    assert not strike_available(cm, war=1, arms="weak", pact=1)
    assert not strike_available(cm, war=0, arms="strong", pact=1)
    assert not strike_available(cm, war=0, arms="weak", pact=0)
    assert not strike_available(cm)  # the initial state: arms strong, no pact


def test_relaxing_one_part_drops_that_conjunct_only():
    cm = parted().compile(relax={"A.strike:pact"})
    strike = cm.actors[0].actions[cm.actors[0].action_index("strike")]
    assert [(n, e is TRUE) for n, e in strike.guard_parts] == [
        ("quiet", False),
        ("weak", False),
        ("pact", True),
    ]
    assert isinstance(strike.guard_expr, And) and len(strike.guard_expr.items) == 2
    assert strike_available(cm, war=0, arms="weak", pact=0)
    assert not strike_available(cm, war=1, arms="weak", pact=0)
    assert not strike_available(cm, war=0, arms="strong", pact=0)


def test_relaxing_the_action_name_relaxes_every_part():
    m = parted()
    whole = m.compile(relax={"A.strike"})
    parts = m.compile(relax={"A.strike:quiet", "A.strike:weak", "A.strike:pact"})
    for cm in (whole, parts):
        strike = cm.actors[0].actions[cm.actors[0].action_index("strike")]
        assert strike.guard_expr is TRUE
        assert all(e is TRUE for _, e in strike.guard_parts)
        assert strike_available(cm, war=1, arms="strong", pact=0)
    assert {"A.strike:quiet", "A.strike:weak", "A.strike:pact"} <= whole.relax


def test_unknown_parts_are_errors_and_trivial_parts_no_ops():
    m = parted()
    with pytest.raises(ModelError, match="unknown assumption.*A.strike:nope"):
        m.compile(relax={"A.strike:nope"})
    with pytest.raises(ModelError, match="unknown assumption.*A.wait:x"):
        m.compile(relax={"A.wait:x"})  # a plain guard has no parts
    m2 = Model("m", horizon=2)
    m2.actor("A").action("x", guard={"always": TRUE, "late": V.tick >= 1})
    m2.compile(relax={"A.x:always"})  # accepted, no effect


def test_plain_guards_keep_their_behaviour():
    cm = parted().compile(relax={"A.wait"})
    wait = cm.actors[0].actions[cm.actors[0].action_index("wait")]
    assert wait.guard_parts == () and wait.guard_expr is TRUE


# -- observation check ---------------------------------------------------------------------


def test_observation_check_applies_to_every_part():
    m = Model("m", horizon=2)
    m.var("aims", levels=["limited", "hegemonic"], hidden_from=["A"])
    m.flag("ready")
    a = m.actor("A")
    a.action("x", guard={"ready": V.ready, "aims": V.aims == "limited"})
    with pytest.raises(ModelError, match=r"guard part A\.x:aims references variable 'aims'"):
        m.compile()
    # Nature observes everything
    m2 = Model("m", horizon=2)
    m2.var("aims", levels=["limited", "hegemonic"], hidden_from=["A"])
    m2.actor("A")
    m2.nature().event("e", guard={"aims": V.aims == "limited"})
    m2.compile()
