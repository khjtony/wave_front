# Waiting on the owner, 2026-10-30

Status: the branch `owner-decisions-2026-10-23` (pull request #5) is clean and pushed. Decisions taken so far are in [owner_decisions_2026-10-23.md](owner_decisions_2026-10-23.md).

## Done since the last list

- **Phase 2 passed** (decision 7h).
- **July 1914 v1, first sight** (reports/july1914_v1.md): J1v1, J2v1, J4v1, J5v1, J7v1, J9v1 pass; J3v1 fails as expected; J6v1 fails on its second clause (the British sets reach `GENERAL_WAR`, which counts Britain at war, without a continental war); J8v1 fails on (c) (Vienna's kernel left at 31, not 22).
- **Cold War v1, first sight** (reports/cw_v1.md): V1 and V4 pass; V2, V3, V5, V6, V7, V8, V9 fail; V10 open on a code defect. H7 held only in 1967 to 1973; from 1974 the US can hold the balance alone, from 1982 both; this reverses v0.
- **Framework change 2**, ambiguous levels as sets; the windows applied in a separate layer; every recorded WW2 result checked is robust; V6's input comparison is fragile in 1961 only.
- **Overnight, decision-free:** the full suite (1314 passed, 12 failed, all registered claims failing as recorded); a code review of the branch with its seven findings fixed (no recorded number changed); the spec paragraphs for the evidence modules; cw_v1's sizes remeasured.

## Decisions (cw_v1 report section 16; recommendations in brackets)

1. **V10's defect:** the Able Archer and Cuba exit maps write `accidental` unconditionally. Fix (unchanged reachable transitions), log, rerun V10 and record it beside the first-sight error? [yes]
2. **V9's budget:** part (d) needs about 11.4 million states under `opportunist`. Rerun it with a 12 million budget, logged (the verdict stays a fail)? [yes]
3. **V9 (b):** give `USSR.invade_west:response` the plans' condition (a war begun by NATO), a guard edit after first sight? [no: the single relaxation lifts only the US deterrent, as H6 predicts]
4. **New registrations under new ids** (first sights of V2, V5, V6 stand): V6a (the projected number against the count by ratio, or ICBM launchers alone, since the bands hid 700 against 235 in 1961), V2a (the joint window and its ends as the registered quantity), V5a (the triangle at the 1969 entry only). [V6a and V2a]
5. **H7** recorded in docs/transfer_hypotheses.md as "held 1967 to 1973 on cw_v1, failed as stated". [yes]
6. **July 1914 v1 proposals** (reports/july1914_v1.md, last section), notably J6v1's target reading (war on the continent rather than `GENERAL_WAR`, which counts Britain). [read the report]
7. **The hand-coded 1958 replay row** reads NIE 11-4-57's mid-1959 bomber column; the mid-1960 column gives about 730 instead of 580, the same band (no verdict changes). Correct it, logged? [yes, as a data correction]
8. **The phase 3 gate.** Neither v0 nor v1 passes as written; every failure is explained as model content, claim reading or a defect, none as an engine defect; framework changes 2 of 5. Treat it as phase 2 was treated (amend where the reading was at fault, then accept with the failures explained), or build further? Then the go for phase 4.
9. **OCR** (`sudo apt install tesseract-ocr ocrmypdf`) when convenient, for the 1972 to 1983 CIA estimates.
