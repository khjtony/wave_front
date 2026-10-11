"""Expression trees: construction, operators, visitor protocol."""

import pytest

from wavefront.model import FALSE, TRUE, Ite, Max, Min, V
from wavefront.model.expr import (
    And,
    Arith,
    Cmp,
    Const,
    EndingRef,
    InSet,
    InvariantRef,
    Lit,
    Not,
    Observes,
    Or,
    VarRef,
    walk,
)


def test_var_ref_and_comparisons_build_nodes():
    e = V.cap < "high"
    assert isinstance(e, Cmp)
    assert e.op == "<"
    assert isinstance(e.left, VarRef) and e.left.name == "cap"
    assert isinstance(e.right, Lit) and e.right.value == "high"
    for op, node in [
        ("==", V.x == 1),
        ("!=", V.x != 1),
        ("<=", V.x <= 1),
        (">", V.x > 1),
        (">=", V.x >= 1),
    ]:
        assert node.op == op


def test_reflected_comparison_swaps_sides():
    e = 2 < V.x  # Python calls V.x.__gt__(2)
    assert e.op == ">" and e.left.name == "x" and e.right.value == 2


def test_var_to_var_comparison():
    e = V.a == V.b
    assert isinstance(e.right, VarRef) and e.right.name == "b"


def test_boolean_connectives():
    a, b = V.x == 1, V.y == 2
    assert isinstance(a & b, And) and (a & b).items == (a, b)
    assert isinstance(a | b, Or)
    assert isinstance(~a, Not) and (~a).item is a
    imp = a.implies(b)
    assert isinstance(imp, Or) and isinstance(imp.items[0], Not) and imp.items[1] is b


def test_python_bools_lift_to_constants():
    a = V.x == 1
    assert (a & True).items[1] is TRUE
    assert (False | a).items[0] is FALSE
    assert isinstance(TRUE, Const) and TRUE.value is True


def test_is_in_and_arithmetic():
    e = V.cap.is_in(["low", "high"])
    assert isinstance(e, InSet) and e.values == ("low", "high")
    s = V.stock + 1
    assert isinstance(s, Arith) and s.op == "+"
    r = 3 - V.stock
    assert isinstance(r, Arith) and r.left.value == 3 and r.right.name == "stock"
    m = Min(V.a, V.b, 2)
    assert len(m.args) == 3 and m.args[2].value == 2
    assert isinstance(Max(V.a, 1).args[1], Lit)
    i = Ite(V.f == True, 1, V.a)  # noqa: E712
    assert isinstance(i.then, Lit) and isinstance(i.orelse, VarRef)


def test_min_max_need_two_arguments():
    with pytest.raises(ValueError):
        Min(V.a)
    with pytest.raises(ValueError):
        Max()


def test_expressions_have_no_truth_value():
    with pytest.raises(TypeError, match="no truth value"):
        bool(V.x == 1)
    with pytest.raises(TypeError):
        if V.x < 2:  # noqa: SIM108
            pass


def test_nodes_are_immutable_and_hash_by_identity():
    e = V.x == 1
    with pytest.raises(AttributeError):
        e.op = "!="  # type: ignore[misc]
    d = {e: 1}
    assert d[e] == 1
    assert hash(e) != hash(V.x == 1) or e is not (V.x == 1)


def test_named_references_and_observation_sets():
    assert isinstance(V.invariant("balance"), InvariantRef)
    assert isinstance(V.ending("WIN"), EndingRef)
    assert V.all() == Observes("all")
    assert V.all_except("a", "b") == Observes("except", ("a", "b"))
    assert V.only("a") == Observes("only", ("a",))
    assert V["all"].name == "all"
    assert V.tick.name == "tick"


def test_walk_children_and_free_vars():
    e = ((V.a < "x") & ~(V.b == V.c)) | (Min(V.d, 1) > V.tick)
    names = [type(n).__name__ for n in walk(e)]
    assert names[0] == "Or"
    assert e.free_vars() == frozenset({"a", "b", "c", "d", "tick"})
    assert (V.a.is_in(["x"])).free_vars() == frozenset({"a"})
    assert (V.invariant("i") & TRUE).free_vars() == frozenset()


def test_visitor_dispatches_on_class_name():
    class Counter:
        def __init__(self):
            self.seen = []

        def __getattr__(self, name):
            if name.startswith("visit_"):

                def visit(node):
                    self.seen.append(name)
                    for child in node.children():
                        child.accept(self)
                    return name

                return visit
            raise AttributeError(name)

    c = Counter()
    assert (V.a < 2).accept(c) == "visit_Cmp"
    assert c.seen == ["visit_Cmp", "visit_VarRef", "visit_Lit"]


def test_bad_operands_raise():
    with pytest.raises(TypeError):
        V.x == 1.5  # noqa: B015
    with pytest.raises(TypeError):
        (V.x == 1) & 3
