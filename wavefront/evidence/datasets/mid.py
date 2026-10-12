"""Correlates of War, Militarized Interstate Disputes (MID), dispute level.

A minimal loader: one row per dispute with every column of the file (lowercased, numbers
cleaned, ``-9`` as ``None``) plus provenance. Accepts the official dispute-level CSV (``MIDA``)
or the abbreviated mirror in the ``peacesciencer`` R package (``cow_mid_disps.rda``: dispute
number, start year and month, outcome, settlement, fatality, duration, highest action,
hostility level, reciprocation; no participants).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .nmc import read_comment_fields, read_csv_records, read_rda_records

__all__ = ["MIRROR_URL", "SOURCE", "in_years", "load"]

SOURCE = (
    "Correlates of War Project, Militarized Interstate Disputes data set "
    "(Palmer et al. 2022, 'The MID5 Dataset, 2011-2014', Conflict Management and Peace "
    "Science 39(4))"
)
OFFICIAL_PAGE = "https://correlatesofwar.org/data-sets/mids/"
MIRROR_URL = (
    "https://raw.githubusercontent.com/svmiller/peacesciencer/master/data/cow_mid_disps.rda"
)
MIRROR_NOTE = f"peacesciencer R package mirror ({MIRROR_URL}), abbreviated dispute-level table"
MIRROR_VERSION = "5.0"

_TEXT_COLUMNS = ("version", "stabb", "namea", "nameb")


def _clean(column: str, raw: Any) -> Any:
    if raw is None:
        return None
    if column in _TEXT_COLUMNS:
        text = str(raw).strip()
        return text or None
    if isinstance(raw, str):
        text = raw.strip()
        if text in ("", "-9", "NA", "."):
            return None
        try:
            raw = float(text)
        except ValueError:
            return text
    number = float(raw)
    if number != number or number == -9:  # NaN or COW's missing code
        return None
    return int(number) if number.is_integer() else number


def load(
    path: str | Path,
    *,
    version: str | None = None,
    obtained_via: str | None = None,
) -> list[dict[str, Any]]:
    """Read a dispute-level MID file into rows with ``source``, ``version`` and
    ``obtained_via`` attached. The mirror ``cow_mid_disps.rda`` is version 5.0 as documented
    by the package; otherwise the file's ``version`` column is used, or ``version``."""
    path = Path(path)
    if path.suffix.lower() in (".rda", ".rdata"):
        records = read_rda_records(path)
        mirror = path.name == "cow_mid_disps.rda"
        default_via = MIRROR_NOTE if mirror else f"local file {path.name}"
        default_version = MIRROR_VERSION if mirror else None
    else:
        records = read_csv_records(path)
        default_via = read_comment_fields(path).get("obtained_via", f"local file {path.name}")
        default_version = None
    if not records or "dispnum" not in records[0]:
        raise ValueError(f"{path}: not a dispute-level MID table (needs a dispnum column)")
    rows = []
    for record in records:
        row = {column: _clean(column, raw) for column, raw in record.items()}
        row["version"] = version or row.get("version") or default_version or "unknown"
        row["source"] = SOURCE
        row["obtained_via"] = obtained_via or default_via
        rows.append(row)
    return rows


def in_years(rows: Iterable[Mapping[str, Any]], first: int, last: int) -> list[dict[str, Any]]:
    """Disputes that start in ``first`` to ``last`` inclusive, by dispute number."""
    chosen = [dict(r) for r in rows if r.get("styear") is not None and first <= r["styear"] <= last]
    return sorted(chosen, key=lambda r: r["dispnum"])
