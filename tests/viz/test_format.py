"""The guard and property formatter: every expression node kind renders and re-reads."""

import pytest

from models.toy.two_power import model as toy
from wavefront.model import Model, Set, V
from wavefront.model.expr import FALSE, TRUE, Ite, Max, Min
from wavefront.viz import bundle, expr_text, guard_text


@pytest.fixture(scope="module")
def cm():
    return toy.compile()


@pytest.mark.parametrize(
    ("expr", "text"),
    [
        (TRUE, "True"),
        (FALSE, "False"),
        (V.control, "V.control"),
        (V["control"], "V.control"),
        (V.aims == "hegemonic", 'V.aims == "hegemonic"'),
        # integer literals compared with a level variable print as the level name
        (V.tension == 1, 'V.tension == "crisis"'),
        (V.belief <= 1, 'V.belief <= "uncertain"'),
        # counters print integers, flags booleans
        (V.control < 3, "V.control < 3"),
        (V.guarantee == True, "V.guarantee == True"),  # noqa: E712 (builds a node)
        (V.guarantee, "V.guarantee"),
        (~V.guarantee, "not V.guarantee"),
        (~(V.control == 3), "not (V.control == 3)"),
        (V.belief.is_in(["uncertain", "hegemonic"]), 'V.belief in ["uncertain", "hegemonic"]'),
        (V.belief.is_in([0, 2]), 'V.belief in ["limited", "hegemonic"]'),
        (V.control + 1 >= 2, "V.control + 1 >= 2"),
        (V.control - (V.control - 1) == 1, "V.control - (V.control - 1) == 1"),
        (Min(V.control, 2) == 2, "min(V.control, 2) == 2"),
        (Max(V.oversight, 1) == "strong", 'max(V.oversight, "weak") == "strong"'),
        (
            V.control < Ite(V.aims == "hegemonic", 3, 1),
            'V.control < ite(V.aims == "hegemonic", 3, 1)',
        ),
        (V.invariant("balance"), 'invariant("balance")'),
        (V.ending("SETTLED"), 'ending("SETTLED")'),
        (V.tick == 12, "V.tick == 12"),
        (V.last_INC == "resist", 'V.last_INC == "resist"'),
        (V.belief_at_majority != "hegemonic", 'V.belief_at_majority != "hegemonic"'),
    ],
)
def test_every_node_kind_renders(cm, expr, text):
    assert expr_text(expr, cm) == text


def test_connectives_follow_precedence_and_flatten_chains(cm):
    a, b, c = V.aims == "hegemonic", V.control < 1, V.oversight >= "weak"
    assert expr_text(c & (a | b), cm) == (
        'V.oversight >= "weak" and (V.aims == "hegemonic" or V.control < 1)'
    )
    # ``(a & b) & c`` is one chain; an ``and`` inside an ``or`` is parenthesized for reading.
    assert expr_text((a & b) & c, cm) == (
        'V.aims == "hegemonic" and V.control < 1 and V.oversight >= "weak"'
    )
    assert expr_text(a | (b & c), cm) == (
        'V.aims == "hegemonic" or (V.control < 1 and V.oversight >= "weak")'
    )
    assert expr_text(~(a & b), cm) == 'not (V.aims == "hegemonic" and V.control < 1)'
    assert expr_text(a.implies(b), cm) == 'not (V.aims == "hegemonic") or V.control < 1'


def test_the_toy_guards_read_as_written(cm):
    guards = {
        f"{a.name}.{x.name}": expr_text(x.guard_expr, cm) for a in cm.actors for x in a.actions
    }
    assert guards["CH.expand"] == (
        'V.tension == "calm" and V.control < ite(V.aims == "hegemonic", 3, 1)'
    )
    assert guards["CH.defect"] == (
        'V.aims == "hegemonic" and V.last_INC == "resist" and not V.guarantee and V.control < 3'
    )
    assert guards["INC.resist"] == 'V.belief in ["uncertain", "hegemonic"]'
    assert guards["INC.idle"] == "True"


def strike_model():
    m = Model("strike", horizon=2)
    m.flag("china_war")
    m.var("arms_USSR", levels=["weak", "strong"], init="strong")
    m.flag("anticomintern")
    m.flag("struck")
    ger = m.actor("GER")
    ger.action(
        "strike_north",
        guard={
            "china_quiet": ~V.china_war,
            "ussr_weak": V.arms_USSR == "weak",
            "pact": V.anticomintern | V.struck,
        },
        effect=Set("struck", True),
        source="test",
    )
    ger.action("wait", guard=~V.china_war & ~V.struck, source="test")
    m.ending("STRUCK", V.struck)
    return m


def test_parted_guards_print_each_part_with_its_name():
    cm = strike_model().compile()
    strike, wait = cm.actors[0].actions[1:]
    text = (
        'china_quiet: not V.china_war and ussr_weak: V.arms_USSR == "weak" and '
        "pact: (V.anticomintern or V.struck)"
    )
    assert guard_text(strike, cm) == text
    assert (
        guard_text(wait, cm) == expr_text(wait.guard_expr, cm) == "not V.china_war and not V.struck"
    )
    relaxed = strike_model().compile(relax={"GER.strike_north:ussr_weak"})
    assert guard_text(relaxed.actors[0].actions[1], relaxed) == (
        "china_quiet: not V.china_war and ussr_weak: True and pact: (V.anticomintern or V.struck)"
    )
    b = bundle(strike_model())
    actions = {x["name"]: x["guard_text"] for x in b["actors"][0]["actions"]}
    assert actions["strike_north"] == text
    assert actions["wait"] == "not V.china_war and not V.struck"


def test_without_a_model_literals_print_as_written():
    assert expr_text((V.x == "high") & (V.n + 1 > 2)) == 'V.x == "high" and V.n + 1 > 2'
    assert expr_text(V["odd name"] == 1) == 'V["odd name"] == 1'
    assert expr_text(V.x == 'say "hi"') == 'V.x == "say \\"hi\\""'


class _Level(int):
    """A level index that compares with level names of its own variable."""

    def __new__(cls, value, levels):
        obj = super().__new__(cls, value)
        obj.levels = levels
        return obj

    def _other(self, other):
        return self.levels.index(other) if isinstance(other, str) else int(other)

    def __eq__(self, other):
        return int(self) == self._other(other)

    def __ne__(self, other):
        return int(self) != self._other(other)

    def __lt__(self, other):
        return int(self) < self._other(other)

    def __le__(self, other):
        return int(self) <= self._other(other)

    def __gt__(self, other):
        return int(self) > self._other(other)

    def __ge__(self, other):
        return int(self) >= self._other(other)

    __hash__ = int.__hash__


def test_rereads_as_python(cm):
    """The text, evaluated as Python with level names compared against each variable's own
    levels, gives what the compiled guard computes: operators and parentheses are placed
    correctly."""
    from wavefront.engine import explore

    g = explore(cm)
    exprs = [x.guard_expr for a in cm.actors for x in a.actions] + list(toy.invariants.values())
    for expr in exprs:
        text = expr_text(expr, cm)
        for sid in range(0, g.size(), 97):
            state = g.states[sid]

            class Ns:
                def __getattr__(self, name, state=state):
                    v = cm.variables[cm.index[name]]
                    x = state[cm.index[name]]
                    if v.kind == "flag":
                        return bool(x)
                    if v.kind == "counter" or v.origin in ("tick", "pending", "fair"):
                        return x
                    return _Level(x, list(v.levels))

            # ``x in ["a", "b"]`` falls back to the reflected ``_Level.__eq__``.
            env = {"V": Ns(), "ite": lambda c, a, b: a if c else b, "min": min, "max": max}
            assert bool(eval(text, env)) == bool(cm.evaluate(expr, state)), (text, sid)
