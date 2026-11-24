"""Recompute saved readings of the registered v0.3 build on another engine and compare them
with the saved ones (docs/engine_multicore.md section 5, item 5 of the design's correctness
plan). The engine is the harness's (``WF_V03_CORE``, ``WF_V03_THREADS``, ``WF_V03_STEP``,
``WF_V03_ORDER``, ``WF_V03_MEMORY_GB``); the new readings go to ``WF_V03_READINGS``, which
must name another file than the saved readings, so nothing is read back from them.

    WF_V03_CORE=sylvan WF_V03_THREADS=12 WF_V03_STEP=split WF_V03_MEMORY_GB=11 \\
      WF_V03_READINGS=.bench/recheck.jsonl python -m tests.agi_v0_3.recheck_sylvan [NAME ...]

Without names, every question of :data:`QUESTIONS` is run, one at a time.
"""

from __future__ import annotations

import json
import sys

from tests.agi.common import NotComputed
from tests.agi_v0_3 import kernels
from tests.agi_v0_3.common import DEFAULT, ROOT, key

SAVED = ROOT / "reports" / "agi_v0_3_kernels.jsonl"

# name: (coalition, target, profiles, levels, start objective). The first ones are cheap on
# the own core (under a minute in production); the last two are the zones of the design's
# item 5 (the second needs more than 12 GB with the present step, a few GB with the split
# step and the sifted order).
QUESTIONS = {
    "HL_not_silent_aligned": (["H", "L"], "not:SILENT_TAKEOVER", (), {}, "aligned"),
    "HL_not_silent_truth": (["H", "L"], "not:SILENT_TAKEOVER", (), {}, "truth_seeking"),
    "H_coexist_agi_indifferent": (["H"], "balance_coexist", (), {"cap": "agi"}, "indifferent"),
    "H_coexist_agi_aligned": (["H"], "balance_coexist", (), {"cap": "agi"}, "aligned"),
    "H_coexist_agi_truth": (["H"], "balance_coexist", (), {"cap": "agi"}, "truth_seeking"),
    "H_coexist_agi_selfpres": (["H"], "balance_coexist", (), {"cap": "agi"}, "self_preserving"),
    "H_not_open_no_treaty_aligned": (["H"], "not:OPEN_TAKEOVER", ("no_treaty",), {}, "aligned"),
    "HL_control_aligned": (["H", "L"], "balance_control", (), {}, "aligned"),
}


def saved_reading(coalition, target, profiles, levels, objective) -> bool | None:
    """The saved reading of the question on the present model, whatever engine made it."""
    spec = key(DEFAULT, profiles)
    asked = [json.loads(spec), list(coalition), target, sorted(levels.items()), objective]
    question = json.dumps(["membership", *asked], sort_keys=True)
    now = kernels.stamp()
    found = None
    with SAVED.open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if row["question"] == question and row["model"] == now and row["kind"] == "ok":
                found = row["reading"]["inside"][objective]
    return found


def main(names: list[str]) -> int:
    if kernels.READINGS.resolve() == SAVED.resolve():
        raise SystemExit("set WF_V03_READINGS to another file")
    disagree = 0
    for name in names or list(QUESTIONS):
        coalition, target, profiles, levels, objective = QUESTIONS[name]
        want = saved_reading(coalition, target, profiles, levels, objective)
        try:
            got = kernels.membership(
                DEFAULT, coalition, target, profiles, only=[objective], **levels
            )
            inside, seconds = got["inside"][objective], got["seconds"][objective]
            verdict = "agrees" if inside == want else "DISAGREES"
            disagree += inside != want
        except NotComputed as exc:
            inside, seconds, verdict = None, None, f"not computed: {exc}"
        print(
            json.dumps(
                {"name": name, "saved": want, "now": inside, "seconds": seconds, "verdict": verdict}
            ),
            flush=True,
        )
    return 1 if disagree else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
