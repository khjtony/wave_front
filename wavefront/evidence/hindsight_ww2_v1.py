"""Hindsight snapshots for the WW2 v1 model, 1936Q1 to 1945Q3 (docs/ww2_v1_decisions.md E7).

A sibling of :mod:`wavefront.evidence.hindsight_ww2` (the v0 builder, whose outputs are
unchanged) that reuses its quarter arithmetic, event and NMC indicators and readings, and
builds ``snapshots/ww2/hindsight_v1/1935Q4.json`` to ``1945Q3.json`` (40 files: the tick-0
state and the end of each of the 39 modeled quarters) for the model ``ww2_v1``
(``models/ww2/v1.py``). Inputs, all committed:

* ``data/ww2/nmc_1936_1940.csv`` (years to 1940) and ``data/ww2/nmc_1941_1945.csv`` (years
  1941 to 1945, written by ``scripts/fetch_ww2_data.py --extract v1``), the Correlates of War
  NMC extracts, for the resource variables. A row or cell NMC does not have (COW system
  membership gaps: France 1943; missing cells such as France's ``milper`` for 1942) is
  **flagged, never filled**: the rule that needs it says so, and a rule whose answer does not
  depend on the missing value (a lower bound already meets the threshold) states the bound.
  :func:`nmc_gaps` lists every gap the snapshots met.
* ``data/ww2/events_ww2.csv`` (v0) and ``data/ww2/events_ww2_v1.csv`` (v1), the dated
  structural events, read as in v0.
* ``data/ww2/decisions_ww2_v1.csv`` (the dated decisions of delayed actions) for the pending
  counters, and ``data/ww2/realized_moves_v1.csv`` for the last actions and for the three flags
  that only a modeled decision sets and no event row carries (``midway_ordered``,
  ``east_feeler``, ``east_peace``).
* ``docs/ontology_ww2.md`` and ``docs/ontology_ww2_v1.md`` (header-aware: the v1 document's
  bold level additions and its ``(v0)`` row labels), checked against :data:`VARIABLES`.

Built-ins (decisions E1): pending counters by kickoff F2's formula from the v1 decision file;
``last_GER``, ``last_WEST`` and ``last_USSR`` from the v1 realized moves; the latch from the
events; and the fairness counters **computed** along the realized path, not assumed zero: at
the end of quarter Q, ``fair_<name>`` is ``min(fair_<name>(Q - 1) + 1, within)`` if the
constraint's trigger holds on the snapshot's own end-of-Q levels (with the last actions of Q)
and the actor's realized move of Q is not one of the responses, and 0 otherwise (the system
update of framework_spec.md section 3.1 applied along the realized path). The triggers are
written here (:data:`FAIRNESS`) and a test checks them against the model's compiled triggers.

Command line: ``python3 -m wavefront.evidence.hindsight_ww2_v1 --out snapshots/ww2/hindsight_v1``
(``--check`` compares with the committed files and writes nothing).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from . import hindsight_ww2 as v0
from .datasets import nmc
from .hindsight_ww2 import (
    INTERPOLATED,
    Decision,
    Event,
    Variable,
    _decision_indicator,
    _event_indicator,
    quarter_bounds,
    quarter_index,
    quarter_name,
    quarter_of,
)
from .snapshot import validate_snapshot

__all__ = [
    "BUILTIN_NAMES",
    "DELAYED",
    "FAIRNESS",
    "HIDDEN",
    "MODEL",
    "MOVE_FLAGS",
    "ONTOLOGY_RULES",
    "QUARTERS",
    "REMEMBER_LAST",
    "VARIABLES",
    "build",
    "build_all",
    "build_builtins",
    "check_against_ontology",
    "check_builtins",
    "check_decisions_against_moves",
    "fairness_series",
    "load_decisions",
    "load_events",
    "load_moves",
    "load_nmc",
    "main",
    "nmc_gaps",
    "ontology_mismatches",
    "parse_ontology",
]

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "ww2"
DEFAULT_NMC = (DATA / "nmc_1936_1940.csv", DATA / "nmc_1941_1945.csv")
DEFAULT_EVENTS = (DATA / "events_ww2.csv", DATA / "events_ww2_v1.csv")
DEFAULT_ONTOLOGY = (ROOT / "docs" / "ontology_ww2.md", ROOT / "docs" / "ontology_ww2_v1.md")
DEFAULT_DECISIONS = DATA / "decisions_ww2_v1.csv"
DEFAULT_MOVES = DATA / "realized_moves_v1.csv"
MOVES_NAME = "data/ww2/realized_moves_v1.csv"
DECISIONS_NAME = "data/ww2/decisions_ww2_v1.csv"

MODEL = "ww2_v1"
QUARTERS = tuple(f"{y}Q{q}" for y in range(1936, 1946) for q in range(1, 5))[:39]
TICK0 = v0.TICK0
HORIZON = 39

GMY, UKG, FRN, RUS, JPN, USA = 255, 200, 220, 365, 740, 2


def _lv(name: str, levels: str, init: str, section: str) -> Variable:
    return Variable(name, "level", tuple(levels.split()), init, section)


def _flag(name: str, init: bool, section: str = "4") -> Variable:
    return Variable(name, "flag", (False, True), init, section)


_V0 = {v.name: v for v in v0.VARIABLES}
_CHANGED = {
    "commit_US": _lv("commit_US", "isolationist wary engaged total", "isolationist", "3"),
    "france": _lv("france", "independent at_war fallen liberated", "independent", "5"),
}

# The variables of WW2 v1 in the model's declaration order (models/ww2/v1.py), without the
# swept hidden objectives and the two v0 model-step flags. ``section`` is the section of the
# ontology document that defines the variable (v0's document for v0 variables).
VARIABLES: tuple[Variable, ...] = (
    *(_CHANGED.get(n, _V0[n]) for n in ("arms_GER", "arms_WEST", "arms_USSR", "arms_JPN")),
    _V0["ind_GER"],
    _V0["oil_GER"],
    _lv("arms_USA", "low rising high", "low", "2"),
    _lv("mob_USSR", "peace total", "peace", "2"),
    _lv("exhaustion_GER", "sustainable strained exhausted", "sustainable", "2"),
    _lv("oil_JPN", "secure dependent embargoed critical", "dependent", "2"),
    _lv("jpn_navy", "strong attrited", "strong", "2"),
    _flag("bomb_ready", False, "2"),
    _flag("strategic_bombing", False, "2"),
    _lv("air_west", "contested allied", "contested", "2"),
    _V0["belief_WEST"],
    _V0["belief_GER"],
    _V0["commit_WEST"],
    _CHANGED["commit_US"],
    _V0["treaty"],
    *(
        _V0[n]
        for n in (
            "axis",
            "anticomintern",
            "nazi_soviet_pact",
            "polish_guarantee",
            "anglo_soviet_alliance",
            "ussr_axis",
            "italy_estranged",
            "china_war",
        )
    ),
    _flag("east_war", False),
    _lv("war_us_ger", "peace war", "peace", "4"),
    _lv("pacific_war", "peace colonial war surrendered", "peace", "4"),
    _lv("reich", "fighting surrendered", "fighting", "4"),
    _flag("east_feeler", False),
    _flag("east_peace", False),
    _flag("midway_ordered", False),
    *(_V0[n] for n in ("rhineland", "austria", "sudeten", "bohemia", "poland")),
    _CHANGED["france"],
    *(_V0[n] for n in ("britain", "balkans", "siberia", "channel_air", "war_west_ger")),
    _lv("w_ussr", "soviet contested german", "soviet", "5"),
    _lv("caucasus", "soviet contested german", "soviet", "5"),
    _lv("italy", "nonbelligerent at_war surrendered", "nonbelligerent", "5"),
    _lv("indochina", "french north_occupied occupied", "french", "5"),
    _lv("dei", "dutch japanese", "dutch", "5"),
)
BY_NAME = {v.name: v for v in VARIABLES}
NEW = frozenset(BY_NAME) - frozenset(_V0)  # defined in docs/ontology_ww2_v1.md

HIDDEN = {
    **v0.HIDDEN,
    "aims_JPN": ("status_quo", "regional", "hegemonic"),
}

# Event-read variables whose level is a judgment (medium), v0's plus the v1 readings the
# events file itself calls threshold readings or judgments.
JUDGMENT = v0.JUDGMENT | frozenset({"mob_USSR", "exhaustion_GER", "oil_JPN", "air_west"})
NEEDS_EVIDENCE = v0.NEEDS_EVIDENCE | frozenset({"oil_JPN"})
MISSING = {
    **v0.MISSING,
    "oil_JPN": "a dated observation of Japanese oil import dependence (Minerals Yearbook)",
}

# Ontology variables that only a modeled decision sets and that no event row carries: read
# from the realized moves (the flag is set in the quarter the action is realized).
MOVE_FLAGS: dict[str, tuple[str, str, str]] = {
    # variable: (actor, action, confidence when the action is not realized)
    "midway_ordered": ("JPN", "offensive_midway", "high"),
    "east_feeler": ("USSR", "seek_terms_east", "medium"),
    "east_peace": ("GER", "negotiate_east", "high"),
}

# Built-ins of models/ww2/v1.py, in the model's state order.
LATCHES = v0.LATCHES
DELAYED: dict[tuple[str, str], int] = {
    ("GER", "rearm"): 8,
    ("WEST", "rearm"): 4,
    ("WEST", "us_rearm"): 4,
    ("WEST", "victory_program"): 5,
    ("WEST", "atomic_program"): 12,
    ("USSR", "rearm"): 4,
    ("USSR", "mobilize_total"): 3,
}
REMEMBER_LAST = ("GER", "WEST", "USSR")

Levels = Mapping[str, Any]


def _idx(name: str, level: Any) -> int:
    return BY_NAME[name].levels.index(level)


@dataclass(frozen=True)
class Fairness:
    """A fairness constraint of the model, with its trigger written over the snapshot's
    levels (and the last actions of the quarter)."""

    name: str
    actor: str
    within: int
    responses: tuple[str, ...]
    reads: tuple[str, ...]
    trigger_text: str
    trigger: Callable[[Levels, Mapping[str, str]], bool]


FAIRNESS: tuple[Fairness, ...] = (
    Fairness(
        "democratic_response",
        "WEST",
        2,
        ("guarantee_poland", "rearm"),
        ("belief_WEST", "commit_WEST", "poland"),
        "belief_WEST == hegemonic and commit_WEST == wary and poland == independent",
        lambda s, last: (
            s["belief_WEST"] == "hegemonic"
            and s["commit_WEST"] == "wary"
            and s["poland"] == "independent"
        ),
    ),
    Fairness(
        "czech_obligation",
        "WEST",
        1,
        ("declare_war", "concede"),
        ("sudeten", "war_west_ger"),
        "last_GER == attack_czechoslovakia and sudeten == german and war_west_ger == peace",
        lambda s, last: (
            last["GER"] == "attack_czechoslovakia"
            and s["sudeten"] == "german"
            and s["war_west_ger"] == "peace"
        ),
    ),
    Fairness(
        "rhineland_resolution",
        "Nature",
        1,
        ("campaign_rhineland",),
        ("arms_GER",),
        "last_WEST == offensive_west and arms_GER <= rising",
        lambda s, last: (
            last["WEST"] == "offensive_west"
            and _idx("arms_GER", s["arms_GER"]) <= _idx("arms_GER", "rising")
        ),
    ),
    Fairness(
        "oil_clock",
        "Nature",
        8,
        ("stocks_run_down",),
        ("oil_JPN",),
        "oil_JPN == embargoed",
        lambda s, last: s["oil_JPN"] == "embargoed",
    ),
)
BUILTIN_NAMES = (
    *LATCHES,
    *(f"pending_{actor}_{action}" for actor, action in DELAYED),
    *(f"last_{actor}" for actor in REMEMBER_LAST),
    *(f"fair_{f.name}" for f in FAIRNESS),
)

# Provisional numeric operationalization (for the historian's review; not the ontology).
ONTOLOGY_RULES: dict[str, Any] = {
    **v0.ONTOLOGY_RULES,
    "arms_USA": {
        "high_milper_min": 5000,
        "gate": "a funded general programme in force",
        "basis": (
            "Provisional: high reads 'ground and air forces able to mount and sustain a "
            "transatlantic invasion' (docs/ontology_ww2_v1.md section 2.1) as at least five "
            "million in uniform; NMC milper for ccode 2 is 1,801 (1941), 3,859 (1942), 9,045 "
            "(1943), so the threshold places high in 1943, the year of the Victory Program's "
            "date (1 Jul 1943). Rising: the programme event of 19 Jul 1940 in force and milex "
            "above the previous year's. For the historian's review."
        ),
    },
}


# -- inputs ----------------------------------------------------------------------------------


def load_events(paths: Iterable[str | Path] = DEFAULT_EVENTS) -> list[Event]:
    """The rows of the v0 and v1 event files (header-aware: ``#`` lines skipped), checked as
    v0 checks them against the v1 variables, and sorted by date (stable)."""
    events = []
    for path in paths:
        path = Path(path)
        for n, rec in enumerate(nmc.read_csv_records(path), start=1):
            missing = [c for c in v0.EVENT_COLUMNS if c not in rec]
            if missing:
                raise ValueError(f"{path}: row {n} lacks columns {missing}")
            name = rec["variable"].strip()
            if name not in BY_NAME:
                raise ValueError(f"{path}: row {n}: {name!r} is not a WW2 v1 ontology variable")
            day = date.fromisoformat(rec["date"].strip())
            if rec["quarter"].strip() != quarter_of(day):
                raise ValueError(
                    f"{path}: row {n}: quarter {rec['quarter']!r} does not match {day}"
                )
            if not rec["event"].strip() or not rec["source"].strip():
                raise ValueError(f"{path}: row {n}: event and source must not be empty")
            events.append(
                Event(
                    date=day,
                    quarter=quarter_of(day),
                    variable=name,
                    level=v0.parse_level(BY_NAME[name], rec["level"]),
                    event=rec["event"].strip(),
                    source=rec["source"].strip(),
                    note=(rec["note"] or "").strip(),
                )
            )
    return sorted(events, key=lambda e: e.date)


def load_decisions(path: str | Path = DEFAULT_DECISIONS) -> list[Decision]:
    """The rows of ``decisions_ww2_v1.csv``, checked as v0 checks its file, against the v1
    delayed actions (:data:`DELAYED`). A row whose quarter is the one after its date's must
    say ``[SQR]`` in its note; its quarter (the model tick) is the one used."""
    path = Path(path)
    out = []
    for n, rec in enumerate(nmc.read_csv_records(path), start=1):
        missing = [c for c in v0.DECISION_COLUMNS if c not in rec]
        if missing:
            raise ValueError(f"{path}: row {n} lacks columns {missing}")
        actor, action = rec["actor"].strip(), rec["action"].strip()
        if (actor, action) not in DELAYED:
            raise ValueError(f"{path}: row {n}: {actor}.{action} is not a delayed action of v1")
        delay = int(rec["delay_ticks"])
        if delay != DELAYED[(actor, action)]:
            raise ValueError(
                f"{path}: row {n}: delay_ticks {delay} for {actor}.{action}, but the model's "
                f"delay is {DELAYED[(actor, action)]}"
            )
        day = date.fromisoformat(rec["date"].strip())
        quarter = rec["quarter"].strip()
        note = (rec["note"] or "").strip()
        if quarter != quarter_of(day):
            # [SQR]: a reaction to a same-quarter decision sits in the next quarter, which is
            # the model tick the pending arithmetic uses (ww2_v1_notes.md section 2).
            sqr = "[SQR" in note and quarter_index(quarter) == quarter_index(quarter_of(day)) + 1
            if not sqr:
                raise ValueError(f"{path}: row {n}: quarter {quarter!r} does not match {day}")
        if not rec["source"].strip():
            raise ValueError(f"{path}: row {n}: source must not be empty")
        out.append(Decision(day, quarter, actor, action, delay, rec["source"].strip(), note))
    out.sort(key=lambda d: d.date)
    for (actor, action), delay in DELAYED.items():
        ticks = [quarter_index(d.quarter) for d in out if (d.actor, d.action) == (actor, action)]
        for t1, t2 in zip(ticks, ticks[1:], strict=False):
            if t2 <= t1 + delay:
                raise ValueError(
                    f"{path}: {actor}.{action} decided at tick {t2} ({quarter_name(t2)}) while "
                    f"the decision of tick {t1} ({quarter_name(t1)}) is still pending "
                    f"(delay {delay}: unavailable at ticks {t1 + 1} to {t1 + delay})"
                )
    return out


def load_moves(path: str | Path = DEFAULT_MOVES) -> list[dict[str, str]]:
    """The rows of ``realized_moves_v1.csv`` in tick order (``#`` lines skipped)."""
    path = Path(path)
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(line for line in handle if not line.startswith("#")))
    for k, row in enumerate(rows):
        if int(row["tick"]) != k or row["quarter"].strip() != quarter_name(k):
            raise ValueError(f"{path}: row {k} is tick {row['tick']}, quarter {row['quarter']}")
    return rows


def check_decisions_against_moves(
    decisions: Sequence[Decision], moves: Sequence[Mapping[str, str]]
) -> list[str]:
    """As v0's check, for the v1 files and delayed actions."""
    problems = []
    rows = {(d.quarter, d.actor, d.action) for d in decisions}
    for row in moves:
        for actor, action in DELAYED:
            if row.get(actor) == action and (row["quarter"], actor, action) not in rows:
                problems.append(
                    f"realized_moves_v1.csv tick {row['tick']} ({row['quarter']}): {actor} "
                    f"{action} has no row in decisions_ww2_v1.csv"
                )
    by_quarter = {row["quarter"]: row for row in moves}
    for d in decisions:
        row = by_quarter.get(d.quarter)
        if row is None or row.get(d.actor) != d.action:
            played = None if row is None else row.get(d.actor)
            problems.append(
                f"decisions_ww2_v1.csv {d.date} {d.actor} {d.action}: the realized move of "
                f"{d.quarter} is {played!r}"
            )
    return problems


def load_nmc(paths: Iterable[str | Path] = DEFAULT_NMC) -> list[dict[str, Any]]:
    """The NMC rows of the v0 extract (years to 1940) and the v1 extract (1941 on), each row
    tagged with the extract it came from. A (state, year) both extracts carry must agree."""
    paths = [Path(p) for p in paths]
    out: dict[tuple[int, int], dict[str, Any]] = {}
    for k, path in enumerate(paths):
        for row in nmc.load(path):
            key = (row["ccode"], row["year"])
            row = dict(row, extract=f"data/ww2/{path.name}")
            if key in out:
                old = out[key]
                diff = [c for c in nmc.COLUMNS if c != "stateabb" and old[c] != row[c]]
                if diff:
                    raise ValueError(f"{path}: {key} differs from {old['extract']} in {diff}")
                if k == len(paths) - 1 and row["year"] >= 1941:
                    out[key] = row  # 1941 on: the v1 extract
                continue
            out[key] = row
    return list(out.values())


# -- readings ----------------------------------------------------------------------------------


def _nmc_source(row: Mapping[str, Any]) -> str:
    return (
        f"{row['source']}, version {row['version']}, obtained via {row['obtained_via']}; "
        f"committed extract {row.get('extract', 'data/ww2/nmc_1936_1940.csv')}"
    )


def _nmc_indicator(row: Mapping[str, Any], column: str, rule: str) -> dict[str, Any]:
    value = row[column]
    if value is None:  # pragma: no cover - callers check for gaps first
        raise ValueError(f"NMC {column} is missing for {row['stateabb']} {row['year']}")
    return {
        "id": f"nmc_{row['stateabb']}_{row['year']}_{column}",
        "value": value,
        "source": _nmc_source(row),
        "observed": f"{row['year']}-12-31",
        "rule": f"{rule}; {INTERPOLATED}",
    }


class _NMC:
    """Lookup of the merged NMC extracts. ``value`` returns ``None`` for a gap and records it
    in :attr:`gaps` (flagged, never filled)."""

    def __init__(self, rows: Iterable[Mapping[str, Any]]) -> None:
        self.rows = {(r["ccode"], r["year"]): r for r in rows}
        self.gaps: set[str] = set()

    def row(self, ccode: int, year: int) -> Mapping[str, Any] | None:
        row = self.rows.get((ccode, year))
        if row is None:
            self.gaps.add(f"{nmc.COW_ABB.get(ccode, ccode)} {year}: no NMC row")
        return row

    def value(self, ccode: int, year: int, column: str) -> Any:
        row = self.row(ccode, year)
        if row is None:
            return None
        if row[column] is None:
            self.gaps.add(f"{nmc.COW_ABB.get(ccode, ccode)} {year}: {column} missing")
        return row[column]

    def get(self, ccode: int, year: int, column: str) -> Any:
        value = self.value(ccode, year, column)
        if value is None:
            raise ValueError(f"NMC {column} is missing for ccode {ccode}, year {year}")
        return value


def _gap_text(ccode: int, year: int, column: str) -> str:
    return (
        f"NMC has no {column} for {nmc.COW_ABB.get(ccode, ccode)} {year} (COW system "
        "membership gap or missing cell): flagged, not filled"
    )


class _Reader(v0._Reader):
    """v0's reader, with the v1 variables' initial levels."""

    def current(self, name: str) -> tuple[Any, list[Event]]:
        rows = self.history(name)
        if not rows:
            return BY_NAME[name].init, []
        level = rows[-1].level
        first = len(rows) - 1
        while first > 0 and rows[first - 1].level == level:
            first -= 1
        chosen = [rows[first]] if first == len(rows) - 1 else [rows[first], rows[-1]]
        return level, chosen


def _doc(var: Variable) -> str:
    return "docs/ontology_ww2_v1.md" if var.name in NEW else "docs/ontology_ww2.md"


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
        f"1936Q1 initial level {var.init!r} ({_doc(var)} section {var.section})"
    )
    if nxt is None:  # pragma: no cover - every event-read variable has a row
        raise ValueError(f"the events files have no row for {var.name}")
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


def _move_flag(quarter: str, var: Variable, moves: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    actor, action, absent_confidence = MOVE_FLAGS[var.name]
    iq = quarter_index(quarter)
    done = [row for row in moves[: max(iq + 1, 0)] if row[actor].strip() == action]
    if done:
        row = done[0]
        rule = (
            f"{var.name} is set by {actor} {action}, realized in {row['quarter']} "
            f"({MOVES_NAME}, tick {row['tick']}), so it holds at the end of {quarter}; no event "
            "row carries the flag (it records a modeled decision)"
        )
        ind = {
            "id": f"move_{row['quarter']}_{actor}",
            "value": action,
            "source": row["source"],
            "observed": quarter_bounds(row["quarter"])[1].isoformat(),
            "rule": rule,
        }
        return {"level": True, "confidence": "high", "indicators": [ind]}
    last = moves[-1]
    rule = (
        f"{var.name} is set only by {actor} {action}, which no row of {MOVES_NAME} records "
        f"(ticks 0 to {last['tick']}), so it keeps its initial level False at the end of "
        f"{quarter} ({_doc(var)} section {var.section})"
    )
    ind = {
        "id": f"moves_without_{actor}_{action}",
        "value": f"no {actor} {action} in the realized moves",
        "source": MOVES_NAME,
        "observed": quarter_bounds(last["quarter"])[1].isoformat(),
        "rule": rule,
    }
    return {"level": False, "confidence": absent_confidence, "indicators": [ind]}


def _arms_ger(r: _Reader, data: _NMC, rules: Mapping[str, Any], at_text: str) -> dict[str, Any]:
    """v0's rule, plus ``total`` from the dated planning record (the decree of 10 Jan 1942
    and Speer's appointment, 8 Feb 1942; events_ww2_v1.csv), as v0's ``high`` (decisions D12)."""
    cfg = rules["arms_GER"]
    y = r.year
    milper, milex = data.value(GMY, y, "milper"), data.value(GMY, y, "milex")
    prev = data.value(GMY, y - 1, "milex")
    gate, gate_event = v0._gate(r, "arms_GER", "rising")
    threshold = cfg["high_milper_min"]
    rule = (
        f"provisional rule for arms_GER (ontology section 2): high if NMC milper >= {threshold} "
        "thousand (a field army able to sustain a major campaign); rising if "
        f"{cfg['gate']} (events_ww2.csv) and NMC milex above the previous year's; otherwise "
        "low; high and total are also read from the dated planning record (decisions D12; "
        "events_ww2_v1.csv for total)"
    )
    total_rows = [e for e in r.history("arms_GER") if e.level == "total"]
    high_rows = [e for e in r.history("arms_GER") if e.level == "high"]
    record = total_rows[-1] if total_rows else (high_rows[-1] if high_rows else None)
    if total_rows:
        level = "total"
    elif high_rows:
        level = "high"
    elif milper is not None and milper >= threshold:
        level = "high"
    elif gate and milex is not None and prev is not None and milex > prev:
        level = "rising"
    else:
        level = "low"
    row = data.row(GMY, y)
    indicators = []
    if row is not None and milper is not None:
        indicators.append(
            _nmc_indicator(row, "milper", f"{rule}; milper {milper} vs threshold {threshold}")
        )
    if row is not None and milex is not None:
        indicators.append(_nmc_indicator(row, "milex", f"{rule}; milex {milex} vs {y - 1}: {prev}"))
    if record is not None:
        indicators.insert(
            0,
            _event_indicator(
                record, f"planning-record definition of {record.level} (decisions D12)"
            ),
        )
    if gate_event is not None:
        state = "in force" if gate else f"not yet in force at {at_text}"
        indicators.append(_event_indicator(gate_event, f"gate of the arms_GER rule, {state}"))
    return {"level": level, "confidence": "medium", "indicators": indicators}


def _arms_west(r: _Reader, data: _NMC, rules: Mapping[str, Any], at_text: str) -> dict[str, Any]:
    """v0's rule. Where France's milex is missing (1943: no NMC row) the combined value is
    not computed: the United Kingdom's alone is a lower bound, and the rule reads ``high``
    only if the bound already meets the threshold; the gap is flagged in the rule."""
    cfg = rules["arms_WEST"]
    y, base_year, k = r.year, cfg["baseline_year"], cfg["high_milex_multiple"]
    uk_now = data.get(UKG, y, "milex")
    fr_now = data.value(FRN, y, "milex")
    base = data.get(UKG, base_year, "milex") + data.get(FRN, base_year, "milex")
    uk_prev = data.get(UKG, y - 1, "milex")
    fr_prev = data.value(FRN, y - 1, "milex")
    gate, gate_event = v0._gate(r, "arms_WEST", "rising")
    rule = (
        "provisional rule for arms_WEST (ontology section 2): high if the combined United "
        f"Kingdom and France NMC milex is at least {k} times its {base_year} value (the year "
        f"before the programmes); rising if {cfg['gate']} (events_ww2.csv) and the combined "
        "milex is above the previous year's; otherwise low"
    )
    uk = data.row(UKG, y)
    fr = data.row(FRN, y)
    if fr_now is not None:
        now = uk_now + fr_now
        prev = uk_prev + fr_prev if fr_prev is not None else None
        if now >= k * base:
            level = "high"
        elif gate and prev is not None and now > prev:
            level = "rising"
        else:
            level = "low"
        detail = (
            f"combined milex {now} (UKG {uk_now} + FRN {fr_now}); {base_year}: {base} "
            f"(ratio {now / base:.2f}, threshold {k}); {y - 1}: {prev}"
        )
        value = now
    else:
        if uk_now < k * base:  # pragma: no cover - not met by the committed data
            raise ValueError(f"arms_WEST {y}: France missing and the bound does not decide")
        level = "high"
        detail = (
            f"{_gap_text(FRN, y, 'milex')}; the United Kingdom's milex alone, {uk_now}, is a "
            f"lower bound of the combined value and already {uk_now / base:.2f} times the "
            f"{base_year} value {base} (threshold {k}), so the level does not depend on the "
            "missing value"
        )
        value = uk_now
    indicators = [
        {
            "id": f"nmc_UKG_FRN_{y}_milex",
            "value": value,
            "source": _nmc_source(uk),
            "observed": f"{y}-12-31",
            "rule": f"{rule}; {detail}; {INTERPOLATED}",
        },
        _nmc_indicator(uk, "milper", "context for arms_WEST, not in the rule; UKG milper"),
    ]
    if fr is not None and fr["milper"] is not None:
        indicators.append(
            _nmc_indicator(fr, "milper", "context for arms_WEST, not in the rule; FRN milper")
        )
    else:
        data.value(FRN, y, "milper")  # record the gap
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
    rule = "arms_JPN is fixed at high in v0 and v1 (ontology section 2); NMC shown as context"
    return {
        "level": "high",
        "confidence": "medium",
        "indicators": [_nmc_indicator(row, "milex", rule), _nmc_indicator(row, "milper", rule)],
    }


def _arms_usa(r: _Reader, data: _NMC, rules: Mapping[str, Any], at_text: str) -> dict[str, Any]:
    cfg = rules["arms_USA"]
    y = r.year
    milper, milex = data.get(USA, y, "milper"), data.get(USA, y, "milex")
    prev = data.get(USA, y - 1, "milex")
    gate, gate_event = v0._gate(r, "arms_USA", "rising")
    threshold = cfg["high_milper_min"]
    rule = (
        "provisional rule for arms_USA (docs/ontology_ww2_v1.md section 2.1; decisions E7): "
        f"high if NMC milper >= {threshold} thousand; rising if {cfg['gate']} "
        "(events_ww2_v1.csv, 19 Jul 1940) and NMC milex above the previous year's; otherwise "
        "low; threshold for the historian's review"
    )
    if milper >= threshold:
        level = "high"
    elif gate and milex > prev:
        level = "rising"
    else:
        level = "low"
    row = data.row(USA, y)
    indicators = [
        _nmc_indicator(row, "milper", f"{rule}; milper {milper} vs threshold {threshold}"),
        _nmc_indicator(row, "milex", f"{rule}; milex {milex} vs {y - 1}: {prev}"),
    ]
    if gate_event is not None:
        state = "in force" if gate else f"not yet in force at {at_text}"
        indicators.append(_event_indicator(gate_event, f"gate of the arms_USA rule, {state}"))
    high_rows = [e for e in r.history("arms_USA") if e.level == "high"]
    if high_rows:
        indicators.append(
            _event_indicator(
                high_rows[-1], "cross-check for arms_USA high, not in the rule (the planning date)"
            )
        )
    return {"level": level, "confidence": "medium", "indicators": indicators}


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


def _variables(
    quarter: str,
    data: _NMC,
    events: Sequence[Event],
    moves: Sequence[Mapping[str, str]],
    rules: Mapping[str, Any],
    at: str = "end",
) -> tuple[str, dict[str, Any]]:
    first, last = quarter_bounds(quarter)
    cutoff = last if at == "end" else first
    at_text = cutoff.isoformat() + (" (end of quarter)" if at == "end" else " (before the quarter)")
    r = _Reader(events, cutoff, at == "end", first.year)
    mq = quarter if at == "end" else quarter_name(quarter_index(quarter) - 1)
    out: dict[str, Any] = {}
    for var in VARIABLES:
        if var.name == "arms_GER":
            out[var.name] = _arms_ger(r, data, rules, at_text)
        elif var.name == "arms_WEST":
            out[var.name] = _arms_west(r, data, rules, at_text)
        elif var.name == "arms_USSR":
            out[var.name] = _arms_ussr(r, data, at_text)
        elif var.name == "arms_JPN":
            out[var.name] = _arms_jpn(r, data)
        elif var.name == "arms_USA":
            out[var.name] = _arms_usa(r, data, rules, at_text)
        elif var.name == "ind_GER":
            out[var.name] = _ind_ger(r, data, rules)
        elif var.name in MOVE_FLAGS:
            out[var.name] = _move_flag(mq, var, moves)
        else:
            out[var.name] = _event_variable(r, var, at_text)
    return cutoff.isoformat(), out


# -- built-ins ---------------------------------------------------------------------------------


def _pending(
    quarter: str, actor: str, action: str, delay: int, decisions: Sequence[Decision]
) -> dict[str, Any]:
    name = f"pending_{actor}_{action}"
    iq = quarter_index(quarter)
    mine = [d for d in decisions if (d.actor, d.action) == (actor, action)]
    past = [d for d in mine if quarter_index(d.quarter) <= iq]
    if not past:
        nxt = mine[0] if mine else None
        rule = (
            f"{name} = 0: no {actor} {action} decision in {DECISIONS_NAME} at or before "
            f"{quarter}, so nothing is pending at the end of {quarter} (tick {iq + 1})"
        )
        if nxt is None:
            return {"value": 0, "confidence": "assumed", "indicators": [], "rule": rule}
        ind = _decision_indicator(nxt, f"the first such decision, dated after {quarter}")
        return {"value": 0, "confidence": "high", "indicators": [ind], "rule": rule}
    d = past[-1]
    it = quarter_index(d.quarter)
    value = max(0, delay - (iq - it))
    lands = it + 1 + delay
    arithmetic = (
        f"{name} = max(0, d - (index(Q) - index(t))) = max(0, {delay} - ({iq} - {it})) "
        f"= {value}: {actor} {action} decided {d.date.isoformat()} ({d.quarter}, model tick "
        f"{it}) with delay d = {delay}, read at the end of Q = {quarter} (tick {iq + 1}); "
    )
    if value:
        arithmetic += (
            f"the effect applies in the transition into tick {lands} (the end of "
            f"{quarter_name(lands - 1)}) and {actor} {action} is unavailable until then"
        )
    else:
        arithmetic += (
            f"the effect applied in the transition into tick {lands} (the end of "
            f"{quarter_name(lands - 1)}), so nothing is pending"
        )
    rule = arithmetic + "; the delay is the model's (docs/actions_ww2_v1.md), hence medium"
    return {
        "value": value,
        "confidence": "medium",
        "indicators": [_decision_indicator(d, f"the latest {actor} {action} decision")],
        "rule": rule,
    }


def _move_confidence(row: Mapping[str, str], actor: str, action: str) -> str:
    note = row.get("note") or ""
    if action in ("idle", "none"):
        return "medium"
    if f"{action} [SQR" in note or f"{action} [NSL" in note:
        return "medium"
    return "high"


def _last(quarter: str, actor: str, moves: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    name = f"last_{actor}"
    iq = quarter_index(quarter)
    first, last = quarter_bounds(quarter)
    if iq < 0:
        row = moves[0]
        rule = (
            f"{name} = none: the end of {quarter} is the model's tick 0, before any modeled "
            "decision (framework_spec.md section 3.1: last_<actor> starts at none)"
        )
        ind = {
            "id": f"move_{row['quarter']}_{actor}",
            "value": row[actor],
            "source": row["source"],
            "observed": quarter_bounds(row["quarter"])[1].isoformat(),
            "rule": f"the first modeled decision of {actor}, in {row['quarter']}, after {quarter}",
        }
        return {"value": "none", "confidence": "high", "indicators": [ind], "rule": rule}
    row = moves[iq]
    action = row[actor].strip()
    rule = (
        f"{name} = {action}: {actor}'s realized move of {quarter} ({MOVES_NAME}, tick {iq}), "
        f"the action chosen in the transition into tick {iq + 1}"
    )
    confidence = _move_confidence(row, actor, action)
    if action == "idle":
        rule += "; idle is a reading of the record: no catalogue action of the actor that quarter"
    elif confidence == "medium":
        rule += "; the move is placed one quarter after its historical date [SQR]"
    ind = {
        "id": f"move_{quarter}_{actor}",
        "value": action,
        "source": row["source"],
        "observed": last.isoformat(),
        "rule": f"realized move of {actor} in {quarter} ({first.isoformat()} to {last})",
    }
    return {"value": action, "confidence": confidence, "indicators": [ind], "rule": rule}


_RANK = {"high": 3, "medium": 2, "low": 1, "assumed": 0}


def fairness_series(
    levels: Mapping[str, Mapping[str, Mapping[str, Any]]],
    moves: Sequence[Mapping[str, str]],
) -> dict[str, dict[str, dict[str, Any]]]:
    """The fairness counters along the realized path (decisions E1): ``{quarter: {name:
    entry}}`` for :data:`TICK0` and every quarter in ``levels`` (in quarter order), where
    ``levels[quarter]`` is the snapshot's ``variables`` section for the end of the quarter."""
    out: dict[str, dict[str, dict[str, Any]]] = {}
    counts = {f.name: 0 for f in FAIRNESS}
    run_conf: dict[str, list[str]] = {f.name: [] for f in FAIRNESS}
    for quarter in levels:
        iq = quarter_index(quarter)
        out[quarter] = {}
        if iq < 0:
            for f in FAIRNESS:
                out[quarter][f"fair_{f.name}"] = {
                    "value": 0,
                    "confidence": "high",
                    "indicators": [
                        {
                            "id": f"model_init_fair_{f.name}",
                            "value": 0,
                            "source": "models/ww2/v1.py (framework_spec.md section 3.1)",
                            "observed": quarter_bounds(quarter)[1].isoformat(),
                            "rule": "fairness counters start at 0 in the model's initial state",
                        }
                    ],
                    "rule": (
                        f"fair_{f.name} = 0: the end of {quarter} is the model's tick 0, where "
                        "every fairness counter has its initial value 0"
                    ),
                }
            continue
        snap = levels[quarter]
        row = moves[iq]
        last = {a: row[a].strip() for a in ("GER", "WEST", "USSR", "JPN", "Nature")}
        for f in FAIRNESS:
            s = {name: snap[name]["level"] for name in f.reads}
            held = f.trigger(s, last)
            move = last[f.actor]
            responded = move in f.responses
            prev = counts[f.name]
            new = min(prev + 1, f.within) if held and not responded else 0
            counts[f.name] = new
            confs = [snap[name]["confidence"] for name in f.reads]
            confs.append(_move_confidence(row, f.actor, move))
            if new:
                run_conf[f.name] = [*run_conf[f.name], *confs]
                considered = run_conf[f.name]
            else:
                run_conf[f.name] = []
                considered = confs
            confidence = min(considered, key=_RANK.__getitem__)
            if confidence == "assumed":
                confidence = "low"
            reading = ", ".join(f"{k} = {v}" for k, v in s.items())
            why = (
                f"the trigger ({f.trigger_text}) {'holds' if held else 'does not hold'} on this "
                f"snapshot's levels ({reading}; last_GER = {last['GER']}, last_WEST = "
                f"{last['WEST']}) and {f.actor}'s realized move of {quarter} is {move}"
                f"{' (a response)' if responded else ''}"
            )
            if new:
                arithmetic = f"min({prev} + 1, {f.within}) = {new}"
            else:
                arithmetic = "0"
            rule = (
                f"fair_{f.name} = {arithmetic}: computed along the realized path (decisions "
                f"E1): {why}"
            )
            indicators = [
                {
                    "id": f"trigger_{f.name}_{quarter}",
                    "value": held,
                    "source": f"the variables section of this snapshot ({', '.join(f.reads)})",
                    "observed": quarter_bounds(quarter)[1].isoformat(),
                    "rule": f"trigger of {f.name}: {f.trigger_text}",
                },
                {
                    "id": f"move_{quarter}_{f.actor}",
                    "value": move,
                    "source": row["source"],
                    "observed": quarter_bounds(quarter)[1].isoformat(),
                    "rule": (
                        f"realized move of {f.actor} in {quarter} ({MOVES_NAME}); responses of "
                        f"{f.name}: {', '.join(f.responses)}"
                    ),
                },
            ]
            out[quarter][f"fair_{f.name}"] = {
                "value": new,
                "confidence": confidence,
                "indicators": indicators,
                "rule": rule,
            }
    return out


def build_builtins(
    quarter: str,
    events: Sequence[Event],
    decisions: Sequence[Decision],
    moves: Sequence[Mapping[str, str]],
    fair: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """The ``builtins`` section for the end of ``quarter``, in the model's state order;
    ``fair`` is the quarter's entry of :func:`fairness_series`."""
    events = sorted(events, key=lambda e: e.date)
    out: dict[str, Any] = {}
    for name in LATCHES:
        out[name] = v0._latch(quarter, name, events)
    for (actor, action), delay in DELAYED.items():
        out[f"pending_{actor}_{action}"] = _pending(quarter, actor, action, delay, decisions)
    for actor in REMEMBER_LAST:
        out[f"last_{actor}"] = _last(quarter, actor, moves)
    for f in FAIRNESS:
        out[f"fair_{f.name}"] = fair[f"fair_{f.name}"]
    return out


def _rates(rules: Mapping[str, Any]) -> dict[str, Any]:
    return {name: {"ticks": s["ticks"], "basis": s["basis"]} for name, s in rules["rates"].items()}


def build_all(
    nmc_rows: Iterable[Mapping[str, Any]],
    events: Sequence[Event],
    decisions: Sequence[Decision],
    moves: Sequence[Mapping[str, str]],
    rules: Mapping[str, Any] = ONTOLOGY_RULES,
    quarters: Iterable[str] = QUARTERS,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """The snapshots of :data:`TICK0` and ``quarters`` (which must start at 1936Q1 and be
    consecutive, since the fairness counters run along the path), and the NMC gaps met."""
    quarters = list(quarters)
    if quarters and quarters[0] != QUARTERS[0]:
        raise ValueError("the fairness counters need the quarters from 1936Q1 on")
    for a, b in zip(quarters, quarters[1:], strict=False):
        if quarter_index(b) != quarter_index(a) + 1:
            raise ValueError(f"quarters must be consecutive: {a} then {b}")
    data = _NMC(nmc_rows)
    events = sorted(events, key=lambda e: e.date)
    dated: dict[str, tuple[str, dict[str, Any]]] = {}
    for q in [TICK0, *quarters]:
        dated[q] = _variables(q, data, events, moves, rules)
    fair = fairness_series({q: v for q, (_, v) in dated.items()}, moves)
    out: dict[str, dict[str, Any]] = {}
    for q, (day, variables) in dated.items():
        out[q] = {
            "$schema": "../../schema.json",
            "date": day,
            "model": MODEL,
            "variables": variables,
            "builtins": build_builtins(q, events, decisions, moves, fair[q]),
            "rates": _rates(rules),
        }
    return out, sorted(data.gaps)


def build(
    quarter: str,
    nmc_rows: Iterable[Mapping[str, Any]],
    events: Sequence[Event],
    decisions: Sequence[Decision],
    moves: Sequence[Mapping[str, str]],
    rules: Mapping[str, Any] = ONTOLOGY_RULES,
) -> dict[str, Any]:
    """The snapshot for the end of ``quarter`` (``1935Q4`` to ``1945Q3``)."""
    iq = quarter_index(quarter)
    upto = [q for q in QUARTERS if quarter_index(q) <= iq]
    snaps, _ = build_all(nmc_rows, events, decisions, moves, rules, upto)
    return snaps[quarter]


def nmc_gaps(
    nmc_rows: Iterable[Mapping[str, Any]],
    events: Sequence[Event],
    decisions: Sequence[Decision],
    moves: Sequence[Mapping[str, str]],
) -> list[str]:
    """The NMC gaps the readings of the 40 snapshots meet (flagged, never filled)."""
    return build_all(nmc_rows, events, decisions, moves)[1]


def start_levels(
    quarter: str,
    nmc_rows: Iterable[Mapping[str, Any]],
    events: Sequence[Event],
    moves: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    """The levels in force on the first day of ``quarter``; for 1936Q1 these are the
    ontology's initial levels (tested)."""
    data = _NMC(nmc_rows)
    events = sorted(events, key=lambda e: e.date)
    _, variables = _variables(quarter, data, events, moves, ONTOLOGY_RULES, at="start")
    return {k: v["level"] for k, v in variables.items()}


# -- checks ------------------------------------------------------------------------------------


def check_against_ontology(snapshot: Mapping[str, Any]) -> list[str]:
    """As v0's check, against the v1 variables."""
    problems = []
    given = snapshot.get("variables", {})
    for name, entry in given.items():
        if name in HIDDEN:
            problems.append(f"{name} is swept by the model and must not be fixed")
            continue
        var = BY_NAME.get(name)
        if var is None:
            problems.append(f"{name} is not a WW2 v1 ontology variable")
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


def check_builtins(snapshot: Mapping[str, Any]) -> list[str]:
    given = list(snapshot.get("builtins", {}))
    problems = [
        f"builtin {n} is not a built-in of {MODEL}" for n in given if n not in BUILTIN_NAMES
    ]
    problems += [f"builtin {n} is missing" for n in BUILTIN_NAMES if n not in given]
    return problems


_NAME_CELL = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)`(?:\s*\(v0\))?")


def _cell_levels(cell: str) -> tuple[Any, ...]:
    cell = cell.replace("**", "").strip()
    if cell == "flag":
        return (False, True)
    parts = tuple(p.strip() for p in cell.split(","))
    if parts == ("False", "True"):
        return (False, True)
    return tuple(int(p) if p.isdigit() else p for p in parts)


def parse_ontology(
    paths: Sequence[str | Path] = DEFAULT_ONTOLOGY,
) -> dict[str, dict[str, Any]]:
    """The variable tables of the v0 ontology overlaid with the v1 delta document,
    header-aware: a table declares variables when its header has ``Variable`` first and a
    ``Levels`` column; ``Init`` is any column whose header starts with ``Init``; bold level
    additions (``**total**``) are read as levels, and ``(v0)`` after a name marks a v0
    variable restated. ``{name: {levels, init, section, doc}}``."""
    out: dict[str, dict[str, Any]] = {}
    for path in paths:
        section = ""
        in_table = is_variables = False
        levels_col = init_col = None
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            m = re.match(r"## (\d+)", line)
            if m:
                section = m.group(1)
            if not line.startswith("|"):
                in_table = False
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not in_table:
                in_table = True
                levels_col = next((i for i, c in enumerate(cells) if c == "Levels"), None)
                is_variables = cells[0] == "Variable" and levels_col is not None
                init_col = next((i for i, c in enumerate(cells) if c.startswith("Init")), None)
                continue
            name = _NAME_CELL.fullmatch(cells[0])
            if not is_variables or not name or len(cells) < 2:
                continue
            init: Any = None
            if init_col is not None:
                raw = cells[init_col].replace("**", "").strip()
                init = (raw == "True") if raw in ("True", "False") else raw
            old = out.get(name.group(1), {})
            out[name.group(1)] = {
                "levels": _cell_levels(cells[levels_col]),
                "init": init if init_col is not None else old.get("init"),
                "section": section,
                "doc": Path(path).name,
            }
    for spec in out.values():
        if isinstance(spec["init"], str) and spec["init"].isdigit():
            spec["init"] = int(spec["init"])
    return out


def ontology_mismatches(paths: Sequence[str | Path] = DEFAULT_ONTOLOGY) -> list[str]:
    """Differences between :data:`VARIABLES` (plus :data:`HIDDEN`) and the two documents."""
    doc = parse_ontology(paths)
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


# -- command line ------------------------------------------------------------------------------


def _dump(snapshot: Mapping[str, Any]) -> str:
    return json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m wavefront.evidence.hindsight_ww2_v1",
        description="Build the WW2 v1 hindsight snapshots, 1935Q4 (tick 0) to 1945Q3.",
    )
    parser.add_argument("--out", type=Path, required=True, help="output directory")
    parser.add_argument("--nmc", type=Path, nargs="+", default=list(DEFAULT_NMC))
    parser.add_argument("--events", type=Path, nargs="+", default=list(DEFAULT_EVENTS))
    parser.add_argument("--ontology", type=Path, nargs="+", default=list(DEFAULT_ONTOLOGY))
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--moves", type=Path, default=DEFAULT_MOVES)
    parser.add_argument(
        "--check", action="store_true", help="compare with the files in --out; write nothing"
    )
    args = parser.parse_args(argv)

    problems = []
    if all(p.exists() for p in args.ontology):
        problems += [f"ontology: {p}" for p in ontology_mismatches(args.ontology)]
    decisions, moves = load_decisions(args.decisions), load_moves(args.moves)
    problems += check_decisions_against_moves(decisions, moves)
    snapshots, gaps = build_all(load_nmc(args.nmc), load_events(args.events), decisions, moves)
    for quarter, snap in snapshots.items():
        problems += [f"{quarter}: {p}" for p in validate_snapshot(snap)]
        problems += [f"{quarter}: {p}" for p in check_against_ontology(snap)]
        problems += [f"{quarter}: {p}" for p in check_builtins(snap)]
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
    if gaps:
        print("NMC gaps flagged (not filled): " + "; ".join(gaps))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
