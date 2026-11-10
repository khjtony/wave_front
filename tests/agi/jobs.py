"""The first-sight job runner: ``python -m tests.agi.jobs [--workers N] [--minutes M]
[--memory-gb G]``.

Collects the ``JOBS`` lists of ``tests/agi/scenarios/test_G*.py``, and computes every job
that is not in the cache, each in its own process with a time budget and an address-space
cap (a storyline or forced-distance job gets ``BUDGET_FACTOR`` times the budget). A job over
its budget or its cap leaves a ``.failed.json`` record, and the claim parts that need it read
"not computed". One line per job goes to standard output: label, seconds, nodes, peak.

The run is resumable and runs each job once: a job with a result or a failure record is left
alone on a second invocation (``--retry`` runs the failed ones again, which the first sight
does not do on one machine; a pass on a larger machine, with a higher ``--memory-gb``, is how
the jobs lost to the cap are computed: docs/agi_v0_decisions.md section 2). The one exception
is a job whose process the machine killed (signal 9: the
machine's memory, neither the job's budget nor its cap); it is run once more, alone, after
the others.
``--list`` prints the jobs without running any.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import pickle
import resource
import signal
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from tests.agi import common
from tests.agi.common import Job
from wavefront.symbolic import cores

SCENARIOS = Path(__file__).resolve().parent / "scenarios"
MEMORY_GB = 9  # the cap on a fixpoint, unless --memory-gb names another
WRITE_GB = 3  # room above the cap to write a finished region out (common._room_to_write)
# A storyline job is a sequence of attractors, one per waypoint, and a forced-distance job a
# kernel and then up to twelve layers, so each gets a longer budget than a single fixpoint
# (docs/agi_v0_decisions.md section 3: set on a timing probe that printed seconds and peak
# only, and on the count of fixpoints for the forced distances).
BUDGET_FACTOR = {"chain": 3.0, "rank": 3.0}


def collect() -> list[Job]:
    """Every registered job, in file order, without duplicates."""
    jobs: dict[Job, None] = {}
    for path in sorted(SCENARIOS.glob("test_G*.py")):
        mod = importlib.import_module(f"tests.agi.scenarios.{path.stem}")
        for job in getattr(mod, "JOBS", ()):
            jobs[job] = None
    return list(jobs)


def _child(blob: str, memory_gb: int) -> None:
    cap = memory_gb << 30
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap + (WRITE_GB << 30)))
    try:  # if the machine runs out of memory a job goes first, not the runner
        Path("/proc/self/oom_score_adj").write_text("500")
    except OSError:
        pass
    print(json.dumps(common.run(pickle.loads(bytes.fromhex(blob)))))


def _fail(job: Job, reason: str, seconds: float) -> str:
    common.failure_path(job).write_text(json.dumps({"reason": reason, "seconds": seconds}))
    return f"NOT COMPUTED {job.label}: {reason} after {seconds}s"


def _one(
    job: Job, minutes: float, retry: bool, alone: bool = False, memory_gb: int = MEMORY_GB
) -> tuple[str, bool]:
    """The log line of ``job``, and whether it is to be run again alone."""
    t0 = time.perf_counter()

    def seconds() -> float:
        return round(time.perf_counter() - t0, 1)

    try:
        if job.path.exists():
            return f"cached   {job.label}", False
        failed = common.failure_path(job)
        if failed.exists():
            if not retry:
                why = json.loads(failed.read_text())["reason"]
                return f"left     {job.label}: {why}", False
            failed.unlink()
        minutes *= BUDGET_FACTOR.get(job.kind, 1.0)
        done = subprocess.run(
            [
                sys.executable,
                "-m",
                "tests.agi.jobs",
                "--memory-gb",
                str(memory_gb),
                "--child",
                pickle.dumps(job).hex(),
            ],
            timeout=minutes * 60,
            capture_output=True,
            text=True,
            check=False,
        )
        if done.returncode == -signal.SIGKILL and not alone:
            return f"killed   {job.label}: by the machine after {seconds()}s; again alone", True
        if done.returncode < 0:
            return _fail(job, f"killed by signal {-done.returncode}", seconds()), False
        if done.returncode != 0:
            tail = (done.stderr.strip().splitlines() or ["no output"])[-1]
            return _fail(job, f"failed ({tail[:120]}; cap {memory_gb} GB)", seconds()), False
        cost = json.loads(done.stdout.strip().splitlines()[-1])
        return (
            f"done     {job.label}: {cost['seconds']}s nodes {cost['nodes']}"
            f" peak {cost['peak_nodes']} core {cost['core']}",
            False,
        )
    except subprocess.TimeoutExpired:
        return _fail(job, f"over the budget of {minutes:g} minutes", seconds()), False
    except Exception as exc:  # one job's accident does not stop the others
        try:
            return _fail(job, f"runner error {exc!r}"[:200], seconds()), False
        except OSError:
            return f"NOT COMPUTED {job.label}: runner error {exc!r}, and no record written", False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--minutes", type=float, default=25)
    ap.add_argument("--memory-gb", type=int, default=MEMORY_GB, help="the cap on a fixpoint")
    ap.add_argument("--retry", action="store_true", help="run the jobs with a failure record")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--child")
    args = ap.parse_args()
    if args.child:
        _child(args.child, args.memory_gb)
        return
    jobs = collect()
    if args.list:
        for job in jobs:
            print(job.key, "cached" if job.path.exists() else "      ", job.label)
        print(len(jobs), "jobs, cache", common.CACHE)
        return
    if not cores.c_available() or (os.environ.get(cores.ENV) or "c").strip().lower() != "c":
        sys.exit(
            f"the compiled BDD core is not in use ({cores.c_import_error() or cores.ENV}):"
            " no job is run on the reference core"
        )
    common.CACHE.mkdir(parents=True, exist_ok=True)
    print(
        f"{len(jobs)} jobs, cache {common.CACHE}, {args.workers} at a time,"
        f" {args.minutes:g} minutes, cap {args.memory_gb} GB",
        flush=True,
    )
    lines, again = [], []
    with ThreadPoolExecutor(args.workers) as pool:
        results = pool.map(
            lambda j: _one(j, args.minutes, args.retry, memory_gb=args.memory_gb), jobs
        )
        for job, (line, rerun) in zip(jobs, results, strict=True):
            print(line, flush=True)
            lines.append(line)
            if rerun:
                again.append(job)
    for job in again:
        line, _ = _one(job, args.minutes, args.retry, alone=True, memory_gb=args.memory_gb)
        print(line, flush=True)
        lines.append(line)
    print("finished:", dict(Counter(line.split()[0] for line in lines)), flush=True)


if __name__ == "__main__":
    main()
