"""Correlates of War, National Material Capabilities (NMC).

One row per state and year with ``irst`` (iron and steel production, thousands of tons),
``milex`` (military expenditure, thousands of current US dollars from 1914), ``milper``
(military personnel, thousands), ``pec`` (primary energy consumption, thousands of coal-ton
equivalents), ``tpop`` and ``upop`` (total and urban population, thousands) and ``cinc``.

Two file forms are accepted:

* the official CSV (columns ``stateabb, ccode, year, irst, milex, milper, pec, tpop, upop,
  cinc, version``; extra columns of the full release are ignored; ``-9`` marks a missing
  value), including the small extracts written by :func:`write_csv`, whose ``#`` header lines
  are skipped and may carry ``obtained_via:``;
* the R data mirror in the ``peacesciencer`` package (``cow_nmc.rda``), which omits
  ``stateabb`` and ``version``. The state abbreviation is filled from :data:`COW_ABB` where
  known, and the version is inferred from the last year covered (:data:`VERSION_BY_LAST_YEAR`)
  unless given.
"""

from __future__ import annotations

import csv
import math
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

__all__ = [
    "COLUMNS",
    "COW_ABB",
    "MIRROR_URL",
    "SOURCE",
    "VERSION_BY_LAST_YEAR",
    "extract",
    "load",
    "value",
    "write_csv",
]

COLUMNS = (
    "stateabb",
    "ccode",
    "year",
    "irst",
    "milex",
    "milper",
    "pec",
    "tpop",
    "upop",
    "cinc",
    "version",
)
PROVENANCE = ("source", "version", "obtained_via")

SOURCE = (
    "Correlates of War Project, National Material Capabilities data set "
    "(Singer, Bremer and Stuckey 1972; Singer 1988)"
)
OFFICIAL_PAGE = "https://correlatesofwar.org/data-sets/national-material-capabilities/"
MIRROR_URL = "https://raw.githubusercontent.com/svmiller/peacesciencer/master/data/cow_nmc.rda"
MIRROR_NOTE = f"peacesciencer R package mirror ({MIRROR_URL})"

# COW state abbreviations for the states the WW2 testbed reads (COW state system list).
COW_ABB = {
    2: "USA",
    200: "UKG",
    220: "FRN",
    255: "GMY",
    290: "POL",
    325: "ITA",
    365: "RUS",
    740: "JPN",
}

# Each NMC release ends in a known year; the mirror carries no version column.
VERSION_BY_LAST_YEAR = {2007: "4.0", 2012: "5.0", 2016: "6.0", 2022: "7.0"}

_INTEGER_COLUMNS = ("ccode", "year", "irst", "milex", "milper", "pec", "tpop", "upop")
_MISSING = ("", "-9", "NA", "NaN", "nan", ".")
_KEY = re.compile(r"[a-z_]+")


def _number(raw: Any, column: str) -> int | float | None:
    """A cleaned numeric value: ``None`` for COW's ``-9`` and empty or NaN cells, ``int`` for
    whole numbers in the integer columns."""
    if raw is None:
        return None
    if isinstance(raw, str):
        text = raw.strip()
        if text in _MISSING:
            return None
        raw = float(text)
    number = float(raw)
    if math.isnan(number) or number == -9:
        return None
    if column in _INTEGER_COLUMNS and number.is_integer():
        return int(number)
    return number


def read_comment_fields(path: Path) -> dict[str, str]:
    """``key: value`` pairs from the leading ``#`` lines of a CSV file."""
    fields: dict[str, str] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.startswith("#"):
                break
            body = line[1:].strip()
            key, sep, rest = body.partition(":")
            if sep and _KEY.fullmatch(key.strip()):
                fields.setdefault(key.strip(), rest.strip())
    return fields


def read_csv_records(path: Path) -> list[dict[str, str]]:
    """Records of a CSV file, skipping leading ``#`` comment lines; column names lowercased."""
    with path.open(encoding="utf-8", newline="") as handle:
        lines = [line for line in handle if not line.startswith("#")]
    reader = csv.DictReader(lines)
    return [{(k or "").strip().lower(): v for k, v in record.items()} for record in reader]


def read_rda_records(path: Path, name: str | None = None) -> list[dict[str, Any]]:
    """Records of the (single, or ``name``d) data frame in an R data file. Needs ``pyreadr``
    (the ``data`` extra); it is imported here and nowhere at module import time."""
    try:
        import pyreadr
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise ImportError(
            f"reading {path.name} needs pyreadr: pip install 'wave-front[data]'"
        ) from exc
    frames = pyreadr.read_r(str(path))
    if name is not None:
        frame = frames[name]
    elif len(frames) == 1:
        frame = next(iter(frames.values()))
    else:
        raise ValueError(f"{path}: holds several data frames ({', '.join(frames)}); name one")
    frame.columns = [str(c).lower() for c in frame.columns]
    return frame.to_dict("records")


def _infer_version(years: Iterable[int]) -> str:
    last = max(years, default=None)
    if last in VERSION_BY_LAST_YEAR:
        return VERSION_BY_LAST_YEAR[last]
    return f"unknown (coverage ends {last})"


def load(
    path: str | Path,
    *,
    version: str | None = None,
    obtained_via: str | None = None,
) -> list[dict[str, Any]]:
    """Read an NMC file (official CSV, an extract written by :func:`write_csv`, or the
    ``.rda`` mirror) into rows.

    Each row has the :data:`COLUMNS` (missing values as ``None``) plus ``source``,
    ``version`` and ``obtained_via``. ``version`` overrides the file's own; without it a CSV
    row keeps its ``version`` column and an ``.rda`` file's version is inferred from its
    coverage. ``obtained_via`` defaults to the CSV header's ``obtained_via:`` line, to the
    mirror for ``cow_nmc.rda``, and otherwise to the file name."""
    path = Path(path)
    if path.suffix.lower() in (".rda", ".rdata"):
        records = read_rda_records(path)
        default_via = MIRROR_NOTE if path.name == "cow_nmc.rda" else f"local file {path.name}"
    else:
        records = read_csv_records(path)
        default_via = read_comment_fields(path).get("obtained_via", f"local file {path.name}")
    if not records or "ccode" not in records[0] or "year" not in records[0]:
        raise ValueError(f"{path}: not an NMC table (needs at least ccode and year columns)")
    rows: list[dict[str, Any]] = []
    for record in records:
        row: dict[str, Any] = {}
        for column in COLUMNS:
            if column in ("stateabb", "version"):
                continue
            row[column] = _number(record.get(column), column)
        abb = record.get("stateabb")
        row["stateabb"] = str(abb).strip() if abb else COW_ABB.get(row["ccode"], "")
        file_version = record.get("version")
        row["version"] = str(file_version).strip() if file_version not in (None, "") else None
        rows.append(row)
    inferred = version or _infer_version(r["year"] for r in rows)
    via = obtained_via or default_via
    out = []
    for row in rows:
        if version is not None or row["version"] is None:
            row["version"] = inferred
        row["source"] = SOURCE
        row["obtained_via"] = via
        out.append({c: row[c] for c in COLUMNS} | {p: row[p] for p in PROVENANCE})
    return out


def extract(
    rows: Iterable[Mapping[str, Any]],
    years: Iterable[int],
    ccodes: Iterable[int],
) -> list[dict[str, Any]]:
    """The rows for the given years and COW country codes, ordered by country code then year
    (the order of the official file)."""
    years, ccodes = set(years), set(ccodes)
    chosen = [dict(r) for r in rows if r["year"] in years and r["ccode"] in ccodes]
    return sorted(chosen, key=lambda r: (r["ccode"], r["year"]))


def value(rows: Iterable[Mapping[str, Any]], ccode: int, year: int, column: str) -> Any:
    """The ``column`` value for one state and year; ``KeyError`` if there is no such row."""
    for row in rows:
        if row["ccode"] == ccode and row["year"] == year:
            return row[column]
    raise KeyError(f"no NMC row for ccode {ccode}, year {year}")


def _cell(v: Any) -> str:
    if v is None:
        return "-9"
    if isinstance(v, float):
        return repr(v)
    return str(v)


def write_csv(rows: Iterable[Mapping[str, Any]], path: str | Path, header_comment: str) -> None:
    """Write rows in the official column layout, preceded by ``header_comment`` as ``#``
    lines (name the source and version there). Missing values are written as ``-9`` as in the
    official file. When the rows share one ``obtained_via``, an ``obtained_via:`` header line
    records it so that :func:`load` restores the provenance."""
    rows = list(rows)
    path = Path(path)
    lines = [f"# {line}".rstrip() for line in header_comment.strip("\n").splitlines()]
    vias = {r.get("obtained_via") for r in rows} - {None}
    if len(vias) == 1:
        lines.append(f"# obtained_via: {vias.pop()}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        for line in lines:
            handle.write(line + "\n")
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(COLUMNS)
        for row in rows:
            writer.writerow([_cell(row.get(c)) for c in COLUMNS])
