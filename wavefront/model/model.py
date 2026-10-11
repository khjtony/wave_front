"""Model declarations: variables, actors, actions, latches, fairness, profiles, predicates.

A :class:`Model` only records declarations and checks what can be checked locally (names,
levels, initial values, argument types). Cross-references (levels used in expressions,
observation sets, effect targets, response actions) are checked by
:func:`wavefront.model.compile.compile`, which turns a model into a
:class:`~wavefront.model.compile.CompiledModel`.
"""

from __future__ import annotations

import keyword
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .effects import Bump, Set, SetIf
from .expr import FALSE, TRUE, Expr, Observes, V, lift_bool

if TYPE_CHECKING:
    from .compile import CompiledModel

__all__ = [
    "ModelError",
    "Model",
    "Actor",
    "VarDecl",
    "ActionDecl",
    "LatchDecl",
    "FairnessDecl",
    "ProfileDecl",
    "NATURE",
    "IDLE",
    "NONE",
]

NATURE = "Nature"
IDLE = "idle"
NONE = "none"
RESERVED_NAMES = frozenset({"tick", NATURE}) | V.RESERVED
RESERVED_PREFIXES = ("last_", "pending_", "fair_")


class ModelError(ValueError):
    """An error in a model, raised at declaration, compile or explore time."""


@dataclass(frozen=True)
class VarDecl:
    """A declared variable. ``init`` is a level index or ``None`` (every level)."""

    name: str
    kind: str  # 'level' | 'counter' | 'flag'
    levels: tuple[str, ...]
    init: int | None
    monotone: bool = False
    hidden_from: tuple[str, ...] = ()


@dataclass(frozen=True, eq=False)
class ActionDecl:
    """A declared action (or Nature event) of one actor."""

    actor: str
    name: str
    guard: Expr
    effects: tuple[Set | Bump | SetIf, ...]
    delay: int = 0
    source: str = ""
    speculative: bool = False


@dataclass(frozen=True, eq=False)
class LatchDecl:
    """``latch(name, of, when)``: freezes the value of ``of`` when ``when`` first holds."""

    name: str
    of: str
    when: Expr


@dataclass(frozen=True, eq=False)
class FairnessDecl:
    """Bounded fairness: ``actor`` must respond within ``within`` ticks of ``trigger``."""

    name: str
    actor: str
    trigger: Expr
    within: int
    responses: tuple[str, ...]


@dataclass(frozen=True, eq=False)
class ProfileDecl:
    """Behavioral profile: ``forbid`` is unavailable to ``actor`` unless ``unless`` holds."""

    name: str
    actor: str
    forbid: tuple[str, ...]
    unless: Expr


def check_identifier(name: object, what: str) -> str:
    """Raise :class:`ModelError` unless ``name`` is a usable identifier."""
    if not isinstance(name, str) or not name.isidentifier() or keyword.iskeyword(name):
        raise ModelError(f"{what} name {name!r} is not a Python identifier")
    return name


@dataclass(eq=False)
class Actor:
    """A player. Create with :meth:`Model.actor` or :meth:`Model.nature`."""

    model: Model
    name: str
    observes: Observes
    remember_last: bool = False
    idle: bool = True
    is_nature: bool = False
    actions: list[ActionDecl] = field(default_factory=list)

    def action(
        self,
        name: str,
        guard: Expr | bool = TRUE,
        effect: Set | Bump | SetIf | Iterable[Set | Bump | SetIf] | None = None,
        delay: int = 0,
        source: str = "",
        speculative: bool = False,
    ) -> ActionDecl:
        """Declare an action. ``effect`` is one effect or a list; ``delay=d`` applies the
        effect ``d`` ticks later (see spec 3.1)."""
        check_identifier(name, f"action of {self.name}")
        if name in (IDLE, NONE):
            raise ModelError(f"action name {name!r} is reserved for the built-in action")
        if any(a.name == name for a in self.actions):
            raise ModelError(f"duplicate action name {name!r} for actor {self.name}")
        if isinstance(delay, bool) or not isinstance(delay, int) or delay < 0:
            raise ModelError(f"action {self.name}.{name}: delay must be an int >= 0")
        decl = ActionDecl(
            actor=self.name,
            name=name,
            guard=lift_bool(guard),
            effects=_effect_tuple(effect, f"{self.name}.{name}"),
            delay=delay,
            source=str(source),
            speculative=bool(speculative),
        )
        self.actions.append(decl)
        return decl

    def event(
        self,
        name: str,
        guard: Expr | bool = TRUE,
        effect: Set | Bump | SetIf | Iterable[Set | Bump | SetIf] | None = None,
        delay: int = 0,
        source: str = "",
        speculative: bool = False,
    ) -> ActionDecl:
        """Alias of :meth:`action`, used for Nature's events."""
        return self.action(name, guard, effect, delay, source, speculative)


def _effect_tuple(effect: object, where: str) -> tuple[Set | Bump | SetIf, ...]:
    if effect is None:
        return ()
    items = (effect,) if isinstance(effect, Set | Bump | SetIf) else tuple(effect)  # type: ignore[arg-type]
    for item in items:
        if not isinstance(item, Set | Bump | SetIf):
            raise ModelError(f"action {where}: {item!r} is not an effect")
    return items


class Model:
    """A finite concurrent game under construction. See spec section 3.1."""

    def __init__(self, name: str, horizon: int, description: str = "") -> None:
        if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon < 1:
            raise ModelError(f"model {name!r}: horizon must be an int >= 1")
        self.name = name
        self.horizon = horizon
        self.description = description
        self.variables: list[VarDecl | LatchDecl] = []
        self.actors: list[Actor] = []
        self.latches: list[LatchDecl] = []
        self.fairness_constraints: list[FairnessDecl] = []
        self.profiles: list[ProfileDecl] = []
        self.invariants: dict[str, Expr] = {}
        self.endings: dict[str, Expr] = {}
        self._nature: Actor | None = None
        self._names: dict[str, str] = {}

    # -- names -------------------------------------------------------------------------
    def _claim(self, name: str, what: str) -> str:
        check_identifier(name, what)
        if name in RESERVED_NAMES or name.startswith(RESERVED_PREFIXES):
            raise ModelError(f"{what} name {name!r} is reserved")
        if name in self._names:
            raise ModelError(f"duplicate name {name!r}: already used by a {self._names[name]}")
        self._names[name] = what
        return name

    # -- variables ---------------------------------------------------------------------
    def var(
        self,
        name: str,
        levels: Sequence[str],
        init: str | None = ...,  # type: ignore[assignment]
        monotone: bool = False,
        hidden_from: Iterable[str] = (),
    ) -> VarDecl:
        """Declare a leveled variable. ``init`` defaults to the first level; ``None``
        means every level is an initial value."""
        levels = tuple(levels)
        if len(levels) < 2:
            raise ModelError(f"variable {name!r} needs at least two levels")
        for level in levels:
            if not isinstance(level, str) or not level:
                raise ModelError(f"variable {name!r}: level {level!r} is not a non-empty string")
        if len(set(levels)) != len(levels):
            raise ModelError(f"variable {name!r} has duplicate levels")
        if init is ...:
            init = levels[0]
        index = None if init is None else _level_index(name, levels, init)
        return self._add_var(name, "level", levels, index, monotone, hidden_from)

    def counter(
        self,
        name: str,
        max: int,
        init: int | None = 0,
        monotone: bool = False,
        hidden_from: Iterable[str] = (),
    ) -> VarDecl:
        """Declare an integer counter ``0..max``."""
        if isinstance(max, bool) or not isinstance(max, int) or max < 1:
            raise ModelError(f"counter {name!r}: max must be an int >= 1")
        levels = tuple(str(i) for i in range(max + 1))
        if init is not None and (isinstance(init, bool) or init not in range(max + 1)):
            raise ModelError(f"counter {name!r}: init {init!r} is not in 0..{max}")
        return self._add_var(name, "counter", levels, init, monotone, hidden_from)

    def flag(
        self,
        name: str,
        init: bool | None = False,
        monotone: bool = False,
        hidden_from: Iterable[str] = (),
    ) -> VarDecl:
        """Declare a boolean flag with levels ``False``/``True``."""
        if init is not None and not isinstance(init, bool):
            raise ModelError(f"flag {name!r}: init must be a bool or None")
        index = None if init is None else int(init)
        return self._add_var(name, "flag", ("False", "True"), index, monotone, hidden_from)

    def _add_var(
        self,
        name: str,
        kind: str,
        levels: tuple[str, ...],
        init: int | None,
        monotone: bool,
        hidden_from: Iterable[str],
    ) -> VarDecl:
        self._claim(name, "variable")
        if isinstance(hidden_from, str):
            hidden_from = (hidden_from,)
        decl = VarDecl(name, kind, levels, init, bool(monotone), tuple(hidden_from))
        self.variables.append(decl)
        return decl

    # -- actors ------------------------------------------------------------------------
    def actor(
        self,
        name: str,
        observes: Observes | None = None,
        remember_last: bool = False,
        idle: bool = True,
    ) -> Actor:
        """Declare an actor. ``observes`` defaults to ``V.all()``."""
        self._claim(name, "actor")
        observes = V.all() if observes is None else observes
        if not isinstance(observes, Observes):
            raise ModelError(
                f"actor {name}: observes must be V.all(), V.all_except(...) or V.only(...)"
            )
        actor = Actor(self, name, observes, bool(remember_last), bool(idle))
        self.actors.append(actor)
        return actor

    def nature(self) -> Actor:
        """The built-in Nature actor (always last, observes everything, has ``none``)."""
        if self._nature is None:
            self._nature = Actor(self, NATURE, V.all(), idle=False, is_nature=True)
        return self._nature

    def actor_named(self, name: str) -> Actor:
        """Look up an actor (``"Nature"`` included) by name."""
        if name == NATURE:
            return self.nature()
        for actor in self.actors:
            if actor.name == name:
                return actor
        raise ModelError(f"unknown actor {name!r}")

    # -- derived variables and constraints ---------------------------------------------
    def latch(self, name: str, of: str, when: Expr | bool) -> LatchDecl:
        """Add a variable that copies ``of`` when ``when`` first holds (levels of ``of``
        with ``"unset"`` prepended)."""
        self._claim(name, "latch")
        decl = LatchDecl(name, of, lift_bool(when))
        self.latches.append(decl)
        self.variables.append(decl)
        return decl

    def fairness(
        self,
        name: str,
        actor: str | Actor,
        trigger: Expr | bool,
        within: int,
        responses: Iterable[str],
    ) -> FairnessDecl:
        """Bounded fairness: after ``within`` ticks of an unanswered ``trigger`` the actor
        is restricted to ``responses`` (spec 3.1)."""
        self._claim(name, "fairness constraint")
        if isinstance(within, bool) or not isinstance(within, int) or within < 1:
            raise ModelError(f"fairness {name!r}: within must be an int >= 1")
        actor_name = actor.name if isinstance(actor, Actor) else actor
        responses = (responses,) if isinstance(responses, str) else tuple(responses)
        if not responses:
            raise ModelError(f"fairness {name!r}: responses must not be empty")
        decl = FairnessDecl(name, actor_name, lift_bool(trigger), within, responses)
        self.fairness_constraints.append(decl)
        return decl

    def profile(
        self,
        name: str,
        actor: str | Actor,
        forbid: Iterable[str],
        unless: Expr | bool = FALSE,
    ) -> ProfileDecl:
        """Behavioral profile, inert unless selected when compiling."""
        self._claim(name, "profile")
        actor_name = actor.name if isinstance(actor, Actor) else actor
        forbid = (forbid,) if isinstance(forbid, str) else tuple(forbid)
        decl = ProfileDecl(name, actor_name, forbid, lift_bool(unless))
        self.profiles.append(decl)
        return decl

    def invariant(self, name: str, expr: Expr | bool) -> Expr:
        """Declare a named invariant; reference it with ``V.invariant(name)``."""
        self._claim(name, "invariant")
        self.invariants[name] = lift_bool(expr)
        return self.invariants[name]

    def ending(self, name: str, expr: Expr | bool) -> Expr:
        """Declare a named ending; states satisfying it are terminal."""
        self._claim(name, "ending")
        self.endings[name] = lift_bool(expr)
        return self.endings[name]

    # -- compile -----------------------------------------------------------------------
    def compile(self, profile: str | Iterable[str] | None = None) -> CompiledModel:
        """Shorthand for :func:`wavefront.model.compile.compile`."""
        from .compile import compile as compile_model

        return compile_model(self, profile=profile)

    def __repr__(self) -> str:
        return f"Model({self.name!r}, horizon={self.horizon})"


def _level_index(var: str, levels: tuple[str, ...], level: object) -> int:
    if isinstance(level, str) and level in levels:
        return levels.index(level)
    raise ModelError(f"variable {var!r} has no level {level!r} (levels: {', '.join(levels)})")
