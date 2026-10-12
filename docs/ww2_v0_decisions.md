# WW2 v0: architect's decisions for the model (step 1.5)

Inputs: [ontology_ww2.md](ontology_ww2.md), [actions_ww2.md](actions_ww2.md), [ww2_v0_notes.md](ww2_v0_notes.md) (the draft's replay check and test-by-test analysis), the hindsight snapshots. These decisions settle the open points the draft raised. Each is logged in [guard_changelog_ww2.md](guard_changelog_ww2.md) where it changes a guard, effect or invariant after a computed result was seen. The registered claims in ww2_testbed.md section 5 are not edited; where a claim cannot hold as written, the test fails and the report says so.

## D1. Tick convention and same-quarter reactions

Accepted as in ww2_v0_notes.md section 2: the state at tick t is the start of quarter t; a row holds the quarter's decisions; a reaction to another actor's same-quarter decision appears one tick later and is marked [SQR] in `data/ww2/realized_moves.csv` with its real date. T1 replays that file. The three points where the model lags the hindsight snapshots by one tick (`treaty`, `polish_guarantee`, `poland`) are reported, and the phase 2 replay metrics allow a one-tick lag for reactions. Finer time for 1936Q1, 1939Q1 and 1939Q3 is phase 2 work (crisis sub-games).

## D2. The balance invariant

The skeleton's last clause made `balance_europe` false by definition from the lapse of Locarno to the Polish guarantee, which would decide T8 and T13 by definition rather than by computation. `balance_europe` is therefore:

```
balance_europe := german_regions < 5 ∧ france != fallen ∧ britain in {at_peace, at_war}
```

and the treaty clause becomes a separate invariant, not used by any registered test:

```
commitment_alive := treaty != dead ∨ polish_guarantee ∨ anglo_soviet_alliance ∨ war_west_ger == war
```

## D3. The 1936 option and a German-defeat ending (T2)

The draft's `arms_at_war` latch on `campaign_west` was chosen after a counterexample and is withdrawn. Instead:

- `campaign_west` (Nature) requires the current `arms_GER >= high`; its outcome stays nondeterministic (France falls or holds).
- WEST gains `offensive_west`, guard parts `at_war: war_west_ger == war` and `german_army_unready: arms_GER <= rising`, effect: no state change; Nature `campaign_rhineland` then resolves, deterministically, to the ending `GERMAN_DEFEAT` while `arms_GER <= rising`. Source: Gamelin's demand for general mobilization and the French General Staff's assessment of 8 to 9 March 1936; Blomberg's proposal to withdraw; the German army's own judgment of its inability to resist a French offensive in 1936 to 1937 (the historian confirms the citations). This is the structural fact T2 is about: the 1936 army could not fight France.
- `GERMAN_DEFEAT` is an ending (absorbing). It also gives the negative control "Britain alone defeats Germany by 1941" a real meaning: from the realized 1940 states it needs relaxing the unready-army part and more.
- The `arms_at_war` latch is removed from the state.

## D4. The Czech treaty obligation (T8)

Adopted as an institutional constraint, not a behaviour: fairness `czech_obligation` on WEST, trigger `last_GER == attack_czechoslovakia ∧ sudeten == german ∧ war_west_ger == peace`, within 1, responses `declare_war`, `concede`. Source: the Franco-Czechoslovak treaty of alliance of 25 January 1924 and the treaty of mutual guarantee signed at Locarno on 16 October 1925; the French statements of September 1938 and the British statement of 26 September 1938. (An earlier version of this decision gave a wrong date, 25 January 1925.) It is a named assumption and relaxable, so the mining layer shows whether it carries T8.

## D5. Hypothesis gates

The [H] gates on `occupy_bohemia`, `attack_poland`, `join_axis` and the effect of `attack_czechoslovakia` are accepted: a swept hidden objective defines the decision space, as in the toy model and the AGI design. The report states that T8's first half (concessions reach `NO_GENERAL_WAR` under revisionist aims) is a consistency check of the gates, and that the finding, if any, is the second half (what a concession does to the Western kernel under hegemonic aims).

## D6. State-space budget

The draft's encoding passed 3 million states. Reductions, each logged with the information it loses:

1. `belief_GER` is constant in v0 and leaves the state (it returns in v1 with T9).
2. `remember_last` only for `GER` and `WEST` (the only `last_*` reads).
3. `arms_JPN` is a constant, not a variable.
4. The `arms_at_war` latch is removed (D3).
5. Exploration is per hypothesis (one initial state), `max_states` 3 million.

If a hypothesis still exceeds 1 million states, the model step reports the count and uses the bounded checker for traces (T1, T4, T5 first half, T10) and, for kernel questions (T2, T8), a sufficiency check: WEST's strategy fixed by a profile, and the bounded checker showing that no play reaches the invariant's failure within the horizon. A kernel membership shown that way is reported as "sufficient check by fixed strategy", never as the kernel itself. Further reductions (for example `commit_US` to two levels) are allowed only with a changelog entry.

## D7. Negative controls and guard granularity (T10)

Guards may be declared as named parts, each a separate relaxable assumption (framework_spec.md section 3.1, added for this purpose). The model uses parts wherever a guard joins independent documented constraints, so that relaxation counts measure documented constraints rather than packaging. For the Far-East controls:

- a flag `china_war` set by Nature `china_incident` (the Marco Polo Bridge incident, 7 July 1937, and the decision for a general war in China), the main constraint on a northern strike;
- `strike_north` with parts `pact: anticomintern`, `army_free: not china_war`, `ussr_weak: arms_USSR == weak`;
- `campaign_siberia` with parts `no_two_front: not china_war` and `japanese_superiority`, which the record never supports (the Far Eastern Red Army outnumbered the Kwantung Army; Nomonhan 1939), written as a condition the v0 state never satisfies.

The registered expectation "three or more relaxations" is then tested as registered. If the count is lower, the test fails and the report proposes an amendment of the claim for the owner's decision; the model is not tuned to the number. The two controls with no variable in v0 (Germany conquers the United States; Britain alone defeats Germany by 1941 before D3) are reported as vacuous where they are, never as passes.

## D8. The horizon artifact in T5

The second half of T5 holds in v0 because the chain of campaign, air battle and invasion does not fit before 1941Q1. The test passes as registered; the report says why, and phase 2 (horizon 1945) re-tests it.

## D9. The guarantee's belief condition (T4)

Kept as registered. The report describes it as the political precondition the record supports (ww2_v0_notes.md section 5), not as a capability result.

## D10. Tests to implement in this step

T1, T2, T4, T5, T8 and T10 are un-skipped and implemented against `models/ww2/v0.py` with the hindsight snapshots as starting states (helper: fix `aims_GER` and `aims_USSR` per hypothesis when loading a snapshot, since the snapshots sweep them). T3, T9 and T13 stay skipped (phase 2). A failing registered test is a result: it stays failing, the report explains it, and any guard edit made in response is logged.

## D11. Deliverables

`models/ww2/v0.py` (every action with `source=` from the catalogue; parts named as in D3 and D7), `tests/ww2/test_model_ww2.py`, the six scenario tests, `docs/guard_changelog_ww2.md` entries, `reports/ww2_v0.md` (per-test outcome with rendered traces, state-space counts per hypothesis, the parameter budget, informativeness over the T10 controls, the [SQR] table, failures with proposed amendments), and `reports/ww2_v0_viz.html` (the hegemonic hypothesis, the T1 trace).
