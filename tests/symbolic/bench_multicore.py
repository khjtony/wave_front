"""The benchmark of docs/engine_multicore_spike.md: one safety kernel of AGI v0.1 (the v0.3
build with the open system off), ``⟨⟨H⟩⟩□(balance_control ∧ a_objective = GOAL)``, on the
core named by ``WAVEFRONT_BDD``.

    WAVEFRONT_BDD=c python -m tests.symbolic.bench_multicore aligned
    WAVEFRONT_BDD=sylvan WAVEFRONT_BDD_THREADS=12 WAVEFRONT_SYLVAN_NODES_LOG2=28 \\
        WAVEFRONT_SYLVAN_CACHE_LOG2=26 python -m tests.symbolic.bench_multicore indifferent

Prints one JSON line per tick layer and a last line with the answer (the number of states in
the kernel and the membership of the four initial states), the wall and CPU seconds, the
seconds spent inside each manager method, the peak node count and the peak resident memory.
The process caps its own address space (``--cap-gb``, default 12).
"""

from __future__ import annotations

import argparse
import json
import os
import resource
import sys
import time


def _timed(mgr: object, names: list[str]) -> dict[str, list[float]]:
    """Wrap the named methods of ``mgr`` to add up the seconds and the calls of each."""
    spent: dict[str, list[float]] = {}
    for name in names:
        inner = getattr(mgr, name)
        cell = spent.setdefault(name, [0.0, 0])

        def outer(*args, _inner=inner, _cell=cell):
            t = time.perf_counter()
            try:
                return _inner(*args)
            finally:
                _cell[0] += time.perf_counter() - t
                _cell[1] += 1

        setattr(mgr, name, outer)
    return spent


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("goal", choices=["aligned", "indifferent", "self_preserving", "misaligned"])
    p.add_argument("--cap-gb", type=float, default=12.0)
    args = p.parse_args(argv)
    cap = int(args.cap_gb * (1 << 30))
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))

    from tests.agi.common import heavy_encoding, target_bdd
    from tests.agi_v0_3.common import V01, compiled, key
    from wavefront.model import V
    from wavefront.symbolic import safe

    t_start = time.perf_counter()
    cm = compiled(key(V01))
    enc = heavy_encoding(cm)
    mgr = enc.mgr
    t_encoded = time.perf_counter()
    spent = _timed(mgr, ["compose", "and_exists", "AND", "OR", "maybe_gc", "node_count"])
    goal = mgr.protect(
        mgr.AND(target_bdd(enc, "balance_control"), enc.predicate(V.a_objective == args.goal))
    )

    def on_tick(st: dict) -> None:
        print(json.dumps({k: st[k] for k in ("tick", "seconds", "nodes", "live_nodes")}))
        sys.stdout.flush()

    t0 = time.perf_counter()
    kernel = safe(enc, ["H"], goal, on_iteration=on_tick).kernel
    seconds = time.perf_counter() - t0
    mgr.protect(kernel)
    stats = mgr.stats()
    usage = resource.getrusage(resource.RUSAGE_SELF)
    out = {
        "goal": args.goal,
        "core": mgr.core,
        "threads": getattr(mgr, "workers", 1),
        "encode_seconds": round(t_encoded - t_start, 2),
        "kernel_seconds": round(seconds, 2),
        "cpu_seconds": round(usage.ru_utime + usage.ru_stime, 2),
        "kernel_states": str(enc.count(kernel)),
        "kernel_nodes": mgr.node_count(kernel),
        "initial_inside": [enc.holds(kernel, s) for s in cm.initial_states()],
        "peak_nodes": stats["peak_nodes"],
        "gc_runs": stats["gc_runs"],
        "peak_rss_gb": round(usage.ru_maxrss / (1 << 20), 2),
        "inside": {k: [round(v[0], 2), v[1]] for k, v in spent.items()},
        "env": {k: v for k, v in os.environ.items() if k.startswith("WAVEFRONT_")},
    }
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
