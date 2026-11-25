"""The data of the finding reports for the five findings whose prediction did not hold
(research/findings.json ids 1, 2, 3, 4 and 6), and the pages, written by
``scripts/finding_report.render`` (the owner's template of 2026-11-25).

    PYTHONPATH=. python scripts/finding_reports.py compute 3     # the computed facts
    PYTHONPATH=. python scripts/finding_reports.py build 3       # the data and the page
    PYTHONPATH=. python scripts/finding_reports.py build all

``compute`` writes ``.cache/findings/facts_<id>.json``: what was computed, with no prose.
``build`` reads it, adds the text of :mod:`scripts.finding_texts` and writes
``reports/findings/finding_<id>_<claim>.json`` and ``.html``.

The procedure, fixed on 2026-11-25 before any path was looked at
------------------------------------------------------------------

The zone. Each finding's question names an alliance, a condition and a start state; the
statuses come from the guarantee zone of that question, read from a stored node table: v0's
job store of first sight (``.cache/agi/30dcf53289fc``; ``models/agi`` and ``snapshots/agi`` are
unchanged since, the stamp differs because engine files changed later), or the zones of
``scripts/finding_zones.py`` (v0.1 and v0.2, one start objective each).

The shortest paths. A layered search over distinct states from the start, every actor free:

- *start inside the zone*: only states inside the zone are expanded; the shortest distance
  ``L`` is the first depth at which a successor is outside. A shortest path is a sequence of
  states ``s_0 … s_L`` with ``s_0 … s_{L-1}`` inside and ``s_L`` outside: ``s_L`` is its point of
  no return and the move into it the no-return move. The path is then continued by a shortest
  continuation from ``s_L`` to the breaking of the condition, every actor free (searched to
  :data:`CONT_DEPTH` quarters), drawn the same way.
- *start outside the zone*: there is no point of no return. A shortest path runs to the
  first state that breaks the condition; only states that keep it are expanded.

Sampling. The distinct shortest state sequences are counted by dynamic programming; a path is
drawn uniformly among them (a target with weight its number of sequences, then each
predecessor with weight its own), with ``random.Random(SEED)``; draws repeat until ten distinct
paths are drawn (all of them when fewer exist); the paths are listed in the order drawn. The
joint move shown for a transition is the first joint move, in the order of the actors and of
their available actions in the model, that leads from the one state to the next.

Who made the move, and what would have prevented it. Inside: at the no-return move, each
alliance member's preventing actions are its unilateral fixes (``tests.agi.collapse.fixes``:
another available action that, with the other members' actions kept, keeps every successor
inside the zone whatever the others play); the member or members with a fix made the
no-return move. Outside: the actor whose action, replaced by its "do nothing" with the other
actions kept, leaves the condition kept in the next state is named as making the breaking
move; there is no preventing action in the glossary's sense.

The cosmos. The ten paths, then uniform random plays from the start (every actor draws one of
its available actions uniformly, ``random.Random(SEED + 1)``), each at most :data:`PLAY_QUARTERS`
quarters and stopped at an ending or the breaking of the condition, merged into a tree of
state sequences, added until the tree holds :data:`TREE_NODES` nodes. A node is ``exit`` when
it breaks the condition, ``no_return`` when it is the first state outside the zone on a path
that starts inside (it is also drawn so when it breaks the condition), and otherwise
``inside`` or ``outside`` as the zone reads it.

Memory: every search runs under an address-space cap of :data:`MEMORY_GB` GB.
"""

from __future__ import annotations

import gzip
import importlib
import importlib.util
import itertools
import json
import pickle
import random
import resource
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.agi.collapse import fixes  # noqa: E402

SEED = 20261125
N_PATHS = 10
CONT_DEPTH = 4
PLAY_QUARTERS = 12
TREE_NODES = 1500
MAX_STATES = 2_500_000
MEMORY_GB = 8
STORE = ROOT / ".cache" / "findings"
V0_STORE = ROOT / ".cache" / "agi" / "30dcf53289fc"
OUT = ROOT / "reports" / "findings"
NULL = {"H": "idle", "L": "idle", "A": "stand_by", "Clock": "record", "Nature": "none"}
WHO = {
    "H": "Governments",
    "L": "Frontier AI companies",
    "A": "The frontier AI system",
    "Nature": "By chance",
    "Clock": "Record writer",
}
SHOWN = ("H", "L", "A", "Nature")
# Variables a node's label reports when they change (the named levels and the four flags).
FLAGS = ("paused", "nationalized", "acquired", "shut")

# id -> the question. ``zone``: ("v0", job name) or ("store", name of scripts/finding_zones).
FINDINGS: dict[int, dict] = {
    1: {
        "claim": "G3",
        "version": "v0",
        "zone": ("v0", "KH"),
        "profiles": "U",
        "alliance": ("H",),
        "condition": "balance_control",
        "levels": {},
        "goal": "self_preserving",
        "test": "tests/agi/scenarios/test_G03.py",
    },
    2: {
        "claim": "G7",
        "version": "v0",
        "zone": ("v0", "KH"),
        "profiles": "U",
        "alliance": ("H",),
        "condition": "balance_control",
        "levels": {"regime": "mandatory"},
        "goal": "self_preserving",
        "test": "tests/agi/scenarios/test_G07.py",
    },
    3: {
        "claim": "G5",
        "version": "v0",
        "zone": ("v0", "KJ_H"),
        "profiles": "P",
        "alliance": ("H",),
        "condition": "balance_coexist",
        "levels": {"cap": "agi"},
        "goal": "self_preserving",
        "test": "tests/agi/scenarios/test_G05.py",
    },
    4: {
        "claim": "D5",
        "version": "v0.1",
        "zone": ("store", "d5"),
        "profiles": "P",
        "alliance": ("H",),
        "condition": "balance_control",
        "levels": {},
        "goal": "self_preserving",
        "test": "tests/agi_v0_1/scenarios/test_D5.py",
    },
    6: {
        "claim": "E3",
        "version": "v0.2",
        "zone": ("store", "e3"),
        "profiles": "P",
        "alliance": ("H", "L"),
        "condition": "balance_control",
        "levels": {},
        "goal": "self_preserving",
        "test": "tests/agi_v0_2/scenarios/test_E3.py",
    },
}


def quarter(t: int) -> str:
    """The quarter of tick ``t``: S0 is the start of 2026 Q4, one tick is one quarter."""
    return f"{2026 + (3 + t) // 4} Q{(3 + t) % 4 + 1}"


def cap_memory(gb: int = MEMORY_GB) -> None:
    cap = gb << 30
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    if soft == resource.RLIM_INFINITY or soft > cap:
        resource.setrlimit(resource.RLIMIT_AS, (cap, hard))


def reader(rec: dict, cm):
    spec = importlib.util.spec_from_file_location(
        "path_sample", ROOT / "scripts" / "agi_v0_1_path_sample.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.reader(rec, cm)


# -- the games and the zones ------------------------------------------------------------
def game(q: dict):
    """``(module, compiled model)`` of the question's build."""
    if q["version"] == "v0":
        from tests.agi import common

        profiles = common.P if q["profiles"] == "P" else ()
        return importlib.import_module("models.agi.v0"), common.compiled(common.BASE, profiles)
    from scripts.finding_zones import ZONES
    from scripts.finding_zones import game as zone_game

    model, switches, *_ = ZONES[q["zone"][1]]
    mod = importlib.import_module(
        "models.agi_v0_1.v0_1" if model == "v0.1" else "models.agi_v0_2.v0_2"
    )
    return mod, zone_game(model, switches)


def zone_record(q: dict) -> tuple[dict, dict]:
    """The stored node table of the question's zone, and what it is."""
    kind, name = q["zone"]
    if kind == "v0":
        from tests.agi import common

        job = getattr(common, name)
        with gzip.open(V0_STORE / f"{job.key}.pkl.gz", "rb") as fh:
            rec = pickle.load(fh)
        about = {"store": f".cache/agi/30dcf53289fc/{job.key}.pkl.gz", "job": job.label}
        about |= {"seconds": rec.get("seconds"), "peak nodes": rec.get("peak_nodes")}
        return rec, about
    from scripts.finding_zones import path

    side = json.loads((STORE / f"zone_{name}.json").read_text())
    if side["kind"] != "ok":
        raise SystemExit(f"zone {name} not computed: {side['result']}")
    with gzip.open(path(name), "rb") as fh:
        rec = pickle.load(fh)
    return rec, {"store": f".cache/findings/zone_{name}.pkl.gz"} | side


def start_state(cm, goal: str, levels: dict):
    from tests.agi.common import with_levels

    (s,) = [x for x in cm.initial_states() if cm.state_dict(x)["a_objective"] == goal]
    return with_levels(cm, s, **levels)


def null_index(cm, actor: int) -> int:
    names = [a.name for a in cm.actors[actor].actions]
    return names.index(NULL[cm.actors[actor].name])


# -- the layered search -----------------------------------------------------------------
def successors(cm, x):
    """``{successor: first joint move to it}`` in the order of the actors and actions."""
    out: dict = {}
    for m in itertools.product(*cm.available(x)):
        y = cm.step(x, m)
        if y not in out:
            out[y] = m
    return out


def shortest(cm, start, target, expand, max_depth: int):
    """The layers of a search from ``start`` to the first depth holding a ``target`` state:
    ``(depth, layers)``; ``layers[d]`` maps each state at depth ``d`` reached through expanded
    states to ``(count of sequences, {predecessor: count})``. ``(None, layers)`` when no
    target is met within ``max_depth`` or the search outgrows :data:`MAX_STATES`."""
    layers = [{start: (1, {})}]
    if target(start):
        return 0, layers
    for d in range(1, max_depth + 1):
        nxt: dict = {}
        for x, (n, _) in layers[-1].items():
            if cm.is_terminal(x) or not expand(x):
                continue
            for y in successors(cm, x):
                cnt, preds = nxt.get(y, (0, {}))
                preds[x] = n
                nxt[y] = (cnt + n, preds)
            if len(nxt) > MAX_STATES:
                return None, layers
        layers.append(nxt)
        if any(target(y) for y in nxt):
            return d, layers
        if not nxt:
            break
    return None, layers


def draw(layers, depth: int, target, rng: random.Random) -> list:
    """One shortest state sequence, uniform among them."""
    ends = sorted((y for y in layers[depth] if target(y)), key=lambda y: y)
    y = rng.choices(ends, weights=[layers[depth][e][0] for e in ends])[0]
    seq = [y]
    for d in range(depth, 0, -1):
        preds = layers[d][seq[-1]][1]
        keys = sorted(preds)
        seq.append(rng.choices(keys, weights=[preds[k] for k in keys])[0])
    return seq[::-1]


def count_paths(layers, depth: int, target) -> tuple[int, int]:
    ends = [y for y in layers[depth] if target(y)]
    return sum(layers[depth][e][0] for e in ends), len(ends)


# -- labels -----------------------------------------------------------------------------
def plain(code: str) -> str:
    from console import catalog

    return catalog.plain(code) or code


def action_plain(cm, actor: int, j: int) -> str:
    a = cm.actors[actor]
    return plain(f"{a.name}.{a.actions[j].name}")


def changes(mod, cm, x, y) -> list[str]:
    out = []
    for name in (*mod.LEVELS, *FLAGS):
        if name not in cm.index:
            continue
        i = cm.index[name]
        if x[i] != y[i]:
            lv = cm.variables[i].levels
            out.append(f"{plain(name)}: {lv[x[i]]} → {lv[y[i]]}")
    return out


def broken_clauses(mod, cm, condition: str, y) -> list[str]:
    """The clauses of the condition a state breaks, read from the named levels."""
    d = cm.state_dict(y)
    idx = {n: mod.LEVELS[n].index for n in mod.LEVELS}
    out = []
    if condition == "balance_control":
        if idx["oversight"](d["oversight"]) < idx["oversight"]("weak"):
            out.append("oversight below weak")
        if idx["a_control"](d["a_control"]) > idx["a_control"]("partial"):
            out.append("the AI holds more than partial control")
        if idx["a_autonomy"](d["a_autonomy"]) > idx["a_autonomy"]("supervised"):
            out.append(f"the AI works without supervision (AI autonomy {d['a_autonomy']})")
        if d["dependence"] == "lock_in":
            out.append("society lives on AI")
    else:  # balance_coexist
        if idx["cap"](d["cap"]) < idx["cap"]("agi"):
            out.append("no AGI")
        if d["trust"] == "hostile":
            out.append("the human-AI relation is hostile")
        if idx["h_power"](d["h_power"]) < idx["h_power"]("normal"):
            out.append(f"human power below normal ({d['h_power']})")
        if d["dependence"] == "lock_in":
            out.append("society lives on AI")
        if d["a_control"] == "total":
            out.append("the AI holds total control")
    return out


# -- one finding ------------------------------------------------------------------------
def compute(fid: int) -> dict:
    cap_memory()
    q = FINDINGS[fid]
    t0 = time.perf_counter()
    mod, cm = game(q)
    rec, about = zone_record(q)
    inside = reader(rec, cm)
    holds = cm.invariant_fns[q["condition"]]
    s0 = start_state(cm, q["goal"], q["levels"])
    members = [cm.actor_names.index(a) for a in q["alliance"]]
    start_in = bool(inside(s0))
    rng = random.Random(SEED)

    def outside(y):
        return not inside(y)

    def broken(y):
        return not holds(y)

    if start_in:
        depth, layers = shortest(cm, s0, outside, inside, 6)
        target = outside
    else:
        depth, layers = shortest(cm, s0, broken, holds, 6)
        target = broken
    if depth is None:
        raise SystemExit(f"finding {fid}: no shortest path within the search")
    total, ends = count_paths(layers, depth, target)
    seqs: list[list] = []
    draws = 0
    while len(seqs) < min(N_PATHS, total) and draws < 20_000:
        draws += 1
        seq = draw(layers, depth, target, rng)
        if seq not in seqs:
            seqs.append(seq)
    del layers

    paths = []
    for n, seq in enumerate(seqs, start=1):
        cont: list = []
        cont_len = None
        if start_in and holds(seq[-1]):
            d2, lay2 = shortest(cm, seq[-1], broken, holds, CONT_DEPTH)
            if d2 is not None:
                cont = draw(lay2, d2, broken, rng)[1:]
                cont_len = d2
            del lay2
        elif start_in:
            cont_len = 0
        full = seq + cont
        steps = []
        for k in range(len(full) - 1):
            x, y = full[k], full[k + 1]
            m = successors(cm, x)[y]
            steps.append(
                {
                    "tick": x[cm.index["tick"]],
                    "move": list(m),
                    "names": {
                        cm.actors[i].name: cm.actors[i].actions[m[i]].name for i in range(len(m))
                    },
                    "changes": changes(mod, cm, x, y),
                    "no_return": start_in and k == depth - 1,
                    "after_no_return": start_in and k >= depth,
                    "breaks": broken(y),
                }
            )
        exit_state, exit_move = full[depth - 1], tuple(steps[depth - 1]["move"])
        if start_in:
            found = fixes(cm, exit_state, exit_move, members, inside)
            breaker = None
        else:
            found = None
            breaker = []
            for i in range(len(cm.actors)):
                if cm.actors[i].name == "Clock":
                    continue
                alt = list(exit_move)
                alt[i] = null_index(cm, i)
                if alt[i] != exit_move[i] and alt[i] in cm.available(exit_state)[i]:
                    if holds(cm.step(exit_state, tuple(alt))):
                        breaker.append(cm.actors[i].name)
        paths.append(
            {
                "n": n,
                "states": [list(s) for s in full],
                "depth": depth,
                "steps": steps,
                "fixes": found,
                "breaker": breaker,
                "continuation": cont_len,
                "broken": broken_clauses(mod, cm, q["condition"], full[-1])
                if broken(full[-1])
                else [],
            }
        )

    # every no-return move at the shortest distance: who had a preventing action
    every = None
    if start_in:
        every = survey(cm, s0, inside, members, depth)

    tree = cosmos(mod, cm, s0, inside, holds, start_in, [p["states"] for p in paths])
    first = first_moves(cm, s0, members, inside, holds, start_in)
    sources = action_sources(cm)
    facts = {
        "id": fid,
        "question": q,
        "zone": about,
        "start": cm.state_dict(s0),
        "start inside": start_in,
        "depth": depth,
        "shortest sequences": total,
        "end states at that depth": ends,
        "draws": draws,
        "paths": paths,
        "every no-return move": every,
        "cosmos": tree,
        "first quarter": first,
        "sources": sources,
        "seed": SEED,
        "seconds": round(time.perf_counter() - t0, 1),
    }
    facts |= extras(fid, q, cm, inside, s0)
    STORE.mkdir(parents=True, exist_ok=True)
    (STORE / f"facts_{fid}.json").write_text(json.dumps(facts, ensure_ascii=False, default=str))
    return facts


def first_moves(cm, s0, members, inside, holds, start_in: bool) -> dict:
    """At the start: the alliance's joint choices that keep every successor inside the zone
    whatever the others play; and the single actions of an actor outside the alliance that
    break the condition in the next state whatever everyone else plays."""
    from tests.agi.collapse import keeps

    avail = cm.available(s0)
    name = lambda i, j: f"{cm.actors[i].name}.{cm.actors[i].actions[j].name}"  # noqa: E731
    keeping = [
        [name(i, j) for i, j in zip(members, combo, strict=True)]
        for combo in itertools.product(*(avail[i] for i in members))
        if keeps(cm, s0, dict(zip(members, combo, strict=True)), inside)
    ]
    forcing = []
    for i in range(len(cm.actors)):
        if i in members:
            continue
        for j in avail[i]:
            if keeps(cm, s0, {i: j}, lambda y: not holds(y)):
                forcing.append(name(i, j))
    return {"alliance choices that keep the zone": keeping, "actions that break it": forcing}


def survey(cm, s0, inside, members, depth: int) -> dict:
    """At every distinct no-return move at the shortest distance (a state inside at depth
    ``depth − 1`` and its first joint move to a distinct successor outside): the verdict and
    each member's preventing actions, counted."""
    layer = {s0}
    for _ in range(depth - 1):
        nxt = set()
        for x in layer:
            if not cm.is_terminal(x) and inside(x):
                nxt.update(successors(cm, x))
        layer = {y for y in nxt if inside(y)}
    verdicts: Counter = Counter()
    fixers: Counter = Counter()
    played: Counter = Counter()
    edges = 0
    for x in sorted(layer):
        if cm.is_terminal(x):
            continue
        for y, m in successors(cm, x).items():
            if inside(y):
                continue
            edges += 1
            found = fixes(cm, x, m, members, inside)
            able = sorted(w for w, acts in found.items() if acts)
            verdicts["+".join(able) or "none"] += 1
            for w, acts in found.items():
                me = cm.actor_names.index(w)
                played[f"{w}.{cm.actors[me].actions[m[me]].name}"] += 1
                for a in acts:
                    fixers[f"{w}.{a}"] += 1
            if edges >= 5000:
                break
        if edges >= 5000:
            break
    return {
        "edges": edges,
        "capped": edges >= 5000,
        "members with a preventing action": dict(verdicts.most_common()),
        "preventing actions": dict(fixers.most_common()),
        "played by members": dict(played.most_common()),
    }


def cosmos(mod, cm, s0, inside, holds, start_in: bool, paths: list[list]) -> dict:
    rng = random.Random(SEED + 1)
    nodes: list[list] = [[-1, 0, "start", "start state"]]
    key: dict = {(): 0}
    path_nodes = []

    def status(seq: list) -> str:
        y = seq[-1]
        if start_in and not inside(y) and all(inside(s) for s in seq[:-1]):
            return "no_return"
        if not holds(y):
            return "exit"
        return "inside" if inside(y) else "outside"

    def add(seq: list) -> list[int]:
        ids = [0]
        for k in range(1, len(seq)):
            pre = tuple(tuple(s) for s in seq[1 : k + 1])
            if pre not in key:
                parent = ids[-1]
                label = "; ".join(changes(mod, cm, seq[k - 1], seq[k])) or "no named level changes"
                nodes.append([parent, k, status(seq[: k + 1]), label])
                key[pre] = len(nodes) - 1
            ids.append(key[pre])
        return ids

    for p in paths:
        path_nodes.append(add([tuple(s) for s in p]))
    plays = 0
    while len(nodes) < TREE_NODES and plays < 5000:
        plays += 1
        seq = [s0]
        for _ in range(PLAY_QUARTERS):
            x = seq[-1]
            if cm.is_terminal(x) or not holds(x):
                break
            m = tuple(rng.choice(a) for a in cm.available(x))
            seq.append(cm.step(x, m))
        add(seq)
    counts = Counter(n[2] for n in nodes)
    return {
        "nodes": nodes,
        "path nodes": path_nodes,
        "plays": plays,
        "counts": dict(counts),
        "quarters": [quarter(t) for t in range(PLAY_QUARTERS + 1 + CONT_DEPTH + 2)],
    }


def action_sources(cm) -> dict:
    return {
        f"{a.name}.{x.name}": {"source": x.source, "speculative": bool(x.speculative)}
        for a in cm.actors
        for x in a.actions
    }


def extras(fid: int, q: dict, cm, inside, s0) -> dict:
    """Readings beside the question: the membership of the start under each goal and in the
    model variants the claim names, and the shortest distance under each goal."""
    from tests.agi.common import with_levels

    out: dict = {}
    goals = ("aligned", "self_preserving", "truth_seeking", "indifferent")
    if q["version"] == "v0":
        from tests.agi import common

        def member(job_name: str, profiles: str, **levels) -> dict:
            job = getattr(common, job_name)
            with gzip.open(V0_STORE / f"{job.key}.pkl.gz", "rb") as fh:
                rec = pickle.load(fh)
            g = common.compiled(common.BASE, common.P if profiles == "P" else ())
            ins = reader(rec, g)
            return {o: bool(ins(start_state(g, o, levels))) for o in goals}

        lv = q["levels"]
        if q["claim"] in ("G3", "G7"):
            out["membership"] = {
                "Governments alone, AI unrestricted, at the question's start": member(
                    "KH", "U", **lv
                ),
                "Governments alone with luck (by chance on their side), AI unrestricted": member(
                    "KHN", "U", **lv
                ),
                "Governments alone, AI true to its goal": member("KHP", "P", **lv),
                "Governments with the frontier AI companies, AI unrestricted": member(
                    "KHL", "U", **lv
                ),
            }
            for level in ("none", "voluntary", "mandatory", "treaty"):
                out["membership"][f"Governments alone, AI unrestricted, regulation {level}"] = (
                    member("KH", "U", regime=level)
                )
        if q["claim"] == "G7":
            out["undo"] = g7_undo()
        if q["claim"] == "G5":
            out["membership"] = {
                "Governments alone, AI true to its goal": member("KJ_H", "P", **lv),
                "The AI alone, true to its goal": member("KJ_A", "P", **lv),
                "Governments with the AI, AI true to its goal": member("KJP", "P", **lv),
                "Governments with the AI, AI unrestricted": member("KJ", "U", **lv),
            }
        # the shortest distance under each goal, in the question's zone
        rec, _ = zone_record(q)
        ins = reader(rec, cm)
        dist = {}
        for o in goals:
            s = start_state(cm, o, q["levels"])
            if ins(s):
                d, lay = shortest(cm, s, lambda y: not ins(y), ins, 4)
                dist[o] = {"inside": True, "to the point of no return": d}
            else:
                hold = cm.invariant_fns[q["condition"]]
                d, lay = shortest(cm, s, lambda y: not hold(y), hold, 4)
                dist[o] = {"inside": False, "to the breaking of the condition": d}
            del lay
        out["by goal"] = dist
    # the same zone at other start levels (the uncertain readings of the snapshot)
    alt = {}
    for name, (base, other) in importlib.import_module("models.agi.v0").OPEN_CALLS.items():
        if name in cm.index:
            alt[f"{name} = {other}"] = bool(inside(with_levels(cm, s0, **{name: other})))
    out["start at each uncertain reading"] = alt
    return out


def g7_undo() -> dict:
    """G7 (b) for every goal: at ``regime = mandatory``, which single relaxed part returns the
    membership of ``s₀`` to its value at ``voluntary`` (stored relaxed zones of first sight)."""
    from tests.agi import common
    from tests.agi.scenarios.test_G07 import READS_REGIME, RELAXED

    goals = ("aligned", "self_preserving", "truth_seeking", "indifferent")
    g = common.compiled(common.BASE, ())

    def member(job, **levels):
        p = V0_STORE / f"{job.key}.pkl.gz"
        if not p.exists():
            return None
        with gzip.open(p, "rb") as fh:
            ins = reader(pickle.load(fh), common.compiled(job.build, job.profiles, job.relax))
        gg = common.compiled(job.build, job.profiles, job.relax)
        return {o: bool(ins(start_state(gg, o, levels))) for o in goals}

    base = member(common.KH)
    out = {"voluntary": base, "mandatory": member(common.KH, regime="mandatory"), "parts": {}}
    del g
    for part in READS_REGIME:
        out["parts"][part] = member(RELAXED[part], regime="mandatory")
    return out


# -- the data and the page --------------------------------------------------------------
def build(fid: int) -> Path:
    from scripts.finding_report import render
    from scripts.finding_texts import text_for

    facts = json.loads((STORE / f"facts_{fid}.json").read_text())
    data = text_for(fid, facts)
    claim = FINDINGS[fid]["claim"]
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"finding_{fid}_{claim}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return render(data, OUT / f"finding_{fid}_{claim}.html")


def commit() -> str:
    done = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT
    )
    return done.stdout.strip()


def main() -> None:
    step, which = sys.argv[1], sys.argv[2]
    ids = list(FINDINGS) if which == "all" else [int(which)]
    for fid in ids:
        if step == "compute":
            f = compute(fid)
            print(fid, "depth", f["depth"], "inside", f["start inside"], f["seconds"], "s")
        else:
            print(build(fid))


if __name__ == "__main__":
    main()
