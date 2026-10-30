# Ambiguous periods as sets of levels

Owner's decision of 2026-10-27: adopt "ambiguous periods as sets". This note gives the semantics, what the change does and does not do, where it sits in the specification, and a list of candidate windows for the owner. It is logged as framework change 2 in [framework_changes.md](framework_changes.md).

## 1. The problem

History moves continuously. A snapshot gives each variable one level, so where a quantity crosses a threshold during a period, the quarter (or year) in which the snapshot moves it is a judgement. Where independent readings of the record disagree over a window, a single level makes every finding from that window conditional on a choice nobody recorded as a choice. The replays give the clearest case. Two independent readers (reports/replay_ww2_frus_claude/README.md, reports/replay_ww2_frus_deepseek/README.md) read `italy_estranged` as false (Italy reconciled with the West) from 1938Q2, after the Anglo-Italian agreement of 16 Apr 1938, while the hindsight snapshot keeps it true throughout.

## 2. Semantics

**A snapshot with level sets denotes a set of concrete states.** Over a contested window a snapshot may give a variable a set of levels instead of one (`italy_estranged ∈ {true, false}`). The snapshot then denotes the product set: one concrete state for each combination of member levels of its set-valued variables, with every other variable, built-in and latch as the snapshot gives them. A snapshot without a set denotes exactly one state, as before. A set is a statement about the evidence ("the record supports each of these levels at this date"), not about the world: the world was in one state, and we do not know which.

**Every question is asked per member.** Kernel membership, the forced, shortest and margin distances, forced/blocked/contested status, attractor ranks, pivotal coalitions and sensitivity rows are computed from each member state on its own. A finding is:

- **robust** when it has the same answer from every member;
- **fragile** when the answer depends on the member. A fragile finding is reported with the members on which each answer holds (for example "fragile: in the kernel from [italy_estranged=true]; not from [italy_estranged=false]").

The report's deliverables stay those of CLAUDE.md (minimal assumption sets, kernel membership and distance, pivotal coalitions); robust/fragile is a qualifier on each of them, never a new kind of finding. A bare reachability result stays a non-finding whether it is robust or not.

Asking per member differs from asking once of the whole set. `pivotal(g, e, initial=members)` returns the coalitions that force the ending from *every* member, which is a weaker statement than "the same coalitions are minimal from each member": a coalition can force from both members while a smaller one forces from one of them. The robust wrapper answers the second question; the first stays available and is what a caller gets by passing all members as `initial`.

**No engine change.** The explicit engine and the symbolic engine already take a set of start states (`explore(cm, initial=[...])`; `reachable(enc, initial=enc.states_bdd(...))`). With the symbolic engine a caller asks per member through `robust(question, members, ask)` with its own `ask`. The members are explored together in one graph, and the per-member answers are read off the fixpoints for each member's state id; only sensitivity, which perturbs start states, explores once per member.

**Order of members.** Set-valued variables in the model's declaration order, each one's levels in the variable's level order; the first variable varies slowest. Members are labelled by their set-valued levels (`cap=low, pick=b`).

**No probabilities.** Members are not weighted, and nothing is averaged or counted as "holds in k of n members" toward a verdict. A fragile finding is reported as fragile, with its split; turning that into a probability would need a distribution over readings that the record does not give.

## 3. Snapshot format

A variable entry is either a single level, as now:

```json
"italy_estranged": {"level": true, "confidence": "medium", "indicators": [...]}
```

or a set of levels over a contested window:

```json
"italy_estranged": {
  "levels": [
    {"level": true,  "confidence": "medium", "indicators": [<Axis, Spain, Munich...>]},
    {"level": false, "confidence": "low",    "indicators": [<Anglo-Italian agreement, 16 Apr 1938>]}
  ],
  "ambiguity": "the threshold is crossed between the Anglo-Italian agreement (16 Apr 1938) and the Pact of Steel (22 May 1939); two independent replay readers read it crossed, the hindsight reading does not"
}
```

- `levels` and `level` are mutually exclusive (an entry with both is invalid), and `confidence` and `indicators` belong to the members, not to the entry.
- At least two members; a single level is written with `level`. The loader refuses a level given twice.
- **Confidence and indicators per member level.** Each member carries the provenance rule of a single level (indicators required unless `confidence: "assumed"`). This keeps the evidence for each reading next to it; a member supported by no evidence is visibly `assumed`.
- `ambiguity` (required, non-empty) says why the crossing is a judgement in this window: the threshold, the readings and their dates.

**Built-ins stay single-valued.** A pending counter, a last action or a fairness count is derived from a dated decision by a stated rule; if the decision itself is ambiguous, the analyst writes two snapshots (or sets the variable it acts on), not a set of counters. Latches are filled into each member state as for the model's own initial states, so a latch whose condition holds in one member and not another is set in the first only; a latch given as `unset` while its condition holds in some member is refused naming that member.

**The snapshot convention.** The clock-consistency pass of the hindsight builders (owner's decision 7, 2026-10-15; spec section 9) produces concrete levels and is unchanged. A set is written by the modeller, with its provenance, over the builder's output. Where the pass would move a variable to the model's own clock, a set on that variable over the same window should contain the model's value, so that the clock convention is one of the members and not silently overridden.

## 4. API

- `wavefront.evidence.snapshot_to_states(data, cm) -> SnapshotStates` and `load_snapshot_states(path, cm)`: `states` (the product set), `ambiguous` (each set-valued variable with its levels), `members` (per state, the set-valued variables' levels), `label(i)`, `is_set`. `snapshot_to_state` and `load_snapshot` are unchanged for a snapshot without a set and refuse one with a set, naming the variables and pointing at `snapshot_to_states`. `level_set(entry)` reads either form of an entry without a model.
- `wavefront.analysis.robust(question, members, ask) -> Robustness`: the general wrapper; `ask` answers the question for one state. `Robustness` has `labels`, `answers`, `robust`, `verdict` (`"robust"` or `"fragile"`), `value` (the common answer when robust), `classes` (members grouped by answer) and `summary()`.
- Companions over one graph explored from the members: `robust_kernel(g, members, coalition, invariant, adversary=None) -> RobustKernel(in_kernel, distance)`, `robust_status(g, members, coalition, ending)`, `robust_attractor(g, members, coalition, target)`, `robust_pivotal(g, members, ending)`; and `robust_sensitivity(model, members, invariant, coalition, ...)` (one exploration per member).
- `run_all(model, members=...)` explores from the members and fills `Analysis.robustness` (kernel membership and distance per invariant and coalition, status per ending and coalition, pivotal coalitions per ending); `render` adds a section "Robust and fragile findings" when it is set.
- CLI: `wf viable --snapshot FILE` and `wf report --snapshot FILE` (new on `report`, with `--fix`) list the members and print robust/fragile when the snapshot has a set; output for a snapshot without a set is unchanged. `wf viz --snapshot` takes a single-state snapshot only (the loader's refusal names the set).

## 5. The replay harness and its metrics

A hindsight snapshot may carry a set; replay snapshots, which are built from accepted proposals, do not (a copied resource variable keeps the hindsight entry, set included).

- **Agreement.** A replayed level agrees with a set-valued hindsight level when it is in the set (a copied set agrees when it is contained in the hindsight set). These variable-quarters count in the per-variable agreement as agreeing, and are also counted and reported separately (`Metrics.ambiguous`; one summary line: the replay is in the set on k of n set-valued quarters, per variable), so the effect of the sets on the headline figure is visible. The "reading nothing" baseline counts a quarter as unread-agreeing when the initial level is in the set.
- **Flips.** A documented flip across a window (a concrete level `a` before a run of set-valued quarters, a concrete `b != a` after it) is one flip `a -> b` dated by the window: from its first quarter to the first concrete quarter after it. A replayed flip to `b` anywhere in that range has lag 0; outside it the lag is counted from the nearer end; lag in days is not given for a windowed flip. A run of set-valued quarters with the same concrete level on both sides documents no flip. A replayed flip that answers no documented flip but lands in a set-valued quarter on a level of that quarter's set, or that comes back on the first concrete quarter after a window from a level of the window's set to that quarter's hindsight level, is listed as a flip inside an ambiguous window, not as a false flip (the return was added 2026-10-30: a replay agreeing in every quarter of a window has no false flip at its end).
- **Cold War metrics** (`replay_cw`): agreement against a set-valued hindsight truth is membership; C6's "the replayed belief exceeds the hindsight force" is true when it exceeds every member, false when it exceeds none, and undetermined (`None`, fragile) otherwise.

Without a set anywhere every metric is computed exactly as before.

## 6. What this does not do

- No probabilities or weights over members (section 2).
- No sets in the model: the model's `init`, its swept hidden variables (`init=None`, which are hypotheses about objectives, not readings of evidence) and its transition relation are untouched. A set on a hidden objective is not the same thing as a swept hypothesis and is not offered: hypotheses stay per-hypothesis reports (spec section 8).
- No intervals of time inside a tick: the window is a run of snapshots, each still dated at its tick.
- No set-valued built-ins (section 3), and no sets in proposals or reviewed replay snapshots.
- No domain snapshot is changed. Which periods are ambiguous is a modelling decision for the owner (section 8).

## 7. Where it goes in the specification, and whether it is a framework change

Spec sections changed: 7 (the robust wrapper), 8 (`run_all(members=)` and the report section), 9 (the snapshot format, the loader, the replay metrics), 10 (the CLI options). `snapshots/schema.json` gains `$defs.variable_set`.

It is a framework change in the sense of [PHASES.md](PHASES.md) phase 3 and [framework_changes.md](framework_changes.md): the snapshot schema and loader are part of the contract the spec owns (section 9), and the analysis and report entry points are extended. It is episode-agnostic: the rationale (a threshold's crossing is a judgement where readings disagree; carry the readings and separate the findings that depend on the choice) names no episode; the episode that forced it is named only in the forcing-need column. It is logged as change 2 of the phase 3 budget of 5 (owner's decision 7c counted the cadence as 1), and the WW2 suite was rerun (framework_changes.md).

## 8. Candidate ambiguous windows (proposals only; nothing is changed)

1. **`italy_estranged ∈ {true, false}`, WW2 v0 and v1 hindsight, 1938Q2 to 1939Q1.** Both replay readers read Italy reconciled with the West from 1938Q2 (Claude) or 1938Q1 (DeepSeek), citing the Anglo-Italian agreement of 16 Apr 1938 (in force 16 Nov 1938) and the change of Italian attitude noted in the dispatches; the hindsight keeps it true from Ethiopia (Oct 1935) on. The window closes with the Pact of Steel (22 May 1939), so 1939Q2 is arguably concrete `true` again; the owner's own example uses 1938Q2 to 1939Q2, and either end is defensible. After June 1940 (Italy at war with France and Britain) no reading supports `false`, so the readers' later disagreement is not a candidate.
2. **`belief_GER`, WW2 hindsight, 1938Q2 to 1938Q4: {will_not_fight, will_fight}.** The second variable on which both readers disagree with the hindsight: both read Berlin as expecting the West to fight over Czechoslovakia in the summer and autumn of 1938 (the May crisis, the Sudeten crisis of September), where the hindsight reads `will_not_fight` (Munich). The ontology already notes that `belief_GER`'s defence rests on secondary reconstructions (docs/ontology_ww2.md). Whether `uncertain` belongs to the set is the owner's. The readers' `uncertain` against the hindsight `will_fight` from 1939Q3 (after the declarations of war of 3 Sep 1939) is a weaker candidate: a declaration of war is hard to read as doubt about resolve.
3. **`oil_GER ∈ {dependent, secured}`, WW2 v1 hindsight, 1939Q3 to 1939Q4.** v1's `accept_pact` sets `secured` in 1939Q3 (the pact of 23 Aug 1939); the v1 snapshots read `dependent` until the Commercial Agreement of 11 Feb 1940; the ontology's threshold names both agreements; the snapshot change that dated `secured` from the credit agreement of 19 Aug 1939 was withdrawn on the owner's decision 5c, and the difference stays tabulated (docs/crisis_1939_decisions.md C12, docs/guard_changelog_ww2.md row of 2026-10-23). A set would carry both readings without using the credit agreement as a source: the `secured` member would rest on the model's clock under the snapshot convention (the pact) and the `dependent` member on the record's delivery date. Under decision 5c the owner decides whether the `secured` member may stand on that basis.
4. **Cold War `belief_force_USA`, the contemporaneous (replay) snapshots of 1958 to 1961.** The blind replay over the CIA estimates read the force in being (`few`: about ten prototype ICBMs), the manual replay the projections of the missile gap (`survivable`); reports/replay_cw_crest_deepseek.md. The owner's decision 7d fixed the reading as the projected force, and decision 7g gives the variable its own scale (projected numbers of delivery vehicles in bands) for cw_v1 and the Cold War replay episode, so on v0's scale the ambiguity is one of reading, now decided, not of the record. What stays a candidate is the projection itself: the estimates of 1957 to 1961 give ranges (a low and a high case, revised downward through 1961), so on the 7g scale a set of the bands between an estimate's low and high projection, per year, would carry the record's own spread; v0 (`{few, survivable}`) only if the owner wants C6 reported robust or fragile to the pre-7d reading. The hindsight truth is not in question.
