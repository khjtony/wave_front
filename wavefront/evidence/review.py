"""The review step: nothing changes a replay snapshot without a reviewer's decision.

Proposals are written by the extractor to ``<dir>/proposals/<label>.json`` (for the replay,
``snapshots/ww2/replay/proposals/<quarter>.json``). A reviewer lists them, and accepts or
rejects each with a note (:func:`decide`, ``wf review``). After every decision the replay
snapshots are rebuilt from the accepted proposals only (:func:`rebuild_snapshots`): the
snapshot ``<dir>/<label>.json`` for each proposals file whose proposals, and those of every
earlier file in the directory, have all been decided. A file with pending proposals has no
snapshot (an existing one is removed), so a snapshot never silently leaves out unread
evidence. This module is the only writer of replay snapshots.

A replay snapshot is a schema-valid snapshot (snapshots/schema.json) for the model's
variables:

* a text-derived variable takes the level of its latest accepted proposal dated at or before
  the cut-off; its indicators are the proposal that set that level (and the latest
  confirming one), each carrying the document quote (``value``), the URL (``source``), the
  observation date and the proposal's rule with the reviewer's decision;
* a text-derived variable with no accepted proposal keeps the ontology's initial level with
  confidence ``assumed`` and no indicator;
* the resource variables are copied from the dataset-derived hindsight snapshot of the
  quarter, marked as copied (they are read from datasets, not from documents).

``--auto-accept`` (:data:`AUTO_REVIEWER`) is refused unless the proposals came from a
synthetic fixture corpus, and every indicator it produces says AUTO-ACCEPTED.

The harness rules (:mod:`.harness_rules`; recorded in each proposals file as
``harness_rules``, both on by default) act here: a proposal *held* by the two-document rule or
*blocked* by the no-retrospective rule is not a proposal for review, cannot be accepted and
does not keep a snapshot from being written; a ``retrospective?`` proposal is shown flagged
and needs a decision like any other; a level is set only by proposals in force under the
rules (:func:`.harness_rules.gate_records`).
"""

from __future__ import annotations

import copy
import json
import os
from collections.abc import Iterable, Sequence
from datetime import date
from pathlib import Path
from typing import Any

from . import hindsight_ww2 as hw
from .extract.extractor import read_proposals, save_proposals
from .extract.schema import RESOURCE_VARIABLES, TEXT_VARIABLES
from .harness_rules import (
    DEFAULT_RULES,
    FOR_REVIEW,
    Gate,
    Gating,
    gate_records,
    parse_rules,
    record_key,
)
from .snapshot import validate_snapshot

__all__ = [
    "AUTO_REVIEWER",
    "DEFAULT_HINDSIGHT",
    "DEFAULT_REPLAY",
    "ReviewError",
    "build_snapshot",
    "decide",
    "directory_rules",
    "file_gates",
    "file_rules",
    "format_listing",
    "label_for",
    "proposal_files",
    "rebuild_snapshots",
    "review_gating",
]

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HINDSIGHT = ROOT / "snapshots" / "ww2" / "hindsight"
DEFAULT_REPLAY = ROOT / "snapshots" / "ww2" / "replay"
SCHEMA = ROOT / "snapshots" / "schema.json"
AUTO_REVIEWER = "auto-accept (synthetic run only)"
STATUSES = ("accepted", "rejected")


class ReviewError(ValueError):
    """A review request that cannot be carried out (unknown id, missing note, auto-accept of
    a real corpus, an invalid resulting snapshot)."""


def label_for(until: date) -> str:
    """``YYYYQn`` when ``until`` is the last day of a quarter, else the ISO date."""
    quarter = hw.quarter_of(until)
    return quarter if hw.quarter_bounds(quarter)[1] == until else until.isoformat()


def _parse_ids(ids: str | Iterable[str]) -> list[str]:
    if isinstance(ids, str):
        ids = ids.split(",")
    return [i.strip() for i in ids if i.strip()]


def _proposal_lines(rec: dict[str, Any], gate: Gate | None) -> list[str]:
    p = rec["proposal"]
    flag = ""
    if gate is not None and gate.status not in ("ok",):
        flag = f"  {gate.status}"
    lines = [
        f"{rec['id']}  [{rec['status']}]{flag}  {p['variable']} := {p['level']}  "
        f"({p['date']}, {p['confidence']})  {rec['document']}",
        f"    quote: {p['quote']}",
        f"    rule:  {p['rule']}",
    ]
    if gate is not None and gate.status != "ok":
        lines.append(f"    harness: {gate.reason}")
    if rec["decisions"]:
        last = rec["decisions"][-1]
        lines.append(f"    decision: {last['status']} by {last['reviewer']}: {last['note']}")
    return lines


def format_listing(
    data: dict[str, Any],
    gates: dict[str, Gate] | None = None,
    rules: Sequence[str] | None = None,
) -> str:
    """A plain-text listing of a proposals file for the reviewer: every proposal with its
    status, the variable and level, the document and the full quote. With ``gates`` (by
    proposal id, :func:`file_gates`) the proposals the harness rules hold or block are listed
    apart, after the proposals for review, and a ``retrospective?`` one is flagged."""
    gates = gates or {}
    rules = file_rules(data) if rules is None else tuple(rules)
    lines = [
        f"proposals {data['label']} (documents dated to {data['until']}; "
        f"corpus {data['corpus'].get('source')}"
        + (", SYNTHETIC" if data["corpus"].get("synthetic") else "")
        + f"; backend {data.get('backend', {}).get('name')}; "
        f"harness rules: {', '.join(rules) or 'none'})"
    ]
    apart = []
    for rec in data["proposals"]:
        gate = gates.get(rec["id"])
        if gate is not None and gate.status in ("held", "blocked"):
            apart.append(rec)
            continue
        lines += _proposal_lines(rec, gate)
    if apart:
        lines.append(
            f"-- not for review under the harness rules ({len(apart)}): held until a second "
            "document proposes the same flip, or a move back of a monotone variable, never "
            "applied --"
        )
        for rec in apart:
            lines += _proposal_lines(rec, gates[rec["id"]])
    pending = sum(1 for r in data["proposals"] if r["status"] == "pending")
    review = sum(
        1
        for r in data["proposals"]
        if r["status"] == "pending" and (r["id"] not in gates or gates[r["id"]].for_review)
    )
    lines.append(
        f"{len(data['proposals'])} proposals, {pending} pending ({review} awaiting review); "
        f"{len(data.get('discarded', []))} discarded by the checks; "
        f"{len(data.get('errors', []))} backend errors"
    )
    return "\n".join(lines)


def file_rules(data: dict[str, Any]) -> tuple[str, ...]:
    """The harness rules recorded in a proposals file (the default for a file written before
    the rules were recorded)."""
    recorded = data.get("harness_rules")
    return DEFAULT_RULES if recorded is None else parse_rules(recorded)


def directory_rules(files: Sequence[tuple[Path, dict[str, Any]]]) -> tuple[str, ...]:
    """The harness rules of a directory of proposals files; they must all agree."""
    found = {file_rules(data) for _p, data in files}
    if len(found) > 1:
        shown = "; ".join(sorted(", ".join(r) or "none" for r in found))
        raise ReviewError(
            f"the proposals files disagree on the harness rules ({shown}); replay the "
            "directory with one --rules setting"
        )
    return found.pop() if found else DEFAULT_RULES


def _unique(files: Sequence[tuple[Path, dict[str, Any]]]) -> tuple[list[dict[str, Any]], dict]:
    records: list[dict[str, Any]] = []
    index: dict[tuple[Any, ...], int] = {}
    for _p, data in files:
        for rec in data["proposals"]:
            key = record_key(rec)
            if key not in index:
                index[key] = len(records)
                records.append(rec)
    return records, index


def review_gating(
    files: Sequence[tuple[Path, dict[str, Any]]],
    until: date,
    rules: Sequence[str],
    *,
    measure: bool = False,
) -> tuple[list[dict[str, Any]], dict[tuple[Any, ...], int], Gating]:
    """The harness rules applied at ``until`` to the proposals of ``files`` (deduplicated,
    in file order): the records, the index of each record key and the gating."""
    records, index = _unique(files)
    return records, index, gate_records(records, until, rules, measure=measure)


def file_gates(path: str | Path) -> dict[str, Gate]:
    """The gate of each proposal of the file at ``path`` (by proposal id), at its cut-off,
    with the files of its directory dated up to it and the directory's harness rules."""
    path = Path(path).resolve()
    files = [f for f in proposal_files(path.parent)]
    this = next((data for p, data in files if p.resolve() == path), None)
    if this is None:  # pragma: no cover - the file is in its own directory
        this = read_proposals(path)
        files = [(path, this)]
    until = date.fromisoformat(this["until"])
    upto = [f for f in files if date.fromisoformat(f[1]["until"]) <= until]
    records, index, gating = review_gating(upto, until, directory_rules(files))
    out: dict[str, Gate] = {}
    for rec in this["proposals"]:
        gate = gating.gates[index[record_key(rec)]]
        if gate is not None:
            out[rec["id"]] = gate
    return out


def decide(
    path: str | Path,
    ids: str | Iterable[str],
    status: str,
    *,
    note: str,
    reviewer: str,
    snapshots_dir: str | Path | None = None,
    hindsight_dir: str | Path = DEFAULT_HINDSIGHT,
    auto: bool = False,
    today: date | None = None,
) -> list[Path]:
    """Record ``status`` (``accepted`` or ``rejected``) with ``note`` for the proposals
    ``ids`` of the file at ``path``, then rebuild the replay snapshots. A decision may be
    changed later; every decision is kept in the proposal's history. The snapshots go to
    ``snapshots_dir``, by default the parent of the ``proposals`` directory holding the
    file. Returns the snapshot files written."""
    if status not in STATUSES:
        raise ReviewError(f"status must be one of {STATUSES}, not {status!r}")
    if not note or not note.strip():
        raise ReviewError("a reviewer note is required for every decision")
    if not reviewer or not reviewer.strip():
        raise ReviewError("a reviewer name is required")
    path = Path(path)
    if snapshots_dir is not None:
        out = Path(snapshots_dir)
    elif path.parent.name == "proposals":
        out = path.parent.parent
    else:
        raise ReviewError(
            f"{path}: not in a 'proposals' directory, so give the snapshot directory "
            "(--snapshots DIR)"
        )
    data = read_proposals(path)
    if auto and not data["corpus"].get("synthetic"):
        raise ReviewError(
            f"{path}: auto-accept is only for the synthetic fixture corpus; real proposals "
            "need a reviewer's decision"
        )
    if reviewer == AUTO_REVIEWER and not auto:
        raise ReviewError(f"the reviewer name {AUTO_REVIEWER!r} is reserved for auto-accept")
    wanted = _parse_ids(ids)
    if not wanted:
        raise ReviewError("no proposal ids given")
    by_id = {rec["id"]: rec for rec in data["proposals"]}
    unknown = [i for i in wanted if i not in by_id]
    if unknown:
        raise ReviewError(f"{path}: no proposals {', '.join(unknown)}")
    if status == "accepted":
        gates = file_gates(path)
        refused = [i for i in wanted if i in gates and not gates[i].acceptable]
        if refused:
            raise ReviewError(
                f"{path}: {', '.join(refused)} cannot be accepted under the harness rules "
                f"({gates[refused[0]].reason}); see the listing"
            )
    stamp = (today or date.today()).isoformat()
    for i in wanted:
        rec = by_id[i]
        rec["status"] = status
        rec["decisions"].append(
            {
                "status": status,
                "reviewer": reviewer,
                "note": note.strip(),
                "date": stamp,
                "auto": auto,
            }
        )
    save_proposals(path, data)
    return rebuild_snapshots(path.parent, out, hindsight_dir=hindsight_dir)


def proposal_files(proposals_dir: str | Path) -> list[tuple[Path, dict[str, Any]]]:
    """The proposals files in a directory, ordered by cut-off date."""
    files = []
    for p in sorted(Path(proposals_dir).glob("*.json")):
        files.append((p, read_proposals(p)))
    return sorted(files, key=lambda f: (f[1]["until"], f[0].name))


def _indicator(rec: dict[str, Any]) -> dict[str, Any]:
    p = rec["proposal"]
    last = rec["decisions"][-1]
    if last.get("measured"):
        decision = f"NOT REVIEWED, treated as accepted for proposal-level metrics ({last['note']})"
    elif last.get("auto"):
        decision = f"AUTO-ACCEPTED in a synthetic run, no human review ({last['note']})"
    else:
        decision = f"accepted by {last['reviewer']} on {last['date']}: {last['note']}"
    return {
        "id": p["indicator_id"],
        "value": p["quote"],
        "source": p["url"],
        "observed": p["date"],
        "rule": f"{p['rule']} [proposal {rec['id']}; {decision}]",
    }


def _copied(entry: dict[str, Any], quarter: str) -> dict[str, Any]:
    entry = copy.deepcopy(entry)
    prefix = (
        f"copied from the hindsight snapshot {quarter} (a resource variable read from the "
        "datasets, not extracted from documents)"
    )
    for ind in entry.get("indicators", []):
        ind["rule"] = f"{prefix}: {ind['rule']}"
    return entry


def build_snapshot(
    until: date,
    accepted: Sequence[dict[str, Any]],
    *,
    hindsight_dir: str | Path = DEFAULT_HINDSIGHT,
    schema_ref: str | None = None,
) -> dict[str, Any]:
    """The replay snapshot at ``until`` from ``accepted`` proposal records (in file order).
    Raises :class:`ReviewError` if the result is not a valid snapshot of the ontology."""
    quarter = hw.quarter_of(until)
    hindsight_path = Path(hindsight_dir) / f"{quarter}.json"
    hindsight = (
        json.loads(hindsight_path.read_text(encoding="utf-8"))["variables"]
        if hindsight_path.exists()
        else {}
    )
    order = {id(rec): n for n, rec in enumerate(accepted)}
    variables: dict[str, Any] = {}
    for var in hw.VARIABLES:
        name = var.name
        if name in RESOURCE_VARIABLES and name in hindsight:
            variables[name] = _copied(hindsight[name], quarter)
            continue
        rows = sorted(
            (
                r
                for r in accepted
                if r["proposal"]["variable"] == name
                and date.fromisoformat(r["proposal"]["date"]) <= until
            ),
            key=lambda r: (r["proposal"]["date"], order[id(r)]),
        )
        if not rows or name not in TEXT_VARIABLES:
            variables[name] = {"level": var.init, "confidence": "assumed", "indicators": []}
            continue
        level = rows[-1]["proposal"]["level"]
        first = len(rows) - 1
        while first > 0 and rows[first - 1]["proposal"]["level"] == level:
            first -= 1
        chosen = [rows[first]] if first == len(rows) - 1 else [rows[first], rows[-1]]
        variables[name] = {
            "level": level,
            "confidence": rows[-1]["proposal"]["confidence"],
            "indicators": [_indicator(r) for r in chosen],
        }
    snapshot: dict[str, Any] = {}
    if schema_ref:
        snapshot["$schema"] = schema_ref
    snapshot |= {"date": until.isoformat(), "model": hw.MODEL, "variables": variables}
    problems = validate_snapshot(snapshot) + hw.check_against_ontology(snapshot)
    if problems:
        raise ReviewError("the replay snapshot would be invalid: " + "; ".join(problems))
    return snapshot


def _schema_ref(out_dir: Path) -> str | None:
    try:
        out_dir.resolve().relative_to(ROOT)
    except ValueError:
        return None
    return os.path.relpath(SCHEMA, out_dir.resolve()).replace(os.sep, "/")


def rebuild_snapshots(
    proposals_dir: str | Path,
    snapshots_dir: str | Path,
    *,
    hindsight_dir: str | Path = DEFAULT_HINDSIGHT,
) -> list[Path]:
    """Rebuild every replay snapshot of ``proposals_dir`` into ``snapshots_dir`` (see the
    module docstring). Proposals repeated across files (the same document, variable, level
    and quote) count once. Under the directory's harness rules, a snapshot is written for a
    file when no proposal of it or of an earlier file still awaits review (held and blocked
    proposals do not), and its levels come from the accepted proposals in force. Returns the
    files written."""
    out_dir = Path(snapshots_dir)
    files = proposal_files(proposals_dir)
    rules = directory_rules(files)
    written: list[Path] = []
    for n, (_path, data) in enumerate(files):
        until = date.fromisoformat(data["until"])
        upto = files[: n + 1]
        records, index, gating = review_gating(upto, until, rules)
        awaiting = 0
        for _p, d in upto:
            for rec in d["proposals"]:
                gate = gating.gates[index[record_key(rec)]]
                if rec["status"] == "pending" and (gate is None or gate.status in FOR_REVIEW):
                    awaiting += 1
        target = out_dir / f"{data['label']}.json"
        if awaiting:
            if target.exists():
                target.unlink()  # stale: evidence up to this date is not all reviewed
            continue
        snapshot = build_snapshot(
            until, gating.in_force, hindsight_dir=hindsight_dir, schema_ref=_schema_ref(out_dir)
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        written.append(target)
    return written
