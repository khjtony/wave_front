# The owner's decisions of 2026-10-23

Status: recorded 2026-10-23 at `main` a1bf705, on the branch `owner-decisions-2026-10-23`. Answers the open items of docs/HANDOFF.md section 5. Where a proposal offered alternatives, the first-listed one is taken (the owner accepted "the proposals"; the choices below were stated to the owner before execution).

## 1. The Claude-backend replay (phase 2)

Not yet decided: who runs it (the owner with the commands of docs/replay_harness.md, or a session on the owner's machine with the key in its environment). The replay criterion of phase 2 stays open until then.

## 2. Amendments: all proposals accepted

**Summer 1939** (reports/crisis_1939.md section 11):
- 2a. K2 (d): amended as proposed (forced by Germany without the belief condition; contested in the fortune sense with Polish passage left open).
- 2b. K3: the driving-variable clause amended as proposed (the three variables the record places in 19 to 21 Aug); the daily re-ask is not taken.
- 2c. K4 (g): amended as proposed (the shortest trace through the realized cancellation of 25 Aug).
- 2d. K1: the reading "the exit state equals v1's realized transition of 1939Q3, differences from the hindsight snapshot tabulated" is adopted; the `oil_GER` disagreement between v1's snapshots and `accept_pact` is resolved under the snapshot convention of 2026-10-15 (decision 7) and logged.

**July 1914** (reports/july1914.md section 12):
- 2e. J2: the departure from tick 0 is recorded beside the result, and the point of no return is restated as Russia's last exit (30 July).
- 2f. J3 (a): restated as forceability; (b) and (c): "localized" read with the declaration of war required by 3 August, and GBR's non-pivotality registered as the model's result.
- 2g. J4 (d): restated as "the point of no return precedes the belief change".
- 2h. J6: a 1914 v1 with `GER.mobilize`'s own Russian-measures and [H] parts and Tisza's consent as a decision, run as a new registration under the total hold-out.
- 2i. J7: re-registered on the response lag rather than on the point of no return.

**Cold War** (reports/cw_v0.md section 18; docs/review_phase3_2026-10-18.md section 2):
- 2j. C3: asked with `no_war` in place of `balance_cw`.
- 2k. C3 (c), C4 (c), C9 (c): "contested" read in the fortune sense (ww2_testbed.md section 4.6), as for T6 and T9.
- 2l. C5: `USSR.nuclear_use` gains the Warsaw Pact plans' condition (a war begun by NATO; Mastny and Byrne 2005), a guard edit after first sight, logged with a full rerun of the Cold War and WW2 suites.
- 2m. C2 and C11: a cw_v1 with the American crisis-initiating options of the 1970s and 1980s (the 1973 alert as a sub-game) and the Sino-Soviet confrontation of 1969 as a sub-game, run as a new registration. Its PRC scope follows item 3.
- 2n. C6 (b), C8 (b), C10 (b): belief and oversight measured by their effect on reachability and on unilateral kernels, not on the joint kernel's distance.
- 2o. C2: also asked with a balance predicate without the opponent's-bloc clause (review section 2, the T13 precedent), beside the registered one.
- 2p. Data: supplied from the owner's machine, which reaches the testbed's hosts (docs/HANDOFF.md section 6).

## 3. Cold War scope

- 3a. The PRC: the owner asks whether the PRC's behaviour differs in kind from the USSR's, the United States' and the West's, and directs a research note and an experimental run to decide whether cw_v1 makes the PRC a principal (and from when) beside the USA, the USSR and Nature. The experiment runs analysis builds of v0, registers no claim, and is disclosed as an early sight in cw_v1's registration.
- 3b. The hindsight convention for beliefs (decisions D6): kept.
- 3c. The manual replay for C6 and C7 stands until the blind replay on the CIA estimates runs; then the blind result replaces it and both are reported.

## 4. Framework-change budget

The owner allows a larger budget. The cadence change (framework change 1) is counted as 1 of the phase 3 budget. The size of the increase is to be confirmed by the owner; until then the budget stays at five, and no Cold War framework change has been made.

## 5. Follow-up decisions (2026-10-24, after the amended runs)

- 5a. C5: v0 stays as recorded after the guard edit of 2l (C5 fails by a new route: the Soviet ICBM decision of 1950, Berlin, Korea, escalations adding up). No second guard edit; the route is a cw_v1 matter.
- 5b. J3: stays failing as amended; no further rewording.
- 5c. `oil_GER`: the German-Soviet Credit Agreement of 19 Aug 1939 is not used as a source. The snapshot change made under 2d is withdrawn; the difference stays tabulated (docs/guard_changelog_ww2.md, row of 2026-10-23).
- 5d. The branch is pushed and a pull request opened.

## 6. Decisions of 2026-10-24 (morning, on docs/owner_questions_2026-10-24.md)

- 6a. Item 7: the DeepSeek backend's default is `deepseek-flash` with guidance g2 (`DEFAULT_GUIDANCE`, the text of data/extract/deepseek_guidance_g2.txt); `--guidance-file` replaces it.
- 6b. Item 8: OCR is installed by the owner on the owner's machine.
- 6c. Item 9: the owner merges pull request #5.
- Items 1 to 6 were explained to the owner and are open.

## 7. Decisions of 2026-10-27 (on docs/owner_questions_2026-10-24.md items 1 to 6)

- 7a. Item 1, phase 2 gate: review a sample first (the proposals behind the documented and the false flips and the disagreeing quarters), then re-measure with `--metrics-only` and decide.
- 7b. Item 2: the owner asks how the framework represents the ambiguity of a continuous history read as discrete levels (answered in conversation; no change yet).
- 7c. Item 3: the framework-change budget stays at five (1 used, the cadence).
- 7d. Item 4: `belief_force_USA` is Washington's *projected* Soviet force (a reading fixed after the blind replay was seen, logged as such); the blind replay over the CIA estimates is rerun under that wording, with DeepSeek and with Claude as a second reader.
- 7e. Item 5, July 1914 v1: (a) the Russian mobilization steps gain an Austrian-measures part, symmetric with decision 2h, before first sight; (b) go for the first sight of J1v1 to J9v1.
- 7f. Item 6, Cold War v1: (a) the 1969 sub-game's exit carries the talks into the coarse game; (b) V8's composite years use the layered lifting instead of counting as undecided; (c) the R notes are reviewed and decided by a separate high-effort agent; (e) the owner asked what a crisis-initiating option is (answered in conversation; open); (f) C7 is not re-asked in v1. The go for cw_v1's first sight is not yet given.
- 7g. C6 (2026-10-28, after the two-reader blind replay under 7d, reports/replay_cw_crest_projected.md): `belief_force_USA` gets its own scale, the projected **number** of Soviet intercontinental delivery vehicles in bands, with a hindsight counterpart on the same scale, because the missile gap was a gap in numbers that `nuke_USSR`'s survivability scale cannot express. Applied to cw_v1 before its first sight (V6's comparison is amended accordingly, before first sight) and to the Cold War replay episode. v0's C6 stays as recorded (total hold-out, decisions D9).
- 7h. Phase 2 gate (2026-10-28): **accepted** by the owner on the replay criterion after the sample review (reports/replay_ww2_frus_claude/README.md, "Sample review"): 95 % agreement on the text-derived variables, 8 of 9 documented flips within one quarter, with the 17 rejected proposals of the delegated, blind review dropped. The hold-out part of the gate stands as recorded on 2026-10-14 and amended on the owner's decisions of 2026-10-15; the transfer hypotheses were committed before phase 3.
- 7i. V6 (2026-10-28), before first sight: (A) the projected count is compared with the hindsight count **at the date the estimate projects** (two to three years after its own date), not with the count on the estimate's date; the 1990 edition of Norris and Cochran (NRDC WP 90-1, Table 2) throughout; cw_v1 does not read v0's survivability-scale replay rows; ranges read at their midpoints uniformly.
- 7j. Ambiguous windows (2026-10-28): the four candidate windows of docs/ambiguous_levels.md are accepted as proposed, pending more reliable documents (the owner has none to hand). They are applied in a separate ambiguous layer of snapshots, so that the registered claims' start states and the single-state loaders are unchanged.
- 7k. V6's replay input (2026-10-28): the blind replay over the CIA estimates (Claude backend, proposal level), run as part of cw_v1's first sight; the hand-coded replay is computed and printed beside it. Then the go for cw_v1's first sight (V1 to V10).
