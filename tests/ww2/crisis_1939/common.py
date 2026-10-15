"""Shared construction for the summer-1939 crisis tests (not a test module).

The entry state of every registered claim is v1's state at the start of 1939Q3
(``1939Q2.json`` with its built-ins) under ``aims_GER = hegemonic``, ``aims_USSR =
defensive`` (and ``aims_JPN = hegemonic``, which the sub-game does not read); the realized
states are the replay of ``data/ww2/crises/1939/realized_moves.csv`` from it
(docs/crisis_1939_decisions.md, section R). Compiled models and graphs are cached: every
result is computed with the explicit engine.
"""

from __future__ import annotations

import copy
import functools
import itertools
import json
from collections.abc import Iterable, Sequence

from models.ww2 import v1
from models.ww2.crises import summer_1939 as crisis
from models.ww2.hypotheses import REALIZED_MOVES_V1, SNAPSHOTS_V1, realized_rows, snapshot_state
from wavefront.engine import Graph, attractor, explore, flatten
from wavefront.model import Model, V
from wavefront.model.compile import CompiledModel

V1_CM = v1.model.compile()
COARSE_Q2_STATE = snapshot_state(
    V1_CM,
    "1939Q2",
    "hegemonic",
    "defensive",
    snapshots=SNAPSHOTS_V1,
    builtins=True,
    aims_JPN="hegemonic",
)
COARSE_Q2 = V1_CM.state_dict(COARSE_Q2_STATE)
SNAPSHOT_Q3 = json.loads((SNAPSHOTS_V1 / "1939Q3.json").read_text(encoding="utf-8"))
BELIEFS = ("will_not_fight", "uncertain", "will_fight")
PACT = V.german_approach == "pact"


def _profiles(profile: str | Iterable[str] | None) -> tuple[str, ...] | None:
    if profile is None:
        return None
    return (profile,) if isinstance(profile, str) else tuple(sorted(profile))


@functools.lru_cache(maxsize=None)
def _compiled(inert: bool, passage: str | None, profile: tuple[str, ...] | None) -> CompiledModel:
    return crisis.build(inert=inert, passage=passage).compile(profile=profile)


def compiled(
    inert: bool = False,
    passage: str | None = None,
    profile: str | Iterable[str] | None = None,
) -> CompiledModel:
    """The sub-game compiled with the given build options and profiles (cached)."""
    return _compiled(inert, passage, _profiles(profile))


def entry(cm: CompiledModel, belief: str | None = None) -> tuple[int, ...]:
    """The entry state of ``cm``; ``belief`` replaces the entry level of ``belief_GER``
    (a counterfactual entry state, K2 and K4)."""
    state = list(crisis.entry_state(cm, COARSE_Q2))
    if belief is not None:
        i = cm.index["belief_GER"]
        state[i] = cm.variables[i].levels.index(belief)
    return tuple(state)


def with_level(cm: CompiledModel, state: Sequence[int], var: str, level: str) -> tuple[int, ...]:
    """``state`` with ``var`` set to ``level``."""
    out = list(state)
    i = cm.index[var]
    out[i] = cm.variables[i].levels.index(level)
    return tuple(out)


def realized_states(cm: CompiledModel) -> list[tuple[int, ...]]:
    """The realized states at ticks 0 to 20 in ``cm`` (raises if a move is unavailable;
    in a scenario build the realized path does not exist past tick 13)."""
    return crisis.replay(cm, entry(cm), crisis.realized_moves(cm))


@functools.lru_cache(maxsize=None)
def _graph(cm: CompiledModel, initial: tuple[tuple[int, ...], ...]) -> Graph:
    return explore(cm, initial=list(initial))


def graph(cm: CompiledModel, initial: Iterable[Sequence[int]]) -> Graph:
    """The explicit graph of ``cm`` from ``initial`` (cached)."""
    return _graph(cm, tuple(tuple(s) for s in initial))


def sid(g: Graph, state: Sequence[int]) -> int:
    return g.index[tuple(state)]


def where(g: Graph, expr) -> set[int]:
    """The state ids of ``g`` satisfying an expression."""
    return g.states_where(expr)


def minimal_coalitions(universe: Sequence[str], works) -> list[frozenset[str]]:
    """Minimal coalitions (by inclusion) drawn from ``universe`` for which ``works`` holds,
    by increasing size (supersets of minimal ones skipped)."""
    found: list[frozenset[str]] = []
    for size in range(len(universe) + 1):
        for combo in itertools.combinations(universe, size):
            c = frozenset(combo)
            if any(m <= c for m in found):
                continue
            if works(c):
                found.append(c)
    return found


def forcing_coalitions(g: Graph, state_id: int, target: set[int], universe=("WEST", "USSR")):
    """Minimal coalitions over ``universe`` that can force ``target`` from ``state_id``."""
    return minimal_coalitions(list(universe), lambda c: state_id in attractor(g, c, target).win)


def minimal_hitting_sets(sets: Sequence[Sequence[str]]) -> list[frozenset[str]]:
    """The minimal sets meeting every set of ``sets`` (brute force over their union)."""
    universe = sorted({x for s in sets for x in s})
    out: list[frozenset[str]] = []
    for size in range(len(universe) + 1):
        for combo in itertools.combinations(universe, size):
            c = frozenset(combo)
            if any(h <= c for h in out):
                continue
            if all(c & set(s) for s in sets):
                out.append(c)
    return out


# -- v1's realized transition of 1939Q3 and the flattened game ------------------------------


def v1_realized_q3() -> dict[str, str]:
    """v1's own realized transition of 1939Q3: ``step`` from the ``1939Q2.json`` state with
    the realized row of tick 14 of ``data/ww2/realized_moves_v1.csv``."""
    row = next(r for r in realized_rows(REALIZED_MOVES_V1) if int(r["tick"]) == 14)
    move = tuple(a.action_index(row[a.name]) for a in V1_CM.actors)
    return V1_CM.state_dict(V1_CM.step(COARSE_Q2_STATE, move))


def snapshot_q3() -> dict[str, str]:
    """The levels of ``1939Q3.json`` (v1's hindsight snapshot at the end of 1939Q3)."""
    return {k: str(v["level"]) for k, v in SNAPSHOT_Q3["variables"].items()}


def exit_applied(fine_terminal: Sequence[int], cm: CompiledModel) -> dict[str, str]:
    """The nine exit variables of the coarse state after the exit map of the terminal fine
    state ``fine_terminal`` is applied to the entry coarse state (string values)."""
    out = crisis.exit(cm.state_dict(fine_terminal), dict(COARSE_Q2))
    merged = dict(COARSE_Q2)
    merged.update({k: str(v) for k, v in out.items()})
    return {k: merged[k] for k in crisis.EXIT_VARIABLES}


def flattened_v1() -> tuple[object, CompiledModel]:
    """A copy of v1 with a GER action ``crisis_1939`` (no effect, no delay), compiled and
    flattened with the sub-game (full build) attached to it, and the sub-game."""
    coarse: Model = copy.deepcopy(v1.model)
    coarse.actor_named("GER").action(
        "crisis_1939",
        source="analysis device: the sub-game docs/crisis_1939_testbed.md is entered here",
    )
    ccm = coarse.compile()
    sub = crisis.build().compile()
    return flatten(ccm, [crisis.crisis(sub=sub)]), sub
