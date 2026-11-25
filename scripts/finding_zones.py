"""The guarantee zones the finding reports read that no store holds (scripts/finding_reports.py).

Each zone is computed once in a forked child under an address-space cap (default 10 GB,
``WF_FINDING_MEMORY_GB``) on the single-core engine (``WAVEFRONT_BDD=c``), with the split
step and collections made more often (the same zone, docs/engine_split_step.md), and the
target cut to one start objective: nothing in these builds writes ``a_objective``, so the
zone of ``φ ∧ a_objective = o`` is the zone of ``φ`` among the states with objective ``o``.
The zone is stored as a node table (``tests.agi.common._dump``) under ``.cache/findings``,
with a sidecar ``.json`` of its cost; over the cap the sidecar records that and no zone.

    PYTHONPATH=. WAVEFRONT_BDD=c python scripts/finding_zones.py d5
    PYTHONPATH=. WAVEFRONT_BDD=c python scripts/finding_zones.py e3
"""

from __future__ import annotations

import gzip
import json
import multiprocessing
import os
import pickle
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / ".cache" / "findings"
MEMORY_GB = int(os.environ.get("WF_FINDING_MEMORY_GB", "10"))
GC_MIN_NODES = 40_000_000
GC_FACTOR = 1.25

# name -> (model, build switches, coalition, target, start objective). A under its profile.
ZONES = {
    "d5": ("v0.1", {}, ("H",), "balance_control", "self_preserving"),
    "e3": (
        "v0.2",
        {"recall": False, "pressure": True, "testing": False, "retrain": False},
        ("H", "L"),
        "balance_control",
        "self_preserving",
    ),
}


def game(model: str, switches: dict):
    if model == "v0.1":
        from models.agi_v0_1 import v0_1

        return v0_1.build(**switches).compile(profile=tuple(v0_1.OBJECTIVE_PROFILES))
    from models.agi_v0_2 import v0_2

    return v0_2.build(**switches).compile(profile=tuple(v0_2.OBJECTIVE_PROFILES))


def path(name: str) -> Path:
    return STORE / f"zone_{name}.pkl.gz"


def _work(name: str) -> dict:
    from tests.agi.common import _dump, heavy_encoding, target_bdd
    from wavefront.model import V
    from wavefront.symbolic import safe

    model, switches, coalition, target, objective = ZONES[name]
    cm = game(model, switches)
    t0 = time.perf_counter()
    enc = heavy_encoding(cm)
    enc.mgr.gc_min_nodes = GC_MIN_NODES
    enc.mgr.gc_factor = GC_FACTOR
    goal = enc.mgr.AND(target_bdd(enc, target), enc.predicate(V.a_objective == objective))
    enc.mgr.protect(goal)

    def tell(st: dict) -> None:
        print(f"{name} layer {st.get('tick')} {st.get('seconds')}s nodes {st.get('nodes')}")
        sys.stdout.flush()

    f = safe(enc, list(coalition), goal, on_iteration=tell, step="split").kernel
    enc.mgr.protect(f)
    seconds = round(time.perf_counter() - t0, 1)
    peak = enc.mgr.stats()["peak_nodes"]
    rec = _dump(enc, f) | {"zone": name, "objective": objective}
    STORE.mkdir(parents=True, exist_ok=True)
    tmp = path(name).with_suffix(".tmp")
    with gzip.open(tmp, "wb", compresslevel=3) as fh:
        pickle.dump(rec, fh)
    tmp.replace(path(name))
    return {"seconds": seconds, "peak nodes": peak, "core": enc.mgr.core}


def compute(name: str) -> dict:
    model, switches, coalition, target, objective = ZONES[name]
    os.environ["WAVEFRONT_BDD"] = "c"
    ctx = multiprocessing.get_context("fork")
    recv, send = ctx.Pipe(duplex=False)

    def child() -> None:
        cap = MEMORY_GB << 30
        resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
        try:
            send.send(("ok", _work(name)))
        except MemoryError as exc:
            send.send(("over", f"over the cap of {MEMORY_GB} GB: {exc}"))
        except BaseException as exc:
            send.send(("error", repr(exc)))

    started = time.strftime("%Y-%m-%d %H:%M:%S %z")
    proc = ctx.Process(target=child)
    proc.start()
    send.close()
    try:
        kind, value = recv.recv()
    except EOFError:
        kind, value = "over", f"the child died unanswered (exit status {proc.exitcode})"
    proc.join()
    row = {
        "zone": name,
        "model": model,
        "switches": switches,
        "coalition": list(coalition),
        "target": target,
        "objective": objective,
        "profiles": "A under its profile",
        "memory cap GB": MEMORY_GB,
        "engine": {"core": "c", "step": "split", "gc min nodes": GC_MIN_NODES}
        | {"gc factor": GC_FACTOR},
        "started": started,
        "finished": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "kind": kind,
        "result": value,
    }
    STORE.mkdir(parents=True, exist_ok=True)
    (STORE / f"zone_{name}.json").write_text(json.dumps(row, indent=1) + "\n")
    return row


if __name__ == "__main__":
    print(json.dumps(compute(sys.argv[1]), indent=1))
