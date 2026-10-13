"""The backend protocol of the extractor, and the paragraph splitting every backend uses so
that no document is ever truncated silently."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ..corpora.base import Document
from .schema import Proposal, VariableSpec

__all__ = ["Backend", "ExtractError", "split_paragraphs", "split_sentences", "merge_proposals"]


class ExtractError(RuntimeError):
    """A backend failed on a document. ``retryable`` says whether trying again later may
    succeed (rate limits, server errors, network failures)."""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


@runtime_checkable
class Backend(Protocol):
    """Proposes levels for ``variables`` from one document.

    A backend reads only the document it is given: no other document, no later knowledge it
    can avoid. Its proposals are checked by the extractor (:func:`~.schema.check_proposal`)
    and are only proposals until a reviewer accepts them."""

    name: str

    def propose(self, document: Document, variables: Sequence[VariableSpec]) -> list[Proposal]: ...


_SENTENCE_END = re.compile(r"(?<=[.!?])[\"')”’]?\s+(?=[\"'(“‘]?[A-Z0-9])")


def split_sentences(paragraph: str) -> list[str]:
    """Sentences of a paragraph (a period, question or exclamation mark followed by space and
    a capital). Abbreviations such as ``Mr.`` split wrongly but harmlessly: no text is lost."""
    text = " ".join(paragraph.split())
    if not text:
        return []
    parts = _SENTENCE_END.split(text)
    out: list[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Re-join a split after a title abbreviation (Mr. Churchill, M. Molotov, Dr. Schuschnigg).
        if out and re.search(r"\b(Mr|Mrs|Dr|M|St|Gen|Col|Lt|Sir|No)\.$", out[-1]):
            out[-1] = f"{out[-1]} {part}"
        else:
            out.append(part)
    return out


def split_paragraphs(text: str, max_chars: int) -> list[str]:
    """Split ``text`` into chunks of at most ``max_chars`` characters at paragraph breaks,
    falling back to sentence breaks inside an over-long paragraph and to hard cuts inside an
    over-long sentence. Every word of every paragraph is in exactly one chunk, in order (runs
    of whitespace inside a split paragraph become single spaces):
    nothing is dropped."""
    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    pieces: list[str] = []
    for p in paragraphs:
        if len(p) <= max_chars:
            pieces.append(p)
            continue
        for s in split_sentences(p):
            while len(s) > max_chars:
                pieces.append(s[:max_chars])
                s = s[max_chars:]
            if s:
                pieces.append(s)
    chunks: list[str] = []
    current = ""
    for piece in pieces:
        candidate = f"{current}\n\n{piece}" if current else piece
        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(current)
            current = piece
    if current:
        chunks.append(current)
    return chunks


def merge_proposals(proposals: Sequence[Proposal], text: str | None = None) -> list[Proposal]:
    """Proposals from the parts of one document, without duplicates: one per (variable,
    level, date), keeping the first (its quote is the earliest passage) and noting in its
    rule how many parts agreed. A document that supports two levels of one variable keeps
    both; the reviewer decides. With the document's ``text``, a proposal whose quote is not in
    it is never merged into another or used as the kept one: it is passed on unchanged, so
    the extractor's checks discard it visibly instead of it hiding a sound proposal."""
    from .schema import quote_in_text

    seen: dict[tuple[str, str, str], int] = {}
    out: list[Proposal] = []
    counts: list[int] = []
    for p in proposals:
        if text is not None and not quote_in_text(p.quote, text):
            out.append(p)
            counts.append(1)
            continue
        key = (p.variable, repr(p.level), p.date)
        if key in seen:
            counts[seen[key]] += 1
            continue
        seen[key] = len(out)
        out.append(p)
        counts.append(1)
    merged = []
    for p, n in zip(out, counts, strict=True):
        if n > 1:
            p = Proposal(
                **{**p.to_json(), "rule": f"{p.rule} (also read in {n - 1} other part(s))"}
            )
        merged.append(p)
    return merged
