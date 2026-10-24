"""Shared machinery for the Cold War tests: per-hypothesis models, hindsight and replay
states, the realized path on the flattened game, symbolic kernels on the coarse game, the
bounded cut-off and the lifted crisis kernels of docs/cw_v0_decisions.md D5, minimal
coalitions and minimal relaxation sets. Analysis devices only; the model is
``models/cw/v0.py`` with ``models/cw/crises/`` and the readings are decisions section R.
"""

from __future__ import annotations

import itertools
import time
from collections import deque
from collections.abc import Callable, Iterable, Sequence
from functools import lru_cache

import z3

from models.cw import crises
from models.cw.snapshots import snapshot_state
from models.cw.v0 import REALIZED_MOVES, YEAR0, build
from models.ww2 import bounded
from models.ww2.hypotheses import fixed_model, realized_moves
from wavefront.bmc.queries import _check
from wavefront.engine import attractor, explore, safe
from wavefront.model.compile import CompiledModel

HYPS = ("status_quo", "opportunist")
OPP = "opportunist"
PRINCIPALS = ("USA", "USSR", "PRC")
CRISIS_DATA = REALIZED_MOVES.parent / "crises"
ADVERSE = ("GENERAL_WAR", "ACCIDENTAL_WAR")


def tick(year: int) -> int:
    return year - YEAR0


# -- models ---------------------------------------------------------------------------------
@lru_cache(maxsize=None)
def model_of(aims: str, prc_principal: bool = True, frozen_oversight: bool = False):
    return fixed_model(build(prc_principal, frozen_oversight), aims_USSR=aims)


@lru_cache(maxsize=None)
def compiled(
    aims: str,
    prc_principal: bool = True,
    frozen_oversight: bool = False,
    relax: frozenset[str] = frozenset(),
) -> CompiledModel:
    return model_of(aims, prc_principal, frozen_oversight).compile(relax=relax)


@lru_cache(maxsize=None)
def flat_of(aims: str, prc_principal: bool = True):
    return crises.flat(compiled(aims, prc_principal))


def hindsight(year: int, aims: str, prc_principal: bool = True, frozen: bool = False):
    """The coarse state of 1 January ``year`` from the hindsight snapshot."""
    return snapshot_state(compiled(aims, prc_principal, frozen), year, aims)


def replay_state(year: int, aims: str):
    """The coarse state of 1 January ``year`` from the manual replay snapshot."""
    return snapshot_state(compiled(aims), year, aims, kind="replay")


def with_level(cm, state, var: str, level) -> tuple[int, ...]:
    """``state`` with ``var`` set to ``level`` (a level name or an index)."""
    i = cm.index[var]
    v = cm.variables[i]
    value = level if isinstance(level, int) else list(map(str, v.levels)).index(str(level))
    s = list(state)
    s[i] = value
    return tuple(s)


def level(cm, state, var: str) -> str:
    return cm.state_dict(state)[var]


# -- the realized path ----------------------------------------------------------------------
def _crisis_index(fm, move) -> int | None:
    for k, comp in enumerate(fm._compiled):
        if move[comp.actor] == comp.action:
            return k
    return None


@lru_cache(maxsize=None)
def realized(aims: str, prc_principal: bool = True):
    """The realized play on the flattened game from the 1947 hindsight snapshot:
    ``(coarse, fine, stop)``. ``coarse[t]`` is the coarse state at tick t; ``fine`` maps a
    crisis name to its realized fine states (flat states, the first after entry); ``stop``
    is ``None`` or ``(year, crisis or None, step, actor, action)`` for the first move that
    is unavailable."""
    fm = flat_of(aims, prc_principal)
    cm = fm.coarse
    s = hindsight(1947, aims, prc_principal)
    coarse, fine = [s], {}
    for t, move in enumerate(realized_moves(cm, REALIZED_MOVES)):
        av = fm.available(s)
        for a, j, acts in zip(cm.actors, move, av, strict=True):
            if j not in acts:
                return tuple(coarse), fine, (YEAR0 + t, None, 0, a.name, a.actions[j].name)
        k = _crisis_index(fm, move)
        s = fm.step(s, move)
        if k is not None:
            comp = fm._compiled[k]
            name = comp.crisis.label
            sub = comp.crisis.sub
            states = [s]
            rows = realized_moves(sub, CRISIS_DATA / name / "realized_moves.csv")
            for step, fmove in enumerate(rows):
                if sub.is_terminal(fm.split(s)[2]):
                    break
                flat_move = list(fm._wait)
                for (ai, off), fj in zip(comp.layout, fmove, strict=True):
                    flat_move[ai] = off + fj
                av = fm.available(s)
                for ai, j in enumerate(flat_move):
                    if j not in av[ai]:
                        actor = fm.actors[ai]
                        return (
                            tuple(coarse),
                            fine,
                            (YEAR0 + t, name, step, actor.name, actor.actions[j].name),
                        )
                s = fm.step(s, tuple(flat_move))
                states.append(s)
            fine[name] = tuple(states)
            s = fm.step(s, comp.ret_move)
        coarse.append(s)
    return tuple(coarse), fine, None


# -- the bounded cut-off (decisions D5) -----------------------------------------------------
class Cut:
    """A compiled (or flattened) model whose coarse states at tick ``cut`` or later are
    terminal with the ending ``CUT``: the analysis cut-off of decisions D5. Everything else
    is delegated."""

    def __init__(self, cm, cut: int) -> None:
        self._cm = cm
        self._cut = cut
        self._tick = cm.index["tick"]

    def __getattr__(self, name: str):
        return getattr(self._cm, name)

    def _is_fine(self, s) -> bool:
        return hasattr(self._cm, "is_fine") and self._cm.is_fine(s)

    def ending_of(self, s):
        e = self._cm.ending_of(s)
        if e is None and not self._is_fine(s) and s[self._tick] >= self._cut:
            return "CUT"
        return e

    def is_terminal(self, s) -> bool:
        return self.ending_of(s) is not None


class Forbid:
    """A model in which the listed ``(actor, action)`` pairs are never available (the
    restricted games of decisions R C9). Everything else is delegated."""

    def __init__(self, cm, pairs: Iterable[tuple[str, str]]) -> None:
        self._cm = cm
        self._drop = {}
        for actor_name, action in pairs:
            actor = next(a for a in cm.actors if a.name == actor_name)
            self._drop.setdefault(actor.index, set()).add(actor.action_index(action))

    def __getattr__(self, name: str):
        return getattr(self._cm, name)

    def available(self, s):
        out = self._cm.available(s)
        if not self._drop:
            return out
        return [
            [j for j in acts if j not in self._drop.get(i, ())] or acts[:1]
            if self._drop.get(i)
            else acts
            for i, acts in enumerate(out)
        ]


def graph(cm, start, cut: int | None = None, max_states: int = 3_000_000):
    m = Cut(cm, cut) if cut is not None else cm
    return explore(m, initial=[start], max_states=max_states)


def ids_where(g, fn: Callable[[int], bool]) -> set[int]:
    return {i for i in range(g.size()) if fn(i)}


def ending_ids(g, *names: str) -> set[int]:
    return {i for i, e in enumerate(g.ending) if e in names}


def bfs_distance(g, source: int, targets: set[int]) -> int | None:
    """Fewest transitions from ``source`` to ``targets`` on ``g`` (all actors)."""
    if source in targets:
        return 0
    seen = {source}
    queue = deque([(source, 0)])
    while queue:
        s, d = queue.popleft()
        for t in g.succ[s]:
            if t in targets:
                return d + 1
            if t not in seen:
                seen.add(t)
                queue.append((t, d + 1))
    return None


def bfs_path(g, source: int, targets: set[int]) -> list[tuple[int, tuple[int, ...]]] | None:
    """A shortest path ``[(state, joint move), ...]`` from ``source`` into ``targets``."""
    if source in targets:
        return []
    parent = {source: None}
    queue = deque([source])
    while queue:
        s = queue.popleft()
        for move, t in zip(g.moves[s], g.succ[s], strict=True):
            if t in parent:
                continue
            parent[t] = (s, move)
            if t in targets:
                path, x = [], t
                while parent[x] is not None:
                    p, m = parent[x]
                    path.append((p, m))
                    x = p
                return path[::-1]
            queue.append(t)
    return None


def move_names(cm, move) -> list[str]:
    """``actor.action`` for every non-idle action of a joint move."""
    out = []
    for a, j in zip(cm.actors, move, strict=True):
        x = a.actions[j]
        if not x.is_idle:
            out.append(f"{a.name}.{x.name}")
    return out


# -- symbolic kernels on the coarse game ----------------------------------------------------
@lru_cache(maxsize=None)
def encoding(aims: str, prc_principal: bool = True, frozen_oversight: bool = False):
    from wavefront.symbolic import encode

    return encode(compiled(aims, prc_principal, frozen_oversight))


@lru_cache(maxsize=None)
def kernel(
    aims: str,
    coalition: tuple[str, ...],
    invariant: str = "balance_cw",
    prc_principal: bool = True,
    frozen_oversight: bool = False,
):
    from wavefront.symbolic import safe as ssafe

    enc = encoding(aims, prc_principal, frozen_oversight)
    return ssafe(enc, list(coalition), enc.predicate(invariant))


def outside(res) -> int:
    enc = res.enc
    return enc.mgr.DIFF(enc.dom, res.kernel)


ALL_ACTORS = (*PRINCIPALS, "Nature")


@lru_cache(maxsize=None)
def reach_all(aims: str, what: str, invariant: str = "balance_cw"):
    """The attractor of every actor, Nature included (so a state's rank is its shortest
    trace), over the whole coarse domain, to ``what``: ``"adverse"`` (the states of
    GENERAL_WAR or ACCIDENTAL_WAR) or ``"out:<coalition>"`` (the outside of that
    coalition's kernel of ``invariant``, coalition members joined by '+')."""
    from wavefront.model import V
    from wavefront.symbolic import attractor

    enc = encoding(aims)
    if what == "adverse":
        target = enc.predicate(~V.invariant("no_general_war"))
    else:
        coalition = tuple(what.split(":", 1)[1].split("+"))
        target = outside(kernel(aims, coalition, invariant))
    return attractor(enc, list(ALL_ACTORS), target)


def far(d: int | None) -> float:
    """A shortest trace as a comparable distance (unreachable is infinitely far)."""
    return float("inf") if d is None else float(d)


def compare(near: dict, far_: dict) -> tuple[bool, bool]:
    """``(some, none_reverse)`` for two dicts of distances to the adverse side (smaller is
    nearer; None is unreachable): ``some`` iff some measure is smaller in ``near``,
    ``none_reverse`` iff no measure is smaller in ``far_``."""
    some = any(far(near[k]) < far(far_[k]) for k in near)
    reverse = any(far(far_[k]) < far(near[k]) for k in near)
    return some, not reverse


def fortune(g, sides: Sequence[str], target: set[int], start: int) -> tuple[bool, dict]:
    """Contested in the fortune sense (ww2_testbed.md section 4.6), for each side P of
    ``sides``: P joined by Nature forces ``target`` against the others' best play, and the
    others joined by Nature keep it away against P's best play. Returns the verdict and,
    per side, the standard region and the region with Nature joined."""
    from wavefront.engine import contested

    def region(r):
        return "forced" if start in r.forced else "blocked" if start in r.blocked else "contested"

    ok, table = True, {}
    for side in sides:
        alone = contested(g, [side], target, "reach")
        joined = contested(g, [side, "Nature"], target, "reach")
        table[side] = (region(alone), region(joined))
        ok = ok and start in joined.forced and start in alone.blocked
    return ok, table


def shortest_out(res, state, max_depth: int | None = None) -> int | None:
    """Fewest transitions of arbitrary play from ``state`` out of the kernel ``res``."""
    from wavefront.symbolic import shortest

    if not res.contains(state):
        return 0
    return shortest(res.enc, state, outside(res), max_depth=max_depth)


# -- lifted crisis kernels (decisions D5) ---------------------------------------------------
def crisis_entry(fm, coarse_state, crisis_name: str):
    """The first fine state of ``crisis_name`` entered from ``coarse_state`` (the crisis
    actor plays the crisis action, the others their built-in action) and the crisis
    index."""
    k = next(i for i, c in enumerate(fm._compiled) if c.crisis.label == crisis_name)
    comp = fm._compiled[k]
    return fm.step(coarse_state, comp.ret_move), k


@lru_cache(maxsize=None)
def _fine_graph(aims: str, coarse_state: tuple, crisis_name: str, prc_principal: bool = True):
    fm = flat_of(aims, prc_principal)
    first, k = crisis_entry(fm, coarse_state, crisis_name)
    comp = fm._compiled[k]
    sub = comp.crisis.sub
    g = explore(sub, initial=[fm.split(first)[2]], max_states=1_000_000)
    returns = {}
    for i in range(g.size()):
        if g.terminal[i]:
            returns[i] = fm.step(coarse_state + (k,) + g.states[i], comp.ret_move)
    return g, returns, k


def fine_graph(aims, coarse_state, crisis_name, prc_principal=True):
    """``(g, returns, k)``: the sub-game graph from its entry, the coarse return state of
    every terminal fine state, and the crisis index."""
    return _fine_graph(aims, tuple(coarse_state), crisis_name, prc_principal)


def lifted_kernel(g, returns, coalition, coarse_member: Callable[[tuple], bool]) -> set[int]:
    """Fine states from which ``coalition`` keeps the play inside the crisis (where every
    coarse invariant holds) until a return state with ``coarse_member`` true."""
    phi = {i for i in range(g.size()) if not g.terminal[i] or coarse_member(returns[i])}
    return safe(g, list(coalition), phi).kernel


def lifted_attractor(g, returns, coalition, coarse_target: Callable[[tuple], bool]) -> set[int]:
    """Fine states from which ``coalition`` forces a return state with ``coarse_target``."""
    target = {i for i in range(g.size()) if g.terminal[i] and coarse_target(returns[i])}
    return attractor(g, list(coalition), target).win


# -- coalitions and relaxations -------------------------------------------------------------
def minimal_coalitions(universe: Sequence[str], works: Callable[[tuple[str, ...]], bool]):
    """Inclusion-minimal coalitions of ``universe`` for which ``works`` holds."""
    found: list[frozenset[str]] = []
    for n in range(len(universe) + 1):
        for c in itertools.combinations(universe, n):
            if any(m <= frozenset(c) for m in found):
                continue
            if works(c):
                found.append(frozenset(c))
    return found


def fmt(family) -> str:
    if not family:
        return "none"
    return ", ".join("{" + ", ".join(sorted(c)) + "}" for c in family)


def minimal_relaxation_sets(cm, start, k, target, max_size=3, max_sets=40):
    """Every inclusion-minimal set of named assumptions of size at most ``max_size`` whose
    relaxation makes ``target`` reachable within ``k`` transitions from ``start`` (the
    bounded encoding of ``wavefront.bmc`` unrolled from ``start``, as in tests/july1914).
    ``[[]]`` means reachable as is."""
    q = bounded._QueryFrom(cm, start, k, target)
    enc = q.enc
    bools = dict(enc.assume)
    relaxed = [z3.Not(b) for b in bools.values()]
    solver = q.solver()
    solver.add(q.by[k])
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
