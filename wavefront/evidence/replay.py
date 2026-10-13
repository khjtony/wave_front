"""The blind replay driver and its metrics (ww2_testbed.md sections 8 and 9).

For each quarter T of the range, in order:

1. ``corpus(T)``: the corpus filtered to the documents dated at or before T's last day.
2. The extractor runs on the documents of ``corpus(T)`` not read at an earlier quarter of the
   run, and writes ``<out>/proposals/<T>.json``. Reading each document once is equivalent to
   re-reading ``corpus(T)`` at every quarter, because a backend reads one document at a time;
   it means each proposal is reviewed once.
3. With ``auto_accept`` (synthetic fixture corpus only; the output says so everywhere) every
   proposal is accepted through :func:`wavefront.evidence.review.decide`, which writes
   ``<out>/<T>.json``. Without it the proposals wait for ``wf review``.

Proposal-level measurement (:func:`measured_snapshots`, ``wf replay --measure-proposals``) is
the way to measure a backend on a real corpus before anyone has reviewed its proposals: every
proposal of the proposals files is treated as if accepted, whatever its review status, the
quarter-end snapshots are built in memory with the same rules as :mod:`.review`, and the metrics
are computed from them. Nothing is written but the report, which says on its first line that no
proposal was reviewed. It measures the backend, not the reviewed evidence.

Then :func:`compare` sets the replay snapshots against the hindsight snapshots: per-variable
agreement of the levels at each quarter's end, the lag of each replayed flip against the
documented flip, false flips and missed flips; :func:`render_report` writes the Markdown
metrics report. Resource variables are copied from the hindsight snapshots, not extracted:
their agreement is shown but is not a test of anything.
"""

from __future__ import annotations

import copy
import json
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from . import hindsight_ww2 as hw
from .corpora.base import Corpus
from .extract.backend import Backend, ExtractError
from .extract.extractor import extract, write_proposals
from .extract.schema import RESOURCE_VARIABLES, TEXT_VARIABLES, text_variables
from .review import (
    AUTO_REVIEWER,
    DEFAULT_HINDSIGHT,
    build_snapshot,
    decide,
    proposal_files,
    rebuild_snapshots,
)

__all__ = [
    "BELIEF_COMMIT",
    "Flip",
    "Metrics",
    "ReplayError",
    "compare",
    "measured_snapshots",
    "parse_quarters",
    "proposal_counts",
    "quarter_end",
    "render_report",
    "replay",
]

BELIEF_COMMIT = ("belief_WEST", "belief_GER", "commit_WEST", "commit_US")
GROUPS = {
    "beliefs and commitment": BELIEF_COMMIT,
    "treaty": ("treaty",),
    "pacts and structural flags": (
        "axis",
        "anticomintern",
        "nazi_soviet_pact",
        "polish_guarantee",
        "anglo_soviet_alliance",
        "ussr_axis",
        "italy_estranged",
        "china_war",
    ),
    "war": ("war_west_ger",),
    "regions": (
        "rhineland",
        "austria",
        "sudeten",
        "bohemia",
        "poland",
        "france",
        "britain",
        "balkans",
        "siberia",
        "channel_air",
    ),
    "oil": ("oil_GER",),
}
MATCH_WINDOW = 4  # quarters within which a replayed flip may answer a documented one
AUTO_NOTE = "auto-accepted by wf replay --auto-accept: synthetic fixture run, not a review"
MEASURE_REVIEWER = "proposal-level measurement (no review)"
MEASURE_NOTE = "wf replay --measure-proposals: a measurement of the backend, never written"


class ReplayError(ValueError):
    """A replay that cannot run: a bad quarter range, auto-accept on a real corpus, or a
    backend error that would leave a quarter's proposals incomplete."""


_Q = re.compile(r"(\d{4})Q([1-4])")


def _qindex(quarter: str) -> int:
    m = _Q.fullmatch(quarter)
    if not m:
        raise ReplayError(f"{quarter!r} is not a quarter of the form YYYYQn")
    return int(m.group(1)) * 4 + int(m.group(2)) - 1


def _qname(index: int) -> str:
    return f"{index // 4}Q{index % 4 + 1}"


def parse_quarters(text: str) -> list[str]:
    """``1936Q1..1940Q4`` (inclusive), a single quarter, or a comma-separated list."""
    text = text.strip()
    if ".." in text:
        a, b = (t.strip() for t in text.split("..", 1))
        i, j = _qindex(a), _qindex(b)
        if j < i:
            raise ReplayError(f"empty quarter range {text!r}")
        return [_qname(k) for k in range(i, j + 1)]
    quarters = [q.strip() for q in text.split(",") if q.strip()]
    for q in quarters:
        _qindex(q)
    if [_qindex(q) for q in quarters] != sorted({_qindex(q) for q in quarters}):
        raise ReplayError(f"quarters {text!r} must be increasing and distinct")
    return quarters


def quarter_end(quarter: str) -> date:
    _qindex(quarter)
    return hw.quarter_bounds(quarter)[1]


# -- the driver -----------------------------------------------------------------------------


@dataclass
class QuarterRun:
    quarter: str
    visible: int
    read: int
    proposals: int
    discarded: int
    snapshot: Path | None


def replay(
    corpus: Corpus,
    quarters: Sequence[str],
    out_dir: str | Path,
    backend: Backend,
    *,
    auto_accept: bool = False,
    hindsight_dir: str | Path = DEFAULT_HINDSIGHT,
) -> list[QuarterRun]:
    """Run the blind replay over ``quarters`` (see the module docstring)."""
    if auto_accept and not corpus.synthetic:
        raise ReplayError(
            "--auto-accept is only for the synthetic fixture corpus; a real corpus needs wf review"
        )
    out_dir = Path(out_dir)
    proposals_dir = out_dir / "proposals"
    read_before: set[str] = set()
    if proposals_dir.exists():
        first_end = quarter_end(quarters[0])
        for _p, data in proposal_files(proposals_dir):
            if date.fromisoformat(data["until"]) < first_end:
                read_before.update(d["id"] for d in data["documents"])
    variables = text_variables()
    runs: list[QuarterRun] = []
    for quarter in quarters:
        until = quarter_end(quarter)
        visible = sum(1 for _ in corpus.iter_documents(until=until))
        try:
            result = extract(
                corpus, until=until, backend=backend, variables=variables, skip_ids=read_before
            )
        except ExtractError as exc:  # pragma: no cover - extract records errors
            raise ReplayError(f"{quarter}: {exc}") from exc
        if result.errors:
            raise ReplayError(
                f"{quarter}: the backend failed on {len(result.errors)} document(s), so the "
                f"quarter's proposals would be incomplete: {result.errors[0]['error']}"
            )
        path = proposals_dir / f"{quarter}.json"
        data = write_proposals(
            path,
            result,
            label=quarter,
            corpus=corpus.describe(),
            backend=_backend_info(backend),
        )
        read_before.update(d.id for d in result.documents)
        snapshot = None
        if auto_accept and data["proposals"]:
            written = decide(
                path,
                [r["id"] for r in data["proposals"]],
                "accepted",
                note=AUTO_NOTE,
                reviewer=AUTO_REVIEWER,
                snapshots_dir=out_dir,
                hindsight_dir=hindsight_dir,
                auto=True,
            )
            snapshot = next((w for w in written if w.stem == quarter), None)
        elif auto_accept:
            # Nothing to decide in this quarter: rebuild so the quarter still has a snapshot.
            written = rebuild_snapshots(proposals_dir, out_dir, hindsight_dir=hindsight_dir)
            snapshot = next((w for w in written if w.stem == quarter), None)
        runs.append(
            QuarterRun(
                quarter=quarter,
                visible=visible,
                read=len(result.documents),
                proposals=len(data["proposals"]),
                discarded=len(result.discarded),
                snapshot=snapshot,
            )
        )
    return runs


def _backend_info(backend: Backend) -> dict[str, Any]:
    info: dict[str, Any] = {"name": backend.name}
    model = getattr(backend, "model", None)
    if model:
        info["model"] = model
    return info


# -- proposal-level measurement -------------------------------------------------------------


def _as_measured(rec: dict[str, Any]) -> dict[str, Any]:
    rec = copy.deepcopy(rec)
    rec["status"] = "accepted"
    rec["decisions"] = [
        {
            "status": "accepted",
            "reviewer": MEASURE_REVIEWER,
            "note": MEASURE_NOTE,
            "date": date.today().isoformat(),
            "auto": False,
            "measured": True,
        }
    ]
    return rec


def measured_snapshots(
    proposals_dir: str | Path,
    quarters: Sequence[str],
    hindsight_dir: str | Path = DEFAULT_HINDSIGHT,
) -> dict[str, dict[str, Any]]:
    """Quarter-end snapshots, in memory, in which every proposal of the files in
    ``proposals_dir`` dated up to the quarter's end counts as accepted, whatever its review
    status (pending, accepted or rejected). Built with :func:`.review.build_snapshot`, so the
    levels follow the same rules as reviewed snapshots; every indicator says NOT REVIEWED.
    Nothing is written. A quarter whose own proposals file is missing has no snapshot."""
    files = proposal_files(proposals_dir)
    labels = {data["label"] for _p, data in files}
    out: dict[str, dict[str, Any]] = {}
    for quarter in quarters:
        if quarter not in labels:
            continue
        until = quarter_end(quarter)
        records: list[dict[str, Any]] = []
        keys: set[tuple[Any, ...]] = set()
        for _p, data in files:
            if date.fromisoformat(data["until"]) > until:
                continue
            for rec in data["proposals"]:
                p = rec["proposal"]
                key = (rec["document"], p["variable"], repr(p["level"]), p["quote"])
                if key not in keys:
                    keys.add(key)
                    records.append(_as_measured(rec))
        out[quarter] = build_snapshot(until, records, hindsight_dir=hindsight_dir)
    return out


def proposal_counts(proposals_dir: str | Path, quarters: Sequence[str]) -> dict[str, Counter[str]]:
    """The number of proposals per variable and level in the proposals files of ``quarters``
    (levels as strings)."""
    wanted = set(quarters)
    counts: dict[str, Counter[str]] = {}
    for _p, data in proposal_files(proposals_dir):
        if data["label"] not in wanted:
            continue
        for rec in data["proposals"]:
            p = rec["proposal"]
            counts.setdefault(p["variable"], Counter())[_lv(p["level"])] += 1
    return counts


# -- metrics --------------------------------------------------------------------------------


@dataclass(frozen=True)
class Flip:
    """A change of level of ``variable`` between the end of the previous quarter and the end
    of ``quarter``; ``observed`` is the date of the indicator that set the new level."""

    variable: str
    quarter: str
    before: Any
    after: Any
    observed: str | None


@dataclass
class FlipMatch:
    documented: Flip | None
    replayed: Flip | None

    @property
    def lag_quarters(self) -> int | None:
        if self.documented is None or self.replayed is None:
            return None
        return _qindex(self.replayed.quarter) - _qindex(self.documented.quarter)

    @property
    def lag_days(self) -> int | None:
        if self.documented is None or self.replayed is None:
            return None
        if not self.documented.observed or not self.replayed.observed:
            return None
        return (
            date.fromisoformat(self.replayed.observed)
            - date.fromisoformat(self.documented.observed)
        ).days


@dataclass
class Metrics:
    quarters: list[str]
    missing_replay: list[str]
    levels: dict[str, dict[str, tuple[Any, Any]]] = field(
        default_factory=dict
    )  # var -> q -> (h, r)
    agreement: dict[str, tuple[int, int]] = field(default_factory=dict)  # var -> (agree, total)
    # var -> q -> (hindsight entry, replay entry) where they disagree
    details: dict[str, dict[str, tuple[dict[str, Any], dict[str, Any]]]] = field(
        default_factory=dict
    )
    matches: dict[str, list[FlipMatch]] = field(default_factory=dict)
    auto_accepted: bool = False
    synthetic: bool = False
    #: True when the snapshots were built from unreviewed proposals (proposal-level mode)
    proposal_level: bool = False
    #: proposals per variable and level (proposal-level mode)
    counts: dict[str, Counter[str]] = field(default_factory=dict)
    #: var -> (agree, total) of a replay that reads nothing (every level the initial one)
    unread: dict[str, tuple[int, int]] = field(default_factory=dict)
    #: var -> (agree, total) over the quarters whose hindsight level is not the initial one
    moved: dict[str, tuple[int, int]] = field(default_factory=dict)

    def matched(self, variable: str) -> list[FlipMatch]:
        return [m for m in self.matches.get(variable, []) if m.documented and m.replayed]

    def false_flips(self, variable: str) -> list[Flip]:
        return [m.replayed for m in self.matches.get(variable, []) if m.documented is None]

    def missed_flips(self, variable: str) -> list[Flip]:
        return [m.documented for m in self.matches.get(variable, []) if m.replayed is None]

    def share(self, names: Sequence[str], of: str = "agreement") -> tuple[int, int]:
        """Summed (agree, total) over ``names`` of ``agreement``, ``unread`` or ``moved``."""
        table: dict[str, tuple[int, int]] = getattr(self, of)
        agree = sum(table.get(n, (0, 0))[0] for n in names)
        total = sum(table.get(n, (0, 0))[1] for n in names)
        return agree, total


def _read(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _setting_date(entry: dict[str, Any] | None) -> str | None:
    if not entry or not entry.get("indicators"):
        return None
    return entry["indicators"][0].get("observed")


def _flips(series: list[tuple[str, dict[str, Any] | None]], name: str) -> list[Flip]:
    out = []
    for (q0, s0), (q1, s1) in zip(series, series[1:], strict=False):
        if s0 is None or s1 is None:
            continue
        a, b = s0["variables"][name]["level"], s1["variables"][name]["level"]
        if a != b:
            out.append(Flip(name, q1, a, b, _setting_date(s1["variables"][name])))
    return out


def _match(documented: list[Flip], replayed: list[Flip]) -> list[FlipMatch]:
    """Pair each documented flip with the nearest unmatched replayed flip to the same level
    within :data:`MATCH_WINDOW` quarters; the rest are missed or false flips."""
    free = list(replayed)
    out: list[FlipMatch] = []
    for d in documented:
        candidates = [
            r
            for r in free
            if r.after == d.after and abs(_qindex(r.quarter) - _qindex(d.quarter)) <= MATCH_WINDOW
        ]
        if candidates:
            best = min(
                candidates,
                key=lambda r: (abs(_qindex(r.quarter) - _qindex(d.quarter)), _qindex(r.quarter)),
            )
            free.remove(best)
            out.append(FlipMatch(d, best))
        else:
            out.append(FlipMatch(d, None))
    out += [FlipMatch(None, r) for r in free]
    return out


def _initial() -> dict[str, Any]:
    return {"variables": {v.name: {"level": v.init, "indicators": []} for v in hw.VARIABLES}}


def compare(
    replay_dir: str | Path,
    quarters: Sequence[str],
    hindsight_dir: str | Path = DEFAULT_HINDSIGHT,
    *,
    measure_proposals: bool = False,
) -> Metrics:
    """The section 9 metrics of the replay snapshots in ``replay_dir`` against the hindsight
    snapshots, for ``quarters``. The baseline for flips at the first quarter is the hindsight
    snapshot of the previous quarter and, for the replay, its snapshot of that quarter if
    there is one, else the ontology's initial levels.

    With ``measure_proposals`` the replay snapshots are not read: they are built in memory
    from every proposal in ``replay_dir/proposals`` as if accepted (:func:`measured_snapshots`),
    and the metrics say so."""
    replay_dir, hindsight_dir = Path(replay_dir), Path(hindsight_dir)
    prev = _qname(_qindex(quarters[0]) - 1)
    measured: dict[str, dict[str, Any]] = {}
    if measure_proposals:
        measured = measured_snapshots(replay_dir / "proposals", quarters, hindsight_dir)
    hind = [(prev, _read(hindsight_dir / f"{prev}.json"))]
    rep = [(prev, _initial() if measure_proposals else _read(replay_dir / f"{prev}.json"))]
    if rep[0][1] is None:
        rep[0] = (prev, _initial())
    for q in quarters:
        hind.append((q, _read(hindsight_dir / f"{q}.json")))
        rep.append((q, measured.get(q) if measure_proposals else _read(replay_dir / f"{q}.json")))
    m = Metrics(quarters=list(quarters), missing_replay=[q for q, s in rep[1:] if s is None])
    if measure_proposals:
        m.proposal_level = True
        m.counts = proposal_counts(replay_dir / "proposals", quarters)
    auto = False
    for _q, s in rep[1:]:
        if s is None:
            continue
        for entry in s["variables"].values():
            if any("AUTO-ACCEPTED" in i.get("rule", "") for i in entry.get("indicators", [])):
                auto = True
    m.auto_accepted = auto
    init = {v.name: v.init for v in hw.VARIABLES}
    for name in (*TEXT_VARIABLES, *RESOURCE_VARIABLES):
        per_q: dict[str, tuple[Any, Any]] = {}
        agree = total = unread = moved = moved_agree = 0
        for (q, h), (_q, r) in zip(hind[1:], rep[1:], strict=True):
            if h is None or r is None or name not in h["variables"]:
                continue
            hl, rl = h["variables"][name]["level"], r["variables"][name]["level"]
            per_q[q] = (hl, rl)
            total += 1
            agree += hl == rl
            unread += hl == init.get(name)
            if hl != init.get(name):
                moved += 1
                moved_agree += hl == rl
            if hl != rl:
                m.details.setdefault(name, {})[q] = (h["variables"][name], r["variables"][name])
        m.levels[name] = per_q
        m.agreement[name] = (agree, total)
        m.unread[name] = (unread, total)
        m.moved[name] = (moved_agree, moved)
        if name in TEXT_VARIABLES:
            m.matches[name] = _match(_flips(hind, name), _flips(rep, name))
    return m


# -- the report -----------------------------------------------------------------------------


def _pct(agree: int, total: int) -> str:
    return f"{agree}/{total} ({100 * agree / total:.0f}%)" if total else "n/a"


def _lv(level: Any) -> str:
    return str(level).lower() if isinstance(level, bool) else str(level)


def render_report(
    metrics: Metrics,
    *,
    title: str,
    corpus: dict[str, Any],
    backend: dict[str, Any],
    command: str,
    runs: Sequence[QuarterRun] = (),
) -> str:
    """The Markdown metrics report. A synthetic or auto-accepted run says so in its title,
    its first line and its summary."""
    synthetic = bool(corpus.get("synthetic"))
    lines: list[str] = []
    if metrics.proposal_level:
        lines.append(
            "PROPOSAL-LEVEL MEASUREMENT: no proposal below was reviewed. Every proposal the "
            "backend made was treated as if accepted to compute these metrics, no replay "
            "snapshot was written, and the levels and quotes below are the backend's "
            "unreviewed readings, not evidence accepted by a reviewer."
        )
        lines.append("")
    if synthetic or metrics.auto_accepted:
        lines.append(
            "SYNTHETIC RUN: the corpus is a fixture written for pipeline tests, every proposal "
            "was auto-accepted without review, and nothing below is evidence about 1936 to "
            "1940. It measures the mechanics of the harness only."
        )
        lines.append("")
        title = f"{title} (SYNTHETIC)" if "SYNTHETIC" not in title.upper() else title
    lines += [f"# {title}", ""]
    q0, q1 = metrics.quarters[0], metrics.quarters[-1]
    lines += [
        f"- Quarters: {q0} to {q1} ({len(metrics.quarters)}); snapshot compared at each "
        "quarter's last day.",
        f"- Corpus: {corpus.get('source')}"
        + (f", `{corpus['root']}`" if corpus.get("root") else "")
        + (" (synthetic fixtures)" if synthetic else ""),
        f"- Backend: {backend.get('name')}",
        "- Review: "
        + (
            "auto-accepted (synthetic run only)"
            if metrics.auto_accepted
            else "none: proposal-level measurement (every proposal treated as accepted, "
            "nothing written)"
            if metrics.proposal_level
            else "human review"
        ),
        f"- Command: `{command}`",
        "- Target: the hindsight snapshots in `snapshots/ww2/hindsight/` (levels at each "
        "quarter's end, read with full knowledge of the record).",
        "",
    ]
    if synthetic:
        lines += [
            "What this run shows: that the harness filters each quarter's corpus by document "
            "date, extracts proposals in the fixed schema, checks them, turns accepted "
            "proposals into schema-valid snapshots with their quotes and rules, and computes "
            "the agreement, lag and false-flip metrics against the hindsight snapshots. What it "
            "does not show: anything about extraction quality on real documents. The fixtures "
            "summarize the same dated events the hindsight snapshots are built from, and the "
            "rule backend's keywords were written alongside them, so high agreement is "
            "expected; the disagreements that remain are listed at the end with the "
            "indicators behind them.",
            "",
        ]
    if metrics.missing_replay:
        what = "a proposals file" if metrics.proposal_level else "a reviewed replay snapshot"
        lines += [
            f"Quarters without {what} (not compared): {', '.join(metrics.missing_replay)}.",
            "",
        ]
    if runs:
        lines += ["## Date filtering", ""]
        lines += [
            "| Quarter | Documents dated at or before its end | Read this quarter | "
            "Proposals | Discarded by the checks |",
            "|---|---|---|---|---|",
        ]
        for r in runs:
            lines.append(
                f"| {r.quarter} | {r.visible} | {r.read} | {r.proposals} | {r.discarded} |"
            )
        lines.append("")
    if metrics.proposal_level:
        lines += _proposal_table(metrics)
    # summary
    text_a = metrics.share(TEXT_VARIABLES)
    unread = metrics.share(TEXT_VARIABLES, "unread")
    moved = metrics.share(TEXT_VARIABLES, "moved")
    res_a = metrics.share(RESOURCE_VARIABLES)
    bc = [m for v in BELIEF_COMMIT for m in metrics.matched(v)]
    within = [m for m in bc if abs(m.lag_quarters or 0) <= 1]
    documented_bc = sum(
        1 for v in BELIEF_COMMIT for m in metrics.matches.get(v, []) if m.documented
    )
    false_total = sum(len(metrics.false_flips(v)) for v in TEXT_VARIABLES)
    missed_total = sum(len(metrics.missed_flips(v)) for v in TEXT_VARIABLES)
    lines += [
        "## Summary against section 9",
        "",
        f"- Text-derived variables, exact level agreement over variable-quarters: {_pct(*text_a)}.",
        f"- For scale: a replay that reads nothing (every text variable at its initial level) "
        f"agrees on {_pct(*unread)}. Split by the hindsight level: where it is still the "
        f"initial one, this replay agrees on {_pct(text_a[0] - moved[0], unread[0])}; where it "
        f"has moved, on {_pct(*moved)}.",
        f"- Resource variables: {_pct(*res_a)}, but they are copied from the hindsight "
        "snapshots (they come from the datasets), so this checks the copy, not a reading; the "
        "section 9 target of 80 percent for resource variables is not tested by a replay of "
        "documents.",
        f"- Belief and commitment flips: {len(within)} of {documented_bc} documented flips "
        f"replayed within one quarter ({len(bc)} matched within {MATCH_WINDOW} quarters).",
        f"- False flips (replayed, no documented flip to the same level within {MATCH_WINDOW} "
        f"quarters): {false_total}. Missed flips: {missed_total}.",
        "",
        "## Agreement per variable",
        "",
        "| Group | Variable | Agreement | Reading nothing | "
        "Quarters that disagree (hindsight / replay) |",
        "|---|---|---|---|---|",
    ]
    for group, names in GROUPS.items():
        for name in names:
            a = metrics.agreement.get(name, (0, 0))
            bad = [
                f"{q} ({_lv(h)} / {_lv(r)})"
                for q, (h, r) in metrics.levels.get(name, {}).items()
                if h != r
            ]
            lines.append(
                f"| {group} | `{name}` | {_pct(*a)} | {_pct(*metrics.unread.get(name, (0, 0)))} "
                f"| {', '.join(bad) or '-'} |"
            )
    for name in RESOURCE_VARIABLES:
        lines.append(
            f"| resources (copied) | `{name}` | {_pct(*metrics.agreement.get(name, (0, 0)))} "
            "| - | - |"
        )
    lines += [
        "",
        "## Flips: lag against the documented date",
        "",
        "A documented flip is a change of level between consecutive hindsight snapshots, dated "
        "by the event that set the new level; a replayed flip is the same in the replay "
        "snapshots, dated by the "
        + ("proposal (treated as accepted)" if metrics.proposal_level else "accepted proposal")
        + " that set it. Lag is replay minus documented "
        "(positive: the replay is late).",
        "",
        "| Variable | Level | Documented (quarter, date) | Replayed (quarter, date) | "
        "Lag (quarters) | Lag (days) |",
        "|---|---|---|---|---|---|",
    ]
    for name in TEXT_VARIABLES:
        for m in metrics.matches.get(name, []):
            d, r = m.documented, m.replayed
            level = _lv((d or r).after)
            dcell = f"{d.quarter}, {d.observed}" if d else "none (false flip)"
            rcell = f"{r.quarter}, {r.observed}" if r else "none (missed)"
            lq = "-" if m.lag_quarters is None else f"{m.lag_quarters:+d}"
            ld = "-" if m.lag_days is None else f"{m.lag_days:+d}"
            lines.append(f"| `{name}` | {level} | {dcell} | {rcell} | {lq} | {ld} |")
    lines.append("")
    lines += _disagreements(metrics)
    return "\n".join(lines)


def _proposal_table(metrics: Metrics) -> list[str]:
    lines = [
        "## Proposals per variable",
        "",
        "Every proposal kept by the extractor's checks over the quarters, by level.",
        "",
        "| Variable | Proposals | By level |",
        "|---|---|---|",
    ]
    for name in TEXT_VARIABLES:
        c = metrics.counts.get(name, Counter())
        levels = ", ".join(f"{lv} {n}" for lv, n in sorted(c.items(), key=lambda x: -x[1]))
        lines.append(f"| `{name}` | {sum(c.values())} | {levels or '-'} |")
    total = sum(sum(c.values()) for c in metrics.counts.values())
    lines += [f"| all | {total} | |", ""]
    return lines


def _first_of_runs(quarters: Sequence[str]) -> list[str]:
    out, prev = [], None
    for q in quarters:
        if prev is None or _qindex(q) != _qindex(prev) + 1:
            out.append(q)
        prev = q
    return out


def _cite(entry: dict[str, Any]) -> str:
    inds = entry.get("indicators") or []
    if not inds:
        return f"`{_lv(entry['level'])}` ({entry.get('confidence')}, no indicator)"
    ind = inds[-1]
    value = " ".join(str(ind.get("value", "")).split())
    return f'`{_lv(entry["level"])}` from {ind.get("observed")}: "{value}"'


def _disagreements(metrics: Metrics) -> list[str]:
    """For the first quarter of each run of disagreement, the indicator behind each side."""
    if not metrics.details:
        return []
    lines = [
        "## Disagreements and the indicators behind them",
        "",
        "At the first quarter of each run of disagreement: the hindsight level with its latest "
        "event, and the replay level with the latest "
        + ("proposal's (unreviewed) quote." if metrics.proposal_level else "accepted quote."),
        "",
    ]
    for name in TEXT_VARIABLES:
        per_q = metrics.details.get(name)
        if not per_q:
            continue
        for q in _first_of_runs(sorted(per_q, key=_qindex)):
            h, r = per_q[q]
            lines.append(f"- `{name}`, {q}: hindsight {_cite(h)}; replay {_cite(r)}.")
    lines.append("")
    return lines
