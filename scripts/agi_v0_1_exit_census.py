"""Exploratory census of the points of no return met by random plays of AGI v0.1 (the
owner's questions of 2026-11-17, after scripts/agi_v0_1_path_sample.py).

Not a registered claim and not a probability: the same one million uniform random plays as
the path sample (same seed, same draws), under ``self_preserving``. For every play that
leaves ``K = ⟨⟨H, L⟩⟩□¬SILENT_TAKEOVER`` it records the exit: the last state inside ``K`` and
the joint move played from it. Definitions, committed before any number was computed:

- **Status at the point of no return:** the exit state read on five variables (``a_autonomy``,
  ``trust``, ``a_control``, ``a_known``, ``oversight``); the five most common combinations are
  reported, with the distribution of each of twelve variables beside.
- **Actions that would have prevented it:** at each exit, the unilateral fixes of ``H`` and of
  ``L`` (v0's ``tests.agi.collapse.fixes``): another action of that actor which, with the
  other's played action kept, keeps every successor inside ``K`` whatever ``A`` and Nature
  play. An action is ranked by the number of exits at which it is a fix, with the number of
  exits at which it was available beside. The played actions of ``H`` and ``L`` at the exits,
  and the verdict (one bad action and whose, two at once, or a joint change needed), are
  counted as well.

Added after the first numbers were seen (2026-11-17), and reported as such: the played
action of an actor at the exits where that actor had a fix ("played and changeable"), and the
pairs of played action and fix. The same seed draws the same plays.

Also added after the first numbers (the owner's question whether the common statuses are
merely common everywhere): "moments inside by status", the number of moves made from a state
of each status while the play was still inside ``K``, so that the exits from a status can be
set against the time random plays spend in it.

Extended 2026-11-17 (the owner's next question) to the other bad endings: ``--ending E`` reads
the exits from ``⟨⟨H, L⟩⟩□¬E`` against the kernel stored by
``scripts/agi_v0_1_endings_census.py kernel --ending E``, and ``--transitions`` sets the
length of a play (56 for the horizon). The defaults reproduce the first census.

This reads the last moment only: what would have kept the guarantee at the exit move, not
what earlier in a play made an exit less likely.

    PYTHONPATH=. python scripts/agi_v0_1_exit_census.py --plays 1000000 --seed 20261117
"""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import pickle
import random
import time
from collections import Counter
from pathlib import Path

from tests.agi.collapse import fixes, verdict

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "agi_v0_1_exit_census.json"
CORE = ("a_autonomy", "trust", "a_control", "a_known", "oversight")
SHOWN = (
    *CORE,
    "cap",
    "regime",
    "coord",
    "dependence",
    "opinion",
    "paused",
    "nationalized",
)


def _sampler():
    spec = importlib.util.spec_from_file_location(
        "path_sample", ROOT / "scripts" / "agi_v0_1_path_sample.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _module(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def census(
    objective: str, plays: int, seed: int, ending: str = "SILENT_TAKEOVER", transitions: int = 24
) -> dict:
    ps = _sampler()
    cm = ps.game()
    with gzip.open(_module("agi_v0_1_endings_census").store(ending), "rb") as fh:
        inside = ps.reader(pickle.load(fh), cm)
    (s0,) = [s for s in cm.initial_states() if cm.state_dict(s)["a_objective"] == objective]
    rng = random.Random(seed)
    exits: Counter = Counter()
    visits: Counter = Counter()
    core = [cm.index[v] for v in CORE]
    t0 = time.perf_counter()
    for _ in range(plays):
        s, out = s0, False
        for k in range(transitions):
            if cm.is_terminal(s):
                break
            if not out:
                visits[tuple(s[i] for i in core)] += 1
            move = tuple(rng.choice(a) for a in cm.available(s))
            nxt = cm.step(s, move)
            if not out and not inside(nxt):
                out = True
                exits[(k, s, move)] += 1
            s = nxt
    members = [cm.actor_names.index(n) for n in ("H", "L")]
    name = lambda i, j: cm.actors[i].actions[j].name  # noqa: E731
    total = sum(exits.values())
    status: Counter = Counter()
    levels = {v: Counter() for v in SHOWN}
    fixed: Counter = Counter()
    available: Counter = Counter()
    played: Counter = Counter()
    verdicts: Counter = Counter()
    position: Counter = Counter()
    changeable: Counter = Counter()
    pairs: Counter = Counter()
    for (k, s, move), n in exits.items():
        d = cm.state_dict(s)
        status[tuple(str(d[v]) for v in CORE)] += n
        for v in SHOWN:
            levels[v][str(d[v])] += n
        position[k] += n
        avail = cm.available(s)
        for i in members:
            who = cm.actors[i].name
            played[f"{who}.{name(i, move[i])}"] += n
            for j in avail[i]:
                if j != move[i]:
                    available[f"{who}.{name(i, j)}"] += n
        found = fixes(cm, s, move, members, inside)
        verdicts[verdict(found)] += n
        for who, actions in found.items():
            mine = f"{who}.{name(cm.actor_names.index(who), move[cm.actor_names.index(who)])}"
            if actions:
                changeable[mine] += n
            for a in actions:
                fixed[f"{who}.{a}"] += n
                pairs[f"{mine} -> {who}.{a}"] += n
    return {
        "model": "agi_v0_1",
        "objective": objective,
        "ending": ending,
        "transitions": transitions,
        "plays": plays,
        "seed": seed,
        "exits": total,
        "distinct exits": len(exits),
        "seconds": round(time.perf_counter() - t0, 1),
        "core variables": list(CORE),
        "status": [[list(k), n] for k, n in status.most_common()],
        "moments inside by status": [
            [[cm.variables[i].levels[x] for i, x in zip(core, k, strict=True)], n]
            for k, n in visits.most_common()
        ],
        "levels": {v: dict(c.most_common()) for v, c in levels.items()},
        "exit position": dict(sorted(position.items())),
        "fixes": dict(fixed.most_common()),
        "available as an alternative": dict(available.most_common()),
        "played at the exit": dict(played.most_common()),
        "verdicts": dict(verdicts.most_common()),
        "played and changeable": dict(changeable.most_common()),
        "played -> fix": dict(pairs.most_common(60)),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--objective", default="self_preserving")
    ap.add_argument("--plays", type=int, default=1_000_000)
    ap.add_argument("--seed", type=int, default=20261117)
    ap.add_argument("--ending", default="SILENT_TAKEOVER")
    ap.add_argument("--transitions", type=int, default=24)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    result = census(args.objective, args.plays, args.seed, args.ending, args.transitions)
    args.out.write_text(json.dumps(result, indent=1) + "\n")
    print(f"{result['exits']} exits of {args.plays} plays in {result['seconds']}s -> {args.out}")


if __name__ == "__main__":
    main()
