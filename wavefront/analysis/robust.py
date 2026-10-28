"""Robust and fragile findings over a set of start states (docs/ambiguous_levels.md; spec
section 7).

A snapshot that gives a set of levels for a variable over a contested window denotes the
product set of concrete states (:class:`~wavefront.evidence.SnapshotStates`). Every question
of the analysis layer is asked of each member state on its own, and a finding is **robust**
when every member gives the same answer, **fragile** otherwise; a fragile finding names the
members on which the answer differs. No member is weighted: there are no probabilities.

:func:`robust` is the general wrapper: it takes the members and a function answering the
question for one state. The others are the existing entry points asked per member on one
graph explored from every member state (:func:`robust_kernel`, :func:`robust_status`,
:func:`robust_attractor`, :func:`robust_pivotal`) or per member exploration
(:func:`robust_sensitivity`). Note that a question asked of the whole set at once, as
:func:`~wavefront.analysis.pivotal` does with ``initial=`` several states (coalitions that
force the ending from *every* state), is a different and weaker deliverable: the robust
answer says that the coalitions are the same from each member.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable, Sequence
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from ..engine import Graph, attractor, contested
from ..model.model import Model, ModelError
from ._common import check_ending
from .pivotal import PivotalResult, pivotal
from .relax import DEFAULT_MAX_STATES
from .sensitivity import SensitivityRow, sensitivity
from .viability import Distance, distance_table, viability

__all__ = [
    "Robustness",
    "RobustKernel",
    "members_of",
    "robust",
    "robust_kernel",
    "robust_status",
    "robust_attractor",
    "robust_pivotal",
    "robust_sensitivity",
]

T = TypeVar("T")
State = tuple[int, ...]

ROBUST = "robust"
FRAGILE = "fragile"


@dataclass(frozen=True)
class Robustness(Generic[T]):
    """The answers to one question from each member state.

    ``labels[i]`` names member ``i`` (for a snapshot, its set-valued variables' levels) and
    ``answers[i]`` is the answer from it. ``robust`` holds when every answer is equal;
    ``classes`` groups the members by answer, in order of first appearance."""

    question: str
    labels: tuple[str, ...]
    answers: tuple[T, ...]

    @property
    def robust(self) -> bool:
        return all(a == self.answers[0] for a in self.answers[1:])

    @property
    def verdict(self) -> str:
        return ROBUST if self.robust else FRAGILE

    @property
    def value(self) -> T | None:
        """The common answer of a robust finding, else ``None``."""
        return self.answers[0] if self.answers and self.robust else None

    @property
    def classes(self) -> list[tuple[T, list[str]]]:
        out: list[tuple[T, list[str]]] = []
        for label, answer in zip(self.labels, self.answers, strict=True):
            for known, names in out:
                if known == answer:
                    names.append(label)
                    break
            else:
                out.append((answer, [label]))
        return out

    def summary(self, show: Callable[[T], str] = str) -> str:
        """``robust: <answer>``, or ``fragile: <answer> from <members>; <answer> from ...``."""
        if self.robust:
            return f"{ROBUST}: {show(self.answers[0])}" if self.answers else ROBUST
        parts = [f"{show(a)} from [{'; '.join(names)}]" for a, names in self.classes]
        return f"{FRAGILE}: " + "; ".join(parts)


def members_of(members: Any) -> tuple[tuple[State, ...], tuple[str, ...]]:
    """The states and labels of ``members``: a :class:`~wavefront.evidence.SnapshotStates`
    (labelled by their set-valued levels) or a sequence of states (labelled ``#0``, ...)."""
    if hasattr(members, "states") and hasattr(members, "label"):
        states = tuple(tuple(s) for s in members.states)
        return states, tuple(members.label(i) for i in range(len(states)))
    states = tuple(tuple(int(x) for x in s) for s in members)
    return states, tuple(f"#{i}" for i in range(len(states)))


def robust(question: str, members: Any, ask: Callable[[State], T]) -> Robustness[T]:
    """Ask ``ask(state)`` of every member state and say whether the answer is robust."""
    states, labels = members_of(members)
    if not states:
        raise ModelError("robust: no member state to ask")
    return Robustness(question, labels, tuple(ask(s) for s in states))


def _ids(g: Graph, states: Sequence[State]) -> list[int]:
    out = []
    for s in states:
        if s not in g.index:
            raise ModelError(
                f"member state {s} is not in the graph; explore with initial= the member states"
            )
        out.append(g.index[s])
    return out


@dataclass(frozen=True)
class RobustKernel:
    """Kernel membership and the distances out of the kernel, per member."""

    in_kernel: Robustness[bool]
    distance: Robustness[Distance]


def robust_kernel(
    g: Graph,
    members: Any,
    coalition: Collection[str],
    invariant_name: str,
    adversary: Collection[str] | None = None,
) -> RobustKernel:
    """Kernel membership of each member state for ``coalition`` and ``invariant_name``, and
    its :class:`~wavefront.analysis.Distance` (``forced`` against ``adversary`` if given).
    ``g`` must contain every member state (explore with ``initial=`` the members)."""
    states, labels = members_of(members)
    ids = _ids(g, states)
    k = viability(g, coalition, invariant_name)
    dist = distance_table(g, ids, k.kernel, coalition, adversary)
    who = "{" + ", ".join(coalition) + "}"
    return RobustKernel(
        Robustness(
            f"{invariant_name}: in the kernel of {who}",
            labels,
            tuple(s in k.kernel for s in ids),
        ),
        Robustness(
            f"{invariant_name}: distance out of the kernel of {who}",
            labels,
            tuple(dist[s] for s in ids),
        ),
    )


def robust_status(
    g: Graph, members: Any, coalition: Collection[str], ending_name: str
) -> Robustness[str]:
    """Whether ``coalition`` forces, blocks or contests ``ending_name`` from each member."""
    states, labels = members_of(members)
    ids = _ids(g, states)
    res = contested(g, coalition, check_ending(g, ending_name), "reach")
    status = tuple(
        "forced" if s in res.forced else "blocked" if s in res.blocked else "contested" for s in ids
    )
    return Robustness(f"{ending_name}: status for {{{', '.join(coalition)}}}", labels, status)


def robust_attractor(
    g: Graph, members: Any, coalition: Collection[str], target: Collection[int], name: str = ""
) -> Robustness[int | None]:
    """The rank of each member state in ``attractor(coalition, target)`` (``None``: the
    coalition cannot force the target from it)."""
    states, labels = members_of(members)
    rank = attractor(g, coalition, target).rank
    question = f"{name or 'target'}: forced within, by {{{', '.join(coalition)}}}"
    return Robustness(question, labels, tuple(rank.get(s) for s in _ids(g, states)))


def robust_pivotal(
    g: Graph,
    members: Any,
    ending_name: str,
    actors: Iterable[str] | None = None,
    include_nature: bool = False,
) -> Robustness[PivotalResult]:
    """The minimal forcing and blocking coalitions for ``ending_name`` from each member state
    on its own (``pivotal(..., initial=[member])``)."""
    states, labels = members_of(members)
    actor_list = None if actors is None else list(actors)
    answers = tuple(
        pivotal(g, ending_name, actor_list, include_nature, initial=[s]) for s in _ids(g, states)
    )
    return Robustness(f"{ending_name}: pivotal coalitions", labels, answers)


def robust_sensitivity(
    model: Model,
    members: Any,
    invariant_name: str,
    coalition: Collection[str],
    adversary: Collection[str] | None = None,
    profile: str | Iterable[str] | None = None,
    max_states: int = DEFAULT_MAX_STATES,
) -> Robustness[list[SensitivityRow]]:
    """The sensitivity rows of each member state on its own (one exploration per member)."""
    return robust(
        f"{invariant_name}: sensitivity for {{{', '.join(coalition)}}}",
        members,
        lambda s: sensitivity(
            model,
            invariant_name,
            coalition,
            adversary,
            profile=profile,
            initial=[s],
            max_states=max_states,
        ),
    )
