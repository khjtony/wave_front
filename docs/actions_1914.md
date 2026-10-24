# July 1914 v0 action catalogue

Status: written for the model step after the registration of J1 to J7 and before any claim was run. Variables and levels are in [ontology_1914.md](ontology_1914.md); the architect's decisions and the readings of the claims in [july1914_decisions.md](july1914_decisions.md). The model is `models/july1914/v0.py`; every action there carries the `source=` text summarized here. Abbreviations as in the ontology.

**Hold-out.** J2 to J6 are hold-out claims under a total hold-out (testbed section 0; the architect's brief names J2 to J5, decisions D9). Every guard, effect, delay, cadence, fairness constraint and profile below was written from the record before any claim was run. After their first sight nothing here changes for them; a failing claim stays failing with its explanation and a proposed amendment for the owner.

## The feasibility principle and the conventions

As for WW2: a guard says when an action was feasible (a capability, an institutional constraint, a prior condition), never what the actor would prefer. Every action has a `source=` naming the dated record in which the alternative was decided, debated or refused; an action without such a record would be `speculative=True` (there is none in v0). A conjunct on a swept hidden objective is a hypothesis gate [H], the part named `hypothesis`. Guards that join independent documented constraints are declared as named parts, each a relaxable assumption `<actor>.<action>:<part>`. A part named `level`, `once` or `target` only keeps an action from repeating or from lowering a level.

1. **Day ticks.** A dated decision falls in its day's tick; a decision after midnight counts on its day. Effects are visible the next day.
2. **[SQR].** A reaction to another actor's decision of the same day can only be chosen the next day. None of the realized decisions needs it: each realized reaction was taken at least a day after what it answers, or its guard reads an earlier condition (AUH `mobilize_partial` reads the note's delivery, not the reply of the same day; GBR `ultimatum_GER` reads the note to Belgium, not the invasion of the same day). Both choices are stated under the actions.
3. **[NSL].** Nature plays one event per tick. Nature's four realized events fall on four different days; the Belgian refusal and Grey's statement of 3 August, which would have shared a day, are respectively inside `invade_belgium` and a GBR action.
4. **Cadence** (decisions D3). A principal with cadence k decides at most once every k days; the counter `cadence_<actor>` is the refractory period after a declared action (framework_spec.md section 3.1). k is the smallest gap between two consecutive realized decisions of the government in `data/july1914/decisions.csv`: AUH 3, FRA 2, GER 1, RUS 1, GBR 1 (the table in decisions D3). The French voyage is a guard part (`in_paris`), not a cadence.
5. **Pre-commitments** (decisions D4). A mobilization level is the order in force; no action lowers it except `RUS.revoke` before general mobilization. The German plan's steps after mobilization are obligations (`western_timetable`, `liege`), not choices that can be withheld.

## Austria-Hungary (`AUH`, cadence 3)

| Action | Guard (parts) | Effect | Delay | Realized |
|---|---|---|---|---|
| `council` | `german_support: blank_cheque`; `target: ultimatum == none` | `ultimatum := resolved` | 0 | tick 9 (7 Jul) |
| `ultimatum` | `resolved: ultimatum == resolved`; `council: tick >= 16` | `ultimatum := delivered` | 4 | tick 21 (19 Jul), delivered visible tick 26 |
| `mobilize_partial` | `occasion: ultimatum >= delivered`; `harvest_leave: tick >= 27`; `level: mob_AUH == none` | `mob_AUH := partial` | 0 | tick 27 (25 Jul) |
| `declare_war_SER` | `rejected: ultimatum == rejected`; `mobilizing: mob_AUH >= partial`; `level: war_AUH_SER == peace` | `war_AUH_SER := war` | 0 | tick 30 (28 Jul) |
| `accept_halt` | `proposed: halt_in_belgrade == proposed` | `halt_in_belgrade := accepted` | 0 | never |
| `mobilize_general` | `russian_measures: mob_RUS >= partial`; `halt_refused: halt_in_belgrade != accepted`; `level: mob_AUH != general` | `mob_AUH := general` | 0 | tick 33 (31 Jul) |

- **`council`**. Source: "Common Ministerial Council of 7 Jul 1914 (minutes; Geiss): action against Serbia decided in principle, demands to be put in a note, against Tisza's objection to a surprise attack; convened on Hoyos's return with the German assurance (Szögyény's telegrams of 5 and 6 Jul)." `german_support`: the Council proceeded on the assurance; Berchtold had sent Hoyos to obtain it first (Franz Joseph's letter and the revised Matscheko memorandum, carried 4 to 5 Jul).
- **`ultimatum`**. Source: "Tisza's consent, 14 Jul (Berchtold's report to Franz Joseph); the Common Ministerial Council of 19 Jul approving the text and fixing delivery for 23 Jul after Poincaré's departure from St Petersburg; Giesl's delivery, 23 Jul 18:00, 48-hour limit (Red Book; Geiss; Albertini vol. II)." Part `council` (`tick >= 16`): the joint government's approval required the Hungarian premier, whose consent the record dates 14 July; written as a date because Tisza's change of mind is not a modeled decision (the WW2 precedent: `embargo_jpn:instrument`, decisions E2 item 6). Delay 4: the delivery date fixed at the decision (19 to 23 July). It is a delay, not a part, because the date was decided with the text and Giesl executed it without a further decision; the Poincaré timing is therefore a pre-commitment the bounded relaxation cannot lift (decisions D4).
- **`mobilize_partial`**. Source: "Franz Joseph's order of 25 Jul (evening, Bad Ischl) for the mobilization against Serbia (Plan B), first mobilization day 28 Jul (Albertini vol. II)." `occasion`: the Council of 19 July prepared mobilization as the sanction of the note; the guard reads the delivery, so the order of the evening of 25 July, the day of the reply, is not an [SQR] reaction (convention 2). `harvest_leave` (`tick >= 27`): Conrad's statement to Berchtold, in the week after the Council of 7 July, that men of several corps were on harvest leave until 25 July and that an early recall would alarm Europe (Clark; the date of the statement not verified). A documented constraint the record never lifts.
- **`declare_war_SER`**. Source: "Berchtold's telegram of 28 Jul (about 11:00) declaring war, against Conrad's advice to wait until operations could begin (about 12 Aug); Franz Joseph's signature of 27 Jul (Red Book; Albertini vol. II)." `mobilizing`: no declaration without a mobilization order was debated.
- **`accept_halt`**. Source: "the Halt in Belgrade put to Berchtold by Tschirschky, 29 to 30 Jul; Berchtold's evasive answer of 30 Jul; the Council of 31 Jul declining it (Geiss; Albertini vol. II)." The documented alternative, not taken; not speculative.
- **`mobilize_general`**. Source: "order signed 31 Jul 12:23, first day 4 Aug, on the news of the Russian partial mobilization and Moltke's telegram to Conrad of 30 Jul; decided with the Council of 31 Jul that declined the Halt (Albertini vol. II; Mombauer)." `russian_measures`: the general mobilization answered the Russian partial mobilization (Plan R against Russia); `halt_refused`: the Council of 31 July took both decisions together, and an accepted halt would have suspended operations beyond Belgrade.

## Germany (`GER`, cadence 1)

| Action | Guard (parts) | Effect | Delay | Realized |
|---|---|---|---|---|
| `blank_cheque` | `once: not blank_cheque` | `blank_cheque := True` | 0 | tick 7 (5 to 6 Jul) |
| `restrain_vienna` | `occasion: ultimatum == rejected`; `open: halt_in_belgrade != accepted` | `halt_in_belgrade := proposed` if `none` | 0 | ticks 30 (28 Jul), 32 (30 Jul) |
| `kriegsgefahr` | [H] `hypothesis: aims_GER == continental or mob_RUS == general`; `russian_measures: mob_RUS >= partial`; `level: mob_GER == none` | `mob_GER := kriegsgefahr` | 0 | tick 33 (31 Jul) |
| `mobilize` | `sequence: mob_GER == kriegsgefahr` | `mob_GER := general; war_GER_RUS := war` | 0 | tick 34 (1 Aug) |
| `mobilize_east` | `sequence: mob_GER == kriegsgefahr`; `coupling: FALSE` | `mob_GER := general` | 0 | never (refused 1 Aug) |
| `ultimatum_belgium` | `plan: war_GER_RUS == war`; `target: belgium == neutral` | `belgium := demanded` | 0 | tick 35 (2 Aug) |
| `declare_war_FRA` | `plan: war_GER_RUS == war`; `target: war_GER_FRA == peace` | `war_GER_FRA := war` | 0 | tick 36 (3 Aug) |

- **`blank_cheque`**. Source: "Wilhelm II to Szögyény at Potsdam, 5 Jul; Bethmann and Zimmermann to Szögyény and Hoyos, 6 Jul (Szögyény's telegrams; Geiss)." No feasibility condition: the assurance could have been given (or refused) on any day after Sarajevo; it was given on Vienna's request.
- **`restrain_vienna`**. Source: "Wilhelm II's note to Jagow of 28 Jul (morning) on the Serbian reply (Belgrade as a pledge); Bethmann's telegram to Tschirschky of 28 Jul 22:15 transmitting it in weakened form; Bethmann's telegrams of 30 Jul 02:55 and 03:00 after Lichnowsky's report ('we must decline to be drawn into a world conflagration'), suspended in the night of 30 Jul (Kautsky; Geiss; the hour of the suspension not verified)." One action for both realized plays: each puts the Halt to Vienna; the model gives the second no further state effect, because its only possible effect, Vienna's acceptance, is Vienna's decision (`AUH.accept_halt`) under Vienna's cadence. This is the restraint of claim J4. `occasion`: the Kaiser's proposal answered the Serbian reply.
- **`kriegsgefahr`**. Source: "proclaimed 31 Jul 13:00 on the news of the Russian general mobilization, with the ultimatums to Russia (12 hours) and France (18 hours); Falkenhayn's demand of 29 Jul for it after the Russian partial measures, refused by Bethmann that day; Moltke's memorandum of 29 Jul (Mombauer; Geiss)." [H]: under `localize` Germany proclaims it only after a Russian general mobilization order (Bethmann's position on 29 to 30 July, waiting for Russia to move first); under `continental` the Russian partial measures suffice (Falkenhayn's alternative). `russian_measures`: no German general measure before a Russian mobilization order was debated in July.
- **`mobilize`**. Source: "the mobilization order of 1 Aug (about 17:00), first day 2 Aug, and the declaration on Russia handed over by Pourtalès about 19:00: under the deployment plan in force since April 1913 (Aufmarsch I West only) mobilization meant war, declared at once to open the western operations (Mombauer; Trachtenberg 1990/91)." The declaration is part of the effect because no German debate separated it from the mobilization order: the coupling.
- **`mobilize_east`**. Source: "Wilhelm II's demand of 1 Aug (evening, on Lichnowsky's telegram) that the army deploy against Russia only, and Moltke's refusal: no plan existed, the eastern deployment (Aufmarsch II Ost) having been abandoned in April 1913 (Moltke's memoir, postwar; Mombauer)." The refused alternative is documented, so the action is not speculative; it is infeasible by the part `coupling` (the constant FALSE). **Relaxing `GER.mobilize_east:coupling` is the coupling relaxed** (claim J2): an eastern-only mobilization without a declaration of war becomes available. This is how decisions D4's "guard part named `coupling` on the German mobilization's war effect" is written in a DSL whose effects have no parts (decisions D4).
- **`ultimatum_belgium`**. Source: "the note drafted by Moltke on 26 Jul, sent sealed to Below-Saleske on 29 Jul, delivered 2 Aug 19:00, 12-hour limit; Luxembourg occupied the same day (Geiss; Albertini vol. III)." `plan`: the note belonged to the western deployment that followed the mobilization-with-war; after `mobilize_east` it is not available.
- **`declare_war_FRA`**. Source: "the declaration handed to Viviani by Schoen, 3 Aug 18:45, on the pretext of French air raids (Geiss; Albertini vol. III)." `plan` as above.

## Russia (`RUS`, cadence 1)

| Action | Guard (parts) | Effect | Delay | Realized |
|---|---|---|---|---|
| `pre_mobilize` | `occasion: ultimatum >= delivered`; `level: mob_RUS == none` | `mob_RUS := pre_mobilization` | 0 | tick 27 (24 to 25 Jul) |
| `mobilize_partial` | `prepared: mob_RUS == pre_mobilization`; `occasion: war_AUH_SER == war` | `mob_RUS := partial` | 0 | tick 31 (29 Jul) |
| `mobilize_general` | [H] `hypothesis: aims_RUS == fight or mob_GER >= kriegsgefahr or mob_AUH == general`; `prepared: mob_RUS >= pre_mobilization`; `level: mob_RUS != general` | `mob_RUS := general` | 0 | tick 32 (30 Jul) |
| `revoke` | `revocable: mob_RUS in {pre_mobilization, partial}` | `mob_RUS` one level down | 0 | never |

- **`pre_mobilize`**. Source: "the Council of Ministers of 24 Jul (Sazonov, Krivoshein: partial mobilization in principle and preparatory measures) and the Tsar's council at Krasnoe Selo of 25 Jul approving the period preparatory to war from 26 Jul (Lieven; Orange Book; the council journals as printed in the literature, not verified)." One decision over two days, placed on the Tsar's day (25 July): the Council of 24 July deliberated, the Tsar decided.
- **`mobilize_partial`**. Source: "Sazonov's decision of 28 Jul to announce the partial mobilization of four districts on the Austro-Hungarian declaration of war; announced 29 Jul, ordered in the night of 29 to 30 Jul (Lieven; Albertini vol. II)." `occasion`: the Council of 25 July made it conditional on Austro-Hungarian military action against Serbia.
- **`mobilize_general`**. Source: "authorized by Nicholas II at Peterhof on 30 Jul after Sazonov's audience and ordered about 17:00 (Yanushkevich, Dobrorolsky), first day 31 Jul (Lieven; Albertini vol. II)." `prepared`: the General Staff could order it from the preparatory period (it held the partial order technically unsound). [H]: under `deter` only in answer to a German or Austro-Hungarian general measure; under `fight` once the preparatory period is in force. The realized order of 30 July preceded every such measure, so it is available only under `fight`.
- **`revoke`**. Source: "Nicholas II's countermand of 29 Jul (about 21:40, after Wilhelm II's telegram) of the general order signed that day, replaced by the partial order (Lieven; Albertini vol. II)." The record shows a Russian order revoked before general mobilization began. The testbed's record line ("partial decided 29 July and revoked that evening") conflates the two orders of 29 July; the order revoked was the general one, and the partial order went out that night (decisions D4). In the model the general order is irrevocable (the architect's decision: revocation exists until general mobilization), so `revoke` steps back one level from `partial` or `pre_mobilization`. It is not on the realized path: the countermand fell on the day of the order it changed, and the model's day holds one Russian decision (the partial order, which is what stood at the end of 29 July).

## France (`FRA`, cadence 2)

| Action | Guard (parts) | Effect | Delay | Realized |
|---|---|---|---|---|
| `covering_troops` | `in_paris: tick >= 31`; `threat: mob_RUS >= partial or mob_GER != none`; `level: mob_FRA == none` | `mob_FRA := covering_troops` | 0 | tick 32 (30 Jul) |
| `mobilize` | `in_paris: tick >= 31`; `german_measures: mob_GER != none`; `level: mob_FRA != general` | `mob_FRA := general` | 0 | tick 34 (1 Aug) |

- **`covering_troops`**. Source: "the Council of Ministers of 30 Jul granting Joffre the covering troops without reservists, with the ten-kilometre withdrawal (Messimy's order; DDF vol. XI; Joffre's memoirs)." `in_paris` (`tick >= 31`): Poincaré and Viviani were at sea from the night of 23 July and in Paris on 29 July; the Council under Bienvenu-Martin deferred military decisions to their return (Poincaré, *Au service de la France* vol. IV). The architect allowed the voyage as a part or a cadence; a part keeps it relaxable and named, and FRA's cadence (2) is then the gap between its two decisions. `threat`: Joffre's requests of 29 to 30 July cited the German frontier measures and the Russian partial mobilization.
- **`mobilize`**. Source: "the general mobilization decided by the Council on 1 Aug and posted from 15:45 to 16:00, after the German ultimatum of 31 Jul and Joffre's demand (DDF vol. XI; Yellow Book)." `german_measures`: the decision followed the Kriegsgefahrzustand.

## Britain (`GBR`, cadence 1)

| Action | Guard (parts) | Effect | Delay | Realized |
|---|---|---|---|---|
| `naval_assurance` | `continental_war: war_GER_RUS == war or war_GER_FRA == war`; `level` | `commitment_GBR := max(naval_assurance)` | 0 | tick 35 (2 Aug) |
| `guarantee_belgium` | `continental_war` as above; `level` | `commitment_GBR := max(belgian_guarantee)`; `belief_GER_GBR` +2 (clamped) | 0 | tick 36 (2 to 3 Aug) |
| `ultimatum_GER` | `belgian_route: belgium >= demanded`; `parliament: commitment_GBR >= belgian_guarantee`; `level` | `commitment_GBR := war`; `belief_GER_GBR` +2 (clamped) | 0 | tick 37 (4 Aug) |

- **`naval_assurance`**. Source: "the Cabinet of 2 Aug (morning) and Grey's assurance to Cambon that afternoon, after the Cabinets of 29 Jul and 1 Aug had refused any commitment; the Grey-Cambon letters of 22 to 23 Nov 1912 (BD XI; Asquith's letters, 2 Aug)." `continental_war`: the Cabinet would consider a commitment only once a continental war had begun (the refusals of 29 July and 1 August; the decision of 2 August after the German declaration on Russia).
- **`guarantee_belgium`**. Source: "the Cabinet of 2 Aug (evening) resolving that a substantial violation of Belgian neutrality would compel action; Grey's statement in the Commons, 3 Aug about 15:00 (Hansard; BD XI)." Placed on 3 August with the statement (the Cabinet of 2 August took two decisions; the model's day holds one). Read in Berlin as Britain fighting, so it raises `belief_GER_GBR` (a clamped `Bump`, which composes with a Nature `Set` on the same day).
- **`ultimatum_GER`**. Source: "Grey's telegrams to Goschen of 4 Aug: the morning demand that Germany withdraw its note to Belgium, then the ultimatum expiring at 23:00 London time; Britain at war from 23:00 (BD XI)." `belgian_route`: the demand answered the German note to Belgium, known in London on 3 August, before the invasion of 4 August was known; reading the note rather than the invasion keeps the realized decision on its day (convention 2). `parliament`: the ultimatum followed Grey's statement and the House's support.

## Nature

| Event | Guard (parts) | Effect | Realized |
|---|---|---|---|
| `serbian_reply` | `delivered: ultimatum == delivered` | `ultimatum := rejected` | tick 27 (25 Jul) |
| `lichnowsky_warning` | `occasion: war_AUH_SER == war` | `belief_GER_GBR := fights` | tick 31 (29 Jul) |
| `lichnowsky_offer` | `occasion: mob_GER == kriegsgefahr`; `no_commitment: commitment_GBR == none` | `belief_GER_GBR := uncertain` | tick 34 (1 Aug) |
| `invade_belgium` | `demanded: belgium == demanded`; `western_war: war_GER_FRA == war` | `belgium := invaded` | tick 37 (4 Aug) |

- **`serbian_reply`**. Source: "the reply handed to Giesl on 25 Jul at 17:55, accepting most demands and refusing point 6; Giesl's departure at 18:30 (Red Book; Geiss)." Serbia is not a principal (testbed). The only outcome is the rejection (the reply as Vienna judged it): an unconditional acceptance was not the Serbian government's decision on 24 to 25 July (Albertini vol. II discusses the reports that it was considered; not modeled).
- **`lichnowsky_warning`**. Source: "Lichnowsky's telegram of 29 Jul reporting Grey's private warning, received in Berlin that evening (Kautsky; Geiss; the hour not verified)." `occasion`: Grey's warning followed the Austro-Hungarian declaration and the Cabinet of 29 July. No part reads the belief itself (decisions D5): the event may recur, with no effect once Berlin reads Britain as fighting.
- **`lichnowsky_offer`**. Source: "Lichnowsky's telegram of 1 Aug reporting Grey's inquiry as an offer of British and French neutrality, received about 17:00, corrected by George V's telegram the same night (Kautsky; Geiss)." `occasion`: Grey's inquiry answered the German ultimatums of 31 July.
- **`invade_belgium`**. Source: "the Belgian refusal of 3 Aug 07:00 and the entry of German troops on 4 Aug about 08:00 towards Liège, the plan's first operation (Geiss; Albertini vol. III)." A timetable step carried by Nature (decisions D2): no German decision separated the entry from the note and the declaration on France.

## Constraints (fairness)

| Name | Actor | Trigger | Within | Responses | Source |
|---|---|---|---|---|---|
| `reply_deadline` | Nature | `ultimatum == delivered` | 2 | `serbian_reply` | the 48-hour limit of the note (23 Jul 18:00 to 25 Jul 18:00); Giesl's instructions to leave on anything short of unconditional acceptance |
| `mobilization_race` | GER | `mob_RUS == general and mob_GER != general` | 1 | `kriegsgefahr`, `mobilize`, `mobilize_east` | the General Staff's rule that Germany mobilizes when Russia does: Moltke's memorandum of 29 Jul; the Kriegsgefahrzustand within about 90 minutes of the confirmed news (31 Jul 11:40 to 13:00, the hour of the news not verified) and the mobilization at the expiry of the 12-hour ultimatum (1 Aug); the Kaiser's attempt of 1 Aug to stop the western deployment, refused (Mombauer) |
| `western_timetable` | GER | `war_GER_RUS == war and (belgium == neutral or war_GER_FRA == peace)` | 1 | `ultimatum_belgium`, `declare_war_FRA` | the deployment plan's timetable: the Liège coup de main on the first days of mobilization (Ludendorff's brigade), the note to Belgium prepared from 26 Jul, Luxembourg occupied on the first mobilization day (2 Aug) (Mombauer; Albertini vol. III) |
| `liege` | Nature | `belgium == demanded and war_GER_FRA == war` | 1 | `invade_belgium` | the entry on 4 Aug about 08:00, the morning after the refusal and the declaration on France (Albertini vol. III) |

The two German obligations are the timetable as pre-commitment (decisions D4). `mobilization_race` binds the day after a Russian general order is visible: Germany must then take a general measure (Kriegsgefahr, then mobilization one day later at the latest); its responses include `mobilize_east`, so with the coupling relaxed the obligation can be met without war. `western_timetable` makes the Belgian note and the declaration on France follow the mobilization-with-war within days ("a German choice the plan made unavoidable only through the coupling", J5). A binding fairness overrides the cadence (framework_spec.md 3.1); GER's cadence is 1, so this never matters on the realized path.

Profiles: none. `assume`: none (the four hypothesis pairs are swept).

## Delays (every delay in days, with its source)

| Step | Delay in the model | Source |
|---|---|---|
| AUH `ultimatum`: decision to delivery | 4 days (decided 19 Jul, tick 21; delivered 23 Jul, visible tick 26) | the Council of 19 Jul fixing delivery for 23 Jul 17:00 (moved to 18:00 on the day) |
| Serbian reply | at most 2 days after the delivery is visible (`reply_deadline`) | the 48-hour limit |
| RUS general mobilization: decision to order | 0 (30 Jul about 17:00, tick 32, visible 33) | the order the same afternoon |
| GER Kriegsgefahrzustand | 0, at most 1 day after the Russian order is visible (`mobilization_race`) | 31 Jul 13:00 |
| GER mobilization and the declaration on Russia | 0, the same day (one action, tick 34, visible 35) | 1 Aug about 17:00 and 19:00 |
| GER note to Belgium | at most 1 day after the mobilization is visible (`western_timetable`) | 2 Aug 19:00 |
| GER declaration on France | at most 2 days after the mobilization is visible (`western_timetable`, which binds again the day after a response) | 3 Aug 18:45 |
| Entry into Belgium | at most 1 day after the note and the declaration on France are both visible (`liege`) | 4 Aug about 08:00 |
| GBR ultimatum to war | 0 (the ultimatum expired the same day) | 4 Aug 23:00 |

The model has one `delay` (the ultimatum's); the timetable's other steps are obligations with a bounded window rather than delays, because the plan's steps were dated by the mobilization days but each was still issued by a German act, and a delayed effect in the DSL cannot be staggered over several days.

## Parameter budget (v0, `CompiledModel.budget()`)

| Item | v0 |
|---|---|
| Declared variables / levels | 15 / 42 (war_GBR_GER folded into `commitment_GBR`) |
| Built-in variables | 8 (`tick`, `pending_AUH_ultimatum`, four fairness counters, `cadence_AUH`, `cadence_FRA`) |
| Actions (AUH, GER, RUS, FRA, GBR) | 22 (6, 7, 4, 2, 3) |
| Nature events | 4 |
| Guards (non-trivial) / guard parts | 26 / 54 |
| Hypothesis gates [H] | 2 (`GER.kriegsgefahr`, `RUS.mobilize_general`) |
| Speculative actions | 0 |
| Delayed actions | 1 (`AUH.ultimatum`, 4) |
| Fairness / profiles / `assume` | 4 / 0 / 0 |
| Actors with cadence k >= 2 (`cadence`) | 2 (AUH 3, FRA 2) |
| Date-coded parts | 4 for three constraints (`AUH.ultimatum:council`, `AUH.mobilize_partial:harvest_leave`, `FRA.covering_troops:in_paris` and `FRA.mobilize:in_paris`) |
| Constant-false parts | 1 (`GER.mobilize_east:coupling`) |
| Invariants / endings | 2 / 4 |
| Reachable states from tick 0 (four pairs, explicit) | 181,913 (J7 build: 73,937) |

## v1 additions (2026-10-24)

Written for the v1 model step (`models/july1914/v1.py`) after the v1 registration ([july1914_testbed.md](july1914_testbed.md) section 8, owner's decision 2h of 2026-10-23) and before any of J1v1 to J9v1 was run; decisions in [july1914_v1_decisions.md](july1914_v1_decisions.md). Every action above holds for v1 unchanged except the three rows below, and v1 adds one action. v0 is not changed by this section.

| Action (v1) | Guard (parts) | Effect | Delay | Realized |
|---|---|---|---|---|
| AUH `tisza_consent` (new) | `council: ultimatum == resolved`; `once: tisza == opposed` | `tisza := consented` | 0 | tick 16 (14 Jul) |
| AUH `ultimatum` | `resolved: ultimatum == resolved`; `tisza: tisza == consented` (replaces `council: tick >= 16`) | `ultimatum := delivered` | 4 | tick 21 (19 Jul) |
| GER `mobilize` | [H] `hypothesis: aims_GER == continental or mob_RUS == general`; `russian_measures: mob_RUS >= partial`; `sequence: mob_GER == kriegsgefahr` | `mob_GER := general; war_GER_RUS := war` | 0 | tick 34 (1 Aug) |
| GER `mobilize_east` | [H] `hypothesis` and `russian_measures` as `mobilize`; `sequence`; `coupling: FALSE` | `mob_GER := general` | 0 | never |

- **`tisza_consent`** (v1). Source: "Tisza's consent to an ultimatum, given in conference with Berchtold on 14 Jul (Berchtold's report to Franz Joseph of 14 Jul), with the condition of territorial disinterest adopted by the Council of 19 Jul. The documented alternative, withholding consent (AUH idle), is Tisza's course of 1 to 8 Jul: the memorandum of 1 Jul; the dissent at the Council of 7 Jul; the memorandum of 8 Jul (Geiss, documents of 1, 7, 8 and 14 Jul, numbers not verified; Albertini vol. II ch. 4; Clark ch. 9; Otte ch. 3; McMeekin, *July 1914*, 2013)." Not speculative: the alternative is documented. `council`: the consent was to the course the Council of 7 July had decided. Tisza is not a principal (testbed 8.2 item 2); the action is under AUH's cadence (3), which the record's gaps (7 and 5) satisfy.
- **`ultimatum`** (v1). Source as v0, with part `tisza` read from the decision (`AUH.tisza_consent`) instead of from its date. The part is renamed so that `AUH.ultimatum:council` keeps one meaning (v0's date part) across the two models.
- **`mobilize`** (v1). Source as v0, plus: "the order was given at the expiry of the twelve-hour ultimatum of 31 Jul demanding that Russia demobilize (Geiss; Mombauer (ed.), *The Origins of the First World War: Diplomatic and Military Documents*, 2013). [H]: under localize only after a Russian general mobilization order (Bethmann's insistence that Russia be seen to move first: his statement to the Prussian State Ministry of 30 Jul; Müller's diary of 1 Aug; Mombauer 2001; Clark ch. 11); under continental the Russian partial measures suffice (Moltke's memorandum of 28 to 29 Jul and his telegram to Conrad of 30 Jul; Mombauer 2001 and 2013; Otte)." `russian_measures` as for the Kriegsgefahr.
- **`mobilize_east`** (v1). Source as v0; the two new parts as `mobilize`, so that relaxing `GER.mobilize_east:coupling` still relaxes the war effect only (J2v1).

Not added (testbed 8.5, open for the owner): a part by which a Russian mobilization step answers a measure of another power.

Data: `data/july1914/v1/realized_moves.csv` and `decisions.csv` (v0's, with AUH `tisza_consent` at tick 16), `data/july1914/v1/events.csv` (the dated observations of `tisza`).

Parameter budget (v1, `CompiledModel.budget()`): declared variables / levels 16 / 44; built-in variables 8; actions 23 (AUH 7, GER 7, RUS 4, FRA 2, GBR 3) and Nature events 4; guards / guard parts 27 / 60; hypothesis gates [H] 4 (`GER.kriegsgefahr`, `GER.mobilize`, `GER.mobilize_east`, `RUS.mobilize_general`); speculative 0; delayed actions 1; fairness / profiles / `assume` 4 / 0 / 0; cadence 2 (AUH 3, FRA 2); date-coded parts 3 (`AUH.mobilize_partial:harvest_leave`, `FRA.covering_troops:in_paris`, `FRA.mobilize:in_paris`); constant-false parts 1; invariants / endings 2 / 4; reachable states from tick 0 (four pairs, explicit) 193,721 (J7v1 build: 83,829); fingerprints `836afdb695b7` (daily build `3b23e6bec46e`).
