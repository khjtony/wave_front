# The replay harness

Phase 2 decision D3 ([phase2_kickoff.md](phase2_kickoff.md)); the contract is
[ww2_testbed.md](ww2_testbed.md) sections 6.2, 8 and 9 and the evidence pipeline of
[DESIGN.md](DESIGN.md) section 5.3: extract into a fixed schema, review by a human, and
nothing changes a snapshot without review.

## Layers

```
corpus (dated documents)          wavefront/evidence/corpora/
   | iter_documents(until, since)   strict filter by the document's own date
extractor + backend               wavefront/evidence/extract/
   | proposals (fixed schema)       checked: level, date <= document date, verbatim quote
proposals file                    <dir>/proposals/<label>.json
   | harness rules                  two-document, no-retrospective (wavefront/evidence/harness_rules.py)
   | wf review --accept/--reject    a note for every decision; history kept
replay snapshot                   <dir>/<label>.json   (written only by review.py)
   | compare with hindsight         wavefront/evidence/replay.py
metrics report (Markdown)
```

### Corpora

Every source yields `Document(id, date, source, title, text, url)`, and
`iter_documents(until, since=None)` returns only documents dated in `[since, until]`, in date
order. The published sources (`frus`, `hansard`, `chronicling`, `trove`) are indexed corpora:
a fetch step writes raw pages to `data/ww2/corpora/raw/<source>/` with a manifest (URL, fetch
date, size, SHA-256) and an index; reading a document parses its raw file again, and the
index date must equal the parsed date. `local` reads a directory of dated text files (a
`key: value` header with at least `date`, a blank line, the body). See
[data/ww2/corpora/README.md](../data/ww2/corpora/README.md) for formats, terms of use and the
blocked-host note.

Blindness at this layer: undated documents never enter an index; FRUS editorial notes and the
editors' footnotes (written decades later) are excluded from the text, and so are the editors'
bracketed insertions in the running text (summaries of omitted passages, cross-references,
narrative bridges that quote later telegrams; `frus.strip_editorial`); a document is filtered
on its index date before it is parsed.

**CIA estimates (`crest`, Cold War).** `data/cw/corpora/raw/crest/` holds the Steury (1996)
volume of 41 estimates on Soviet strategic forces (whole and in parts) and estimates fetched
one by one from the CIA reading room, as PDFs with a hand-written manifest; there is no fetch
step: `python3 scripts/fetch_corpora.py crest` indexes the files on disk (it needs `pdftotext`)
and `--check crest` validates the index. The volume is split into one document per estimate by
its table of contents (`crest.STEURY_1996`) and the printed page numbers; the editor's
introductions and section essays, the headings and running heads the editor set on the
estimates' pages, the 1996 front matter and afterword, and every declassification stamp
("APPROVED FOR RELEASE", "RELEASE DATE: 16-Jul-2011") are left out of the text. Each document
is dated by its estimate's own date, never by 1996: a separately fetched file by the date in its
name, an estimate of the volume by the date `STEURY_1996` records with where it is printed;
the volume prints no date with most of its facsimiles, and an estimate without a recorded date
is undated and not indexed (listed under `skipped` in `index.json`, as are the PDFs without a
text layer). The PFIAB report "The Soviet War Scare" is dated 15 February 1990 and is
invisible to any replay before then. An estimate held twice (the volume's extract and the full
text, or two parts or copies) is one document per file with the same `work`, the estimate's
number, and the two-document rule counts it once (see Harness rules).

### Extraction

The fixed proposal schema (`extract/schema.py`): `indicator_id`, `variable`, `level`, `date`,
`quote`, `url`, `rule`, `confidence`. The variables read from text are `belief_WEST`,
`belief_GER`, `commit_WEST`, `commit_US`, `treaty`, the section 4 flags (pacts and structural
flags), `war_west_ger`, the regions and `oil_GER`; the resource variables (`arms_*`,
`ind_GER`) come from the datasets and are copied from the hindsight snapshot of the quarter,
never extracted. Each variable's levels and threshold text are read from
[ontology_ww2.md](ontology_ww2.md).

A backend implements `propose(document, variables) -> list[Proposal]`. The extractor checks
every proposal of every backend and keeps a failing one under `discarded` with its reasons:
an unknown variable or level, a date after the document's date (a document cannot observe its
future), a quote that is not verbatim in the document, an empty field or an unknown
confidence. Backend errors are recorded per document; the replay stops on any, because a
quarter with a failed document would have incomplete proposals.

**Rule backend** (`extract/rules.py`): keyword rules over sentences, one table row per level,
with keywords taken from the ontology's threshold text and the section cited in each rule;
per variable the most specific level is tried first and the first rule that fires gives the
document's one proposal for that variable. Date rule: the document's date, or a full date the
sentence names within the 31 days before it, or the day before for "yesterday". What it
handles: the period wording of the synthetic fixtures, explicit treaty, annexation and
declaration events, named legislation (the Neutrality Acts, conscription), and the belief
phrases the ontology cites (Birmingham, the Obersalzberg address). What it cannot do: tell who
is speaking or about whom beyond its keyword pairs, read negation, modality or hypotheticals
beyond a few exclusions, combine sentences, or know the current level (a warning during a war
reads as `uncertain` even when belief is already `hegemonic`). It is a baseline that makes the
pipeline testable, not a reader of real corpora.

**Claude backend** (`extract/claude_backend.py`), written to the Claude API reference bundled
with the Claude Code `claude-api` skill:

- The `anthropic` SDK is the optional extra `extract` (`pip install -e '.[extract]'`) and is
  imported lazily on the first request; the zero-argument client resolves credentials from
  the environment (reference: Defaults; Python README, Client Initialization).
- One `client.beta.messages.create` request per part of a document, with the default model
  (`DEFAULT_MODEL` in the module; configurable with `--model`), no `thinking` parameter so the
  model runs adaptive thinking by omission (reference: Thinking and Effort quick reference),
  an explicit `output_config.effort` (`high`; the model's own default is lower), and
  structured outputs through `output_config.format` with a JSON schema of `{"proposals": [...]}`
  (Python `tool-use.md`, Structured Outputs, Raw Schema). The levels are strings in the schema
  and are converted to the variable's levels afterwards.
- The server-side refusal fallback is opted in with `fallbacks="default"` and the beta
  `server-side-fallback-2026-07-01` (reference: the `refusal` stop reason and the `"default"`
  form; Python README, Refusal Fallbacks, for the beta call shape).
- `stop_reason` is checked before the content: `refusal` raises `ExtractionRefused` with its
  category; `max_tokens` splits the part in two and reads both halves (Stop Reasons).
- Errors are caught most specific first: `BadRequestError`, `AuthenticationError`,
  `PermissionDeniedError`, `NotFoundError`, `RateLimitError` (with `retry-after`),
  `APIStatusError` (5xx retryable), `APIConnectionError` (Python README, Error Handling; the
  reference's Common Pitfalls on error chains). The SDK's own retries run first.
- No silent truncation: a document longer than `max_chars` (200,000 characters) is split at
  paragraph breaks (then sentences, then hard cuts inside a single over-long sentence) and the
  proposals of all parts are merged by (variable, level, date); a proposal whose quote is not
  in the document is never merged away, so the extractor discards it visibly (Common Pitfalls:
  do not truncate inputs).
- The system prompt (instructions and the threshold rules) is stable across documents and is
  marked for prompt caching; the `indicator_id` and `url` of every proposal are set from the
  document, not taken from the model.

Caveat for every real run with a language model: the model was trained on text written long
after 1940 and knows the outcome. The date filter, the verbatim-quote check and the
instruction to use only the document limit what it can contribute, but they do not make its
reading blind. The reviewer's decision is the safeguard, and a replay report from a model
backend says which model read the documents.

### Review

`wf review PROPOSALS` lists the proposals (status, variable and level, date, document, full
quote, rule). `--accept IDS` or `--reject IDS` with `--note` records a decision (reviewer
name from `--reviewer` or the login name; a decision can be changed later and every decision
is kept). After each decision `review.py` rebuilds the replay snapshots of the directory from
accepted proposals only: a snapshot is written for a proposals file only when it and every
earlier file have no pending proposal, and a stale one is removed. In a replay snapshot a text
variable takes the level of its latest accepted proposal, with the quote as `value`, the URL
as `source`, the observation date and the proposal's rule plus the decision as `rule`; a text
variable with no accepted proposal keeps the ontology's initial level as `assumed`; the
resource variables are copied from the hindsight snapshot and marked as copied. The
snapshots validate against `snapshots/schema.json` and the ontology.

Under the harness rules (next section) the listing puts the proposals the rules hold or block
after the proposals for review, under "not for review under the harness rules", flags a
`retrospective?` one, and gives the reason on a `harness:` line; `--accept` refuses a held or
blocked proposal, and a held or blocked proposal does not keep a snapshot from being written.

`--auto-accept` exists for the synthetic run only: it is refused unless the corpus is the
synthetic fixture corpus (every file carries the `SYNTHETIC FIXTURE` header), the reviewer
name it uses is reserved, and every indicator it produces says AUTO-ACCEPTED.

### Replay and metrics

`wf replay --corpus DIR --quarters 1936Q1..1940Q4 --out DIR [--auto-accept]`: for each
quarter, the corpus filtered to documents dated at or before the quarter's last day; the
documents not read at an earlier quarter go to the extractor (equivalent to re-reading the
whole filtered corpus, since a backend reads one document at a time, and each proposal is
reviewed once); proposals to `OUT/proposals/<quarter>.json`. Then the metrics of section 9,
written to `OUT/metrics.md` (or `--report`):

- per-variable agreement: the share of quarters whose replay level equals the hindsight level
  at the quarter's end, for the text-derived variables; the copied resource variables are
  shown but test nothing;
- flips: a change of level between consecutive quarter-end snapshots, dated by the indicator
  that set the new level; each documented flip is paired with the nearest replayed flip to
  the same level within four quarters, and the lag is given in quarters and days (positive:
  the replay is late); unpaired replayed flips are false flips, unpaired documented flips are
  missed. Both series start from the same baseline, the record's level at the end of the
  quarter before the first (its hindsight snapshot, else the initial levels), never the
  replay's own snapshot of that quarter, so a replay that agrees in every quarter has no false
  flip whatever `--quarters` starts with (fixed 2026-10-30; until then a measurement started
  the replay from the initial levels, which gave a false flip at the first quarter of a range
  starting after 1936Q1 for every variable already moved; every recorded WW2 report starts at
  1936Q1, where the two baselines are equal, and is unchanged). With set-valued hindsight
  levels, a replayed flip inside a window to a level of its set, or on the first concrete
  quarter after it back to that quarter's hindsight level, is a flip inside the window, not a
  false flip ([ambiguous_levels.md](ambiguous_levels.md) section 5);
- the disagreements, each with the hindsight event and the replay quote behind it.

`--metrics-only` recomputes the report from the snapshots already reviewed. It counts no
pending proposal: a quarter has a reviewed snapshot only when no proposal of it or of an earlier
quarter awaits review (see "Review"), and a quarter without one is listed as "not compared". A
review of a sample therefore leaves `--metrics-only` with nothing to compare; for a partly
reviewed run use `--measure-proposals --drop-rejected` (below).

`--measure-proposals` measures a backend before anyone has reviewed its proposals: every
proposal in `OUT/proposals/` counts as accepted, whatever its status (pending, accepted or
rejected), the quarter-end snapshots are built in memory with the same rules as the review
step (`replay.measured_snapshots`, which calls `review.build_snapshot`), and the same metrics
are computed. Nothing is written but the report, whose first line says that no proposal was
reviewed; it adds a table of proposals per variable and level. With `--corpus` the extraction
runs first (proposals only, as without the flag); without it the proposals already in `OUT` are
measured. It cannot be combined with `--auto-accept` or `--metrics-only`. It is a measurement
of the backend, not a replay snapshot: the review step stays human.

`--measure-proposals --drop-rejected` measures a partly reviewed run (added 2026-10-27 for the
owner's decision 7a of 2026-10-23, the review of a sample of the Claude backend's FRUS
proposals): the proposals a reviewer rejected are left out as if never proposed (so a
rejected document is not a proposing document under `two-document`, as in review), the
accepted and the pending proposals count as accepted, and a `retrospective?` proposal is
applied only if a reviewer accepted it (as in review; a plain measurement never applies it).
An accepted proposal keeps its reviewer's decision in its indicator; a pending one says NOT
REVIEWED. The report's first line gives the number of proposals accepted, rejected and still
pending, and its tables of proposals leave the rejected ones out. Nothing is written but the
report. It goes with proposals already written only (no `--corpus`), and the WW2 replay only.
With no decision recorded it gives exactly the metrics of `--measure-proposals`. Under it,
rejecting the proposal that set a level lets the next proposal of that level still in the run
set it: a false reading goes away only when every proposal carrying it is rejected.

Every report also gives the agreement of a replay that reads nothing (every text variable at
its ontology initial level), per variable and in total, and splits the replay's agreement
between the variable-quarters whose hindsight level is still the initial one and those where it
has moved: a backend that proposes nothing scores the first, and one that proposes every
event at once scores the second.

## Harness rules

Adopted by the owner on 2026-10-15 (decision 9), from the two harness changes the FRUS
baseline left for decision ([reports/replay_ww2_frus.md](../reports/replay_ww2_frus.md)). They
act in the replay and review layer (`wavefront/evidence/harness_rules.py`) on the proposals of
any backend; the rule backend's keyword table is not touched and stays the frozen baseline.

**Scope: the structural variables only.** Neither rule applies to `belief_WEST`, `belief_GER`,
`commit_WEST` or `commit_US` (`READINGS`, excluded by name): they are the variables the replay
exists to read, and applied to them the rules froze the first false reading of `belief_WEST`
and `commit_WEST` on FRUS (decision of 2026-10-15; the measurement of both variants is in the
FRUS report). A proposal for one of them is shown and counted as the backend made it.

**`two-document`.** A flip of a structural variable that changes once needs two independent
documents before it is shown as a proposal for review or counted by `--measure-proposals`.
"Changes once" is every flag and every variable the model declares monotone, less the belief
and commitment variables (`ONCE`; the list of v0's monotone variables, `V0_MONOTONE`, is kept
equal by a test to the `monotone=True` declarations of `models/ww2/v0.py`, the model the replay
snapshots are for, so a change in the model is caught): the pacts and structural flags (with
`italy_estranged`, a flag that is not monotone), the regions except `rhineland`,
`war_west_ger` and `oil_GER`. Not under the rule: `treaty`, `rhineland`, and the four belief
and commitment variables. A flip is a proposal whose level differs from the variable's current
level in the replay; "independent" means a different document id, or a different `work` where
the corpus records one (`crest`: one estimate in the volume and as a full text is one work), so
a document printed in two FRUS volumes under two ids still counts twice (the baseline report
lists such near-duplicates). Both documents are dated at or before the quarter, because a quarter's proposals come only from
documents dated up to its end. The first proposal is *held*: not shown for review, not
acceptable, not counted. The proposal of the second document carries the flip, so the flip
enters the quarter of that document and is dated by it; the first is then shown with it as
*corroborating* and never sets the level by itself. Later proposals of the same level are
shown as usual. In review a rejected proposal does not count as a proposing document.

**`no-retrospective`.** A proposal that would move a variable back to an earlier level (a
retrospective reading) is, for a monotone structural variable (`MONOTONE`), never applied
(*blocked*: listed apart, not acceptable, not counted); for the other structural variables
(`treaty`, `rhineland`, `italy_estranged`) it is shown flagged `retrospective?` and never
applied automatically: the measurement does not count it, `--auto-accept` rejects it with a
note that says why, and only a reviewer's acceptance applies it. "Back" means, for a monotone
variable, a level below the current one in the level order; for any other variable, a level the
variable has held earlier in the replay (its initial level included) and has since left (so
`treaty` moving from `eroded` to `enforced` is a flip, and back from `dead` to `eroded` is
flagged).

**The current level** is the replay's own level just before the proposal's date, the proposals
taken in date order with file order breaking ties: in review, the level set by the accepted
proposals in force; in a measurement or an auto-accepted run, the level set by every proposal in
force. So the rules make a level sticky once it is in force: a false flip that two documents
support is not undone by a later correct reading of a monotone variable, and the reviewer, not
the rules, is the safeguard against it.

**Switching.** `--rules two-document,no-retrospective` (the default), `--rules two-document`,
`--rules no-retrospective` or `--rules none` on `wf replay` and `wf extract`. The rules are
recorded in each proposals file (`harness_rules`; a file written before 2026-10-15 has none and
reads as the default), `wf review` uses the recorded rules (the files of a directory must
agree), and `wf replay --measure-proposals --rules ...` on proposals already written replaces
the recorded rules for that measurement only, which is how the same proposals are measured with
the rules on and off. Every generated report states the rules in force on its "Harness rules in
force" line, and a measurement under the rules adds a table of what they did (proposals shown
and counted, held, first of two documents, blocked, `retrospective?`).

**On the fixtures.** `tests/evidence/fixtures/corpus_rules/` holds ten synthetic documents,
one case per rule: a single document on the Marco Polo Bridge (held: `china_war` never flips),
two documents on the Anschluss in 1938Q1 and 1938Q2 (`austria` flips in 1938Q2, dated by the
second), two documents on the partition of Poland followed by a 1940 recollection of the German
attack (`poland` back from `partitioned` to `german`: blocked), the remilitarization of the
Rhineland followed by a 1937 recollection of the demilitarized zone, which the fake Claude
backend of the tests reads as `demilitarized` (`rhineland` back to its initial level:
`retrospective?`; the rule backend proposes nothing there), and the conference of 23 May and
the Obersalzberg address (`belief_GER` back to its initial level: outside the rules, counted
as made). `tests/evidence/test_harness_rules.py` runs them through the measurement (each rule
on, off and alone), the review step, auto-accept, and the Claude backend with a fake client.
The synthetic run corpus has one document per event, so with the rules on many of its flips
are held (agreement 381/500, 76 percent, against 488/500 with the rules off); its committed
report is the mechanics run with `--rules none`.

## Running on the owner's machine

```
pip install -e '.[extract]'                      # only for the Claude backend
python3 scripts/fetch_corpora.py frus --since 1936-01-01 --until 1940-12-31  # [--mirror PATTERN]
python3 scripts/fetch_corpora.py hansard --since 1936-01-01 --until 1940-12-31 --terms Germany
python3 scripts/fetch_corpora.py --check
wf replay --corpus data/ww2/corpora/raw/frus --quarters 1936Q1..1940Q4 \
    --out snapshots/ww2/replay --backend claude  # writes proposals only
wf review snapshots/ww2/replay/proposals/1936Q1.json
wf review snapshots/ww2/replay/proposals/1936Q1.json --accept 1936Q1-001,1936Q1-003 --note "..."
wf review snapshots/ww2/replay/proposals/1936Q1.json --reject 1936Q1-002 --note "..."
wf replay --quarters 1936Q1..1940Q4 --out snapshots/ww2/replay --metrics-only \
    --report reports/replay_ww2.md
```

One corpus directory is replayed at a time. To replay several sources together, run the
replay per source into the same `--out` in date order, or collect the documents into one
`local` directory.

## The synthetic run

`tests/evidence/fixtures/corpus_synthetic/` holds forty short documents written for the tests,
one for each date of `data/ww2/events_ww2.csv` from 1936 to 1940, each a period-style summary of
the event of that date. Every file starts with `SYNTHETIC FIXTURE: written for pipeline tests,
not a source`; they are not evidence and are never cited as such.

```
wf replay --corpus tests/evidence/fixtures/corpus_synthetic --quarters 1936Q1..1940Q4 \
    --out <scratch> --auto-accept --rules none --report reports/replay_ww2_synthetic.md \
    --title "Replay metrics on the synthetic fixture corpus, WW2 1936Q1 to 1940Q4"
```

What it proves: the date filter (each quarter reads only documents dated up to its end, each
once), extraction into the fixed schema with every proposal passing the checks, the review
gate (auto-accept only on synthetic fixtures, flagged), snapshot construction with provenance,
and the agreement, lag and false-flip metrics against the hindsight snapshots. What it does
not prove: anything about extraction from real documents. The fixtures summarize the same
dated events the hindsight snapshots are built from, and the rule keywords were written
alongside the fixtures, so agreement is high by construction.

The result ([reports/replay_ww2_synthetic.md](../reports/replay_ww2_synthetic.md)): 98 percent
agreement over the 500 text-derived variable-quarters; every documented flip replayed in its
quarter, except one; two false flips. The disagreements show where the
rule backend, following the ontology's threshold text, and the events file part ways:

- `belief_WEST` reads `uncertain` from 1939Q3: the 1 September 1939 fixture reports the
  British and French warnings in Berlin, and the ontology's `uncertain` rule names warnings.
  A keyword reader does not know that belief was already `hegemonic`; a reviewer would reject
  the proposal.
- `belief_GER` stays `will_not_fight` from the Obersalzberg address (22 August 1939), while
  the hindsight snapshot reads `will_fight` from the declarations of war on 3 September. The
  events file reads that level from observed resolve ("not a reported belief"); the
  ontology's threshold text asks for a German record that treats war with the West as the
  consequence of the next step, which no fixture of 3 September contains. This is a question
  for the historian about the rule, not a defect of the harness.

### Rule edits after the first synthetic run (logged)

The rule table was written from the ontology before the first run. After the first run on the
fixtures, five rules were corrected for defects that do not depend on the hindsight levels
(each made a rule fire on a sentence about something else):

1. `commit_WEST.resolved` fired on US peacetime conscription (the destroyers-for-bases
   fixture): it now requires a British or French subject.
2. `anglo_soviet_alliance.false` fired on the Molotov talks in Berlin: it now requires a
   British, French or Anglo party.
3. `ussr_axis.false` fired on the Moscow military talks of August 1939: it now requires Berlin
   or the Three-Power Pact.
4. `poland.german` fired on the plan to attack Poland (the conference of 23 May 1939): it now
   requires a past-tense verb of an event (attacked, invaded, bombed, crossed).
5. `britain.negotiated` fired on the French armistice: it now requires a British subject.

The misreadings that follow from what a keyword reader cannot do (the two above) were left
in place.

## Real FRUS baseline

The first blind replay on real documents: the rule backend over the FRUS volumes for 1936 to
1940 that cover Germany, Britain, France, the USSR, Italy, Czechoslovakia and Poland, measured
at the proposal level. Result and failure analysis:
[reports/replay_ww2_frus.md](../reports/replay_ww2_frus.md). It is the baseline the Claude
backend is measured against; the rules were frozen for it (rule changes it suggests are listed
in the report, not applied).

Reproduce (about 30 s to fetch 68 MB, 40 s to replay):

```
python3 scripts/fetch_corpora.py frus --since 1936-01-01 --until 1940-12-31 \
    --volumes frus1936v01,frus1936v02,frus1937v01,frus1937v02,frus1938v01,frus1938v02,frus1939v01,frus1939v02,frus1940v01,frus1940v02,frus1940v03,frus1933-39 \
    --mirror 'https://raw.githubusercontent.com/HistoryAtState/frus/99d851c79a570dcd1a6594981600eaa2515c5bef/volumes/{volume}.xml'
python3 scripts/fetch_corpora.py --check frus     # 10550 documents
wf replay --corpus data/ww2/corpora/raw/frus --quarters 1936Q1..1940Q4 --out <scratch> \
    --measure-proposals --rules none --report <scratch>/metrics.md \
    --title "Replay metrics, FRUS 1936 to 1940, rule backend, proposal level"
wf replay --out <scratch> --quarters 1936Q1..1940Q4 --measure-proposals \
    --report <scratch>/metrics_rules.md \
    --title "Replay metrics, FRUS 1936 to 1940, rule backend, proposal level, harness rules on"
```

The baseline was measured before the harness rules existed, so its reproduction needs
`--rules none`; the second command measures the same proposals with the rules on (the report's
section "Harness rules adopted, 2026-10-15").

The mirror is the Office of the Historian's own TEI repository on GitHub (history.state.gov is
blocked here); the pattern pins commit `99d851c7`, and the SHA-256 of every volume used is in
[data/ww2/corpora/frus/MANIFEST.json](../data/ww2/corpora/frus/MANIFEST.json), a copy of the
manifest the fetch wrote (the raw files and the 2.9 MB index stay git-ignored under
`data/ww2/corpora/raw/frus/`; the commands above rebuild them, and a rebuild must reproduce
those checksums). The generated metrics section of the report is the `metrics.md` of the last
command, unedited. `wf replay` reads the documents quarter by quarter exactly as `wf extract
--since <previous quarter end + 1> --until <quarter end>` would, and writes one proposals file
per quarter, all pending.

What real documents changed in the harness: the editors' bracketed insertions (above) were
found in 917 of the 10,550 documents, 39 of them naming a later year than the document, and
are now left out of the text; the `--mirror` option of the fetch script; the proposal-level
mode and the reading-nothing baseline. The TEI parser otherwise held: every document dated by
its dateline (10,205 in the opener, 345 in the closer or the body), all within a day of the
editors' normalized range, no encoding problem, one editorial note skipped.

## Running the Claude backend on the real corpus

Decision 8 of 2026-10-15: the owner runs the Claude backend over the same FRUS corpus on their
own machine, with their API key, and sends the proposals back. Nothing below needs this
repository's environment; every step but 3 and 4 is free.

What runs: `wavefront/evidence/extract/claude_backend.py` with its defaults, which these
commands do not change: model `claude-opus-5-5` (`DEFAULT_MODEL`), effort `high`, adaptive
thinking, `max_tokens` 16,000, structured output to the proposal schema, the server-side refusal
fallback, the system prompt cached. One request per document (a document over 200,000
characters is read in parts: one in this corpus). The SDK reads the key from the environment
variable `ANTHROPIC_API_KEY` (it also accepts `ANTHROPIC_AUTH_TOKEN` or a profile from
`ant auth login`); never put the key in a file of the repository or in a command you send back.

```
# 0. Once: the SDK, and the key in the environment (the value is yours; it is never written).
pip install -e '.[extract]'
export ANTHROPIC_API_KEY=...            # in your shell only

# 1. The corpus, from the pinned mirror (skip the fetch if --check already passes).
python3 scripts/fetch_corpora.py frus --since 1936-01-01 --until 1940-12-31 \
    --volumes frus1936v01,frus1936v02,frus1937v01,frus1937v02,frus1938v01,frus1938v02,frus1939v01,frus1939v02,frus1940v01,frus1940v02,frus1940v03,frus1933-39 \
    --mirror 'https://raw.githubusercontent.com/HistoryAtState/frus/99d851c79a570dcd1a6594981600eaa2515c5bef/volumes/{volume}.xml'
python3 scripts/fetch_corpora.py --check frus     # 10550 documents; checksums as in data/ww2/corpora/frus/MANIFEST.json

# 2. What a run would send (free; nothing is sent or written).
OUT=~/wf_runs/frus_claude                          # outside the repository
wf replay --corpus data/ww2/corpora/raw/frus --quarters 1936Q1..1940Q4 --out $OUT \
    --backend claude --dry-run

# 3. Pilot: one quarter (320 documents, 3 percent of the corpus). The proposals file records
#    the tokens used ("backend": {"usage": ...}) and the cache hits.
wf replay --corpus data/ww2/corpora/raw/frus --quarters 1936Q1..1936Q1 --out $OUT \
    --backend claude --workers 4
python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['backend'])" $OUT/proposals/1936Q1.json

# 4. The rest. If it stops (network, rate limit, an interruption), run the same command again:
#    every document already answered is read from $OUT/cache/claude/ and not sent again.
wf replay --corpus data/ww2/corpora/raw/frus --quarters 1936Q2..1940Q4 --out $OUT \
    --backend claude --workers 4

# 5. The measurement (free): with the harness rules on (the default) and off, as for the baseline.
wf replay --out $OUT --quarters 1936Q1..1940Q4 --measure-proposals \
    --report $OUT/metrics_claude.md \
    --title "Replay metrics, FRUS 1936 to 1940, Claude backend, proposal level"
wf replay --out $OUT --quarters 1936Q1..1940Q4 --measure-proposals --rules none \
    --report $OUT/metrics_claude_rules_off.md \
    --title "Replay metrics, FRUS 1936 to 1940, Claude backend, proposal level, harness rules off"

# 6. The review (human, free, can wait): list, then accept or reject with a note.
wf review $OUT/proposals/1936Q1.json
wf review $OUT/proposals/1936Q1.json --accept 1936Q1-001,1936Q1-003 --note "..."
wf review $OUT/proposals/1936Q1.json --reject 1936Q1-002 --note "..."
wf replay --out $OUT --quarters 1936Q1..1940Q4 --metrics-only --report $OUT/metrics_reviewed.md
# With only a sample reviewed, --metrics-only has no snapshot to compare; measure without the
# rejected proposals instead (scripts/apply_review.py applies a filled review sheet to a copy of
# the proposals and runs both):
wf replay --out $OUT --quarters 1936Q1..1940Q4 --measure-proposals --drop-rejected \
    --report $OUT/metrics_partial.md
```

**What to send back:** the two reports of step 5 (`$OUT/metrics_claude.md`,
`$OUT/metrics_claude_rules_off.md`), the proposals directory `$OUT/proposals/` (twenty JSON
files: every proposal with its quote, the documents read, the discarded proposals with their
reasons, the backend errors, and per quarter the model, the tokens and the cache counts), the
output of `fetch_corpora.py --check frus`, and the commit of the repository the run used
(`git rev-parse HEAD`). The cache is not needed. If a quarter fails on a refusal ("the request
was declined", not retryable: running again asks again), send the error message as well.

**Resuming.** The answers are cached per document under `$OUT/cache/claude/`, keyed by the
model, the effort, the token and part limits, the system prompt with the ontology's threshold
rules, and the document's text; only complete answers are cached, never an error. Running the
same command again therefore sends only the documents not yet answered (`--dry-run` shows how
many are left: its "cached" column). The document's source, title and URL, which are sent with
its text, are not in the key (so the recorded runs' caches stay valid) but are recorded in each
entry: an entry answered under another header (a corrected `crest` title, another URL) is read
again (an entry from before 2026-10-30, without a header, is used as before). Keep `--model` and the repository's commit the same across
the resumed runs: a different model or a changed threshold rule reads every document again. A
quarter whose proposals carry a reviewer's decision is never replayed over (the replay refuses
instead of resetting the decisions), so start `--quarters` after the reviewed ones. `--workers`
sets how many documents are read at once (default 1); with a low rate limit a 429 surfaces as an
error after the SDK's own retries, and running again resumes.

**Cost, order of magnitude.** From the dry run of step 2 on this corpus (computed here, not on
the owner's machine):

| Quarter | Documents | Characters | Quarter | Documents | Characters |
|---|---|---|---|---|---|
| 1936Q1 | 320 | 892,763 | 1938Q3 | 508 | 1,255,652 |
| 1936Q2 | 266 | 803,937 | 1938Q4 | 475 | 1,192,121 |
| 1936Q3 | 532 | 1,189,967 | 1939Q1 | 385 | 938,914 |
| 1936Q4 | 506 | 1,175,680 | 1939Q2 | 437 | 1,080,498 |
| 1937Q1 | 430 | 1,073,509 | 1939Q3 | 682 | 1,356,684 |
| 1937Q2 | 454 | 1,126,700 | 1939Q4 | 776 | 1,459,335 |
| 1937Q3 | 495 | 1,272,486 | 1940Q1 | 452 | 1,263,065 |
| 1937Q4 | 444 | 1,265,183 | 1940Q2 | 937 | 1,638,654 |
| 1938Q1 | 518 | 1,578,001 | 1940Q3 | 702 | 1,531,071 |
| 1938Q2 | 505 | 1,364,406 | 1940Q4 | 726 | 1,542,941 |

10,550 documents, 10,551 requests, 25.0 million characters of document text. At a rough four
characters a token (a planning figure, not the API's count, which can differ by a third either
way): about 6.3 million tokens of document text and about 1.1 million of per-request headers (the
dry run allows 400 characters a request for the document's id, date, title and URL), plus the
system prompt (11,795 characters, about 2,950 tokens) on every request, 31 million tokens in
all, which the prompt cache serves at the cache-read price once written, as long as requests
keep coming less than five minutes apart. The output is
the JSON answer (`{"proposals": [...]}`; a proposal with its one-sentence quote and rule is
roughly 100 to 150 tokens, and most documents should have none or one) and the adaptive
thinking at effort `high`, which is billed as output and has no fixed size; it is the large
unknown and the pilot measures it.

Prices, from the Claude API reference bundled with the Claude Code `claude-api` skill (its model
table, cached 2026-10-06, and its prompt-caching notes; the `anthropic` SDK itself is not
installed in this environment, and the live pricing page should be checked before the run):
`claude-opus-5-5` costs $4 per million input tokens and $20 per million output tokens; cache
reads $0.20 per million, cache writes 1.25 times the input price for the five-minute TTL.
Hence, before thinking: document text and headers about $29, the cached system prompt about $6
(about $125 if it were never cached), the JSON answers about $20 to $35; each 1,000 thinking
tokens a request, on average, adds about 10.6 million output tokens, about $210. Order of
magnitude: one to a few hundred dollars for the whole corpus, dominated by thinking. The pilot
of step 3 reads 320 of the 10,551 requests: multiply its recorded `usage` by about 33 for the
whole run, and its wall-clock time by 33 divided by the `--workers` used.

## The DeepSeek backend

`wavefront/evidence/extract/deepseek_backend.py` (`--backend deepseek`, optional `--model`) reads
documents through DeepSeek's OpenAI-compatible chat API with the standard library; no extra
dependency. It sends the Claude backend's instructions and threshold rules followed by the
answer's JSON schema, in JSON mode (the API does not enforce a schema, so the extractor's checks
discard anything outside it, with the reason). Default model `deepseek-flash`
(`DEFAULT_DEEPSEEK_MODEL`, with the guidance `DEFAULT_GUIDANCE` adopted on 2026-10-24, the text of data/extract/deepseek_guidance_g2.txt; `--guidance-file` replaces it; the account listed `deepseek-v4-pro` and `deepseek-flash` on 2026-10-24); `--model deepseek-v4-pro` for the larger model. The key is
read from `DEEPSEEK_API_KEY`, the base URL from `DEEPSEEK_BASE_URL` (default
`https://api.deepseek.com`); never put either in a file of the repository. Long documents are
split as for Claude (parts of at most 120,000 characters; a part whose answer stops on
`length` is split again); `content_filter` is a refusal; HTTP 429, 5xx, network failures (a
response cut short, `http.client.HTTPException`, included) and an answer interrupted by the
provider (`finish_reason` `insufficient_system_resource`) are retried three times with a
doubling wait, 402 is reported as insufficient balance, and a body that is not UTF-8 or JSON is
an error; every failure is recorded against its document. An empty `--guidance-file` means no
guidance (as in `scripts/compare_backends.py`); no `--guidance-file` means the default. The
proposals file's `backend` records the guidance (`"default"`, `"none"`, or `"sha256:<hex>"` of
the file's text), the report's backend line names it, and the report's command line gives
`--guidance-file`. Usage
is recorded per quarter under the API's names (`prompt_tokens`, `completion_tokens`,
`prompt_cache_hit_tokens`, `prompt_cache_miss_tokens`, `reasoning_tokens`). Answers are
cached per document like Claude's, under an identity naming the base URL, model, limits, JSON
mode and system prompt, so the two backends never share cache entries. The same run as for
Claude, with `--backend deepseek` and a different `--out`, gives comparable metrics; a pilot
quarter first measures the cost.

## The Cold War episode

The harness reads one domain model at a time, named by an episode
(`wavefront/evidence/episodes.py`): `ww2` (the default; everything above) or `cw`, the Cold
War v1 model (`cw_v1`; [ontology_cw.md](ontology_cw.md); decisions D6 and D7 of
[cw_v0_decisions.md](cw_v0_decisions.md), kept in v1, and D9 of
[cw_v1_decisions.md](cw_v1_decisions.md)). Until 2026-10-28 the episode was for `cw_v0`, with
`belief_force_USA` on `nuke_USSR`'s scale; on the owner's decision 7g it moved to `cw_v1` and
the count scale before any replay under the new scale was run (v0's C6 stays as recorded). The episode is threaded through
`text_variables(episode=...)`, the system prompt, the harness rules, the review step, the
replay driver, its metrics and the CLI (`wf replay --episode cw`, `wf extract --episode cw`);
`wf review` reads it from the proposals file. With the default every WW2 output is unchanged:
the WW2 system prompt, its variables and the answer schema are byte-identical (a test pins
the prompt's SHA-256), so cached Claude answers stay valid.

**Variables.** The text-derived variables are the three beliefs of the ontology's section 3,
with the levels and initial levels of `models/cw/v1.py` (a test keeps them equal) and the
`Threshold rule` column of the ontology as their rule text:

| Variable | Levels | Initial (1 January 1947) |
|---|---|---|
| `belief_force_USA` | none, under_200, under_1000, over_1000 | none |
| `belief_USA_USSR` | status_quo, opportunist, expansionist | opportunist |
| `belief_USSR_USA` | status_quo, hostile, first_strike_intent | hostile |

`belief_force_USA` is the projected number of Soviet intercontinental delivery vehicles
(ICBM and SLBM launchers, heavy bombers) about two to three years after the estimate's date, in
the bands none, under 200, under 1,000 and 1,000 or more (the owner's decision 7g; ontology
section 3); its own rule states the bands, so no other variable's rule is appended to it (until
2026-10-28 it was on `nuke_USSR`'s scale and `nuke_USA`'s thresholds were appended). The
`Dated indicator` column (the record, read with hindsight) never enters the prompt, nor does the
hindsight counterpart `count_USSR`; a test checks that no NIE number, bomber or missile gap,
Norris, NSC-68, Novikov or RYAN appears in it.

**Prompt.** The WW2 instructions with two changes: the first sentence names "a model of the
Cold War between the United States and the Soviet Union, 1947 to 1991", and a paragraph before
the variables says that every variable is the belief of one named government, to be read from
that government's own estimate (an estimate that projects a force is evidence of the
estimating government's belief whether or not the force was built), and that a document of one
government reporting another's belief or fear is evidence of the reporting government's belief:
the other's reading is proposed only where the document reproduces that government's own
words. The initial levels are stated at 1 January 1947. The DeepSeek backend appends its schema
to the same prompt. The Cold War prompt is about 1,050 tokens.

**Periods.** The model ticks yearly, so the replay runs by year (`--years 1957..1962`, or a
comma-separated list); quarters are refused for this episode. The period `1958` is the state on
1 January 1958 (tick 11), read from the documents dated to 31 December 1957: "documents dated
before the snapshot's date" of D7. Its proposals file is `proposals/1958.json` (`until`
1957-12-31, `"episode": "cw"`); `wf extract --episode cw` needs `--until YYYY-12-31` for its
file to become a snapshot. A replay directory holds one episode.

**Harness rules.** All three variables are beliefs, which are outside both rules (as WW2's
belief and commitment variables), so the rules are recorded but act on nothing.

**Review and snapshots.** A Cold War replay snapshot `<year>.json` is dated 1 January, for
`cw_v1`: each belief takes the level of its latest accepted proposal (else its initial level,
`assumed`, as in WW2); every other variable, the rates and the built-ins (`nuke_USSR` and
`count_USSR` among them) are carried from `snapshots/cw_v1/hindsight/<year>.json` as
`assumed`, as in v1's manual replay: the estimate is `belief_force_USA`, and the hindsight force
stays the record's.

**Metrics** (`wavefront/evidence/replay_cw.py`). Per year, each replayed belief beside (1) its
hindsight truth from the hindsight snapshot (D6: `belief_force_USA` against the record's
`count_USSR`, the number of vehicles in being in the same bands, D9 of cw_v1_decisions.md;
`belief_USSR_USA` against `hostile`; `belief_USA_USSR` has none, its truth being the swept
hypothesis) and (2) the contemporaneous belief of the record: v1's manual replay snapshot of the
year where there is one (`snapshots/cw_v1/replay/`, 1957 to 1962, 1983), else the latest
`belief` row visible on 1 January of `data/cw/events.csv` with `data/cw/v1/events.csv` (v1's
rows of a variable replacing v0's, as the v1 snapshots read them), the rule the manual replay
follows (a test checks that both agree in the manual years). The report has the C6 table (per
year, whether the replayed `belief_force_USA` is in a higher band than the hindsight
`count_USSR`, beside the same for the manual replay; R V6 (a) of cw_v1_decisions.md), the C7 line (`belief_USSR_USA` on 1 January 1983), agreement per variable with both
series, the flips of the replay against the documented flips of the contemporaneous series
(matched within two years, lag in years; both series start from the record's contemporaneous
level of the year before the first, never from a replay snapshot of that year, so a replay of
1982 to 1985 that reads `over_1000` from the start has no false flip), and the indicators behind every disagreement. These
are inputs of C6 and C7; the claims themselves are computed on the model from the snapshots.

```
wf replay --episode cw --years 1957..1962 --corpus data/cw/corpora/raw/crest --source crest \
    --backend claude --out $OUT --dry-run
wf replay --episode cw --years 1957..1962 --corpus data/cw/corpora/raw/crest --source crest \
    --backend claude --out $OUT --workers 4
wf replay --episode cw --years 1957..1962 --out $OUT --measure-proposals
wf review $OUT/proposals/1958.json
```

**Dry run on `crest`** (2026-10-24; nothing sent): for 1957 to 1962, 22 documents (1, 4, 4, 1,
6 and 6 new per year), 25 requests with the Claude backend, 2.20 million characters, about
577,000 input tokens. Again on 2026-10-28 with the count scale: the same documents and
requests, about 578,500 input tokens (the system prompt 1,054 tokens). For 1982 to 1985 in a fresh directory, 38 documents, all but one read
for 1982 (everything dated to 1981, back to 1956) and none dated 1982 or 1983: the corpus holds
nothing between NIE 11-8-71 (Oct 1971) and SNIE 11-10-84 (May 1984), which becomes visible for
1985; about 682,000 input tokens. Run after 1957 to 1962 in the same directory, the later years
read only the documents not yet read.

What a blind C6 and C7 replay still needs:

- **Part III of the Steury volume** (estimates 27 to 41, 1972 to 1983) has no text layer: OCR
  outside the harness. Without it nothing is read between 1971 and 1984, and C7's year has no
  American document either.
- **The estimates of Parts I and II** are all dated now: the twelve the volume prints no date
  for carry one with its source in `crest.STEURY_1996` (a citation with the date in another
  estimate of the corpus, the FRUS printing, or the CIA's 2004 list of declassified NIEs). The
  Memorandum to Holders of NIE 11-5-58 (no text layer) still bears on 1959 unread. The C6
  years are read now from 22 documents.
- **C7 needs Soviet documents.** `crest` holds American estimates only; under the prompt's rule
  an American estimate of what Moscow fears is Washington's belief, so `belief_USSR_USA` can
  only be read from a document reproducing Moscow's own words (the KGB's RYAN instructions as
  published by Andrew and Gordievsky, the Wilson Center's Soviet records), which no corpus of
  the repository holds. The PFIAB report (1990) is dated after every C7 year.
- `belief_USA_USSR` is read from Washington's basic national security papers (NSC-68,
  NSC 162/2), which are FRUS documents, not estimates; a FRUS corpus for 1950 to 1953 would be
  needed to replay it.

## Open items

- Done 2026-10-29: framework_spec.md section 2 (package layout), section 9 (evidence) and
  section 10 (CLI) now have their paragraphs for the `corpora` (the `crest` corpus included),
  `extract` (the DeepSeek backend and the per-document cache included), `harness_rules`,
  `review`, `episodes`, `replay` and `replay_cw` modules, and for the `extract`, `review` and
  `replay` subcommands with every option and its default (`--episode`, `--years`,
  `--guidance-file` and `--drop-rejected` included).
- The two-document rule counts document ids, so a document printed in two FRUS volumes under
  two ids corroborates itself; a near-duplicate check (same date, same sender, most of the
  text in common) would close that. Where a corpus knows the duplication it says so: a
  document's `work` (set by `crest` for an estimate held twice) is counted instead of its id.
- `crest`: Part III of the Steury volume (estimates 27 to 41, 1972 to 1983, among them NIE
  11-4-82, 11-3/8-82 and 11-3/8-83), the whole-volume PDF, the two Memoranda to Holders (NIE
  11-5-58, NIE 11-8-62) and SNIE 11-9-84 have no text layer and enter no index until they are
  OCRed outside the harness; Part III's estimates also need a date with its source in
  `crest.STEURY_1996` once they are readable.
- A document the Claude backend refuses stops its quarter on every run; a way to record it and
  go on (with the quarter marked incomplete in the report) is not built.
- Chronicling America's move to the loc.gov API (snippets only in search results) needs a
  page-text fetch before that source can be replayed.
- DGFP, the Nuremberg documents, the 1941 Imperial Conference records and the Cabinet papers
  have no fetch module; they enter as `local` directories of dated text files.
- The WW2 replay snapshots carry no `builtins` section; the built-in counters of a replayed
  state come from the model's initial values when it is loaded. (The Cold War snapshots carry
  the hindsight snapshot's built-ins.)
