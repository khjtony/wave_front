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

## Sample review (2026-10-28, owner's decision 7a)

The 113 proposals of `review_sample.csv` were reviewed, on the owner's instruction, by a delegated reviewer (an automated reader with high reasoning effort, not a person): blind to the hindsight levels and to why each proposal was sampled (a shuffled copy without those columns), judging each proposal against the full text of its document and the variable's threshold rule only. Decisions and one-sentence reasons are in `review_sample.csv` (`decision`, `note`): 96 accepted, 17 rejected; one acceptance (1939Q1-078, `polish_guarantee`) is refused by the two-document rule and stays pending. Main grounds for rejection: a conjunctive threshold only partly shown (Austria's annexation, Balkan alignment, Italy's reconciliation from the unratified April 1938 agreement), a third party's reading presented as a German decision record (`belief_GER`), rumour or forecast read as fact. Rules the reviewer found ambiguous: `italy_estranged` (no threshold for `false`), the dated windows of `austria` and `balkans`, `belief_GER` (lenient for `uncertain`, strict for `will_not_fight`).

Re-measure with the rejected proposals dropped and the unreviewed ones counted (`wf replay --measure-proposals --drop-rejected`; `metrics_claude_reviewed_sample.md`): text-derived agreement 477/500 (95 %), 8 of 9 documented flips within one quarter, 1 missed (`belief_GER` -> `will_fight`, 1939Q3: its only proposal was rejected), 3 false flips. With the three `oil_GER` acceptances that rest on the German-Soviet credit agreement of 19 Aug 1939 also rejected (the owner's decision 5c; `metrics_claude_reviewed_sample_5c.md`): the same figures.
