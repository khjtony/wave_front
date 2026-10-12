# Guard changelog: WW2 model

Rule (ww2_testbed.md section 7): tests T1 to T13 were registered before any guard was written. Every edit to a guard, effect, delay, fairness constraint, profile or assume made *after* a registered test has been run against the model is logged here with the test that prompted it, what changed, the contemporaneous source that justifies the new version, and whether the full suite was rerun. An edit without a source is a speculative tag, not a guard change.

Parameter budget is reported with every entry (the `budget()` counts before and after).

| Date | Test | Change | Source | Budget before → after | Suite rerun |
|---|---|---|---|---|---|
| 2026-10-12 | (none) | catalogue skeleton written; no guard yet tested | docs/actions_ww2.md | n/a | n/a |
| 2026-10-12 | scratch replay (notes §3), before the model existed | `balance_europe` loses its treaty clause; `commitment_alive` added as a separate invariant (decisions D2) | definition, not a guard; logged because it was changed after a computed result | n/a | n/a |
| 2026-10-12 | T2 counterexample (notes §3) | the draft's `arms_at_war` latch condition on `campaign_west` is withdrawn; `campaign_west` requires current `arms_GER >= high`; WEST `offensive_west` and Nature `campaign_rhineland` with the `GERMAN_DEFEAT` ending are added (D3) | French General Staff and Gamelin, 8 to 9 March 1936; Blomberg's withdrawal proposal; the German army's 1936 to 1937 assessments (historian to confirm) | n/a | n/a |
| 2026-10-12 | T8 analysis (notes §4) | fairness `czech_obligation` adopted (D4) | Franco-Czechoslovak treaty, 25 January 1925; French and British statements of September 1938 | n/a | n/a |
| 2026-10-12 | T10 analysis (notes §4) | `china_war` flag and Nature `china_incident`; parted guards on `strike_north` and `campaign_siberia` (D7) | the China incident of 7 July 1937; Nomonhan 1939 | n/a | n/a |
