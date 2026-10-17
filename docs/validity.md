# Validity argument

This is the assurance case for the `wavefront` framework: a top claim, the sub-claims it rests on, the evidence for each, and the known gaps. It is updated at every phase gate (PHASES.md; PLAN.md steps 0.13, 4.5 and 5.6) and is the front page of every AGI report. Definitions are in [theory.md](theory.md), the contract in [framework_spec.md](framework_spec.md), and the registered tests in [ww2_testbed.md](ww2_testbed.md) §5, [coldwar_testbed.md](coldwar_testbed.md) §5 and [agi_testbed.md](agi_testbed.md) §5.

Status as of 2026-10-17: phases 0 to 2 assessed (section 9 has the gate entries); section 8 holds the status of every sub-claim. The AGI claims are registered before any guard ([agi_testbed.md](agi_testbed.md)); no AGI mechanism is validated, and the untested list of section 6 stands.

---

## 1. Top claim

> **G.** For a model expressed in the framework, the framework's outputs (reachability traces, kernel membership, forced distance, minimal relaxation sets, pivotal coalitions) are correct relative to the model, and the method is reliable on cases with the structural features listed.

"Correct relative to the model" means equal to the definitions in theory.md, applied to the compiled game. "Reliable" means that on historical models built under the protocol, the outputs land where the registered tests say they should. "The structural features listed" are those in section 6.

G is split into four sub-claims:

| Id | Sub-claim | Role in the argument |
|---|---|---|
| A | Engine correctness | the outputs mean what theory.md says they mean |
| B | Method reliability on historical cases | the meaning is useful on cases where the answer is known or argued |
| C | The anti-hindsight protocol | B is not an artifact of fitting the known outcome |
| D | The evidence pipeline | initial states come from dated evidence by a procedure that can be checked |

A alone gives correctness relative to the model. B, C and D together give reliability of the method. None of them gives the truth of any particular model (section 6).

---

## 2. A: engine correctness

**Claim.** For every model the DSL accepts, `explore`, `attractor`, `safe`, `contested`, `witness`, the BMC functions and the analysis functions return what their definitions in theory.md and the spec say.

| Id | Sub-claim | Evidence |
|---|---|---|
| A1 | The compiler implements spec §1 and §3: availability, effect composition, delays, latches, fairness counters, profiles, terminal states, error conditions | `tests/model/` (spec §11) |
| A2 | `attractor` and `safe` equal the fixpoints, and the returned strategies win | brute-force enumeration of memoryless coalition strategies on random tiny models (hypothesis: at most 3 actors, 2 actions each, at most 4 variables, horizon at most 4); hand-built games with known answers (`tests/engine/`) |
| A3 | `contested` returns the contested region of a non-determined game | a matching-pennies game whose result must be `contested` (spec §11) |
| A4 | `witness` returns shortest traces | `tests/engine/` |
| A5 | BMC `reach` agrees with explicit reachability within depth `k` | random small models, `tests/bmc/` (spec §6) |
| A6 | BMC `relax` returns minimum-cardinality relaxation sets, loosening only | size agreement with `relax_explicit` on models with at most 6 guards (spec §6) |
| A7 | Analysis functions match their definitions | hand-built games with known answers, `tests/analysis/` (PLAN.md 0.7) |
| A8 | Results agree with an independent checker | PRISM-games on the toy models once the exporter exists (PLAN.md step 6.3) |
| A9 | The engine scales to the phase 1 target | about 10^5 states explored in under 120 s (spec §11, `slow`) |

**Argument.** Theorems 1 to 4 in theory.md show that the fixpoints decide the logic fragment, that memoryless strategies suffice, and that a state excluded by a fixpoint has no winning strategy of any kind. A2 to A6 check that the code computes those fixpoints. A8 guards against an error shared by the code and the brute-force oracle, both written in this project.

**Gaps.**
- The brute-force oracle must enumerate state-based memoryless strategies. The fixpoints are perfect-information results; if the oracle enumerates observation-uniform strategies, it will disagree on models with hidden variables (theory.md §2).
- A8 waits for the PRISM-games exporter (phase 6); until then the only independent oracle is the brute-force enumeration written in this project.
- Random models are tiny. Bugs that need many actors, long horizons or many fairness constraints may survive. Hand-built games with those features are needed.
- The proofs in theory.md are sketches. They are not mechanized.
- Z3 is trusted. A5 and A6 cross-check it against the explicit engine, not against an independent solver.

**Status.** A1 to A7 and A9 met at the phase 0 gate (section 8); A8 waits on the PRISM-games exporter (phase 6).

---

## 3. B: method reliability on historical cases

**Claim.** On the WW2 and Cold War models, built under protocol C, the framework produces the registered outputs, including `contested` where the historiography is split.

| Id | Sub-claim | Tests |
|---|---|---|
| B1 | The realized trajectory is reachable with zero relaxations (a necessary condition, weak on its own) | T1, C1 |
| B2 | Documented alternatives are in the decision space, and their consequences come out as registered | T2, T5, C4, C5 |
| B3 | Questions the record leaves open come out `contested`, not forced | T3, T6, T9, C3, C4, C9 |
| B4 | Hidden objectives, lagging beliefs and objective-conditional levers behave as registered; belief error against dated ground truth is visible | T4, T8, C6, C7 |
| B5 | Resource-bound action and preventive defection under threat | T6, T7 |
| B6 | Institutional lag (fairness, profiles): a belief change precedes a response | T4, T11 |
| B7 | A held balance appears as joint-kernel membership outside the unilateral kernels; near misses leave and re-enter | C2, C3, C5, C10, C11 |
| B8 | Points of no return fall inside registered windows, name a driving variable, and are stable under refinement | T6, T13, C13 |
| B9 | Assumption mining discriminates: negative controls need the registered number of relaxations; informativeness at least 80 percent | T7, T10, C9, C12 |
| B10 | Pivotal coalitions match the registered ones, including a change with the actor set | T5, T9, C11 |
| B11 | Oversight and capability: verification widens the margin; capability past a threshold stops mattering; one capability discontinuity | C8, C10, T12 |
| B12 | An ending with no adversarial act (exhaustion) is reachable and its assumption set excludes the other side's actions | C9, C13 |
| B13 | Transfer hypotheses written at phase 2 exit hold on the Cold War unchanged, or their failure is explained as model content | PHASES.md phases 2 and 3; `docs/transfer_hypotheses.md` |

Every registered test, with the sub-claims it supports:

| Test | Sub-claims | Test | Sub-claims |
|---|---|---|---|
| T1 | B1 | C1 | B1 |
| T2 | B2 | C2 | B7 |
| T3 | B3 | C3 | B3, B7 |
| T4 | B4, B6 | C4 | B2, B3 |
| T5 | B2, B10 | C5 | B2, B7 |
| T6 | B3, B5, B8 | C6 | B4, D3 |
| T7 | B5, B9 | C7 | B4, D3 |
| T8 | B4 | C8 | B11 |
| T9 | B3, B10 | C9 | B3, B9, B12 |
| T10 | B9 | C10 | B7, B11 |
| T11 | B6 | C11 | B7, B10 |
| T12 | B11 | C12 | B9 |
| T13 | B8 | C13 | B8, B12 |

**Argument.** WW2 is a case where the balance broke. The Cold War is a case where it held. Both have known outcomes and argued counterfactuals. A method that reproduces the outcomes and places the debates in the right region (forced, blocked or contested), under a protocol that prevents tuning, is reliable on cases with the same structure. Two episodes are two samples. The one-shot July 1914 episode (PHASES.md phase 4) is the reserve.

**Gaps in the test definitions** (to resolve before the tests are written as code, PLAN.md 0.10, without weakening any claim):
- T7 ("{embargo maintained, `aims[JPN] ≠ status_quo`}") and C9 ("contains `econ_health` and `legit`") state assumption sets as variable conditions and strategy choices. The spec relaxes only guards and fairness constraints (theory.md §5.1). Either the modeled guards must carry these conditions, or relaxation must be extended to initial-value restrictions.
- C12 requires `ACCIDENTAL_WAR` to be "reachable with zero relaxations and forceable by no coalition". Reachability means the coalition of all actors with Nature can force it, so C12 must be read with `include_nature=False`.
- `contested` results depend on where Nature sits: it is always on the side opposite the queried coalition, so outcomes decided by Nature alone come out `blocked` (theory.md §3.5). T3, T6, T9, C3, C4 and C9 should name the coalition and Nature's placement.
- C8 ("the distance to the boundary increases") and DESIGN.md Q6 need a named distance. Against the rest, distance from inside a unilateral kernel is always undefined (theory.md §4.3, Lemma 5).
- C3 needs nested crisis sub-games (theory.md §7), which are scheduled for phase 2.

**Status.** WW2 and the two crisis episodes assessed at phases 1 and 2 (section 8): B1, B2, B4 and B11 partial (met for WW2, B4 with one deferral; the Cold War tests at phase 3); B6 met for WW2 and, for 1914, on the lag but not on the kernel tick; B3, B9 and B10 partial (WW2 and 1939 met as amended; 1914 J3 and J6 not met); B8 met as amended for WW2, 1939 and 1914 J2, J7 not met; B5 not met as registered; B7 and B12 planned for phase 3; B13 planned (written, with two historical anchors; tested at phase 3).

---

## 4. C: the anti-hindsight protocol

**Claim.** The historical results are not produced by tuning the model to the known outcome.

| Id | Sub-claim | Evidence |
|---|---|---|
| C1 | Tests are registered before any guard is written | ww2_testbed.md §11 and coldwar_testbed.md §8, both dated 2026-10-11, and agi_testbed.md §9, dated 2026-10-17; git history; test files with verbatim claims (PLAN.md 0.10; tests/agi/test_registration.py) |
| C2 | Decision spaces come from contemporaneous alternatives | `source=` on every action; `speculative=True` counted in the parameter budget and listed in reports (spec §3.1, §8) |
| C3 | A hold-out is respected | T6, T7, T11 and T12 run without guard edits after first sight; T3, T9 and T13 run with the contested and window criteria (PHASES.md phase 2) |
| C4 | Every guard edit after a failing test is logged | `docs/guard_changelog_ww2.md`, `docs/guard_changelog_cw.md` |
| C5 | The Cold War stays a validation set | at most five logged, episode-agnostic framework changes, each naming its forcing test and rerunning the WW2 suite (`docs/framework_changes.md`); the 1914 one-shot becomes mandatory if the budget is exceeded |
| C6 | Adding parameters does not buy fit | parameter budget reported with every result; informativeness must not fall when the budget rises (theory.md §5.4) |
| C7 | Negative controls run on every change | T10 and C12 in CI |

**Gaps.** The protocol constrains fitting but cannot remove hindsight from the people choosing decision spaces and level boundaries; the historian review is the mitigation. The tests and the model are written by the same team. Expected outputs that still say "refine at phase 3" (C13) may be refined only without weakening the claim.

**Status.** C1 met (phases 0 and 2, and the AGI registration of 2026-10-17); C3 met for WW2 v1, the 1939 sub-game and July 1914 (phase 2; no AGI run exists yet); C4, C6 and C7 met for phases 1 and 2; C2 partial (historian review pending); C5 planned for phases 3 and 4, with one framework change logged so far in docs/framework_changes.md, whether it counts against the budget being the owner's decision.

---

## 5. D: the evidence pipeline

**Claim.** Initial states come from dated evidence through a procedure whose accuracy is measured, and nothing changes a state without review.

| Id | Sub-claim | Evidence |
|---|---|---|
| D1 | Every snapshot level is traceable to an indicator, a source and a mapping rule | `snapshots/schema.json`; the loader refuses a variable with no indicator unless `confidence == "assumed"` (spec §9) |
| D2 | Replay is blind to the future | corpus filtered strictly by document date (ww2_testbed.md §6.2, §8) |
| D3 | Replayed snapshots agree with hindsight snapshots | WW2 1936 to 1940: at least 80 percent exact on resource variables; belief flips within one quarter of documented dates (ww2_testbed.md §9). Cold War: NIE-based belief replay (C6, C7) |
| D4 | The LLM extractor only fills a fixed schema, and a human reviews every level change | extractor and review CLI (PLAN.md 2.5) |

**Gaps.** Replay measures estimation of the current state, not prediction. For the AGI model there is no hindsight snapshot, so D3 cannot be measured there; it transfers only as a property of the procedure.

**Status.** D1 met (phase 0); D2 met in mechanics on the real FRUS replay; D4 met in mechanics, with no real proposal reviewed yet; D3 not met with the rule backend (the Claude backend waits on a credential on the owner's machine); the Cold War replay at phase 3.

---

## 6. What historical validation establishes and does not

If B, C and D pass, the method is shown reliable on cases with these structural features:
- hidden objectives and lagging beliefs about them (appeasement; the missile gap; the 1983 war scare);
- resource-bound action (oil and steel; economic staying power);
- preventive defection under threat with no continuity guarantee (Japan 1941; Germany 1939 and 1941);
- institutional lag between a belief change and a response (Britain after Prague; the United States after Pearl Harbor);
- balances held only under joint strategies, with near misses that return (deterrence 1965 to 1991; Cuba 1962);
- secondarily: verification regimes as oversight, an ending by exhaustion with no adversarial act, a changing actor set, and one capability discontinuity.

It does **not** establish the content of the AGI model. The AGI model's guards, levels, action sets and balance definition are hypotheses that no historical episode tests. Its mechanisms are tagged `validated:ww2`, `validated:cw` or `untested` (PHASES.md phase 5). After both episodes these remain untested:

| Untested mechanism | Why no episode covers it | Plan |
|---|---|---|
| Recursive capability growth | no historical actor improved its own capability in a loop; T12 and the Cold War jumps are single steps | carried as `untested`; every AGI result is reported under the sweep of agi_testbed.md section 6 item 3, which does not validate the mechanism |
| A copyable or exfiltrating actor | every historical principal was a single, located entity | carried as `untested`; every AGI result is reported under the sweep of agi_testbed.md section 6 item 3, which does not validate the mechanism |
| Dependence lock-in with no adversary (`DISEMPOWERMENT`) | both episodes end through adversarial or exhaustion dynamics | attention-economy testbed, 2008 to 2020 (PHASES.md phase 6) |
| Non-state principals (labs) | every principal in both episodes is a state | none yet |
| Overwhelming speed and information asymmetry | Ultra, Magic and satellite reconnaissance are partial asymmetry only | carried as `untested`; speed is swept (agi_testbed.md section 6 item 3), information asymmetry is fixed by the observation functions and not swept |

Two episodes, or three with 1914, are a small sample. Reliability on them is evidence about the method on similar structures, not a forecast and not a guarantee for structures they lack.

---

## 7. How to read a report

**The front-page caveat.** Every report opens with: "every result is conditional on the model version and the initial state; no bare reachability result is a finding" (spec §8). It is followed by this document's status table and, for the AGI model, the untested-mechanism list.

**Bare reachability is never a finding.** `EF E` says that some joint choice of every actor and of Nature reaches `E`. With nondeterministic actors almost every ending is reachable, and relaxing any assumption can only add paths (theory.md §4.4). A reachable ending is a starting point for the questions below, never a conclusion. "Unreachable" is meaningful, but only relative to the model.

**Minimal relaxation sets.** "E needs at least r relaxations, and these are the minimum sets" means: for `E` to become reachable within `k` ticks, at least `r` of the model's named guards or fairness constraints must fail, and each listed set suffices. Read it with:
- the depth `k`: a longer horizon can only lower `r`;
- the granularity: one guard counts as one assumption, however much it tests;
- the evidence: the useful question is whether current evidence supports the listed assumptions failing;
- the type of question: sets for reachability are well-defined by monotonicity; sets for forcing are not (theory.md §5.1).

**Kernel membership and distance.** "s is in C's kernel for φ" means `C` has a strategy keeping `φ` until a terminal state, whatever the others do. Read it with:
- the coalition: unilateral and joint kernels answer different questions, and a balance in the joint kernel only is kept only if all its members choose to keep it;
- information: kernel membership is computed with perfect information, so for a coalition that lacks observations it is an upper bound unless the report states that the uniformity check passed (theory.md §2);
- the horizon: states near the horizon are in kernels more easily;
- distance: the report names which distance it gives (theory.md §4.3). Against the rest, the distance from inside a unilateral kernel is undefined by construction.

The point of no return is the first state of a trace outside the kernel. The silent phase runs from there to the first visible violation of `φ`, split into a contested part and a lost part (theory.md §4.2).

**Pivotal coalitions.** The minimal coalitions, by inclusion, that can force or block `E` from every initial state considered. Several incomparable minimal coalitions can exist. When a hidden variable is swept, check whether the result is stated across all its values or per value, and whether Nature was a candidate member.

**`contested`.** Neither the coalition can force the result nor the rest can prevent it. Whoever commits first can be refuted (theory.md §3.5). It does not mean even odds, and it is not a failure of the tool: it marks where the model alone does not decide and real-world evidence has to carry the argument. Nature always sits with the side opposite the queried coalition, so an outcome decided by chance alone shows as `blocked` for the coalition, not `contested`.

**Speculative actions.** The report lists every speculative action used by any reported trace. A result that disappears when they are removed rests on actions with no contemporaneous source.

---

## 8. Status

| Id | Claim | Evidence | Status | Assessed at |
|---|---|---|---|---|
| A1 | Compiler implements the semantics | `tests/model/` (74 tests: errors, composition, delays, latches, fairness, profiles, monotone, observation); reviewer's hand-checked model | met | phase 0 |
| A2 | Fixpoints and strategies correct | brute-force enumeration of all memoryless strategies on 246 random models (67,125 strategies) plus 300 hypothesis examples per check; layered-definition check; mutation check caught five planted solver bugs; hand-built chain for ranks | met | phase 0 |
| A3 | Contested region correct | matching pennies comes out contested for reach and keep; random cases confirm forced and blocked never overlap | met | phase 0 |
| A4 | Witnesses shortest | witness length equals the all-actor reachability rank on random models | met | phase 0 |
| A5 | BMC reach agrees with explicit | random models from two generators (200 hypothesis examples plus 200-seed sweeps each): trace length equals the explicit rank and every trace replays; 77 expression-node tests against `cm.evaluate`; 9 planted encoder bugs caught; reviewer's hand-checked queries | met | phase 0 |
| A6 | BMC relax minimum sizes correct | brute force over all assumption subsets on 120 hypothesis models plus a 120-seed sweep (at most 6 assumptions): exact minimum sets match; explicit and bounded agree on the toy model | met | phase 0 |
| A7 | Analysis functions correct | 53 tests on hand-built games with known answers (kernels, silent phase indices, margin against the literal iteration, pivotal antichains, relaxations including forceability and ill-formed sets, per-member uniformity); 33 toy demonstrations | met | phase 0 |
| A8 | Independent checker agrees | PRISM-games cross-check once the exporter exists (PLAN step 6.3) | planned | phase 6 |
| A9 | Scale | 110,670 states with 8.5e6 joint moves explored in about 25 s; attractor 3.7 s, safe 2.7 s | met | phase 0 |
| B1 | Realized trajectories reachable | T1 met (the 1936 to 1940 decision sequence replays with every action available, zero relaxations); C1 | partial (WW2 met) | phases 1, 3 |
| B2 | Documented alternatives behave as registered | T5 met; T2 met in its amended conditional form, with the tick-0 hegemonic result recorded (reports/ww2_v0.md sections 4 and 13); C4, C5 | partial (WW2 met) | phases 1, 3 |
| B3 | Split questions come out contested | T3 met under both hypotheses. T6 and T9 as amended on 2026-10-15 (the fortune sense of ww2_testbed.md section 4.6): T6 met under `fight_on`; T9 re-asked in the summer-1939 sub-game, where K2's conditional holds and "otherwise contested" holds only in the fortune sense (reports/crisis_1939.md section 10). July 1914: J3's localization is forceable only with Vienna in the coalition, Britain never pivotal (reports/july1914.md section 6); C3, C4, C9 | partial (WW2 and 1939 met as amended; 1914 J3 not met) | phases 2, 3 |
| B4 | Hidden objectives and beliefs | T4 met; T8(a) met, T8(b) met as the load-bearing-obligation result with the kernel comparison deferred to phase 2 (report sections 7 and 13); C6, C7 | partial (WW2 met, one deferral) | phases 1, 3 |
| B5 | Resource bounds and preventive defection | T6: Germany cannot force the eastern conquest; the point of no return is the attack itself (1941Q3), one quarter before the registered window, and no later variable restores the kernel. T7: the oil clock closes Japan's option to attack after eight quarters under the embargo but compels nothing (Japan's documented "Option 1" stays open), so "unavoidable" is not met and the minimal assumption set is empty (reports/ww2_v1.md sections 5, 6) | not met as registered (WW2); the mechanisms are visible | phase 2 |
| B6 | Institutional lag | T4 met (phase 1). T11 met under every `aims_JPN` (reports/ww2_v1.md section 9). July 1914, J4: Berlin's belief that Britain fights flips on 29 July and the earliest Viennese acceptance of the Halt is visible on 1 August, a two-day lag set by Vienna's decision cadence; but the kernel is left on the day of the flip, not inside the lag (reports/july1914.md section 7) | met (WW2); 1914 met on the lag, not on the kernel tick | phases 1, 2 |
| B7 | Joint balances and near misses | C2, C3, C5, C10, C11 | planned | phase 3 |
| B8 | Point-of-no-return windows, stable under refinement | T6 as amended: t_K = 1941Q3, the attack itself, inside the amended window; the driving variables are the attack's own preconditions. T13 as amended: 1936Q2 under hegemonic aims and 1939Q3 under revisionist aims, stable from v0 to v1 within two quarters, with the driving variable found at the departure state. 1939 sub-game, K3: the alliance stops being possible with the decisions of 19 to 21 August as registered, the driving variable a three-way tie. July 1914, J2: every coalition without Russia leaves the kernel at the Russian general order of 30 July, inside the window as read; the coupling of mobilization and war is the driving constraint (relaxed, the departure moves by three days); from 28 June the kernel is left on 20 July. J7: the cadence asymmetry moves the response lag, not the kernel boundary; C13 | met as amended (WW2, 1939, 1914 J2); J7 not met | phases 2, 3 |
| B9 | Assumption mining discriminates | T10 met on v0 and v1 (one minimal set, the constraint the record never lifts). T7 as amended: Japan's option under the oil clock, met. K5 (1939): the attack before 26 August needs exactly the readiness part, minimum size 1. J6 (1914): a general war by 15 July needs one relaxation, the sequencing part of the German mobilization, a content gap; both controls are below the three-or-more informativeness target of ww2_testbed.md section 9; C9, C12 | partial (T10, T7 met; K5 met at size 1; J6 not met) | phases 1 to 3 |
| B10 | Pivotal coalitions | T5 met (phase 1). T9 at quarterly resolution: nothing blocks (recorded); re-asked in the 1939 sub-game, K2: {WEST, USSR} with Polish passage granted is the only minimal blocking coalition under the belief condition, on the profile `deterred`. July 1914: J5 met (the Belgian route forces British entry within two days; without it the minimal relaxations are the Belgian route and the naval assurance); J3 not met ({GER, RUS} never pivotal, Vienna always in the minimal coalition); C11 | partial (T5, K2, J5 met; J3 not met) | phases 1 to 3 |
| B11 | Oversight and capability thresholds | T12 met under every `aims_JPN`: the bomb ends the war whatever Japan's aims, and only for a programme decided at least 13 ticks before the event (the claim's 12 is implied; reports/ww2_v1.md section 10); C8, C10 | partial (WW2 met) | phases 2, 3 |
| B12 | Exhaustion with no adversarial act | C9, C13 | planned | phase 3 |
| B13 | Transfer hypotheses hold | `docs/transfer_hypotheses.md` written before any Cold War guard; phase 2 results bear on H3 and H8 (reports/ww2_v1.md section 15); July 1914 J2 and J7 bear on H3 (the point of no return set by a pre-commitment clock; speed asymmetry acting on the response lag, reports/july1914.md section 11); Cold War suite | planned (written; two historical anchors) | phases 2 (written), 3 (tested) |
| C1 | Tests before guards | testbed changelogs; the skipping test files under `tests/ww2/scenarios` and `tests/coldwar/scenarios` (phase 0); the 1939 sub-game claims K1 to K6 and the July 1914 claims J1 to J7 registered as documents and skipped tests before any guard (commit 7e533d4, 2026-10-15); the AGI registration (agi_testbed.md claims G1 to G22, an id space distinct from this document's sub-claims) as `docs/agi_testbed.md` and skipped tests under `tests/agi/scenarios` before any AGI guard (2026-10-17), with `tests/agi/test_registration.py` checking that the files carry the section 5 rows verbatim and stay skipped until first sight is recorded | met | phases 0, 2 (the AGI registration of 2026-10-17, ahead of phase 5) |
| C2 | Contemporaneous decision spaces | every WW2 action carries a dated record as `source=`; one speculative action; historian review pending | partial | phases 1, 3 |
| C3 | Hold-out respected | WW2 v1: first sight on 2026-10-13 at 3d5c55e, no guard edit after it until the owner's logged decision 1 of 2026-10-15 (the German offer, with sources and a full rerun). 1939 sub-game: K1 to K6 run once at f00e5be, no edit after. July 1914: J1 to J7 run once at f00e5be under a total hold-out, no edit after; the four failures stand. Both single runs reproduced by the architect | met (WW2, 1939, 1914) | phase 2 |
| C4 | Guard edits logged | docs/guard_changelog_ww2.md (phase 1, the v1 rows before first sight, the 1939 sub-game's model-step and first-run rows, and the owner-directed German offer after first sight with its sources) and docs/guard_changelog_1914.md (the model step and the single-run marker); no edit changed a registered outcome except as logged | met for phases 1 and 2 | phases 1 to 3 |
| C5 | Framework-change budget kept | `docs/framework_changes.md` | planned | phases 3, 4 |
| C6 | Budget does not buy fit | v1 budget reported (84 guards, 202 parts, 8 hypothesis gates, 2 speculative actions, 7 delays, 4 fairness constraints, 5 profiles, 1 assume); informativeness over the non-vacuous controls 1 of 1 on v1 (3 of 3 on v0); no parameter was added to pass a test, and three registered claims fail as read | met for phases 1 and 2 | phases 1 to 3 |
| C7 | Negative controls in CI | T10 runs in the suite on v0 and, as the Japan content control, on v1 (`slow`-marked, 322 s); G11 once `models/agi/v0.py` exists (agi_testbed.md section 6 item 6) | met for phases 1 and 2 | phases 1 to 3 |
| D1 | Snapshot provenance | strict JSON Schema plus hand-written validator cross-checked against `jsonschema` on a 1,715-document mutation corpus; loader refuses missing provenance, unknown levels and unfixed swept variables; 93 tests | met | phase 0 |
| D2 | Blind replay | FRUS 1936 to 1940 (12 volumes, 10,550 documents from a pinned mirror commit) replayed quarter by quarter with the corpus filtered strictly by dateline; the editors' bracketed insertions, which carry later facts into earlier documents, are stripped (reports/replay_ww2_frus.md; docs/replay_harness.md) | met in mechanics (WW2) | phase 2 |
| D3 | Replay agreement | rule backend on real FRUS, proposal level, nothing reviewed: text variables 356/500 (71 percent) against 305/500 for reading nothing; the belief and commitment variables below the reading-nothing baseline; 4 of 9 documented belief and commitment flips within a quarter; resource variables come from datasets and are not replayed from text. The registered criterion is not met by the rule backend; the Claude backend needs a credential on the owner's machine (reports/replay_ww2_frus.md) | not met (WW2, rule backend) | phases 2, 3 |
| D4 | Extraction reviewed | the extractor emits only schema-valid proposals with verbatim quotes and document ids; the review step is the only writer of replay snapshots and refuses auto-acceptance outside the synthetic corpus; `--measure-proposals` measures unreviewed proposals without writing a snapshot (tests/evidence) | met in mechanics; no real proposal reviewed yet | phase 2 |

## 9. Change log

- 2026-10-17: the review of status and roadmap against the project's goal (docs/review_2026-10-17.md); the AGI claims G1 to G22 registered before any guard (docs/agi_testbed.md; C1); the status line of the preamble and those of sections 2 to 5 aligned with section 8; C1's evidence and assessed-at columns extended to the AGI registration. No status changed.
- 2026-10-16: the owner's decisions of 2026-10-15 executed: T6, T7, T9, T13 and T8(b) amended and their tests green under the amended wording; the summer-1939 crisis sub-game (K1 to K6) and July 1914 (J1 to J7) each run once under their hold-outs; B3, B8, B10 partial-to-met as amended, B6 met on the lag, B9 partial (two controls at size 1), B13 with two historical anchors for H3; C1, C3, C4 met for the new registrations; framework change 1 (per-actor cadence) logged in docs/framework_changes.md.
- 2026-10-14: phase 2 (WW2 v1, both theatres to 1945Q3; the symbolic engine; the real FRUS replay; crisis sub-games) assessed under the registered wording: B6 and B11 met for WW2; B3, B9 and B10 partial; B5 and B8 not met as registered (T6's point of no return one quarter before the window; T7's war avoidable; T13 degenerate); C3, C4, C6 and C7 met for phase 2 (no post-hoc guard edit); D2 and D4 met in mechanics, D3 not met with the rule backend. The T8(b) kernel comparison is not met (reports/ww2_v0.md section 14.1). Amendments are proposed for the owner in reports/ww2_v1.md section 13; no claim was edited.
- 2026-10-12: phase 1 (WW2 v0, Europe 1936 to 1940) assessed under the original wording: B1, C4 and C7 met for WW2; B2, B4 and C2 partial; B9 not met (reports/ww2_v0.md sections 4 to 8).
- 2026-10-12: the owner amended T2, T8 and T10 (ww2_testbed.md section 11) and settled the China-incident semantics and the readiness calibration; under the amended claims every phase 1 test passes and the gate is passed with T8(b) deferred to phase 2 (report section 13).
- 2026-10-11: A1 to A4 and A9 assessed as met after the phase 0 engine review (commit 5d60ccc).
- 2026-10-11: A5, A6, A7 and D1 assessed as met after the wave 2 review. Phase 0 gate passed: engine correct on known games, the DSL covers the requirement list, both historical test lists are committed as test files, the budget and informativeness instrumentation exists, and `pytest`, `ruff check` and `ruff format --check` are clean (373 passed, 26 skipped). Gate commit: 5128836 (a local tag `phase0` points at it; the remote refused the tag push, so tag it on the main repository when merging).

- 2026-10-11: created in phase 0. All sub-claims planned except C1 (partial). Gaps recorded in sections 2 and 3.
