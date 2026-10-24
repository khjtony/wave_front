"""CIA intelligence estimates on the Soviet Union (National Intelligence Estimates and related
papers): an edited volume split into its estimates, and estimates fetched one by one.

Raw files. ``data/cw/corpora/raw/crest/`` holds PDFs and a ``MANIFEST.json`` (URL, fetch date,
size, SHA-256 and a note for each file), written by whoever fetched them; there is no fetch
step in this module (the CIA reading room was down when the files were fetched, and most came
from the Wayback Machine). :func:`build_index` reads the files already there and writes
``index.json``. Text comes from each PDF's text layer through ``pdftotext`` (poppler-utils),
run on a temporary copy of the checksummed bytes; nothing is OCRed here. A PDF without a usable
text layer (scanned images only) yields no document and is listed under ``skipped``.

The volume. Steury (ed.), *Intentions and Capabilities: Estimates on Soviet Strategic Forces,
1950-1983* (CIA Center for the Study of Intelligence, 1996) reproduces 41 estimates, the
longer ones as their summaries or key judgments with extracts, in page facsimile, with
introductions by the editor between groups of estimates. The CSI publishes it whole
(``Steury1996_Intentions-and-Capabilities-1.pdf``) and split into front matter, Parts I-III and
an afterword (``Steury1996_*``). :data:`STEURY_1996` is the volume's table of contents: every
estimate and every editorial section with the volume page it starts on. A volume file is split
by its printed page numbers (read from the foot of each page): the pages from an estimate's
first page up to the page before the next entry of the contents are that estimate; the pages of
an editorial section are dropped.

Anti-hindsight rule (as for the FRUS editors' notes, ``frus.strip_editorial``). Left out of
every document: the editor's introductions and section essays (written in 1996), the front
matter and the afterword; on the estimate's pages, the editor's heading ("6. NIE 11-5-58
Soviet Capabilities ..."), the running head "6. (Continued)" and the volume's page number.
Left out of every file: the release stamps added at declassification ("APPROVED FOR RELEASE /
CIA HISTORICAL REVIEW PROGRAM", "RELEASE DATE: 16-Jul-2011", "DECLASSIFIED IN PART PER E.O.
13526", "Sanitized Copy Approved for Release ..."). The original markings (classification,
control numbers) stay: they are part of the document as issued.

Dating. A document's date is its estimate's own date (the date the estimate was issued or
concurred in), never the date of the 1996 volume or of the release. A separately fetched file
is dated by its file name, ``<series>_<number>[_MH]_<YYYY-MM-DD>_<title>.pdf``, which names the
date on its cover. The volume prints no date with most estimates (its facsimiles start at the
estimate's first text page, after the cover), so :data:`STEURY_1996` gives a date only where
the date is printed in this corpus or recorded with a source in this repository, and says
where (``basis``); an estimate without one is undated and not admissible, like any undated
document, and is listed under ``skipped``. The PFIAB report "The Soviet War Scare" (15
February 1990) is a retrospective; it is dated 1990-02-15 and is invisible to any replay
before then.

Duplicates. An estimate held twice (reproduced in the volume and fetched as a full text, or
fetched as two parts or two copies) gives one document per file, each with its own id, and all
of them carry the same :attr:`~.base.Document.work` (the estimate's number), so the
two-document rule of the harness counts them once.

Ids. ``crest:<number>_<date>`` (``crest:NIE_11-8/1-61_1961-09-21``), with ``/<part>`` for a part
or a second copy (``/annex-c``, ``/iscap-2013-015``) and ``@steury1996`` for the volume's
reproduction. The locator inside a raw file is the page range: ``vol. pp. 121-138`` (the
volume's printed pages) or ``pp. 1-46`` (the pages of a single PDF); :attr:`Document.source`
repeats it and the URL points at the first page (``#page=N``).
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .base import ROOT, CorpusError, Document, IndexedCorpus, IndexEntry, clean_text

__all__ = [
    "CW_RAW_ROOT",
    "STEURY_1996",
    "CrestCorpus",
    "Entry",
    "SeparateFile",
    "build_index",
    "has_text_layer",
    "parse_separate_name",
    "pdf_pages",
    "split_volume",
    "strip_release_stamps",
    "volume_page_numbers",
    "works",
]

CW_RAW_ROOT = ROOT / "data" / "cw" / "corpora" / "raw"
VOLUME = "Steury 1996"
VOLUME_PREFIX = "Steury1996_"
# Files of the volume that hold no estimate: the 1996 front matter and afterword.
EDITORIAL_FILES = ("Front-Matter", "Part-IV-Afterword")
# A page with fewer characters than this has no usable text layer.
MIN_PAGE_CHARS = 100


@dataclass(frozen=True)
class Entry:
    """One entry of the volume's table of contents: an estimate (``no`` 1 to 41) or one of the
    editor's sections (``no`` 0), with the volume page it starts on. ``date`` is the
    estimate's own date where it is established, and ``basis`` says where it is printed."""

    no: int
    number: str
    title: str
    start: int
    date: date | None = None
    basis: str = ""

    @property
    def editorial(self) -> bool:
        return self.no == 0


def _e(no, number, title, start, day=None, basis=""):
    return Entry(no, number, title, start, date.fromisoformat(day) if day else None, basis)


def _ed(title, start):
    return Entry(0, "", title, start)


_CITED_5858 = "cited with its date in NIE 11-5-58 (vol. p. 65)"
# The contents of Steury 1996 (front matter, pp. v-vi). Dates: see Entry.basis; an estimate
# with no date here is undated in this corpus (its date is not printed in the volume or in
# another document of the corpus).
STEURY_1996: tuple[Entry, ...] = (
    _ed("Part I: The Soviet Union as a World Power", 1),
    _ed('The "Bomber Gap," 1955-58', 5),
    _e(
        1,
        "NIE 11-56",
        "Soviet Gross Capabilities for Attack on the US and Key Overseas "
        "Installations and Forces Through Mid-1959",
        9,
        "1956-03-06",
        "printed on the cover, vol. p. 9 (concurred in by the IAC on 6 March 1956)",
    ),
    _e(
        2,
        "SNIE 11-6-57",
        "Soviet Gross Capabilities for Attack on the Continental US in Mid-1960",
        39,
    ),
    _e(3, "SNIE 11-7-58", "Strength and Composition of the Soviet Long Range Bomber Force", 47),
    _ed('The "Missile Gap," 1957-61', 55),
    _e(
        4,
        "NIE 11-5-57",
        "Soviet Capabilities and Probable Programs in the Guided Missile Field",
        59,
        "1957-03-12",
        _CITED_5858,
    ),
    _e(5, "SNIE 11-10-57", "The Soviet ICBM Program", 63, "1957-12-10", _CITED_5858),
    _e(
        6,
        "NIE 11-5-58",
        "Soviet Capabilities in Guided Missiles and Space Vehicles",
        65,
        "1958-08-19",
        "the cover of the full text in this corpus",
    ),
    _e(
        7,
        "NIE 11-8-59",
        "Soviet Capabilities for Strategic Attack Through Mid-1964",
        71,
        "1960-02-09",
        "cited with its date in NIE 11-8-60 (vol. p. 109); the full text",
    ),
    _e(
        8,
        "NIE 11-8-60",
        "Soviet Capabilities for Long Range Attack Through Mid-1965",
        109,
        "1960-08-01",
        "the cover of the full text in this corpus",
    ),
    _e(
        9,
        "NIE 11-8-61",
        "Soviet Capabilities for Long Range Attack",
        115,
        "1961-06-07",
        "cited with its date in NIE 11-8/1-61 (vol. p. 121); the full text",
    ),
    _e(
        10,
        "NIE 11-8/1-61",
        "Strength and Deployment of Soviet Long Range Ballistic Missile Forces",
        121,
        "1961-09-21",
        "data/cw/events.csv (Prados 1982; Ruffner (ed.) 1995); not printed in the volume",
    ),
    _ed("Part II: Soviet Force Requirements", 139),
    _e(11, "NIE 11-4-60", "Main Trends in Soviet Capabilities and Policies, 1960-1965", 141),
    _e(12, "NIE 11-4-63", "Soviet Military Capabilities and Policies, 1962-1967", 147),
    _e(13, "NIE 11-4-64", "Main Trends in Soviet Military Policy", 157),
    _e(
        14,
        "NIE 11-4-65",
        "Main Trends in Soviet Military Policy",
        163,
        "1965-04-14",
        "the editor's note, vol. p. 139",
    ),
    _e(
        15,
        "NIE 11-4-68",
        "Main Issues in Soviet Military Policy",
        173,
        "1968-09-19",
        "the editor's note, vol. p. 139",
    ),
    _e(16, "NIE 11-8-62", "Soviet Capabilities for Long Range Attack", 181),
    _e(
        17,
        "NIE 11-8-64",
        "Soviet Capabilities for Strategic Attack",
        191,
        "1964-10-08",
        "cited with its date in the Memorandum to Holders of NIE 11-8-64 (vol. p. 199)",
    ),
    _e(18, "M/H NIE 11-8-64", "Soviet Capabilities for Strategic Attack", 199),
    _e(19, "NIE 11-8-65", "Soviet Capabilities for Strategic Attack", 203),
    _e(
        20,
        "NIE 11-8-66",
        "Soviet Capabilities for Strategic Attack",
        209,
        "1966-10-20",
        "cited with its date in the Memorandum to Holders of NIE 11-8-66 (vol. p. 221)",
    ),
    _e(
        21,
        "M/H NIE 11-8-66",
        "Soviet Capabilities for Strategic Attack",
        221,
        "1967-03-13",
        "printed at its end, vol. p. 222 (paragraphs 1-4 approved by USIB 13 March 1967, "
        "paragraph 5 on 2 March 1967)",
    ),
    _ed("Soviet ICBM Accuracy and MIRVs", 223),
    _e(22, "NIE 11-8-67", "Soviet Capabilities for Strategic Attack", 225),
    _e(23, "NIE 11-8-68", "Soviet Strategic Attack Forces", 239),
    _e(24, "NIE 11-8-69", "Soviet Strategic Attack Forces", 253),
    _e(
        25,
        "NIE 11-8-70",
        "Soviet Forces for Intercontinental Attack",
        263,
        "1970-11-24",
        "cited with its date in NIE 11-8-71 (vol. p. 275)",
    ),
    _e(26, "NIE 11-8-71", "Soviet Forces for Intercontinental Attack", 275),
    _ed("Part III: Soviet Strategic Objectives and Force Planning", 287),
    _e(27, "NIE 11-4-72", "Issues and Options in Soviet Military Policy", 289),
    _e(28, "SNIE 11-4-73", "Soviet Strategic Arms Programs and Detente: What are They Up To?", 297),
    _ed("Arms Control and Qualitative Competition", 309),
    _e(29, "NIE 11-8-72", "Soviet Forces for Intercontinental Attack", 311),
    _e(30, "NIE 11-8-73", "Soviet Forces for Intercontinental Attack", 323),
    _e(31, "NIE 11-3/8-74", "Soviet Forces for Intercontinental Conflict", 329),
    _ed("The A-Team/B-Team Experiment and Its Aftermath", 335),
    _e(
        32,
        "NIE 11-3/8-76",
        "Soviet Forces for Intercontinental Conflict Through the Mid-1980s",
        339,
    ),
    _e(33, "B-Team Report", "Soviet Strategic Objectives: An Alternative View", 365),
    _e(34, "NIE 11-4-77", "Soviet Strategic Objectives", 391),
    _e(35, "NIE 11-4-78", "Soviet Goals and Expectations in the Global Power Arena", 397),
    _e(
        36,
        "NIE 11-3/8-79",
        "Soviet Capabilities for Strategic Nuclear Conflict Through the 1980s",
        407,
    ),
    _e(
        37,
        "NIE 11-3/8-80",
        "Soviet Capabilities for Strategic Nuclear Conflict Through Late 1980s",
        429,
    ),
    _ed("Strategic Weapons in Context With Soviet Ambitions", 467),
    _e(38, "M/H NIE 11-4-78", "Soviet Goals and Expectations in the Global Power Arena", 469),
    _e(39, "NIE 11-4-82", "The Soviet Challenge to US Security Interests", 475),
    _e(40, "NIE 11-3/8-82", "Soviet Capabilities for Strategic Nuclear Conflict, 1982-1992", 483),
    _e(41, "NIE 11-3/8-83", "Soviet Capabilities for Strategic Nuclear Conflict, 1982-1992", 491),
)


# -- PDF text --------------------------------------------------------------------------------


def pdf_pages(data: bytes, *, layout: bool = False) -> list[str]:
    """The text layer of a PDF, one string per page (``pdftotext``; ``layout`` keeps the
    physical layout, which puts the page number on the last line, but runs columns together).
    The PDF is never executed or rendered, only its text objects are read."""
    exe = shutil.which("pdftotext")
    if exe is None:
        raise CorpusError("pdftotext not found: install poppler-utils to read the CREST corpus")
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "in.pdf"
        src.write_bytes(data)
        args = [exe, "-q", "-enc", "UTF-8", *(["-layout"] if layout else []), str(src), "-"]
        done = subprocess.run(args, capture_output=True, check=False, timeout=600)
    if done.returncode != 0:
        raise CorpusError(f"pdftotext failed ({done.returncode}): {done.stderr[:200]!r}")
    pages = done.stdout.decode("utf-8", errors="replace").split("\f")
    if pages and not pages[-1].strip():
        pages.pop()  # pdftotext ends the last page with a form feed
    return pages


def _chars(page: str) -> int:
    return len("".join(page.split()))


def has_text_layer(pages: Sequence[str]) -> bool:
    """True when at least a quarter of the pages carry text (a scanned PDF without a text
    layer gives empty pages, or a few stray characters)."""
    if not pages:
        return False
    return sum(_chars(p) >= MIN_PAGE_CHARS for p in pages) * 4 >= len(pages)


# Declassification stamps (added decades later, not part of the document as issued).
_STAMP_WORDS = re.compile(
    r"APPR\S{0,4}\s*\S{0,3}\s*F\S{0,2}R\s*R\S{1,3}[AE]S|R[EF]L?\S?EASE|H\S?[I1l]S\S{1,3}R[I1lC]|"
    r"REV\S?[I1l]?\S?EW|PROG\S{0,2}R?A|DECLASS|SANITI[ZS]|F\S{0,2}R\s+\S{0,2}R\S{0,4}[SA]SE\b",
)
_STAMP_LINE = re.compile(
    r"(?i)(approved\s+for\s+release|sanitized\s+copy|declassified|release\s+date|"
    r"release\s+as\s+sanitized|historical[\s.-]*review|^\W*date:?\W*$|^\W*date:\s*\d|"
    r"^\W*app\S{0,6}(\s+f\S{0,2}r)?\W*$|\bhr\s?-?70-14\b|"
    # a release date: 16-Jul-2011, -18-2012, 2005/03/24 (years after the estimates)
    r"\d{1,3}-[a-z]{3}-\d{4}|-\d{1,2}-(?:199\d|20[0-3]\d)\b|\b(?:199\d|20[0-3]\d)/\d\d/\d\d\b)"
)


# The release line CREST prints on every page ("Sanitized Copy Approved for Release
# 2011/08/12 : CIA-RDP..."), which can be long.
_RELEASE_LINE = re.compile(
    r"(?i)approved\s+for\s+release\s+(?:19|20)\d\d/\d\d/\d\d|sanitized\s+copy"
)


def _is_stamp(line: str) -> bool:
    s = line.strip()
    if not s or len(s) > 160:
        return False
    if _RELEASE_LINE.search(s):
        return True
    if len(s) > 70:
        return False
    if _STAMP_LINE.search(s):
        return True
    letters = [c for c in s if c.isalpha()]
    upper = sum(c.isupper() for c in letters)
    return len(letters) >= 5 and upper >= 0.7 * len(letters) and bool(_STAMP_WORDS.search(s))


def strip_release_stamps(text: str) -> str:
    """``text`` without the lines that are declassification stamps."""
    return "\n".join(line for line in text.split("\n") if not _is_stamp(line))


# -- the volume ------------------------------------------------------------------------------


_DIGITS = str.maketrans({"l": "1", "I": "1", "i": "1", "O": "0", "o": "0"})
_NUMBER = re.compile(r"\d{1,3}")


def _page_number_candidates(page: str) -> list[int]:
    lines = [ln.strip() for ln in page.split("\n") if ln.strip()]
    out = []
    for ln in lines[-3:]:
        s = ln.translate(_DIGITS)
        if _NUMBER.fullmatch(s):
            out.append(int(s))
    return out


def volume_page_numbers(pages: Sequence[str]) -> list[int | None]:
    """The printed volume page number of each page, read from its last lines: the first
    number read anchors the sequence, and each later page takes the smallest number read on
    it within three pages of the last one (a blank page of the volume may be missing from the
    file, and the original document's own page numbers stand near the volume's); a page with
    no such number is ``None``, unless it is the only page between two read pages one number
    apart."""
    out: list[int | None] = []
    prev: int | None = None
    for page in pages:
        cands = _page_number_candidates(page)
        value: int | None = None
        if prev is None:
            value = max(cands) if cands else None
        else:
            ok = [c for c in cands if prev < c <= prev + 3]
            value = min(ok) if ok else None
        if value is not None:
            prev = value
        out.append(value)
    for i in range(1, len(out) - 1):
        a, b = out[i - 1], out[i + 1]
        if out[i] is None and a is not None and b is not None and b - a == 2:
            out[i] = a + 1
    return out


_CONTINUED = re.compile(r"C[o0][nmr]?[tr]?[il]nu?ed")
# The entry number of a heading set as a block of its own ("2.", OCR "-t" for "4.").
_NUMBER_ONLY = re.compile(r"^\s*\S{1,4}\s*$")


def _blocks(page: str) -> list[str]:
    return [b for b in re.split(r"\n\s*\n", page) if b.strip()]


def _is_continued(page: str) -> bool:
    """The editor's running head "N. (Continued)" opens the page."""
    head = " ".join(_blocks(page)[:2])[:40]
    return bool(_CONTINUED.search(head))


def _drop_head(page: str, first: bool) -> str:
    """The page without the editor's heading (first page) or running head (the others)."""
    blocks = _blocks(page)
    if first:
        k = 1 if blocks and _NUMBER_ONLY.match(blocks[0]) else 0
        return "\n\n".join(blocks[k + 1 :])  # "N. DESIGNATOR Title", set apart above
    if blocks and _CONTINUED.search(blocks[0][:40]):
        return "\n\n".join(blocks[1:])
    if len(blocks) > 1 and _NUMBER_ONLY.match(blocks[0]) and _CONTINUED.search(blocks[1][:40]):
        return "\n\n".join(blocks[2:])
    return "\n\n".join(blocks)


def _drop_page_number(page: str, number: int | None) -> str:
    if number is None:
        return page
    lines = page.split("\n")
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().translate(_DIGITS) == str(number):
            del lines[i]
            break
    return "\n".join(lines)


@dataclass(frozen=True)
class VolumeDocument:
    """An estimate found in a volume file: its contents entry, printed pages, the file's
    pages (1-based) and its text without the editor's matter."""

    entry: Entry
    first: int
    last: int
    pdf_first: int
    pdf_last: int
    text: str

    @property
    def locator(self) -> str:
        return f"vol. pp. {self.first}-{self.last}"


def split_volume(
    pages: Sequence[str],
    number_pages: Sequence[str] | None = None,
    contents: Sequence[Entry] = STEURY_1996,
) -> tuple[list[VolumeDocument], list[str]]:
    """Split the pages of a volume file into its estimates by the contents ``contents`` and
    the printed page numbers (read from ``number_pages``, the same pages laid out, when
    given). Returns the estimates found (with text) and the problems: an estimate whose
    first page carries the running head of a continued one, or an editorial page that does,
    means the page numbers were misread and the split cannot be trusted."""
    numbers = volume_page_numbers(number_pages if number_pages is not None else pages)
    entries = sorted(contents, key=lambda e: e.start)

    def entry_of(vol: int) -> Entry | None:
        found = None
        for e in entries:
            if e.start <= vol:
                found = e
        return found

    owner: list[Entry | None] = [entry_of(n) if n is not None else None for n in numbers]
    for i, n in enumerate(numbers):
        if n is not None:
            continue
        before = next((owner[j] for j in range(i - 1, -1, -1) if numbers[j] is not None), None)
        after = next((owner[j] for j in range(i + 1, len(numbers)) if numbers[j] is not None), None)
        if before is not None and (before is after or _is_continued(pages[i])):
            owner[i] = before
    problems: list[str] = []
    found: list[VolumeDocument] = []
    for entry in entries:
        idx = [i for i, e in enumerate(owner) if e is entry]
        if entry.editorial:
            for i in idx:
                if _is_continued(pages[i]):
                    problems.append(
                        f"page {i + 1} (vol. p. {numbers[i]}) carries an estimate's running "
                        f"head but falls in the editor's section {entry.title!r}"
                    )
            continue
        if not idx:
            continue
        start = idx[0]
        if numbers[start] != entry.start or _is_continued(pages[start]):
            problems.append(
                f"no. {entry.no} {entry.number}: its first page (vol. p. {entry.start}) was "
                f"not found where it starts (file page {start + 1}, vol. p. {numbers[start]})"
            )
            continue
        heading = " ".join(_blocks(pages[start])[:2])
        if entry.number.rsplit("-", 1)[-1][-2:] not in heading:
            problems.append(
                f"no. {entry.no} {entry.number}: the editor's heading on its first page (file "
                f"page {start + 1}) does not name it: {heading[:60]!r}"
            )
            continue
        parts = []
        for i in idx:
            body = _drop_page_number(pages[i], numbers[i])
            parts.append(_drop_head(body, first=i == start))
        text = clean_text(strip_release_stamps("\n\n".join(parts)))
        printed = [numbers[i] for i in idx if numbers[i] is not None]
        found.append(
            VolumeDocument(entry, min(printed), max(printed), idx[0] + 1, idx[-1] + 1, text)
        )
    return found, problems


# -- separately fetched estimates ------------------------------------------------------------


_SEPARATE = re.compile(
    r"^(?P<series>S?NIE|PFIAB)_(?:(?P<num>[0-9][0-9-]*?)_)?(?P<mh>MH_)?"
    r"(?P<date>\d{4}-\d{2}-\d{2})_(?P<title>.+)\.pdf$"
)
_NOTE_NUMBER = re.compile(r"^(?:Memorandum to Holders of )?(S?NIE [0-9][0-9/-]*[0-9])")
# The end of a file title that names a part or a copy: it goes into the document id.
_PART = re.compile(
    r"_(?P<part>main_text_Annexes_[A-Z]-[A-Z]|Annexes_[A-Z]-[A-Z]|Annex_[A-Z]|Key_Judgments|"
    r"full|ISCAP-[0-9-]+)$"
)


@dataclass(frozen=True)
class SeparateFile:
    """What a separately fetched file's name (and its manifest note) says about it."""

    number: str
    date: date
    title: str
    part: str
    memorandum: bool

    @property
    def work(self) -> str:
        return f"M/H {self.number}" if self.memorandum else self.number


def parse_separate_name(name: str, note: str = "") -> SeparateFile | None:
    """The estimate in a file named ``<series>_<number>[_MH]_<date>_<title>.pdf``. The number
    is taken from the manifest note when it starts with one (the file name writes ``/`` as
    ``-``: ``NIE_11-3-8-84-85`` is NIE 11-3/8-84/85), else from the name."""
    m = _SEPARATE.match(name)
    if not m:
        return None
    series, num = m.group("series"), m.group("num")
    if series == "PFIAB":
        number = "PFIAB The Soviet War Scare"
    else:
        noted = _NOTE_NUMBER.match(note)
        number = noted.group(1) if noted else f"{series} {num}"
    title = m.group("title")
    part = ""
    pm = _PART.search(title)
    if pm:
        part = pm.group("part")
        title = title[: pm.start()]
    return SeparateFile(
        number=number,
        date=date.fromisoformat(m.group("date")),
        title=title.replace("_", " "),
        part=part.lower().replace("_", "-") if part not in ("full",) else "",
        memorandum=bool(m.group("mh")),
    )


def _slug(number: str) -> str:
    return number.replace(" ", "_")


# -- the corpus ------------------------------------------------------------------------------


class CrestCorpus(IndexedCorpus):
    source = "crest"
    #: the volume's table of contents the volume files are split by
    contents: tuple[Entry, ...] = STEURY_1996

    def __init__(self, root: str | Path | None = None) -> None:
        super().__init__(root if root is not None else CW_RAW_ROOT / self.source)
        self._notes: dict[str, dict] | None = None

    def _record(self, path: str) -> dict:
        if self._notes is None:
            self._notes = self.read_manifest()
        return self._notes.get(path, {})

    def documents_in_raw(self, data: bytes, path: str) -> dict[str, Document]:
        return self.parse_file(data, path)[0]

    def parse_file(self, data: bytes, path: str) -> tuple[dict[str, Document], list[str]]:
        """The documents in one raw file by locator, and what was skipped in it with why."""
        record = self._record(path)
        url = str(record.get("url", ""))
        if path.startswith(VOLUME_PREFIX):
            if any(tag in path for tag in EDITORIAL_FILES):
                return {}, [f"{path}: the volume's front matter or afterword (1996, editorial)"]
            pages = pdf_pages(data)
            if not has_text_layer(pages):
                return {}, [f"{path}: no text layer ({len(pages)} pages of scanned images)"]
            found, problems = split_volume(pages, pdf_pages(data, layout=True), self.contents)
            if problems:
                raise CorpusError(f"{path}: the volume cannot be split", problems)
            docs: dict[str, Document] = {}
            skipped: list[str] = []
            for v in found:
                e = v.entry
                if e.date is None:
                    skipped.append(
                        f"{path}: no. {e.no} {e.number} ({v.locator}): undated (the volume "
                        "prints no date for it and no document of the corpus gives one)"
                    )
                    continue
                if not v.text:
                    skipped.append(f"{path}: no. {e.no} {e.number}: no text")
                    continue
                docs[v.locator] = Document(
                    id=f"crest:{_slug(e.number)}_{e.date.isoformat()}@steury1996",
                    date=e.date,
                    source=f"CIA estimates: {VOLUME}, no. {e.no}, {v.locator}",
                    title=f"{e.number}: {e.title} (as reproduced in {VOLUME}, no. {e.no})",
                    text=v.text,
                    url=f"{url or 'file:' + path}#page={v.pdf_first}",
                    work=e.number,
                )
            return docs, skipped
        info = parse_separate_name(path, str(record.get("note", "")))
        if info is None:
            return {}, [f"{path}: not a file of the corpus (unknown name)"]
        pages = pdf_pages(data)
        if not has_text_layer(pages):
            return {}, [f"{path}: no text layer ({len(pages)} pages of scanned images)"]
        text = clean_text(strip_release_stamps("\n\n".join(pages)))
        locator = f"pp. 1-{len(pages)}"
        suffix = f"/{info.part}" if info.part else ""
        doc_id = f"crest:{_slug(info.work)}_{info.date.isoformat()}{suffix}"
        return {
            locator: Document(
                id=doc_id,
                date=info.date,
                source=f"CIA estimates: {path}, {locator}",
                title=f"{info.work}: {info.title}" + (f" ({info.part})" if info.part else ""),
                text=text,
                url=url or f"file:{path}",
                work=info.work,
            )
        }, []


def build_index(corpus: CrestCorpus) -> tuple[int, list[str]]:
    """Index the PDFs of the raw directory that the manifest records (no network). Returns
    the number indexed and what was skipped with why: files without a text layer, the 1996
    editorial files, the estimates of the volume that are undated or have no text layer, and
    files on disk that the manifest does not record."""
    manifest = corpus.read_manifest()
    if not manifest:
        raise CorpusError(f"{corpus.manifest_path}: no manifest (nothing to index)")
    names = sorted(n for n in manifest if n.lower().endswith(".pdf"))
    # The parts of the volume before the whole volume: an estimate found in both comes once.
    names.sort(key=lambda n: (not n.startswith(VOLUME_PREFIX + "Part"), n))
    entries: list[IndexEntry] = []
    skipped: list[str] = []
    seen_volume: set[str] = set()
    for name in names:
        file = corpus.root / name
        if not file.exists():
            skipped.append(f"{name}: in the manifest, not on disk")
            continue
        docs, rejected = corpus.parse_file(file.read_bytes(), name)
        skipped += rejected
        for locator, doc in docs.items():
            if name.startswith(VOLUME_PREFIX):
                if doc.id in seen_volume:
                    continue
                seen_volume.add(doc.id)
            entries.append(IndexEntry(doc.id, doc.date, doc.title, doc.url, name, locator))
    # Every estimate of the contents is either indexed from a volume file or skipped with why.
    for e in corpus.contents:
        if e.editorial:
            continue
        if any(
            x.id.startswith(f"crest:{_slug(e.number)}_") and x.id.endswith("@steury1996")
            for x in entries
        ):
            continue
        if any(f" no. {e.no} {e.number} (" in r for r in skipped):
            continue
        skipped.append(
            f"{VOLUME} no. {e.no} {e.number} (vol. p. {e.start}): no volume file with a text "
            "layer holds it" + ("" if e.date else "; undated")
        )
    on_disk = {p.name for p in corpus.root.glob("*.pdf")}
    skipped += [f"{n}: on disk, not in the manifest" for n in sorted(on_disk - set(manifest))]
    corpus.write_index(entries, skipped)
    return len(entries), skipped


def works(docs: Iterable[Document]) -> dict[str, list[str]]:
    """The document ids of each work that the corpus holds more than once."""
    by: dict[str, list[str]] = {}
    for d in docs:
        by.setdefault(d.work_key, []).append(d.id)
    return {w: ids for w, ids in by.items() if len(ids) > 1}
