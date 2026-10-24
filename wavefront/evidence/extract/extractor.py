"""The extractor: runs a backend over the documents of a corpus up to a date and writes the
proposals file the reviewer works on.

A proposals file (JSON) holds::

    {
      "kind": "wave_front proposals",
      "format": 1,
      "label": "1939Q1",                # the quarter, or the cut-off date
      "until": "1939-03-31", "since": null,
      "corpus": {"source": "local", "synthetic": true, "root": "..."},
      "backend": {"name": "rules"},
      "harness_rules": ["two-document", "no-retrospective"],   # see evidence/harness_rules.py
      "documents": [{"id", "date", "source", "title", "url"[, "work"]}, ...],
      "proposals": [
        {"id": "1939Q1-001", "document": "<document id>",
         ["work": "<the work the document is a copy or part of, when it has one>",]
         "proposal": {<the fixed schema>},
         "status": "pending" | "accepted" | "rejected",
         "decisions": [{"status", "reviewer", "note", "date", "auto"}]}
      ],
      "discarded": [{"document", "proposal", "reasons"}],
      "errors": [{"document", "error", "retryable"}]
    }

Only documents dated at or before ``until`` (and on or after ``since``) are read: the corpus
filters by document date before the backend sees anything. Every proposal of every backend is
checked (:func:`~.schema.check_proposal`); a proposal that fails is kept under ``discarded``
with its reasons, never silently dropped. ``harness_rules`` records the replay and review
layer's rules for the file (absent: the default, both on); the extractor does not apply them.

With ``workers`` above 1 the backend reads several documents at once (threads); the results
are recorded in document order, so the file is the same as with one worker.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from ..corpora.base import Corpus, Document
from .backend import Backend, ExtractError
from .schema import Proposal, VariableSpec, check_proposal, text_variables

__all__ = [
    "PROPOSALS_KIND",
    "Extraction",
    "ProposalsFileError",
    "extract",
    "write_proposals",
    "read_proposals",
    "save_proposals",
]

PROPOSALS_KIND = "wave_front proposals"
FORMAT = 1


class ProposalsFileError(ValueError):
    """A proposals file that cannot be read or does not have the expected shape."""


@dataclass
class Extraction:
    until: date
    since: date | None
    documents: list[Document] = field(default_factory=list)
    kept: list[tuple[Document, Proposal]] = field(default_factory=list)
    discarded: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)


def extract(
    corpus: Corpus,
    *,
    until: date,
    backend: Backend,
    since: date | None = None,
    variables: Sequence[VariableSpec] | None = None,
    skip_ids: Iterable[str] = (),
    stop_on_error: bool = False,
    workers: int = 1,
) -> Extraction:
    """Run ``backend`` on every document of ``corpus`` dated in ``[since, until]`` except
    those in ``skip_ids`` (already read in an earlier step of a replay), check its proposals,
    and return what was kept, discarded and failed. With ``stop_on_error`` the first backend
    error is raised instead of recorded. ``workers`` documents are read at a time; the
    results are recorded in document order."""
    variables = list(variables) if variables is not None else text_variables()
    by_name = {v.name: v for v in variables}
    skip = set(skip_ids)
    result = Extraction(until=until, since=since)
    for doc in corpus.iter_documents(until=until, since=since):
        if doc.date > until or (since is not None and doc.date < since):  # defence in depth
            raise ExtractError(f"{doc.id}: corpus returned a document outside the date range")
        if doc.id in skip:
            continue
        result.documents.append(doc)

    def read(doc: Document) -> list[Proposal] | ExtractError:
        try:
            return backend.propose(doc, variables)
        except ExtractError as exc:
            if stop_on_error:
                raise
            return exc

    if workers > 1 and len(result.documents) > 1:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            outcomes = list(pool.map(read, result.documents))
    else:
        outcomes = [read(doc) for doc in result.documents]
    for doc, outcome in zip(result.documents, outcomes, strict=True):
        if isinstance(outcome, ExtractError):
            result.errors.append(
                {"document": doc.id, "error": str(outcome), "retryable": outcome.retryable}
            )
            continue
        for p in outcome:
            reasons = check_proposal(p, by_name, doc.date, doc.text)
            if reasons:
                result.discarded.append(
                    {"document": doc.id, "proposal": p.to_json(), "reasons": reasons}
                )
            else:
                result.kept.append((doc, p))
    return result


def write_proposals(
    path: str | Path,
    extraction: Extraction,
    *,
    label: str,
    corpus: dict[str, Any],
    backend: dict[str, Any],
    harness_rules: Sequence[str] | None = None,
    episode: str | None = None,
) -> dict[str, Any]:
    """Write ``extraction`` as a proposals file with every proposal pending, recording the
    harness rules the replay and review layer applies to it (``None``: not recorded, which
    reads as the default) and, unless ``None``, the episode (:mod:`..episodes`; a file
    without one is WW2's)."""
    seen: set[str] = set()
    records = []
    for n, (doc, p) in enumerate(extraction.kept, start=1):
        indicator = p.indicator_id
        k = 2
        while indicator in seen:  # two proposals of one rule in one document
            indicator = f"{p.indicator_id}#{k}"
            k += 1
        seen.add(indicator)
        payload = p.to_json() | {"indicator_id": indicator}
        records.append(
            {
                "id": f"{label}-{n:03d}",
                "document": doc.id,
                **({"work": doc.work} if doc.work else {}),
                "proposal": payload,
                "status": "pending",
                "decisions": [],
            }
        )
    data = {
        "kind": PROPOSALS_KIND,
        "format": FORMAT,
        "label": label,
        "until": extraction.until.isoformat(),
        "since": extraction.since.isoformat() if extraction.since else None,
        "corpus": corpus,
        "backend": backend,
        **({} if harness_rules is None else {"harness_rules": list(harness_rules)}),
        **({} if episode is None else {"episode": episode}),
        "documents": [d.header() for d in extraction.documents],
        "proposals": records,
        "discarded": extraction.discarded,
        "errors": extraction.errors,
    }
    save_proposals(path, data)
    return data


def save_proposals(path: str | Path, data: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def read_proposals(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ProposalsFileError(f"{path}: no such proposals file") from None
    except json.JSONDecodeError as exc:
        raise ProposalsFileError(f"{path}: not valid JSON: {exc}") from None
    if not isinstance(data, dict) or data.get("kind") != PROPOSALS_KIND:
        raise ProposalsFileError(f"{path}: not a proposals file")
    for key in ("label", "until", "proposals", "corpus"):
        if key not in data:
            raise ProposalsFileError(f"{path}: missing {key!r}")
    for rec in data["proposals"]:
        try:
            Proposal.from_json(rec["proposal"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ProposalsFileError(f"{path}: proposal {rec.get('id')!r}: {exc}") from None
    return data
