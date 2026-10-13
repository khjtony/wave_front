# WW2 v1 ontology: deltas on v0, both theatres, 1936Q1 to 1945Q3

Status: phase 2 step 2.1 draft for historian review, written as deltas on [ontology_ww2.md](ontology_ww2.md) (v0), which stays in force for everything not mentioned here. Read [ww2_testbed.md](ww2_testbed.md) sections 5 and 7 and [phase2_kickoff.md](phase2_kickoff.md) D1 and D2 first. T6, T7, T11 and T12 are hold-out tests: this document was written from the record before any of them was run, and nothing in it was chosen to make a registered claim pass. Where a registered claim's wording and the record pull apart, the record is followed and the gap is stated in [ww2_v1_notes.md](ww2_v1_notes.md) section 6.

The actions, Nature events, constraints and the parameter budget are in [actions_ww2_v1.md](actions_ww2_v1.md); conventions, the realized-sequence check, the test-by-test dependencies and the citations I am least sure of are in [ww2_v1_notes.md](ww2_v1_notes.md). Data: `data/ww2/events_ww2_v1.csv`, `data/ww2/decisions_ww2_v1.csv`, `data/ww2/realized_moves_v1.csv`.

Same standards as v0: every level is an observable condition with a stated threshold and a named indicator; references name a document with its date or a book with its chapter, never an invented page; "(chapter not verified)" marks a chapter I could not check. Abbreviations as in v0, plus: Ike (Ike (ed.), *Japan's Decision for War: Records of the 1941 Policy Conferences*, 1967, which prints the Liaison and Imperial Conference records by date), IGHQ (Imperial General Headquarters), GKO (the Soviet State Defence Committee), Stavka (the Soviet supreme command), CCS (the Anglo-American Combined Chiefs of Staff), COSSAC (the Allied planning staff for the cross-Channel invasion, 1943), USSBS (United States Strategic Bombing Survey, postwar, hindsight only), MAUD (the British MAUD Committee), FRUS Japan (FRUS, *Japan 1931-1941*, 2 vols., 1943), NMC (Correlates of War, with the added COW code Netherlands 210 for context only).

## 0. Scope and time

- Tick: one quarter. Tick 0 = 1936Q1, tick 38 = 1945Q3, horizon 39 (tick 39 = 1945Q4, terminal). Kickoff D1.
- Tick convention unchanged from v0 (decisions D1): the state at tick t is the start of quarter t; the row at tick t holds what each actor decided during quarter t; effects are visible at t + 1. A reaction to another actor's decision of the same quarter appears one tick later and is marked [SQR].
- New marker [NSL] (Nature slot). Nature plays one event per tick, so two Nature events dated in one quarter cannot both sit in it. The realized file places the second in the nearest free Nature slot and marks it [NSL] with its real date. There are two such placements on the realized path (ww2_v1_notes.md section 2). This is a limitation of a single Nature actor across two theatres, stated rather than smoothed.
- Theatres: Europe (v0 plus the Eastern front, the United States as a belligerent, Italy, the Western front of 1944, German exhaustion) and Asia and the Pacific (Japan's decisions 1937 to 1945, the embargo, the southern advance, the naval war, the atomic programme).
- Principals unchanged: `GER`, `WEST`, `USSR`, `JPN`, and `Nature` (kickoff D1: Europe keeps v0's actors). **WEST now carries the United States' executive decisions** (rearmament, lend-lease, the embargo, the war production programme, the atomic programme, the landings), as well as the British and French ones. v0 had the United States' domestic decisions as Nature events (`us_neutrality_revision`, `us_engages`); those two stay Nature events, unchanged. The departure, and its cost (WEST has one action per quarter for London and Washington together), is in section 8.
- `USSR` is declared with `remember_last=True` in v1 (Nature's eastern resolutions read `last_USSR`). A departure from v0 decisions D6, reduction 2; the reason is in section 8.

## 1. Hidden objectives (swept)

v0's `aims_GER` and `aims_USSR` unchanged. Added:

| Variable | Levels | Hidden from | Hypothesis each level encodes | Source for the hypothesis space |
|---|---|---|---|---|
| `aims_JPN` | status_quo, regional, hegemonic | GER, WEST, USSR | **status_quo**: Japan seeks to keep Manchukuo and its position in north China and to end the China war on those terms; it has no aim that requires force against the Western powers or the USSR. **regional**: a Japanese-led order in East and Southeast Asia (China plus the southern resource area of Indochina, Malaya and the Dutch East Indies), taken by force if the Western powers block it, but no territorial aim against the USSR. **hegemonic**: the regional aims plus the "northern solution", a war to take the Soviet Far East when the occasion offered. | status_quo is the reading in which the war came from an American policy that left Japan no acceptable way out of China (Schroeder, *The Axis Alliance and Japanese-American Relations, 1941*, 1958; the "Option 1" of the Liaison Conference of 1 Nov 1941, to avoid war and accept gradual decline, in Ike). regional is the autarky reading: Barnhart, *Japan Prepares for Total War* (1987); Iriye 1987 (chapters on 1940 and 1941, not verified); Sagan 1988, in which a rational leadership chose a desperate war to keep its regional position. Contemporaneous statements, each dated: Konoe's statement on a New Order in East Asia, 3 Nov 1938; Matsuoka's announcement of a Greater East Asia Co-Prosperity Sphere, 1 Aug 1940; the Liaison Conference decision of 27 Jul 1940, "Main principles for coping with the changing world situation" (Morley (ed.), *The Fateful Choice*, 1980). hegemonic: the Imperial Conference of 2 Jul 1941 ("Outline of national policies in view of the changing situation", Ike), which resolved to settle the northern question by force if the German-Soviet war went in Japan's favour, and the Kwantung Army's special manoeuvres (Kantokuen) of Jul to Aug 1941. |

No default restriction on `aims_JPN`; all three levels are swept.

Hypothesis gates [H] on `aims_JPN` (actions_ww2_v1.md): `occupy_south_indochina`, `attack_south` and `strike_colonies_only` are gated on `aims_JPN != status_quo`; `strike_north` is gated on `aims_JPN == hegemonic`. The realized Japan of 1941 took both the southern decision and the conditional northern resolution, so the realized trajectory is reachable under `hegemonic` (and under `regional` up to the northern option, which was not taken). As with v0's Germany, the realized behaviour therefore sits at the most expansive hypothesis, and the other two are counterfactual readings; that is a property of the hypothesis definitions and the report should say so.

## 2. Capability and resources

### 2.1 New variables

| Variable | Levels | Init 1936Q1 | Threshold rule | Hindsight indicator |
|---|---|---|---|---|
| `arms_USA` | low, rising, high | low | **low**: the peacetime establishment (an army of under 200,000, the navy at treaty strength under the Vinson-Trammell Act of 27 Mar 1934), no programme of general rearmament funded. The Naval Act of 17 May 1938 and the aircraft programme discussed at the White House on 14 Nov 1938 are partial steps that do not meet **rising**. **rising**: a funded general programme in force and expenditure rising year on year: Roosevelt's message to Congress of 16 May 1940 (50,000 aircraft a year), the defence appropriations of Jun 1940, the Two-Ocean Navy Act of 19 Jul 1940 and the Selective Training and Service Act of 16 Sep 1940. **high**: war production at scale and ground and air forces able to mount and sustain a transatlantic invasion: the production goals of 6 Jan 1942 and the War Production Board (16 Jan 1942) delivering, with the date the planners themselves gave, 1 Jul 1943, as the earliest at which the army could be ready for major offensive operations (the Joint Board estimate of 11 Sep 1941, the "Victory Program"). | NMC `milex`, `milper` for ccode 2 by year; Harrison (ed.) 1998, the chapter on the United States (Rockoff; chapter number not verified); Matloff and Snell, *Strategic Planning for Coalition Warfare 1941-1942* (1953), the chapter on the Victory Program; Kirkpatrick, *An Unknown Future and a Doubtful Present* (1990) |
| `mob_USSR` | peace, total | peace | **peace**: the Soviet economy and reserves on the prewar plan, however large the standing army. **total**: the war economy in being: the evacuated plants back in production in the Volga, Urals and Siberian regions and the reserve armies raised. Read from the output record: Soviet munitions output recovering in the course of 1942 and exceeding Germany's in tanks and aircraft for the year 1942. The decision record is the formation of the Evacuation Council (24 Jun 1941) and of the GKO (30 Jun 1941), and the war-economic plan for the eastern regions of 16 Aug 1941. | Harrison (ed.) 1998, the chapter on the USSR (Harrison; chapter number not verified); Harrison, *Soviet Planning in Peace and War 1938-1945* (1985); Halder's war diary, 11 Aug 1941 ("we reckoned with 200 divisions; we have already counted 360"), as the contemporaneous German record that Soviet mobilization outran the plan |
| `exhaustion_GER` | sustainable, strained, exhausted | sustainable | **sustainable**: Germany can replace its losses and keep armaments output rising on its current organization. **strained**: a two-front war in which losses exceed replacement and the regime itself declares a manpower and production emergency: the decree of 13 Jan 1943 on the comprehensive deployment of men and women for Reich defence, and Goebbels's Sportpalast speech of 18 Feb 1943, after the loss of the Sixth Army at Stalingrad (2 Feb 1943). **exhausted**: armaments output falling month on month and fuel output below the needs of the armed forces: aviation fuel output collapsed after the oil offensive began (12 May 1944), the Romanian supply was lost (Romania's change of sides, 23 Aug 1944; Ploiești taken 30 Aug 1944), and the armaments output index fell from its peak of Jul 1944. Indicator dated Sep 1944. | Speer's memoranda to Hitler on the fuel situation, summer 1944 (as reproduced in the USSBS oil reports; date not verified); USSBS, *The Effects of Strategic Bombing on the German War Economy* (1945), hindsight only; Tooze 2006, the chapters on 1943 to 1945; Overy 1995, the chapters on the air war and on production (not verified) |
| `oil_JPN` | secure, dependent, embargoed, critical | dependent | Not monotone. **secure**: oil under Japanese control in quantities sufficient for war consumption, with the sea lanes to it open: the Dutch East Indies fields held (Palembang from 14 to 16 Feb 1942; the Dutch capitulation on Java, 8 Mar 1942) and tankers getting through. **dependent**: most supply imported by trade, most of it from the United States (about four fifths in the late 1930s, by the usual estimate, not verified). **embargoed**: trade supply cut and the fleet and economy living on stocks: from the freezing of Japanese assets (Executive Order 8832, 26 Jul 1941) and the refusal of export licences for oil (from 1 Aug 1941). **critical**: stocks below what a major naval operation needs, or the sea lanes from the southern area cut. Two routes reach it: the stocks running down under embargo (the "clock": the navy's estimate that stocks would last about two years, about eighteen months at war consumption, put to the Imperial and Liaison Conferences of Sep to Nov 1941, Ike), and the tanker war (imports from the southern area ceased in Mar 1945). | US Bureau of Mines, *Minerals Yearbook* (annual, contemporaneous), petroleum chapters, for 1936 to 1941; Ike for the 1941 estimates; FRUS 1941 vol. IV for the freeze and licensing; USSBS, *Oil in Japan's War* (1946), hindsight only, for 1942 to 1945 |
| `jpn_navy` | strong, attrited | strong | Monotone. **strong**: the Combined Fleet's carrier force intact and able to mount an ocean offensive. **attrited**: the carrier force reduced so that Japan can no longer take the offensive at sea: four fleet carriers lost at Midway (4 to 7 Jun 1942); the attrition of the Solomons (Aug 1942 to Feb 1943) and the Philippine Sea (19 to 20 Jun 1944) are the alternative routes. | US Navy action reports; Morison, *History of United States Naval Operations in World War II*, vol. IV (1949), for Midway; Japanese naval records as summarized in Frank 1999 (chapter not verified) |
| `bomb_ready` | False, True | False | Flag. True when the United States has an atomic weapon ready for use: the Trinity test of 16 Jul 1945 and the weapons delivered to Tinian in late Jul 1945. Set by the delayed effect of WEST `atomic_program`. | Hewlett and Anderson, *The New World, 1939-1946* (1962); Rhodes, *The Making of the Atomic Bomb* (1986) |
| `strategic_bombing` | False, True | False | Flag. True when a combined Anglo-American bomber offensive against the German war economy is directed policy: the Casablanca directive of 21 Jan 1943, confirmed by the Pointblank directive of 10 Jun 1943. Earlier British bombing (the area-bombing directive of 14 Feb 1942) does not meet the rule, which requires the American daylight force. | CCS directives of 21 Jan 1943 and 10 Jun 1943; Webster and Frankland, *The Strategic Air Offensive against Germany* (1961) |
| `air_west` | contested, allied | contested | Monotone. **allied**: Allied air superiority over western Europe by day, the condition COSSAC set for a landing (a substantial reduction of German fighter strength): the defeat of the German day-fighter force between "Big Week" (20 to 25 Feb 1944) and May 1944. | COSSAC outline plan, 15 Jul 1943; Murray, *Strategy for Defeat: The Luftwaffe 1933-1945* (1983) |

### 2.2 Existing variables read differently in v1

- `arms_GER = total`. v0's rule: armaments as the dominant claim on output and labour, the reorganization under the armaments ministry from 1940 to 1942. On the realized path v0's second German `rearm` (14 Oct 1938, delay 8) makes `total` visible at tick 20 (1941Q1), which v0 never reached. The record dates the threshold to 1942: Hitler's armaments decree of 10 Jan 1942 and Speer's appointment (8 Feb 1942). No v1 guard reads `total`, so the one-year discrepancy has no effect on any action; it does put the model and the hindsight snapshots out of step for 1941, and the historian should decide whether the 1938 decision's delay or the rule moves. Not changed.
- `arms_USSR`. v0's `rearm` (decided 1940Q2, delay 4) makes `strong` visible at tick 22 (1941Q3). v0's rule says the record does not show the restored command before June 1941; the record of 1941 and 1942 (the frontier battles; Kiev, Sep 1941; Kharkov, May 1942) shows it later, and the observable marker is the restoration of unitary command (decree of 9 Oct 1942) in autumn 1942. Because of this mismatch **no v1 Eastern-front guard reads `arms_USSR`**; the Soviet side of the eastern campaigns reads `mob_USSR`, whose decision record and lag are wartime. `arms_USSR` stays as in v0 for the purge, `campaign_siberia` and the v0 tests. Proposed (not adopted, historian's decision): either raise USSR `rearm`'s delay or keep it and accept that `arms_USSR` in v1 is a 1940 command-reform variable only.

### 2a. Initial levels at 1936Q1 of the new variables (state at 1 January 1936)

| Variable | Level | Dated evidence |
|---|---|---|
| `aims_JPN` | swept | section 1 |
| `arms_USA` | low | Vinson-Trammell Act, 27 Mar 1934 (navy to treaty limits only); army strength under 200,000 (NMC `milper`, ccode 2, 1935 and 1936) |
| `mob_USSR` | peace | no war; the second Five-Year Plan in force |
| `exhaustion_GER` | sustainable | no war |
| `oil_JPN` | dependent | *Minerals Yearbook* 1935 and 1936, petroleum trade tables: Japanese supply mostly imported, the United States the main source |
| `jpn_navy` | strong | Japan's notice of termination of the Washington naval treaty (29 Dec 1934, effective 31 Dec 1936) and withdrawal from the London Naval Conference (15 Jan 1936); a fleet at treaty strength and building |
| `bomb_ready`, `strategic_bombing` | False | no programme; no war |
| `air_west` | contested | no war in the West ("contested" also covers "no air battle yet", as v0's `channel_air`) |
| `commit_US` (v0) | isolationist | as v0 |
| regions and structure | section 4 and 5 below | |

## 3. Beliefs and commitment

| Variable | Levels | Init | Change in v1 | Threshold rule and indicator |
|---|---|---|---|---|
| `commit_US` | isolationist, wary, engaged, **total** | isolationist | **level added** (`total`) | v0 levels unchanged. **total**: the United States a belligerent by declaration of war against a principal: against Japan, 8 Dec 1941 (Senate 82 to 0, House 388 to 1); against Germany and Italy, 11 Dec 1941, the day Germany and Italy declared war on the United States. T11's `commit[USA] = total` is read as this level. The rule reads the declaration, not the economic mobilization that followed (the production goals of 6 Jan 1942 are `arms_USA`'s indicator). Lend-lease (Act of 11 Mar 1941), the occupation of Iceland (7 Jul 1941) and the "shoot on sight" order after the *Greer* incident (11 Sep 1941) are all `engaged`. Indicators: the joint resolutions of 8 and 11 Dec 1941; FRUS 1941; the Gallup (AIPO) series as a check on opinion, not as the indicator. |
| `belief_GER` | will_not_fight, uncertain, will_fight | will_not_fight | **no longer constant** (v0 decisions D6, reduction 1, said it returns in v1 with T9) | Rules as v0. Two effects in actions_ww2_v1.md: WEST `guarantee_poland` raises it to `uncertain` (the conference of 23 May 1939, L-79, eight weeks after the guarantee, contemplates war with Britain and France); WEST `declare_war` sets `will_fight` (observed resolve, 3 Sep 1939). The record's dip back to `will_not_fight` on 22 Aug 1939 (798-PS, 1014-PS) is **not** modeled: it would be an effect of the pact, which is chosen in the same tick as the declaration of war, and two different `Set`s on one variable in one joint move are a model error. The variable is therefore monotone in v1. |

`belief_WEST` (London's reading of German aims) is unchanged and stays `hegemonic` from 1939. No v1 variable carries Washington's or Moscow's reading of Japanese aims; T7 does not ask for one, and the Magic decrypts (from Sep 1940) are not modeled (section 7).

## 4. Structure

| Variable | Levels | Init | Note |
|---|---|---|---|
| `east_war` | flag | False | Monotone. A German-Soviet war in progress: from 22 Jun 1941. Set by GER `attack_ussr`. Not reset by a negotiated peace (`east_peace` is an ending). |
| `war_us_ger` | peace, war | peace | Monotone. The United States and Germany at war by declaration: 11 Dec 1941. Set by GER `declare_war_us` or WEST `us_declare_war`. The undeclared naval war in the Atlantic (from Sep 1941) is `peace` here and `engaged` in `commit_US`. |
| `pacific_war` | peace, colonial, war, surrendered | peace | Monotone. **colonial**: Japan at war with Britain and the Netherlands but not with the United States (never realized; the documented 1940 principle of limiting force to Britain "as far as possible"). **war**: Japan at war with the United States (and Britain and the Netherlands): from 7 to 8 Dec 1941. T7's `war[JPN][USA]` is `pacific_war >= war`. **surrendered**: Japan has accepted Allied terms: 14 Aug 1945 (the Emperor's broadcast of 15 Aug; the instrument of 2 Sep 1945). |
| `reich` | fighting, surrendered | fighting | Monotone. surrendered: the unconditional surrender of the German armed forces, Reims 7 May and Berlin 8 May 1945. |
| `anglo_soviet_alliance` (v0) | flag | False | **New setter in v1**: set by GER `attack_ussr` (see actions_ww2_v1.md for why it is an effect and not a WEST decision). Indicator: the Anglo-Soviet Agreement of 12 Jul 1941 (mutual assistance; neither party to negotiate or conclude an armistice or peace except by mutual agreement); the Treaty of Alliance of 26 May 1942. The v0 meaning (the 1939 alliance, never concluded) is the same flag. |
| `east_feeler` | flag | False | Monotone. A Soviet approach for a separate peace on record. Set only by the speculative USSR `seek_terms_east`. |
| `east_peace` | flag | False | A German-Soviet negotiated peace. Defines part of `NEGOTIATED_PEACE`. Never true in the record. |
| `midway_ordered` | flag | False | Monotone. The Combined Fleet's Midway operation ordered (IGHQ Navy Order of 5 May 1942; the number is given as 18 in the literature, not verified). Set by JPN `offensive_midway`, read by Nature `midway`. A flag rather than `last_JPN`: JPN stays without `remember_last` (v0 D6, reduction 2), as `north_strike` did in v0. |

v0's `axis`, `anticomintern`, `nazi_soviet_pact`, `polish_guarantee`, `ussr_axis`, `china_war`, `italy_estranged` are unchanged. Two readings are made explicit: `nazi_soviet_pact` records that the pact was concluded, not that it is in force (it stays True after 22 Jun 1941; no v1 guard reads it after that date); `anticomintern` is the German-Japanese pact flag that T7's "GER-JPN pact" reads, and the Tripartite Pact (27 Sep 1940) is a confirming event, not a new flag (events_ww2.csv already carries it).

## 5. Regions

| Variable | Levels | Init | Monotone | Note |
|---|---|---|---|---|
| `w_ussr` | soviet, contested, german | soviet | no | Western USSR: the Baltic republics, Belorussia, the Ukraine and the approaches to Leningrad and Moscow. **contested**: German armies on Soviet territory of 22 Jun 1941 and the Red Army in the field: from 22 Jun 1941. **german**: the objective of Directive No. 21 (18 Dec 1940) met: the Red Army's main forces destroyed and the line from Archangel to the Volga reached, which in the planning record includes the fall of Moscow. Never realized. **soviet** (again): the Red Army at the state frontier of 22 Jun 1941: first reached on the Prut, 26 Mar 1944; Belorussia freed by Operation Bagration (Minsk 3 Jul, Brest 28 Jul 1944) as the confirming event. |
| `caucasus` | soviet, contested, german | soviet | no | The North Caucasus and the oil regions of Maikop, Grozny and Baku. **contested**: German armies in the region: from Jul 1942 (Rostov 23 Jul; Maikop, its fields wrecked, 9 Aug 1942). **german**: the oilfields of Grozny and Baku held, the objective of Directive No. 41 (5 Apr 1942) and No. 45 (23 Jul 1942). Never realized. **soviet** (again): the German withdrawal from the Caucasus ordered 28 Dec 1942 and carried out from Jan 1943, after the encirclement at Stalingrad (19 to 23 Nov 1942); the Kuban bridgehead held to Oct 1943 is not counted as `contested`. |
| `france` (v0) | independent, at_war, fallen, **liberated** | independent | yes | **Level added.** liberated: the German armies in France defeated and Paris retaken: 25 Aug 1944 (the Falaise pocket closed 21 Aug). Every v0 guard that reads `france` reads `== fallen`, `== at_war` or `!= fallen`; `!= fallen` (in `balance_europe`) now also holds for `liberated`, which is intended. |
| `italy` | nonbelligerent, at_war, surrendered | nonbelligerent | yes | Italy in the European war. **at_war**: from the declaration of 10 Jun 1940 (decision in principle, Mussolini's memorandum of 31 Mar 1940; see the [NSL] note). **surrendered**: the armistice of Cassibile, signed 3 Sep and announced 8 Sep 1943, after Mussolini's deposition (25 Jul 1943). Italy is carried by Nature, as in v0. The Italian war in Ethiopia (to May 1936) and in Spain are outside this variable. |
| `indochina` | french, north_occupied, occupied | french | no | **north_occupied**: Japanese forces in Tonkin under the agreements of 30 Aug and 22 Sep 1940 (entry 22 to 23 Sep 1940). **occupied**: Japanese forces in southern Indochina with air and naval bases, under the agreement with Vichy of 29 Jul 1941 (entry 28 Jul 1941). Not monotone: Japan's Proposal B (delivered 20 Nov 1941) offered to withdraw from the south, which is the action `withdraw_south_indochina`. |
| `dei` | dutch, japanese | dutch | yes | The Dutch East Indies. japanese: the Dutch capitulation on Java, 8 Mar 1942 (Palembang 14 to 16 Feb; Balikpapan Jan 1942). |

v0's regions are otherwise unchanged. `balkans` keeps two levels: the Balkan campaign of Apr 1941, Bulgaria's accession (1 Mar 1941) and the defections of 1944 are not modeled (section 7). `poland` is not liberated in the model; its liberation is folded into `reich`'s collapse. `siberia` and the whole Siberian apparatus of T10 (`campaign_siberia` with its four parts, `north_strike`, `china_war`, `china_incident`) are kept as in v0; only the guard of `strike_north` changes (actions_ww2_v1.md, with the reason).

## 6. Balance, invariants, endings

```
german_regions_v1 := german_regions (v0, with [france == fallen] as before)
                   + [w_ussr == german] + [caucasus == german]
balance_europe    := reich == surrendered
                   ∨ (german_regions_v1 < 5 ∧ france != fallen ∧ britain in {at_peace, at_war})
balance_asia      := pacific_war == surrendered ∨ dei != japanese
commitment_alive  := as v0
peace_europe      := war_west_ger == peace ∧ ¬east_war ∧ war_us_ger == peace
```

`balance_europe` keeps v0's three clauses (decisions D2) and adds the German surrender as a restoration of the balance, since the model has no variable that returns Poland, the Czech lands or Austria. `balance_asia` reads "Japan does not hold the southern resource area, or has surrendered". `peace_europe` is offered for T13 (ww2_v1_notes.md section 6); no registered test uses it yet.

Endings, mutually exclusive on every state, declared in this order (each conjoined with the negation of every earlier one, as in v0):

| Ending | Definition | Absorbing or horizon | Change from v0 |
|---|---|---|---|
| `GERMAN_DEFEAT` | `german_defeat` (the 1936 to 1938 French offensive against an unready army; v0 D3) | absorbing | unchanged |
| `NEGOTIATED_PEACE` | `britain == negotiated ∨ east_peace` | absorbing | adds the German-Soviet separate peace |
| `AXIS_HEGEMONY_EUROPE` | `britain == invaded ∨ (w_ussr == german ∧ caucasus == german)` | absorbing | adds the eastern route; see the note below |
| `JPN_CONQUERS_USSR` | `siberia == japanese` | absorbing | unchanged (T10) |
| `USSR_JOINS_AXIS` | `ussr_axis` | absorbing | unchanged (T10) |
| `ALLIED_VICTORY` | `reich == surrendered ∧ pacific_war == surrendered` | absorbing | new; the realized ending, reached at tick 39 |
| `AXIS_HEGEMONY_ASIA` | at the horizon: `dei == japanese ∧ indochina == occupied ∧ pacific_war in {peace, colonial}` | horizon | new; see the note below |
| `PACIFIC_WAR_CONTINUES` | at the horizon: `reich == surrendered ∧ pacific_war in {colonial, war}` | horizon | new |
| `NO_GENERAL_WAR` | at the horizon: `peace_europe ∧ poland == independent ∧ pacific_war == peace` | horizon | redefined: no principal at war with another (testbed 4.6) |
| `LIMITED_WAR` | at the horizon: `war_west_ger == peace ∧ ¬east_war ∧ war_us_ger == peace` (Europe at peace between principals, with Poland taken or a war in Asia) | horizon | redefined |
| `WAR_UNRESOLVED` | at the horizon: any other state | horizon | redefined |

**Retired v0 horizon endings.** `STATIC_FRONT` and `BRITAIN_ALONE` described the state at 1941Q1 and have no meaning at 1945Q4; they are retired. `NO_GENERAL_WAR`, `LIMITED_WAR` and `WAR_UNRESOLVED` keep their names with v1 definitions at tick 39. v0's own horizon (tick 20) no longer ends anything in v1.

**Note on `AXIS_HEGEMONY_EUROPE`.** The testbed defines it as "Germany holds 6 or more European regions including Britain or western USSR". On the realized path Germany holds seven v0 regions from 1940Q4, so the testbed reading makes the ending absorbing the moment `w_ussr` becomes `german`. That would end the run before Japan's documented response to a Soviet collapse (`strike_north`, whose 1941 condition is exactly that collapse) could be represented, and before the Caucasus oil, which German planning named as the second objective (Directive No. 41), was taken. v1 therefore requires both eastern regions. The departure is listed in section 8; T6's claim is phrased on the same pair ("control of western USSR plus the Caucasus").

**Note on `AXIS_HEGEMONY_ASIA`.** The testbed reads "Japan holds the Asian regions and the United States is at `commit ≤ wary`". In v1 `commit_US` is `engaged` from 1940Q3 on the realized path for Atlantic reasons, which says nothing about the Pacific, so the testbed reading would make the ending unreachable after 1940 for a reason unrelated to Asia. v1 reads the Pacific condition directly: Japan holds the southern area and is not at war with the United States at the horizon.

**Endings and two theatres.** An absorbing ending stops the whole run. `GERMAN_DEFEAT`, `NEGOTIATED_PEACE` and `AXIS_HEGEMONY_EUROPE` are European outcomes that therefore also end the Pacific. For runs that start in 1941 or later (T6, T7, T11, T12) this matters only for the European ones; T7 and T12 should report whether any witness ends in Europe before the Pacific question is decided.

## 7. Not modeled in v1, by decision

| Omitted | Test touched | Why it does not change the test (or why it does) |
|---|---|---|
| The Atlantic: the U-boat war, the *Greer* (4 Sep 1941), *Kearny* (17 Oct 1941) and *Reuben James* (31 Oct 1941) incidents | T11 | **Bears on T11's wording.** German submarines attacked American warships in autumn 1941 and Roosevelt did not ask for war. The model does not treat those incidents as "an attack on the United States" (they are inside `engaged`); if T11's "attack" were read to include them, the claim and the record would disagree (ww2_v1_notes.md section 6). |
| A German invasion of the United States | T10 | Still no variable; the T10 United States control stays vacuous in v1. |
| The Balkan campaign (Apr 1941), Crete, North Africa (1940 to 1943), Torch (8 Nov 1942), Tunisia (May 1943) | T6 | The Balkan delay to Barbarossa is a contested reading (the attack was planned for 15 May 1941 and launched 22 Jun); the model's `attack_ussr` is available from 1941Q2 in either case, so the campaign's feasibility in 1941 does not depend on it. North Africa bears on German exhaustion only through the two-front term, which the war with Britain already sets. |
| The Leningrad siege, the 1942 Rzhev battles, the Kharkov battles of 1943, the Kuban bridgehead | T6 | Inside the levels of `w_ussr` and `caucasus`. |
| The Ardennes offensive (decided 16 Sep 1944, launched 16 Dec 1944) and the V-weapons | none | No registered claim reaches 1944Q4 in Europe; a German counter-offensive in the West after exhaustion has no level to change. |
| The Soviet entry into the war against Japan (Yalta agreement of 11 Feb 1945; declaration 8 Aug 1945) | T12 | **Bears on T12's reading.** The declaration falls in the last quarter (1945Q3) and its effect would be visible only at the horizon, so it cannot change any reachable state before tick 39. The record's surrender came after both the bombs and the Soviet entry (Hasegawa, *Racing the Enemy*, 2005, against Frank 1999); the model folds Japan's surrender decision into Nature's `atomic`, as T12's wording does. |
| A Japanese surrender without the bomb | T12 | The postwar counterfactual (USSBS, *Summary Report (Pacific War)*, 1 Jul 1946: surrender before 31 Dec 1945, "in all probability" before 1 Nov 1945) dates it after the horizon, so no event represents it. |
| Burma, India, Imphal (1944), China after 1941 (Ichigo, 1944) | none | No registered claim reads them. |
| Magic (from Sep 1940) and Ultra as observability | T7, T9 | `intel` is not a v1 variable; every principal observes the whole state except the hidden objectives, as in v0. |
| The US elections of 1940, 1942 and 1944 as Nature events | T11 | T11's `electoral` profile carries the electoral constraint (actions_ww2_v1.md); no event changes state on an election day. |
| Danzig as a region (v0 notes, open question 6) | T8, T9 | Not added; the v0 reading of the revisionist hypothesis stands. |
| The 20 July 1944 plot and German peace feelers to the West | none | No record of an Allied alternative after the Casablanca declaration of unconditional surrender (24 Jan 1943); no German government decision to seek terms. |

## 8. Departures from v0 and from the testbed text

None edits a registered claim.

1. **WEST carries the United States' executive decisions** (testbed section 2 proposed USA and UK as separate principals in v1; kickoff D1 keeps v0's actors). Cost: one WEST action per quarter for London and Washington together. On the realized path this displaces one v0 row (tick 18, `fight_on` replaced by `us_rearm`, since `negotiate` was not on the table that quarter and the profile `fight_on` removes it anyway) and leaves several British decisions without a row (ww2_v1_notes.md section 2). The US domestic Nature events of v0 are kept.
2. **`USSR` declared with `remember_last=True`**, against v0 D6 reduction 2, because three Nature resolutions read the Soviet offensive of the previous quarter, as v0's `campaign_west` read `last_GER`. A flag would keep an offensive "on record" forever (the defect of `north_strike`); the eastern front needs the one-quarter reading. JPN stays without it; its one read action uses the flag `midway_ordered`.
3. **Levels added** to `commit_US` (`total`) and `france` (`liberated`); both stay monotone.
4. **`belief_GER` is no longer constant**: two effects, both raises (section 3).
5. **`AXIS_HEGEMONY_EUROPE` and `AXIS_HEGEMONY_ASIA`** read differently from the testbed (section 6, with the reasons).
6. **v0's horizon endings retired or redefined** (section 6).
7. **`anglo_soviet_alliance`** gets a v1 setter that is an effect of a German action (actions_ww2_v1.md).
8. **The [NSL] placement rule** for Nature events that share a quarter (section 0).
9. **`arms_USSR` not read by any eastern guard**, because v0's delay lands it at a date the record does not support (section 2.2).
