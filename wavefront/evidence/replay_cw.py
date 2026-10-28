"""The metrics of a Cold War replay (the episode ``cw`` of :mod:`.episodes`), by year.

A Cold War replay snapshot ``<year>.json`` is the state on 1 January of the year, read from
the documents dated to the 31 December before (:mod:`.replay` runs it, :mod:`.review` builds
it). :func:`compare` sets the three belief variables of each year against two series:

* the **hindsight** snapshots of cw_v1 (``snapshots/cw_v1/hindsight/<year>.json``): the
  hindsight truth of what each belief estimates (decisions D6 of docs/cw_v0_decisions.md): for
  ``belief_force_USA`` the record's ``count_USSR``, the number of Soviet intercontinental
  delivery vehicles in being in the bands of the belief (the owner's decision 7g;
  docs/cw_v1_decisions.md D9), which claim C6 compares the replayed estimate with; for
  ``belief_USSR_USA`` the record's American aims (``hostile`` throughout), which C7 compares
  with in 1983. ``belief_USA_USSR`` has no hindsight level (its truth is the swept
  hypothesis), so it is compared with the second series only;
* the **contemporaneous** beliefs of the record: the manual replay snapshots of cw_v1
  (``snapshots/cw_v1/replay/<year>.json``, 1957 to 1962 and 1983; decisions D7) where there is
  one, else the latest ``belief`` row visible on 1 January of ``data/cw/events.csv`` with
  ``data/cw/v1/events.csv`` (v1's ``belief`` rows of a variable replacing v0's, as the v1
  snapshots read them), the rule the manual replay follows. A blind replay that agrees with
  this series reads the documents as the record's coder did, without the coder's knowledge of
  the outcome.

The report (:func:`render_report`) gives, per year, the replayed level beside both, the C6
table (whether the replayed ``belief_force_USA`` exceeds the hindsight ``count_USSR``), the C7
line (``belief_USSR_USA`` in 1983), the flips of the replay against the documented flips of
the contemporaneous series with their lag in years, and the indicators behind each
disagreement. It reports inputs to C6 and C7, not their verdicts: the claims are computed on
the model from the snapshots (tests/coldwar).
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .episodes import CW, ROOT
from .harness_rules import describe_rules
from .replay import (
    _GATE_COLUMNS,
    QuarterRun,
    _lv,
    _pct,
    gate_counts,
    measured_snapshots,
    proposal_counts,
)
from .review import directory_rules, proposal_files
from .snapshot import level_set

__all__ = [
    "DEFAULT_EVENTS",
    "DEFAULT_MANUAL",
    "YearFlip",
    "YearMetrics",
    "compare",
    "contemporaneous",
    "render_report",
]

DEFAULT_MANUAL = ROOT / "snapshots" / "cw_v1" / "replay"
#: v0's events, then v1's (whose ``belief`` rows of a variable replace v0's)
DEFAULT_EVENTS = (ROOT / "data" / "cw" / "events.csv", ROOT / "data" / "cw" / "v1" / "events.csv")
C6_YEARS = ("1958", "1959", "1960", "1961")
C7_YEAR = "1983"


def _read(path: Path) -> dict[str, Any] | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _belief_rows(events: str | Path | Sequence[str | Path]) -> list[dict[str, str]]:
    """The ``belief`` rows of the events files in order, a later file's rows of a variable
    replacing the earlier files' rows of it (v1's rows of ``belief_force_USA``, on the count
    scale, replace v0's on the survivability scale)."""
    paths = [events] if isinstance(events, str | Path) else list(events)
    rows: list[dict[str, str]] = []
    for path in paths:
        if not Path(path).exists():
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            found = [
                r
                for r in csv.DictReader(line for line in fh if not line.startswith("#"))
                if r["series"] == "belief"
            ]
        names = {r["variable"] for r in found}
        rows = [r for r in rows if r["variable"] not in names] + found
    return rows


def contemporaneous(
    years: Sequence[str],
    manual_dir: str | Path = DEFAULT_MANUAL,
    events: str | Path | Sequence[str | Path] = DEFAULT_EVENTS,
) -> dict[str, dict[str, tuple[Any, str]]]:
    """Per belief variable and year, the contemporaneous level and where it comes from: the
    manual replay snapshot of the year if there is one, else the latest ``belief`` row of the
    events files (:func:`_belief_rows`) visible on 1 January of the year
    (``visible_year <= year``)."""
    rows = _belief_rows(events)
    out: dict[str, dict[str, tuple[Any, str]]] = {n: {} for n in CW.text_variables}
    for year in years:
        manual = _read(Path(manual_dir) / f"{year}.json")
        for name in CW.text_variables:
            if manual is not None and name in manual["variables"]:
                out[name][year] = (manual["variables"][name]["level"], "manual replay")
                continue
            found = [
                r
                for r in rows
                if r["variable"] == name
                and r["series"] == "belief"
                and int(r["visible_year"]) <= int(year)
            ]
            if found:
                row = max(found, key=lambda r: int(r["visible_year"]))
                out[name][year] = (row["level"], f"events.csv ({row['event']})")
    return out


@dataclass(frozen=True)
class YearFlip:
    """A change of level of ``variable`` between 1 January of the previous year and of
    ``year``; ``observed`` is the date of the indicator that set it (replay only)."""

    variable: str
    year: str
    before: Any
    after: Any
    observed: str | None = None


@dataclass
class YearMetrics:
    years: list[str]
    missing_replay: list[str]
    #: var -> year -> replayed level
    replay: dict[str, dict[str, Any]] = field(default_factory=dict)
    #: var -> year -> the replay snapshot's entry (for the indicators)
    entries: dict[str, dict[str, dict[str, Any]]] = field(default_factory=dict)
    #: var -> year -> hindsight level of the variable's truth (absent: no hindsight level;
    #: a tuple: the hindsight snapshot gives a set of levels, docs/ambiguous_levels.md)
    hindsight: dict[str, dict[str, Any]] = field(default_factory=dict)
    #: var -> year -> (contemporaneous level, its source)
    contemporaneous: dict[str, dict[str, tuple[Any, str]]] = field(default_factory=dict)
    #: var -> list of (documented contemporaneous flip or None, replayed flip or None)
    matches: dict[str, list[tuple[YearFlip | None, YearFlip | None]]] = field(default_factory=dict)
    auto_accepted: bool = False
    proposal_level: bool = False
    counts: dict[str, Counter[str]] = field(default_factory=dict)
    gates: dict[str, Counter[str]] = field(default_factory=dict)
    rules: tuple[str, ...] | None = None

    def agreement(self, name: str, against: str) -> tuple[int, int]:
        """(agree, total) of the replay with ``hindsight`` or ``contemporaneous``; against a
        set-valued hindsight level, a replayed level in the set agrees."""
        table = self.hindsight if against == "hindsight" else self.contemporaneous
        agree = total = 0
        for year, level in self.replay.get(name, {}).items():
            other = table.get(name, {}).get(year)
            if other is None:
                continue
            other = other[0] if against == "contemporaneous" else other
            total += 1
            agree += level in other if isinstance(other, tuple) else level == other
        return agree, total

    def exceeds(self, year: str, series: str = "replay") -> bool | None:
        """Whether ``belief_force_USA`` of ``series`` (``replay`` or ``contemporaneous``)
        exceeds the hindsight ``count_USSR`` in ``year`` (C6 (a)); ``None`` when either is
        missing. Against a set-valued hindsight level the answer is ``True`` when the belief
        exceeds every member, ``False`` when it exceeds none, and ``None`` when it depends on
        the member (fragile)."""
        levels = CW.variable("belief_force_USA").levels
        if series == "replay":
            belief = self.replay.get("belief_force_USA", {}).get(year)
        else:
            belief = self.contemporaneous.get("belief_force_USA", {}).get(year, (None,))[0]
        truth = self.hindsight.get("belief_force_USA", {}).get(year)
        if belief is None or truth is None:
            return None
        members = truth if isinstance(truth, tuple) else (truth,)
        answers = {levels.index(belief) > levels.index(t) for t in members}
        return answers.pop() if len(answers) == 1 else None


def _flips(series: dict[str, Any], name: str, observed: dict[str, str | None]) -> list[YearFlip]:
    years = sorted(series, key=int)
    return [
        YearFlip(name, b, series[a], series[b], observed.get(b))
        for a, b in zip(years, years[1:], strict=False)
        if int(b) == int(a) + 1 and series[a] != series[b]
    ]


def _match(
    documented: list[YearFlip], replayed: list[YearFlip]
) -> list[tuple[YearFlip | None, YearFlip | None]]:
    free = list(replayed)
    out: list[tuple[YearFlip | None, YearFlip | None]] = []
    for d in documented:
        near = [
            r
            for r in free
            if r.after == d.after and abs(int(r.year) - int(d.year)) <= CW.match_window
        ]
        if near:
            best = min(near, key=lambda r: (abs(int(r.year) - int(d.year)), int(r.year)))
            free.remove(best)
            out.append((d, best))
        else:
            out.append((d, None))
    return out + [(None, r) for r in free]


def compare(
    replay_dir: str | Path,
    years: Sequence[str],
    hindsight_dir: str | Path | None = None,
    *,
    measure_proposals: bool = False,
    rules: Sequence[str] | None = None,
    manual_dir: str | Path = DEFAULT_MANUAL,
    events: str | Path | Sequence[str | Path] = DEFAULT_EVENTS,
) -> YearMetrics:
    """The Cold War replay of ``years`` in ``replay_dir`` against the hindsight snapshots and
    the contemporaneous beliefs (see the module docstring). With ``measure_proposals`` the
    replay snapshots are built in memory from every proposal as if accepted
    (:func:`.replay.measured_snapshots`), and the metrics say so. The flips are taken
    between consecutive years of ``years``; the year before the first is the baseline (its
    replay snapshot if there is one, else the initial levels)."""
    for y in years:
        CW.index(y)
    replay_dir = Path(replay_dir)
    hindsight_dir = CW.hindsight if hindsight_dir is None else Path(hindsight_dir)
    proposals = replay_dir / "proposals"
    files = proposal_files(proposals) if proposals.exists() else []
    in_force = tuple(rules) if rules is not None else directory_rules(files) if files else None
    if measure_proposals:
        snaps = measured_snapshots(proposals, years, hindsight_dir, in_force, episode=CW)
    else:
        snaps = {y: s for y in years if (s := _read(replay_dir / f"{y}.json")) is not None}
    m = YearMetrics(years=list(years), missing_replay=[y for y in years if y not in snaps])
    m.rules = in_force
    m.proposal_level = measure_proposals
    if measure_proposals:
        m.counts = proposal_counts(proposals, years)
        m.gates = gate_counts(proposals, years, in_force or (), episode=CW)
    m.auto_accepted = any(
        "AUTO-ACCEPTED" in ind.get("rule", "")
        for s in snaps.values()
        for entry in s["variables"].values()
        for ind in entry.get("indicators", [])
    )
    m.contemporaneous = contemporaneous(years, manual_dir, events)
    prev = str(int(years[0]) - 1)
    base = None if measure_proposals else _read(replay_dir / f"{prev}.json")
    for name in CW.text_variables:
        init = CW.variable(name).init
        truth = CW.truth_of(name)
        series = {prev: base["variables"][name]["level"] if base else init}
        observed: dict[str, str | None] = {}
        m.replay[name], m.entries[name], m.hindsight[name] = {}, {}, {}
        for y in years:
            h = _read(hindsight_dir / f"{y}.json")
            if h is not None and truth in h["variables"]:
                found = level_set(h["variables"][truth])
                m.hindsight[name][y] = found[0] if len(found) == 1 else found
            if y not in snaps:
                continue
            entry = snaps[y]["variables"][name]
            m.replay[name][y] = series[y] = entry["level"]
            m.entries[name][y] = entry
            inds = entry.get("indicators") or []
            observed[y] = inds[0].get("observed") if inds else None
        documented_series = {y: lv for y, (lv, _src) in m.contemporaneous[name].items()}
        prior = contemporaneous([prev], manual_dir, events)[name].get(prev)
        documented_series[prev] = prior[0] if prior else init
        m.matches[name] = _match(
            _flips(documented_series, name, {}), _flips(series, name, observed)
        )
    return m


# -- the report -----------------------------------------------------------------------------


def _cite(entry: dict[str, Any] | None) -> str:
    if not entry:
        return "-"
    if "levels" in entry:
        why = " ".join(str(entry.get("ambiguity", "")).split())
        return f"`{_lv(level_set(entry))}` (a set over a contested window: {why})"
    inds = entry.get("indicators") or []
    if not inds:
        return f"`{_lv(entry['level'])}` ({entry.get('confidence')}, no indicator)"
    ind = inds[-1]
    value = " ".join(str(ind.get("value", "")).split())
    return f'`{_lv(entry["level"])}` from {ind.get("observed")}: "{value}"'


def _cell(value: Any) -> str:
    return "-" if value is None else _lv(value)


def render_report(
    metrics: YearMetrics,
    *,
    title: str,
    corpus: dict[str, Any],
    backend: dict[str, Any],
    command: str,
    runs: Sequence[QuarterRun] = (),
) -> str:
    """The Markdown metrics report of a Cold War replay. A synthetic, auto-accepted or
    proposal-level run says so first."""
    synthetic = bool(corpus.get("synthetic"))
    lines: list[str] = []
    if metrics.proposal_level:
        lines += [
            "PROPOSAL-LEVEL MEASUREMENT: no proposal below was reviewed. Every proposal the "
            "backend made was treated as if accepted to compute these metrics, no replay "
            "snapshot was written, and the levels and quotes below are the backend's "
            "unreviewed readings, not evidence accepted by a reviewer.",
            "",
        ]
    if synthetic or metrics.auto_accepted:
        lines += [
            "SYNTHETIC RUN: the corpus is a fixture written for pipeline tests, every proposal "
            "was auto-accepted without review, and nothing below is evidence about 1947 to "
            "1991. It measures the mechanics of the harness only.",
            "",
        ]
        title = f"{title} (SYNTHETIC)" if "SYNTHETIC" not in title.upper() else title
    lines += [f"# {title}", ""]
    y0, y1 = metrics.years[0], metrics.years[-1]
    lines += [
        f"- Years: {y0} to {y1} ({len(metrics.years)}); the snapshot of a year is the state on "
        "its 1 January, read from the documents dated to the 31 December before.",
        f"- Corpus: {corpus.get('source')}"
        + (f", `{corpus['root']}`" if corpus.get("root") else "")
        + (" (synthetic fixtures)" if synthetic else ""),
        f"- Backend: {backend.get('name')}"
        + (f", model `{backend['model']}`" if backend.get("model") else "")
        + (f", effort {backend['effort']}" if backend.get("effort") else ""),
        "- Harness rules recorded: "
        + (describe_rules(metrics.rules) if metrics.rules is not None else "unknown")
        + "; the three belief variables are readings, outside both rules, so the rules act on "
        "nothing here.",
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
        "- Compared with: the hindsight snapshots in `snapshots/cw/hindsight/` (the truth of "
        "what each belief estimates, decisions D6) and the contemporaneous beliefs of the "
        "record (the manual replay snapshots in `snapshots/cw/replay/`, else the `belief` rows "
        "of `data/cw/events.csv`). Every variable but the beliefs is carried from the hindsight "
        "snapshot as `assumed`.",
        "",
    ]
    if metrics.missing_replay:
        what = "a proposals file" if metrics.proposal_level else "a reviewed replay snapshot"
        lines += [
            f"Years without {what} (not compared): {', '.join(metrics.missing_replay)}.",
            "",
        ]
    if runs:
        lines += [
            "## Date filtering",
            "",
            "| Year | Documents dated before its 1 January | Read this year | Proposals | "
            "Discarded by the checks |",
            "|---|---|---|---|---|",
        ]
        lines += [
            f"| {r.quarter} | {r.visible} | {r.read} | {r.proposals} | {r.discarded} |"
            for r in runs
        ]
        lines.append("")
    if metrics.proposal_level:
        lines += _proposal_table(metrics)
    lines += _c6_table(metrics)
    lines += _c7_lines(metrics)
    lines += [
        "## Agreement per variable",
        "",
        "| Variable | With the hindsight truth | With the contemporaneous belief |",
        "|---|---|---|",
    ]
    for name in CW.text_variables:
        h = metrics.agreement(name, "hindsight")
        c = metrics.agreement(name, "contemporaneous")
        hcell = _pct(*h) if h[1] else "n/a (no hindsight level: the swept hypothesis)"
        lines.append(f"| `{name}` | {hcell} | {_pct(*c)} |")
    lines += [
        "",
        "## Flips: lag against the contemporaneous record",
        "",
        "A documented flip is a change of the contemporaneous belief between consecutive "
        "1 Januaries; a replayed flip is the same in the replay, dated by the "
        + ("proposal (treated as accepted)" if metrics.proposal_level else "accepted proposal")
        + f" that set it. Matched within {CW.match_window} years to the same level; lag is "
        "replay minus documented, in years (positive: the replay is late).",
        "",
        "| Variable | Level | Documented (year) | Replayed (year, date) | Lag (years) |",
        "|---|---|---|---|---|",
    ]
    for name in CW.text_variables:
        for d, r in metrics.matches.get(name, []):
            level = _lv((d or r).after)  # type: ignore[union-attr]
            dcell = d.year if d else "none (false flip)"
            rcell = f"{r.year}, {r.observed}" if r else "none (missed)"
            lag = f"{int(r.year) - int(d.year):+d}" if d and r else "-"
            lines.append(f"| `{name}` | {level} | {dcell} | {rcell} | {lag} |")
    lines.append("")
    lines += _disagreements(metrics)
    return "\n".join(lines)


def _proposal_table(metrics: YearMetrics) -> list[str]:
    lines = [
        "## Proposals per variable",
        "",
        "Every proposal kept by the extractor's checks over the years, by level, and how the "
        "harness rules classified it.",
        "",
        "| Variable | Proposals | By level | " + " | ".join(t for _s, t in _GATE_COLUMNS) + " |",
        "|---|---|---|" + "---|" * len(_GATE_COLUMNS),
    ]
    for name in CW.text_variables:
        c = metrics.counts.get(name, Counter())
        g = metrics.gates.get(name, Counter())
        levels = ", ".join(f"{lv} {n}" for lv, n in sorted(c.items(), key=lambda x: -x[1]))
        cells = " | ".join(str(g.get(s, 0)) for s, _t in _GATE_COLUMNS)
        lines.append(f"| `{name}` | {sum(c.values())} | {levels or '-'} | {cells} |")
    return [*lines, ""]


def _c6_table(metrics: YearMetrics) -> list[str]:
    name = "belief_force_USA"
    lines = [
        "## C6: the replayed estimate of the Soviet force against the hindsight force",
        "",
        "Per year, the replayed `belief_force_USA` and the hindsight `count_USSR`, the number "
        "of Soviet intercontinental delivery vehicles in being, in the same bands (the owner's "
        "decision 7g; cw_v1 decisions R V6 (a), v0's C6 as amended: the replayed belief "
        "exceeds the hindsight count, a higher band, in every year 1958 to 1961), "
        "beside the contemporaneous belief of the record. These are inputs of C6; its parts "
        "(b) and (c) are computed on the model.",
        "",
        "| Year | Replayed | Hindsight `count_USSR` | Replay exceeds | Contemporaneous "
        "(source) | Contemporaneous exceeds |",
        "|---|---|---|---|---|---|",
    ]
    for y in metrics.years:
        c = metrics.contemporaneous.get(name, {}).get(y)
        ex, cex = metrics.exceeds(y), metrics.exceeds(y, "contemporaneous")
        lines.append(
            f"| {y} | {_cell(metrics.replay.get(name, {}).get(y))} | "
            f"{_cell(metrics.hindsight.get(name, {}).get(y))} | "
            f"{'-' if ex is None else 'yes' if ex else 'no'} | "
            f"{_cell(c[0]) if c else '-'}{f' ({c[1]})' if c else ''} | "
            f"{'-' if cex is None else 'yes' if cex else 'no'} |"
        )
    in_range = [y for y in C6_YEARS if y in metrics.years]
    if in_range:
        known = [y for y in in_range if metrics.exceeds(y) is not None]
        n = sum(1 for y in known if metrics.exceeds(y))
        lines += [
            "",
            f"Years {in_range[0]} to {in_range[-1]} with a replay snapshot: {len(known)} of "
            f"{len(in_range)}; the replayed estimate exceeds the hindsight force in {n} of them.",
        ]
    return [*lines, ""]


def _c7_lines(metrics: YearMetrics) -> list[str]:
    if C7_YEAR not in metrics.years:
        return []
    name = "belief_USSR_USA"
    c = metrics.contemporaneous.get(name, {}).get(C7_YEAR)
    return [
        "## C7: Moscow's reading of American aims on 1 January 1983",
        "",
        f"- Replayed `belief_USSR_USA`: {_cell(metrics.replay.get(name, {}).get(C7_YEAR))} "
        f"({_cite(metrics.entries.get(name, {}).get(C7_YEAR))}).",
        f"- Hindsight: {_cell(metrics.hindsight.get(name, {}).get(C7_YEAR))}. Contemporaneous: "
        + (f"{_cell(c[0])} ({c[1]})." if c else "-."),
        "- A reading of Moscow's belief needs a document that reproduces Moscow's own words "
        "(the extractor's instructions); an American estimate of what Moscow fears is "
        "Washington's belief, not Moscow's.",
        "",
    ]


def _disagreements(metrics: YearMetrics) -> list[str]:
    rows = []
    for name in CW.text_variables:
        for y, level in metrics.replay.get(name, {}).items():
            c = metrics.contemporaneous.get(name, {}).get(y)
            h = metrics.hindsight.get(name, {}).get(y)
            if (c is not None and c[0] != level) or (h is not None and h != level):
                rows.append(
                    f"- `{name}`, {y}: replay {_cite(metrics.entries[name].get(y))}; "
                    f"hindsight {_cell(h)}; contemporaneous "
                    + (f"{_cell(c[0])} ({c[1]})" if c else "-")
                    + "."
                )
    if not rows:
        return []
    return [
        "## Disagreements and the indicators behind them",
        "",
        "Every year in which the replay differs from the hindsight truth or from the "
        "contemporaneous belief, with the replay's latest "
        + ("proposal's (unreviewed) quote." if metrics.proposal_level else "accepted quote."),
        "",
        *rows,
        "",
    ]
