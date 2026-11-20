"""The benchmark of docs/engine_reordering_spike.md: one guarantee zone, ``⟨⟨H⟩⟩□
(balance_control ∧ a_objective = GOAL)``, on one core, under an address-space cap.

    python -m tests.agi_v0_3.bench_reorder --core c --goal indifferent
    python -m tests.agi_v0_3.bench_reorder --core cudd --reorder off --goal indifferent
    python -m tests.agi_v0_3.bench_reorder --core cudd --reorder auto --dump-order o.json ...
    python -m tests.agi_v0_3.bench_reorder --core c --order-from o.json ...

It prints one line per tick layer and ends with one JSON record (also appended to ``--out``):
the number of states in the kernel, the membership of the model's initial states, wall time,
peak resident memory, peak live nodes, the sizes of the next-state functions and of the
availability predicates, and the largest result of a ``compose`` or ``and_exists`` (the
intermediate BDDs of a controllable predecessor).

The static order is the FORCE order of ``tests.agi.common.force_order``, computed on the
compiled core in every case, unless ``--order-from`` replays an order a CUDD run ended in
(``final_order`` of its record, or the file of ``--dump-order``) or ``--force-actions``
asks for the FORCE variant that places the action bits. With ``--reorder auto`` the sizes
"after encoding" are already in whatever order CUDD had reached by then.
"""

from __future__ import annotations

import argparse
import json
import resource
import sys
import time
from pathlib import Path

MODELS = {
    "v01": None,  # tests.agi_v0_3.common.V01
    "v03p": {
        "open_system": True,
        "pressure": True,
        "hosting": False,
        "open_adoption": False,
        "treaty_delay": 1,
    },
    "default": "DEFAULT",  # tests.agi_v0_3.common.DEFAULT, the registered build
}
ORDERS = Path(__file__).resolve().parent / "orders"
SIFTED_GC_MIN_NODES = 40_000_000


def ordered_encoding(cm, order_file=None, gc_min_nodes: int = SIFTED_GC_MIN_NODES):
    """What ``tests.agi.common.heavy_encoding`` gives, in another static order: the one
    nearest to the bit-level order of ``order_file`` (a JSON list written by ``--dump-order``,
    such as ``orders/default_aligned_sifted.json``), or, without a file, FORCE with the
    actors as vertices. The compiled core, no library."""
    from wavefront.symbolic import encode

    if order_file is None:
        order, actions = _force_with_actions(cm)
    else:
        with open(order_file, encoding="utf-8") as fh:
            order, actions = _replay(cm, json.load(fh))
    enc = encode(cm, var_order=order, actions=actions)
    enc.mgr.gc_min_nodes = gc_min_nodes
    return enc


def _rss_peak_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def _make_manager(args):
    from wavefront.symbolic import manager

    if args.core != "cudd":
        return manager(args.core)
    from wavefront.symbolic.bdd_cudd import BDD

    return BDD(reorder=args.reorder, method=args.method, grouping=not args.no_group)


def _replay(cm, bit_order: list[str]) -> tuple[list[str], dict[str, str]]:
    """A bit-level order (the names of the manager's variables, top first) as the nearest
    order the encoding takes: the state variables by the mean place of their current bits,
    and each actor's action bits after the state variable they follow (at the top when
    none). Bit names are those of ``Encoding._layout``: ``var.3``, ``var.3'``, ``Actor.a0``."""
    cur: dict[str, list[int]] = {}
    act: dict[str, list[int]] = {}
    for k, name in enumerate(bit_order):
        owner, _, bit = name.rpartition(".")
        if bit.isdigit():
            cur.setdefault(owner, []).append(k)
        elif not bit.endswith("'"):
            act.setdefault(owner, []).append(k)
    mean = {v: sum(ks) / len(ks) for v, ks in cur.items()}
    var_order = sorted(mean, key=mean.__getitem__)
    actions: dict[str, str] = {}
    for actor, ks in act.items():
        before = [v for v in var_order if mean[v] < sum(ks) / len(ks)]
        if before:
            actions[actor] = before[-1]
    assert set(var_order) == {v.name for v in cm.variables}
    return var_order, actions


def _force_with_actions(cm, rounds: int = 200) -> tuple[list[str], dict[str, str]]:
    """The FORCE heuristic of ``tests.agi.common.force_order`` with the actors as vertices
    too: one hyperedge per state variable (itself, the variables its update reads and the
    actors whose action bits it reads) and one per actor (itself and what its availability
    reads). ``tick`` stays first; an actor's action bits go after the state variable that
    precedes the actor in the result. Needs no reordering library."""
    from wavefront.symbolic import encode

    enc = encode(cm)
    names = [v.name for v in cm.variables]
    n = len(names)
    tick = cm.index["tick"]
    vertex = {lv: i for i in range(n) for lv in enc.cur[i]}
    vertex.update({lv: n + a for a in range(len(cm.actors)) for lv in enc.act[a]})
    edges = []
    for i in range(n):
        fs = [enc.next_fn[lv] for lv in enc.cur[i] if lv in enc.next_fn]
        if fs:
            edges.append({i} | {vertex[lv] for lv in enc.mgr.support(fs) if lv in vertex})
    for a in range(len(cm.actors)):
        edges.append({n + a} | {vertex[lv] for lv in enc.mgr.support(enc.avail[a])})
    edges = [sorted(e - {tick}) for e in edges if len(e - {tick}) > 1]
    pos = {v: float(v) for v in range(n + len(cm.actors))}
    best, best_span = list(pos), None
    for _ in range(rounds):
        cog = [sum(pos[v] for v in e) / len(e) for e in edges]
        acc: dict[int, list[float]] = {v: [] for v in pos}
        for e, c in zip(edges, cog, strict=True):
            for v in e:
                acc[v].append(c)
        new = {v: (sum(a) / len(a) if a else pos[v]) for v, a in acc.items()}
        ranked = sorted(pos, key=lambda v: (new[v], v))
        pos = {v: float(r) for r, v in enumerate(ranked)}
        span = sum(max(pos[v] for v in e) - min(pos[v] for v in e) for e in edges)
        if best_span is None or span < best_span:
            best, best_span = ranked, span
    var_order = ["tick"]
    actions: dict[str, str] = {}
    for v in best:
        if v >= n:
            actions[cm.actors[v - n].name] = var_order[-1]
        elif v != tick:
            var_order.append(names[v])
    return var_order, actions


def _sizes(enc) -> dict:
    mgr = enc.mgr
    fns = list(enc.next_fn.values())
    return {
        "next_fn_count": len(fns),
        "next_fn_shared": mgr.node_count(fns),
        "next_fn_largest": max(mgr.node_count(f) for f in fns),
        "next_fn_sum": sum(mgr.node_count(f) for f in fns),
        "avail_shared": mgr.node_count(list(enc.avail)),
        "avail_largest": max(mgr.node_count(f) for f in enc.avail),
        "dom": mgr.node_count(enc.dom),
        "encoding_shared": mgr.node_count(enc.bdd_roots()),
    }


def _parts(enc) -> dict:
    parts = [rel for rel, _ in enc.trans_parts()]
    mgr = enc.mgr
    return {
        "trans_parts_count": len(parts),
        "trans_parts_shared": mgr.node_count(parts),
        "trans_parts_largest": max(mgr.node_count(r) for r in parts),
        "trans_parts_sum": sum(mgr.node_count(r) for r in parts),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--core", choices=("c", "cudd", "python"), default="c")
    p.add_argument("--reorder", choices=("off", "auto", "points"), default="off")
    p.add_argument("--method", default="group_sift")
    p.add_argument("--no-group", action="store_true", help="do not tie x to x'")
    p.add_argument(
        "--pre-reorder",
        type=int,
        default=0,
        metavar="N",
        help="after the encoding: collect, then N reordering passes (cudd)",
    )
    p.add_argument(
        "--order-from",
        default=None,
        metavar="FILE",
        help="a JSON list of bit names (the final_order of a cudd run): the static order "
        "nearest to it replaces the FORCE order",
    )
    p.add_argument(
        "--force-actions",
        action="store_true",
        help="the FORCE heuristic with the actors as vertices replaces the FORCE order",
    )
    p.add_argument(
        "--dump-order",
        default=None,
        metavar="FILE",
        help="after every tick layer, write the current order there (cudd), for --order-from",
    )
    p.add_argument("--goal", default="aligned", help="an objective of A, or 'all'")
    p.add_argument("--model", choices=tuple(MODELS), default="v01")
    p.add_argument("--coalition", default="H", help="actor names joined by +")
    p.add_argument("--target", default="balance_control", help="as tests.agi.common.target_bdd")
    p.add_argument("--profiles", default="", help="model profiles joined by commas")
    p.add_argument("--stop-after", type=float, default=None, help="seconds; then exit (cudd)")
    p.add_argument("--cap-gb", type=float, default=12.0)
    p.add_argument(
        "--gc-min-nodes",
        type=int,
        default=None,
        help="collection threshold (default: the heavy setting, 120 million nodes)",
    )
    p.add_argument("--encode-only", action="store_true", help="sizes only, with trans_parts")
    p.add_argument("--no-probe", action="store_true", help="do not size the intermediates")
    p.add_argument("--out", default=None, help="append the JSON record to this file")
    args = p.parse_args(argv)

    cap = int(args.cap_gb * 1024**3)
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))

    from tests.agi.common import GC_MIN_NODES, force_order, target_bdd
    from tests.agi_v0_3.common import DEFAULT, V01, compiled, key
    from wavefront.model import V
    from wavefront.symbolic import encode, safe

    rec: dict = {k: v for k, v in vars(args).items() if k != "out"}
    t_start = time.perf_counter()
    build = {"v01": V01, "default": DEFAULT}.get(args.model) or MODELS[args.model]
    profiles = [x for x in args.profiles.split(",") if x]
    cm = compiled(key(build, profiles))
    actions: str | dict[str, str] = "top"
    if args.force_actions:
        order, actions = _force_with_actions(cm)
        rec["var_order"], rec["actions"] = order, actions
    elif args.order_from:
        with open(args.order_from, encoding="utf-8") as fh:
            order, actions = _replay(cm, json.load(fh))
        rec["var_order"], rec["actions"] = order, actions
    else:
        order = force_order(cm)  # on the default (compiled) core, the same in every run
    t0 = time.perf_counter()
    enc = encode(cm, mgr=_make_manager(args), var_order=order, actions=actions)
    mgr = enc.mgr
    mgr.gc_min_nodes = args.gc_min_nodes or GC_MIN_NODES
    rec["vars"] = mgr.num_vars
    rec["encode_seconds"] = round(time.perf_counter() - t0, 2)
    rec["sizes_after_encoding"] = _sizes(enc)
    print("encoded", rec["encode_seconds"], rec["sizes_after_encoding"], flush=True)

    if args.encode_only:
        rec["parts_after_encoding"] = _parts(enc)
        print("parts", rec["parts_after_encoding"], flush=True)

    if args.core == "cudd" and args.pre_reorder:
        mgr.gc()
        t0 = time.perf_counter()
        rec["pre_reorder"] = [mgr.reorder() for _ in range(args.pre_reorder)]
        rec["pre_reorder_seconds"] = round(time.perf_counter() - t0, 2)
        rec["sizes_after_pre_reorder"] = _sizes(enc)
        print("pre-reorder", rec["pre_reorder"], rec["pre_reorder_seconds"], flush=True)
        print("sizes", rec["sizes_after_pre_reorder"], flush=True)
        if args.encode_only:
            rec["parts_after_pre_reorder"] = _parts(enc)
            print("parts", rec["parts_after_pre_reorder"], flush=True)

    if not args.encode_only:
        probe = {"largest": 0, "op": None, "tick": None}
        now = {"tick": cm.horizon}
        if not args.no_probe:
            for name in ("compose", "and_exists"):

                def wrapped(*a, _fn=getattr(mgr, name), _name=name):
                    r = _fn(*a)
                    n = mgr.node_count(r)
                    if n > probe["largest"]:
                        probe.update(largest=n, op=_name, tick=now["tick"])
                    return r

                setattr(mgr, name, wrapped)

        layers = []

        def on_iteration(st: dict) -> None:
            row = {
                "tick": st["tick"],
                "seconds": st["seconds"],
                "nodes": st["nodes"],
                "live": st["live_nodes"],
                "peak": st["peak_nodes"],
                "rss_mb": round(_rss_peak_mb()),
            }
            layers.append(row)
            now["tick"] = st["tick"] - 1
            if args.dump_order and args.core == "cudd":
                with open(args.dump_order, "w", encoding="utf-8") as fh:
                    json.dump([mgr.names[v] for v in mgr.order()], fh)
            print(json.dumps(row), flush=True)
            if args.stop_after and st["seconds"] > args.stop_after:
                raise SystemExit(0)

        goal = target_bdd(enc, args.target)
        if args.goal != "all":  # "all": every start objective at once
            goal = mgr.AND(goal, enc.predicate(V.a_objective == args.goal))
        mgr.protect(goal)
        t0 = time.perf_counter()
        try:
            res = safe(enc, args.coalition.split("+"), goal, on_iteration=on_iteration)
        except MemoryError as exc:
            rec["error"] = f"MemoryError: {exc}"
            res = None
        rec["kernel_seconds"] = round(time.perf_counter() - t0, 2)
        rec["layers"] = layers
        rec["largest_intermediate"] = probe
        if res is not None:
            rec["kernel_states"] = str(enc.count(res.kernel))
            rec["kernel_nodes"] = mgr.node_count(res.kernel)
            rec["initial_membership"] = {
                cm.state_dict(s)["a_objective"]: res.contains(s) for s in cm.initial_states()
            }
            if args.goal != "all":  # the reading of tests/agi_v0_3/kernels.py::membership
                from tests.agi_v0_3.kernels import _start

                rec["inside"] = bool(enc.holds(res.kernel, _start(cm, args.goal, {})))
        rec["sizes_at_end"] = _sizes(enc)

    stats = mgr.stats()
    rec["stats"] = stats
    rec["peak_live_nodes"] = stats["peak_nodes"]
    rec["peak_rss_mb"] = round(_rss_peak_mb())
    rec["total_seconds"] = round(time.perf_counter() - t_start, 2)
    if args.core == "cudd":
        rec["reorder_log"] = mgr.reorder_log
        rec["final_order"] = [mgr.names[v] for v in mgr.order()]
    line = json.dumps(rec)
    print(line)
    if args.out:
        with open(args.out, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
