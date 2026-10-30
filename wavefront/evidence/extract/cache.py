"""A per-document cache of a backend's answers, so that an interrupted run of a paid backend
resumes without asking again for the documents it has already read.

The cache stores, per document, the proposals the backend returned (before the extractor's
checks, which run again on every read). An entry is keyed by the document (id, date and a
hash of its text) and by the backend's identity for the request (``cache_identity``: for
the Claude backend the model, effort, token and part limits, the fallback setting, a hash of
the system prompt with the variables' threshold rules and a hash of the answer's schema; for
the DeepSeek backend the base URL, model, token and part limits, JSON mode, effort and a hash
of the system prompt with its guidance and schema), so changing the model, the prompt or the
ontology's rule text reads the document again. Only successful answers are stored; an error
is never cached. Entries are written atomically, one file per document, so a run stopped
mid-way leaves only whole entries. The replay keeps one cache per backend, under
``OUT/cache/<backend>/``.

**The document's header.** Both LLM backends also send the document's ``source``, ``title``
and ``url`` with the text. They are not part of the key, so that the caches of the recorded
runs stay valid, and they are not fixed by the document's id and text: in the ``crest``
corpus the title comes from the contents table of the volume (``crest.STEURY_1996``, code that
can be edited) and the URL and source from the manifest and the raw file, so the same id and
text can come with another header. Each entry therefore records the header it was answered
with (``header``), and an entry whose header differs from the document's is not used: the
document is read again and the entry replaced. An entry written before headers were recorded
(no ``header``) is used as before.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ..corpora.base import Document
from .backend import Backend
from .schema import Proposal, VariableSpec

__all__ = ["CachedBackend", "cache_key", "header"]

_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _identity(backend: Backend, variables: Sequence[VariableSpec]) -> dict[str, Any]:
    ident = getattr(backend, "cache_identity", None)
    if callable(ident):
        return {"backend": backend.name, **ident(variables)}
    rules = [(v.name, v.level_names(), v.rule_text) for v in variables]
    return {"backend": backend.name, "variables": rules}


def header(document: Document) -> dict[str, str]:
    """The header fields the LLM backends send with the text (checked, not keyed)."""
    return {"source": document.source, "title": document.title, "url": document.url}


def cache_key(backend: Backend, document: Document, variables: Sequence[VariableSpec]) -> str:
    """The SHA-256 of the backend's identity and the document (id, date, text); the header
    (:func:`header`) is checked against the entry, not keyed (module docstring)."""
    payload = {
        "identity": _identity(backend, variables),
        "document": document.id,
        "date": document.date.isoformat(),
        "text": hashlib.sha256(document.text.encode("utf-8")).hexdigest(),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


class CachedBackend:
    """``backend`` with its answers cached under ``directory`` (see the module docstring).
    ``hits`` and ``misses`` count the documents answered from the cache and by the backend."""

    def __init__(self, backend: Backend, directory: str | Path) -> None:
        self.backend = backend
        self.name = backend.name
        self.directory = Path(directory)
        self.hits = 0
        self.misses = 0
        self._lock = threading.Lock()

    def __getattr__(self, attr: str) -> Any:  # model, usage, requests of the wrapped backend
        return getattr(self.backend, attr)

    def path(self, document: Document, variables: Sequence[VariableSpec]) -> Path:
        key = cache_key(self.backend, document, variables)
        return self.directory / f"{_SAFE.sub('_', document.id)}.{key[:20]}.json"

    def _entry(self, document: Document, variables: Sequence[VariableSpec]) -> Any:
        """The usable cached entry of ``document``, or None (none, or another header)."""
        path = self.path(document, variables)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("header", header(document)) != header(document):
            return None
        return data

    def cached(self, document: Document, variables: Sequence[VariableSpec]) -> bool:
        return self._entry(document, variables) is not None

    def propose(self, document: Document, variables: Sequence[VariableSpec]) -> list[Proposal]:
        path = self.path(document, variables)
        data = self._entry(document, variables)
        if data is not None:
            with self._lock:
                self.hits += 1
            return [Proposal.from_json(p) for p in data["proposals"]]
        proposals = self.backend.propose(document, variables)
        self.directory.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f"{path.name}.{threading.get_ident()}.part")
        tmp.write_text(
            json.dumps(
                {
                    "document": document.id,
                    "header": header(document),
                    "proposals": [p.to_json() for p in proposals],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        tmp.replace(path)
        with self._lock:
            self.misses += 1
        return proposals
