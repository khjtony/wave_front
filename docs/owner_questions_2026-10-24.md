# Waiting on the owner, 2026-10-24

Status: written at the end of the overnight work of 2026-10-24 on the branch `owner-decisions-2026-10-23` (pull request #5). Each item says what was done, what is open, and a recommendation. Decisions already taken are in [owner_decisions_2026-10-23.md](owner_decisions_2026-10-23.md).

## What was done overnight

| Work | Result | Where |
|---|---|---|
| Claude-backend replay, FRUS 1936 to 1940 (phase 2) | 94 % agreement (target 80 %), 8 of 9 flips within a quarter, about USD 75, 0 errors | reports/replay_ww2_frus_claude/ |
| DeepSeek backend (flash), same corpus | 93 %, 7 of 9 flips, about CNY 45 (USD 6) | reports/replay_ww2_frus_deepseek/, wavefront/evidence/extract/deepseek_backend.py |
| Cold War episode in the extractor; dates for 12 CIA estimates | blind replay possible over the CIA estimates | docs/replay_harness.md "The Cold War episode" |
| Blind Cold War replay, CIA estimates 1957 to 1962 (DeepSeek) | does not reproduce the missile gap (see item 4) | reports/replay_cw_crest_deepseek.md |
| PRC experiment | not reducible to the Soviet bloc; matters in 1951 (Korea) within v0 | docs/prc_experiment.md |
| July 1914 v1 | registered (J1v1 to J9v1), built, test bodies written; first sight held | docs/july1914_testbed.md section 8, docs/july1914_v1_decisions.md |
| Cold War v1 | registered (V1 to V10), built (0 framework changes), year-by-year lifting validated, test bodies written; first sight held | docs/coldwar_testbed.md section 9, docs/cw_v1_decisions.md |

## Decisions

1. **Phase 2 gate.** The replay criterion is met at the proposal level (every proposal treated as accepted). Accept the gate on that, or first review proposals with `wf review` (a sample, or all the proposals of the 20 files) and re-measure with `--metrics-only`? *Recommendation:* accept at the proposal level and review a stratified sample (the flips and the disagreeing quarters) to confirm.
2. **The hindsight coding of `italy_estranged` and `belief_GER`.** Both readers, independently, read Italy as reconciled with the West from 1938Q1/Q2 (the Anglo-Italian negotiations and the agreement of 16 April 1938) where the snapshot keeps it estranged, and both differ on `belief_GER` 1938 to 1940. Re-examine the snapshot's threshold for these two variables? A change would be a logged edit with sources and a full rerun. *Recommendation:* have the two variables' rules and events re-read against the record; no change until then.
3. **The framework-change budget.** You allowed an increase; its size is open (currently 5, the cadence counted as 1; no Cold War framework change so far, v1 included).
4. **The reading of `belief_force_USA` (C6).** The blind replay reads the CIA estimates' statements of the *current* Soviet force (about ten prototype ICBMs) and so finds no gap 1958 to 1961; the manual replay coded the *projected* force and the political debate as the belief. Which is the variable: the estimate at the date, or the projection? Until you decide, the manual replay stands (decision 3c). Optional: a Claude run of the same 22 estimates (about USD 3) as a second reader.
5. **July 1914 v1 before first sight.** (a) Testbed section 8.5: J6v1 may still fail under `fight` through a single Russian-side relaxation; add an Austrian-measures part to the Russian steps (outside decision 2h) or not? (b) Then the go: `WF_FIRST_SIGHT_1914V1=1 pytest tests/july1914_v1 -s -n 2` (about 20 minutes), run once at a recorded commit.
6. **Cold War v1 before first sight.** (a) The 1969 exit does not carry the talks into the coarse game, so the Soviet strike on China stays open 1970 to 1972: keep that reading or carry the talks? (b) V8's composite years (1972 to 1983) may exceed the explicit budget and then count as undecided, which makes V8 unpassable by construction; allow the layered lifting there instead (an R V8 change)? (c) Review the ten R notes in docs/cw_v1_decisions.md. (d) Sources marked "not verified" (the 1962 to 1963 decree dates, the 1981 NSC dates, the Cienfuegos naval options). (e) Any American crisis option of 1984 to 1991 to add. (f) Whether to re-ask C7 in v1. Then the go: `WF_FIRST_SIGHT_CWV1=1` (several hours).
7. **The DeepSeek backend's default.** Keep `deepseek-flash` with guidance g2 for future runs? The tuning on 200 documents against Claude did not clearly generalize on the held-out 120 (more recall, less precision); on the full corpus it scores one point below Claude with twice the false flips at a twelfth of the cost.
8. **Data for the C7 replay.** The CIA corpus has nothing between Oct 1971 and May 1984 in readable form: Steury Part III needs OCR (`sudo apt install tesseract-ocr ocrmypdf`, which needs your password), and Moscow's belief needs Soviet documents (the Wilson Center's translations; the RYAN instructions in Andrew and Gordievsky). Install OCR, and should a session fetch the Wilson Center documents?
9. **Pull request #5.** Merge when the items above that you want in it are settled.
10. **Phase 4.** Its go follows items 1, 3 and the two v1 first sights.

Spend so far on this branch: Anthropic API about USD 77.5 (pilot and full run); DeepSeek about CNY 53 (CNY 108 left).
