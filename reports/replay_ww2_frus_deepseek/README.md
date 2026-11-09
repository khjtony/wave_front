# Blind replay of FRUS 1936 to 1940 with the DeepSeek backend

The same run as reports/replay_ww2_frus_claude/, with `--backend deepseek --model deepseek-flash --guidance-file data/extract/deepseek_guidance_g2.txt --workers 6`, 2026-10-24 08:35:41 to 12:37:04 UTC, at the commit in `commit.txt`. The guidance g2 was tuned on 200 documents of 1936Q1 against the Claude backend's proposals and checked on the other 120 of that quarter (scripts/compare_backends.py), where it agreed with Claude about as well as the untuned prompt; those 320 documents are part of this run.

Usage: prompt 45,468,406 tokens (38,349,274 cache hits), completion 8,978,768 (8,556,662 reasoning); 0 errors, 2,660 proposals. Cost about CNY 45 (about USD 6), read from the account balance before and after (it includes a 22-document crest run).

**Result, proposal level (unreviewed), beside the Claude backend:**

| Measure | DeepSeek, rules on | rules off | Claude, rules on | rules off |
|---|---|---|---|---|
| Text-derived agreement (target 80 %) | 465/500 (93 %) | 474/500 (95 %) | 472/500 (94 %) | 483/500 (97 %) |
| Flips within one quarter | 7 of 9 | | 8 of 9 | |
| False flips | 9 | | 4 | |

Both readers disagree with the hindsight snapshots in the same places: `italy_estranged` (read as reconciled with the West from 1938Q1/Q2, after the Anglo-Italian negotiations and agreement; hindsight estranged throughout) and `belief_GER` (1938 to 1940). Two independent readers agreeing against the snapshot is a reason to re-examine the snapshot's coding of those variables; any change follows the guard-changelog rule and is the owner's.
