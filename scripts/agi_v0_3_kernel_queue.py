"""The kernels of the v0.3 claims F3, F4, F6 and F7, computed one start objective at a time
and saved to reports/agi_v0_3_kernels.jsonl (tests/agi_v0_3/kernels.py).

The claim files read the saved readings back, so this queue can run before them and in
pieces: a kernel that goes over the memory or time limit is recorded as such and is computed
again the next time the queue (or a claim file) asks, for example under a larger limit. The
order is the cheap ones first: the variant without the open system, then the registered
variant, the two quick objectives before the two slow ones. Only a line per kernel is
printed: what was asked, and the reading or the limit it went over.

    WF_V03_MEMORY_GB=23 PYTHONPATH=. python scripts/agi_v0_3_kernel_queue.py
"""

from __future__ import annotations

import os
import sys

from tests.agi.common import NotComputed
from tests.agi_v0_3.common import CLOSED, DEFAULT
from tests.agi_v0_3.kernels import MEMORY_GB, membership

H, HL = ("H",), ("H", "L")
ORDER = ("aligned", "truth_seeking", "indifferent", "self_preserving")
# (claim, build name, build, coalition, target, profiles, levels)
F7 = [
    (H, "balance_control", {}),
    (HL, "balance_control", {}),
    (HL, "not:SILENT_TAKEOVER", {}),
    (H, "balance_coexist", {"cap": "agi"}),
]
QUEUE = [("F7", "closed", CLOSED, c, t, (), lv) for c, t, lv in F7]
QUEUE += [
    ("F3", "default", DEFAULT, H, "not:OPEN_TAKEOVER", (), {}),
    ("F6", "default", DEFAULT, HL, "balance_control", (), {}),
    ("F4", "default", DEFAULT, H, "not:OPEN_TAKEOVER", ("no_treaty",), {}),
    ("F4", "default", DEFAULT, HL, "not:OPEN_TAKEOVER", ("no_treaty",), {}),
    ("F6", "default", DEFAULT, HL, "balance_control", ("no_nationalize",), {}),
]
QUEUE += [("F7", "default", DEFAULT, c, t, (), lv) for c, t, lv in F7 if (c, t) != (HL, F7[1][1])]


def main() -> None:
    # ``--goal X`` runs one start objective only, so that several queues can share the machine.
    only = sys.argv[sys.argv.index("--goal") + 1 :][:1] if "--goal" in sys.argv else []
    # ``--start N`` skips the first N zones of the list (a second worker on one goal).
    start = int(sys.argv[sys.argv.index("--start") + 1]) if "--start" in sys.argv else 0
    # The console reads this line to know each worker's memory limit.
    print(f"=== worker pid={os.getpid()} goal={(only or ['all'])[0]} limit={MEMORY_GB}", flush=True)
    for objective in only or ORDER:
        for claim, name, build, coalition, target, profiles, levels in QUEUE[start:]:
            what = (
                f"{claim} {name} {'+'.join(coalition)} {target} {' '.join(profiles)} {levels or ''}"
            )
            try:
                got = membership(build, coalition, target, profiles, only=(objective,), **levels)
            except NotComputed as exc:
                print(f"{what} | {objective} | not computed: {exc}", flush=True)
            else:
                inside = "inside" if got["inside"][objective] else "outside"
                print(
                    f"{what} | {objective} | {inside} | {got['seconds'][objective]} s", flush=True
                )
    print("QUEUE_DONE", flush=True)


if __name__ == "__main__":
    main()
