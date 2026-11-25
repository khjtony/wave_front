"""Stepping a model by hand and searching it for a shortest path, for the Explore page.

A state travels to the page and back as the list of level indices the compiled model uses, so
the server keeps nothing between requests. Everything here is exploration: a path found by
the search says that the path exists, never that it is likely or that nobody could prevent it.
"""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
import time

from console import catalog

SEARCH_SECONDS = 240


def _index(variable, value) -> int:
    levels = [str(x) for x in variable.levels]
    if str(value) not in levels:
        raise ValueError(f"{variable.name} has no level {value!r}")
    return levels.index(str(value))


def origin_levels(origin: str) -> dict:
    """The levels a named start state sets (``s0`` sets none: it is the model's own)."""
    if origin != "srt":
        return {}
    s = catalog.states()
    return {k: v for k, v in s["srt"]["levels"].items() if s["s0"]["levels"].get(k) != v}


def start_state(cm, origin: str, overrides: dict | None) -> tuple:
    (state,) = cm.initial_states()
    state = list(state)
    wanted = {**origin_levels(origin), **(overrides or {})}
    for name, value in wanted.items():
        if name in cm.index:  # a start state may name variables an older model lacks
            state[cm.index[name]] = _index(cm.variables[cm.index[name]], value)
    return tuple(state)


def view(cm, state) -> dict:
    """What the page needs to draw one state and offer the next round."""
    state = tuple(int(x) for x in state)
    if len(state) != len(cm.variables):
        raise ValueError("this state does not belong to this model variant")
    terminal = bool(cm.is_terminal(state))
    available = []
    for actor, choices in zip(cm.actors, cm.available(state), strict=True):
        acts = [
            {"i": j, "name": actor.actions[j].name}
            | {"plain": catalog.plain(f"{actor.name}.{actor.actions[j].name}")}
            for j in choices
        ]
        available.append({"actor": actor.name, "actions": [] if terminal else acts})
    return {
        "state": list(state),
        "levels": {k: str(v) for k, v in cm.state_dict(state).items()},
        "terminal": terminal,
        "ending": cm.ending_of(state),
        "conditions": {n: bool(f(state)) for n, f in cm.invariant_fns.items()},
        "available": available,
    }


def _cm(q: dict):
    goal = q.get("goal") or "self_preserving"
    if goal not in catalog.BY_ID[q["version"]].get("goals", catalog.GOALS):
        raise ValueError("unknown AI goal")
    return catalog.compiled(q["version"], q.get("knobs"), {"a_objective": goal})[1]


def begin(q: dict) -> dict:
    cm = _cm(q)
    return view(cm, start_state(cm, q.get("origin", "s0"), q.get("overrides")))


def step(q: dict) -> dict:
    cm = _cm(q)
    state = tuple(int(x) for x in q["state"])
    move = tuple(int(x) for x in q["move"])
    offered = cm.available(state)
    if cm.is_terminal(state) or len(move) != len(offered):
        raise ValueError("no round can be played from this state")
    if any(m not in ok for m, ok in zip(move, offered, strict=True)):
        raise ValueError("an action in this round is not available")
    out = view(cm, cm.step(state, move))
    out["played"] = [f"{a.name}.{a.actions[m].name}" for a, m in zip(cm.actors, move, strict=True)]
    return out


def shortest(q: dict) -> dict:
    """A shortest path to an ending or to the breaking of a safe condition, searched in a
    process of its own under a time limit; logged to research/explorations.jsonl."""
    cm = _cm(q)
    t0 = time.perf_counter()
    try:
        done = subprocess.run(
            [sys.executable, "-m", "console.sim"],
            input=json.dumps(q),
            capture_output=True,
            text=True,
            timeout=SEARCH_SECONDS,
            cwd=catalog.ROOT,
            check=False,
        )
        got = json.loads(done.stdout) if done.returncode == 0 else {"error": done.stderr[-600:]}
    except subprocess.TimeoutExpired:
        got = {"error": f"no answer within {SEARCH_SECONDS} seconds"}
    seconds = round(time.perf_counter() - t0, 1)
    out: dict = {"seconds": seconds, "found": bool(got.get("states")), "error": got.get("error")}
    if out["found"]:
        out["path"] = [view(cm, s) for s in got["states"]]
        out["rounds"] = [
            [f"{a.name}.{a.actions[m].name}" for a, m in zip(cm.actors, move, strict=True)]
            for move in got["moves"]
        ]
    row = {k: q.get(k) for k in ("version", "knobs", "goal", "origin", "overrides", "target")}
    row |= {"at": time.strftime("%Y-%m-%d %H:%M"), "seconds": seconds, "error": out["error"]}
    row["quarters"] = len(got["moves"]) if out["found"] else None
    with catalog.LOCK, (catalog.RESEARCH / "explorations.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out


def _search() -> None:
    """The child process of :func:`shortest`: reads the question, prints the path."""
    from wavefront.bmc.queries import reach
    from wavefront.model import V

    q = json.loads(sys.stdin.read())
    mod = importlib.import_module(catalog.BY_ID[q["version"]]["module"])
    wanted = {**origin_levels(q.get("origin", "s0")), **(q.get("overrides") or {})}
    start = {"a_objective": q.get("goal") or "self_preserving"}
    for name, value in wanted.items():
        if name not in mod.LEVELS:
            raise SystemExit(
                f"a search can start from a changed level of {sorted(mod.LEVELS)} only"
            )
        start[name] = value
    cm = catalog.compiled(q["version"], q.get("knobs"), start)[1]
    target = q["target"]
    if target.startswith("break:"):
        target = ~V.invariant(target[6:])
    elif target not in cm.ending_fns:
        raise SystemExit("unknown target")
    trace = reach(cm, 24, target)
    found = trace is not None
    print(
        json.dumps(
            {
                "states": [list(map(int, s)) for s in trace.states] if found else [],
                "moves": [list(map(int, m)) for m in trace.moves] if found else [],
            }
        )
    )


if __name__ == "__main__":
    _search()
