"""What the console shows, read from the repository on request: the model versions and their
structure, the claims and their results, the runs, the start states and the small stores the
owner writes to from the page. Nothing here is a second copy of a result."""

from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import json
import re
import subprocess
import threading
import time
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from wavefront.model import expr as X
from wavefront.model.effects import Bump, Set, SetIf

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
GOALS = ("aligned", "self_preserving", "truth_seeking", "indifferent")
PROFILES = ("A_self_preserving", "A_indifferent", "A_truth_seeking")
LOCK = threading.Lock()
# Glossary entries that name a group of code names, not each of them.
GROUP_TERMS = ("History records", "Open-weight AI service providers")

VERSIONS: list[dict] = [
    {
        "id": "v0",
        "title": "AGI v0",
        "module": "models.agi.v0",
        "date": "2026-11-09",
        "family": "G",
        "summary": "Governments, frontier AI companies, one AI system with a hidden goal, and"
        " chance, quarter by quarter from 2026 Q4 to 2040 Q4.",
        "scenarios": "tests/agi/scenarios",
        "parts": ["reports/agi_v0_first_sight_parts.jsonl", "reports/agi_v0_collapse_parts.jsonl"],
        "doc": "docs/agi_testbed.md",
        "reports": [
            "reports/agi_2026-11-12.md",
            "reports/agi_v0_collapse_2026-11-13.md",
            "reports/agi_v0_effort_2026-11-13.md",
            "reports/agi_worked_example.md",
            "reports/agi_terms_and_claims_2026-11-15.html",
        ],
        "knobs": ["unknown_capability", "self_improve_delay", "h_lag"],
    },
    {
        "id": "v0.1",
        "title": "AGI v0.1",
        "module": "models.agi_v0_1.v0_1",
        "date": "2026-11-15",
        "family": "D",
        "summary": "v0 with the deployment delay: deploying AI agents raises society's reliance"
        " on AI three quarters later, and the countdown can be cancelled.",
        "scenarios": "tests/agi_v0_1/scenarios",
        "parts": [
            "reports/agi_v0_1_parts_first_sight.jsonl",
            "reports/agi_v0_1_parts_part_b.jsonl",
            "reports/agi_v0_1_parts_d4_rerun.jsonl",
            "reports/agi_v0_1_parts_d5_alone.jsonl",
        ],
        "doc": "docs/agi_v0_1.md",
        "reports": [
            "reports/agi_v0_1_part_a_2026-11-15.md",
            "reports/agi_v0_1_part_b_2026-11-15.html",
            "reports/agi_v0_1_takeover_diagram.html",
            "reports/agi_v0_1_path_sample_2026-11-17.html",
            "reports/agi_v0_1_exit_census_2026-11-17.html",
            "reports/agi_v0_1_endings_census_2026-11-17.html",
            "reports/agi_v0_1_effort_weighted_2026-11-17.html",
            "reports/agi_v0_1_effort_sensitivity_2026-11-17.html",
            "reports/agi_v0_1_endings_fixes_2026-11-18.html",
        ],
        "knobs": ["unknown_capability", "self_improve_delay", "h_lag"],
    },
    {
        "id": "v0.2",
        "title": "AGI v0.2",
        "module": "models.agi_v0_2.v0_2",
        "date": "2026-11-17",
        "family": "E",
        "summary": "v0.1 with an open-weight release and its four consequences: cannot be"
        " recalled, race pressure, outside testing, retraining.",
        "scenarios": "tests/agi_v0_2/scenarios",
        "parts": ["reports/agi_v0_2_parts.jsonl"],
        "doc": "docs/agi_v0_2.html",
        "reports": [
            "reports/agi_v0_2_part_a_2026-11-17.html",
            "reports/agi_v0_2_part_b_2026-11-18.html",
            "docs/agi_open_weights_review.html",
        ],
        "knobs": ["recall", "pressure", "testing", "retrain"],
    },
    {
        "id": "v0.3",
        "title": "AGI v0.3",
        "module": "models.agi_v0_3.v0_3",
        "date": "2026-11-18",
        "family": "F",
        "summary": "v0.1 with the open-weight AI system as a second AI that follows the frontier"
        " two quarters behind and that no pause or shutdown reaches.",
        "scenarios": "tests/agi_v0_3/scenarios",
        "parts": ["reports/agi_v0_3_parts.jsonl"],
        "doc": "docs/agi_v0_3.html",
        "reports": ["reports/agi_v0_3_part_a_2026-11-18.html"],
        "knobs": ["open_system", "pressure", "hosting", "open_adoption", "treaty_delay"],
    },
    {
        "id": "v0.4",
        "title": "AGI v0.4",
        "module": "models.agi_v0_4.v0_4",
        "date": "2026-11-23",
        "family": "X",
        "summary": "v0.3 with a fifth AI goal, expansionist, and a footprint for each AI system:"
        " its share of computing power, energy, manufacturing and land.",
        "scenarios": "tests/agi_v0_4/scenarios",
        "parts": ["reports/agi_v0_4_parts.jsonl"],
        "doc": "docs/agi_v0_4.html",
        "reports": [],
        "knobs": ["open_system", "pressure", "hosting", "open_adoption", "treaty_delay"]
        + ["expansion", "reclaim", "ceiling", "counter"],
        "goals": [*GOALS, "expansionist"],
    },
]
BY_ID = {v["id"]: v for v in VERSIONS}


# -- plain names from the glossary -------------------------------------------------------
@lru_cache(maxsize=1)
def _glossary(mtime: float) -> tuple[dict[str, str], list[dict]]:
    names: dict[str, str] = {}
    entries: list[dict] = []
    category = ""
    for line in (ROOT / "docs" / "agi_glossary.html").read_text(encoding="utf-8").splitlines():
        head = re.match(r'\s*\[("[^"]+"), ("[^"]*"), \[$', line)
        if head:
            category = json.loads(head.group(1))
            continue
        if not line.startswith('    ["'):
            continue
        try:
            term, ids, also, meaning, note = json.loads(line.strip().rstrip(","))
        except ValueError:
            continue
        entries.append(
            {"term": term, "code": ids, "also": also, "meaning": meaning, "note": note}
            | {"category": category}
        )
    # An entry with one code name owns it; an entry that lists several (a group such as the
    # history records) lends its name only where no entry of its own exists.
    for wide in (False, True):
        for e in entries:
            if (len(e["code"]) > 1) is wide and e["term"] not in GROUP_TERMS:
                for one in e["code"]:
                    names.setdefault(one.strip(), e["term"])
    for goal in GOALS:
        names[f"Nature.retrain_{goal}"] = f"Retrain to {goal.replace('_', '-')}"
    return names, entries


def glossary() -> tuple[dict[str, str], list[dict]]:
    return _glossary((ROOT / "docs" / "agi_glossary.html").stat().st_mtime)


def plain(code: str) -> str:
    return glossary()[0].get(code, "")


# -- expressions as text -----------------------------------------------------------------
def text(e: object) -> str:
    """An expression of the model in a readable line."""
    if isinstance(e, X.VarRef):
        return e.name
    if isinstance(e, X.Lit | X.Const):
        return str(e.value)
    if isinstance(e, X.Cmp):
        return f"{text(e.left)} {e.op} {text(e.right)}"
    if isinstance(e, X.InSet):
        return f"{text(e.var)} in {{{', '.join(map(str, e.values))}}}"
    if isinstance(e, X.Not):
        return f"not ({text(e.item)})"
    if isinstance(e, X.And | X.Or):
        # ``x or False`` and ``x and True`` are leftovers of how the models build conditions.
        neutral = isinstance(e, X.And)
        items = [i for i in e.items if not (isinstance(i, X.Const) and i.value is neutral)]
        if len(items) == 1:
            return text(items[0])
        word = " and " if neutral else " or "
        same = type(e)
        parts = [
            f"({text(i)})" if isinstance(i, X.And | X.Or) and type(i) is not same else text(i)
            for i in items
        ]
        return word.join(parts) if parts else str(neutral)
    if isinstance(e, X.Arith):
        return f"{text(e.left)} {e.op} {text(e.right)}"
    if isinstance(e, X.Ite):
        return f"({text(e.then)} if {text(e.cond)} else {text(e.orelse)})"
    if isinstance(e, X.Min | X.Max):
        return f"{type(e).__name__.lower()}({', '.join(map(text, e.args))})"
    if isinstance(e, X.InvariantRef | X.EndingRef):
        return e.name
    return str(e)


def effect(e: object) -> dict:
    if isinstance(e, Bump):
        return {"var": e.var, "text": f"{e.var} {'+' if e.amount >= 0 else '−'}{abs(e.amount)}"}
    if isinstance(e, SetIf):
        return {"var": e.var, "text": f"{e.var} := {text(e.value)}  when {text(e.cond)}"}
    if isinstance(e, Set):
        return {"var": e.var, "text": f"{e.var} := {text(e.value)}"}
    return {"var": getattr(e, "var", "?"), "text": str(e)}


# -- models ------------------------------------------------------------------------------
def knob_spec(version: str) -> list[dict]:
    mod = importlib.import_module(BY_ID[version]["module"])
    params = inspect.signature(mod.build).parameters
    out = []
    for name in BY_ID[version]["knobs"]:
        default = params[name].default
        kind = "bool" if isinstance(default, bool) else "int"
        out.append({"name": name, "kind": kind, "default": default})
    return out


def clean_knobs(version: str, knobs: dict | None) -> dict:
    out = {}
    for spec in knob_spec(version):
        value = (knobs or {}).get(spec["name"], spec["default"])
        out[spec["name"]] = bool(value) if spec["kind"] == "bool" else max(0, min(8, int(value)))
    return out


@lru_cache(maxsize=24)
def _compiled(version: str, knobs: str, start: str):
    mod = importlib.import_module(BY_ID[version]["module"])
    model = mod.build(start=json.loads(start), **json.loads(knobs))
    return model, model.compile(profile=getattr(mod, "OBJECTIVE_PROFILES", PROFILES))


def compiled(version: str, knobs: dict | None = None, start: dict | None = None):
    """``(model, compiled model)`` of a version, the AI true to its goal."""
    return _compiled(
        version,
        json.dumps(clean_knobs(version, knobs), sort_keys=True),
        json.dumps(start or {}, sort_keys=True),
    )


def describe(version: str, knobs: dict | None = None) -> dict:
    """The structure of one model variant, for the inspector."""
    model, cm = compiled(version, knobs)
    budget = dict(cm.budget())
    budget["state_space_digits"] = len(str(budget.pop("state_space_bound")))
    variables = [
        {
            "name": v.name,
            "plain": plain(v.name),
            "levels": list(v.levels),
            "init": list(v.init),
            "kind": v.kind,
            "origin": v.origin,
        }
        for v in cm.variables
    ]
    actors = []
    for a in cm.actors:
        acts = []
        for x in a.actions:
            code = f"{a.name}.{x.name}"
            reads = sorted(x.guard_expr.free_vars()) if hasattr(x.guard_expr, "free_vars") else []
            acts.append(
                {
                    "name": x.name,
                    "plain": plain(code),
                    "delay": x.delay,
                    "source": x.source or "",
                    "unsourced": bool(x.speculative),
                    "idle": bool(x.is_idle),
                    "parts": [[n, text(g)] for n, g in (x.guard_parts or ())],
                    "condition": text(x.guard_expr),
                    "effects": [effect(e) for e in x.effects],
                    "writes": sorted({e.var for e in x.effects}),
                    "reads": reads,
                }
            )
        actors.append({"name": a.name, "plain": plain(a.name), "actions": acts})
    return {
        "version": version,
        "knobs": clean_knobs(version, knobs),
        "knob_spec": knob_spec(version),
        "horizon": cm.horizon,
        "budget": budget,
        "variables": variables,
        "actors": actors,
        "endings": [
            {"name": n, "plain": plain(n), "text": text(e)} for n, e in model.endings.items()
        ],
        "conditions": [
            {"name": n, "plain": plain(n), "text": text(e)} for n, e in model.invariants.items()
        ],
        "deadlines": [
            {
                "name": f.name,
                "actor": f.actor,
                "within": f.within,
                "responses": list(f.responses),
                "trigger": text(f.trigger),
            }
            for f in cm.fairness_constraints
        ],
        "patterns": [
            {"name": p.name, "actor": p.actor, "forbid": list(p.forbid), "unless": text(p.unless)}
            for p in model.profiles
        ],
    }


@lru_cache(maxsize=1)
def stages() -> list[dict]:
    """Every version with its size and what it adds to the one before."""
    out: list[dict] = []
    seen: dict[str, tuple[set, set]] = {}
    # v0.2 and v0.3 both start from v0.1; v0.4 starts from v0.3.
    parents = {"v0": None, "v0.1": "v0", "v0.2": "v0.1", "v0.3": "v0.1", "v0.4": "v0.3"}
    for v in VERSIONS:
        d = describe(v["id"])
        acts = {f"{a['name']}.{x['name']}" for a in d["actors"] for x in a["actions"]}
        names = {x["name"] for x in d["variables"] if x["origin"] == "var"}
        seen[v["id"]] = (acts, names)
        before = seen.get(parents[v["id"]] or "")
        row = {k: v[k] for k in ("id", "title", "date", "family", "summary", "doc", "reports")}
        row["budget"] = d["budget"]
        row["players"] = [a["name"] for a in d["actors"]]
        row["goals"] = list(v.get("goals", GOALS))
        row["added_actions"] = sorted(acts - before[0]) if before else []
        row["removed_actions"] = sorted(before[0] - acts) if before else []
        row["added_variables"] = sorted(names - before[1]) if before else []
        row["compared_with"] = parents[v["id"]]
        out.append(row)
    return out


# -- claims ------------------------------------------------------------------------------
def _claim_of(path: Path) -> dict | None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CLAIM":
            try:
                return ast.literal_eval(node.value)
            except ValueError:
                return None
    return None


def _status(outcomes: list[str]) -> str:
    if not outcomes:
        return "not run"
    if any(o.startswith("not met") or o == "fail" for o in outcomes):
        return "did not hold"
    if any(o.startswith(("not computed", "skip")) for o in outcomes):
        return "incomplete"
    if any(o in ("met", "pass") for o in outcomes):
        return "held"
    return "reported"


def claims(version: str) -> list[dict]:
    v = BY_ID[version]
    parts: dict[str, dict[str, dict]] = {}
    for name in v["parts"]:
        path = ROOT / name
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            detail = row.get("detail")
            shown = detail if isinstance(detail, str) else json.dumps(detail, ensure_ascii=False)
            parts.setdefault(row["claim"], {})[row["part"]] = {
                "part": row["part"],
                "outcome": row["outcome"],
                "detail": shown[:1500],
            }
    out = []
    for path in sorted((ROOT / v["scenarios"]).glob("test_*.py")):
        claim = _claim_of(path)
        if not claim:
            continue
        rows = list(parts.get(claim["id"], {}).values())
        out.append(
            {
                "id": claim["id"],
                "from_state": claim.get("from_state", ""),
                "claim": claim.get("claim", ""),
                "predicted": claim.get("expected", ""),
                "file": str(path.relative_to(ROOT)),
                "parts": rows,
                "status": _status([r["outcome"] for r in rows]),
            }
        )
    out.sort(key=lambda c: [int(n) if n.isdigit() else n for n in re.findall(r"\d+|\D+", c["id"])])
    return out


# -- runs --------------------------------------------------------------------------------
def live() -> list[dict]:
    """The model computations running on this machine now."""
    got = subprocess.run(
        ["ps", "-eo", "pid,etimes,rss,args"], capture_output=True, text=True, check=False
    ).stdout.splitlines()[1:]
    out = []
    for line in got:
        pid, seconds, rss, args = line.split(None, 3)
        hit = re.match(
            r"\S*python\S*\s+(?:-m pytest .*?)?(scripts/agi_\S+\.py|tests/agi\S*)(.*)", args
        )
        if hit:
            out.append(
                {
                    "pid": int(pid),
                    "seconds": int(seconds),
                    "gb": round(int(rss) / 1048576, 1),
                    "what": hit.group(1),
                    "args": hit.group(2).strip()[:160],
                }
            )
    return out


def readings() -> list[dict]:
    """The saved guarantee-zone readings of v0.3, one per zone and AI goal."""
    path = ROOT / "reports" / "agi_v0_3_kernels.jsonl"
    latest: dict[str, dict] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            q = json.loads(row["question"])
            if q[0] != "membership" or len(q) < 6:
                continue
            spec, alliance, target, levels, goal = q[1], q[2], q[3], q[4], q[5]
            build = spec["build"]
            variant = (
                "everything on"
                if build.get("open_system") and all(build.get(k) for k in ("pressure", "hosting"))
                else "no open system"
                if not build.get("open_system") and build.get("treaty_delay")
                else "v0.1 again"
                if not build.get("open_system")
                else "other"
            )
            inside = row["reading"]["inside"].get(goal) if row["kind"] == "ok" else None
            latest[row["question"]] = {
                "variant": variant,
                "patterns": spec["profiles"],
                "alliance": alliance,
                "target": target,
                "levels": dict(levels),
                "goal": goal,
                "kind": row["kind"],
                "inside": inside,
                "seconds": row["reading"].get("seconds") if row["kind"] == "ok" else None,
                "note": "" if row["kind"] == "ok" else str(row["reading"])[:200],
                "at": row.get("at", ""),
            }
    return list(latest.values())


# The heavy claims' zones in the order scripts/agi_v0_3_kernel_queue.py computes them (a test
# keeps the two lists equal): (claim, variant, alliance, target, behavior patterns, levels).
_ON = {"open_system": True, "pressure": True, "hosting": True, "open_adoption": True}
BUILDS = {
    "default": {**_ON, "treaty_delay": 1},
    "closed": {**_ON, "open_system": False, "treaty_delay": 1},
}
_F7 = [
    (["H"], "balance_control", {}),
    (["H", "L"], "balance_control", {}),
    (["H", "L"], "not:SILENT_TAKEOVER", {}),
    (["H"], "balance_coexist", {"cap": "agi"}),
]
PLAN = [("F7", "closed", c, t, [], lv) for c, t, lv in _F7] + [
    ("F3", "default", ["H"], "not:OPEN_TAKEOVER", [], {}),
    ("F6", "default", ["H", "L"], "balance_control", [], {}),
    ("F4", "default", ["H"], "not:OPEN_TAKEOVER", ["no_treaty"], {}),
    ("F4", "default", ["H", "L"], "not:OPEN_TAKEOVER", ["no_treaty"], {}),
    ("F6", "default", ["H", "L"], "balance_control", ["no_nationalize"], {}),
    ("F7", "default", ["H"], "balance_control", [], {}),
    ("F7", "default", ["H", "L"], "not:SILENT_TAKEOVER", [], {}),
    ("F7", "default", ["H"], "balance_coexist", [], {"cap": "agi"}),
]
PLAN_GOALS = ("aligned", "truth_seeking", "indifferent", "self_preserving")
_STAMP = "%Y-%m-%d %H:%M:%S %z"


def _question(item: tuple, goal: str) -> str:
    _, variant, alliance, target, patterns, levels = item
    spec = {"build": BUILDS[variant], "profiles": sorted(patterns)}
    return json.dumps(
        ["membership", spec, alliance, target, sorted(levels.items()), goal], sort_keys=True
    )


def _workers(now: float) -> list[dict]:
    """The queue processes on this machine: each worker with the zone process it has forked."""
    got = subprocess.run(
        ["ps", "-eo", "pid,ppid,etimes,rss,args"], capture_output=True, text=True, check=False
    ).stdout.splitlines()[1:]
    procs = {}
    for line in got:
        pid, ppid, seconds, rss, args = line.split(None, 4)
        if re.match(r"\S*python\S*\s+scripts/agi_v0_3_kernel_queue\.py", args):
            goal = re.search(r"--goal (\w+)", args)
            first = re.search(r"--start (\d+)", args)
            procs[int(pid)] = {"pid": int(pid), "ppid": int(ppid), "seconds": int(seconds)}
            procs[int(pid)] |= {"gb": round(int(rss) / 1048576, 1), "goal": goal and goal.group(1)}
            procs[int(pid)] |= {"args": args, "start": int(first.group(1)) if first else 0}
    out = []
    for p in procs.values():
        if p["ppid"] in procs:
            continue
        child = next((c for c in procs.values() if c["ppid"] == p["pid"]), None)
        out.append({**p, "started": now - p["seconds"], "child": child, "limit": None})
    return sorted(out, key=lambda w: w["started"])


def _layer(pid: int) -> dict | None:
    """How far a zone computation has got: layers done of the simulation's quarters."""
    try:
        got = json.loads((ROOT / ".cache" / "agi_v0_3_progress" / f"{pid}.json").read_text())
        total = int(got["horizon"]) + 1
        return {"done": total - int(got["tick"]), "of": total, "nodes": got.get("nodes")}
    except (OSError, ValueError, KeyError, TypeError):
        return None


def queue() -> dict:
    """The heavy claims' queue: every zone and AI goal as done, running, waiting or not
    fitting, with who computes it and for how long. The running zone of a worker is inferred:
    it is the first in the worker's order that has no reading and that the worker has not
    already found too large."""
    now = time.time()
    path = ROOT / "reports" / "agi_v0_3_kernels.jsonl"
    done: dict[str, dict] = {}
    over: dict[str, list[dict]] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            try:
                row["epoch"] = datetime.strptime(row["at"], _STAMP).timestamp()
            except (KeyError, ValueError):
                row["epoch"] = 0.0
            if row["kind"] == "ok":
                done[row["question"]] = row
            else:
                over.setdefault(row["question"], []).append(row)
    workers = _workers(now)
    # A worker's memory limit: the line it printed when it started, else the limit of the
    # queue's own log header (the all-goals worker), else the limit it was last seen to hit.
    headers = "\n".join(
        f.read_text(encoding="utf-8", errors="replace")
        for f in sorted((ROOT / "reports").glob("agi_v0_3_kernel_queue*.log"))
    )
    stated = {
        int(a): int(b) for a, b in re.findall(r"=== worker pid=(\d+) goal=\w+ limit=(\d+)", headers)
    }
    runner = re.findall(r"=== queue \w+ limit (\d+) GB", headers)
    for w in workers:
        hits = [
            t
            for ts in over.values()
            for t in ts
            if t["epoch"] >= w["started"] - 60 and json.loads(t["question"])[5] == w["goal"]
        ]
        w["limit"] = (
            stated.get(w["pid"])
            or (int(runner[-1]) if runner and not w["goal"] else None)
            or (max(hits, key=lambda t: t["epoch"]).get("memory cap GB") if hits else None)
        )
    workers.sort(key=lambda w: (w["goal"] is None, w["started"]))
    items = {}
    for goal in PLAN_GOALS:
        for item in PLAN:
            q = _question(item, goal)
            entry = {"claim": item[0], "variant": item[1], "alliance": item[2], "target": item[3]}
            entry |= {"id": item_id(q), "question": q}
            entry |= {"patterns": item[4], "levels": item[5], "goal": goal, "status": "waiting"}
            tries = over.get(q, [])
            entry["largest_limit_tried"] = max(
                (t.get("memory cap GB", 0) for t in tries), default=0
            )
            if q in done:
                r = done[q]["reading"]
                entry |= {"status": "done", "inside": r["inside"][goal], "seconds": r["seconds"]}
                entry["at"] = done[q].get("at", "")
            items[q] = entry
    held = held_claims()
    for n, w in enumerate(workers, 1):
        w["name"] = f"worker {n}"
        mine = next((q for q, c in held.items() if c["pid"] == w["pid"]), None)
        if mine is not None or w["pid"] in {c["pid"] for c in held.values()}:
            w["pull"] = True
            if mine in items and items[mine]["status"] != "done" and w["child"]:
                e = items[mine]
                e |= {"status": "running", "seconds": w["child"]["seconds"], "worker": w["name"]}
                e |= {"gb": w["child"]["gb"], "limit": w["limit"]}
                e["layer"] = _layer(w["child"]["pid"])
            continue
        if w["limit"] is None or w["limit"] == 0:
            w["pull"] = "--pull" in w.get("args", "")
        if w.get("pull"):
            continue
        # A worker of the fixed-order kind: its zone is inferred from its order.
        w["name"] += f" (fixed order, {w['goal'] or 'all'} goal)"
        first = True
        for goal in [w["goal"]] if w["goal"] else PLAN_GOALS:
            for item in PLAN[w.get("start", 0) :]:
                e = items[_question(item, goal)]
                tried = any(
                    t["epoch"] >= w["started"] - 60 and t.get("memory cap GB") == (w["limit"] or 0)
                    for t in over.get(_question(item, goal), [])
                )
                if e["status"] != "waiting" or tried or not first:
                    continue
                first = False
                if w["child"]:
                    e |= {"status": "running", "seconds": w["child"]["seconds"]}
                    e |= {"gb": w["child"]["gb"], "worker": w["name"], "limit": w["limit"]}
                    e["layer"] = _layer(w["child"]["pid"])
    rank = {i: n for n, i in enumerate(priority())}
    since = min((w["started"] for w in workers), default=now)
    waiting = sorted(
        (e for e in items.values() if e["status"] == "waiting"), key=lambda e: rank[e["id"]]
    )
    for n, e in enumerate(waiting):
        last = max((t["epoch"] for t in over.get(e["question"], [])), default=0)
        e |= {"position": n, "waiting_seconds": int(now - max(since, last))}
    order = {"running": 0, "waiting": 1, "done": 2}
    rows = sorted(items.values(), key=lambda e: (order[e["status"]], e.get("position", 0)))
    for e in rows:
        e.pop("question", None)
    return {
        "workers": [{k: w.get(k) for k in ("name", "seconds", "limit", "pull")} for w in workers],
        "items": rows,
        "counts": {k: sum(1 for e in rows if e["status"] == k) for k in order},
    }


# -- the queue's order and the workers' claims ---------------------------------------------
ORDER_FILE = RESEARCH / "queue_order.json"
CLAIMS = ROOT / ".cache" / "agi_v0_3_claims"


def item_id(question: str) -> str:
    return hashlib.sha1(question.encode()).hexdigest()[:12]


def _all_questions() -> list[str]:
    return [_question(item, goal) for goal in PLAN_GOALS for item in PLAN]


def priority() -> list[str]:
    """Every zone's id in the order the workers take them: the owner's order first
    (research/queue_order.json, written from the console), then the plan's own."""
    plan = [item_id(q) for q in _all_questions()]
    try:
        chosen = [i for i in json.loads(ORDER_FILE.read_text(encoding="utf-8")) if i in plan]
    except (OSError, ValueError):
        chosen = []
    return chosen + [i for i in plan if i not in chosen]


def move(zone: str, to: str) -> list[str]:
    """Move a waiting zone to the top, up or down among the waiting ones."""
    with LOCK:
        waiting = [e["id"] for e in queue()["items"] if e["status"] == "waiting"]
        if zone not in waiting:
            raise ValueError("this zone is not waiting")
        at = waiting.index(zone)
        goal = {"top": 0, "up": max(0, at - 1), "down": min(len(waiting) - 1, at + 1)}[to]
        waiting.insert(goal, waiting.pop(at))
        ORDER_FILE.write_text(json.dumps(waiting) + "\n", encoding="utf-8")
        return waiting


def held_claims() -> dict[str, dict]:
    """The zones the pulling workers have taken, by question; a claim whose process is gone
    is dropped."""
    out = {}
    for path in CLAIMS.glob("*.json") if CLAIMS.exists() else ():
        try:
            c = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if Path(f"/proc/{c['pid']}").exists():
            out[c["question"]] = c
        else:
            path.unlink(missing_ok=True)
    return out


def pick(limit: int, pid: int, step: str) -> tuple[tuple, str, str] | None:
    """The first zone in the owner's order that has no reading, that no other worker holds
    and that has not already failed under these engine settings with as much memory; it is
    claimed for ``pid``. ``None`` when there is none."""
    path = ROOT / "reports" / "agi_v0_3_kernels.jsonl"
    done, failed = set(), set()
    for line in path.read_text(encoding="utf-8").splitlines() if path.exists() else ():
        row = json.loads(line)
        if row["kind"] == "ok":
            done.add(row["question"])
        elif row.get("memory cap GB", 0) >= limit and _engine(row) == step:
            failed.add(row["question"])
    by_id = {item_id(_question(item, goal)): (item, goal) for goal in PLAN_GOALS for item in PLAN}
    CLAIMS.mkdir(parents=True, exist_ok=True)
    taken = held_claims()
    for zone in priority():
        item, goal = by_id[zone]
        q = _question(item, goal)
        if q in done or q in failed or q in taken:
            continue
        try:
            with (CLAIMS / f"{zone}.json").open("x", encoding="utf-8") as fh:
                json.dump({"question": q, "pid": pid, "limit": limit, "at": time.time()}, fh)
        except FileExistsError:
            continue
        return item, goal, q
    return None


def _engine(row: dict) -> str:
    """The step a failed attempt was made with. Rows written before the harness recorded it:
    the split step was in use from 2026-11-21 06:30 (docs/agi_v0_3.html, changelog)."""
    return row.get("engine") or ("split" if row.get("at", "") >= "2026-11-21 06:30" else "compose")


def release(question: str) -> None:
    (CLAIMS / f"{item_id(question)}.json").unlink(missing_ok=True)


def logs() -> list[dict]:
    out = []
    for path in sorted((ROOT / "reports").glob("*.log"), key=lambda p: -p.stat().st_mtime):
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        out.append(
            {
                "name": path.name,
                "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(path.stat().st_mtime)),
                "lines": len(lines),
                "tail": [ln[:300] for ln in lines[-12:]],
            }
        )
    return out


def _same_moment(written: float, epoch: float) -> bool:
    """Is a clock time written on the host this moment? The console may run in another time
    zone than the host that wrote the log (the container is in UTC), so the two may differ
    by a whole number of quarter hours, up to a day."""
    off = abs(written - epoch)
    return off < 86400 and min(off % 900, 900 - off % 900) < 120


def _last_parts(version: str, claim: str) -> list[dict]:
    """The parts of ``claim`` at the end of the version's parts log, back to the first
    repeated part (an earlier run)."""
    path = ROOT / "reports" / f"{version}_parts.jsonl"
    out: list[dict] = []
    if not path.exists():
        return out
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    for row in reversed([r for r in rows if r.get("claim") == claim]):
        if any(o["part"] == row["part"] for o in out):
            break
        d = row.get("detail")
        took = sum(d["seconds"].values()) if isinstance(d, dict) and "seconds" in d else None
        note = d[:160] if isinstance(d, str) else ""
        out.append({"part": row["part"], "outcome": row["outcome"], "seconds": took, "note": note})
    return out[::-1]


def claim_runs(version: str = "agi_v0_4") -> dict:
    """The heavy claims of a version that run as claim files, not through the v0.3 queue: each
    running claim with the zone process it has forked (time, memory, engine, layer), the
    zones it has finished since it started, and the planned runs that have not started
    (research/claim_runs_plan.json; a run has started once reports/<version>_chain.log names
    it)."""
    now = time.time()
    got = subprocess.run(
        ["ps", "-eo", "pid,ppid,etimes,rss,nlwp,args"], capture_output=True, text=True, check=False
    ).stdout.splitlines()[1:]
    procs = {}
    for line in got:
        pid, ppid, seconds, rss, threads, args = line.split(None, 5)
        hit = re.search(rf"-m pytest .*tests/{version}/scenarios/test_(\w+)\.py", args)
        if hit:
            procs[int(pid)] = {"pid": int(pid), "ppid": int(ppid), "seconds": int(seconds)}
            procs[int(pid)] |= {"gb": round(int(rss) / 1048576, 1), "claim": hit.group(1)}
            procs[int(pid)] |= {"threads": int(threads)}
    log = ROOT / "reports" / f"{version}_chain.log"
    text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    started = re.findall(r"=== (\S+ \S+) \S+ (\w+) cap (\d+) GB", text)
    saved = []
    path = ROOT / "reports" / f"{version}_kernels.jsonl"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            q = json.loads(row["question"])
            try:
                epoch = datetime.strptime(row["at"], _STAMP).timestamp()
            except (KeyError, ValueError):
                epoch = 0.0
            ok = row["kind"] == "ok"
            saved.append(
                {
                    "epoch": epoch,
                    "alliance": q[2],
                    "target": q[3],
                    "levels": dict(q[4]),
                    "goal": q[5],
                    "kind": row["kind"],
                    "inside": row["reading"]["inside"].get(q[5]) if ok else None,
                    "seconds": row["reading"].get("seconds") if ok else None,
                    "note": "" if ok else str(row["reading"])[:160],
                    "limit": row.get("memory cap GB"),
                    "core": row.get("core"),
                }
            )
    running = []
    for p in sorted(procs.values(), key=lambda p: -p["seconds"]):
        if p["ppid"] in procs:
            continue
        child = next((c for c in procs.values() if c["ppid"] == p["pid"]), None)
        begun = now - p["seconds"]
        # The run's memory limit is the chain log's, when the log's line is this start; the
        # readings saved since then under that limit are this run's. A run started by hand
        # has no such line: its finished parts are then the claim's last in the parts log.
        limit = next(
            (
                int(g)
                for at, c, g in reversed(started)
                if c == p["claim"]
                and _same_moment(datetime.strptime(at, "%Y-%m-%d %H:%M:%S").timestamp(), begun)
            ),
            None,
        )
        entry = {"claim": p["claim"], "seconds": p["seconds"], "limit": limit, "zone": None}
        if limit is not None:
            mine = [r for r in saved if r["epoch"] >= begun - 5 and r["limit"] == limit]
            entry["finished"] = [{k: v for k, v in r.items() if k != "epoch"} for r in mine]
        else:
            entry["finished"] = _last_parts(version, p["claim"])
        if child:
            layer = None
            try:
                at = ROOT / ".cache" / f"{version}_progress" / f"{child['pid']}.json"
                st = json.loads(at.read_text())
                if st["at"] >= now - child["seconds"] - 5:
                    total = int(st["horizon"]) + 1
                    layer = {"done": total - int(st["tick"]), "of": total}
            except (OSError, ValueError, KeyError, TypeError):
                pass
            workers = child["threads"] - 1
            entry["zone"] = {"seconds": child["seconds"], "gb": child["gb"], "layer": layer}
            entry["zone"]["engine"] = (
                f"multi-core engine, {workers} threads" if workers > 1 else "single-core engine"
            )
        running.append(entry)
    try:
        plan = json.loads((RESEARCH / "claim_runs_plan.json").read_text(encoding="utf-8"))
        plan = [s for s in plan if s.get("version") == version]
    except (OSError, ValueError):
        plan = []
    return {"running": running, "waiting": plan[len(started) :], "version": version}


def runs() -> dict:
    return {
        "live": live(),
        "queue": queue(),
        "claim_runs": claim_runs(),
        "readings": readings(),
        "logs": logs(),
    }


# -- states and stores -------------------------------------------------------------------
def states() -> dict:
    s0 = json.loads((RESEARCH / "states" / "s0.json").read_text(encoding="utf-8"))
    srt = json.loads((RESEARCH / "states" / "srt.json").read_text(encoding="utf-8"))
    snapshot = json.loads((ROOT / s0["snapshot"]).read_text(encoding="utf-8"))
    return {"s0": s0, "srt": srt, "indicators": snapshot["variables"], "rates": snapshot["rates"]}


def store(name: str) -> list[dict]:
    path = RESEARCH / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def store_write(name: str, change: dict) -> list[dict]:
    """Add an item (no ``id``) or update one (``id`` and the fields to change)."""
    allowed = {
        "requests": ("text", "kind", "version", "status", "answer"),
        "news": ("title", "url", "source", "date", "variable", "effect", "note", "status"),
    }
    with LOCK:
        items = store(name)
        fields = {k: str(v)[:4000] for k, v in change.items() if k in allowed[name]}
        if change.get("id"):
            for item in items:
                if item["id"] == change["id"]:
                    item.update(fields)
        else:
            stamp = time.strftime("%Y-%m-%d %H:%M")
            new = max((i["id"] for i in items), default=0) + 1
            items.append({"id": new, "created": stamp, "status": "new", **fields})
        (RESEARCH / f"{name}.json").write_text(
            json.dumps(items, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return items


def overview() -> dict:
    counts = {}
    for v in VERSIONS:
        tally: dict[str, int] = {}
        for c in claims(v["id"]):
            tally[c["status"]] = tally.get(c["status"], 0) + 1
        counts[v["id"]] = tally
    s = states()
    moved = [k for k, lv in s["srt"]["levels"].items() if s["s0"]["levels"].get(k) != lv]
    return {
        "stages": stages(),
        "claims": counts,
        "live": live(),
        "requests_open": sum(1 for r in store("requests") if r["status"] != "done"),
        "news_new": sum(1 for n in store("news") if n["status"] == "new"),
        "findings": len(store("findings")),
        "srt_date": s["srt"]["date"],
        "srt_reviewed": s["srt"].get("reviewed", s["srt"]["date"]),
        "srt_moved": moved,
    }
