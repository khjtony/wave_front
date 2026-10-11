# The Cold War as the second validation episode

Purpose: after the framework is developed on the Second World War ([ww2_testbed.md](ww2_testbed.md)), run it on a second episode with a different structure, so that passing both is evidence about the framework rather than about one fit. The Cold War is the validation set; it is not used for development. Framework changes it forces are allowed only under a logged budget (see [PHASES.md](PHASES.md), phase 3 and 4).

Status: claims C1 to C13 are registered now, before any WW2 guard exists, so that the second episode cannot be chosen to fit a framework already tuned. Expected outputs that still need historiographical detail are marked `refine at phase 3`; refinements go in the changelog (section 8) and may not weaken a claim.

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
| C2 | each year from 1965 (mutual survivable second strike) | the realized state is inside the joint kernel `⟨⟨USA, USSR⟩⟩□balance_cw` every year, and outside the unilateral kernels `⟨⟨USA⟩⟩□balance_cw` and `⟨⟨USSR⟩⟩□balance_cw` | joint membership every year; unilateral non-membership every year; the report names what each side could do to break it | Schelling 1960, 1966; Trachtenberg 1999 |
| C3 | 1962, October, crisis sub-game | Cuba leaves the unilateral kernels and stays inside the joint kernel; the shortest trace back matches the realized de-escalation (withdrawal plus the Jupiter trade); war outcomes are `contested` | as stated | Allison and Zelikow 1999; Fursenko and Naftali 1997; the ExComm recordings |
| C4 | 1948, June | the airlift (`resist_without_escalation`) is in the decision space; `NEGOTIATED_SETTLEMENT` of the blockade is reachable; `GENERAL_WAR` is `contested` | as stated | FRUS 1948; Trachtenberg |
| C5 | 1950, June | a `LIMITED_WAR` in Korea is reachable and `GENERAL_WAR` is blockable by the United States alone, because nuclear use requires `commit = total` and `belief[USA][USSR].aims ≠ opportunist` | `⟨⟨USA⟩⟩□¬GENERAL_WAR` true in the 1950 state under the documented guards | FRUS 1950; Gaddis 1982 and 2005 |
| C6 | 1957 to 1961, annual replay | the replayed `belief[USA][USSR].force` from dated estimates and press exceeds the hindsight `nuke[USSR]`; analysis from the replay snapshot shows more adversarial reachability than from the hindsight snapshot; the gap closes within one year of `intel[USA] = overhead_reconnaissance` (1960 to 1961) | as stated; the closing is driven by `intel`, not by any force change | the NIE series (CIA CREST); Gaddis 2005; Preble 2004 |
| C7 | 1983, November | the Soviet belief `belief[USSR][USA].aims = first_strike_intent` moves the state toward the boundary with *no change in any hindsight force variable*; the shortest trace to `GENERAL_WAR` from the replay snapshot is shorter than from the hindsight snapshot | as stated | Jones 2016; the 1990 PFIAB report (declassified 2015) |
| C8 | 1963, 1972, 1987 | each verification regime raises `oversight`; holding forces constant, the distance to the boundary increases; with `oversight` frozen at 1962 levels, the 1987 to 1991 drawdown is unreachable within the horizon | as stated | the treaty texts; Hoffman 2009 |
| C9 | 1985 to 1991 | `CHALLENGER_EXHAUSTION` is reachable with zero relaxations; its minimal assumption set contains `econ_health` and `legit` and does *not* contain any United States action; whether United States actions were *sufficient* is `contested` | as stated | Kotkin 2001; Zubok 2007; Brown 2009; Miller 2016 |
| C10 | each year from 1965 | once both principals hold survivable second strike, further increases in `nuke` do not change kernel membership; `oversight` and `belief` do | the sensitivity report (Q7) ranks `nuke` below `oversight` and `belief` after 1965 and above them before | Schelling 1966; Kristensen and Norris series |
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
