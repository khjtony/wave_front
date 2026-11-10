"""Render the first-sight record of the AGI claims as Markdown tables.

Reads ``reports/agi_v0_first_sight_parts.jsonl`` (one row per claim part, written by
``tests/agi/common.Parts`` at first sight) and the job cache, and prints

- one line per claim: parts met, not met, not computed, reported;
- one table per claim: part, outcome, detail;
- the job table: label, build, seconds, peak nodes, or the reason a job was not computed.

It computes nothing: a job that is not in the cache is listed as not run.

    PYTHONPATH=. python scripts/agi_first_sight_tables.py > reports/agi_v0_first_sight_tables.md
"""

from __future__ import annotations

import json
import re
from collections import Counter

from tests.agi import common, jobs

OUTCOMES = ("met", "not met", "not computed", "reported")


def cell(text: object, limit: int = 600) -> str:
    flat = re.sub(r"\s+", " ", str(text)).replace("|", "\\|")
    return flat if len(flat) <= limit else flat[: limit - 1] + "…"


def claim_number(name: str) -> int:
    return int(re.sub(r"\D", "", name) or 0)


def parts() -> dict[str, list[dict]]:
    by_claim: dict[str, list[dict]] = {}
    if common.PARTS_LOG.exists():
        for line in common.PARTS_LOG.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            by_claim.setdefault(row["claim"], []).append(row)
    return dict(sorted(by_claim.items(), key=lambda kv: claim_number(kv[0])))


def main() -> None:
    by_claim = parts()
    print("# AGI v0 first sight: parts and jobs\n")
    print("| Claim | " + " | ".join(OUTCOMES) + " |")
    print("|---|" + "---|" * len(OUTCOMES))
    for claim, rows in by_claim.items():
        count = Counter(r["outcome"] for r in rows)
        print(f"| {claim} | " + " | ".join(str(count.get(o, 0)) for o in OUTCOMES) + " |")
    for claim, rows in by_claim.items():
        print(f"\n## {claim}\n")
        print("| Part | Outcome | Detail |")
        print("|---|---|---|")
        for r in rows:
            print(f"| {cell(r['part'])} | {r['outcome']} | {cell(r['detail'])} |")
    print("\n## Jobs\n")
    print("| Job | Seconds | Peak nodes | Status |")
    print("|---|---|---|---|")
    for job in jobs.collect():
        failed = common.failure_path(job)
        if job.path.exists():
            rec = common.record(job)
            print(f"| {cell(job.label)} | {rec['seconds']} | {rec['peak_nodes']} | computed |")
        elif failed.exists():
            rec = json.loads(failed.read_text())
            print(f"| {cell(job.label)} | {rec['seconds']} | - | {cell(rec['reason'])} |")
        else:
            print(f"| {cell(job.label)} | - | - | not run |")


if __name__ == "__main__":
    main()
