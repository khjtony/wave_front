# Code review, branch owner-decisions-2026-10-23 against main (2026-10-29)

Scope: the framework and evidence code named in the request (DeepSeek and Claude backends,
schema, extractor, `crest` and `base` corpora, episodes, replay, replay_cw, harness rules,
review, CLI options, snapshot level sets, robust analysis, report, the four scripts, and the
layered lifting in `tests/coldwar_v1/layered.py`). Findings only; no file other than this one
was changed. `pytest -q tests/evidence` passes (399 tests) at HEAD. Every finding below was
reproduced with a script or traced through a real caller; candidates I could not
substantiate are listed at the end as checked and dropped.

Ranked most severe first.

## 1. A replay that leaves and comes back across an ambiguous window gets a false flip (medium)

`wavefront/evidence/replay.py:669-677` (`Metrics.false_flips` / `_in_window`) with `_flips`
at `:702-727`.

When the hindsight series is `a` then a set window `{a, b}` then `a` again, there is no
documented flip, which is correct. A replay that moves to `b` inside the window and back to
`a` on the first concrete quarter after it agrees with the hindsight on every quarter. But
only the move into the window is excused (`_in_window` looks up `flip.quarter` in
`windows`). The move back is dated by the first concrete quarter, which is not in
`windows`, so it is counted as a false flip.

Reproduction (scratchpad script, belief_GER: will_not_fight, then the set over 1938Q2..Q4,
then will_not_fight in 1939Q1; the replay reads will_fight in 1938Q3 and 1938Q4):

```
agree all: True
window flips [Flip(... quarter='1938Q3', after='will_fight')]
false flips  [Flip(... quarter='1939Q1', before='will_fight', after='will_not_fight')]
```

This is the real layer's shape. In `snapshots/ww2/hindsight_ambiguous/`, `belief_GER` is a set
over 1938Q2..1938Q4 and is `will_not_fight` in 1939Q1. `italy_estranged` is a set over
1938Q2..1939Q1, and its 1939Q2 file is the canonical one. Both return to the level they had
before the window. So a replay that reads the contested reading inside the window gets a
false flip charged at the window's end, even though its agreement is 100%.

Test coverage: `tests/evidence/test_ambiguous_levels.py:279` covers a return that lands inside
the window (1939Q2 is in its test window) but not one that lands on the first quarter after
it.

## 2. Cold War flips: the replay baseline is the initial level, the documented baseline is the record (medium)

`wavefront/evidence/replay_cw.py:252-273` (`compare`).

The replay series starts from `base` (the previous year's replay snapshot, else `init`, and
always `init` with `--measure-proposals`). The documented series starts from
`contemporaneous([prev])`. When the record's level before the first year differs from the
initial level, the replay's first year produces a flip `init -> X` that has no documented
counterpart. That flip is reported as a false flip, even when the replay agrees with the
record in every year.

Reproduction: replay snapshots 1982 and 1983 with `belief_force_USA = over_1000`, which is the
record's level since 1968, and `compare(dir, ['1982', '1983'])`:

```
agree contemporaneous (2, 2)
[(None, YearFlip(variable='belief_force_USA', year='1982', before='none', after='over_1000'))]
```

`docs/replay_harness.md` plans exactly this run (`1982 to 1985`). For the registered
1957..1962 run the two baselines happen to coincide (1956: none, opportunist, hostile, which
equal the initial levels), so V6's input is not affected. The WW2 `compare` has the same
asymmetry in measure mode (`_initial()` against the hindsight snapshot of the previous
quarter, which predates this branch). It bites any `--quarters` range that does not start
at 1936Q1.

Test coverage: none. `tests/evidence/test_episode_cw.py:276` uses 1957..1962, where the
baselines agree.

## 3. CLI: the proposal-level banner moved under `--drop-rejected` (low)

`wavefront/cli.py:775-779`. On main, the line `print("PROPOSAL-LEVEL: every proposal treated
as accepted ...")` sat under `if args.measure_proposals:`. It now sits under
`if args.drop_rejected:`. As a result:

- a plain `--measure-proposals` run no longer prints its warning on stdout;
- a `--drop-rejected` run prints "every proposal treated as accepted", which is false for that
  mode (rejected proposals are left out).

The report file itself is correct, because `render_report` writes the right first line.

Test coverage: none (no test checks stdout).

## 4. DeepSeek backend: error classes that are not mapped (low)

`wavefront/evidence/extract/deepseek_backend.py:262-287, 304-322`.

- The DeepSeek chat API documents `finish_reason == "insufficient_system_resource"` (the
  answer was interrupted by the provider). It is treated as a normal answer. The truncated
  `content` then fails to parse and raises a non-retryable
  `ExtractError("... not the proposal schema")`, which reads as the model's fault. It should
  be retryable, or at least named.
- `http.client.HTTPException` (for example `IncompleteRead` while reading a 200 body) and
  `UnicodeDecodeError` are not caught by `_send`. They escape `extract()`, which only catches
  `ExtractError`. The exception comes out of the worker pool and ends the whole run, not just
  that document. This is loud, not silent, but it bypasses the per-document error record and
  the retry.

The retry and backoff loop itself, and the locking of `requests` and `usage`, are correct.
Test coverage: `tests/evidence/test_deepseek_backend.py` covers the mapped HTTP statuses
only.

## 5. Settings that change the answer but are not recorded or keyed (low)

- **Document header fields.** `cache_key` (`extract/cache.py:41-50`) hashes the document's id,
  date and text, but not its `title`, `source` or `url`. Both backends send all three in
  the user message (`deepseek_backend.py:221-224`, `claude_backend.py:248-251`). For
  `crest`, the title comes from `STEURY_1996` and the source carries the raw file and page
  locator. Editing a contents title, or moving a document between the Part and
  whole-volume files with identical text, therefore reuses the stale answer. The Claude side
  predates this branch; the DeepSeek backend repeats it.
- **The guidance file.** `--guidance-file` is in the DeepSeek cache key (inside the hash of
  the system prompt), but it is not in the proposals file's `backend` record
  (`replay.backend_info` keeps only name, model and effort) or in the report's command
  line. Two runs with different guidance cannot be told apart from their outputs.
- **An empty guidance file.** `make_backend` (`extract/__init__.py:57`) drops an empty
  guidance string (`if guidance`), so an empty file silently means the WW2-tuned
  `DEFAULT_GUIDANCE`. `scripts/compare_backends.py` passes `""` through, which means no
  guidance at all. The same file therefore gives two different prompts depending on the
  entry point.

Test coverage: none.

## 6. Cold War snapshots break on a set-valued hindsight entry (low, latent)

`wavefront/evidence/review.py:466-474` (`_build_annual`). Every carried hindsight entry is
given `entry["confidence"] = "assumed"` and its indicators' rules are rewritten. On a
set-valued entry (`levels` plus `ambiguity`), this adds `confidence` at the top level, which
`_check_level_set` refuses (only `levels` and `ambiguity` are allowed). The members'
indicators are also left unmarked. Today no `snapshots/cw_v1/hindsight/` file has a set, so
nothing fails. Once the Cold War window of `data/ambiguous_windows.csv` is built into a
hindsight layer, every Cold War review and measurement against it will raise `ReviewError`.
That is loud, not wrong.

Test coverage: none.

## 7. `scripts/compare_backends.py`: recall counts failed documents as misses (low)

`scripts/compare_backends.py:120-130`. A document the backend failed on (it appears in
`result.errors`) has no proposals, so every reference pair of that document is counted as
`missing`. Recall is understated by the failure rate. The error count is printed, but the
reported recall does not exclude those documents. Separately, the comment at `:62` says
"level differs" is halved, but the code does not halve it. Precision and recall use only
`match`, so they are unaffected; the `counts` it prints are per side.

Test coverage: none (script).

## Checked and dropped (no defect found)

- **Period boundaries.** `Episode.cutoff` and `snapshot_date` for years: 1958 is read to
  1957-12-31, and the snapshot is dated 1958-01-01. `_read_before`, `plan`,
  `measured_snapshots` and `_build_annual` (which refuses any cut-off other than a
  31 December) all use the cut-off. `IndexedCorpus.load` refuses a document whose
  re-parsed date differs from its index date, and `check_proposal` refuses a proposal dated
  after its document. No early-visibility path found. `contemporaneous` uses
  `visible_year <= year`, which matches the CSV's meaning ("first 1 January showing the
  level").
- **`crest` dating and works.** Every estimate date is the estimate's own date. The PFIAB
  report is dated 1990. Works are consistent between the volume and the separately fetched
  files (`NIE 11-5-58`, `NIE 11-8-59`, `NIE 11-8-60`, `NIE 11-8-61` and its two parts).
  The whole-volume file, which has no afterword entry in the contents, has no text layer,
  so it cannot leak 1996 text.
- **The two-document rule on works.** `_work` is used for both the bucket test and the
  bucket entries. `work` survives `write_proposals`, `read_proposals` and `save_proposals`.
  In the Cold War episode every text variable is a reading, so the rule acts on nothing
  there.
- **`--drop-rejected`.** Rejected proposals are removed before `_unique` and before gating;
  pending proposals count as accepted; `retrospective?` proposals are applied only if
  accepted. Combining it with `--corpus` or with the Cold War episode is refused.
  `gate_counts` takes no `applies_back`, but it only counts gates, so the gate counts are
  unaffected.
- **Concurrency.** `CachedBackend` writes atomically to a temporary file named per thread,
  and its hit and miss counters are locked. The usage and request counters of both backends
  are locked. The per-quarter usage delta is read only between quarters.
- **`snapshot_to_states`, `robust` and the report.** A level given twice is refused. The
  product order and the latch fill per member are correct. In `Distance`, the margin is
  determined by the shortest distance, so no "fragile" verdict can show identical answers.
- **Layered lifting.** Its conditions (constant entry maps except Able Archer's, exits that
  read only the fine state, one crisis per tick, no exit variable written by a delayed
  effect) are asserted in `tests/coldwar_v1/test_yearwise.py:285`, not in `Lift.__init__`
  as its docstring says. They hold for every crisis map in `models/cw/crises/`. `Window`
  checks that no crisis is available before the crisis tick. I found no unsound step in
  `Window.kernel` or `Window.distance`.
- **`apply_review.py`.** Every `decide` call is atomic. Grouping by note and accepting before
  rejecting can change which acceptances are left pending, but under `--drop-rejected` a
  pending proposal counts as an accepted one, so the measured metrics do not depend on that
  order. A BOM or a bad encoding fails loudly.

## Fixes (2026-10-30)

Each finding has a regression test that fails at d24e361 and passes with the fix.

1. **False flip on the return out of a window.** `Metrics._in_window` (`replay.py`) also
   excuses an unmatched replayed flip on the first concrete quarter after a window when it
   leaves a level of the window's set for that quarter's hindsight level. Test:
   `tests/evidence/test_ambiguous_levels.py::test_a_return_on_the_first_quarter_after_a_window_is_not_a_false_flip`
   (the return is a window flip; a return one quarter late is still a false flip).
2. **Flip baselines.** Both series now start from the record, the definition the WW2 metrics
   use for documented flips (docs/replay_harness.md, "Replay and metrics"): Cold War, the
   contemporaneous level of the year before the first (`replay_cw.compare`); WW2, the hindsight
   snapshot of the quarter before the first, else the initial levels, in both modes (the WW2
   asymmetry was in measure mode and, when no replay snapshot of that quarter existed, in the
   reviewed mode too). A replay snapshot of the previous period is not read. The Cold War
   report's flips section states the baseline. Tests:
   `tests/evidence/test_episode_cw.py::test_cw_flips_start_from_the_record_of_the_year_before`
   (1982..1983, the review's reproduction) and
   `tests/evidence/test_replay.py::test_metrics_a_range_after_1936q1_starts_both_series_from_the_record`.
   Recorded WW2 metrics: all start at 1936Q1, and `snapshots/ww2/hindsight/1935Q4.json` equals
   the initial levels for every text variable, so nothing changes. Recomputed with the fix outside
   the repository (the five measurements of `reports/replay_ww2_frus_claude/` and
   `reports/replay_ww2_frus_deepseek/`, the two reviewed-sample ones through
   `scripts/apply_review.py`, the 5c one with the three `oil_GER` acceptances of 19 to 25 Aug
   1939 rejected): every report matches its recorded file line for line except the title and the
   command line. The recorded reports are unchanged.
3. **Proposal-level banner.** `cmd_replay` prints it under `--measure-proposals`, with the
   rejected-dropped wording under `--drop-rejected`. Test:
   `tests/evidence/test_replay.py::test_measure_proposals_prints_the_banner_of_its_mode`.
4. **DeepSeek error classes.** `finish_reason == "insufficient_system_resource"` is a retryable
   `ExtractError` raised inside the retry loop (usage still counted);
   `http.client.HTTPException` is a retryable network error and `UnicodeDecodeError` a
   non-retryable one, so `extract()` records them per document. Tests:
   `tests/evidence/test_deepseek_backend.py::test_an_answer_interrupted_for_lack_of_resources_is_retried`,
   `::test_transport_and_decoding_failures_are_extract_errors`.
5. **Unrecorded settings.** Header fields: the same id and text can come with another title or
   URL (`crest` titles come from the code table `STEURY_1996`, URLs and sources from the manifest
   and the raw file), so they are not part of the document's identity. The key is unchanged (the
   recorded caches stay valid); each new cache entry records its `header` (source, title, url)
   and an entry with another header is read again; an entry without a header is used as before
   (`extract/cache.py` docstring, spec section 9). Guidance: `backend_info` records `guidance`
   (`default`, `none`, or `sha256:<hex>` of the file), the report's backend line names it and its
   command line gives `--guidance-file`; `make_backend(guidance=None)` keeps the default and an
   empty string means no guidance, as in `scripts/compare_backends.py`. Tests:
   `tests/evidence/test_deepseek_backend.py::test_a_cached_answer_is_not_reused_under_another_header`,
   `::test_the_guidance_is_recorded_and_an_empty_one_means_none`.
6. **Set-valued entry in a Cold War snapshot.** `_build_annual` carries a set as a set: no
   `confidence` at the set level, each member `assumed` with its indicators' rules marked. Test:
   `tests/evidence/test_episode_cw.py::test_a_set_valued_hindsight_entry_is_carried_as_a_set`.
7. **`compare_backends.py` recall.** Documents in `result.errors` are left out of every count,
   precision and recall, and reported as `failed_documents` with
   `reference_proposals_on_failed`; the "halve it" comment is replaced by the docstring (a
   "level differs" pair is counted on each side). Test:
   `tests/evidence/test_compare_backends.py::test_failed_documents_are_not_counted_as_misses`.

The other reviewer's six: (a) `wf replay --source` help lists `crest`; (b) as 3; (c) the
`_evidence` docstring says that `wf replay` turns a backend failure into a `ReplayError` (exit
2) and `wf extract` exits 1; (d) `--no-cache` help and the `replay` docstrings say
`OUT/cache/<backend>/`; (e) the `cache.py` docstring names the fallback setting and the schema
hash of the Claude key, and the DeepSeek key; (f) the WW2 report's Target line names the
hindsight directory compared with (`Metrics.hindsight`; test
`tests/evidence/test_replay.py::test_report_target_names_the_hindsight_directory_compared_with`).
The layered lifting's docstring (`tests/coldwar_v1/layered.py`) now says which conditions
`Lift` checks (no latch, no exit variable written by a delayed effect, one crisis per state)
and which are asserted on cw_v1 in `tests/coldwar_v1/test_yearwise.py` (exits read only the
fine state, entries read only `entry_reads`). Specification: docs/framework_spec.md sections 9
and 10, docs/replay_harness.md and docs/ambiguous_levels.md section 5.
