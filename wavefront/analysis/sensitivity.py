"""Sensitivity of kernel membership and distance to the initial values (spec section 7)."""

from __future__ import annotations

import math
from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass

from ..engine import Graph, explore, safe
from ..model.compile import CompiledModel
from ..model.compile import compile as compile_model
from ..model.model import Model, ModelError
from ._common import check_invariant
from .relax import DEFAULT_MAX_STATES
from .viability import distance_table

__all__ = ["SensitivityRow", "sensitivity", "sensitivity_table"]

State = tuple[int, ...]


@dataclass(frozen=True)
class SensitivityRow:
    """The effect of moving one variable's initial value one level up or down.

    The row compares the ``states`` initial states whose ``variable`` is ``from_level``
    with the same states with ``variable`` set to ``to_level``. ``*_in_kernel`` count the
    states inside the coalition's kernel; ``flips`` counts the states whose membership
    changed. ``*_shortest`` and ``*_forced`` are the smallest :class:`Distance` entries
    over the states (``None``: no state has a finite one; ``forced`` is ``None`` when no
    adversary was given). ``error`` holds the :class:`ModelError` message when the
    perturbed states could not be explored (the numbers are then ``None``)."""

    variable: str
    from_level: str
    to_level: str
    states: int
    base_in_kernel: int
    new_in_kernel: int | None
    flips: int | None
    base_shortest: int | None
    new_shortest: int | None
    base_forced: int | None = None
    new_forced: int | None = None
    error: str | None = None

    @property
    def effect(self) -> tuple[float, float, float]:
        """The sort key: membership flips, then the change of the shortest distance, then
        the change of the forced distance (a change between finite and ``None`` counts
        as infinite)."""
        if self.error is not None:
            return (-1.0, 0.0, 0.0)
        return (
            float(self.flips or 0),
            _change(self.base_shortest, self.new_shortest),
            _change(self.base_forced, self.new_forced),
        )


def _change(a: int | None, b: int | None) -> float:
    if a is None and b is None:
        return 0.0
    if a is None or b is None:
        return math.inf
    return float(abs(a - b))


def _smallest(values: Iterable[int | None]) -> int | None:
    finite = [v for v in values if v is not None]
    return min(finite) if finite else None


def _perturbations(
    cm: CompiledModel, base: list[State], recompute_latches: bool
) -> list[tuple[int, int, int, list[tuple[State, State]]]]:
    """``(variable index, from value, to value, [(base state, perturbed state)])`` for
    every declared variable and every value it takes in ``base``."""
    latches = []
    if recompute_latches:
        for decl in cm.model.latches:
            when = cm.compile_expr(decl.when)
            latches.append((cm.index[decl.name], cm.index[decl.of], when))
    assumes = list(cm.assume_fns.values()) if recompute_latches else []
    out = []
    for i, var in enumerate(cm.variables):
        if var.origin != "var":
            continue
        values = sorted({s[i] for s in base})
        for x in values:
            for y in (x - 1, x + 1):
                if not 0 <= y < var.size:
                    continue
                pairs = []
                for s in base:
                    if s[i] != x:
                        continue
                    new = list(s)
                    new[i] = y
                    for idx, src, when in latches:
                        new[idx] = new[src] + 1 if when(new) else 0
                    if all(fn(new) for fn in assumes):
                        pairs.append((s, tuple(new)))
                if pairs:
                    out.append((i, x, y, pairs))
    return out


Query = tuple[str, Collection[str], Collection[str] | None]


def sensitivity_table(
    cm: CompiledModel,
    queries: Sequence[Query],
    initial: Sequence[Sequence[int]] | None = None,
    max_states: int = DEFAULT_MAX_STATES,
) -> list[list[SensitivityRow]]:
    """Sensitivity rows for several ``(invariant, coalition, adversary)`` queries on one
    exploration of the base and perturbed initial states. With ``initial=None`` the base is
    ``cm.initial_states()``, perturbed states have their latches recomputed and must
    satisfy the model's ``assume`` restrictions; explicit ``initial`` states are perturbed
    as given."""
    base = [tuple(s) for s in (cm.initial_states() if initial is None else initial)]
    perts = _perturbations(cm, base, recompute_latches=initial is None)
    everything = list(dict.fromkeys([*base, *(t for *_, ps in perts for _, t in ps)]))
    graphs: list[Graph | str]
    try:
        g = explore(cm, initial=everything, max_states=max_states)
        graphs = [g] * len(perts)
        base_graph: Graph = g
    except ModelError:
        base_graph = explore(cm, initial=base, max_states=max_states)
        graphs = []
        for *_, pairs in perts:
            try:
                states = list(dict.fromkeys([*base, *(t for _, t in pairs)]))
                graphs.append(explore(cm, initial=states, max_states=max_states))
            except ModelError as exc:
                graphs.append(str(exc))
    tables: list[list[SensitivityRow]] = []
    for invariant, coalition, adversary in queries:
        check_invariant(base_graph, invariant)
        cache: dict[int, tuple[set[int], dict]] = {}

        def analyse(gr: Graph) -> tuple[set[int], dict]:
            if id(gr) not in cache:
                kernel = safe(gr, coalition, gr.states_where(invariant)).kernel
                table = distance_table(gr, range(gr.size()), kernel, coalition, adversary)
                cache[id(gr)] = (kernel, table)
            return cache[id(gr)]

        rows = []
        for (i, x, y, pairs), gr in zip(perts, graphs, strict=True):
            var = cm.variables[i]
            name, frm, to = var.name, var.levels[x], var.levels[y]
            bk, bd = analyse(base_graph)
            b_ids = [base_graph.index[s] for s, _ in pairs]
            base_in = sum(s in bk for s in b_ids)
            base_short = _smallest(bd[s].shortest for s in b_ids)
            base_forced = _smallest(bd[s].forced for s in b_ids)
            if isinstance(gr, str):
                rows.append(
                    SensitivityRow(
                        name,
                        frm,
                        to,
                        len(pairs),
                        base_in,
                        None,
                        None,
                        base_short,
                        None,
                        base_forced,
                        None,
                        error=gr,
                    )
                )
                continue
            nk, nd = analyse(gr)
            n_ids = [gr.index[t] for _, t in pairs]
            flips = sum((b in bk) != (n in nk) for b, n in zip(b_ids, n_ids, strict=True))
            rows.append(
                SensitivityRow(
                    name,
                    frm,
                    to,
                    len(pairs),
                    base_in,
                    sum(n in nk for n in n_ids),
                    flips,
                    base_short,
                    _smallest(nd[n].shortest for n in n_ids),
                    base_forced,
                    _smallest(nd[n].forced for n in n_ids),
                )
            )
        rows.sort(key=lambda r: r.effect, reverse=True)
        tables.append(rows)
    return tables


def sensitivity(
    model: Model,
    invariant_name: str,
    coalition: Collection[str],
    adversary: Collection[str] | None = None,
    profile: str | Iterable[str] | None = None,
    initial: Sequence[Sequence[int]] | None = None,
    max_states: int = DEFAULT_MAX_STATES,
) -> list[SensitivityRow]:
    """For each declared variable and each value it takes in the initial states, move the
    value one level down and one level up (where legal) and recompute the kernel
    membership of those initial states for ``coalition`` and ``invariant_name``, their
    ``shortest`` distance and, if ``adversary`` is given, their ``forced`` distance.
    Rows are sorted by :attr:`SensitivityRow.effect`, largest first (stable in variable
    order). Perturbed states that violate an ``assume`` restriction are dropped; latches
    are recomputed for the perturbed state."""
    cm = compile_model(model, profile=profile)
    return sensitivity_table(cm, [(invariant_name, coalition, adversary)], initial, max_states)[0]
