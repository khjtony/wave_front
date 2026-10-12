"""Z3 encoding of a compiled model unrolled to ``k`` transitions (spec section 6).

The encoding mirrors :meth:`wavefront.model.compile.CompiledModel._successor` step by
step, so that every assignment satisfying the transition constraints between ticks ``t``
and ``t + 1`` is a joint move the explicit engine allows and the successor it computes.

Unknowns
--------
- ``state[t][i]``: an ``Int`` per state variable ``i`` (in state order) per tick
  ``t = 0..k``, constrained to ``0..size-1``.
- ``chosen[t][a]``: an ``Int`` per actor ``a`` (Nature last) per transition
  ``t = 0..k-1``: the index of the action the actor plays at tick ``t``, numbered as in
  :class:`~wavefront.model.compile.ActorSpec` (index 0 is ``idle`` or ``none``), so a
  decoded joint move can be replayed with :meth:`CompiledModel.step`.
- ``assume[name]``: a ``Bool`` per name in :meth:`CompiledModel.assumptions` (one per
  part for a guard declared as named parts). When it is false the assumption is relaxed:
  a guard reads ``TRUE``, a guard part drops out of its conjunction, a fairness constraint no
  longer restricts its actor, a profile is not applied, an ``assume`` no longer filters
  the initial states. The encoding itself leaves these Bools free; queries assert or
  assume them.
- ``active[t]``: a ``Bool`` per tick, true on a prefix of the ticks (``active[0]`` is
  true). Transition ``t -> t + 1`` is only enforced when ``active[t + 1]`` holds, so a
  path may stop anywhere; queries ask for a target at an active tick. Without this, a
  state with no available move (which the explicit engine reports as a ``ModelError``)
  after the target would make the whole query unsatisfiable.

Transitions (non-terminal ``t``, in the order of ``_successor``)
-----------------------------------------------------------------
1. availability: ``chosen == j -> available_j(t)`` with the action's guard
   (``assume_<actor>.<action> -> guard``, or for a parted guard
   ``assume_<actor>.<action>:<part> -> part`` for each part), its delay counter at 0, the
   selected profiles
   (``assume_<profile> -> unless``) and the fairness restrictions
   (``assume_<f> -> (fair_<f> < within or j in responses)``);
2. immediate effects of the chosen non-delayed actions, evaluated on the pre-state:
   ``Set`` values win, summed ``Bump`` amounts are added, the result is clamped;
3. tick increment;
4. delay counters (``d`` when chosen, then decremented) and the delayed effects of the
   counters going from 1 to 0, evaluated on the pre-state and composed as a second phase
   (delayed ``Set`` overrides, delayed ``Bump`` adds, then clamping);
5. ``last_<actor>``;
6. latches, in declaration order, on the state built so far;
7. fairness counters, in declaration order, on the state built so far.

Transitions the explicit engine rejects with :class:`~wavefront.model.ModelError`
(two different ``Set`` values on one variable in one phase, a strict ``Bump`` taking a
variable out of range, a monotone variable decreasing) are excluded by constraints. A
state with no available action for some actor simply has no successor.

Terminal states (an ending holds, or ``tick == horizon`` in a timed model) are frozen:
``terminal(t) -> state(t + 1) == state(t)``, with every ``chosen`` fixed to 0 so that
equal traces have one representation.

Initial states are the product of the declared initial values, with latches set where
their condition already holds, and ``assume_<name> -> expr(0)`` for every unrelaxed
``assume`` restriction.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import z3

from ..model.compile import CompiledModel, is_condition
from ..model.effects import Bump, SetIf
from ..model.expr import (
    And,
    Arith,
    Cmp,
    Const,
    EndingRef,
    Expr,
    InSet,
    InvariantRef,
    Ite,
    Lit,
    Max,
    Min,
    Not,
    Or,
    VarRef,
)
from ..model.model import ModelError

__all__ = ["Encoding", "encode", "Target"]

Target = Expr | str
Env = Sequence[Any]  # one z3 Int expression per state variable

_BOOL_NODES = (Const, Cmp, And, Or, Not, InSet, InvariantRef, EndingRef)


# -- expressions ---------------------------------------------------------------------------


class _Translator:
    """Translate expression trees to Z3 over an environment (one Int per variable).

    Level names are resolved exactly as in the Python code generator of
    :mod:`wavefront.model.compile` (whose helpers it reuses), so a translated expression
    and the compiled Python function agree on every state.
    """

    def __init__(self, cm: CompiledModel) -> None:
        self.cm = cm
        self.gen = cm._gen  # level resolution and literal contexts, shared with compile
        self.variables = cm.variables

    def boolean(self, node: Expr, env: Env) -> z3.BoolRef:
        return node.accept(_BoolVisitor(self, env))

    def value(self, node: Expr, env: Env, ctx: int | None) -> z3.ArithRef:
        return node.accept(_ValueVisitor(self, env, ctx))

    def var(self, name: str) -> int:
        return self.gen.var_index(name, "bmc")

    def named(self, node: InvariantRef | EndingRef) -> Expr:
        table = (
            self.cm.model.invariants if isinstance(node, InvariantRef) else self.cm.model.endings
        )
        if node.name not in table:
            raise ModelError(f"unknown invariant or ending {node.name!r}")
        return table[node.name]


class _BoolVisitor:
    """Boolean nodes (``visit_<Class>``) to ``z3.BoolRef``."""

    def __init__(self, tr: _Translator, env: Env) -> None:
        self.tr = tr
        self.env = env

    def _value(self, node: Expr, ctx: int | None) -> z3.ArithRef:
        return self.tr.value(node, self.env, ctx)

    def visit_Const(self, node: Const) -> z3.BoolRef:
        return z3.BoolVal(bool(node.value))

    def visit_VarRef(self, node: VarRef) -> z3.BoolRef:
        i = self.tr.var(node.name)
        if self.tr.variables[i].kind != "flag":
            raise ModelError(f"variable {node.name!r} is used as a condition")
        return self.env[i] == 1

    def visit_Cmp(self, node: Cmp) -> z3.BoolRef:
        gen = self.tr.gen
        ctx = gen.ctx(node.left, "bmc")
        if ctx is None:
            ctx = gen.ctx(node.right, "bmc")
        left = self._value(node.left, ctx)
        right = self._value(node.right, ctx)
        return {
            "==": lambda: left == right,
            "!=": lambda: left != right,
            "<": lambda: left < right,
            "<=": lambda: left <= right,
            ">": lambda: left > right,
            ">=": lambda: left >= right,
        }[node.op]()

    def visit_And(self, node: And) -> z3.BoolRef:
        return z3.And(*(i.accept(self) for i in node.items))

    def visit_Or(self, node: Or) -> z3.BoolRef:
        return z3.Or(*(i.accept(self) for i in node.items))

    def visit_Not(self, node: Not) -> z3.BoolRef:
        return z3.Not(node.item.accept(self))

    def visit_InSet(self, node: InSet) -> z3.BoolRef:
        i = self.tr.var(node.var.name)
        values = sorted({self.tr.gen.resolve(v, i, "bmc") for v in node.values})
        return z3.Or(*(self.env[i] == v for v in values)) if values else z3.BoolVal(False)

    def visit_Ite(self, node: Ite) -> z3.BoolRef:
        return z3.If(node.cond.accept(self), node.then.accept(self), node.orelse.accept(self))

    def visit_InvariantRef(self, node: InvariantRef) -> z3.BoolRef:
        return self.tr.named(node).accept(self)

    def visit_EndingRef(self, node: EndingRef) -> z3.BoolRef:
        return self.tr.named(node).accept(self)

    def visit_Lit(self, node: Lit) -> z3.BoolRef:
        raise ModelError(f"{node!r} is not a condition")

    visit_Arith = visit_Min = visit_Max = visit_Lit


class _ValueVisitor:
    """Integer-valued nodes to ``z3.ArithRef``; ``ctx`` is the variable whose levels name
    literals (as in ``_CodeGen.value``)."""

    def __init__(self, tr: _Translator, env: Env, ctx: int | None) -> None:
        self.tr = tr
        self.env = env
        self.ctx = ctx

    def _inner(self, node: Expr) -> _ValueVisitor:
        ctx = self.ctx if self.ctx is not None else self.tr.gen.ctx(node, "bmc")
        return self if ctx == self.ctx else _ValueVisitor(self.tr, self.env, ctx)

    def visit_Lit(self, node: Lit) -> z3.ArithRef:
        return z3.IntVal(self.tr.gen.resolve(node.value, self.ctx, "bmc"))

    def visit_VarRef(self, node: VarRef) -> z3.ArithRef:
        return self.env[self.tr.var(node.name)]

    def visit_Arith(self, node: Arith) -> z3.ArithRef:
        inner = self._inner(node)
        left, right = node.left.accept(inner), node.right.accept(inner)
        return left + right if node.op == "+" else left - right

    def visit_Min(self, node: Min) -> z3.ArithRef:
        inner = self._inner(node)
        args = [a.accept(inner) for a in node.args]
        out = args[0]
        for a in args[1:]:
            out = z3.If(a < out, a, out)
        return out

    def visit_Max(self, node: Max) -> z3.ArithRef:
        inner = self._inner(node)
        args = [a.accept(inner) for a in node.args]
        out = args[0]
        for a in args[1:]:
            out = z3.If(a > out, a, out)
        return out

    def visit_Ite(self, node: Ite) -> z3.ArithRef:
        inner = self._inner(node)
        cond = self.tr.boolean(node.cond, self.env)
        return z3.If(cond, node.then.accept(inner), node.orelse.accept(inner))

    def _bool(self, node: Expr) -> z3.ArithRef:
        return z3.If(self.tr.boolean(node, self.env), 1, 0)

    visit_Const = visit_Cmp = visit_And = visit_Or = visit_Not = _bool
    visit_InSet = visit_InvariantRef = visit_EndingRef = _bool


# -- effects -------------------------------------------------------------------------------


@dataclass(frozen=True)
class _SetItem:
    var: int
    cond: Expr | None  # SetIf condition, on the pre-state
    value: int | Expr  # a resolved constant, or an expression clamped to the range


@dataclass(frozen=True)
class _BumpItem:
    var: int
    amount: int
    strict: bool


def _effect_items(cm: CompiledModel, effects: Sequence[Any]) -> list[_SetItem | _BumpItem]:
    """An action's effect list with targets and literal values resolved."""
    out: list[_SetItem | _BumpItem] = []
    for eff in effects:
        i = cm.index[eff.var]
        if isinstance(eff, Bump):
            out.append(_BumpItem(i, eff.amount, eff.strict))
            continue
        cond = eff.cond if isinstance(eff, SetIf) else None
        value = eff.value
        if not isinstance(value, Expr):
            value = cm._gen.resolve(value, i, "bmc")
        out.append(_SetItem(i, cond, value))
    return out


# -- the encoding --------------------------------------------------------------------------


@dataclass(eq=False)
class Encoding:
    """The unrolled model. ``constraints`` hold the initial-state, domain and transition
    constraints; :meth:`solver` returns a solver with all of them asserted."""

    cm: CompiledModel
    k: int
    state: list[list[z3.ArithRef]]
    chosen: list[list[z3.ArithRef]]
    assume: dict[str, z3.BoolRef]
    active: list[z3.BoolRef]
    terminal: list[z3.BoolRef] = field(default_factory=list)
    constraints: list[z3.BoolRef] = field(default_factory=list)

    @property
    def names(self) -> list[str]:
        """Assumption names, in :meth:`CompiledModel.assumptions` order."""
        return list(self.assume)

    def expr(self, expr: Expr, t: int) -> z3.ExprRef:
        """``expr`` at tick ``t``: a Bool for conditions (a bare flag included), an Int for
        values."""
        if is_condition(expr) or self._is_flag(expr):
            return self.condition(expr, t)
        return _Translator(self.cm).value(expr, self.state[t], None)

    def condition(self, expr: Expr, t: int) -> z3.BoolRef:
        """``expr`` at tick ``t`` read as a condition. Anything the compiler accepts as a
        condition (comparisons, connectives, a flag used directly, ``Ite`` with condition
        branches, named invariants and endings) is translated as such; a value expression
        is true when non-zero, as Python reads the compiled function's result."""
        tr = _Translator(self.cm)
        try:
            return tr.boolean(expr, self.state[t])
        except ModelError:
            if is_condition(expr):
                raise
            return tr.value(expr, self.state[t], None) != 0

    def _is_flag(self, expr: Expr) -> bool:
        if not isinstance(expr, VarRef) or expr.name not in self.cm.index:
            return False
        return self.cm.variables[self.cm.index[expr.name]].kind == "flag"

    def target(self, target: Target, t: int) -> z3.BoolRef:
        """The target predicate at tick ``t``: an ending name (``"HORIZON"`` means terminal
        by tick with no ending), an invariant name, or a condition expression."""
        cm = self.cm
        if isinstance(target, str):
            if target == "HORIZON" and "HORIZON" not in cm.model.endings:
                if not cm.timed:
                    return z3.BoolVal(False)
                tick = self.state[t][cm.index["tick"]]
                endings = [self.condition(e, t) for e in cm.model.endings.values()]
                if not endings:
                    return tick >= cm.horizon
                return z3.And(tick >= cm.horizon, z3.Not(z3.Or(*endings)))
            if target in cm.model.endings:
                return self.condition(cm.model.endings[target], t)
            if target in cm.model.invariants:
                return self.condition(cm.model.invariants[target], t)
            raise ModelError(f"no ending or invariant named {target!r}")
        if not isinstance(target, Expr):
            raise ModelError(f"target {target!r} is not an expression or a name")
        cm.compile_expr(target)  # report level-name errors like the explicit engine
        return self.condition(target, t)

    def solver(self) -> z3.Solver:
        """A fresh solver with every constraint of the encoding asserted."""
        s = z3.Solver()
        s.add(*self.constraints)
        return s

    def decode(self, model: z3.ModelRef, length: int) -> tuple[list[tuple], list[tuple]]:
        """States ``0..length`` and the ``length`` joint moves between them."""

        def val(x: z3.ArithRef) -> int:
            return model.eval(x, model_completion=True).as_long()

        states = [tuple(val(x) for x in self.state[t]) for t in range(length + 1)]
        moves = [tuple(val(x) for x in self.chosen[t]) for t in range(length)]
        return states, moves


class _Builder:
    """Builds an :class:`Encoding`; one method per part of ``_successor``."""

    def __init__(self, cm: CompiledModel, k: int) -> None:
        if isinstance(k, bool) or not isinstance(k, int) or k < 0:
            raise ValueError(f"k must be an int >= 0, not {k!r}")
        self.cm = cm
        self.k = k
        self.tr = _Translator(cm)
        self.hi = [v.size - 1 for v in cm.variables]
        self.tick = cm.index.get("tick")
        self.out: list[z3.BoolRef] = []
        state = [[z3.Int(f"{v.name}@{t}") for v in cm.variables] for t in range(k + 1)]
        chosen = [[z3.Int(f"chosen_{a.name}@{t}") for a in cm.actors] for t in range(k)]
        assume = {name: z3.Bool(f"assume_{name}") for name in cm.assumptions()}
        active = [z3.BoolVal(True)] + [z3.Bool(f"active@{t}") for t in range(1, k + 1)]
        self.enc = Encoding(cm, k, state, chosen, assume, active)
        self._prepare()

    # -- static tables -------------------------------------------------------------------
    def _prepare(self) -> None:
        cm = self.cm
        m = cm.model
        self.immediate: list[tuple[int, int, list[_SetItem | _BumpItem]]] = []
        self.delayed: list[tuple[int, int, int, int, list[_SetItem | _BumpItem]]] = []
        for actor in cm.actors:
            for action in actor.actions:
                items = _effect_items(cm, action.effects)
                if action.delay:
                    assert action.pending is not None
                    self.delayed.append(
                        (actor.index, action.index, action.pending, action.delay, items)
                    )
                elif items:
                    self.immediate.append((actor.index, action.index, items))
        self.latches = [(cm.index[d.name], cm.index[d.of], d.when) for d in m.latches]
        self.fair = []
        for f in cm.fairness_constraints:
            actor = next(a for a in cm.actors if a.name == f.actor)
            responses = frozenset(actor.action_index(r) for r in f.responses)
            self.fair.append((cm.index[f"fair_{f.name}"], actor.index, responses, f))
        self.lasts = [(a.index, a.last) for a in cm.actors if a.last is not None]
        self.monotone = [i for i, v in enumerate(cm.variables) if v.monotone]

    # -- top level -----------------------------------------------------------------------
    def build(self) -> Encoding:
        enc = self.enc
        self._domains()
        self._initial()
        for t in range(self.k + 1):
            enc.terminal.append(self._terminal(enc.state[t]))
        for t in range(self.k):
            self.out.append(z3.Implies(enc.active[t + 1], enc.active[t]))
            self.out.append(z3.Implies(enc.active[t + 1], self._transition(t)))
        enc.constraints = self.out
        return enc

    def _domains(self) -> None:
        enc = self.enc
        for row in enc.state:
            for x, hi in zip(row, self.hi, strict=True):
                self.out.append(z3.And(x >= 0, x <= hi))
        for row in enc.chosen:
            for x, actor in zip(row, self.cm.actors, strict=True):
                self.out.append(z3.And(x >= 0, x < len(actor.actions)))

    def _initial(self) -> None:
        cm = self.cm
        s0 = self.enc.state[0]
        latch_idx = {idx for idx, _, _ in self.latches}
        for i, v in enumerate(cm.variables):
            if i in latch_idx:
                continue
            if len(v.init) < v.size:
                self.out.append(z3.Or(*(s0[i] == x for x in v.init)))
        env: list[Any] = list(s0)
        for idx in latch_idx:
            env[idx] = z3.IntVal(0)
        for idx, src, when in self.latches:  # sequential, as in initial_states()
            env[idx] = z3.If(self.tr.boolean(when, env), env[src] + 1, 0)
        for idx in latch_idx:
            self.out.append(s0[idx] == env[idx])
        for name, expr in cm.model.assumes.items():
            if name not in cm.relax:
                self.out.append(z3.Implies(self.enc.assume[name], self.tr.boolean(expr, s0)))

    def _terminal(self, s: Env) -> z3.BoolRef:
        parts = [self.tr.boolean(e, s) for e in self.cm.model.endings.values()]
        if self.tick is not None:
            parts.append(s[self.tick] >= self.cm.horizon)
        return z3.Or(*parts) if parts else z3.BoolVal(False)

    def _transition(self, t: int) -> z3.BoolRef:
        enc = self.enc
        s, n, ch = enc.state[t], enc.state[t + 1], enc.chosen[t]
        env: list[Any] = list(s)
        side: list[z3.BoolRef] = []  # conditions the explicit engine would raise on
        self._availability(s, ch, side)
        self._immediate_effects(env, s, ch, side)
        self._tick_increment(env, s)
        self._delays(env, s, ch, side)
        self._last_actions(env, ch)
        self._latches(env)
        self._fairness(env, s, ch)
        self._monotone_check(env, s, side)
        step = z3.And(*side, *(x == e for x, e in zip(n, env, strict=True)))
        frozen = z3.And(*(x == y for x, y in zip(n, s, strict=True)), *(c == 0 for c in ch))
        return z3.If(enc.terminal[t], frozen, step)

    # -- availability --------------------------------------------------------------------
    def _availability(self, s: Env, ch: Sequence[Any], side: list[z3.BoolRef]) -> None:
        cm = self.cm
        enc = self.enc
        for actor in cm.actors:
            forbids: dict[int, list[z3.BoolRef]] = {}
            for p in cm.model.profiles:
                if p.name in cm.profiles and p.actor == actor.name:
                    unless = z3.Or(z3.Not(enc.assume[p.name]), self.tr.boolean(p.unless, s))
                    for name in p.forbid:
                        forbids.setdefault(actor.action_index(name), []).append(unless)
            for action in actor.actions:
                conds: list[z3.BoolRef] = []
                if action.guard_parts:
                    guards = [
                        (f"{actor.name}.{action.name}:{part}", g) for part, g in action.guard_parts
                    ]
                else:
                    guards = [(f"{actor.name}.{action.name}", action.guard_expr)]
                for name, g in guards:
                    if not (isinstance(g, Const) and g.value):
                        a = enc.assume[name]
                        conds.append(z3.Or(z3.Not(a), self.tr.boolean(g, s)))
                if action.pending is not None:
                    conds.append(s[action.pending] == 0)
                conds.extend(forbids.get(action.index, []))
                for idx, actor_i, responses, f in self.fair:
                    if actor_i == actor.index and action.index not in responses:
                        conds.append(z3.Not(z3.And(enc.assume[f.name], s[idx] >= f.within)))
                if conds:
                    side.append(z3.Implies(ch[actor.index] == action.index, z3.And(*conds)))

    # -- effects -------------------------------------------------------------------------
    def _compose(
        self,
        env: list[Any],
        s: Env,
        contributions: list[tuple[z3.BoolRef, list[_SetItem | _BumpItem]]],
        side: list[z3.BoolRef],
    ) -> None:
        """``_compose``: per variable, Sets win, then summed Bumps, then clamping.

        ``contributions`` pairs each effect list with the condition under which it
        applies; values and ``SetIf`` conditions are evaluated on the pre-state ``s``.
        Conflicting Sets and strict Bumps out of range are excluded (``side``).
        """
        sets: dict[int, list[tuple[z3.BoolRef, Any]]] = {}
        bumps: dict[int, list[tuple[z3.BoolRef, int, bool]]] = {}
        for when, items in contributions:
            for item in items:
                if isinstance(item, _BumpItem):
                    bumps.setdefault(item.var, []).append((when, item.amount, item.strict))
                    continue
                cond = when
                if item.cond is not None:
                    cond = z3.And(when, self.tr.boolean(item.cond, s))
                if isinstance(item.value, Expr):
                    raw = self.tr.value(item.value, s, item.var)
                    value = z3.If(
                        raw < 0, 0, z3.If(raw > self.hi[item.var], self.hi[item.var], raw)
                    )
                else:
                    value = z3.IntVal(item.value)
                sets.setdefault(item.var, []).append((cond, value))
        for v in sorted(set(sets) | set(bumps)):
            x = env[v]
            if v in sets:
                chain = env[v]
                for cond, value in reversed(sets[v]):
                    chain = z3.If(cond, value, chain)
                side.extend(z3.Implies(cond, value == chain) for cond, value in sets[v])
                x = chain
            if v in bumps:
                x = x + z3.Sum(*(z3.If(c, amt, 0) for c, amt, _ in bumps[v]))
                strict = [c for c, _, is_strict in bumps[v] if is_strict]
                if strict:
                    side.append(z3.Implies(z3.Or(*strict), z3.And(x >= 0, x <= self.hi[v])))
                x = z3.If(x < 0, 0, z3.If(x > self.hi[v], self.hi[v], x))
            env[v] = x

    def _immediate_effects(
        self, env: list[Any], s: Env, ch: Sequence[Any], side: list[z3.BoolRef]
    ) -> None:
        contributions = [(ch[a] == j, items) for a, j, items in self.immediate]
        if contributions:
            self._compose(env, s, contributions, side)

    def _tick_increment(self, env: list[Any], s: Env) -> None:
        if self.tick is not None:
            env[self.tick] = s[self.tick] + 1

    def _delays(self, env: list[Any], s: Env, ch: Sequence[Any], side: list[z3.BoolRef]) -> None:
        fired = []
        for actor_i, action_j, idx, d, items in self.delayed:
            c = s[idx]
            env[idx] = z3.If(c > 0, c - 1, z3.If(ch[actor_i] == action_j, d, c))
            if items:
                fired.append((c == 1, items))
        if fired:
            self._compose(env, s, fired, side)

    def _last_actions(self, env: list[Any], ch: Sequence[Any]) -> None:
        for actor_i, idx in self.lasts:
            env[idx] = ch[actor_i] + 1

    def _latches(self, env: list[Any]) -> None:
        for idx, src, when in self.latches:
            fire = z3.And(env[idx] == 0, self.tr.boolean(when, env))
            env[idx] = z3.If(fire, env[src] + 1, env[idx])

    def _fairness(self, env: list[Any], s: Env, ch: Sequence[Any]) -> None:
        for idx, actor_i, responses, f in self.fair:
            responded = z3.Or(*(ch[actor_i] == j for j in sorted(responses)))
            count = z3.If(s[idx] + 1 > f.within, f.within, s[idx] + 1)
            unanswered = z3.And(z3.Not(responded), self.tr.boolean(f.trigger, env))
            env[idx] = z3.If(unanswered, count, 0)

    def _monotone_check(self, env: list[Any], s: Env, side: list[z3.BoolRef]) -> None:
        for i in self.monotone:
            side.append(env[i] >= s[i])


def encode(cm: CompiledModel, k: int) -> Encoding:
    """Unroll ``cm`` to ``k`` transitions (ticks ``0..k``); see the module docstring."""
    return _Builder(cm, k).build()
