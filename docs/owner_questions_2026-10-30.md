# Waiting on the owner, 2026-10-30

Status: written 2026-10-30 on the branch `owner-decisions-2026-10-23`; reissued 2026-11-08 in this layout, with nothing decided in between, when the branch's work since pull request #5 went to `main` in a new pull request. Decisions already taken are in [owner_decisions_2026-10-23.md](owner_decisions_2026-10-23.md).

## Where things stand

| Item | State | Where |
|---|---|---|
| Phase 2 | passed (decision 7h) | docs/PHASES.md |
| July 1914 v1, first sight | J1v1, J2v1, J4v1, J5v1, J7v1, J9v1 pass; J3v1, J6v1, J8v1 fail | reports/july1914_v1.md |
| Cold War v1, first sight | V1, V4 pass; V2, V3, V5 to V9 fail; V10 open on a code defect | reports/cw_v1.md |
| Framework change 2 | ambiguous levels as sets, in a separate layer; 2 of the 5 changes used | docs/framework_changes.md |
| Full suite | 1314 passed, 12 failed, every failure a registered claim failing as recorded | reports/full_suite_2026-10-30/ |
| Code review of the branch | seven findings, all fixed; no recorded number changed | reports/code_review_2026-10-29.md |

What changed in the results:

- **J6v1** fails on its second clause. The British sets reach `GENERAL_WAR`, which counts Britain at war, without a continental war.
- **J8v1** fails on (c). Vienna's kernel is left at 31, not 22.
- **H7** held only from 1967 to 1973. From 1974 the United States can hold the balance alone, and from 1982 both sides can. This reverses v0.
- **V6's** input comparison is robust in 1958 to 1960 and fragile in 1961 only. Every recorded WW2 result checked under the ambiguous layer is robust.

## Decisions

Each item says what happened, what to decide, and the recommendation. Items 1 to 7 come from reports/cw_v1.md section 16 and reports/july1914_v1.md section 11.

### 1. V10: a code defect

- **What happened:** the Able Archer and Cuba exit maps write `accidental` whether or not it is true.
- **Decide:** fix it, log it, rerun V10 and record the result beside the first-sight error? Every reachable transition stays the same.
- **Recommendation:** yes.

### 2. V9: the state budget

- **What happened:** part (d) needs about 11.4 million states under `opportunist` and stopped at the budget.
- **Decide:** rerun it with a 12 million budget, logged? The verdict stays a fail.
- **Recommendation:** yes.

### 3. V9 (b): a guard edit after first sight

- **What happened:** `USSR.invade_west:response` does not read the Warsaw Pact plans' condition (a war begun by NATO), as `USSR.nuclear_use` does since decision 2l.
- **Decide:** add the condition, as a guard edit after first sight with a logged rerun?
- **Recommendation:** no. The single relaxation lifts only the US deterrent, as H6 predicts.

### 4. New registrations under new ids

The first sights of V2, V5 and V6 stand whatever is chosen.

- **V6a:** compare the projected number with the count as a ratio, or count ICBM launchers alone. The bands hid 700 projected against 235 in being in 1961.
- **V2a:** register the joint window and its ends (1973, 1981) as the quantity, instead of "every year".
- **V5a:** ask the triangle at the 1969 sub-game's entry only.
- **Recommendation:** V6a and V2a.

### 5. H7 in the transfer hypotheses

- **Decide:** record H7 in docs/transfer_hypotheses.md as "held 1967 to 1973 on cw_v1, failed as stated", with V2's table?
- **Recommendation:** yes.

### 6. July 1914 v1 proposals

Five proposals in reports/july1914_v1.md section 11. The main one is J6v1's target: read it as a war on the continent rather than `GENERAL_WAR`, which counts Britain.

- **Recommendation:** read the report section.

### 7. The 1958 replay row: a data correction

- **What happened:** the hand-coded 1958 row reads NIE 11-4-57's mid-1959 bomber column. The mid-1960 column gives about 730 instead of 580, in the same band, so no verdict changes.
- **Decide:** correct it, logged?
- **Recommendation:** yes, as a data correction.

### 8. The phase 3 gate

- **What happened:** neither Cold War v0 nor v1 passes as written. Every failure is explained as model content, a claim's reading or a defect; none is an engine defect. 2 of the 5 framework changes are used.
- **Decide:** treat it as phase 2 was treated (amend where the reading was at fault, then accept with the failures explained), or build further? Then the go for phase 4.

### 9. OCR

Install `tesseract-ocr` and `ocrmypdf` (`sudo apt install tesseract-ocr ocrmypdf`) when convenient, for the 1972 to 1983 CIA estimates.
