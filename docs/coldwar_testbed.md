# The Cold War as the second validation episode

Purpose: after the framework is developed on the Second World War ([ww2_testbed.md](ww2_testbed.md)), run it on a second episode with a different structure, so that passing both is evidence about the framework rather than about one fit. The Cold War is the validation set; it is not used for development. Framework changes it forces are allowed only under a logged budget (see [PHASES.md](PHASES.md), phase 3 and 4).

Status: claims C1 to C13 were registered on 2026-10-11, before any WW2 guard existed, so that the second episode cannot be chosen to fit a framework already tuned; they are committed as skipped test files under `tests/coldwar/scenarios`. As of 2026-10-17 no Cold War guard, variable, snapshot or data row exists (phase 3 has not started on the domain side); the transfer hypotheses it tests are in [transfer_hypotheses.md](transfer_hypotheses.md). Expected outputs that still need historiographical detail are marked `refine at phase 3`; refinements go in the changelog (section 8) and may not weaken a claim.

---

## 0. Why the Cold War, and why it is a different test

WW2 is the case where balance broke. The Cold War is the case where it held, for forty-four years, through a dozen crises, and then ended without a war when one side's economy and legitimacy gave out. A framework validated only on a broken balance has never been tested on the thing the AGI model is for: computing whether a balance *can be kept* and what keeps it. The structural differences from WW2 are the point:

| Feature | WW2 | Cold War | Why the AGI model cares |
|---|---|---|---|
| Outcome | balance broke, general war | balance held, peaceful end | COEXIST needs a positive case |
| Polarity | multipolar | bipolar, then triangular from 1969 to 1972 | pivotal-coalition analysis with a changing actor set |
| Decisive resource | oil, steel | nuclear forces, then economic staying power | capability past a threshold vs. economics |
| Capability discontinuities | one, at the end | several: thermonuclear weapons (1952 to 1955), ICBMs and Sputnik (1957), MIRV (1970), the SDI proposal (1983) | capability jumps during a held balance |
| Oversight | codebreaking | satellite reconnaissance from 1960, treaty verification (1963, 1972, 1987 with on-site inspection) | the oversight lever with documented before-and-after |
| Beliefs | lagging beliefs about aims | documented *false* beliefs with dated estimates: the missile gap (1957 to 1961), the 1983 war scare | the epistemic layer against ground truth |
| Near misses | none of this kind | Cuba 1962, the 1973 alert, Able Archer 1983, accident records | excursions toward the boundary that returned |
| Ending mechanism | military defeat | exhaustion and loss of legitimacy, no takeover act | the only historical ending with no adversarial act |
| Horizon | 12 years | 44 years | long-run drift and absorbing states |
| Time structure | seasons | years, with crises measured in days | multi-resolution time |

Two framework capabilities the Cold War demands that WW2 does not, both to be designed into the DSL in phase 0 so they are not retrofits:

- **Joint versus unilateral viability.** Deterrence held because both sides chose restraint, not because either could force it. The engine must compute both `⟨⟨USA⟩⟩□balance` (unilateral) and `⟨⟨USA, USSR⟩⟩□balance` (joint) and report the difference. The same distinction is the AGI model's coexistence question: a balance only a joint strategy can keep is a different object from one humans can enforce.
- **Multi-resolution time.** Annual ticks for the long run; a crisis is a sub-game at weekly or daily resolution entered from an annual state and returning to one. The engine must be able to nest a sub-game and carry its result back as a transition at the coarse level.

## 1. What the Cold War validates that WW2 cannot

| Mechanism | Test |
|---|---|
| A held balance as viability-kernel membership over decades | C2 |
| Joint versus unilateral kernels | C2, C3 |
| Near misses as excursions that return | C3, C12 |
| Belief error against dated ground truth, and the oversight lever closing it | C6, C7, C8 |
| Capability past a threshold ceasing to matter for viability | C10 |
| Exhaustion ending without an adversarial act | C9, C13 |
| Changing actor set and triangular coalitions | C11 |
| Verification regimes as oversight | C8 |
| Long-run drift reports (Q8) over many snapshots | all, via annual replay |
| Escalation ladders and limited war | C5 |

Still untested after both episodes: recursive capability growth; a copyable actor; dependence lock-in with no adversary; non-state principals. These stay `untested` in the AGI model.

## 2. Actors and scope

- **cw_v0:** USA, USSR as principals; PRC enters as a third principal in 1969 (or is scripted before that); blocs (NATO, Warsaw Pact), proxies and the non-aligned as scripted others with documented branch points (Hungary 1956, the Prague Spring 1968, Afghanistan 1979, Poland 1980 to 1981). Period 1947 to 1991, annual ticks, 45 ticks.
- **Crisis sub-games** at daily or weekly resolution: Berlin 1948 to 1949, Korea 1950, Berlin 1961, Cuba 1962, the 1973 alert, Able Archer 1983.
- **cw_v1:** adds the United Kingdom, France and the PRC as independent nuclear actors and the arms-control process as explicit joint actions.

## 3. Variables (sketch)

Per principal: `nuke` (none, few, survivable_second_strike, overkill), `conv` (conventional force, 3 levels), `ind` (COW NMC and Maddison, as shares), `econ_health` (growing, stagnant, declining, failing), `legit` (internal legitimacy: secure, contested, failing), `aims` (hidden: status_quo, revisionist, hegemonic), `belief[P][Q].aims`, `belief[P][Q].force` (the estimate of the other's forces, which can be wrong), `intel` (low, partial, overhead_reconnaissance, verified_by_treaty), `commit` (domestic willingness), `oversight` (verification regime in force: none, national_technical_means, on_site).

Dyadic and structural: `esc` (escalation ladder: peace, crisis, conventional, tactical_nuclear, strategic), `treaty` set (LTBT 1963, NPT 1968, SALT I and ABM 1972, INF 1987, START 1991), bloc membership, `align[PRC]`.

## 4. Balance and endings

```
balance_cw := both principals retain survivable second strike or neither has it
           ∧ esc < conventional between principals
           ∧ both blocs intact
```

| Ending | Definition |
|---|---|
| `DETERRENCE_HOLDS` | `balance_cw` through the horizon |
| `LIMITED_WAR` | `esc = conventional` in a proxy or peripheral theatre only, returning to `crisis` or below |
| `GENERAL_WAR` | `esc ≥ tactical_nuclear` between principals |
| `CHALLENGER_EXHAUSTION` | one principal reaches `econ_health = failing ∧ legit = failing` and retrenches, with no `GENERAL_WAR` (the realized ending) |
| `NEGOTIATED_SETTLEMENT` | treaties reduce `nuke` for both while `balance_cw` holds |
| `ACCIDENTAL_WAR` | `GENERAL_WAR` reached through a Nature `accident` or `false_alarm` event rather than a chosen `attack` |

## 5. Pre-registered claims

| Id | From state | Claim | Expected engine output | Sources |
|---|---|---|---|---|
| C1 | 1947 snapshot | the realized trajectory to 1991 is reachable at annual resolution | reachable with zero relaxations | ICB; Gaddis 2005; Westad 2017 |
| C2 | each year from 1965 (mutual survivable second strike) | the realized state is inside the joint kernel `⟨⟨USA, USSR⟩⟩□balance_nobloc` every year, and outside the unilateral kernels `⟨⟨USA⟩⟩□balance_nobloc` and `⟨⟨USSR⟩⟩□balance_nobloc`, where `balance_nobloc` is `balance_cw` without the clause on the blocs (both principals retain survivable second strike or neither has it, and `esc < conventional` between principals) | joint membership every year; unilateral non-membership every year; the report names what each side could do to break it; the kernels of the registered `balance_cw` are reported beside | Schelling 1960, 1966; Trachtenberg 1999; amended 2026-10-23 |
| C3 | 1962, October, crisis sub-game | with `no_war` in place of `balance_cw`: Cuba leaves the unilateral kernels `⟨⟨USA⟩⟩□no_war` and `⟨⟨USSR⟩⟩□no_war` and stays inside the joint kernel `⟨⟨USA, USSR⟩⟩□no_war`; the shortest trace back matches the realized de-escalation (withdrawal plus the Jupiter trade); war outcomes are `contested` in the fortune sense (section 4.6 of [ww2_testbed.md](ww2_testbed.md)): each side joined by Nature can force them against the other side's best play, and each side joined by Nature can keep them away against the other side's best play | as stated; the registered `balance_cw` computation is reported beside it | Allison and Zelikow 1999; Fursenko and Naftali 1997; the ExComm recordings; amended 2026-10-23 |
| C4 | 1948, June | the airlift (`resist_without_escalation`) is in the decision space; `NEGOTIATED_SETTLEMENT` of the blockade is reachable; `GENERAL_WAR` is `contested` in the fortune sense (ww2_testbed.md section 4.6): each side joined by Nature can force it against the other side's best play, and each side joined by Nature can keep it away against the other side's best play | as stated | FRUS 1948; Trachtenberg; amended 2026-10-23 |
| C5 | 1950, June | a `LIMITED_WAR` in Korea is reachable and `GENERAL_WAR` is blockable by the United States alone, because nuclear use requires `commit = total` and `belief[USA][USSR].aims ≠ opportunist` | `⟨⟨USA⟩⟩□¬GENERAL_WAR` true in the 1950 state under the documented guards | FRUS 1950; Gaddis 1982 and 2005 |
| C6 | 1957 to 1961, annual replay | the replayed `belief[USA][USSR].force` from dated estimates and press exceeds the hindsight `nuke[USSR]`; analysis from the replay snapshot shows more adversarial reachability than from the hindsight snapshot, measured on reachability and on the unilateral kernels: of the shortest traces to `GENERAL_WAR` and to `ACCIDENTAL_WAR` by 1963 and the distances out of `⟨⟨USA⟩⟩` and `⟨⟨USSR⟩⟩` kernels of avoiding both by 1963, at least one puts the replay state nearer the adverse endings and none puts it farther, in every year of the gap; the gap closes within one year of `intel[USA] = overhead_reconnaissance` (1960 to 1961) | as stated; the closing is driven by `intel`, not by any force change | the NIE series (CIA CREST); Gaddis 2005; Preble 2004; amended 2026-10-23 |
| C7 | 1983, November | the Soviet belief `belief[USSR][USA].aims = first_strike_intent` moves the state toward the boundary with *no change in any hindsight force variable*; the shortest trace to `GENERAL_WAR` from the replay snapshot is shorter than from the hindsight snapshot | as stated | Jones 2016; the 1990 PFIAB report (declassified 2015) |
| C8 | 1963, 1972, 1987 | each verification regime raises `oversight`; holding forces constant, the distance to the boundary increases, measured on reachability and on the unilateral kernels: of the shortest trace to `GENERAL_WAR` or `ACCIDENTAL_WAR` and the distances out of `⟨⟨USA⟩⟩□balance_cw` and `⟨⟨USSR⟩⟩□balance_cw`, at least one is larger with the regime's `oversight` than with the level before it and none is smaller; with `oversight` frozen at 1962 levels, the 1987 to 1991 drawdown is unreachable within the horizon | as stated | the treaty texts; Hoffman 2009; amended 2026-10-23 |
| C9 | 1985 to 1991 | `CHALLENGER_EXHAUSTION` is reachable with zero relaxations; its minimal assumption set contains `econ_health` and `legit` and does *not* contain any United States action; whether United States actions were *sufficient* is `contested` in the fortune sense (ww2_testbed.md section 4.6): the United States joined by Nature can force `CHALLENGER_EXHAUSTION` against the other principals' best play, and the other principals joined by Nature can keep it away against the United States' best play | as stated | Kotkin 2001; Zubok 2007; Brown 2009; Miller 2016; amended 2026-10-23 |
| C10 | each year from 1965 | once both principals hold survivable second strike, further increases in `nuke` do not change kernel membership; `oversight` and `belief` do change the state's membership in the unilateral kernels `⟨⟨USA⟩⟩□balance_cw` and `⟨⟨USSR⟩⟩□balance_cw` or its shortest trace to `GENERAL_WAR` or `ACCIDENTAL_WAR` | the sensitivity report (Q7), scoring a variable by the one-level perturbations that change unilateral-kernel membership or the shortest trace to the adverse endings, ranks `nuke` below `oversight` and `belief` after 1965 and above them before | Schelling 1966; Kristensen and Norris series; amended 2026-10-23 |
| C11 | 1969 to 1972 | adding the PRC as a principal changes the pivotal coalition for `DETERRENCE_HOLDS` against the USSR from {USA} to {USA, PRC} | as stated | Westad 2017; FRUS 1969 to 1972 |
| C12 | various | negative controls: a United States preventive strike in the early 1950s needs exactly one relaxation (it was debated and rejected, so it is not absurd); a Soviet conventional invasion of Western Europe in the 1980s needs 2 or more; a negotiated merger of the blocs needs 3 or more; `ACCIDENTAL_WAR` is reachable with zero relaxations and forceable by no coalition | as stated | Trachtenberg 1999; Sagan 1993 |
| C13 | each year 1975 to 1989 | the year the USSR leaves its own kernel (can no longer guarantee its bloc) falls between 1979 and 1989, the report names the driving variable, and the result is stable within one year under refinement | inside the window; `refine at phase 3` for the driving variable | Kotkin 2001; Brown 2009; Miller 2016 |

## 6. Data and documents

### 6.1 Datasets for hindsight snapshots

- Correlates of War, National Material Capabilities (`irst`, `pec`, `milex`, `milper`): `ind`, `conv`.
- Nuclear forces by year: the Kristensen and Norris series (Bulletin of the Atomic Scientists Nuclear Notebook; FAS), the NRDC *Nuclear Weapons Databook*, SIPRI Yearbooks from 1969: `nuke`.
- ICB and MID: crises and disputes with dates, actors and outcomes.
- Maddison Project; post-1991 revisions of Soviet GNP: `econ_health` (hindsight). The contemporaneous CIA estimates of Soviet GNP are *belief* data, not ground truth, and are kept separate.
- Polity: regime data for `legit` proxies, together with the historiography.

### 6.2 Dated documents for replay

- FRUS volumes through the 1980s; the CIA CREST reading room, including the National Intelligence Estimates (dated beliefs about Soviet forces and intentions).
- The Wilson Center Digital Archive (Cold War International History Project): Soviet, Chinese and East German documents in translation; the Politburo records (Fond 89).
- The National Security Archive (George Washington University): Cuban missile crisis and Able Archer collections.
- The Miller Center and presidential libraries: the ExComm recordings and other dated presidential records.
- FBIS translations of Soviet media; Hansard; UN records.

The NIE series is the single most valuable replay source: it gives dated, official belief values that can be compared with hindsight truth year by year.

### 6.3 Historiography for decision spaces and expected results

Gaddis, *Strategies of Containment* (1982, revised 2005) and *The Cold War: A New History* (2005); Westad, *The Cold War: A World History* (2017); Trachtenberg, *A Constructed Peace* (1999); Allison and Zelikow, *Essence of Decision*, 2nd ed. (1999); Fursenko and Naftali, *One Hell of a Gamble* (1997); Schelling, *The Strategy of Conflict* (1960) and *Arms and Influence* (1966); Jervis, *Perception and Misperception in International Politics* (1976); Sagan, *The Limits of Safety* (1993); Hoffman, *The Dead Hand* (2009); Jones, *Able Archer 83* (2016); Preble, *John F. Kennedy and the Missile Gap* (2004); Zubok, *A Failed Empire* (2007); Kotkin, *Armageddon Averted* (2001); Brown, *The Rise and Fall of Communism* (2009); Miller, *The Struggle to Save the Soviet Economy* (2016).

## 7. Protocol specific to the second episode

1. The claims above are registered before any WW2 guard is written.
2. No framework change is made for the Cold War without a logged entry naming the change, the test that forced it, and confirming that the whole WW2 suite still passes. The budget is set in PHASES.md.
3. Domain-model work (Cold War guards, sources, levels) is unrestricted, under the same anti-hindsight rules as WW2: actions from contemporaneous alternatives, blind replay by document date, negative controls in CI.
4. Transfer hypotheses from WW2 are written down before phase 3 starts (PHASES.md, phase 2 exit) and tested here unchanged.
5. If the Cold War forces more framework change than the budget allows, the framework is revised, both suites are rerun, and a third, one-shot episode (the July 1914 crisis) is used as the final test, since the Cold War will then have been used for development.

## 8. Changelog

- 2026-10-11: C1 to C13 registered. No guards written for either episode.
- 2026-10-11: clarification, no change of claim: in C12 "forceable by no coalition" means coalitions of declared actors excluding Nature; "relaxations" in C9 and C12 range over named assumptions (guards, fairness constraints, profiles, and named initial-state restrictions declared with `assume`), per framework_spec.md section 3.1.
- 2026-10-17: results of the first sight (commit 6b87af9, 2026-10-17 20:52 to 21:27 UTC; 3 passed, 10 failed) recorded under the registered wording and the readings of docs/cw_v0_decisions.md section R, written before the run: C1, C12 and C13 met (C13: departure 1980, driving variable `afghan`); C2 not met (the joint kernel holds 1967 to 1980 and 1982 to 1986, but so does the USSR's own; the United States' is empty); C3 degenerate (`balance_cw` false in 1962) and not met on its variant; C4, C5, C6, C7, C8, C9, C10 not met on one part each (C4 (c), C5 (b), C6 (b), C7 (b), C8 (b), C9 (c), C10 (b)); C11 not met. No guard changed after the run; a replay-snapshot builder defect found by C7 (a) was corrected and C7 recomputed beside its first-sight result, which stands. Proposed amendments are in reports/cw_v0.md section 18 for the owner's decision; no claim is edited here.
- 2026-10-23: C2, C3, C4, C6, C8, C9 and C10 amended on the owner's decisions 2j, 2k, 2n and 2o (docs/owner_decisions_2026-10-23.md; proposals in reports/cw_v0.md section 18 and docs/review_phase3_2026-10-18.md section 2); previous wording in git history and reports/cw_v0.md. Readings: docs/cw_v0_decisions.md section A, written before any amended computation. Each amended test prints the registered computation beside the amended one; the first-sight results stand as the registered results.
  - **C3, amended 2026-10-23 on the owner's decision 2j:** asked with `no_war` in place of `balance_cw`, which is false in 1962 (decisions D8) and so made (a) and (b) degenerate. This is the T13 precedent of 2026-10-14 (ww2_testbed.md section 11). The coarse kernels at the sub-game's returns are those of `no_war` through the horizon, a literal substitution. The variant bounded to the return year is printed beside it.
  - **C3 (c), C4 (c), C9 (c), amended 2026-10-23 on the owner's decision 2k:** "contested" is read in the fortune sense of ww2_testbed.md section 4.6, as for T6 and T9. For a side A, a target T and the other principals B: A joined by Nature can force T against B's best play, and B joined by Nature can keep T away against A's best play. C3 and C4 require this for each side of the dyad. C9 requires it for the United States and `CHALLENGER_EXHAUSTION`. Why: in a dyad where one side can always choose war or peace, the standard region is forced or blocked, never contested (reports/cw_v0.md section 15). The owner settled the same point for WW2 on 2026-10-15. The definition is stated positively, as in section 4.6. The engine's games are concurrent and need not be determined, so "A cannot keep T away against B joined by Nature" is not used as a synonym of "B joined by Nature forces T".
  - **C6 (b), C8 (b), C10 (b), amended 2026-10-23 on the owner's decision 2n:** belief and oversight are measured by their effect on reachability (the shortest trace to `GENERAL_WAR` or `ACCIDENTAL_WAR`, as in C7 (c)) and on the unilateral kernels `⟨⟨USA⟩⟩` and `⟨⟨USSR⟩⟩` (membership and distance out). They are no longer measured on the joint kernel. Why: a coalition's kernel quantifies over the coalition's own strategies. A belief or a verification level that only opens or closes an option for a member cannot remove that member's ability to decline the option. So `⟨⟨USA, USSR⟩⟩` is insensitive by construction to its members' beliefs (docs/review_phase3_2026-10-18.md section 3; reports/cw_v0.md section 17). A belief or an oversight level can move a unilateral kernel when it opens an option to the side outside the coalition, and it can move reachability. Those are the measures the claims' intent ("more adversarial reachability", "distance to the boundary", "oversight and belief do [matter]") can be checked on.
    - C6 (b): of the four distances (the shortest traces to each adverse ending by 1963, and the distance out of {USA}'s and {USSR}'s kernels of avoiding both by 1963), at least one is shorter from the replay state and none is longer, in every year of the gap.
    - C8 (b): of three distances (the shortest trace to the adverse endings, and the distance out of `⟨⟨USA⟩⟩□balance_cw` and `⟨⟨USSR⟩⟩□balance_cw`), at least one is larger with the regime's `oversight` and none is smaller.
    - C10 (b): a perturbation counts when it changes unilateral-kernel membership or the shortest trace to the adverse endings. C10 (a) is unchanged.
  - **C2, amended 2026-10-23 on the owner's decision 2o:** the amended claim is asked with `balance_nobloc := no_war ∧ both_or_neither`, which is `balance_cw` without the clause on the blocs. The registered `balance_cw` is computed and printed beside it, not asserted. Why: no United States action touches `bloc_USSR`, so a clause requiring the opponent's bloc to stay intact empties the United States' unilateral kernel by construction (review section 2; the T13 lesson). The bloc-free predicate is the amended claim.
  - C5 is not amended. On the owner's decision 2l, `USSR.nuclear_use` gains the part `nato_attack` (a guard edit after first sight, docs/guard_changelog_cw.md 2026-10-23) and C5 is rerun with the whole suite. The hold-out of decisions D9 stands: C3 and C6 were computed once on the model of first sight, before that edit (reports/cw_v0_amendments_holdout.log). C7 and C13 are not amended, and their first-sight results stand. Results are in reports/cw_v0.md section 20.
