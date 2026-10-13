"""Corpus indices for the replay harness: one :class:`Document` record for every source and
strict filtering by document date (ww2_testbed.md sections 6.2 and 8)."""

from __future__ import annotations

import json
from pathlib import Path

from .base import (
    RAW_ROOT,
    Corpus,
    CorpusError,
    Document,
    IndexedCorpus,
    IndexEntry,
    default_fetcher,
)
from .chronicling import ChroniclingCorpus
from .frus import FrusCorpus
from .hansard import HansardCorpus
from .local import SYNTHETIC_HEADER, LocalCorpus
from .trove import TroveCorpus

__all__ = [
    "RAW_ROOT",
    "SOURCES",
    "SYNTHETIC_HEADER",
    "ChroniclingCorpus",
    "Corpus",
    "CorpusError",
    "Document",
    "FrusCorpus",
    "HansardCorpus",
    "IndexEntry",
    "IndexedCorpus",
    "LocalCorpus",
    "TroveCorpus",
    "default_fetcher",
    "open_corpus",
]

SOURCES: dict[str, type[IndexedCorpus]] = {
    "frus": FrusCorpus,
    "hansard": HansardCorpus,
    "chronicling": ChroniclingCorpus,
    "trove": TroveCorpus,
}


def open_corpus(path: str | Path, source: str | None = None) -> Corpus:
    """The corpus in directory ``path``: an indexed source corpus when the directory holds an
    ``index.json`` (its ``source`` field, or ``source``, names the kind), otherwise a
    :class:`LocalCorpus` of dated text files (``source`` may also say ``local``)."""
    path = Path(path)
    if not path.is_dir():
        raise CorpusError(f"{path}: not a directory")
    if source in (None, "local") and not (path / "index.json").exists():
        return LocalCorpus(path)
    if source is None:
        try:
            source = json.loads((path / "index.json").read_text(encoding="utf-8"))["source"]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise CorpusError(f"{path}/index.json: cannot read the source name: {exc}") from None
    if source == "local":
        return LocalCorpus(path)
    if source not in SOURCES:
        raise CorpusError(f"unknown corpus source {source!r} (known: local, {', '.join(SOURCES)})")
    return SOURCES[source](path)
