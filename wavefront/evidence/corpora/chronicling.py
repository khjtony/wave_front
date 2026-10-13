"""Chronicling America (Library of Congress): digitized US newspaper pages to 1963.

Format. The classic search API returns JSON for
``https://chroniclingamerica.loc.gov/search/pages/results/?ortext=...&date1=MM/DD/YYYY&date2=MM/DD/YYYY&dateFilterType=range&rows=N&page=K&format=json``:
an object with ``totalItems``, ``startIndex``, ``endIndex``, ``itemsPerPage`` and ``items``,
one item per newspaper page with ``id`` (``/lccn/<lccn>/<yyyy-mm-dd>/ed-<n>/seq-<n>/``),
``date`` (``YYYYMMDD``, the issue date), ``title`` (the newspaper), ``sequence`` (page
number) and ``ocr_eng`` (the page's full OCR text). The page is read at
``https://chroniclingamerica.loc.gov<id>``.

The Library of Congress has been moving this collection to the loc.gov API
(``https://www.loc.gov/collections/chronicling-america/?fo=json``), whose search results carry
snippets rather than the page text. This module reads the classic format only; a result
without ``ocr_eng`` is skipped, never indexed with partial text. Check which API is live
before a fetch on the owner's machine (data/ww2/corpora/README.md).

Dating. The issue date is the document's date. A newspaper reports an event on the same or a
later day, so replay lags from this source are measured from the issue date.
"""

from __future__ import annotations

import json
import re
import urllib.parse
from collections.abc import Iterable
from datetime import date

from .base import (
    CorpusError,
    Document,
    Fetcher,
    IndexedCorpus,
    IndexEntry,
    clean_text,
    matches_terms,
    sha256_bytes,
)

__all__ = ["ChroniclingCorpus", "parse_results", "search_url", "fetch", "SEARCH"]

SEARCH = "https://chroniclingamerica.loc.gov/search/pages/results/"
SITE = "https://chroniclingamerica.loc.gov"
_DATE8 = re.compile(r"(\d{4})(\d{2})(\d{2})")


def search_url(terms: Iterable[str], since: date, until: date, page: int, rows: int = 50) -> str:
    params = {
        "ortext": " ".join(terms),
        "date1": since.strftime("%m/%d/%Y"),
        "date2": until.strftime("%m/%d/%Y"),
        "dateFilterType": "range",
        "rows": str(rows),
        "page": str(page),
        "format": "json",
    }
    return SEARCH + "?" + urllib.parse.urlencode(params)


def _item_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    m = _DATE8.fullmatch(value.strip())
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


def parse_results(data: bytes) -> tuple[dict[str, Document], list[str], dict[str, int]]:
    """The pages of one search-results response by item id, the skipped items with reasons,
    and the paging fields (``totalItems``, ``endIndex``)."""
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        raise CorpusError(f"not a Chronicling America JSON response: {exc}") from None
    if not isinstance(payload, dict) or "items" not in payload:
        raise CorpusError("not a Chronicling America search response (no 'items')")
    docs: dict[str, Document] = {}
    skipped: list[str] = []
    for item in payload["items"]:
        item_id = str(item.get("id") or "")
        day = _item_date(item.get("date"))
        text = item.get("ocr_eng")
        if not item_id or day is None:
            skipped.append(f"{item_id or '?'}: undated or without id")
            continue
        if not isinstance(text, str) or not text.strip():
            skipped.append(f"{item_id}: no full text in the result")
            continue
        paper = " ".join(str(item.get("title") or "newspaper").split())
        seq = item.get("sequence")
        docs[item_id] = Document(
            id=f"chronicling:{item_id.strip('/')}",
            date=day,
            source=f"Chronicling America, {paper}",
            title=f"{paper}, {day.isoformat()}, page {seq}" if seq else f"{paper}, {day}",
            text=clean_text(text),
            url=SITE + item_id,
        )
    paging = {
        "totalItems": int(payload.get("totalItems") or 0),
        "endIndex": int(payload.get("endIndex") or 0),
    }
    return docs, skipped, paging


class ChroniclingCorpus(IndexedCorpus):
    source = "chronicling"

    def documents_in_raw(self, data: bytes, path: str) -> dict[str, Document]:
        return parse_results(data)[0]


def fetch(
    corpus: ChroniclingCorpus,
    *,
    since: date,
    until: date,
    terms: Iterable[str],
    fetcher: Fetcher,
    rows: int = 50,
    max_pages: int | None = None,
) -> tuple[int, list[str]]:
    """Page through the search results for ``terms`` in ``[since, until]``; store each
    response and index the pages dated inside the range (the API's date filter is trusted
    only as a pre-filter)."""
    terms = [t for t in terms if t]
    if not terms:
        raise CorpusError("a Chronicling America fetch needs query terms")
    try:
        entries = {e.id: e for e in corpus.read_index()}
    except CorpusError:
        entries = {}
    skipped: list[str] = []
    page = 1
    while max_pages is None or page <= max_pages:
        url = search_url(terms, since, until, page, rows)
        data = fetcher(url)
        docs, rejected, paging = parse_results(data)
        skipped += rejected
        if not docs and not rejected:
            break
        name = corpus.store_raw(f"search_{sha256_bytes(url.encode())[:16]}.json", data, url)
        for locator, doc in docs.items():
            if since <= doc.date <= until and matches_terms(doc.text, terms):
                entries[doc.id] = IndexEntry(doc.id, doc.date, doc.title, doc.url, name, locator)
        if paging["endIndex"] >= paging["totalItems"]:
            break
        page += 1
    corpus.write_index(entries.values(), skipped)
    return len(entries), skipped
