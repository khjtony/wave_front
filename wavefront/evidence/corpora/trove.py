"""Trove (National Library of Australia): digitized Australian newspapers, the Empire press.

Format. The Trove API version 3 answers
``https://api.trove.nla.gov.au/v3/result?category=newspaper&q=...&encoding=json&reclevel=full&include=articletext&n=100&s=<cursor>``
(an API key in the ``X-API-KEY`` header) with an object whose ``category`` list holds, for
``code == "newspaper"``, a ``records`` object with ``total``, ``nextStart`` and ``article``:
one record per article with ``id``, ``heading``, ``date`` (``YYYY-MM-DD``), ``title``
(``{"id", "title"}``, the newspaper), ``page``, ``troveUrl`` and, with
``include=articletext``, ``articleText`` (HTML). Version 2 responses (``response.zone[]``
with ``records.article``) are read the same way. The date range goes into the query as
``date:[YYYY-MM-DDT00:00:00Z TO YYYY-MM-DDT00:00:00Z]``.

The key is read from the environment by the fetch script and never written to the manifest
or the index. An article without ``articleText`` is skipped, never indexed with partial text.
"""

from __future__ import annotations

import json
import re
import urllib.parse
from collections.abc import Iterable, Iterator
from datetime import date
from html import unescape
from typing import Any

from .base import (
    CorpusError,
    Document,
    Fetcher,
    IndexedCorpus,
    IndexEntry,
    clean_text,
    matches_terms,
    parse_iso_date,
    sha256_bytes,
)

__all__ = ["TroveCorpus", "parse_results", "search_url", "fetch", "API"]

API = "https://api.trove.nla.gov.au/v3/result"
_TAG = re.compile(r"<[^>]+>")
_BLOCK_END = re.compile(r"</(p|div|br|h\d)\s*>|<br\s*/?>", re.I)


def search_url(
    terms: Iterable[str], since: date, until: date, start: str = "*", n: int = 100
) -> str:
    query = " OR ".join(f'"{t}"' if " " in t else t for t in terms)
    span = f"date:[{since.isoformat()}T00:00:00Z TO {until.isoformat()}T00:00:00Z]"
    params = {
        "category": "newspaper",
        "q": f"({query}) {span}",
        "encoding": "json",
        "reclevel": "full",
        "include": "articletext",
        "n": str(n),
        "s": start,
    }
    return API + "?" + urllib.parse.urlencode(params)


def _html_text(html: str) -> str:
    return clean_text(unescape(_TAG.sub("", _BLOCK_END.sub("\n\n", html))))


def _records(payload: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for cat in payload.get("category", []):  # v3
        if cat.get("code") == "newspaper":
            yield cat.get("records") or {}
    for zone in (payload.get("response") or {}).get("zone", []):  # v2
        if zone.get("name") == "newspaper":
            yield zone.get("records") or {}


def parse_results(data: bytes) -> tuple[dict[str, Document], list[str], str | None]:
    """The articles of one response by Trove id, the skipped ones with reasons, and the
    cursor of the next page (``None`` at the end)."""
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        raise CorpusError(f"not a Trove JSON response: {exc}") from None
    if not isinstance(payload, dict):
        raise CorpusError("not a Trove search response")
    docs: dict[str, Document] = {}
    skipped: list[str] = []
    next_start: str | None = None
    found = False
    for records in _records(payload):
        found = True
        next_start = records.get("nextStart") or next_start
        for art in records.get("article", []):
            art_id = str(art.get("id") or "")
            try:
                day = parse_iso_date(str(art.get("date")))
            except ValueError:
                skipped.append(f"{art_id or '?'}: undated")
                continue
            html = art.get("articleText")
            if not art_id or not isinstance(html, str) or not html.strip():
                skipped.append(f"{art_id or '?'}: no article text in the result")
                continue
            paper = art.get("title")
            paper = paper.get("title") if isinstance(paper, dict) else paper
            paper = " ".join(str(paper or "newspaper").split())
            heading = " ".join(str(art.get("heading") or art_id).split())
            docs[art_id] = Document(
                id=f"trove:{art_id}",
                date=day,
                source=f"Trove, {paper}",
                title=heading,
                text=_html_text(html),
                url=str(art.get("troveUrl") or f"https://nla.gov.au/nla.news-article{art_id}"),
            )
    if not found:
        raise CorpusError("not a Trove newspaper search response (no newspaper records)")
    return docs, skipped, next_start


class TroveCorpus(IndexedCorpus):
    source = "trove"

    def documents_in_raw(self, data: bytes, path: str) -> dict[str, Document]:
        return parse_results(data)[0]


def fetch(
    corpus: TroveCorpus,
    *,
    since: date,
    until: date,
    terms: Iterable[str],
    api_key: str,
    fetcher: Fetcher,
    max_pages: int | None = None,
) -> tuple[int, list[str]]:
    """Page through the results for ``terms`` in ``[since, until]`` with the cursor; store each
    response (under a URL without the key) and index the articles dated inside the range."""
    terms = [t for t in terms if t]
    if not terms:
        raise CorpusError("a Trove fetch needs query terms")
    if not api_key:
        raise CorpusError("a Trove fetch needs an API key (set TROVE_API_KEY)")
    try:
        entries = {e.id: e for e in corpus.read_index()}
    except CorpusError:
        entries = {}
    skipped: list[str] = []
    start, pages = "*", 0
    while max_pages is None or pages < max_pages:
        url = search_url(terms, since, until, start)
        data = fetcher(url, {"X-API-KEY": api_key})
        docs, rejected, next_start = parse_results(data)
        skipped += rejected
        name = corpus.store_raw(f"result_{sha256_bytes(url.encode())[:16]}.json", data, url)
        for locator, doc in docs.items():
            if since <= doc.date <= until and matches_terms(doc.title + "\n" + doc.text, terms):
                entries[doc.id] = IndexEntry(doc.id, doc.date, doc.title, doc.url, name, locator)
        pages += 1
        if not next_start or next_start == start or not docs and not rejected:
            break
        start = next_start
    corpus.write_index(entries.values(), skipped)
    return len(entries), skipped
