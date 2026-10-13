"""Multi-resolution time: crisis sub-games flattened into one game (theory.md section 7,
spec section 14).

A *coarse* compiled model (annual ticks, say) gets one or more :class:`Crisis` sub-games: a
declared coarse action with no state effect (the crisis move) stands for playing a *fine*
compiled model (daily ticks, say) from an entry state computed from the coarse state, and
the fine model's terminal states map back to coarse states. :func:`flatten` builds the
flattened game of theory section 7 as a :class:`FlatModel`, which duck-types
:class:`~wavefront.model.compile.CompiledModel`, so :func:`~wavefront.engine.explore`, the
solvers, witnesses and the analysis functions that take a graph run on it unchanged.

State encoding (all states are tuples of small integers, hence hashable):

- a coarse state is the coarse model's own state tuple, unchanged (length ``n``, the
  number of coarse variables), so coarse states of the flattening and of the coarse model
  compare equal and explicit initial states are given as coarse states;
- a fine state is ``s + (k,) + h``: the coarse state ``s`` the crisis was entered from
  (frozen during the crisis), the crisis index ``k`` and the fine model's state ``h``.

Semantics (the rules spec section 14 states):

1. *Entry.* In a coarse state, a joint move in which an actor plays a crisis action leads
   to the fine initial state ``s + (k,) + iota(s)``, whatever the other actors chose (their
   choices are discarded; the coarse tick does not advance). Two crisis actions in one joint
   move are a :class:`ModelError`.
2. *Inside.* In a fine state whose fine part is not terminal, the moves are the fine
   model's and the successor is the fine model's ``step``. Coarse actors that are not fine
   actors play their built-in ``idle`` (``none`` for Nature; a synthetic ``idle`` if the
   actor was declared with ``idle=False``). The coarse part stays frozen: delay counters,
   latches, fairness counters and ``last_<actor>`` of the coarse model do not move.
3. *Return.* A fine state whose fine part is terminal (fine horizon or fine ending) has
   exactly one joint move: the crisis actor plays the crisis action, every other actor its
   built-in ``idle``/``none``. Its successor is one coarse transition from the entered-from
   state ``s`` in which the only immediate effects are the exit levels
   ``lambda(h, s)``: the tick advances by one, and delays, latches, fairness counters and
   ``last_<actor>`` update as in any coarse transition with that joint move (a delayed
   effect falling due in that tick still fires, and a delayed ``Set`` overrides an exit
   level as it would override an immediate ``Set``). The whole crisis fits inside one
   coarse tick.
4. *Predicates.* Coarse invariants and endings are evaluated on coarse states. On a fine
   state every coarse invariant holds and no coarse ending holds; the fine state is never
   terminal in the flattening (a fine ending only ends the sub-game and triggers the
   return). Ad-hoc expressions (``compile_expr``, ``evaluate``, ``Graph.states_where``
   with an expression or a Python predicate) read the frozen coarse state on fine states.
5. *Actors.* Every fine actor (Nature included) must be a coarse actor of the same name,
   so that a coalition means the same players at both levels.

Ranks and witness lengths on the flattening count its transitions: a crisis costs its
entry, its fine steps and its return, while the coarse tick advances by one.
"""

from __future__ import annotations

import dataclasses
import itertools
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ..model.compile import ActionSpec, ActorSpec, CompiledModel, VarSpec
from ..model.expr import TRUE, Expr
from ..model.model import ModelError

__all__ = ["Crisis", "FlatModel", "flatten"]

State = tuple[int, ...]
EntryMap = Callable[[dict[str, str]], Mapping[str, object]]
ExitMap = Callable[[dict[str, str], dict[str, str]], Mapping[str, object]]


@dataclass(frozen=True, eq=False)
class Crisis:
    """A crisis sub-game attached to a coarse action.

    - ``actor``, ``action``: a declared action of the coarse model with no effect and no
      delay; choosing it enters the crisis.
    - ``sub``: the fine compiled model (timed, with its own horizon and endings).
    - ``entry(coarse_state_dict) -> {fine variable: value}``: the fine initial values of
      the variables it names (values are level names, counter integers or booleans; the
      strings of ``state_dict`` are accepted). Every other fine variable takes its declared
      initial value; a swept fine variable (``init=None``) must be named.
    - ``exit(fine_state_dict, coarse_state_dict) -> {coarse variable: value}``: called on a
      terminal fine state with the coarse state the crisis was entered from; the levels of
      the coarse variables the crisis changes. Unnamed coarse variables keep their values.
    - ``name``: the crisis's label in states and messages (default: ``action``).
    """

    actor: str
    action: str
    sub: CompiledModel
    entry: EntryMap
    exit: ExitMap
    name: str | None = None

    @property
    def label(self) -> str:
        """The crisis's name in states and messages."""
        return self.name or self.action


def _resolve(spec: VarSpec, value: object, where: str) -> int:
    """A level name, counter integer or boolean as a value index of ``spec``."""
    if isinstance(value, bool):
        idx = int(value) if spec.kind == "flag" else -1
    elif isinstance(value, int):
        idx = value if spec.kind == "counter" else -1
    elif isinstance(value, str) and value in spec.levels:
        idx = spec.levels.index(value)
    else:
        idx = -1
    if not 0 <= idx < spec.size:
        raise ModelError(
            f"{where} gives {spec.name}={value!r}, which is not a value of {spec.name!r} "
            f"(levels: {', '.join(spec.levels)})"
        )
    return idx


@dataclass
class _Compiled:
    """Per-crisis lookups computed once by :class:`FlatModel`."""

    crisis: Crisis
    actor: int  # coarse actor index of the crisis actor
    action: int  # its action index
    layout: list[tuple[int, int]]  # per fine actor: (flat actor index, action offset)
    ret_move: tuple[int, ...]  # the flat joint move of the return transition
    ret_coarse: tuple[int, ...]  # the same move as coarse action indices (-1: no action)


class FlatModel:
    """The flattened game of a coarse model and its crisis sub-games (see the module
    docstring for the state encoding and the semantics). Built by :func:`flatten`.

    Attributes not defined here (``model``, ``assumptions``, ``initial_states``,
    ``level_name``, ``assume_fns``, ...) are the coarse model's: ``initial_states()``
    returns coarse states, and ``variables`` and ``index`` describe the coarse part of
    every state. The named assumptions are the coarse model's; relaxing a fine model's
    assumption means compiling that fine model with ``relax=`` and flattening again."""

    def __init__(self, coarse: CompiledModel, crises: Iterable[Crisis]) -> None:
        self.coarse = coarse
        self.crises = tuple(crises)
        self.n = len(coarse.variables)
        self.name = "+".join([coarse.name, *(c.label for c in self.crises)])
        self.variables = coarse.variables
        self.index = coarse.index
        self.horizon = coarse.horizon
        self.timed = coarse.timed
        self._validate()
        self.actors, self._wait = self._build_actors()
        self._compiled = [self._compile_crisis(c) for c in self.crises]
        self._crisis_at = {(c.actor, c.action): k for k, c in enumerate(self._compiled)}
        self.invariant_fns = {
            name: self._on_coarse(fn, True) for name, fn in coarse.invariant_fns.items()
        }
        self.ending_fns = {
            name: self._on_coarse(fn, False) for name, fn in coarse.ending_fns.items()
        }

    # -- construction ------------------------------------------------------------------
    def __getattr__(self, name: str) -> Any:
        if name == "coarse":  # not yet set: avoid infinite recursion during __init__
            raise AttributeError(name)
        return getattr(self.coarse, name)

    def _validate(self) -> None:
        coarse = self.coarse
        names = {a.name: a for a in coarse.actors}
        seen_labels: set[str] = set()
        seen_actions: set[tuple[str, str]] = set()
        for c in self.crises:
            where = f"crisis {c.label!r}"
            if not isinstance(c.sub, CompiledModel):
                raise ModelError(f"{where}: sub must be a compiled model, not {c.sub!r}")
            if c.label in seen_labels:
                raise ModelError(f"{where}: two crises share this name")
            seen_labels.add(c.label)
            if (c.actor, c.action) in seen_actions:
                raise ModelError(f"{where}: {c.actor}.{c.action} already enters another crisis")
            seen_actions.add((c.actor, c.action))
            actor = names.get(c.actor)
            if actor is None:
                raise ModelError(f"{where}: {c.actor!r} is not an actor of {coarse.name!r}")
            spec = next((a for a in actor.actions if a.name == c.action), None)
            if spec is None or spec.is_idle:
                raise ModelError(
                    f"{where}: {c.actor}.{c.action} is not a declared action of {coarse.name!r}"
                )
            if spec.effects or spec.delay:
                raise ModelError(
                    f"{where}: the crisis action {c.actor}.{c.action} must have no effect and "
                    "no delay (its effect is the sub-game's exit map)"
                )
            if not c.sub.timed:
                raise ModelError(
                    f"{where}: the sub-game {c.sub.name!r} must be timed, so that every crisis "
                    "ends within one coarse tick"
                )
            for fine in c.sub.actors:
                if fine.name not in names:
                    raise ModelError(
                        f"{where}: actor {fine.name!r} of the sub-game {c.sub.name!r} is not an "
                        f"actor of {coarse.name!r}; fine actors must be coarse actors of the "
                        "same name so that coalitions mean the same at both levels"
                    )

    def _build_actors(self) -> tuple[list[ActorSpec], list[int]]:
        """Flat actors: each coarse actor's actions (same indices), then a synthetic
        ``idle`` if the actor has no built-in one, then each crisis's fine actions."""
        actors: list[ActorSpec] = []
        wait: list[int] = []
        for actor in self.coarse.actors:
            actions = list(actor.actions)
            if actions[0].is_idle:
                wait.append(0)
            else:
                wait.append(len(actions))
                idle = ActionSpec(
                    name="idle",
                    actor=actor.name,
                    index=len(actions),
                    guard=lambda s: True,
                    effects=(),
                    delay=0,
                    source="",
                    speculative=False,
                    is_idle=True,
                    guard_expr=TRUE,
                )
                actions.append(idle)
            actors.append(dataclasses.replace(actor, actions=actions))
        return actors, wait

    def _compile_crisis(self, c: Crisis) -> _Compiled:
        by_name = {a.name: a for a in self.actors}
        layout = []
        for fine in c.sub.actors:
            flat = by_name[fine.name]
            offset = len(flat.actions)
            flat.actions.extend(
                dataclasses.replace(spec, index=offset + spec.index) for spec in fine.actions
            )
            layout.append((flat.index, offset))
        actor = by_name[c.actor]
        action = actor.action_index(c.action)
        ret_move = tuple(
            action if a.index == actor.index else self._wait[a.index] for a in self.actors
        )
        ret_coarse = tuple(
            j if j < len(a.actions) else -1
            for a, j in zip(self.coarse.actors, ret_move, strict=True)
        )
        return _Compiled(c, actor.index, action, layout, ret_move, ret_coarse)

    def _on_coarse(self, fn: Callable[[Sequence[int]], Any], on_fine: bool) -> Callable:
        n = self.n

        def wrapped(state: Sequence[int]) -> Any:
            return fn(state) if len(state) == n else on_fine

        return wrapped

    # -- encoding ----------------------------------------------------------------------
    def is_fine(self, state: Sequence[int]) -> bool:
        """True for a state inside a crisis."""
        return len(state) > self.n

    def split(self, state: Sequence[int]) -> tuple[State, Crisis | None, State | None]:
        """``(coarse part, crisis, fine part)``; the last two are ``None`` on a coarse
        state. On a fine state the coarse part is the state the crisis was entered from."""
        n = self.n
        if len(state) == n:
            return tuple(state), None, None
        return tuple(state[:n]), self.crises[state[n]], tuple(state[n + 1 :])

    def coarse_part(self, state: Sequence[int]) -> State:
        """The coarse state (the entered-from state on a fine state)."""
        return tuple(state[: self.n])

    # -- transitions -------------------------------------------------------------------
    def _context(self, k: int, s: Sequence[int]) -> str:
        return f"crisis {self.crises[k].label!r} entered from {self.coarse.format_state(s)}"

    def _enter(self, k: int, s: State) -> State:
        """``s + (k,) + iota(s)``."""
        c = self.crises[k]
        sub = c.sub
        where = f"{self._context(k, s)}: the entry map"
        values = c.entry(dict(self.coarse.state_dict(s)))
        if not isinstance(values, Mapping):
            raise ModelError(f"{where} must return a mapping, not {values!r}")
        fine = [v.init[0] for v in sub.variables]
        for name, value in values.items():
            i = sub.index.get(name)
            if i is None or sub.variables[i].origin != "var":
                raise ModelError(
                    f"{where} names {name!r}, which is not a declared variable of the "
                    f"sub-game {sub.name!r}"
                )
            fine[i] = _resolve(sub.variables[i], value, where)
        for i, v in enumerate(sub.variables):
            if len(v.init) > 1 and v.name not in values:
                raise ModelError(
                    f"{where} does not fix {v.name!r}, which the sub-game {sub.name!r} sweeps "
                    "(init=None); a crisis must start from one state"
                )
        for idx, src, when in sub._latches:
            if fine[idx] == 0 and when(fine):
                fine[idx] = fine[src] + 1
        for name, fn in sub.assume_fns.items():
            if not fn(fine):
                raise ModelError(
                    f"{self._context(k, s)}: the entry state {sub.format_state(fine)} violates "
                    f"the sub-game's assumption {name!r}"
                )
        return (*s, k, *fine)

    def _return(self, k: int, s: State, h: State) -> State:
        """One coarse transition from ``s`` whose only immediate effects are the exit
        levels ``lambda(h, s)``."""
        c = self.crises[k]
        coarse = self.coarse
        where = f"{self._context(k, s)}: the exit map"
        values = c.exit(dict(c.sub.state_dict(h)), dict(coarse.state_dict(s)))
        if not isinstance(values, Mapping):
            raise ModelError(f"{where} must return a mapping, not {values!r}")
        sets = []
        for name, value in values.items():
            i = coarse.index.get(name)
            if i is None or coarse.variables[i].origin != "var":
                raise ModelError(
                    f"{where} names {name!r}, which is not a declared variable of {coarse.name!r}"
                )
            spec = coarse.variables[i]
            x = _resolve(spec, value, where)
            if spec.monotone and x < s[i]:
                raise ModelError(
                    f"{where} lowers monotone variable {name!r} from "
                    f"{spec.levels[s[i]]} to {spec.levels[x]}"
                )
            sets.append((i, x))
        contribs = [(tuple(sets), ())] if sets else []
        return coarse._successor(s, self._compiled[k].ret_coarse, contribs)

    def _crisis_in(self, s: Sequence[int], jm: Sequence[int]) -> int | None:
        at = self._crisis_at
        hits = [at[(i, j)] for i, j in enumerate(jm) if (i, j) in at]
        if not hits:
            return None
        if len(hits) > 1:
            names = ", ".join(repr(self.crises[k].label) for k in hits)
            raise ModelError(
                f"crises {names} are entered together in state {self.coarse.format_state(s)} "
                f"under joint move {self.format_move(jm)}; a joint move may enter at most "
                "one crisis"
            )
        return hits[0]

    def available(self, state: Sequence[int]) -> list[list[int]]:
        """Per actor, the available flat action indices (see the module docstring)."""
        n = self.n
        if len(state) == n:
            return self.coarse.available(state)
        k = state[n]
        comp = self._compiled[k]
        sub = comp.crisis.sub
        h = state[n + 1 :]
        if sub.is_terminal(h):
            return [[j] for j in comp.ret_move]
        try:
            fav = sub.available(h)
        except ModelError as exc:
            raise ModelError(f"{self._context(k, state[:n])}: {exc}") from None
        out = [[w] for w in self._wait]
        for (i, offset), acts in zip(comp.layout, fav, strict=True):
            out[i] = [offset + j for j in acts]
        return out

    def step(self, state: Sequence[int], joint_move: Sequence[int]) -> State:
        """The successor of a flat state under a flat joint move."""
        state, jm = tuple(state), tuple(joint_move)
        if len(jm) != len(self.actors):
            raise ModelError(f"joint move {jm} needs {len(self.actors)} entries")
        n = self.n
        if len(state) == n:
            k = self._crisis_in(state, jm)
            return self.coarse.step(state, jm) if k is None else self._enter(k, state)
        k = state[n]
        comp = self._compiled[k]
        s, h = state[:n], state[n + 1 :]
        if comp.crisis.sub.is_terminal(h):
            return self._return(k, s, h)
        fine_jm = tuple(jm[i] - offset for i, offset in comp.layout)
        try:
            return (*s, k, *comp.crisis.sub.step(h, fine_jm))
        except ModelError as exc:
            raise ModelError(f"{self._context(k, s)}: {exc}") from None

    def successors(
        self, state: State, avail: list[list[int]], moves: Iterable[tuple[int, ...]]
    ) -> list[State]:
        """Successors of ``state`` for ``moves`` (``product(*avail)`` in order), as
        :meth:`CompiledModel.successors`."""
        n = self.n
        moves = list(moves)
        if len(state) == n:
            return self._coarse_successors(state, avail, moves)
        k = state[n]
        comp = self._compiled[k]
        sub = comp.crisis.sub
        s, h = state[:n], state[n + 1 :]
        if sub.is_terminal(h):
            return [self._return(k, s, h)] * len(moves)
        fine_avail = [[j - offset for j in avail[i]] for i, offset in comp.layout]
        fine_moves = list(itertools.product(*fine_avail))
        try:
            table = dict(zip(fine_moves, sub.successors(h, fine_avail, fine_moves), strict=True))
        except ModelError as exc:
            raise ModelError(f"{self._context(k, s)}: {exc}") from None
        layout = comp.layout
        return [(*s, k, *table[tuple(jm[i] - off for i, off in layout)]) for jm in moves]

    def _coarse_successors(
        self, state: State, avail: list[list[int]], moves: list[tuple[int, ...]]
    ) -> list[State]:
        at = self._crisis_at
        if not any((i, j) in at for i, acts in enumerate(avail) for j in acts):
            return self.coarse.successors(state, avail, moves)
        plain = [[j for j in acts if (i, j) not in at] for i, acts in enumerate(avail)]
        table: dict[tuple[int, ...], State] = {}
        if all(plain):
            plain_moves = list(itertools.product(*plain))
            table = dict(
                zip(plain_moves, self.coarse.successors(state, plain, plain_moves), strict=True)
            )
        entered: dict[int, State] = {}
        out = []
        for jm in moves:
            k = self._crisis_in(state, jm)
            if k is None:
                out.append(table[jm])
            else:
                if k not in entered:
                    entered[k] = self._enter(k, state)
                out.append(entered[k])
        return out

    # -- predicates --------------------------------------------------------------------
    def is_terminal(self, state: Sequence[int]) -> bool:
        """Coarse terminal states only; a fine state is never terminal."""
        return len(state) == self.n and self.coarse.is_terminal(state)

    def ending_of(self, state: Sequence[int]) -> str | None:
        """The coarse ending (or ``HORIZON``) of a coarse state; ``None`` on fine states."""
        return self.coarse.ending_of(state) if len(state) == self.n else None

    def fine_ending_of(self, state: Sequence[int]) -> str | None:
        """The sub-game's ending (or ``HORIZON``) of a fine state; ``None`` otherwise."""
        _, c, h = self.split(state)
        return None if c is None else c.sub.ending_of(h)

    def compile_expr(self, expr: Expr) -> Callable[[Sequence[int]], Any]:
        """An ad-hoc coarse expression; on a fine state it reads the frozen coarse state."""
        fn = self.coarse.compile_expr(expr)
        n = self.n

        def wrapped(state: Sequence[int]) -> Any:
            return fn(state if len(state) == n else state[:n])

        return wrapped

    def evaluate(self, expr_or_name: Expr | str, state: Sequence[int]) -> bool | int:
        """A named coarse invariant or ending (rule 4 of the module docstring), or an
        expression read on the coarse part of the state."""
        if isinstance(expr_or_name, str):
            if expr_or_name in self.invariant_fns:
                return bool(self.invariant_fns[expr_or_name](state))
            if expr_or_name in self.ending_fns:
                return bool(self.ending_fns[expr_or_name](state))
            raise ModelError(f"no invariant or ending named {expr_or_name!r}")
        return self.coarse.evaluate(expr_or_name, self.coarse_part(state))

    def observe(self, actor_name: str, state: Sequence[int]) -> tuple:
        """On a coarse state, the coarse observation. On a fine state, the crisis's name,
        the observation of the frozen coarse state and, for a fine actor, its fine
        observation (so a coarse and a fine state never look alike)."""
        s, c, h = self.split(state)
        if c is None:
            return self.coarse.observe(actor_name, s)
        view: tuple = (c.label, self.coarse.observe(actor_name, s))
        if any(a.name == actor_name for a in c.sub.actors):
            view += (c.sub.observe(actor_name, h),)
        return view

    # -- rendering ---------------------------------------------------------------------
    @property
    def actor_names(self) -> list[str]:
        """Actor names in joint-move order (Nature last), as in the coarse model."""
        return [a.name for a in self.actors]

    def state_dict(self, state: Sequence[int]) -> dict[str, str]:
        """``{variable: level name}``; on a fine state the coarse variables (frozen) and the
        fine ones as ``<crisis>.<variable>``."""
        s, c, h = self.split(state)
        out = self.coarse.state_dict(s)
        if c is not None:
            out.update({f"{c.label}.{k}": v for k, v in c.sub.state_dict(h).items()})
        return out

    def format_state(self, state: Sequence[int]) -> str:
        """A coarse state as the coarse model prints it; a fine state as
        ``[crisis <name> from {coarse state}] {fine state}``."""
        s, c, h = self.split(state)
        if c is None:
            return self.coarse.format_state(s)
        return f"[crisis {c.label} from {self.coarse.format_state(s)}] {c.sub.format_state(h)}"

    def format_move(self, joint_move: Sequence[int]) -> str:
        """A flat joint move as ``A.action, B.idle, Nature.none``."""
        return ", ".join(
            f"{a.name}.{a.actions[j].name}" for a, j in zip(self.actors, joint_move, strict=True)
        )

    def trace_tick(self, state: Sequence[int], step: int) -> str:
        """The first column of :meth:`Trace.render`: the coarse tick (step number in an
        untimed coarse model), and on a fine state the crisis and its fine tick."""
        s, c, h = self.split(state)
        base = str(s[self.index["tick"]]) if self.timed else str(step)
        if c is None:
            return base
        return f"{base} [{c.label} {h[c.sub.index['tick']]}]"

    def trace_changes(self, state: Sequence[int], nxt: Sequence[int]) -> list[str]:
        """The changes column of :meth:`Trace.render` for one transition: coarse changes,
        the fine entry state, fine changes (as ``<crisis>.<variable>``) or the return."""
        s, c, h = self.split(state)
        t, d, e = self.split(nxt)
        if c is None and d is None:
            return _changes(self.coarse, s, t)
        if c is None:
            assert d is not None and e is not None
            shown = [i for i, v in enumerate(d.sub.variables) if v.origin == "var"]
            start = ", ".join(
                f"{d.sub.variables[i].name}={d.sub.level_name(i, e[i])}" for i in shown
            )
            return [f"enter crisis {d.label} ({start})"]
        if d is None:
            return [f"return from crisis {c.label}", *_changes(self.coarse, s, t)]
        assert h is not None and e is not None
        return [f"{c.label}.{x}" for x in _changes(c.sub, h, e)]

    def budget(self) -> dict[str, int]:
        """The coarse model's budget plus the crises: their number and the summed
        variables, actions, guards and speculative actions of the sub-games;
        ``state_space_bound`` covers the fine states."""
        out = dict(self.coarse.budget())
        fine = [c.sub.budget() for c in self.crises]
        out["crises"] = len(self.crises)
        for key in ("variables", "actions", "guards", "speculative_actions"):
            out[f"crisis_{key}"] = sum(b[key] for b in fine)
        out["state_space_bound"] = out["state_space_bound"] * (
            1 + sum(b["state_space_bound"] for b in fine)
        )
        return out

    def __repr__(self) -> str:
        labels = ", ".join(c.label for c in self.crises)
        return f"FlatModel({self.coarse.name!r}, crises: {labels})"


def _changes(cm: CompiledModel, s: Sequence[int], t: Sequence[int]) -> list[str]:
    """Variables that differ between two states of ``cm`` (``tick`` and ``last_*``
    omitted), as :meth:`Trace.render` prints them."""
    return [
        f"{v.name}: {cm.level_name(i, s[i])} -> {cm.level_name(i, t[i])}"
        for i, v in enumerate(cm.variables)
        if v.origin not in ("tick", "last") and s[i] != t[i]
    ]


def flatten(coarse: CompiledModel, crises: Iterable[Crisis]) -> FlatModel:
    """The flattened game of ``coarse`` with ``crises`` (theory.md section 7, spec section
    14). The result can be passed to :func:`~wavefront.engine.explore` and everything that
    takes its graph. Raises :class:`ModelError` for an unknown crisis actor or action, a
    crisis action with an effect or a delay, an untimed sub-game, a fine actor that is not
    a coarse actor, or two crises on one action; entry and exit maps are checked when they
    are applied (unknown variables, values out of range, an unfixed swept fine variable,
    a monotone coarse variable lowered)."""
    return FlatModel(coarse, crises)
