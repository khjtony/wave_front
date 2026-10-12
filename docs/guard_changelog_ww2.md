# Guard changelog: WW2 model

Rule (ww2_testbed.md section 7): tests T1 to T13 were registered before any guard was written. Every edit to a guard, effect, delay, fairness constraint, profile or assume made *after* a registered test has been run against the model is logged here with the test that prompted it, what changed, the contemporaneous source that justifies the new version, and whether the full suite was rerun. An edit without a source is a speculative tag, not a guard change.

Parameter budget is reported with every entry (the `budget()` counts before and after).

| Date | Test | Change | Source | Budget before → after | Suite rerun |
|---|---|---|---|---|---|
| 2026-10-12 | (none) | catalogue skeleton written; no guard yet tested | docs/actions_ww2.md | n/a | n/a |
