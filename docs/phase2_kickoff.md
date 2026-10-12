# Phase 2 kickoff: WW2 v1 and the replay harness

Owner's instruction: go for phase 2 (2026-10-12). This document fixes the decisions the phase 2 agents build against. Steps are PLAN.md 2.1 to 2.7 plus the two framework items phase 1 demanded. Gate: PHASES.md phase 2.

## Environment facts that shape the plan

- The document corpora hosts (FRUS, Hansard, Chronicling America, Trove) and the dataset hosts are blocked from this environment by policy. Code that reads them is written against their published formats, tested on fixtures, and run for real on the owner's machine through fetch scripts.
- No Claude API credential exists in this environment and the SDK is not installed. The extraction backend is written to the Claude API reference, imported lazily, and exercised through a fake backend in tests.
- No binary decision diagram library installs here. The symbolic engine carries its own small BDD implementation, which also keeps the core free of third-party dependencies.

## Framework decisions

### F1. Symbolic engine (PLAN step 2.2)

The reachable space of WW2 v0 from 1936 exceeds three million states, and v1 is larger. Kernel questions from early states (T2, T8, T13, T3, T9) need an engine that does not enumerate. Decision: an in-house reduced ordered BDD package (`wavefront/symbolic/bdd.py`) and a symbolic encoding of compiled models (`wavefront/symbolic/encode.py`) with per-variable partitioned transition relations and action variables per actor, over which the controllable predecessor `∃ C-moves ∀ other moves` and the attractor and safety fixpoints are computed (`wavefront/symbolic/solve.py`). Results are membership predicates and counts; witnesses are extracted by stepping the explicit model under the symbolic strategy. Correctness is established by cross-checks against the explicit engine on random models, the toy model, and WW2 v0 from late states whose exact kernels are known (1938Q3: 198,443 states; 1938Q2: 1,423,926). The benchmark is V_WEST for `balance_europe` from the tick-0 state of WW2 v0 under both hypotheses and the T13 per-quarter sweep. If the pure-Python engine cannot do that within an hour on one machine, the step reports so and names the next step (a compiled BDD core); the sufficiency checks of phase 1 remain the fallback.

The Rust port decision (PLAN 2.2) is recorded as: not now. The explicit engine's limit is the size of the reachable set, not its speed, and a faster enumerator does not change that; the symbolic engine is the right investment. Revisit only if the symbolic engine fails on the benchmark.

### F2. Snapshots carrying pending decisions

Phase 1's T8(b) could not be evaluated because snapshot states carry no built-in counters (pending delayed decisions, last actions, latches, fairness counters). Decision: the snapshot schema gains an optional `builtins` section, `{name: {value, confidence, indicators, rule}}`, where `name` is a built-in variable of the model (`pending_<actor>_<action>` with the remaining ticks, `last_<actor>` with an action name, a latch with its level, `fair_<name>` with its count). The loader fills these into the state and refuses unknown built-in names; the ordinary `variables` section still cannot set built-ins. The hindsight builder computes them from a new decision-record file `data/ww2/decisions_ww2.csv` (`date, quarter, actor, action, delay_ticks, source, note`, one row per dated decision with a delay) and from `data/ww2/realized_moves.csv` (last actions), with provenance per entry. Pending at the end of quarter Q for a decision in quarter t with delay d is `max(0, d - (index(Q) - index(t)))`. Latches are read from the events; fairness counters default to 0 with confidence `assumed`.

With that in place, the amended T8(b) is evaluated: WEST's kernel for `balance_europe` from the 1938Q2 and 1938Q3 states with their built-ins, under hegemonic aims, by the explicit engine, and reported in `reports/ww2_v0.md` section 14.

## Domain decisions

### D1. v1 scope (PLAN 2.1)

v1 covers both theatres from 1936Q1 (tick 0) to 1945Q3 (horizon 39). The testbed's "1933 to 1945" is narrowed at the front: nothing registered depends on 1933 to 1935, and twelve extra ticks of rearmament prelude only enlarge the state space. The narrowing is logged in the testbed changelog as a clarification. Europe keeps v0's actors and adds the 1941 to 1945 mechanisms the registered tests need (Barbarossa and the Eastern front, the Western front of 1944, exhaustion, the United States as a belligerent); the Pacific adds Japan's decisions (the China war already present, the southern advance, the oil embargo and its clock, the decision for war, the naval campaign) and the atomic program. The hidden objectives gain `aims_JPN` (status_quo, regional, hegemonic). Everything is kept at the altitude of v0: a region is a level, a campaign is a Nature resolution, a programme is a delayed action.

### D2. Hold-out (ww2_testbed.md section 7.3)

T6, T7, T11 and T12 are hold-out tests. The v1 content (ontology, actions, decisions, events) is written from the record before any of them is run. After first sight of a hold-out result, no guard, effect, delay, fairness, profile or assume may change without a changelog row that gives a source and a rerun of the whole suite, and the report states which results came after such an edit. T3, T9 and T13 are also run in this phase under the same rule.

### D3. Replay harness (PLAN 2.4 to 2.6)

The corpora are blocked here, so the harness is built in three layers: corpus indices for each source with date filters and fetch scripts (run on the owner's machine); an extractor with a backend protocol (a deterministic rule backend for tests and a Claude backend written to the API reference, lazily imported); a review CLI that never changes a snapshot without a human decision. The blind replay runs here on a synthetic fixture corpus of about forty short dated documents written for the purpose and labeled as synthetic in every file; its metrics prove the mechanics (date filtering, extraction, level proposals, agreement and lag metrics against the hindsight snapshots), not the real replay, which waits for the real corpora. The report says so.

### D4. Transfer hypotheses (PLAN 2.7)

Written by the architect from the phase 1 results before any Cold War guard is written, in `docs/transfer_hypotheses.md`, each naming the Cold War claim that tests it.

## Waves

- Wave A (parallel): F1 symbolic engine; F2 pending-decision snapshots and the T8(b) evaluation; D1 v1 historical content (ontology, actions, decisions, events, realized moves 1941 to 1945, snapshots to 1945Q3); D3 replay harness.
- Wave B (after A): the v1 model with the hold-out tests T6, T7, T11, T12 and the phase tests T3, T9, T13; the phase report and page; the transfer hypotheses; the gate.
