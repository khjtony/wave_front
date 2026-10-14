"""Symbolic fixpoints over a BDD encoding: controllable predecessor, attractor, safety
kernel, contested region, reachable states and witness traces.

Semantics are those of :mod:`wavefront.engine.solve` (spec sections 1 and 5.3, theory
section 3.2), computed over every state of the domain rather than over an explored graph.
A state's membership depends only on the states reachable from it, so on reachable states
the results equal the explicit engine's.

- ``cpre(enc, C, X) = {s active | exists C-move available in s . forall completions available
  in s . step(s, move) in X}``, where *active* is non-terminal with an available action for
  every actor. With ``P(s, a) = X(f(s, a))`` (the next-state functions substituted into
  ``X``), it is ``exists a_C . avail_C & ~(exists a_O . avail_O & ~P)``, quantified actor by
  actor.
- :func:`attractor`: ``mu X . T | cpre(X)``, keeping every stage ``X_0 = T``,
  ``X_{i+1} = T | cpre(X_i)``; the rank of a state is its first stage.
- :func:`safe`: ``nu X . phi & (Term | cpre(X))``. For a timed model it is computed backward
  one tick layer at a time (``K_H = phi & tick == H``, ``K_t = phi & tick == t & (Term |
  cpre(K_{t+1}))``): successors of a non-terminal state at tick ``t`` are at tick ``t + 1``,
  so this is the same fixpoint reached in ``horizon + 1`` steps, each over one layer.
  ``method="iterate"`` runs the plain iteration instead.
- :func:`contested`, as in the explicit engine.
- :func:`reachable`: forward image fixpoint; with ``check=True`` it raises
  :class:`ModelError` where ``explore`` would (an actor without an available action,
  overlapping endings, a transition with conflicting Sets, a strict Bump out of range or a
  monotone decrease).

Results are predicates (BDD edges over current-state bits) with ``contains(state)``,
``count(within=None)`` and, for attractors and kernels, ``strategy_move(state)``: one
coalition sub-move (action indices in actor order) witnessing membership, computed by
restricting the same quantified formula to the one state. :func:`witness` steps the
explicit model under that strategy against an adversary that maximizes the rank.

Memory: the fixpoints collect garbage between steps (:meth:`BDD.maybe_gc`). Edges stay
valid across a call if they are its arguments, are held by a result, by the encoding
(including :meth:`Encoding.predicate` results), or are protected
(:meth:`BDD.protect`, :meth:`BDD.protecting`); any other edge the caller holds may be
invalidated by a collection during the call.
"""

from __future__ import annotations

import itertools
import time
from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass, field
from typing import Literal

from ..model.compile import CompiledModel
from ..model.model import ModelError
from .bdd import FALSE, TRUE
from .encode import Encoding

__all__ = [
    "cpre",
    "attractor",
    "safe",
    "contested",
    "reachable",
    "shortest",
    "witness",
    "SymbolicAttractor",
    "SymbolicSafe",
    "SymbolicContested",
    "SymbolicReach",
]

State = tuple[int, ...]
SubMove = tuple[int, ...]
Progress = Callable[[dict], None]


def _maybe_gc(enc: Encoding, roots: Sequence[int]) -> None:
    """Collect garbage when the node table has grown enough (see :meth:`BDD.maybe_gc`)."""
    enc.mgr.maybe_gc(roots)


def _split(enc: Encoding, coalition: Collection[str]) -> tuple[list[int], list[int]]:
    members = enc.actor_indices(coalition)
    others = [a.index for a in enc.cm.actors if a.index not in set(members)]
    return members, others


def _cpre_from(enc: Encoding, members: list[int], others: list[int], p: int) -> int:
    """``exists a_C . avail_C & forall a_O . (avail_O -> p)`` for ``p`` over (s, a)."""
    mgr = enc.mgr
    bad = p ^ 1
    for o in others:
        bad = mgr.and_exists(enc.avail[o], bad, enc.actor_vs[o])
    good = bad ^ 1
    for c in members:
        good = mgr.and_exists(enc.avail[c], good, enc.actor_vs[c])
    return good


def cpre(enc: Encoding, coalition: Collection[str], x: int) -> int:
    """The controllable predecessor of ``x`` for ``coalition`` (actor names, Nature
    included when named)."""
    members, others = _split(enc, coalition)
    return enc.mgr.AND(_cpre_from(enc, members, others, enc.preimage(x)), enc.active)


def _winning_moves(enc: Encoding, members: list[int], x: int, state: Sequence[int]) -> int:
    """The coalition sub-moves (a BDD over the members' action bits) available in ``state``
    all of whose available completions lead into ``x``."""
    mgr = enc.mgr
    assign = enc.state_assignment(state)
    mapping: dict[int, int] = {}
    for lv in enc.state_levels:
        f = enc.next_fn.get(lv)
        mapping[lv] = (TRUE if assign[lv] else FALSE) if f is None else mgr.restrict(f, assign)
    p = mgr.compose(x, mapping)
    avail = [mgr.restrict(av, assign) for av in enc.avail]
    bad = p ^ 1
    for o in range(len(enc.cm.actors)):
        if o not in members:
            bad = mgr.and_exists(avail[o], bad, enc.actor_vs[o])
    good = bad ^ 1
    for c in members:
        good = mgr.AND(good, avail[c])
    return good


def _pick_move(enc: Encoding, members: list[int], moves: int) -> SubMove | None:
    if moves == FALSE:
        return None
    levels = [lv for a in members for lv in enc.act[a]]
    assignment = enc.mgr.pick_one(moves, levels)
    assert assignment is not None
    return enc.decode_move(assignment, members)


@dataclass(eq=False)
class _Result:
    enc: Encoding
    coalition: tuple[str, ...]
    stats: list[dict] = field(default_factory=list, repr=False)

    def _register(self) -> None:
        self.enc.mgr.register(self)

    def _count(self, f: int, within: int | None) -> int:
        if within is not None:
            f = self.enc.mgr.AND(f, within)
        return self.enc.count(f)


@dataclass(eq=False)
class SymbolicAttractor(_Result):
    """``win``: the attractor; ``layers[i]``: the stage ``X_i`` (cumulative, ``X_0`` the
    target)."""

    target: int = FALSE
    layers: list[int] = field(default_factory=list)
    win: int = FALSE

    def bdd_roots(self) -> list[int]:
        return [self.target, self.win, *self.layers]

    def contains(self, state: Sequence[int]) -> bool:
        """Can the coalition force the target from ``state``?"""
        return self.enc.holds(self.win, state)

    def rank(self, state: Sequence[int]) -> int | None:
        """The first stage containing ``state`` (the forced distance), or ``None``."""
        arr = self.enc._state_array(state)
        ev = self.enc.mgr.evaluate
        if not ev(self.win, arr):
            return None
        lo, hi = 0, len(self.layers) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if ev(self.layers[mid], arr):
                hi = mid
            else:
                lo = mid + 1
        return lo

    def count(self, within: int | None = None) -> int:
        """Number of winning states (within ``within`` if given, e.g. reachable states)."""
        return self._count(self.win, within)

    def strategy_move(self, state: Sequence[int]) -> SubMove | None:
        """A coalition sub-move that makes ``state`` join: every completion leads to a
        lower stage. ``None`` for target states and losing states."""
        r = self.rank(state)
        if not r:
            return None
        members = self.enc.actor_indices(self.coalition)
        moves = _winning_moves(self.enc, members, self.layers[r - 1], state)
        return _pick_move(self.enc, members, moves)


@dataclass(eq=False)
class SymbolicSafe(_Result):
    """``kernel``: the states from which the coalition can keep ``phi`` until a terminal
    state."""

    phi: int = FALSE
    kernel: int = FALSE

    def bdd_roots(self) -> list[int]:
        return [self.phi, self.kernel]

    def contains(self, state: Sequence[int]) -> bool:
        """Is ``state`` in the kernel?"""
        return self.enc.holds(self.kernel, state)

    def count(self, within: int | None = None) -> int:
        """Kernel size (within ``within`` if given, e.g. reachable states)."""
        return self._count(self.kernel, within)

    def strategy_move(self, state: Sequence[int]) -> SubMove | None:
        """A coalition sub-move all of whose completions stay in the kernel; ``None`` for
        terminal states and states outside the kernel."""
        enc = self.enc
        if not enc.holds(self.kernel, state) or enc.holds(enc.term, state):
            return None
        members = enc.actor_indices(self.coalition)
        return _pick_move(enc, members, _winning_moves(enc, members, self.kernel, state))


@dataclass(eq=False)
class SymbolicContested:
    """``forced``, ``blocked`` and ``contested`` predicates (over the domain)."""

    enc: Encoding
    forced: int
    blocked: int
    contested: int

    def __post_init__(self) -> None:
        self.enc.mgr.register(self)

    def bdd_roots(self) -> list[int]:
        return [self.forced, self.blocked, self.contested]

    def region(self, state: Sequence[int]) -> str:
        """``"forced"``, ``"blocked"`` or ``"contested"``."""
        if self.enc.holds(self.forced, state):
            return "forced"
        if self.enc.holds(self.blocked, state):
            return "blocked"
        return "contested"


@dataclass(eq=False)
class SymbolicReach:
    """``states``: every state reachable from ``initial``; ``layers[d]``: the states first
    reached at depth ``d`` (when kept); ``depth``: the number of breadth-first steps."""

    enc: Encoding
    initial: int
    states: int
    layers: list[int]
    depth: int = 0
    stats: list[dict] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self.enc.mgr.register(self)

    def bdd_roots(self) -> list[int]:
        return [self.initial, self.states, *self.layers]

    def contains(self, state: Sequence[int]) -> bool:
        return self.enc.holds(self.states, state)

    def count(self) -> int:
        """Number of reachable states."""
        return self.enc.count(self.states)


def _stat(enc: Encoding, k: int, t0: float, x: int, **extra: object) -> dict:
    mgr = enc.mgr
    return {
        "iteration": k,
        "seconds": round(time.perf_counter() - t0, 3),
        "nodes": mgr.node_count(x),
        "live_nodes": mgr.live_nodes,
        "peak_nodes": mgr.stats()["peak_nodes"],
        **extra,
    }


def attractor(
    enc: Encoding,
    coalition: Collection[str],
    target: int,
    on_iteration: Progress | None = None,
) -> SymbolicAttractor:
    """States from which ``coalition`` can force ``target`` (a state predicate)."""
    with enc.mgr.protecting(target):
        return _attractor(enc, coalition, target, on_iteration)


def _attractor(
    enc: Encoding,
    coalition: Collection[str],
    target: int,
    on_iteration: Progress | None,
) -> SymbolicAttractor:
    mgr = enc.mgr
    members, others = _split(enc, coalition)
    goal = mgr.AND(target, enc.dom)
    res = SymbolicAttractor(enc, tuple(coalition), target=goal)
    res._register()
    x = goal
    res.layers.append(x)
    t0 = time.perf_counter()
    while True:
        step = mgr.AND(_cpre_from(enc, members, others, enc.preimage(x)), enc.active)
        new = mgr.OR(goal, step)
        if new == x:
            break
        x = new
        res.layers.append(x)
        res.stats.append(_stat(enc, len(res.layers) - 1, t0, x))
        if on_iteration is not None:
            on_iteration(res.stats[-1])
        _maybe_gc(enc, [x, goal])
    res.win = x
    return res


def safe(
    enc: Encoding,
    coalition: Collection[str],
    phi: int,
    within: int | None = None,
    method: Literal["auto", "layered", "iterate"] = "auto",
    on_iteration: Progress | None = None,
) -> SymbolicSafe:
    """States from which ``coalition`` can keep ``phi`` until a terminal state.

    ``within`` (optional) is a set closed under successors, such as the result of
    :func:`reachable`: the kernel is computed inside it, and each step's argument is
    simplified with it as the care set. ``method``: ``"layered"`` (timed models only),
    ``"iterate"``, or ``"auto"`` (layered when timed)."""
    with enc.mgr.protecting(phi, within):
        return _safe(enc, coalition, phi, within, method, on_iteration)


def _safe(
    enc: Encoding,
    coalition: Collection[str],
    phi: int,
    within: int | None,
    method: str,
    on_iteration: Progress | None,
) -> SymbolicSafe:
    mgr = enc.mgr
    members, others = _split(enc, coalition)
    base = mgr.AND(phi, enc.dom)
    if within is not None:
        base = mgr.AND(base, within)
    res = SymbolicSafe(enc, tuple(coalition), phi=base)
    res._register()
    tick = enc.cm.index.get("tick")
    if method == "auto":
        method = "layered" if tick is not None else "iterate"
    if method == "layered" and tick is None:
        raise ModelError("the layered method needs a timed model")

    def step(x: int) -> int:
        arg = x if within is None or x == FALSE else mgr.simplify(x, within)
        return mgr.AND(_cpre_from(enc, members, others, enc.preimage(arg)), enc.active)

    t0 = time.perf_counter()
    if method == "layered":
        assert tick is not None
        horizon = enc.cm.horizon
        assert horizon is not None
        kernel = FALSE
        nxt = FALSE
        stay = enc.term
        for t in range(horizon, -1, -1):
            at_t = enc.cur_env[tick].get(t, FALSE)
            layer = mgr.AND(base, at_t)
            if layer != FALSE:
                keep = stay if nxt == FALSE else mgr.OR(stay, step(nxt))
                layer = mgr.AND(layer, keep)
            kernel = mgr.OR(kernel, layer)
            nxt = layer
            res.stats.append(_stat(enc, horizon - t, t0, layer, tick=t))
            if on_iteration is not None:
                on_iteration(res.stats[-1])
            _maybe_gc(enc, [kernel, nxt, base])
        res.kernel = kernel
        return res
    x = base
    k = 0
    while True:
        new = mgr.AND(base, mgr.OR(enc.term, step(x)))
        if new == x:
            break
        x = new
        k += 1
        res.stats.append(_stat(enc, k, t0, x))
        if on_iteration is not None:
            on_iteration(res.stats[-1])
        _maybe_gc(enc, [x, base])
    res.kernel = x
    return res


def contested(
    enc: Encoding,
    coalition: Collection[str],
    goal: int,
    kind: Literal["reach", "keep"],
) -> SymbolicContested:
    """Forced, blocked and contested regions for a reach or keep objective (as
    :func:`wavefront.engine.solve.contested`)."""
    mgr = enc.mgr
    members = set(enc.actor_indices(coalition))
    rest = [a.name for a in enc.cm.actors if a.index not in members]
    if kind not in ("reach", "keep"):
        raise ValueError(f"kind must be 'reach' or 'keep', not {kind!r}")
    goal = mgr.AND(goal, enc.dom)
    other = mgr.DIFF(enc.dom, goal)
    with mgr.protecting(goal, other):
        if kind == "reach":
            first = attractor(enc, coalition, goal)
            second = safe(enc, rest, other)
            forced, blocked = first.win, second.kernel
        else:
            first = safe(enc, coalition, goal)
            second = attractor(enc, rest, other)
            forced, blocked = first.kernel, second.win
    middle = mgr.DIFF(mgr.DIFF(enc.dom, forced), blocked)
    return SymbolicContested(enc, forced, blocked, middle)


def reachable(
    enc: Encoding,
    initial: int | None = None,
    check: bool = True,
    on_iteration: Progress | None = None,
    keep_layers: bool = False,
) -> SymbolicReach:
    """States reachable from ``initial`` (default: the model's initial states). With
    ``check``, raises :class:`ModelError` where :func:`wavefront.engine.explore` would.
    ``keep_layers`` keeps the breadth-first layers (the states first reached at each
    depth) in ``layers``; otherwise only the last frontier is kept."""
    with enc.mgr.protecting(initial):
        return _reachable(enc, initial, check, on_iteration, keep_layers)


def _reachable(
    enc: Encoding,
    initial: int | None,
    check: bool,
    on_iteration: Progress | None,
    keep_layers: bool,
) -> SymbolicReach:
    mgr = enc.mgr
    init = mgr.AND(enc.initial if initial is None else initial, enc.dom)
    states = init
    frontier = init
    layers = [init] if keep_layers else []
    depth = 0
    stats: list[dict] = []
    t0 = time.perf_counter()
    while frontier != FALSE:
        new = mgr.DIFF(enc.image(frontier, keep=[states, init, *layers]), states)
        if new == FALSE:
            break
        states = mgr.OR(states, new)
        frontier = new
        depth += 1
        if keep_layers:
            layers.append(new)
        stats.append(_stat(enc, depth, t0, states))
        if on_iteration is not None:
            on_iteration(stats[-1])
        _maybe_gc(enc, [states, frontier, init, *layers])
    res = SymbolicReach(enc, init, states, layers, depth, stats)
    if check:
        _check(enc, states)
    return res


def shortest(
    enc: Encoding,
    state: Sequence[int],
    target: int,
    max_depth: int | None = None,
) -> int | None:
    """The fewest transitions from ``state`` to a state in ``target`` (breadth-first
    images; terminal states are not expanded), or ``None`` if no target state is
    reachable (within ``max_depth`` steps, if given). This is the rank of ``state`` in the
    attractor of every actor, Nature included (the explicit ``distance(...).shortest``
    when ``target`` is the outside of a kernel), computed forward so that only states
    reachable from ``state`` are built."""
    mgr = enc.mgr
    with mgr.protecting(target):
        seen = frontier = enc.state_cube(state)
        depth = 0
        while frontier != FALSE:
            if mgr.AND(frontier, target) != FALSE:
                return depth
            if max_depth is not None and depth >= max_depth:
                return None
            with mgr.protecting(seen):
                nxt = enc.image(frontier, keep=[seen, target])
            frontier = mgr.DIFF(nxt, seen)
            seen = mgr.OR(seen, frontier)
            depth += 1
    return None


def _example(enc: Encoding, f: int) -> State:
    assignment = enc.mgr.pick_one(f, enc.state_levels)
    assert assignment is not None
    return enc.cube_to_state(assignment)


def _check(enc: Encoding, states: int) -> None:
    mgr, cm = enc.mgr, enc.cm
    overlap = mgr.AND(states, enc.ending_overlap)
    if overlap != FALSE:
        cm.ending_of(_example(enc, overlap))  # raises with the explicit engine's message
        raise ModelError("endings overlap on a reachable state")
    moving = mgr.DIFF(states, enc.term)
    stuck = mgr.DIFF(moving, enc.live)
    if stuck != FALSE:
        cm.available(_example(enc, stuck))  # raises naming the state and the actor
        raise ModelError("an actor has no available action in a reachable state")
    bad = mgr.exists(mgr.and_all([moving, enc.moves, enc.error]), enc.action_vs)
    if bad != FALSE:
        state = _example(enc, bad)
        avail = cm.available(state)
        for jm in itertools.product(*avail):
            if enc.is_error(state, jm):
                cm.step(state, jm)  # raises with the explicit engine's message
        raise ModelError(f"a transition from {cm.format_state(state)} is rejected")


def witness(
    enc: Encoding,
    cm: CompiledModel,
    state: Sequence[int],
    target: int,
    coalition: Collection[str],
    result: SymbolicAttractor | None = None,
) -> list[tuple[State, tuple[int, ...] | None]] | None:
    """A play from ``state`` into ``target`` in which ``coalition`` follows the symbolic
    attractor strategy and the other actors, at every step, pick the completion leading to
    the highest stage (the latest the target can be forced). Returns ``[(state,
    joint_move), ..., (last_state, None)]`` with explicit states and joint moves (replayable
    with ``cm.step``), or ``None`` if the coalition cannot force the target from ``state``.
    ``result`` may pass a precomputed attractor for the same coalition and target."""
    res = result if result is not None else attractor(enc, coalition, target)
    members = enc.actor_indices(coalition)
    state = tuple(state)
    if not res.contains(state):
        return None
    trace: list[tuple[State, tuple[int, ...] | None]] = []
    while not enc.holds(res.target, state):
        sub = res.strategy_move(state)
        assert sub is not None, "a winning non-target state has a strategy move"
        avail = cm.available(state)
        for a, j in zip(members, sub, strict=True):
            if j not in avail[a]:
                raise ModelError(f"strategy move {sub} is not available in {state}")
        fixed = dict(zip(members, sub, strict=True))
        choices = [[fixed[a]] if a in fixed else acts for a, acts in enumerate(avail)]
        best: tuple[int, tuple[int, ...], State] | None = None
        for jm in itertools.product(*choices):
            nxt = cm.step(state, jm)
            r = res.rank(nxt)
            if r is None:
                raise ModelError(f"strategy move {sub} lets {jm} leave the attractor")
            if best is None or r > best[0]:
                best = (r, jm, nxt)
        assert best is not None
        trace.append((state, best[1]))
        state = best[2]
    trace.append((state, None))
    return trace
