"""Shared machinery for the Cold War v1 tests: per-hypothesis builds, hindsight and replay
states from ``snapshots/cw_v1``, the realized play on the flattened game, and the analysis
devices of docs/cw_v1_decisions.md (the cut-off, restricted games, symbolic boundary values
for explicit graphs, lifted crisis kernels). Analysis devices only; the model is
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


def kernel(aims: str, coalition: tuple[str, ...], invariant: str, **build):
    """The coarse kernel of ``invariant`` for ``coalition`` through the horizon, over the
    whole domain (symbolic; the crisis actions inert)."""
    from wavefront.symbolic import safe as ssafe

    enc = encoding(aims, **build)
    return ssafe(enc, list(coalition), enc.predicate(invariant))


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
