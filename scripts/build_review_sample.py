"""Build the review sample of the Claude backend's FRUS replay (owner's decision 7a, 2026-10-23).

Reads the proposals of a replay directory (default ``reports/replay_ww2_frus_claude``) without
changing them and writes ``review_sample.md`` and ``review_sample.csv`` beside them. The sample:

* (a) the proposals that set a level in a documented flip (every row of the flips table with a
  documented flip): the proposal the measurement dated the replayed flip by and, for a
  variable under the ``two-document`` rule, the first document it needed;
* (b) the same for the false flips;
* (c) the proposals behind each disagreeing quarter: the indicators of the replay level at
  every quarter that disagrees with the hindsight snapshot (the proposal that set the level
  and the latest confirming one) and every other proposal of that replayed level for that
  variable dated within the run of disagreement and read by its end (so a rejection is not silently
  replaced by the next pending proposal of the same level), and, where the replay level is
  the assumed initial one, the proposals of the hindsight level read by then;
* (d) a random sample of the remaining proposals counted by the measurement (not held,
  blocked or ``retrospective?``), stratified by quarter (proportional allocation, largest
  remainder, seed fixed).

A proposal in several categories is listed once, under the first. Nothing is decided here.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
from collections import Counter
from datetime import date
from pathlib import Path

from wavefront.evidence.harness_rules import (
    BLOCKED,
    CORROBORATING,
    HELD,
    RETROSPECTIVE,
    record_key,
)
from wavefront.evidence.replay import (
    _qindex,
    compare,
    measured_snapshots,
    parse_quarters,
    quarter_end,
)
from wavefront.evidence.review import (
    DEFAULT_HINDSIGHT,
    directory_rules,
    proposal_files,
    review_gating,
)

ROOT = Path(__file__).resolve().parent.parent
BC = ("belief_WEST", "belief_GER", "commit_WEST", "commit_US")
PROPOSAL_ID = re.compile(r"\[proposal ([^;\]]+);")
CATEGORIES = {
    "a": "Documented flips: the proposals that set the replayed level",
    "b": "False flips: the proposals that set the replayed level",
    "c": "Disagreeing quarters: the proposals behind the replay level",
    "d": "Random check of the remaining counted proposals",
}
COLUMNS = [
    "category",
    "id",
    "file",
    "quarter",
    "document",
    "document_date",
    "title",
    "variable",
    "level",
    "hindsight",
    "harness",
    "why",
    "proposal_date",
    "quote",
    "rule",
    "confidence",
    "url",
    "decision",
    "note",
]


def _quarter_of(day: str) -> str:
    d = date.fromisoformat(day)
    return f"{d.year}Q{(d.month - 1) // 3 + 1}"


def _lv(level) -> str:
    return str(level).lower() if isinstance(level, bool) else str(level)


HEADER = """# Review sample: Claude backend, FRUS replay 1936 to 1940

The sample of the owner's decision 7a (docs/owner_decisions_2026-10-23.md): the proposals that
decide the metrics of `metrics_claude.md`, and a random check of the rest, for a human review
before the phase 2 gate is decided. Nothing here is decided: every proposal is still
`pending` in `proposals/`. Built by `python scripts/build_review_sample.py` (seed {seed});
the same rows are in `review_sample.csv`, whose `decision` (accept or reject) and `note`
columns are for the reviewer. `python scripts/apply_review.py FILLED.csv [--skip-blank]
[--out ~/wf_runs/frus_claude_reviewed]` applies the filled sheet to a copy of `proposals/`
(never to this directory) with `wf review`, then re-measures; a row without a decision is
refused unless `--skip-blank` leaves it pending.

## How the unreviewed proposals are counted (read this first)

`wf replay --metrics-only` does **not** count pending proposals, and with a sample it measures
nothing. It reads only the replay snapshots that `wf review` writes, and `wf review` writes
the snapshot of a quarter only when no proposal of that quarter or of any earlier quarter is
still pending (a held or blocked proposal excepted), and removes it otherwise
(docs/replay_harness.md, "Review"). With {total} proposals of which {n} are in this sample,
every quarter from 1936Q1 keeps pending proposals, so after the review no snapshot exists and
`--metrics-only` reports all twenty quarters as "not compared". It measures the reviewed
evidence only once every proposal has been decided.

`wf replay --measure-proposals` (the measurement of `metrics_claude.md`) counts every proposal
as accepted **whatever its status**: a rejected proposal still counts. It would not see the
review either.

The measure set up for a partly reviewed run is therefore `wf replay --measure-proposals
--drop-rejected` (added for this; docs/replay_harness.md, "Replay and metrics"): the rejected
proposals are left out as if never proposed (so a rejected document no longer counts under
`two-document` either), the accepted and the pending ones count as accepted, and a
`retrospective?` proposal is applied only if the reviewer accepted it. Its report says on its
first line how many proposals were accepted, rejected and left pending. It is still a
proposal-level measurement, not a replay snapshot: it shows what the metrics become once the
reviewer's rejections are taken out, with the {rest} unreviewed proposals as the backend read
them. `scripts/apply_review.py` runs both: `--measure-proposals --drop-rejected` (the
re-measure) and `--metrics-only` (kept for the record; with a sample it compares nothing).

Under `--drop-rejected`, rejecting the proposal that set a level lets the next pending proposal
of the same level set it (for a structural variable, from a second document). That is why
category (c) lists, besides the indicators, the other proposals of the replayed level inside
each disagreeing run: a false flip goes away only if every proposal carrying it is rejected.

## The sample

| Category | Proposals |
|---|---|
{table}
| all | {n} |

Category (a) covers every replayed flip that answers a documented flip, all variables of the
flips table (the four belief and commitment variables: {a_bc}; the structural variables:
{a_struct}). For a variable under the `two-document` rule, both the proposal that carried the
flip and the first document it needed are listed (`harness: corroborating`). Category (d) is
drawn from the {remaining} proposals counted by the measurement and not in (a) to (c) (held,
blocked and `retrospective?` proposals are not counted, so not drawn), stratified by the
quarter of their file with proportional allocation.

A proposal in several categories is listed once, under the first; `why` gives every reason.
`hindsight` is the level of the hindsight snapshot at the end of the quarter of the proposal's
date (and of its file's quarter, where that differs). `harness` is the measurement's gate at
the end of 1940Q4 (and at the end of the file's quarter, where that differs). Under the rules,
`wf review --accept` refuses a held or blocked proposal; it can be rejected.

"""


def _md(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def render(rows, counts, remaining, total, args) -> str:
    a_bc = sum(1 for r in rows if r["category"] == "a" and r["variable"] in BC)
    out = [
        HEADER.format(
            seed=args.seed,
            total=total,
            n=len(rows),
            rest=total - len(rows),
            remaining=remaining,
            a_bc=a_bc,
            a_struct=counts["a"] - a_bc,
            table="\n".join(f"| ({c}) {CATEGORIES[c]} | {counts[c]} |" for c in CATEGORIES),
        )
    ]
    for cat, title in CATEGORIES.items():
        mine = [r for r in rows if r["category"] == cat]
        out.append(f"## ({cat}) {title}: {len(mine)}\n")
        quarter = None
        for r in mine:
            if r["quarter"] != quarter:
                quarter = r["quarter"]
                out.append(f"### {quarter}\n")
            out.append(
                f"**{r['id']}** · `{r['variable']}` = **{r['level']}** "
                f"(hindsight: {r['hindsight']})\n\n"
                f"- File: `{r['file']}`; document `{r['document']}`, dated "
                f"{r['document_date']}: {_md(r['title'])}; proposal dated {r['proposal_date']}\n"
                f'- Quote: "{_md(r["quote"])}"\n'
                f"- Rule: {_md(r['rule'])}\n"
                f"- Confidence: {r['confidence']}; harness: {_md(r['harness'])}\n"
                f"- Why sampled: {_md(r['why'])}\n"
                f"- FRUS: <{r['url']}>\n"
                "- Decision: ______ Note: ______\n"
            )
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", default=str(ROOT / "reports/replay_ww2_frus_claude"))
    ap.add_argument("--quarters", default="1936Q1..1940Q4")
    ap.add_argument("--random", type=int, default=40, help="size of the random check (d)")
    ap.add_argument("--seed", type=int, default=20261027)
    args = ap.parse_args(argv)
    run = Path(args.run)
    quarters = parse_quarters(args.quarters)
    pdir = run / "proposals"
    files = proposal_files(pdir)
    rules = directory_rules(files)

    by_id: dict[str, dict] = {}
    for path, data in files:
        docs = {d["id"]: d for d in data["documents"]}
        for rec in data["proposals"]:
            by_id[rec["id"]] = {
                "rec": rec,
                "file": path.name,
                "quarter": data["label"],
                "doc": docs.get(rec["document"], {}),
            }

    # Gates at each quarter's end, as the measurement classifies them (a flip's first
    # document can change when a later file brings an earlier-dated proposal).
    gate_at: dict[str, dict] = {}
    corroborates_at: dict[str, dict[str, list[str]]] = {}  # quarter -> carrier -> firsts
    for q in quarters:
        upto = [f for f in files if date.fromisoformat(f[1]["until"]) <= quarter_end(q)]
        records, _index, gating = review_gating(upto, quarter_end(q), rules, measure=True)
        gate_at[q] = {}
        corroborates_at[q] = {}
        for rec, g in zip(records, gating.gates, strict=True):
            if g is None:
                continue
            gate_at[q][record_key(rec)] = g
            if g.status == CORROBORATING:
                carrier = g.reason.rsplit(" ", 1)[-1]
                corroborates_at[q].setdefault(carrier, []).append(rec["id"])

    def gate(pid: str):
        """The measurement's gate of a proposal at the end of its own file's quarter."""
        return gate_at[by_id[pid]["quarter"]].get(record_key(by_id[pid]["rec"]))

    snaps = measured_snapshots(pdir, quarters)
    hind = {}
    for f in sorted(Path(DEFAULT_HINDSIGHT).glob("*.json")):
        hind[f.stem] = json.loads(f.read_text(encoding="utf-8"))

    def indicator_ids(q: str, var: str) -> list[str]:
        entry = snaps[q]["variables"][var]
        out = []
        for ind in entry.get("indicators", []):
            m = PROPOSAL_ID.search(ind.get("rule", ""))
            if m:
                out.append(m.group(1))
        return out

    metrics = compare(run, quarters, measure_proposals=True)
    chosen: dict[str, tuple[str, list[str]]] = {}  # id -> (category, reasons)

    def add(pid: str, cat: str, why: str) -> None:
        if pid not in by_id:
            raise SystemExit(f"unknown proposal {pid}")
        if pid in chosen:
            chosen[pid][1].append(why)
        else:
            chosen[pid] = (cat, [why])

    # (a) and (b): the proposal that set each replayed flip, and its first document.
    for var, matches in metrics.matches.items():
        for m in matches:
            r = m.replayed
            if r is None:
                continue
            cat = "a" if m.documented else "b"
            what = (
                f"{'documented' if m.documented else 'false'} flip {var} -> {_lv(r.after)} "
                f"(replayed {r.quarter}"
                + (f", documented {m.documented.quarter}" if m.documented else "")
                + ")"
            )
            ids = indicator_ids(r.quarter, var)
            setter = ids[0]
            add(setter, cat, f"sets the {what}")
            for first in corroborates_at[r.quarter].get(setter, []):
                add(first, cat, f"first of two documents for the {what}")

    # (c): the disagreeing quarters.
    for var, per_q in metrics.details.items():
        qs = sorted(per_q, key=_qindex)
        runs: list[list[str]] = []
        for q in qs:
            if runs and _qindex(q) == _qindex(runs[-1][-1]) + 1:
                runs[-1].append(q)
            else:
                runs.append([q])
        for run_qs in runs:
            span = run_qs[0] if len(run_qs) == 1 else f"{run_qs[0]} to {run_qs[-1]}"
            last_end = quarter_end(run_qs[-1])
            first_end = quarter_end(run_qs[0])
            run_start = first_end.replace(month=first_end.month - 2, day=1)
            replay_levels = set()
            hind_levels = set()
            for q in run_qs:
                h, r = per_q[q]
                replay_levels.add(repr(r["level"]))
                hind_levels.add(repr(h["level"]))
                for pid in indicator_ids(q, var):
                    add(
                        pid,
                        "c",
                        f"behind {var} = {_lv(r['level'])} at {q} "
                        f"(hindsight {_lv(h['level'])}; disagreement {span})",
                    )
            # Every proposal of the replayed level (and, where the replay sits at its assumed
            # initial level, of the hindsight level) read by the end of the run.
            for pid, info in by_id.items():
                p = info["rec"]["proposal"]
                if p["variable"] != var:
                    continue
                if quarter_end(info["quarter"]) > last_end:
                    continue
                lv = repr(p["level"])
                if lv in replay_levels:
                    if date.fromisoformat(p["date"]) < run_start:
                        continue
                    add(pid, "c", f"same level as the replay ({_lv(p['level'])}) in {span}")
                elif lv in hind_levels and all(not per_q[q][1].get("indicators") for q in run_qs):
                    add(pid, "c", f"hindsight level ({_lv(p['level'])}), not in force in {span}")

    # (d): a stratified random check of the rest.
    counted = [
        pid
        for pid in by_id
        if pid not in chosen
        and (g := gate(pid)) is not None
        and g.status not in (HELD, BLOCKED, RETROSPECTIVE)
    ]
    per_q: dict[str, list[str]] = {}
    for pid in counted:
        per_q.setdefault(by_id[pid]["quarter"], []).append(pid)
    total = len(counted)
    quota = {q: args.random * len(v) / total for q, v in per_q.items()}
    alloc = {q: int(x) for q, x in quota.items()}
    rest = args.random - sum(alloc.values())
    for q in sorted(quota, key=lambda q: (-(quota[q] - alloc[q]), q))[:rest]:
        alloc[q] += 1
    rng = random.Random(args.seed)
    for q in sorted(per_q, key=_qindex):
        for pid in rng.sample(sorted(per_q[q]), alloc[q]):
            add(pid, "d", f"random check ({q}: {alloc[q]} of {len(per_q[q])} remaining)")

    rows = []
    for pid, (cat, why) in chosen.items():
        info = by_id[pid]
        rec, p, doc = info["rec"], info["rec"]["proposal"], info["doc"]
        hq = _quarter_of(p["date"])
        hl = hind.get(hq, {}).get("variables", {}).get(p["variable"], {}).get("level", "n/a")
        hindsight = f"{_lv(hl)} ({hq} end)"
        if info["quarter"] != hq:
            hf = hind[info["quarter"]]["variables"][p["variable"]]["level"]
            hindsight += f"; {_lv(hf)} ({info['quarter']} end)"
        g, g_end = gate(pid), gate_at[quarters[-1]].get(record_key(rec))
        harness = f"{g_end.status}: {g_end.reason}" if g_end else ""
        if g and g_end and g != g_end:
            harness = f"{g.status} at {info['quarter']} end ({g.reason}); {harness}"
        rows.append(
            {
                "category": cat,
                "id": pid,
                "file": f"proposals/{info['file']}",
                "quarter": info["quarter"],
                "document": rec["document"],
                "document_date": doc.get("date", ""),
                "title": doc.get("title", ""),
                "variable": p["variable"],
                "level": _lv(p["level"]),
                "hindsight": hindsight,
                "harness": harness,
                "why": "; ".join(dict.fromkeys(why)),
                "proposal_date": p["date"],
                "quote": " ".join(p["quote"].split()),
                "rule": p["rule"],
                "confidence": p.get("confidence", ""),
                "url": p["url"],
                "decision": "",
                "note": "",
            }
        )
    rows.sort(key=lambda r: (r["category"], _qindex(r["quarter"]), r["id"]))

    with (run / "review_sample.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    counts = Counter(r["category"] for r in rows)
    print(f"{len(rows)} proposals: " + ", ".join(f"({c}) {counts[c]}" for c in CATEGORIES))
    print(f"random check drawn from {total} remaining counted proposals")
    (run / "review_sample.md").write_text(
        render(rows, counts, total, len(by_id), args), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
