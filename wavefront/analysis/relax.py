"""Brute-force assumption mining and informativeness (spec section 7; theory.md
section 5)."""

from __future__ import annotations

import itertools
from collections.abc import Collection, Iterable, Sequence

from ..engine import BudgetExceeded, attractor, explore
from ..model.compile import compile as compile_model
from ..model.model import Model, ModelError
from ._common import check_ending

__all__ = [
    "RelaxSets",
    "relax_explicit",
    "minimal_relaxation_size",
    "informativeness",
    "OPS",
]

DEFAULT_MAX_STATES = 1_000_000


class RelaxSets(list):
    """The minimal relaxation sets found by :func:`relax_explicit` (a ``list[list[str]]``,
    smallest first, in assumption order within a size), with what the search covered:

    - ``assumptions``: the named assumptions searched over;
    - ``max_size``: the largest set size tried (so an empty list means "none up to that
      size", not "none at all");
    - ``ill_formed``: ``(set, message)`` for relaxations whose model raised
      :class:`~wavefront.model.ModelError` when compiled or explored; these are reported,
      not treated as results;
    - ``undecided``: ``(set, message)`` for relaxations whose exploration passed
      ``max_states``.
    """

    def __init__(
        self,
        sets: Iterable[list[str]] = (),
        *,
        assumptions: Sequence[str] = (),
        max_size: int = 0,
        ill_formed: Iterable[tuple[list[str], str]] = (),
        undecided: Iterable[tuple[list[str], str]] = (),
    ) -> None:
        super().__init__(sets)
        self.assumptions = list(assumptions)
        self.max_size = max_size
        self.ill_formed = list(ill_formed)
        self.undecided = list(undecided)

    @property
    def minimum_size(self) -> int | None:
        """The size of the smallest set found, or ``None`` if none was found."""
        return len(self[0]) if self else None


def _check_ending_name(model: Model, name: str) -> None:
    if name not in model.endings and not (name == "HORIZON" and model.timed):
        known = ", ".join([*model.endings, *(["HORIZON"] if model.timed else [])]) or "none"
        raise ModelError(f"no ending named {name!r} (endings: {known})")


def _holds(
    model: Model,
    ending_name: str,
    relax: frozenset[str],
    coalition: Collection[str] | None,
    profile: str | Iterable[str] | None,
    initial: Sequence[Sequence[int]] | None,
    max_states: int,
) -> bool:
    cm = compile_model(model, profile=profile, relax=relax)
    g = explore(cm, initial=initial, max_states=max_states)
    target = check_ending(g, ending_name)
    if not target:
        return False
    if coalition is None:
        return True  # every explored state is reachable from an initial state
    win = attractor(g, coalition, target).win
    return bool(g.initial) and all(s in win for s in g.initial)


def relax_explicit(
    model: Model,
    ending_name: str,
    max_size: int = 2,
    coalition: Collection[str] | None = None,
    profile: str | Iterable[str] | None = None,
    initial: Sequence[Sequence[int]] | None = None,
    max_states: int = DEFAULT_MAX_STATES,
) -> RelaxSets:
    """All minimal relaxation sets of size at most ``max_size`` for ``ending_name``.

    Subsets of ``compile(model, profile=profile).assumptions()`` are tried by increasing
    size (supersets of sets that worked are skipped); each is compiled with
    ``relax=subset``, explored and tested. With ``coalition=None`` the test is plain
    reachability: the ending is reached from some initial state. With a coalition it is
    forceability: the coalition can force the ending from every initial state. Forcing is
    not monotone in relaxations (loosening can help either side), which is why only this
    brute-force search answers it. ``initial``, if given, replaces the model's initial
    states for every relaxation (``assume`` relaxations then change nothing). Relaxations
    that raise :class:`ModelError` are listed in ``ill_formed`` and those that exceed
    ``max_states`` in ``undecided``; neither counts as a result. The horizon is the full
    model horizon (no bound ``k``)."""
    _check_ending_name(model, ending_name)
    names = compile_model(model, profile=profile).assumptions()
    if coalition is not None:
        coalition = list(coalition)
    found: list[frozenset[str]] = []
    out: list[list[str]] = []
    ill: list[tuple[list[str], str]] = []
    undecided: list[tuple[list[str], str]] = []
    for size in range(max(max_size, 0) + 1):
        for combo in itertools.combinations(names, size):
            subset = frozenset(combo)
            if any(f <= subset for f in found):
                continue
            try:
                ok = _holds(model, ending_name, subset, coalition, profile, initial, max_states)
            except BudgetExceeded as exc:
                undecided.append((list(combo), str(exc)))
                continue
            except ModelError as exc:
                ill.append((list(combo), str(exc)))
                continue
            if ok:
                found.append(subset)
                out.append(list(combo))
    return RelaxSets(
        out, assumptions=names, max_size=max(max_size, 0), ill_formed=ill, undecided=undecided
    )


def minimal_relaxation_size(
    model: Model,
    ending_name: str,
    max_size: int,
    profile: str | Iterable[str] | None = None,
    max_states: int = DEFAULT_MAX_STATES,
) -> int | None:
    """``rho(E)``: the size of a minimum relaxation set for reaching ``ending_name``, or
    ``None`` if there is none of size at most ``max_size``."""
    return relax_explicit(
        model, ending_name, max_size=max_size, profile=profile, max_states=max_states
    ).minimum_size


OPS = (">=", "==", "<=")


def informativeness(
    model: Model,
    negative_controls: Sequence[tuple[str, str, int]],
    profile: str | Iterable[str] | None = None,
    max_states: int = DEFAULT_MAX_STATES,
) -> float:
    """``Inf(G, N)`` of theory.md section 5.4: the fraction of negative controls
    ``(ending, op, n)`` satisfied, where ``op`` in ``>=``, ``==``, ``<=`` compares the
    minimum relaxation size ``rho(ending)`` with ``n``. ``>=`` searches up to size
    ``n - 1`` (none found means at least ``n``); ``==`` and ``<=`` search up to ``n``."""
    if not negative_controls:
        raise ValueError("informativeness needs at least one negative control")
    bound: dict[str, int] = {}
    for ending, op, n in negative_controls:
        if op not in OPS:
            raise ValueError(f"control op must be one of {', '.join(OPS)}, not {op!r}")
        if isinstance(n, bool) or not isinstance(n, int) or n < 0:
            raise ValueError(f"control bound must be an int >= 0, not {n!r}")
        _check_ending_name(model, ending)
        need = n - 1 if op == ">=" else n
        bound[ending] = max(bound.get(ending, -1), need)
    rho = {
        e: (
            minimal_relaxation_size(model, e, b, profile=profile, max_states=max_states)
            if b >= 0
            else None
        )
        for e, b in bound.items()
    }
    satisfied = 0
    for ending, op, n in negative_controls:
        r = rho[ending]
        if op == ">=":
            ok = r is None or r >= n
        elif op == "==":
            ok = r == n
        else:
            ok = r is not None and r <= n
        satisfied += ok
    return satisfied / len(negative_controls)
