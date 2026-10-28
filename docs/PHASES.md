# Phases

The program runs in seven phases. A phase ends when its gate passes, not when its time is up. The framework (DSL, engine, analysis, evidence pipeline) is domain-free; domain models are instances. Changes to the framework are logged with the test that forced them. After phase 4 the framework is frozen at version 1.0 and changes only through versioned releases that rerun every historical suite.

The discipline is train, validate, test, deploy: WW2 is the development set, the Cold War is the validation set with a logged change budget, a one-shot third episode is held in reserve, and the AGI model is the deployment.

Rough sizes assume one full-time engineer and a part-time historian reviewer. The slow parts are sourcing decision spaces and corpus work, not the engine.

---

## Phase 0: theory and framework core

**Goal.** A domain-free formal foundation and an engine that is correct on games with known answers, before any historical content exists.

**Work.**
- `docs/theory.md`: definitions (concurrent game structure with hidden variables and observation functions; memoryless and uniform strategies; the ATL fragment used; unilateral and joint viability kernels; point of no return; contested region; assumption mining as unsat core and MaxSAT; pivotal-coalition lattice; scenario clusters; the informativeness metric), the algorithms (attractor as least fixpoint, safety as greatest fixpoint, bounded unrolling), and soundness statements of the form "if the engine reports that no strategy exists, none exists in the model".
- A validity argument: what historical validation can establish about the method (reliability on cases with the same structural features) and what it cannot (the content of any particular model). This document is updated at every gate and is the honest front page of every AGI report.
- Requirements gathered from all three domains before the DSL is designed, so the Cold War and AGI needs are not retrofits: hidden variables with beliefs, observability, delays, fairness, behavioral profiles, multi-resolution time with nested crisis sub-games, joint and unilateral kernels, escalation ladders, exhaustion endings, capability events, treaty and verification variables, latched history variables.
- The DSL, the explicit-state engine, the bounded-model-checking skeleton on Z3, the report format, the parameter-budget and informativeness instrumentation.
- Engine tests on hand-built games with known answers, cross-checked against brute-force enumeration of memoryless strategies on random tiny models. The external cross-check against PRISM-games waits for the exporter in phase 6.
- Both historical test lists committed: WW2 T1 to T13 and Cold War C1 to C13.

**Gate.** Engine suite and cross-check pass; the DSL covers the requirement list; both test lists are committed; instrumentation exists.

**Gate record.** Passed 2026-10-11 at commit 5128836 (local tag `phase0`); evidence per sub-claim in validity.md section 8.

**Risk.** Over-designing the DSL. Mitigation: every construct must be demanded by a named test in one of the two lists.

**Size.** 4 to 6 weeks.

---

## Phase 1: WW2 v0, Europe 1936 to 1940

**Goal.** The first domain model, built under the anti-hindsight protocol, with the engine answering real questions.

**Work.**
- `models/ww2/v0.py`: four principals (Germany, USSR, Japan, WEST), 8 regions, 20 quarterly ticks; every action cited to a contemporaneous debate; speculative actions tagged.
- Hindsight snapshots per quarter from the datasets (NMC, ICB, MID, Harrison, Minerals Yearbook).
- Tests T1, T2, T4, T5, T8 and the negative controls T10 as files; the parameter budget reported.

**Gate.** T1, T2, T4, T5 and T8 pass; negative controls need 3 or more relaxations where registered; informativeness at or above 80 percent; the reachable set at or under 10^6 states.

**Gate record.** Passed 2026-10-12 under the claims as amended by the owner (ww2_testbed.md section 11), with T8(b) deferred to phase 2: T1, T2, T4, T5, T8(a) and the three non-vacuous T10 controls pass; informativeness 3 of 3. Under the original wording, T2 and T8 failed under hegemonic aims and the Japan and Britain-alone controls needed 1 and 2 relaxations (reports/ww2_v0.md sections 4 to 10). The reachable set from tick 0 exceeds 3 million states, so the bounded checker and fixed-strategy sufficiency checks answered the trace and kernel questions; phase 2 owes snapshots carrying pending decisions and either crisis sub-games or a symbolic engine.

**Risk.** Tuning guards to the known outcome. Mitigation: the protocol in ww2_testbed.md section 7; every guard edit after a failing test is logged with its rationale.

**What it teaches for the AGI model.** Whether the appeasement lever (concessions working only under limited aims) and the belief-then-response lag come out of the engine rather than being put in.

**Size.** 6 to 8 weeks.

---

## Phase 2: WW2 v1 and the replay harness

**Goal.** Scale the model to both theatres and 1933 to 1945, run the hold-out tests, and prove the evidence pipeline on dated documents.

**Work.**
- `models/ww2/v1.py`: five principals plus scripted others, about 14 regions, 51 ticks; bounded model checking and symbolic paths in the engine.
- Hold-out tests T6, T7, T11, T12 run without guard edits after first sight; T3, T9 and T13 run with the contested-region and window criteria.
- The replay harness: corpora indices for FRUS, Hansard, Chronicling America and Trove; the extractor against a fixed schema; the review CLI; blind replay by document date; replay agreement and belief-flip-lag metrics for 1936 to 1940.
- Transfer hypotheses written down at exit, before phase 3: the structural claims the WW2 suite produced that should hold on the Cold War unchanged (candidates: a belief change precedes a response by an institutional lag, and the point of no return hides in that lag; concessions remove the motive for conflict only under limited aims; preventive defection follows a credible threat with no continuity guarantee).

**Gate.** Hold-out tests pass without post-hoc guard edits; replay agreement at or above 80 percent on resource variables and belief flips within one quarter of the documented dates; transfer hypotheses committed.

**Gate record (2026-10-14): not passed as written; the protocol held.** (1) Hold-out: T11 and T12 pass under every hypothesis; T6 and T7 fail as read (the point of no return is the attack itself, 1941Q3, one quarter before the window; the embargo closes Japan's option after eight quarters but does not compel war). T3 passes, T9 fails (the attack on Poland is forced from 1939Q2 before any alliance can exist), T13 is degenerate under the registered predicate; T10's Japan control holds on v1. No guard, effect, delay, fairness constraint, profile or assume changed after first sight (commit 3d5c55e, 2026-10-13); the failures stand as computed, with amendments proposed for the owner in reports/ww2_v1.md section 13 and reports/ww2_v0.md section 14.1 (T8(b)'s kernel comparison, evaluated with the symbolic engine: not met, because under hegemonic aims the West leaves its kernel at the Rhineland). (2) Replay: the pipeline ran blind on 10,550 real FRUS documents; with the frozen rule backend the belief and commitment variables score below reading nothing and 4 of 9 flips land within a quarter, so the agreement criterion is not met; resource variables come from datasets and are not replayed from text; the Claude backend needs a credential on the owner's machine (reports/replay_ww2_frus.md). (3) Transfer hypotheses committed before any Cold War guard (docs/transfer_hypotheses.md). Framework items delivered: the symbolic engine with the v0 benchmark inside the hour (docs/engine_scaling.md; a compiled BDD core is the named next step for v1-sized forward reachability), snapshots with built-ins, the crisis sub-game flattening (spec section 14), the replay harness. The owner decides the amendments, as in phase 1; phase 3 can start on the framework side. Suite at the gate commit (slow tests included, 1 h 58 min): 857 passed, 15 skipped, 15 failed, every failure a registered claim failing as read (T6 six parametrizations, T7 five, T9 three, T8(b) one); `ruff check .` and `ruff format --check .` clean.

**Addendum (2026-10-16): the owner's decisions of 2026-10-15 executed.** T6, T7, T9, T13 and T8(b) amended (ww2_testbed.md section 11) and green under the amended wording; the "contested" reading settled (section 4.6); the harness rules adopted and re-measured on the real FRUS proposals (76 percent text agreement, belief flips unchanged at 4 of 9), with the Claude-backend run packaged for the owner's machine; the per-actor cadence added as framework change 1; the summer-1939 crisis sub-game built on the crisis machinery and run once (K2 re-asks T9 at 3-day resolution and holds on its three main clauses; reports/crisis_1939.md); July 1914 built at daily ticks with cadences from the decision record and run once under a total hold-out (J1, J2, J5 met; J3, J4, J6, J7 not; reports/july1914.md); the compiled BDD core delivered (about ten times the pure-Python speed on the v0 benchmark and 4.5 times the nodes per gigabyte; v1's forward reachability and its kernels inside the reachable set now fit; docs/engine_scaling.md section 7); the snapshot convention applied (seven levels moved to the model's own clock, listed in the two snapshot READMEs) and the German offer added as a documented, refused alternative with a speculative Soviet acceptance, both followed by a full rerun on 2026-10-16: 1016 passed, 15 skipped, 7 failed, the seven being the recorded crisis-model claims; no WW2 result moved except T7's option at the start tick, now open because the start state carries the alliance. The replay criterion still waits on the Claude backend. Amendments for the new failures are proposed in the two reports for the owner's decision.

**Addendum (2026-10-24): the Claude-backend replay and the owner's decisions of 2026-10-23.** The Claude backend ran blind over the 10,550 FRUS documents of 1936 to 1940 on the owner's machine (reports/replay_ww2_frus_claude/): at the proposal level, unreviewed, exact agreement on the text-derived variables 472/500 (94 percent; 97 with the harness rules off) against the target of 80 percent, and 8 of 9 documented flips within one quarter, 4 false flips. The replay criterion is met at the proposal level; the result after a human review, and so the gate, is the owner's. The amendments the owner accepted (docs/owner_decisions_2026-10-23.md) are executed: summer 1939 K1 to K6 pass as amended (the `oil_GER` snapshot change withdrawn on the owner's instruction); July 1914 J2, J4, J7 pass as amended, J3 fails as amended and stays, J6 waits for the 1914 v1, registered (J1v1 to J9v1) and built with its first sight held for the owner. A DeepSeek backend exists beside the Claude one (docs/replay_harness.md).

**Addendum (2026-10-28): the first sight of July 1914 v1.** J1v1 to J9v1 run once on the owner's go (decision 7e(b)) at c0c4460: J1v1, J2v1, J4v1, J5v1, J7v1, J9v1 pass; J3v1, J6v1 (its minimum of two relaxations holds; the set-membership clause fails), J8v1 (c) fail; reports/july1914_v1.md, with proposals for the owner.

**Open at exit (2026-10-17).** When the WW2 model is finished: work out where it and the human-SI relationship differ in kind (an SI carries no historical burden and may not be bound by the restrictions on human choices), starting from [ww2_si_disanalogies.md](ww2_si_disanalogies.md).

**Risk.** OCR noise and extraction drift in the corpora. Mitigation: resource variables come from datasets, and the extractor is scored only on the text-derived variables.

**Size.** 8 to 12 weeks.

---

## Phase 3: the Cold War, 1947 to 1991

**Goal.** Validate the framework on an episode with a different structure, under a logged framework-change budget.

**Work.**
- `models/cw/v0.py`: USA and USSR, with the PRC from 1969; annual ticks with nested crisis sub-games at daily or weekly resolution; blocs and proxies scripted with documented branch points.
- Hindsight snapshots per year from NMC, the nuclear-forces series, Maddison and the post-1991 revisions; replay snapshots from FRUS, the NIE series, the Wilson Center archive and the National Security Archive.
- Tests C1 to C13 as files; the transfer hypotheses from phase 2 run unchanged.
- Framework-change budget: at most five logged changes, each episode-agnostic (a change whose rationale names a historical episode is a domain-model change, not a framework change). Every change reruns the full WW2 suite.

**Gate.** C1 to C13 pass within the budget; the transfer hypotheses hold or their failure is explained as a model-content difference, not an engine defect; the WW2 suite still passes.

**Risk.** The budget is exceeded. Then the framework is revised, both suites are rerun, and the one-shot third episode in phase 4 becomes mandatory rather than optional.

**What it teaches for the AGI model.** Whether a held balance shows up as joint-kernel membership; whether the oversight lever and belief error behave as the AGI model assumes; whether capability stops mattering past a threshold.

**Gate record (2026-10-17): not passed as written; the protocol held.** Cold War v0 built (models/cw/v0.py, three crisis sub-games, hindsight snapshots 1947 to 1992 and a manual replay for C6 and C7; docs/ontology_cw.md, docs/actions_cw.md, docs/cw_v0_decisions.md). C1 to C13 run once at commit 6b87af9 (34 min 50 s): C1, C12, C13 pass; C2 to C11 fail as read (reports/cw_v0.md). Framework changes: 0 of 5. Transfer hypotheses: H3 and H6 held, H5 tested, H8 not tested, H1, H2, H4 and H7 failed or unsupported, each explained as model content or claim reading, none as an engine defect. The WW2 suite is unchanged (no framework change; this session's run: 1059 passed, 40 skipped, 7 failed, the seven the recorded crisis-model claims). The testbed's data hosts are blocked from the development environment, so no level is read from a series and the replay is manual (data/cw/README.md). One early sight close to C2 is disclosed (decisions D9). Proposed amendments and a cw_v1 for the owner's decision: reports/cw_v0.md section 18.

**Addendum (2026-10-24): the owner's decisions of 2026-10-23 on phase 3.** C2, C3, C4, C6, C8, C9 and C10 amended and C5 given the guard part `nato_attack` (a logged edit after first sight); the rerun gives C1, C12, C13 passing and C2 to C11 failing, also as amended (reports/cw_v0.md section 20): in v0 neither side has a war-forcing option against the other's restraint, so each can keep the peace alone, and beliefs and oversight move no unilateral kernel or distance. C5 stays as recorded (decision 5a). The PRC research and experiment (docs/prc_research.md, docs/prc_experiment.md) support the PRC as a principal from 1950 with a minimal action set. cw_v1 is registered (V1 to V10, docs/coldwar_testbed.md section 9) and its model step is in progress with first sight held for the owner. A blind replay on the CIA estimates (reports/replay_cw_crest_deepseek.md) reads the estimates' current force, not their projections, and does not reproduce the missile gap; the reading of `belief_force_USA` is the owner's. Framework changes in phase 3: the cadence counted as 1 of the budget (decision 4); the size of the increase the owner allowed is open.

**Size.** 10 to 14 weeks.

---

## Phase 4: generalization audit and framework freeze

**Goal.** Establish what the two episodes jointly support, and freeze the framework.

**Work.**
- The framework diff: every framework change made during phases 1 to 3, with the test that forced it.
- Ablations on both suites: remove the epistemic layer, the fairness constraints, the delays, the joint kernel; record which tests fail in which episode. A layer that no test needs is removed; a layer both episodes need is a structural finding.
- Cross-episode structural findings, stated as claims with the tests that support them.
- Optional, mandatory if the phase 3 budget was exceeded: the one-shot third episode, the July 1914 crisis (six weeks at daily ticks; a known outcome; a large counterfactual literature; mobilization schedules as pre-commitments, which is itself an automation analog). Its tests are registered before any 1914 guard is written and it is run once.
- The validity argument updated; the framework released as 1.0 with the three suites as its regression tests.

**Gate.** Framework 1.0 tagged; the findings and limitations documents committed; every suite passes on the tagged version.

**Size.** 3 to 4 weeks, plus 4 to 6 weeks if the 1914 episode runs.

---

## Phase 5: the AGI model v0

**Goal.** Instantiate the AGI domain model in the frozen framework and produce the first inclination report.

**Work.**
- The claims are registered in [agi_testbed.md](agi_testbed.md) (G1 to G22, 2026-10-17) before any guard, with the scenario tests as skipped files under `tests/agi/scenarios`; the ontology step fixes levels, thresholds and guard gating without editing the claims, every result is reported under the untested-mechanism sweeps, and an amended claim is a new registration (agi_testbed.md section 6).
- `models/agi/v0.py` as specified in DESIGN.md sections 2 and 3; every mechanism tagged `validated:ww2`, `validated:cw`, or `untested`.
- The first AGI snapshot with per-variable indicators, sources and mapping rules (DESIGN.md section 5).
- The brief's three scenarios and COEXIST as tests; the worked example in DESIGN.md section 7 confirmed or refuted.
- The first inclination report: kernel membership, distance to the boundary, minimal assumption sets per ending, pivotal coalitions, the untested-mechanism list on the front page.

**Gate.** The scenario tests run; the report exists with its untested list; the validity argument states what the historical episodes do and do not support for this model.

**Risk.** Reading the report as a forecast. Mitigation: the front page, and the rule that no bare reachability result is quoted.

**Size.** 4 to 6 weeks.

---

## Phase 6: live operation and extensions

**Goal.** Keep the AGI model current and extend coverage of the untested mechanisms.

**Work.**
- Quarterly snapshots from the live evidence pipeline with human review; drift reports; sensitivity reports naming the indicator that matters most this quarter.
- `models/agi/v1.py`: split human and lab actors, two AI systems; uniform-strategy synthesis for imperfect information; PRISM-games export for the quantitative layer, reported as intervals.
- A small third testbed for dependence lock-in with no adversary (the attention economy, 2008 to 2020), to move `DISEMPOWERMENT` from `untested` to validated.
- Periodic red-teaming of the rules; every framework change reruns the historical suites.

**Gate.** Ongoing; each quarter's report is the deliverable.

---

## Summary

| Phase | Role in the discipline | Gate in one line |
|---|---|---|
| 0 Theory and core | foundation | engine correct on known games; both test lists committed |
| 1 WW2 v0 | development | T1, T2, T4, T5, T8 pass under the anti-hindsight protocol |
| 2 WW2 v1 and replay | development, hold-out | hold-out tests pass; replay metrics met; transfer hypotheses committed |
| 3 Cold War | validation | C1 to C13 pass within the framework-change budget |
| 4 Audit and freeze | generalization | framework 1.0; findings and limitations committed; optional 1914 one-shot |
| 5 AGI v0 | deployment | first inclination report with its untested list |
| 6 Live operation | deployment | quarterly reports; untested mechanisms reduced over time |
