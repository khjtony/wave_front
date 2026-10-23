"""Hindsight and replay snapshots of Cold War v0, built from ``data/cw/events.csv`` and
``data/cw/decisions.csv`` (decisions D6 and D7).

A snapshot named ``<year>.json`` is the state on 1 January of that year, which is the model's
state at tick ``year - 1947``; ``1947.json`` is tick 0 and ``1992.json`` the horizon.

* **Hindsight** (``snapshots/cw/hindsight/``, 1947 to 1992): every declared variable at the
  level of the latest ``record`` row visible by that date. A belief variable takes the
  hindsight truth of what it estimates (coldwar_testbed.md section 6.1: belief data are kept
  separate from hindsight truth): ``belief_force_USA`` the record's ``nuke_USSR``,
  ``belief_USSR_USA`` the record's American aims. ``aims_USSR`` and ``belief_USA_USSR`` (whose
  truth is the swept hypothesis) are left out; :func:`snapshot_state` fixes both per
  hypothesis. The built-ins are the pending delayed decisions of ``decisions.csv``.
* **Replay** (``snapshots/cw/replay/``, 1957 to 1962 and 1983): the manual replay of decisions
  D7. Belief variables take the latest ``belief`` row, and a variable with ``replay`` rows the
  latest of them, both from documents dated before the snapshot; every other variable is
  carried from the hindsight snapshot with ``confidence: "assumed"``. It is not the blind
  pipeline of docs/replay_harness.md, whose corpora are not reachable from the development
  environment (data/cw/README.md).

Regenerate and check::

    python -m models.cw.snapshots --out snapshots/cw
    python -m models.cw.snapshots --out snapshots/cw --check
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
from pathlib import Path
from typing import Any

from wavefront.evidence import snapshot_to_state, validate_snapshot
from wavefront.model.compile import CompiledModel

from .v0 import DATA, ROOT, YEAR0, model

SNAPSHOTS = ROOT / "snapshots" / "cw"
EVENTS = DATA / "events.csv"
DECISIONS = DATA / "decisions.csv"
YEARS = range(1947, 1993)
REPLAY_YEARS = (1957, 1958, 1959, 1960, 1961, 1962, 1983)
BELIEFS = ("belief_force_USA", "belief_USA_USSR", "belief_USSR_USA")
SWEPT = ("aims_USSR", "belief_USA_USSR")  # fixed per hypothesis (decisions D6)
# The hindsight truth of each belief variable: the record variable it estimates.
TRUTH = {"belief_force_USA": "nuke_USSR", "belief_USSR_USA": "belief_USSR_USA"}


def events() -> list[dict[str, str]]:
    with open(EVENTS, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(line for line in fh if not line.startswith("#")))


def decisions() -> list[dict[str, str]]:
    with open(DECISIONS, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _flag(level: str) -> Any:
    return {"True": True, "False": False}.get(level, level)


def _indicator(row: dict[str, str], rule: str) -> dict[str, Any]:
    note = f" Note: {row['note']}" if row["note"] else ""
    return {
        "id": f"event_{row['year']}_{row['variable']}_{row['series']}",
        "value": row["event"],
        "source": row["source"],
        "observed": f"{row['year']}-12-31" if int(row["year"]) >= YEAR0 - 1 else row["year"],
        "rule": rule + note,
    }


def _latest(rows, variable: str, series: tuple[str, ...], tick: int):
    found = [
        r
        for r in rows
        if r["variable"] == variable and r["series"] in series and int(r["visible_tick"]) <= tick
    ]
    return max(found, key=lambda r: int(r["visible_tick"])) if found else None


def _builtins(tick: int) -> dict[str, Any]:
    out = {}
    for d in decisions():
        t, delay = int(d["tick"]), int(d["delay_years"])
        if delay and t < tick <= t + delay:
            out[f"pending_{d['actor']}_{d['action']}"] = {
                "value": t + 1 + delay - tick,
                "confidence": "high",
                "indicators": [
                    {
                        "id": f"decision_{d['year']}_{d['actor']}_{d['action']}",
                        "value": f"{d['actor']}.{d['action']} decided {d['year']}",
                        "source": d["source"],
                        "observed": f"{d['year']}-12-31",
                        "rule": "years until the delayed effect of the decision is visible "
                        "(framework_spec.md section 3.1)",
                    }
                ],
                "rule": f"decided at tick {t} with delay {delay}: pending t + 1 + d - T",
            }
    return out


def hindsight(year: int) -> dict[str, Any]:
    """The hindsight snapshot of 1 January ``year``."""
    tick = year - YEAR0
    rows = events()
    variables: dict[str, Any] = {}
    for decl in model.variables:
        name = decl.name
        if name in SWEPT:
            continue
        if name in TRUTH:
            row = _latest(rows, TRUTH[name], ("record",), tick)
            rule = (
                f"hindsight truth of the estimated quantity ({TRUTH[name]} in the record; "
                "decisions D6)"
            )
        else:
            row = _latest(rows, name, ("record",), tick)
            rule = "the record row in force on 1 January (data/cw/events.csv)"
        if row is None:
            raise ValueError(f"{year}: no record row for {name}")
        variables[name] = {
            "level": _flag(row["level"]),
            "confidence": "medium" if "not verified" in row["note"] else "high",
            "indicators": [_indicator(row, rule)],
        }
    data = {
        "$schema": "../../schema.json",
        "date": f"{year}-01-01",
        "model": model.name,
        "variables": variables,
        "rates": {},
    }
    builtins = _builtins(tick)
    if builtins:
        data["builtins"] = builtins
    return data


def replay(year: int) -> dict[str, Any]:
    """The manual replay snapshot of 1 January ``year`` (decisions D7)."""
    tick = year - YEAR0
    rows = events()
    data = hindsight(year)
    data["$schema"] = "../../schema.json"
    out: dict[str, Any] = {}
    for decl in model.variables:
        name = decl.name
        if name == "aims_USSR":
            continue
        series = ("belief",) if name in BELIEFS else ("replay",)
        row = _latest(rows, name, series, tick)
        if row is not None and name not in BELIEFS:
            # a contemporaneous reading stands until the record moves past it
            later = _latest(rows, name, ("record",), tick)
            if later is not None and int(later["visible_tick"]) > int(row["visible_tick"]):
                row = None
        if row is not None:
            out[name] = {
                "level": _flag(row["level"]),
                "confidence": "medium",
                "indicators": [
                    _indicator(row, "the contemporaneous reading dated before 1 January")
                ],
            }
        else:
            entry = copy.deepcopy(data["variables"][name])
            entry["confidence"] = "assumed"
            for ind in entry["indicators"]:
                ind["rule"] = "not read in the manual replay: the hindsight level. " + ind["rule"]
            out[name] = entry
    data["variables"] = out
    return data


def write(out: Path, check: bool = False) -> list[str]:
    """Write (or with ``check`` compare) every snapshot; return the problems."""
    problems = []
    targets = [(out / "hindsight" / f"{y}.json", hindsight(y)) for y in YEARS]
    targets += [(out / "replay" / f"{y}.json", replay(y)) for y in REPLAY_YEARS]
    for path, data in targets:
        problems += [f"{path}: {p}" for p in validate_snapshot(data)]
        text = json.dumps(data, indent=1, ensure_ascii=False) + "\n"
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                problems.append(f"{path}: out of date")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    return problems


def snapshot_data(year: int, aims_USSR: str, kind: str = "hindsight") -> dict[str, Any]:
    """The parsed snapshot with the swept variables fixed for one hypothesis: ``aims_USSR``,
    and in a hindsight snapshot ``belief_USA_USSR`` at the hypothesis's own level (its
    hindsight truth; decisions D6), both ``assumed``."""
    path = SNAPSHOTS / kind / f"{year}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    fixed = {"aims_USSR": aims_USSR}
    if kind == "hindsight":
        fixed["belief_USA_USSR"] = aims_USSR
    for name, level in fixed.items():
        data["variables"][name] = {"level": level, "confidence": "assumed", "indicators": []}
    return data


def snapshot_state(
    cm: CompiledModel, year: int, aims_USSR: str, kind: str = "hindsight"
) -> tuple[int, ...]:
    """The state of ``cm`` on 1 January ``year`` (tick ``year - 1947``) from the snapshot of
    ``kind`` with its built-ins, for one hypothesis."""
    state = list(snapshot_to_state(snapshot_data(year, aims_USSR, kind), cm))
    state[cm.index["tick"]] = year - YEAR0
    return tuple(state)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=SNAPSHOTS)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    problems = write(args.out, args.check)
    for p in problems:
        print(p, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
