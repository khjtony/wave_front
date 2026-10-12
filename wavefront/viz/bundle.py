"""The visualizer's data bundle (docs/visualizer.md section 5).

:func:`bundle` explores a model once and computes everything the page draws, as a
JSON-serializable dict; the page itself computes nothing that depends on the engine. The
schema (every list below is a JSON array; state ids index the ``states`` arrays):

``meta``
    ``name, description, fingerprint, horizon, timed, profile, caveat, budget``, plus
    ``initial_source`` (``"model"``, ``"explicit"`` or ``"snapshot"``), ``max_relax``,
    ``default`` (the filter selection the page opens with: ``hypothesis``, ``coalition``,
    ``ending`` indices) and ``counts`` (states, joint moves, joint moves included).
``variables``
    ``[{name, kind, levels, builtin, hidden_from, origin, swept}]`` in state order.
    ``builtin`` is true for the compiler's bookkeeping variables (tick, delay counters,
    last actions, fairness counters); latches are declared by the model and are not
    built-ins. ``hidden_from`` lists the actors that do not observe the variable.
``actors``
    ``[{name, is_nature, color_slot, actions: [{name, guard_text, source, speculative,
    delay, is_idle}]}]`` in joint-move order (Nature last). ``color_slot`` is the
    categorical slot (1-based, declaration order) or ``None`` for Nature.
``hypotheses``
    ``{variables, values, items}``. ``variables`` are the variables whose value differs
    between the initial states (the swept hypotheses); ``items`` has one entry per initial
    state: ``{label, values, state, reachable, identical_to, card, tables}``. ``card`` is
    the initial state card (status, shortest distance and margin per property and
    coalition, minimum depth to each ending); ``tables`` are the report tables computed by
    :func:`~wavefront.analysis.run_all` from this initial state.
``coalitions``
    ``[{name, members}]``; default each declared actor alone and all of them together.
``endings``
    The endings the page offers (default: every declared ending, then ``HORIZON``).
``all_endings``
    Every ending a terminal state can have (declared endings, then ``HORIZON`` in a timed
    model); ``states.ending`` indexes this list.
``properties``
    The predicates ``phi`` that statuses are computed against: one ``{kind: "avoid"}`` per
    offered declared ending (``phi`` = the ending does not hold) and one
    ``{kind: "invariant"}`` per declared invariant, each with ``id, name, label, text``.
``states``
    Per-state arrays: ``tick`` (the tick, or the BFS depth in an untimed model),
    ``terminal`` (0/1), ``ending`` (index into ``all_endings``, or -1), ``values`` (one array per
    variable of level indices), ``status[p][c]`` (a string with one digit per state: 0 kept,
    1 contested, 2 lost, 3 failed, for property ``p`` and coalition ``c``), ``depth[h]``
    (BFS depth from hypothesis ``h``'s initial state, -1 when unreachable from it) and
    ``rank[e][c]`` (attractor rank to ending ``e`` for coalition ``c``, -1 outside the
    attractor; the extra last entry ``c = len(coalitions)`` is every actor and Nature, the
    plain backward wavefront).
``moves``
    ``{complete, avail_table, avail, offset, succ}``: ``avail[s]`` indexes
    ``avail_table`` (per actor the available action indices) or is -1 when the state's
    moves are not included (always for terminal states); the successors of ``s`` are
    ``succ[offset[s] : offset[s] + n]`` in ``itertools.product`` order of the available
    actions (the last actor varies fastest). ``complete`` is false when the size policy
    kept only the neighborhood of the shown traces.
``traces``
    One entry per hypothesis and offered ending: ``{hypothesis, ending, states, moves,
    phases, classes, replays}`` (``states`` is ``None`` when the ending is unreachable from
    the hypothesis). ``phases[p][c]`` holds ``t_K, t_L, t_phi`` (state indices along the
    trace, ``None`` when the event does not happen); ``classes[p][c][t][a]`` lists
    ``[action, class]`` for each action actor ``a`` had at step ``t`` (class 0 safe, 1
    risky, 2 losing, 3 ends); ``replays`` replays the joint moves from every other
    hypothesis's initial state (see :func:`replay`).
``tables``
    ``speculative``: the speculative actions used by any reference trace or replay.
``snapshot``
    The loaded snapshot's date and per-variable provenance, or ``None``.

Status codes (docs/visualizer.md section 1), for a property ``phi`` and coalition ``C``:
*failed* when ``phi`` is false in the state; otherwise *kept* when the state is in
``Safe_C(phi)``, *lost* when it is in ``Attr_rest(not phi)`` (``rest`` is every actor not
in ``C``, Nature included) and *contested* otherwise.

Decision classes, for actor ``X`` playing action ``a`` in state ``s``, over all joint moves
where ``X`` plays ``a``: *safe* when every successor is kept (a terminal successor is kept
exactly when it satisfies ``phi``); else *ends* when every successor is terminal; else
*losing* when no successor is kept; else *risky*.
"""

from __future__ import annotations

import json
from collections import deque
from collections.abc import Collection, Iterable, Sequence
from pathlib import Path
from typing import Any

from ..analysis import distance_table, fingerprint, run_all
from ..analysis.relax import DEFAULT_MAX_STATES
from ..engine import Graph, attractor, explore, safe, witness
from ..model.compile import CompiledModel
from ..model.compile import compile as compile_model
from ..model.model import Model, ModelError
from ..report.markdown import CAVEAT
from .format import expr_text, guard_text

__all__ = [
    "bundle",
    "status_codes",
    "decision_classes",
    "replay",
    "STATUS_NAMES",
    "DECISION_NAMES",
    "DEFAULT_MAX_MOVES",
]

STATUS_NAMES = ("kept", "contested", "lost", "failed")
DECISION_NAMES = ("safe", "risky", "losing", "ends")
KEPT, CONTESTED, LOST, FAILED = range(4)
SAFE, RISKY, LOSING, ENDS = range(4)
DEFAULT_MAX_MOVES = 1_500_000
_BUILTIN_ORIGINS = ("tick", "pending", "last", "fair")

Coalition = tuple[str, ...]


# -- small helpers ---------------------------------------------------------------------------


def _coalition_name(members: Sequence[str]) -> str:
    return "{" + ", ".join(members) + "}"


def _normalize_coalitions(g: Graph, coalitions: Iterable[Iterable[str]] | None) -> list[Coalition]:
    cm = g.model
    if coalitions is None:
        players = [a.name for a in cm.actors if not a.is_nature]
        out: list[Coalition] = [(p,) for p in players]
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


def _rest(g: Graph, coalition: Collection[str]) -> list[str]:
    members = set(g.actor_indices(coalition))
    return [a.name for a in g.model.actors if a.index not in members]


def _bfs_depth(g: Graph, source: int) -> list[int]:
    depth = [-1] * g.size()
    depth[source] = 0
    queue = deque([source])
    while queue:
        s = queue.popleft()
        d = depth[s] + 1
        for t in g.succ[s]:
            if depth[t] < 0:
                depth[t] = d
                queue.append(t)
    return depth


def _num(x: int | float | None) -> int | str | None:
    """A distance as JSON: ``None`` stays, infinity becomes ``"unbounded"``."""
    if x is None:
        return None
    if isinstance(x, float):
        return "unbounded" if x == float("inf") else int(x)
    return int(x)


# -- statuses, decision classes and replays ---------------------------------------------------


def status_codes(g: Graph, coalition: Collection[str], phi: Collection[int]) -> list[int]:
    """Status code per state for ``coalition`` and the predicate ``phi`` (a set of state
    ids): 0 kept (in ``Safe_C(phi)``), 1 contested, 2 lost (in ``Attr_rest(not phi)``),
    3 failed (``phi`` is false)."""
    phi = set(phi)
    kernel = safe(g, coalition, phi).kernel
    outside = set(range(g.size())) - phi
    lost = attractor(g, _rest(g, coalition), outside).win
    codes = []
    for s in range(g.size()):
        if s not in phi:
            codes.append(FAILED)
        elif s in kernel:
            codes.append(KEPT)
        elif s in lost:
            codes.append(LOST)
        else:
            codes.append(CONTESTED)
    return codes


def decision_classes(g: Graph, codes: Sequence[int], state_id: int) -> list[list[list[int]]]:
    """Per actor, ``[action, class]`` for every action available in ``state_id`` (see the
    module docstring for the classes), from the status ``codes`` of one property and
    coalition. A terminal state has no decisions (empty lists)."""
    cm = g.model
    if g.terminal[state_id]:
        return [[] for _ in cm.actors]
    buckets: list[dict[int, list[int]]] = [{} for _ in cm.actors]
    for move, t in zip(g.moves[state_id], g.succ[state_id], strict=True):
        for i, j in enumerate(move):
            buckets[i].setdefault(j, []).append(t)
    out = []
    for i, avail in enumerate(g.avail[state_id]):
        row = []
        for j in avail:
            succ = buckets[i][j]
            kept = [codes[t] == KEPT for t in succ]
            if all(kept):
                cls = SAFE
            elif all(g.terminal[t] for t in succ):
                cls = ENDS
            elif not any(kept):
                cls = LOSING
            else:
                cls = RISKY
            row.append([j, cls])
        out.append(row)
    return out


def replay(
    cm: CompiledModel, g: Graph, start: int, joint_moves: Sequence[Sequence[int]]
) -> dict[str, Any]:
    """Replay ``joint_moves`` with ``cm.step`` from state ``start`` while every chosen action
    stays available (``cm.available``). Returns ``{states, moves, stop}``: ``stop`` is
    ``None`` when every move was replayed, else ``{index, reason, actor, action}`` with the
    state index along the replay where it stopped and why (``"unavailable"``: the actor's
    chosen action is not available there; ``"terminal"``: the replay reached a terminal
    state before the moves ran out; ``"unexplored"``: the successor is not in the graph)."""
    states = [start]
    moves: list[list[int]] = []
    for move in joint_moves:
        s = states[-1]
        index = len(states) - 1
        if g.terminal[s]:
            return {"states": states, "moves": moves, "stop": _stop(index, "terminal")}
        avail = cm.available(g.states[s])
        for actor, (j, acts) in enumerate(zip(move, avail, strict=True)):
            if j not in acts:
                stop = _stop(index, "unavailable", actor, j)
                return {"states": states, "moves": moves, "stop": stop}
        nxt = g.index.get(cm.step(g.states[s], move))
        if nxt is None:
            return {"states": states, "moves": moves, "stop": _stop(index, "unexplored")}
        moves.append(list(move))
        states.append(nxt)
    return {"states": states, "moves": moves, "stop": None}


def _stop(index: int, reason: str, actor: int | None = None, action: int | None = None) -> dict:
    return {"index": index, "reason": reason, "actor": actor, "action": action}


def _phases(codes: Sequence[int], ids: Sequence[int]) -> dict[str, int | None]:
    def first(pred) -> int | None:
        return next((k for k, s in enumerate(ids) if pred(codes[s])), None)

    return {
        "t_K": first(lambda c: c != KEPT),
        "t_L": first(lambda c: c in (LOST, FAILED)),
        "t_phi": first(lambda c: c == FAILED),
    }


# -- the bundle ---------------------------------------------------------------------------------


def _initial_states(
    cm: CompiledModel,
    initial: Sequence[Sequence[int]] | None,
    snapshot: str | Path | dict | None,
) -> tuple[list[tuple[int, ...]] | None, dict | None, str]:
    if snapshot is not None and initial is not None:
        raise ValueError("give either initial states or a snapshot, not both")
    if snapshot is not None:
        from ..evidence import read_snapshot, snapshot_to_state, validate_snapshot
        from ..evidence.snapshot import SnapshotError

        if isinstance(snapshot, dict):
            problems = validate_snapshot(snapshot)
            if problems:
                raise SnapshotError("invalid snapshot: " + "; ".join(problems), problems)
            data = snapshot
        else:
            data = read_snapshot(snapshot)
        state = snapshot_to_state(data, cm)
        info = {
            "date": data.get("date"),
            "model": data.get("model"),
            "variables": data.get("variables", {}),
        }
        return [tuple(state)], json.loads(json.dumps(info)), "snapshot"
    if initial is not None:
        return [tuple(int(x) for x in s) for s in initial], None, "explicit"
    return None, None, "model"


def _variables(cm: CompiledModel, swept: set[int]) -> list[dict]:
    players = [a for a in cm.actors if not a.is_nature]
    out = []
    for i, v in enumerate(cm.variables):
        out.append(
            {
                "name": v.name,
                "kind": v.kind,
                "levels": list(v.levels),
                "builtin": v.origin in _BUILTIN_ORIGINS,
                "hidden_from": [a.name for a in players if v.name not in a.observes],
                "origin": v.origin,
                "swept": i in swept,
            }
        )
    return out


def _actors(cm: CompiledModel) -> list[dict]:
    out = []
    slot = 0
    for a in cm.actors:
        if not a.is_nature:
            slot += 1
        out.append(
            {
                "name": a.name,
                "is_nature": a.is_nature,
                "color_slot": None if a.is_nature else slot,
                "actions": [
                    {
                        "name": x.name,
                        "guard_text": guard_text(x, cm),
                        "source": x.source,
                        "speculative": bool(x.speculative),
                        "delay": int(x.delay),
                        "is_idle": bool(x.is_idle),
                    }
                    for x in a.actions
                ],
            }
        )
    return out


def _tables(analysis: Any, cm: CompiledModel) -> dict:
    """The report tables of one :func:`run_all` result, as JSON."""
    order = {n: i for i, n in enumerate(cm.actor_names)}

    def coalitions(cs: Iterable[Iterable[str]]) -> list[list[str]]:
        return [sorted(c, key=order.__getitem__) for c in cs]

    relax = []
    for e in analysis.endings:
        r = analysis.relaxations[e]
        relax.append(
            {
                "ending": e,
                "sets": [list(s) for s in r],
                "minimum_size": r.minimum_size,
                "max_size": r.max_size,
                "ill_formed": [{"set": list(s), "message": m} for s, m in r.ill_formed],
                "undecided": [{"set": list(s), "message": m} for s, m in r.undecided],
            }
        )
    pivotal = [
        {
            "ending": e,
            "forcing": coalitions(analysis.pivotal[e].forcing),
            "blocking": coalitions(analysis.pivotal[e].blocking),
        }
        for e in analysis.endings
    ]
    sensitivity = []
    for (inv, c), rows in analysis.sensitivity.items():
        sensitivity.append(
            {
                "invariant": inv,
                "coalition": list(c),
                "rows": [
                    {
                        "variable": r.variable,
                        "from": r.from_level,
                        "to": r.to_level,
                        "states": r.states,
                        "base_in_kernel": r.base_in_kernel,
                        "new_in_kernel": r.new_in_kernel,
                        "flips": r.flips,
                        "base_shortest": r.base_shortest,
                        "new_shortest": r.new_shortest,
                        "error": r.error,
                    }
                    for r in rows
                ],
            }
        )
    uniformity = []
    for n in analysis.uniformity:
        res = n.result
        uniformity.append(
            {
                "kind": n.kind,
                "subject": n.subject,
                "coalition": list(n.coalition),
                "uniform": bool(res.uniform),
                "jointly_uniform": bool(res.jointly_uniform),
                "conflicts": len(res.conflicts),
                "example": list(res.conflicts[0]) if res.conflicts else None,
            }
        )
    return {
        "relaxations": relax,
        "max_relax": analysis.max_relax,
        "pivotal": pivotal,
        "sensitivity": sensitivity,
        "uniformity": uniformity,
        "speculative_in_witnesses": list(analysis.speculative),
    }


def _move_table(g: Graph, include: Collection[int] | None) -> tuple[dict[str, Any], int]:
    table: list[list[list[int]]] = []
    table_index: dict[tuple, int] = {}
    avail: list[int] = []
    offset: list[int] = []
    succ: list[int] = []
    for s in range(g.size()):
        if g.terminal[s] or (include is not None and s not in include):
            avail.append(-1)
            offset.append(-1)
            continue
        key = tuple(tuple(a) for a in g.avail[s])
        k = table_index.get(key)
        if k is None:
            k = table_index[key] = len(table)
            table.append([list(a) for a in key])
        avail.append(k)
        offset.append(len(succ))
        succ.extend(g.succ[s])
    data = {
        "complete": include is None,
        "avail_table": table,
        "avail": avail,
        "offset": offset,
        "succ": succ,
    }
    return data, len(succ)


def bundle(
    model: Model,
    *,
    coalitions: Iterable[Iterable[str]] | None = None,
    endings: Iterable[str] | None = None,
    profile: str | Iterable[str] | None = None,
    initial: Sequence[Sequence[int]] | None = None,
    snapshot: str | Path | dict | None = None,
    max_states: int = DEFAULT_MAX_STATES,
    max_moves: int = DEFAULT_MAX_MOVES,
    max_relax: int = 2,
) -> dict[str, Any]:
    """The JSON-serializable data bundle of the visualizer for ``model`` (see the module
    docstring for the schema).

    ``coalitions`` default to each declared actor alone and all of them together;
    ``endings`` (the endings the page offers, first one selected) default to every declared
    ending and ``HORIZON``. ``initial`` (explicit initial states) or ``snapshot`` (a snapshot
    file path or parsed dict, see :mod:`wavefront.evidence`) replace the model's initial
    states. ``max_moves`` is the size policy: when the reachable graph has more joint moves
    the move table covers only the shown traces' states, their successors and those
    successors' successors. ``max_relax`` bounds the relaxation search of the tables.
    """
    if profile is not None and not isinstance(profile, str):
        profile = tuple(profile)
    cm = compile_model(model, profile=profile)
    explicit, snap, source = _initial_states(cm, initial, snapshot)
    g = explore(cm, initial=explicit, max_states=max_states)
    if not g.initial:
        raise ModelError(f"model {model.name!r} has no initial state")
    groups = _normalize_coalitions(g, coalitions)
    declared_endings = list(model.endings)
    all_endings = [*declared_endings, *(["HORIZON"] if model.timed else [])]
    if endings is None:
        shown = all_endings
    else:
        shown = []
        for e in [endings] if isinstance(endings, str) else endings:
            if e not in all_endings:
                known = ", ".join(all_endings) or "none"
                raise ModelError(f"no ending named {e!r} (endings: {known})")
            if e not in shown:
                shown.append(e)
    n = g.size()

    # -- hypotheses -----------------------------------------------------------------------
    starts = list(g.initial)
    swept = [i for i in range(len(cm.variables)) if len({g.states[s][i] for s in starts}) > 1]
    depths = [_bfs_depth(g, s) for s in starts]

    # -- properties and statuses --------------------------------------------------------------
    properties: list[dict] = []
    phis: list[set[int]] = []
    everything = set(range(n))
    for e in shown:
        if e == "HORIZON":
            continue
        properties.append(
            {
                "id": f"avoid:{e}",
                "kind": "avoid",
                "name": e,
                "label": f"not {e}",
                "text": f"not ending({json.dumps(e)})",
            }
        )
        phis.append(everything - g.ending_states(e))
    for inv, expr in model.invariants.items():
        properties.append(
            {
                "id": f"invariant:{inv}",
                "kind": "invariant",
                "name": inv,
                "label": inv,
                "text": expr_text(expr, cm),
            }
        )
        phis.append(g.states_where(inv))
    codes = [[status_codes(g, c, phi) for c in groups] for phi in phis]
    kernels = [[{s for s in range(n) if cs[s] == KEPT} for cs in per_c] for per_c in codes]

    # -- backward ranks --------------------------------------------------------------------------
    ranks: list[list[list[int]]] = []
    everyone = list(cm.actor_names)
    for e in shown:
        target = g.ending_states(e)
        per = []
        for c in [*groups, tuple(everyone)]:
            rank = attractor(g, c, target).rank
            per.append([rank.get(s, -1) for s in range(n)])
        ranks.append(per)

    # -- traces and replays ----------------------------------------------------------------------
    traces = []
    shown_states: set[int] = set()
    speculative: dict[str, None] = {}

    def note_speculative(moves: Iterable[Sequence[int]]) -> None:
        for move in moves:
            for actor, j in zip(cm.actors, move, strict=True):
                if actor.actions[j].speculative:
                    speculative[f"{actor.name}.{actor.actions[j].name}"] = None

    for h, start in enumerate(starts):
        for e in shown:
            trace = witness(g, start, g.ending_states(e))
            entry: dict[str, Any] = {"hypothesis": h, "ending": e}
            if trace is None:
                entry.update(states=None, moves=None, phases=None, classes=None, replays=[])
                traces.append(entry)
                continue
            ids = trace.state_ids
            moves = [list(m) for m in trace.joint_moves]
            shown_states.update(ids)
            note_speculative(moves)
            entry["states"] = ids
            entry["moves"] = moves
            entry["phases"] = [[_phases(cs, ids) for cs in per_c] for per_c in codes]
            entry["classes"] = [
                [[decision_classes(g, cs, s) for s in ids[:-1]] for cs in per_c] for per_c in codes
            ]
            replays = []
            for h2, other in enumerate(starts):
                if h2 == h:
                    continue
                r = replay(cm, g, other, moves)
                r["hypothesis"] = h2
                shown_states.update(r["states"])
                note_speculative(r["moves"])
                replays.append(r)
            entry["replays"] = replays
            traces.append(entry)

    # -- moves (size policy) ---------------------------------------------------------------------
    total_moves = sum(len(m) for m in g.moves)
    if total_moves <= max_moves:
        moves_data, included = _move_table(g, None)
    else:
        hood = set(shown_states)
        frontier = set(shown_states)
        for _ in range(2):
            frontier = {t for s in frontier for t in g.succ[s]} - hood
            hood |= frontier
        moves_data, included = _move_table(g, hood)

    # -- per hypothesis: card and tables ---------------------------------------------------------
    players = [a.name for a in cm.actors if not a.is_nature]
    items = []
    for h, start in enumerate(starts):
        state = g.states[start]
        values = {cm.variables[i].name: cm.level_name(i, state[i]) for i in swept}
        label = ", ".join(f"{k} = {v}" for k, v in values.items()) or (
            "snapshot" if source == "snapshot" else "initial state"
        )
        identical = [
            a
            for a in players
            if len(starts) > 1
            and all(cm.observe(a, g.states[o]) == cm.observe(a, state) for o in starts)
        ]
        card_status, card_short, card_margin = [], [], []
        for p, per_c in enumerate(codes):
            st, sh, mg = [], [], []
            for c, cs in enumerate(per_c):
                d = distance_table(g, [start], kernels[p][c], groups[c], None)[start]
                st.append(cs[start])
                sh.append(_num(d.shortest))
                mg.append(_num(d.margin))
            card_status.append(st)
            card_short.append(sh)
            card_margin.append(mg)
        card = {
            "status": card_status,
            "shortest": card_short,
            "margin": card_margin,
            "endings": {
                e: (ranks[k][-1][start] if ranks[k][-1][start] >= 0 else None)
                for k, e in enumerate(shown)
            },
        }
        if source == "model" and len(starts) == 1:
            run_initial = None
        else:
            run_initial = [state]
        analysis = run_all(
            model,
            coalitions=groups,
            profile=profile,
            initial=run_initial,
            max_relax=max_relax,
            max_states=max_states,
        )
        items.append(
            {
                "label": label,
                "values": values,
                "state": start,
                "reachable": sum(1 for d in depths[h] if d >= 0),
                "identical_to": identical,
                "card": card,
                "tables": _tables(analysis, cm),
            }
        )

    # -- defaults: the first offered ending, from the first hypothesis that reaches it -----------
    default_h = 0
    if shown:
        for t in traces:
            if t["ending"] == shown[0] and t["states"] is not None:
                default_h = t["hypothesis"]
                break

    ending_index = {e: k for k, e in enumerate(all_endings)}
    profile_text = (
        None if not profile else (profile if isinstance(profile, str) else ", ".join(profile))
    )
    result = {
        "schema": 1,
        "meta": {
            "name": model.name,
            "description": model.description or "",
            "fingerprint": fingerprint(model),
            "horizon": model.horizon,
            "timed": bool(model.timed),
            "profile": profile_text,
            "caveat": CAVEAT,
            "budget": cm.budget(),
            "initial_source": source,
            "max_relax": max_relax,
            "default": {"hypothesis": default_h, "coalition": 0, "ending": 0},
            "counts": {
                "states": n,
                "moves": total_moves,
                "moves_included": included,
                "max_moves": max_moves,
            },
        },
        "variables": _variables(cm, set(swept)),
        "actors": _actors(cm),
        "hypotheses": {
            "variables": [cm.variables[i].name for i in swept],
            "values": {
                cm.variables[i].name: [
                    lvl
                    for k, lvl in enumerate(cm.variables[i].levels)
                    if any(g.states[s][i] == k for s in starts)
                ]
                for i in swept
            },
            "items": items,
        },
        "coalitions": [{"name": _coalition_name(c), "members": list(c)} for c in groups],
        "endings": shown,
        "all_endings": all_endings,
        "properties": properties,
        "states": {
            "count": n,
            "tick": [
                (s[cm.index["tick"]] if cm.timed else g.depth[k]) for k, s in enumerate(g.states)
            ],
            "terminal": [1 if t else 0 for t in g.terminal],
            "ending": [ending_index.get(e, -1) if e is not None else -1 for e in g.ending],
            "values": [[s[i] for s in g.states] for i in range(len(cm.variables))],
            "status": [["".join(map(str, cs)) for cs in per_c] for per_c in codes],
            "depth": depths,
            "rank": ranks,
        },
        "moves": moves_data,
        "traces": traces,
        "tables": {"speculative": list(speculative)},
        "snapshot": snap,
    }
    return result
