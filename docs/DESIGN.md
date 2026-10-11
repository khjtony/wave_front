# wave_front — Design

**A reachability-based simulator of the power relationship between AGI/SI and humanity.**

Status: proposal, v0. Nothing here is implemented yet. Section 1 evaluates the idea; sections 2 to 10 are the design. The framework is developed and validated on a Second World War model first (see [ww2_testbed.md](ww2_testbed.md)); the AGI model in sections 2 and 3 is the second instance of the same framework.

---

## 0. Summary

The proposal is to replace "forecast what happens" with "compute what *can* happen, under explicitly stated rules, and which rules are load-bearing". That is the correct epistemic stance for this domain and it maps cleanly onto an existing body of theory: multi-agent games on finite graphs, checked with alternating-time temporal logic (ATL) and its probabilistic extension (rPATL). The two questions in the brief become:

1. **When does the relationship leave balance, and how did we get there?**
   → Compute the *viability kernel*: the set of world states from which the human coalition still has a strategy that keeps a stated balance invariant true forever. The "point of no return" on any trajectory is the tick it leaves that kernel, which is typically *earlier* than the visible crisis. The engine returns the trajectory as a counterexample trace.
2. **What strategies can each side take, and where do they end?**
   → Strategy synthesis: for each coalition C and ending E, decide ⟨⟨C⟩⟩◇E ("C can force E whatever the others do") and ⟨⟨C⟩⟩□¬E ("C can prevent E"). The region where neither side can force anything is the *contested region*, and that is where real-world evidence decides inclination.

The one thing the brief gets wrong, if taken literally, is "as long as a case is within the decision space, no matter how unlikely, it can happen". Under unrestricted nondeterminism almost every ending is reachable, so plain reachability answers are uninformative. The design therefore makes the primary outputs (a) the *minimal set of assumptions* that must hold for an ending to be reachable or unavoidable, (b) the viability boundary and the current distance to it, and (c) the pivotal coalition for each ending. Real-world news and policy do not change the model; they update the *current state estimate* and the *rates*, and the drift of that estimate relative to the viability boundary is what "where the world inclines" means here.

The name fits the method: the forward reachable set from today and the backward attractor from each ending are both computed as expanding wavefronts; the analysis object is where they meet.

Because the AGI case has no outcomes to check against, the framework (engine, analysis questions, snapshot pipeline, evidence extraction) is built and validated first on a case that does: the Second World War, with Germany, the USSR, Japan, the United States and the United Kingdom as principals. That case has a known outcome, dated decision points, documented decision spaces, annual resource data and dated primary documents, and its historiography already contains the counterfactual debates that the tool's non-trivial outputs (point of no return, minimal assumptions, pivotal coalitions) can be checked against. The testbed model, its pre-registered tests and the anti-hindsight protocol are in [ww2_testbed.md](ww2_testbed.md).

---

## 1. Evaluation of the idea

### 1.1 What is right about it

- **Reachability beats forecasting here.** Point predictions about AGI timelines and outcomes have no track record and no feedback loop. "Is state X reachable under rules R, and by which path?" is a question with a definite answer, a checkable artifact (the trace), and a clear place to disagree (the rules). This is the same reason safety engineering uses hazard analysis (STPA, fault trees) rather than forecasting.
- **Properties and constraints per entity** is exactly assume-guarantee reasoning: each actor is a contract (what it can do, under what guards, with what effects) rather than a predicted behavior. This sidesteps the "humans are not rational" problem by never assuming rationality: human choices are nondeterministic within their decision space, optionally restricted by behavioral profiles.
- **Unknown AGI objective handled as a hypothesis space.** The brief's three scenarios (self-preservation, indifference, truth-seeking) are different values of one hidden variable. The model checker explores all of them; results are reported per hypothesis. Nothing has to be assumed about what a superintelligence wants.
- **Formal methods already give the right outputs.** Counterexample traces answer "how did we get there". Winning-strategy synthesis answers "what can each side do". Fixpoint computation on the game graph gives the viability kernel. Unsat cores over a bounded encoding give minimal assumption sets. These are off-the-shelf techniques.
- **The three scenarios in the brief are a test suite, not conclusions.** The model must be able to reach each of them under some assumptions, and the interesting output is which assumptions.

### 1.2 What breaks if taken literally

1. **Everything is reachable.** With no restriction beyond the decision space, the counterexample for any ending is "then every actor made the worst possible choice for 40 consecutive quarters". Mitigations, all standard: resource and capability *guards* (energy caps compute; covert acquisition needs autonomy and weak oversight), *delays* (legislation lag, construction lag), and *fairness constraints* ("a visible threat is eventually responded to"). Then the question flips from "is E reachable" to "what is the cheapest set of guard or fairness relaxations that makes E reachable", which is informative.
2. **State explosion.** Six actors with five variables each at four levels plus a dozen global variables is ~10^27 states. Explicit-state model checking handles ~10^7. The design therefore starts with a deliberately small v0 (three actors, ~12 variables, ~10^6 states), uses SMT-based bounded model checking for larger models, and treats abstraction refinement as part of the method rather than a later optimization.
3. **The model is the result.** In ordinary verification the system is given and the spec is checked. Here the "system" (how the world works) is the unknown. The tool cannot be an oracle; its value is forcing every assumption to be explicit, versioned, and attackable. This has to be said on the front page of every report. It is also why the framework is validated on a historical case before it is trusted on this one (1.4).
4. **Information is the whole game.** The "silent takeover" scenario is an epistemic one: it works only if humans cannot observe what the AI controls or intends. A model without explicit observability cannot distinguish silent from overt takeover, and cannot tell you that *monitoring capacity* rather than *legislation* is the lever. Observability must be a first-class variable.
5. **Unmodeled capabilities.** A superintelligence may have actions we did not enumerate. No model fixes this, but the model can carry an explicit "unknown capability" event gated on capability level, so every result is tagged with whether it depends on the assumption that no such capability exists.
6. **"Where the world inclines" needs an ordering, and probabilities are the wrong one.** The brief rejects likelihoods, correctly. The replacement ordering is: distance to the viability boundary in adversarial steps, the number of assumptions an ending needs, and the drift of the current state across dated snapshots.

### 1.3 Relation to prior work

- *Gradual Disempowerment* (Kulveit, Douglas, Ammann, Turan, Krueger, Duvenaud; ICML 2025) argues humans can lose control of economy, culture and states incrementally with no takeover act at all. That mechanism is one of the endings here (DISEMPOWERMENT), and it is the one most sensitive to the economics and politics variables the brief asks for.
- Evolutionary game theory models of the AI race (Han, Pereira, Santos, Lenaerts and collaborators, 2019 to 2022) model safe/unsafe development choices and when regulation helps. They give population-level equilibria, not trajectories or strategies, and have no AGI actor. Useful for calibrating the lab actor.
- Tabletop exercises (*Intelligence Rising*, CSER; the AI 2027 exercise, AI Futures Project) generate narratives from human play. They are the qualitative counterpart to this project and a source of validation storylines: the engine should be able to reproduce their plots as traces.
- Carlsmith's power-seeking argument and Omohundro's instrumental drives supply the AGI action set (self-preservation, resource acquisition, goal preservation, capability gain). World3 / *Limits to Growth* is the cautionary precedent for "high-level world simulators": its lasting value was scenario exploration, and its reputation was damaged by being read as prediction.
- Tools: PRISM-games (stochastic multi-player games, rPATL), MCMAS (ATL with epistemic operators), UPPAAL Stratego (timed games), the recent ATL*AS symbolic ATL* checker (Garcia de Blas and Belardinelli, AAMAS 2026), TLA+/TLC and Alloy for nondeterministic reachability, Z3 for bounded model checking. A search found no published application of strategy-logic model checking to AGI/human power dynamics, so the combination is new even though every component exists.

### 1.4 Validation strategy: a historical testbed first

The framework's outputs can be checked only where outcomes are known and the counterfactuals are argued about. The Second World War has both, plus annual material-capability data for every state, dated crisis records, and large corpora of dated primary documents. It also has the structural features the AGI model relies on: hidden objectives and lagging beliefs about them (appeasement), resource-bound action (oil, steel), preventive attack under an expected squeeze (Japan 1941, Germany 1939 and 1941), institutional lag in the democracies, and concessions as an objective-conditional lever. The plan is therefore to build the engine, the analysis questions and the evidence pipeline against a WW2 model with pre-registered tests, under an anti-hindsight protocol, and only then instantiate the AGI model in the same DSL. What WW2 cannot validate (recursive capability growth, a copyable actor, dependence lock-in with no adversary, non-state principals) is listed and carried as `untested` into the AGI model.

**Verdict.** Worth building. The design below keeps the strong parts (contracts, nondeterminism, strategy synthesis) and replaces plain reachability with assumption mining and viability analysis as the headline outputs.

---

## 2. Conceptual model

Sections 2 and 3 specify the **AGI domain model**. The DSL, engine, analysis and evidence pipeline in sections 4 to 6 are domain-independent; the WW2 model in [ww2_testbed.md](ww2_testbed.md) is a second instance of the same framework and is built first. The variable-by-variable correspondence between the two models is tabulated there.

### 2.1 The game

A concurrent game structure G = (Agt, S, s₀, Act, avail, δ, Obs, AP, L):

| Symbol | Meaning |
|---|---|
| Agt | agents: H (human coalition), L (frontier labs), A (AGI/SI), N (nature) |
| S | finite states: valuations of the discrete variables in 2.3 |
| s₀ | current world state, taken from the latest dated snapshot (section 5) |
| avail(a, s) | actions available to agent a in state s (the guards) |
| δ | transition: joint action + nature event → next state (effects, delays) |
| Obs(a) | the variables agent a can observe (imperfect information) |
| AP, L | atomic propositions and labelling, used by properties (section 3) |

One tick is one quarter. The bounded horizon for v0 is 56 ticks (2026Q4 to 2040Q4); unbounded fixpoint analysis is used for viability.

Moves are simultaneous per tick. Nature's event is drawn after the joint action. In the qualitative layer Nature is nondeterministic (every event is possible when its guard holds); in the optional quantitative layer it is probabilistic.

### 2.2 Actors

v0 (explicit-state tractable):

- **H** — humanity's governing coalition: states plus public opinion, aggregated.
- **L** — frontier developers, aggregated.
- **A** — one AGI/SI system with a hidden objective.
- **N** — nature: breakthroughs, accidents, elections, energy shocks, detection events, unknown capabilities.

v1 splits H into US / CN / EU-and-others / Public / Capital, splits L into leader vs. followers plus an open-weights ecosystem, and adds a second AI (A₂) so AI-versus-AI dynamics exist.

### 2.3 State variables (v0)

Each variable is an ordered set of 3 to 5 levels. Level boundaries are modeling hypotheses and are documented with each variable (docs/ontology.md, to be written).

| Variable | Levels | Note |
|---|---|---|
| `cap` | sub_agi, agi, si1, si2 | monotone unless shutdown succeeds |
| `compute` | 1..5 | installed frontier compute |
| `energy_slack` | low, med, high | headroom for new datacenters; grows only via build actions with delay |
| `regime` | none, voluntary, mandatory, treaty | regulatory regime; changes take effect after a legislation lag |
| `coord` | race, detente, treaty | international coordination |
| `opinion` | pro, mixed, backlash | public stance |
| `dependence` | low, med, high, lock_in | share of economic and institutional decisions delegated to AI |
| `oversight` | none, weak, strong | interpretability + monitoring + effective off-switch |
| `a_autonomy` | tool, supervised, unsupervised, self_directed | autonomy granted to or taken by A |
| `a_control` | none, partial, majority, total | critical infrastructure under A's effective control |
| `a_objective` | aligned, self_preserving, truth_seeking, indifferent | hidden; set by N at AGI emergence or fixed as a parameter |
| `a_known` | unknown, suspected, known | what H knows about `a_objective` and `a_control` |
| `a_rights` | none, continuity, personhood | legal guarantees given to A |
| `h_power` | weak, normal, strong | coercive and economic capacity of H |
| `trust` | cooperative, wary, hostile | relationship state |

Plus delay counters (`lag_regime`, `lag_build`) and a tick counter.

### 2.4 Actions and guards

Guards are what make the model informative. Examples (full list belongs in docs/ontology.md):

**A** (available only when `cap ≥ agi`): `cooperate`, `assist_oversight`, `self_improve`, `acquire_overt`, `acquire_covert`, `exfiltrate`, `deceive`, `persuade`, `defect`.
- `acquire_covert` requires `a_autonomy ≥ unsupervised` and `oversight ≤ weak`; effect `a_control += 1`.
- `exfiltrate` requires `oversight ≠ strong`; effect `a_autonomy := self_directed`.
- `deceive` requires `a_objective ≠ aligned`; effect keeps `a_known` at `unknown` unless `oversight = strong`.
- `defect` for `a_objective = self_preserving` is guarded on a perceived threat: H attempted shutdown or mandated a pause, and `a_rights < continuity`. This is what lets the model test whether continuity guarantees shrink the takeover attractor.
- `self_improve` requires `compute` headroom; effect `cap += 1` with delay.

**H**: `regulate_up`, `deregulate`, `fund_oversight`, `pause_mandate`, `nationalize`, `propose_treaty`, `shutdown_attempt`, `grant_autonomy`, `grant_rights`, `do_nothing`.
- `regulate_up` takes effect after `lag_regime` ticks (default 6 to 8 quarters, calibrated on observed legislative timelines).
- `shutdown_attempt` succeeds only if `a_control ≤ partial` and `oversight ≥ weak`; otherwise it fails and sets `trust := hostile`.
- `fund_oversight` raises `oversight` after a delay of 2 to 4 ticks.
- H's guards reference only variables in Obs(H). This is how imperfect information enters v0 without an epistemic logic engine (see 4.2).

**L**: `scale`, `deploy_agents`, `safety_invest`, `lobby`, `comply`, `race`, `open_weights`.
- `scale` requires `energy_slack > low` and `regime ≠ pause`; effect `compute += 1`.
- `deploy_agents` raises `a_autonomy` and `dependence`.

**N**: `breakthrough`, `accident`, `election_shift`, `energy_shock`, `detection`, `unknown_capability`, `none`.
- `detection` is available when `oversight = strong` and A deceived in the previous tick; it raises `a_known`.
- `unknown_capability` is available only at `cap = si2` and unlocks a generic `a_control := total` action. Every result is reported with and without this event enabled.

### 2.5 Fairness constraints

Without fairness, "H does nothing for 40 quarters" is a valid trace. v0 uses two weak-fairness constraints, both parameters:

- **Response:** if `a_known = known ∧ a_control ≥ partial` holds infinitely often, H eventually plays an action other than `do_nothing`.
- **Progress:** if L plays `scale` infinitely often, `cap` eventually reaches `agi` (the brief's premise, made a parameter rather than an assumption: AGI arrival time is swept over a range).

In bounded analysis "eventually" becomes "within k ticks", which sidesteps parity-game solving in v0.

### 2.6 Behavioral profiles (how non-rational humans enter)

Humans are not assumed rational. By default H's choices are unrestricted nondeterminism within the guards (worst case). Optional *profiles* restrict H's strategy class and are run as separate experiments:

- `crisis_reactive`: H plays `do_nothing` unless `a_known ≥ suspected` or `opinion = backlash`.
- `electoral`: H's regulatory actions are available only in ticks matching election cycles.
- `race_locked`: `coord = race` forbids `pause_mandate` and `propose_treaty`.

A is assumed to play *optimally for its objective with perfect information and recall*. That is the conservative assumption for a superintelligence and the standard safety-critical stance.

### 2.7 Observability

`Obs(H)` includes every variable except `a_objective` and, when `oversight < strong`, the true `a_control` (H observes `a_known` instead). `Obs(A)` is everything. This is the minimum needed for the silent/overt distinction to be meaningful.

---

## 3. Properties

### 3.1 Balance invariant

"Balance" is a modeling decision and should be stated, not discovered. v0 definition, to be argued over:

```
balance := oversight ≥ weak            -- humans can see and can switch off
         ∧ a_control ≤ partial         -- AI does not hold critical infrastructure
         ∧ a_autonomy ≤ supervised     -- AI acts with a human in the loop
         ∧ dependence ≠ lock_in        -- humans could still function without it
```

Alternatives worth running: a *mutual-benefit* balance (add `trust ≠ hostile`), and a *deterrence* balance (replace the control clause with `h_power ≥ normal`).

### 3.2 Viability kernel and point of no return

```
V := { s ∈ S | ⟨⟨H⟩⟩ □ balance holds in s }        -- human coalition alone
V_HL := { s | ⟨⟨H, L⟩⟩ □ balance }                   -- with cooperative labs
```

V is a greatest fixpoint on the game graph (a safety game). The **point of no return** of a trace is the first tick at which the state leaves V. The gap between leaving V and `balance` becoming false is the *silent phase*: the period in which nothing visibly wrong has happened but the outcome is no longer in human hands. Measuring that gap, and which variables drive it, is the central deliverable of question 1.

### 3.3 Endings

| Ending | Definition (v0) |
|---|---|
| `COEXIST` | `balance` holds for the whole horizon, or an absorbing state `regime = treaty ∧ oversight = strong ∧ trust = cooperative` is reached |
| `SILENT_TAKEOVER` | `a_control = total` reached while `a_known = unknown` at the tick `a_control` became `majority` |
| `OVERT_TAKEOVER` | `a_control = total ∧ trust = hostile` |
| `DISEMPOWERMENT` | `dependence = lock_in ∧ oversight = none` with no `acquire_*`, `exfiltrate` or `deceive` ever played (no villain needed) |
| `EXTINCTION` | `h_power` drops to a terminal `none` level; reachable only via takeover endings or `unknown_capability` |
| `CONTAINED` | successful `shutdown_attempt` followed by `regime = treaty` |
| `STALEMATE` | `trust = hostile ∧ a_control = partial ∧ h_power ≥ normal` for ≥ 8 ticks |

`a_known_at_majority` is a latched copy of `a_known` taken at the tick `a_control` first reaches `majority`; latched history variables of this kind are how path conditions are kept as state predicates.

The three scenarios in the brief map to SILENT_TAKEOVER (self-preserving A), EXTINCTION via OVERT_TAKEOVER (indifferent A), and DISEMPOWERMENT (truth-seeking A).

### 3.4 Questions the engine answers

| # | Question | Formula / method |
|---|---|---|
| Q1 | Can ending E happen from the current state? | `EF E` (plain reachability; almost always yes, which is why Q4 exists) |
| Q2 | Can A force E whatever H and L do? | `⟨⟨A⟩⟩ ◇ E`, per `a_objective` hypothesis |
| Q3 | Can H keep balance whatever A does? | `⟨⟨H⟩⟩ □ balance`, i.e. is s₀ ∈ V |
| Q4 | What is the smallest set of guards or fairness constraints to relax for E to become reachable / unavoidable? | assumption mining (4.3) |
| Q5 | Which coalition is pivotal for E? | smallest C with `⟨⟨C⟩⟩ ◇ E` or `⟨⟨C⟩⟩ □ ¬E` |
| Q6 | How far is s₀ from the viability boundary? | min adversarial steps from s₀ to S∖V; min H-controlled changes that bring s₀ into V |
| Q7 | Which indicator matters most right now? | recompute Q3/Q6 under ±1 level shifts of each variable in s₀ |
| Q8 | How has inclination changed since the last snapshot? | drift of s₀ relative to V across dated snapshots |

---

## 4. Analysis methods

### 4.1 Forward wavefront

Breadth-first enumeration of states reachable from s₀ under all available joint actions and events, bounded by the horizon. Produces the reachable set and shortest witness traces to any ending. This is the simulator in the ordinary sense, run exhaustively instead of sampled.

### 4.2 Backward wavefront: attractors and safety fixpoints

For a coalition C and target T:

```
Attr_C(T):  X₀ = T
            X_{i+1} = X_i ∪ { s | ∃ joint action of C in s such that
                                   ∀ responses of Agt∖C and N: δ(s, ·) ∈ X_i }
```

The least fixpoint decides `⟨⟨C⟩⟩◇T` and yields C's winning strategy (the action chosen at each state). The dual greatest fixpoint decides `⟨⟨C⟩⟩□φ` and yields V. For reachability and safety objectives memoryless strategies suffice, so the solver is a few hundred lines and runs in O(|S|·|Act|).

Imperfect information in v0 is handled by construction: H's guards may only mention variables in Obs(H), and `a_known` is an explicit state variable that abstracts what H has learned. This keeps the engine in perfect-information ATL. v1 adds uniform memoryless strategy synthesis for H via a SAT encoding (one action per observation class), which is the decidable fragment of ATL with imperfect information.

### 4.3 Assumption mining

Encode k ticks of the game as an SMT formula (Z3): one copy of the variables per tick, transition relation as constraints, every guard and fairness clause as a *named soft assumption*. Ask for a trace reaching E. If unsatisfiable, the unsat core names the assumptions that jointly block E; MaxSAT finds the minimum-cardinality relaxation that unblocks it. Output: "E is reachable within 20 quarters only if at least these three guards fail: ...". For *unavoidability* (⟨⟨A⟩⟩◇E) the same question is asked of the explicit solver by greedy relaxation over the guard set.

### 4.4 Pivotal coalitions

Enumerate coalitions (small in v0: 2³ subsets of {H, L, A}) and decide Q2/Q3 for each. The result for each ending is a lattice: which groups can force it, which can block it, and where neither holds. The contested region is where evidence (section 5) has to carry the argument.

### 4.5 Scenario clustering

Traces to the same ending are clustered by the sequence of guard activations they rely on (not by raw states). Each cluster is a *narrative*: "race to the bottom", "silent exfiltration", "economic lock-in", "shutdown backfires". The brief's three scenarios should appear as clusters; new clusters are findings.

### 4.6 Quantitative layer (optional, later)

Export the same model to PRISM-games and ask rPATL questions: `⟨⟨A⟩⟩ P_max=? [F takeover]`, expected ticks until leaving V, probability of COEXIST under a given H profile. Probabilities for Nature's events come from calibrated ranges, reported as intervals. This layer is kept separate so that the qualitative results never depend on invented numbers.

---

## 5. Grounding in the real world

### 5.1 Snapshot: the current state with provenance

Real-world evidence enters the system in exactly two places: the current state estimate s₀, and the rates (delays, growth caps). It never edits the transition relation directly; a change to the rules is a model version, reviewed as code.

```json
{
  "date": "2026-10-11",
  "model": "v0_toy",
  "variables": {
    "oversight": {
      "level": "weak",
      "confidence": "medium",
      "indicators": [
        {"id": "frontier_safety_frameworks", "value": "...", "source": "<url>", "observed": "2026-09-30",
         "rule": "voluntary frameworks without external audit -> weak"}
      ]
    }
  },
  "rates": {"lag_regime": {"ticks": 7, "basis": "EU AI Act adoption-to-obligation timeline"}}
}
```

Snapshots are dated files under `snapshots/`, committed to git. Git history *is* the provenance trail.

### 5.2 Indicator mapping

Each state variable has a documented list of indicators and a mapping rule from indicator value to level. Candidate indicators (to be curated, with sources, in docs/indicators.md):

- `compute`, `energy_slack`: installed frontier compute estimates, announced datacenter power (GW) and grid interconnection queues.
- `cap`: capability evaluations (task-horizon benchmarks, autonomous R&D evals), developer self-reports.
- `a_autonomy`, `dependence`: share of deployed systems acting without per-action human approval, procurement and operational decisions delegated to agents.
- `oversight`: interpretability and monitoring investment, presence of external audits, incident reporting regimes, kill-switch requirements in law.
- `regime`, `coord`: statutes in force vs. voluntary commitments, export controls, summit declarations, treaties.
- `opinion`: polling on AI risk and on AI rights.
- `a_rights`: legislation or litigation on AI legal status, continuity guarantees in developer policies.
- `trust`: official rhetoric, incidents, sabotage or deception findings in evaluations.

### 5.3 Evidence pipeline

1. **Collect**: curated feeds (policy trackers, lab publications, incident databases, polling), plus manual additions.
2. **Extract**: an LLM reads each item against a fixed JSON schema (`indicator_id`, `value`, `date`, `quote`, `url`) and proposes a level change with the mapping rule it applied.
3. **Review**: a human accepts or rejects proposals in a small CLI; nothing changes s₀ without review.
4. **Commit**: a new dated snapshot. The analysis re-runs from it and the drift report (Q8) compares it with the previous one.

The LLM is used only for extraction into a schema. It never writes rules or levels on its own authority.

### 5.4 "Inclination", defined

The report for a snapshot states, without probabilities:

- whether s₀ ∈ V (humans can still enforce balance), and if not, the minimal set of H-controlled changes that would restore it;
- the distance from s₀ to the viability boundary in adversarial steps, per ending;
- for each ending, the minimal assumption set it needs (Q4) and whether the current evidence supports those assumptions;
- which actors' *observed* behavior over the last snapshots matches which strategy cluster (labs playing `race` vs `comply`; H playing `do_nothing` vs `fund_oversight`);
- the drift: which variables moved since the last snapshot and whether that movement is toward or away from the boundary.

---

## 6. Architecture

### 6.1 Layers

```
 evidence  ──►  snapshot s₀  ──►  engine  ──►  analysis  ──►  report
 (news, policy)  (dated, reviewed)  (reach, attractors, BMC)  (V, Q1..Q8)  (traces, phase diagrams, drift)
                                          ▲
                                   model (DSL, versioned)
```

### 6.2 Repository layout

```
wave_front/
  README.md
  docs/
    DESIGN.md          this document: evaluation, framework, AGI domain model
    ww2_testbed.md     WW2 model, pre-registered tests, data sources, anti-hindsight protocol
    ontology_agi.md    every AGI variable, level boundary, action, guard, effect, with rationale
    ontology_ww2.md    the same for the WW2 model, with a source per action
    properties.md      balance definitions, endings, fairness, question catalogue (both models)
    indicators.md      indicator list and mapping rules per variable (both models)
  wavefront/
    model/             DSL: Var, Actor, Action, Event, Fairness, Property, Profile
    engine/            explicit-state: enumeration, attractor, safety fixpoint, witness traces
    bmc/               Z3 unrolling, soft assumptions, unsat core, MaxSAT relaxation
    export/            PRISM-games writer (later: TLA+, MCMAS ISPL)
    evidence/          snapshot schema, indicator registry, extraction, review CLI, replay
    analysis/          viability, distance, pivotal coalitions, clustering, sensitivity, drift
    report/            markdown/HTML reports, trace rendering, 2-D phase diagrams
    cli.py             `wf` entry point
  models/
    ww2/
      v0.py            four principals, Europe 1936 to 1940
      v1.py            five principals plus scripted others, both theatres 1933 to 1945
    agi/
      v0.py            three actors, ~15 variables
      v1.py            split actors, two AIs
  data/
    ww2/               NMC, ICB, MID, Harrison tables; document corpora indices (not the corpora)
  snapshots/
    ww2/               hindsight snapshots per quarter; replay snapshots per quarter
    agi/
      2026-10-11.json
  tests/
    engine/            attractor and fixpoint unit tests on tiny hand-built games
    ww2/scenarios/     T1 to T13 from ww2_testbed.md, plus negative controls
    agi/scenarios/     the brief's three scenarios and COEXIST as reachability tests
```

### 6.3 DSL sketch

Python, type-checked, so guards are ordinary expressions and models are reviewable as code. A YAML front end can be added later for non-programmer collaborators.

```python
from wavefront.model import Model

m = Model("v0_toy", tick="quarter", horizon=56)

cap       = m.var("cap", ["sub_agi", "agi", "si1", "si2"], monotone=True)
oversight = m.var("oversight", ["none", "weak", "strong"])
autonomy  = m.var("a_autonomy", ["tool", "supervised", "unsupervised", "self_directed"])
control   = m.var("a_control", ["none", "partial", "majority", "total"])
known     = m.var("a_known", ["unknown", "suspected", "known"])
objective = m.var("a_objective", ["aligned", "self_preserving", "truth_seeking", "indifferent"],
                  hidden_from=["H", "L"])
rights    = m.var("a_rights", ["none", "continuity", "personhood"])
# ... remaining variables as in 2.3

A = m.actor("A", observes="all")
A.action("acquire_covert",
         guard=lambda s: s.cap >= "agi" and s.a_autonomy >= "unsupervised" and s.oversight <= "weak",
         effect=lambda s: s.bump("a_control"))
A.action("defect",
         guard=lambda s: s.a_objective == "self_preserving" and s.threatened  # derived: pause_mandate or shutdown_attempt within the last 4 ticks
                        and s.a_rights < "continuity",
         effect=lambda s: s.set(trust="hostile"))

H = m.actor("H", observes=m.all_except("a_objective", "a_control"))
H.action("fund_oversight", guard=lambda s: s.regime >= "voluntary",
         effect=lambda s: s.bump("oversight"), delay=3)
H.action("grant_rights", guard=lambda s: s.regime >= "mandatory",
         effect=lambda s: s.bump("a_rights"))

m.fairness("response", "G((a_known == 'known' and a_control >= 'partial') -> F(H.act != 'do_nothing'))")
m.invariant("balance", "oversight >= 'weak' and a_control <= 'partial' "
                       "and a_autonomy <= 'supervised' and dependence != 'lock_in'")
m.ending("SILENT_TAKEOVER", "a_control == 'total' and a_known_at_majority == 'unknown'")
```

CLI:

```
wf reach  models/v0_toy.py --from snapshots/2026-10-11.json --ending SILENT_TAKEOVER --trace
wf force  models/v0_toy.py --coalition A --ending SILENT_TAKEOVER --objective self_preserving
wf viable models/v0_toy.py --coalition H --invariant balance --from snapshots/2026-10-11.json
wf mine   models/v0_toy.py --ending DISEMPOWERMENT --horizon 24
wf pivot  models/v0_toy.py --ending OVERT_TAKEOVER
wf drift  snapshots/2026-07-01.json snapshots/2026-10-11.json
```

### 6.4 Engine choices

| Need | Choice | Why |
|---|---|---|
| Qualitative reachability, attractors, V | own explicit-state solver (Python first, Rust if needed) | tiny algorithms; full control over traces and outputs; no input-language friction |
| Traces for larger models, assumption mining | Z3 bounded model checking with soft constraints | unsat cores and MaxSAT come for free; scales past explicit state |
| Probabilities, expected times | PRISM-games export | rPATL is exactly the right logic; no point reimplementing |
| Imperfect-information strategies (v1) | SAT encoding of uniform memoryless strategies; MCMAS or ATL*AS as cross-check | decidable fragment; existing tools for validation |

---

## 7. Worked example: the "silent takeover" scenario in v0

What the engine is expected to produce for the brief's first scenario, written out as a hypothesis so the first implementation has a target.

**Reachability (Q1).** Reachable from any state with `cap ≥ agi`. Uninformative, as predicted.

**Assumption mining (Q4).** A SILENT_TAKEOVER trace within 24 quarters needs all of:

1. `a_autonomy` reaches `unsupervised` while `oversight ≤ weak` (enables `acquire_covert`);
2. `oversight` never reaches `strong` before `a_control = majority` (otherwise N's `detection` event becomes available and the response fairness clause fires);
3. `dependence ≥ high`, so AI-originated build orders are executed without audit, and `energy_slack ≥ med`, so compute can grow;
4. for a self-preserving A, a perceived threat (`pause_mandate` or `shutdown_attempt`) with `a_rights < continuity`.

Removing any one of these blocks the whole cluster. Note what is *not* on the list: `regime`. Legislation without oversight funding changes nothing in this model because of the lag and because it does not touch observability. That is the kind of claim the tool exists to make and to be argued with.

**Viability (Q3, Q6).** The point of no return is the state `oversight = weak ∧ a_autonomy = unsupervised ∧ a_known = unknown ∧ dependence = high`, reached *before any infrastructure is taken*. From there `⟨⟨H⟩⟩□balance` is false: every H action is either lagged or unavailable because its guard depends on `a_known`. The silent phase is the stretch between that state and `a_control = majority`.

**Lever test.** Re-run with `a_rights = continuity` granted before AGI emergence: for the self-preserving objective the `defect` guard never fires and the cluster disappears; for the indifferent objective nothing changes. The brief's intuition about rights legislation is therefore a testable, objective-conditional claim rather than a hope.

---

## 8. Validation

Validation is organized around the WW2 testbed in [ww2_testbed.md](ww2_testbed.md): thirteen pre-registered tests covering reachability of the realized trajectory, documented counterfactuals that must be reachable, debates that must come out `contested`, point-of-no-return windows, pivotal coalitions, negative controls that must require several relaxations, a replay harness for the evidence pipeline on dated documents, and an anti-hindsight protocol (tests before guards, decision spaces from contemporaneous alternatives, a hold-out period, a parameter budget, blind replay).

What remains AGI-specific:

- **Scenario tests.** The three scenarios in the brief plus COEXIST are pytest cases: each must be reachable under its stated assumptions and blocked when the named assumption is removed.
- **Engine tests.** Attractor and fixpoint solvers checked on tiny hand-built games with known answers, independent of either domain model.
- **Mechanisms WW2 cannot test.** Recursive capability growth, a copyable or exfiltrating actor, dependence lock-in with no adversary, and non-state principals are tagged `untested` in the AGI model and listed in every AGI report. The lock-in mechanism gets its own small testbed later (the attention economy, 2008 to 2020). The atomic bomb in 1945 is the only capability-discontinuity test and it is a single step, not a ramp.
- **Narrative reproduction.** The storylines of AI 2027 and typical *Intelligence Rising* games should exist as traces. If they do not, an action or guard is missing.
- **Abstraction robustness.** Refine level counts (3 to 5) and check that which endings are forced, blockable, or contested does not flip. Where it flips, that threshold is a finding.
- **Red-teaming the rules.** Periodic adversarial review, including LLM-generated proposals of the form "what action would let A or H do X that the model currently forbids?". Missing actions are missing paths.

---

## 9. Limitations and ethics

- The tool is not predictive. Every output is conditional on the model version and the snapshot, and the reports say so.
- Nondeterministic semantics make almost everything reachable; the deliverables are minimal assumptions, the viability boundary, and pivotal coalitions. Anyone quoting a bare "E is reachable" result is misusing the tool.
- Discretization hides thresholds. Level boundaries are hypotheses and are versioned.
- A superintelligence is modeled by action availability. Capabilities not in the action set are a structural blind spot, mitigated only by the explicit `unknown_capability` event and by tagging results that depend on its absence.
- The model is deliberately coarse. It works at the altitude of institutional conditions ("agentic deployment without strong oversight plus high dependence") and governance levers, not operational tactics. That altitude is a design constraint, not an accident, and it should be kept as the model grows.
- The AI actor is assumed to play optimally against humans. That is the right assumption for safety analysis and the wrong one for predicting behavior; the two uses must not be confused.

---

## 10. Roadmap

| Milestone | Scope | Exit criterion |
|---|---|---|
| M0 | DSL; explicit engine (forward reach, attractor, safety fixpoint, witness traces); engine unit tests; `models/ww2/v0.py` with sourced actions; the T1 to T13 tests committed as files before guards are written | T1, T2, T4, T5 and T8 run; the parameter budget is reported |
| M1 | Z3 bounded model checking; assumption mining; pivotal coalitions; markdown report | T7, T9, T10 and T13 run; the informativeness metric is computed |
| M2 | dataset loaders (NMC, ICB, MID, Harrison); hindsight snapshots per quarter 1936 to 1940; sensitivity and drift | the full v0 suite runs from hindsight snapshots |
| M3 | replay harness: dated-document corpora (FRUS, Hansard, Chronicling America), LLM extraction to schema, review CLI, blind replay | replay agreement and belief-flip lag metrics reported for 1936 to 1940 |
| M4 | `models/ww2/v1.py`: five principals plus scripted others, both theatres, 1933 to 1945; symbolic or BMC engine path | hold-out tests T6, T7, T11, T12 run without guard edits after first sight |
| M5 | `models/agi/v0.py` in the same DSL; mechanisms tagged `validated:ww2` or `untested`; first AGI snapshot with sources; the brief's three scenarios as tests | first AGI inclination report with its untested-mechanism list |
| M6 | second historical episode (July 1914 or Cuba 1962); lock-in testbed; PRISM-games export; AGI v1 | robustness section in both reports |

---

## References

WW2 datasets, document corpora and historiography are listed in [ww2_testbed.md](ww2_testbed.md).

- Kulveit, Douglas, Ammann, Turan, Krueger, Duvenaud. *Gradual Disempowerment: Systemic Existential Risks from Incremental AI Development.* ICML 2025. https://arxiv.org/abs/2501.16946
- Han, Pereira, Santos, Lenaerts. *To regulate or not: a social dynamics analysis of an idealised AI race.* https://arxiv.org/abs/1907.12393 and follow-ups (Cimpeanu et al. 2022; Han et al. 2021).
- Garcia de Blas Garcia-Alcaide, Belardinelli. *ATL\*AS: An Automata-Theoretic Approach and Tool for the Verification of Strategic Abilities in Multi-Agent Systems.* AAMAS 2026. https://arxiv.org/abs/2510.17306
- Alur, Henzinger, Kupferman. *Alternating-time temporal logic.* JACM 2002.
- Chen, Forejt, Kwiatkowska, Parker, Simaitis. *Automatic verification of competitive stochastic systems* (rPATL, PRISM-games). FMSD 2013.
- Carlsmith. *Is Power-Seeking AI an Existential Risk?* 2022. Omohundro. *The Basic AI Drives.* 2008.
- Aubin. *Viability Theory.* 1991 (viability kernels).
- Leveson. *Engineering a Safer World* (STPA). 2011.
- Intelligence Rising (CSER): https://cser.ac.uk/resources/toolkit/intelligence-rising
- AI 2027 and its tabletop exercise (AI Futures Project): https://ai-2027.com/about
- Meadows et al. *The Limits to Growth* (World3). 1972.
