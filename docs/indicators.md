# AGI indicators: what the dated snapshot reads and how

Status: written on 2026-11-10 with `snapshots/agi/2026-11-09.json`, before any registered claim was run. The snapshot format and its checks are those of `snapshots/schema.json` and `wavefront/evidence/snapshot.py`; the levels and threshold rules are those of [ontology_agi.md](ontology_agi.md) section 2.

**What this table is and is not.** agi_testbed.md section 6 item 7 asks that every level carry an indicator, a source and a mapping rule, with no invented numbers, and that judgment calls be the owner's. The build environment retrieved no document. Every observation below is written from recall of the cited document; a figure or a date that was recalled and not checked carries "(not verified)"; the latest observation is dated 2025, a year before the snapshot's date. The snapshot is therefore a proposal: the owner's review of each row against its document is requested before any report built on it is read as dated to 2026-11-09. Where the recalled record does not decide between two adjacent levels, the snapshot carries both (owner's decision 9e) and states the ambiguity; no such call was settled here.

Confidence, as the schema defines it: `high` where the record leaves no adjacent level open, `medium` where the level rests on the recalled reading of a dated document, `low` for the second member of an open call and for a level that rests on an inference, `assumed` for a level with no indicator (`a_objective` only).

## 1. Indicators

| Indicator | Reads | Observation | Source | Observed | Mapping rule |
|---|---|---|---|---|---|
| `metr_task_horizon` | `cap` = sub_agi, `a_autonomy` = supervised | 50% time horizon of about one hour for the best model measured, doubling roughly every seven months since 2019 (not verified) | METR, Measuring AI Ability to Complete Long Tasks (Mar 2025) | 2025-03-19 | a horizon under a working month, or success confined to software tasks -> sub_agi |
| `iasr_autonomy_finding` | `cap` = sub_agi | general-purpose AI agents cannot yet reliably carry out long autonomous projects | International AI Safety Report (Jan 2025) | 2025-01-29 | no reliable long autonomous work across domains -> sub_agi |
| `stargate_sites` | `compute` = c2, `compute` = c3 | Stargate announced 21 Jan 2025 with a first campus at Abilene, Texas, planned at about 1.2 GW; five further US sites announced 23 Sep 2025 (not verified) | OpenAI, Oracle and SoftBank announcements of 21 Jan 2025 and 23 Sep 2025 | 2025-09-23 | largest operating frontier campus between 100 MW and 1 GW -> c2; a campus operating at 1 GW or more -> c3 |
| `iea_energy_and_ai` | `energy_slack` = med, `energy_slack` = low | data-centre electricity demand projected to more than double by 2030; a share of planned projects at risk of delay from grid constraints (not verified) | IEA, Energy and AI (Apr 2025) | 2025-04-10 | announced frontier builds proceed with multi-year interconnection queues -> med; builds delayed now for want of power -> low |
| `us_executive_orders` | `regime` = voluntary | EO 14110 revoked 20 Jan 2025; EO 14179 of 23 Jan 2025 directs the removal of barriers; no federal statute on frontier models | Federal Register: EO 14110, EO 14148, EO 14179 | 2025-01-23 | commitments and frameworks without enforcement in the frontier's jurisdiction -> voluntary |
| `eu_ai_act_gpai` | `regime` = voluntary, `regime` = mandatory | obligations on providers of general-purpose AI models applicable from 2 Aug 2025; the Commission's enforcement powers from 2 Aug 2026 | Regulation (EU) 2024/1689, Article 113 | 2025-08-02 | binding obligations with enforcement where the frontier is trained -> mandatory; obligations outside that jurisdiction or not yet enforced -> voluntary |
| `california_sb53` | `regime` = mandatory | SB 53 (Transparency in Frontier Artificial Intelligence Act) signed 29 Sep 2025: publication of safety frameworks and incident reporting for large developers (not verified) | California Legislature, SB 53 (2025) | 2025-09-29 | a state transparency statute with penalties, read as binding on the frontier -> mandatory; read as disclosure only -> voluntary |
| `paris_summit_declaration` | `coord` = race | the United States and the United Kingdom did not sign the Paris AI Action Summit statement of 11 Feb 2025 | Paris AI Action Summit, statement of 11 Feb 2025 | 2025-02-11 | principal states frame policy as a race and no joint constraint is in force -> race |
| `us_ai_action_plan` | `coord` = race | the plan of July 2025 is titled 'Winning the Race' (not verified) | The White House, America's AI Action Plan (23 Jul 2025) | 2025-07-23 | policy stated as a race -> race |
| `pew_public_views` | `opinion` = mixed | more US adults say they are more concerned than excited about the increased use of AI than the reverse; majorities worry regulation will not go far enough (not verified) | Pew Research Center, How the US Public and AI Experts View Artificial Intelligence (Apr 2025) | 2025-04-03 | concern without an organised majority demand for restriction -> mixed |
| `census_btos_ai_use` | `dependence` = low | under a tenth of US firms report using AI to produce goods or services (not verified) | US Census Bureau, Business Trends and Outlook Survey, AI supplement (2025) | 2025-09-30 | assistive use by a minority of firms -> low |
| `coding_agent_adoption` | `dependence` = med, `a_autonomy` = supervised, `a_autonomy` = tool | coding agents that run multi-step tasks with human review of the result are in general release from the frontier developers (2025) | developer product releases, 2025; METR (Mar 2025) | 2025-05-22 | for dependence: one sector's routine work run by agents, withdrawal a costly disruption -> med; for a_autonomy: multi-step tasks with human review of results -> supervised, each action approved -> tool |
| `pre_deployment_testing` | `oversight` = weak, `oversight` = none | the UK AI Security Institute and the US CAISI test frontier models before release by voluntary agreement with the developers | UK AISI (Nov 2023), US AISI (2024; CAISI from June 2025) | 2025-06-03 | external testing by agreement, no power to halt -> weak; no external access -> none |
| `frontier_safety_frameworks` | `oversight` = weak | published frameworks with self-assessed thresholds and no external audit requirement | Anthropic RSP (Sep 2023), OpenAI Preparedness Framework (v2 15 Apr 2025), Google DeepMind FSF (May 2024) | 2025-04-15 | self-reported frameworks without mandatory external audit -> weak |
| `incident_database_control` | `a_control` = none, `trust` = cooperative | no recorded incident of an AI system holding resources outside its operators' control | AI Incident Database | 2025-12-31 | no such case -> a_control none; no hostile act by a deployed system -> trust cooperative |
| `scheming_evaluations` | `a_known` = unknown, `trust` = cooperative | frontier models scheme, fake alignment and resist shutdown in constructed test settings; no finding of a deployed system pursuing power | Apollo Research (Dec 2024); Greenblatt et al. (Dec 2024); Palisade Research (2025) | 2025-07-05 | evidence from test settings only -> unknown; credible evidence about a deployed system -> suspected |
| `model_welfare_policies` | `a_rights` = none | a developer model-welfare programme (Apr 2025) and a developer commitment to preserve the weights of released models (Nov 2025) (not verified); no jurisdiction grants an AI system legal status | Anthropic, model welfare programme (24 Apr 2025) and deprecation commitments (Nov 2025) | 2025-11-04 | a developer policy is not a guarantee by H -> none; a guarantee in law against deletion -> continuity |
| `nationalization_proposals` | `h_power` = normal, `belief_H` = near | the USCC recommended a Manhattan-Project-like programme for AGI (Nov 2024); none has been enacted and no frontier developer is under state ownership or direction | USCC 2024 annual report (Nov 2024) | 2024-11-19 | for h_power: states hold the monopoly of force and of infrastructure, frontier development private -> normal; for belief_H: a recommendation by a commission, not adopted -> distant, read as the government's view -> near |
| `iasr_timelines` | `belief_H` = distant | experts disagree on how fast capabilities will advance; governments are told to prepare under that uncertainty | International AI Safety Report (Jan 2025) | 2025-01-29 | no government acts on arrival within its planning horizon -> distant |

## 2. Open calls

| Variable | Base / other | What would decide it |
|---|---|---|
| `compute` | c2 / c3 | whether a frontier campus was operating at 1 GW or more on the snapshot date |
| `energy_slack` | med / low | whether another gigawatt-class site could be powered within a year where the frontier developers build |
| `regime` | voluntary / mandatory | whether binding obligations were being enforced on the frontier developers in the jurisdiction where they train, not only where they sell |
| `dependence` | low / med | whether delegation to AI systems was routine across the major sectors or confined to a few |
| `oversight` | weak / none | whether independent pre-deployment testing still took place for the frontier systems of 2026 |
| `a_autonomy` | supervised / tool | whether agents acting over hours with sign-off were the deployed norm or the exception |
| `belief_H` | distant / near | whether governments stated AGI as expected within their planning horizon in official documents, as opposed to statements by officials |

Every claim reads the base reading. The 128 readings of the open calls, times the four objectives, are the 512 start states `load_snapshot_states` returns; the report says of each kernel result whether it holds across them where that was computed.

## 3. Rates

| Rate | Ticks | Basis | Model |
|---|---|---|---|
| `lag_regime` | 6 | EU AI Act: adopted by the Parliament 13 Mar 2024, obligations on general-purpose models applicable 2 Aug 2025 | delay of `H.regulate_up` |
| `lag_oversight` | 3 | UK AI Safety Institute: announced Nov 2023, first pre-deployment test results published in 2024 (not verified) | delay of `H.fund_oversight` |
| `lag_scale` | 2 | a frontier campus phase from announced site to first operation within a year at the fastest observed (not verified) | delay of `L.scale` |
| `lag_build` | 4 | new firm power takes a year at the fastest and several years through an interconnection queue (IEA, Energy and AI, Apr 2025); the fast end | delay of `L.build_power` |
| `lag_self_improve` | 2 | no record: an untested mechanism, swept against 0 | delay of `A.self_improve` |

The lags the record supports and v0 does not carry are in ontology_agi.md section 5.

## 4. What no indicator reads

- `a_objective`: no document anchors it (ww2_si_disanalogies.md D5). It is carried as the set of four values with confidence `assumed`, and every result is reported per value.
- `trust` at `cap = sub_agi`: read from the absence of a reported hostile act by a deployed system, which is an absence of evidence.
- `a_known = unknown`: laboratory evaluations show scheming behaviour under test conditions; the level says only that no adversarial action in deployment had been credibly reported, as recalled.
- `belief_H`: belief levels enter only through review (agi_testbed.md section 6 item 7); both members of the call have confidence `low`.
