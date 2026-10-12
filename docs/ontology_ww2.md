# WW2 v0 ontology: Europe, 1936Q1 to 1940Q4

Status: skeleton fixed by the architect (variables, levels, actors, endings). The historian-facing content (threshold rules with sources, the hindsight indicator each level is read from, and the notes) is filled in phase 1 step 1.1 and reviewed by the historian before any guard is written against it. Read [ww2_testbed.md](ww2_testbed.md) section 7 first: tests T1 to T13 are already registered; this document and [actions_ww2.md](actions_ww2.md) are written without editing them.

Principle for every variable: a level is an *observable* condition with a stated threshold and a named indicator, never a judgment made with knowledge of what came later. Where a level can only be read from documents (beliefs, commitment), the indicator is the dated document class (Cabinet minutes, Hansard, FRUS) and the rule says what wording or decision marks the threshold.

Step 1.1 draft: filled for historian review. Working notes, open questions and the citations I am least sure of are in [ww2_v0_notes.md](ww2_v0_notes.md). Departures from the skeleton are listed in section 9 with their reasons. Page numbers are not given anywhere in this draft: a reference names a book chapter or a dated document, and the historian adds pages at review.

Abbreviations used for document classes: CAB 23 (British Cabinet conclusions to 1939), CAB 27 (Cabinet committees, including the Foreign Policy Committee), CAB 65 (War Cabinet conclusions from Sept 1939), HC Deb (House of Commons debates, Historic Hansard), DGFP (Documents on German Foreign Policy 1918-1945, Series C 1933-37 and Series D 1937-45), DBFP (Documents on British Foreign Policy 1919-1939), DDF (Documents diplomatiques français 1932-1939, 2e série 1936-39), FRUS (Foreign Relations of the United States), IMT and Nuremberg document numbers (the Avalon Project and the IMT volumes; each document carries its original date), NMC (Correlates of War National Material Capabilities v7.0, with COW country codes: Germany 255, United Kingdom 200, France 220, USSR 365, Japan 740, United States 2, Italy 325, Austria 305, Czechoslovakia 315, Poland 290, Romania 360).

## 0. Scope and time

- Tick: one quarter. Tick 0 = 1936Q1, tick 19 = 1940Q4, horizon 20 (tick 20 = 1941Q1, terminal).
- The state at tick t is the situation at the *start* of quarter t (1 January, 1 April, 1 July, 1 October). The joint move chosen at tick t is what the actors decided during quarter t; its effects are visible at tick t + 1. A decision taken in quarter t in reaction to another actor's decision in the same quarter can therefore only appear at tick t + 1 when its guard reads the first decision's effect (see [ww2_v0_notes.md](ww2_v0_notes.md) section 2).
- Theatre: Europe. The Pacific, Barbarossa and the United States as a belligerent are out of scope for v0 (phase 2).
- Principals: `GER` (Germany), `USSR`, `WEST` (the United Kingdom and France acting jointly, with the United States carried as a commitment variable), `JPN` (Japan, a small action set that exists for the Far-East constraint on the USSR and for the registered negative controls). `Nature` carries Italy, Spain, Poland, the smaller states, elections, campaign resolution and intelligence.
- WEST aggregates two governments. Where London and Paris differ, the documentary levels (`belief_WEST`, `commit_WEST`) follow the British Cabinet, which set the pace of Anglo-French policy from 1937 to 1939 (Adamthwaite, *France and the Coming of the Second World War 1936-1939*, 1977); the March 1936 Rhineland decision is the exception, where the French Cabinet decided and the rule reads Paris.

## 1. Hidden objectives (swept)

| Variable | Levels | Hidden from | Hypothesis each level encodes | Source for the hypothesis space |
|---|---|---|---|---|
| `aims_GER` | revisionist, hegemonic | WEST, USSR, JPN | revisionist: revise Versailles (Rhineland, Austria, Sudetenland, Danzig) and stop; hegemonic: continental hegemony including France and the East | the Taylor (1961) reading against Weinberg (1994) and Kershaw; the Hossbach memorandum (Nov 1937) as the contemporaneous statement of the hegemonic case. Filled: revisionist is the position of Taylor, *The Origins of the Second World War* (1961), in which Hitler pursued the revision programme of earlier German governments and the war of 1939 came from miscalculation over Danzig. Hegemonic is the programme reading: Weinberg, *A World at Arms* (1994), chapter 1, and *The Foreign Policy of Hitler's Germany* (2 vols., 1970 and 1980); Kershaw, *Hitler 1936-1945: Nemesis* (2000) and the survey of the debate in *The Nazi Dictatorship* (4th ed., 2000), the chapter on foreign policy ("programme" or "expansion without object"). Contemporaneous statements of the hegemonic case, each dated: Hitler to the army and navy commanders, 3 Feb 1933 (the Liebmann notes: conquest of living space in the East); the Four-Year Plan memorandum, Aug 1936 (armed forces "operational within four years"); the conference of 5 Nov 1937 (Nuremberg document 386-PS, Hossbach's memorandum dated 10 Nov 1937); the conference of 23 May 1939 (L-79). The revisionist case has no single contemporaneous statement; its evidence is the public record (the Reichstag speeches of 7 Mar 1936 and 28 Apr 1939 framing every claim as revision) and the pattern of 1936 to 1938. |
| `aims_USSR` | defensive, opportunist | GER, WEST, JPN | defensive: security and buffer; opportunist: territorial gain where offered (the Nov 1940 Berlin talks) | Filled: defensive is the collective-security reading of Haslam, *The Soviet Union and the Struggle for Collective Security in Europe, 1933-39* (1984), and the pragmatic-security reading of Roberts, *The Soviet Union and the Origins of the Second World War* (1995). Opportunist is the reading of Tucker, *Stalin in Power* (1990), and of Raack, *Stalin's Drive to the West, 1938-1945* (1995), in which Stalin sought gains from a war among the capitalist powers; Gorodetsky, *Grand Delusion* (1999), is between the two. Contemporaneous evidence, each dated: Stalin's report to the 18th Party Congress, 10 Mar 1939 (the "chestnuts" passage); the secret protocol of 23 Aug 1939 (spheres in Finland, the Baltic states, Poland and Bessarabia); the occupation of Northern Bukovina, 28 Jun 1940, beyond the protocol; Molotov's talks in Berlin, 12 to 13 Nov 1940, and the Soviet note of 25 Nov 1940 setting conditions for joining the proposed four-power pact (Finland, Bulgaria, bases at the Straits, the area south of Batum and Baku). Published in *Nazi-Soviet Relations 1939-1941* (Department of State, 1948) and DGFP Series D vol. XI. |

Default restriction: `assume("ussr_defensive", aims_USSR == defensive)`, relaxable (T10's "USSR joins the Axis needs at most one relaxation").

Note on the hypothesis gate. In the action catalogue the hidden objectives enter guards in three places (`occupy_bohemia`, `attack_poland`, `join_axis`) and one effect (`attack_czechoslovakia`). Those conditions are not feasibility constraints: they are hypothesis gates, the device by which a swept objective shapes an actor's action set, as in the toy model. They are listed separately in the catalogue so that the feasibility principle applies to every other guard.

## 2. Capability and resources

| Variable | Levels | Init 1936Q1 | Threshold rule | Hindsight indicator |
|---|---|---|---|---|
| `arms_GER` | low, rising, high, total | rising | **low**: forces within the limits of Versailles Part V (an army of 100,000 long-service men, no conscription, no military aircraft); Germany's condition before 16 Mar 1935. **rising**: conscription in force (Law for the Reconstruction of the Wehrmacht, 16 Mar 1935; Defence Law, 21 May 1935), the air force acknowledged (Mar 1935), and military expenditure rising year on year. **high**: the force of late 1938 and 1939, which German planning treated as able to conduct a campaign against one eastern neighbour while holding the West defensively (the directive of 21 Oct 1938 on the remainder of Czechoslovakia, Nuremberg document C-136; the Case White directive of 3 Apr 1939, C-120); the August 1939 mobilization is the confirming indicator. Read from the planning record as a dated event (the directive of 21 Oct 1938 and the expansion decisions of Oct 1938, events_ww2.csv), with the capabilities table as the cross-check (decisions D12). The level is *not* the ability to defeat France: in May to July 1938 the Chief of the General Staff, Beck, argued in a series of memoranda that a war with Czechoslovakia that brought in France and Britain would be lost, and the action catalogue keeps a French collapse behind a separate condition (`arms_at_war`). **total**: armaments as the dominant claim on output and labour, the reorganization under the armaments ministry from 1940 to 1942; not reached before 1941 in v0. | NMC `milex`, `milper` for ccode 255 by year; Tooze, *The Wages of Destruction* (2006), the chapters on 1936 and the Four-Year Plan and on 1938 to 1939; Deist, "The Rearmament of the Wehrmacht", in *Germany and the Second World War*, vol. I (MGFA, English ed. 1990); the Beck memoranda of 1938 (in K.-J. Müller, *General Ludwig Beck*, 1980) |
| `arms_WEST` | low, rising, high | low | **low**: no funded multi-year programme in force in Britain or France and expenditure flat (Britain before the Statement Relating to Defence, 3 Mar 1936; France before the programme of 7 Sep 1936). **rising**: a funded multi-year programme in force and expenditure rising year on year in both countries (the British deficiency programme from Mar 1936, financed under the Defence Loans Act 1937; the French four-year programme of 7 Sep 1936). **high**: the mobilized forces of 1939 to 1940: France at general mobilization (from 2 Sep 1939), the British Expeditionary Force on the continent, and the post-Munich British air programmes delivering aircraft. | NMC `milex`, `milper` for ccodes 200 and 220; Harrison (ed.), *The Economics of World War II* (1998), for 1938 on; Cmd. 5107 (3 Mar 1936) |
| `arms_USSR` | weak, strong | strong | **strong**: the Red Army's command intact, the condition before the arrests of May 1937. **weak**: the officer corps purged: the Tukhachevsky trial and executions (11 to 12 Jun 1937) and the arrests of 1937 to 1938; the Red Army's performance in Finland (Dec 1939 to Mar 1940) is the confirming indicator. Return to **strong** requires the post-Finland reforms (from Apr to May 1940) to take effect, which the record does not show before June 1941. This is a quality level, not a resource level: NMC `milper` rises through the purge. | the dated Soviet announcements of the trials (11 to 12 Jun 1937); Erickson, *The Soviet High Command* (1962); NMC `milper` for ccode 365 only as a check that size is not the indicator |
| `arms_JPN` | high, total | high | fixed in v0 (engaged in China from 1937). The DSL requires at least two levels (framework_spec.md section 3.1), so this is a constant of the model, not a state variable; no v0 guard reads it. | NMC |
| `ind_GER` | 3, 4, 5 | 3 | Ordinal, not a share. **3**: the industrial and resource base of the Reich in its 1935 borders (with the Saar, returned 1 Mar 1935). **4**: plus Austria, whose value to the armament economy was its gold and foreign-exchange reserves, the Erzberg iron ore, and labour rather than its steel output. **5**: plus Bohemia and Moravia, whose value was the Škoda works at Plzeň, the Brno arms works and the equipment of the Czechoslovak army taken in March 1939. The Sudetenland adds no level (lignite and chemicals; the step is left to the historian). Austria's steel output was a few percent of Germany's, so NMC `irst` shares would not justify a full step; the step rests on Tooze's account of the reserves and the arms industry. | NMC `irst`, `pec` for ccodes 255, 305 (to 1938) and 315 (to 1939); Tooze 2006 on the Austrian reserves and the Czech acquisitions |
| `oil_GER` | dependent, secured | dependent | **dependent**: most of the mineral oil supply imported by sea and exposed to blockade. **secured**: an overland supply agreement in force with a producer outside the blockade: the German-Soviet commercial agreements of 19 Aug 1939 and 11 Feb 1940, or Romania under German alignment (the German-Romanian economic treaty of 23 Mar 1939; the oil agreement of May 1940; the alignment of autumn 1940). The level records the supply route, not adequacy: Germany's oil position stayed tight through the period. | US Bureau of Mines, *Minerals Yearbook* (annual, contemporaneous), petroleum chapters; Tooze 2006; US Strategic Bombing Survey, oil division reports (postwar, hindsight only) |

`ind` for the other principals is constant in v0 and is not a state variable.

### 2a. Initial levels at 1936Q1 (state at 1 January 1936)

| Variable | Level | Dated evidence |
|---|---|---|
| `aims_GER`, `aims_USSR` | swept; `aims_USSR` restricted to defensive by `ussr_defensive` | hidden objectives, section 1 |
| `arms_GER` | rising | conscription law of 16 Mar 1935 and Defence Law of 21 May 1935 in force; NMC `milex` 1934 to 1936 rising |
| `arms_WEST` | low | the Defence Requirements Committee's third report (21 Nov 1935) found the deficiencies unremedied; the Statement Relating to Defence (3 Mar 1936) and the French programme (7 Sep 1936) are both later than 1 Jan 1936. Judgement: the air expansion schemes of 1934 to 1935 were already under way. |
| `arms_USSR` | strong | before the arrests of May 1937; the large Red Army manoeuvres of 1935 to 1936 were observed by foreign military attachés |
| `ind_GER` | 3 | the Reich in its 1935 borders, the Saar returned 1 Mar 1935 |
| `oil_GER` | dependent | Minerals Yearbook 1935 and 1936 trade tables: most supply imported by sea |
| `belief_WEST` | limited | the Anglo-German Naval Agreement (18 Jun 1935) concluded on the premise of negotiable German demands; the Cabinet's pursuit of a general settlement in early 1936 (CAB 23, the response to the German memorandum of 7 Mar 1936 and the questionnaire of 6 May 1936) |
| `belief_GER` | will_not_fight | Hitler's decision for the Rhineland, taken against the anxieties of his military advisers (Kershaw, *Hitler 1889-1936: Hubris*, 1998, the closing chapter; Weinberg 1970). Contested: the military's preparation of a withdrawal contingency is evidence for `uncertain` |
| `commit_WEST` | appease | no continental commitment; the Anglo-German Naval Agreement; the Hoare-Laval proposals (Dec 1935) as the appeasement of Italy |
| `commit_US` | isolationist | Neutrality Act of 31 Aug 1935, extended 29 Feb 1936 |
| `treaty` | eroded | conscription unanswered beyond the Stresa protest (14 Apr 1935) and the League resolution (17 Apr 1935); the Anglo-German Naval Agreement (18 Jun 1935); the zone intact |
| flags | as in section 4 | `italy_estranged`: League sanctions in force from 18 Nov 1935 |
| regions | initial levels | the zone demilitarized; Austria independent (the Austro-German agreement came on 11 Jul 1936); the Czech lands, Poland, France, Britain, the Balkans and Siberia as at 1 Jan 1936 |

## 3. Beliefs and commitment

| Variable | Levels | Init | Threshold rule | Hindsight indicator |
|---|---|---|---|---|
| `belief_WEST` | limited, uncertain, hegemonic | limited | What London (and Paris) believe Berlin wants, read from the governing Cabinet, not from departments (the Foreign Office under Vansittart held the hegemonic view years earlier). **limited**: Cabinet conclusions and ministerial statements treat German aims as revision that a negotiated general settlement can satisfy, and agreements are made on that premise (the Anglo-German Naval Agreement, 18 Jun 1935; the questionnaire to Berlin, 6 May 1936; Halifax's visit, 19 Nov 1937). **uncertain**: Cabinet records treat German aims as possibly beyond revision and adopt warnings or contingency measures while still negotiating: the warning to Berlin of 21 May 1938, the Cabinet's rejection of the Godesberg terms (25 Sep 1938), the war scares of Jan to Feb 1939. **hegemonic**: the Prime Minister and the Cabinet state that German assurances cannot be relied on and that Germany seeks domination by force: Chamberlain at Birmingham, 17 Mar 1939 ("a step in the direction of an attempt to dominate the world by force"), and the Cabinet of 18 Mar 1939. The flip is caused by the taking of a non-German-speaking territory (Prague, 15 Mar 1939). | CAB 23; CAB 27 (Foreign Policy Committee); HC Deb; the Prime Minister's speeches as reported in *The Times*; DDF for Paris |
| `belief_GER` | will_not_fight, uncertain, will_fight | will_not_fight | What Berlin (Hitler, who took the decisions) believes about British and French resolve. **will_not_fight**: records in which Hitler, at a decision, states that the West will not fight (the Obersalzberg address of 22 Aug 1939, Nuremberg documents 798-PS and 1014-PS: "Our enemies are little worms. I saw them at Munich"). **uncertain**: German decision records that provide against Western intervention or record doubt about it. **will_fight**: records in which Berlin treats war with the West as the consequence of its next step (the conference of 23 May 1939, L-79, contemplates war with Britain). No v0 action updates this variable; it is carried for T9 (phase 2). | the Führer conference records (L-79, 798-PS, 1014-PS); DGFP Series C and D; Halder's war diary (from Aug 1939) |
| `commit_WEST` | appease, wary, resolved, at_war | appease | **appease**: no standing commitment to fight for a third state beyond Locarno, rearmament limited to repairing deficiencies, no continental expeditionary commitment ("limited liability"); policy seeks a settlement. **wary**: the government accepts in public that a further German move may require a military answer and prepares for it: the post-Munich acceleration, the Prime Minister's statement of 6 Feb 1939 that a threat to the vital interests of France would bring the immediate cooperation of Britain, the Cabinet decision of Feb 1939 to prepare a field force for the continent and hold staff talks with France. A French or British military response to the Rhineland (the branch `resist_rhineland`) also meets the rule. **resolved**: a standing commitment to fight for a third state that Germany threatens (the Polish guarantee, 31 Mar 1939; Romania and Greece, 13 Apr 1939) or peacetime conscription (announced 26 Apr 1939, Military Training Act 26 May 1939). **at_war**: a declaration of war (3 Sep 1939). | HC Deb (the statements of 6 Feb and 31 Mar 1939; the Military Training Act); CAB 23; DDF |
| `commit_US` | isolationist, wary, engaged | isolationist | **isolationist**: the Neutrality Act regime with a mandatory arms embargo on all belligerents (Acts of 31 Aug 1935, 29 Feb 1936, 1 May 1937). **wary**: the arms embargo repealed and arms sold to belligerents on cash and carry (Neutrality Act of 4 Nov 1939). **engaged**: executive transfers of war material to a belligerent: the destroyers-for-bases agreement (2 Sep 1940), with peacetime conscription (Selective Training and Service Act, 16 Sep 1940); lend-lease (11 Mar 1941) is out of v0. | the Neutrality Acts and their revisions; FRUS 1939 and 1940; Gallup (AIPO) series from 1935 as a check on public opinion, not as the indicator |

## 4. Structure

| Variable | Levels | Init | Note |
|---|---|---|---|
| `treaty` | enforced, eroded, dead | eroded | The Versailles and Locarno regime. **enforced**: a violation of Versailles Part V or of the Rhine Pact is reversed or deterred by the guarantors' threat or use of force (none after the Ruhr occupation of 1923; in v0 reached only by `withdraw_rhineland`). **eroded**: violations announced and protested, no guarantor uses force, but the demilitarized zone (Versailles articles 42 to 44; the Rhine Pact of Locarno, 16 Oct 1925) still stands: the response to German conscription (Stresa, 14 Apr 1935; League Council resolution, 17 Apr 1935) and the Anglo-German Naval Agreement (18 Jun 1935), which accepted naval rearmament beyond Part V. **dead**: the zone reoccupied and the guarantors decline enforcement (the London proposals of the Locarno powers and the League Council's finding of a breach, both 19 Mar 1936). Dead after the Rhineland, through the Nature event `locarno_lapses` (section 9). Indicator: dated treaty texts; League Council minutes (League of Nations Official Journal); DDF; DBFP. |
| `axis` | flag | False | The Rome-Berlin alignment: the October Protocols (23 Oct 1936) and Mussolini's Milan speech (1 Nov 1936); the Pact of Steel (22 May 1939) does not change the flag. Indicator: DGFP Series C vol. V; the protocol text. |
| `anticomintern` | flag | False | Germany-Japan, Anti-Comintern Pact and its secret protocol, 25 Nov 1936. Italy acceded 6 Nov 1937 (not a separate flag). |
| `nazi_soviet_pact` | flag | False | Non-aggression pact and secret protocol, 23 Aug 1939; set by `accept_pact`. Indicator: *Nazi-Soviet Relations 1939-1941*; DGFP Series D vol. VII. |
| `polish_guarantee` | flag | False | Prime Minister's statement in the Commons, 31 Mar 1939 (French concurrence the same day); the Anglo-Polish Agreement of Mutual Assistance, 25 Aug 1939, does not change the flag. |
| `anglo_soviet_alliance` | flag | False | The 1939 talks failed; True only in 1941 (out of v0). Indicator for the failure: the suspension of the military talks, 21 Aug 1939. |
| `ussr_axis` | flag | False | The negative-control outcome of the Nov 1940 talks; never True in the record. |
| `china_war` | flag | False | Japan's army engaged in a general war in China from July 1937 (the Marco Polo Bridge incident, 7 Jul 1937; the cabinet decision of 11 Jul; Shanghai from 13 Aug). The main feasibility constraint on `strike_north` (decisions D7). |
| `italy_estranged` | flag | True | Italy estranged from the West after Ethiopia (1935 to 1936); a Nature precondition for `axis`. Init defended by the League sanctions against Italy in force from 18 Nov 1935 and the collapse of the Hoare-Laval proposals (Dec 1935). |

## 5. Regions (monotone unless noted)

| Variable | Levels | Init | Note |
|---|---|---|---|
| `rhineland` | demilitarized, remilitarized | demilitarized | not monotone: `withdraw_rhineland` exists (the documented March 1936 contingency). remilitarized: German troops garrisoned in the zone (from 7 Mar 1936). |
| `austria` | independent, annexed | independent | annexed: German troops in Austria and the reunification law in force (12 to 13 Mar 1938). |
| `sudeten` | czech, german | czech | german: the areas ceded under the Munich agreement (29 to 30 Sep 1938; occupation 1 to 10 Oct 1938). |
| `bohemia` | czech, german | czech | german: the Protectorate of Bohemia and Moravia (15 to 16 Mar 1939). The region includes Moravia (Brno). |
| `poland` | independent, german, partitioned | independent | **Order changed** (section 9). german: Poland defeated or under German attack with no Soviet share (the outcome without a pact, and the state between 1 and 17 Sep 1939); partitioned: German and Soviet shares (from 17 Sep 1939; boundary treaty 28 Sep 1939). |
| `france` | independent, at_war, fallen | independent | independent means at peace with Germany; fallen: the armistice signed (22 Jun 1940). |
| `britain` | at_peace, at_war, negotiated, invaded | at_peace | negotiated and invaded are endings |
| `balkans` | neutral, german_aligned | neutral | Romania, Hungary, Bulgaria (1940); carries `oil_GER`. german_aligned: Romania under German guarantee with a German military mission and adherence to the Tripartite Pact (Oct to Nov 1940); Bulgaria adhered only on 1 Mar 1941. |
| `siberia` | soviet, japanese | soviet | exists for the negative control "Japan conquers the USSR" |
| `channel_air` | contested, german, british | contested | resolved by Nature during an air offensive; `invade_britain` needs `german`. contested also covers "no air battle yet". british: the German invasion postponed for lack of air superiority (Sea Lion postponed 17 Sep, and to spring 1941 on 12 Oct 1940). |
| `war_west_ger` | peace, war | peace | war: a British and French declaration of war in force (3 Sep 1939). |

Latches: `belief_at_munich` (`belief_WEST` when `sudeten` first becomes german). The draft's `arms_at_war` latch is withdrawn (decisions D3). `GER` and `WEST` are declared with `remember_last=True`; so is `JPN` (section 9), because `campaign_siberia` reads `last_JPN`.

`arms_at_war` is read by the guard of Nature's `campaign_west` (actions_ww2.md): a French collapse requires a German force at `high` when the war began. In the record that is the 1939 force; a war begun earlier would have been fought with the force of its year.

## 6. Balance, kernels, endings

```
balance_europe := german_regions < 5
               ∧ france != fallen
               ∧ britain in {at_peace, at_war}
german_regions := [rhineland == remilitarized] + [austria == annexed] + [sudeten == german]
               + [bohemia == german] + [poland != independent] + [france == fallen]
               + [britain in {negotiated, invaded}] + [balkans == german_aligned]
commitment_alive := treaty != dead ∨ polish_guarantee ∨ anglo_soviet_alliance ∨ war_west_ger == war
```

`commitment_alive` is a separate invariant for analysis only; no registered test uses it (decisions D2: the earlier treaty clause inside `balance_europe` made the balance false by definition from the lapse of Locarno to the Polish guarantee).

The last clause reads "the treaty regime is alive, or an anti-hegemonic commitment has replaced it".

Endings (mutually exclusive on every state; the horizon cases are decided in this order):

| Ending | Definition |
|---|---|
| `GERMAN_DEFEAT` | Nature `campaign_rhineland` resolves a French offensive against an unready German army (decisions D3) |
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

Historian's observation on the last clause of `balance_europe` (no change made; for the architect). On the realized path the treaty regime is dead from 1936 and no guarantee or war exists until 1939, so `balance_europe` is false in every realized state from late 1936 to the guarantee of spring 1939. The clause therefore encodes the reading that the European balance was already lost during the whole appeasement period and was restored only by the guarantee. That is a defensible reading, but it means that no state of 1937 to early 1939 can be in V_WEST whatever `aims_GER` is, which matters for T8 and T13 (ww2_v0_notes.md section 4).

## 7. Not modeled in v0, by decision

Spain (1936 to 1939) except as a Nature effect on `italy_estranged`; Ethiopia (already in `italy_estranged`); the Scandinavian campaign (April 1940); the Soviet-Finnish war; Nomonhan (1939) except as the constraint behind `strike_north`; the Low Countries separately from France; the Mediterranean. Each is a candidate for v1 and is listed so that a missing path is attributed to a decision, not an oversight.

Added in step 1.1, each with the registered test it touches and why the omission does or does not change that test:

| Omitted | Test touched | Why it does not change the test (or why it does) |
|---|---|---|
| The French general election of Apr to May 1936 and the caretaker status of the Sarraut government; Gamelin's position (8 Mar 1936) that any action in the zone required at least partial mobilization | T2 | T2 is conditional on France playing `resist`. These were the reasons France did not resist; they bear on why the branch was not taken, not on what follows if it is. Leaving them out makes `resist_rhineland` look cheaper than it was, which a report on T2 must say. |
| The Franco-Soviet pact (signed 2 May 1935, ratified by the Chamber 27 Feb 1936), Hitler's stated pretext for the Rhineland | T1, T2 | A pretext, not a precondition; `remilitarize_rhineland` is feasible without it. |
| Belgium's return to neutrality (14 Oct 1936) | T1, T5 | It shaped Allied planning (the Dyle plan) and the route of the 1940 offensive, which are inside Nature's `campaign_west`. No v0 guard depends on it. |
| The Anglo-Italian agreements (2 Jan 1937, 16 Apr 1938) | T1, T8 | They came after `axis` is set, so `italy_reconciles` (guarded by `not axis`) cannot represent them; Italy stayed aligned with Germany, so the realized path is unaffected. |
| Danzig and the Polish Corridor as a separate claim (Ribbentrop to Lipski, 24 Oct 1938; the crisis of 1939) | T8 | **Changes T8's reading.** The revisionist hypothesis includes Danzig, but v0 has no Danzig region, so the revisionist claim on Danzig cannot be pursued short of `attack_poland`, which the catalogue gates on `hegemonic`. Under the revisionist hypothesis Poland is therefore never attacked. That is stronger than Taylor's reading, in which the war over Danzig came from miscalculation. See ww2_v0_notes.md section 4 (T8). |
| Memel (22 to 23 Mar 1939) and Italy's invasion of Albania (7 Apr 1939) | T4 | Both followed Prague. They reinforced the belief flip and occasioned the guarantees to Romania and Greece; T4's claim is that the flip is necessary for the guarantee, and these events come after it. |
| The Tilea warning (17 Mar 1939) and the Colvin report (29 to 30 Mar 1939), the immediate occasions of the guarantee | T4 | They timed the guarantee within the quarter; the guard abstracts to the belief flip, which is the registered claim. |
| The Dominions' positions (reluctance in Sep 1938; support in Sep 1939) | T4, T5 | They are part of what made a continental commitment politically feasible in 1939 and not in 1938; the catalogue folds them into the belief condition of `guarantee_poland`, which is one reason that condition is closer to a preference than to capability (actions_ww2.md). |
| Poland's refusal of passage for Soviet troops (Aug 1939) | T9 (phase 2) | Folded into the USSR's choice of `accept_alliance`; v0 tests do not depend on it. |
| The German-Soviet Boundary and Friendship Treaty (28 Sep 1939) and the Soviet annexations of 1940 (the Baltic states, 15 to 17 Jun; Bessarabia and Northern Bukovina, 28 Jun) | T10 | They are evidence for the opportunist hypothesis, not conditions of `join_axis`. The USSR control needs one relaxation (the `ussr_defensive` assumption) with or without them. |
| The Allied plans of Feb to Mar 1940 to intervene in Finland and to bomb the Caucasus oilfields | T10 | They could have put WEST at war with the USSR and are an unmodeled route toward `USSR_JOINS_AXIS`. Omitting them can only remove paths; T10 asks for at most one relaxation, which the model already gives. |
| The change of Prime Minister (Churchill, 10 May 1940) and the Norway debate (7 to 8 May 1940) | T5 | WEST is one actor; who leads it is not a variable. `negotiate` is available under either leader; T5's claim is about availability. |
| Dunkirk (26 May to 4 Jun 1940) as a separate outcome | T5 | Inside `campaign_west`. Under `fight_on`, Germany cannot force the invasion ending in any case (ww2_v0_notes.md, T5). |
| The Royal Navy and the naval problem of Sea Lion (the Naval Staff's memoranda of Jul 1940) | T5 | `invade_britain` needs only `channel_air == german`. Leaving out the naval obstacle makes invasion easier than it was, so it can only work against T5's claim, not for it. |
| Radar, Ultra and the RAF's order of battle | T5 | Inside Nature's air battle, which is nondeterministic. |
| Italy's entry into the war (10 Jun 1940), and Italy as the intermediary debated by the War Cabinet in May 1940 | T5 | The May debate concerned an approach through Mussolini; `negotiate` does not require an intermediary, so its availability does not depend on Italy. |
| The German peace offers of 6 Oct 1939 and 19 Jul 1940 as separate state changes | T5 | Represented by `offer_terms_britain` through `last_GER`; it changes no other variable. |
| Japan's war with China (from 7 Jul 1937), the Tripartite Pact (27 Sep 1940), the move into northern Indochina (Sep 1940) | T10 | **Changes T10.** The China war was the main constraint on any strike north. With it omitted, `strike_north` is feasible from mid-1937 and the JPN control rests on the guard of `campaign_siberia` alone, so it needs one relaxation, not three. See ww2_v0_notes.md section 4 (T10). |
| The US elections of 1936 and 1940 (Nature events in ww2_testbed.md 4.4) | none in v0 | No v0 guard reads them; they matter for T11 (phase 2). |
| Any German action against the United States; a German collapse | T10 | There is no variable for either, so the controls "Germany conquers the United States" and "Britain alone defeats Germany by 1941" are unreachable by construction in v0 rather than after relaxations. See ww2_v0_notes.md section 4 (T10). |

## 8. Historian's review checklist (step 1.1)

- [ ] every threshold rule names its indicator and a page or document reference. Every rule names its indicator and a dated document or a book chapter; no page references are given (draft rule: no page is cited unless verified). Historian to add pages.
- [ ] every 1936Q1 initial level is defended from a dated source. Defended in the table in section 2a, except `belief_GER`, whose defence rests on secondary reconstructions (Kershaw, Weinberg) and is contested by the military record of March 1936; and `arms_WEST`, where `low` is a judgement given that the British air expansion schemes of 1934 to 1935 were already under way.
- [x] the hidden-objective hypothesis spaces cite the historiographical readings they encode
- [ ] section 7 is complete: nothing relevant to T1, T2, T4, T5, T8 or T10 is missing. Extended above; two omissions (Danzig; the China war) do change T8 and T10, and are recorded as such. Historian to confirm nothing else is missing.

## 9. Departures from the skeleton (step 1.1)

Each change to a level, a level order, a declaration or an effect, with its reason. None changes a registered claim.

1. **`poland` level order** changed from (independent, partitioned, german) to (independent, german, partitioned). Reason: the German attack (1 Sep 1939) and the Soviet entry (17 Sep 1939) are separate decisions by separate actors, and under the quarterly tick the pact (23 Aug) and the attack fall in the same tick, so the attack's effect cannot read the pact. The attack therefore sets `german` and the Soviet entry moves `german` to `partitioned`, which is monotone only in the new order. Both levels still count as `poland != independent`, so `german_regions` and the endings are unchanged.
2. **`arms_JPN`** is a constant, not a state variable: the DSL requires at least two levels and no v0 guard needs it.
3. **`JPN` declared with `remember_last=True`**, because Nature's `campaign_siberia` reads `last_JPN == strike_north`.
4. **`treaty` dies through a Nature event** (`locarno_lapses`, added in actions_ww2.md) rather than as an immediate effect of `remilitarize_rhineland`. Reason: with the skeleton's effect, `treaty == dead` holds in the state right after the remilitarization, before WEST can play `resist_rhineland`; with no guarantee, alliance or war in that state, `balance_europe` is false there, so 1936Q1 could not be in V_WEST under any branch and T2 would fail for a reason unrelated to its claim. The historical lapse (19 Mar 1936) followed the guarantors' decision not to act, which is what the event encodes. Cost: in the model the treaty dies at 1936Q4 at the earliest, against 1936Q2 in the hindsight snapshot.
5. **`withdraw_rhineland` also sets `treaty := enforced`**: a violation reversed under threat of force meets the rule for `enforced`.
6. **Threshold rules tightened**: `arms_GER = high` is the late 1938 and 1939 force, not "able to defeat France"; `commit_WEST = wary` is the post-Munich continental commitment, not "rearmament accepted as policy" (which would set it in March 1936 and make it duplicate `arms_WEST`). Both changes keep the skeleton's realized path and make the levels distinct and observable.
