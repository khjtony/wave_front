# Detailed step plan

This expands [PHASES.md](PHASES.md) into steps. Each step has a goal, inputs, outputs, an acceptance check, and an owner. "Agent" means an implementation agent working to a written brief; "review" means a human or the orchestrating reviewer reads the output and runs the checks before anything is committed. A step is done when its acceptance check passes, not when its files exist.

Owner legend: A = implementation agent, R = reviewer (reads, runs, decides), H = historian reviewer (part time), U = project owner (decisions only they can make).

---

## Phase 0: theory and framework core

Gate: engine correct on known games; DSL covers the requirement list; both historical test lists committed as test files; instrumentation exists; `pytest`, `ruff check`, `ruff format --check` clean.

| Step | Goal | Inputs | Outputs | Acceptance | Owner |
|---|---|---|---|---|---|
| 0.1 | Fix the contract | DESIGN.md, PHASES.md, both testbeds | `docs/framework_spec.md`, `CLAUDE.md` | spec covers every DSL construct the registered tests need: hidden init, observation, delays, latches, bounded fairness, profiles, endings, joint and unilateral kernels, multi-resolution hook | R (done) |
| 0.2 | DSL and compiled model | spec sections 3 and 4 | `wavefront/model/*`, `tests/model/*`, `pyproject.toml` | compile-time and explore-time errors as specified; effect composition, delays, latches, fairness counters, profiles, monotone checks all unit-tested | A, then R |
| 0.3 | Explicit engine | spec section 5 | `wavefront/engine/*`, `tests/engine/*` | `attractor` and `safe` match brute-force enumeration of memoryless uniform strategies on random tiny models; a non-determined game comes out contested; witnesses are shortest; 1e5 states explored in under 120 s | A, then R |
| 0.4 | Theory note | spec, DESIGN.md | `docs/theory.md` | definitions match the spec exactly; soundness and sufficiency of memoryless strategies stated with proof sketches; contested region, kernels, point of no return, distance, assumption mining, bounded fairness, multi-resolution hook, clustering all defined | A, then R |
| 0.5 | Validity argument | PHASES.md, both testbeds | `docs/validity.md` | every sub-claim has named evidence and a status; the untested-mechanism list is present; the "how to read a report" section exists | A, then R |
| 0.6 | Bounded model checker | spec section 6, the compiled model | `wavefront/bmc/*`, `tests/bmc/*` | `reach` agrees with explicit reachability within k on random small models; `relax` minimal sizes agree with brute force on models with at most 6 guards; relaxations are loosening only | A, then R |
| 0.7 | Analysis layer | spec section 7 | `wavefront/analysis/*`, `tests/analysis/*` | viability, point of no return, distance, pivotal, relax_explicit, sensitivity, cluster, budget, informativeness each tested on hand-built games with known answers | A, then R |
| 0.8 | Report and CLI | spec sections 8 and 10 | `wavefront/report/*`, `wavefront/cli.py`, `tests/report/*`, `tests/cli/*` | report sections in the specified order with the front-page caveat; every CLI subcommand runs on the toy model; exit code 2 on ModelError | A, then R |
| 0.9 | Domain-neutral toy model | spec, DESIGN.md section 7 | `models/toy/two_power.py`, `tests/toy/*` | exercises every DSL construct; the engine shows concession removing conflict only under limited aims and a belief flip preceding a response by the fairness lag, as engine demonstrations (not findings) | A, then R |
| 0.10 | Registered tests as files | both testbeds | `tests/ww2/scenarios/test_T01.py` to `test_T13.py`, `tests/coldwar/scenarios/test_C01.py` to `test_C13.py` | each file carries the claim, the expected output and the sources verbatim from the testbed docs, and skips with reason "model not built" | A, then R |
| 0.11 | Snapshot schema and loader | spec section 9, DESIGN.md section 5.1 | `snapshots/schema.json`, `wavefront/evidence/*`, `tests/evidence/*` | schema validates the DESIGN.md example; loader refuses missing provenance; unknown level is an error | A, then R |
| 0.12 | Integration review | everything above | fixes; `docs/spec_deviations.md` resolved into the spec or rejected | full suite green; lint clean; spec and code agree; reviewer has read every public module | R |
| 0.13 | Gate record | 0.12 | `docs/validity.md` status rows updated; tag `phase0` | gate criteria listed in PHASES.md all checked | R, U |

Wave plan for agents: 0.2 and 0.3 as one agent (the engine depends on the compiled model's API); 0.4 and 0.5 as one agent in parallel; after review of 0.2 and 0.3, run 0.6, 0.7 plus 0.8, and 0.9 plus 0.10 plus 0.11 as three parallel agents; then 0.12 and 0.13.

---

## Phase 1: WW2 v0, Europe 1936 to 1940

Gate: T1, T2, T4, T5 and T8 pass under the anti-hindsight protocol; negative controls need three or more relaxations where registered; informativeness at or above 80 percent; reachable set at or under 1e6 states (or the BMC path is used and documented).

| Step | Goal | Inputs | Outputs | Acceptance | Owner |
|---|---|---|---|---|---|
| 1.1 | Ontology | ww2_testbed.md section 4.2 | `docs/ontology_ww2.md` | every variable has levels, threshold rules with a source, and the hindsight indicator it is read from | A draft, H review |
| 1.2 | Action catalogue | ww2_testbed.md section 4.3, Kershaw, Weinberg, Tooze, FRUS, Hansard, Cabinet papers | `docs/actions_ww2.md` | every action has a guard, effect, delay, and a citation to a contemporaneous debate; speculative actions tagged; count reported | A draft, H review |
| 1.3 | Dataset loaders | NMC v7, ICB v16, MID, Harrison tables, Minerals Yearbook extracts | `wavefront/evidence/datasets/*`, `data/ww2/README.md` with licenses and download scripts | loaders produce per-year tables with provenance; hand-entered tables carry page references | A, then R |
| 1.4 | Hindsight snapshots | 1.1, 1.3 | `snapshots/ww2/hindsight/1936Q1.json` to `1940Q4.json` | every level traceable to an indicator; quarterly interpolation flagged | A, then R |
| 1.5 | Model code | 1.1, 1.2 | `models/ww2/v0.py` | compiles; reachable set size and parameter budget reported; speculative actions listed | A, then R |
| 1.6 | Tests T1, T2, T4, T5, T8, T10 | 1.5, test files from 0.10 | the test files un-skipped; `docs/guard_changelog_ww2.md` | every guard edit after a failing test logged with rationale | A, R, H |
| 1.7 | Phase report | 1.6 | `reports/ww2_v0.md` | traces for each passing test, informativeness, budget, lessons for the AGI model | R |

---

## Phase 2: WW2 v1 and the replay harness

Gate: hold-out tests pass without post-hoc guard edits; replay agreement at or above 80 percent on resource variables and belief flips within one quarter; transfer hypotheses committed.

| Step | Goal | Inputs | Outputs | Acceptance | Owner |
|---|---|---|---|---|---|
| 2.1 | v1 ontology and actions | 1.1, 1.2, Pacific sources (Ike, Sagan, Iriye) | `docs/ontology_ww2.md`, `docs/actions_ww2.md` extended | same standards as 1.1 and 1.2 for both theatres, 1933 to 1945 | A draft, H review |
| 2.2 | Engine scaling | 0.3, 0.6 | symbolic or BMC path for 1e7+ states; the multi-resolution macro-transition implemented (demanded by C3); a Rust port decision recorded in `docs/engine_scaling.md` | the v1 model's registered questions answer within hours on one machine | A, then R |
| 2.3 | Hold-out tests | T6, T7, T11, T12, plus T3, T9, T13 | test files un-skipped | no guard edits after first sight without a logged rationale and a full rerun | A, R, H |
| 2.4 | Corpora indices | FRUS, Hansard, Chronicling America, Trove | `wavefront/evidence/corpora/*` with date filters; `data/ww2/corpora/README.md` | every document carries a date; a document without one is excluded | A, then R |
| 2.5 | Extractor and review CLI | DESIGN.md section 5.3, snapshot schema | `wavefront/evidence/extract.py`, `wavefront/evidence/review.py` | the extractor only emits schema-valid proposals with quotes and URLs; nothing changes a snapshot without review | A, then R |
| 2.6 | Blind replay 1936 to 1940 | 2.4, 2.5, 1.4 | `snapshots/ww2/replay/*.json`, `reports/replay_ww2.md` | agreement and belief-flip-lag metrics as in ww2_testbed.md section 9 | A, then R |
| 2.7 | Transfer hypotheses | 1.7, 2.3 | `docs/transfer_hypotheses.md` | written before any Cold War guard; each hypothesis names the Cold War claim that tests it | R, H |

---

## Phase 3: the Cold War, 1947 to 1991

Gate: C1 to C13 pass within a budget of five logged, episode-agnostic framework changes; transfer hypotheses hold or their failure is explained as model content; the WW2 suite still passes.

| Step | Goal | Inputs | Outputs | Acceptance | Owner |
|---|---|---|---|---|---|
| 3.1 | Ontology and actions | coldwar_testbed.md sections 3 and 4; Gaddis, Trachtenberg, Zubok, FRUS, CWIHP | `docs/ontology_cw.md`, `docs/actions_cw.md` | same standards as phase 1 | A draft, H review |
| 3.2 | Datasets | nuclear-forces series, Maddison and post-1991 revisions, NIE series index | loaders and `data/cw/README.md` | belief data (NIEs, CIA estimates) kept separate from hindsight truth | A, then R |
| 3.3 | Snapshots | 3.1, 3.2 | `snapshots/cw/hindsight/1947.json` to `1991.json`; replay snapshots | provenance as in phase 1 | A, then R |
| 3.4 | Model code with crisis sub-games | 3.1, 2.2 | `models/cw/v0.py` and `models/cw/crises/*.py` | compiles; the sub-games for Berlin 1948, Cuba 1962 and Able Archer 1983 run and lift results to annual transitions | A, then R |
| 3.5 | Tests C1 to C13 and transfer hypotheses | 3.4, 2.7 | test files un-skipped; `docs/guard_changelog_cw.md`; `docs/framework_changes.md` | each framework change names the forcing test and confirms the WW2 suite passes | A, R, H |
| 3.6 | Phase report | 3.5 | `reports/cw_v0.md` | budget usage, transfer results, lessons | R |

---

## Phase 4: generalization audit and freeze

Gate: framework 1.0 tagged; findings and limitations committed; every suite passes on the tagged version.

| Step | Goal | Inputs | Outputs | Acceptance | Owner |
|---|---|---|---|---|---|
| 4.1 | Framework diff | `docs/framework_changes.md`, git history | `reports/framework_diff.md` | every framework change since phase 0 listed with its forcing test | R |
| 4.2 | Ablations | both suites | `reports/ablations.md` | each layer (epistemic, fairness, delays, joint kernel) removed in turn; failing tests per episode recorded; unneeded layers removed | A, then R |
| 4.3 | Structural findings | 1.7, 3.6, 4.2 | `docs/findings.md` | each finding states the tests in both episodes that support it | R, H |
| 4.4 | One-shot 1914 episode (optional; mandatory if the phase 3 budget was exceeded) | Clark 2012, the July crisis document collections | `docs/1914_testbed.md` with tests registered before guards; `models/1914/v0.py`; one run | run once, results recorded whatever they are | A, R, H, U decides |
| 4.5 | Validity update and release | all | `docs/validity.md` statuses; tag `v1.0` | regression suite is the three historical suites | R, U |

---

## Phase 5: the AGI model v0

Gate: scenario tests run; the first inclination report exists with its untested-mechanism list; validity.md states what the episodes do and do not support for this model.

| Step | Goal | Inputs | Outputs | Acceptance | Owner |
|---|---|---|---|---|---|
| 5.1 | AGI ontology | DESIGN.md sections 2 and 3 | `docs/ontology_agi.md` | every variable, level boundary, action, guard and effect with a rationale; each mechanism tagged `validated:ww2`, `validated:cw`, or `untested` | A draft, R |
| 5.2 | Indicators and first snapshot | DESIGN.md section 5.2 | `docs/indicators.md`, `snapshots/agi/<date>.json` | every level has an indicator, a source and a mapping rule; no invented numbers | A draft, R, U for judgment calls |
| 5.3 | Model code | 5.1 | `models/agi/v0.py` | compiles; budget reported | A, then R |
| 5.4 | Scenario tests | DESIGN.md section 8 | `tests/agi/scenarios/*` | the brief's three scenarios reachable under stated assumptions and blocked when the named assumption is removed; COEXIST reachable | A, then R |
| 5.5 | Worked example check | DESIGN.md section 7 | `reports/agi_worked_example.md` | each hypothesis in section 7 marked confirmed or refuted with traces | R |
| 5.6 | First inclination report | 5.2 to 5.5 | `reports/agi_<date>.md` | front-page caveat and untested list present; no bare reachability result quoted | R, U |

---

## Phase 6: live operation and extensions

Gate: ongoing; each quarter's report is the deliverable.

| Step | Goal | Outputs | Acceptance | Owner |
|---|---|---|---|---|
| 6.1 | Live evidence pipeline | quarterly `snapshots/agi/*.json`, drift and sensitivity reports | human review on every level change | A, R, U |
| 6.2 | AGI v1 | `models/agi/v1.py`: split actors, two AIs; uniform-strategy synthesis | the v0 tests still pass; new mechanisms tagged | A, then R |
| 6.3 | Quantitative layer | PRISM-games export, interval results | qualitative results unchanged by the export | A, then R |
| 6.4 | Lock-in testbed | `docs/lockin_testbed.md`, `models/lockin/v0.py`, registered tests | moves `DISEMPOWERMENT` from `untested` to validated, or records why not | A, R, H |
| 6.5 | Red-team cadence | `reports/redteam_<date>.md` | missing actions found are logged and either added with a source or recorded as speculative | A, R |

---

## Working rules for every step

- The brief for an agent names the files it owns, the spec sections it implements, and what to report. Agents do not commit; the reviewer commits after reading the code and running the checks.
- A step that needs a spec change records the change in the same commit with the reason.
- Historical steps are never done by an agent alone: the historian reviewer signs off on sources and levels.
- Every phase gate updates `docs/validity.md`.
