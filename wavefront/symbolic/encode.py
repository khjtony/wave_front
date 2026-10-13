"""Binary encoding of a :class:`~wavefront.model.compile.CompiledModel` as BDDs.

The encoding has the structure of the Z3 encoding of :mod:`wavefront.bmc.encode` (spec
section 6) for one transition, with Boolean variables in place of integers, and mirrors
:meth:`CompiledModel._successor` step by step.

Variables and order
-------------------
- Each state variable of size ``n`` gets ``ceil(log2 n)`` *current* bits and as many *next*
  bits (most significant bit first), with the domain constraint ``value < n``. Current and
  next bits of a variable are interleaved (``x1 x1' x0 x0'``), so renaming between them
  keeps the order.
- Each actor (Nature included) gets ``ceil(log2 k)`` *action* bits for its ``k`` actions,
  numbered as in :class:`~wavefront.model.compile.ActorSpec` (index 0 is ``idle`` or
  ``none``); codes ``>= k`` are never available.
- The order is the state order of the compiled model (or ``var_order``), with the action
  bits of all actors on top by default (``actions="top"``), at the bottom
  (``actions="bottom"``), or each actor's block placed after a named state variable
  (``actions={"WEST": "commit_WEST", ...}``; unnamed actors go on top).

Integer expressions
-------------------
An integer-valued expression is a *value partition*: a ``dict`` mapping each value it can
take to the BDD of the condition under which it takes it (conditions disjoint, covering
the domain). Arithmetic (``+``, ``-``, ``Min``, ``Max``, ``Ite``), clamping and
comparisons combine partitions value by value; the values are small (level indices,
counters, sums of indicator terms), so this is the bit-level circuit written as a case
split, and a comparison against a constant is a disjunction of the variable's value cubes.

Transition
----------
For every current state bit the *next-state function* ``f(s, a)`` over current and action
bits is built in the order of ``_successor``: immediate effects of the chosen non-delayed
actions (``Set`` values win, ``Bump`` amounts summed, then clamped), tick increment, delay
counters with the delayed effects of the counters going from 1 to 0 composed as a second
phase, ``last_<actor>``, latches on the state built so far, fairness counters on the state
built so far with the chosen action. Transitions on which the explicit engine raises
(conflicting ``Set`` values in one phase, a strict ``Bump`` out of range, a monotone
variable decreasing) are collected in :attr:`Encoding.error`; the fixpoints do not use it
and :func:`wavefront.symbolic.solve.reachable` raises :class:`ModelError` when a reachable
state has such a move, as ``explore`` does.

Availability per actor (:attr:`Encoding.avail`): the action's guard (``guard_expr``: the
conjunction of a parted guard's unrelaxed parts), its delay counter at 0, the selected
profiles' ``unless`` conditions, and the fairness restrictions (an actor whose counter has
reached ``within`` may only play its responses). ``live`` holds where every actor has an
available action, and ``active`` is ``dom & ~term & live``. Terminal states (an ending holds, or ``tick == horizon``) have no moves;
their image is themselves (they are frozen).

The per-variable transition relation parts ``x' <-> f(s, a)`` (:meth:`Encoding.trans_parts`)
are used for forward images; backward steps substitute the next-state functions into the
target set (:meth:`Encoding.preimage`).
"""

from __future__ import annotations

import operator
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

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
from .bdd import BDD, FALSE, TRUE

__all__ = ["Encoding", "encode", "Partition"]

Partition = dict[int, int]  # value -> BDD edge of the condition

_CMP: dict[str, Callable[[int, int], bool]] = {
    "==": operator.eq,
    "!=": operator.ne,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
}

_BOOL_NODES = (Const, Cmp, And, Or, Not, InSet, InvariantRef, EndingRef)


def _bits(n: int) -> int:
    """Bits needed for ``n`` values."""
    return max(0, (n - 1).bit_length())


class _Parts:
    """Value-partition arithmetic over one manager."""

    def __init__(self, mgr: BDD) -> None:
        self.mgr = mgr

    def const(self, v: int) -> Partition:
        return {v: TRUE}

    def add_into(self, out: Partition, v: int, c: int) -> None:
        if c != FALSE:
            old = out.get(v)
            out[v] = c if old is None else self.mgr.OR(old, c)

    def combine(self, a: Partition, b: Partition, fn: Callable[[int, int], int]) -> Partition:
        out: Partition = {}
        AND = self.mgr.AND
        for x, cx in a.items():
            for y, cy in b.items():
                self.add_into(out, fn(x, y), AND(cx, cy))
        return out

    def map(self, a: Partition, fn: Callable[[int], int]) -> Partition:
        out: Partition = {}
        for x, cx in a.items():
            self.add_into(out, fn(x), cx)
        return out

    def ite(self, c: int, a: Partition, b: Partition) -> Partition:
        if c == TRUE:
            return a
        if c == FALSE:
            return b
        AND = self.mgr.AND
        out: Partition = {}
        for x, cx in a.items():
            self.add_into(out, x, AND(c, cx))
        for x, cx in b.items():
            self.add_into(out, x, AND(c ^ 1, cx))
        return out

    def compare(self, a: Partition, b: Partition, op: str) -> int:
        fn = _CMP[op]
        mgr = self.mgr
        if len(b) == 1:
            ((y, cy),) = b.items()
            if cy == TRUE:
                return mgr.or_all(cx for x, cx in a.items() if fn(x, y))
        if len(a) == 1:
            ((x, cx),) = a.items()
            if cx == TRUE:
                return mgr.or_all(cy for y, cy in b.items() if fn(x, y))
        terms = []
        for x, cx in a.items():
            ys = [cy for y, cy in b.items() if fn(x, y)]
            if ys:
                terms.append(mgr.AND(cx, mgr.or_all(ys)))
        return mgr.or_all(terms)

    def clamp(self, a: Partition, hi: int) -> Partition:
        return self.map(a, lambda x: 0 if x < 0 else hi if x > hi else x)


class Encoding:
    """The BDD encoding of a compiled model (see the module docstring).

    Main attributes: ``mgr`` (the :class:`~wavefront.symbolic.bdd.BDD` manager), ``cur`` and
    ``nxt`` (per state variable, its current and next bit levels), ``act`` (per actor, its
    action bit levels), ``dom``, ``term``, ``live``, ``avail`` (per actor), ``action_avail``
    (per actor, per action: the state condition), ``next_fn`` (current bit level -> next-state
    function, identity bits omitted), ``error`` and ``initial``.
    """

    def __init__(
        self,
        cm: CompiledModel,
        mgr: BDD | None = None,
        var_order: Sequence[str] | None = None,
        actions: str | Mapping[str, str] = "top",
    ) -> None:
        self.cm = cm
        self.mgr = mgr if mgr is not None else BDD()
        self.P = _Parts(self.mgr)
        self._gen = cm._gen
        self._named_cache: dict[tuple[str, str], int] = {}
        self._layout(var_order, actions)
        self.state_vs = self.mgr.varset(self.state_levels)
        self.next_vs = self.mgr.varset(self.next_levels)
        self.action_vs = self.mgr.varset(self.action_levels)
        self.actor_vs = [self.mgr.varset(levels) for levels in self.act]
        self.cur_to_next = {
            c: n for i in range(len(cm.variables)) for c, n in zip(self.cur[i], self.nxt[i])
        }
        self.next_to_cur = {n: c for c, n in self.cur_to_next.items()}
        self.cur_env: list[Partition] = [self.var_partition(i) for i in range(len(cm.variables))]
        self._build_static()
        self._build_availability()
        self._build_transition()
        self._trans_parts: list[tuple[int, frozenset[int]]] | None = None
        self.mgr.register(self)

    # -- layout --------------------------------------------------------------------------
    def _layout(self, var_order: Sequence[str] | None, actions: str | Mapping[str, str]) -> None:
        cm, mgr = self.cm, self.mgr
        names = [v.name for v in cm.variables]
        if var_order is None:
            order = list(range(len(names)))
        else:
            order = [cm.index[n] for n in var_order]
            rest = [i for i in range(len(names)) if i not in set(order)]
            order += rest
            if sorted(order) != list(range(len(names))):
                raise ModelError("var_order names a variable twice")
        placement: dict[int, list[int]] = {}  # state index -> actors placed after it
        top: list[int] = []
        bottom: list[int] = []
        if actions == "top":
            top = [a.index for a in cm.actors]
        elif actions == "bottom":
            bottom = [a.index for a in cm.actors]
        elif isinstance(actions, Mapping):
            for a in cm.actors:
                where = actions.get(a.name)
                if where is None:
                    top.append(a.index)
                else:
                    placement.setdefault(cm.index[where], []).append(a.index)
        else:
            raise ValueError(f"actions must be 'top', 'bottom' or a mapping, not {actions!r}")
        self.cur: list[list[int]] = [[] for _ in names]
        self.nxt: list[list[int]] = [[] for _ in names]
        self.act: list[list[int]] = [[] for _ in cm.actors]

        def place_actor(a: int) -> None:
            actor = cm.actors[a]
            for b in range(_bits(len(actor.actions))):
                self.act[a].append(mgr.add_var(f"{actor.name}.a{b}"))

        for a in top:
            place_actor(a)
        for i in order:
            spec = cm.variables[i]
            for b in range(_bits(spec.size)):
                self.cur[i].append(mgr.add_var(f"{spec.name}.{b}"))
                self.nxt[i].append(mgr.add_var(f"{spec.name}.{b}'"))
            for a in placement.get(i, ()):
                place_actor(a)
        for a in bottom:
            place_actor(a)
        self.var_order = [names[i] for i in order]
        self.state_levels = sorted(v for bits in self.cur for v in bits)
        self.next_levels = sorted(v for bits in self.nxt for v in bits)
        self.action_levels = sorted(v for bits in self.act for v in bits)

    # -- cubes and partitions ------------------------------------------------------------
    def value_cube(self, levels: Sequence[int], value: int) -> int:
        """The cube ``bits(levels) == value`` (most significant bit first)."""
        k = len(levels)
        return self.mgr.cube({lv: (value >> (k - 1 - b)) & 1 for b, lv in enumerate(levels)})

    def var_partition(self, i: int, levels: Sequence[int] | None = None) -> Partition:
        """The value partition of state variable ``i`` (current bits by default)."""
        bits = self.cur[i] if levels is None else levels
        return {v: self.value_cube(bits, v) for v in range(self.cm.variables[i].size)}

    def chosen(self, actor: int, j: int) -> int:
        """Actor ``actor`` (index) plays action ``j``."""
        return self.value_cube(self.act[actor], j)

    def state_cube(self, state: Sequence[int]) -> int:
        """The cube of one state (current bits)."""
        return self.mgr.cube(self.state_assignment(state))

    state_to_cube = state_cube

    def state_assignment(self, state: Sequence[int]) -> dict[int, int]:
        """``{current bit level: bit}`` for a state tuple."""
        out: dict[int, int] = {}
        for i, x in enumerate(state):
            bits = self.cur[i]
            k = len(bits)
            for b, lv in enumerate(bits):
                out[lv] = (x >> (k - 1 - b)) & 1
        return out

    def _state_array(self, state: Sequence[int]) -> list[int]:
        arr = [0] * self.mgr.num_vars
        for i, x in enumerate(state):
            bits = self.cur[i]
            k = len(bits)
            for b, lv in enumerate(bits):
                arr[lv] = (x >> (k - 1 - b)) & 1
        return arr

    def cube_to_state(self, assignment: Mapping[int, int]) -> tuple[int, ...]:
        """The state tuple of an assignment ``{level: bit}`` (missing bits read as 0)."""
        out = []
        for bits in self.cur:
            x = 0
            for lv in bits:
                x = (x << 1) | (1 if assignment.get(lv, 0) else 0)
            out.append(x)
        return tuple(out)

    def decode_move(self, assignment: Mapping[int, int], actors: Iterable[int]) -> tuple[int, ...]:
        """Action indices of ``actors`` (indices) read from an assignment of action bits."""
        out = []
        for a in actors:
            x = 0
            for lv in self.act[a]:
                x = (x << 1) | (1 if assignment.get(lv, 0) else 0)
            out.append(x)
        return tuple(out)

    def move_cube(self, actors: Iterable[int], move: Sequence[int]) -> int:
        """The cube of action bits for ``actors`` playing ``move``."""
        out = TRUE
        for a, j in zip(actors, move, strict=True):
            out = self.mgr.AND(out, self.chosen(a, j))
        return out

    def holds(self, f: int, state: Sequence[int]) -> bool:
        """Does the state predicate ``f`` (over current bits) hold in ``state``?"""
        return self.mgr.evaluate(f, self._state_array(state))

    def states_bdd(self, states: Iterable[Sequence[int]]) -> int:
        """The set of the given state tuples."""
        return self.mgr.or_all(self.state_cube(s) for s in states)

    # -- expressions ---------------------------------------------------------------------
    def _var(self, name: str) -> int:
        return self._gen.var_index(name, "symbolic")

    def _named(self, node: InvariantRef | EndingRef) -> Expr:
        m = self.cm.model
        table = m.invariants if isinstance(node, InvariantRef) else m.endings
        if node.name not in table:
            raise ModelError(f"unknown invariant or ending {node.name!r}")
        return table[node.name]

    def boolean(self, node: Expr, env: Sequence[Partition] | None = None) -> int:
        """A condition as a BDD over the environment (current bits by default)."""
        env = self.cur_env if env is None else env
        mgr = self.mgr
        if isinstance(node, Const):
            return TRUE if node.value else FALSE
        if isinstance(node, VarRef):
            i = self._var(node.name)
            if self.cm.variables[i].kind != "flag":
                raise ModelError(f"variable {node.name!r} is used as a condition")
            return env[i].get(1, FALSE)
        if isinstance(node, Cmp):
            gen = self._gen
            ctx = gen.ctx(node.left, "symbolic")
            if ctx is None:
                ctx = gen.ctx(node.right, "symbolic")
            left = self.value(node.left, env, ctx)
            right = self.value(node.right, env, ctx)
            return self.P.compare(left, right, node.op)
        if isinstance(node, And):
            return mgr.and_all(self.boolean(i, env) for i in node.items)
        if isinstance(node, Or):
            return mgr.or_all(self.boolean(i, env) for i in node.items)
        if isinstance(node, Not):
            return self.boolean(node.item, env) ^ 1
        if isinstance(node, InSet):
            i = self._var(node.var.name)
            values = {self._gen.resolve(v, i, "symbolic") for v in node.values}
            return mgr.or_all(c for x, c in env[i].items() if x in values)
        if isinstance(node, Ite):
            return mgr.ITE(
                self.boolean(node.cond, env),
                self.boolean(node.then, env),
                self.boolean(node.orelse, env),
            )
        if isinstance(node, InvariantRef | EndingRef):
            if env is self.cur_env:
                key = (type(node).__name__, node.name)
                hit = self._named_cache.get(key)
                if hit is None:
                    hit = self._named_cache[key] = self.boolean(self._named(node), env)
                return hit
            return self.boolean(self._named(node), env)
        raise ModelError(f"{node!r} is not a condition")

    def value(self, node: Expr, env: Sequence[Partition] | None, ctx: int | None) -> Partition:
        """An integer expression as a value partition; ``ctx`` is the variable whose levels
        name literals (as in the compiler's code generator)."""
        env = self.cur_env if env is None else env
        P = self.P
        if isinstance(node, Lit):
            return P.const(self._gen.resolve(node.value, ctx, "symbolic"))
        if isinstance(node, VarRef):
            return env[self._var(node.name)]
        inner = ctx if ctx is not None else self._gen.ctx(node, "symbolic")
        if isinstance(node, Arith):
            left = self.value(node.left, env, inner)
            right = self.value(node.right, env, inner)
            return P.combine(left, right, operator.add if node.op == "+" else operator.sub)
        if isinstance(node, Min | Max):
            fn = min if isinstance(node, Min) else max
            out = self.value(node.args[0], env, inner)
            for a in node.args[1:]:
                out = P.combine(out, self.value(a, env, inner), fn)
            return out
        if isinstance(node, Ite):
            cond = self.boolean(node.cond, env)
            return P.ite(
                cond, self.value(node.then, env, inner), self.value(node.orelse, env, inner)
            )
        if isinstance(node, _BOOL_NODES):
            b = self.boolean(node, env)
            return {1: b, 0: b ^ 1} if b not in (TRUE, FALSE) else P.const(int(b == TRUE))
        raise ModelError(f"{node!r} is not a value")

    def condition(self, expr: Expr) -> int:
        """``expr`` read as a condition on the current state: conditions (and a flag used
        directly) as such, a value expression as true when non-zero (as the explicit engine
        reads the compiled function)."""
        self.cm.compile_expr(expr)  # report level-name errors like the explicit engine
        if is_condition(expr) or self._is_flag(expr):
            return self.boolean(expr)
        part = self.value(expr, None, None)
        return self.mgr.or_all(c for x, c in part.items() if x != 0)

    def _is_flag(self, expr: Expr) -> bool:
        if not isinstance(expr, VarRef) or expr.name not in self.cm.index:
            return False
        return self.cm.variables[self.cm.index[expr.name]].kind == "flag"

    def predicate(self, target: Expr | str) -> int:
        """A state predicate: an ending name (``"HORIZON"``: terminal by tick with no
        ending), an invariant name, or an expression (see :meth:`condition`). Restricted to
        the domain."""
        cm = self.cm
        if isinstance(target, str):
            if target == "HORIZON" and "HORIZON" not in cm.model.endings:
                if not cm.timed:
                    return FALSE
                f = self.mgr.DIFF(self.at_horizon, self.any_ending)
            elif target in cm.model.endings:
                f = self.boolean(cm.model.endings[target])
            elif target in cm.model.invariants:
                f = self.boolean(cm.model.invariants[target])
            else:
                raise ModelError(f"no ending or invariant named {target!r}")
        elif isinstance(target, Expr):
            f = self.condition(target)
        else:
            raise ModelError(f"target {target!r} is not an expression or a name")
        return self.mgr.AND(f, self.dom)

    # -- static predicates ---------------------------------------------------------------
    def _build_static(self) -> None:
        cm, mgr = self.cm, self.mgr
        self.dom = mgr.and_all(
            mgr.or_all(self.cur_env[i].values()) for i in range(len(cm.variables))
        )
        self.next_dom = mgr.rename(self.dom, self.cur_to_next)
        self.ending_bdds = {n: self.boolean(e) for n, e in cm.model.endings.items()}
        self.any_ending = mgr.or_all(self.ending_bdds.values())
        tick = cm.index.get("tick")
        if tick is not None:
            self.at_horizon = mgr.or_all(
                c for x, c in self.cur_env[tick].items() if x >= cm.horizon
            )
        else:
            self.at_horizon = FALSE
        self.term = mgr.AND(mgr.OR(self.any_ending, self.at_horizon), self.dom)
        overlap = FALSE
        names = list(self.ending_bdds)
        for k, a in enumerate(names):
            for b in names[k + 1 :]:
                overlap = mgr.OR(overlap, mgr.AND(self.ending_bdds[a], self.ending_bdds[b]))
        self.ending_overlap = mgr.AND(overlap, self.dom)
        self.initial = mgr.AND(self._initial(), self.dom)

    def _initial(self) -> int:
        cm, mgr, P = self.cm, self.mgr, self.P
        latch_idx = {cm.index[d.name] for d in cm.model.latches}
        f = TRUE
        for i, v in enumerate(cm.variables):
            if i not in latch_idx:
                f = mgr.AND(f, mgr.or_all(self.cur_env[i][x] for x in v.init))
        env = list(self.cur_env)
        for i in latch_idx:
            env[i] = P.const(0)
        for d in cm.model.latches:
            idx, src = cm.index[d.name], cm.index[d.of]
            fire = self.boolean(d.when, env)
            env[idx] = P.ite(fire, P.map(env[src], lambda x: x + 1), env[idx])
        for i in latch_idx:
            f = mgr.AND(f, P.compare(self.cur_env[i], env[i], "=="))
        for name in cm.assume_fns:
            f = mgr.AND(f, self.boolean(cm.model.assumes[name]))
        return f

    # -- availability --------------------------------------------------------------------
    def _build_availability(self) -> None:
        cm, mgr = self.cm, self.mgr
        self.avail: list[int] = []
        self.action_avail: list[list[int]] = []
        for actor in cm.actors:
            forbids: dict[int, list[int]] = {}
            for p in cm.model.profiles:
                if p.name in cm.profiles and p.actor == actor.name:
                    unless = self.boolean(p.unless)
                    for name in p.forbid:
                        forbids.setdefault(actor.action_index(name), []).append(unless)
            row = []
            for action in actor.actions:
                g = self.boolean(action.guard_expr)
                if action.pending is not None:
                    g = mgr.AND(g, self.cur_env[action.pending][0])
                for unless in forbids.get(action.index, ()):
                    g = mgr.AND(g, unless)
                for idx, within, responses, _ in actor.fairness:
                    if action.index not in responses:
                        bound = mgr.or_all(c for x, c in self.cur_env[idx].items() if x >= within)
                        g = mgr.DIFF(g, bound)
                row.append(g)
            self.action_avail.append(row)
            self.avail.append(
                mgr.or_all(mgr.AND(self.chosen(actor.index, j), g) for j, g in enumerate(row))
            )
        self.live = mgr.and_all(mgr.exists(av, vs) for av, vs in zip(self.avail, self.actor_vs))
        self.moves = mgr.and_all(self.avail)
        self.active = mgr.and_all([self.dom, self.term ^ 1, self.live])

    # -- transition ----------------------------------------------------------------------
    def _effect_items(self, effects: Sequence[Any]) -> list[tuple]:
        cm = self.cm
        out: list[tuple] = []
        for eff in effects:
            i = cm.index[eff.var]
            if isinstance(eff, Bump):
                out.append(("bump", i, eff.amount, eff.strict))
                continue
            cond = eff.cond if isinstance(eff, SetIf) else None
            value = eff.value
            if not isinstance(value, Expr):
                value = self._gen.resolve(value, i, "symbolic")
            out.append(("set", i, cond, value))
        return out

    def _compose(
        self, env: list[Partition], contributions: list[tuple[int, list[tuple]]]
    ) -> None:
        """Spec 3.4 for one phase: per variable, Sets win (first in order; two different
        values are an error), then summed Bumps, then clamping (strict: error)."""
        mgr, P = self.mgr, self.P
        hi = [v.size - 1 for v in self.cm.variables]
        sets: dict[int, list[tuple[int, Partition]]] = {}
        bumps: dict[int, list[tuple[int, int, bool]]] = {}
        for when, items in contributions:
            for item in items:
                if item[0] == "bump":
                    _, v, amount, strict = item
                    bumps.setdefault(v, []).append((when, amount, strict))
                    continue
                _, v, cond, value = item
                c = when if cond is None else mgr.AND(when, self.boolean(cond))
                if isinstance(value, Expr):
                    part = P.clamp(self.value(value, self.cur_env, v), hi[v])
                else:
                    part = P.const(value)
                sets.setdefault(v, []).append((c, part))
        for v in sorted(set(sets) | set(bumps)):
            x = env[v]
            if v in sets:
                items = sets[v]
                chain = x
                for c, part in reversed(items):
                    chain = P.ite(c, part, chain)
                for k, (ck, pk) in enumerate(items):
                    for cl, pl in items[k + 1 :]:
                        both = mgr.AND(ck, cl)
                        if both != FALSE:
                            differ = P.compare(pk, pl, "!=")
                            self.error = mgr.OR(self.error, mgr.AND(both, differ))
                x = chain
            if v in bumps:
                total = P.const(0)
                for c, amount, _ in bumps[v]:
                    total = P.ite(c, P.map(total, lambda d, a=amount: d + a), total)
                raw = P.combine(x, total, operator.add)
                strict = mgr.or_all(c for c, _, s in bumps[v] if s)
                if strict != FALSE:
                    out = mgr.or_all(c for val, c in raw.items() if val < 0 or val > hi[v])
                    self.error = mgr.OR(self.error, mgr.AND(strict, out))
                x = P.clamp(raw, hi[v])
            env[v] = x

    def _build_transition(self) -> None:
        cm, mgr, P = self.cm, self.mgr, self.P
        self.error = FALSE
        env = list(self.cur_env)
        immediate = []
        delayed = []
        for actor in cm.actors:
            for action in actor.actions:
                items = self._effect_items(action.effects)
                if action.delay:
                    delayed.append((actor.index, action.index, action.pending, action.delay, items))
                elif items:
                    immediate.append((self.chosen(actor.index, action.index), items))
        if immediate:
            self._compose(env, immediate)
        tick = cm.index.get("tick")
        if tick is not None:
            env[tick] = P.map(self.cur_env[tick], lambda x: min(x + 1, cm.horizon))
        fired = []
        for actor_i, action_j, idx, d, items in delayed:
            cur = self.cur_env[idx]
            ch = self.chosen(actor_i, action_j)
            new: Partition = {}
            for x, c in cur.items():
                if x > 0:
                    P.add_into(new, x - 1, c)
                else:
                    P.add_into(new, d, mgr.AND(c, ch))
                    P.add_into(new, 0, mgr.DIFF(c, ch))
            env[idx] = new
            if items:
                fired.append((cur[1], items))
        if fired:
            self._compose(env, fired)
        for actor in cm.actors:
            if actor.last is not None:
                part: Partition = {}
                valid = FALSE
                for j in range(len(actor.actions)):
                    c = self.chosen(actor.index, j)
                    valid = mgr.OR(valid, c)
                    P.add_into(part, j + 1, c)
                P.add_into(part, 0, valid ^ 1)
                env[actor.last] = part
        for d in cm.model.latches:
            idx, src = cm.index[d.name], cm.index[d.of]
            fire = mgr.AND(env[idx].get(0, FALSE), self.boolean(d.when, env))
            env[idx] = P.ite(fire, P.map(env[src], lambda x: x + 1), env[idx])
        for f in cm.fairness_constraints:
            actor = next(a for a in cm.actors if a.name == f.actor)
            idx = cm.index[f"fair_{f.name}"]
            responses = sorted(actor.action_index(r) for r in f.responses)
            responded = mgr.or_all(self.chosen(actor.index, j) for j in responses)
            unanswered = mgr.DIFF(self.boolean(f.trigger, env), responded)
            count = P.map(self.cur_env[idx], lambda x, w=f.within: min(x + 1, w))
            env[idx] = P.ite(unanswered, count, P.const(0))
        for i, v in enumerate(cm.variables):
            if v.monotone:
                self.error = mgr.OR(self.error, P.compare(env[i], self.cur_env[i], "<"))
        self.error = mgr.AND(self.error, self.dom)
        self.new_env = env
        self.next_fn: dict[int, int] = {}
        for i, part in enumerate(env):
            if part is self.cur_env[i]:
                continue
            bits = self.cur[i]
            k = len(bits)
            for b, lv in enumerate(bits):
                f = mgr.or_all(c for x, c in part.items() if (x >> (k - 1 - b)) & 1)
                if f != mgr.var(lv):
                    self.next_fn[lv] = f

    # -- transition use ------------------------------------------------------------------
    def preimage(self, x: int) -> int:
        """``x(f(s, a))``: the (state, joint action) pairs whose successor is in ``x`` (a
        predicate over current bits)."""
        return self.mgr.compose(x, self.next_fn)

    @property
    def changed_levels(self) -> frozenset[int]:
        """Current bit levels of the state variables whose value can change."""
        return frozenset(
            lv
            for bits in self.cur
            if any(c in self.next_fn for c in bits)
            for lv in bits
        )

    def trans_parts(self) -> list[tuple[int, frozenset[int]]]:
        """Per state variable whose value can change, ``(x' <-> f(s, a), support)``; the
        unchanged variables are omitted (their next bits equal their current bits)."""
        if self._trans_parts is None:
            mgr = self.mgr
            parts = []
            for i in range(len(self.cm.variables)):
                if not any(c in self.next_fn for c in self.cur[i]):
                    continue
                rel = TRUE
                for c, n in zip(self.cur[i], self.nxt[i], strict=True):
                    f = self.next_fn.get(c, mgr.var(c))
                    rel = mgr.AND(rel, mgr.XOR(mgr.var(n), f) ^ 1)
                parts.append((rel, frozenset(mgr.support(rel))))
            self._trans_parts = parts
        return self._trans_parts

    def image(self, s: int) -> int:
        """Successors of the states in ``s`` under available joint moves (terminal states
        are frozen: their image is themselves).

        A relational product over the partitioned transition relation and the actors'
        availability: parts are conjoined greedily, each time the part that lets the most
        action and current bits be quantified (action bits weigh more), and every bit is
        quantified as soon as no remaining part mentions it. Unchanged variables keep their
        current bits."""
        mgr = self.mgr
        acts = set(self.action_levels)
        parts = [(rel, set(sup)) for rel, sup in self.trans_parts()]
        parts += [(av, set(mgr.support(av))) for av in self.avail]
        changed = self.changed_levels
        quant = acts | changed
        acc = mgr.DIFF(s, self.term)
        acc_sup = mgr.support(acc)
        occurs: dict[int, set[int]] = {}
        for k, (_, sup) in enumerate(parts):
            for v in sup:
                occurs.setdefault(v, set()).add(k)
        done = {v for v in quant & acc_sup if not occurs.get(v)}
        if done:
            acc = mgr.exists(acc, done)
        remaining = set(range(len(parts)))
        while remaining:
            best: tuple[tuple[int, int, int], int, set[int]] | None = None
            for k in sorted(remaining):
                sup = parts[k][1]
                q = {v for v in (sup & quant) - done if occurs[v] == {k}}
                score = sum(4 if v in acts else 1 for v in q)
                key = (score, -len(sup - acc_sup), -k)
                if best is None or key > best[0]:
                    best = (key, k, q)
            assert best is not None
            _, k, q = best
            rel, sup = parts[k]
            acc = mgr.and_exists(acc, rel, q) if q else mgr.AND(acc, rel)
            done |= q
            acc_sup |= sup
            remaining.discard(k)
            for v in sup:
                occurs[v].discard(k)
        leftover = quant - done
        if leftover:
            acc = mgr.exists(acc, leftover)
        out = mgr.rename(acc, {self.cur_to_next[c]: c for c in changed})
        return mgr.OR(out, mgr.AND(s, self.term))

    # -- explicit-state helpers (testing and witnesses) ----------------------------------
    def available(self, state: Sequence[int]) -> list[list[int]]:
        """Per actor, the available action indices in ``state`` read from the BDDs."""
        arr = self._state_array(state)
        return [
            [j for j, g in enumerate(row) if self.mgr.evaluate(g, arr)]
            for row in self.action_avail
        ]

    def successor(self, state: Sequence[int], move: Sequence[int]) -> tuple[int, ...]:
        """The successor of ``state`` under a joint move, read from the next-state
        functions."""
        arr = self._state_array(state)
        for a, j in enumerate(move):
            bits = self.act[a]
            k = len(bits)
            for b, lv in enumerate(bits):
                arr[lv] = (j >> (k - 1 - b)) & 1
        out = []
        ev = self.mgr.evaluate
        for bits in self.cur:
            x = 0
            for lv in bits:
                f = self.next_fn.get(lv)
                bit = arr[lv] if f is None else ev(f, arr)
                x = (x << 1) | int(bit)
            out.append(x)
        return tuple(out)

    def is_error(self, state: Sequence[int], move: Sequence[int]) -> bool:
        """Would the explicit engine raise on this transition?"""
        arr = self._state_array(state)
        for a, j in enumerate(move):
            bits = self.act[a]
            k = len(bits)
            for b, lv in enumerate(bits):
                arr[lv] = (j >> (k - 1 - b)) & 1
        return self.mgr.evaluate(self.error, arr)

    def actor_indices(self, names: Iterable[str]) -> list[int]:
        """Sorted actor indices of a coalition given by names."""
        known = {a.name: a.index for a in self.cm.actors}
        out = set()
        for name in names:
            if name not in known:
                raise ModelError(f"unknown actor {name!r} (actors: {', '.join(known)})")
            out.add(known[name])
        return sorted(out)

    def count(self, f: int) -> int:
        """Number of states (in the domain) satisfying ``f``."""
        return self.mgr.count(self.mgr.AND(f, self.dom), self.state_levels)

    def bdd_roots(self) -> list[int]:
        roots = [
            self.dom,
            self.next_dom,
            self.term,
            self.any_ending,
            self.at_horizon,
            self.ending_overlap,
            self.initial,
            self.live,
            self.moves,
            self.active,
            self.error,
            *self.avail,
            *(g for row in self.action_avail for g in row),
            *self.next_fn.values(),
            *self.ending_bdds.values(),
            *self._named_cache.values(),
            *(c for part in self.cur_env for c in part.values()),
        ]
        if self._trans_parts is not None:
            roots.extend(rel for rel, _ in self._trans_parts)
        return roots


def encode(
    cm: CompiledModel,
    mgr: BDD | None = None,
    var_order: Sequence[str] | None = None,
    actions: str | Mapping[str, str] = "top",
) -> Encoding:
    """Encode ``cm`` (see the module docstring)."""
    return Encoding(cm, mgr, var_order, actions)
