"""Bounded reachability and minimum relaxations over the Z3 encoding (spec section 6).

- :func:`reach`: a shortest trace of at most ``k`` transitions from an initial state to a
  state satisfying a target, with every named assumption asserted (or some relaxed).
- :func:`relax`: when the target is unreachable within ``k``, the unsat core over the
  assumption Bools, the minimum number of assumptions to relax (``z3.Optimize`` with one
  soft constraint per assumption), and every relaxation set of that size, enumerated with
  blocking clauses.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

import z3

from ..model.compile import CompiledModel
from ..model.model import ModelError
from .encode import Encoding, Target, encode

__all__ = ["BmcTrace", "RelaxResult", "reach", "relax"]


@dataclass
class BmcTrace:
    """A play found by the solver: ``states[0]`` is an initial state, ``moves[t]`` is the
    joint move (action indices, Nature last) from ``states[t]`` to ``states[t + 1]``, and
    the last state satisfies the target. ``relaxed`` lists the assumptions relaxed for it."""

    states: list[tuple[int, ...]]
    moves: list[tuple[int, ...]]
    relaxed: list[str] = field(default_factory=list)

    def __len__(self) -> int:
        """The number of transitions."""
        return len(self.moves)

    def render(self, cm: CompiledModel) -> str:
        """A Markdown table in the format of :meth:`wavefront.engine.Trace.render`: tick,
        each actor's action, and the variables that changed (level names; ``tick`` and
        ``last_*`` omitted). In an untimed model the first column is the step number."""
        names = cm.actor_names
        header = ["tick" if cm.timed else "step", *names, "changes"]
        rows = [header, ["---"] * len(header)]
        shown = [i for i, v in enumerate(cm.variables) if v.origin not in ("tick", "last")]
        for k, state in enumerate(self.states):
            tick = str(state[cm.index["tick"]]) if cm.timed else str(k)
            if k == len(self.moves):
                end = cm.ending_of(state)
                note = f"ending: {end}" if end is not None else "(trace ends)"
                rows.append([tick, *(["-"] * len(names)), note])
                continue
            nxt = self.states[k + 1]
            changes = [
                f"{cm.variables[i].name}: {cm.level_name(i, state[i])} -> "
                f"{cm.level_name(i, nxt[i])}"
                for i in shown
                if state[i] != nxt[i]
            ]
            move = [a.actions[j].name for a, j in zip(cm.actors, self.moves[k], strict=True)]
            rows.append([tick, *move, "; ".join(changes) or "-"])
        return "\n".join("| " + " | ".join(row) + " |" for row in rows)


@dataclass
class RelaxResult:
    """Outcome of :func:`relax`.

    - ``reachable_as_is``: the target is reachable within ``k`` with every assumption.
    - ``core``: assumption names in an unsat core (empty when reachable as is).
    - ``minimum_size``: the fewest assumptions whose relaxation makes the target reachable
      (0 when reachable as is; ``None`` when no set of at most ``max_relax`` works).
    - ``minimal_sets``: every relaxation set of minimum size, up to ``max_sets`` of them,
      each in :meth:`CompiledModel.assumptions` order.
    - ``trace``: a shortest trace under the first set (or with nothing relaxed).
    """

    reachable_as_is: bool
    core: list[str]
    minimum_size: int | None
    minimal_sets: list[list[str]]
    trace: BmcTrace | None


class _Query:
    """An encoding plus the goal "target holds at some active tick <= m" for every m."""

    def __init__(self, cm: CompiledModel, k: int, target: Target) -> None:
        self.enc: Encoding = encode(cm, k)
        enc = self.enc
        self.hit = [z3.And(enc.active[t], enc.target(target, t)) for t in range(k + 1)]
        self.by: list[z3.BoolRef] = [z3.Bool(f"reached_by@{t}") for t in range(k + 1)]
        self.goal: list[z3.BoolRef] = []
        for t in range(k + 1):
            earlier = [self.by[t - 1]] if t else []
            self.goal.append(z3.Implies(self.by[t], z3.Or(*earlier, self.hit[t])))

    def solver(self) -> z3.Solver:
        s = self.enc.solver()
        s.add(*self.goal)
        return s

    def literals(self, relaxed: frozenset[str]) -> list[z3.BoolRef]:
        """Each assumption Bool asserted, or negated when relaxed."""
        return [z3.Not(b) if n in relaxed else b for n, b in self.enc.assume.items()]

    def first_hit(self, model: z3.ModelRef) -> int:
        for t, h in enumerate(self.hit):
            if z3.is_true(model.eval(h, model_completion=True)):
                return t
        raise AssertionError("model does not reach the target")

    def shortest(
        self, solver: z3.Solver, lits: list[z3.BoolRef], relaxed: list[str]
    ) -> BmcTrace | None:
        """A shortest trace under ``lits``, by binary search over the goal depth."""
        if _check(solver, *lits, self.by[self.enc.k]) != z3.sat:
            return None
        model = solver.model()
        hi = self.first_hit(model)
        lo = 0
        while lo < hi:
            mid = (lo + hi) // 2
            if _check(solver, *lits, self.by[mid]) == z3.sat:
                model = solver.model()
                hi = self.first_hit(model)
            else:
                lo = mid + 1
        states, moves = self.enc.decode(model, hi)
        return BmcTrace(states, moves, relaxed)


def _check(solver: z3.Solver | z3.Optimize, *assumptions: z3.BoolRef) -> z3.CheckSatResult:
    result = solver.check(*assumptions)
    if result == z3.unknown:
        raise RuntimeError(f"z3 returned unknown: {solver.reason_unknown()}")
    return result


def _relax_names(cm: CompiledModel, relax: Iterable[str]) -> frozenset[str]:
    """Validate relaxation names; trivial guards and unselected profiles are no-ops."""
    names = frozenset((relax,) if isinstance(relax, str) else relax)
    m = cm.model
    known = set(cm.assumptions())
    known |= {f"{a.name}.{x.name}" for a in [*m.actors, m.nature()] for x in a.actions}
    known |= {p.name for p in m.profiles}
    unknown = sorted(names - known)
    if unknown:
        raise ModelError(f"model {cm.name!r}: cannot relax unknown assumption(s) {unknown}")
    return names


def reach(
    cm: CompiledModel,
    k: int,
    target: Target,
    relax: Iterable[str] = frozenset(),
) -> BmcTrace | None:
    """A shortest trace of at most ``k`` transitions from an initial state to a state
    satisfying ``target`` (an ending name, ``"HORIZON"``, an invariant name or a condition
    expression), with every named assumption asserted except those in ``relax``; ``None``
    if there is none."""
    relaxed = _relax_names(cm, relax)
    q = _Query(cm, k, target)
    order = [n for n in q.enc.assume if n in relaxed]
    return q.shortest(q.solver(), q.literals(relaxed), order)


def relax(
    cm: CompiledModel,
    k: int,
    target: Target,
    max_relax: int = 3,
    max_sets: int = 20,
) -> RelaxResult:
    """Minimum-cardinality relaxations of the named assumptions that make ``target``
    reachable within ``k`` transitions (see :class:`RelaxResult`)."""
    q = _Query(cm, k, target)
    enc = q.enc
    bools = enc.assume
    names_of = {b.get_id(): n for n, b in bools.items()}
    goal = q.by[k]

    solver = q.solver()
    solver.set("core.minimize", True)
    if _check(solver, *bools.values(), goal) == z3.sat:
        trace = q.shortest(solver, q.literals(frozenset()), [])
        return RelaxResult(True, [], 0, [[]], trace)
    core_ids = {c.get_id() for c in solver.unsat_core()}
    core = [n for n, b in bools.items() if b.get_id() in core_ids]

    relaxed_count = [z3.Not(b) for b in bools.values()]
    opt = z3.Optimize()
    opt.add(*enc.constraints, *q.goal, goal)
    if relaxed_count:
        opt.add(z3.AtMost(*relaxed_count, max_relax))
    for b in bools.values():
        opt.add_soft(b, 1)
    if not bools or _check(opt) == z3.unsat:
        return RelaxResult(False, core, None, [], None)
    model = opt.model()
    size = sum(1 for b in bools.values() if z3.is_false(model.eval(b, model_completion=True)))

    enum = q.solver()
    enum.add(goal, z3.AtMost(*relaxed_count, size))
    found: list[list[str]] = []
    while len(found) < max_sets and _check(enum) == z3.sat:
        model = enum.model()
        chosen = [b for b in bools.values() if z3.is_false(model.eval(b, model_completion=True))]
        found.append([names_of[b.get_id()] for b in chosen])
        enum.add(z3.Or(*chosen))
    trace = reach(cm, k, target, relax=found[0])
    return RelaxResult(False, core, size, found, trace)
