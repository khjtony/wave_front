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
editors' footnotes (written decades later) are excluded from the text; a document is filtered
on its index date before it is parsed.

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
  missed;
- the disagreements, each with the hindsight event and the replay quote behind it.

`--metrics-only` recomputes the report from the snapshots already reviewed.

## Running on the owner's machine

```
pip install -e '.[extract]'                      # only for the Claude backend
python3 scripts/fetch_corpora.py frus --since 1936-01-01 --until 1940-12-31
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
    --out <scratch> --auto-accept --report reports/replay_ww2_synthetic.md \
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

## Open items

- framework_spec.md section 2 (package layout), section 9 (evidence) and section 10 (CLI)
  do not yet list the `corpora`, `extract`, `review` and `replay` modules and the `extract`,
  `review` and `replay` subcommands; the spec belongs to the framework step and should gain
  a paragraph for each.
- Chronicling America's move to the loc.gov API (snippets only in search results) needs a
  page-text fetch before that source can be replayed.
- DGFP, the Nuremberg documents, the 1941 Imperial Conference records and the Cabinet papers
  have no fetch module; they enter as `local` directories of dated text files.
- The replay snapshots carry no `builtins` section; the built-in counters of a replayed
  state come from the model's initial values when it is loaded.
