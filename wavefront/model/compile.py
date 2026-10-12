"""Compile a :class:`~wavefront.model.model.Model` into a :class:`CompiledModel`.

State layout
------------
A state is a tuple of small non-negative ints, one per variable, in this order:

1. ``tick`` (index 0, values ``0..horizon``);
2. declared variables and latches, in declaration order (a latch has the levels of the
   variable it copies with ``"unset"`` prepended);
3. ``pending_<actor>_<action>`` delay counters (actor order, then action order);
4. ``last_<actor>`` for actors declared with ``remember_last=True`` (levels ``"none"``
   followed by the actor's action names in action order);
5. ``fair_<name>`` fairness counters, in declaration order.

Each actor's actions are its built-in action first (``idle``, or ``none`` for Nature),
then its declared actions in declaration order. A joint move is a tuple with one action
index per actor, Nature last.

Generated code
--------------
Expressions are translated once into Python source over the state tuple ``s`` and turned
into functions with a single ``eval`` whose globals hold no builtins except ``min``, ``max``
and ``itertools.compress``. For example, with ``cap`` at index 1 (levels low, mid, high)
and ``belief`` at index 3::

    (V.belief <= "uncertain") & (V.cap < "high")   ->   lambda s: ((s[3] <= 1) and (s[1] < 2))
    V.stock + 1 >= Min(V.a, 2)                     ->   lambda s: ((s[4] + 1) >= min(s[5], 2))
    V.cap.is_in(["low", "high"])                   ->   lambda s: (s[1] in {0, 2})
    V.rights          (a flag used as a condition) ->   lambda s: (s[6] == 1)

Each actor gets one generated availability function evaluating all of its guards (with
delay counters and selected profiles folded in)::

    lambda s: [*compress((0, 1, 2), (True, ((s[3] <= 1) and (s[7] == 0)), (s[1] < 2)))]

Each action's effects become a *contribution* ``(sets, bumps)``: ``sets`` is a tuple of
``(variable index, value)`` and ``bumps`` a tuple of ``(variable index, amount, strict)``.
A contribution without conditional parts is a constant computed at compile time; one with
``SetIf`` or expression values is a generated function of the pre-state::

    lambda s: (((1, 2), *(((3, 0),) if (s[5] == 1) else ())), ((4, 1, False),))

Evaluation therefore costs one function call per guard set and per effectful action;
there is no per-node interpretation at run time.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

from .effects import Bump, Set, SetIf
from .expr import (
    TRUE,
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
    walk,
)
from .model import (
    IDLE,
    NONE,
    ActionDecl,
    LatchDecl,
    Model,
    ModelError,
    VarDecl,
    conjunction,
    is_true,
)

__all__ = [
    "compile",
    "CompiledModel",
    "VarSpec",
    "ActionSpec",
    "ActorSpec",
    "Contribution",
    "expand_relax",
]

Contribution = tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int, bool], ...]]
State = tuple[int, ...]

_GLOBALS: dict[str, Any] = {
    "__builtins__": {},
    "min": min,
    "max": max,
    "compress": itertools.compress,
}

_BOOL_NODES = (Const, Cmp, And, Or, Not, InSet, InvariantRef, EndingRef)



def _trivial(expr: object) -> bool:
    """True for the constant ``TRUE`` guard (or part)."""
    return isinstance(expr, Const) and bool(expr.value)

def _make_fn(src: str) -> Callable[[Sequence[int]], Any]:
    """Turn ``src`` (an expression over ``s``) into ``lambda s: src``."""
    return eval("lambda s: " + src, dict(_GLOBALS))


@dataclass(frozen=True)
class VarSpec:
    """One state component. ``kind`` is ``'level'``, ``'counter'``, ``'flag'`` or
    ``'builtin'``; ``origin`` says which construct created it (``'tick'``, ``'var'``,
    ``'latch'``, ``'pending'``, ``'last'``, ``'fair'``)."""

    name: str
    kind: str
    levels: tuple[str, ...]
    size: int
    origin: str
    init: tuple[int, ...]
    monotone: bool = False


@dataclass(eq=False)
class ActionSpec:
    """A compiled action. ``guard`` is the action's own guard as a callable on a state
    (delay counters, fairness and profiles are applied by :meth:`CompiledModel.available`).

    ``guard_expr`` is the guard as compiled (``TRUE`` when relaxed). For a guard declared
    as named parts, ``guard_parts`` lists ``(part, expr)`` in declaration order with
    relaxed parts replaced by ``TRUE``, and ``guard_expr`` is the conjunction of the
    non-trivial ones; ``guard_parts`` is empty for a plain guard."""

    name: str
    actor: str
    index: int
    guard: Callable[[Sequence[int]], Any]
    effects: tuple[Set | Bump | SetIf, ...]
    delay: int
    source: str
    speculative: bool
    is_idle: bool
    guard_expr: Expr
    pending: int | None = None
    contribution: Contribution | None = None
    contribution_fn: Callable[[Sequence[int]], Contribution] | None = None
    guard_parts: tuple[tuple[str, Expr], ...] = ()

    def contribute(self, state: Sequence[int]) -> Contribution | None:
        """The effect contribution of this action in ``state`` (``None`` if empty)."""
        if self.contribution_fn is not None:
            return self.contribution_fn(state)
        return self.contribution


@dataclass(eq=False)
class ActorSpec:
    """A compiled actor with its actions (built-in action first) and observation set."""

    name: str
    index: int
    actions: list[ActionSpec]
    observes: frozenset[str]
    is_nature: bool = False
    last: int | None = None
    avail_fn: Callable[[Sequence[int]], list[int]] | None = None
    observed_indices: tuple[int, ...] = ()
    fairness: list[tuple[int, int, frozenset[int], str]] = field(default_factory=list)

    def action_index(self, name: str) -> int:
        """Index of the action called ``name``."""
        for action in self.actions:
            if action.name == name:
                return action.index
        raise ModelError(f"actor {self.name} has no action {name!r}")


class _CodeGen:
    """Translate expressions to Python source over the state tuple ``s``."""

    def __init__(self, model: Model, variables: list[VarSpec], index: dict[str, int]) -> None:
        self.model = model
        self.variables = variables
        self.index = index
        self._expanding: list[str] = []

    # -- helpers -----------------------------------------------------------------------
    def var_index(self, name: str, where: str) -> int:
        try:
            return self.index[name]
        except KeyError:
            if name == "tick":
                raise ModelError(f"{where}: an untimed model has no variable 'tick'") from None
            raise ModelError(f"{where}: unknown variable {name!r}") from None

    def resolve(self, value: object, ctx: int | None, where: str) -> int:
        """Resolve a literal (level name, int, bool) to an int in the context of the
        variable at state index ``ctx``."""
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            if ctx is None:
                raise ModelError(
                    f"{where}: level name {value!r} is not compared with or assigned to a "
                    "variable, so it cannot be resolved"
                )
            spec = self.variables[ctx]
            if value in spec.levels:
                return spec.levels.index(value)
            raise ModelError(
                f"{where}: variable {spec.name!r} has no level {value!r} "
                f"(levels: {', '.join(spec.levels)})"
            )
        raise ModelError(f"{where}: cannot use {value!r} as a value")

    def ctx(self, node: Expr, where: str) -> int | None:
        """The variable whose levels name literals compared with ``node``."""
        if isinstance(node, VarRef):
            return self.var_index(node.name, where)
        if isinstance(node, Arith | Min | Max | Ite):
            for child in node.children():
                if not isinstance(child, Lit) and not isinstance(child, _BOOL_NODES):
                    found = self.ctx(child, where)
                    if found is not None:
                        return found
        return None

    def named(self, kind: str, name: str, where: str) -> Expr:
        table = self.model.invariants if kind == "invariant" else self.model.endings
        if name not in table:
            raise ModelError(f"{where}: unknown {kind} {name!r}")
        if name in self._expanding:
            raise ModelError(f"{where}: {kind} {name!r} refers to itself")
        return table[name]

    # -- boolean expressions -----------------------------------------------------------
    def boolean(self, node: Expr, where: str) -> str:
        """Source of a condition."""
        if isinstance(node, Const):
            return "True" if node.value else "False"
        if isinstance(node, VarRef):
            i = self.var_index(node.name, where)
            if self.variables[i].kind != "flag":
                raise ModelError(
                    f"{where}: variable {node.name!r} is used as a condition; compare it "
                    "with a level"
                )
            return f"(s[{i}] == 1)"
        if isinstance(node, Cmp):
            ctx = self.ctx(node.left, where)
            if ctx is None:
                ctx = self.ctx(node.right, where)
            left = self.value(node.left, ctx, where)
            right = self.value(node.right, ctx, where)
            return f"({left} {node.op} {right})"
        if isinstance(node, And | Or):
            joiner = " and " if isinstance(node, And) else " or "
            return "(" + joiner.join(self.boolean(i, where) for i in node.items) + ")"
        if isinstance(node, Not):
            return f"(not {self.boolean(node.item, where)})"
        if isinstance(node, InSet):
            i = self.var_index(node.var.name, where)
            values = sorted({self.resolve(v, i, where) for v in node.values})
            if not values:
                return "False"
            return f"(s[{i}] in {{{', '.join(map(str, values))}}})"
        if isinstance(node, Ite):
            cond = self.boolean(node.cond, where)
            then = self.boolean(node.then, where)
            orelse = self.boolean(node.orelse, where)
            return f"({then} if {cond} else {orelse})"
        if isinstance(node, InvariantRef | EndingRef):
            kind = "invariant" if isinstance(node, InvariantRef) else "ending"
            expr = self.named(kind, node.name, where)
            self._expanding.append(node.name)
            try:
                return self.boolean(expr, f"{where} ({kind} {node.name})")
            finally:
                self._expanding.pop()
        raise ModelError(f"{where}: {node!r} is not a condition")

    # -- integer expressions -----------------------------------------------------------
    def value(self, node: Expr, ctx: int | None, where: str) -> str:
        """Source of an integer value (a level index, counter value or arithmetic)."""
        if isinstance(node, Lit):
            return str(self.resolve(node.value, ctx, where))
        if isinstance(node, VarRef):
            return f"s[{self.var_index(node.name, where)}]"
        if isinstance(node, Arith):
            inner = ctx if ctx is not None else self.ctx(node, where)
            left = self.value(node.left, inner, where)
            right = self.value(node.right, inner, where)
            return f"({left} {node.op} {right})"
        if isinstance(node, Min | Max):
            inner = ctx if ctx is not None else self.ctx(node, where)
            fn = "min" if isinstance(node, Min) else "max"
            return f"{fn}({', '.join(self.value(a, inner, where) for a in node.args)})"
        if isinstance(node, Ite):
            inner = ctx if ctx is not None else self.ctx(node, where)
            cond = self.boolean(node.cond, where)
            then = self.value(node.then, inner, where)
            orelse = self.value(node.orelse, inner, where)
            return f"({then} if {cond} else {orelse})"
        if isinstance(node, _BOOL_NODES):
            return f"(1 if {self.boolean(node, where)} else 0)"
        raise ModelError(f"{where}: {node!r} is not a value")

    def expand_free_vars(self, node: Expr, where: str) -> frozenset[str]:
        """Free variables with named invariants and endings expanded."""
        out: set[str] = set()
        for sub in walk(node):
            if isinstance(sub, VarRef):
                out.add(sub.name)
            elif isinstance(sub, InSet):
                out.add(sub.var.name)
            elif isinstance(sub, InvariantRef | EndingRef):
                kind = "invariant" if isinstance(sub, InvariantRef) else "ending"
                expr = self.named(kind, sub.name, where)
                self._expanding.append(sub.name)
                try:
                    out |= self.expand_free_vars(expr, where)
                finally:
                    self._expanding.pop()
        return frozenset(out)


def is_condition(node: Expr) -> bool:
    """True if ``node`` is boolean-valued (as opposed to an integer value)."""
    if isinstance(node, Ite):
        return is_condition(node.then) and is_condition(node.orelse)
    return isinstance(node, _BOOL_NODES)


class CompiledModel:
    """A model compiled to a state layout and Python callables (spec section 4)."""

    def __init__(
        self,
        model: Model,
        profile: str | Iterable[str] | None = None,
        relax: Iterable[str] = frozenset(),
    ) -> None:
        self.model = model
        self.name = model.name
        self.horizon = model.horizon
        self.timed = model.horizon is not None
        self.relax = expand_relax(model, relax)
        self.selected_profiles = _select_profiles(model, profile)
        self.profiles = self.selected_profiles - self.relax
        self.fairness_constraints = [
            f for f in model.fairness_constraints if f.name not in self.relax
        ]
        self.variables: list[VarSpec] = []
        self.index: dict[str, int] = {}
        self.actors: list[ActorSpec] = []
        self._build_variables()
        self._tick = self.index.get("tick")
        self._gen = _CodeGen(model, self.variables, self.index)
        self._hi = [v.size - 1 for v in self.variables]
        self._monotone = [i for i, v in enumerate(self.variables) if v.monotone]
        self._build_actors()
        self._check_hidden_from()
        self.observation_check()
        self._compile_effects()
        self._compile_system_updates()
        self._compile_profiles_and_availability()
        self._compile_predicates()
        self._expr_cache: dict[Expr, Callable[[Sequence[int]], Any]] = {}

    # -- construction ------------------------------------------------------------------
    def _add(self, spec: VarSpec) -> int:
        if spec.name in self.index:
            raise ModelError(f"duplicate variable name {spec.name!r}")
        self.index[spec.name] = len(self.variables)
        self.variables.append(spec)
        return self.index[spec.name]

    def _build_variables(self) -> None:
        m = self.model
        if m.horizon is not None:
            ticks = tuple(str(i) for i in range(m.horizon + 1))
            self._add(VarSpec("tick", "builtin", ticks, len(ticks), "tick", (0,)))
        decls = {d.name: d for d in m.variables if isinstance(d, VarDecl)}
        for decl in m.variables:
            if isinstance(decl, VarDecl):
                init = tuple(range(len(decl.levels))) if decl.init is None else (decl.init,)
                spec = VarSpec(
                    decl.name, decl.kind, decl.levels, len(decl.levels), "var", init, decl.monotone
                )
            else:
                levels = ("unset",) + self._latch_source_levels(decl, decls)
                spec = VarSpec(decl.name, "builtin", levels, len(levels), "latch", (0,))
            self._add(spec)
        for actor in self._actor_decls():
            for a in actor.actions:
                if a.delay > 0:
                    name = f"pending_{actor.name}_{a.name}"
                    levels = tuple(str(i) for i in range(a.delay + 1))
                    self._add(VarSpec(name, "builtin", levels, len(levels), "pending", (0,)))
        for actor in self._actor_decls():
            if actor.remember_last:
                levels = (NONE,) + tuple(n for n, _ in self._action_names(actor))
                self._add(
                    VarSpec(f"last_{actor.name}", "builtin", levels, len(levels), "last", (0,))
                )
        for f in self.fairness_constraints:
            levels = tuple(str(i) for i in range(f.within + 1))
            self._add(VarSpec(f"fair_{f.name}", "builtin", levels, len(levels), "fair", (0,)))

    def _latch_source_levels(self, decl: LatchDecl, decls: dict[str, VarDecl]) -> tuple[str, ...]:
        if decl.of == "tick" and self.horizon is not None:
            return tuple(str(i) for i in range(self.horizon + 1))
        if decl.of not in decls:
            raise ModelError(f"latch {decl.name!r}: unknown variable {decl.of!r}")
        return decls[decl.of].levels

    def _actor_decls(self) -> list[Any]:
        return [*self.model.actors, self.model.nature()]

    @staticmethod
    def _action_names(actor: Any) -> list[tuple[str, ActionDecl | None]]:
        builtin: list[tuple[str, ActionDecl | None]] = []
        if actor.is_nature:
            builtin = [(NONE, None)]
        elif actor.idle:
            builtin = [(IDLE, None)]
        return builtin + [(a.name, a) for a in actor.actions]

    def _build_actors(self) -> None:
        for i, decl in enumerate(self._actor_decls()):
            names = self._action_names(decl)
            if not names:
                raise ModelError(f"actor {decl.name} has no actions (idle=False and none declared)")
            actions = [self._action_spec(decl, j, n, a) for j, (n, a) in enumerate(names)]
            last = self.index.get(f"last_{decl.name}") if decl.remember_last else None
            observes = self._observation_set(decl)
            spec = ActorSpec(decl.name, i, actions, observes, bool(decl.is_nature), last)
            spec.observed_indices = tuple(
                j for j, v in enumerate(self.variables) if v.name in observes
            )
            self.actors.append(spec)

    def _action_spec(self, actor: Any, j: int, name: str, decl: ActionDecl | None) -> ActionSpec:
        if decl is None:
            return ActionSpec(name, actor.name, j, _make_fn("True"), (), 0, "", False, True, TRUE)
        where = f"guard of {actor.name}.{name}"
        parts = tuple(
            (part, TRUE if decl.part_assumption(part) in self.relax else expr)
            for part, expr in decl.guard_parts
        )
        if parts:
            guard = conjunction([e for _, e in parts])
        else:
            guard = TRUE if decl.assumption in self.relax else decl.guard
        guard_fn = _make_fn(self._gen.boolean(guard, where))
        pending = self.index.get(f"pending_{actor.name}_{name}") if decl.delay else None
        return ActionSpec(
            name,
            actor.name,
            j,
            guard_fn,
            decl.effects,
            decl.delay,
            decl.source,
            decl.speculative,
            False,
            guard,
            pending,
            guard_parts=parts,
        )

    def _observation_set(self, actor: Any) -> frozenset[str]:
        everything = frozenset(self.index)
        obs = actor.observes
        if actor.is_nature or obs.kind == "all":
            base = everything
        else:
            for name in obs.names:
                if name not in self.index:
                    raise ModelError(f"actor {actor.name}: observes unknown variable {name!r}")
            if obs.kind == "except":
                base = everything - frozenset(obs.names)
            else:
                own = {"tick", f"last_{actor.name}"}
                own |= {n for n in self.index if n.startswith(f"pending_{actor.name}_")}
                own |= {
                    f"fair_{f.name}" for f in self.fairness_constraints if f.actor == actor.name
                }
                base = (frozenset(obs.names) | own) & everything
        hidden = {
            d.name
            for d in self.model.variables
            if isinstance(d, VarDecl) and actor.name in d.hidden_from
        }
        return base - hidden

    def _check_hidden_from(self) -> None:
        user_actors = {a.name for a in self.model.actors}
        for d in self.model.variables:
            if isinstance(d, VarDecl):
                for name in d.hidden_from:
                    if name not in user_actors:
                        raise ModelError(
                            f"variable {d.name!r}: hidden_from names unknown actor {name!r} "
                            "(Nature observes everything)"
                        )

    def observation_check(self) -> None:
        """Raise :class:`ModelError` if an actor's action guard (every part of a parted
        guard), fairness trigger or profile ``unless`` condition references a variable the
        actor does not observe (these decide the actor's availability; Nature observes
        everything)."""
        for actor in self.actors:
            for action in actor.actions:
                if action.is_idle:
                    continue
                for part, expr in action.guard_parts:
                    self._check_observed(
                        actor.name,
                        expr,
                        f"the guard part {actor.name}.{action.name}:{part}",
                    )
                if not action.guard_parts:
                    self._check_observed(
                        actor.name,
                        action.guard_expr,
                        f"the guard of action {actor.name}.{action.name}",
                    )
        for f in self.fairness_constraints:
            self._check_observed(
                f.actor, f.trigger, f"the trigger of fairness constraint {f.name!r}"
            )
        for p in self.model.profiles:
            if p.name not in self.relax:
                self._check_observed(
                    p.actor, p.unless, f"the unless condition of profile {p.name!r}"
                )

    def _check_observed(self, actor_name: str, expr: Expr, construct: str) -> None:
        actor = self._actor(actor_name, construct)
        if actor.is_nature:
            return
        for name in sorted(self._gen.expand_free_vars(expr, construct)):
            if name not in actor.observes:
                raise ModelError(
                    f"observation violation: {construct} references variable {name!r}, "
                    f"which actor {actor.name} does not observe"
                )

    # -- effects -----------------------------------------------------------------------
    def _compile_effects(self) -> None:
        for actor in self.actors:
            for action in actor.actions:
                const, src = self._contribution(action)
                action.contribution = const
                action.contribution_fn = None if src is None else _make_fn(src)

    def _effect_target(self, var: str, where: str) -> int:
        i = self._gen.var_index(var, where)
        if self.variables[i].origin != "var":
            raise ModelError(f"{where}: effects may not target built-in variable {var!r}")
        return i

    def _set_value(self, i: int, value: object, where: str) -> tuple[int | None, str]:
        """(constant value or None, source) for a Set value on variable index ``i``."""
        spec = self.variables[i]
        if isinstance(value, Expr):
            src = self._gen.value(value, i, where)
            return None, f"min(max({src}, 0), {spec.size - 1})"
        v = self._gen.resolve(value, i, where)
        if not 0 <= v < spec.size:
            raise ModelError(f"{where}: value {value!r} is out of range for {spec.name!r}")
        return v, str(v)

    def _contribution(self, action: ActionSpec) -> tuple[Contribution | None, str | None]:
        """Compile an action's effects to a constant contribution or generated source."""
        where = f"effect of {action.actor}.{action.name}"
        set_parts: list[str] = []
        const_sets: dict[int, int] = {}
        dynamic = False
        bumps: list[tuple[int, int, bool]] = []
        for eff in action.effects:
            i = self._effect_target(eff.var, where)
            spec = self.variables[i]
            if isinstance(eff, Bump):
                if spec.monotone and eff.amount < 0:
                    raise ModelError(
                        f"{where}: Bump({eff.var!r}, {eff.amount}) decreases monotone variable"
                    )
                bumps.append((i, eff.amount, eff.strict))
                continue
            value, src = self._set_value(i, eff.value, where)
            if spec.monotone and value == 0:
                raise ModelError(
                    f"{where}: Set({eff.var!r}, {eff.value!r}) sets monotone variable to its "
                    "lowest level"
                )
            if isinstance(eff, SetIf):
                cond = self._gen.boolean(eff.cond, where)
                set_parts.append(f"*((({i}, {src}),) if {cond} else ())")
                dynamic = True
            elif value is None:
                set_parts.append(f"({i}, {src})")
                dynamic = True
            else:
                if const_sets.get(i, value) != value:
                    raise ModelError(f"{where}: two Sets on {eff.var!r} with different values")
                const_sets[i] = value
                set_parts.append(f"({i}, {src})")
        bump_t = tuple(bumps)
        if not dynamic:
            sets_t = tuple(const_sets.items())
            return (None if not sets_t and not bump_t else (sets_t, bump_t)), None
        return None, f"(({', '.join(set_parts)},), {bump_t!r})"

    # -- system updates ----------------------------------------------------------------
    def _compile_system_updates(self) -> None:
        self._delays: list[tuple[int, int, int, int, ActionSpec]] = []
        for actor in self.actors:
            for action in actor.actions:
                if action.delay:
                    assert action.pending is not None
                    self._delays.append(
                        (actor.index, action.index, action.pending, action.delay, action)
                    )
        self._lasts = [(a.index, a.last) for a in self.actors if a.last is not None]
        self._latches: list[tuple[int, int, Callable[[Sequence[int]], Any]]] = []
        for decl in self.model.latches:
            where = f"latch {decl.name}"
            src = self._gen.var_index(decl.of, where)
            when = _make_fn(self._gen.boolean(decl.when, where))
            self._latches.append((self.index[decl.name], src, when))
        self._fair: list[tuple[int, int, frozenset[int], int, Callable[[Sequence[int]], Any]]] = []
        for f in self.fairness_constraints:
            where = f"fairness {f.name}"
            actor = self._actor(f.actor, where)
            responses = frozenset(self._action_of(actor, r, where) for r in f.responses)
            trigger = _make_fn(self._gen.boolean(f.trigger, where))
            idx = self.index[f"fair_{f.name}"]
            self._fair.append((idx, actor.index, responses, f.within, trigger))
            actor.fairness.append((idx, f.within, responses, f.name))

    def _actor(self, name: str, where: str) -> ActorSpec:
        for actor in self.actors:
            if actor.name == name:
                return actor
        raise ModelError(f"{where}: unknown actor {name!r}")

    @staticmethod
    def _action_of(actor: ActorSpec, name: str, where: str) -> int:
        for action in actor.actions:
            if action.name == name:
                return action.index
        raise ModelError(f"{where}: actor {actor.name} has no action {name!r}")

    # -- availability ------------------------------------------------------------------
    def _compile_profiles_and_availability(self) -> None:
        conditions: dict[tuple[int, int], list[str]] = {}
        for p in self.model.profiles:
            where = f"profile {p.name}"
            actor = self._actor(p.actor, where)
            indices = [self._action_of(actor, name, where) for name in p.forbid]
            unless = self._gen.boolean(p.unless, where)
            if p.name in self.profiles:
                for j in indices:
                    conditions.setdefault((actor.index, j), []).append(unless)
        for actor in self.actors:
            terms = []
            for action in actor.actions:
                parts = [
                    self._gen.boolean(action.guard_expr, f"guard of {actor.name}.{action.name}")
                ]
                if action.pending is not None:
                    parts.append(f"(s[{action.pending}] == 0)")
                parts.extend(conditions.get((actor.index, action.index), []))
                parts = [p for p in parts if p != "True"] or ["True"]
                terms.append(parts[0] if len(parts) == 1 else "(" + " and ".join(parts) + ")")
            indices = tuple(range(len(actor.actions)))
            actor.avail_fn = _make_fn(f"[*compress({indices!r}, ({', '.join(terms)},))]")

    # -- predicates --------------------------------------------------------------------
    def _compile_predicates(self) -> None:
        m = self.model
        self.invariant_fns = {
            n: _make_fn(self._gen.boolean(e, f"invariant {n}")) for n, e in m.invariants.items()
        }
        self.ending_fns = {
            n: _make_fn(self._gen.boolean(e, f"ending {n}")) for n, e in m.endings.items()
        }
        self.assume_fns = {
            n: _make_fn(self._gen.boolean(e, f"assumption {n}"))
            for n, e in m.assumes.items()
            if n not in self.relax
        }
        names = tuple(m.endings)
        if names:
            terms = ", ".join(self._gen.boolean(e, f"ending {n}") for n, e in m.endings.items())
            self._endings_fn = _make_fn(f"[*compress({names!r}, ({terms},))]")
        else:
            self._endings_fn = _make_fn("[]")

    # -- public API --------------------------------------------------------------------
    @property
    def actor_names(self) -> list[str]:
        """Actor names in joint-move order (Nature last)."""
        return [a.name for a in self.actors]

    def initial_states(self) -> list[State]:
        """The product of declared initial values (``init=None`` contributes every level),
        filtered by the model's (unrelaxed) ``assume`` restrictions. Latches whose condition
        already holds in an initial state are set there."""
        out: dict[State, None] = {}
        for combo in itertools.product(*(v.init for v in self.variables)):
            state = list(combo)
            for idx, src, when in self._latches:
                if state[idx] == 0 and when(state):
                    state[idx] = state[src] + 1
            if all(fn(state) for fn in self.assume_fns.values()):
                out[tuple(state)] = None
        return list(out)

    def available(self, state: Sequence[int]) -> list[list[int]]:
        """Per actor, the indices of available actions: guards, delay counters, selected
        profiles and fairness restrictions. Raises :class:`ModelError` naming the state and
        actor if some actor has no available action."""
        out = []
        for actor in self.actors:
            acts = actor.avail_fn(state)  # type: ignore[misc]
            for idx, within, responses, fname in actor.fairness:
                if state[idx] >= within:
                    acts = [j for j in acts if j in responses]
                    if not acts:
                        raise ModelError(
                            f"fairness constraint {fname!r} restricts actor {actor.name} to "
                            f"its responses, but none is available in state "
                            f"{self.format_state(state)}"
                        )
            if not acts:
                raise ModelError(
                    f"actor {actor.name} has no available action in state "
                    f"{self.format_state(state)}"
                )
            out.append(acts)
        return out

    def step(self, state: Sequence[int], joint_move: Sequence[int]) -> State:
        """The successor of ``state`` under ``joint_move`` (one action index per actor)."""
        if len(joint_move) != len(self.actors):
            raise ModelError(f"joint move {tuple(joint_move)} needs {len(self.actors)} entries")
        contribs = [
            actor.actions[j].contribute(state) if not actor.actions[j].delay else None
            for actor, j in zip(self.actors, joint_move, strict=True)
        ]
        return self._successor(state, tuple(joint_move), contribs)

    def successors(
        self, state: State, avail: list[list[int]], moves: Iterable[tuple[int, ...]]
    ) -> list[State]:
        """Successors of ``state`` for ``moves`` (which must be ``product(*avail)`` in
        order). Effect contributions are computed once per available action."""
        per_actor = []
        for actor, acts in zip(self.actors, avail, strict=True):
            row = []
            for j in acts:
                action = actor.actions[j]
                if action.delay:
                    row.append(None)
                elif action.contribution_fn is not None:
                    row.append(action.contribution_fn(state))
                else:
                    row.append(action.contribution)
            per_actor.append(row)
        succ = self._successor
        return [
            succ(state, jm, cs) for jm, cs in zip(moves, itertools.product(*per_actor), strict=True)
        ]

    def _successor(
        self, s: Sequence[int], jm: tuple[int, ...], contribs: Sequence[Contribution | None]
    ) -> State:
        new = list(s)
        if any(contribs):
            self._compose(new, s, jm, contribs, delayed=False)
        if self._tick is not None:
            new[self._tick] = s[self._tick] + 1
        if self._delays:
            self._update_delays(new, s, jm)
        for actor_i, idx in self._lasts:
            new[idx] = jm[actor_i] + 1
        for idx, src, when in self._latches:
            if new[idx] == 0 and when(new):
                new[idx] = new[src] + 1
        for idx, actor_i, responses, within, trigger in self._fair:
            if jm[actor_i] not in responses and trigger(new):
                c = s[idx] + 1
                new[idx] = within if c > within else c
            else:
                new[idx] = 0
        for i in self._monotone:
            if new[i] < s[i]:
                self._monotone_error(s, jm, i, new[i])
        return tuple(new)

    def _compose(
        self,
        new: list[int],
        s: Sequence[int],
        jm: tuple[int, ...],
        contribs: Sequence[Contribution | None],
        delayed: bool,
    ) -> None:
        """Apply contributions to ``new`` in place (spec 3.4): Sets, then summed Bumps,
        then clamping (or a strict error)."""
        sets: dict[int, int] = {}
        bumps: dict[int, int] = {}
        strict: set[int] = set()
        for c in contribs:
            if c is None:
                continue
            for v, val in c[0]:
                if sets.setdefault(v, val) != val:
                    self._conflict_error(s, jm, v, delayed)
            for v, amt, is_strict in c[1]:
                bumps[v] = bumps.get(v, 0) + amt
                if is_strict:
                    strict.add(v)
        for v, val in sets.items():
            new[v] = val
        hi = self._hi
        for v, amt in bumps.items():
            x = new[v] + amt
            if x < 0 or x > hi[v]:
                if v in strict:
                    raise ModelError(
                        f"strict Bump takes {self.variables[v].name!r} out of range in state "
                        f"{self.format_state(s)} under joint move {self.format_move(jm)}"
                    )
                x = 0 if x < 0 else hi[v]
            new[v] = x

    def _update_delays(self, new: list[int], s: Sequence[int], jm: tuple[int, ...]) -> None:
        fired: list[Contribution | None] = []
        for actor_i, action_j, idx, d, action in self._delays:
            c = s[idx]
            if c:
                new[idx] = c - 1
                if c == 1:
                    fired.append(action.contribute(s))
            elif jm[actor_i] == action_j:
                new[idx] = d
        if any(fired):
            self._compose(new, s, jm, fired, delayed=True)

    # -- error reporting ---------------------------------------------------------------
    def _conflict_error(self, s: Sequence[int], jm: tuple[int, ...], v: int, delayed: bool) -> None:
        setters = []
        actions = (
            [a for _, _, idx, _, a in self._delays if s[idx] == 1]
            if delayed
            else [actor.actions[j] for actor, j in zip(self.actors, jm, strict=True)]
        )
        for action in actions:
            c = action.contribute(s)
            for var, val in c[0] if c else ():
                if var == v:
                    setters.append(f"{action.actor}.{action.name} sets {self.level_name(v, val)}")
        kind = "delayed effects" if delayed else "joint move " + self.format_move(jm)
        raise ModelError(
            f"conflicting Set on {self.variables[v].name!r} in state {self.format_state(s)} "
            f"under {kind}: {'; '.join(setters)}"
        )

    def _monotone_error(self, s: Sequence[int], jm: tuple[int, ...], v: int, value: int) -> None:
        raise ModelError(
            f"monotone variable {self.variables[v].name!r} decreases from "
            f"{self.level_name(v, s[v])} to {self.level_name(v, value)} in state "
            f"{self.format_state(s)} under joint move {self.format_move(jm)}"
        )

    # -- predicates and rendering ------------------------------------------------------
    def is_terminal(self, state: Sequence[int]) -> bool:
        """True when ``tick == horizon`` (timed models) or some ending holds."""
        if self._tick is not None and state[self._tick] >= self.horizon:  # type: ignore[operator]
            return True
        return bool(self._endings_fn(state))

    def ending_of(self, state: Sequence[int]) -> str | None:
        """The ending that holds, ``"HORIZON"`` if terminal by tick only, else ``None``.
        Raises :class:`ModelError` if two endings hold."""
        hits = self._endings_fn(state)
        if len(hits) == 1:
            return hits[0]
        if hits:
            raise ModelError(
                f"endings {', '.join(hits)} hold together in state {self.format_state(state)}; "
                "endings must be mutually exclusive"
            )
        if self._tick is not None and state[self._tick] >= self.horizon:  # type: ignore[operator]
            return "HORIZON"
        return None

    def observe(self, actor_name: str, state: Sequence[int]) -> tuple[int, ...]:
        """The projection of ``state`` onto the variables ``actor_name`` observes, in state
        order."""
        actor = self._actor(actor_name, "observe")
        return tuple(state[i] for i in actor.observed_indices)

    def assumptions(self) -> list[str]:
        """Named assumptions that can be relaxed: non-trivial action guards
        (``"<actor>.<action>"``, or for a guard declared as named parts its non-trivial
        parts ``"<actor>.<action>:<part>"`` in declaration order), fairness constraints,
        selected profiles and ``assume`` restrictions, in that order. Relaxing a declared
        action whose guard (or part) is ``TRUE`` is accepted as a no-op but such guards are
        not listed. The list is the same whatever is relaxed."""
        m = self.model
        guards: list[str] = []
        for actor in [*m.actors, m.nature()]:
            for a in actor.actions:
                if a.guard_parts:
                    guards += [a.part_assumption(p) for p, e in a.guard_parts if not is_true(e)]
                elif not is_true(a.guard):
                    guards.append(a.assumption)
        fair = [f.name for f in m.fairness_constraints]
        profiles = [p.name for p in m.profiles if p.name in self.selected_profiles]
        return [*guards, *fair, *profiles, *m.assumes]

    def compile_expr(self, expr: Expr) -> Callable[[Sequence[int]], Any]:
        """Compile an ad-hoc expression (cached by identity)."""
        fn = self._expr_cache.get(expr)
        if fn is None:
            where = "expression"
            src = (
                self._gen.boolean(expr, where)
                if is_condition(expr)
                else self._gen.value(expr, None, where)
            )
            fn = self._expr_cache[expr] = _make_fn(src)
        return fn

    def evaluate(self, expr_or_name: Expr | str, state: Sequence[int]) -> bool | int:
        """Evaluate a named invariant or ending, or an expression, in ``state``."""
        if isinstance(expr_or_name, str):
            if expr_or_name in self.invariant_fns:
                return bool(self.invariant_fns[expr_or_name](state))
            if expr_or_name in self.ending_fns:
                return bool(self.ending_fns[expr_or_name](state))
            raise ModelError(f"no invariant or ending named {expr_or_name!r}")
        result = self.compile_expr(expr_or_name)(state)
        return bool(result) if is_condition(expr_or_name) else int(result)

    def level_name(self, var: int | str, value: int) -> str:
        """The level name of ``value`` for a variable (by index or name)."""
        spec = self.variables[self.index[var] if isinstance(var, str) else var]
        return spec.levels[value] if 0 <= value < spec.size else str(value)

    def state_dict(self, state: Sequence[int]) -> dict[str, str]:
        """``{variable: level name}`` for a state."""
        return {
            v.name: self.level_name(i, x) for i, (v, x) in enumerate(zip(self.variables, state))
        }

    def format_state(self, state: Sequence[int]) -> str:
        """A state as ``{tick=0, cap=low, ...}`` with level names."""
        return "{" + ", ".join(f"{k}={v}" for k, v in self.state_dict(state).items()) + "}"

    def format_move(self, joint_move: Sequence[int]) -> str:
        """A joint move as ``INC.concede, CH.idle, Nature.none``."""
        return ", ".join(
            f"{a.name}.{a.actions[j].name}" for a, j in zip(self.actors, joint_move, strict=True)
        )

    def budget(self) -> dict[str, int]:
        """The parameter budget: counts of the model's modeling choices."""
        user_vars = [v for v in self.variables if v.origin == "var"]
        declared = [a for actor in self.actors for a in actor.actions if not a.is_idle]
        state_bound = 1
        for v in self.variables:
            state_bound *= v.size
        return {
            "variables": len(user_vars),
            "levels": sum(v.size for v in user_vars),
            "actors": len(self.actors),
            "actions": len(declared),
            "guards": sum(
                1 for a in declared if not (isinstance(a.guard_expr, Const) and a.guard_expr.value)
            ),
            "guard_parts": sum(
                sum(1 for _, e in a.guard_parts if not _trivial(e))
                if a.guard_parts
                else (0 if a.is_idle or _trivial(a.guard_expr) else 1)
                for a in declared
            ),
            "speculative_actions": sum(1 for a in declared if a.speculative),
            "fairness_constraints": len(self.model.fairness_constraints),
            "delays": sum(1 for a in declared if a.delay),
            "latches": len(self.model.latches),
            "invariants": len(self.model.invariants),
            "endings": len(self.model.endings),
            "builtin_variables": len(self.variables) - len(user_vars),
            "state_space_bound": state_bound,
        }

    def __repr__(self) -> str:
        n_vars, n_actors = len(self.variables), len(self.actors)
        return f"CompiledModel({self.name!r}, {n_vars} variables, {n_actors} actors)"


def _select_profiles(model: Model, profile: str | Iterable[str] | None) -> frozenset[str]:
    if profile is None:
        return frozenset()
    names = (profile,) if isinstance(profile, str) else tuple(profile)
    known = {p.name for p in model.profiles}
    for name in names:
        if name not in known:
            raise ModelError(f"model {model.name!r} has no profile {name!r}")
    return frozenset(names)


def expand_relax(model: Model, relax: Iterable[str]) -> frozenset[str]:
    """Validate assumption names to relax and expand them: ``<actor>.<action>`` for a guard
    declared as named parts stands for all of its parts ``<actor>.<action>:<part>``, which
    are added to the returned set. Unknown names raise :class:`ModelError`; names of
    trivial guards and parts and of unselected profiles are accepted."""
    names = frozenset((relax,) if isinstance(relax, str) else relax)
    known: set[str] = set()
    parts_of: dict[str, list[str]] = {}
    for actor in [*model.actors, model.nature()]:
        for x in actor.actions:
            known.add(x.assumption)
            if x.guard_parts:
                parts_of[x.assumption] = [x.part_assumption(p) for p, _ in x.guard_parts]
                known.update(parts_of[x.assumption])
    known |= {f.name for f in model.fairness_constraints}
    known |= {p.name for p in model.profiles}
    known |= set(model.assumes)
    unknown = sorted(names - known)
    if unknown:
        raise ModelError(
            f"model {model.name!r}: cannot relax unknown assumption(s) {', '.join(unknown)}"
        )
    expanded = set(names)
    for name in names:
        expanded.update(parts_of.get(name, ()))
    return frozenset(expanded)


def compile(
    model: Model,
    profile: str | Iterable[str] | None = None,
    relax: Iterable[str] = frozenset(),
) -> CompiledModel:
    """Compile ``model``, optionally selecting behavioral profiles and relaxing named
    assumptions (see :meth:`CompiledModel.assumptions`): a relaxed guard becomes ``TRUE``,
    a relaxed guard part is dropped from its guard's conjunction (relaxing
    ``<actor>.<action>`` relaxes every part of a parted guard), a relaxed fairness
    constraint is removed (with its counter), a relaxed profile is not applied and a
    relaxed ``assume`` no longer filters the initial states."""
    return CompiledModel(model, profile, relax)
