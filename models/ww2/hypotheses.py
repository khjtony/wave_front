"""Helpers for running ``models/ww2/v0.py`` from the hindsight snapshots, per hypothesis.

The hindsight snapshots (``snapshots/ww2/hindsight/``) omit the two swept hidden objectives
``aims_GER`` and ``aims_USSR`` on purpose: a snapshot that fixed them would assert a
historiographical hypothesis as an observation. A per-hypothesis run fixes them here, by
adding one entry with ``confidence: "assumed"`` to a copy of the snapshot, as the snapshot
README prescribes.

Tick mapping (snapshot README): the file named for quarter ``Q`` holds the levels in force
at the *end* of ``Q``, which is the model's state at tick ``index(Q) + 1``, where
``index("1936Q1") == 0``; ``1935Q4.json`` is tick 0. The snapshot loader leaves every
built-in at its initial value, so :func:`snapshot_state` sets ``tick`` from the file name
and leaves the rest as the loader does: no pending delayed effect, no last action
(``last_GER`` and ``last_WEST`` are ``none``), fairness counters at zero. Latches are set
by the loader from the loaded state (so ``belief_at_munich`` reads the snapshot's belief,
not the belief of October 1938).

:func:`realized_moves` reads ``data/ww2/realized_moves.csv`` as joint moves (action indices
in actor order, Nature last); :func:`fixed_model` returns a copy of a model with swept
variables pinned, which is how the bounded checker (which always starts from the model's
declared initial states) is pointed at one hypothesis's tick-0 state.

:func:`restricted` wraps a compiled model so that some actors play a fixed memoryless
strategy (a function of the state choosing one of the available actions). Exploring the
wrapper gives the game in which only the other actors choose. It is an analysis device, not
a model edit: if a coalition cannot keep an invariant against one fixed strategy of its
opponents, it cannot keep it against all of them, so a state outside the kernel of the
restricted game is outside the true kernel (a refutation of membership); conversely, fixing
the coalition's own strategy and finding no violating play shows membership (the
sufficiency check of decisions D6).
"""

from __future__ import annotations

import copy
import csv
import dataclasses
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from wavefront.evidence import read_snapshot, snapshot_to_state
from wavefront.model import Model, ModelError
from wavefront.model.compile import CompiledModel

__all__ = [
    "ROOT",
    "SNAPSHOTS",
    "REALIZED_MOVES",
    "HYPOTHESES",
    "quarter_tick",
    "snapshot_data",
    "snapshot_state",
    "realized_rows",
    "realized_moves",
    "fixed_model",
    "Strategy",
    "restricted",
    "first_available",
    "realized_corridor",
]

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOTS = ROOT / "snapshots" / "ww2" / "hindsight"
REALIZED_MOVES = ROOT / "data" / "ww2" / "realized_moves.csv"

# The two hypotheses of the registered tests: aims_GER swept, aims_USSR fixed by the
# default assumption ``ussr_defensive``.
HYPOTHESES = (
    {"aims_GER": "revisionist", "aims_USSR": "defensive"},
    {"aims_GER": "hegemonic", "aims_USSR": "defensive"},
)


def quarter_tick(quarter: str) -> int:
    """The model tick at the *end* of ``quarter`` (``"1935Q4"`` is 0, ``"1936Q1"`` is 1,
    ``"1940Q4"`` is 20)."""
    try:
        year, q = quarter.split("Q")
        index = (int(year) - 1936) * 4 + int(q) - 1
    except ValueError:
        raise ValueError(f"not a quarter like 1938Q4: {quarter!r}") from None
    if not 1 <= int(q) <= 4:
        raise ValueError(f"not a quarter like 1938Q4: {quarter!r}")
    return index + 1


def snapshot_data(quarter: str, **fixed: str) -> dict[str, Any]:
    """The parsed snapshot ``<quarter>.json`` with each ``fixed`` variable added as an
    ``assumed`` entry (the snapshot must not already contain it)."""
    data = read_snapshot(SNAPSHOTS / f"{quarter}.json")
    data = copy.deepcopy(data)
    for name, level in fixed.items():
        if name in data["variables"]:
            raise ModelError(f"snapshot {quarter} already fixes {name!r}")
        data["variables"][name] = {"level": level, "confidence": "assumed", "indicators": []}
    return data


def snapshot_state(
    cm: CompiledModel,
    quarter: str,
    aims_GER: str,
    aims_USSR: str = "defensive",
) -> tuple[int, ...]:
    """The state of ``cm`` at the end of ``quarter`` (tick ``quarter_tick(quarter)``) read
    from the hindsight snapshot, with the hidden objectives fixed to one hypothesis."""
    data = snapshot_data(quarter, aims_GER=aims_GER, aims_USSR=aims_USSR)
    state = list(snapshot_to_state(data, cm))
    if cm.timed:
        state[cm.index["tick"]] = quarter_tick(quarter)
    return tuple(state)


def realized_rows(path: str | Path = REALIZED_MOVES) -> list[dict[str, str]]:
    """The rows of the realized move file, in tick order."""
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for k, row in enumerate(rows):
        if int(row["tick"]) != k:
            raise ValueError(f"{path}: row {k} has tick {row['tick']}")
    return rows


def realized_moves(cm: CompiledModel, path: str | Path = REALIZED_MOVES) -> list[tuple[int, ...]]:
    """The realized decisions as joint moves of ``cm`` (one action index per actor, in actor
    order with Nature last). The CSV's ``idle`` and ``none`` are the built-in actions."""
    moves = []
    for row in realized_rows(path):
        move = []
        for actor in cm.actors:
            name = row[actor.name]
            try:
                move.append(actor.action_index(name))
            except ModelError:
                raise ModelError(
                    f"{path}: tick {row['tick']}: {actor.name} has no action {name!r}"
                ) from None
        moves.append(tuple(move))
    return moves


def fixed_model(model: Model, **levels: str) -> Model:
    """A shallow copy of ``model`` whose swept variables named in ``levels`` have a single
    initial level. Nothing else changes: same actions, guards, constraints and assumptions,
    so ``compile(fixed_model(m, aims_GER="hegemonic"))`` has exactly the initial states of
    ``m`` in which ``aims_GER`` is hegemonic."""
    out = copy.copy(model)
    out.variables = list(model.variables)
    found = set()
    for k, decl in enumerate(out.variables):
        name = getattr(decl, "name", None)
        if name in levels:
            if getattr(decl, "init", 0) is not None:
                raise ModelError(f"variable {name!r} is not swept (declared with an init)")
            if levels[name] not in decl.levels:
                raise ModelError(f"variable {name!r} has no level {levels[name]!r}")
            out.variables[k] = dataclasses.replace(decl, init=decl.levels.index(levels[name]))
            found.add(name)
    missing = set(levels) - found
    if missing:
        raise ModelError(f"no variable named {', '.join(sorted(missing))}")
    return out


# A memoryless strategy: given the state and the actor's available action names, the name of
# the action to play (it must be one of them).
Strategy = Callable[[Mapping[str, str], Sequence[str]], str]


class _Restricted:
    """A :class:`CompiledModel` whose ``available`` lets the actors in ``strategies`` play
    only the action their strategy picks; everything else is delegated."""

    def __init__(self, cm: CompiledModel, strategies: Mapping[str, Strategy]) -> None:
        self._cm = cm
        self._fixed = []
        for name, fn in strategies.items():
            actor = next((a for a in cm.actors if a.name == name), None)
            if actor is None:
                raise ModelError(f"unknown actor {name!r}")
            self._fixed.append((actor.index, actor, fn))

    def __getattr__(self, name: str) -> Any:
        return getattr(self._cm, name)

    def available(self, state: Sequence[int]) -> list[list[int]]:
        out = self._cm.available(state)
        if not self._fixed:
            return out
        view = self._cm.state_dict(state)
        for i, actor, fn in self._fixed:
            names = [actor.actions[j].name for j in out[i]]
            choice = fn(view, names)
            if choice not in names:
                raise ModelError(
                    f"strategy for {actor.name} chose {choice!r}, not available "
                    f"({', '.join(names)}) in {self._cm.format_state(state)}"
                )
            out = [*out[:i], [actor.action_index(choice)], *out[i + 1 :]]
        return out


def restricted(cm: CompiledModel, strategies: Mapping[str, Strategy]) -> CompiledModel:
    """``cm`` with the named actors fixed to memoryless strategies (see the module
    docstring). The result can be passed to :func:`wavefront.engine.explore`."""
    return _Restricted(cm, strategies)  # type: ignore[return-value]


def first_available(*preferences: str) -> Strategy:
    """The strategy that plays the first of ``preferences`` that is available, else the
    built-in action (``idle``, or ``none`` for Nature)."""

    def play(state: Mapping[str, str], names: Sequence[str]) -> str:
        for p in preferences:
            if p in names:
                return p
        return names[0]

    return play


def realized_corridor(model: Model | None = None, path: str | Path = REALIZED_MOVES) -> Model:
    """A display device for the visualizer, not a model of record.

    ``model`` (default ``models/ww2/v0.py``) restricted to the decisions recorded in
    ``data/ww2/realized_moves.csv``: every declared action gets one more guard part,
    ``corridor``, that allows it only in the quarters in which the file records it (or when a
    fairness constraint restricts its actor to its responses and it is one of them). Each
    principal is declared without the built-in ``idle`` and gets a last action ``abstain`` (no
    effect) instead, so that its realized decision comes first in move order; Nature must play
    its recorded event in its quarter whenever the event's guard holds (one fairness
    constraint ``corridor_<event>`` per event). The game left is the realized path with every
    combination of omitted decisions by the four principals, small enough to explore whole
    from tick 0, and its shortest witness to ``BRITAIN_ALONE`` is the realized path itself.
    Variables, effects, delays, the model's own fairness constraints, profiles, invariants
    and endings are unchanged. No registered test uses it; the page built from it says so."""
    from wavefront.model import FALSE, V
    from wavefront.model.model import Actor, conjunction

    if model is None:
        from .v0 import model as base
    else:
        base = model
    rows = realized_rows(path)
    out = copy.copy(base)
    out.name = base.name + "_corridor"
    out.description = (
        "Display corridor of " + base.name + ", not the model of record: each principal may "
        "take only its realized decision of the quarter (data/ww2/realized_moves.csv) or "
        "abstain, and Nature plays its recorded event where it can; every other declaration as "
        "in " + base.name + "."
    )
    out._names = dict(base._names)
    out.fairness_constraints = list(base.fairness_constraints)
    binding: dict[tuple[str, str], list] = {}
    for f in base.fairness_constraints:
        for r in f.responses:
            binding.setdefault((f.actor, r), []).append(V[f"fair_{f.name}"] >= f.within)

    def any_of(terms: list) -> Any:
        if not terms:
            return FALSE
        expr = terms[0]
        for t in terms[1:]:
            expr = expr | t
        return expr

    actors = []
    for actor in [*base.actors, base.nature()]:
        player = not actor.is_nature
        new = Actor(out, actor.name, actor.observes, actor.remember_last, idle=not player)
        new.is_nature = actor.is_nature
        for a in actor.actions:
            ticks = [int(r["tick"]) for r in rows if r[actor.name] == a.name]
            corridor = any_of([V.tick == t for t in ticks] + binding.get((actor.name, a.name), []))
            parts = [*(a.guard_parts or [("feasible", a.guard)]), ("corridor", corridor)]
            new.actions.append(
                dataclasses.replace(
                    a, guard=conjunction([e for _, e in parts]), guard_parts=tuple(parts)
                )
            )
            if actor.is_nature and ticks:
                out.fairness(
                    f"corridor_{a.name}",
                    actor="Nature",
                    trigger=any_of([V.tick == t for t in ticks]) & a.guard,
                    within=1,
                    responses=[a.name],
                )
        if player:
            new.action("abstain", source="display corridor: the realized decision not taken")
        actors.append(new)
    out.actors = actors[:-1]
    out._nature = actors[-1]
    return out
