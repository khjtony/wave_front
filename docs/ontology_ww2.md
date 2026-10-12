# WW2 v0 ontology: Europe, 1936Q1 to 1940Q4

Status: skeleton fixed by the architect (variables, levels, actors, endings). The historian-facing content (threshold rules with sources, the hindsight indicator each level is read from, and the notes) is filled in phase 1 step 1.1 and reviewed by the historian before any guard is written against it. Read [ww2_testbed.md](ww2_testbed.md) section 7 first: tests T1 to T13 are already registered; this document and [actions_ww2.md](actions_ww2.md) are written without editing them.

Principle for every variable: a level is an *observable* condition with a stated threshold and a named indicator, never a judgment made with knowledge of what came later. Where a level can only be read from documents (beliefs, commitment), the indicator is the dated document class (Cabinet minutes, Hansard, FRUS) and the rule says what wording or decision marks the threshold.

## 0. Scope and time

- Tick: one quarter. Tick 0 = 1936Q1, tick 19 = 1940Q4, horizon 20 (tick 20 = 1941Q1, terminal).
- Theatre: Europe. The Pacific, Barbarossa and the United States as a belligerent are out of scope for v0 (phase 2).
- Principals: `GER` (Germany), `USSR`, `WEST` (the United Kingdom and France acting jointly, with the United States carried as a commitment variable), `JPN` (Japan, a small action set that exists for the Far-East constraint on the USSR and for the registered negative controls). `Nature` carries Italy, Spain, Poland, the smaller states, elections, campaign resolution and intelligence.

## 1. Hidden objectives (swept)

| Variable | Levels | Hidden from | Hypothesis each level encodes | Source for the hypothesis space |
|---|---|---|---|---|
| `aims_GER` | revisionist, hegemonic | WEST, USSR, JPN | revisionist: revise Versailles (Rhineland, Austria, Sudetenland, Danzig) and stop; hegemonic: continental hegemony including France and the East | the Taylor (1961) reading against Weinberg (1994) and Kershaw; the Hossbach memorandum (Nov 1937) as the contemporaneous statement of the hegemonic case |
| `aims_USSR` | defensive, opportunist | GER, WEST, JPN | defensive: security and buffer; opportunist: territorial gain where offered (the Nov 1940 Berlin talks) | to be filled |

Default restriction: `assume("ussr_defensive", aims_USSR == defensive)`, relaxable (T10's "USSR joins the Axis needs at most one relaxation").

## 2. Capability and resources

| Variable | Levels | Init 1936Q1 | Threshold rule (to be sourced) | Hindsight indicator |
|---|---|---|---|---|
| `arms_GER` | low, rising, high, total | rising | rising: conscription in force and milex rising (1935 on); high: field army able to sustain a major campaign (the 1939 force); total: full war economy (not reached before 1941 in v0) | COW NMC `milex`, `milper` for Germany by year; Tooze 2006 chapters on rearmament |
| `arms_WEST` | low, rising, high | low | rising: the UK Defence Requirements programme funded (1936 on) and French rearmament law; high: the 1939 to 1940 mobilized force | NMC `milex`, `milper` for UK and France |
| `arms_USSR` | weak, strong | strong | weak: the officer corps purged (1937 to 1938); strong otherwise | NMC `milper`; the purge dates |
| `arms_JPN` | high | high | fixed in v0 (engaged in China from 1937) | NMC |
| `ind_GER` | 3, 4, 5 | 3 | +1 with Austria, +1 with Bohemia (the Škoda and Brno works) | NMC `irst`; Tooze on the Czech acquisitions |
| `oil_GER` | dependent, secured | dependent | secured: Soviet deliveries under the 1939 to 1940 agreements or Romanian oil under German alignment | Tooze 2006; the Minerals Yearbook |

`ind` for the other principals is constant in v0 and is not a state variable.

## 3. Beliefs and commitment

| Variable | Levels | Init | Threshold rule (to be sourced) | Hindsight indicator |
|---|---|---|---|---|
| `belief_WEST` | limited, uncertain, hegemonic | limited | what London and Paris believe Berlin wants; hegemonic once a non-German-speaking territory is taken (Prague, March 1939) | CAB 23 minutes; Hansard; the Chamberlain Birmingham speech, 17 March 1939 |
| `belief_GER` | will_not_fight, uncertain, will_fight | will_not_fight | what Berlin believes about British and French resolve | the Führer conferences (May and August 1939); DGFP |
| `commit_WEST` | appease, wary, resolved, at_war | appease | wary: rearmament accepted as policy; resolved: a guarantee or conscription (UK conscription April 1939); at_war | Hansard; conscription; the guarantee |
| `commit_US` | isolationist, wary, engaged | isolationist | wary: cash-and-carry (Nov 1939); engaged: the destroyers deal (Sept 1940) and lend-lease (March 1941, out of v0) | the Neutrality Acts and their revisions; FRUS |

## 4. Structure

| Variable | Levels | Init | Note |
|---|---|---|---|
| `treaty` | enforced, eroded, dead | eroded | the Versailles and Locarno regime; dead after the Rhineland |
| `axis` | flag | False | the Rome-Berlin alignment (Oct 1936; the Pact of Steel May 1939) |
| `anticomintern` | flag | False | Germany-Japan (Nov 1936) |
| `nazi_soviet_pact` | flag | False | Aug 1939 |
| `polish_guarantee` | flag | False | 31 March 1939 |
| `anglo_soviet_alliance` | flag | False | the 1939 talks failed; True only in 1941 |
| `ussr_axis` | flag | False | the negative-control outcome of the Nov 1940 talks |
| `italy_estranged` | flag | True | Italy estranged from the West after Ethiopia (1935 to 1936); a Nature precondition for `axis` |

## 5. Regions (monotone unless noted)

| Variable | Levels | Init | Note |
|---|---|---|---|
| `rhineland` | demilitarized, remilitarized | demilitarized | not monotone: `withdraw_rhineland` exists (the documented March 1936 contingency) |
| `austria` | independent, annexed | independent | |
| `sudeten` | czech, german | czech | |
| `bohemia` | czech, german | czech | |
| `poland` | independent, partitioned, german | independent | partitioned: the Sept 1939 outcome with the Soviet share |
| `france` | independent, at_war, fallen | independent | |
| `britain` | at_peace, at_war, negotiated, invaded | at_peace | negotiated and invaded are endings |
| `balkans` | neutral, german_aligned | neutral | Romania, Hungary, Bulgaria (1940); carries `oil_GER` |
| `siberia` | soviet, japanese | soviet | exists for the negative control "Japan conquers the USSR" |
| `channel_air` | contested, german, british | contested | resolved by Nature during an air offensive; `invade_britain` needs `german` |
| `war_west_ger` | peace, war | peace | |

Latches: `belief_at_munich` (`belief_WEST` when `sudeten` first becomes german); `arms_at_war` (`arms_GER` when `war_west_ger` first becomes war). `GER` and `WEST` are declared with `remember_last=True`.

## 6. Balance, kernels, endings

```
balance_europe := german_regions < 5
               ∧ france != fallen
               ∧ britain in {at_peace, at_war}
               ∧ (treaty != dead ∨ polish_guarantee ∨ anglo_soviet_alliance ∨ war_west_ger == war)
german_regions := [rhineland == remilitarized] + [austria == annexed] + [sudeten == german]
               + [bohemia == german] + [poland != independent] + [france == fallen]
               + [britain in {negotiated, invaded}] + [balkans == german_aligned]
```

The last clause reads "the treaty regime is alive, or an anti-hegemonic commitment has replaced it".

Endings (mutually exclusive on every state; the horizon cases are decided in this order):

| Ending | Definition |
|---|---|
| `NEGOTIATED_PEACE` | `britain == negotiated` |
| `AXIS_HEGEMONY_EUROPE` | `britain == invaded` |
| `JPN_CONQUERS_USSR` | `siberia == japanese` (negative control) |
| `USSR_JOINS_AXIS` | `ussr_axis` (negative control, at most one relaxation) |
| `NO_GENERAL_WAR` | at the horizon: `war_west_ger == peace ∧ poland == independent` |
| `LIMITED_WAR` | at the horizon: `war_west_ger == peace ∧ poland != independent` |
| `STATIC_FRONT` | at the horizon: `war_west_ger == war ∧ france == at_war` (the phoney war never ended) |
| `BRITAIN_ALONE` | at the horizon: `war_west_ger == war ∧ france == fallen ∧ britain == at_war` (the realized 1940Q4 state) |
| `WAR_UNRESOLVED` | at the horizon: any other case with `war_west_ger == war` |

`ALLIED_VICTORY` cannot occur before 1941 and is not an ending of v0; the negative control "Britain alone defeats Germany by 1941" is the unreachability of a German collapse within the horizon.

## 7. Not modeled in v0, by decision

Spain (1936 to 1939) except as a Nature effect on `italy_estranged`; Ethiopia (already in `italy_estranged`); the Scandinavian campaign (April 1940); the Soviet-Finnish war; Nomonhan (1939) except as the constraint behind `strike_north`; the Low Countries separately from France; the Mediterranean. Each is a candidate for v1 and is listed so that a missing path is attributed to a decision, not an oversight.

## 8. Historian's review checklist (step 1.1)

- [ ] every threshold rule names its indicator and a page or document reference
- [ ] every 1936Q1 initial level is defended from a dated source
- [ ] the hidden-objective hypothesis spaces cite the historiographical readings they encode
- [ ] section 7 is complete: nothing relevant to T1, T2, T4, T5, T8 or T10 is missing
