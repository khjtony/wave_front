"""Historic Hansard: dated UK parliamentary debates, 1803 to 2005.

Format. The Historic Hansard site (``https://api.parliament.uk/historic-hansard/``) serves
static HTML. A sitting day is listed at ``sittings/<yyyy>/<mon>/<dd>`` (``mon`` is the
three-letter lower-case month), which links to its debate sections at
``commons/<yyyy>/<mon>/<dd>/<slug>`` and ``lords/<yyyy>/<mon>/<dd>/<slug>``. A section page has
the heading in ``<h1 class="title">``, a ``<title>`` of the form ``HEADING (Hansard, 31 March
1939)``, and one ``<div class="hentry member_contribution">`` per speech, with the speaker in
``<cite class="member ...">`` and the words in ``<blockquote class="contribution_text
entry-content">``; procedural lines are ``<p class="procedural">``.

Dating. The sitting day in the URL is the document's date, cross-checked against the date in
the ``<title>`` when there is one. A speech is reported in the Official Report of its sitting
day; the Report itself appeared the next morning, which a replay at quarterly resolution
does not distinguish.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date, timedelta
from html.parser import HTMLParser

from .base import (
    CorpusError,
    Document,
    Fetcher,
    IndexedCorpus,
    IndexEntry,
    clean_text,
    matches_terms,
)

__all__ = [
    "HansardCorpus",
    "parse_section",
    "section_links",
    "sitting_url",
    "fetch",
    "BASE",
]

BASE = "https://api.parliament.uk/historic-hansard"
MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")
_SECTION = re.compile(
    r"(?:https?://api\.parliament\.uk)?/historic-hansard/(commons|lords)/"
    r"(\d{4})/([a-z]{3})/(\d{2})/([a-z0-9][a-z0-9-]*)/?$"
)
_TITLE_DATE = re.compile(r"\(Hansard, (\d{1,2}) ([A-Z][a-z]+) (\d{4})\)")
_MONTH_NAMES = (
    "January February March April May June July August September October November December"
).split()


def sitting_url(day: date) -> str:
    return f"{BASE}/sittings/{day.year}/{MONTHS[day.month - 1]}/{day.day:02d}"


def section_date(url: str) -> tuple[str, date, str]:
    """``(house, date, slug)`` of a section URL."""
    m = _SECTION.search(url)
    if not m:
        raise CorpusError(f"{url}: not a Historic Hansard section URL")
    house, year, mon, dd, slug = m.groups()
    if mon not in MONTHS:
        raise CorpusError(f"{url}: unknown month {mon!r}")
    return house, date(int(year), MONTHS.index(mon) + 1, int(dd)), slug


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)


def section_links(html: str, houses: Iterable[str] = ("commons", "lords")) -> list[str]:
    """The absolute URLs of the debate sections a sitting-day page links to, in page order."""
    parser = _LinkParser()
    parser.feed(html)
    houses = set(houses)
    out: list[str] = []
    for href in parser.links:
        m = _SECTION.search(href)
        if m and m.group(1) in houses:
            url = f"{BASE}/{m.group(1)}/{m.group(2)}/{m.group(3)}/{m.group(4)}/{m.group(5)}"
            if url not in out:
                out.append(url)
    return out


class _SectionParser(HTMLParser):
    """Collects the heading, the page title and the contributions of a section page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.heading = ""
        self.paragraphs: list[str] = []
        self.fallback: list[str] = []
        self._stack: list[tuple[str, set[str]]] = []
        self._buf: list[str] = []
        self._speaker = ""
        self._in_title = self._in_h1 = self._in_cite = False
        self._p_depth = 0

    def _within(self, cls: str) -> bool:
        return any(cls in classes for _, classes in self._stack)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = set((dict(attrs).get("class") or "").split())
        if tag in ("br", "img", "hr", "input", "meta", "link"):
            return
        if tag == "p" and any(t == "p" for t, _ in self._stack):
            self.handle_endtag("p")  # an unclosed paragraph ends where the next begins
        self._stack.append((tag, classes))
        if tag == "title":
            self._in_title = True
        elif tag == "h1":
            self._in_h1 = True
        elif tag == "cite" and "member" in classes:
            self._in_cite = True
            self._speaker = ""
        elif tag == "p":
            self._p_depth += 1
            self._buf = []

    def handle_endtag(self, tag: str) -> None:
        while self._stack:
            open_tag, classes = self._stack.pop()
            self._close(open_tag, classes)
            if open_tag == tag:
                break

    def _close(self, tag: str, classes: set[str]) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False
        elif tag == "cite" and "member" in classes:
            self._in_cite = False
        elif tag == "p" and self._p_depth:
            self._p_depth -= 1
            text = " ".join("".join(self._buf).split())
            self._buf = []
            if not text:
                return
            if self._within("contribution_text"):
                if self._speaker:
                    text = f"{self._speaker}: {text}"
                    self._speaker = ""
                self.paragraphs.append(text)
            elif "procedural" in classes:
                self.paragraphs.append(text)
            else:
                self.fallback.append(text)

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        if self._in_h1:
            self.heading += data
        if self._in_cite:
            self._speaker = " ".join((self._speaker + data).split())
        if self._p_depth:
            self._buf.append(data)


def parse_section(html: str, url: str) -> Document:
    """The debate section at ``url`` as a document dated by its sitting day."""
    house, day, slug = section_date(url)
    parser = _SectionParser()
    parser.feed(html)
    parser.close()
    m = _TITLE_DATE.search(parser.title)
    if m and m.group(2) in _MONTH_NAMES:
        titled = date(int(m.group(3)), _MONTH_NAMES.index(m.group(2)) + 1, int(m.group(1)))
        if titled != day:
            raise CorpusError(f"{url}: the page title dates it {titled}, the URL {day}")
    heading = " ".join(parser.heading.split()) or parser.title.split(" (Hansard")[0].strip()
    paragraphs = parser.paragraphs or parser.fallback
    text = clean_text("\n\n".join(paragraphs))
    if not text:
        raise CorpusError(f"{url}: no debate text found")
    label = "HC Deb" if house == "commons" else "HL Deb"
    return Document(
        id=f"hansard:{house}/{day.isoformat()}/{slug}",
        date=day,
        source=f"Historic Hansard, {label} {day.day} {_MONTH_NAMES[day.month - 1]} {day.year}",
        title=heading or slug,
        text=text,
        url=url,
    )


def _raw_name(url: str) -> str:
    house, day, slug = section_date(url)
    return f"{house}_{day.isoformat()}_{slug}.html"


class HansardCorpus(IndexedCorpus):
    source = "hansard"

    def documents_in_raw(self, data: bytes, path: str) -> dict[str, Document]:
        # The locator of a section page is its URL; the file name encodes it.
        stem = path.removesuffix(".html")
        house, day, slug = stem.split("_", 2)
        d = date.fromisoformat(day)
        url = f"{BASE}/{house}/{d.year}/{MONTHS[d.month - 1]}/{d.day:02d}/{slug}"
        return {url: parse_section(data.decode("utf-8", errors="replace"), url)}


def fetch(
    corpus: HansardCorpus,
    *,
    since: date,
    until: date,
    terms: Iterable[str] = (),
    houses: Iterable[str] = ("commons",),
    fetcher: Fetcher,
) -> tuple[int, list[str]]:
    """For each day in ``[since, until]``, read the sitting-day page (a day without a sitting
    is skipped), fetch every linked section of ``houses``, and index those whose heading or
    text contains one of ``terms``. Section pages that do not match are not stored."""
    terms = list(terms)
    houses = list(houses)
    try:
        entries = {e.id: e for e in corpus.read_index()}
    except CorpusError:
        entries = {}
    skipped: list[str] = []
    day = since
    while day <= until:
        url = sitting_url(day)
        try:
            listing = fetcher(url).decode("utf-8", errors="replace")
        except Exception as exc:  # no sitting that day (404) or a transient failure
            skipped.append(f"{url}: {exc}")
            day += timedelta(days=1)
            continue
        for section in section_links(listing, houses):
            data = fetcher(section)
            try:
                doc = parse_section(data.decode("utf-8", errors="replace"), section)
            except CorpusError as exc:
                skipped.append(str(exc))
                continue
            if not matches_terms(doc.title + "\n" + doc.text, terms):
                continue
            name = corpus.store_raw(_raw_name(section), data, section)
            entries[doc.id] = IndexEntry(doc.id, doc.date, doc.title, doc.url, name, section)
        day += timedelta(days=1)
    corpus.write_index(entries.values(), skipped)
    return len(entries), skipped
