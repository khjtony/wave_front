# Replay corpora (WW2)

The dated documents the blind replay reads ([docs/ww2_testbed.md](../../../docs/ww2_testbed.md)
section 6.2, [docs/replay_harness.md](../../../docs/replay_harness.md)). Nothing here is
committed except this file and `frus/MANIFEST.json` (see below): `scripts/fetch_corpora.py`
writes the raw pages it downloads into `data/ww2/corpora/raw/<source>/` (git-ignored), with

- `MANIFEST.json`: one entry per raw file with its URL, fetch date, size in bytes and SHA-256;
- `index.json`: the admissible documents found in those files (id, document date, title,
  reading URL, raw file, locator inside it) and the items skipped with the reason.

The index never holds text: reading a document parses its raw file again, and
`python3 scripts/fetch_corpora.py --check` validates every index against its manifest and
files without the network (sizes, checksums, every entry parsed with the date the index
gives).

## Blocked hosts

The corpus hosts (history.state.gov, api.parliament.uk, chroniclingamerica.loc.gov and
www.loc.gov, api.trove.nla.gov.au) are blocked from the development environment by policy
(docs/phase2_kickoff.md). The parsers are written against the published formats and tested on
small samples written in those formats (tests/evidence/test_corpora.py). The fetch is run on
the owner's machine.

One exception was observed on 2026-10-13: the FRUS TEI mirror on raw.githubusercontent.com is
reachable from the development environment. The twelve volumes of the real FRUS baseline
([reports/replay_ww2_frus.md](../../../reports/replay_ww2_frus.md)) were fetched from it at
commit `99d851c79a570dcd1a6594981600eaa2515c5bef` of `HistoryAtState/frus` (URL pattern
`https://raw.githubusercontent.com/HistoryAtState/frus/<commit>/volumes/{volume}.xml`, given to the
fetch script with `--mirror`): 68 MB, 10,550 documents dated 1936 to 1940.

`frus/MANIFEST.json` is a copy of the manifest of that fetch (URL, fetch date, size and
SHA-256 of each volume), committed as the record of what the report read. The raw volumes and
the index (2.9 MB) are not committed; rebuild them with the command in
[docs/replay_harness.md](../../../docs/replay_harness.md), section "Real FRUS baseline", and
check that the SHA-256 values in `raw/frus/MANIFEST.json` equal the committed ones.

## Sources

| Source | What it provides | Dated by | Format read | Terms of use (verify before a run) |
|---|---|---|---|---|
| `frus`: Foreign Relations of the United States | US diplomatic documents (telegrams, memoranda, notes), one TEI XML file per volume; default volumes: 1936 to 1940 v01 to v05, Japan 1931 to 1941 v01 and v02 | the document's dateline (`<date when>`, local time); else the editors' `frus:doc-dateTime-max` | TEI from the `HistoryAtState/frus` repository (`volumes/<id>.xml`; `--mirror` sets the URL pattern, for example to pin a commit); editorial notes, every `<note>` (the editors' later footnotes) and the editors' bracketed insertions in the text are excluded | a work of the US government, in the public domain in the United States; the repository states its own licence |
| `hansard`: Historic Hansard | UK parliamentary debates, one page per debate section; Commons by default | the sitting day in the URL, cross-checked against the page title | static HTML: sitting-day pages and section pages (`member_contribution`, `contribution_text`, `procedural`) | Parliamentary copyright, reusable under the Open Parliament Licence; crawl politely (the script waits 1 s between requests) |
| `chronicling`: Chronicling America (Library of Congress) | US newspaper pages to 1963 with full OCR text | the issue date | the classic search JSON (`/search/pages/results/?format=json`, `items[].ocr_eng`) | the Library of Congress's rights statement for the collection (rights can differ by title for pages after 1926); no key; observe the published rate limits |
| `trove`: Trove (National Library of Australia) | Australian newspaper articles, the Empire press, with article text | the article's issue date | API v3 JSON (`category[].records.article[]` with `articleText`); v2 responses are also read | an API key (set `TROVE_API_KEY`) under the Trove API terms (non-commercial use, attribution, rate limits); the key is never written to the manifest or the index |

Notes:

- **Chronicling America** is moving to the loc.gov API, whose search results carry snippets,
  not page text. The module reads the classic format only and skips a result without
  `ocr_eng` rather than index partial text. Check which API is live before fetching.
- **Hansard**: the Official Report of a sitting appeared the next morning; the replay dates
  the debate by its sitting day, which a quarterly replay does not distinguish.
- **Excluded**: encyclopedias and later histories (ww2_testbed.md section 6.2). Documents on
  German Foreign Policy, the Nuremberg documents (Avalon Project), the 1941 Imperial
  Conference records and the Cabinet papers are admissible by their original dates but have
  no fetch module yet; they can be added as a dated text directory (the `local` corpus
  format) after a manual collection.

## Commands

```
python3 scripts/fetch_corpora.py frus --since 1936-01-01 --until 1940-12-31
python3 scripts/fetch_corpora.py hansard --since 1939-03-01 --until 1939-04-30 --terms Poland,Germany
python3 scripts/fetch_corpora.py chronicling --since 1939-03-01 --until 1939-03-31 --terms Hitler,Danzig
TROVE_API_KEY=... python3 scripts/fetch_corpora.py trove --since 1939-03-01 --until 1939-03-31
python3 scripts/fetch_corpora.py --check
```

Without `--terms`, FRUS and Hansard index every document of the range and the newspaper
sources use the default query terms in the script (the crises of 1936 to 1940).
