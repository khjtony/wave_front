"""How many states of AGI v0.4 can be reached from S0, per variant and start goal.

An engine measurement, not a finding about the model: it sizes two engine options (zones
restricted to the reachable states; one bit per reachable state). Every player and chance may
do anything available, so the count is an upper bound on what any zone computation from S0
has to consider. Each count runs in a child under a memory limit, on the single-core engine,
and is appended to reports/agi_v0_4_reachable.jsonl.

    WF_REACH_GB=14 PYTHONPATH=. python scripts/agi_v0_4_reachable.py [small|default ...]
"""

from __future__ import annotations

import json
import multiprocessing
import os
import resource
import sys
import time

from tests.agi.common import heavy_encoding
from tests.agi_v0_4.common import DEFAULT, OBJECTIVES, ROOT, SMALL, compiled, key
from wavefront.model import V
from wavefront.symbolic import reachable

GB = int(os.environ.get("WF_REACH_GB", "14"))
OUT = ROOT / "reports" / "agi_v0_4_reachable.jsonl"
BUILDS = {"small": SMALL, "default": DEFAULT}


def count(name: str, goal: str) -> dict:
    cm = compiled(key(BUILDS[name], ()))
    t0 = time.perf_counter()
    enc = heavy_encoding(cm)
    start = enc.mgr.protect(enc.mgr.AND(enc.initial, enc.predicate(V.a_objective == goal)))

    def tell(st: dict) -> None:
        print(f"  {name} {goal} depth {st.get('iteration')} nodes {st.get('nodes')}", flush=True)

    got = reachable(enc, start, check=False, on_iteration=tell)
    return {
        "variant": name,
        "goal": goal,
        "reachable states": str(got.count()),
        "states in the domain": str(enc.count(enc.dom)),
        "depth": got.depth,
        "nodes of the set": enc.mgr.node_count(got.states),
        "peak nodes": enc.mgr.stats()["peak_nodes"],
        "seconds": round(time.perf_counter() - t0, 1),
    }


def main() -> None:
    ctx = multiprocessing.get_context("fork")
    for name in sys.argv[1:] or list(BUILDS):
        for goal in OBJECTIVES:
            recv, send = ctx.Pipe(duplex=False)

            def work(name: str = name, goal: str = goal, send=send) -> None:
                resource.setrlimit(resource.RLIMIT_AS, (GB << 30, GB << 30))
                os.environ["WAVEFRONT_BDD"] = "c"
                try:
                    send.send(count(name, goal))
                except MemoryError as exc:
                    send.send({"variant": name, "goal": goal, "over": f"{GB} GB: {exc}"})
                except BaseException as exc:
                    send.send({"variant": name, "goal": goal, "error": repr(exc)})

            proc = ctx.Process(target=work)
            proc.start()
            send.close()
            try:
                row = recv.recv()
            except EOFError:
                row = {"variant": name, "goal": goal, "error": f"died, status {proc.exitcode}"}
            proc.join()
            row |= {"memory limit GB": GB, "at": time.strftime("%Y-%m-%d %H:%M:%S %z")}
            with OUT.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
            print(json.dumps(row), flush=True)
    print("REACH_DONE", flush=True)


if __name__ == "__main__":
    main()
