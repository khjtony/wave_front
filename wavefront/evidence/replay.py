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
proposal was reviewed. It measures the backend, not the reviewed evidence. With
``drop_rejected`` (``--drop-rejected``) it measures a partly reviewed run: the proposals a
reviewer rejected are removed (they neither propose nor set a level), the accepted ones and the
pending ones count as accepted, and a ``retrospective?`` proposal is applied only when a
reviewer accepted it, as in review.

The harness rules (:mod:`.harness_rules`: ``two-document`` and ``no-retrospective``, both on
by default) are recorded in every proposals file the replay writes and act on review, on
auto-accept and on the measurement alike; every report states which rules were in force.
With a paid backend the replay caches each document's answer under ``<out>/cache/`` (see
:mod:`.extract.cache`), so a run stopped by an error resumes, when run again, from the
documents it has not read; :func:`plan` (``wf replay --dry-run``) counts what a run would send.

The episode (:mod:`.episodes`; ``episode="ww2"`` by default, ``"cw"`` for the Cold War) names
the text variables, the prompt, the periods and the hindsight snapshots. A Cold War replay runs
by year: the period ``1958`` reads the documents dated to 31 December 1957 and its snapshot is
the state on 1 January 1958; its metrics are those of :mod:`.replay_cw`.

Then :func:`compare` sets the replay snapshots against the hindsight snapshots: per-variable
agreement of the levels at each quarter's end, the lag of each replayed flip against the
documented flip, false flips and missed flips; :func:`render_report` writes the Markdown
metrics report. Resource variables are copied from the hindsight snapshots, not extracted:
their agreement is shown but is not a test of anything.

A hindsight snapshot may give a set of levels for a variable over a contested window
(docs/ambiguous_levels.md). A replayed level then agrees when it is in the set; those
variable-quarters are also counted separately (``Metrics.ambiguous``) and reported on their
own line. A documented flip across a window (concrete level ``a`` before it, ``b != a``
after it) is dated by the window: its quarter is the window's first and ``window_end`` the
first concrete quarter after it, and a replayed flip to ``b`` anywhere in that range has lag
0. A replayed flip inside a window to a level of the window's set that answers no documented
flip is listed as a flip inside an ambiguous window, not as a false flip.
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
from .episodes import Episode, get_episode
from .extract.backend import Backend, ExtractError
from .extract.cache import CachedBackend
from .extract.extractor import extract, write_proposals
from .extract.schema import RESOURCE_VARIABLES, TEXT_VARIABLES, text_variables
from .harness_rules import (
    BLOCKED,
    CORROBORATING,
    DEFAULT_RULES,
    HELD,
    OK,
    RETROSPECTIVE,
    describe_rules,
    record_key,
)
from .review import (
    AUTO_REVIEWER,
    DEFAULT_HINDSIGHT,
    build_snapshot,
    decide,
    directory_episode,
    directory_rules,
    proposal_files,
    rebuild_snapshots,
    review_gating,
)
from .snapshot import level_set

__all__ = [
    "BELIEF_COMMIT",
    "CHARS_PER_TOKEN",
    "Flip",
    "Metrics",
    "ReplayError",
    "backend_info",
    "compare",
    "measured_snapshots",
    "parse_quarters",
    "plan",
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
REVIEW_STATUSES = ("accepted", "rejected", "pending")
AUTO_RETRO_NOTE = (
    "auto-rejected by wf replay --auto-accept: retrospective? under the no-retrospective rule "
    "is never applied automatically (synthetic fixture run, not a review)"
)
CHARS_PER_TOKEN = 4  # a rough planning figure for English prose; the API's count is exact


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


def _read_before(proposals_dir: Path, first_quarter: str, ep: Episode | None = None) -> set[str]:
    """The documents read by the proposals files of the quarters before ``first_quarter``."""
    ep = get_episode(ep)
    read: set[str] = set()
    if proposals_dir.exists():
        files = proposal_files(proposals_dir)
        if files and directory_episode(files) != ep.name:
            raise ReplayError(
                f"{proposals_dir} holds proposals of the episode {directory_episode(files)}, "
                f"not {ep.name}; use another --out"
            )
        first_end = ep.cutoff(first_quarter)
        for _p, data in proposal_files(proposals_dir):
            if date.fromisoformat(data["until"]) < first_end:
                read.update(d["id"] for d in data["documents"])
    return read


def _reviewed(path: Path) -> int:
    """The proposals of an existing file that carry a decision other than an auto-accept."""
    if not path.exists():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    return sum(
        1 for r in data.get("proposals", []) if any(not d.get("auto") for d in r["decisions"])
    )


def _cached(backend: Backend, out_dir: Path, cache: bool) -> Backend:
    if not cache or backend.name == "rules" or isinstance(backend, CachedBackend):
        return backend
    return CachedBackend(backend, out_dir / "cache" / backend.name)


def replay(
    corpus: Corpus,
    quarters: Sequence[str],
    out_dir: str | Path,
    backend: Backend,
    *,
    auto_accept: bool = False,
    hindsight_dir: str | Path | None = None,
    rules: Sequence[str] = DEFAULT_RULES,
    workers: int = 1,
    cache: bool = True,
    episode: str | Episode | None = None,
) -> list[QuarterRun]:
    """Run the blind replay over ``quarters`` (see the module docstring). ``rules`` are the
    harness rules recorded in the proposals files; ``workers`` documents are read at a time;
    a backend other than the rule backend is cached under ``<out>/cache/`` unless ``cache``
    is false. ``quarters`` are the periods of ``episode`` (default WW2): years for the Cold
    War."""
    ep = get_episode(episode)
    if auto_accept and not corpus.synthetic:
        raise ReplayError(
            "--auto-accept is only for the synthetic fixture corpus; a real corpus needs wf review"
        )
    out_dir = Path(out_dir)
    proposals_dir = out_dir / "proposals"
    read_before = _read_before(proposals_dir, quarters[0], ep)
    backend = _cached(backend, out_dir, cache)
    variables = text_variables(episode=ep)
    runs: list[QuarterRun] = []
    for quarter in quarters:
        reviewed = _reviewed(proposals_dir / f"{quarter}.json")
        if reviewed:
            raise ReplayError(
                f"{quarter}: {reviewed} proposal(s) of {proposals_dir / quarter}.json carry a "
                "reviewer's decision, and replaying the quarter would rewrite the file with "
                "every proposal pending; start --quarters after it, or use another --out"
            )
    for quarter in quarters:
        until = ep.cutoff(quarter)
        visible = sum(1 for _ in corpus.iter_documents(until=until))
        usage_before = Counter(getattr(backend, "usage", None) or {})
        hits_before = getattr(backend, "hits", 0), getattr(backend, "misses", 0)
        try:
            result = extract(
                corpus,
                until=until,
                backend=backend,
                variables=variables,
                skip_ids=read_before,
                workers=workers,
            )
        except ExtractError as exc:  # pragma: no cover - extract records errors
            raise ReplayError(f"{quarter}: {exc}") from exc
        if result.errors:
            raise ReplayError(
                f"{quarter}: the backend failed on {len(result.errors)} document(s), so the "
                f"quarter's proposals would be incomplete: {result.errors[0]['error']}"
                + (
                    "; the documents read are cached: run the same command again to resume"
                    if isinstance(backend, CachedBackend)
                    else ""
                )
            )
        path = proposals_dir / f"{quarter}.json"
        info = backend_info(backend)
        usage = Counter(getattr(backend, "usage", None) or {}) - usage_before
        if usage:
            info["usage"] = dict(usage)
        if isinstance(backend, CachedBackend):
            info["cache"] = {
                "hits": backend.hits - hits_before[0],
                "misses": backend.misses - hits_before[1],
            }
        data = write_proposals(
            path,
            result,
            label=quarter,
            corpus=corpus.describe(),
            backend=info,
            harness_rules=rules,
            episode=None if ep.name == "ww2" else ep.name,
        )
        read_before.update(d.id for d in result.documents)
        snapshot = None
        if auto_accept:
            snapshot = _auto_decide(path, data, quarter, out_dir, hindsight_dir, ep)
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


def _auto_decide(
    path: Path,
    data: dict[str, Any],
    quarter: str,
    out_dir: Path,
    hindsight_dir: str | Path | None,
    ep: Episode | None = None,
) -> Path | None:
    """Synthetic runs only: accept what a measurement would count, reject (with a note)
    what the no-retrospective rule never applies automatically, and leave held and blocked
    proposals pending (they are not proposals for review). The gates are those of a
    measurement at the quarter's end, so an auto-accepted run and a measurement agree."""
    proposals_dir = path.parent
    files = proposal_files(proposals_dir)
    until = get_episode(ep).cutoff(quarter)
    upto = [f for f in files if date.fromisoformat(f[1]["until"]) <= until]
    records, index, gating = review_gating(upto, until, directory_rules(files), measure=True)
    accept, reject = [], []
    for rec in data["proposals"]:
        gate = gating.gates[index[record_key(rec)]]
        if gate is None:
            continue
        if gate.status in (OK, CORROBORATING):
            accept.append(rec["id"])
        elif gate.status == RETROSPECTIVE:
            reject.append(rec["id"])
    common = dict(
        reviewer=AUTO_REVIEWER, snapshots_dir=out_dir, hindsight_dir=hindsight_dir, auto=True
    )
    written: list[Path] = []
    if reject:
        written = decide(path, reject, "rejected", note=AUTO_RETRO_NOTE, **common)
    if accept:
        written = decide(path, accept, "accepted", note=AUTO_NOTE, **common)
    if not accept and not reject:
        # Nothing to decide in this quarter: rebuild so the quarter still has a snapshot.
        written = rebuild_snapshots(proposals_dir, out_dir, hindsight_dir=hindsight_dir)
    return next((w for w in written if w.stem == quarter), None)


@dataclass
class PlanRow:
    """What a replay of one quarter would send to the backend (``wf replay --dry-run``)."""

    quarter: str
    visible: int
    to_read: int
    cached: int
    characters: int
    requests: int


def plan(
    corpus: Corpus,
    quarters: Sequence[str],
    out_dir: str | Path,
    backend: Backend,
    *,
    episode: str | Episode | None = None,
) -> list[PlanRow]:
    """Count, without calling the backend, what :func:`replay` would read per quarter: the
    documents not read by an earlier quarter's proposals file in ``out_dir``, those of them
    already in the cache (a resumed run does not send them), and the characters and requests
    (one per part of at most the backend's ``max_chars``) of the rest."""
    ep = get_episode(episode)
    out_dir = Path(out_dir)
    read_before = _read_before(out_dir / "proposals", quarters[0], ep)
    cached = _cached(backend, out_dir, True)
    variables = text_variables(episode=ep)
    parts = getattr(backend, "parts", None)
    rows: list[PlanRow] = []
    for quarter in quarters:
        until = ep.cutoff(quarter)
        visible = to_read = hits = chars = requests = 0
        for doc in corpus.iter_documents(until=until):
            visible += 1
            if doc.id in read_before:
                continue
            read_before.add(doc.id)
            to_read += 1
            if isinstance(cached, CachedBackend) and cached.cached(doc, variables):
                hits += 1
                continue
            chars += len(doc.text)
            requests += len(parts(doc)) if callable(parts) else 1
        rows.append(PlanRow(quarter, visible, to_read, hits, chars, requests))
    return rows


def backend_info(backend: Backend) -> dict[str, Any]:
    info: dict[str, Any] = {"name": backend.name}
    model = getattr(backend, "model", None)
    if isinstance(model, str) and model:
        info["model"] = model
    effort = getattr(backend, "effort", None)
    if isinstance(effort, str) and effort:
        info["effort"] = effort
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
    hindsight_dir: str | Path | None = None,
    rules: Sequence[str] | None = None,
    *,
    episode: str | Episode | None = None,
    drop_rejected: bool = False,
) -> dict[str, dict[str, Any]]:
    """Quarter-end snapshots, in memory, in which every proposal of the files in
    ``proposals_dir`` dated up to the quarter's end counts as accepted, whatever its review
    status (pending, accepted or rejected), unless the harness ``rules`` (default: those
    recorded in the files) hold it, block it or flag it ``retrospective?``. Built with
    :func:`.review.build_snapshot`, so the levels follow the same rules as reviewed snapshots;
    every indicator says NOT REVIEWED. Nothing is written. A quarter whose own proposals file
    is missing has no snapshot. The episode is the files' unless given.

    With ``drop_rejected`` the rejected proposals are removed first (as if never proposed),
    the accepted ones keep their reviewer's decision in their indicator, the pending ones
    count as accepted (NOT REVIEWED), and a ``retrospective?`` proposal is applied only if a
    reviewer accepted it."""
    files = proposal_files(proposals_dir)
    rules = directory_rules(files) if rules is None else tuple(rules)
    ep = get_episode(directory_episode(files) if episode is None else episode)
    if drop_rejected:
        files = _without_rejected(files)
    applies_back = (lambda r: r["status"] == "accepted") if drop_rejected else None
    labels = {data["label"] for _p, data in files}
    out: dict[str, dict[str, Any]] = {}
    for quarter in quarters:
        if quarter not in labels:
            continue
        until = ep.cutoff(quarter)
        upto = [f for f in files if date.fromisoformat(f[1]["until"]) <= until]
        _records, _index, gating = review_gating(
            upto, until, rules, measure=True, episode=ep, applies_back=applies_back
        )
        records = [
            rec if drop_rejected and rec["status"] == "accepted" else _as_measured(rec)
            for rec in gating.in_force
        ]
        out[quarter] = build_snapshot(until, records, hindsight_dir=hindsight_dir, episode=ep)
    return out


def _without_rejected(
    files: Sequence[tuple[Path, dict[str, Any]]],
) -> list[tuple[Path, dict[str, Any]]]:
    """The proposals files with the proposals a reviewer rejected removed (not written)."""
    out = []
    for path, data in files:
        kept = [rec for rec in data["proposals"] if rec["status"] != "rejected"]
        out.append((path, {**data, "proposals": kept}))
    return out


def review_counts(proposals_dir: str | Path, quarters: Sequence[str]) -> Counter[str]:
    """The proposals of ``quarters`` by review status (accepted, rejected, pending)."""
    wanted = set(quarters)
    out: Counter[str] = Counter({s: 0 for s in REVIEW_STATUSES})
    for _p, data in proposal_files(proposals_dir):
        if data["label"] in wanted:
            out.update(rec["status"] for rec in data["proposals"])
    return out


def gate_counts(
    proposals_dir: str | Path,
    quarters: Sequence[str],
    rules: Sequence[str],
    *,
    episode: str | Episode | None = None,
    drop_rejected: bool = False,
) -> dict[str, Counter[str]]:
    """Per variable, how the harness ``rules`` classify the proposals of ``quarters`` at the
    last quarter's end, measured as in :func:`measured_snapshots` (without the rejected
    proposals with ``drop_rejected``)."""
    files = [f for f in proposal_files(proposals_dir) if f[1]["label"] in set(quarters)]
    if drop_rejected:
        files = _without_rejected(files)
    if not files:
        return {}
    ep = get_episode(directory_episode(files) if episode is None else episode)
    records, _index, gating = review_gating(
        files, ep.cutoff(quarters[-1]), rules, measure=True, episode=ep
    )
    return gating.counts(records)


def proposal_counts(
    proposals_dir: str | Path, quarters: Sequence[str], *, drop_rejected: bool = False
) -> dict[str, Counter[str]]:
    """The number of proposals per variable and level in the proposals files of ``quarters``
    (levels as strings); without the rejected ones with ``drop_rejected``."""
    wanted = set(quarters)
    counts: dict[str, Counter[str]] = {}
    for _p, data in proposal_files(proposals_dir):
        if data["label"] not in wanted:
            continue
        for rec in data["proposals"]:
            if drop_rejected and rec["status"] == "rejected":
                continue
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
    #: for a documented flip across a window of set-valued hindsight levels: the first
    #: concrete quarter after the window (``quarter`` is the window's first)
    window_end: str | None = None


def _gap(documented: Flip, replayed: Flip) -> int:
    """Quarters from the documented flip (or its window) to the replayed flip: 0 inside the
    window, positive when the replay is late."""
    r, lo = _qindex(replayed.quarter), _qindex(documented.quarter)
    hi = lo if documented.window_end is None else _qindex(documented.window_end)
    return 0 if lo <= r <= hi else r - hi if r > hi else r - lo


@dataclass
class FlipMatch:
    documented: Flip | None
    replayed: Flip | None

    @property
    def lag_quarters(self) -> int | None:
        if self.documented is None or self.replayed is None:
            return None
        return _gap(self.documented, self.replayed)

    @property
    def lag_days(self) -> int | None:
        if self.documented is None or self.replayed is None:
            return None
        if not self.documented.observed or not self.replayed.observed:
            return None
        if self.documented.window_end is not None:
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
    #: the harness rules in force (None: unknown, no proposals files)
    rules: tuple[str, ...] | None = None
    #: per variable, the proposals by harness gate status (proposal-level mode)
    gates: dict[str, Counter[str]] = field(default_factory=dict)
    #: True when the rejected proposals were removed from the measurement (--drop-rejected)
    drop_rejected: bool = False
    #: the proposals by review status (proposal-level mode)
    review: Counter[str] = field(default_factory=Counter)
    #: var -> (agree, total) over the quarters whose hindsight level is a set (agree: the
    #: replayed level is in it); these quarters are also counted in ``agreement``
    ambiguous: dict[str, tuple[int, int]] = field(default_factory=dict)
    #: var -> quarter -> the hindsight set of levels, for the set-valued quarters
    windows: dict[str, dict[str, tuple[Any, ...]]] = field(default_factory=dict)

    def matched(self, variable: str) -> list[FlipMatch]:
        return [m for m in self.matches.get(variable, []) if m.documented and m.replayed]

    def false_flips(self, variable: str) -> list[Flip]:
        return [
            m.replayed
            for m in self.matches.get(variable, [])
            if m.documented is None and not self._in_window(m.replayed)
        ]

    def window_flips(self, variable: str) -> list[Flip]:
        """Replayed flips that answer no documented flip but land inside a window of
        set-valued hindsight levels on a level of the window's set (not false flips)."""
        return [
            m.replayed
            for m in self.matches.get(variable, [])
            if m.documented is None and self._in_window(m.replayed)
        ]

    def _in_window(self, flip: Flip | None) -> bool:
        if flip is None:
            return False
        window = self.windows.get(flip.variable, {}).get(flip.quarter)
        return window is not None and flip.after in window

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
    """The flips of ``name`` along ``series``. Between concrete levels a flip is a change
    from one quarter to the next; a run of set-valued quarters between concrete levels
    ``a != b`` gives one flip ``a -> b`` dated by the window (module docstring); a missing
    snapshot breaks the series."""
    out = []
    last: Any = None  # the last concrete level, or None
    known = False
    start: str | None = None  # the first quarter of the current run of set-valued levels
    for q, s in series:
        if s is None:
            known, start = False, None
            continue
        entry = s["variables"][name]
        levels = level_set(entry)
        if len(levels) > 1:
            if start is None:
                start = q
            continue
        level = levels[0]
        if known and last != level:
            if start is None:
                out.append(Flip(name, q, last, level, _setting_date(entry)))
            else:
                out.append(Flip(name, start, last, level, _setting_date(entry), window_end=q))
        last, known, start = level, True, None
    return out


def _match(documented: list[Flip], replayed: list[Flip]) -> list[FlipMatch]:
    """Pair each documented flip with the nearest unmatched replayed flip to the same level
    within :data:`MATCH_WINDOW` quarters; the rest are missed or false flips."""
    free = list(replayed)
    out: list[FlipMatch] = []
    for d in documented:
        candidates = [r for r in free if r.after == d.after and abs(_gap(d, r)) <= MATCH_WINDOW]
        if candidates:
            best = min(candidates, key=lambda r: (abs(_gap(d, r)), _qindex(r.quarter)))
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
    rules: Sequence[str] | None = None,
    episode: str | Episode | None = None,
    drop_rejected: bool = False,
) -> Metrics:
    """The section 9 metrics of the replay snapshots in ``replay_dir`` against the hindsight
    snapshots, for ``quarters``. The baseline for flips at the first quarter is the hindsight
    snapshot of the previous quarter and, for the replay, its snapshot of that quarter if
    there is one, else the ontology's initial levels.

    With ``measure_proposals`` the replay snapshots are not read: they are built in memory
    from every proposal in ``replay_dir/proposals`` as if accepted (:func:`measured_snapshots`)
    under the harness ``rules`` (default: those recorded in the files), and the metrics say
    so; with ``drop_rejected`` as well the rejected proposals are left out (a partly
    reviewed run: accepted and pending count, rejected do not).

    For the Cold War (``episode="cw"``) this is :func:`.replay_cw.compare` (``quarters`` are
    years; ``hindsight_dir`` may be ``None`` for the episode's)."""
    if drop_rejected and not measure_proposals:
        raise ReplayError("drop_rejected goes with measure_proposals only")
    if get_episode(episode).name == "cw":
        if drop_rejected:
            raise ReplayError("drop_rejected is implemented for the WW2 replay only")
        from .replay_cw import compare as compare_cw

        return compare_cw(  # type: ignore[return-value]
            replay_dir,
            quarters,
            None if hindsight_dir == DEFAULT_HINDSIGHT else hindsight_dir,
            measure_proposals=measure_proposals,
            rules=rules,
        )
    replay_dir, hindsight_dir = Path(replay_dir), Path(hindsight_dir)
    prev = _qname(_qindex(quarters[0]) - 1)
    measured: dict[str, dict[str, Any]] = {}
    files = proposal_files(replay_dir / "proposals") if (replay_dir / "proposals").exists() else []
    in_force = tuple(rules) if rules is not None else directory_rules(files) if files else None
    if measure_proposals:
        measured = measured_snapshots(
            replay_dir / "proposals",
            quarters,
            hindsight_dir,
            in_force,
            drop_rejected=drop_rejected,
        )
    hind = [(prev, _read(hindsight_dir / f"{prev}.json"))]
    rep = [(prev, _initial() if measure_proposals else _read(replay_dir / f"{prev}.json"))]
    if rep[0][1] is None:
        rep[0] = (prev, _initial())
    for q in quarters:
        hind.append((q, _read(hindsight_dir / f"{q}.json")))
        rep.append((q, measured.get(q) if measure_proposals else _read(replay_dir / f"{q}.json")))
    m = Metrics(quarters=list(quarters), missing_replay=[q for q, s in rep[1:] if s is None])
    m.rules = in_force
    if measure_proposals:
        m.proposal_level = True
        m.drop_rejected = drop_rejected
        m.review = review_counts(replay_dir / "proposals", quarters)
        m.counts = proposal_counts(replay_dir / "proposals", quarters, drop_rejected=drop_rejected)
        m.gates = gate_counts(
            replay_dir / "proposals", quarters, in_force or (), drop_rejected=drop_rejected
        )
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
        agree = total = unread = moved = moved_agree = amb = amb_agree = 0
        for (q, h), (_q, r) in zip(hind[1:], rep[1:], strict=True):
            if h is None or r is None or name not in h["variables"]:
                continue
            hl, rl = _level(h["variables"][name]), _level(r["variables"][name])
            per_q[q] = (hl, rl)
            ok = _agrees(hl, rl)
            total += 1
            agree += ok
            initial = _agrees(hl, init.get(name))
            unread += initial
            if not initial:
                moved += 1
                moved_agree += ok
            if isinstance(hl, tuple):
                amb += 1
                amb_agree += ok
                m.windows.setdefault(name, {})[q] = hl
            if not ok:
                m.details.setdefault(name, {})[q] = (h["variables"][name], r["variables"][name])
        m.levels[name] = per_q
        m.agreement[name] = (agree, total)
        m.unread[name] = (unread, total)
        m.moved[name] = (moved_agree, moved)
        if amb:
            m.ambiguous[name] = (amb_agree, amb)
        if name in TEXT_VARIABLES:
            m.matches[name] = _match(_flips(hind, name), _flips(rep, name))
    return m


def _level(entry: dict[str, Any]) -> Any:
    """A snapshot entry's level, or the tuple of its levels when it gives a set."""
    levels = level_set(entry)
    return levels[0] if len(levels) == 1 else levels


def _agrees(hindsight: Any, replayed: Any) -> bool:
    """Whether a replayed level (or set, for a copied set-valued entry) agrees with a
    hindsight level or set: every replayed level is in the hindsight set."""
    h = hindsight if isinstance(hindsight, tuple) else (hindsight,)
    r = replayed if isinstance(replayed, tuple) else (replayed,)
    return all(any(x == y for y in h) for x in r)


# -- the report -----------------------------------------------------------------------------


def _pct(agree: int, total: int) -> str:
    return f"{agree}/{total} ({100 * agree / total:.0f}%)" if total else "n/a"


def _lv(level: Any) -> str:
    if isinstance(level, tuple):
        return "{" + ", ".join(_lv(x) for x in level) + "}"
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
    its first line and its summary. The metrics of a Cold War replay
    (:class:`.replay_cw.YearMetrics`) are rendered by :func:`.replay_cw.render_report`."""
    if not isinstance(metrics, Metrics):
        from .replay_cw import render_report as render_cw

        return render_cw(
            metrics, title=title, corpus=corpus, backend=backend, command=command, runs=runs
        )
    synthetic = bool(corpus.get("synthetic"))
    lines: list[str] = []
    if metrics.proposal_level and metrics.drop_rejected:
        r = metrics.review
        lines.append(
            "PROPOSAL-LEVEL MEASUREMENT, REJECTED PROPOSALS DROPPED: of the "
            f"{sum(r.values())} proposals, accepted by a reviewer {r['accepted']}, rejected "
            f"{r['rejected']}, not reviewed {r['pending']}. The rejected ones "
            "are left out; the accepted ones and the unreviewed ones are treated as accepted "
            "to compute these metrics, no replay snapshot was written, and a level or quote "
            "below may be an unreviewed reading."
        )
        lines.append("")
    elif metrics.proposal_level:
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
        f"- Backend: {backend.get('name')}"
        + (f", model `{backend['model']}`" if backend.get("model") else "")
        + (f", effort {backend['effort']}" if backend.get("effort") else ""),
        "- Harness rules in force: "
        + (
            describe_rules(metrics.rules)
            if metrics.rules is not None
            else "unknown (no proposals files in the replay directory)"
        )
        + ' ([docs/replay_harness.md](../docs/replay_harness.md), section "Harness rules")',
        "- Review: "
        + (
            "auto-accepted (synthetic run only)"
            if metrics.auto_accepted
            else "partial: proposal-level measurement without the rejected proposals "
            f"({metrics.review['accepted']} accepted, {metrics.review['rejected']} rejected and "
            f"left out, {metrics.review['pending']} pending treated as accepted; nothing "
            "written)"
            if metrics.proposal_level and metrics.drop_rejected
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
        if metrics.rules:
            lines += _gate_table(metrics)
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
        *_ambiguous_summary(metrics),
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
                if not _agrees(h, r)
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
            dcell = (
                f"{d.quarter} to {d.window_end} (ambiguous window), {d.observed}"
                if d and d.window_end
                else f"{d.quarter}, {d.observed}"
                if d
                else "none (inside an ambiguous window)"
                if metrics._in_window(r)
                else "none (false flip)"
            )
            rcell = f"{r.quarter}, {r.observed}" if r else "none (missed)"
            lq = "-" if m.lag_quarters is None else f"{m.lag_quarters:+d}"
            ld = "-" if m.lag_days is None else f"{m.lag_days:+d}"
            lines.append(f"| `{name}` | {level} | {dcell} | {rcell} | {lq} | {ld} |")
    lines.append("")
    lines += _disagreements(metrics)
    return "\n".join(lines)


def _ambiguous_summary(metrics: Metrics) -> list[str]:
    """The set-valued hindsight quarters, reported on their own (docs/ambiguous_levels.md)."""
    if not metrics.ambiguous:
        return []
    text = [n for n in TEXT_VARIABLES if n in metrics.ambiguous]
    parts = [f"`{n}` {_pct(*metrics.ambiguous[n])}" for n in metrics.ambiguous]
    windowed = sum(len(metrics.window_flips(v)) for v in TEXT_VARIABLES)
    return [
        "- Set-valued hindsight levels (contested windows; a replayed level in the set counts "
        "as agreeing above): the replay is in the set on "
        f"{_pct(*metrics.share(text, 'ambiguous'))} of the text variables' set-valued "
        f"quarters ({'; '.join(parts)}). Replayed flips inside a window, not counted as "
        f"false: {windowed}."
    ]


def _proposal_table(metrics: Metrics) -> list[str]:
    lines = [
        "## Proposals per variable",
        "",
        "Every proposal kept by the extractor's checks over the quarters, by level"
        + (", less the rejected ones." if metrics.drop_rejected else "."),
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


_GATE_COLUMNS = (
    (OK, "Shown and counted"),
    (HELD, "Held: one document"),
    (CORROBORATING, "First of two documents"),
    (BLOCKED, "Blocked: monotone, back"),
    (RETROSPECTIVE, "retrospective? (not counted)"),
)


def _gate_table(metrics: Metrics) -> list[str]:
    lines = [
        "## What the harness rules did",
        "",
        "Every proposal of the quarters, classified at the last quarter's end under "
        f"{describe_rules(metrics.rules or ())}. Only the first column is counted by the "
        "metrics; a flip of a variable under the two-document rule is counted at, and dated "
        'by, the proposal of its second document (the first is listed under "First of two '
        'documents").',
        "",
        "| Variable | Proposals | " + " | ".join(t for _s, t in _GATE_COLUMNS) + " |",
        "|---|---|" + "---|" * len(_GATE_COLUMNS),
    ]
    totals: Counter[str] = Counter()
    for name in TEXT_VARIABLES:
        c = metrics.gates.get(name, Counter())
        totals.update(c)
        cells = " | ".join(str(c.get(s, 0)) for s, _t in _GATE_COLUMNS)
        lines.append(f"| `{name}` | {sum(c.values())} | {cells} |")
    cells = " | ".join(str(totals.get(s, 0)) for s, _t in _GATE_COLUMNS)
    lines += [f"| all | {sum(totals.values())} | {cells} |", ""]
    return lines


def _first_of_runs(quarters: Sequence[str]) -> list[str]:
    out, prev = [], None
    for q in quarters:
        if prev is None or _qindex(q) != _qindex(prev) + 1:
            out.append(q)
        prev = q
    return out


def _cite(entry: dict[str, Any]) -> str:
    if "levels" in entry:
        why = " ".join(str(entry.get("ambiguity", "")).split())
        return f"`{_lv(_level(entry))}` (a set over a contested window: {why})"
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
