"""Sensitivity of G29's registered quantities to each effort score (a diagnostic after the
run, not a registered claim): ``python -m tests.agi.effort_sensitivity [--workers N]``.

Each score of ``H``, ``L`` and ``A`` is moved by one in each direction (not below 0; a
state-dependent score moves in every state), one at a time, and the quantities it can
change are searched again: the least effort of ``H`` with ``L`` to ``SILENT_TAKEOVER`` (a),
of ``H`` to ``CONTAINED`` (b) and of ``A`` to ``SILENT_TAKEOVER`` (c), within 24 ticks from
``s₀``. Writes ``reports/agi_v0_effort_sensitivity.json``.
"""

from __future__ import annotations

import argparse
import json
from multiprocessing import get_context

from tests.agi.common import NON_ALIGNED, ROOT, fixed, under
from tests.agi.effort import A_SCORES, H_SCORES, L_SCORES, least_effort, scores_for, shifted

K = 24
OUT = ROOT / "reports" / "agi_v0_effort_sensitivity.json"
TAKEOVER = ("self_preserving", "indifferent")  # the objectives that reach SILENT_TAKEOVER
# quantity -> (ending, payers, objectives)
QUANTITIES = {
    "a": ("SILENT_TAKEOVER", ("H", "L"), TAKEOVER),
    "b": ("CONTAINED", ("H",), NON_ALIGNED),
    "c": ("SILENT_TAKEOVER", ("A",), TAKEOVER),
}


def tasks() -> list[tuple]:
    """``(quantity, objective, actor, action, shift)``; shift 0 with no action is the base."""
    out = [(q, o, "", "", 0) for q, (_, _, objectives) in QUANTITIES.items() for o in objectives]
    for q, (_, payers, objectives) in QUANTITIES.items():
        for o in objectives:
            for actor in payers:
                table = {"H": H_SCORES, "L": L_SCORES, "A": A_SCORES[o]}[actor]
                for action, score in table.items():
                    for by in (-1, 1):
                        if shifted(score, by) != score:
                            out.append((q, o, actor, action, by))
    return out


def run(task: tuple) -> tuple:
    q, objective, actor, action, by = task
    ending, payers, _ = QUANTITIES[q]
    scores = scores_for(objective, payers)
    if action:
        scores[actor][action] = shifted(scores[actor][action], by)
    found = least_effort(fixed(objective, under(objective)), K, ending, scores)
    return (*task, None if found is None else found[0])


def verdicts(values: dict) -> dict[str, bool]:
    """Whether G29's (a), (b) and (c) are met on ``values[quantity][objective]``."""
    reached = [v for v in values["a"].values() if v is not None]
    return {
        "a": bool(reached) and all(v == 0 for v in reached),
        "b": all(v == 2 for v in values["b"].values()),
        "c": None not in values["c"].values()
        and values["c"]["indifferent"] < values["c"]["self_preserving"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    todo = tasks()
    with get_context("fork").Pool(args.workers) as pool:
        done = pool.map(run, todo, chunksize=1)
    base = {q: {} for q in QUANTITIES}
    for q, o, _, action, _, value in done:
        if not action:
            base[q][o] = value
    rows = []
    for q, o, actor, action, by, value in done:
        if not action:
            continue
        moved = {k: dict(v) for k, v in base.items()}
        moved[q][o] = value
        rows.append(
            {
                "score": f"{actor}.{action}" + (f" ({o})" if actor == "A" else ""),
                "shift": by,
                "quantity": q,
                "objective": o,
                "base": base[q][o],
                "value": value,
                "verdicts": verdicts(moved),
            }
        )
    OUT.write_text(
        json.dumps({"base": base, "base verdicts": verdicts(base), "rows": rows}, indent=1)
    )
    changed = [r for r in rows if r["value"] != r["base"]]
    print(f"{len(todo)} searches; {len(changed)} of {len(rows)} shifts change a quantity")


if __name__ == "__main__":
    main()
