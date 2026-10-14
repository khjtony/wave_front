"""Benchmark of the symbolic engine on WW2 v0 (docs/engine_scaling.md). Not collected by
pytest; run as ``python3 -m tests.symbolic.bench_ww2 <command>`` from the repository root.

Commands:

- ``kernel``: WEST's kernel for ``balance_europe`` over the whole state space (both
  hypotheses at once, since ``aims_GER`` is a state variable), then membership of the
  tick-0 states, the T13 per-quarter sweep and the T8(b) states, with the shortest
  distance out of the kernel (forward breadth-first layers until one leaves the kernel).
- ``reach <label>``: the reachable set from one of the named states and the kernel's size
  inside it (``--limit`` seconds per state).
"""

from __future__ import annotations

import argparse
import json
import time

from models.ww2.hypotheses import fixed_model, realized_moves, snapshot_state
from models.ww2.v0 import model
from wavefront.symbolic import BDD, encode, reachable, safe, shortest

QUARTERS = [f"{y}Q{q}" for y in range(1936, 1940) for q in range(1, 5)][:15]  # to 1939Q3


def named_states(cm):
    """Start states of the benchmark, by label."""
    out = {}
    for aims in ("revisionist", "hegemonic"):
        out[f"tick0 {aims}"] = snapshot_state(cm, "1935Q4", aims)
    for aims in ("hegemonic", "revisionist"):
        for q in QUARTERS:
            out[f"T13 {q} {aims}"] = snapshot_state(cm, q, aims)
            try:
                out[f"T13 {q} {aims} builtins"] = snapshot_state(cm, q, aims, builtins=True)
            except Exception as exc:  # a snapshot without a builtins section
                print(f"# {q} {aims} builtins: {exc}")
    arms = cm.index["arms_GER"]
    high = cm.variables[arms].levels.index("high")
    for q in ("1938Q2", "1938Q3"):
        s = snapshot_state(cm, q, "hegemonic", builtins=True)
        out[f"T8b {q} builtins"] = s
        t = list(s)
        t[arms] = high
        out[f"T8b {q} builtins arms_GER=high"] = tuple(t)
    s = snapshot_state(cm, "1935Q4", "hegemonic")
    for k, move in enumerate(realized_moves(cm)):
        s = cm.step(s, move)
        if k + 1 in (10, 11):
            out[f"T8b replay tick {k + 1}"] = s
        if k + 1 == 11:
            break
    return out


def cmd_kernel(args):
    cm = (fixed_model(model, aims_GER=args.aims) if args.aims else model).compile()
    mgr = BDD()
    t = time.perf_counter()
    enc = encode(cm, mgr)
    t_enc = time.perf_counter() - t
    phi = enc.predicate("balance_europe")
    t = time.perf_counter()
    res = safe(enc, ["WEST"], phi, on_iteration=lambda s: print(" ", s, flush=True))
    t_safe = time.perf_counter() - t
    print(
        json.dumps(
            {
                "encode_s": round(t_enc, 2),
                "safe_s": round(t_safe, 1),
                "kernel_nodes": mgr.node_count(res.kernel),
                "peak_nodes": mgr.stats()["peak_nodes"],
                "bdd_vars": mgr.num_vars,
            }
        ),
        flush=True,
    )
    for label, s in named_states(cm).items():
        if not args.all and not label.startswith(tuple(args.only)):
            continue
        t = time.perf_counter()
        inside = res.contains(s)
        outside = mgr.DIFF(enc.dom, res.kernel)
        d = shortest(enc, s, outside, args.depth) if args.distance else None
        print(
            json.dumps(
                {
                    "state": label,
                    "tick": s[cm.index["tick"]],
                    "in_kernel": inside,
                    "shortest": d,
                    "seconds": round(time.perf_counter() - t, 1),
                    "peak_nodes": mgr.stats()["peak_nodes"],
                }
            ),
            flush=True,
        )
    return enc, res


def cmd_reach(args):
    cm = model.compile()
    mgr = BDD()
    enc = encode(cm, mgr)
    phi = enc.predicate("balance_europe")
    t = time.perf_counter()
    res = safe(enc, ["WEST"], phi)
    t_safe = time.perf_counter() - t
    states = named_states(cm)
    for label in args.labels:
        s = states[label]
        mgr.gc()
        t = time.perf_counter()
        r = reachable(
            enc,
            enc.state_cube(s),
            check=args.check,
            on_iteration=lambda st: print(" ", label, st, flush=True),
        )
        t_reach = time.perf_counter() - t
        print(
            json.dumps(
                {
                    "state": label,
                    "safe_s": round(t_safe, 1),
                    "reachable": r.count(),
                    "reach_s": round(t_reach, 1),
                    "reach_nodes": mgr.node_count(r.states),
                    "in_kernel": res.contains(s),
                    "kernel_reachable": res.count(r.states),
                    "peak_nodes": mgr.stats()["peak_nodes"],
                }
            ),
            flush=True,
        )


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    k = sub.add_parser("kernel")
    k.add_argument("--aims", default=None)
    k.add_argument("--all", action="store_true")
    k.add_argument("--only", nargs="*", default=["tick0", "T13", "T8b"])
    k.add_argument("--distance", action="store_true")
    k.add_argument("--depth", type=int, default=None)
    r = sub.add_parser("reach")
    r.add_argument("labels", nargs="+")
    r.add_argument("--check", action="store_true")
    args = p.parse_args()
    {"kernel": cmd_kernel, "reach": cmd_reach}[args.cmd](args)


if __name__ == "__main__":
    main()
