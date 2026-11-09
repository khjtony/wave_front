"""Build the ambiguous layers of snapshots from the canonical files and the window tables.

Owner's decision 7j (docs/owner_decisions_2026-10-23.md): the candidate windows of
docs/ambiguous_levels.md section 8 are applied in a separate layer, so that the canonical
snapshots (the registered claims' start states, read by the single-state loaders) are
unchanged. A layer holds only the files of the window quarters; each is a copy of the
canonical file in which every windowed variable is given as a set of levels (``levels`` with
``ambiguity``, docs/framework_spec.md section 9), and nothing else differs.

Inputs, both declarative:

- ``data/ambiguous_windows.csv``: one row per window (``episode``, ``variable``, ``levels``
  separated by ``;``, ``first`` and ``last`` quarter or year inclusive, ``status``,
  ``ambiguity``, ``sources``). Only rows with ``status == "build"`` are built; any other
  status (such as the Cold War row, to be built after cw_v1's replay coding is final) is
  recorded and skipped, and its ``levels`` are not parsed.
- ``data/ambiguous_members.csv``: the indicators of the members whose level differs from
  the canonical file's (``episodes`` separated by spaces, ``variable``, ``level``,
  ``confidence``, ``first``: the first window file the indicator is attached to, and the
  indicator's ``id``, ``observed``, ``value``, ``source``, ``rule``). The member whose level
  is the canonical one is the canonical entry itself (level, confidence and indicators).

Run ``python scripts/build_ambiguous_layer.py`` to write the layers (stale files in a layer
directory are removed) and ``--check`` to verify that they are up to date (exit 1 if not).
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = ROOT / "data" / "ambiguous_windows.csv"
MEMBERS = ROOT / "data" / "ambiguous_members.csv"
BUILD = "build"

#: episode -> (canonical directory, layer directory)
EPISODES: dict[str, tuple[Path, Path]] = {
    "ww2_v0": (
        ROOT / "snapshots" / "ww2" / "hindsight",
        ROOT / "snapshots" / "ww2" / "hindsight_ambiguous",
    ),
    "ww2_v1": (
        ROOT / "snapshots" / "ww2" / "hindsight_v1",
        ROOT / "snapshots" / "ww2" / "hindsight_v1_ambiguous",
    ),
    "cw_v1_replay": (
        ROOT / "snapshots" / "cw_v1" / "replay",
        ROOT / "snapshots" / "cw_v1" / "replay_ambiguous",
    ),
}


class LayerError(Exception):
    pass


@dataclass(frozen=True)
class Window:
    episode: str
    variable: str
    levels: tuple[str, ...]
    first: str
    last: str
    status: str
    ambiguity: str
    sources: str

    @property
    def built(self) -> bool:
        return self.status == BUILD

    @property
    def periods(self) -> list[str]:
        return periods(self.first, self.last)


def periods(first: str, last: str) -> list[str]:
    """The quarters (``1938Q2``) or years (``1958``) from ``first`` to ``last`` inclusive."""
    if "Q" in first:
        (y0, q0), (y1, q1) = (map(int, p.split("Q")) for p in (first, last))
        out = []
        y, q = y0, q0
        while (y, q) <= (y1, q1):
            out.append(f"{y}Q{q}")
            y, q = (y, q + 1) if q < 4 else (y + 1, 1)
        return out
    return [str(y) for y in range(int(first), int(last) + 1)]


def read_windows(path: Path = WINDOWS) -> list[Window]:
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for row in rows:
        w = Window(
            episode=row["episode"],
            variable=row["variable"],
            levels=tuple(lv.strip() for lv in row["levels"].split(";"))
            if row["status"] == BUILD
            else (),
            first=row["first"],
            last=row["last"],
            status=row["status"],
            ambiguity=row["ambiguity"].strip(),
            sources=row["sources"].strip(),
        )
        if w.episode not in EPISODES:
            raise LayerError(f"{path}: unknown episode {w.episode!r}")
        if w.built and len(set(w.levels)) < 2:
            raise LayerError(f"{path}: window {w.episode} {w.variable} needs two levels")
        if not w.ambiguity:
            raise LayerError(f"{path}: window {w.episode} {w.variable} has no ambiguity text")
        out.append(w)
    return out


def read_members(path: Path = MEMBERS) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _parse(text: str, like: Any) -> Any:
    """A level as the canonical file writes it: a boolean, an integer or a name."""
    if isinstance(like, bool):
        if text not in ("true", "false"):
            raise LayerError(f"level {text!r} is not a boolean")
        return text == "true"
    if isinstance(like, int):
        return int(text)
    return text


def _member(window: Window, level: str, period: str, canonical: dict, members) -> dict:
    """The member entry for ``level`` at ``period``: the canonical entry where the level is
    the canonical one, else the indicators of the members table attached from ``first``."""
    value = _parse(level, canonical["level"])
    if value == canonical["level"]:
        return {k: copy.deepcopy(canonical[k]) for k in ("level", "confidence", "indicators")}
    order = window.periods
    rows = [
        r
        for r in members
        if window.episode in r["episodes"].split()
        and r["variable"] == window.variable
        and r["level"] == level
        and r["first"] in order
        and order.index(r["first"]) <= order.index(period)
    ]
    if not rows:
        raise LayerError(
            f"{window.episode} {window.variable}={level} at {period}: no member indicator"
        )
    confidence = {r["confidence"] for r in rows}
    if len(confidence) != 1:
        raise LayerError(f"{window.episode} {window.variable}={level}: mixed confidence")
    return {
        "level": value,
        "confidence": confidence.pop(),
        "indicators": [
            {k: r[k] for k in ("id", "value", "source", "observed", "rule")} for r in rows
        ],
    }


def build_episode(episode: str, windows: list[Window], members) -> dict[str, str]:
    """The layer of ``episode``: file name -> text."""
    canonical_dir, _ = EPISODES[episode]
    mine = [w for w in windows if w.episode == episode and w.built]
    files: dict[str, dict] = {}
    for w in mine:
        for period in w.periods:
            name = f"{period}.json"
            if name not in files:
                path = canonical_dir / name
                if not path.exists():
                    raise LayerError(f"{episode}: no canonical file {path}")
                files[name] = json.loads(path.read_text(encoding="utf-8"))
            data = files[name]
            entry = data["variables"].get(w.variable)
            if entry is None or "level" not in entry:
                raise LayerError(f"{episode} {name}: {w.variable} is not a single level")
            if entry["level"] not in [_parse(lv, entry["level"]) for lv in w.levels]:
                raise LayerError(
                    f"{episode} {name}: the canonical level {entry['level']!r} of "
                    f"{w.variable} is not a member of {w.levels}"
                )
            data["variables"][w.variable] = {
                "levels": [_member(w, lv, period, entry, members) for lv in w.levels],
                "ambiguity": f"{w.ambiguity} Sources: {w.sources}.",
            }
    return {name: json.dumps(d, indent=2, ensure_ascii=False) + "\n" for name, d in files.items()}


def build_all(windows=None, members=None) -> dict[Path, dict[str, str]]:
    """Every layer with a built window: layer directory -> {file name: text}."""
    from wavefront.evidence import validate_snapshot

    windows = read_windows() if windows is None else windows
    members = read_members() if members is None else members
    out = {}
    for episode in sorted({w.episode for w in windows if w.built}):
        texts = build_episode(episode, windows, members)
        for name, text in texts.items():
            problems = validate_snapshot(json.loads(text))
            if problems:
                raise LayerError(f"{episode} {name}: {problems}")
        out[EPISODES[episode][1]] = texts
    return out


def stale(layers: dict[Path, dict[str, str]]) -> list[str]:
    """Differences between the layers on disk and the built ones."""
    found = []
    for layer, texts in layers.items():
        on_disk = {p.name for p in layer.glob("*.json")} if layer.exists() else set()
        for name in sorted(on_disk - set(texts)):
            found.append(f"{layer / name}: not in the window table")
        for name, text in texts.items():
            path = layer / name
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                found.append(f"{path}: out of date")
    return found


def write(layers: dict[Path, dict[str, str]]) -> None:
    for layer, texts in layers.items():
        layer.mkdir(parents=True, exist_ok=True)
        for p in layer.glob("*.json"):
            if p.name not in texts:
                p.unlink()
        for name, text in texts.items():
            path = layer / name
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                path.write_text(text, encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="verify the layers, write nothing")
    args = ap.parse_args(argv)
    windows = read_windows()
    layers = build_all(windows)
    for w in windows:
        if not w.built:
            print(f"skipped: {w.episode} {w.variable} {w.first}..{w.last} ({w.status})")
    if args.check:
        found = stale(layers)
        for line in found:
            print(line)
        return 1 if found else 0
    write(layers)
    for layer, texts in layers.items():
        print(f"{layer.relative_to(ROOT)}: {', '.join(sorted(texts))}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    sys.exit(main())
