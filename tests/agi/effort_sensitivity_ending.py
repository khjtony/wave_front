"""How the least joint effort of ``H`` and ``L`` to one ending moves when each of their scores
is raised by one (a diagnostic, not a registered claim):
``python -m tests.agi.effort_sensitivity_ending [ENDING] [OBJECTIVE]``.

Written after G29 reported ``DISEMPOWERMENT`` at effort 0, to say which scores that zero
rests on. Writes ``reports/agi_v0_effort_sensitivity_<ending>.json``.
"""

from __future__ import annotations

import json
import sys
from multiprocessing import get_context

from tests.agi.common import ROOT, fixed, under
from tests.agi.effort import H_SCORES, L_SCORES, least_effort, scores_for, shifted

K = 24
ENDING = sys.argv[1] if len(sys.argv) > 1 else "DISEMPOWERMENT"
OBJECTIVE = sys.argv[2] if len(sys.argv) > 2 else "self_preserving"


def run(task: tuple[str, str]) -> dict:
    actor, action = task
    scores = scores_for(OBJECTIVE, ("H", "L"))
    if action:
        scores[actor][action] = shifted(scores[actor][action], 1)
    found = least_effort(fixed(OBJECTIVE, under(OBJECTIVE)), K, ENDING, scores)
    return {
        "score": f"{actor}.{action}" if action else "base",
        "shift": 1 if action else 0,
        "least effort of H with L": None if found is None else found[0],
        "ticks": None if found is None else len(found[2]),
    }


def main() -> None:
    tasks = [("", ""), *(("H", a) for a in H_SCORES), *(("L", a) for a in L_SCORES)]
    with get_context("fork").Pool(10) as pool:
        rows = pool.map(run, tasks, chunksize=1)
    out = ROOT / "reports" / f"agi_v0_effort_sensitivity_{ENDING.lower()}.json"
    out.write_text(json.dumps({"objective": OBJECTIVE, "ending": ENDING, "rows": rows}, indent=1))
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
