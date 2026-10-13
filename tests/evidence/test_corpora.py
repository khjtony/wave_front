"""Corpus indices: the uniform Document, strict date filtering, the source formats (FRUS TEI,
Historic Hansard HTML, Chronicling America and Trove JSON) on small samples written in those
formats, the fetch step through a fake fetcher, index checks, and the synthetic fixtures."""

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from wavefront.evidence.corpora import (
    ChroniclingCorpus,
    CorpusError,
    FrusCorpus,
    HansardCorpus,
    LocalCorpus,
    TroveCorpus,
    chronicling,
    frus,
    hansard,
    open_corpus,
    trove,
)
from wavefront.evidence.corpora.local import SYNTHETIC_LINE
from wavefront.evidence.hindsight_ww2 import load_events

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "evidence" / "fixtures" / "corpus_synthetic"


class FakeFetcher:
    """Serves canned bodies by URL (or by a predicate) and records the requests."""

    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def __call__(self, url, headers=None):
        self.calls.append((url, headers))
        for key, body in self.pages.items():
            if (callable(key) and key(url)) or key == url:
                if isinstance(body, Exception):
                    raise body
                return body if isinstance(body, bytes) else body.encode("utf-8")
        raise OSError(f"404 for {url}")


# -- the synthetic fixture corpus ---------------------------------------------------------


def test_fixture_corpus_is_synthetic_and_labeled_in_every_file():
    files = sorted(FIXTURES.glob("*.txt"))
    assert 35 <= len(files) <= 45
    for f in files:
        assert f.read_text(encoding="utf-8").splitlines()[0] == SYNTHETIC_LINE
    corpus = LocalCorpus(FIXTURES)
    assert corpus.check() == []
    assert corpus.synthetic is True
    assert corpus.describe()["synthetic"] is True


def test_fixture_dates_match_the_dated_events():
    event_dates = {e.date for e in load_events()}
    docs = list(LocalCorpus(FIXTURES).iter_documents(until=date(1940, 12, 31)))
    assert len(docs) == len(list(FIXTURES.glob("*.txt")))
    for doc in docs:
        assert date(1936, 1, 1) <= doc.date <= date(1940, 12, 31)
        assert doc.date in event_dates, doc.id
        assert doc.url.startswith("synthetic:")
        assert "not a source" in doc.source


@pytest.mark.parametrize(
    "until, since",
    [
        (date(1936, 3, 7), None),
        (date(1938, 9, 29), None),
        (date(1938, 9, 30), None),
        (date(1939, 12, 31), date(1939, 9, 3)),
        (date(1935, 12, 31), None),
    ],
)
def test_iter_documents_filters_strictly_by_document_date(until, since):
    corpus = LocalCorpus(FIXTURES)
    every = list(corpus.iter_documents(until=date(2000, 1, 1)))
    got = list(corpus.iter_documents(until=until, since=since))
    expected = [d for d in every if d.date <= until and (since is None or d.date >= since)]
    assert got == expected
    assert [d.date for d in got] == sorted(d.date for d in got)


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_local_corpus_rejects_undated_mismatched_mixed_and_duplicate_files(tmp_path):
    _write(tmp_path / "a" / "x.txt", "title: no date\n\nbody\n")
    assert any("no date" in p for p in LocalCorpus(tmp_path / "a").check())
    _write(tmp_path / "b" / "1939-03-17_x.txt", "date: 1939-03-18\n\nbody\n")
    assert any("file name" in p for p in LocalCorpus(tmp_path / "b").check())
    _write(tmp_path / "c" / "1.txt", f"{SYNTHETIC_LINE}\ndate: 1939-03-18\n\nbody\n")
    _write(tmp_path / "c" / "2.txt", "date: 1939-03-18\n\nbody\n")
    assert any("mixes" in p for p in LocalCorpus(tmp_path / "c").check())
    _write(tmp_path / "d" / "1.txt", "id: same\ndate: 1939-03-18\n\nbody\n")
    _write(tmp_path / "d" / "2.txt", "id: same\ndate: 1939-03-19\n\nbody\n")
    assert any("duplicate" in p for p in LocalCorpus(tmp_path / "d").check())
    with pytest.raises(CorpusError):
        list(LocalCorpus(tmp_path / "d").iter_documents(until=date(1940, 1, 1)))


def test_local_corpus_defaults_and_real_files_are_not_synthetic(tmp_path):
    _write(tmp_path / "1939-03-18_note.txt", "date: 1939-03-18\n\nOne.\n\n\nTwo.\n")
    corpus = open_corpus(tmp_path)
    assert isinstance(corpus, LocalCorpus) and corpus.synthetic is False
    (doc,) = corpus.iter_documents(until=date(1939, 3, 18))
    assert doc.id == "1939-03-18_note" and doc.source == "local"
    assert doc.text == "One.\n\nTwo." and doc.url == "file:1939-03-18_note.txt"


# -- FRUS ------------------------------------------------------------------------------------

TEI_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xml:id="frus1939v01" xmlns="http://www.tei-c.org/ns/1.0"
     xmlns:frus="http://history.state.gov/frus/ns/1.0">
 <text><body>
  <div type="chapter" xml:id="ch1"><head>I. Sample chapter</head>
   <div frus:doc-dateTime-max="1939-03-19T12:00:00-05:00"
        frus:doc-dateTime-min="1939-03-19T12:00:00-05:00" n="50"
        subtype="historical-document" type="document" xml:id="d50">
    <note rend="inline" type="source">860F.48/52: Telegram</note>
    <head><hi rend="italic">The Minister in Czechoslovakia</hi> (<persName>Carr</persName>)
      to the Secretary of State</head>
    <opener><dateline><placeName>Praha</placeName>, <date calendar="gregorian"
      when="1939-03-19T18:00:00+01:00">March 19, 1939—6 p.m.</date><lb/>[Received March
      19—3 p.m.]</dateline></opener>
    <p>The Czechoslovak state <pb n="55"/> has ended.<note n="1" xml:id="d50fn1">An
      editor's footnote written decades later.</note> Arrests continue [sic].</p>
    <p>[Here follows text of a note handed over March 21, 1939, printed infra.]</p>
    <p>Sir: [Here follows review of the negotiations since March 3.] Second paragraph.</p>
    <closer><signed>Carr</signed></closer>
    <p>[In telegram No. 9, April 2, 1940, the Department replied:</p>
    <p>“The occupation was never recognized.” (860F.01/1)]</p>
   </div>
   <div subtype="editorial-note" type="document" xml:id="d51">
    <head>Editorial Note</head><p>Written by the editors.</p></div>
   <div frus:doc-dateTime-max="1939-08-24T23:59:59-04:00" n="52"
        subtype="historical-document" type="document" xml:id="d52">
    <head>Memorandum</head><p>Undated in its dateline, dated by the editors.</p></div>
   <div n="53" subtype="historical-document" type="document" xml:id="d53">
    <head>No date at all</head><p>Text.</p></div>
  </div>
 </body></text>
</TEI>
"""


def test_frus_parse_volume_dates_by_dateline_and_drops_notes_and_editorial_documents():
    docs, skipped = frus.parse_volume(TEI_SAMPLE.encode(), "frus1939v01")
    assert set(docs) == {"d50", "d52"}
    d = docs["d50"]
    assert d.id == "frus:frus1939v01/d50"
    assert d.date == date(1939, 3, 19)  # the writer's local date, not the normalized one
    assert d.url == "https://history.state.gov/historicaldocuments/frus1939v01/d50"
    assert d.title == "The Minister in Czechoslovakia (Carr) to the Secretary of State"
    assert "has ended. Arrests continue [sic]." in d.text  # a restoration is kept
    assert "footnote" not in d.text and "860F.48" not in d.text
    assert "[Received March 19—3 p.m.]" in d.text  # the receipt stamp is part of the document
    # The editors' bracketed insertions, single or across paragraphs, are left out.
    assert "Here follows" not in d.text and "1940" not in d.text and "recognized" not in d.text
    assert "Sir: Second paragraph." in d.text
    assert d.text.endswith("Carr")
    assert docs["d52"].date == date(1939, 8, 24)
    assert any("d51" in s and "editorial-note" in s for s in skipped)
    assert any("d53" in s and "undated" in s for s in skipped)


def test_frus_strip_editorial_insertions():
    strip = frus.strip_editorial
    assert strip("[Enclosure]\n\nText.") == "Text."
    assert strip("[Washington,] January 9, 1936.") == "[Washington,] January 9, 1936."
    assert strip("[Received November 14.]") == "[Received November 14.]"
    assert strip("Text [For text of treaty, signed later, see Treaty Series No. 930.] more.") == (
        "Text more."
    )
    assert strip("[An editorial bridge\n\nacross two paragraphs.]\n\nNext.") == "Next."
    # A bracket that never closes is not a span the filter can bound: kept.
    assert strip("[Unclosed\n\nText.") == "[Unclosed\n\nText."
    assert strip("It was [a conference among the other powers] held.") == (
        "It was [a conference among the other powers] held."
    )


def test_frus_mirror_url_pattern(tmp_path):
    assert frus.volume_url("frus1939v01") == (
        "https://raw.githubusercontent.com/HistoryAtState/frus/master/volumes/frus1939v01.xml"
    )
    pinned = "https://raw.githubusercontent.com/HistoryAtState/frus/abc123/volumes/{volume}.xml"
    url = frus.volume_url("frus1939v01", pinned)
    assert url.endswith("/abc123/volumes/frus1939v01.xml")
    with pytest.raises(CorpusError, match="placeholder"):
        frus.volume_url("frus1939v01", "https://example.org/volumes/")
    corpus = FrusCorpus(tmp_path / "frus")
    fetcher = FakeFetcher({url: TEI_SAMPLE})
    frus.fetch(
        corpus, ["frus1939v01"], since=None, until=date(1940, 1, 1), fetcher=fetcher, mirror=pinned
    )
    assert fetcher.calls[0][0] == url
    assert json.loads(corpus.manifest_path.read_text())["files"]["frus1939v01.xml"]["url"] == url


REAL_FRUS = ROOT / "data" / "ww2" / "corpora" / "raw" / "frus" / "frus1939v01.xml"


@pytest.mark.skipif(not REAL_FRUS.exists(), reason="the real FRUS volume is not fetched")
def test_frus_parser_on_the_real_volume_if_fetched():
    """On the real TEI (fetched with scripts/fetch_corpora.py; not committed): every
    historical document is dated by its dateline within a day of the editors' normalized
    range (time zones), and no editorial insertion is left in the text."""
    import xml.etree.ElementTree as ET

    data = REAL_FRUS.read_bytes()
    docs, skipped = frus.parse_volume(data, "frus1939v01")
    assert len(docs) > 1000 and not [s for s in skipped if "undated" in s]
    for div in ET.fromstring(data).iter(f"{frus.TEI}div"):
        doc = docs.get(div.get(frus.XML_ID) or "")
        if doc is None:
            continue
        lo = date.fromisoformat(div.get(f"{frus.FRUS}doc-dateTime-min", "")[:10])
        hi = date.fromisoformat(div.get(f"{frus.FRUS}doc-dateTime-max", "")[:10])
        assert (lo - doc.date).days <= 1 and (doc.date - hi).days <= 1, doc.id
        assert "[Here follow" not in doc.text and "printed supra" not in doc.text, doc.id


def test_frus_fetch_index_check_and_filtering(tmp_path):
    url = frus.volume_url("frus1939v01")
    fetcher = FakeFetcher({url: TEI_SAMPLE})
    corpus = FrusCorpus(tmp_path / "frus")
    n, skipped = frus.fetch(
        corpus,
        ["frus1939v01"],
        since=date(1939, 1, 1),
        until=date(1939, 12, 31),
        fetcher=fetcher,
    )
    assert n == 2 and len(skipped) == 2
    manifest = json.loads(corpus.manifest_path.read_text())["files"]["frus1939v01.xml"]
    assert manifest["url"] == url and manifest["bytes"] == len(TEI_SAMPLE.encode())
    assert len(manifest["sha256"]) == 64 and manifest["fetched"]
    assert corpus.check() == []
    assert [d.id for d in corpus.iter_documents(until=date(1939, 3, 31))] == [
        "frus:frus1939v01/d50"
    ]
    assert open_corpus(tmp_path / "frus").__class__ is FrusCorpus
    # Query terms filter the index; the raw volume is still recorded.
    n, _ = frus.fetch(
        corpus,
        ["frus1939v01"],
        since=None,
        until=date(1939, 12, 31),
        terms=["memorandum"],
        fetcher=fetcher,
    )
    assert n == 1
    # Tampering with a raw file is caught without the network.
    (tmp_path / "frus" / "frus1939v01.xml").write_text(TEI_SAMPLE.replace("Arrests", "Arrestz"))
    assert any("checksum" in p for p in corpus.check())


# -- Historic Hansard -------------------------------------------------------------------------

SITTING = """<html><body><h1>Sitting of 31 March 1939</h1><ol>
<li><a href="/historic-hansard/commons/1939/mar/31/european-situation">EUROPEAN SITUATION.</a></li>
<li><a href="/historic-hansard/commons/1939/mar/31/supply">SUPPLY.</a></li>
<li><a href="/historic-hansard/lords/1939/mar/31/foreign-affairs">FOREIGN AFFAIRS.</a></li>
<li><a href="/historic-hansard/people/mr-neville-chamberlain">Mr Chamberlain</a></li>
</ol></body></html>"""

SECTION = """<html><head><title>EUROPEAN SITUATION. (Hansard, 31 March 1939)</title></head>
<body><div id="header"><h1 class="title">EUROPEAN SITUATION.</h1></div>
<div id="content">
<p class="procedural">2.52 p.m.</p>
<div class="hentry member_contribution" id="S5CV0345P0-1">
<cite class="member author entry-title"><a href="/historic-hansard/people/x">The PRIME
MINISTER (Mr. Chamberlain)</a></cite>
<blockquote class="contribution_text entry-content">
<a class="permalink column-permalink" href="#column_2415">2415</a>
<p>In the event of any action which clearly threatened Polish independence, His
Majesty's Government would feel themselves bound at once to lend the Polish
Government all support in their power.<p>They stand in the same position.</p>
</blockquote></div></div></body></html>"""

SUPPLY = (
    SECTION.replace("EUROPEAN SITUATION.", "SUPPLY.")
    .replace("Polish independence", "the estimates")
    .replace("Polish\nGovernment", "Committee")
)


def test_hansard_links_and_section_parsing():
    links = hansard.section_links(SITTING)
    assert links == [
        f"{hansard.BASE}/commons/1939/mar/31/european-situation",
        f"{hansard.BASE}/commons/1939/mar/31/supply",
        f"{hansard.BASE}/lords/1939/mar/31/foreign-affairs",
    ]
    doc = hansard.parse_section(SECTION, links[0])
    assert doc.date == date(1939, 3, 31)
    assert doc.id == "hansard:commons/1939-03-31/european-situation"
    assert doc.title == "EUROPEAN SITUATION."
    assert doc.source == "Historic Hansard, HC Deb 31 March 1939"
    paragraphs = doc.text.split("\n\n")
    assert paragraphs[0] == "2.52 p.m."
    assert paragraphs[1].startswith("The PRIME MINISTER (Mr. Chamberlain): In the event")
    assert paragraphs[2] == "They stand in the same position."
    assert "2415" not in doc.text
    with pytest.raises(CorpusError, match="title dates it"):
        hansard.parse_section(SECTION, f"{hansard.BASE}/commons/1939/apr/01/european-situation")


def test_hansard_fetch_skips_days_without_sittings_and_unmatched_sections(tmp_path):
    fetcher = FakeFetcher(
        {
            hansard.sitting_url(date(1939, 3, 31)): SITTING,
            f"{hansard.BASE}/commons/1939/mar/31/european-situation": SECTION,
            f"{hansard.BASE}/commons/1939/mar/31/supply": SUPPLY,
        }
    )
    corpus = HansardCorpus(tmp_path / "hansard")
    n, skipped = hansard.fetch(
        corpus,
        since=date(1939, 3, 30),
        until=date(1939, 4, 1),
        terms=["Polish"],
        fetcher=fetcher,
    )
    assert n == 1
    assert sum("sittings/1939/mar/30" in s for s in skipped) == 1  # no sitting: a 404
    assert not any("lords" in url for url, _ in fetcher.calls)  # Commons only by default
    assert corpus.check() == []
    (doc,) = corpus.iter_documents(until=date(1939, 3, 31))
    assert "Polish independence" in doc.text
    assert list(corpus.iter_documents(until=date(1939, 3, 30))) == []


# -- Chronicling America ----------------------------------------------------------------------


def _ca_page(items, total, end):
    return json.dumps(
        {"totalItems": total, "endIndex": end, "startIndex": 1, "itemsPerPage": 2, "items": items}
    )


CA_ITEMS = [
    {
        "id": "/lccn/sn83045462/1939-03-18/ed-1/seq-1/",
        "date": "19390318",
        "title": "Evening star.",
        "sequence": 1,
        "ocr_eng": "CHAMBERLAIN WARNS HITLER\nBirmingham speech asks whether Germany\n"
        "seeks to dominate the world.",
    },
    {
        "id": "/lccn/sn83045462/1939-03-19/ed-1/seq-2/",
        "date": "19390319",
        "title": "Evening star.",
        "sequence": 2,
    },
]


def test_chronicling_parse_and_paged_fetch(tmp_path):
    docs, skipped, paging = chronicling.parse_results(_ca_page(CA_ITEMS, 3, 2).encode())
    (doc,) = docs.values()
    assert doc.date == date(1939, 3, 18)
    assert doc.id == "chronicling:lccn/sn83045462/1939-03-18/ed-1/seq-1"
    assert doc.url == "https://chroniclingamerica.loc.gov/lccn/sn83045462/1939-03-18/ed-1/seq-1/"
    assert doc.title == "Evening star., 1939-03-18, page 1"
    assert skipped == ["/lccn/sn83045462/1939-03-19/ed-1/seq-2/: no full text in the result"]
    assert paging == {"totalItems": 3, "endIndex": 2}
    third = {**CA_ITEMS[0], "id": "/lccn/sn1/1939-04-02/ed-1/seq-1/", "date": "19390402"}
    fetcher = FakeFetcher(
        {
            (lambda u: "page=1" in u): _ca_page(CA_ITEMS, 3, 2),
            (lambda u: "page=2" in u): _ca_page([third], 3, 3),
        }
    )
    corpus = ChroniclingCorpus(tmp_path / "chronicling")
    n, _ = chronicling.fetch(
        corpus, since=date(1939, 3, 1), until=date(1939, 3, 31), terms=["Hitler"], fetcher=fetcher
    )
    assert len(fetcher.calls) == 2 and "ortext=Hitler" in fetcher.calls[0][0]
    assert "date1=03%2F01%2F1939" in fetcher.calls[0][0]
    assert n == 1  # the April page is outside the range and is not indexed
    assert corpus.check() == []
    with pytest.raises(CorpusError, match="query terms"):
        chronicling.fetch(
            corpus, since=date(1939, 3, 1), until=date(1939, 3, 2), terms=[], fetcher=fetcher
        )


# -- Trove -----------------------------------------------------------------------------------

TROVE_V3 = {
    "category": [
        {
            "code": "newspaper",
            "records": {
                "s": "*",
                "n": 2,
                "total": 2,
                "article": [
                    {
                        "id": "17567890",
                        "heading": "MR. CHAMBERLAIN'S SPEECH",
                        "title": {
                            "id": "35",
                            "title": "The Sydney Morning Herald (NSW : 1842 - 1954)",
                        },
                        "date": "1939-03-18",
                        "troveUrl": "https://nla.gov.au/nla.news-article17567890",
                        "articleText": "<p>LONDON, March 17.</p>"
                        "<p>Mr. Chamberlain &amp; the Empire.</p>",
                    },
                    {"id": "17567891", "heading": "NO TEXT", "date": "1939-03-18"},
                ],
            },
        }
    ]
}


def test_trove_parse_v3_and_v2_and_fetch_keeps_the_key_out_of_the_manifest(tmp_path):
    docs, skipped, nxt = trove.parse_results(json.dumps(TROVE_V3).encode())
    doc = docs["17567890"]
    assert doc.text == "LONDON, March 17.\n\nMr. Chamberlain & the Empire."
    assert doc.source == "Trove, The Sydney Morning Herald (NSW : 1842 - 1954)"
    assert doc.date == date(1939, 3, 18) and doc.id == "trove:17567890"
    assert skipped == ["17567891: no article text in the result"] and nxt is None
    v2 = {
        "response": {"zone": [{"name": "newspaper", "records": TROVE_V3["category"][0]["records"]}]}
    }
    assert set(trove.parse_results(json.dumps(v2).encode())[0]) == {"17567890"}
    with pytest.raises(CorpusError):
        trove.parse_results(b'{"category": []}')
    fetcher = FakeFetcher({(lambda u: True): json.dumps(TROVE_V3)})
    corpus = TroveCorpus(tmp_path / "trove")
    with pytest.raises(CorpusError, match="API key"):
        trove.fetch(
            corpus,
            since=date(1939, 3, 1),
            until=date(1939, 3, 31),
            terms=["Hitler"],
            api_key="",
            fetcher=fetcher,
        )
    n, _ = trove.fetch(
        corpus,
        since=date(1939, 3, 1),
        until=date(1939, 3, 31),
        terms=["Chamberlain"],
        api_key="SECRET",
        fetcher=fetcher,
    )
    assert n == 1
    assert fetcher.calls[0][1] == {"X-API-KEY": "SECRET"}
    assert "SECRET" not in corpus.manifest_path.read_text()
    assert "SECRET" not in corpus.index_path.read_text()
    assert corpus.check() == []


# -- the fetch script ------------------------------------------------------------------------


def test_fetch_script_check_validates_indexes_without_network(tmp_path):
    corpus = FrusCorpus(tmp_path / "frus")
    frus.fetch(
        corpus,
        ["frus1939v01"],
        since=None,
        until=date(1940, 1, 1),
        fetcher=FakeFetcher({frus.volume_url("frus1939v01"): TEI_SAMPLE}),
    )
    script = ROOT / "scripts" / "fetch_corpora.py"
    ok = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert ok.returncode == 0, ok.stderr
    assert "frus: index valid (2 documents)" in ok.stdout
    assert "hansard: no index" in ok.stdout
    (tmp_path / "frus" / "frus1939v01.xml").unlink()
    bad = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path), "--check", "frus"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert bad.returncode == 1 and "raw file missing" in bad.stdout


def test_raw_corpus_directory_is_git_ignored():
    assert "data/ww2/corpora/raw/" in (ROOT / ".gitignore").read_text().splitlines()
