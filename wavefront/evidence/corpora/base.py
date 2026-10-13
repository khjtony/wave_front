"""Corpus indices for the replay harness (ww2_testbed.md sections 6.2 and 8).

Every corpus yields the same :class:`Document` record and filters strictly by the document's
own date: :meth:`Corpus.iter_documents` returns only documents dated at or before ``until``
(and on or after ``since`` when given), so that a blind replay of quarter T never shows the
extractor a document written after T. A document without a date is not admissible and never
enters an index.

Two kinds of corpus exist:

* :class:`IndexedCorpus`, for the published sources (FRUS, Hansard, Chronicling America,
  Trove). A fetch step, run on the owner's machine, writes the raw pages it downloads into
  ``data/ww2/corpora/raw/<source>/`` (git-ignored), records each file in ``MANIFEST.json``
  (URL, fetch date, size, SHA-256) and lists the documents found in ``index.json`` (id, date,
  title, URL, the raw file and a locator inside it). Reading a document parses its raw file
  again, so the index never holds text that is not in a recorded file; :meth:`check` validates
  an index against the manifest and the files without the network.
* :class:`~wavefront.evidence.corpora.local.LocalCorpus`, a directory of dated plain-text
  files (the synthetic fixture corpus of the tests).
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import time
import urllib.request
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

__all__ = [
    "ROOT",
    "RAW_ROOT",
    "CorpusError",
    "Document",
    "Corpus",
    "IndexEntry",
    "IndexedCorpus",
    "Fetcher",
    "default_fetcher",
    "sha256_bytes",
    "clean_text",
    "parse_iso_date",
    "matches_terms",
    "shown_path",
]

ROOT = Path(__file__).resolve().parents[3]
RAW_ROOT = ROOT / "data" / "ww2" / "corpora" / "raw"
INDEX_NAME = "index.json"
MANIFEST_NAME = "MANIFEST.json"
INDEX_FORMAT = 1

# A fetcher takes a URL (and optional extra headers) and returns the response body.
Fetcher = Callable[..., bytes]


class CorpusError(ValueError):
    """A corpus that cannot be read: a bad index, a missing or altered raw file, an undated
    document, or a parse error. ``problems`` lists every problem found."""

    def __init__(self, message: str, problems: list[str] | None = None) -> None:
        super().__init__(message)
        self.problems = list(problems) if problems is not None else [message]


@dataclass(frozen=True)
class Document:
    """One dated document of a corpus.

    ``date`` is the document's own date (a dispatch, a sitting day, an issue date), never the
    date of its publication in a later collection. ``source`` names the corpus and, where it
    has one, the series; ``url`` is where a reader finds the document."""

    id: str
    date: date
    source: str
    title: str
    text: str
    url: str

    def header(self) -> dict[str, str]:
        """The document without its text, as a JSON-ready mapping."""
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "source": self.source,
            "title": self.title,
            "url": self.url,
        }


def parse_iso_date(text: str) -> date:
    """``YYYY-MM-DD`` (a longer ISO timestamp is cut to its date part)."""
    return date.fromisoformat(text.strip()[:10])


_SPACE = re.compile(r"[ \t\r\f\v]+")
_BLANKS = re.compile(r"\n\s*\n+")


def clean_text(text: str) -> str:
    """Collapse runs of spaces inside lines and runs of blank lines; keep paragraph breaks."""
    lines = [_SPACE.sub(" ", line).strip() for line in text.replace("\r\n", "\n").split("\n")]
    joined = "\n".join(lines)
    return _BLANKS.sub("\n\n", joined).strip()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def default_fetcher(delay: float = 1.0, timeout: float = 120.0) -> Fetcher:
    """A polite HTTP fetcher (``urllib``; proxies and CA bundles come from the environment):
    it waits ``delay`` seconds before each request."""

    def fetch(url: str, headers: dict[str, str] | None = None) -> bytes:
        if delay:
            time.sleep(delay)
        request = urllib.request.Request(
            url, headers={"User-Agent": "wave_front corpus fetch", **(headers or {})}
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()

    return fetch


class Corpus:
    """The interface every corpus offers."""

    source: str = ""
    #: True for a corpus written for tests (the synthetic fixtures); only such a corpus may be
    #: replayed with ``--auto-accept``.
    synthetic: bool = False

    def iter_documents(self, until: date, since: date | None = None) -> Iterator[Document]:
        """The admissible documents dated on or after ``since`` and at or before ``until``,
        in date order (ties by id)."""
        raise NotImplementedError

    def check(self) -> list[str]:
        """Problems with the corpus, found without the network; empty when it is sound."""
        raise NotImplementedError

    def describe(self) -> dict[str, Any]:
        return {"source": self.source, "synthetic": self.synthetic}


def _in_range(day: date, until: date, since: date | None) -> bool:
    return day <= until and (since is None or day >= since)


@dataclass(frozen=True)
class IndexEntry:
    """One document of an index: where its raw file is and how to find it there."""

    id: str
    date: date
    title: str
    url: str
    path: str
    locator: str

    def to_json(self) -> dict[str, str]:
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "title": self.title,
            "url": self.url,
            "path": self.path,
            "locator": self.locator,
        }


class IndexedCorpus(Corpus):
    """A corpus of raw pages fetched from a published source, with an index and a manifest.

    Subclasses set :attr:`source` and implement :meth:`documents_in_raw`, which parses one raw
    file into the documents it contains (each with its locator). The fetch functions of the
    source modules use :meth:`store_raw` and :meth:`write_index`."""

    #: the series name shown in :attr:`Document.source`
    label: str = ""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root) if root is not None else RAW_ROOT / self.source
        self._parsed: dict[str, dict[str, Document]] = {}

    # -- parsing (source-specific) --------------------------------------------------------

    def documents_in_raw(self, data: bytes, path: str) -> dict[str, Document]:
        """The admissible documents in one raw file, by locator."""
        raise NotImplementedError

    # -- the index ------------------------------------------------------------------------

    @property
    def index_path(self) -> Path:
        return self.root / INDEX_NAME

    @property
    def manifest_path(self) -> Path:
        return self.root / MANIFEST_NAME

    def read_index(self) -> list[IndexEntry]:
        try:
            data = json.loads(self.index_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise CorpusError(f"{self.index_path}: no index (run the fetch step)") from None
        except json.JSONDecodeError as exc:
            raise CorpusError(f"{self.index_path}: not valid JSON: {exc}") from None
        if not isinstance(data, dict) or data.get("source") != self.source:
            raise CorpusError(f"{self.index_path}: not an index of source {self.source!r}")
        entries = []
        problems = []
        for k, raw in enumerate(data.get("documents", [])):
            try:
                entries.append(
                    IndexEntry(
                        id=str(raw["id"]),
                        date=parse_iso_date(raw["date"]),
                        title=str(raw["title"]),
                        url=str(raw["url"]),
                        path=str(raw["path"]),
                        locator=str(raw["locator"]),
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                problems.append(f"{self.index_path}: documents[{k}]: {exc!r}")
        if problems:
            raise CorpusError("; ".join(problems), problems)
        return sorted(entries, key=lambda e: (e.date, e.id))

    def read_manifest(self) -> dict[str, dict[str, Any]]:
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        return dict(data.get("files", {}))

    def write_index(self, entries: Iterable[IndexEntry], skipped: Iterable[str] = ()) -> Path:
        """Write ``index.json`` (entries sorted by date and id; duplicate ids rejected)."""
        entries = sorted(entries, key=lambda e: (e.date, e.id))
        seen: set[str] = set()
        for e in entries:
            if e.id in seen:
                raise CorpusError(f"duplicate document id {e.id!r} in the index")
            seen.add(e.id)
        self.root.mkdir(parents=True, exist_ok=True)
        payload = {
            "source": self.source,
            "format": INDEX_FORMAT,
            "documents": [e.to_json() for e in entries],
            "skipped": sorted(set(skipped)),
        }
        self.index_path.write_text(
            json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return self.index_path

    def store_raw(self, name: str, data: bytes, url: str, fetched: date | None = None) -> str:
        """Write a downloaded page to the raw directory (via a temporary name) and record its
        URL, fetch date, size and SHA-256 in the manifest. Returns the relative path."""
        if "/" in name or "\\" in name or name.startswith("."):
            raise CorpusError(f"raw file name {name!r} must be a plain file name")
        self.root.mkdir(parents=True, exist_ok=True)
        target = self.root / name
        partial = target.with_name(name + ".part")
        partial.write_bytes(data)
        shutil.move(partial, target)
        manifest = self.read_manifest()
        manifest[name] = {
            "url": url,
            "fetched": (fetched or date.today()).isoformat(),
            "bytes": len(data),
            "sha256": sha256_bytes(data),
        }
        self.manifest_path.write_text(
            json.dumps({"source": self.source, "files": manifest}, indent=1, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return name

    # -- reading --------------------------------------------------------------------------

    def _documents_of(self, path: str) -> dict[str, Document]:
        if path not in self._parsed:
            data = (self.root / path).read_bytes()
            self._parsed[path] = self.documents_in_raw(data, path)
        return self._parsed[path]

    def load(self, entry: IndexEntry) -> Document:
        """Parse an index entry's document from its raw file; its date must be the index's."""
        try:
            doc = self._documents_of(entry.path)[entry.locator]
        except FileNotFoundError:
            raise CorpusError(f"{self.root / entry.path}: raw file missing") from None
        except KeyError:
            raise CorpusError(
                f"{entry.id}: locator {entry.locator!r} not found in {entry.path}"
            ) from None
        if doc.date != entry.date:
            raise CorpusError(
                f"{entry.id}: the raw file dates it {doc.date}, the index {entry.date}"
            )
        return doc

    def iter_documents(self, until: date, since: date | None = None) -> Iterator[Document]:
        # Filter on the index date first, so an excluded document is never even parsed.
        for entry in self.read_index():
            if _in_range(entry.date, until, since):
                yield self.load(entry)

    def check(self) -> list[str]:
        """Validate the index without the network: entries well formed and unique, every raw
        file present with the size and checksum the manifest records, every entry parsed from
        its file with the date the index gives."""
        try:
            entries = self.read_index()
        except CorpusError as exc:
            return exc.problems
        problems: list[str] = []
        manifest = self.read_manifest()
        ids = [e.id for e in entries]
        for dup in sorted({i for i in ids if ids.count(i) > 1}):
            problems.append(f"duplicate document id {dup!r}")
        for path in sorted({e.path for e in entries}):
            file = self.root / path
            record = manifest.get(path)
            if record is None:
                problems.append(f"{path}: not in {MANIFEST_NAME}")
            if not file.exists():
                problems.append(f"{path}: raw file missing")
                continue
            data = file.read_bytes()
            if record is not None:
                if record.get("bytes") != len(data):
                    problems.append(f"{path}: {len(data)} bytes, manifest says {record['bytes']}")
                if record.get("sha256") != sha256_bytes(data):
                    problems.append(f"{path}: checksum differs from the manifest")
        for entry in entries:
            if not (self.root / entry.path).exists():
                continue
            try:
                self.load(entry)
            except CorpusError as exc:
                problems.extend(exc.problems)
            except Exception as exc:  # a parse error in a raw file
                problems.append(f"{entry.id}: cannot parse {entry.path}: {exc!r}")
        return problems

    def describe(self) -> dict[str, Any]:
        return {"source": self.source, "synthetic": False, "root": shown_path(self.root)}


def shown_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def matches_terms(text: str, terms: Iterable[str]) -> bool:
    """True if ``terms`` is empty or the text contains any of them (case-insensitive)."""
    terms = [t.lower() for t in terms if t]
    if not terms:
        return True
    low = text.lower()
    return any(t in low for t in terms)
