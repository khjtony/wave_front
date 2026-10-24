"""Hindsight and replay snapshots of Cold War v1, built from ``data/cw/events.csv`` with
``data/cw/v1/events.csv`` and from ``data/cw/decisions.csv`` with ``data/cw/v1/decisions.csv``
(docs/cw_v1_decisions.md D5, the conventions of v0's decisions D6 and D7, which the owner's
decision 3b keeps).

A snapshot named ``<year>.json`` is the state on 1 January of that year (tick ``year -
1947``). The rules are v0's (``models/cw/snapshots.py``):

* **Hindsight** (``snapshots/cw_v1/hindsight/``, 1947 to 1992): every declared variable at
  the level of the latest ``record`` row visible by that date; a belief variable takes the
  hindsight truth of what it estimates; ``aims_USSR`` and ``belief_USA_USSR`` are fixed per
  hypothesis by :func:`snapshot_state`; the built-ins are the pending delayed decisions.
* **Replay** (``snapshots/cw_v1/replay/``, 1957 to 1962 and 1983): the manual replay of v0's
  decisions D7, unchanged (v1 adds no belief and no ``replay`` row).

Regenerate and check::

    python -m models.cw.snapshots_v1 --out snapshots/cw_v1
    python -m models.cw.snapshots_v1 --out snapshots/cw_v1 --check
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

from . import snapshots as v0_snapshots
from .snapshots import BELIEFS, REPLAY_YEARS, SWEPT, TRUTH, YEARS, _flag, _indicator, _latest
from .v1 import DATA_V1, ROOT, YEAR0, model

SNAPSHOTS = ROOT / "snapshots" / "cw_v1"
EVENTS_V1 = DATA_V1 / "events.csv"
DECISIONS_V1 = DATA_V1 / "decisions.csv"


def events() -> list[dict[str, str]]:
    """v0's dated events followed by v1's additions."""
    with open(EVENTS_V1, newline="", encoding="utf-8") as fh:
        added = list(csv.DictReader(line for line in fh if not line.startswith("#")))
    return v0_snapshots.events() + added


def decisions() -> list[dict[str, str]]:
    """v0's dated decisions followed by v1's additions."""
    with open(DECISIONS_V1, newline="", encoding="utf-8") as fh:
        return v0_snapshots.decisions() + list(csv.DictReader(fh))


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
            rule = (
                "the record row in force on 1 January (data/cw/events.csv, data/cw/v1/events.csv)"
            )
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
    """The manual replay snapshot of 1 January ``year`` (v0's decisions D7)."""
    tick = year - YEAR0
    rows = events()
    data = hindsight(year)
    out: dict[str, Any] = {}
    for decl in model.variables:
        name = decl.name
        if name == "aims_USSR":
            continue
        series = ("belief",) if name in BELIEFS else ("replay",)
        row = _latest(rows, name, series, tick)
        if row is not None and name not in BELIEFS:
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
    """The parsed snapshot with the swept variables fixed for one hypothesis, as v0's."""
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
    """The state of ``cm`` (a v1 build) on 1 January ``year`` from the snapshot of ``kind``
    with its built-ins, for one hypothesis."""
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
