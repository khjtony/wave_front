"""The CIA estimates corpus (``crest``): the split of the Steury (1996) volume into its estimates
by the printed page numbers, the removal of the editor's matter and the release stamps, the
dating of separately fetched files by their names, the marking of one estimate held twice, and
the index on a synthetic sample (``fixtures/crest/``; text pages stand in for the PDFs). One
test runs on the real corpus when ``data/cw/corpora/raw/crest/`` and ``pdftotext`` are there."""

import json
import re
import shutil
from datetime import date
from pathlib import Path

import pytest

from wavefront.evidence.corpora import CorpusError, crest, open_corpus
from wavefront.evidence.corpora.crest import (
    STEURY_1996,
    CrestCorpus,
    Entry,
    build_index,
    has_text_layer,
    parse_separate_name,
    split_volume,
    strip_release_stamps,
    volume_page_numbers,
)
from wavefront.evidence.harness_rules import CORROBORATING, DEFAULT_RULES, HELD, OK, gate_records

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "tests" / "evidence" / "fixtures" / "crest" / "volume_sample.txt"
REAL = ROOT / "data" / "cw" / "corpora" / "raw" / "crest"

CONTENTS = (
    Entry(0, "", "Part I", 1),
    Entry(1, "NIE 11-1-57", "Soviet Capabilities for Missile Testing", 3, date(1957, 3, 1), "x"),
    Entry(0, "", 'The "Missile Gap," 1957-61', 6),
    Entry(2, "SNIE 11-2-58", "The Soviet ICBM Program", 7),
)
# Phrases of the editor (1996) and of the release, never in a document's text.
EDITORIAL = ("this volume", "declassified", "1996", "editor", "steury", "in retrospect")


def _pages():
    return SAMPLE.read_text(encoding="utf-8").split("\f")[:-1]


def test_page_numbers_skip_a_missing_blank_page_and_fill_a_single_gap():
    assert volume_page_numbers(_pages()) == [1, 3, 4, 5, 6, 7, 9]
    # The original's own page number ("2") does not take the volume's place.
    assert volume_page_numbers(["x\n\n7", "y\n\n2\n\n8", "z\n\n1\n\n10", "no number"]) == [
        7,
        8,
        10,
        None,
    ]


def test_split_volume_keeps_the_estimates_and_drops_the_editors_matter():
    found, problems = split_volume(_pages(), contents=CONTENTS)
    assert problems == []
    assert [(v.entry.no, v.first, v.last, v.pdf_first, v.pdf_last) for v in found] == [
        (1, 3, 5, 2, 4),
        (2, 7, 9, 6, 7),
    ]
    one, two = (v.text for v in found)
    assert "ten test vehicles by mid-1958" in one and "Table A" in one
    assert "very high priority" in one
    assert "first operational capability is expected in 1959" in two
    assert found[0].locator == "vol. pp. 3-5"
    for text in (one, two):
        low = text.lower()
        assert not any(p in low for p in EDITORIAL), text
        assert "continued" not in low and "cominued" not in low  # the running heads
        assert "NIE 11-1-57" not in text and "SNIE 11-2-58" not in text  # the headings
        assert "APPROVED FOR RELEASE" not in text and "2011" not in text  # the stamps
        assert not re.search(r"^\s*[3-9]\s*$", text, re.M)  # the volume's page numbers


def test_split_volume_reports_a_misread_page_number():
    pages = _pages()
    pages[1] = pages[1].replace("\n\n3", "\n\n2")  # the first page of no. 1 now reads vol. 2
    pages[2] = pages[2].replace("\n\n4", "\n\n3")  # and its continuation reads vol. 3
    _found, problems = split_volume(pages, contents=CONTENTS)
    assert any("no. 1 NIE 11-1-57" in p for p in problems)


def test_release_stamps_are_dropped_and_the_text_kept():
    text = (
        "APPROVED FOR RELEASE\nCIA HISTORICAL-REVIEW PROGRAM\nRELEASE DATE: 16-Jul-2011\n"
        "HR70-14\nDECLASSIFIED IN PART PER E.O.13526\n"
        "Sanitized Copy Approved for Release 2011/08/12 : CIA-RDP09T00367R000300290001-4\n"
        "TOP SECRET\nConcurred in by the USIB on 3 November 1959.\nSOVIET CAPABILITIES"
    )
    assert strip_release_stamps(text).split("\n") == [
        "TOP SECRET",
        "Concurred in by the USIB on 3 November 1959.",
        "SOVIET CAPABILITIES",
    ]


def test_text_layer_detection():
    assert not has_text_layer(["", " ", "\n"])
    assert not has_text_layer([])
    assert has_text_layer(["x" * 200, "", "", ""])
    assert not has_text_layer(["x" * 200] + [""] * 4)


def test_separate_file_names():
    a = parse_separate_name(
        "NIE_11-3-8-84-85_1985-04-25_Soviet_Capabilities_Key_Judgments.pdf",
        "NIE 11-3/8-84/85, 25 Apr 1985, Soviet Capabilities ...",
    )
    assert (a.number, a.date, a.part, a.work) == (
        "NIE 11-3/8-84/85",
        date(1985, 4, 25),
        "key-judgments",
        "NIE 11-3/8-84/85",
    )
    b = parse_separate_name("NIE_11-5-58_MH_1958-11-25_Memorandum_to_Holders.pdf")
    assert (b.work, b.date, b.memorandum) == ("M/H NIE 11-5-58", date(1958, 11, 25), True)
    c = parse_separate_name("NIE_11-8-61_1961-06-07_Long_Range_Attack_Annex_C.pdf")
    assert (c.work, c.part) == ("NIE 11-8-61", "annex-c")
    d = parse_separate_name("NIE_11-8-60_1960-08-01_Long_Range_Attack_full.pdf")
    assert d.part == "" and d.title == "Long Range Attack"
    e = parse_separate_name("PFIAB_1990-02-15_The_Soviet_War_Scare_ISCAP-2013-015.pdf")
    assert (e.work, e.date, e.part) == (
        "PFIAB The Soviet War Scare",
        date(1990, 2, 15),
        "iscap-2013-015",
    )
    assert parse_separate_name("notes.pdf") is None


def test_contents_of_the_volume():
    estimates = [e for e in STEURY_1996 if not e.editorial]
    assert [e.no for e in estimates] == list(range(1, 42))
    starts = [e.start for e in STEURY_1996]
    assert starts == sorted(starts)
    for e in estimates:
        assert (e.date is None) == (e.basis == ""), e
        if e.date is not None:  # dated by the estimate, never by the volume
            assert e.date.year < 1990


# -- the corpus on a synthetic sample --------------------------------------------------------

FULL_TEXT = "\f".join(
    [
        "APPROVED FOR RELEASE DATE: 16-Jul-2011\nNATIONAL INTELLIGENCE ESTIMATE NUMBER 11-1-57\n"
        "SOVIET CAPABILITIES FOR MISSILE TESTING\nConcurred in by the Intelligence Advisory "
        "Committee on 1 March 1957.",
        "1. We estimate that the USSR will have ten test vehicles by mid-1958, and that the "
        "program has a very high priority.",
    ]
)
PFIAB_TEXT = (
    'The Soviet "War Scare"\nPresident\'s Foreign Intelligence Advisory Board\n'
    "February 15, 1990\nDECLASSIFIED IN PART PER E.O.13526\n"
    "In 1983 we may have inadvertently placed our relations with the Soviet Union on a hair "
    "trigger."
)


@pytest.fixture
def sample_corpus(tmp_path, monkeypatch):
    """A raw directory of fake PDFs whose bytes are their text pages (``pdf_pages`` is
    replaced: the parsing, splitting, dating and indexing are the corpus's own)."""
    monkeypatch.setattr(
        crest, "pdf_pages", lambda data, layout=False: data.decode("utf-8").split("\f")
    )
    corpus = CrestCorpus(tmp_path / "crest")
    corpus.contents = CONTENTS
    volume = "\f".join(_pages()).encode("utf-8")
    files = {
        "Steury1996_Part-I-Sample.pdf": volume,
        "Steury1996_Front-Matter-Sample.pdf": b"Foreword. This volume ...",
        "NIE_11-1-57_1957-03-01_Soviet_Capabilities_for_Missile_Testing_full.pdf": (
            FULL_TEXT.encode("utf-8")
        ),
        "PFIAB_1990-02-15_The_Soviet_War_Scare.pdf": PFIAB_TEXT.encode("utf-8"),
        "SNIE_11-9-84_1984-08-14_Soviet_Policy_Key_Judgments.pdf": b"\f \f\f",
    }
    for name, data in files.items():
        corpus.store_raw(name, data, f"https://example.org/{name}", fetched=date(2026, 10, 23))
    return corpus


def test_index_dates_marks_duplicates_and_skips_with_reasons(sample_corpus):
    n, skipped = build_index(sample_corpus)
    assert n == 3
    assert sample_corpus.check() == []
    docs = list(sample_corpus.iter_documents(until=date(1999, 12, 31)))
    by_id = {d.id: d for d in docs}
    assert set(by_id) == {
        "crest:NIE_11-1-57_1957-03-01@steury1996",
        "crest:NIE_11-1-57_1957-03-01",
        "crest:PFIAB_The_Soviet_War_Scare_1990-02-15",
    }
    vol = by_id["crest:NIE_11-1-57_1957-03-01@steury1996"]
    full = by_id["crest:NIE_11-1-57_1957-03-01"]
    assert vol.work == full.work == "NIE 11-1-57" and vol.work_key == full.work_key
    assert crest.works(docs) == {"NIE 11-1-57": sorted([full.id, vol.id])}
    assert vol.url == "https://example.org/Steury1996_Part-I-Sample.pdf#page=2"
    assert "vol. pp. 3-5" in vol.source
    assert {e.locator for e in sample_corpus.read_index()} == {"vol. pp. 3-5", "pp. 1-2", "pp. 1-1"}
    for d in docs:
        assert not any(p in d.text.lower() for p in EDITORIAL if p != "1996"), d.id
        assert "2011" not in d.text
    assert any("no. 2 SNIE 11-2-58" in s and "undated" in s for s in skipped)
    assert any(s.startswith("SNIE_11-9-84") and "no text layer" in s for s in skipped)
    assert any(s.startswith("Steury1996_Front-Matter") and "editorial" in s for s in skipped)
    index = json.loads(sample_corpus.index_path.read_text(encoding="utf-8"))
    assert index["source"] == "crest" and index["skipped"] == sorted(set(skipped))
    # open_corpus finds the source from the index.
    assert isinstance(open_corpus(sample_corpus.root), CrestCorpus)


def test_blind_reading_by_estimate_date(sample_corpus):
    build_index(sample_corpus)
    ids = [d.id for d in sample_corpus.iter_documents(until=date(1957, 2, 28))]
    assert ids == []
    ids = [d.id for d in sample_corpus.iter_documents(until=date(1989, 12, 31))]
    assert len(ids) == 2 and not any("PFIAB" in i for i in ids)  # the 1990 retrospective
    ids = [d.id for d in sample_corpus.iter_documents(until=date(1990, 2, 15))]
    assert any("PFIAB" in i for i in ids)


def test_check_catches_an_altered_raw_file(sample_corpus):
    build_index(sample_corpus)
    path = sample_corpus.root / "PFIAB_1990-02-15_The_Soviet_War_Scare.pdf"
    path.write_bytes(path.read_bytes() + b" ")
    assert any("checksum" in p for p in sample_corpus.check())


def test_a_misread_volume_is_an_error_not_a_silent_split(sample_corpus):
    pages = _pages()
    pages[1] = pages[1].replace("\n\n3", "\n\n2")
    pages[2] = pages[2].replace("\n\n4", "\n\n3")
    sample_corpus.store_raw("Steury1996_Part-I-Sample.pdf", "\f".join(pages).encode(), "u")
    with pytest.raises(CorpusError):
        build_index(sample_corpus)


def _rec(i, doc, work=None):
    rec = {
        "id": f"r{i}",
        "document": doc,
        "proposal": {"variable": "austria", "level": "annexed", "date": "1938-03-12"},
        "status": "pending",
        "decisions": [],
    }
    rec["proposal"]["quote"] = f"q{i}"
    if work:
        rec["work"] = work
    return rec


def test_two_document_rule_counts_one_estimate_held_twice_once():
    end = date(1938, 12, 31)
    same = [_rec(1, "crest:NIE_x@steury1996", "NIE x"), _rec(2, "crest:NIE_x", "NIE x")]
    g = gate_records(same, end, DEFAULT_RULES, measure=True)
    assert [x.status for x in g.gates] == [HELD, HELD]
    other = [*same, _rec(3, "crest:NIE_y", "NIE y")]
    g = gate_records(other, end, DEFAULT_RULES, measure=True)
    assert [x.status for x in g.gates] == [CORROBORATING, CORROBORATING, OK]
    # Without a work, distinct ids stay independent (FRUS and the other corpora).
    g = gate_records([_rec(1, "d1"), _rec(2, "d2")], end, DEFAULT_RULES, measure=True)
    assert [x.status for x in g.gates] == [CORROBORATING, OK]


# -- the real corpus -------------------------------------------------------------------------

_MONTHS = {
    m: i
    for i, m in enumerate(
        "January February March April May June July August September October November "
        "December".split(),
        start=1,
    )
}
_FULL_DATE = re.compile(r"\b(\d{1,2}) (" + "|".join(_MONTHS) + r"),? (19\d\d)\b")
# The editor's running head "6. (Continued)" as a line of its own.
_RUNNING_HEAD = re.compile(r"(?m)^\s*\S{0,4}\s*[\(\[/{f]?\s*C[o0][nmr]?[tr]?[il]nu?ed\W{0,3}$")
# Later dates a document legitimately names: a projection ("by 1 May 1960"), the completion
# of the concurrence after the cover date, and OCR misreadings of the year.
_LATER_OK = {
    ("crest:NIE_11-8-60_1960-08-01", "1980-08-01"),  # OCR of "1 August 1960"
}


@pytest.mark.slow
@pytest.mark.skipif(
    not (REAL / "MANIFEST.json").exists() or shutil.which("pdftotext") is None,
    reason="the CIA estimates corpus (data/cw/corpora/raw/crest) or pdftotext is not there",
)
def test_real_corpus(tmp_path):
    root = tmp_path / "crest"
    root.mkdir()
    for f in REAL.iterdir():
        if f.suffix.lower() == ".pdf":
            (root / f.name).symlink_to(f)
    shutil.copy(REAL / "MANIFEST.json", root / "MANIFEST.json")
    corpus = CrestCorpus(root)
    # The volume: 41 estimates in the contents; Parts I and II (estimates 1 to 26) carry a
    # text layer, Part III (27 to 41) and the whole-volume PDF are scanned images.
    found = []
    for f in sorted(root.glob("Steury1996_Part-*.pdf")):
        pages = crest.pdf_pages(f.read_bytes())
        if not has_text_layer(pages):
            continue
        split, problems = split_volume(pages, crest.pdf_pages(f.read_bytes(), layout=True))
        assert problems == []
        found += [v.entry.no for v in split]
    assert sorted(found) == list(range(1, 27))
    n, skipped = build_index(corpus)
    assert corpus.check() == []
    docs = list(corpus.iter_documents(until=date(2000, 1, 1)))
    assert len(docs) == n >= 25
    contents = {e.number: e for e in STEURY_1996 if not e.editorial}
    by_work: dict[str, set[date]] = {}
    for d in docs:
        assert isinstance(d.date, date) and d.work, d.id  # every document dated, its work named
        by_work.setdefault(d.work, set()).add(d.date)
        if d.id.endswith("@steury1996"):
            assert d.date == contents[d.work].date  # the estimate's date, not 1996
            low = d.text.lower()
            for phrase in EDITORIAL:
                assert phrase not in low, (d.id, phrase)
            assert not _RUNNING_HEAD.search(d.text), d.id
        assert "declassified" not in d.text.lower(), d.id
        assert not re.search(r"\d{1,2}-[A-Z][a-z]{2}-(?:19[9]\d|20\d\d)", d.text), d.id
        for m in _FULL_DATE.finditer(" ".join(d.text.split())):
            try:
                day = date(int(m.group(3)), _MONTHS[m.group(2)], int(m.group(1)))
            except ValueError:
                continue
            if day <= d.date or (d.id, day.isoformat()) in _LATER_OK:
                continue
            context = " ".join(d.text.split())
            before = context[max(0, m.start() - 12) : m.start()]
            # a projection, or the concurrence completed within days of the cover date
            assert "by " in before or (day - d.date).days <= 31, (d.id, day, before)
    # One estimate, one date, however many copies.
    assert all(len(days) == 1 for days in by_work.values()), by_work
    duplicated = crest.works(docs)
    assert {"NIE 11-5-58", "NIE 11-8-59", "NIE 11-8-60", "NIE 11-8-61"} <= set(duplicated)
    pfiab = [d for d in docs if d.work.startswith("PFIAB")]
    assert len(pfiab) == 2 and all(d.date == date(1990, 2, 15) for d in pfiab)
    no_text = {s.split(":")[0] for s in skipped if "no text layer" in s}
    assert "Steury1996_Intentions-and-Capabilities-1.pdf" in no_text
