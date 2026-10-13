"""Foreign Relations of the United States (FRUS): dated US diplomatic documents.

Format. The Office of the Historian publishes every FRUS volume as one TEI XML file
(namespace ``http://www.tei-c.org/ns/1.0``), mirrored in the public ``HistoryAtState/frus``
repository as ``volumes/<volume-id>.xml`` (for example ``frus1939v01``). Each document is a
``<div type="document" subtype="historical-document" xml:id="dN">`` whose ``<opener>`` carries
a ``<dateline>`` with a ``<date when="...">`` in the writer's local time; the div itself
carries ``frus:doc-dateTime-min`` and ``frus:doc-dateTime-max`` (namespace
``http://history.state.gov/frus/ns/1.0``) normalized by the editors. The reading page of a
document is ``https://history.state.gov/historicaldocuments/<volume-id>/dN``.

Dating and admissibility. A document's date is the date of its own dateline (the latest bound
when the dateline gives a range: ``when``, else ``notAfter`` or ``to``), else the date part of
``frus:doc-dateTime-max``. Editorial notes (``subtype="editorial-note"``) are written by the
editors decades later and are not admissible; inside a document, every ``<note>`` (source
notes and the editors' footnotes, which cite later knowledge) is left out of the text.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
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
    parse_iso_date,
)

__all__ = ["FrusCorpus", "parse_volume", "fetch", "volume_url", "DEFAULT_VOLUMES", "MIRROR"]

TEI = "{http://www.tei-c.org/ns/1.0}"
FRUS = "{http://history.state.gov/frus/ns/1.0}"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
# The raw-file URL pattern of the GitHub mirror; ``{volume}`` is replaced by the volume id.
# ``master`` follows the repository; a commit hash in its place pins the files fetched.
MIRROR = "https://raw.githubusercontent.com/HistoryAtState/frus/master/volumes/{volume}.xml"
READING = "https://history.state.gov/historicaldocuments/{volume}/{doc}"

# The general, European and Far Eastern volumes for 1936 to 1940 and the two Japan volumes.
DEFAULT_VOLUMES = (
    *(f"frus{y}v{v:02d}" for y in range(1936, 1941) for v in range(1, 6)),
    "frus1931-41v01",
    "frus1931-41v02",
)
# Block elements whose text starts a new paragraph.
_BLOCKS = {"p", "head", "opener", "closer", "dateline", "salute", "signed", "list", "item", "lg"}


def volume_url(volume: str, mirror: str = MIRROR) -> str:
    """The URL of a volume's TEI file under the URL pattern ``mirror`` (see :data:`MIRROR`)."""
    if "{volume}" not in mirror:
        raise CorpusError(f"mirror pattern {mirror!r} has no {{volume}} placeholder")
    return mirror.replace("{volume}", volume)


def _text(elem: ET.Element) -> str:
    """The text of ``elem`` without any ``<note>``, with paragraph breaks between blocks."""
    parts: list[str] = []

    def walk(e: ET.Element) -> None:
        tag = e.tag.removeprefix(TEI) if isinstance(e.tag, str) else ""
        if tag == "note":
            if e.tail:
                parts.append(e.tail)
            return
        if tag in _BLOCKS:
            parts.append("\n\n")
        if tag == "lb":
            parts.append("\n")
        if e.text:
            parts.append(e.text)
        for child in e:
            walk(child)
        if tag in _BLOCKS:
            parts.append("\n\n")
        if e.tail:
            parts.append(e.tail)

    walk(elem)
    # Line breaks inside a paragraph are layout only.
    text = "".join(parts)
    paragraphs = [" ".join(p.split()) for p in text.split("\n\n")]
    return clean_text("\n\n".join(p for p in paragraphs if p))


def _document_date(div: ET.Element) -> date | None:
    dateline = div.find(f"{TEI}opener/{TEI}dateline")
    if dateline is None:
        dateline = div.find(f".//{TEI}dateline")
    if dateline is not None:
        for d in dateline.iter(f"{TEI}date"):
            for attr in ("when", "notAfter", "to"):
                value = d.get(attr)
                if value:
                    try:
                        return parse_iso_date(value)
                    except ValueError:
                        continue
    value = div.get(f"{FRUS}doc-dateTime-max")
    if value:
        try:
            return parse_iso_date(value)
        except ValueError:
            return None
    return None


def parse_volume(data: bytes, volume: str) -> tuple[dict[str, Document], list[str]]:
    """The admissible documents of a volume by ``xml:id``, and the ids skipped with why."""
    try:
        tree = ET.fromstring(data)
    except ET.ParseError as exc:
        raise CorpusError(f"{volume}: not well-formed TEI: {exc}") from None
    docs: dict[str, Document] = {}
    skipped: list[str] = []
    for div in tree.iter(f"{TEI}div"):
        if div.get("type") != "document":
            continue
        doc_id = div.get(XML_ID) or ""
        if div.get("subtype") != "historical-document":
            skipped.append(
                f"{volume}/{doc_id}: {div.get('subtype')} (not a contemporaneous document)"
            )
            continue
        day = _document_date(div)
        if day is None:
            skipped.append(f"{volume}/{doc_id}: undated")
            continue
        head = div.find(f"{TEI}head")
        title = " ".join(_text(head).split()) if head is not None else doc_id
        body = [child for child in div if child.tag != f"{TEI}head"]
        text = clean_text("\n\n".join(t for t in (_text(c) for c in body) if t))
        if not text:
            skipped.append(f"{volume}/{doc_id}: no text")
            continue
        docs[doc_id] = Document(
            id=f"frus:{volume}/{doc_id}",
            date=day,
            source=f"FRUS {volume}",
            title=title,
            text=text,
            url=READING.format(volume=volume, doc=doc_id),
        )
    return docs, skipped


class FrusCorpus(IndexedCorpus):
    source = "frus"

    def documents_in_raw(self, data: bytes, path: str) -> dict[str, Document]:
        return parse_volume(data, path.removesuffix(".xml"))[0]


def fetch(
    corpus: FrusCorpus,
    volumes: Iterable[str],
    *,
    since: date | None,
    until: date,
    terms: Iterable[str] = (),
    fetcher: Fetcher,
    mirror: str = MIRROR,
) -> tuple[int, list[str]]:
    """Download each volume's TEI file (from the URL pattern ``mirror``) into the raw
    directory and index the documents dated in ``[since, until]`` whose text contains one of
    ``terms`` (all when ``terms`` is empty). Existing index entries of other volumes are kept.
    Returns the number indexed and the skipped documents with reasons."""
    terms = list(terms)
    try:
        kept = corpus.read_index()
    except CorpusError:
        kept = []
    volumes = list(volumes)
    entries = [e for e in kept if e.path.removesuffix(".xml") not in volumes]
    skipped: list[str] = []
    for volume in volumes:
        url = volume_url(volume, mirror)
        data = fetcher(url)
        name = corpus.store_raw(f"{volume}.xml", data, url)
        docs, rejected = parse_volume(data, volume)
        skipped += rejected
        for locator, doc in docs.items():
            if doc.date > until or (since is not None and doc.date < since):
                continue
            if not matches_terms(doc.title + "\n" + doc.text, terms):
                continue
            entries.append(IndexEntry(doc.id, doc.date, doc.title, doc.url, name, locator))
    corpus.write_index(entries, skipped)
    return len(entries), skipped
