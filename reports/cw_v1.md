# Cold War v1: the first sight of V1 to V10

> Every result is conditional on the model version and the initial state; no bare reachability result is a finding. The deliverables are minimal assumption sets, kernel membership and distance, and pivotal coalitions; each is given with its engine.

Model `cw_v1` (`models/cw/v1.py`), fingerprint `6cbb54f105b1`; the builds `build(prc_principal=False)` `8eb285056b15` (V5 (b), V10's control), `build(us_crisis_options=False)` `9780a34b6304` (V2's control), `build(frozen_oversight=True)` `6b7059a046d4` (V7 (c)). Sub-games (`models/cw/crises/`): Berlin 1948 `c7b956d15290`, Cuba 1962 `2abcb5e9c735`, Sino-Soviet 1969 `ac9a1b01ddaa` (PRC-to-Nature build `6df79b14f313`), the October 1973 alert `6e4f5e7c5efe`, Able Archer 1983 `abcf2dea1928`. Coarse budget: variables 29, levels 86, actions 68, guards 68, guard parts 137, delays 8, invariants 9, endings 5; speculative 0, fairness 0, profiles 0, assume 0. Registered claims: [docs/coldwar_testbed.md](../docs/coldwar_testbed.md) section 9.3, with V6 as amended before first sight (decisions 7g, 7i; section 8). Readings: [docs/cw_v1_decisions.md](../docs/cw_v1_decisions.md) section R and the R notes of 2026-10-24 and 2026-10-27, all written before the run. Logs: [reports/cw_v1_first_sight/](cw_v1_first_sight/).

**Hold-out record.** The owner gave the go (decision 7k). V1 to V10 were then run once, from a clean worktree (0 dirty files) at commit `1663c43ac4b5f3c33ebd60a0f3c2130550104194`, on 2026-10-29 from 07:17:49 to 08:19:27 UTC (61 min 38 s), in two steps:

1. **The blind replay that is V6's input** (decision 7k, R V6), 07:17:49 to 07:21:57, exit 0: `wf replay --episode cw --years 1957..1962 --corpus data/cw/corpora/raw/crest --source crest --backend claude --measure-proposals`. Its proposals and metrics are in `cw_v1_first_sight/blind_replay/`.
2. **The ten claim files**, run with `WF_FIRST_SIGHT_CWV1=1` and `WF_CWV1_BLIND_REPLAY` set, one pytest process per file, two at a time, 07:21:57 to 08:19:27.

**Result: 2 passed (V1, V4), 8 failed.** Six failed on their assertions (V2, V3, V5, V6, V7, V8). Two stopped on an exception before their assertion: V9 (`BudgetExceeded`) and V10 (`ModelError`). Both are defects in the test or model code found at first sight (section 12). Neither changes a verdict that can be read now.

**Total hold-out** (decisions D8): V3, V5 and V6. Their first-sight computation is their result, and no row after the first-sight row may serve them. No guard, effect, delay, fairness constraint, profile, assumption, snapshot, test body or reading has changed since the run. Seen before first sight: the construction checks and sizes (decisions section S). Nothing else was seen.

| Claim | Result | Engine | Time | Key numbers | § |
|---|---|---|---|---|---|
| V1 realized trajectory | **pass** | explicit replay on the flattened game; control explicit, cut 1954 | 73 s | under `opportunist` every coarse and fine move available with zero relaxations (an existence check, not a finding), five crises played, `CHALLENGER_EXHAUSTION` at tick 45; `status_quo` stops at `USSR.approve_korea` (1950); control: no `esc_usprc = war` by 1954 with the Korean entry forbidden (1,078,351 and 482,887 states) | 1 |
| V2 joint, not unilateral | **fail** | layered 1967–71, composite 1972–83, symbolic 1984–91 | 1650 s | `K_J` every year 1967–91; outside both unilateral kernels only **1967–73**; `K_USA` from 1974, `K_USSR` from 1982; the control holds (without the American options `K_USSR` every year) | 2 |
| V3 the 1973 alert (hold-out) | **fail** on (b) | explicit sub-game (197 fine states); composite beside | 67 s | entry in `K_J` and in **`K_USA`** (bounded to 1974), out of `K_USSR`; unbounded: out of both; (a), (c), control hold | 3 |
| V4 Korea | **pass** | explicit, flattened, cut 1954; symbolic to 1962 beside | 6.6 s | (b) `⟨⟨USA⟩⟩□¬GENERAL_WAR_core` to 1954 and to 1962; (d) {USSR, PRC, Nature} cannot force it (380 states); v0's C5 route is closed | 4 |
| V5 the triangle (hold-out) | **fail** on (a), (b) | explicit sub-game (975) lifted to symbolic bounded kernels | 65 s | pivotal families: entry none, 1970 {USA}, 1971 and 1972 {}; PRC-to-Nature: {USA}, {USA}, {}, {}; control holds | 5 |
| V6 the missile gap (hold-out) | **fail** on (a), (b), control | blind replay against hindsight; layered (explicit form) to 1963 | 134 s | the replayed belief exceeds the count at the projected date in 1957–60, not in 1961 (`under_1000` against 235 on 1 Jan 1963); (b) nearer only in 1958 under `status_quo`; (c) holds; blind and manual series agree | 6 |
| V7 verification | **fail** on (b) | layered 1964, composite 1973, symbolic 1988 | 3100 s | every distance equal with and without the regime's oversight (1964: 8, 0, 0; 1973: 5, 0, 0; 1988: never); (c) holds (drawdown in 7 years; frozen: never) | 7 |
| V8 capability threshold | **fail** on (b) | layered 1947–83, symbolic 1984–91 | 436 s | (a) holds; `oversight` scores 0 in every year; `belief` scores in 1951–53 and 1982–83; `nuke` 0 before 1965 and 1 in 1974–75 | 8 |
| V9 negative controls | **fail** (stopped in (d) under `opportunist`) | bounded (Z3) for (a), (b); explicit, flattened, cut 1963 for (d) | 627 s | (a) `status_quo` 2, `opportunist` 1 ({`policy`}); (b) `status_quo` 2, `opportunist` **1** ({`no_us_nuclear`}); (d) `status_quo` holds (5,673,596 states); `opportunist` (d) over 6,000,000 states | 9 |
| V10 the Soviet bloc kernel | **fail** (stopped in (b) under `status_quo`) | composite to 1984, symbolic beyond | 95 s | departure **1980** (1981 outside; re-entered 1982; left 1987); fortune departure 1989; (b) raised `ModelError` in the Able Archer exit from a perturbed state | 10 |

## 1. V1: the realized trajectory (pass)

Under `opportunist` every realized coarse move and every realized fine move of the five sub-games is available at its tick from the 1947 hindsight snapshot, with zero relaxations. This is an existence check, quoted with its relaxation count, not a finding. The play ends at tick 45 in `CHALLENGER_EXHAUSTION`. The crisis part is 105 fine states. The PRC's realized decisions are `intervene_korea` (1951), `border_clash` (1969), `rapprochement` (1972) and `normalize` (1989). Under `status_quo` the play stops in 1950 at `USSR.approve_korea`, as in v0.

Control: with `PRC.intervene_korea` forbidden, no state with `esc_usprc = war` exists by 1 January 1954, under either hypothesis (explicit, 1,078,351 and 482,887 states). So the US–PRC war was the PRC's decision, not an effect of the Korean war.

## 2. V2: joint and unilateral kernels of `balance_core` (fail)

The kernels are of `balance_core := esc < conventional ∧ both_or_neither`, through the horizon. The two hypotheses give identical tables, row for row.

| Years | `K_J` | `K_USA` | `K_USSR` | Fortune {USA, Nature} / {USSR, Nature} | `balance_cw` (J, USA, USSR) | `balance_tri` | Coarse, sub-games inert |
|---|---|---|---|---|---|---|---|
| 1967–1973 | **in** | out | out | out / in | in, out, out | in, out, out | in, in, out |
| 1974–1980 | **in** | **in** | out | in / in | in, out, out | in, in, out | in, in, out |
| 1981 | **in** | **in** | out | in / in | out, out, out | in, in, out | in, in, out |
| 1982–1986 | **in** | **in** | **in** | in / in | in, out, in | in, in, in | in, in, in |
| 1987–1991 | **in** | **in** | **in** | in / in | out, out, out | in, in, in | in, in, in |

Engines: layered lifting 1967 to 1971; composite 1972 to 1983 (explicit part 1,485,415 states from 1972 under `status_quo`, 2,983,389 under `opportunist`, falling to 32 and 35 from 1983); symbolic from 1984.

**The registered claim fails.** H7's pattern (joint in, both unilateral out) holds in 1967 to 1973, 7 of the 25 years.

- **Breaking `K_USA`, 1967 to 1973.** The Soviet forcing strategy (with Nature, the PRC idle) idles to 1973 and enters the alert sub-game, "forced through it". The test prints no more of the play. The sub-game shows the route:
  - the alert's exit returns `esc = crisis` unless the USSR accepts the UN force (`accept_un_force`) (`models/cw/crises/alert_1973.py`, `exit_map`);
  - at `esc = crisis`, `USSR.escalate` raises `esc` to conventional.

  The USSR can therefore carry a standing crisis into 1974 and open combat. It can do so even with Nature on the American side: the fortune {USA, Nature} column is out. With the sub-games inert, `K_USA` holds from 1967 (last column). So the 1967 to 1973 result is owed to the 1973 sub-game.
- **Breaking `K_USSR`, 1967 to 1981.** The American forcing strategy (with Nature) idles to 1981, plays `USA.blockade_cuba` (Haig's rejected proposal of 1981), and Nature's `accident` follows in 1982. The fortune {USSR, Nature} column is in every year. So the United States can break the balance only by a threat that leaves something to chance (Schelling), not by a war-forcing move of its own.
- **From 1974, `K_USA`.** After the alert no Soviet option opens a standing crisis against American restraint.
- **From 1982, `K_USSR`.**
  - The last American crisis-initiating option is the 1981 blockade.
  - The source search for 1984 to 1991 found none (docs/cw_v1_us_options_1984_1991.md).
  - In 1982 and 1983 Able Archer needs Soviet preemption, which the USSR can decline.

  So the United States has no way out of `balance_core` of its own from 1982, not only from 1984. That is the comment in `models/cw/v1.py`, which v1 confirms two years earlier.
- **Control (holds).** On `build(us_crisis_options=False)`, `K_USSR` holds in every year 1967 to 1991. Every American breaking route in the main result runs through the added options.

## 3. V3: the October 1973 alert (fail on (b); total hold-out)

Engine: the sub-game explored explicitly from the 1973 hindsight entry (197 fine states), with the kernels lifted to the bounded predicate `no_war_core` at the 1974 return. Beside: the unbounded column (composite, 403,770 and 809,926 states). The two hypotheses give the same results.

- **(a) holds.** The realized play (4 days, the alert, no Soviet intervention, `CEASEFIRE`) is available with zero relaxations. Quoted with its count, not as a finding.
- **(b) fails.** The entry is in `K_J`, in **`K_USA`** and out of `K_USSR`. The claim needed both unilateral kernels out. In the sub-game only the American alert opens fighting: through `USA.engage` once Soviet forces have landed, and through Nature's `naval_incident` under DEFCON 3. The Soviet landing needs a violated ceasefire and no UN force, and it brings no combat by itself. So the United States alone keeps the peace to 1974 by not alerting, and the USSR's readiness moves leave nothing to chance that the United States cannot remove.
  - Fortune, bounded: {USA, Nature} and {USSR, Nature} are both in.
  - Unbounded (through the horizon): `K_J` in, `K_USA` out, `K_USSR` out. The USSR can return a standing crisis (section 2).
  - The cut at 1974 therefore decides the American kernel (H8).
- **(c) holds.**
  - The shortest play from the entry into the realized return is 1 transition, and no shortest play contains `USA.defcon3`.
  - To a return with `esc ≥ conventional`: 1 transition after the alert, 2 after the reply alone. The alert brought the play nearer war, not farther.
- **Control holds.** With every declared action of USA and USSR forbidden, `fighting` is unreachable.

## 4. V4: Korea (pass)

Under `opportunist` (the registered hypothesis), on the flattened game from 1950 cut at 1954 (129,549 states):

- **(a)** A limited war (`korea = armistice`, `esc < conventional`) is reachable with zero relaxations in 2 transitions. This is an existence check.
- **(b)** The 1950 state is in `⟨⟨USA⟩⟩□¬GENERAL_WAR_core` through 1954. It is also in it at the cut plus eight ticks, 1962 (symbolic; H8).
- **(c)** The American nuclear option in Korea is `nuclear_korea` alone. It is offered in 1,743 states, and in each of them only with total commitment and a non-opportunist reading of Soviet aims.
- **(d)** With the United States idle (380 states), {USSR, PRC, Nature} cannot force `GENERAL_WAR_core`.
- **Control:** the 1950 state is outside `⟨⟨USA⟩⟩□(korea = peace)` to 1951.

Under `status_quo` no Korean war is reachable, so (a) and the control fail, as the claim expects ("the war needs Stalin's approval").

**Against v0.** C5 failed on (b) twice: first through Soviet nuclear use in a Berlin crisis, then, after the guard edit of decision 2l, through the ICBM decision of 1950 and escalations added across crises (reports/cw_v0.md section 20). Decision 5a's content closes both routes:
- `USSR.icbm_buildup:technology` is available only from 1962;
- the escalations raise `esc` to conventional instead of adding.

## 5. V5: the triangle (fail; total hold-out)

`balance_tri` bounded to 1 January 1973. The pivotal family is the set of inclusion-minimal coalitions of {USA, PRC} whose kernel contains the state; "none" means not even {USA, PRC}. The two hypotheses give the same results.

| State | (a) cw_v1 | Fortune | Unbounded | (b) PRC-to-Nature, `balance_core` | (b) unbounded |
|---|---|---|---|---|---|
| Entry of the 1969 sub-game | none | none | none | {USA} | none |
| 1970 | {USA} | {USA} | none | {USA} | none |
| 1971 | {} | {} | none | {} | none |
| 1972 | {} | {} | none | {} | none |

- **(a) fails** in every row; the registration expected {{USA, PRC}}. At the entry no coalition without the USSR keeps `balance_tri`: inside the sub-game the Soviet strike is open, and neither Beijing's acceptance of talks nor an American signal closes it in time. That is v0's C11 finding, now with the sub-game active.
- **From 1970** the talks flag (`sino_soviet_talks`, decision 7f(a)) closes `strike_china`. In 1971 and 1972 the empty coalition keeps the predicate. This is the degeneracy the owner accepted as a risk before first sight (decisions section O).
- **{USA} in 1970.** The only option on the record that can raise `esc` in 1970 is the American one, `confront_cienfuegos`. So the coalition that must abstain is the United States itself. This is read from the guards, not printed by the test.
- **(b) fails.** It holds at the entry and in 1970, and fails on 1971 and 1972 for the same reason.
- **Control holds:** the 1968 state is in `safe({PRC}, esc_sino < war)` to 1970.
- **Unbounded,** no coalition keeps either predicate in any row (H8).

## 6. V6: the missile gap, on the blind replay (fail; total hold-out)

### 6.1 The input: blind replay and hand-coded series

The blind replay read the CREST corpus by document date: 1, 4, 4, 1, 6 and 6 documents for 1957 to 1962. It proposed 14 levels of `belief_force_USA` and 3 of `belief_USA_USSR`, and none of `belief_USSR_USA`. Five proposals were discarded by the extractor's checks ("the quote is not in the document"). No proposal was reviewed: at proposal level every proposal is treated as accepted (`metrics.md`). The blind level agrees with the contemporaneous (hand-coded) belief in 6 of 6 years and with the hindsight truth in 0 of 6.

In the table, "→ count" is the hindsight `count_USSR` on the 1 January read. The blind dates follow the rule: the latest estimate's date plus 30 months. The hand-coded series is given on its recorded `projected_for` (data/cw/v1/events.csv) and, beside it, on the same rule.

| 1 Jan | Blind: level, latest estimate (date) | Rule date → count | Hand-coded: level, estimate (date), projection | Recorded date → count | Hand-coded on the rule → count |
|---|---|---|---|---|---|
| 1957 | under_1000, NIE 11-56 (1956-03-06) | 1958-09 → 1958: 28, under_200 | under_1000, NIE 11-56 (1956-03-06), 520 for mid-1958 | 1958-07-01 → 1958: 28 | 1958: 28 |
| 1958 | under_1000, NIE 11-4-57 (1957-11-12); SNIE 11-10-57's proposal discarded | 1960-05 → 1960: 108, under_200 | under_1000, SNIE 11-10-57 (1957-12-10), 580 for mid-1960 | 1960-07-01 → 1960: 108 | 1960: 108 |
| 1959 | under_1000, NIE 11-4-58 (1958-12-23); an earlier `under_200` from SNIE 11-7-58 (bombers only) superseded | 1961-06 → 1961: 138, under_200 | under_1000, NIE 11-4-58 (1958-12-23), 430 for mid-1961 | 1961-07-01 → 1961: 138 | 1961: 138 |
| 1960 | under_1000, carried (one document read, no proposal) | 1961-06 → 1961: 138, under_200 | under_1000, NIE 11-4-58 carried (NIE 11-5-59 projects nothing), 430 | 1961-07-01 → 1961: 138 | 1961: 138 |
| 1961 | under_1000, NIE 11-8-60 (1960-08-01), program A | 1963-02 → 1963: **235, under_1000** | under_1000, NIE 11-8-60 (1960-08-01), 700 for mid-1963 | 1963-07-01 → 1963: **235** | 1963: 235 |
| 1962 | under_1000, NIE 11-8-61 (1961-06-07); NIE 11-8/1-61 read, no proposal | 1963-12 → 1963: 235, under_1000 | under_1000, NIE 11-8/1-61 (1961-09-21), 300 for mid-1963 | 1963-07-01 → 1963: 235 | 1964: 302 |

### 6.2 The result

The two series give the same verdicts on every reading (the log prints blind/rule, manual/rule and manual/recorded).

- **(a) fails in 1961.**
  - In 1957 to 1960 the projection is `under_1000` against `under_200` on the projected date: it exceeds.
  - In 1961, NIE 11-8-60's projection (about 700 on the hand-coded row, 540 to 700 in the blind proposal's reasoning) faces 235 vehicles at the end of 1962. Both are in the band 200 to 999, so the projection does not exceed, although it was three times the force.
  - The bands of decision 7g (edges 200 and 1,000) cannot express that error once decision 7i moves the comparison to 1963, when the count has crossed 200. The model's own source note on `estimate_revised` says the same of the 1961 revision ("moved the projection within its band").
- **(b) fails.** The table gives the fewest transitions to `GENERAL_WAR` and `ACCIDENTAL_WAR` and the distances out of `K_USA` and `K_USSR` of `no_general_war`, kept to 1963.

  | Year | Replay | Hindsight, `status_quo` | Hindsight, `opportunist` |
  |---|---|---|---|
  | 1958 | 2, 2, 0, 1 | **3**, 2, 0, 1 | 2, 2, 0, 1 |
  | 1959 to 1961 | 2, 1, 0, 0 | 2, 1, 0, 0 | 2, 1, 0, 0 |

  Only in 1958 under `status_quo` is the replay state nearer an adverse ending. In that cell the replay state also carries the record's `belief_USA_USSR = opportunist` against the hypothesis's own `status_quo`. The nearer `GENERAL_WAR` may come from that belief and not from the force estimate; that reading is not computed. The replay and hindsight states reach 24,681 and 19,681 states in 1958 (42,578 under `opportunist`). As in v0, the belief opens more states without shortening a way to war.
- **(c) holds, but not by the mechanism it names.** Overhead coverage is in the replay from 1961 and the gap "closes" in 1961. The closing is the band effect of (a). Nature's `estimate_revised` sets the belief to the band above the count, which is `under_1000` again.
- **The control fails** for the same reason. With overhead coverage held at `partial` from 1960, the belief of 1 January 1962 is `under_1000`. The 1963 count is in the same band, so it does not exceed.

## 7. V7: verification (fail on (b))

Hindsight state s of Y + 1 and s⁻ with the oversight of Y. Each cell gives the distance to the adverse endings, then out of `K_USA` and out of `K_USSR` of `balance_core`, with the regime's oversight / with the oversight before it. The two hypotheses give the same results.

| Regime | (a) | Distances | Fortune, out of {USA, Nature} and {USSR, Nature} |
|---|---|---|---|
| 1963, none → test_ban (layered) | ✓ | 8, 0, 0 / 8, 0, 0 | 0, 0 / 0, 0 |
| 1972, test_ban → ntm (composite, 699,338 and 1,403,138 states) | ✓ | 5, 0, 0 / 5, 0, 0 | 0, 2 / 0, 2 |
| 1987, ntm → on_site (symbolic) | ✓ | never, never, never / same | never, never / same |

(b) fails: no distance moves.
- (c) holds: from 1962, `arms = reduced` is reachable in 7 years on the model, quoted as a zero-relaxation existence check, and unreachable on the frozen-oversight build.
- 0 out of `K_USA` in 1973 is V2's non-membership in that year.
- "never" in 1988: the state is inside both unilateral kernels and no adverse ending is reachable.

Oversight gates treaties; it does not shorten or lengthen a way to war. This is v0's C8 result, unchanged by v1's content.

## 8. V8: capability past a threshold (fail on (b))

Family scores per year: the best one-level perturbation that changes `K_USA` or `K_USSR` membership of `balance_core` or the fewest transitions to the adverse endings. The two hypotheses give the same results except where marked.

| Years | nuke | belief | oversight | Note |
|---|---|---|---|---|
| 1947–1950, 1954–1964 | 0 | 0 | 0 | fortune: nuke 1 in most years |
| 1951–1953 | 0 | 1 (`status_quo`), 2 (`opportunist`) | 0 | `belief_USA_USSR` (the reading part of `nuclear_korea`) |
| 1965–1973, 1976–1981 | 0 | 0 | 0 | |
| 1974–1975 | 1 (`nuke_USSR`) | 0 | 0 | |
| 1982–1983 | 0 | 1 (`belief_USSR_USA`) | 0 | the war scare: Able Archer's entry copies this belief |
| 1984–1991 | 0 | 0 | 0 | |

- **(a) holds:** from 1965, raising a force at or above survivable flips no membership in `K_J`.
- **(b) fails both ways.**
  - From 1966, `nuke` is not below `oversight` in any year: oversight never scores.
  - The control, `nuke` above both before 1965, fails in every year: `nuke` scores 0 there and `belief` scores in 1951 to 1953.
- **What is new against v0's C10:** beliefs now move something. They score in 1951 to 1953 and 1982 to 1983, where in v0 they scored 0 in every year. The test does not print which measure moved, a unilateral kernel or the shortest trace.

## 9. V9: negative controls (fail; stopped in (d) under `opportunist`)

| Part | `status_quo` | `opportunist` | v0's C12 |
|---|---|---|---|
| (a) `us_strike` by 1955, minimum (bounded) | **2**: {`policy`, `Nature.new_look:level`}, {`threat`, `policy`}, {`policy`, `Nature.nsc68:level`} | **1**: {`USA.preventive_strike:policy`} | 2 and 1, the same sets |
| (b) `invasion_west` by 1990, minimum (bounded) | 2: {`USSR.invade_west:hypothesis`, `no_us_nuclear`} | **1**: {`USSR.invade_west:no_us_nuclear`} | 3 and 2 |
| (c) merger of the blocs | vacuous | vacuous | vacuous |
| (d) `ACCIDENTAL_WAR` | shortest 1 from 1959, zero relaxations (5,673,596 states); no coalition forces it; reachable from the Cuba sub-game, forced by none | **not computed**: `BudgetExceeded` in `graph(fm, s59, cut=16, max_states=6_000_000)` | 1, forced by none |

V9 holds iff (a), (b) and (d) under one hypothesis. Under `status_quo` (a) fails. Under `opportunist` (b) fails. **So V9 fails whatever (d) gives;** the defect (section 12.1) decides no verdict.

- **(b) under `opportunist`, model content.** In v0 every minimal set lifted `no_us_nuclear` and one more part. The other part was `response` (`esc ≥ crisis`), which nothing could satisfy after 1980 in v0. In v1, `USA.blockade_cuba` (1981) opens a standing crisis and satisfies `response`. The guard's part reads "a crisis", while its source says "a war begun by NATO". So the single remaining set lifts the American deterrent, the constraint the record never lifts. As a content control (H6) the result is the expected one. As a count it has fallen to 1 because the new American option meets a proxy part.
- **(a) under `status_quo`** needs the hypothesis's own belief relaxed in, as in v0.

## 10. V10: the USSR's own kernel of its bloc (fail; stopped in (b) under `status_quo`)

Computed before the error, under `status_quo`, by the composite engine:

| | 1975 to 1980 | 1981 | 1982 to 1986 | 1987 to 1990 |
|---|---|---|---|---|
| `safe({USSR}, bloc_intact)` | in | out | in | out |
| Fortune, `safe({USSR, Nature}, bloc_intact)` | in | in | in | in (out in 1990) |

- **Departure 1980.** It is inside the window (a) and within one year of v0's 1980 (c). The fortune departure is 1989.
- **(b) raised a `ModelError`.** It perturbs the 1981 state one level per variable and explores the composite graph from all the perturbed states together. The cause is in section 12.2.
- **Not computed:** the driving variable, the control (the PRC-to-Nature build) and all of `opportunist`.

The kernel table is v0's C13 table year for year. The verdict cannot be read until (b) and the control are computed.

## 11. Against v0, claim by claim

| v1 | v0 | v0 result | v1 result | What moved |
|---|---|---|---|---|
| V1 | C1 | pass | pass | five sub-games and the PRC added; same ending |
| V2 | C2 (amended) | fail: both unilateral kernels from 1973 (bloc-free) | fail: joint only 1967–73 | the 1973 sub-game puts `K_USA` out to 1973; the American options put `K_USSR` out to 1981 |
| V3 | (new) | — | fail on (b) | — |
| V4 | C5 | fail on (b), twice | **pass** | decision 5a's content closes both routes |
| V5 | C11 | fail | fail | at the entry, still no coalition without the USSR; 1971–72 now degenerate by the talks flag |
| V6 | C6 (amended) | fail on (b) | fail on (a), (b), control | the count scale: (a) now fails in 1961; (b) as before |
| V7 | C8 (amended) | fail on (b) | fail on (b) | nothing |
| V8 | C10 (amended) | fail on (b), every score 0 | fail on (b) | belief scores in 1951–53 and 1982–83; oversight still 0 |
| V9 | C12 | pass | fail | (b): the 1981 option satisfies `response`; (d) under `opportunist` not computed |
| V10 | C13 | pass (1980, `afghan`) | fail (error); departure 1980 | (b) not computed |

## 12. Defects found at first sight

### 12.1 V9 (d): the explicit budget under `opportunist`

- **Where.** `tests/coldwar_v1/scenarios/test_V09.py` line 92 builds the flattened game from the 1959 hindsight state, cut at tick 16, with `max_states=6_000_000`. Under `opportunist` it raised `BudgetExceeded`, after (a), (b) and (c) of that hypothesis had been computed and printed. Under `status_quo` the same graph has 5,673,596 states.
- **Cause.** The budget was set from decisions section S's row "1959 to 1963: 4,283,960 (opportunist)". That row is unmarked: it was not remeasured after the count edit of 2026-10-28 (D9). That edit added `USSR.first_icbms` with its delay (a pending counter in 1959), `count_USSR` and three new events, and it enlarged the window. The section's rule remeasured only the rows marked ✓. This cause is inferred: the size after D9 was not measured.
- **Corrected computation.** Either:
  - measure the graph and raise `max_states` for this one graph; or
  - compute (d)'s distance and the coalition attractors by the layered lifting with the cut at 16, as V6 does for the same window (V6's hindsight measure from 1959 under `opportunist` gives `ACCIDENTAL_WAR` at 1 transition). The attractor would need `Lift.attractor`, a form D7 has not validated against the explicit engine.
- **Hold-out and verdict.** V9 is not under the total hold-out, so a logged test-code correction may be rerun. The corrected (d) cannot change the verdict, because V9 already fails on (b) under `opportunist` and on (a) under `status_quo`.

### 12.2 V10 (b): an exit map lowers a monotone flag from a perturbed state

- **Where.** In `drivers(status_quo, 1980)` on the **main build** (`prc_principal=True`), not in the control or in the fortune column. `inside(aims, 1981, perturbed)` builds one composite graph from all one-level perturbations of the 1981 hindsight state.
- **The trigger.** One perturbation is `accidental -> True`, which gives a state with `accidental = True` and `esc = peace`.
  - The model never reaches such a state. `accidental` is set only with an `esc` rise to a nuclear rung: by Nature's `accident` (`Bump("esc", 3)` from `esc ≥ crisis`) or by a nuclear exit of the Cuba or Able Archer sub-game. Every such state is a `GENERAL_WAR`/`ACCIDENTAL_WAR` ending.
  - From the perturbed state the play continues. In 1983 it enters Able Archer: the traceback's state is tick 36, with `belief_USSR_USA = first_strike_intent`.
  - The play reaches a deliberate strike. `able_archer_1983.exit_map` then returns `{"esc": "strategic", "accidental": day["accident"] == "True"}`, which is `accidental: False`.
  - `FlatModel._return` (wavefront/engine/multires.py line 338) refuses to lower a monotone variable and raises the error. The framework did its job.
- **Root cause.** The exit map writes `accidental` unconditionally where it means "set it when the accident was the cause". Cuba's exit map has the same pattern (`models/cw/crises/cuba_1962.py` line 213). The change log of the model step records a near miss of the same kind (2026-10-24, `USA.accept_assurance`). R notes 8 foresaw `ModelError` from perturbed states for V8 and removed the risk there by lookup; V10 explores from perturbed states.
- **Minimal fix (not applied).** In both exit maps, write the flag only when true:

  ```python
  out = {"esc": "strategic"}          # Cuba: "tactical_nuclear"
  if day["accident"] == "True":
      out["accidental"] = True
  return out
  ```

  On every reachable state `accidental` is False at entry, so the change leaves every reachable transition, every count and every first-sight number unchanged. Exit maps are not part of a sub-game's fingerprint. The alternative is in the test: drop perturbed states that no play reaches (`accidental` true on a non-terminal state) from `drivers`. That fix changes the set of perturbations the claim reads, so it is a reading change, which the exit-map fix is not.
- **Hold-out and verdict.** V10 is not under the total hold-out (D8: V3, V5, V6), so after a logged correction it may be rerun. The rerun could change the verdict: (a) and (c) hold on the computed table, and (b) and the control are open. Other perturbations might raise further errors once this one is fixed; that was not checked, since checking it would mean running the claim.

## 13. What the failures are

| Cause | Claims |
|---|---|
| (a) Model content | V2: no Soviet breaking option after the 1973 alert, no American one after 1981 (the source search of D2). V3 (b): only the American alert opens combat in the alert sub-game. V5 (a) at the entry: the Soviet strike in the 1969 sub-game. V6 (a), (c), control: the bands of decision 7g cannot express a threefold overestimate once the count has passed 200. V6 (b), V7 (b), V8 (b): oversight acts on treaties, beliefs on options. V9 (b): the 1981 option satisfies the proxy part `response` of `invade_west` |
| (b) Claim reading | V5 (a), (b) in 1971–72: degenerate by the talks flag (decision 7f(a), the accepted risk). V8 (b): a ranking with ties and zeros, as v0's C10. V3 (b) and V5: bounded to a cut that decides the unilateral result (unbounded columns differ; H8). V6 (a): the comparison date of decision 7i moves 1961 into the band of the 1963 count |
| (c) Defect in test or model code, found at first sight | V9 (d) under `opportunist`: a budget set from an unremeasured size (decides no verdict). V10 (b): an exit map not monotone-safe, met by a test that starts from unreachable perturbed states (verdict open) |

No failure is a framework defect: `wavefront/` was not touched, and the `ModelError` is the engine's guard working as specified. Framework changes: 0 of the budget.

## 14. The transfer hypotheses

| Id | v0 | v1 | Claims and numbers |
|---|---|---|---|
| H1 belief lag; point of no return in the lag | not supported | **partly; changed** | The beliefs now move a unilateral kernel or the shortest trace in two windows: `belief_USSR_USA` in 1982–83 (the war scare) and `belief_USA_USSR` in 1951–53 (V8). The dated belief error of the missile gap still does not move the boundary (V6 (b): nearer only in 1958 under `status_quo`, possibly through the aims belief). The lag itself was not re-measured |
| H2 concessions only under limited aims | failed on C8 | **not supported** | V7 (b): oversight moves no distance; (c): the drawdown needs oversight |
| H3 preventive defection on a clock | held where tested | **held where tested** | V9 (a): exactly the documented rejection under `opportunist`; V8 (a): past survivable, more force flips no joint membership |
| H4 obligations load-bearing for levers | failed | **held on Korea, failed on the triangle** | V4 (b), (c): the United States alone keeps general war away to 1954 and to 1962, with the nuclear option only after total commitment and a non-opportunist reading; V5: no coalition holds the triangle at the entry |
| H5 pending decisions are state | tested | **not re-tested** | Every v1 kernel was asked from snapshots that carry their pending counters (V3's 1974 state: `pending_USSR_mirv = 2`); no run without them |
| H6 controls as content controls | held | **held as content, count moved** | V9 (b): the one minimal set lifts the American deterrent (`no_us_nuclear`); the count fell from 2 to 1 because the new option meets a packaged part: H6's point that counts depend on packaging |
| H7 a held balance is joint, not unilateral | failed (USSR-unilateral; both from 1973 on the bloc-free predicate) | **held 1967–73 only** | V2: joint and neither unilateral 1967–73; US-unilateral 1974–81; both unilateral 1982–91; the control shows the American side owes its breaking to the added options. With v0's `balance_cw`, v1 is joint-only 1967–80 |
| H8 the horizon can decide a forcing question | not tested | **held where tested** | V3: `K_USA` in bounded to 1974, out through the horizon; V5: bounded families against "none" unbounded in every row; V4 (b) holds at the cut and at the cut plus eight |

**H7 in detail.**
- **Is the balance joint now?** Yes in 1967 to 1973, and for a definite reason: each side has a way out against the other's restraint. The USSR's way out runs through the 1973 alert sub-game: a standing crisis kept by refusing the UN force, then escalation. It works even against the United States joined by Nature. The American way out runs through the added options and needs Nature's accident. The printed strategy uses the 1981 blockade, and the control without the options closes it.
- **From 1974** the balance is the United States' to hold alone: no Soviet option opens a crisis against American restraint.
- **From 1982** each side can hold it alone. The United States has no option of its own after the 1981 blockade (the 1984–91 search found none, and Able Archer needs Soviet preemption).
- **Against v0.** v1 reverses v0's direction. v0's balance was the USSR's own (registered predicate), or both sides' from 1973 (bloc-free). In v1 the Soviet side loses its unilateral hold until 1982 and the American side gains it from 1974.
- **The verdict.** H7 as stated ("every year") fails. Its pattern exists, in a window bounded by dated options on each side.
- **What this means for the AGI model.** The coexistence question (section 17 of v0's report) needs the human side's breaking options catalogued with their dates: the joint-only window ends when the last such option lapses.

## 15. Gate

Not passed as written: V1 and V4 pass; V2, V3, V5 to V8 fail on content or reading; V9 fails on content whatever its open part gives; V10 is open behind a code defect. The total hold-out now applies to V3, V5 and V6. No edit followed the run.

## 16. Proposals for the owner (proposals only)

None of these is made; each needs the owner's decision and, where it edits a guard, effect or test, a logged row after the first-sight row that does not serve V3, V5 or V6.

1. **V10 (defect).** Make the Able Archer and Cuba exit maps write `accidental` only when true (section 12.2). This is a model-code change that leaves every reachable transition unchanged. Log it, rerun V10 and record its result beside the first-sight error. Add a construction check that no exit map lowers a monotone coarse variable from any coarse state at its tick.
2. **V9 (defect).** Remeasure decisions section S's unmarked rows after D9. Then rerun V9 (d) under `opportunist` with a measured budget or by the layered lifting, logged. The verdict stays a fail.
3. **V9 (b).** Decide whether `USSR.invade_west:response` should read the plans' condition through `us_began_war`, as `USSR.nuclear_use:nato_attack` does (decision 2l; Mastny and Byrne 2005). That is a guard edit after first sight, logged with a rerun. The alternative is to accept the count of 1 as H6's packaging effect.
4. **V6 (hold-out; a new row V6a if anything).** The band scale cannot carry the 1961 error, 700 projected against 235 in being. A V6a could compare the projected number with the count as a ratio, or count ICBM launchers alone, the gap the estimates argued about. It would be a new registration, with V6's first-sight result standing.
5. **V2 and H7.** Record H7 in docs/transfer_hypotheses.md as "held 1967–73 on cw_v1, failed as stated", with V2's table. Consider a V2a that asks for the joint-only window and its ends (1973, 1981) as the registered quantity, not "every year".
6. **V5 (hold-out).** Re-ask the triangle at the 1969 sub-game's entry only, where it is not degenerate. The coarse years 1971 and 1972 are empty by the talks flag.
7. **V3 (hold-out).** Note for any later alert model: the registered expectation needs a Soviet readiness move that opens a Nature event without the American alert. v1 has none, and the record of 25 October (the Politburo's decision against both the landing and an answer to the alert) does not supply one.
8. **V7 and V8.** As v0's proposal 5, they measure what oversight cannot move. If they are re-asked, ask where v1 shows effects: the drawdown's reachability (V7 (c)) and the two belief windows (V8).
