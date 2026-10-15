"""Bounded queries from a given state, for the WW2 v1 tests (an analysis device, not a model).

:func:`wavefront.bmc.reach` and :func:`wavefront.bmc.relax` start from the model's declared
initial states (tick 0). The registered tests start from hindsight snapshot states with
their built-ins (decisions E1), so this module unrolls the same Z3 encoding
(:mod:`wavefront.bmc.encode`, spec section 6) with the initial-state constraints replaced by
``state[0] == start`` (every variable, built-ins included; ``assume`` filters are not
applied, as for ``explore(cm, initial=...)``). Everything else is the encoding of the
package: guards with their assumption Bools, delays, fairness, profiles, terminal freezing.

Constraints on the actors' choices (``constrain=``, a function of the encoding returning Z3
constraints) express the readings of decisions E5: a move fixed at a tick (T3's refused
concession, T7's embargo), an action never chosen (T11's "without an attack"), or a whole
actor playing a fixed memoryless strategy (:func:`play`: the first available action of a
priority list, else the built-in action). A fixed strategy is how the fallback of decisions
E6 is computed: if the actors outside a coalition, fixed to one strategy, leave no play that
avoids a target, the coalition (with them fixed) forces it, which shows that their side
*cannot keep* the complement (a refutation of their kernel membership); and if a coalition
fixed to one strategy leaves no play that reaches the target, the coalition keeps its
complement whatever the others do (a sufficiency check of its kernel membership). Results
computed this way are reported as "by fixed strategy", never as the kernel itself.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any

import z3

from wavefront.bmc.encode import Encoding, _Builder, _BumpItem, _effect_items, _SetItem, _Translator
from wavefront.bmc.queries import BmcTrace, RelaxResult, _check, _Query
from wavefront.model import V
from wavefront.model.compile import CompiledModel, expand_relax
from wavefront.model.expr import Const, Expr

__all__ = [
    "Priorities",
    "available",
    "avoid",
    "blocks",
    "forces",
    "strategies",
    "chosen",
    "exists_from",
    "fix",
    "never",
    "play",
    "reach_from",
    "relax_from",
    "replay",
    "terminal",
    "wellformed_from",
]

Constrain = Callable[[Encoding], Iterable[z3.BoolRef]]


class _FromState(_Builder):
    """The encoding of :mod:`wavefront.bmc.encode` with ``state[0] == start``."""

    def __init__(self, cm: CompiledModel, k: int, start: Sequence[int]) -> None:
        if len(start) != len(cm.variables):
            raise ValueError("start state has the wrong length")
        self.start = tuple(start)
        super().__init__(cm, k)

    def _initial(self) -> None:
        s0 = self.enc.state[0]
        self.out.extend(x == v for x, v in zip(s0, self.start, strict=True))


class _QueryFrom(_Query):
    """:class:`wavefront.bmc.queries._Query` over the encoding from ``start``."""

    def __init__(self, cm: CompiledModel, start: Sequence[int], k: int, target: Any) -> None:
        self.enc = _FromState(cm, k, start).build()
        enc = self.enc
        self.hit = [z3.And(enc.active[t], enc.target(target, t)) for t in range(k + 1)]
        self.by = [z3.Bool(f"reached_by@{t}") for t in range(k + 1)]
        self.goal = []
        for t in range(k + 1):
            earlier = [self.by[t - 1]] if t else []
            self.goal.append(z3.Implies(self.by[t], z3.Or(*earlier, self.hit[t])))


def _actor(cm: CompiledModel, name: str):
    return next(a for a in cm.actors if a.name == name)


def chosen(enc: Encoding, t: int, actor: str) -> z3.ArithRef:
    """The action index chosen by ``actor`` at step ``t``."""
    return enc.chosen[t][_actor(enc.cm, actor).index]


def fix(enc: Encoding, t: int, actor: str, action: str) -> list[z3.BoolRef]:
    """``actor`` plays ``action`` at step ``t`` (the move is required, so the state at step
    ``t`` must offer it)."""
    a = _actor(enc.cm, actor)
    return [enc.active[t + 1], chosen(enc, t, actor) == a.action_index(action)]


def never(enc: Encoding, actor: str, action: str) -> list[z3.BoolRef]:
    """``actor`` never plays ``action``."""
    j = _actor(enc.cm, actor).action_index(action)
    return [chosen(enc, t, actor) != j for t in range(enc.k)]


def terminal(cm: CompiledModel) -> Expr:
    """The terminal predicate as an expression: an ending holds or the horizon is reached."""
    expr = V.tick >= cm.horizon
    for name in cm.model.endings:
        expr = expr | V.ending(name)
    return expr


def available(enc: Encoding, t: int, actor: str, action: str) -> z3.BoolRef:
    """Availability of ``actor.action`` at step ``t`` as the encoding defines it: every
    unrelaxed guard part (with its assumption Bool), the delay counter, the selected profiles
    and the actor's fairness restriction."""
    cm = enc.cm
    tr = getattr(enc, "_tr", None)
    if tr is None:
        tr = enc._tr = _Translator(cm)  # type: ignore[attr-defined]
    a = _actor(cm, actor)
    x = a.actions[a.action_index(action)]
    s = enc.state[t]
    conds: list[z3.BoolRef] = []
    if x.guard_parts:
        guards = [(f"{a.name}.{x.name}:{p}", g) for p, g in x.guard_parts]
    else:
        guards = [(f"{a.name}.{x.name}", x.guard_expr)]
    for name, g in guards:
        if not (isinstance(g, Const) and g.value):
            conds.append(z3.Or(z3.Not(enc.assume[name]), tr.boolean(g, s)))
    if x.pending is not None:
        conds.append(s[x.pending] == 0)
    for p in cm.model.profiles:
        if p.name in cm.profiles and p.actor == a.name and x.name in p.forbid:
            conds.append(z3.Or(z3.Not(enc.assume[p.name]), tr.boolean(p.unless, s)))
    for f in cm.fairness_constraints:
        if f.actor == a.name and x.name not in f.responses:
            idx = cm.index[f"fair_{f.name}"]
            conds.append(z3.Not(z3.And(enc.assume[f.name], s[idx] >= f.within)))
    return z3.And(*conds) if conds else z3.BoolVal(True)


Priorities = Sequence[str] | Sequence[tuple[Any, Sequence[str]]]


def play(enc: Encoding, actor: str, priorities: Priorities) -> list[z3.BoolRef]:
    """``actor`` plays a fixed memoryless strategy at every non-terminal step: the first
    available action of ``priorities``, then of the actor's remaining actions in index order
    (the built-in ``idle`` or ``none`` first). The order is total, so the strategy is defined
    in every state in which the actor has an available action (a fairness restriction
    included), and the constraint never removes a play for want of a move.

    ``priorities`` is a list of action names, or a list of ``(condition, names)`` pairs,
    the condition an expression (or ``True``) on the state of the step: the first pair whose
    condition holds supplies the priority list for that step (a conditional memoryless
    strategy, still a function of the state); when none holds the actor plays the first
    available of its actions in index order."""
    a = _actor(enc.cm, actor)
    names = [x.name for x in a.actions]
    cases: list[tuple[Any, Sequence[str]]]
    if priorities and isinstance(priorities[0], tuple):
        cases = list(priorities)  # type: ignore[arg-type]
    else:
        cases = [(True, list(priorities))]  # type: ignore[arg-type]
    for _, prio in cases:
        unknown = [p for p in prio if p not in names]
        if unknown:
            raise ValueError(f"{actor} has no action {unknown}")

    def chain(t: int, prio: Sequence[str]) -> z3.ArithRef:
        order = [*prio, *(n for n in names if n not in prio)]
        choice: z3.ArithRef = z3.IntVal(a.action_index(order[-1]))
        for name in reversed(order[:-1]):
            choice = z3.If(available(enc, t, actor, name), a.action_index(name), choice)
        return choice

    out = []
    for t in range(enc.k):
        choice = chain(t, [])
        for cond, prio in reversed(cases):
            branch = chain(t, prio)
            if cond is True:
                choice = branch
            else:
                choice = z3.If(enc.target(cond, t), branch, choice)
        out.append(z3.Implies(z3.Not(enc.terminal[t]), chosen(enc, t, actor) == choice))
    return out


def exists_from(
    cm: CompiledModel,
    start: Sequence[int],
    k: int,
    condition: Callable[[Encoding], z3.BoolRef],
    constrain: Constrain | Sequence[Constrain] | None = None,
) -> BmcTrace | None:
    """A play of at most ``k`` transitions from ``start``, with every named assumption
    asserted and the extra constraints, on which ``condition(enc)`` (a Z3 formula over the
    unrolled states and moves) holds; the play returned runs to step ``k`` (states past a
    terminal state repeat it). ``None`` if there is none."""
    q = _QueryFrom(cm, start, k, terminal(cm))
    enc = q.enc
    solver = enc.solver()
    solver.add(*enc.active, *enc.assume.values(), *_constraints(enc, constrain), condition(enc))
    if _check(solver) != z3.sat:
        return None
    model = solver.model()
    states, moves = enc.decode(model, k)
    return BmcTrace(states, moves)


def _constraints(enc: Encoding, constrain: Constrain | Sequence[Constrain] | None) -> list:
    if constrain is None:
        return []
    fns = [constrain] if callable(constrain) else list(constrain)
    return [c for fn in fns for c in fn(enc)]


def reach_from(
    cm: CompiledModel,
    start: Sequence[int],
    k: int,
    target: Any,
    relax: Iterable[str] = frozenset(),
    constrain: Constrain | Sequence[Constrain] | None = None,
) -> BmcTrace | None:
    """A shortest play of at most ``k`` transitions from ``start`` to ``target`` (an ending
    or invariant name or an expression), with every named assumption asserted except those
    in ``relax`` and the extra constraints; ``None`` if there is none."""
    relaxed = expand_relax(cm.model, relax)
    q = _QueryFrom(cm, start, k, target)
    solver = q.solver()
    solver.add(*_constraints(q.enc, constrain))
    order = [n for n in q.enc.assume if n in relaxed]
    return q.shortest(solver, q.literals(relaxed), order)


def relax_from(
    cm: CompiledModel,
    start: Sequence[int],
    k: int,
    target: Any,
    max_relax: int = 3,
    max_sets: int = 20,
    constrain: Constrain | Sequence[Constrain] | None = None,
    candidates: Iterable[str] | None = None,
) -> RelaxResult:
    """:func:`wavefront.bmc.relax` from ``start`` with the extra constraints. With
    ``candidates`` only those assumptions may be relaxed (the others stay asserted)."""
    q = _QueryFrom(cm, start, k, target)
    enc = q.enc
    extra = _constraints(enc, constrain)
    names = list(enc.assume) if candidates is None else [n for n in enc.assume if n in candidates]
    fixed = [b for n, b in enc.assume.items() if n not in names]
    bools = {n: enc.assume[n] for n in names}
    names_of = {b.get_id(): n for n, b in bools.items()}
    goal = q.by[k]
    solver = q.solver()
    solver.add(*extra, *fixed)
    solver.set("core.minimize", True)
    if _check(solver, *bools.values(), goal) == z3.sat:
        trace = q.shortest(solver, list(bools.values()), [])
        return RelaxResult(True, [], 0, [[]], trace)
    core_ids = {c.get_id() for c in solver.unsat_core()}
    core = [n for n, b in bools.items() if b.get_id() in core_ids]
    relaxed_count = [z3.Not(b) for b in bools.values()]
    opt = z3.Optimize()
    opt.set("elim_01", False)
    opt.add(*enc.constraints, *q.goal, goal, *extra, *fixed)
    if relaxed_count:
        opt.add(z3.AtMost(*relaxed_count, max_relax))
    for b in bools.values():
        opt.add_soft(b, 1)
    if not bools or _check(opt) == z3.unsat:
        return RelaxResult(False, core, None, [], None)
    model = opt.model()
    size = sum(1 for b in bools.values() if z3.is_false(model.eval(b, model_completion=True)))
    enum = q.solver()
    enum.add(*extra, *fixed, goal, z3.AtMost(*relaxed_count, size))
    found: list[list[str]] = []
    while len(found) < max_sets and _check(enum) == z3.sat:
        model = enum.model()
        picked = [b for b in bools.values() if z3.is_false(model.eval(b, model_completion=True))]
        found.append([names_of[b.get_id()] for b in picked])
        enum.add(z3.Or(*picked))
    trace = reach_from(cm, start, k, target, relax=found[0], constrain=constrain)
    return RelaxResult(False, core, size, found, trace)


def replay(cm: CompiledModel, start: Sequence[int], moves: Sequence[Sequence[int]]) -> list:
    """The states of ``moves`` played from ``start`` with ``cm.step``, each move checked
    available; raises naming the first unavailable action."""
    states = [tuple(start)]
    for move in moves:
        s = states[-1]
        avail = cm.available(s)
        for a, j, acts in zip(cm.actors, move, avail, strict=True):
            if j not in acts:
                raise ValueError(
                    f"tick {cm.state_dict(s)['tick']}: {a.name}.{a.actions[j].name} unavailable"
                )
        states.append(cm.step(s, move))
    return states


def _value(enc: Encoding, item: _SetItem, t: int) -> z3.ArithRef:
    if isinstance(item.value, Expr):
        hi = enc.cm.variables[item.var].size - 1
        raw = _Translator(enc.cm).value(item.value, enc.state[t], item.var)
        return z3.If(raw < 0, 0, z3.If(raw > hi, hi, raw))
    return z3.IntVal(item.value)


def _hazards(enc: Encoding, t: int) -> list[tuple[str, z3.BoolRef]]:
    """Conditions at step ``t`` under which the explicit engine would raise on some joint
    move (spec sections 1 and 3.4): an actor with no available action, two immediate ``Set``s
    of one variable to different values by two actors, two delayed ``Set``s of one variable
    to different values falling due together, a ``Set`` lowering a monotone variable, and a
    negative ``Bump`` of a monotone variable."""
    cm = enc.cm
    tr = _Translator(cm)
    s = enc.state[t]
    out: list[tuple[str, z3.BoolRef]] = []
    for a in cm.actors:
        avail = [available(enc, t, a.name, x.name) for x in a.actions]
        out.append((f"{a.name} has no available action", z3.Not(z3.Or(*avail))))
    immediate: dict[int, list[tuple[str, str, z3.BoolRef, z3.ArithRef]]] = {}
    delayed: dict[int, list[tuple[str, z3.BoolRef, z3.ArithRef]]] = {}
    for a in cm.actors:
        for x in a.actions:
            items = _effect_items(cm, x.effects)
            for item in items:
                if isinstance(item, _BumpItem):
                    if cm.variables[item.var].monotone and item.amount < 0:
                        out.append(
                            (f"{a.name}.{x.name} lowers a monotone variable", z3.BoolVal(True))
                        )
                    continue
                cond = z3.BoolVal(True) if item.cond is None else tr.boolean(item.cond, s)
                val = _value(enc, item, t)
                name = f"{a.name}.{x.name}"
                if x.delay:
                    due = z3.And(s[x.pending] == 1, cond)
                    delayed.setdefault(item.var, []).append((name, due, val))
                    when = due
                else:
                    when = z3.And(available(enc, t, a.name, x.name), cond)
                    immediate.setdefault(item.var, []).append((a.name, name, when, val))
                if cm.variables[item.var].monotone:
                    out.append(
                        (
                            f"{name} lowers {cm.variables[item.var].name}",
                            z3.And(when, val < s[item.var]),
                        )
                    )
    for v, items in immediate.items():
        for i, (a1, n1, w1, v1) in enumerate(items):
            for a2, n2, w2, v2 in items[i + 1 :]:
                if a1 != a2:
                    out.append(
                        (
                            f"{n1} and {n2} set {cm.variables[v].name} differently",
                            z3.And(w1, w2, v1 != v2),
                        )
                    )
    for v, items in delayed.items():
        for i, (n1, w1, v1) in enumerate(items):
            for n2, w2, v2 in items[i + 1 :]:
                out.append(
                    (
                        f"{n1} and {n2} (delayed) set {cm.variables[v].name} differently",
                        z3.And(w1, w2, v1 != v2),
                    )
                )
    return out


def wellformed_from(
    cm: CompiledModel, start: Sequence[int], k: int | None = None
) -> list[tuple[str, BmcTrace]]:
    """Every hazard of :func:`_hazards` reachable from ``start`` within ``k`` transitions
    (default: to the horizon, so every reachable state is covered), each with a shortest
    play to a state that has it; an empty list means that the explicit engine raises on no
    state reachable from ``start``. The encoding excludes the transitions on which the
    engine raises, so the first hazard on any play is found at its source state."""
    tick = start[cm.index["tick"]]
    k = cm.horizon - tick if k is None else k
    q = _QueryFrom(cm, start, k, terminal(cm))
    enc = q.enc
    found = []
    by_name: dict[str, list[z3.BoolRef]] = {}
    for t in range(k + 1):
        live = z3.And(enc.active[t], z3.Not(enc.terminal[t]))
        for name, cond in _hazards(enc, t):
            by_name.setdefault(name, []).append(z3.And(live, cond))
    base = enc.solver()
    base.add(*enc.assume.values())
    for name, conds in by_name.items():
        base.push()
        base.add(z3.Or(*conds))
        if _check(base) == z3.sat:
            model = base.model()
            last = next(
                t for t, c in enumerate(conds) if z3.is_true(model.eval(c, model_completion=True))
            )
            states, moves = enc.decode(model, last)
            found.append((name, BmcTrace(states, moves)))
        base.pop()
    return found


def avoid(expr: Any) -> Constrain:
    """A constraint: ``expr`` is false at every step of the play (an expression, or an
    ending or invariant name)."""

    def fn(enc: Encoding) -> list[z3.BoolRef]:
        return [z3.Implies(enc.active[t], z3.Not(enc.target(expr, t))) for t in range(enc.k + 1)]

    return fn


def strategies(fixed: dict[str, Priorities]) -> Constrain:
    """Every actor in ``fixed`` plays :func:`play` with its priority list."""

    def fn(enc: Encoding) -> list[z3.BoolRef]:
        return [c for actor, prio in fixed.items() for c in play(enc, actor, prio)]

    return fn


def forces(
    cm: CompiledModel,
    start: Sequence[int],
    target: Any,
    fixed: dict[str, Priorities],
    k: int | None = None,
) -> tuple[bool, BmcTrace | None]:
    """Whether the actors in ``fixed``, playing those strategies, force ``target`` from
    ``start`` within ``k`` transitions (default: to the horizon) against every play of the
    others: no play avoids the target until a terminal state or step ``k``. Returns
    ``(True, None)``, or ``(False, play)`` with an avoiding play (which shows only that this
    strategy does not force it)."""
    k = cm.horizon - start[cm.index["tick"]] if k is None else k
    end = terminal(cm) | (V.tick >= start[cm.index["tick"]] + k)
    trace = reach_from(cm, start, k, end, constrain=[strategies(fixed), avoid(target)])
    return trace is None, trace


def blocks(
    cm: CompiledModel,
    start: Sequence[int],
    target: Any,
    fixed: dict[str, Priorities],
    k: int | None = None,
) -> tuple[bool, BmcTrace | None]:
    """Whether the actors in ``fixed``, playing those strategies, keep ``target`` false from
    ``start`` for ``k`` transitions (default: to the horizon) against every play of the
    others. Returns ``(True, None)``, or ``(False, play)`` with a play reaching the target."""
    k = cm.horizon - start[cm.index["tick"]] if k is None else k
    trace = reach_from(cm, start, k, target, constrain=[strategies(fixed)])
    return trace is None, trace
