# The PRC-scope experiment (owner's decision 3a)

> **Status: exploratory analysis, not a registered claim and not a model edit.** It was run on analysis builds derived from Cold War v0 at run time (`models/cw/v0.py` is unedited and stays under protocol). Its results were seen before any cw_v1 claim was registered, so they are **disclosed as an early sight in cw_v1's registration**. Every result is conditional on v0's decision space and on the hindsight snapshots. No bare reachability result is a finding here: results are kernel membership, pivotal coalitions and shortest-trace distances, each with its engine.

Question (docs/owner_decisions_2026-10-23.md, 3a): does the PRC's behaviour differ in kind from the USSR's, so that cw_v1 should make it a principal beside the USA, the USSR and Nature, and from when? Inputs: [prc_research.md](prc_research.md) (section 2 C: principal from 1950, candidate actions), [cw_v0_decisions.md](cw_v0_decisions.md) (D2, D5, R C2, R C11), [ontology_cw.md](ontology_cw.md), [actions_cw.md](actions_cw.md).

Files:
- Analysis builds: `models/cw/experiments/prc_scope.py`.
- Experiment script: `scripts/cw_prc_experiment.py`.
- Full output, both hypotheses: `reports/prc_experiment.log`.
- Construction checks: `tests/coldwar_experiments/test_prc_scope.py`.

## 1. Method

- **Engine.** Symbolic kernels and attractors on the coarse game (compiled BDD core). The crisis sub-games are inert at the coarse level (decisions D5), as in C2 and C11.
- **States.** v0's hindsight snapshots for 1 January 1950 to 1991, per `aims_USSR` hypothesis. On the builds with P50's content, the added variables take their record levels (section 2.3).
- **Predicates.** The same six on every variant, so that variants are compared on one question:
  - **Core family**, US–Soviet only:
    - `no_war_core`: `esc < conventional`;
    - `balance_nobloc_core`: `no_war_core ∧ both_or_neither`;
    - `balance_cw_core`: `balance_nobloc_core ∧ bloc_intact`.
  - **Tri family**: the same, with `no_war` also excluding a Sino-Soviet war (`esc_sino = war`) and, where the variable exists, a US–PRC war (`esc_usprc = war`).
  - v0's registered `no_war`, `balance_nobloc` and `balance_cw` are the core family on S and the tri family on P69.
- **Measures.**
  1. Kernel membership of every coalition of the variant's principals, with and without Nature (the fortune variant), each year.
  2. Pivotal coalitions: the inclusion-minimal coalitions whose kernel contains the state. They are computed against the USSR (from the principals other than the USSR, as R C11) and in general.
  3. The shortest trace, all actors, to a US–Soviet general war (`esc ≥ tactical_nuclear`) and to a Sino-Soviet war. This is the rank in the all-actor attractor. **Who must move** is read from restricted games: each actor's declared actions get the guard part `dropped: FALSE`, so pending decisions keep their delayed effects. An actor must move if the target becomes unreachable, or further away, without it.
  4. Pairwise differences in kernel membership.
  5. The behaviour-model check (section 6).
- **Run.** Two processes, one per hypothesis, on the shared machine: 46 min 18 s (status_quo) and 46 min 43 s (opportunist). By variant, per hypothesis: S 34 s, P69 233 to 277 s, P50 2,139 to 2,166 s, N50 42 to 46 s, B 29 s. The behaviour check took the rest. P50's three-principal kernels cost about nine times P69's. Its slowest kernels, about 4 min each, are those of `balance_nobloc_core` for coalitions containing the USSR and Nature.

## 2. Variants

| Variant | Model | Declared variables | Actions (with built-ins) | The PRC's decisions are |
|---|---|---|---|---|
| S | `08da3b3a28da` (v0 `build(prc_principal=False)`) | 26 | USA 17, USSR 25, Nature 19 | Nature's (v0's 3) |
| P69 | `527d0f540ac6` (v0 `build()`) | 26 | USA 17, USSR 25, PRC 4, Nature 16 | the PRC's from 1969 (v0's 3) |
| P50 | `d1fc1abd2f34` | 29 | USA 17, USSR 25, PRC 11, Nature 17 | the PRC's from 1950 (v0's 3 + 7) |
| N50 (control) | `18bfcf582b18` | 29 | USA 17, USSR 25, Nature 27 | Nature's (P50's content) |
| B | `2455f8da8a76` | 29 | USA 17, USSR 35, Nature 17 | the USSR's (P50's content) |

The test checks that S and P69 have the fingerprints of v0's two builds.

**N50 is a control the owner did not list.** S against P50 mixes two effects, the added content and the PRC's agency. S against N50 isolates the content; N50 against P50 isolates the agency (the same actions, chosen by the PRC instead of by Nature).

**B** gives every PRC decision to the USSR, the "bloc member" model. In B the USSR plays at most one action a year for itself and the PRC together. The bundled reading (marked P50b) puts the PRC always on Moscow's side of a coalition, with two moves a year. It is read off P50's kernels. Every pivotal-coalition row of P50b equals B's (reports/prc_experiment.log, section 2), so the one-move limit does not matter here.

Wars counted and endings, on the P50-content builds:
- **P50** (the PRC a principal): a Sino-Soviet war and a US–PRC war break `no_war`. A Sino-Soviet war (a Soviet strike) is `GENERAL_WAR`; a US–PRC war is not.
- **N50 and B**: neither war counts, as in S.

The uniform predicate families of section 1 make the comparison independent of these choices.

### 2.1 Added variables (P50, N50, B)

| Variable | Levels | How it touches v0 |
|---|---|---|
| `align_PRC` | adds `independent` after `us_aligned` (monotone kept) | only `independent_line` sets it; `strike_china`'s part reads it (below) |
| `esc_usprc` | peace, crisis, war | US–PRC escalation. Read by `USA.nuclear_korea` (below) and by `bomb_programme`. It is not `esc`, which stays US–Soviet |
| `nuke_PRC` | none, programme, few (monotone) | gates `USSR.strike_china` |
| `polemic_PRC` | flag (monotone) | gates `USSR.withdraw_advisers` |

### 2.2 Added actions and edits

None is speculative. The research note grades none of these sources [U]. Where it grades the documented alternative [S/U] (the 1961 suspension debate), the action's own source is [S].

| Action | Guard (parts) | Effect | Contemporaneous source | Documented alternative |
|---|---|---|---|---|
| `PRC.intervene_korea` | `korea = war`, `esc_usprc = peace` | `esc_usprc := war` | Mao's telegrams of 2 Oct (Chinese text) and 13 Oct 1950; the CPV order of 8 Oct 1950 (CWIHP; Mansourov; Chen Jian 1994). Note 1.2 | the Russian text of 2 Oct; the Politburo majority of 4–5 Oct; the halt of 12 Oct |
| `PRC.strait_pressure` | `esc_usprc = peace`, `korea = armistice` | `esc_usprc` +1 | shelling of Jinmen, 3 Sep 1954 and 23 Aug 1958; Mao to Peng and Huang, 27 Jul 1958; Supreme State Conference, 5 and 8 Sep 1958. Note 1.4 | the postponement of 27 Jul 1958 |
| `PRC.strait_relax` | `esc_usprc = crisis` | `esc_usprc` −1 | Zhou at Bandung, 23 Apr 1955; the message of 6 Oct 1958. Note 1.4 | continuing the shelling |
| `PRC.bomb_programme` | `nuke_PRC = none`, `threat: esc_usprc ≥ crisis` | `nuke_PRC := programme` | Secretariat enlarged meeting, 15 Jan 1955 (Lewis and Xue 1988). Note 1.8 | suspension, 1961 debate [S/U] |
| `Nature.prc_test` | `nuke_PRC = programme`, `tick ≥ 1964` | `nuke_PRC := few` | first test, 16 Oct 1964. The note: "better kept as Nature" | — |
| `PRC.challenge_moscow` | `align_PRC = soviet_ally`, `¬polemic_PRC` | `polemic_PRC := True` | Mao–Khrushchev, 2 Oct 1959; "Long Live Leninism!", 16 Apr 1960. Note 1.6 | Wang Jiaxiang's letters, Feb–Mar 1962 |
| `PRC.deter_in_vietnam` | `tick = 1965`, `align_PRC ≥ split` | none | Zhou via Ayub Khan, 2 Apr 1965; Mao–Kosygin, 11 Feb 1965. Note 1.9 | united action. **No effect**: v0 has no Vietnam and no ceiling for it to act on (D2) |
| `PRC.independent_line` | `align_PRC = us_aligned` | `align_PRC := independent` | Hu Yaobang's report, 12th Congress, Sep 1982. Note 1.16 | continuing the alignment (1981) |

Further details:
- P50's PRC actions all carry the scope part `principal: tick ≥ 3` (1950). v0's `border_clash`, `rapprochement` and `normalize` keep their guards, with the scope part moved from 1969 to 1950.
- The names differ from the note's `enter_korea` and `build_bomb`, because in B those would collide with the USSR's own actions.

Edits of v0's actions on these builds. Each is a reading of the note, not a historical finding:
- **`USSR.withdraw_advisers`** gains the part `challenge: polemic_PRC`. The split becomes a Chinese challenge that Moscow answers (note 1.6).
- **`USSR.strike_china`**:
  - The part `targets` changes from `tick ≥ 1965` to `nuke_PRC = few`. On the record these are the same years.
  - The part `no_us_link` changes from `align_PRC ≠ us_aligned` to `align_PRC < us_aligned`, so the 1982 independent line does not reopen the strike. The alternative reading (`≠`) would reopen it from 1983 while `esc_sino = clash`. It was not computed.
- **`USA.armistice`** also sets `esc_usprc := peace`.
- **`USA.nuclear_korea`**: its part `total_commitment` (`esc ≥ conventional`) also holds when `esc_usprc = war`. Truman's press conference of 30 Nov 1950 answered the Chinese offensive. This is the **only link from any PRC decision to the US–Soviet ladder**, and section 4 shows that it carries every core difference.

### 2.3 Hindsight levels of the added variables

| Variable | Record on 1 January |
|---|---|
| `esc_usprc` | war 1952–1953; crisis 1955; otherwise peace |
| `nuke_PRC` | programme 1956–1964; few from 1965 |
| `polemic_PRC` | True from 1960 |
| `align_PRC` | independent from 1983 |

How the record is placed at annual resolution:
- **The Korean entry is shown one year late ([SQR]).** The entry of Oct 1950 answered a war that began inside the same year (`korea = war` is first visible on 1 Jan 1951). So the 1951 state is the state *before* the entry.
- **1958.** The crisis began and ended inside the year.
- **The challenge** is placed in 1959 (the quarrel of 2 Oct 1959), because the withdrawal of Jul 1960 answered the polemic of Apr 1960 inside one year ([SQR]).

At one PRC move a year, both relaxations fall in a year that already has another PRC decision ([NSL]). The realized decisions are therefore checked at their hindsight states, not replayed as a path:
- 1951 `intervene_korea`
- 1954 and 1958 `strait_pressure`
- 1955 `bomb_programme`
- 1959 `challenge_moscow`
- 1965 `deter_in_vietnam`
- 1969 `border_clash`
- 1972 `rapprochement`
- 1982 `independent_line`
- 1989 `normalize`

The test checks that each of these is available at its state under both hypotheses.

## 3. Kernels and pivotal coalitions

Full tables are in reports/prc_experiment.log, sections 1 and 2. Years 1950–1991; "none" means no year in that range.

**Common to every variant and both hypotheses** (v0's known shape, R C2 and the amendments):
- The United States alone keeps no predicate before 1962.
- From 1962 every coalition, including the empty one, keeps `no_war_core`. A US–Soviet general war has no trace from 1962 in any variant (section 5).
- The USSR alone keeps the core family in 1950–1958 (except as below).
- In 1959–1961, during the Berlin crisis, no coalition without Nature keeps `no_war_core`. The USSR with Nature keeps it.

**Where the variants differ.**

| Years | Predicates | Coalition | S | P69 | N50 | P50 | B |
|---|---|---|---|---|---|---|---|
| 1951 | core and tri, all three | {USSR} | in | in | out | **out** | **in** |
| 1951 | core, all three (status_quo) | {USSR, Nature} | in | in | in | **out** | in |
| 1951 | core and tri | {USSR, PRC} | — | in | — | in | (= {USSR}) in |
| 1952–1953 | core and tri, all three | {USSR} | in | in | out | out | out |
| 1952–1953 | core (status_quo); tri (both) | {USSR, Nature} | in | in | out | out | out |
| 1952–1953 | core and tri | {USSR, PRC} | — | in | — | out | — |
| 1951–1953 | tri | {USA, USSR} | in | in | out | out | in 1951, out 1952–1953 |
| 1962–1969 | `no_war_tri` | {Nature}, {USA, Nature} | in | out | in (to 1969) | out 1965–69, in 1962–64 | in (to 1964) |
| 1962/1967–1969 | tri | {PRC}, {USA, PRC} | — | **in** | — | **in** | — |

Notes on the table:
- **1951 and 1952–1953.** The PRC can enter Korea (1951). Its entry opens the US nuclear option (1952–1953: `nuclear_korea` with `esc_usprc = war`). Under status_quo the part `reading` (belief ≠ opportunist) holds, and the United States alone can then make a general war in one step. Under opportunist, Nature must first raise the belief (NSC-68), so with Nature joined the USSR keeps the peace in 1952–1953 under opportunist but not under status_quo.
- **1962–1969, tri.** Joining Nature is enough wherever Nature, not the PRC, holds the border clash (S, N50), or holds the bomb test that the strike needs (P50 and B, 1962–1964: Nature withholds `prc_test`). The 1962–1964 cell is an artefact of placing the test date in Nature's hands.
- **Tri family, 1951–1953.** In the tri family a US–PRC war is itself a break, so whoever holds the entry decides 1951 (Nature on N50, the PRC on P50, Moscow on B). In 1952–1953 the predicate is false on the P50-content hindsight states (the war is on the record).
- **The bundled reading.** P50b equals B in every year: {USSR, PRC} in P50 has exactly B's {USSR} kernels.

**Pivotal coalitions** (minimal coalitions whose kernel contains the state), core family, all hypotheses unless stated:

| Years | S, P69 | N50 | P50 | B (= P50b) |
|---|---|---|---|---|
| 1950, 1954–1958 | {USSR} | {USSR} | {USSR} | {USSR} |
| 1951 | {USSR} | {USA, USSR}; +N {USSR} | **{USA, USSR} and {USSR, PRC}**; +N same (status_quo), {USSR} (opportunist) | {USSR} |
| 1952–1953 | {USSR} | {USA, USSR}; +N {USA, USSR} (sq), {USSR} (opp) | same as N50 | same as N50 |
| 1959–1961 | none; +N {USSR} | same | same | same |
| 1962–1991 | {} | {} | {} | {} |

**Against the USSR** (R C11's reading: the principals other than the USSR), core family:
- There is no pivotal coalition before 1962 in any variant. The USSR, joined by Nature or not, can always break the core predicates.
- From 1962 the empty coalition is enough for `no_war_core`. For `balance_cw_core` the empty coalition is enough only with Nature joined (1967–1989, as v0).
- In the tri family the PRC is pivotal against the USSR in 1962–1969 on P69 and P50 (`no_war_tri`: {PRC}; P50 1962–1964 only without Nature). In 1967–1969 it is pivotal for `balance_nobloc_tri` and, with Nature, for `balance_cw_tri`. This is the C11 mechanism: before the clash of 1969 the PRC keeps the Sino-Soviet war away by not opening it. It needs only the 1969 scope, and B and S cannot show it.

## 4. The differences, read as the owner's test

**S against P50 or P69: the PRC's agency changes US–Soviet outcomes, but only in Korea.**
- On the core family, P69 equals S in every year.
- P50 differs from S only in 1951–1953.
- **S against N50** (content only): the 1951–1953 difference is there already in N50, with the PRC's decisions in Nature's hands. In 1952–1953 it is a difference of content, not of agency: the Chinese entry opens the US nuclear option whoever chose it.
- **N50 against P50** (agency only): on the core family they differ in **1951 only, and only under status_quo with Nature joined** ({USSR, Nature} is in N50's kernel, not P50's). Under opportunist they agree everywhere on the core family. On the tri family they also differ in 1965–1969 ({Nature} and {USA, Nature}: in N50, Nature holds the clash).

**B against P50: the PRC is not reducible to a Soviet-bloc member, but the evidence is one year.**
- On every predicate and both hypotheses, B and P50 differ only in **1951**. In B the USSR alone keeps all six predicates (it withholds the entry). In P50 it does not, and the pivotal family gains {USSR, PRC} beside {USA, USSR}.
- From 1952 to 1991 B and P50 agree on every coalition the two share. P50's own PRC coalitions add the tri-family pivotality of 1962–1969, which B cannot express.

**S, B and P50 do not agree everywhere.** By the owner's criterion the PRC should be a principal. But inside v0's decision space its agency moves US–Soviet kernels in exactly one year (1951). It moves Sino-Soviet kernels in 1962–1969, which P69 already captures.

## 5. Shortest traces and who must move

Rank in the all-actor attractor (ticks), from the hindsight state of each year.

| Target | Years | S, P69 | N50, P50, B (status_quo) | N50, P50, B (opportunist) |
|---|---|---|---|---|
| US–Soviet general war | 1950–1951, 1954–1958 | 2 | 2 | 2 |
| | 1952–1953 | 2 | **1** | 2 |
| | 1959–1961 | 1 | 1 | 1 |
| | 1962–1991 | no trace | no trace | no trace |
| Sino-Soviet war | 1950 | 16 (S), 21 (P69) | no trace on P50, N50, B (see limits) | 16 |
| | 1951 → 1972 | falls by one a year; 2 in 1964–1969, 1 in 1970–1972 | same (N50: 3 in 1963–1964) | same |
| | 1973–1991 | no trace | no trace | no trace |

**Who must move** (restricted games):
- **US–Soviet general war.** The USSR must move in 1950–1958 in every variant, with these exceptions under both hypotheses:
  - 1951–1953 on N50 and P50, and 1952–1953 on B (where the entry is Moscow's own). There the US nuclear option after a Chinese entry gives a trace without the USSR. Under opportunist that trace also needs Nature's NSC-68 to raise the US reading. On N50 in 1951 it is longer without the USSR: 3 ticks instead of 2.
- **The United States** must move in no year. Without it, the 1952–1953 trace lengthens from 1 to 2 (status_quo).
- **Sino-Soviet war.** The USSR must move in every year with a trace.
  - The PRC must move 1950/1951–1969 on P69 and P50 (the clash).
  - Nature must move to 1969 on S and N50 (Nature holds the clash), and to 1964 on P50 and B (the bomb test).
  - On B the USSR must move both for itself (the strike) and for the PRC (the clash).

## 6. Behaviour-model check

**Method.** For each realized PRC decision, at the hindsight state of its year, per hypothesis and for all six predicates:
- **On B:** is the decision, played by the USSR, *kernel-preserving* for the USSR? That is, every completion (every available move of the other actors) leads into B's K_USSR. The same is computed for idle, and for the USSR's own realized move where it differs.
- **On P50:** the same for the coalition {USSR, PRC}, with the USSR's realized move fixed, and for {PRC} alone.
- **Distances** to both targets from the successor under the others' realized moves.

A decision that is not kernel-preserving, when idle is, is one that B's USSR **would not choose** under a safety objective.

| Year | Decision | B: preserving for K_USSR? (decision / idle) | Distance to general war after decision / idle | Reading |
|---|---|---|---|---|
| 1951 | `intervene_korea` | **none of six / all six**, both hypotheses | sq **1** / 2; opp 2 / 2 | **B's USSR would not make it**: it leaves Moscow's kernel of every predicate. In P50 it is likewise not preserving for {USSR, PRC} (none / all six). {PRC} alone is outside its kernel either way, so the entry costs the PRC nothing it could have kept alone, while it costs the bloc controller everything. |
| 1954 | `strait_pressure` | all six / all six | 2 / 2 | indifferent: no predicate reads `esc_usprc` below war |
| 1955 | `bomb_programme` | all six / all six | 2 / 2 | indifferent |
| 1958 | `strait_pressure` | `no_war` core and tri / same | 2 / 2 (1 after Moscow's own Berlin ultimatum) | indifferent |
| 1959 | `challenge_moscow` | none / none (the Berlin crisis: the state is outside K_USSR) | 1 / 1 | indifferent |
| 1965 | `deter_in_vietnam` | `no_war` core and tri / same | no trace | indifferent (no effect) |
| 1969 | `border_clash` | all six / all six | Sino-Soviet war 1 / 2 | **not discriminated by kernels**: in B Moscow also holds the strike, so a clash costs it nothing. In P50, {PRC} alone keeps `no_war_tri` after idle but not after the clash. The clash shortens the Sino-Soviet trace from 2 to 1. |
| 1972 | `rapprochement` | all six / all six | Sino-Soviet war no trace / 1 | not discriminated: safe both ways for B |
| 1982 | `independent_line` | 4 of 6 / same | no trace | indifferent (the reading of `no_us_link` keeps it inert) |
| 1989 | `normalize` | 4 of 6 / same | no trace | indifferent |

**Findings by episode:**
- **Korea 1951.** This is the one realized PRC decision that the computation shows a USSR-aligned actor would not take. It leaves the USSR's kernel of every predicate under both hypotheses, and under status_quo it brings a US–Soviet general war one tick nearer. This matches the note's section 1.2 (Stalin withdrew air cover and was ready to let Kim fall).
- **The 1958 Strait crisis and the 1959–1960 challenge.** Both are indifferent in v0's decision space. Nothing in v0 links the Strait to the US–Soviet ladder (no US escalation option against the PRC, no Soviet guarantee), and the split changes no predicate until the clash.
- **The 1969 clash.** The safety measure cannot tell it apart, because B gives Moscow the strike as well. The difference shows instead as the PRC's pivotality against the USSR in 1962–1969 (section 3), which a bloc member cannot have.

## 7. Recommendation for cw_v1

**Make the PRC a principal from 1950 (P50 scope), with a smaller action set than the note's.**

Evidence:
1. **Not S.** S differs from P69 and P50 in the tri family 1962–1969: the PRC is pivotal against the USSR, and {Nature} loses the kernel when the PRC holds the clash. With P50's content it also differs on the US–Soviet core in 1951–1953.
2. **Not B.** B differs from P50 in 1951 on every predicate and both hypotheses. The realized 1951 entry is a move B's USSR would not choose: it is preserving for none of six kernels while idle is preserving for all six. B also cannot express the PRC's pivotality of 1962–1969.
3. **From 1950, not 1969.** P69 and P50 differ only in 1951–1953 (Korea) and in the Nature-test artefact of 1962–1964. The 1951 difference is the agency of the entry ({USSR, PRC} pivotal beside {USA, USSR}). It is the only year in which the PRC's own choice changes a US–Soviet kernel. A 1969 start keeps it inside `korea = war`.
4. **Fewer actions than the note's eight.** In v0's decision space these actions are indifferent in every computed measure, while P50 costs about 9× P69's kernel time:
   - `strait_pressure` and `strait_relax`;
   - `challenge_moscow`;
   - `deter_in_vietnam`;
   - `independent_line`;
   - `bomb_programme` with `prc_test`, beyond dating the strike's target.

   cw_v1 should keep them only together with the variables they would act on: US escalation options against the PRC in the Strait, a Soviet guarantee, a ceiling on US escalation in Vietnam, and the reading of `strike_china` after 1982. The minimal P50 for cw_v1 is `intervene_korea`, the `nuclear_korea` link and v0's three actions, with the scope part at 1950. `nuke_PRC` (or the dated `targets` part) can stay as the strike's condition.

If the owner prefers the smaller model, **P69 plus a Korean exception** (the PRC a principal for its 1950 entry decision only) reproduces every difference found here.

## 8. Limits

- **v0's decision space.**
  - **US–Soviet general war has no trace from 1962 in any variant.** After the Wall neither side has a war-forcing option (C2), so no PRC variant can change a US–Soviet kernel after 1961. A cw_v1 with the American crisis options (decision 2m), or with a Strait escalation ladder, may find PRC effects that this experiment cannot see.
  - **Every core difference runs through one link**, the `nuclear_korea` guard reading. Without it the PRC touches no US–Soviet predicate at all.
- **Annual resolution.**
  - The Chinese entry is placed in 1951 ([SQR]), so `esc_usprc = war` is on the record from 1952, not 1951.
  - The relaxations of 1955 and 1958 share their year with another PRC decision ([NSL]).
  - The decisions were checked at hindsight states, not along a replayed path.
- **Artefacts of the encoding.**
  - **Nature holds the test date.** With Nature joined to a coalition, Nature withholds `prc_test` and so blocks the strike in 1962–1964.
  - **`strait_pressure` needs `korea = armistice`, and `bomb_programme` needs a Strait crisis.** Under status_quo, where Stalin's approval of the war is unavailable, the bomb, and with it the Soviet strike, has no trace from 1950. This is why the Sino-Soviet trace is missing for 1950 on N50, P50 and B. A guard `korea ≠ war` would remove the artefact.
- **The B model.** One USSR move a year. The bundled reading P50b gives the same tables.
- **The behaviour check** uses kernel preservation (a safety objective) and distance. It cannot separate decisions whose consequences the controller also controls (the 1969 clash under B).
- **Engine.** The coarse game is computed symbolically from hindsight states. The crisis sub-games are inert (D5). The lifting of D5 was not applied (no sub-game falls in the years where the variants differ, 1951–1953 and 1962–1969, other than Cuba 1962, which is inert here in every variant alike).
