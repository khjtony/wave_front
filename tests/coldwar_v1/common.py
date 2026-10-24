"""Shared machinery for the Cold War v1 tests: per-hypothesis builds, hindsight and replay
states from ``snapshots/cw_v1``, the realized play on the flattened game, and the analysis
devices of docs/cw_v1_decisions.md (the cut-off, restricted games, symbolic boundary values
for explicit graphs, lifted crisis kernels, the composite engine and the layered lifting of D7,
the latter in tests/coldwar_v1/layered.py). Analysis devices only; the model is
``models/cw/v1.py`` with ``models/cw/crises/`` and the readings are decisions section R.

The generic devices (``Cut``, ``Forbid``, ``bfs_distance``, ``minimal_coalitions``,
``fortune``, ``lifted_kernel``, ...) are v0's, imported from tests/coldwar/common.py.
"""

from __future__ import annotations

import os
from functools import lru_cache

from models.cw import v1
from models.cw.snapshots_v1 import snapshot_state
from models.ww2.hypotheses import fixed_model, realized_moves
from tests.coldwar.common import (  # noqa: F401  (re-exported for the scenario tests)
    ADVERSE,
    HYPS,
    OPP,
    Cut,
    Forbid,
    Timer,
    bfs_distance,
    bfs_path,
    compare,
    ending_ids,
    far,
    fmt,
    fortune,
    ids_where,
    lifted_attractor,
    lifted_kernel,
    minimal_coalitions,
    minimal_relaxation_sets,
    move_names,
)
from tests.coldwar_v1.layered import Lift, idle_pairs
from wavefront.engine import explore
from wavefront.model.compile import CompiledModel

# The switch for the first sight of V1 to V10 (docs/cw_v1_decisions.md D8): the registered
# scenario tests run only with WF_FIRST_SIGHT_CWV1=1, set by the owner for the one run.
FIRST_SIGHT_ENV = "WF_FIRST_SIGHT_CWV1"
FIRST_SIGHT = os.environ.get(FIRST_SIGHT_ENV) == "1"

YEAR0 = v1.YEAR0
CRISIS_DATA = v1.DATA / "crises"


def tick(year: int) -> int:
    return year - YEAR0


# -- builds ---------------------------------------------------------------------------------
@lru_cache(maxsize=None)
def model_of(
    aims: str,
    prc_principal: bool = True,
    frozen_oversight: bool = False,
    us_crisis_options: bool = True,
):
    m = v1.build(prc_principal, frozen_oversight, us_crisis_options)
    return fixed_model(m, aims_USSR=aims)


@lru_cache(maxsize=None)
def compiled(
    aims: str,
    prc_principal: bool = True,
    frozen_oversight: bool = False,
    us_crisis_options: bool = True,
    relax: frozenset[str] = frozenset(),
) -> CompiledModel:
    return model_of(aims, prc_principal, frozen_oversight, us_crisis_options).compile(relax=relax)


@lru_cache(maxsize=None)
def flat_of(
    aims: str,
    prc_principal: bool = True,
    frozen_oversight: bool = False,
    us_crisis_options: bool = True,
):
    cm = compiled(aims, prc_principal, frozen_oversight, us_crisis_options)
    return v1.flat(cm, prc_principal)


def hindsight(year: int, aims: str, **build):
    """The coarse state of 1 January ``year`` from the v1 hindsight snapshot."""
    return snapshot_state(compiled(aims, **build), year, aims)


def replay_state(year: int, aims: str, **build):
    """The coarse state of 1 January ``year`` from the v1 manual replay snapshot."""
    return snapshot_state(compiled(aims, **build), year, aims, kind="replay")


# -- the realized path ----------------------------------------------------------------------
def _crisis_index(fm, move) -> int | None:
    for k, comp in enumerate(fm._compiled):
        if move[comp.actor] == comp.action:
            return k
    return None


@lru_cache(maxsize=None)
def realized(aims: str):
    """The realized play on the flattened v1 game from the 1947 hindsight snapshot, move by
    move with ``available`` and ``step``: ``(coarse, fine, stop)`` as tests/coldwar/common.py's
    ``realized`` (``stop`` is the first unavailable move, or None)."""
    fm = flat_of(aims)
    cm = fm.coarse
    s = hindsight(1947, aims)
    coarse, fine = [s], {}
    for t, move in enumerate(realized_moves(cm, v1.REALIZED_MOVES)):
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


def graph(cm, start, cut: int | None = None, max_states: int = 3_000_000):
    m = Cut(cm, cut) if cut is not None else cm
    return explore(m, initial=[start], max_states=max_states)


# -- symbolic kernels on the coarse game (sub-games inert) ----------------------------------
@lru_cache(maxsize=None)
def encoding(aims: str, **build):
    from wavefront.symbolic import encode

    return encode(compiled(aims, **build))


@lru_cache(maxsize=None)
def kernel(aims: str, coalition: tuple[str, ...], invariant, **build):
    """The coarse kernel of ``invariant`` for ``coalition`` through the horizon, over the
    whole domain (symbolic; the crisis actions inert)."""
    from wavefront.symbolic import safe as ssafe

    enc = encoding(aims, **build)
    return ssafe(enc, list(coalition), enc.predicate(invariant))


@lru_cache(maxsize=None)
def bounded_kernel(aims: str, coalition: tuple[str, ...], invariant: str, cut: int, **build):
    """The coarse kernel of ``invariant`` kept only to tick ``cut`` (states at or after the
    cut count as kept: decisions D5's cut-off), symbolic, crisis actions inert."""
    from wavefront.model import V
    from wavefront.symbolic import safe as ssafe

    enc = encoding(aims, **build)
    phi = enc.predicate(V.invariant(invariant) | (V.tick >= cut))
    return ssafe(enc, list(coalition), phi)


def boundary_kernel(g, coalition, phi_ids: set[int], boundary) -> set[int]:
    """The kernel, on an explicit graph ``g`` explored with a cut, of the states in
    ``phi_ids`` whose cut states (ending ``CUT``) are kept iff ``boundary(state)``: the
    explicit graph to the last crisis with the symbolic values beyond it (decisions R V2)."""
    from wavefront.engine import safe

    keep = {i for i in phi_ids if g.ending[i] != "CUT" or boundary(g.states[i])}
    return safe(g, list(coalition), keep).kernel


# -- lifted crisis kernels ------------------------------------------------------------------
def crisis_entry(fm, coarse_state, crisis_name: str):
    """The first fine state of ``crisis_name`` entered from ``coarse_state`` and the crisis
    index."""
    k = next(i for i, c in enumerate(fm._compiled) if c.crisis.label == crisis_name)
    comp = fm._compiled[k]
    return fm.step(coarse_state, comp.ret_move), k


def fine_graph(fm, coarse_state, crisis_name: str):
    """``(g, returns, k)``: the sub-game graph from its entry, the coarse return state of
    every terminal fine state, and the crisis index."""
    first, k = crisis_entry(fm, tuple(coarse_state), crisis_name)
    comp = fm._compiled[k]
    g = explore(comp.crisis.sub, initial=[fm.split(first)[2]], max_states=1_000_000)
    returns = {
        i: fm.step(tuple(coarse_state) + (k,) + g.states[i], comp.ret_move)
        for i in range(g.size())
        if g.terminal[i]
    }
    return g, returns, k


# -- the engines of decisions D7 ------------------------------------------------------------
# No crisis action is available from 1 January 1984 (tick 37): the composite engine's cut.
COMPOSITE_CUT = 37
EVERYONE = ("USA", "USSR", "PRC", "Nature")


def engine_for(year: int) -> str:
    """The engine decisions R assigns to a year's unbounded kernels and distances:
    ``"symbolic"`` from 1984, ``"composite"`` for 1972 to 1983, ``"layered"`` before 1972."""
    return "symbolic" if year >= 1984 else "composite" if year >= 1972 else "layered"


@lru_cache(maxsize=None)
def lift_of(aims: str, forbid: frozenset = frozenset(), **build) -> Lift:
    """The layered lifting (D7) of the flattened game of ``aims`` and ``build``, with the
    ``(actor, action)`` pairs of ``forbid`` never available."""
    return Lift(flat_of(aims, **build), encoding(aims, **build), forbid=forbid)


def prc_idle(aims: str, **build) -> frozenset:
    """The pairs that leave the PRC idle (R V2's breaking moves)."""
    return idle_pairs(compiled(aims, **build), "PRC")


@lru_cache(maxsize=None)
def layered_kernel(aims: str, coalition: tuple[str, ...], invariant, **build):
    """The kernel of ``invariant`` for ``coalition`` through the horizon on the flattened
    game, over the whole coarse domain, by the layered lifting (exact)."""
    lift = lift_of(aims, **build)
    return lift.kernel(coalition, lift.enc.predicate(invariant))


def phi_ids(g, fm, pred) -> set[int]:
    """Ids of ``g`` satisfying the coarse predicate ``pred`` (every fine state does)."""
    return {i for i, s in enumerate(g.states) if fm.is_fine(s) or fm.coarse.evaluate(pred, s)}


def composite_graph(aims: str, starts, max_states: int = 6_000_000, forbid=(), **build):
    """The flattened game explored from ``starts`` to 1 January 1984 (the composite engine's
    explicit part); raises ``BudgetExceeded`` beyond ``max_states``."""
    fm = flat_of(aims, **build)
    m = Forbid(fm, sorted(forbid)) if forbid else fm
    return explore(Cut(m, COMPOSITE_CUT), initial=list(starts), max_states=max_states)


def composite_kernel(g, aims: str, coalition: tuple[str, ...], pred, **build) -> set[int]:
    """The composite kernel (D7) on the explicit part ``g``: its cut states valued by the
    symbolic coarse kernel of ``pred`` through the horizon (exact from 1984)."""
    fm = flat_of(aims, **build)
    sym = kernel(aims, coalition, pred, **build)
    return boundary_kernel(g, coalition, phi_ids(g, fm, pred), sym.contains)


@lru_cache(maxsize=None)
def everyone_attractor(aims: str, key: str, **build):
    """The symbolic attractor of every actor (Nature included) on the coarse game, over the
    whole domain, so that a state's rank is its fewest transitions (exact from 1984):
    ``key`` is ``"adverse"`` (GENERAL_WAR or ACCIDENTAL_WAR) or ``"out:<coalition>:<inv>"``
    (outside that coalition's symbolic kernel of the invariant, members joined by '+')."""
    from wavefront.model import V
    from wavefront.symbolic import attractor

    enc = encoding(aims, **build)
    if key == "adverse":
        target = enc.predicate(~V.invariant("no_general_war"))
    else:
        _, coalition, inv = key.split(":")
        res = kernel(aims, tuple(coalition.split("+")), inv, **build)
        target = enc.mgr.DIFF(enc.dom, res.kernel)
    return attractor(enc, list(EVERYONE), target)


@lru_cache(maxsize=None)
def layered_distance(aims: str, key: str, **build):
    """Fewest transitions on the flattened game from every coarse state, by the layered
    lifting (exact): ``key`` as in :func:`everyone_attractor`, the kernel being the layered
    one (fine states outside the lifted kernel count as outside)."""
    from wavefront.model import V

    lift = lift_of(aims, **build)
    if key == "adverse":
        return lift.distance(lift.enc.predicate(~V.invariant("no_general_war")))
    _, coalition, inv = key.split(":")
    return lift.distance(
        None, kernel=layered_kernel(aims, tuple(coalition.split("+")), inv, **build)
    )


def composite_distances(aims: str, g, keys, **build) -> dict[str, list]:
    """Per key (as :func:`everyone_attractor`), the fewest transitions from every state of
    the composite graph ``g``: explicit to the cut, the symbolic rank beyond it."""
    from tests.coldwar_v1.layered import dag_distance

    fm = flat_of(aims, **build)
    out = {}
    for key in keys:
        beyond = everyone_attractor(aims, key, **build)
        if key == "adverse":
            targets = ending_ids(g, *ADVERSE)
        else:
            _, coalition, inv = key.split(":")
            k = composite_kernel(g, aims, tuple(coalition.split("+")), inv, **build)
            targets = set(range(g.size())) - k
        out[key] = dag_distance(g, fm, targets, beyond.rank)
    return out
