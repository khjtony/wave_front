# The summer-1939 crisis sub-game: ontology (3-day ticks, 5 July to 3 September 1939)

Status: written by the historian after the claims K1 to K6 were registered (docs/crisis_1939_testbed.md, committed before any guard) and before any of them was run. K2 is the hold-out claim. Nothing here was chosen to make a registered claim pass; where a claim's wording and the record pull apart, the record is followed and the gap is stated in [crisis_1939_decisions.md](crisis_1939_decisions.md). Actions, Nature events, constraints and the parameter budget are in [actions_crisis_1939.md](actions_crisis_1939.md). Data: `data/ww2/crises/1939/events.csv` (dated level changes and confirming observations), `decisions.csv` (the one delayed decision), `realized_moves.csv` (the realized joint move of every tick). Model: `models/ww2/crises/summer_1939.py`.

Standards as in [ontology_ww2_v1.md](ontology_ww2_v1.md): every level is an observable condition with a stated threshold and a dated indicator; references name a document with its date; "(not verified)" marks a date or reference I recall but could not check against the document. Abbreviations: DBFP (Documents on British Foreign Policy 1919-1939, Third Series; vol. VI covers Jun to Aug 1939, vol. VII Aug to Sep 1939, with the record of the Moscow military talks in appendix II), DGFP (Documents on German Foreign Policy, Series D; vol. VI to 12 Aug 1939, vol. VII from 9 Aug 1939), DDF (Documents diplomatiques français, 2e série), NSR (Nazi-Soviet Relations 1939-1941, Department of State, 1948), Cmd. 6106 (the British Blue Book of Sep 1939, *Documents concerning German-Polish relations and the outbreak of hostilities*), CAB 23/100 (British Cabinet conclusions, Aug to Sep 1939).

## 0. Scope and time

- One tick is three days. Tick 0 is 5 to 7 July 1939; tick t covers the three days from 5 July + 3t; tick 20 is 3 September 1939 (the British and French declarations), the horizon and a terminal state. Sixty days, twenty decision ticks (0 to 19).
- The state at tick t is the start of its first day; the joint move at tick t is what each actor decided during those three days; effects are visible at t + 1. A dated decision falls in the tick containing its day. Two decisions of one actor in one tick: the realized file keeps the one the claims need and notes the other. A reaction to another actor's decision of the same tick appears one tick later where the reaction's guard reads that decision ([SQR], as in v0 and v1). Nature plays one event per tick ([NSL] where two fall together; none does on the realized path).
- Principals `GER`, `WEST` (Britain and France), `USSR`, and `Nature`, which carries Poland's decisions (Beck's answer on Soviet passage; the two mobilizations) and Italy's (Mussolini's letter of 25 August), as v1 carries Italy's. `JPN` takes no part. The sub-game has no hidden objective of its own: `aims_GER` and `aims_USSR` enter from the coarse state.
- Everything structural (armaments, regions, the China war, the coarse built-ins) is frozen at the entry values and not represented: the sub-game moves diplomacy, military conversations, orders and beliefs.

| Tick | Days | Tick | Days | Tick | Days |
|---|---|---|---|---|---|
| 0 | 5 to 7 Jul | 7 | 26 to 28 Jul | 14 | 16 to 18 Aug |
| 1 | 8 to 10 Jul | 8 | 29 to 31 Jul | 15 | 19 to 21 Aug |
| 2 | 11 to 13 Jul | 9 | 1 to 3 Aug | 16 | 22 to 24 Aug |
| 3 | 14 to 16 Jul | 10 | 4 to 6 Aug | 17 | 25 to 27 Aug |
| 4 | 17 to 19 Jul | 11 | 7 to 9 Aug | 18 | 28 to 30 Aug |
| 5 | 20 to 22 Jul | 12 | 10 to 12 Aug | 19 | 31 Aug to 2 Sep |
| 6 | 23 to 25 Jul | 13 | 13 to 15 Aug | 20 | 3 Sep (horizon) |

## 1. Hidden objectives (fixed by the entry map)

| Variable | Levels | Hidden from | Use in the sub-game |
|---|---|---|---|
| `aims_GER` | revisionist, hegemonic | WEST, USSR | v1's hypothesis gate [H] on the attack carries over: `attack_poland` has the part `hypothesis: aims_GER == hegemonic` (v1, after v0: the destruction of Poland as a step of the hegemonic programme, L-79 of 23 May 1939). Declared `init=None` so that the entry map must name it. |
| `aims_USSR` | defensive, opportunist | GER, WEST | Read by no guard of the sub-game (v1's `accept_pact` has no hypothesis gate either; v1 gates only Soviet aggression, which falls after the horizon). Carried so that the entry state names the hypothesis under which every result is computed; K6's "under `aims_USSR = defensive`" is this entry value. |

The entry state of every registered claim is v1's state at the start of 1939Q3 (`1939Q2.json` with its built-ins) under `aims_GER = hegemonic` and `aims_USSR = defensive`.

## 2. The negotiations

| Variable | Levels | Init (5 Jul) | Threshold rule | Dated indicator |
|---|---|---|---|---|
| `talks` | political, military, adjourned, broken | political | The Anglo-French-Soviet negotiation. **political**: talks on a treaty text without military staff conversations (the Soviet draft of 2 Jun 1939; the deadlock on "indirect aggression" in July). **military**: the military missions in session in Moscow with a mandate to negotiate a convention. **adjourned**: the military talks suspended by the Soviet side pending answers, with the missions still in Moscow. **broken**: the Soviet side has declared that the talks cannot continue. Declared without `monotone`, though no action lowers it. | political: the Soviet draft of 2 Jun and Molotov's statement of 17 Jul (DBFP vol. VI); military: the opening session of 12 Aug (DBFP vol. VII app. II); adjourned: Voroshilov, 17 Aug; broken: the adjournment sine die of 21 Aug and Voroshilov's statement to Doumenc of 22 Aug that the political situation had changed (Doumenc's report, not verified) |
| `passage` | unasked, asked, refused, granted | unasked | Polish consent to the passage of Soviet forces. **asked**: the Soviet side has made passage a condition of a convention. **refused**: the Polish government has answered no. **granted**: the Polish government has consented (never on the record). Monotone; an answer is final within the window. Beck's formula of 23 Aug ("collaboration is not excluded") is not consent and leaves `refused`; Daladier's assurance to Doumenc of 21 Aug that Poland agreed was not Poland's. | asked: Voroshilov's "cardinal question", 14 Aug (DBFP vol. VII app. II); refused: Beck to Noël, 19 Aug, and the Polish General Staff, 20 Aug (Kennard's telegrams, DBFP vol. VII; DDF vol. XVIII, not verified) |
| `west_powers` | flag | False | The Western delegations hold written authority to sign a military convention. | False: Voroshilov's request of 12 Aug for written powers, which Drax did not have (DBFP vol. VII app. II); True: Daladier's instruction to Doumenc of 21 Aug and the British delegation's written powers of 21 Aug (not verified) |
| `alliance` | flag | False (entry: `anglo_soviet_alliance`) | An Anglo-French-Soviet military convention concluded (the Soviet condition of 2 Jun and 17 Jul: the political and military agreements in force together, so the convention is the alliance). Monotone. Never on the record. | none |
| `german_approach` | none, opened, pact_proposed, pact | none (entry: `pact` if the coarse pact holds) | The German approach to Moscow. **none**: no German offer of a political settlement standing (the May contacts lapsed: Hitler stopped the economic talks in late June, not verified). **opened**: a German offer of a political settlement put to Soviet representatives. **pact_proposed**: a German proposal of a non-aggression pact with a settlement of spheres (what Molotov's "special protocol" of 17 Aug asked for) before the Soviet government. **pact**: the pact signed. Monotone. | opened: Schnurre with Astakhov and Barbarin, 26 Jul (NSR); pact_proposed: Ribbentrop's telegram of 14 Aug read to Molotov on 15 Aug and its sequel of 16 Aug (NSR); pact: signed in the night of 23 to 24 Aug (NSR; DGFP vol. VII) |

The alliance exists when `alliance` is True; the pact exists when `german_approach == pact` (testbed section 2).

## 3. Case White, the guarantee and belief

| Variable | Levels | Init (5 Jul) | Threshold rule | Dated indicator |
|---|---|---|---|---|
| `attack_order` | none, ordered, cancelled, launched | none (entry: `launched` if the coarse `poland` is not independent) | Case White. **none**: the plan and its date of readiness exist (C-120, 3 Apr) but no date of attack has been ordered. **ordered**: a day for the attack has been fixed by Hitler and transmitted to the army. **cancelled**: an order given and halted, the deployment kept. **launched**: German forces have crossed the Polish frontier. Not monotone (cancelled to ordered by a new order). | ordered: Y-day fixed on 23 Aug for 26 Aug (Halder's diary, 23 Aug; not verified) and the order of 25 Aug, 15:02; cancelled: the halt of 25 Aug, about 19:30 (Halder's diary 25 to 26 Aug; Ciano's diary 25 Aug); launched: 1 Sep, 04:45 (Directive No. 1 of 31 Aug) |
| `british_treaty` | none, guarantee, treaty | guarantee (entry: from `polish_guarantee`) | **guarantee**: the unilateral guarantee of 31 Mar 1939 in force. **treaty**: the Agreement of Mutual Assistance signed. Monotone. | guarantee: HC Deb 31 Mar 1939; the communiqué of 6 Apr announcing a permanent agreement; treaty: signed in London, 25 Aug 1939 (Cmd. 6106) |
| `belief_GER` | will_not_fight, uncertain, will_fight | uncertain (entry, from v1: `guarantee_poland` raised it, the conference of 23 May, L-79) | What Berlin (Hitler, who took the decisions) believes about British and French resolve. Rules as v0 and v1 (ontology_ww2.md section 3): **will_not_fight**: records in which Hitler, at a decision, states that the West will not fight; **uncertain**: German decision records that provide against Western intervention or record doubt about it; **will_fight**: records in which Berlin treats war with the West as the consequence of its next step. Monotone, as in v1. Raised in the sub-game by documented events: Chamberlain's letter (to at least uncertain), the treaty (to will_fight: the halt of 25 Aug, taken on the news of the treaty and Mussolini's letter, to gain time to detach Britain), the declarations (will_fight, applied on return). | uncertain: L-79 (23 May); the Obersalzberg address of 22 Aug (798-PS, 1014-PS: "our enemies are little worms") would put it at will_not_fight for a day and is **not modeled** (monotone; v1 made the same choice); will_fight: Halder's diary 25 to 26 Aug and Henderson's telegrams of 25 Aug (the offer to Britain); contested by Directive No. 1 of 31 Aug, which provides for both cases, and by Schmidt's postwar account of Hitler's "What now?" on 3 Sep |
| `war_declared` | flag | False (entry: `war_west_ger == war`) | Britain and France have declared war on Germany. Monotone. | 3 Sep 1939, 11:00 and 17:00 (CAB 23/100; HC Deb 3 Sep 1939) |

## 4. Poland and Italy (Nature's variables)

| Variable | Levels | Init (5 Jul) | Threshold rule | Dated indicator |
|---|---|---|---|---|
| `mobilization_POL` | none, partial, general | none | **partial**: reservists called up in some corps areas (the "alarm" mobilization). **general**: general mobilization proclaimed. Monotone. | partial: 23 to 24 Aug; general: ordered 29 Aug, suspended at the British and French request, proclaimed 30 Aug for 31 Aug (Kennard's telegrams, DBFP vol. VII) |
| `italy_ready` | unknown, not_ready | unknown | **not_ready**: Mussolini has told Hitler formally that Italy cannot go to war (Ciano's warnings at Salzburg, 11 to 13 Aug, do not meet the rule). Monotone. | Mussolini's letter of 25 Aug and the list of 26 Aug (DGFP vol. VII; Ciano's diary) |

Both are **inert**: no guard, effect on another variable, invariant, ending, fairness constraint or profile reads them. They record the Polish and Italian decisions the claims name (K1's sequence, K4's "documented reason") and their events occupy Nature's slot. `build(inert=False)` drops them and their three events; every question that does not mention them has the same answer on both builds (checked by a bisimulation test, tests/ww2/crisis_1939/test_model_crisis_1939.py).

## 5. Entry and exit (framework_spec.md section 14)

**Entry** (`entry(coarse_state_dict)`), from v1's state at the start of 1939Q3 (`1939Q2.json` with built-ins, tick 14): `aims_GER`, `aims_USSR`, `belief_GER` (uncertain), `british_treaty` (guarantee from `polish_guarantee`), `german_approach` (pact if `nazi_soviet_pact`, else none), `alliance` (from `anglo_soviet_alliance`), `war_declared` (from `war_west_ger`), `attack_order` (none while `poland == independent`, else launched), `talks` (political, or broken if the coarse pact holds). Everything else takes its declared initial value, the record's of 5 July. The army (`arms_GER == high` in the entry state) is frozen: v1's `army_ready` part holds throughout and is not represented; Case White's readiness part carries the date. WEST's approach to Moscow is standing in the sense of the testbed (the talks are under way); `last_WEST` in `1939Q2.json` is `guarantee_poland` (v1's 1939Q2 row), so the entry does not read it.

**Exit** (`exit(fine_state_dict, coarse_state_dict)`), on a terminal fine state with the entered-from coarse state, returns only the coarse variables the crisis changes: `poland := german` when the attack was launched; when WEST declared war, or when the obligation `polish_obligation` is due in the terminal state (attack launched, guarantee or treaty in force, no declaration yet; decisions C3), `war_west_ger := war`, `france := at_war`, `britain := at_war`, `commit_WEST := at_war` and `belief_GER := will_fight` (v1's `declare_war`); `nazi_soviet_pact := True` and `oil_GER := secured` with the pact (v1's `accept_pact`); `anglo_soviet_alliance := True` with the alliance; `belief_GER` as the sub-game left it otherwise. No exit lowers a monotone coarse variable. The coarse built-ins (`last_*`, delay counters) are updated by the coarse return transition (framework_spec.md section 14), not by the exit map.

## 6. Analysis predicates

- Invariants: `no_attack` (`attack_order != launched`), `no_pact` (`german_approach != pact`), `alliance_race` (`no pact, and the alliance concluded or the horizon not yet reached`: keeping it to the horizon is keeping the pact out and concluding the alliance by tick 20).
- Endings at the horizon: `ATTACK_LAUNCHED`, `NO_ATTACK` (mutually exclusive, covering every horizon state). `build(target=(name, expr))` replaces both by one target ending for relaxation searches (K5, K6).
- Scenarios (analysis devices, not the model): `build(passage="granted" | "refused")` keeps only that Nature answer to Voroshilov's question and makes Nature give it at the first tick the question is before Warsaw (fairness `scenario_passage`, within 1).

## 7. Not modeled, by decision

- The political treaty text (indirect aggression, the guaranteed states): the Soviet condition makes the military convention the alliance's form; the political deadlock is inside `talks == political`.
- Romania's consent (part of Voroshilov's question): only Poland's is on the record of the talks' end; Romania was never asked formally (not verified).
- The Danzig crisis as a separate variable, the Henderson-Ribbentrop exchanges of 28 to 31 Aug, the Dahlerus contacts and the Polish plenipotentiary demand: inside the German decision to attack and the belief rule.
- Mussolini's proposal of a conference (31 Aug to 2 Sep) and Italian non-belligerency (1 Sep): after the realized attack decision, no claim needs them.
- The Soviet occupation of eastern Poland (17 Sep): after the horizon; v1's USSR `occupy_east_poland` at tick 15 of v1.
- The dip of `belief_GER` to `will_not_fight` on 22 Aug (monotone variable, as v1).
- Japan (Nomonhan, the Japanese reaction to the pact): JPN is not a fine actor.
