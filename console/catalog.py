"""What the console shows, read from the repository on request: the model versions and their
structure, the claims and their results, the runs, the start states and the small stores the
owner writes to from the page. Nothing here is a second copy of a result."""

from __future__ import annotations

import ast
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
    out, before = [], None
    for v in VERSIONS:
        d = describe(v["id"])
        acts = {f"{a['name']}.{x['name']}" for a in d["actors"] for x in a["actions"]}
        names = {x["name"] for x in d["variables"] if x["origin"] == "var"}
        row = {k: v[k] for k in ("id", "title", "date", "family", "summary", "doc", "reports")}
        row["budget"] = d["budget"]
        row["players"] = [a["name"] for a in d["actors"]]
        row["added_actions"] = sorted(acts - before[0]) if before else []
        row["removed_actions"] = sorted(before[0] - acts) if before else []
        row["added_variables"] = sorted(names - before[1]) if before else []
        # v0.2 and v0.3 both start from v0.1, so each is compared with v0.1.
        if v["id"] in ("v0", "v0.1"):
            before = (acts, names)
        row["compared_with"] = {"v0": None, "v0.1": "v0", "v0.2": "v0.1", "v0.3": "v0.1"}[v["id"]]
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
            procs[int(pid)] = {"pid": int(pid), "ppid": int(ppid), "seconds": int(seconds)}
            procs[int(pid)] |= {"gb": round(int(rss) / 1048576, 1), "goal": goal and goal.group(1)}
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
    for n, w in enumerate(workers, 1):
        w["name"] = f"queue {n}" + (f" ({w['goal']} goal)" if w["goal"] else " (all goals)")
        position = 0
        for goal in [w["goal"]] if w["goal"] else PLAN_GOALS:
            for item in PLAN:
                e = items[_question(item, goal)]
                tried = any(
                    t["epoch"] >= w["started"] - 60 and t.get("memory cap GB") == (w["limit"] or 0)
                    for t in over.get(_question(item, goal), [])
                )
                if e["status"] != "waiting" or tried or e.get("worker"):
                    continue
                e["worker"] = w["name"]
                e["limit"] = w["limit"]
                if position == 0 and w["child"]:
                    e |= {"status": "running", "seconds": w["child"]["seconds"]}
                    e["gb"] = w["child"]["gb"]
                    e["layer"] = _layer(w["child"]["pid"])
                else:
                    e |= {"position": position, "waiting_seconds": w["seconds"]}
                position += 1
    for e in items.values():
        if e["status"] == "waiting" and not e.get("worker"):
            e["status"] = "did not fit" if e["largest_limit_tried"] else "not queued"
    order = {"running": 0, "waiting": 1, "did not fit": 2, "not queued": 3, "done": 4}
    rows = sorted(items.values(), key=lambda e: (order[e["status"]], e.get("position", 0)))
    return {
        "workers": [{k: w[k] for k in ("name", "seconds", "limit")} for w in workers],
        "items": rows,
        "counts": {k: sum(1 for e in rows if e["status"] == k) for k in order},
    }


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


def runs() -> dict:
    return {"live": live(), "queue": queue(), "readings": readings(), "logs": logs()}


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
