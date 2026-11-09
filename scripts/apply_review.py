"""Apply a filled review sheet to a copy of a replay's proposals, then re-measure.

The sheet is ``review_sample.csv`` (``scripts/build_review_sample.py``) with its ``decision``
column (``accept`` or ``reject``) and ``note`` column filled by the reviewer. The proposals
directory of the run (default ``reports/replay_ww2_frus_claude/proposals``) is never changed:
it is copied to ``OUT/proposals`` (default ``~/wf_runs/frus_claude_reviewed``), every decision
is recorded there with ``wf review FILE --accept|--reject IDS --note NOTE --reviewer NAME``
(file by file in quarter order, the acceptances of a file before its rejections), and the
metrics are computed on the copy:

* ``OUT/metrics_partial.md``: ``wf replay --measure-proposals --drop-rejected``, the measure of
  a partly reviewed run (rejected proposals left out, accepted and pending ones counted);
* ``OUT/metrics_reviewed.md``: ``wf replay --metrics-only``, from the reviewed snapshots only;
  it compares a quarter only once every proposal up to it is decided, so with a sample it
  compares nothing (kept for the record).

Every row must carry a valid decision and a note; a row with an empty decision is refused
unless ``--skip-blank`` (it then stays pending). An acceptance that the harness rules refuse (a
proposal held, at its own quarter, as the only document so far, or blocked) is left pending
and listed: under ``--drop-rejected`` a pending proposal counts exactly as an accepted one
would. Any other failure stops the run before the metrics. Example::

    python scripts/apply_review.py reports/replay_ww2_frus_claude/review_sample_filled.csv \\
        --out ~/wf_runs/frus_claude_reviewed --reviewer owner
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import getpass
import io
import shutil
import sys
from pathlib import Path

from wavefront.cli import main as wf

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "reports" / "replay_ww2_frus_claude"
DECISIONS = {"accept": "--accept", "reject": "--reject"}
HARNESS_REFUSAL = "cannot be accepted under the harness rules"


def read_sheet(path: Path, skip_blank: bool) -> tuple[list[dict[str, str]], list[str]]:
    """The decided rows of the sheet, and the problems that refuse it."""
    rows, problems, seen = [], [], set()
    with path.open(encoding="utf-8", newline="") as fh:
        for n, row in enumerate(csv.DictReader(fh), start=2):
            pid = (row.get("id") or "").strip()
            file = (row.get("file") or "").strip()
            decision = (row.get("decision") or "").strip().lower()
            note = (row.get("note") or "").strip()
            if not pid or not file:
                problems.append(f"line {n}: no id or file")
                continue
            if pid in seen:
                problems.append(f"line {n}: {pid} appears twice")
                continue
            seen.add(pid)
            if not decision:
                if not skip_blank:
                    problems.append(
                        f"line {n}: {pid} has no decision (use --skip-blank to leave it)"
                    )
                continue
            if decision not in DECISIONS:
                problems.append(f"line {n}: {pid}: decision {decision!r} is not accept or reject")
                continue
            if not note:
                problems.append(f"line {n}: {pid}: a note is required with every decision")
                continue
            rows.append({"id": pid, "file": file, "decision": decision, "note": note})
    return rows, problems


def run_wf(args: list[str]) -> tuple[int, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = wf(args)
    return code, out.getvalue() + err.getvalue()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sheet", type=Path, help="the filled review sheet (CSV)")
    ap.add_argument(
        "--proposals",
        type=Path,
        default=RUN / "proposals",
        help="the run's proposals directory, copied and never changed (default: %(default)s)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("~/wf_runs/frus_claude_reviewed").expanduser(),
        help="directory of the reviewed copy and the reports (default: %(default)s)",
    )
    ap.add_argument("--replace", action="store_true", help="replace an existing OUT/proposals")
    ap.add_argument("--reviewer", default=None, help="reviewer name (default: the login name)")
    ap.add_argument("--skip-blank", action="store_true", help="leave undecided rows pending")
    ap.add_argument("--quarters", default="1936Q1..1940Q4")
    ap.add_argument("--report", type=Path, help="default: OUT/metrics_partial.md")
    ap.add_argument("--title", default="Replay metrics, FRUS 1936 to 1940, Claude backend")
    args = ap.parse_args(argv)

    rows, problems = read_sheet(args.sheet, args.skip_blank)
    source = args.proposals.resolve()
    target = (args.out / "proposals").resolve()
    if target == source or source in target.parents or target in source.parents:
        problems.append(f"{target}: the copy must not be, or overlap, {source}")
    for row in rows:
        if Path(row["file"]).name != row["file"].removeprefix("proposals/"):
            problems.append(f"{row['id']}: file {row['file']!r} is not proposals/<quarter>.json")
        elif not (source / Path(row["file"]).name).exists():
            problems.append(f"{row['id']}: no file {row['file']} in {source}")
    if target.exists() and not args.replace:
        problems.append(f"{target} exists: give --replace to start again from a fresh copy")
    if problems:
        print("refused:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2

    if target.exists():
        shutil.rmtree(target)
    args.out.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)
    reviewer = args.reviewer or getpass.getuser()

    # Group by file (quarter order), then acceptances before rejections, then the note.
    groups: dict[tuple[str, str, str], list[str]] = {}
    for row in rows:
        key = (Path(row["file"]).name, row["decision"], row["note"])
        groups.setdefault(key, []).append(row["id"])
    order = sorted(groups, key=lambda k: (k[0], k[1] != "accept"))
    left_pending: list[str] = []
    done = {"accept": 0, "reject": 0}
    for name, decision, note in order:
        path = str(target / name)
        common = ["--note", note, "--reviewer", reviewer]
        ids = groups[(name, decision, note)]
        code, text = run_wf(["review", path, DECISIONS[decision], ",".join(ids), *common])
        if code == 0:
            done[decision] += len(ids)
            continue
        if decision != "accept" or HARNESS_REFUSAL not in text:
            print(
                f"stopped: wf review {name} {DECISIONS[decision]} {ids}:\n{text}", file=sys.stderr
            )
            return 1
        for pid in ids:  # one at a time, to find the ones the rules refuse
            code, text = run_wf(["review", path, "--accept", pid, *common])
            if code == 0:
                done["accept"] += 1
            elif HARNESS_REFUSAL in text:
                left_pending.append(f"{pid} ({name}): {text.strip()}")
            else:
                print(f"stopped: wf review {name} --accept {pid}:\n{text}", file=sys.stderr)
                return 1
    print(f"copy: {target}")
    print(f"recorded as {reviewer}: {done['accept']} accepted, {done['reject']} rejected")
    if left_pending:
        print(f"left pending ({len(left_pending)}), the harness rules refuse their acceptance:")
        for line in left_pending:
            print(f"  {line}")

    out = str(args.out)
    report = args.report or args.out / "metrics_partial.md"
    base = ["replay", "--out", out, "--quarters", args.quarters]
    code, text = run_wf(
        [
            *base,
            "--measure-proposals",
            "--drop-rejected",
            "--report",
            str(report),
            "--title",
            f"{args.title}, reviewed sample, rejected proposals dropped",
        ]
    )
    if code:
        print(f"stopped: the measurement failed:\n{text}", file=sys.stderr)
        return 1
    print(f"re-measure (--measure-proposals --drop-rejected): {report}")
    reviewed = args.out / "metrics_reviewed.md"
    code, text = run_wf(
        [*base, "--metrics-only", "--report", str(reviewed), "--title", f"{args.title}, reviewed"]
    )
    if code:
        print(f"stopped: --metrics-only failed:\n{text}", file=sys.stderr)
        return 1
    print(f"--metrics-only (reviewed snapshots only): {reviewed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
