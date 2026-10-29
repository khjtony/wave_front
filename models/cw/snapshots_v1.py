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
  decisions D7, with ``belief_force_USA`` on the projected-count scale of the owner's decision
  7g (v1's belief rows, each citing the estimate and its numbers) and without v0's ``replay``
  rows of ``nuke_USSR`` (docs/cw_v1_decisions.md D9). Where the belief row records the date the
  estimate projects for and the projected number (the owner's decision 7i), the replay entry of
  ``belief_force_USA`` carries them as a second indicator, read by :func:`projection`.
* **The count** ``count_USSR`` (hindsight, and the truth of ``belief_force_USA``): the bands of
  ``data/cw/v1/strategic_launchers.csv`` through its ``record`` rows in
  ``data/cw/v1/events.csv``.

Regenerate and check::

    python -m models.cw.snapshots_v1 --out snapshots/cw_v1
    python -m models.cw.snapshots_v1 --out snapshots/cw_v1 --check
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import re
import sys
from datetime import date
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


# The owner's decision 7g (2026-10-28, before first sight; docs/cw_v1_decisions.md D9):
# belief_force_USA is the projected count of Soviet intercontinental delivery vehicles, whose
# hindsight truth is count_USSR. v0's rows on the survivability scale are not read in v1: its
# belief rows of belief_force_USA (replaced by v1's), and its replay rows of nuke_USSR, which
# coded the projected missile force as a survivable one (the projected ICBMs of 1958 to 1961
# were soft; reports/replay_cw_crest_projected.md); the projection is now the belief's, and the
# replay snapshots carry the hindsight nuke_USSR as ``assumed``.
TRUTH_V1 = {**TRUTH, "belief_force_USA": "count_USSR"}
DROPPED_V0_ROWS = (("belief_force_USA", "belief"), ("nuke_USSR", "replay"))

# The owner's decision 7i (2026-10-28, before first sight; docs/cw_v1_decisions.md D9): V6
# compares the projected count with the hindsight count at the date the estimate projects for.
# The belief rows record that date and the number (columns projected_for, projected_count);
# the replay snapshot carries them in an indicator whose value is "<number> for <date>".
BELIEF = "belief_force_USA"
PROJECTION = re.compile(r"^(\d+) for (\d{4}-\d{2}-\d{2})$")


def events() -> list[dict[str, str]]:
    """v0's dated events, less the rows of ``DROPPED_V0_ROWS``, followed by v1's additions."""
    with open(EVENTS_V1, newline="", encoding="utf-8") as fh:
        added = list(csv.DictReader(line for line in fh if not line.startswith("#")))
    kept = [r for r in v0_snapshots.events() if (r["variable"], r["series"]) not in DROPPED_V0_ROWS]
    return kept + added


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
        if name in TRUTH_V1:
            row = _latest(rows, TRUTH_V1[name], ("record",), tick)
            rule = (
                f"hindsight truth of the estimated quantity ({TRUTH_V1[name]} in the record; "
                "decisions D6, and D9 of docs/cw_v1_decisions.md)"
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
            indicators = [_indicator(row, "the contemporaneous reading dated before 1 January")]
            if row.get("projected_for"):
                indicators.append(_projection_indicator(row))
            out[name] = {
                "level": _flag(row["level"]),
                "confidence": "medium",
                "indicators": indicators,
            }
        else:
            entry = copy.deepcopy(data["variables"][name])
            entry["confidence"] = "assumed"
            for ind in entry["indicators"]:
                ind["rule"] = "not read in the manual replay: the hindsight level. " + ind["rule"]
            out[name] = entry
    data["variables"] = out
    return data


def _projection_indicator(row: dict[str, str]) -> dict[str, Any]:
    return {
        "id": f"projection_{row['year']}_{row['variable']}",
        "value": f"{int(row['projected_count'])} for {row['projected_for']}",
        "source": row["source"],
        "observed": row["estimate_date"],
        "rule": (
            "the date the estimate (of the observed date) projects for, from its own text, and "
            "the projected number there (every range at its midpoint, linear between its stated "
            "milestones); V6 compares the band with the hindsight count_USSR at that date, read "
            "from the hindsight snapshot of the latest 1 January not after it (the owner's "
            "decision 7i; docs/cw_v1_decisions.md D9 and R V6)"
        ),
    }


def _projection_of(entry: dict[str, Any]) -> dict[str, Any] | None:
    return next((i for i in entry["indicators"] if i["id"].startswith("projection_")), None)


def projection(year: int, kind: str = "replay") -> tuple[date, int] | None:
    """The date the manually replayed ``belief_force_USA`` of 1 January ``year`` projects for
    and the projected number, from the replay snapshot (None if its row records none)."""
    path = SNAPSHOTS / kind / f"{year}.json"
    ind = _projection_of(json.loads(path.read_text(encoding="utf-8"))["variables"][BELIEF])
    if ind is None:
        return None
    m = PROJECTION.match(str(ind["value"]))
    if m is None:
        raise ValueError(f"{path}: malformed projection {ind['value']!r}")
    return date.fromisoformat(m.group(2)), int(m.group(1))


def year_read_at(day: date) -> int:
    """The hindsight snapshot read for the count at ``day``: the latest 1 January not after it.
    The counts are end-of-year force levels (Norris and Cochran 1990, Table 2), so for a
    mid-year date this is the count in being half a year before it, never a vehicle deployed
    after it (docs/cw_v1_decisions.md R V6)."""
    return day.year


def projected_year(year: int) -> int:
    """The year of the hindsight snapshot read against the manual replay of ``year`` on its
    recorded projected date (the owner's decision 7i; docs/cw_v1_decisions.md D9)."""
    found = projection(year)
    if found is None:
        raise ValueError(f"replay {year}: no projected date recorded")
    return year_read_at(found[0])


# The owner's decision 7k (2026-10-28, before first sight; docs/cw_v1_decisions.md R V6): V6's
# replay input is the blind replay at proposal level, whose proposals carry the date and level
# of an estimate but not the date it projects for. Its projected date is fixed by rule: the
# estimate's date plus 30 months, the midpoint of decision 7d's "two to three years after its
# own date" (the midpoint rule of decision 7i applied to the horizon). The same rule is applied
# to the manual series, from the date of its estimate, when it is printed beside.
BLIND_REPLAY_ENV = "WF_CWV1_BLIND_REPLAY"
HORIZON_MONTHS = 30


def estimate_date(entry: dict[str, Any]) -> date | None:
    """The date of the estimate behind a snapshot entry of ``belief_force_USA``: the observed
    date of the manual replay's projection indicator if it has one, else the latest observed
    date of its indicators (the blind replay's latest proposal at the level in force); None
    if it has no indicator (the initial level, no estimate read)."""
    ind = _projection_of(entry)
    if ind is not None:
        return date.fromisoformat(ind["observed"])
    days = [date.fromisoformat(i["observed"]) for i in entry["indicators"]]
    return max(days) if days else None


def rule_projected_date(estimate: date) -> date:
    """The projected date by the rule of decision 7k: ``estimate`` plus 30 months (the day
    clipped to 28 so that every month has it)."""
    months = estimate.year * 12 + estimate.month - 1 + HORIZON_MONTHS
    return date(months // 12, months % 12 + 1, min(estimate.day, 28))


def rule_year(year: int, entry: dict[str, Any]) -> int:
    """The hindsight snapshot read against the replayed belief of 1 January ``year`` by the
    rule of decision 7k; with no estimate behind the entry, the snapshot's own year."""
    estimate = estimate_date(entry)
    return year if estimate is None else year_read_at(rule_projected_date(estimate))


def blind_snapshots(replay_dir: str | Path, years) -> dict[int, dict[str, Any]]:
    """The blind replay of ``years`` in ``replay_dir`` (the ``--out`` of ``wf replay --episode
    cw``) at proposal level: every proposal treated as accepted, as ``wf replay
    --measure-proposals`` reads it (:func:`wavefront.evidence.replay.measured_snapshots`), the
    variables the replay does not read carried from the cw_v1 hindsight snapshots. Raises
    FileNotFoundError if the directory has no proposals and ValueError if a year is missing."""
    from wavefront.evidence.episodes import CW
    from wavefront.evidence.replay import measured_snapshots

    proposals = Path(replay_dir) / "proposals"
    if not proposals.is_dir():
        raise FileNotFoundError(f"{proposals}: no blind replay proposals (decision 7k)")
    labels = [str(y) for y in years]
    snaps = measured_snapshots(proposals, labels, SNAPSHOTS / "hindsight", None, episode=CW)
    missing = [y for y in labels if y not in snaps]
    if missing:
        raise ValueError(f"{proposals}: no proposals file for {', '.join(missing)}")
    return {int(y): snaps[y] for y in labels}


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


def snapshot_data(
    year: int, aims_USSR: str, kind: str = "hindsight", data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """The parsed snapshot with the swept variables fixed for one hypothesis, as v0's; with
    ``data``, that snapshot (of ``kind``, e.g. a blind replay's) instead of the file."""
    if data is None:
        path = SNAPSHOTS / kind / f"{year}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = copy.deepcopy(data)
    fixed = {"aims_USSR": aims_USSR}
    if kind == "hindsight":
        fixed["belief_USA_USSR"] = aims_USSR
    for name, level in fixed.items():
        data["variables"][name] = {"level": level, "confidence": "assumed", "indicators": []}
    return data


def snapshot_state(
    cm: CompiledModel,
    year: int,
    aims_USSR: str,
    kind: str = "hindsight",
    data: dict[str, Any] | None = None,
) -> tuple[int, ...]:
    """The state of ``cm`` (a v1 build) on 1 January ``year`` from the snapshot of ``kind``
    (or ``data``) with its built-ins, for one hypothesis."""
    state = list(snapshot_to_state(snapshot_data(year, aims_USSR, kind, data), cm))
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
