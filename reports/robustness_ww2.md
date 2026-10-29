# WW2: robust and fragile findings under the ambiguous windows (exploratory)

**Exploratory.** This is not a rerun of any registered claim's verdict, and nothing here changes one. It asks of results already recorded and run whether they stay the same from every member state of the ambiguous layer that the owner's decision 7j adds (docs/owner_decisions_2026-10-23.md; docs/ambiguous_levels.md). Each finding is **robust** (the same answer from every member) or **fragile** (the answer depends on the member, with the members named). Members are not weighted (docs/ambiguous_levels.md section 2).

Reproduce with `python scripts/robustness_ww2.py t13` (about 15 s) and `python scripts/robustness_ww2.py t9` (about 6 min). Each question is answered per member with `wavefront.analysis.robust`, using the engine, start state, built-ins, hypotheses and strategies of the recorded test, imported from the test module, so the comparison is like for like. For each question the script checks that the canonical start state is one of the members.

## The windows as applied

Layers built by `scripts/build_ambiguous_layer.py` from `data/ambiguous_windows.csv` and `data/ambiguous_members.csv`. A layer file is its canonical file with only the windowed variables changed. The canonical files are unchanged, and `tests/evidence/test_ambiguous_layer.py` checks all of this.

| Layer | Variable | Members | Files (end of quarter) |
|---|---|---|---|
| `snapshots/ww2/hindsight_ambiguous/` (v0), `snapshots/ww2/hindsight_v1_ambiguous/` (v1) | `italy_estranged` | {true, false} | 1938Q2 to 1939Q1 |
| same | `belief_GER` | {will_not_fight, will_fight} | 1938Q2 to 1938Q4 |
| `snapshots/ww2/hindsight_v1_ambiguous/` | `oil_GER` | {dependent, secured} | 1939Q3, 1939Q4 |

So 1938Q2 to 1938Q4 have 4 members each and 1939Q1, 1939Q3 and 1939Q4 have 2 each. The Cold War window (`belief_force_USA`, cw_v1 replay, 1958 to 1961) is in the table and not built (status: to build after cw_v1's replay coding is final).

## Results

### T13: the departure quarter along the realized path (v0, symbolic engine)

The reading is that of `tests/ww2/scenarios/test_T13.py`, primary: WEST's kernel for `balance_europe` on v0, and the snapshot states with their built-ins under each `aims_GER`. Membership of the window states, ticks 10 to 13 (files 1938Q2 to 1939Q1):

| aims_GER | 1938Q2 | 1938Q3 | 1938Q4 | 1939Q1 |
|---|---|---|---|---|
| revisionist | in the kernel, robust (4 members) | in, robust (4) | in, robust (4) | in, robust (2) |
| hegemonic | outside the kernel, robust (4) | outside, robust (4) | outside, robust (4) | outside, robust (2) |

**Departure quarter.** Over all 128 member paths (every choice of member at each window file), the departure is **robust**:
- revisionist: tick 14, the decisions of 1939Q3;
- hegemonic: tick 1, the decisions of 1936Q2.

Both are the recorded departures. The departure states (1939Q2.json and 1936Q1.json) are outside the windows, so the recorded driving variables at those states are unaffected (not recomputed). Structurally, v0 reads neither windowed variable in a way that is live here: no v0 guard reads `belief_GER`, and the only guards on `italy_estranged` also require `~axis`, while `axis` is true (and monotone) from 1936Q4.

The v1 refinement check of T13 (bounded checker) was not asked.

### T9: the interim quarterly reading (v1, bounded checker with fixed strategies)

T9 starts in a window. Its start state, 1939Q1.json with its built-ins, is inside the `italy_estranged` window. `belief_GER` there is concrete (the window closes at 1938Q4), and T9 sweeps it anyway. There are 2 members, `italy_estranged=true` and `italy_estranged=false`.

The readings are those of `tests/ww2/scenarios/test_T09.py`: `aims_GER = hegemonic`; the profile `deterred`; the alliance counterfactually concluded; `poland_blocked` through tick 20.

| belief_GER | {WEST, USSR} | {WEST} | {USSR} | as the record has it (no alliance) | {WEST, USSR} without `deterred` |
|---|---|---|---|---|---|
| will_not_fight | outside, robust | outside, robust | outside, robust | outside, robust | outside, robust |
| uncertain | outside, robust | outside, robust | outside, robust | outside, robust | outside, robust |
| will_fight | **inside, robust** | inside, robust | inside, robust | outside, robust | outside, robust |

- **Pivotal coalitions.** The coalitions over {WEST, USSR} that keep Poland are the same from both members in every row. That is: none below `will_fight`; at `will_fight` with the alliance concluded, each of {WEST} and {USSR} alone suffices, by fixed strategy. This is because `deterred` forbids the attack while the alliance holds and the belief is `will_fight`.
- **"Otherwise contested."** For {GER} and Poland taken, the region is **forced, robust**, at both `will_not_fight` and `uncertain`.
- **Timing.** WEST can first bring `will_fight` about at tick 14, and Poland is first taken at tick 14. Both are robust.

**T9's interim reading is therefore robust under the window.** This is expected: in v1, as in v0, `italy_estranged` is read only by guards that also require `~axis`, and `axis` is true at the start state.

### K2: the summer-1939 pivotal coalitions

**Unaffected; not computed.** K2's entry state is v1's state at the start of 1939Q3, which is `1939Q2.json` with its built-ins (tests/ww2/crisis_1939/common.py). That file is in no window:
- the `italy_estranged` window ends at 1939Q1;
- the `belief_GER` window ends at 1938Q4, and K2 sweeps the entry level anyway;
- the `oil_GER` window starts at 1939Q3.

The `oil_GER` window touches K1's exit comparison with `1939Q3.json` (docs/crisis_1939_decisions.md C12), which was not asked here.
