"""Shared machinery for the July 1914 v1 tests: a copy of tests/july1914/common.py (as at
commit e082977) with the model switched to ``models/july1914/v1.py`` and its realized moves
(data/july1914/v1/realized_moves.csv). Per-hypothesis models, the realized replay, explicit
graphs from tick 0 or from a realized state, kernel departures along the realized path,
minimal coalitions per state, and inclusion-minimal relaxation sets by the bounded encoding.
Analysis devices only; the readings are docs/july1914_v1_decisions.md section R.
"""

from __future__ import annotations

import itertools
import time
from functools import lru_cache

import z3

from models.july1914.v1 import PRINCIPALS, REALIZED_MOVES, build
from models.ww2 import bounded
from models.ww2.hypotheses import fixed_model, realized_moves
from wavefront.analysis._common import remap_states
from wavefront.bmc.queries import _check
from wavefront.engine import attractor, explore
from wavefront.model.compile import CompiledModel

PAIRS = tuple(
    (g, r) for g in ("localize", "continental") for r in ("deter", "fight")
)  # (aims_GER, aims_RUS)
FIGHT = tuple(p for p in PAIRS if p[1] == "fight")
NOT_RUS = ("AUH", "GER", "FRA", "GBR")
X = NOT_RUS  # the largest coalition excluding Russia
COALITIONS_WITHOUT_RUS = tuple(
    c for n in range(len(NOT_RUS) + 1) for c in itertools.combinations(NOT_RUS, n)
)
COUPLING = "GER.mobilize_east:coupling"


def label(pair: tuple[str, str]) -> str:
    return f"aims_GER={pair[0]}, aims_RUS={pair[1]}"


@lru_cache(maxsize=None)
def model_of(pair: tuple[str, str], cadence: bool = True):
    return fixed_model(build(cadence), aims_GER=pair[0], aims_RUS=pair[1])


@lru_cache(maxsize=None)
def compiled(
    pair: tuple[str, str], cadence: bool = True, relax: frozenset[str] = frozenset()
) -> CompiledModel:
    return model_of(pair, cadence).compile(relax=relax)


@lru_cache(maxsize=None)
def replay(pair: tuple[str, str], cadence: bool = True):
    """The realized prefix: (states, stop) where ``states[t]`` is the state at tick t for as
    long as every realized move is available, and ``stop`` is ``None`` or ``(tick, actor,
    action)`` for the first unavailable realized decision."""
    cm = compiled(pair, cadence)
    (s,) = cm.initial_states()
    states = [s]
    for move in realized_moves(cm, REALIZED_MOVES):
        avail = cm.available(s)
        for a, j, acts in zip(cm.actors, move, avail, strict=True):
            if j not in acts:
                return tuple(states), (s[cm.index["tick"]], a.name, a.actions[j].name)
        s = cm.step(s, move)
        states.append(s)
    return tuple(states), None


@lru_cache(maxsize=None)
def graph0(pair: tuple[str, str], cadence: bool = True):
    """The explicit graph from the tick-0 state of the hypothesis pair."""
    return explore(compiled(pair, cadence), max_states=2_000_000)


@lru_cache(maxsize=None)
def graph_from(
    pair: tuple[str, str], tick: int, cadence: bool = True, relax: frozenset[str] = frozenset()
):
    """The explicit graph from the realized state at ``tick`` (remapped into the relaxed
    layout when ``relax`` drops a fairness counter)."""
    states, _ = replay(pair, cadence)
    base = compiled(pair, cadence)
    cm = compiled(pair, cadence, relax)
    (start,) = remap_states(base, cm, [states[tick]])
    return explore(cm, initial=[start], max_states=2_000_000)


def path_ids(g, pair, tick, cadence=True, relax=frozenset()):
    """Ids in ``g`` of the realized states from ``tick`` on (as far as the prefix goes)."""
    states, _ = replay(pair, cadence)
    base = compiled(pair, cadence)
    cm = compiled(pair, cadence, relax)
    return [g.index[s] for s in remap_states(base, cm, states[tick:])]


def departure(ids, kernel, start_tick):
    """The tick of the first state of ``ids`` (realized states from ``start_tick``) outside
    ``kernel``, or ``None``."""
    for k, s in enumerate(ids):
        if s not in kernel:
            return start_tick + k
    return None


def kept_as(dep):
    """A departure for arithmetic: a kernel kept to the end of the path counts as 39."""
    return 39 if dep is None else dep


def forcing_family(wins: dict[frozenset, set], state: int) -> list[frozenset]:
    """Minimal coalitions (by inclusion) whose attractor contains ``state``."""
    found: list[frozenset] = []
    for c in sorted(wins, key=lambda c: (len(c), sorted(c))):
        if any(m <= c for m in found):
            continue
        if state in wins[c]:
            found.append(c)
    return found


def all_attractors(g, target: set[int], universe=PRINCIPALS) -> dict[frozenset, set]:
    """``attractor(g, C, target).win`` for every coalition C of ``universe`` (Nature
    excluded, so it is an adversary)."""
    out = {}
    for n in range(len(universe) + 1):
        for c in itertools.combinations(universe, n):
            out[frozenset(c)] = attractor(g, list(c), target).win
    return out


def fmt(family) -> str:
    if not family:
        return "none"
    return ", ".join("{" + ", ".join(sorted(c)) + "}" if c else "{}" for c in family)


def minimal_relaxation_sets(cm, start, k, target, max_size=3, max_sets=40, constrain=None):
    """Every inclusion-minimal set of named assumptions, of size at most ``max_size``,
    whose relaxation makes ``target`` reachable within ``k`` transitions from ``start``
    (the encoding of ``wavefront.bmc`` unrolled from ``start``, models/ww2/bounded.py).
    Sizes are enumerated upwards and each set found blocks its supersets, so every set
    returned is minimal; at most ``max_sets`` are returned. ``[[]]`` means reachable as
    is."""
    q = bounded._QueryFrom(cm, start, k, target)
    enc = q.enc
    bools = dict(enc.assume)
    relaxed = [z3.Not(b) for b in bools.values()]
    solver = q.solver()
    solver.add(*bounded._constraints(enc, constrain), q.by[k])
    found: list[list[str]] = []
    blocks = []
    for size in range(max_size + 1):
        solver.push()
        solver.add(z3.AtMost(*relaxed, size), *blocks)
        while len(found) < max_sets and _check(solver) == z3.sat:
            model = solver.model()
            picked = [
                n for n, b in bools.items() if z3.is_false(model.eval(b, model_completion=True))
            ]
            found.append(picked)
            if not picked:
                solver.pop()
                return found
            block = z3.Or(*[bools[n] for n in picked])
            blocks.append(block)
            solver.add(block)
        solver.pop()
    return found


class Timer:
    def __init__(self):
        self.t = time.time()

    def __str__(self):
        return f"{time.time() - self.t:.1f} s"
