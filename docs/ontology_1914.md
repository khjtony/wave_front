# July 1914 v0 ontology: variables, levels, thresholds, endings

Status: written for the model step after the registration of J1 to J7 ([july1914_testbed.md](july1914_testbed.md), committed in 7e533d4 before any guard) and before any claim was run. The actions, Nature events, constraints, delays and the parameter budget are in [actions_1914.md](actions_1914.md); the architect's decisions and the settled readings of the claims in [july1914_decisions.md](july1914_decisions.md). Data: `data/july1914/events.csv` (dated structural events per variable), `data/july1914/decisions.csv` (dated decisions with their delays), `data/july1914/realized_moves.csv` (the realized joint move of every day). Model: `models/july1914/v0.py`.

Standards as for the WW2 ontologies: every level is an observable condition with a threshold and a dated indicator; references name a document with its date or a book, never an invented page; "(not verified)" marks a date or reference recalled but not checked against the document. Abbreviations: Geiss (Geiss (ed.), *July 1914: The Outbreak of the First World War, Selected Documents*, 1967), Kautsky (the German documents, *Die deutschen Dokumente zum Kriegsausbruch*, 1919), BD XI (*British Documents on the Origins of the War*, vol. XI), DDF (*Documents diplomatiques français*, 3e série, vols. X and XI), Albertini (*The Origins of the War of 1914*, 1952 to 1957), Clark (*The Sleepwalkers*, 2012), Lieven (*Towards the Flame*, 2015), Mombauer (*Helmuth von Moltke and the Origins of the First World War*, 2001), Otte (*July Crisis*, 2014).

## 0. Scope and time

- One tick is one day. **The state at tick t is the start of day t**; tick 0 is Sunday 28 June 1914 (Sarajevo). The joint move at tick t is what each actor decided during day t; a decision taken after midnight counts on its day (Bethmann's telegrams of 30 July 02:55 are on 30 July, tick 32). Its effects are visible at t + 1.
- Tick 37 is 4 August 1914, the last day of decisions. The DSL horizon is **38**: the state after 4 August (the British ultimatum expired at 23:00 London time, midnight in Berlin). The testbed's "tick 37 is 4 August, the horizon" is read this way (decisions D1): with a horizon of 37 the decisions of 4 August, which the testbed's own record dates to that day, could not be played.
- Day to tick: `tick = (date - 28 June 1914).days`. 5 July = 7, 7 July = 9, 14 July = 16, 15 July = 17, 19 July = 21, 23 July = 25, 24 July = 26, 25 July = 27, 28 July = 30, 29 July = 31, 30 July = 32, 31 July = 33, 1 August = 34, 2 August = 35, 3 August = 36, 4 August = 37.
- [SQR]: a reaction to another actor's decision of the same day appears the next day. [NSL]: Nature plays one event per tick. On the realized path neither marker is needed (actions_1914.md, conventions; reports/july1914.md section 3).

## 1. Hidden objectives (swept, `init=None`, no `assume`)

| Variable | Levels | Hidden from | What each level encodes | Source for the hypothesis space |
|---|---|---|---|---|
| `aims_GER` | localize, continental | AUH, RUS, FRA, GBR | **localize**: Berlin sought a localized Austro-Serbian war and accepted the risk of a continental war only as a consequence of Russian action (the "calculated risk"); Germany takes no general measure before Russia orders general mobilization. **continental**: Berlin accepted, or sought, a continental war to break the encirclement while Russia's rearmament was incomplete; the Russian partial measures suffice for German measures. | localize: Bethmann's reasoning as reported in Riezler's diary, 7 to 14 Jul 1914 (contested edition); Clark, chapters 7 and 9. continental: Fischer, *Griff nach der Weltmacht* (1961) and *Krieg der Illusionen* (1969); Moltke's remarks to Conrad at Karlsbad, May 1914, and to Jagow, as reported by Jagow (postwar, not verified); Falkenhayn's demand of 29 Jul for the Kriegsgefahrzustand (Mombauer). |
| `aims_RUS` | deter, fight | AUH, GER | **deter**: the Russian measures of 24 to 29 July were signals meant to deter Austria-Hungary and Germany; general mobilization only in answer to a German or Austro-Hungarian general measure. **fight**: the measures prepared a war Russia accepted over Serbia; general mobilization once the preparatory period was in force. | deter: Lieven, chapter on July 1914; Sazonov's statements of 24 to 30 Jul (Orange Book). fight: McMeekin, *The Russian Origins of the First World War* (2011); the period preparatory to war as secret mobilization (Dobrorolsky's memoir, 1922, postwar). |

The four pairs are swept; the report gives every result per pair. Each hypothesis enters exactly one guard as a part named `hypothesis` (actions_1914.md): `GER.kriegsgefahr` and `RUS.mobilize_general`. The realized sequence reaches the horizon only under `aims_RUS = fight` (Russia ordered general mobilization on 30 July before any German or Austro-Hungarian general measure), under both German aims; that is a property of the definitions, stated as in the WW2 ontology for the most expansive hypothesis.

## 2. The Austro-Serbian crisis

| Variable | Levels | Init | Threshold rule | Dated indicator |
|---|---|---|---|---|
| `blank_cheque` | flag | False | Monotone. True from the German assurance that Germany would stand by Austria-Hungary in action against Serbia, whatever Russia did. | Wilhelm II to Szögyény at Potsdam, 5 Jul; Bethmann and Zimmermann to Szögyény and Hoyos, 6 Jul (Szögyény's telegrams, Geiss). Visible at tick 8. |
| `ultimatum` | none, resolved, delivered, rejected | none | Monotone. **resolved**: the Common Ministerial Council has decided on demands to Serbia (7 Jul). **delivered**: the note is in Belgrade with its 48-hour limit (23 Jul 18:00). **rejected**: the reply has been judged unsatisfactory and relations broken (25 Jul 17:55 to 18:30). The decision of 19 July with its delivery date is the pending counter `pending_AUH_ultimatum`, not a level. | Council minutes of 7 and 19 Jul; the Austrian Red Book; Giesl's report of 25 Jul. |
| `halt_in_belgrade` | none, proposed, accepted | none | Monotone. **proposed**: Berlin has put to Vienna a halt after the occupation of Belgrade as a pledge (the Kaiser's note of 28 Jul morning, transmitted by Bethmann at 22:15 in weakened form, pressed again on 30 Jul at 02:55 and 03:00). **accepted**: Vienna has accepted it (never). | Kautsky; Geiss; the Common Ministerial Council of 31 Jul (declined). |
| `war_AUH_SER` | peace, war | peace | Monotone. **war**: declared (28 Jul, about 11:00). | Berchtold's telegram of 28 Jul; Belgrade shelled in the night of 28 to 29 Jul. |

## 3. Mobilization orders

A level is the **order in force**, not the mobilization's progress: the testbed dates every level by its order. Mobilization days (the first day of mobilization) are given for reference only. Nothing lowers a mobilization level except Russia's documented revocation before general mobilization (actions_1914.md, `RUS.revoke`).

| Variable | Levels | Init | Threshold rule | Dated indicator |
|---|---|---|---|---|
| `mob_AUH` | none, partial, general | none | Monotone. **partial**: the mobilization against Serbia (Plan B, eight corps) ordered (25 Jul evening; first day 28 Jul). **general**: general mobilization ordered (signed 31 Jul 12:23; first day 4 Aug). | Albertini vol. II; Mombauer. |
| `mob_RUS` | none, pre_mobilization, partial, general | none | Not monotone (`revoke`). **pre_mobilization**: the "period preparatory to war" in force (decided 25 Jul at Krasnoe Selo, in force 26 Jul). **partial**: partial mobilization of the Kiev, Odessa, Moscow and Kazan districts ordered (announced 29 Jul, ordered in the night of 29 to 30 Jul). **general**: general mobilization ordered (30 Jul about 17:00; first day 31 Jul). | Lieven; Albertini vol. II; Orange Book. |
| `mob_GER` | none, kriegsgefahr, general | none | Monotone. **kriegsgefahr**: the "state of imminent danger of war" proclaimed (31 Jul 13:00). **general**: mobilization ordered (1 Aug about 17:00; first day 2 Aug). | Kautsky; Mombauer. |
| `mob_FRA` | none, covering_troops, general | none | Monotone. **covering_troops**: the frontier covering troops ordered into position without reservists, with the ten-kilometre withdrawal (30 Jul). **general**: general mobilization ordered (1 Aug, posted 15:45 to 16:00; first day 2 Aug). | DDF vol. XI; French Yellow Book. |

"Great-power mobilization" (the endings and the invariant `localized`) means a mobilization order that calls up reservists: `mob_AUH == general` (the partial mobilization against Serbia is the localized war's own), `mob_RUS >= partial`, `mob_GER == general`, `mob_FRA == general`. The preparatory measures (Russia's period preparatory to war, the German Kriegsgefahrzustand, the French covering troops without reservists) are not mobilizations. Stated because the testbed's "no great-power mobilization" does not say where the line falls.

## 4. The great-power wars and Belgium

| Variable | Levels | Init | Threshold rule | Dated indicator |
|---|---|---|---|---|
| `war_GER_RUS` | peace, war | peace | Monotone. **war**: Germany's declaration handed over (1 Aug about 19:00). | Kautsky; Pourtalès's report. |
| `war_GER_FRA` | peace, war | peace | Monotone. **war**: Germany's declaration handed over (3 Aug 18:45). | Kautsky; Yellow Book. |
| `war_GBR_GER` | (folded) | | Not a separate state variable: the expression `commitment_GBR == war`. The British ultimatum of 4 August expired at 23:00 the same day, with no decision between the ultimatum and the state of war, so the two variables of the testbed coincide on every reachable state (decisions D6). | BD XI. |
| `belgium` | neutral, demanded, invaded | neutral | Monotone. **demanded**: the German note demanding passage delivered (2 Aug 19:00, 12-hour limit). **invaded**: German troops across the frontier (4 Aug about 08:00). The Belgian refusal (3 Aug 07:00) has no level of its own: the plan's entry followed whatever the answer, and the refusal is inside Nature's `invade_belgium` (decisions D6). | Geiss; Albertini vol. III. |

## 5. Britain and Berlin's reading of Britain

| Variable | Levels | Init | Threshold rule | Dated indicator |
|---|---|---|---|---|
| `commitment_GBR` | none, naval_assurance, belgian_guarantee, war | none | Monotone. **none**: the Cabinet refuses any commitment (24, 27, 29 Jul; 1 Aug); keeping the First Fleet together (26 Jul) is an Admiralty measure inside `none`. **naval_assurance**: the assurance to France that the fleet would protect the French coasts against a German fleet in the Channel (Cabinet of 2 Aug morning; Grey to Cambon that afternoon). **belgian_guarantee**: the Cabinet's resolution that a substantial violation of Belgium would compel action (2 Aug evening), made public in Grey's statement (3 Aug). **war**: the ultimatum to Germany sent (4 Aug), war from its expiry at 23:00. | BD XI; Hansard, 3 Aug; Asquith's letters to Venetia Stanley (Brock (ed.), 1982). |
| `belief_GER_GBR` | stays_out, uncertain, fights | stays_out | Not monotone. Berlin's (the Chancellor's and the Kaiser's) reading of Britain. **stays_out**: the working assumption that Britain would not enter a continental war started in the East: the Kaiser's statements of 5 to 6 Jul and Jagow's of mid-July (Geiss; not verified for Jagow's exact date). **uncertain**: no settled reading. **fights**: Berlin reads Britain as entering a war in which France is engaged. Raised by Lichnowsky's telegram of 29 Jul (Grey's warning; `fights`); set to `uncertain` by the misread telegram of 1 Aug (the reported offer of neutrality, believed from about 17:00 and corrected by George V's telegram the same night; the day's net reading); raised by Grey's statement of 3 Aug and by the ultimatum of 4 Aug (`fights`). | Kautsky; Geiss; Mombauer for 1 Aug. |

`belief_GER_GBR` is read by no guard, fairness constraint or profile (decisions D5; the feasibility principle). It is the record of Berlin's reading against which claim J4 measures the lag of the institutional response.

## 6. Invariants and endings

| Name | Kind | Definition |
|---|---|---|
| `no_war_GER_RUS` | invariant (J2, J4) | `war_GER_RUS == peace` |
| `localized` | invariant (J3, J7) | no great-power war (`war_GER_RUS`, `war_GER_FRA` peace, `commitment_GBR != war`) and no great-power mobilization (section 3) |
| `GENERAL_WAR` | ending, any tick | `commitment_GBR == war` (Britain in); terminal when it first holds |
| `CONTINENTAL_WAR` | ending, at tick 38 | a great-power war without Britain |
| `LOCALIZED` | ending, at tick 38 | `war_AUH_SER == war`, no great-power war, no great-power mobilization |
| `NO_WAR` | ending, at tick 38 | `war_AUH_SER == peace` and no great-power war |
| `HORIZON` | (built-in) | tick 38 with none of the above: an Austro-Serbian war with great-power mobilizations but no great-power war |

The endings are mutually exclusive by construction. Only `GENERAL_WAR` can end the game before the horizon, which it cannot in fact do earlier than its realized date on the realized path.

## 7. Not modeled

| Item | Why |
|---|---|
| Serbia as a principal; Serbia's mobilization (25 Jul 15:00) | Serbia's reply is Nature's (the testbed's actor list); its mobilization changes no claim. |
| Italy's neutrality (2 Aug), Luxembourg (2 Aug), Montenegro, Romania, the Ottoman alliance (2 Aug) | No registered claim reads them. |
| The Willy-Nicky telegrams (29 Jul to 1 Aug) | Inside the Tsar's revocation (`RUS.revoke`) and the 1 Aug demand to deploy east (`GER.mobilize_east`). |
| Grey's mediation proposals (24, 26, 27, 29 Jul) and the German refusals to press them | Proposals without a state effect; the Halt in Belgrade is the one mediation formula with a variable. |
| The Austro-Hungarian declaration on Russia (6 Aug), the British declaration on Austria-Hungary (12 Aug) | After the horizon. |
| The pre-mobilization measures of 26 to 29 Jul in Germany and France (officers recalled from leave, troops from Morocco) | Below the thresholds of section 3. |
| Domestic opinion (the SPD, the Liberal majority, the Russian press) | Inside the guards where the record makes it a constraint (`GBR.ultimatum_GER:parliament`); otherwise not represented. |

## 8. v1 additions (2026-10-24)

Written for the v1 model step (`models/july1914/v1.py`) after the v1 registration ([july1914_testbed.md](july1914_testbed.md) section 8) and before any of J1v1 to J9v1 was run; decisions in [july1914_v1_decisions.md](july1914_v1_decisions.md). Sections 0 to 7 hold for v1 unchanged except as below; v0 does not have this variable.

| Variable | Levels | Init | Threshold rule | Dated indicator |
|---|---|---|---|---|
| `tisza` (v1) | opposed, consented | opposed | Monotone. **opposed**: the Hungarian premier withholds his consent to an ultimatum to Serbia (his memorandum to Franz Joseph of 1 Jul against using the assassination as the occasion for war; his dissent at the Common Ministerial Council of 7 Jul, the only member to oppose; his memorandum of 8 Jul for an acceptable note). **consented**: he has consented to an ultimatum, in conference with Berchtold (14 Jul), with the condition of territorial disinterest adopted on 19 Jul. Without it the joint government could not approve the note (`AUH.ultimatum:tisza`). | Berchtold's report to Franz Joseph of 14 Jul; the Council minutes of 7 and 19 Jul; Tisza's memoranda of 1 and 8 Jul (Geiss; document numbers not verified); Albertini vol. II ch. 4; Clark ch. 9; Otte ch. 3. Visible at tick 17. Data: `data/july1914/v1/events.csv`. |

The hidden objectives are as section 1, except that in v1 `aims_GER` enters three guards as a part named `hypothesis` (`GER.kriegsgefahr`, `GER.mobilize`, `GER.mobilize_east`; july1914_v1_decisions.md V3). Endings and invariants as section 6. The date code of 14 July (section 2's `ultimatum` row reads Tisza dissenting until 14 Jul) is replaced in v1 by this variable.
