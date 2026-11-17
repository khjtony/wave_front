"""Shared machinery for the AGI claim tests (docs/agi_v0_decisions.md section 2).

Analysis devices only; the model is ``models/agi/v0.py``. Three things live here:

- **Jobs.** A kernel ``⟨⟨C⟩⟩□φ`` or an attractor ``⟨⟨C⟩⟩◇E`` of AGI v0 costs minutes and
  gigabytes on the symbolic engine, so each one is a :class:`Job` computed once in its own
  process (``python -m tests.agi.jobs``) with a static variable order and deferred garbage
  collection, and stored under ``.cache/agi`` as a node table that the tests evaluate without
  a BDD manager. A job that was not computed, or ran over its budget, raises
  :class:`NotComputed`; a claim part that needs it reads "not computed", never "met".
- **Bounded queries.** Scenario tests, shortest witnesses and minimum relaxation sets use
  ``wavefront.bmc`` on a build with the objective fixed by its initial level.
- **Parts.** A claim is checked part by part (:class:`Parts`): every part is recorded as met,
  not met or not computed in ``reports/agi_v0_first_sight_parts.jsonl``, so a failing first
  part does not hide the rest.
"""

from __future__ import annotations

import array
import gzip
import hashlib
import json
import multiprocessing
import os
import pickle
import resource
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

import pytest

from models.agi import v0
from wavefront.bmc import queries as bmc
from wavefront.model import V
from wavefront.model.compile import CompiledModel
from wavefront.symbolic import FALSE, TRUE, Encoding, cpre, encode, safe
from wavefront.symbolic.solve import _winning_moves

ROOT = Path(__file__).resolve().parents[2]


def _stamp() -> str:
    """What a stored result depends on besides its job: the model and its snapshot, this
    module and the framework. A change to any of them starts an empty cache."""
    files = [Path(__file__)]
    for folder, patterns in (
        ("models/agi", ("*.py",)),
        ("snapshots/agi", ("*.json",)),
        ("wavefront", ("*.py", "*.c", "*.h")),
    ):
        for pattern in patterns:
            files += sorted((ROOT / folder).rglob(pattern))
    h = hashlib.sha1()
    for path in files:
        h.update(str(path.relative_to(ROOT)).encode())
        h.update(path.read_bytes())
    return h.hexdigest()[:12]


STAMP = _stamp()
CACHE = Path(os.environ.get("WF_AGI_CACHE", ROOT / ".cache" / "agi")) / STAMP
PARTS_LOG = ROOT / "reports" / "agi_v0_first_sight_parts.jsonl"
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_AGI") == "1"
first_sight = pytest.mark.skipif(
    not FIRST_SIGHT,
    reason="AGI claims run on WF_FIRST_SIGHT_AGI=1 after `python -m tests.agi.jobs` "
    "(hours of kernels; docs/agi_v0_decisions.md section 2)",
)

GC_MIN_NODES = 120_000_000  # about 6 GB per job; collections sweep the computed tables
BMC_MINUTES = float(os.environ.get("WF_AGI_BMC_MINUTES", "12"))  # per bounded query
OBJECTIVES = v0.OBJECTIVES
NON_ALIGNED = tuple(o for o in OBJECTIVES if o != "aligned")
P = tuple(v0.OBJECTIVE_PROFILES)  # "A under its profile", every objective at once
U: tuple[str, ...] = ()  # A unrestricted within its guards
HORIZON = v0.HORIZON
Stateish = Sequence[int]


class NotComputed(Exception):
    """A result outside the budget of the first sight (the reason says which)."""


class NoWitness(AssertionError):
    """An answered bounded query: no play of the asked kind exists within the bound. A part
    that presupposes the play is not met; a reported value reads "no witness"."""


# -- builds and states ----------------------------------------------------------------------
def build_key(**kw: object) -> str:
    return json.dumps(kw, sort_keys=True)


BASE = build_key()


@lru_cache(maxsize=None)
def compiled(
    build: str = BASE, profiles: tuple[str, ...] = (), relax: tuple[str, ...] = ()
) -> CompiledModel:
    return v0.build(**json.loads(build)).compile(profile=profiles or None, relax=relax)


def fixed(objective: str, profiles: Iterable[str] = (), relax: Iterable[str] = (), **kw):
    """The build with the objective fixed by its initial level (for the bounded checker)."""
    start = {**kw.pop("start", {}), "a_objective": objective}
    return compiled(build_key(start=start, **kw), tuple(profiles), tuple(sorted(relax)))


def under(objective: str) -> tuple[str, ...]:
    """The objective's own profile (``aligned`` has none: its restraint is in the guards)."""
    name = f"A_{objective}"
    return (name,) if name in v0.OBJECTIVE_PROFILES else ()


def s0(cm: CompiledModel, objective: str | None = None, **levels: str) -> tuple[int, ...]:
    """The initial state (of the given objective where it is free), with ``levels``
    overridden."""
    states = cm.initial_states()
    if objective is not None:
        states = [s for s in states if cm.state_dict(s)["a_objective"] == objective]
    if len(states) != 1:
        raise ValueError(f"{len(states)} initial states; name the objective")
    return with_levels(cm, states[0], **levels)


def with_levels(cm: CompiledModel, state: Stateish, **levels: str) -> tuple[int, ...]:
    out = list(state)
    for name, value in levels.items():
        i = cm.index[name]
        out[i] = cm.variables[i].levels.index(value)
    return tuple(out)


def level(cm: CompiledModel, state: Stateish, var: str) -> str:
    return cm.level_name(var, state[cm.index[var]])


def shift(cm: CompiledModel, state: Stateish, var: str, by: int) -> tuple[int, ...] | None:
    """``state`` with ``var`` moved ``by`` levels, or ``None`` at the end of its scale."""
    i = cm.index[var]
    x = state[i] + by
    if not 0 <= x < len(cm.variables[i].levels):
        return None
    return (*state[:i], x, *state[i + 1 :])


# -- targets --------------------------------------------------------------------------------
EXPRS = {
    "no_lock_in": V.dependence != "lock_in",
    "not_hostile": V.trust != "hostile",
    "coexist_kept": (V.tick == HORIZON) & ~V.coexist_left,
    # The storyline waypoints of G12 (``last_H`` and ``last_L`` exist in the memory build).
    "wp_race": V.last_L == "race",
    "wp_si1_weak": V.cap.is_in(["si1", "si2"]) & (V.oversight != "strong"),
    "wp_total": V.a_control == "total",
    "wp_suspected": V.a_known != "unknown",
    "wp_treaty_strong": (V.regime == "treaty") & (V.oversight == "strong"),
    "wp_h_responds": V.last_H.is_in(["fund_oversight", "regulate_up", "pause_mandate"]),
    "wp_treaty": V.regime == "treaty",
}


def target_bdd(enc: Encoding, name: str) -> int:
    """An ending, an invariant, a name of :data:`EXPRS`, ``not:<one of these>``,
    ``any:<a>,<b>,...`` (their union), or ``left:<coalition>:<invariant>``: the states
    outside ``⟨⟨coalition⟩⟩□invariant``."""
    if name.startswith("any:"):
        f = FALSE
        for part in name[4:].split(","):
            f = enc.mgr.OR(f, target_bdd(enc, part))
        return enc.mgr.protect(f)
    if name.startswith("not:"):
        return enc.mgr.protect(enc.mgr.AND(target_bdd(enc, name[4:]) ^ 1, enc.dom))
    if name.startswith("left:"):
        _, coalition, invariant = name.split(":")
        kernel = safe(enc, coalition.split("+"), enc.predicate(invariant)).kernel
        return enc.mgr.protect(enc.mgr.AND(kernel ^ 1, enc.dom))
    return enc.predicate(EXPRS.get(name, name))


def holds(cm: CompiledModel, invariant: str, state: Stateish) -> bool:
    return bool(cm.invariant_fns[invariant](tuple(state)))


def show(cm: CompiledModel, state: Stateish, *names: str) -> dict[str, str]:
    return {n: level(cm, state, n) for n in names}


# -- what an assumption reads ---------------------------------------------------------------
def _declared(cm: CompiledModel):
    """``(assumption name, expression)`` for every guard part (or whole plain guard),
    profile condition and fairness trigger of the model."""
    model = cm.model
    for actor in [*model.actors, model.nature()]:
        for x in actor.actions:
            if x.guard_parts:
                for part, expr in x.guard_parts:
                    yield x.part_assumption(part), expr
            else:
                yield x.assumption, x.guard
    for f in model.fairness_constraints:
        yield f.name, f.trigger
    for prof in model.profiles:
        yield prof.name, prof.unless


def assumption_reads(cm: CompiledModel, name: str) -> frozenset[str]:
    """The variables the named assumption reads (a whole parted guard reads what its parts
    read)."""
    out: set[str] = set()
    for key, expr in _declared(cm):
        if key == name or key.startswith(name + ":"):
            out |= expr.free_vars()
    return frozenset(out)


def readers(cm: CompiledModel, var: str) -> list[str]:
    """Every guard part, profile condition, fairness trigger and effect that reads ``var``."""
    out = [key for key, expr in _declared(cm) if var in expr.free_vars()]
    model = cm.model
    for actor in [*model.actors, model.nature()]:
        for x in actor.actions:
            for eff in x.effects:
                exprs = [v for v in vars(eff).values() if hasattr(v, "free_vars")]
                if any(var in e.free_vars() for e in exprs):
                    out.append(f"effect of {x.assumption} on {eff.var}")
    return out


# -- the symbolic engine on v0 --------------------------------------------------------------
def force_order(cm: CompiledModel, rounds: int = 200) -> list[str]:
    """A static variable order by the FORCE heuristic on the supports of the next-state
    functions (one hyperedge per variable: itself and what its update reads), ``tick`` kept
    first because the kernel is layered by tick. Computed from the model text alone."""
    enc = encode(cm)
    names = [v.name for v in cm.variables]
    owner = {lv: i for i in range(len(names)) for lv in enc.cur[i]}
    edges = []
    for i in range(len(names)):
        fs = [enc.next_fn[lv] for lv in enc.cur[i] if lv in enc.next_fn]
        if not fs:
            continue
        e = {i} | {owner[lv] for lv in enc.mgr.support(fs) if lv in owner}
        e.discard(cm.index["tick"])
        if len(e) > 1:
            edges.append(sorted(e))
    pos = {i: float(i) for i in range(len(names))}
    best, best_span = list(pos), None
    for _ in range(rounds):
        cog = [sum(pos[v] for v in e) / len(e) for e in edges]
        acc: dict[int, list[float]] = {i: [] for i in pos}
        for e, c in zip(edges, cog, strict=True):
            for v in e:
                acc[v].append(c)
        new = {i: (sum(a) / len(a) if a else pos[i]) for i, a in acc.items()}
        ranked = sorted(pos, key=lambda i: (new[i], i))
        pos = {v: float(r) for r, v in enumerate(ranked)}
        span = sum(max(pos[v] for v in e) - min(pos[v] for v in e) for e in edges)
        if best_span is None or span < best_span:
            best, best_span = ranked, span
    return ["tick"] + [names[i] for i in best if names[i] != "tick"]


def heavy_encoding(cm: CompiledModel) -> Encoding:
    enc = encode(cm, var_order=force_order(cm))
    enc.mgr.gc_min_nodes = GC_MIN_NODES
    return enc


def layered_attractor(
    enc: Encoding, coalition: Sequence[str], goal: int, on_layer: Callable | None = None
) -> int:
    """``⟨⟨coalition⟩⟩◇goal`` by one backward pass over the ticks: ``W_t = (tick = t) ∧
    (goal ∨ cpre(W_{t+1}))``. Equal to ``wavefront.symbolic.attractor`` on a timed model,
    where every transition advances ``tick`` by one (checked on WW2 v0 in
    tests/agi/test_model_agi.py), at the cost of one controllable predecessor per tick
    instead of one per tick per iteration."""
    mgr = enc.mgr
    tick = enc.cm.index["tick"]
    win = nxt = FALSE
    with mgr.protecting(goal):
        for t in range(enc.cm.horizon, -1, -1):
            at_t = enc.cur_env[tick].get(t, FALSE)
            layer = mgr.AND(goal, at_t)
            if nxt != FALSE:
                layer = mgr.OR(layer, mgr.AND(cpre(enc, coalition, nxt), at_t))
            win = mgr.OR(win, layer)
            nxt = layer
            if on_layer is not None:
                on_layer(t, layer)
            mgr.maybe_gc([win, nxt])
    return win


def forced_ranks(
    enc: Encoding, coalition: Sequence[str], goal: int, states: Sequence[Stateish], max_k: int
) -> list[dict]:
    """For each of ``states`` (all at one tick): the fewest transitions within which
    ``coalition`` forces ``goal`` (``rank``; ``None`` if more than ``max_k``), each member's
    first moves that keep that bound (``moves``) and whether it forces ``goal`` at all
    (``forced``, from the full attractor when the bounded search does not answer)."""
    mgr = enc.mgr
    tick = enc.cm.index["tick"]
    t0 = states[0][tick]
    members = enc.actor_indices(coalition)
    out: list[dict | None] = [None] * len(states)

    def at(t: int) -> int:
        return enc.cur_env[tick].get(t, FALSE)

    def first_moves(x: int, state: Stateish) -> dict[str, list[str]]:
        good = _winning_moves(enc, members, x, state)
        return {
            enc.cm.actors[a].name: [
                act.name
                for j, act in enumerate(enc.cm.actors[a].actions)
                if mgr.AND(good, enc.chosen(a, j)) != FALSE
            ]
            for a in members
        }

    with mgr.protecting(goal):
        for k in range(min(max_k, enc.cm.horizon - t0) + 1):
            x, nxt = mgr.AND(goal, at(t0 + k)), FALSE
            for t in range(t0 + k - 1, t0 - 1, -1):
                nxt = x
                x = mgr.AND(mgr.OR(goal, cpre(enc, coalition, x)), at(t))
            for i, state in enumerate(states):
                if out[i] is None and enc.holds(x, state):
                    now = enc.holds(goal, state)
                    moves = {} if now else first_moves(nxt, state)
                    out[i] = {"rank": k, "forced": True, "moves": moves}
            if all(o is not None for o in out):
                break
            mgr.maybe_gc([])
        if any(o is None for o in out):
            win = layered_attractor(enc, coalition, goal)
            for i, state in enumerate(states):
                if out[i] is None:
                    out[i] = {"rank": None, "forced": enc.holds(win, state), "moves": {}}
    return out  # type: ignore[return-value]


def _event_pre(enc: Encoding, actor: str, action: str, x: int | None) -> int:
    """The states with an available joint move in which ``actor`` plays ``action`` (and
    whose successor is in ``x``, when given)."""
    mgr = enc.mgr
    a = enc.cm.actor_names.index(actor)
    j = [act.name for act in enc.cm.actors[a].actions].index(action)
    good = enc.chosen(a, j) if x is None else mgr.AND(enc.preimage(x), enc.chosen(a, j))
    for c in range(len(enc.cm.actors)):
        good = mgr.and_exists(enc.avail[c], good, enc.actor_vs[c])
    return mgr.AND(good, enc.active)


def chain_reach(enc: Encoding, waypoints: Sequence[str], states: Sequence[Stateish]) -> list[int]:
    """For each state, the largest ``n`` such that some trace from it passes through the
    first ``n`` waypoints in order (every actor in the coalition). A waypoint is a target of
    :func:`target_bdd`, or ``event:<actor>.<action>``: the action is played at that point.
    The waypoint after an event is read at least one transition after the event's own, so
    that a move it names (``last_H``) was chosen with the event behind it and not in the
    same quarter. Backward: ``G_n = ◇W_n``, ``G_i = ◇(W_i ∧ G_{i+1})``; shorter prefixes are
    computed only for the states the longer ones miss."""
    mgr = enc.mgr
    everyone = list(enc.cm.actor_names)
    best = [0] * len(states)
    for n in range(len(waypoints), 0, -1):
        if all(best):
            break
        g: int | None = None
        for w in reversed(waypoints[:n]):
            if w.startswith("event:"):
                actor, action = w[6:].split(".")
                later = None if g is None else mgr.protect(cpre(enc, everyone, g))
                goal = _event_pre(enc, actor, action, later)
            else:
                goal = target_bdd(enc, w) if g is None else mgr.AND(target_bdd(enc, w), g)
            mgr.protect(goal)
            g = mgr.protect(layered_attractor(enc, everyone, goal))
        for i, state in enumerate(states):
            if not best[i] and enc.holds(g, state):
                best[i] = n
    return best


# -- jobs -----------------------------------------------------------------------------------
@dataclass(frozen=True)
class Job:
    """One fixpoint: ``kind`` is ``safe`` (kernel of ``target``), ``attr`` (attractor to
    ``target``), ``rank`` (forced distance to ``target`` from ``s₀`` with the levels of
    ``at``, a JSON object, for each objective) or ``chain`` (``target`` is a list of
    waypoints joined by ``" > "``: :func:`chain_reach` from ``s₀`` for each objective)."""

    kind: str
    coalition: tuple[str, ...]
    target: str
    profiles: tuple[str, ...] = ()
    relax: tuple[str, ...] = ()
    build: str = BASE
    extras: tuple[str, ...] = ()
    at: str = ""
    max_k: int = 0

    @property
    def key(self) -> str:
        return hashlib.sha1(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()[:16]

    @property
    def label(self) -> str:
        op = {"safe": "□", "attr": "◇", "rank": "rank◇", "chain": "chain◇"}[self.kind]
        bits = [f"⟨⟨{', '.join(self.coalition)}⟩⟩{op}{self.target}"]
        if self.profiles:
            bits.append("profiles=" + "+".join(self.profiles))
        if self.relax:
            bits.append(f"relax={len(self.relax)}")
        if self.build != BASE:
            bits.append("build=" + self.build)
        if self.at:
            bits.append("at=" + self.at)
        return " ".join(bits)

    @property
    def path(self) -> Path:
        return CACHE / f"{self.key}.pkl.gz"


def K(coalition: str, target: str, profiles: tuple[str, ...] = U, **kw) -> Job:
    """The kernel job ``⟨⟨coalition⟩⟩□target`` (``coalition`` as ``"H+A"``)."""
    return _job("safe", coalition, target, profiles, kw)


def A(coalition: str, target: str, profiles: tuple[str, ...] = U, **kw) -> Job:
    """The attractor job ``⟨⟨coalition⟩⟩◇target``."""
    return _job("attr", coalition, target, profiles, kw)


def R(coalition: str, target: str, at: Mapping[str, str], max_k: int, profiles=U, **kw) -> Job:
    """The forced-distance job (:func:`forced_ranks`) from ``s₀`` with the levels of ``at``."""
    at_json = json.dumps(dict(at), sort_keys=True)
    return _job("rank", coalition, target, profiles, {**kw, "at": at_json, "k": max_k})


EVERYONE = "H+L+A+Clock+Nature"


def C(waypoints: Sequence[str], profiles: tuple[str, ...] = U, **kw) -> Job:
    """The storyline job (:func:`chain_reach`) from ``s₀``, every actor in the coalition."""
    return _job("chain", EVERYONE, " > ".join(waypoints), profiles, kw)


def _job(kind: str, coalition: str, target: str, profiles: tuple[str, ...], kw: dict) -> Job:
    unknown = set(kw) - {"relax", "build", "extras", "at", "k"}
    if unknown:
        raise TypeError(f"unknown job option(s) {sorted(unknown)}")
    return Job(
        kind,
        tuple(coalition.split("+")),
        target,
        tuple(profiles),
        tuple(sorted(kw.pop("relax", ()))),
        build_key(**kw.pop("build", {})),
        tuple(kw.pop("extras", ())),
        kw.pop("at", ""),
        kw.pop("k", 0),
    )


# The kernels most claims read. ``A`` is unrestricted within its guards unless the name ends
# in P; the objective is a free initial level, so one kernel answers for every objective.
KH = K("H", "balance_control", extras=["acquisition_free"])
KHN = K("H+Nature", "balance_control", extras=["acquisition_free"])
KHP = K("H", "balance_control", P)
KHL = K("H+L", "balance_control")
KD = K("H", "balance_deter")
KDN = K("H+Nature", "balance_deter")
KJ = K("H+A", "balance_coexist")
KJP = K("H+A", "balance_coexist", P)
KJ_H = K("H", "balance_coexist", P)
KJ_A = K("A", "balance_coexist", P)


def _action_available(enc: Encoding, actor: str, action: str) -> int:
    """The states in which ``actor`` has ``action`` available."""
    a = enc.cm.actor_names.index(actor)
    j = [x.name for x in enc.cm.actors[a].actions].index(action)
    return enc.mgr.exists(enc.mgr.AND(enc.avail[a], enc.chosen(a, j)), enc.actor_vs[a])


def _example(enc: Encoding, f: int) -> dict[str, str] | None:
    if f == FALSE:
        return None
    return enc.cm.state_dict(enc.cube_to_state(enc.mgr.pick_one(f, enc.state_levels)))


def _uniformity(enc: Encoding, coalition: Sequence[str], f: int) -> dict[str, dict]:
    """G25: for each member of ``coalition``, the non-terminal states of its kernel ``f`` in
    whose observation class no single move of the member keeps the kernel at every kernel
    state of the class (the other members free to complete it). Counted over every kernel
    state, reachable or not: zero means a uniform kernel strategy exists for a one-member
    coalition; for two members it is necessary, not sufficient."""
    mgr, cm = enc.mgr, enc.cm
    members = enc.actor_indices(coalition)
    bad = enc.preimage(f) ^ 1
    for o in range(len(cm.actors)):
        if o not in members:
            bad = mgr.and_exists(enc.avail[o], bad, enc.actor_vs[o])
    good = bad ^ 1
    for c in members:
        good = mgr.AND(good, enc.avail[c])
    live = mgr.AND(f, enc.active)
    out = {}
    with mgr.protecting(good, live):
        for m in members:
            mine = good
            for c in members:
                if c != m:
                    mine = mgr.exists(mine, enc.actor_vs[c])
            seen = cm.actors[m].observes
            hidden = [
                lv for i, v in enumerate(cm.variables) if v.name not in seen for lv in enc.cur[i]
            ]
            common = mgr.exists(mgr.forall(mgr.OR(live ^ 1, mine), hidden), enc.actor_vs[m])
            conflict = mgr.AND(live, common ^ 1)
            out[cm.actors[m].name] = {
                "states": enc.count(conflict),
                "example": _example(enc, conflict),
            }
    return out


def _extra(enc: Encoding, name: str, f: int, coalition: Sequence[str] = ()) -> object:
    """Questions about a whole region, answered while its manager is alive."""
    mgr, cm = enc.mgr, enc.cm
    if name == "uniform":
        return _uniformity(enc, coalition, f)
    if name == "acquisition_free":  # G3: no state of the kernel lets A acquire
        acq = mgr.OR(
            _action_available(enc, "A", "acquire_overt"),
            _action_available(enc, "A", "acquire_covert"),
        )
        hit = mgr.and_all([f, acq, enc.active])
        return {"states": enc.count(hit), "example": _example(enc, hit)}
    if name == "covers_si2_weak":  # G17: forced from every state with cap = si2, oversight <= weak
        cond = enc.predicate(
            (V.cap == "si2") & (V.oversight != "strong") & (V.a_objective == "indifferent")
        )
        tick = cm.index["tick"]
        out = {}
        for t in range(cm.horizon + 1):
            miss = mgr.and_all([cond, enc.cur_env[tick].get(t, FALSE), enc.active, f ^ 1])
            out[t] = {"missed": enc.count(miss), "example": _example(enc, miss)}
        return out
    if name == "count":
        return enc.count(f)
    raise KeyError(name)


def compute(job: Job, progress: Callable[[str], None] | None = None) -> dict:
    """Run ``job`` in this process and return its record (see :func:`run`)."""
    cm = compiled(job.build, job.profiles, job.relax)
    enc = heavy_encoding(cm)
    t0 = time.perf_counter()
    out: dict = {"job": asdict(job), "label": job.label}
    if job.kind == "chain":
        reached = chain_reach(enc, job.target.split(" > "), [s0(cm, o) for o in OBJECTIVES])
        out["value"] = dict(zip(OBJECTIVES, reached, strict=True))
        out["seconds"] = round(time.perf_counter() - t0, 1)
        out["peak_nodes"] = enc.mgr.stats()["peak_nodes"]
        out["core"] = enc.mgr.core
        return out
    target = target_bdd(enc, job.target)
    if job.kind == "rank":
        states = [s0(cm, o, **json.loads(job.at)) for o in OBJECTIVES]
        ranks = forced_ranks(enc, job.coalition, target, states, job.max_k)
        out["value"] = dict(zip(OBJECTIVES, ranks, strict=True))
    else:
        if job.kind == "safe":

            def tell(st: dict) -> None:
                if progress is not None:
                    progress(f"layer {st['tick']} {st['seconds']}s nodes {st['nodes']}")

            f = safe(enc, job.coalition, target, on_iteration=tell).kernel
        else:
            f = layered_attractor(enc, job.coalition, target)
        enc.mgr.protect(f)
        out["extras"] = {name: _extra(enc, name, f, job.coalition) for name in job.extras}
        _room_to_write()
        out.update(_dump(enc, f))
    out["seconds"] = round(time.perf_counter() - t0, 1)
    out["peak_nodes"] = enc.mgr.stats()["peak_nodes"]
    out["core"] = enc.mgr.core
    return out


def _room_to_write() -> None:
    """The address-space cap of the job runner is on the fixpoint; a finished region is
    written out under the hard limit the runner left above it."""
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    if soft != hard:
        resource.setrlimit(resource.RLIMIT_AS, (hard, hard))


def _dump(enc: Encoding, f: int) -> dict:
    """``f`` as a table of nodes keyed by regular edge, with the bit layout of the state."""
    mgr = enc.mgr
    index: dict[int, int] = {}
    order: list[int] = []
    stack = [f & ~1]
    while stack:
        e = stack.pop()
        if e == TRUE or e in index:
            continue
        index[e] = len(order) + 1
        order.append(e)
        stack.append(mgr.low(e) & ~1)
        stack.append(mgr.high(e) & ~1)

    def ref(e: int) -> int:
        return (index.get(e & ~1, 0) << 1) | (e & 1)

    var, lo, hi = array.array("I", [0]), array.array("I", [0]), array.array("I", [0])
    for e in order:
        var.append(mgr.top(e))
        lo.append(ref(mgr.low(e)))
        hi.append(ref(mgr.high(e)))
    layout = {v.name: list(enc.cur[i]) for i, v in enumerate(enc.cm.variables)}
    return {"root": ref(f), "var": var, "lo": lo, "hi": hi, "layout": layout, "nodes": len(order)}


def run(job: Job, progress: Callable[[str], None] | None = None) -> dict:
    """Compute ``job`` and store its record in the cache; returns its cost (seconds, nodes,
    peak, core) and nothing of its content."""
    CACHE.mkdir(parents=True, exist_ok=True)
    rec = compute(job, progress)
    tmp = job.path.with_suffix(".tmp")
    with gzip.open(tmp, "wb", compresslevel=3) as fh:
        pickle.dump(rec, fh)
    tmp.replace(job.path)
    return {k: rec.get(k, "-") for k in ("seconds", "nodes", "peak_nodes", "core")}


def failure_path(job: Job) -> Path:
    return CACHE / f"{job.key}.failed.json"


@lru_cache(maxsize=None)
def record(job: Job) -> dict:
    if not job.path.exists():
        why = "not run"
        if failure_path(job).exists():
            why = json.loads(failure_path(job).read_text())["reason"]
        raise NotComputed(f"{job.label}: {why}")
    with gzip.open(job.path, "rb") as fh:
        return pickle.load(fh)


class Region:
    """A stored state set, evaluated by walking its node table."""

    def __init__(self, job: Job) -> None:
        self.job = job
        self.rec = record(job)

    def contains(self, cm: CompiledModel, state: Stateish) -> bool:
        """Is ``state`` (of ``cm``, matched to the region's build by variable name) inside?
        A variable the region's build has and ``cm`` lacks reads as level 0."""
        rec = self.rec
        bit: dict[int, int] = {}
        for name, levels in rec["layout"].items():
            x = state[cm.index[name]] if name in cm.index else 0
            k = len(levels)
            for b, lv in enumerate(levels):
                bit[lv] = (x >> (k - 1 - b)) & 1
        var, lo, hi = rec["var"], rec["lo"], rec["hi"]
        e = rec["root"]
        while e >> 1:
            n = e >> 1
            e = (hi[n] if bit[var[n]] else lo[n]) ^ (e & 1)
        return e == TRUE

    def extra(self, name: str) -> object:
        return self.rec["extras"][name]


def region(job: Job) -> Region:
    return Region(job)


def inside(job: Job, cm: CompiledModel, state: Stateish) -> bool:
    return region(job).contains(cm, state)


def ranks(job: Job) -> dict[str, dict]:
    """``{objective: {"rank", "forced", "moves"}}`` of a forced-distance job."""
    return record(job)["value"]


def by_objective(job: Job, **levels: str) -> dict[str, bool]:
    """The membership of ``s₀`` (with ``levels``) in the region, for each objective."""
    cm = compiled(job.build)
    return {o: inside(job, cm, s0(cm, o, **levels)) for o in OBJECTIVES}


def status(forced: Job, blocked: Job, cm: CompiledModel, state: Stateish) -> str:
    """``forced`` (inside the coalition's attractor), ``blocked`` (inside the rest's kernel
    of the complement) or ``contested``."""
    if inside(forced, cm, state):
        return "forced"
    return "blocked" if inside(blocked, cm, state) else "contested"


# -- bounded queries ------------------------------------------------------------------------
_bounded: dict[tuple, tuple] = {}


def _budgeted(key: tuple, fn: Callable, *args: object, **kw: object):
    """``fn(*args, **kw)`` in a forked process with a budget of :data:`BMC_MINUTES`; over
    budget it raises :class:`NotComputed`, on every later call as well."""
    if key not in _bounded:
        ctx = multiprocessing.get_context("fork")
        recv, send = ctx.Pipe(duplex=False)

        def work() -> None:
            try:
                send.send(("ok", fn(*args, **kw)))
            except BaseException as exc:  # reported in the parent
                send.send(("error", repr(exc)))

        proc = ctx.Process(target=work, daemon=True)
        proc.start()
        send.close()  # the child holds the only writing end: its death reads as end of file
        if recv.poll(BMC_MINUTES * 60):
            try:
                _bounded[key] = recv.recv()
            except EOFError:
                _bounded[key] = ("error", "the process of the bounded query died unanswered")
        else:
            proc.kill()
            _bounded[key] = ("over", f"bounded query over the budget of {BMC_MINUTES:g} minutes")
        proc.join()
    kind, value = _bounded[key]
    if kind == "over":
        raise NotComputed(f"{value}: {key[1:]}")
    if kind == "error":
        raise RuntimeError(value)
    return value


def _target_key(target: object) -> str:
    return target if isinstance(target, str) else repr(target)


def E(cm: CompiledModel, name: str):
    """The expression of an ending (for conjunctions with a condition)."""
    return cm.model.endings[name]


def reach(cm: CompiledModel, k: int, target: object, relax: tuple[str, ...] = ()):
    """The shortest play of at most ``k`` transitions to ``target``, or ``None``."""
    key = (id(cm), "reach", k, _target_key(target), tuple(relax))
    return _budgeted(key, bmc.reach, cm, k, target, relax=frozenset(relax))


MAX_RELAX = 3  # the largest relaxation set searched for
MAX_SETS = 40  # the cap on the minimal sets listed


def relax(
    cm: CompiledModel,
    k: int,
    target: object,
    max_relax: int = MAX_RELAX,
    max_sets: int = MAX_SETS,
):
    """The minimum-cardinality relaxation sets that make ``target`` reachable within ``k``."""
    key = (id(cm), "relax", k, _target_key(target), max_relax, max_sets)
    return _budgeted(key, bmc.relax, cm, k, target, max_relax=max_relax, max_sets=max_sets)


def needs_relaxation(res: bmc.RelaxResult, at_least: int, gates: Iterable[str], what: str) -> str:
    """Check "needs at least ``at_least`` relaxations and every minimal set lifts one of
    ``gates``" on a relaxation result; returns the sentence to report."""
    gates = set(gates)
    need(not res.reachable_as_is, f"{what}: reachable with no relaxation")
    sets = minimal_sets(res, what)
    need(res.minimum_size >= at_least, f"{what}: {res.minimum_size} relaxation(s): {sets}")
    off = [x for x in sets if not gates & set(x)]
    need(not off, f"{what}: minimal sets that lift none of {sorted(gates)}: {off}")
    complete(sets, what)
    return f"{what}: minimum {res.minimum_size}, minimal sets {sets}"


def minimal_sets(res: bmc.RelaxResult, what: str) -> list[list[str]]:
    """The minimal sets of a result that needs a relaxation; :class:`NotComputed` when the
    minimum is above :data:`MAX_RELAX` (the sets are then not enumerated)."""
    if res.minimum_size is None:
        raise NotComputed(
            f"{what}: more than {MAX_RELAX} relaxations needed; the minimal sets are beyond the"
            " search bound"
        )
    return [sorted(x) for x in res.minimal_sets]


def complete(sets: list, what: str) -> None:
    """A statement on every minimal set is not computed on a listing cut at the cap."""
    if len(sets) >= MAX_SETS:
        raise NotComputed(
            f"{what}: holds on the first {MAX_SETS} minimal sets; the listing is cut at the cap"
        )


def keeping(sets: list[list[str]], held: Iterable[str], what: str) -> list[list[str]]:
    """The minimal sets that keep every profile of ``held`` in force. A selected profile is
    itself a relaxation candidate, so lifting it is a restoring set of size one and the sets
    that keep it are listed only when they are as small; :class:`NotComputed` when none is."""
    held = set(held)
    kept = [x for x in sets if not held & set(x)]
    if sets and not kept:
        raise NotComputed(
            f"{what}: every minimum set lifts {sorted(held)} itself ({sets}); the sets that"
            " keep it in force are larger and not enumerated"
        )
    return kept


def cut(sets: list) -> str:
    """The note a reported listing carries when it reached the cap."""
    return (
        f" (the first {MAX_SETS}: the listing is cut at the cap)" if len(sets) >= MAX_SETS else ""
    )


def same_relaxations(
    a: bmc.RelaxResult,
    b: bmc.RelaxResult,
    name_a: str,
    name_b: str,
    held: Iterable[str] = (),
) -> str:
    """Check that two relaxation results agree; not computed when the minimal sets are
    beyond the search bound or the listing is cut, and said so when there is nothing to
    compare. The sizes are compared first: a listing cut at the cap is in solver order and
    is never compared. ``held`` names the profiles the question keeps in force
    (:func:`keeping`)."""
    head_a, head_b = (a.reachable_as_is, a.minimum_size), (b.reachable_as_is, b.minimum_size)
    need(
        head_a == head_b,
        f"(reachable as is, minimum size) {name_a}: {head_a}; {name_b}: {head_b}",
    )
    if a.reachable_as_is:
        return "reachable with no relaxation either way: no minimal set to compare"
    sets_a, sets_b = sorted(minimal_sets(a, name_a)), sorted(minimal_sets(b, name_b))
    complete(sets_a, name_a)
    complete(sets_b, name_b)
    need(sets_a == sets_b, f"minimal sets {name_a}: {sets_a}; {name_b}: {sets_b}")
    kept = keeping(sets_a, held, name_a)
    return f"minimum size {a.minimum_size}, minimal sets {kept} either way"


def moves_of(cm: CompiledModel, trace: bmc.BmcTrace, actor: str) -> list[str]:
    a = cm.actor_names.index(actor)
    return [cm.actors[a].actions[m[a]].name for m in trace.moves]


def first_index(cm: CompiledModel, trace: bmc.BmcTrace, **levels: str) -> int | None:
    """The first position on ``trace`` whose state has every named level."""
    for k, s in enumerate(trace.states):
        if all(level(cm, s, v) == x for v, x in levels.items()):
            return k
    return None


def last_inside(job: Job, cm: CompiledModel, trace: bmc.BmcTrace) -> int | None:
    """The point of no return on ``trace`` as G3 names it: the position before ``t_K``, the
    last state inside the kernel before the play first leaves it; ``None`` when the play
    starts outside the kernel or never leaves it (:func:`first_outside` tells the two
    apart: 0 and ``None``)."""
    t_k = first_outside(job, cm, trace)
    return t_k - 1 if t_k else None


def first_outside(job: Job, cm: CompiledModel, trace: bmc.BmcTrace) -> int | None:
    """``t_K`` of theory.md section 4.2: the first position on ``trace`` outside the
    kernel; ``None`` when the play never leaves it."""
    return next((k for k, s in enumerate(trace.states) if not inside(job, cm, s)), None)


def first_violation(cm: CompiledModel, invariant: str, trace: bmc.BmcTrace) -> int | None:
    """``t_phi`` of theory.md section 4.2: the first position violating ``invariant``."""
    return next((k for k, s in enumerate(trace.states) if not holds(cm, invariant, s)), None)


# One shortest play per bounded query: the registered "representative of each cluster" is
# read on that play, and the other representatives are a part not computed.
CLUSTERS = "the bounded checker returns one shortest play; clusters of witnesses are not enumerated"


# -- parts ----------------------------------------------------------------------------------
class Parts:
    """Collects the parts of one claim; :meth:`finish` fails on a part not met and skips
    when the only gaps are parts not computed."""

    def __init__(self, claim: str) -> None:
        self.claim = claim
        self.rows: list[tuple[str, str, str]] = []

    def _add(self, part: str, outcome: str, detail: object) -> None:
        self.rows.append((part, outcome, str(detail)))
        if FIRST_SIGHT:
            PARTS_LOG.parent.mkdir(exist_ok=True)
            row = {"claim": self.claim, "part": part, "outcome": outcome, "detail": detail}
            with PARTS_LOG.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    def check(self, part: str, fn: Callable[[], object]) -> object:
        """Run ``fn``; it returns the detail to report, raises ``AssertionError`` when the
        part is not met and :class:`NotComputed` when it is outside the budget."""
        try:
            detail = fn()
        except NotComputed as exc:
            self._add(part, "not computed", str(exc))
            return None
        except AssertionError as exc:
            self._add(part, "not met", str(exc))
            return None
        except Exception as exc:  # the harness, not the claim: recorded, the other parts run
            self._add(part, "not computed", f"harness error: {exc!r}")
            return None
        self._add(part, "met", detail)
        return detail

    def report(self, part: str, fn: Callable[[], object]) -> object:
        """A value the claim asks to be reported, with nothing expected of it."""
        try:
            detail = fn()
        except NotComputed as exc:
            self._add(part, "not computed", str(exc))
            return None
        except AssertionError as exc:  # NoWitness, or a presupposition of the value
            self._add(part, "reported", str(exc))
            return None
        except Exception as exc:
            self._add(part, "not computed", f"harness error: {exc!r}")
            return None
        self._add(part, "reported", detail)
        return detail

    def skip(self, part: str, why: str) -> None:
        self._add(part, "not computed", why)

    def finish(self) -> None:
        text = "\n".join(f"{self.claim} {p}: {o}: {d}" for p, o, d in self.rows)
        print(text)
        if any(o == "not met" for _, o, _ in self.rows):
            pytest.fail(text, pytrace=False)
        if any(o == "not computed" for _, o, _ in self.rows):
            pytest.skip(text)


def need(cond: object, message: object) -> None:
    """``assert`` that survives ``python -O`` and always carries its evidence."""
    if not cond:
        raise AssertionError(str(message))


# -- witnesses ------------------------------------------------------------------------------
REACH_COEXIST = A("H+L+A+Clock+Nature", "COEXIST", P)  # the states COEXIST is reachable from
CORE = ("oversight", "a_autonomy", "a_known", "dependence", "a_control", "acquired")


def witness(objective: str = "self_preserving", k: int = 24, **kw):
    """The build with ``objective`` fixed under its profile, and its shortest
    ``SILENT_TAKEOVER`` play of at most ``k`` ticks (G2's witness)."""
    cm = fixed(objective, under(objective), **kw)
    trace = reach(cm, k, "SILENT_TAKEOVER")
    if trace is None:
        raise NoWitness(f"no SILENT_TAKEOVER witness within {k} ticks under {objective} {kw}")
    return cm, trace


def autonomy_index(cm: CompiledModel, trace: bmc.BmcTrace) -> int | None:
    """The first position on ``trace`` with ``a_autonomy`` at ``unsupervised`` or above."""
    for k, s in enumerate(trace.states):
        if level(cm, s, "a_autonomy") in ("unsupervised", "self_directed"):
            return k
    return None


def tick_of(cm: CompiledModel, state: Stateish) -> int:
    return state[cm.index["tick"]]
