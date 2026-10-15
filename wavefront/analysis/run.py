"""The analysis orchestrator: every derived object of one model in one pass."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

from ..engine import ContestedResult, Graph, SafeResult, Trace, attractor, contested, explore
from ..engine import witness as find_witness
from ..model.compile import CompiledModel
from ..model.compile import compile as compile_model
from ..model.model import Model
from ._common import complement, nearest_source, rest_of
from .pivotal import PivotalResult, pivotal
from .relax import DEFAULT_MAX_STATES, RelaxSets, relax_explicit
from .sensitivity import SensitivityRow, sensitivity_table
from .uniform import UniformityResult, is_uniform, strategy_closure
from .viability import Distance, distance_table, viability

__all__ = [
    "Analysis",
    "KernelEntry",
    "EndingEntry",
    "UniformityNote",
    "budget",
    "fingerprint",
    "run_all",
]

Coalition = tuple[str, ...]


def budget(cm: CompiledModel) -> dict:
    """The parameter budget of a compiled model (delegates to ``cm.budget()``)."""
    return cm.budget()


def fingerprint(model: Model) -> str:
    """A short hash of the model's declarations (variables, actions with guards and guard
    parts, effects, delays and sources, actor cadences, latches, fairness, profiles,
    invariants, endings, assumptions and horizon), so a report names the model version it
    is conditional on."""
    parts = [
        model.name,
        repr(model.horizon),
        repr(model.variables),
        repr([(a.name, a.observes, a.remember_last, a.idle, a.actions) for a in model.actors]),
        repr(model.nature().actions),
        repr(model.fairness_constraints),
        repr(model.profiles),
        repr(sorted(model.invariants.items())),
        repr(sorted(model.endings.items())),
        repr(sorted(model.assumes.items())),
    ]
    parted = [
        (a.actor, a.name, a.guard_parts)
        for actor in [*model.actors, model.nature()]
        for a in actor.actions
        if a.guard_parts
    ]
    if parted:  # only when used, so fingerprints of models without parts are unchanged
        parts.append(repr(parted))
    cadenced = [(a.name, a.cadence) for a in model.actors if getattr(a, "cadence", 1) != 1]
    if cadenced:  # likewise: models without a cadence keep their fingerprints
        parts.append("cadence " + repr(cadenced))
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[:12]


@dataclass
class UniformityNote:
    """Whether the strategy behind a keeping (``kind="keep"``) or forcing
    (``kind="force"``) result is uniform, checked on the part of the strategy used from
    the initial states where the result holds."""

    kind: str
    subject: str
    coalition: Coalition
    result: UniformityResult


@dataclass
class KernelEntry:
    """Kernel of ``coalition`` for ``invariant``. ``in_kernel`` and ``distances`` are per
    initial state id (``forced`` is ``None`` there: see ``defection``). ``defection[m]``
    maps each initial state to the forced distance out of the kernel when member ``m``
    plays with the non-members and Nature against the rest of the coalition (joint
    coalitions only)."""

    invariant: str
    coalition: Coalition
    kernel: SafeResult
    in_kernel: dict[int, bool]
    distances: dict[int, Distance]
    defection: dict[str, dict[int, int | None]] = field(default_factory=dict)
    uniformity: UniformityResult | None = None


@dataclass
class EndingEntry:
    """Forced/blocked/contested status of every initial state for ``coalition`` and the
    reach objective ``ending``; ``rank`` holds the forced distance of forced initial
    states."""

    ending: str
    coalition: Coalition
    result: ContestedResult
    status: dict[int, str]
    rank: dict[int, int]
    uniformity: UniformityResult | None = None


@dataclass
class Analysis:
    """Everything :func:`run_all` computed for one model, profile and initial state set.
    Every entry is conditional on the model version (``fingerprint``) and on the initial
    states (``graph.initial``)."""

    model: Model
    cm: CompiledModel
    graph: Graph
    profile: str | tuple[str, ...] | None
    coalitions: list[Coalition]
    endings: list[str]
    kernels: list[KernelEntry]
    contested: list[EndingEntry]
    witnesses: dict[str, Trace | None]
    relaxations: dict[str, RelaxSets]
    pivotal: dict[str, PivotalResult]
    sensitivity: dict[tuple[str, Coalition], list[SensitivityRow]]
    uniformity: list[UniformityNote]
    budget: dict
    speculative: list[str]
    max_relax: int
    fingerprint: str
    explicit_initial: bool = False


def _normalize(g: Graph, coalitions: Iterable[Iterable[str]] | None) -> list[Coalition]:
    cm = g.model
    if coalitions is None:
        players = [a.name for a in cm.actors if not a.is_nature]
        out = [(p,) for p in players]
        if len(players) > 1:
            out.append(tuple(players))
        return out
    result: list[Coalition] = []
    for c in coalitions:
        names = [c] if isinstance(c, str) else list(c)
        t = tuple(cm.actors[i].name for i in g.actor_indices(names))
        if t not in result:
            result.append(t)
    return result


def _speculative(g: Graph, traces: Iterable[Trace | None]) -> list[str]:
    out: dict[str, None] = {}
    for trace in traces:
        if trace is None:
            continue
        for move in trace.joint_moves:
            for actor, j in zip(g.model.actors, move, strict=True):
                action = actor.actions[j]
                if action.speculative:
                    out[f"{actor.name}.{action.name}"] = None
    return list(out)


def run_all(
    model: Model,
    coalitions: Iterable[Iterable[str]] | None = None,
    profile: str | Iterable[str] | None = None,
    initial: Sequence[Sequence[int]] | None = None,
    max_relax: int = 2,
    max_states: int = DEFAULT_MAX_STATES,
) -> Analysis:
    """Explore ``model`` once and compute, for each coalition (default: each declared
    actor alone and all declared actors together, Nature excluded), kernel membership and
    distances of the initial states for every invariant, the forced/blocked/contested
    status of every ending (``HORIZON`` included in timed models) with the shortest
    witness, the minimal relaxation sets up to ``max_relax`` per ending, the pivotal
    coalitions per ending, sensitivity rows per invariant and coalition, uniformity of
    every strategy a reported result rests on, the parameter budget and the speculative
    actions used by the reported witnesses. ``initial`` replaces the model's initial
    states (for example a snapshot state)."""
    if profile is not None and not isinstance(profile, str):
        profile = tuple(profile)
    cm = compile_model(model, profile=profile)
    g = explore(cm, initial=initial, max_states=max_states)
    groups = _normalize(g, coalitions)
    endings = [*model.endings, *(["HORIZON"] if model.timed else [])]
    init = list(g.initial)
    notes: list[UniformityNote] = []

    kernels: list[KernelEntry] = []
    for inv in model.invariants:
        for c in groups:
            res = viability(g, c, inv)
            dist = distance_table(g, init, res.kernel, c, None)
            entry = KernelEntry(inv, c, res, {s: s in res.kernel for s in init}, dist)
            if len(c) > 1:
                outside = complement(g, res.kernel)
                for m in c:
                    adversary = [*rest_of(g, c), m]
                    rank = attractor(g, adversary, outside).rank
                    entry.defection[m] = {s: rank.get(s) for s in init}
            kept = [s for s in init if s in res.kernel]
            if kept:
                used = strategy_closure(g, c, res.strategy, kept)
                entry.uniformity = is_uniform(g, c, used)
                notes.append(UniformityNote("keep", inv, c, entry.uniformity))
            kernels.append(entry)

    ends: list[EndingEntry] = []
    witnesses: dict[str, Trace | None] = {}
    piv: dict[str, PivotalResult] = {}
    relaxations: dict[str, RelaxSets] = {}
    for e in endings:
        target = g.ending_states(e)
        for c in groups:
            res = contested(g, c, target, "reach")
            status = {
                s: "forced" if s in res.forced else "blocked" if s in res.blocked else "contested"
                for s in init
            }
            entry = EndingEntry(e, c, res, status, {})
            forced = [s for s in init if s in res.forced]
            if forced:
                att = attractor(g, c, target)
                entry.rank = {s: att.rank[s] for s in forced}
                used = strategy_closure(g, c, att.strategy, forced)
                entry.uniformity = is_uniform(g, c, used)
                notes.append(UniformityNote("force", e, c, entry.uniformity))
            ends.append(entry)
        source = nearest_source(g, init, target)
        witnesses[e] = None if source is None else find_witness(g, source, target)
        piv[e] = pivotal(g, e)
        relaxations[e] = relax_explicit(
            model, e, max_size=max_relax, profile=profile, initial=initial, max_states=max_states
        )

    queries = [(inv, c, None) for inv in model.invariants for c in groups]
    tables = sensitivity_table(cm, queries, initial=initial, max_states=max_states)
    sens = {(inv, c): rows for (inv, c, _), rows in zip(queries, tables, strict=True)}

    return Analysis(
        model=model,
        cm=cm,
        graph=g,
        profile=profile,
        coalitions=groups,
        endings=endings,
        kernels=kernels,
        contested=ends,
        witnesses=witnesses,
        relaxations=relaxations,
        pivotal=piv,
        sensitivity=sens,
        uniformity=notes,
        budget=budget(cm),
        speculative=_speculative(g, witnesses.values()),
        max_relax=max_relax,
        fingerprint=fingerprint(model),
        explicit_initial=initial is not None,
    )
