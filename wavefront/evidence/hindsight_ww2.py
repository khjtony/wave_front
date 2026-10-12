"""Hindsight snapshots for the WW2 v0 model, 1936Q1 to 1940Q4 (ww2_testbed.md sections 6 and 8).

A hindsight snapshot is the realized state of the world in a quarter, read with full
knowledge of the record: the comparison target for the blind replay of section 8. It is built
from two committed inputs and the ontology's rules:

* ``data/ww2/nmc_1936_1940.csv``, the Correlates of War NMC extract, for the resource variables
  ``arms_GER``, ``arms_WEST``, ``arms_USSR`` (supporting only), ``arms_JPN`` and ``ind_GER``
  (cross-check). NMC is annual: the year's value is carried to each of its quarters, and every
  such indicator says ``interpolated: annual value carried to the quarter`` in its rule. Its
  ``observed`` date is the last day of the year the value covers, which is after the snapshot
  date for the first three quarters: the reading uses the whole year's figure.
* ``data/ww2/events_ww2.csv``, dated structural events, for the structural, region, pact,
  belief and commitment variables: the level in force at the quarter's end (or, with
  ``at="start"``, on the quarter's first day), with the event and its source as the
  indicator.

The hidden objectives ``aims_GER`` and ``aims_USSR`` are swept by the model and are *not*
fixed here: a snapshot that fixed them would assert a historiographical hypothesis as an
observation. Per-hypothesis analysis fixes them by adding one ``aims_*`` entry with
``confidence: "assumed"`` to a copy of the snapshot. The latches (``belief_at_munich``,
``arms_at_war``) are built-ins and are set by the loader from the loaded state.

Confidence: ``high`` for dataset-backed and dated-event levels; ``medium`` for levels whose
reading depends on a threshold (the numeric NMC thresholds below, which are provisional, and
the belief, commitment and other event readings that are a judgment, listed in
:data:`JUDGMENT`); ``assumed`` only where no dated indicator supports the level, and then the
rule says what is missing.

The numeric thresholds in :data:`ONTOLOGY_RULES` operationalize the ontology's qualitative
rules (docs/ontology_ww2.md section 2) for this pipeline. They are provisional and are listed
for the historian's review; they are not part of the ontology.

Command line: ``python3 -m wavefront.evidence.hindsight_ww2 --out snapshots/ww2/hindsight``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .datasets import nmc
from .snapshot import validate_snapshot

__all__ = [
    "EVENT_COLUMNS",
    "Event",
    "HIDDEN",
    "INTERPOLATED",
    "JUDGMENT",
    "MODEL",
    "ONTOLOGY_RULES",
    "QUARTERS",
    "VARIABLES",
    "Variable",
    "build",
    "build_all",
    "check_against_ontology",
    "load_events",
    "main",
    "parse_ontology",
    "quarter_bounds",
]

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NMC = ROOT / "data" / "ww2" / "nmc_1936_1940.csv"
DEFAULT_EVENTS = ROOT / "data" / "ww2" / "events_ww2.csv"
DEFAULT_ONTOLOGY = ROOT / "docs" / "ontology_ww2.md"

MODEL = "ww2_v0"
QUARTERS = tuple(f"{y}Q{q}" for y in range(1936, 1941) for q in range(1, 5))
INTERPOLATED = "interpolated: annual value carried to the quarter"
EVENT_COLUMNS = ("date", "quarter", "variable", "level", "event", "source", "note")
TICK0 = "1935Q4"  # file name of the tick-0 initial state (end of 1935Q4)

# COW country codes and abbreviations used below.
GMY, UKG, FRN, RUS, JPN = 255, 200, 220, 365, 740


@dataclass(frozen=True)
class Variable:
    """An ontology variable: ``kind`` is ``level`` (named levels), ``flag`` or ``integer``."""

    name: str
    kind: str
    levels: tuple[Any, ...]
    init: Any
    section: str


def _lv(name: str, levels: str, init: str, section: str) -> Variable:
    return Variable(name, "level", tuple(levels.split()), init, section)


def _flag(name: str, init: bool) -> Variable:
    return Variable(name, "flag", (False, True), init, "4")


# The variables of docs/ontology_ww2.md sections 2 to 5, in document order, with their levels
# and 1936Q1 initial values. tests/evidence/test_ww2_hindsight.py checks this list against the
# document's tables.
VARIABLES: tuple[Variable, ...] = (
    _lv("arms_GER", "low rising high total", "rising", "2"),
    _lv("arms_WEST", "low rising high", "low", "2"),
    _lv("arms_USSR", "weak strong", "strong", "2"),
    _lv("arms_JPN", "high total", "high", "2"),
    Variable("ind_GER", "integer", (3, 4, 5), 3, "2"),
    _lv("oil_GER", "dependent secured", "dependent", "2"),
    _lv("belief_WEST", "limited uncertain hegemonic", "limited", "3"),
    _lv("belief_GER", "will_not_fight uncertain will_fight", "will_not_fight", "3"),
    _lv("commit_WEST", "appease wary resolved at_war", "appease", "3"),
    _lv("commit_US", "isolationist wary engaged", "isolationist", "3"),
    _lv("treaty", "enforced eroded dead", "eroded", "4"),
    _flag("axis", False),
    _flag("anticomintern", False),
    _flag("nazi_soviet_pact", False),
    _flag("polish_guarantee", False),
    _flag("anglo_soviet_alliance", False),
    _flag("ussr_axis", False),
    _flag("italy_estranged", True),
    _flag("china_war", False),
    _lv("rhineland", "demilitarized remilitarized", "demilitarized", "5"),
    _lv("austria", "independent annexed", "independent", "5"),
    _lv("sudeten", "czech german", "czech", "5"),
    _lv("bohemia", "czech german", "czech", "5"),
    _lv("poland", "independent german partitioned", "independent", "5"),
    _lv("france", "independent at_war fallen", "independent", "5"),
    _lv("britain", "at_peace at_war negotiated invaded", "at_peace", "5"),
    _lv("balkans", "neutral german_aligned", "neutral", "5"),
    _lv("siberia", "soviet japanese", "soviet", "5"),
    _lv("channel_air", "contested german british", "contested", "5"),
    _lv("war_west_ger", "peace war", "peace", "5"),
)
BY_NAME = {v.name: v for v in VARIABLES}

# Swept by the model (ontology section 1); never fixed by a hindsight snapshot.
HIDDEN = {"aims_GER": ("revisionist", "hegemonic"), "aims_USSR": ("defensive", "opportunist")}

# Event-read variables whose level is a reading of documents or a choice among candidate
# dates, not a dated legal or military fact: confidence medium.
JUDGMENT = frozenset(
    {"belief_WEST", "belief_GER", "commit_WEST", "oil_GER", "balkans", "channel_air"}
)

# Variables whose level before their first dated event is itself a reading of documents, so
# that without a confirming observation it is "assumed". The pre-event level of a structural
# variable (a region not yet transferred, a pact not yet signed) is a fact, read "high".
NEEDS_EVIDENCE = frozenset({"belief_WEST", "belief_GER", "commit_WEST", "commit_US", "oil_GER"})

# What a dated indicator would have to be for the variables that can be read as "assumed".
MISSING = {
    "belief_GER": "a dated record of Berlin's reading of British and French resolve before "
    "May 1939 (the Fuehrer conferences; DGFP)",
    "belief_WEST": "a dated Cabinet or Hansard record of London's reading of German aims",
    "commit_WEST": "a dated record of British and French policy on resisting German moves",
    "oil_GER": "a dated observation of German oil import dependence (Minerals Yearbook)",
    "commit_US": "a dated record of US neutrality legislation or policy",
}

# Provisional numeric operationalization of the ontology's section 2 rules.
ONTOLOGY_RULES: dict[str, Any] = {
    "arms_GER": {
        "high_milper_min": 1000,
        "gate": "conscription in force",
    },
    "arms_WEST": {
        "high_milex_multiple": 3.0,
        "baseline_year": 1935,
        "gate": "both western rearmament programmes in force",
    },
    "ind_GER": {"base": 3},
    "rates": {
        "rearm_delay_ticks": {
            "ticks": 4,
            "basis": (
                "Provisional: the action catalogue's one-year lag from a rearmament decision "
                "to fielded force (docs/actions_ww2.md, rearm). NMC shows German military "
                "personnel rising from 461 to 596 thousand (1935 to 1936) in the year after "
                "conscription was reintroduced in March 1935, and British milex rising by 40 "
                "to 50 percent a year from 1936 to 1938 before the 1939 jump. To be refined by the "
                "historian from the programme records (Tooze 2006 for Germany; the Defence "
                "Requirements reports for Britain)."
            ),
        }
    },
}


# -- quarters and events ---------------------------------------------------------------------


_QUARTER = re.compile(r"(\d{4})Q([1-4])")


def quarter_bounds(quarter: str) -> tuple[date, date]:
    """The first and last day of ``quarter`` (``YYYYQn``)."""
    m = _QUARTER.fullmatch(quarter)
    if not m:
        raise ValueError(f"{quarter!r} is not a quarter of the form YYYYQn")
    year, q = int(m.group(1)), int(m.group(2))
    first = date(year, 3 * q - 2, 1)
    last = date(year + 1, 1, 1) if q == 4 else date(year, 3 * q + 1, 1)
    return first, date.fromordinal(last.toordinal() - 1)


def quarter_of(day: date) -> str:
    return f"{day.year}Q{(day.month - 1) // 3 + 1}"


@dataclass(frozen=True)
class Event:
    date: date
    quarter: str
    variable: str
    level: Any
    event: str
    source: str
    note: str

    @property
    def uncertain(self) -> bool:
        """A date or reference marked ``?`` in the source cell."""
        return "?" in self.source


def parse_level(var: Variable, text: str) -> Any:
    """A level cell of the events file as the snapshot level for ``var``."""
    text = text.strip()
    if var.kind == "flag":
        if text not in ("True", "False"):
            raise ValueError(f"{var.name}: flag level must be True or False, not {text!r}")
        return text == "True"
    if var.kind == "integer":
        value = int(text)
    else:
        value = text
    if value not in var.levels:
        raise ValueError(f"{var.name}: {text!r} is not one of {var.levels}")
    return value


def load_events(path: str | Path = DEFAULT_EVENTS) -> list[Event]:
    """The rows of ``events_ww2.csv``, checked (known variable, valid level, quarter matching
    the date, non-empty event and source) and sorted by date (stable for equal dates)."""
    path = Path(path)
    records = nmc.read_csv_records(path)
    events = []
    for n, rec in enumerate(records, start=1):
        missing = [c for c in EVENT_COLUMNS if c not in rec]
        if missing:
            raise ValueError(f"{path}: row {n} lacks columns {missing}")
        name = rec["variable"].strip()
        if name not in BY_NAME:
            raise ValueError(f"{path}: row {n}: {name!r} is not a WW2 v0 ontology variable")
        day = date.fromisoformat(rec["date"].strip())
        if rec["quarter"].strip() != quarter_of(day):
            raise ValueError(f"{path}: row {n}: quarter {rec['quarter']!r} does not match {day}")
        if not rec["event"].strip() or not rec["source"].strip():
            raise ValueError(f"{path}: row {n}: event and source must not be empty")
        events.append(
            Event(
                date=day,
                quarter=quarter_of(day),
                variable=name,
                level=parse_level(BY_NAME[name], rec["level"]),
                event=rec["event"].strip(),
                source=rec["source"].strip(),
                note=(rec["note"] or "").strip(),
            )
        )
    return sorted(events, key=lambda e: e.date)


# -- indicators ------------------------------------------------------------------------------


def _event_indicator(e: Event, rule: str) -> dict[str, Any]:
    if e.note:
        rule = f"{rule}. Note: {e.note}"
    return {
        "id": f"event_{e.date.isoformat()}_{e.variable}",
        "value": e.event,
        "source": e.source,
        "observed": e.date.isoformat(),
        "rule": rule,
    }


def _nmc_source(row: Mapping[str, Any]) -> str:
    return (
        f"{row['source']}, version {row['version']}, obtained via {row['obtained_via']}; "
        "committed extract data/ww2/nmc_1936_1940.csv"
    )


def _nmc_indicator(row: Mapping[str, Any], column: str, rule: str) -> dict[str, Any]:
    value = row[column]
    if value is None:
        raise ValueError(f"NMC {column} is missing for {row['stateabb']} {row['year']}")
    return {
        "id": f"nmc_{row['stateabb']}_{row['year']}_{column}",
        "value": value,
        "source": _nmc_source(row),
        "observed": f"{row['year']}-12-31",
        "rule": f"{rule}; {INTERPOLATED}",
    }


class _NMC:
    """Lookup of the NMC extract by country code and year."""

    def __init__(self, rows: Iterable[Mapping[str, Any]]) -> None:
        self.rows = {(r["ccode"], r["year"]): r for r in rows}

    def row(self, ccode: int, year: int) -> Mapping[str, Any]:
        try:
            return self.rows[(ccode, year)]
        except KeyError:
            raise ValueError(f"the NMC extract has no row for ccode {ccode}, year {year}") from None

    def get(self, ccode: int, year: int, column: str) -> Any:
        value = self.row(ccode, year)[column]
        if value is None:
            raise ValueError(f"NMC {column} is missing for ccode {ccode}, year {year}")
        return value


# -- the builder -----------------------------------------------------------------------------


class _Reader:
    """Readings for one quarter: events up to ``cutoff`` and the NMC values of ``year``."""

    def __init__(self, events: Sequence[Event], cutoff: date, inclusive: bool, year: int):
        self.year = year
        self.cutoff = cutoff
        self.events = events
        self.in_force = [e for e in events if (e.date <= cutoff if inclusive else e.date < cutoff)]
        self.later = [e for e in events if e not in self.in_force]

    def history(self, name: str) -> list[Event]:
        return [e for e in self.in_force if e.variable == name]

    def next_event(self, name: str) -> Event | None:
        return next((e for e in self.later if e.variable == name), None)

    def current(self, name: str) -> tuple[Any, list[Event]]:
        """The level of ``name`` in force and the events behind it: the row that set the
        level (the first row of the final run of equal levels) and the latest row if it is a
        later confirming observation. No rows: the ontology's initial level and ``[]``."""
        rows = self.history(name)
        if not rows:
            return BY_NAME[name].init, []
        level = rows[-1].level
        first = len(rows) - 1
        while first > 0 and rows[first - 1].level == level:
            first -= 1
        chosen = [rows[first]] if first == len(rows) - 1 else [rows[first], rows[-1]]
        return level, chosen


def _event_variable(r: _Reader, var: Variable, at_text: str) -> dict[str, Any]:
    level, rows = r.current(var.name)
    if rows:
        rule = f"{var.name} takes the level of the latest dated event at or before {at_text}"
        indicators = [_event_indicator(e, f"{rule} ({var.name} := {e.level})") for e in rows]
        return {
            "level": level,
            "confidence": "medium" if var.name in JUDGMENT else "high",
            "indicators": indicators,
        }
    nxt = r.next_event(var.name)
    base_rule = (
        f"no dated event changes {var.name} before {at_text}, so it keeps the ontology's "
        f"1936Q1 initial level {var.init!r} (docs/ontology_ww2.md section {var.section})"
    )
    if nxt is None:  # pragma: no cover - every variable has at least one row
        raise ValueError(f"events_ww2.csv has no row for {var.name}")
    if var.name not in NEEDS_EVIDENCE:
        confidence = "high"
        rule = f"{base_rule}; the first dated change or confirmation is the event shown"
    elif nxt.level == var.init:
        confidence = "medium"
        rule = (
            f"{base_rule}; the level is read from the next dated observation, which confirms "
            f"it but is dated after {at_text}"
        )
    else:
        confidence = "assumed"
        rule = (
            f"{base_rule}; assumed: no dated observation supports it before the change shown. "
            f"Missing: {MISSING[var.name]}"
        )
    return {
        "level": var.init,
        "confidence": confidence,
        "indicators": [_event_indicator(nxt, rule)],
    }


def _gate(r: _Reader, name: str, level: str) -> tuple[bool, Event | None]:
    """Whether the event gate of an NMC rule (a row ``name := level``) is in force, and the
    event to cite: the gate row if in force, otherwise the next one."""
    rows = [e for e in r.history(name) if e.level == level]
    if rows:
        return True, rows[0]
    later = next((e for e in r.later if e.variable == name and e.level == level), None)
    return False, later


def _arms_ger(r: _Reader, data: _NMC, rules: Mapping[str, Any], at_text: str) -> dict[str, Any]:
    cfg = rules["arms_GER"]
    y = r.year
    milper, milex = data.get(GMY, y, "milper"), data.get(GMY, y, "milex")
    prev = data.get(GMY, y - 1, "milex")
    gate, gate_event = _gate(r, "arms_GER", "rising")
    threshold = cfg["high_milper_min"]
    rule = (
        f"provisional rule for arms_GER (ontology section 2): high if NMC milper >= {threshold} "
        "thousand (a field army able to sustain a major campaign); rising if "
        f"{cfg['gate']} (events_ww2.csv) and NMC milex above the previous year's; otherwise "
        "low; total is not read from NMC (a dated full-war-economy decision, none before 1941)"
    )
    high_rows = [e for e in r.history("arms_GER") if e.level == "high"]
    high_event = high_rows[-1] if high_rows else None
    if high_event is not None:
        level = "high"  # the planning-record definition (ontology section 2; decisions D12)
    elif milper >= threshold:
        level = "high"
    elif gate and milex > prev:
        level = "rising"
    else:
        level = "low"
    row = data.row(GMY, y)
    indicators = [
        _nmc_indicator(row, "milper", f"{rule}; milper {milper} vs threshold {threshold}"),
        _nmc_indicator(row, "milex", f"{rule}; milex {milex} vs {y - 1}: {prev}"),
    ]
    if high_event is not None:
        indicators.insert(
            0, _event_indicator(high_event, "planning-record definition of high (decisions D12)")
        )
    if gate_event is not None:
        state = "in force" if gate else f"not yet in force at {at_text}"
        indicators.append(_event_indicator(gate_event, f"gate of the arms_GER rule, {state}"))
    return {"level": level, "confidence": "medium", "indicators": indicators}


def _arms_west(r: _Reader, data: _NMC, rules: Mapping[str, Any], at_text: str) -> dict[str, Any]:
    cfg = rules["arms_WEST"]
    y, base_year, k = r.year, cfg["baseline_year"], cfg["high_milex_multiple"]

    def combined(year: int) -> int:
        return data.get(UKG, year, "milex") + data.get(FRN, year, "milex")

    now, prev, base = combined(y), combined(y - 1), combined(base_year)
    gate, gate_event = _gate(r, "arms_WEST", "rising")
    rule = (
        "provisional rule for arms_WEST (ontology section 2): high if the combined United "
        f"Kingdom and France NMC milex is at least {k} times its {base_year} value (the year "
        f"before the programmes); rising if {cfg['gate']} (events_ww2.csv) and the combined "
        "milex is above the previous year's; otherwise low"
    )
    if now >= k * base:
        level = "high"
    elif gate and now > prev:
        level = "rising"
    else:
        level = "low"
    uk, fr = data.row(UKG, y), data.row(FRN, y)
    detail = (
        f"combined milex {now} (UKG {uk['milex']} + FRN {fr['milex']}); {base_year}: {base} "
        f"(ratio {now / base:.2f}, threshold {k}); {y - 1}: {prev}"
    )
    indicators = [
        {
            "id": f"nmc_UKG_FRN_{y}_milex",
            "value": now,
            "source": _nmc_source(uk),
            "observed": f"{y}-12-31",
            "rule": f"{rule}; {detail}; {INTERPOLATED}",
        },
        _nmc_indicator(uk, "milper", "context for arms_WEST, not in the rule; UKG milper"),
        _nmc_indicator(fr, "milper", "context for arms_WEST, not in the rule; FRN milper"),
    ]
    if gate_event is not None:
        state = "in force" if gate else f"not yet in force at {at_text}"
        indicators.append(_event_indicator(gate_event, f"gate of the arms_WEST rule, {state}"))
    return {"level": level, "confidence": "medium", "indicators": indicators}


def _arms_ussr(r: _Reader, data: _NMC, at_text: str) -> dict[str, Any]:
    entry = _event_variable(r, BY_NAME["arms_USSR"], at_text)
    entry["confidence"] = "medium"
    row = data.row(RUS, r.year)
    entry["indicators"].append(
        _nmc_indicator(
            row,
            "milper",
            "supporting indicator for arms_USSR (ontology section 2: weak while the officer "
            "corps is purged, 1937 to 1938; strong otherwise); NMC milper counts personnel and "
            "does not register the purge",
        )
    )
    return entry


def _arms_jpn(r: _Reader, data: _NMC) -> dict[str, Any]:
    row = data.row(JPN, r.year)
    rule = "arms_JPN is fixed at high in v0 (ontology section 2); NMC shown as context"
    return {
        "level": "high",
        "confidence": "medium",
        "indicators": [_nmc_indicator(row, "milex", rule), _nmc_indicator(row, "milper", rule)],
    }


def _ind_ger(r: _Reader, data: _NMC, rules: Mapping[str, Any]) -> dict[str, Any]:
    base = rules["ind_GER"]["base"]
    austria, a_rows = r.current("austria")
    bohemia, b_rows = r.current("bohemia")
    level = base + (austria == "annexed") + (bohemia == "german")
    rule = (
        f"ind_GER = {base} + 1 with Austria annexed + 1 with Bohemia german (ontology section 2); "
        f"austria is {austria}, bohemia is {bohemia}"
    )
    indicators = [_event_indicator(e, rule) for e in (*a_rows[:1], *b_rows[:1])]
    row = data.row(GMY, r.year)
    irst_rule = "cross-check for ind_GER, not in the rule: German iron and steel (NMC irst)"
    indicators.append(_nmc_indicator(row, "irst", irst_rule))
    return {"level": level, "confidence": "high", "indicators": indicators}


def build(
    quarter: str,
    nmc_rows: Iterable[Mapping[str, Any]],
    events: Sequence[Event],
    ontology_rules: Mapping[str, Any] = ONTOLOGY_RULES,
    *,
    at: str = "end",
) -> dict[str, Any]:
    """The hindsight snapshot for ``quarter`` (``1936Q1`` to ``1940Q4``).

    ``at="end"`` (the default) reads the levels in force on the quarter's last day, which is
    the snapshot's ``date``; ``at="start"`` reads them on its first day, before any event of the
    quarter (for 1936Q1 this is the ontology's initial state). Resource variables use the NMC
    values of the quarter's year either way. The ``aims_*`` variables are omitted (see the
    module docstring)."""
    if at not in ("end", "start"):
        raise ValueError(f"at must be 'end' or 'start', not {at!r}")
    first, last = quarter_bounds(quarter)
    cutoff = last if at == "end" else first
    at_text = cutoff.isoformat() + (" (end of quarter)" if at == "end" else " (before the quarter)")
    r = _Reader(sorted(events, key=lambda e: e.date), cutoff, at == "end", first.year)
    data = _NMC(nmc_rows)
    variables: dict[str, Any] = {}
    for var in VARIABLES:
        if var.name == "arms_GER":
            variables[var.name] = _arms_ger(r, data, ontology_rules, at_text)
        elif var.name == "arms_WEST":
            variables[var.name] = _arms_west(r, data, ontology_rules, at_text)
        elif var.name == "arms_USSR":
            variables[var.name] = _arms_ussr(r, data, at_text)
        elif var.name == "arms_JPN":
            variables[var.name] = _arms_jpn(r, data)
        elif var.name == "ind_GER":
            variables[var.name] = _ind_ger(r, data, ontology_rules)
        else:
            variables[var.name] = _event_variable(r, var, at_text)
    rates = {
        name: {"ticks": spec["ticks"], "basis": spec["basis"]}
        for name, spec in ontology_rules["rates"].items()
    }
    return {
        "$schema": "../../schema.json",
        "date": cutoff.isoformat(),
        "model": MODEL,
        "variables": variables,
        "rates": rates,
    }


def check_against_ontology(snapshot: Mapping[str, Any]) -> list[str]:
    """Problems with a snapshot's variable names and levels against :data:`VARIABLES`:
    unknown variables, levels outside a variable's levels, a fixed ``aims_*``, and ontology
    variables the snapshot leaves out."""
    problems = []
    given = snapshot.get("variables", {})
    for name, entry in given.items():
        if name in HIDDEN:
            problems.append(f"{name} is swept by the model and must not be fixed")
            continue
        var = BY_NAME.get(name)
        if var is None:
            problems.append(f"{name} is not a WW2 v0 ontology variable")
            continue
        level = entry.get("level")
        ok = (isinstance(level, bool) and var.kind == "flag") or (
            not isinstance(level, bool) and var.kind != "flag" and level in var.levels
        )
        if not ok:
            problems.append(f"{name}: level {level!r} is not one of {var.levels}")
    for var in VARIABLES:
        if var.name not in given:
            problems.append(f"{var.name} is missing")
    return problems


def build_all(
    nmc_rows: Iterable[Mapping[str, Any]],
    events: Sequence[Event],
    ontology_rules: Mapping[str, Any] = ONTOLOGY_RULES,
    quarters: Iterable[str] = QUARTERS,
) -> dict[str, dict[str, Any]]:
    rows = list(nmc_rows)
    quarters = list(quarters)
    out: dict[str, dict[str, Any]] = {}
    if quarters and quarters[0] == QUARTERS[0]:
        # The model's tick-0 initial state: the levels in force at the end of 1935Q4, the
        # last day before the first modeled quarter (snapshots/ww2/hindsight/README.md).
        out[TICK0] = build(TICK0, rows, events, ontology_rules)
    out.update({q: build(q, rows, events, ontology_rules) for q in quarters})
    return out


# -- the ontology document ---------------------------------------------------------------------


def _parse_cell_levels(cell: str) -> tuple[Any, ...]:
    cell = cell.strip()
    if cell == "flag":
        return (False, True)
    parts = [p.strip() for p in cell.split(",")]
    return tuple(int(p) if p.isdigit() else p for p in parts)


def _parse_cell_init(cell: str) -> Any:
    cell = cell.strip()
    if cell in ("True", "False"):
        return cell == "True"
    return int(cell) if cell.isdigit() else cell


def parse_ontology(path: str | Path = DEFAULT_ONTOLOGY) -> dict[str, dict[str, Any]]:
    """The variable tables of the ontology document: ``{name: {levels, init, section}}`` for
    every table row whose first cell is a backticked name. ``init`` is ``None`` for tables
    without an ``Init`` column (the hidden objectives)."""
    out: dict[str, dict[str, Any]] = {}
    section = ""
    init_col: int | None = None
    in_table = is_variables = False
    levels_col: int | None = None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(r"## (\d+)\.", line)
        if m:
            section = m.group(1)
        if not line.startswith("|"):
            in_table = False
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not in_table:  # a header row: only tables headed "Variable" declare variables
            in_table = True
            levels_col = next((i for i, c in enumerate(cells) if c == "Levels"), None)
            is_variables = cells[0] == "Variable" and levels_col is not None
            init_col = next((i for i, c in enumerate(cells) if c.startswith("Init")), None)
            continue
        name = re.fullmatch(r"`([A-Za-z_][A-Za-z0-9_]*)`", cells[0])
        if not is_variables or not name or len(cells) < 2:
            continue
        out[name.group(1)] = {
            "levels": _parse_cell_levels(cells[levels_col]),
            "init": _parse_cell_init(cells[init_col]) if init_col is not None else None,
            "section": section,
        }
    return out


def ontology_mismatches(path: str | Path = DEFAULT_ONTOLOGY) -> list[str]:
    """Differences between :data:`VARIABLES` (plus :data:`HIDDEN`) and the ontology tables."""
    doc = parse_ontology(path)
    problems = []
    for name, levels in HIDDEN.items():
        if name not in doc:
            problems.append(f"{name}: not in the ontology")
        elif doc[name]["levels"] != levels:
            problems.append(f"{name}: levels {doc[name]['levels']} in the ontology, {levels} here")
    for var in VARIABLES:
        if var.name not in doc:
            problems.append(f"{var.name}: not in the ontology")
            continue
        if doc[var.name]["levels"] != var.levels:
            problems.append(
                f"{var.name}: levels {doc[var.name]['levels']} in the ontology, {var.levels} here"
            )
        if doc[var.name]["init"] != var.init:
            problems.append(
                f"{var.name}: init {doc[var.name]['init']!r} in the ontology, {var.init!r} here"
            )
    for name in doc:
        if name not in BY_NAME and name not in HIDDEN:
            problems.append(f"{name}: in the ontology but not in the builder")
    return problems


# -- command line ----------------------------------------------------------------------------


def _dump(snapshot: Mapping[str, Any]) -> str:
    return json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m wavefront.evidence.hindsight_ww2",
        description="Build the WW2 v0 hindsight snapshots, 1936Q1 to 1940Q4.",
    )
    parser.add_argument("--out", type=Path, required=True, help="output directory")
    parser.add_argument("--nmc", type=Path, default=DEFAULT_NMC, help="NMC extract or raw file")
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--ontology", type=Path, default=DEFAULT_ONTOLOGY)
    parser.add_argument(
        "--check", action="store_true", help="compare with the files in --out; write nothing"
    )
    args = parser.parse_args(argv)

    problems = []
    if args.ontology.exists():
        problems += [f"ontology: {p}" for p in ontology_mismatches(args.ontology)]
    snapshots = build_all(nmc.load(args.nmc), load_events(args.events))
    for quarter, snap in snapshots.items():
        problems += [f"{quarter}: {p}" for p in validate_snapshot(snap)]
        problems += [f"{quarter}: {p}" for p in check_against_ontology(snap)]
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    stale = []
    for quarter, snap in snapshots.items():
        path = args.out / f"{quarter}.json"
        text = _dump(snap)
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(str(path))
        else:
            args.out.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    if stale:
        print("out of date: " + ", ".join(stale), file=sys.stderr)
        return 1
    verb = "checked" if args.check else "wrote"
    print(f"{verb} {len(snapshots)} snapshots in {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
