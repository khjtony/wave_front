# Cold War v0 ontology: variables, levels, thresholds, endings

Status: written for the model step after the registration of C1 to C13 ([coldwar_testbed.md](coldwar_testbed.md), 2026-10-11) and of the transfer hypotheses ([transfer_hypotheses.md](transfer_hypotheses.md), 2026-10-12), before any registered claim was run. The actions, Nature events and delays are in [actions_cw.md](actions_cw.md); the architect's decisions and the readings of the claims in [cw_v0_decisions.md](cw_v0_decisions.md). Data: `data/cw/events.csv` (dated levels per variable), `data/cw/decisions.csv` (dated decisions with their delays), `data/cw/realized_moves.csv` (the realized joint move of every year), `data/cw/crises/*/realized_moves.csv`. Model: `models/cw/v0.py`, `models/cw/crises/`.

Standards as for the WW2 and July 1914 ontologies: every level is an observable condition with a threshold and a dated indicator; references name a document with its date or a book, never an invented page; "(not verified)" marks a date or a reading recalled but not checked against the document or the data set. The data hosts the testbed names (Correlates of War, the Kristensen and Norris series, Maddison, CIA CREST) are blocked from the development environment (data/cw/README.md), so no level here is read from a downloaded series: the thresholds are stated on the record of deployments, treaties and events, and the series are named as the cross-check to run when they can be reached.

## 0. Scope and time

- One tick is one calendar year; **the state at tick t is 1 January of 1947 + t**; the joint move at tick t is what was decided during that year; its effects are visible at t + 1. Tick 0 is 1 January 1947; the horizon, tick 45, is 1 January 1992.
- Year to tick: `tick = year - 1947`. 1948 = 1, 1950 = 3, 1953 = 6, 1957 = 10, 1961 = 14, 1962 = 15, 1963 = 16, 1965 = 18, 1969 = 22, 1972 = 25, 1975 = 28, 1979 = 32, 1983 = 36, 1985 = 38, 1987 = 40, 1989 = 42, 1991 = 44.
- Actors: `USA`, `USSR`, `PRC` (a principal from 1969), Nature (decisions D2).
- The registered sketch (testbed section 3) is followed where a claim reads a variable; departures are listed in section 11 with their reasons.

## 1. Hidden objective (swept, `init=None`, no `assume`)

| Variable | Levels | Hidden from | What each level encodes | Source for the hypothesis space |
|---|---|---|---|---|
| `aims_USSR` | status_quo, opportunist | USA, PRC | **status_quo**: security within the Soviet sphere and recognition of its gains; no risk of war with the United States for gain outside it. **opportunist**: probing where the cost looked low, retreat before counterforce. | status_quo: Westad 2017; Zubok, *A Failed Empire* (2007); Trachtenberg 1999. opportunist: Kennan, "The Sources of Soviet Conduct" (1947); Gaddis 1982 and 2005; Weathersby 1993 on Korea. |

Each hypothesis enters a guard as a part named `hypothesis` (decisions D3).

## 2. Strategic forces and intelligence

| Variable | Levels | Init | Threshold rule | Dated indicator |
|---|---|---|---|---|
| `nuke_USA` | none, few, survivable, overkill | few | Monotone. **few**: atomic weapons and the means to deliver them, vulnerable to a first strike. **survivable**: a force able to absorb a first strike and retaliate with unacceptable damage (McNamara's criterion: a fifth to a quarter of the population, half the industry): at sea or in hardened silos or on alert. **overkill**: a force several times the assured-destruction requirement, with counterforce options against the other's forces. | few: 13 weapons in mid-1947 (Rosenberg 1983). survivable: first Polaris patrol 15 Nov 1960, SAC alert; visible 1961. overkill: the Kennedy buildup in deployment, 800 Minuteman and 29 Polaris boats by 1965 (Ball 1980; Enthoven and Smith 1971); visible 1965. |
| `nuke_USSR` | as `nuke_USA` | none | Monotone. Same thresholds. | few: test of 29 Aug 1949 (Holloway 1994); visible 1950. survivable: the hardened SS-9 and SS-11 from 1966 (Podvig 2001; the year of a secure Soviet second strike not verified); visible 1967. overkill: the MIRVed SS-17, SS-18 and SS-19 from 1975 (Podvig 2001); visible 1976. Cross-check: the Kristensen and Norris inventories (BAS 2010), not reachable. |
| `intel_USA` | low, partial, overhead | low | Monotone. **partial**: overflights of the USSR. **overhead**: satellite photography of the Soviet strategic force. (The sketch's `verified_by_treaty` is `oversight`.) | partial: U-2 from 4 Jul 1956; visible 1957. overhead: CORONA from 18 Aug 1960; visible 1961. |

## 3. Beliefs

| Variable | Levels | Init | Threshold rule | Dated indicator (contemporaneous belief) |
|---|---|---|---|---|
| `belief_force_USA` | as `nuke_USSR` | none | Washington's estimate of the Soviet strategic force on `nuke_USSR`'s scale, read from the National Intelligence Estimates. A level is the estimate's force in being or within two years, whichever the estimate's text treats as the planning case. | few: the test of 1949 detected (Truman, 23 Sep 1949). survivable: NIE 11-10-57 (10 Dec 1957) and the Gaither report, the missile gap; visible 1958. few: NIE 11-8/1-61 (21 Sep 1961); visible 1962. survivable 1967 and overkill 1976 with the deployments seen by satellite. |
| `belief_USA_USSR` | status_quo, opportunist, expansionist | opportunist | Washington's reading of Soviet aims in its basic national security papers. **opportunist**: expansion by pressure where cheap. **expansionist**: a design of domination pursued by war if the balance allowed. **status_quo**: security-seeking. | opportunist: Kennan 1946 to 1947. expansionist: NSC-68 (Apr 1950, NSC 68/2 of 30 Sep 1950); visible 1951. opportunist: NSC 162/2 (30 Oct 1953); visible 1954. The Bush administration's reassessment of 1989 to 1990 is not placed ([NSL]; no claim reads the level after 1988). |
| `belief_USSR_USA` | status_quo, hostile, first_strike_intent | hostile | Moscow's reading of American aims. **hostile**: containment and pressure by means short of war. **first_strike_intent**: preparation of a disarming first strike. **status_quo**: no threat of attack. | hostile: Novikov's telegram of 27 Sep 1946. first_strike_intent: RYAN, from Andropov's KGB conference of May 1981 to the instructions of Feb 1983; visible 1983. hostile: Geneva, Nov 1985; visible 1986. status_quo: new thinking, the defensive doctrine of 29 May 1987; visible 1988. |

Hindsight truth (decisions D6): `belief_force_USA` is the record's `nuke_USSR`; `belief_USSR_USA` is `hostile` throughout (no American first-strike plan at any time; PFIAB 1990); `belief_USA_USSR` is the hypothesis's own level. The hindsight snapshots carry these, the replay snapshots the contemporaneous beliefs above.

## 4. Arms control and verification

| Variable | Levels | Init | Threshold rule | Dated indicator |
|---|---|---|---|---|
| `offer` | none, test_ban, limits, reductions | none | Monotone. The standing American offer: a treaty text or formal proposal on the table. | test_ban: the Western draft and Eisenhower's proposal of 13 Apr 1959; visible 1960. limits: Glassboro, Jun 1967; visible 1968. reductions: the zero option (18 Nov 1981) and START (9 May 1982); visible 1983 (one US decision per year). |
| `oversight` | none, test_ban, ntm, on_site | none | Monotone. The verification regime in force. **test_ban**: a treaty verified by national means without provisions (LTBT). **ntm**: non-interference with national technical means agreed (SALT I). **on_site**: on-site inspection (INF). | test_ban: LTBT signed 5 Aug 1963; visible 1964. ntm: 26 May 1972; visible 1973. on_site: 8 Dec 1987; visible 1988. |
| `arms` | race, capped, reduced | race | Monotone. **capped**: ceilings on strategic launchers (the Interim Agreement, the ABM Treaty). **reduced**: a treaty eliminating or reducing deployed systems (INF, START). | capped 1973; reduced 1988. |
| `buildup` | flag | False | Monotone. The Reagan buildup decided (strategic modernization, SDI). | Mar and 2 Oct 1981; visible 1982. |

## 5. Escalation between the principals

| Variable | Levels | Init | Threshold rule | Dated indicator |
|---|---|---|---|---|
| `esc` | peace, crisis, conventional, tactical_nuclear, strategic | peace | Not monotone; changes by `Bump` only (decisions D4). **crisis**: a standing confrontation between the principals carried across a 1 January (an ultimatum with a deadline, forces deployed against each other). **conventional**: combat between the principals' forces. **tactical_nuclear**, **strategic**: nuclear use. Crises inside a year are sub-games (section 10). | crisis 1959 to 1961: Khrushchev's ultimatum of 27 Nov 1958 to the Wall (13 Aug 1961). Peace otherwise on every 1 January. |
| `accidental` | flag | False | Monotone. Set by Nature's accident (and a crisis exit caused by one). | never. |
| `us_strike` | flag | False | Monotone. A US preventive strike taken (claim C12). | never. |
| `invasion_west` | flag | False | Monotone. A Soviet conventional offensive into Western Europe (claim C12). | never. |
| `us_began_war` | flag | False | Monotone. **Added 2026-10-23 on the owner's decision 2l.** A war between the principals begun by the United States (NATO): set by `USA.escalate` (combat opened from a standing crisis) and by the Cuba sub-game's war exit (only the United States opens fighting there); not set by the Berlin 1948 war exit, which does not record who opened the clash. The condition `nato_attack` of `USSR.nuclear_use` (the Warsaw Pact plans; Mastny and Byrne 2005). | never. |
| `berlin_wall` | flag | False | Monotone. The sector border sealed. | 13 Aug 1961; visible 1962. |

"Commit = total" (testbed section 3 sketch, claim C5) is folded into `esc`: the record makes total commitment the condition of US nuclear use, and the only commitment the record treats as total is a direct war with the USSR, so `USA.nuclear_korea` has the part `total_commitment: esc >= conventional` (decisions, actions catalogue).

## 6. Peripheral wars

| Variable | Levels | Init | Threshold rule | Dated indicator |
|---|---|---|---|---|
| `korea` | peace, war, armistice | peace | Monotone. | war 25 Jun 1950 (visible 1951); armistice 27 Jul 1953 (visible 1954). |
| `afghan` | none, war, withdrawn | none | Monotone. **withdrawn**: withdrawal agreed and under way. | war Dec 1979 (visible 1980); withdrawn: Geneva Accords 14 Apr 1988, withdrawal from 15 May 1988 (visible 1989). |

## 7. The Soviet economy, polity and bloc

| Variable | Levels | Init | Threshold rule | Dated indicator |
|---|---|---|---|---|
| `econ_USSR` | growing, stagnant, declining, failing | growing | Monotone. Five-year average growth of output on the post-1991 revisions: **growing** ≥ 3 percent; **stagnant** 0 to 3 percent; **declining** near or below zero with external shocks; **failing**: falling output with fiscal and supply collapse. The contemporaneous CIA estimates are belief data, not this variable. | stagnant from the mid-1970s (Easterly and Fischer 1995; the dating not verified against Maddison or Khanin), visible 1976; declining with the oil collapse of 1986 (Gaidar 2007), visible 1987; failing 1990 to 1991 (Miller 2016), visible 1992 ([NSL]). |
| `legit_USSR` | secure, contested, failing | secure | Monotone. **contested**: open challenge to the party's authority (glasnost, national movements). **failing**: the party's monopoly gone and the centre's authority rejected by republics. | contested 1987 (glasnost; Alma-Ata, Dec 1986); failing 1991 (Article 6 repealed, Lithuania 11 Mar 1990, Russian sovereignty 12 Jun 1990). |
| `perestroika` | flag | False | Monotone. Gorbachev's reform programme under way. | 1986 (27th Congress; Law on Individual Labour Activity); visible 1987. |
| `bloc_USSR` | intact, contested, released, dissolved | intact | Not monotone. **contested**: an opposition holding its ground in an East European state across a 1 January. An uprising suppressed within the year (East Berlin 1953, Hungary 1956, Czechoslovakia 1968) is below the threshold. **released**: the communist governments gone without Soviet intervention. **dissolved**: the Warsaw Pact and the USSR dissolved. | contested 1981 (Solidarity), intact 1982 (martial law), contested 1989 (Poland and Hungary 1988), released 1990, dissolved 1992. |

## 8. The PRC

| Variable | Levels | Init | Threshold rule | Dated indicator |
|---|---|---|---|---|
| `align_PRC` | soviet_ally, split, us_aligned | soviet_ally | Monotone. **split**: Soviet aid withdrawn and open polemics. **us_aligned**: a public understanding with the United States against Soviet hegemony. | split 1960 (visible 1961); us_aligned: the Shanghai Communique, 28 Feb 1972 (visible 1973). |
| `china_opening` | flag | False | Monotone. The American opening made. | Jul 1971; visible 1972. |
| `esc_sino` | peace, clash, war | peace | Not monotone; `Bump` only. **clash**: armed confrontation on the border. **war**: a Soviet strike on China. | clash from Mar 1969 (visible 1970) to the normalization of May 1989 (peace, visible 1990). |

## 9. Invariants and endings

| Name | Kind | Definition |
|---|---|---|
| `balance_cw` | invariant | (both principals at `survivable` or above, or neither) ∧ `no_war` ∧ `bloc_intact` (testbed section 4) |
| `no_war` | invariant | `esc < conventional`, and, when the PRC is a principal, `esc_sino < war` |
| `no_general_war` | invariant | not `general_war` |
| `bloc_intact` | invariant | `bloc_USSR ≤ contested` (NATO held intact, decisions D2) |
| `GENERAL_WAR` | ending, any tick | `general_war` ∧ ¬`accidental`; `general_war` is `esc ≥ tactical_nuclear` or, with the PRC a principal, `esc_sino = war` |
| `ACCIDENTAL_WAR` | ending, any tick | `general_war` ∧ `accidental` |
| `CHALLENGER_EXHAUSTION` | ending, any tick | `econ_USSR = failing` ∧ `legit_USSR = failing` ∧ `bloc_USSR = dissolved` ∧ ¬`general_war` (the realized ending, at the horizon) |
| `NEGOTIATED_SETTLEMENT` | ending, at tick 45 | `balance_cw` ∧ `arms = reduced` |
| `DETERRENCE_HOLDS` | ending, at tick 45 | `balance_cw` ∧ `arms ≠ reduced` |
| `HORIZON` | built-in | tick 45 with none of the above (the balance broken without war or exhaustion) |

`LIMITED_WAR` is not an ending (decisions D8). The endings are mutually exclusive by construction.

## 10. Crisis sub-games

### 10.1 Berlin 1948 (`models/cw/crises/berlin_1948.py`; weekly; tick 0 the week of 24 Jun 1948; horizon 47)

| Variable | Levels | Rule |
|---|---|---|
| `airlift` | none, improvised, sustained | **sustained**: carrying the winter minimum (about 5,000 tons a day) from Jan 1949 (Miller 2000) |
| `talks` | none, demands, concession, agreed | Stalin's terms of Aug 1948 (demands), the concession of 30 Jan 1949, the agreement of 4 May 1949 |
| `conceded` | flag | the terms of Aug 1948 accepted by the West (not taken) |
| `access` | blockaded, lifted | lifted 12 May 1949 |
| `esc_b` | standoff, clash, war | an armed incident on the access routes (clash), combat (war) |
| `position` | in_berlin, withdrawn | the Western garrisons withdrawn (not taken) |

Endings: `SETTLED` (lifted by agreement), `TERMS` (lifted on Soviet terms), `WITHDRAWAL`, `WAR`.

### 10.2 Cuba 1962 (`models/cw/crises/cuba_1962.py`; daily; tick 0 is 16 Oct 1962; horizon 14)

| Variable | Levels | Rule |
|---|---|---|
| `missiles` | building, operational, withdrawn | operational: the CIA's reports of 26 to 27 Oct; withdrawn: the decision of 28 Oct |
| `us_move` | deliberating, quarantine, strike, invasion | the quarantine announced 22 Oct |
| `ships` | en_route, stopped, challenged | stopped 24 Oct |
| `tension` | crisis, alert, clash | DEFCON 2 on 24 Oct (alert); the U-2 shot down 27 Oct (clash) |
| `deal` | none, pledge, trade | the non-invasion pledge; the pledge with the Jupiter assurance (27 Oct) |
| `fighting`, `nuclear`, `accident` | flags | combat; nuclear use; nuclear use by accident |

Endings: `WITHDRAWAL`, `WAR`, `NUCLEAR`.

### 10.3 Able Archer 1983 (`models/cw/crises/able_archer_1983.py`; daily; tick 0 is 7 Nov 1983; horizon 6)

| Variable | Levels | Rule |
|---|---|---|
| `belief` | status_quo, hostile, first_strike_intent | the coarse `belief_USSR_USA` at entry |
| `exercise` | running, release, ended | the simulated general release of 9 to 10 Nov; the end on 11 Nov |
| `warning` | flag | the flash reports of 8 or 9 Nov |
| `pact` | normal, readied | the 4th Air Army's aircraft readied, 8 to 11 Nov |
| `us_alert` | normal, raised | not raised (Perroots) |
| `strike`, `accident` | flags | a Soviet strike; by accident |

Ending: `STRIKE`.

## 11. Departures from the sketch, and what is not modeled

| Item | Why |
|---|---|
| `conv`, `ind` per principal | No claim reads them; the conventional balance enters as guard parts (`USSR.invade_west:no_us_nuclear`), staying power as `econ_USSR`. |
| `econ_health`, `legit` for the United States | Never below growing or secure in the record; no claim reads them. |
| `commit` | Folded into `esc` (section 5). |
| `aims` of the United States; `hegemonic` for the USSR | No claim needs them (decisions D3). |
| `treaty` set | Read through `oversight`, `arms` and `offer`; the NPT (1968), SALT II (1979, unratified) and the Helsinki Final Act are not represented. |
| `intel` of the USSR | No claim reads it. |
| The UK, France and the PRC as nuclear actors | cw_v1 (testbed section 2). |
| Vietnam, the Middle East wars, the Taiwan Strait crises, the 1973 alert | No claim reads them at annual resolution; the 1973 alert is a crisis of days inside one year. |
| Hungary 1956, Czechoslovakia 1968 | Below the threshold of `bloc_USSR` (suppressed within the year); they are the record behind `USSR.intervene`. |
| The August coup of 1991, Yeltsin, the republics | Inside `legit_USSR = failing` and `USSR.dissolve`. |
