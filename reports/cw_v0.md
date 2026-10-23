# Cold War v0: the model step and the first sight of C1 to C13

> Every result is conditional on the model version and the initial state; no bare reachability result is a finding. The deliverables are minimal assumption sets, kernel membership and distance, and pivotal coalitions; each is given with its engine.

Model `cw_v0` (`models/cw/v0.py`), fingerprint `430d7ac3cdbb`; the C11 build `build(prc_principal=False)`, `29bf5b8cf12d`; the C8 analysis build `build(frozen_oversight=True)`, `d68077ee7e9e`. Sub-games (`models/cw/crises/`): Berlin 1948 `c7b956d15290`, Cuba 1962 `2abcb5e9c735`, Able Archer 1983 `abcf2dea1928`. Registered claims: [docs/coldwar_testbed.md](../docs/coldwar_testbed.md) section 5, unedited. Content: [docs/ontology_cw.md](../docs/ontology_cw.md), [docs/actions_cw.md](../docs/actions_cw.md), `data/cw/`. Readings: [docs/cw_v0_decisions.md](../docs/cw_v0_decisions.md) section R, written before the run. Log: `reports/cw_v0_first_sight.log`.

**Hold-out record.** C1 to C13 were run once, in one go (`python -m pytest tests/coldwar/scenarios -q -s -p no:cacheprovider`), on 2026-10-17 from 20:52:46 to 21:27:37 UTC, at commit `6b87af9d5790094c4f2af12bae31a813b03bcc6f` with a clean working tree. Result: **3 passed (C1, C12, C13), 10 failed, 34 min 50 s.** No guard, effect, delay, fairness constraint, profile or assumption has changed since; docs/guard_changelog_cw.md has one row after the first-sight marker, a correction of the replay-snapshot builder (section 9), with C7 recomputed beside its first-sight result, which stands. Seen before first sight: the construction checks (replays, events, snapshot convention, well-formedness), the state counts, and the early sight disclosed in decisions D9 (the model's own path in the kernels of `balance_cw`, a draft, close to C2).

| Claim | Result | Engine | Time | Key numbers | § |
|---|---|---|---|---|---|
| C1 realized trajectory reachable | **pass** | explicit replay, flattened game | 0.1 s | under `opportunist` every coarse and crisis move available, `CHALLENGER_EXHAUSTION` at 1992; under `status_quo` it stops at Stalin's approval of the attack in Korea (1950) | 2 |
| C2 joint kernel, unilateral non-membership | **fail** | symbolic | 377 s | joint kernel 1967 to 1980 and 1982 to 1986; but the USSR's own kernel equals the joint one in every year; the United States' is empty every year | 3 |
| C3 Cuba | **fail** | explicit sub-game, symbolic coarse kernels | 2 s | degenerate as registered (`balance_cw` false in 1962); variant `no_war`: joint kernel left 25 to 28 Oct under DEFCON 2; the way back is pledge and withdrawal, not the Jupiter trade; the United States can force war, the USSR cannot | 4 |
| C4 Berlin 1948 | **fail** on (c) | explicit, flattened, cut at 1950 | 5 s | airlift available; `SETTLED` reachable; `GENERAL_WAR` by 1950 blocked for both sides, not contested | 5 |
| C5 Korea | **fail** on (b) | explicit, cut at 1954 | 237 s | limited war reachable; the United States alone cannot keep `GENERAL_WAR` away to 1954: the USSR can force it through a Berlin ultimatum, escalation and nuclear use | 6 |
| C6 the missile gap | **fail** on (b) | replay against hindsight; explicit, cut at 1963 | 250 s | the replayed estimate exceeds the force 1958 to 1961; the gap closes in 1962, a year after overhead coverage (1961), with no force change; but adverse endings are equally near from both states | 7 |
| C7 the war scare | **fail** on (b) (and on (a) at first sight, a builder defect) | explicit, flattened, from 1983 | 7 s | `GENERAL_WAR` reachable in 4 transitions from the replay state, not at all from the hindsight state; distance out of the joint kernel 1 from both | 8 |
| C8 verification | **fail** on (b) | symbolic | 2 s | each regime raises `oversight`; distances unchanged (1973: 2 and 2) or the states outside the joint kernel (1964, 1988); frozen oversight: the drawdown is unreachable (reachable in 7 years on the model) | 9 |
| C9 exhaustion | **fail** on (c) | explicit from 1985 | 13 s | reachable in 5 years; necessary actions are Soviet and Nature's (perestroika, decline, collapse, delegitimation, opposition, revolution, dissolution), no US action; with the United States idle it stays reachable; but the USSR alone can keep it away, so it is blocked for the United States, not contested | 10 |
| C10 capability past a threshold | **fail** on (b) | symbolic | 0.1 s | raising a survivable force never flips joint-kernel membership (a holds); beliefs and oversight never flip it in any year, so the ranking ties at 0 | 11 |
| C11 the triangle | **fail** | symbolic | 15 s | no coalition without the USSR keeps `balance_cw` in 1969 to 1972 on either build; with Nature: {} on the scripted build, {PRC} in 1969 on the model, none after | 12 |
| C12 negative controls | **pass** | bounded, explicit, symbolic | 1175 s | under `opportunist`: preventive strike exactly 1 (`policy`); invasion of the West 2, every minimal set lifts `no_us_nuclear`; merger vacuous; accidental war reachable, forced by no coalition | 13 |
| C13 the Soviet kernel of its bloc | **pass** | symbolic | 5 s | departure 1980 (the state of 1981 is outside); driving variable `afghan` | 14 |

## 1. The model

Three principals and Nature over 45 yearly decision ticks, from 1 January 1947 (tick 0) to 1 January 1992 (the horizon), with three crisis sub-games entered by coarse actions that have no effect of their own: Berlin 1948 by week, Cuba 1962 and Able Archer 1983 by day (spec section 14). One swept objective, `aims_USSR ∈ {status_quo, opportunist}`, enters three guards as [H] parts (`USSR.approve_korea`, `enter_korea`, `invade_west`). The PRC is a principal from 1969 (scope part `principal`); before 1969 it has no decision the model represents. Escalation composes by `Bump` (decisions D4). Beliefs are state, changed by Nature's assessments and by detection of Soviet deployments; the hindsight snapshots carry each belief's hindsight truth, the replay snapshots the contemporaneous beliefs (D6, D7). No fairness constraint, no profile, no `assume`, no speculative action.

| Item | Coarse game | Berlin | Cuba | Able Archer |
|---|---|---|---|---|
| Declared variables / levels | 25 / 76 | 6 / 17 | 8 / 22 | 7 / 16 |
| Actions with Nature's | 58 (USA 16, USSR 22, PRC 3, Nature 17) | 15 | 13 | 8 |
| Guards / guard parts | 58 / 110 | 15 / 22 | 13 / 22 | 8 / 15 |
| Hypothesis gates | 3 | 0 | 0 | 0 |
| Delays | 7 | 1 | 0 | 0 |
| Fairness / profiles / assume / speculative | 0 / 0 / 0 / 0 | 0 | 0 | 0 |

Size: from 1947 under `opportunist` the coarse game reaches 23,685,764,622 states (symbolic, 239 s); from 1975, about 26,000 (explicit); the flattened game from 1983, about 4,100 to 42,000 depending on the start. Kernels over the whole coarse domain take 1 to 4 seconds each with the compiled BDD core.

**Engines and devices** (decisions D5, all in tests/coldwar/common.py, none a framework change): symbolic kernels on the coarse game, in which the three crisis actions are inert; lifting of a sub-game against coarse kernels at its exits (exact after 1962 for every coalition containing USA or USSR); a bounded cut-off that makes coarse states at a stated tick terminal (C4, C5, C6, C12 d); restricted games that forbid actions (C9).

**Data.** The data hosts the testbed names are blocked from the development environment by its network policy (data/cw/README.md). No level is read from a downloaded series; thresholds are stated on dated deployments, treaties and events, and "not verified" marks the levels a series would cross-check (the year of a secure Soviet second strike, the dating of the Soviet slowdown). The replay of C6 and C7 is manual (D7), not the blind pipeline.

## 2. C1: the realized trajectory (pass)

Under `opportunist` all 45 coarse moves and the 69 fine moves of the three crises are available at their ticks from the 1947 hindsight snapshot, and the play ends at the horizon in `CHALLENGER_EXHAUSTION`. Under `status_quo` the play stops in 1950 at `USSR.approve_korea`: the realized sequence is reachable only under the opportunist reading of Stalin's approval, which is a property of the definitions (D3).

## 3. C2: joint and unilateral kernels (fail)

| Years | `balance_cw` | Joint {USA, USSR} | USA alone | USSR alone |
|---|---|---|---|---|
| 1965, 1966 | false | out | out | out |
| 1967 to 1980 | true | **in** | out | **in** |
| 1981 | true | out | out | out |
| 1982 to 1986 | true | **in** | out | **in** |
| 1987 to 1989 | true | out | out | out |
| 1990, 1991 | false | out | out | out |

Identical under both hypotheses. **The registered claim fails**: in every year the joint kernel holds, the USSR's own kernel holds too.

- **Why the USSR alone keeps it.** In v0 the United States has no action after 1961 that can break `balance_cw` against Soviet resistance. The Wall closed the coarse Berlin crisis, the only coarse crisis the record supports. The 1983 exercise is inert in the coarse game, and in its sub-game a strike needs Soviet `preempt`. The Soviet bloc is broken only by Nature's opposition and revolution, which Soviet intervention defeats while `afghan ≠ war` and `legit_USSR = secure`. So the United States' route to a broken balance runs through Soviet choices. This is a model-content result. The v0 decision space lacks the American crisis-initiating options of the 1970s and 1980s (the 1973 alert is not modeled, decisions D2), and it has no mechanism by which American pressure removes Soviet capacity.
- **Why the United States alone does not keep it.** The other side, joined by Nature, forces a broken balance. In 1970 the first move is `USSR.strike_china`, a war between principals once the PRC is one. In 1975 it is Nature's `slowdown` (3 ticks), and from 1980 Nature's `opposition` (2 ticks).
- **The gaps in the joint kernel.** In 1981, Solidarity with the war in Afghanistan: neither side can intervene, and Nature's revolution is open. From 1987, perestroika makes legitimacy contested, and intervention is no longer available. In 1965 and 1966 the first clause of `balance_cw` is false: Soviet survivability is coded from 1967 (ontology section 2, not verified).

## 4. C3: Cuba (fail; degenerate as registered)

As registered, every kernel of `balance_cw` is empty in 1962: the United States is survivable from 1961 and the USSR only from 1967 (decisions D8). The computation confirms this. (a) and (b) fail degenerately, as decisions R C3 expected.

The variant with `no_war` in place of `balance_cw` was computed beside the registered one. It is the same under both hypotheses.

- **Bounded to the return (1963).** The joint kernel holds on the realized days from 16 to 24 October. It is left from 25 to 28 October, after `USA.defcon2` raised tension to the alert level at which Nature's accident is available. It holds again on the return. The United States' kernel holds to 22 October, is left on 23 October (the quarantine in force, ships still en route) and on 25 to 28 October, and holds on the return. The USSR's kernel is left from the first day: the United States can force a war by `air_strike`.
- **Unbounded.** The United States' kernel is never held: the USSR, joined by Nature, breaks peace later.
- **The shortest way back (b).** For the USSR's kernel it is `USA.pledge`, then `USSR.withdraw`. For the United States' kernel (bounded) it is `USSR.turn_back`. The Jupiter trade does not appear: the model's withdrawal needs only the pledge (Khrushchev's letter of 26 October), and the witness prefers the action declared first. Whether the trade was necessary is a debated reading, and v0 encodes the narrower one.
- **War outcomes (c).** These are the `WAR` and `NUCLEAR` endings of the sub-game. They are *forced* for the United States, which can strike, and *blocked* for the USSR, since the United States with Nature can keep them away. They are not contested. The "contested" of (c) is ill-posed for a dyad in which one side can always choose war (section 15).

## 5. C4: Berlin 1948 (fail on (c))

(a) `USA.airlift` is available in the first week, beside `convoy` and `withdraw`. (b) `SETTLED`, `TERMS`, `WITHDRAWAL`, `WAR` and the unresolved horizon are all reachable (22,784 fine states). (c) `GENERAL_WAR` by 1 January 1950 is blocked for the USSR: the rest can keep it away. The USSR has no bomb before 1950, so a war over Berlin needs American nuclear use. It is also blocked for the United States in the framework's sense, since the USSR with Nature can keep it away. So the claim's "contested" is not met. The United States alone could keep a war over Berlin from becoming general in 1948 and 1949, which is close to Trachtenberg's reading but not the registered expectation.

## 6. C5: Korea (fail on (b))

Under `opportunist`, (a) a limited war is reachable: the war, then the armistice, with no war between the principals (230,380 states to 1954). (b) The United States alone cannot keep `GENERAL_WAR` away to 1954, and relaxing either part of `USA.nuclear_korea` changes nothing. The route is not Korea. The USSR, with its bomb from 1950, can issue a Berlin ultimatum (open until the Wall), escalate the standing crisis and use nuclear weapons first (`USSR.nuclear_use`, the Warsaw Pact plans of nuclear use in a European war). Those plans were written for a war begun by NATO, but v0's guard on Soviet nuclear use does not carry that condition. That is a content gap in the guard, and an edit after first sight would need a source and a logged rerun (C5 is not under the total hold-out). Under `status_quo` no Korean war is reachable. H8: the same question to 1962 exceeded the explicit budget of 3 million states.

## 7. C6: the missile gap (fail on (b))

| Year | Replayed `belief_force_USA` | Hindsight `nuke_USSR` | Exceeds |
|---|---|---|---|
| 1957 | few | few | no |
| 1958 to 1961 | survivable (NIE 11-10-57 to NIE 11-8-60) | few | **yes** |
| 1962 | few (NIE 11-8/1-61) | few | no |

(a) holds. (c) holds: overhead coverage is in force from 1961, the gap closes in 1962 (one year), the hindsight force is unchanged, and the only event that lowers the estimate, `estimate_revised`, has the part `overhead`. (b) fails. From the replay state and from the hindsight state, `GENERAL_WAR` and `ACCIDENTAL_WAR` are equally near (2 ticks in 1958, 1 tick in 1959 to 1961, inside the standing Berlin crisis). The replay state reaches far more states (1,681,600 against 245,845 in 1958), but no adverse ending is nearer. In v0 the estimate acts only on the American buildup decision, so a belief error widens what can happen without shortening the way to war.

## 8. C7: the war scare (fail on (b))

At first sight (a) failed. The 1983 replay snapshot carried the 1961 contemporaneous reading of the Soviet force (`few`) instead of the record (`overkill`): the builder took the latest `replay` row whatever the record said later. The builder was corrected (section 9) and C7 recomputed; the first-sight result stands as the registered one.

| | First sight | After the builder correction |
|---|---|---|
| (a) forces equal | false (builder defect) | true |
| (b) distance out of the joint kernel, h and h' | 1 and 1: not nearer | 1 and 1: not nearer |
| (c) shortest to `GENERAL_WAR`, replay and hindsight | 4 and unreachable | 4 and unreachable |

(c) is the claim's content. Only with the Soviet reading of first-strike intent does the 1983 exercise lead to war: enter the exercise, the flash reports, the readying of forces, preemption, in 4 transitions. (b) fails because the joint kernel is left one tick ahead from both states for a different reason: an opposition in Poland while the war in Afghanistan removes the capacity to intervene (C13).

## 9. C8: verification (fail on (b)); the snapshot correction

(a) Each regime raises `oversight`: none to test_ban (1964), test_ban to ntm (1973), ntm to on_site (1988). (b) The state of 1964 is outside the joint kernel (Soviet survivability from 1967), and so is the state of 1988 (perestroika). The state of 1973 is inside, with the same distance out (2) whether `oversight` is ntm or test_ban. Oversight changes the reachability of the drawdown, not the distance out of the balance. (c) holds: from 1962, `arms = reduced` is reachable in 7 years on the model and unreachable on the frozen-oversight build.

**Correction after first sight** (data, not a guard; docs/guard_changelog_cw.md, last row). `models/cw/snapshots.py` now lets a contemporaneous `replay` reading stand only until the record moves past it. Only `snapshots/cw/replay/1983.json` changes (`nuke_USSR`: few to overkill, `assumed`), and C7 is the only claim that reads it.

## 10. C9: exhaustion (fail on (c))

From 1985, under both hypotheses, `CHALLENGER_EXHAUSTION` is reachable in 5 years. The necessary actions are `USSR.perestroika`, `USSR.dissolve` and Nature's `decline`, `collapse`, `delegitimation`, `opposition` and `revolution`. They include economic events (`decline`, `collapse`) and legitimacy events (`perestroika`, `delegitimation`), and no US action. With the United States only idling the ending stays reachable, so (a) and (b) hold. (c) fails: the ending is blocked for the United States, because the USSR alone can keep it away by not reforming. In v0 the exhaustion runs through Gorbachev's reform (Miller 2016), so American sufficiency is not contested: American actions are neither necessary nor sufficient.

## 11. C10: capability past a threshold (fail on (b))

(a) holds. From 1965, raising a force at survivable or above never flips joint-kernel membership. (b) fails because no belief variable and `oversight` ever flip membership, in any year (score 0 throughout). The nuke family scores 1 or 2 in 1947 to 1958 and 1962 to 1975 (the survivability clause of `balance_cw`), and 0 from 1976 and in 1959 to 1961. Membership is moved instead by `esc`, `legit_USSR`, `bloc_USSR` and `esc_sino`. In v0 the joint kernel of the two principals is insensitive to their beliefs: a belief only opens an option, such as preemption, which the joint coalition can decline. This is the structural content of the failure, and it bears on the AGI model (section 17).

## 12. C11: the triangle (fail)

No coalition of the principals other than the USSR keeps `balance_cw` in 1969 to 1972, on either build: the USSR, joined by Nature, breaks it. With Nature joined to the coalition:
- **Scripted build:** the empty coalition keeps it, since no Soviet move alone breaks the balance when the Sino-Soviet war does not count.
- **Model:** {PRC} keeps it in 1969, by not opening the clash, and nothing keeps it from 1970. Once the confrontation exists, the Soviet strike on China is open until the alignment of 1973, and the American opening (1971) and the rapprochement (1972) come too late to close it.

The registered change from {USA} to {USA, PRC} does not appear.

## 13. C12: negative controls (pass)

- **(a)** Under `opportunist`, a US preventive strike by 1955 needs exactly one relaxation, {`USA.preventive_strike:policy`}: the documented rejection. Under `status_quo` it needs two, since the hindsight belief is the hypothesis's own and NSC-68's reading must be relaxed in.
- **(b)** A Soviet offensive into Western Europe by 1990 needs at least 2 relaxations under `opportunist` (3 under `status_quo`). Every minimal set lifts `USSR.invade_west:no_us_nuclear`, the American nuclear deterrent, which the record never lifts. This is a content control in the sense of H6.
- **(c)** A negotiated merger of the blocs is vacuous: there is no action or variable for it.
- **(d)** `ACCIDENTAL_WAR` is reachable in 1 tick from the standing crisis of 1959 and from the Cuba sub-game, and no coalition of declared actors forces it from either.

## 14. C13: the USSR's own kernel of its bloc (pass)

`safe({USSR}, bloc_intact)` holds from 1975 to 1980, is left in 1981, is re-entered in 1982 (martial law) and is left from 1987. **The departure year is 1980**, inside the window 1979 to 1989; the realized move of that year is Nature's opposition (Solidarity).

The perturbations that restore the 1981 state are `afghan → none` or `withdrawn`, `bloc_USSR → intact`, and `esc_sino → war`. The last is an artefact: a Sino-Soviet war is a terminal state in which the bloc is still intact. **The driving variable is `afghan`.** With its army in Afghanistan, the USSR lost the capacity to intervene in Poland, as the Suslov commission's deliberations record (Kramer 1999). (c) Stability under refinement is not tested at v0.

## 15. What the failures are

The transfer-hypotheses document orders the possible causes as model content, framework defect, wrong hypothesis. None of the ten failures is a framework defect. The engines agreed where they overlap: the symbolic kernels are those of the explicit engine on the states both can reach, and the lifting is exact by D5. **No framework change was made: 0 of the budget of 5.**

| Cause | Claims |
|---|---|
| The registered predicate makes the question degenerate in the year asked | C3 (a, b): `balance_cw` false in 1962 |
| "Contested" for a dyad in which one side can always choose war or peace | C3 (c), C4 (c), C9 (c) |
| Model content: the v0 decision space | C2 (no American crisis-initiating option after 1961; the 1973 alert absent), C5 (Soviet nuclear use without the plans' condition of a war begun by NATO), C11 (the Soviet strike on China open until 1973), C6 (b) and C8 (b) (beliefs and oversight act on options and treaties, not on the way to war) |
| A ranking with ties | C10 (b): beliefs and oversight never move the joint kernel |
| A builder defect, corrected | C7 (a) at first sight |

## 16. The transfer hypotheses

| Id | Result | Claims and numbers |
|---|---|---|
| H1 belief change precedes the response by a lag; the point of no return hides in the lag | **not supported** | The lag is there: the missile-gap estimate of Dec 1957, the US buildup of 1961, the force of 1965 (C6). But the belief errors do not move the boundary: C6 (b), C7 (b) and C10 (b) fail. A belief opens an option (C7 c: war reachable only with the war scare); it does not shorten the way out of a kernel |
| H2 a concession removes the motive only under limited aims | **failed on C8, consistent on C9** | Verification widens nothing measurable (C8 b); the exhaustion needs no US action (C9 b). The détente window under the two aims was not computed |
| H3 preventive defection follows a credible threat without a continuity guarantee; the timing is set by a clock | **held where tested** | The preventive strike of the early 1950s needs exactly the one documented rejection while the US monopoly lasts (C12 a, opportunist); past a survivable force, more force does not matter (C10 a). C3 as registered is degenerate |
| H4 obligations are load-bearing for levers | **failed** | The airlift is in the decision space (C4 a), but general war is not blockable by the United States alone in 1950 to 1953 (C5 b), and no coalition holds the triangle (C11) |
| H5 a pending decision is part of the state | **tested** | Every kernel question was asked from snapshots carrying the pending programmes. Without them, only the USSR's own kernel of `balance_cw` changes, in 1948 and 1949 (the pending bomb); no result from 1965 on reverses |
| H6 negative controls are informative as content controls | **held** | C12 (a): the single relaxation is the documented rejection; C12 (b): every minimal set lifts the American deterrent |
| H7 a held balance is joint-kernel membership, not unilateral | **failed** | The state is in the joint kernel in 1967 to 1980 and 1982 to 1986, but in the USSR's own kernel in the same years (C2). In v0 the balance is one the USSR can hold alone; the United States never can |
| H8 the horizon can decide a forcing question | **not tested** | C5 at the bound plus eight ticks exceeded the explicit budget |

## 17. What it teaches for the AGI model

- **A kernel of a coalition is insensitive to the beliefs of its members** (C10 b, C7 b). A belief error mattered in v0 only by opening an option, such as preemption under the war scare, that a member can decline. For the AGI model's coexistence question (agi_testbed.md G5), a joint kernel ⟨⟨H, A⟩⟩ will not register belief errors of H or A. Belief errors show up in unilateral kernels and in reachability, and those are where the report must look for them.
- **The balance was unilateral in v0** (C2, H7). Whether it is joint depends on whether the other side has options that break it against resistance. The registered AGI claims that compare joint and unilateral kernels need the human side's breaking options as carefully catalogued as the AI's.
- **Exhaustion without an adversarial act is reachable with the challenger's own reform as a necessary step** (C9). The AGI analogue, dependence lock-in with no adversary, stays `untested`: v0's exhaustion is driven by the challenger's choices, not by the other side's.
- **Capacity clocks decide departures** (C13): Afghanistan removed the capacity to hold the bloc. This is the same shape as WW2's resource clocks (H3) and July 1914's pre-commitment clock.

## 18. Gate and proposals for the owner

**Phase 3 gate (PHASES.md): not passed as written.** C1, C12 and C13 pass; C2 to C11 fail as read. The transfer hypotheses: two held (H3 where tested, H6), H5 tested, H8 not tested, and H1, H2, H4 and H7 failed or unsupported, each explained above as model content or claim reading, not as an engine defect. The WW2 suite is unchanged, since no framework change was made; its run this session gave 1059 passed, 40 skipped and 7 failed, the seven being the recorded crisis-model claims. Framework changes: 0 of 5.

Proposed, not made, for the owner's decision (decisions section O):
1. **C3:** ask the crisis question with `no_war`, as for T13's retired predicate; the computed variant is in section 4.
2. **C3 (c), C4 (c), C9 (c):** restate "contested" for a dyad in the fortune sense, or as "neither side can force the outcome and neither can be sure of avoiding it with Nature against it".
3. **C5:** either add to `USSR.nuclear_use` the plans' condition (a war begun by NATO; Mastny and Byrne 2005), a guard edit after first sight to be logged with a rerun, or re-ask C5 for general war reached through the Korean theatre.
4. **C2 and C11:** a cw_v1 with the American crisis-initiating options of the 1970s and 1980s (the 1973 alert as a sub-game) and the Sino-Soviet confrontation of 1969 as a sub-game, run as a new registration.
5. **C6 (b), C8 (b), C10 (b):** measure belief and oversight by their effect on reachability and on unilateral kernels, where v0 shows they act (C7 c, C8 c), rather than on the joint kernel's distance.
6. **The data:** allow the testbed's data hosts in the environment's network settings, or supply the files, so that the "not verified" levels can be checked against the series and the NIE replay can run blind.

## 19. Checks made after the run (not registered claims)

- The C5 route, read from the attractor of {USSR, PRC, Nature} on the graph from 1950 cut at 1954 (rank 3, United States idle): `USSR.berlin_ultimatum` (1950), `USSR.escalate` (1951), `USSR.nuclear_use` (1952).
- The engines agree: on the 25,750 states reachable from the 1975 hindsight state, the explicit kernels of `balance_cw` for {USA, USSR}, {USA} and {USSR} equal the symbolic ones state by state.
- H5: the kernels of section 3 and section 14 recomputed from the hindsight states with every pending counter at zero (section 16).
