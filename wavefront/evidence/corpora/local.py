"""A directory of dated plain-text files as a corpus (the fixture corpus of the tests).

Each file is UTF-8 text with a header block of ``key: value`` lines, a blank line and the
body::

    SYNTHETIC FIXTURE: written for pipeline tests, not a source
    id: syn-1939-03-17-birmingham
    date: 1939-03-17
    source: synthetic fixture corpus (not a source)
    title: The Prime Minister speaks at Birmingham
    url: synthetic:corpus_synthetic/1939-03-17_birmingham

    The body, in paragraphs separated by blank lines.

``date`` is required (an undated file is not admissible); ``id`` defaults to the file name
without its extension, ``title`` to the id, ``source`` to ``local`` and ``url`` to a
``file:`` path relative to the corpus. A file whose name starts with a date must carry that
date. A file with the header ``SYNTHETIC FIXTURE`` is synthetic; a directory mixes no
synthetic and real files, and the corpus reports :attr:`LocalCorpus.synthetic`.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import date
from pathlib import Path

from .base import Corpus, CorpusError, Document, clean_text, shown_path

__all__ = ["LocalCorpus", "SYNTHETIC_HEADER", "parse_local_file"]

SYNTHETIC_HEADER = "SYNTHETIC FIXTURE"
SYNTHETIC_LINE = f"{SYNTHETIC_HEADER}: written for pipeline tests, not a source"
_HEADER = re.compile(r"([A-Za-z][A-Za-z _-]*):\s*(.*)")
_NAME_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def parse_local_file(path: Path, root: Path) -> tuple[Document, bool]:
    """The document in ``path`` and whether it is a synthetic fixture."""
    text = path.read_text(encoding="utf-8")
    head, sep, body = text.partition("\n\n")
    if not sep:
        raise CorpusError(f"{path}: no blank line between the header and the body")
    fields: dict[str, str] = {}
    for line in head.splitlines():
        m = _HEADER.fullmatch(line.strip())
        if not m:
            raise CorpusError(f"{path}: header line {line!r} is not 'key: value'")
        key = m.group(1).strip()
        if key in fields:
            raise CorpusError(f"{path}: header {key!r} given twice")
        fields[key] = m.group(2).strip()
    synthetic = SYNTHETIC_HEADER in fields
    if "date" not in fields:
        raise CorpusError(f"{path}: no date header (an undated document is not admissible)")
    try:
        day = date.fromisoformat(fields["date"])
    except ValueError:
        raise CorpusError(f"{path}: date {fields['date']!r} is not YYYY-MM-DD") from None
    named = _NAME_DATE.match(path.name)
    if named and named.group(1) != day.isoformat():
        raise CorpusError(f"{path}: the file name says {named.group(1)}, the header {day}")
    doc_id = fields.get("id") or path.stem
    rel = path.relative_to(root).as_posix()
    body = clean_text(body)
    if not body:
        raise CorpusError(f"{path}: empty body")
    doc = Document(
        id=doc_id,
        date=day,
        source=fields.get("source") or "local",
        title=fields.get("title") or doc_id,
        text=body,
        url=fields.get("url") or f"file:{rel}",
    )
    return doc, synthetic


class LocalCorpus(Corpus):
    """Every ``*.txt`` file under ``root`` (recursively), read with :func:`parse_local_file`."""

    source = "local"

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        if not self.root.is_dir():
            raise CorpusError(f"{self.root}: not a directory")
        self._docs: list[Document] | None = None
        self._synthetic = False

    def _load(self) -> list[Document]:
        if self._docs is None:
            docs, flags, problems = [], set(), []
            for path in sorted(self.root.rglob("*.txt")):
                try:
                    doc, synthetic = parse_local_file(path, self.root)
                except CorpusError as exc:
                    problems.extend(exc.problems)
                    continue
                docs.append(doc)
                flags.add(synthetic)
            ids = [d.id for d in docs]
            problems += [
                f"duplicate document id {i!r}" for i in sorted(set(ids)) if ids.count(i) > 1
            ]
            if len(flags) > 1:
                problems.append(
                    f"{self.root}: mixes synthetic fixtures and other files; keep them apart"
                )
            if not docs and not problems:
                problems.append(f"{self.root}: no .txt documents")
            if problems:
                raise CorpusError("; ".join(problems), problems)
            self._docs = sorted(docs, key=lambda d: (d.date, d.id))
            self._synthetic = flags == {True}
        return self._docs

    @property
    def synthetic(self) -> bool:  # type: ignore[override]
        self._load()
        return self._synthetic

    def iter_documents(self, until: date, since: date | None = None) -> Iterator[Document]:
        for doc in self._load():
            if doc.date <= until and (since is None or doc.date >= since):
                yield doc

    def check(self) -> list[str]:
        try:
            self._load()
        except CorpusError as exc:
            return exc.problems
        return []

    def describe(self) -> dict[str, object]:
        return {"source": self.source, "synthetic": self.synthetic, "root": shown_path(self.root)}
