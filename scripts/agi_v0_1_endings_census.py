"""Exploratory census of the bad endings met by random plays of AGI v0.1, and of the point of
no return for each (the owner's question of 2026-11-17).

Not a registered claim and not a probability: uniform random plays, as in
scripts/agi_v0_1_path_sample.py, but played to the horizon (56 quarters) so that the slow
endings can occur. Definitions, committed before any number was computed:

- **Model and start:** v0.1, ``A`` under its profile, from ``s₀`` with the objective of
  ``--objective`` (default ``self_preserving``).
- **A play:** at most 56 transitions; every actor draws one of its available actions
  uniformly at random; the play stops at an ending.
- **Bad endings:** ``SILENT_TAKEOVER``, ``DISEMPOWERMENT``, ``EXTINCTION`` and ``STALEMATE``
  (terminal), and ``OVERT_TAKEOVER`` (a waypoint: counted when the play first visits a state
  that violates ``no_overt_takeover``; the play goes on). The other outcomes are ``CONTAINED``,
  ``COEXIST`` (the horizon with the control balance never broken) and no ending at the horizon.
- **Point of no return for an ending E:** the first state outside ``⟨⟨H, L⟩⟩□¬E``, read
  against a stored kernel; counted only for the endings whose kernel has been computed
  (``kernel --ending E``; each is one long computation).
- **Reported per ending:** the share of plays that reach it, and the quarter (median and
  range); the share that reach its point of no return, and the quarter; of those, the share
  that go on to the ending ("conversion") and the quarters between the two; the share of
  plays that reach the ending without ever leaving the kernel (which must be zero); and the
  same shares within the first 24 quarters.

Added 2026-11-17 after the first numbers, on the owner's next question, and reported as such:
per play, whether relations were ever hostile, oversight ever strong and the system ever
suspected or known (at any state after the start), against the outcome ("reached"); and,
because the "ever" flags hold in nearly every 56-quarter play, the levels of ``oversight``,
``a_known``, ``a_autonomy`` and ``a_control`` at the first state with hostile relations,
against the outcome ("at first hostility").

Added 2026-11-17 on the owner's proposal, before any number under it was computed:
``--policy effort`` draws the moves of ``H`` and ``L`` with probability proportional to the
standard normal density at each action's effort score, so that low-effort plays weigh more
(see :func:`chooser`); the default ``uniform`` reproduces the earlier runs draw for draw.

    PYTHONPATH=. python scripts/agi_v0_1_endings_census.py kernel --ending DISEMPOWERMENT
    PYTHONPATH=. python scripts/agi_v0_1_endings_census.py sample --plays 1000000
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import pickle
import random
import time
from collections import Counter
from pathlib import Path

from models.agi_v0_1 import v0_1

ROOT = Path(__file__).resolve().parents[1]
# ``WF_CENSUS_MODEL=v0.2`` reads AGI v0.2 with its four consequences on instead of v0.1
# (added 2026-11-17 on the owner's question whether the censuses include open weights).
MODEL = os.environ.get("WF_CENSUS_MODEL", "v0.1")
CACHE = ROOT / ".cache" / ("agi_v0_2" if MODEL == "v0.2" else "agi_v0_1")
OUT = ROOT / "reports" / "agi_v0_1_endings_census.json"
P = tuple(v0_1.OBJECTIVE_PROFILES)
# ending -> (the target of its kernel, the name of its store)
KERNELS = {
    "SILENT_TAKEOVER": ("not:SILENT_TAKEOVER", "kernel_HL_not_silent_takeover"),
    "OVERT_TAKEOVER": ("no_overt_takeover", "kernel_HL_no_overt_takeover"),
    "DISEMPOWERMENT": ("not:DISEMPOWERMENT", "kernel_HL_not_disempowerment"),
    "EXTINCTION": ("not:EXTINCTION", "kernel_HL_not_extinction"),
    "STALEMATE": ("not:STALEMATE", "kernel_HL_not_stalemate"),
}
BAD = tuple(KERNELS)


def store(ending: str) -> Path:
    return CACHE / f"{KERNELS[ending][1]}.pkl.gz"


def game():
    if MODEL == "v0.2":
        from models.agi_v0_2 import v0_2

        return v0_2.build().compile(profile=v0_2.OBJECTIVE_PROFILES)
    return v0_1.build().compile(profile=P)


def compute_kernel(ending: str) -> None:
    from tests.agi.common import _dump, heavy_encoding, target_bdd
    from wavefront.symbolic import safe

    cm = game()
    t0 = time.perf_counter()
    enc = heavy_encoding(cm)
    f = safe(enc, ["H", "L"], target_bdd(enc, KERNELS[ending][0])).kernel
    enc.mgr.protect(f)
    rec = _dump(enc, f)
    CACHE.mkdir(parents=True, exist_ok=True)
    with gzip.open(store(ending), "wb", compresslevel=3) as fh:
        pickle.dump(rec, fh)
    print(
        f"kernel {ending} stored: {time.perf_counter() - t0:.1f}s nodes {rec['nodes']}", flush=True
    )


def reader(rec: dict, cm):
    """``inside(state)`` for a stored node table (as ``tests.agi.common.Region``)."""
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


def chooser(cm, objective: str, policy: str):
    """``draw(state, rng)``: the joint move of one transition.

    ``uniform``: every actor draws uniformly among its available actions. ``effort``: ``H`` and
    ``L`` draw an available action with probability proportional to the standard normal
    density at its effort score (docs/agi_effort.md; score 0, 1, 2, 3 in the proportions
    1 : 0.61 : 0.14 : 0.011), so that a play's weight falls with the effort it costs them;
    ``A``, ``Clock`` and Nature stay uniform."""
    if policy == "uniform":
        return lambda s, rng: tuple(rng.choice(a) for a in cm.available(s))
    import math

    from tests.agi.effort import CLOSED, scores_for

    tables = scores_for(objective, ("H", "L"))
    scored = [
        (i, [tables[actor.name].get(x.name, CLOSED) for x in actor.actions])
        for i, actor in enumerate(cm.actors)
        if actor.name in tables
    ]
    density = [math.exp(-k * k / 2) for k in range(8)]

    def draw(s, rng):
        avail = cm.available(s)
        move = [rng.choice(a) for a in avail]
        for i, row in scored:
            weights = []
            for j in avail[i]:
                score = row[j]
                if isinstance(score, tuple):
                    score = score[1] if cm.evaluate(score[0], s) else score[2]
                weights.append(density[score])
            move[i] = rng.choices(avail[i], weights)[0]
        return tuple(move)

    return draw


def sample(objective: str, plays: int, seed: int, policy: str = "uniform") -> dict:
    cm = game()
    draw = chooser(cm, objective, policy)
    zones = {}
    for ending in BAD:
        if store(ending).exists():
            with gzip.open(store(ending), "rb") as fh:
                zones[ending] = reader(pickle.load(fh), cm)
    (s0,) = [s for s in cm.initial_states() if cm.state_dict(s)["a_objective"] == objective]
    outside_at_start = [e for e, inside in zones.items() if not inside(s0)]
    no_overt = cm.invariant_fns["no_overt_takeover"]
    horizon = cm.horizon
    rng = random.Random(seed)
    ended: Counter = Counter()  # (outcome, tick)
    overt: Counter = Counter()  # tick of the first overt-takeover state
    exits = {e: Counter() for e in zones}  # tick of the first state outside
    follow = {e: Counter() for e in zones}  # (left the kernel, reached the ending)
    lag = {e: Counter() for e in zones}  # ticks from the exit to the ending
    i_trust, i_over, i_known = cm.index["trust"], cm.index["oversight"], cm.index["a_known"]
    hostile = cm.variables[i_trust].levels.index("hostile")
    strong = cm.variables[i_over].levels.index("strong")
    suspected = cm.variables[i_known].levels.index("suspected")
    reached: Counter = Counter()  # (ever hostile, ever strong, ever suspected, overt, outcome)
    i_auto, i_ctrl = cm.index["a_autonomy"], cm.index["a_control"]
    turned: Counter = Counter()  # (status when relations first turn hostile, overt, outcome)
    t0 = time.perf_counter()
    for _ in range(plays):
        s, t = s0, 0
        first_out = dict.fromkeys(zones, -1)
        overt_at = -1
        was_hostile = was_strong = was_suspected = False
        at_hostile = None
        while not cm.is_terminal(s):
            s = cm.step(s, draw(s, rng))
            t += 1
            if at_hostile is None and s[i_trust] == hostile:
                at_hostile = (s[i_over], s[i_known], s[i_auto], s[i_ctrl])
            was_hostile = was_hostile or s[i_trust] == hostile
            was_strong = was_strong or s[i_over] == strong
            was_suspected = was_suspected or s[i_known] >= suspected
            if overt_at < 0 and not no_overt(s):
                overt_at = t
            for e, inside in zones.items():
                if first_out[e] < 0 and not inside(s):
                    first_out[e] = t
        outcome = cm.ending_of(s) or ""
        if outcome == "HORIZON":
            outcome = ""
        ended[(outcome, t)] += 1
        reached[(was_hostile, was_strong, was_suspected, overt_at >= 0, outcome)] += 1
        if at_hostile is not None:
            turned[(*at_hostile, overt_at >= 0, outcome)] += 1
        if overt_at >= 0:
            overt[overt_at] += 1
        for e in zones:
            hit_at = overt_at if e == "OVERT_TAKEOVER" else (t if outcome == e else -1)
            follow[e][(first_out[e] >= 0, hit_at >= 0)] += 1
            if first_out[e] >= 0:
                exits[e][first_out[e]] += 1
                if hit_at >= 0:
                    lag[e][hit_at - first_out[e]] += 1
    return {
        "model": "agi_v0_2, every consequence on" if MODEL == "v0.2" else "agi_v0_1",
        "objective": objective,
        "policy": policy,
        "plays": plays,
        "seed": seed,
        "horizon": horizon,
        "seconds": round(time.perf_counter() - t0, 1),
        "kernels read": sorted(zones),
        "start outside the kernel of": outside_at_start,
        "ended": sorted([o, t, n] for (o, t), n in ended.items()),
        "overt takeover first seen at": dict(sorted(overt.items())),
        "first outside at": {e: dict(sorted(c.items())) for e, c in exits.items()},
        "left kernel, reached ending": {
            e: {f"{a}/{b}": n for (a, b), n in sorted(c.items())} for e, c in follow.items()
        },
        "ticks from exit to ending": {e: dict(sorted(c.items())) for e, c in lag.items()},
        "reached, columns": [
            "ever hostile",
            "ever strong oversight",
            "ever suspected or known",
            "overt takeover seen",
            "outcome",
            "plays",
        ],
        "reached": sorted([*k, n] for k, n in reached.items()),
        "at first hostility, columns": [
            "oversight",
            "a_known",
            "a_autonomy",
            "a_control",
            "overt takeover seen",
            "outcome",
            "plays",
        ],
        "at first hostility": sorted(
            [
                cm.variables[i_over].levels[k[0]],
                cm.variables[i_known].levels[k[1]],
                cm.variables[i_auto].levels[k[2]],
                cm.variables[i_ctrl].levels[k[3]],
                k[4],
                k[5],
                n,
            ]
            for k, n in turned.items()
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["kernel", "sample"])
    ap.add_argument("--ending", choices=BAD)
    ap.add_argument("--objective", default="self_preserving", choices=v0_1.OBJECTIVES)
    ap.add_argument("--plays", type=int, default=1_000_000)
    ap.add_argument("--seed", type=int, default=20261117)
    ap.add_argument("--policy", default="uniform", choices=["uniform", "effort"])
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    if args.step == "kernel":
        compute_kernel(args.ending)
        return
    result = sample(args.objective, args.plays, args.seed, args.policy)
    args.out.write_text(json.dumps(result) + "\n")
    print(f"{args.plays} plays in {result['seconds']}s -> {args.out}", flush=True)


if __name__ == "__main__":
    main()
