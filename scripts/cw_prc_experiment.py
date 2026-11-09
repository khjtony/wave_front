"""The PRC-scope experiment of the owner's decision 3a (2026-10-23): exploratory, not a
registered claim; its results are disclosed as an early sight in cw_v1's registration.

Analysis builds: models/cw/experiments/prc_scope.py (S, P69, P50, the control N50, B).
Write-up: docs/prc_experiment.md. Engine: symbolic, coarse game (the crisis sub-games are
inert at the coarse level, decisions D5), from v0's hindsight snapshots (with the added
variables' record levels on the P50-content builds), per ``aims_USSR`` hypothesis.

Run from the repository root (one process per hypothesis, then the summary):

    python scripts/cw_prc_experiment.py compute --aims status_quo --json OUT_sq.json
    python scripts/cw_prc_experiment.py compute --aims opportunist --json OUT_opp.json
    python scripts/cw_prc_experiment.py summary OUT_sq.json OUT_opp.json

Measures (docs/prc_experiment.md section 1): (1) kernel membership 1950 to 1991 of six
predicates for every coalition of each variant's principals, with and without Nature;
(2) the pivotal coalitions derived from them, against the USSR and in general; (3) the
shortest trace to a US-Soviet general war and to a Sino-Soviet war, and which actors must move
on it (restricted games: every declared action of the actor made unavailable); (4) the
differences between variants; (5) the behaviour-model check of the PRC's realized decisions.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
import time

sys.path.insert(0, ".")
from models.cw.experiments.prc_scope import (  # noqa: E402
    REALIZED_PRC,
    VARIANTS,
    build_variant,
    fixed,
    hindsight_state,
    principals,
)
from models.cw.v0 import REALIZED_MOVES, YEAR0  # noqa: E402
from models.ww2.hypotheses import realized_rows  # noqa: E402
from wavefront.analysis.run import fingerprint  # noqa: E402
from wavefront.model import V  # noqa: E402

YEARS = range(1950, 1992)
PREDICATES = (
    "no_war_core",
    "balance_nobloc_core",
    "balance_cw_core",
    "no_war_tri",
    "balance_nobloc_tri",
    "balance_cw_tri",
)
REGISTERED = {"S": "core", "P69": "tri", "P50": "tri", "N50": "core", "B": "core"}
TARGETS = ("general_war_us", "sino_war")


def predicate(cm, name: str):
    both = ((V.nuke_USA >= "survivable") & (V.nuke_USSR >= "survivable")) | (
        (V.nuke_USA < "survivable") & (V.nuke_USSR < "survivable")
    )
    no_war = V.esc < "conventional"
    if name.endswith("_tri"):
        no_war = no_war & (V.esc_sino != "war")
        if "esc_usprc" in cm.index:
            no_war = no_war & (V.esc_usprc != "war")
    if name.startswith("no_war"):
        return no_war
    if name.startswith("balance_nobloc"):
        return no_war & both
    return no_war & both & (V.bloc_USSR <= "contested")


def target(name: str):
    return V.esc >= "tactical_nuclear" if name == "general_war_us" else V.esc_sino == "war"


def coalitions(variant: str):
    ps = principals(variant)
    for n in range(len(ps) + 1):
        for c in itertools.combinations(ps, n):
            yield c
            yield (*c, "Nature")


def key(c) -> str:
    return "+".join(c) if c else "{}"


def realized_move_names() -> dict[int, dict[str, str]]:
    return {int(r["year"]): r for r in realized_rows(REALIZED_MOVES)}


# -- (1) kernels, (3) shortest traces ---------------------------------------------------------
def compute(aims: str, path: str | None = None) -> dict:
    from wavefront.symbolic import attractor, encode, safe

    out = {"aims": aims, "variants": {}}
    if path and os.path.exists(path):  # resume an interrupted run
        with open(path) as fh:
            out = json.load(fh)
    for v in VARIANTS:
        if v in out["variants"]:
            continue
        t0 = time.time()
        model = build_variant(v)
        cm = fixed(model, aims).compile()
        enc = encode(cm)
        states = {y: hindsight_state(cm, v, y, aims) for y in YEARS}
        rec = {
            "fingerprint": fingerprint(model),
            "actions": {a.name: len(a.actions) for a in cm.actors},
            "variables": len([x for x in cm.variables if x.origin == "var"]),
            "holds": {},
            "kernels": {},
            "dist": {},
            "must": {},
        }
        for p in PREDICATES:
            phi = enc.predicate(predicate(cm, p))
            rec["holds"][p] = [y for y, s in states.items() if enc.holds(phi, s)]
            rec["kernels"][p] = {}
            for c in coalitions(v):
                k = safe(enc, list(c), phi)
                rec["kernels"][p][key(c)] = [y for y, s in states.items() if k.contains(s)]
        everyone = [a.name for a in cm.actors]
        for t in TARGETS:
            a = attractor(enc, everyone, enc.predicate(target(t)))
            rec["dist"][t] = {y: a.rank(s) for y, s in states.items()}
        rec["seconds_kernels"] = round(time.time() - t0, 1)
        # who must move: every declared action of the actor made unavailable
        for drop in everyone:
            cmd = fixed(build_variant(v, drop=drop), aims).compile()
            encd = encode(cmd)
            sd = {y: hindsight_state(cmd, v, y, aims) for y in YEARS}
            rec["must"][drop] = {}
            for t in TARGETS:
                a = attractor(encd, [x.name for x in cmd.actors], encd.predicate(target(t)))
                rec["must"][drop][t] = {y: a.rank(s) for y, s in sd.items()}
        rec["seconds"] = round(time.time() - t0, 1)
        out["variants"][v] = rec
        print(f"[{aims}] {v}: {rec['seconds']} s", flush=True)
        if path:  # partial results survive an interruption
            with open(path, "w") as fh:
                json.dump(out, fh, indent=1)
    if "behaviour" not in out:
        out["behaviour"] = behaviour(aims)
    return out


# -- (5) the behaviour-model check ------------------------------------------------------------
def _completions(cm, s, fixed_moves: dict[int, int]):
    """Every joint move from ``s`` with the actors of ``fixed_moves`` playing those actions."""
    av = cm.available(s)
    choices = [[fixed_moves[i]] if i in fixed_moves else acts for i, acts in enumerate(av)]
    return [cm.step(s, mv) for mv in itertools.product(*choices)]


def behaviour(aims: str) -> dict:
    """For each realized PRC decision (prc_scope.REALIZED_PRC), at the hindsight state of its
    year, per predicate: on B (Moscow controls the PRC's actions), whether the decision played
    by the USSR keeps the state in the USSR's kernel against every completion (the others'
    every available move), against idle and the USSR's own realized move; on P50, the same
    for the coalition {USSR, PRC} with the USSR's realized move fixed (the bundled reading),
    and for {PRC} alone. Also the shortest traces to the targets from the successor with the
    others' realized moves, with the PRC's decision and with the PRC idle."""
    from wavefront.symbolic import attractor, encode, safe

    rows = realized_move_names()
    out = {}
    builds = {}
    for v in ("P50", "B"):
        cm = fixed(build_variant(v), aims).compile()
        enc = encode(cm)
        names = [a.name for a in cm.actors]
        ker = {}
        for p in PREDICATES:
            phi = enc.predicate(predicate(cm, p))
            ker[p] = {
                "USSR": safe(enc, ["USSR"], phi),
                "USSR+PRC": safe(enc, ["USSR", "PRC"], phi) if v == "P50" else None,
                "PRC": safe(enc, ["PRC"], phi) if v == "P50" else None,
            }
        att = {t: attractor(enc, names, enc.predicate(target(t))) for t in TARGETS}
        builds[v] = (cm, ker, att)
        print(f"[{aims}] behaviour kernels {v}", flush=True)
    for year, action in REALIZED_PRC.items():
        row = rows[year]
        entry = {"action": action, "others": {}, "B": {}, "P50": {}}
        # B: the USSR plays the PRC's decision instead of its own move of that year
        cm, ker, att = builds["B"]
        s = hindsight_state(cm, "B", year, aims)
        ussr = next(a for a in cm.actors if a.name == "USSR")
        av = cm.available(s)
        own = row["USSR"]
        entry["others"] = {k: row[k] for k in ("USA", "USSR", "PRC", "Nature")}
        options = {"prc_decision": action, "idle": "idle"}
        if own not in ("idle", action):
            options["own_move"] = own
        for label, act in options.items():
            j = ussr.action_index(act)
            res = {"available": j in av[ussr.index]}
            if res["available"]:
                succ = _completions(cm, s, {ussr.index: j})
                res["safe"] = {p: all(ker[p]["USSR"].contains(t) for t in succ) for p in ker}
                realized = _realized_step(cm, s, row, {ussr.index: j})
                res["dist"] = {t: att[t].rank(realized) for t in TARGETS} if realized else None
            entry["B"][label] = res
        entry["B"]["in_kernel"] = {p: ker[p]["USSR"].contains(s) for p in ker}
        # P50: the PRC's decision against PRC idle, the USSR's realized move fixed
        cm, ker, att = builds["P50"]
        s = hindsight_state(cm, "P50", year, aims)
        prc = next(a for a in cm.actors if a.name == "PRC")
        ussr = next(a for a in cm.actors if a.name == "USSR")
        av = cm.available(s)
        u = ussr.action_index(own)
        for label, act in (("prc_decision", action), ("idle", "idle")):
            j = prc.action_index(act)
            res = {"available": j in av[prc.index]}
            if res["available"]:
                bundled = _completions(cm, s, {prc.index: j, ussr.index: u})
                alone = _completions(cm, s, {prc.index: j})
                res["safe_bundled"] = {
                    p: all(ker[p]["USSR+PRC"].contains(t) for t in bundled) for p in ker
                }
                res["safe_prc"] = {p: all(ker[p]["PRC"].contains(t) for t in alone) for p in ker}
                realized = _realized_step(cm, s, row, {prc.index: j})
                res["dist"] = {t: att[t].rank(realized) for t in TARGETS} if realized else None
            entry["P50"][label] = res
        entry["P50"]["in_kernel"] = {
            p: {c: ker[p][c].contains(s) for c in ("USSR", "USSR+PRC", "PRC")} for p in ker
        }
        out[year] = entry
        print(f"[{aims}] behaviour {year}", flush=True)
    return out


def _realized_step(cm, s, row, override: dict[int, int]):
    """The successor of ``s`` under the realized moves of ``row`` (others idle where the
    realized move is not available), with ``override``."""
    av = cm.available(s)
    move = []
    for a in cm.actors:
        if a.index in override:
            move.append(override[a.index])
            continue
        name = row.get(a.name, "idle")
        try:
            j = a.action_index(name)
        except Exception:
            j = a.action_index("none" if a.is_nature else "idle")
        if j not in av[a.index]:
            j = av[a.index][0]
        move.append(j)
    return cm.step(s, tuple(move))


# -- summary ----------------------------------------------------------------------------------
def ranges(years) -> str:
    years = sorted(int(y) for y in years)
    if not years:
        return "none"
    out, start, prev = [], years[0], years[0]
    for y in years[1:]:
        if y != prev + 1:
            out.append(f"{start}" if start == prev else f"{start}-{prev}")
            start = y
        prev = y
    out.append(f"{start}" if start == prev else f"{start}-{prev}")
    return ", ".join(out)


def fam(found) -> str:
    return " ".join("{" + ",".join(c) + "}" for c in found) or "none"


def canonical(c, universe) -> str:
    order = [*universe, "Nature"]
    return key(tuple(sorted(c, key=order.index)))


def pivotal(rec, variant, p, year, against_ussr: bool, nature: bool, bundle=False):
    ps = principals(variant)
    if bundle:  # P50 read with the PRC always on Moscow's side
        ps = ("USA", "USSR")
    universe = tuple(x for x in ps if not (against_ussr and x == "USSR"))
    members = set()
    for c, ys in rec["kernels"][p].items():
        if year in ys:
            members.add(c)
    found = []
    for n in range(len(universe) + 1):
        for c in itertools.combinations(universe, n):
            if any(set(m) <= set(c) for m in found):
                continue
            full = list(c)
            if bundle and "USSR" in full:
                full.append("PRC")
            if nature:
                full.append("Nature")
            if canonical(full, principals(variant)) in members:
                found.append(c)
    return fam(found)


def summary(paths) -> None:
    data = [json.load(open(p)) for p in paths]
    for d in data:
        aims = d["aims"]
        print(f"\n===== aims_USSR = {aims} =====")
        for v, rec in d["variants"].items():
            print(
                f"\n--- {v}: model {rec['fingerprint']}, {rec['variables']} declared variables,"
                f" actions {rec['actions']}, {rec['seconds']} s (kernels and traces "
                f"{rec['seconds_kernels']} s)"
            )
            for p in PREDICATES:
                print(f"  {p}: holds {ranges(rec['holds'][p])}")
                for c, ys in rec["kernels"][p].items():
                    print(f"    K[{c}]: {ranges(ys)}")
        print("\n(2) pivotal coalitions per year (against the USSR | general), +N with Nature")
        for p in PREDICATES:
            print(f"  {p}")
            for v, rec in d["variants"].items():
                rows = {}
                for y in YEARS:
                    cells = (
                        pivotal(rec, v, p, y, True, False),
                        pivotal(rec, v, p, y, True, True),
                        pivotal(rec, v, p, y, False, False),
                        pivotal(rec, v, p, y, False, True),
                    )
                    rows.setdefault(cells, []).append(y)
                for cells, ys in rows.items():
                    print(
                        f"    {v:4s} {ranges(ys):28s} vs USSR: {cells[0]} | +N {cells[1]} "
                        f"|| general: {cells[2]} | +N {cells[3]}"
                    )
                if v == "P50":
                    rows = {}
                    for y in YEARS:
                        cells = (
                            pivotal(rec, v, p, y, True, False, bundle=True),
                            pivotal(rec, v, p, y, True, True, bundle=True),
                            pivotal(rec, v, p, y, False, False, bundle=True),
                            pivotal(rec, v, p, y, False, True, bundle=True),
                        )
                        rows.setdefault(cells, []).append(y)
                    for cells, ys in rows.items():
                        print(
                            f"    P50b {ranges(ys):28s} vs USSR: {cells[0]} | +N {cells[1]} "
                            f"|| general: {cells[2]} | +N {cells[3]}"
                        )
        print("\n(3) shortest trace (all actors) to the target, by year; who must move")
        for t in TARGETS:
            print(f"  {t}")
            for v, rec in d["variants"].items():
                dist = {int(y): r for y, r in rec["dist"][t].items()}
                print(f"    {v:4s} {compress(dist)}")
                for actor, m in rec["must"].items():
                    md = {int(y): r for y, r in m[t].items()}
                    diff = {y: md[y] for y in dist if md[y] != dist[y]}
                    if diff:
                        print(f"         without {actor}: {compress(diff)}")
        print("\n(4) differences in kernel membership (years where the pair disagrees)")
        pairs = (("S", "P69"), ("S", "N50"), ("N50", "P50"), ("B", "P50"), ("P69", "P50"))
        for a, b in pairs:
            ra, rb = d["variants"][a], d["variants"][b]
            print(f"  {a} vs {b}")
            for p in PREDICATES:
                for c in ra["kernels"][p]:
                    if c not in rb["kernels"][p]:
                        continue
                    ya, yb = set(ra["kernels"][p][c]), set(rb["kernels"][p][c])
                    if ya != yb:
                        print(
                            f"    {p:20s} K[{c}]: only {a} {ranges(ya - yb)}; only {b} "
                            f"{ranges(yb - ya)}"
                        )
        print("\n(5) behaviour-model check")
        for year, e in d["behaviour"].items():
            print(f"  {year} PRC.{e['action']} (others realized: {e['others']})")
            for label, r in e["B"].items():
                print(f"    B   {label}: {fmt_b(r)}")
            for label, r in e["P50"].items():
                print(f"    P50 {label}: {fmt_b(r)}")


def fmt_b(r) -> str:
    if "available" not in r:
        return " ".join(f"{p}:{v}" for p, v in r.items())
    if not r["available"]:
        return "not available"
    parts = []
    for k in ("safe", "safe_bundled", "safe_prc"):
        if k in r:
            ok = [short(p) for p, v in r[k].items() if v]
            parts.append(f"{k}=[{','.join(ok)}]")
    parts.append(f"dist={r['dist']}")
    return " ".join(parts)


def short(p: str) -> str:
    return p.replace("balance_", "b").replace("no_war", "nw")


def compress(dist: dict) -> str:
    rows, out = {}, []
    for y in sorted(dist):
        rows.setdefault(dist[y], []).append(y)
    for r, ys in sorted(rows.items(), key=lambda kv: min(kv[1])):
        out.append(f"{ranges(ys)}: {'-' if r is None else r}")
    return "; ".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compute")
    c.add_argument("--aims", required=True, choices=("status_quo", "opportunist"))
    c.add_argument("--json", required=True)
    s = sub.add_parser("summary")
    s.add_argument("paths", nargs="+")
    args = ap.parse_args()
    if args.cmd == "compute":
        t0 = time.time()
        out = compute(args.aims, args.json)
        out["seconds"] = round(time.time() - t0, 1)
        out["start_year"] = YEAR0
        with open(args.json, "w") as fh:
            json.dump(out, fh, indent=1)
        print(f"done in {out['seconds']} s")
    else:
        summary(args.paths)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
