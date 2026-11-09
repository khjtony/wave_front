"""The layered lifting of docs/cw_v1_decisions.md D7: exact kernels, attractors and
distances of a flattened game (framework spec section 14) computed on the coarse BDD
encoding, one tick layer at a time, with each crisis sub-game explored explicitly once.

Analysis code over the public pieces of ``wavefront.symbolic`` (the encoding's
availability, next-state functions and preimage, the BDD manager) and of
``wavefront.engine`` (``explore``, ``attractor``, ``safe``); not a framework change. The
framework's symbolic engine does not encode the flattened game (spec section 15); this module
does not either: it values the crisis branch of each coarse state from the sub-game's
explicit graph.

Why it is exact. In the flattened game every transition from a coarse state at tick t leads
either to a coarse state at tick t + 1 or, when the crisis actor plays the crisis action, to
the sub-game's first fine state, whose plays all return to a coarse state at tick t + 1.
So the value of a coarse state at tick t depends only on the values at tick t + 1, and a
fixpoint can be computed backward one tick layer at a time. At a layer, with ``X`` the
layer after it:

- the moves without a crisis action are valued by the controllable predecessor with the
  crisis actions masked out of availability (the analysis build with the guard part
  ``dropped: FALSE`` of D7 (i), written as a mask on the same encoding);
- the crisis branch is valued by the lifted value ``L(s)`` (D7 (ii)): for an exit ``e`` of
  the sub-game (the coarse levels its exit map sets), ``R_e(X)`` is the set of coarse states
  whose return transition with exit ``e`` lands in ``X`` (the preimage of ``X`` with the
  exit's levels substituted, restricted to the return move), and ``L(s)`` holds iff the
  coalition can force the sub-game, explored explicitly once per entry value, into terminal
  fine states whose exits all have ``s`` in ``R_e(X)``;
- a layer is ``phi & (Term | F(X))`` for a kernel and ``T | F(X)`` for an attractor, with
  ``F(X) = active & (CPre_masked(X) | (avail_crisis & L))`` when the crisis actor is in the
  coalition and ``active & CPre_masked(X) & (~avail_crisis | L)`` when it is not (D7 (iii)).

Distances (fewest transitions of arbitrary play, a crisis counting its entry, its fine steps
and its return) are computed backward by weighted layers: a coarse move costs 1, a crisis
with exit ``e`` costs 2 plus the fewest fine steps from the entry to a terminal fine state
with that exit, and (for the distance out of a kernel) a fine state outside the lifted kernel
costs 1 plus the fewest fine steps to it.

Conditions: the exit maps read only the fine state (and are evaluated once per terminal fine
state) and the entry maps read only the coarse variables named in ``entry_reads``, asserted
on cw_v1 in tests/coldwar_v1/test_yearwise.py (not checked by :class:`Lift`); no coarse
variable written by an exit is written by a delayed effect, the coarse model has no latch,
and no two crisis actions are available in one state, checked when a :class:`Lift` is built.
Like the symbolic engine (spec section 15), transitions on which the explicit engine would
raise (an exit lowering a monotone variable) are not excluded.

The explicit form (:class:`Window`, R V6): the coarse game explored explicitly to the tick of
a single crisis, that tick's states valued one step ahead with the crisis lifted, and the cut
one tick after it.
"""

from __future__ import annotations

import itertools
from collections import deque
from collections.abc import Callable, Collection, Iterable, Sequence
from dataclasses import dataclass, field

from tests.coldwar.common import Cut, Forbid
from wavefront.engine import attractor as eattractor
from wavefront.engine import explore
from wavefront.engine import safe as esafe
from wavefront.symbolic.bdd import FALSE, TRUE

# The coarse variables each sub-game's entry map reads (every other entry map is constant).
ENTRY_READS = {"able_archer_1983": ("belief_USSR_USA",)}

State = tuple[int, ...]


def idle_pairs(cm, actor: str) -> frozenset[tuple[str, str]]:
    """Every declared (non-built-in) action of ``actor`` in ``cm``: forbidding them leaves
    the actor idle."""
    a = next(x for x in cm.actors if x.name == actor)
    return frozenset((actor, x.name) for x in a.actions if not x.is_idle)


def _resolve(spec, value) -> int:
    names = [str(x) for x in spec.levels]
    return names.index(str(value))


def _bfs(g, source: int) -> list[int | None]:
    dist: list[int | None] = [None] * g.size()
    dist[source] = 0
    queue = deque([source])
    while queue:
        s = queue.popleft()
        for t in g.succ[s]:
            if dist[t] is None:
                dist[t] = dist[s] + 1
                queue.append(t)
    return dist


@dataclass(eq=False)
class _Entry:
    """One entry value of a sub-game: the coarse condition selecting it, the fine graph from
    its first fine state, the exit index of each terminal fine state and the fine
    distances from the first fine state (all actors)."""

    cond: int
    g: object
    exit_of: dict[int, int]
    dist: list[int | None]
    first_terminal: dict[int, int]  # exit index -> a terminal fine id with that exit
    _families: dict = field(default_factory=dict)
    _kernels: dict = field(default_factory=dict)

    def kernel(self, coalition: tuple[str, ...], good: frozenset[int]) -> set[int]:
        """Fine ids from which ``coalition`` forces a terminal fine state whose exit is in
        ``good`` (the lifted kernel when ``good`` is the set of exits returning into the
        kernel; the sub-game is timed, so every play ends in a terminal fine state)."""
        key = (coalition, good)
        if key not in self._kernels:
            g = self.g
            target = {i for i, e in self.exit_of.items() if e in good}
            self._kernels[key] = eattractor(g, list(coalition), target).win
        return self._kernels[key]

    def family(self, coalition: tuple[str, ...], n_exits: int) -> list[frozenset[int]]:
        """The inclusion-minimal sets E of exit indices such that ``coalition`` forces the
        sub-game from its first fine state into terminal fine states with exits in E."""
        if coalition not in self._families:
            first = self.g.initial[0]
            found: list[frozenset[int]] = []
            for size in range(n_exits + 1):
                for c in itertools.combinations(range(n_exits), size):
                    e = frozenset(c)
                    if any(m <= e for m in found):
                        continue
                    if first in self.kernel(coalition, e):
                        found.append(e)
            self._families[coalition] = found
        return self._families[coalition]


@dataclass(eq=False)
class _Crisis:
    k: int
    label: str
    actor: int
    action: int
    actor_name: str
    avail: int  # BDD: the crisis action is available (and not forbidden)
    ret: tuple[int, ...]  # the coarse joint move of the return transition
    flat_ret: tuple[int, ...]  # the flat joint move entering / returning
    exits: list[tuple[tuple[int, int], ...]]  # distinct exits: ((coarse var, level), ...)
    entries: list[_Entry]
    fine_actors: frozenset[str]

    def fine_coalition(self, coalition: Iterable[str]) -> tuple[str, ...]:
        return tuple(sorted(a for a in coalition if a in self.fine_actors))


class _Holder:
    """Keeps BDD edges alive across garbage collection while it lives."""

    def __init__(self, mgr) -> None:
        self.edges: list[int] = []
        mgr.register(self)

    def bdd_roots(self) -> list[int]:
        return self.edges

    def keep(self, f: int) -> int:
        self.edges.append(f)
        return f


@dataclass(eq=False)
class LayeredResult:
    """A kernel (``kind="safe"``) or attractor (``kind="reach"``) of the flattened game on
    coarse states, over the whole domain: ``layers[t]`` the states of tick t in it."""

    lift: Lift
    kind: str
    coalition: tuple[str, ...]
    base: int
    cut: int | None
    layers: dict[int, int]
    win: int

    def bdd_roots(self) -> list[int]:
        return [self.base, self.win, *self.layers.values()]

    def contains(self, state: Sequence[int]) -> bool:
        return self.lift.enc.holds(self.win, state)


@dataclass(eq=False)
class LayeredDistance:
    """Weighted backward layers: ``layers[d]`` the coarse states at distance at most d."""

    lift: Lift
    layers: list[int]

    def bdd_roots(self) -> list[int]:
        return list(self.layers)

    def rank(self, state: Sequence[int]) -> int | None:
        enc = self.lift.enc
        arr = enc._state_array(state)
        ev = enc.mgr.evaluate
        if not ev(self.layers[-1], arr):
            return None
        lo, hi = 0, len(self.layers) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if ev(self.layers[mid], arr):
                hi = mid
            else:
                lo = mid + 1
        return lo


class Lift:
    """The layered lifting of a flattened game ``fm`` over the BDD encoding ``enc`` of its
    coarse model. ``forbid`` is a set of ``(actor, action)`` pairs never available, in the
    coarse game and in every sub-game (the restricted games of ``Forbid``); a built-in
    ``idle``/``none`` may not be forbidden."""

    def __init__(
        self,
        fm,
        enc,
        entry_reads: dict[str, Sequence[str]] | None = None,
        forbid: Collection[tuple[str, str]] = (),
    ) -> None:
        self.fm = fm
        self.cm = cm = fm.coarse
        self.enc = enc
        self.mgr = mgr = enc.mgr
        self.forbid = frozenset(forbid)
        self.holder = _Holder(mgr)
        keep = self.holder.keep
        entry_reads = ENTRY_READS if entry_reads is None else entry_reads
        self.tick = cm.index["tick"]
        if cm._latches:
            raise ValueError("the layered lifting assumes a coarse model without latches")

        crisis_moves = {(c.actor, c.action) for c in fm._compiled}
        self.avail_d: list[int] = []  # masked: forbidden and crisis actions removed
        avail_f: list[int] = []  # forbidden actions removed
        for actor in cm.actors:
            row = enc.action_avail[actor.index]
            dropped = FALSE
            free = FALSE
            for j, g in enumerate(row):
                act = actor.actions[j]
                forbidden = (actor.name, act.name) in self.forbid
                if forbidden and act.is_idle:
                    raise ValueError(f"the built-in {actor.name}.{act.name} may not be forbidden")
                ch = mgr.AND(enc.chosen(actor.index, j), g)
                if not forbidden:
                    free = mgr.OR(free, ch)
                    if (actor.index, j) not in crisis_moves:
                        dropped = mgr.OR(dropped, ch)
            self.avail_d.append(keep(dropped))
            avail_f.append(free)
        live = mgr.and_all(mgr.exists(av, vs) for av, vs in zip(avail_f, enc.actor_vs))
        self.active = keep(mgr.and_all([enc.dom, enc.term ^ 1, live]))
        self.at = [
            keep(mgr.AND(enc.cur_env[self.tick].get(t, FALSE), enc.dom))
            for t in range(cm.horizon + 1)
        ]

        delayed = {
            getattr(e, "var", None)
            for actor in cm.model.actors + [cm.model.nature()]
            for x in actor.actions
            if x.delay
            for e in x.effects
        }
        self.crises: list[_Crisis] = []
        for k, comp in enumerate(fm._compiled):
            c = comp.crisis
            actor = cm.actors[comp.actor]
            act_name = actor.actions[comp.action].name
            if (actor.name, act_name) in self.forbid:
                continue
            if any(j < 0 for j in comp.ret_coarse):
                raise ValueError(f"crisis {c.label}: an actor without idle in the return move")
            avail = keep(mgr.AND(enc.action_avail[comp.actor][comp.action], enc.dom))
            reads = tuple(entry_reads.get(c.label, ()))
            sub = c.sub
            pairs = [
                (a.name, x.name)
                for a in sub.actors
                for x in a.actions
                if (a.name, x.name) in self.forbid
            ]
            fine_model = Forbid(sub, pairs) if pairs else sub
            exits: list[tuple[tuple[int, int], ...]] = []
            entries: list[_Entry] = []
            base = [v.init[0] for v in cm.variables]
            idx = [cm.index[r] for r in reads]
            for values in itertools.product(*(range(cm.variables[i].size) for i in idx)):
                s = list(base)
                cond = enc.dom
                for i, x in zip(idx, values, strict=True):
                    s[i] = x
                    cond = mgr.AND(cond, enc.cur_env[i][x])
                s = tuple(s)
                first = fm.step(s, comp.ret_move)
                g = explore(fine_model, initial=[fm.split(first)[2]], max_states=2_000_000)
                year = dict(cm.state_dict(s))
                exit_of: dict[int, int] = {}
                first_terminal: dict[int, int] = {}
                for i in range(g.size()):
                    if not g.terminal[i]:
                        continue
                    values_e = c.exit(dict(sub.state_dict(g.states[i])), year)
                    e = tuple(
                        sorted(
                            (cm.index[n], _resolve(cm.variables[cm.index[n]], v))
                            for n, v in values_e.items()
                        )
                    )
                    for vi, _ in e:
                        if cm.variables[vi].name in delayed:
                            raise ValueError(f"crisis {c.label}: a delayed effect writes an exit")
                    if e not in exits:
                        exits.append(e)
                    exit_of[i] = exits.index(e)
                    first_terminal.setdefault(exit_of[i], i)
                entries.append(
                    _Entry(keep(cond), g, exit_of, _bfs(g, g.initial[0]), first_terminal)
                )
            self.crises.append(
                _Crisis(
                    k,
                    c.label,
                    comp.actor,
                    comp.action,
                    actor.name,
                    avail,
                    tuple(comp.ret_coarse),
                    tuple(comp.ret_move),
                    exits,
                    entries,
                    frozenset(a.name for a in sub.actors),
                )
            )
        for a, b in itertools.combinations(self.crises, 2):
            if mgr.AND(a.avail, b.avail) != FALSE:
                raise ValueError(f"crises {a.label} and {b.label} are available together")
        self._ret_cache: dict[tuple[int, int, int], int] = {}

    # -- building blocks ----------------------------------------------------------------
    def _move_assignment(self, move: Sequence[int]) -> dict[int, int]:
        out = {}
        for a, j in enumerate(move):
            bits = self.enc.act[a]
            k = len(bits)
            for b, lv in enumerate(bits):
                out[lv] = (j >> (k - 1 - b)) & 1
        return out

    def ret_pre(self, crisis: _Crisis, e: int, x: int) -> int:
        """``R_e(X)``: the coarse states whose return transition from ``crisis`` with exit
        ``e`` lands in ``x``."""
        key = (crisis.k, e, x)
        hit = self._ret_cache.get(key)
        if hit is not None:
            return hit
        enc, mgr = self.enc, self.mgr
        sub = {}
        for i, level in crisis.exits[e]:
            bits = enc.cur[i]
            n = len(bits)
            for b, lv in enumerate(bits):
                sub[lv] = TRUE if (level >> (n - 1 - b)) & 1 else FALSE
        xe = mgr.compose(x, sub) if sub else x
        p = mgr.restrict(enc.preimage(xe), self._move_assignment(crisis.ret))
        out = self.holder.keep(mgr.AND(p, enc.dom))
        self.holder.keep(x)
        self._ret_cache[key] = out
        return out

    def lifted(self, crisis: _Crisis, x: int, coalition: Collection[str]) -> int:
        """``L``: the coarse states from which ``coalition`` forces the sub-game entered
        there into returns in ``x``."""
        mgr = self.mgr
        fc = crisis.fine_coalition(coalition)
        out = FALSE
        for entry in crisis.entries:
            any_e = FALSE
            for family in entry.family(fc, len(crisis.exits)):
                any_e = mgr.OR(
                    any_e, mgr.and_all(self.ret_pre(crisis, e, x) for e in sorted(family))
                )
            out = mgr.OR(out, mgr.AND(entry.cond, any_e))
        return out

    def _cpre_masked(self, members: list[int], others: list[int], x: int) -> int:
        mgr, enc = self.mgr, self.enc
        bad = enc.preimage(x) ^ 1
        for o in others:
            bad = mgr.and_exists(self.avail_d[o], bad, enc.actor_vs[o])
        good = bad ^ 1
        for c in members:
            good = mgr.and_exists(self.avail_d[c], good, enc.actor_vs[c])
        return good

    def _split(self, coalition: Collection[str]) -> tuple[list[int], list[int]]:
        members = self.enc.actor_indices(coalition)
        others = [a.index for a in self.cm.actors if a.index not in set(members)]
        return members, others

    def step(self, coalition: Collection[str], x: int, t: int) -> int:
        """``F(X)`` on the layer of tick ``t``: the coarse states of tick t from which
        ``coalition`` forces the next coarse state into ``x`` (a crisis entered there being
        played out to its return)."""
        mgr = self.mgr
        members, others = self._split(coalition)
        r = self._cpre_masked(members, others, x)
        for crisis in self.crises:
            here = mgr.AND(crisis.avail, self.at[t])
            if here == FALSE:
                continue
            lift = self.lifted(crisis, x, coalition)
            if crisis.actor in members:
                r = mgr.OR(r, mgr.AND(here, lift))
            else:
                r = mgr.AND(r, mgr.OR(here ^ 1, lift))
        return mgr.and_all([r, self.active, self.at[t]])

    def _fixpoint(self, coalition, base: int, kind: str, cut: int | None) -> LayeredResult:
        mgr, enc = self.mgr, self.enc
        top = self.cm.horizon if cut is None else min(cut, self.cm.horizon)
        res = LayeredResult(self, kind, tuple(coalition), base, cut, {}, FALSE)
        mgr.register(res)
        nxt = FALSE
        for t in range(top, -1, -1):
            layer = self.at[t]
            if t == top:
                y = mgr.AND(base, layer)
            elif kind == "safe":
                y = mgr.and_all([base, layer, mgr.OR(enc.term, self.step(coalition, nxt, t))])
            else:
                y = mgr.AND(layer, mgr.OR(base, self.step(coalition, nxt, t)))
            res.layers[t] = y
            res.win = mgr.OR(res.win, y)
            nxt = y
            mgr.maybe_gc([nxt])
        return res

    # -- fixpoints ----------------------------------------------------------------------
    def kernel(self, coalition: Collection[str], phi: int, cut: int | None = None):
        """The states from which ``coalition`` keeps ``phi`` (coarse states; every fine state
        satisfies every coarse invariant) until a terminal state. With ``cut``, states at
        tick ``cut`` are terminal and kept iff in ``phi`` (pass ``phi | tick >= cut`` to keep
        them all)."""
        return self._fixpoint(coalition, phi, "safe", cut)

    def attractor(self, coalition: Collection[str], target: int, cut: int | None = None):
        """The states from which ``coalition`` forces a coarse state in ``target``."""
        return self._fixpoint(coalition, target, "reach", cut)

    def distance(self, target: int, kernel: LayeredResult | None = None, cut=None):
        """Fewest transitions of arbitrary play from each coarse state to ``target``; with
        ``kernel`` (a :meth:`kernel` result), to a state outside it, fine states outside the
        lifted kernel included (``target`` is then ignored)."""
        mgr, enc = self.mgr, self.enc
        res = LayeredDistance(self, [])
        mgr.register(res)
        top = self.cm.horizon if cut is None else min(cut, self.cm.horizon)
        moving = mgr.DIFF(self.active, mgr.or_all(self.at[t] for t in range(top, len(self.at))))
        everyone = [a.index for a in self.cm.actors]
        contribs: list[tuple[int, Callable[[int], int]]] = []  # (weight, f(layer) -> BDD)
        if kernel is not None:
            target = mgr.DIFF(enc.dom, kernel.win)
        target = mgr.AND(target, enc.dom)
        fine_extra: dict[int, int] = {}  # weight -> BDD
        for crisis in self.crises:
            here = mgr.AND(crisis.avail, moving)
            if here == FALSE:
                continue
            for entry in crisis.entries:
                for e in range(len(crisis.exits)):
                    ds = [entry.dist[i] for i, x in entry.exit_of.items() if x == e]
                    ds = [d for d in ds if d is not None]
                    if not ds:
                        continue
                    w = 2 + min(ds)
                    cond = mgr.AND(here, entry.cond)
                    contribs.append((w, self._ret_contrib(crisis, e, cond)))
                if kernel is None:
                    continue
                fc = crisis.fine_coalition(kernel.coalition)
                n = len(crisis.exits)
                into = [self.ret_pre(crisis, e, kernel.win) for e in range(n)]
                for size in range(n + 1):
                    for comb in itertools.combinations(range(n), size):
                        good = frozenset(comb)
                        lk = entry.kernel(fc, good)
                        outside = [
                            entry.dist[i]
                            for i in range(entry.g.size())
                            if i not in lk and entry.dist[i] is not None
                        ]
                        if not outside:
                            continue
                        w = 1 + min(outside)
                        exact = mgr.and_all(into[e] if e in good else into[e] ^ 1 for e in range(n))
                        cond = mgr.and_all([here, entry.cond, exact])
                        fine_extra[w] = mgr.OR(fine_extra.get(w, FALSE), cond)
        for w, cond in fine_extra.items():
            self.holder.keep(cond)
            contribs.append((w, lambda _layer, c=cond: c))
        maxw = max([1, *(w for w, _ in contribs)])
        layers = res.layers
        layers.append(target)
        last_change = 0
        d = 0
        while True:
            d += 1
            prev = layers[-1]
            good = enc.preimage(prev)
            for c in everyone:
                good = mgr.and_exists(self.avail_d[c], good, enc.actor_vs[c])
            new = mgr.OR(prev, mgr.AND(good, moving))
            for w, f in contribs:
                if w <= d:
                    new = mgr.OR(new, f(layers[d - w]))
            layers.append(new)
            if new != prev:
                last_change = d
            elif d - last_change > maxw:
                break
            mgr.maybe_gc([new, target])
        # trim the trailing unchanged layers
        while len(layers) > 1 and layers[-1] == layers[-2]:
            layers.pop()
        return res

    def _ret_contrib(self, crisis: _Crisis, e: int, cond: int) -> Callable[[int], int]:
        self.holder.keep(cond)

        def f(layer: int) -> int:
            return self.mgr.AND(cond, self.ret_pre(crisis, e, layer))

        return f

    # -- explicit reading ---------------------------------------------------------------
    def crisis_at(self, state: Sequence[int]) -> _Crisis | None:
        for c in self.crises:
            if self.enc.holds(c.avail, state):
                return c
        return None

    def entry_of(self, crisis: _Crisis, state: Sequence[int]) -> _Entry:
        return next(e for e in crisis.entries if self.enc.holds(e.cond, state))

    def return_state(self, crisis: _Crisis, state: Sequence[int], e: int) -> State:
        """The coarse state the crisis entered from ``state`` returns to with exit ``e``."""
        entry = self.entry_of(crisis, state)
        h = entry.g.states[entry.first_terminal[e]]
        return self.fm.step(tuple(state) + (crisis.k,) + tuple(h), crisis.flat_ret)

    def lifted_ids(self, crisis: _Crisis, state, coalition, member) -> set[int]:
        """The fine ids of the sub-game entered from ``state`` in ``coalition``'s lifted
        value, the coarse value at the returns read by ``member``."""
        entry = self.entry_of(crisis, state)
        good = frozenset(
            e
            for e in range(len(crisis.exits))
            if e in entry.first_terminal and member(self.return_state(crisis, state, e))
        )
        return entry.kernel(crisis.fine_coalition(coalition), good)

    def available(self, state: Sequence[int]) -> list[list[int]]:
        """Per actor, the available coarse actions with the forbidden ones removed."""
        out = []
        for a, acts in zip(self.cm.actors, self.cm.available(state), strict=True):
            out.append([j for j in acts if (a.name, a.actions[j].name) not in self.forbid])
        return out

    def strategy_move(self, res: LayeredResult, state: Sequence[int]):
        """A coalition sub-move (actor order) all of whose completions keep the play in
        ``res`` (the next layer, or the lifted value when it enters a crisis); ``None`` if
        the state is not in ``res``, is terminal or (for an attractor) is in the target."""
        state = tuple(state)
        enc = self.enc
        if not res.contains(state) or enc.holds(enc.term, state):
            return None
        if res.kind == "reach" and enc.holds(res.base, state):
            return None
        t = state[self.tick]
        nxt = res.layers.get(t + 1, FALSE)
        crisis = self.crisis_at(state)
        lifted_ok = None
        if crisis is not None:
            first = self.entry_of(crisis, state).g.initial[0]
            ids = self.lifted_ids(crisis, state, res.coalition, lambda s: enc.holds(nxt, s))
            lifted_ok = first in ids
        members, others = self._split(res.coalition)
        avail = self.available(state)
        for sub in itertools.product(*(avail[m] for m in members)):
            fixed = dict(zip(members, sub, strict=True))
            if crisis is not None and fixed.get(crisis.actor) == crisis.action:
                if lifted_ok:
                    return sub
                continue
            ok = True
            for rest in itertools.product(*(avail[o] for o in others)):
                move = [0] * len(avail)
                for m, j in fixed.items():
                    move[m] = j
                for o, j in zip(others, rest, strict=True):
                    move[o] = j
                if crisis is not None and move[crisis.actor] == crisis.action:
                    ok = bool(lifted_ok)
                else:
                    ok = enc.holds(nxt, self.cm.step(state, tuple(move)))
                if not ok:
                    break
            if ok:
                return sub
        return None


# -- the explicit form (R V6) --------------------------------------------------------------
class Window:
    """The layered lifting in its explicit form for a window ending one tick after a single
    crisis: the coarse game explored explicitly from ``starts`` to tick ``cut - 1`` (the
    crisis tick), each state of that tick valued one step ahead (its coarse successors are
    cut states, its crisis branch lifted from the sub-game explored once), and states at tick
    ``cut`` terminal (the ``Cut`` of decisions D5). Exact for the flattened game cut at
    ``cut`` when no crisis action is available before tick ``cut - 1``, which is checked."""

    def __init__(self, lift: Lift, starts: Iterable[State], cut: int, max_states=6_000_000):
        self.lift = lift
        self.cm = cm = lift.cm
        self.cut = cut
        self.T = cut - 1
        pairs = [
            (a.name, x.name)
            for a in cm.actors
            for x in a.actions
            if (a.name, x.name) in lift.forbid
        ]
        model = Forbid(cm, pairs) if pairs else cm
        self.g = g = explore(Cut(model, self.T), initial=list(starts), max_states=max_states)
        tick = lift.tick
        self.crisis = None
        for i in range(g.size()):
            s = g.states[i]
            if g.terminal[i]:
                continue
            c = lift.crisis_at(s)
            if c is not None:
                raise ValueError(f"crisis {c.label} available before the window's last tick")
        # one step ahead from each state at the crisis tick
        self.edge: dict[int, list[tuple[tuple[int, ...], State | None]]] = {}
        self.crisis_of: dict[int, _Crisis] = {}
        for i in range(g.size()):
            if g.ending[i] != "CUT":
                continue
            s = g.states[i]
            assert s[tick] == self.T
            c = lift.crisis_at(s)
            if c is not None:
                self.crisis_of[i] = c
            avail = lift.available(s)
            rows = []
            for move in itertools.product(*avail):
                if c is not None and move[c.actor] == c.action:
                    rows.append((move, None))
                else:
                    rows.append((move, cm.step(s, move)))
            self.edge[i] = rows

    def _cut_value(self, s: State, phi: Callable[[State], bool]) -> bool:
        return bool(phi(s))

    def kernel(self, coalition, phi: Callable[[State], bool]) -> set[int]:
        """Ids of ``g`` in the kernel of ``phi`` (a coarse predicate; cut states kept iff
        ``phi``)."""
        lift, g = self.lift, self.g
        members, others = lift._split(coalition)
        value: dict[int, bool] = {}
        for i, rows in self.edge.items():
            s = g.states[i]
            if not phi(s):
                value[i] = False
                continue
            c = self.crisis_of.get(i)
            lifted_ok = False
            if c is not None:
                first = lift.entry_of(c, s).g.initial[0]
                ids = lift.lifted_ids(c, s, coalition, lambda r: bool(phi(r)))
                lifted_ok = first in ids
            value[i] = self._forces(rows, members, others, c, lifted_ok, lambda r: bool(phi(r)))
        phi_ids = {i for i in range(g.size()) if phi(g.states[i])}
        keep = {i for i in phi_ids if g.ending[i] != "CUT" or value[i]}
        return esafe(g, list(coalition), keep).kernel

    @staticmethod
    def _forces(rows, members, others, c, lifted_ok, good) -> bool:
        by_sub: dict[tuple[int, ...], bool] = {}
        for move, nxt in rows:
            sub = tuple(move[m] for m in members)
            ok = lifted_ok if nxt is None else good(nxt)
            by_sub[sub] = by_sub.get(sub, True) and ok
        return any(by_sub.values())

    def distance(self, start: State, target: Callable[[State], bool], kernel=None, coalition=()):
        """Fewest transitions from ``start`` to a coarse state satisfying ``target``; with
        ``kernel`` (ids from :meth:`kernel` for ``coalition`` and the coarse predicate
        ``target`` as its ``phi``), out of the kernel, fine states outside the lifted
        kernel included. ``None`` if unreachable."""
        lift, g = self.lift, self.g
        dist = _bfs(g, g.index[tuple(start)])
        best = None

        def offer(d):
            nonlocal best
            if d is not None and (best is None or d < best):
                best = d

        if kernel is None:
            hit = {i for i in range(g.size()) if target(g.states[i])}
            succ_bad = target
        else:
            hit = set(range(g.size())) - kernel
            phi = target

            def succ_bad(r):
                return not phi(r)

        for i in hit:
            offer(dist[i])
        for i, rows in self.edge.items():
            if dist[i] is None or i in hit:
                continue
            s = g.states[i]
            local = None
            for _, nxt in rows:
                if nxt is not None and succ_bad(nxt):
                    local = 1
                    break
            c = self.crisis_of.get(i)
            if c is not None and local != 1:
                entry = lift.entry_of(c, s)
                for e in range(len(c.exits)):
                    if e not in entry.first_terminal:
                        continue
                    if succ_bad(lift.return_state(c, s, e)):
                        ds = [entry.dist[j] for j, x in entry.exit_of.items() if x == e]
                        ds = [x for x in ds if x is not None]
                        if ds and (local is None or 2 + min(ds) < local):
                            local = 2 + min(ds)
                if kernel is not None:
                    ids = lift.lifted_ids(c, s, coalition, lambda r: bool(phi(r)))
                    outside = [
                        entry.dist[j]
                        for j in range(entry.g.size())
                        if j not in ids and entry.dist[j] is not None
                    ]
                    if outside and (local is None or 1 + min(outside) < local):
                        local = 1 + min(outside)
            if local is not None:
                offer(dist[i] + local)
        return best


# -- distances on an explicit flattened graph ----------------------------------------------
def dag_distance(g, fm, targets: set[int], boundary: Callable[[State], int | None] | None):
    """Fewest transitions from every state of an explicit flattened graph ``g`` (explored
    with a ``Cut``) to ``targets``, a cut state not in ``targets`` being valued by
    ``boundary`` (its distance beyond the cut, or None). The flattened timed game is acyclic
    (a coarse move advances the coarse tick, a fine move the fine tick, a return the coarse
    tick), so one pass in reverse order of (coarse tick, fine or not, fine tick) suffices."""
    n = fm.n
    tick = fm.index["tick"]
    subs = [c.crisis.sub for c in fm._compiled]

    def key(i):
        s = g.states[i]
        if len(s) == n:
            return (s[tick], 0, 0)
        k = s[n]
        h = s[n + 1 :]
        return (s[tick], 1, h[subs[k].index["tick"]])

    order = sorted(range(g.size()), key=key, reverse=True)
    dist: list[int | None] = [None] * g.size()
    for i in order:
        if i in targets:
            dist[i] = 0
            continue
        if g.ending[i] == "CUT":
            dist[i] = boundary(g.states[i]) if boundary is not None else None
            continue
        best = None
        for j in g.succ[i]:
            d = dist[j]
            if d is not None and (best is None or d + 1 < best):
                best = d + 1
        dist[i] = best
    return dist
