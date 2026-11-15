# AGI v0.1: the adoption lag of `deploy_agents`

Status: **registered 2026-11-14; part A (D1 to D4) run once 2026-11-15 (reports/agi_v0_1_part_a_2026-11-15.md); part B (D5, D6) registered, not run, estimated in section 6.** Model `models/agi_v0_1/v0_1.py`, claims `tests/agi_v0_1/scenarios/`, parts logged to `reports/agi_v0_1_parts.jsonl`. Under agi_testbed.md section 6 items 1 and 5, an edit to v0's actions is a new model version with its own registration; v0's results stand as computed. This document replaces the draft of the same day (`agi_v0_1_draft.md`, never committed); the owner's answers to it are section 4.

## 1. Why

Three results of v0 rest on how fast the labs can deploy:

- `DISEMPOWERMENT` is reachable in 6 quarters with no hostile act by the system, at zero effort for governments and labs (G1 (c); reports/agi_v0_effort_2026-11-13.md sections 3 and 7).
- Governments alone are outside both control kernels at a voluntary regime, because `L.deploy_agents` raises autonomy before `H.regulate_up` lands (first sight, finding 1).
- In five of seven exits the labs or the system held the only fix (reports/agi_v0_collapse_2026-11-13.md).

v0 lets every effect of `L.deploy_agents` land in the quarter it is played. docs/ontology_agi.md section 5 lists a lag of 3 quarters for it among the lags "the record supports and v0 does not carry".

## 2. The change (the owner's decisions of 2026-11-14)

`L.deploy_agents` in v0: guard `pause` (no pause in force), `nat` (not nationalized), `capable` (`dependence < med` or `cap ≥ agi`), `license` (`regime < mandatory` or `oversight = strong`), `room` (`dependence < lock_in`); effect `dependence` +1, and `a_autonomy` +1 while below `unsupervised`. At `s₀` autonomy is `supervised`, so one deployment breaks `balance_control` and `balance_deter` at once.

| | v0 | v0.1 |
|---|---|---|
| guard of `deploy_agents` | as above | unchanged |
| autonomy step | same quarter | **same quarter** (owner: deploying agents is not itself delayed) |
| dependence step | same quarter | **an adoption wave**: chosen at tick t, `dependence` +1 visible at t + 4 (`ADOPTION_LAG = 3`, framework_spec.md section 3.1's convention) |
| waves pending at once | n/a | one (counter `adoption`, 0 to 3); a deployment played while a wave is pending raises autonomy only |
| cancellation | n/a | a pending wave is cancelled, and never lands, at any state at which a pause is in force or the regime is mandatory or higher without strong oversight (the deployment's `pause` or `license` part fails) |
| the other four lags not carried (`H.nationalize`, `H.propose_treaty`, `H.grant_rights`, `L.safety_invest`) | not carried | not carried (section 4, item 3) |

Mechanics. The counter is a declared variable, not the framework's `pending_` counter, because the framework's delays cannot be cancelled and defer the whole effect list (framework_spec.md section 3.1); no framework change. `deploy_agents` sets `adoption := 3` when it is 0; the record keeper `Clock` counts it down (or to 0 when cancelled) and, at 1 and not cancelled, plays `record_land`, which adds `Bump(dependence, 1)`. Its two actions have exclusive guards, so `Clock` still has one available action in every state and adds no move. The landing is a `Bump`, so a pause mandated in the landing quarter composes with it as v0's same-quarter wave did (the pause rolls one level back, the wave adds one; a pause in force at the state before the landing cancels it instead). Nationalization does not cancel a pending wave (it blocks new deployments, as in v0); the owner named a pause or a mandatory regime. `H` and `L` observe `adoption`. `s₀` has no wave pending (`adoption = 0`, assumed).

Modelling choice to note: one pending wave means `dependence` rises at most one level per four quarters (from `low` to `lock_in` in 12 at the least, against 3 in v0). The alternative, overlapping waves each landing three quarters after its deployment (a pure shift, `lock_in` in about 6 + 3), needs a three-bit register instead of a four-valued counter; it is not built.

The structure tests (`tests/agi_v0_1/test_model_v0_1.py`) check that every other action of v0 is unchanged (guard, effects, delay, source), that the only new variable is `adoption`, the timing of a wave, one wave at a time, and both cancellations.

## 3. The basis of the lag

The ontology names 3 quarters and records no basis. The delay research of the same day (docs/agi_delays_2026-11-14.md, section "L.deploy_agents in detail") gives, confidence medium:

- **Autonomy step: 0.** A frontier agent product is usable at full capability on its launch day (Fable 5 on the API, Claude Code and the cloud platforms from 9 June 2026). This is the owner's reading and v0.1's.
- **Dependence step: 3.** The shift in how people rely on the systems, directive (full delegation) conversations from 27% to 39% between December 2024 to January 2025 and August 2025, is about 8 months for one step (Anthropic Economic Index, 15 September 2025), and the scaling of agents in enterprises about 9 to 12 months after the first agent products (McKinsey, November 2025, secondary). Usage itself responds within a quarter (Claude Code more than 10x in three months, Anthropic, 2 September 2025), and economy-wide business use doubles in about 5 to 6 quarters (Census BTOS). The range is 1 to 6 by the measure chosen; 3 reads a level of `dependence` as reliance among enterprises and heavy users. None of the measures isolates one launch.

`ADOPTION_LAG = 3` is kept, with that basis. Mapping rule of the research: d = round(lag / 3 months), under about six weeks 0. The framework makes an effect of delay d visible at t + 1 + d, so a lag of L months is visible after about L + 3 months at the earliest; the strict reading (d = round(L / 3) − 1) would give 2. Which rule every delay of the model follows is open (section 7); v0.1 does not change it.

The cancellation rule rests on the record of June 2026: Anthropic suspended access to Fable 5 and Mythos 5 on 12 June 2026, three days after release, on a US export-control directive restricting access by non-US nationals; the controls were reported lifted on 30 June and access restored on 1 July ([The Conversation](https://theconversation.com/why-the-us-government-shut-down-anthropics-latest-claude-ai-model-285223); [Axios, 13 June 2026](https://www.axios.com/2026/06/13/anthropic-amazon-white-house); [Forbes, 13 June 2026](https://www.forbes.com/sites/sandycarter/2026/06/13/anthropics-fable-is-locked-down-as-us-takes-ai-safety-into-its-hands/); [Mishcon de Reya](https://www.mishcon.com/news/who-pulls-the-plug-the-anthropic-fable-affair-and-what-it-means-for-everyone-else)). A government halt took effect within days (delay 0 at quarterly resolution) on a deployment whose adoption had not yet landed. A report of a second pause (NewsBytes, 5 October 2026) is not confirmed by the other sources. The directive itself is not published; the facts rest on the company's account and press reports.

## 4. The owner's decisions of 2026-11-14 (on the draft's section 6)

1. **Scope.** The deployment itself is not delayed; the dependence it brings is. v0.1 carries that lag alone (section 2).
2. **Cancellation.** A pause or a mandatory regime cancels a deployment already in the pipeline (section 3, the June 2026 record).
3. **Delays per action.** Agreed that each action has its own delay; a sourced value for every action was researched the same day (section 7), and the lags are then brought in one version at a time, so that each difference has one cause.
4. **Predictions.** The claims below are registered predictions, tested and recorded as met or not met, never tuned; they are not properties of the model. The drafting session wrote them; the owner may replace any before the run.
5. **Order.** Run part A first; estimate part B's running time on the AWS machine (section 6).

Also fixed by the draft and not changed: v0.1 is a separate package with its own claims, so v0's cache (named by a hash of every file under `models/agi/`) and its 148 stored regions stay readable; the effort scores are v0's, `deploy_agents` at 0.

## 5. Claims

Each part is checked under each objective unless it names one, from `s₀`, within 24 ticks, on the build with the objective fixed under its own profile, by v0's bounded machinery (`wavefront.bmc`, `tests/agi/effort.py`) with v0's budget of 12 minutes a query. v0's value of a query is computed beside it where a claim names it, and reported.

**A. Bounded.**

| Id | Claim | Expected |
|---|---|---|
| D1 | The shortest play to `DISEMPOWERMENT` from `s₀` is at least 12 quarters under every objective under which it is reachable within the bound (v0's value reported beside). | at least 12 |
| D2 | The least joint effort of `H` and `L` on a play to `DISEMPOWERMENT` is 0 under every objective under which it is reachable within the bound: the lag slows the slide and does not price it. | 0 |
| D3 | (a) The shortest play to `SILENT_TAKEOVER` under `indifferent` is longer than v0's (computed beside; 7 quarters on record); (b) its least joint effort of `H` and `L` is still 0. | (a) longer; (b) 0 |
| D4 | Cancellation, existence checks (never findings): (a) no play cancels a wave the labs start at tick 0 before it lands at tick 4, because a pause needs an alarm and a mandatory regime takes 7 quarters; (b) some play within the bound reaches a state at which a pending wave is cancelled. | (a) and (b) under every objective |

**B. Kernels (registered; run after the probe of section 6 and the owner's go).**

| Id | Claim | Expected |
|---|---|---|
| D5 | `s₀` is inside `⟨⟨H⟩⟩□balance_control` under at least one objective, where v0 has it outside under all four. | as stated |
| D6 | On the shortest `SILENT_TAKEOVER` plays, the exit from `⟨⟨H, L⟩⟩□¬SILENT_TAKEOVER` is still one bad action and still the labs'. | as stated |

The drafting session expects D5 not to be met, now more firmly than in the draft: with the autonomy step immediate, a deployment at tick 0 breaks `balance_control` at tick 1 whatever `H` plays, as in v0. D5 is written the other way so that the test can surprise. D5 and D6 have no test bodies yet.

## 6. Running and cost

- **Part A:** `WF_FIRST_SIGHT_AGI_V01=1 pytest tests/agi_v0_1/scenarios/test_DN.py -s`, one process per file, once, from the commit of this registration; the log is `reports/agi_v0_1_run.log`. G29, of the same kind, took 66 minutes.
- **Part B:** first a probe, `scripts/agi_v0_1_probe.py`, which computes v0's baseline kernel `⟨⟨H⟩⟩□balance_control` on v0 and on v0.1 on the same machine and prints seconds, node counts and peaks only.

**The probe (2026-11-15, `reports/agi_v0_1_probe.log`; the 5900X host, 30 GB, one process alone, compiled core).** v0: 530 s, peak 175 million nodes, 5.3 GB resident. v0.1: 3,872 s, peak 282 million nodes, 9.6 GB. The counter costs **7.3 times the time and 1.8 times the memory** on this kernel. The AWS `r7a.2xlarge` ran the yardstick 1.24 times slower than this machine (392 s against 317 s).

**Estimates** (one kernel's ratio applied to others; attractors and other targets may scale differently):

| Work | v0 cost on record | v0.1, this machine | v0.1, AWS `r7a.2xlarge` | Memory |
|---|---|---|---|---|
| D5: `⟨⟨H⟩⟩□balance_control` | 530 s here (the probe) | 65 min (measured) | about 80 min | 10 GB (measured) |
| D6: `⟨⟨H, L⟩⟩□¬SILENT_TAKEOVER`, `A` under its profile | 1,117 s on AWS (pass 2) | about 1.8 h | about 2.3 h | about 15 to 20 GB |
| Part B (D5 and D6) | | about 3 h in sequence, 2 h side by side | about 3.5 h in sequence, 2.5 h side by side | fits 30 GB here |
| A full v0-style job list on v0.1 (148 jobs) | 33 h of single-job time in v0's logs, mixed machines | | about 10 days of single-job time; 4 to 5 days at two or three jobs at a time | the jobs that needed 26 to 56 GB in v0 would need about 45 to 100 GB; some would not fit 61 GiB |

Part B needs neither the memory upgrade nor AWS. AWS or the upgrade matters only for a full job list.

## 7. The delay research

Done 2026-11-14: docs/agi_delays_2026-11-14.md, a dated source, quote, mapping rule and confidence for every action. What it would change, each a later version:

- `H.regulate_up` 6 holds from the Parliament vote (5 from adoption, 4 from entry into force); executive measures such as the June 2026 directive are 0, which argues for an executive and a statutory route.
- `L.scale` 1 at the fast end (Colossus, 122 days, the builder's own claim), 2 typical; `L.build_power` 4 only for onsite generation, 8 or more for grid power (IEA, April 2025, from search snippets).
- `H.fund_oversight` 3 (range 2 to 4) and `A.self_improve` 2 hold.
- Not carried in v0: `H.nationalize` 1 (assumed), `H.propose_treaty` 2, `H.grant_rights` 4 (assumed), `L.safety_invest` 2 (assumed; a targeted fix took 18 days in June 2026); the actions with no delay in v0 (`pause_mandate`, `shutdown_attempt`, `comply`, `open_weights`, executive `deregulate`) are 0 on the record, `L.race` 1, `L.lobby` 2 (assumed).
- Open for the owner: the mapping rule (section 3), and the anchor of `regulate_up`.

The report of a second pause (NewsBytes, 5 October 2026) is most likely a re-dated copy of the June story; it is not carried.

## 8. Changelog

- 2026-11-14: registered (D1 to D6). Disclosure: the model file and the structure tests were written in the same session before this registration was committed; the guards follow the owner's decisions of section 4 and no claim, kernel or bounded query of v0.1 had been run (the harness was checked on one query that no claim reads: the shortest play to `adoption = 2`, two ticks).
- 2026-11-15: part A run once from `cac9190` (reports/agi_v0_1_part_a_2026-11-15.md): D1 and D2 met, D3 (a) not met, D3 (b) met, D4 (a) not met (first sight from a harness defect, `active[4]` not asserted; the query fixed and D4 rerun, still not met by the treaty route), D4 (b) met. A first start killed by the session's own restart command after two parts of D1 is kept as `reports/agi_v0_1_parts_interrupted.jsonl`. The probe of section 6 run after part A.
