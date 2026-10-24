# Blind replay of FRUS 1936 to 1940 with the Claude backend

The run of docs/replay_harness.md, "Running the Claude backend on the real corpus", on the owner's machine (decision 8 of 2026-10-15; the owner's go of 2026-10-24): the pilot quarter 1936Q1 (07:33 to 07:37 UTC) and the rest, 1936Q2 to 1940Q4 (07:42:14 to 09:35:53 UTC, `--workers 4`), with the backend's defaults (model `claude-opus-5-5`, effort `high`), at the commits in `commit.txt` (the pilot at 2e038cd; the rest at the commit recorded there). The corpus check is `fetch_check.txt` (10,550 documents; checksums as data/ww2/corpora/frus/MANIFEST.json). `proposals/` holds the twenty proposals files (every proposal with its quote, the documents read, discards, errors, and per quarter the model, tokens and cache counts); the per-document cache is not kept.

Usage over the twenty quarters: input 8,919,418 tokens, output 1,433,631, cache writes 20,472, cache reads 53,979,546; 0 backend errors, 0 refusals. At the prices recorded in docs/replay_harness.md (2026-10-06), about $75.

**Result, proposal level (no proposal reviewed; every proposal treated as accepted):**

| Measure | Harness rules on (`metrics_claude.md`) | Rules off (`metrics_claude_rules_off.md`) | Rule backend baseline (reports/replay_ww2_frus.md) | Reading nothing |
|---|---|---|---|---|
| Text-derived variables, exact agreement over variable-quarters (section 9 target 80 %) | 472/500 (94 %) | 483/500 (97 %) | 76 % (rules on) | 304/500 (61 %) |
| Documented belief and commitment flips replayed within one quarter | 8 of 9 (all 9 within 4 quarters) | 8 of 9 | 4 of 9 | - |
| False flips | 4 | 5 | | |

Disagreements concentrate in `italy_estranged` (replayed reconciled with the West from 1938Q2, after the Anglo-Italian agreement; hindsight estranged throughout) and `belief_GER` (1938Q3 to 1940Q4). Resource variables are copied from the datasets and not tested by a replay of documents. The criterion of phase 2 (ww2_testbed.md section 9) is met at the proposal level; the protocol's result after a human review (`wf review`, then `--metrics-only`) is the owner's.
