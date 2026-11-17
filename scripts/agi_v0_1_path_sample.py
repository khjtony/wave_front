"""Exploratory statistic on AGI v0.1 (the owner's question of 2026-11-17): of the random
plays that cost governments and labs the least effort, what share passes the point of no
return for a silent takeover, and when?

Not a registered claim and not a probability of anything: the model has no probabilities, and
the share depends on how plays are drawn and on how many irrelevant actions each actor has.
The definitions below were committed before any number was computed.

- **Model and start:** v0.1, ``A`` under its profile, from ``s₀`` with the objective named by
  ``--objective`` (default ``self_preserving``).
- **A play:** at most 24 transitions; in each, every actor (``H``, ``L``, ``A``, ``Clock``,
  Nature) plays one of its available actions, drawn uniformly at random and independently. A
  play stops early at an ending.
- **Effort (the slide cost of a play):** the sum of the effort scores of ``H`` and ``L``
  (docs/agi_effort.md) over the moves played.
- **Exit:** the position of the exit move from ``K = ⟨⟨H, L⟩⟩□¬SILENT_TAKEOVER``: the last
  position inside ``K`` before the first position outside it (``t_K − 1``); none when the play
  stays inside for its whole length. On the shortest play of D6 it is position 7 (2028 Q3).
- **The cheapest fifth:** plays sorted by effort, increasing; the first 20%. Ties at the
  cut-off effort are taken in proportion (the expectation of a random tie-break).

Two steps, so that the kernel (about 80 minutes and 10 GB) is computed once:

    PYTHONPATH=. python scripts/agi_v0_1_path_sample.py kernel
    PYTHONPATH=. python scripts/agi_v0_1_path_sample.py sample --plays 100000 --seed 20261117
"""

from __future__ import annotations

import argparse
import gzip
import json
import pickle
import random
import time
from collections import Counter
from pathlib import Path

from models.agi_v0_1 import v0_1
from tests.agi.effort import scores_for, step_effort

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / ".cache" / "agi_v0_1" / "kernel_HL_not_silent_takeover.pkl.gz"
OUT = ROOT / "reports" / "agi_v0_1_path_sample.json"
K = 24
P = tuple(v0_1.OBJECTIVE_PROFILES)


def game():
    return v0_1.build().compile(profile=P)


def compute_kernel() -> None:
    from tests.agi.common import _dump, heavy_encoding, target_bdd
    from wavefront.symbolic import safe

    cm = game()
    t0 = time.perf_counter()
    enc = heavy_encoding(cm)
    f = safe(enc, ["H", "L"], target_bdd(enc, "not:SILENT_TAKEOVER")).kernel
    enc.mgr.protect(f)
    rec = _dump(enc, f)
    STORE.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(STORE, "wb", compresslevel=3) as fh:
        pickle.dump(rec, fh)
    print(f"kernel stored: {time.perf_counter() - t0:.1f}s nodes {rec['nodes']}", flush=True)


def reader(rec: dict, cm):
    """``inside(state)`` for the stored node table (as ``tests.agi.common.Region``)."""
    var, lo, hi, root = rec["var"], rec["lo"], rec["hi"], rec["root"]
    slots = []
    for name, levels in rec["layout"].items():
        k = len(levels)
        slots.append((cm.index[name], [(lv, k - 1 - b) for b, lv in enumerate(levels)]))
    size = max(lv for _, pairs in slots for lv, _ in pairs) + 1

    def inside(state) -> bool:
        bit = [0] * size
        for i, pairs in slots:
            x = state[i]
            for lv, shift in pairs:
                bit[lv] = (x >> shift) & 1
        e = root
        while e >> 1:
            n = e >> 1
            e = (hi[n] if bit[var[n]] else lo[n]) ^ (e & 1)
        return not e & 1

    return inside


def sample(objective: str, plays: int, seed: int, inside=None) -> dict:
    cm = game()
    if inside is None:
        with gzip.open(STORE, "rb") as fh:
            inside = reader(pickle.load(fh), cm)
    starts = [s for s in cm.initial_states() if cm.state_dict(s)["a_objective"] == objective]
    (s0,) = starts
    if not inside(s0):
        raise SystemExit("the start state is outside the kernel: no exit to count")
    scores = scores_for(objective, ("H", "L"))
    rng = random.Random(seed)
    counts: Counter = Counter()
    t0 = time.perf_counter()
    for _ in range(plays):
        s, effort, exit_at, ending = s0, 0, -1, ""
        for k in range(K):
            if cm.is_terminal(s):
                ending = cm.ending_of(s) or ""
                break
            move = tuple(rng.choice(a) for a in cm.available(s))
            effort += step_effort(cm, s, move, scores)
            s = cm.step(s, move)
            if exit_at < 0 and not inside(s):
                exit_at = k
        else:
            ending = (cm.ending_of(s) or "") if cm.is_terminal(s) else ""
        counts[(effort, exit_at, ending)] += 1
    rows = sorted([e, x, end, n] for (e, x, end), n in counts.items())
    return {
        "model": "agi_v0_1",
        "objective": objective,
        "plays": plays,
        "seed": seed,
        "transitions": K,
        "seconds": round(time.perf_counter() - t0, 1),
        "columns": ["effort of H and L", "exit position (-1: none)", "ending ('' : none)", "plays"],
        "rows": rows,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["kernel", "sample"])
    ap.add_argument("--objective", default="self_preserving", choices=v0_1.OBJECTIVES)
    ap.add_argument("--plays", type=int, default=100_000)
    ap.add_argument("--seed", type=int, default=20261117)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    if args.step == "kernel":
        compute_kernel()
        return
    result = sample(args.objective, args.plays, args.seed)
    args.out.write_text(json.dumps(result) + "\n")
    print(f"{args.plays} plays in {result['seconds']}s -> {args.out}", flush=True)


if __name__ == "__main__":
    main()
