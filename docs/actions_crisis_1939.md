# The summer-1939 crisis sub-game: action catalogue

Status: written by the historian with [ontology_crisis_1939.md](ontology_crisis_1939.md), after K1 to K6 were registered (docs/crisis_1939_testbed.md) and before any of them was run; K2 is the hold-out claim. Every guard, effect, delay, fairness constraint and profile below was written from the record before first sight. After first sight none of them changes without a row in [guard_changelog_ww2.md](guard_changelog_ww2.md) giving a dated source, and a full rerun of tests/ww2/crisis_1939. The code is `models/ww2/crises/summer_1939.py`; the `source=` text of each action is quoted there in full and summarized here. Abbreviations as in the ontology.

## The feasibility principle

As v0 and v1: a guard says when an action was feasible (a prior condition, an institutional constraint, a planning date), never what the actor would prefer. Every action carries `source=` naming the dated record in which the alternative was debated, planned or taken; an action without such a record is `speculative=True`. A conjunct on a hidden objective is a hypothesis gate [H] named `hypothesis`. Guards are declared as named parts, so that each is a separate relaxable assumption `<actor>.<action>:<part>`. Behaviour enters only through named profiles.

## Conventions

1. **Ticks and placement.** Three-day ticks (ontology section 0). A decision is placed in the tick that contains its date; where one actor has two decisions in one tick, the realized file keeps the one the claims need and notes the other (two such cases: the USSR at tick 15, GER at tick 17; decisions C2).
2. **[SQR].** A reaction to another actor's decision of the same tick sits one tick later only where its guard reads that decision. On the realized path: WEST's declaration reacts to the attack of tick 19 and falls at tick 20, the horizon (decisions C3). The halt of 25 Aug reacts to the treaty and Mussolini's letter of the same tick, but its guard does not read them, so it sits at tick 17.
3. **[NSL].** Nature plays one event per tick. The realized Nature events (the refusal, 19 to 20 Aug, tick 15; the partial mobilization, 23 Aug, tick 16; Mussolini's letter, 25 Aug, tick 17; the general mobilization, 29 to 30 Aug, tick 18) fall in four different ticks, so no [NSL] placement is needed.
4. **Raising a belief.** `belief_GER` only rises; a raise is `SetIf(belief_GER < level, belief_GER, level)` so that it never lowers the variable and composes with the one `Set` (WEST's `declare_war`, a WEST action, so the two are never in one joint move).
5. **No hidden objective of its own.** `aims_GER` and `aims_USSR` come from the entry map.

## Germany (`GER`)

| Action | Guard (parts) | Effect | Delay | Speculative? |
|---|---|---|---|---|
| `open_approach` | `first: german_approach == none`; `free: not alliance` | `german_approach := opened` | 0 | no |
| `propose_pact` | `opened: german_approach == opened`; `free: not alliance` | `german_approach := pact_proposed` | 0 | no |
| `order_attack` | `standing: attack_order in {none, cancelled}` | `attack_order := ordered` | 0 | no |
| `cancel_attack` | `standing: attack_order == ordered` | `attack_order := cancelled` | 0 | no |
| `attack_poland` | [H] `hypothesis: aims_GER == hegemonic`; `order: attack_order in {ordered, cancelled}`; `readiness: tick >= 17` | `attack_order := launched` | 0 | no |

- **`open_approach`.** Source: Weizsäcker's instruction to Schulenburg of 30 May 1939 to open political talks (DGFP vol. VI); Schnurre's dinner with Astakhov and Barbarin, 26 Jul 1939 (Schnurre's memorandum of 27 Jul; NSR); Ribbentrop to Astakhov, 2 Aug, and Schulenburg's instructions of 3 Aug 1939. `free`: v1's `propose_pact_ussr` has the same condition (no German approach once an Anglo-Soviet alliance exists); it is a prior condition, not a preference, because the approach's object, Soviet neutrality in a German-Polish war, is foreclosed by the alliance.
- **`propose_pact`.** Source: Ribbentrop to Schulenburg, 14 Aug 1939, read to Molotov on 15 Aug (no question "between the Baltic and the Black Sea" that cannot be settled; Ribbentrop ready to come to Moscow); Ribbentrop to Schulenburg, 16 Aug (a non-aggression pact for 25 years, a joint guarantee of the Baltic states); Hitler's telegram to Stalin, 20 Aug 1939, accepting the Soviet draft and the protocol (NSR; DGFP vol. VII). This is "Germany's proposal of a protocol" of K6: the settlement of spheres that Molotov's "special protocol" of 17 Aug asked for, offered from 14 to 16 Aug and accepted in Hitler's telegram of 20 Aug.
- **`order_attack`.** Source: Case White, the order of 25 Aug 1939, 15:02, for the attack at 04:30 on 26 Aug (Halder's war diary, 25 Aug; DGFP vol. VII); Y-day fixed for 26 Aug on 23 Aug (Halder's diary; not verified); the new date of 1 Sep recorded by Halder on 29 Aug (not verified). No date part: an order fixes a future day; the date constraint is on the execution (`attack_poland:readiness`).
- **`cancel_attack`.** Source: Hitler's halt order of 25 Aug 1939, about 19:30, after Mussolini's letter and the news of the Anglo-Polish treaty (Halder's war diary, 25 to 26 Aug; Ciano's diary, 25 Aug; Schmidt, *Statist auf diplomatischer Bühne*, 1949, postwar). The guard reads only the standing order: the halt was feasible at any time before the troops crossed (some units did not receive it in time on 26 Aug, the Jablunka pass incident; not verified).
- **`attack_poland`.** Source: Case White directive of 3 Apr 1939 (Nuremberg document C-120: operations possible "at any time from 1.9.39"), advanced to 26 Aug; the conference of 23 May 1939 (L-79); Directive No. 1 for the Conduct of the War, 31 Aug 1939, 12:40, and the attack at 04:45 on 1 Sep 1939 (Trevor-Roper (ed.), *Hitler's War Directives 1939-1945*). Parts: `hypothesis` is v1's [H] gate. `order`: the attack executes an order given at least once (a standing order, or a halted one with the deployment kept): the re-order of 31 Aug and the attack of 1 Sep fall in one tick (19) and are one decision (decisions C4). `readiness`: Case White's date of readiness (1 Sep, fixed on 3 Apr) as advanced by the order of 23 Aug to 26 Aug, the earliest day the record shows the army deployed to attack; 26 Aug is in tick 17. The record never shows an earlier feasible day (K5). v1's `army_ready` and `target` parts hold at entry and throughout (structure is frozen; `attack_order` replaces `poland` as the target state) and are not repeated.

## The West (`WEST`)

| Action | Guard (parts) | Effect | Delay | Speculative? |
|---|---|---|---|---|
| `send_missions` | `political: talks == political` | `SetIf(talks == political, talks, military)` | 5 | no |
| `authorize_convention` | `in_session: talks in {military, adjourned}`; `once: not west_powers` | `west_powers := True` | 0 | no |
| `warn_germany` | `guarantee: british_treaty != none` | `belief_GER := max(belief_GER, uncertain)` | 0 | no |
| `sign_treaty` | `once: british_treaty == guarantee` | `british_treaty := treaty`; `belief_GER := max(belief_GER, will_fight)` | 0 | no |
| `declare_war` | `attack: attack_order == launched`; `guarantee: british_treaty != none`; `once: not war_declared` | `war_declared := True`; `belief_GER := will_fight` | 0 | no |

- **`send_missions`.** Source: the Soviet draft of 2 Jun 1939 (political and military agreements to enter into force together) and Molotov's demand of 17 Jul for immediate military talks; the British and French agreement of 23 to 25 Jul 1939 (DBFP vol. VI); Chamberlain in the Commons, 31 Jul; the missions sailed on 5 Aug and opened the talks in Moscow on 12 Aug 1939 (DBFP vol. VII, appendix II). Delay 5 (`decisions.csv`): decided at tick 6, in session at tick 12, the realized pace (the missions were constituted between 26 Jul and 2 Aug and went by sea). The effect is conditional so that the delayed arrival cannot reopen talks the USSR broke off in the meantime.
- **`authorize_convention`.** Source: Daladier's instruction to General Doumenc of 21 Aug 1939 to sign a military convention subject to the government's approval (DDF vol. XVIII; not verified); the British delegation's written powers, requested by Voroshilov on 12 Aug and sent from London on 21 Aug (DBFP vol. VII; not verified). The Soviet side would not sign with delegations that could not sign (12 Aug), so the authority is a prior condition of `conclude_alliance`.
- **`warn_germany`.** Source: Chamberlain's letter to Hitler of 22 Aug 1939, delivered by Henderson at Berchtesgaden on 23 Aug ("His Majesty's Government are determined to fulfil their obligation to Poland"), and Hitler's reply of 23 Aug (DBFP vol. VII; Cmd. 6106); earlier: Halifax's Chatham House speech, 29 Jun 1939. The letter raises the belief only to `uncertain`: Hitler's reply and the Obersalzberg address of the day before show no change in Berlin's expectation (the rule's will_fight needs a German decision record that treats war with the West as the consequence).
- **`sign_treaty`.** Source: Agreement of Mutual Assistance between the United Kingdom and Poland, London, 25 Aug 1939 (Cmd. 6106), announced on 6 Apr 1939 and negotiated from April; its news reached Hitler on the afternoon of 25 Aug (Halder's diary, 25 Aug; Schmidt, postwar). No date part: the text was under negotiation from April and the record shows no condition that kept it from being signed earlier (the acceleration after 23 Aug was a choice). The belief raise is the treaty's documented effect in Berlin: the halt of the same evening and the search for a way to detach Britain (ontology section 3).
- **`declare_war`.** Source: the Anglo-French warnings of 1 Sep 1939; the Cabinet of 2 Sep, 23:30, deciding the ultimatum; the British declaration of 3 Sep, 11:00, and the French of 3 Sep, 17:00 (CAB 23/100; HC Deb 1 to 3 Sep 1939); against Mussolini's proposal of a conference, 31 Aug to 2 Sep (Bonnet's support; DBFP vol. VII). Effects as v1's `declare_war` on the sub-game's variables; the coarse ones are set by the exit map.

## The Soviet Union (`USSR`)

| Action | Guard (parts) | Effect | Delay | Speculative? |
|---|---|---|---|---|
| `ask_passage` | `in_session: talks == military`; `first: passage == unasked` | `passage := asked` | 0 | no |
| `adjourn_talks` | `in_session: talks == military` | `talks := adjourned` | 0 | no |
| `break_talks` | `open: talks in {military, adjourned}`; `no_alliance: not alliance` | `talks := broken` | 0 | no |
| `accept_pact` | `proposal: german_approach == pact_proposed`; `free: not alliance` | `german_approach := pact` | 0 | no |
| `conclude_alliance` | `no_pact: german_approach != pact`; `in_session: talks in {military, adjourned}`; `powers: west_powers`; `passage: passage == granted`; `once: not alliance` | `alliance := True` | 0 | no |
| `conclude_without_passage` | `no_pact`; `in_session`; `powers`; `no_consent: passage != granted`; `once: not alliance` | `alliance := True` | 0 | **yes** |

- **`ask_passage`.** Source: Voroshilov's "cardinal question" to the missions, 14 Aug 1939: would Soviet forces be allowed through the Vilna corridor, Galicia and Romania (DBFP vol. VII, appendix II; the Soviet record in *Dokumenty vneshnei politiki* 1939, vol. XXII; not verified).
- **`adjourn_talks`.** Source: Voroshilov's adjournment of 17 Aug 1939 until answers came from London, Paris and Warsaw (DBFP vol. VII, appendix II).
- **`break_talks`.** Source: Voroshilov's adjournment sine die, 21 Aug 1939, and his statement to Doumenc of 22 Aug that the political situation had changed; the missions left on 25 Aug (DBFP vol. VII; Doumenc's report, not verified).
- **`accept_pact`.** Source: Molotov to Schulenburg, 17 Aug (a pact with a "special protocol") and 19 Aug 1939 (the Soviet draft; Ribbentrop received for 26 to 27 Aug); the credit agreement of 19 Aug; Stalin's reply to Hitler, 21 Aug; the non-aggression pact and secret protocol signed in the night of 23 to 24 Aug 1939 (NSR; DGFP vol. VII). The Soviet decision of 19 to 21 Aug (tick 15); the signature is its effect at tick 16. `proposal`: the Soviet government asked for, and answered, a German proposal; the record shows no Soviet offer of a pact before one (Molotov's replies of 15, 17 and 19 Aug answer Ribbentrop's telegrams). `free`: as v1's `accept_pact`.
- **`conclude_alliance`.** Source: the Soviet condition of 14 Aug 1939: a military convention once passage through Poland and Romania is granted (Voroshilov; DBFP vol. VII, appendix II); the Soviet draft treaty of 2 Jun 1939 and Molotov's position of 17 Jul that the political and military agreements be signed together. `in_session`: a convention is concluded by the military talks (adjourned talks could reconvene, as they did on 21 Aug). `powers`: the Soviet demand of 12 Aug for written powers to sign.
- **`conclude_without_passage`** (speculative). Source: none. Voroshilov on 14 and 21 Aug made passage a condition of any convention, and I know of no Soviet record of a willingness to conclude without Polish consent. Speculative by the architect's decision; its use is reported separately in every result (the profile `documented_only` forbids it).

## Nature (Poland and Italy)

| Event | Guard | Effect | Speculative? |
|---|---|---|---|
| `passage_refused` | `question: passage == asked` | `passage := refused` | no |
| `passage_granted` | `question: passage == asked` | `passage := granted` | no |
| `mobilize_partial` | `first: mobilization_POL == none` | `mobilization_POL := partial` | no |
| `mobilize_general` | `partial: mobilization_POL == partial` | `mobilization_POL := general` | no |
| `italy_declines` | `first: italy_ready == unknown` | `italy_ready := not_ready` | no |

- **`passage_refused`.** Source: Beck to the French ambassador Noël, 19 Aug 1939, and the Polish General Staff's answer of 20 Aug: no Soviet troops on Polish soil (DDF vol. XVIII; DBFP vol. VII, Kennard's telegrams of 19 to 20 Aug).
- **`passage_granted`.** Source: the documented alternative pressed on Warsaw and refused: the French and British démarches of 18 to 21 Aug 1939 (Bonnet to Noël; Gamelin's message through the military attaché; Halifax to Kennard, 20 Aug); Beck's formula of 23 Aug that Polish-Soviet collaboration "is not excluded" (DDF vol. XVIII; DBFP vol. VII; not verified). Not speculative: the decision was put to the Polish government, which could have taken it.
- **`mobilize_partial`.** Source: the Polish alarm mobilization of 23 to 24 Aug 1939 (call-up of reservists in the western and northern corps areas; Polish General Staff records in *Polskie Siły Zbrojne* vol. I, not verified).
- **`mobilize_general`.** Source: general mobilization ordered 29 Aug 1939, suspended the same day at the British and French request, proclaimed on 30 Aug for 31 Aug (DBFP vol. VII, Kennard's telegrams of 29 to 30 Aug).
- **`italy_declines`.** Source: Mussolini's letter to Hitler of 25 Aug 1939: Italy not ready for war without the supplies listed on 26 Aug (DGFP vol. VII; Ciano's diary, 25 to 26 Aug); Ciano had said as much at Salzburg, 11 to 13 Aug.

The last three are inert (ontology section 4).

## Constraints

- **Fairness `polish_obligation`** (WEST, within 1 tick, response `declare_war`, trigger `attack_order == launched and british_treaty != none and not war_declared`). Source: the guarantee of 31 Mar 1939 and the Agreement of Mutual Assistance of 25 Aug 1939, article 1 (Cmd. 6106); the Cabinet of 1 to 3 Sep 1939 (CAB 23/100), which debated only the timing of the ultimatum, not whether to honour the obligation. An institutional constraint, like v1's `czech_obligation`. With an attack decided at tick t ≤ 18 it binds inside the sub-game (the declaration at t + 1); with the realized attack at tick 19 it falls due on return and the exit map applies the declaration (decisions C3).
- **Profile `deterred`** (GER; forbids `attack_poland` unless `not (belief_GER == will_fight and alliance)`): v1's profile for T9 (decisions E5), carried over with `alliance` for `anglo_soviet_alliance`. A named, relaxable behavioural assumption, not feasibility.
- **Analysis profiles** (devices for the readings, not behaviour claims): `documented_only` (USSR; forbids `conclude_without_passage`: the record's decision space), `no_belief_raise` (WEST; forbids `warn_germany` and `sign_treaty`: the belief stays at its entry level until a declaration; K2's sweep), `no_german_proposal` (GER; forbids `propose_pact`; K6).
- **Scenario fairness `scenario_passage`** (Nature, within 1, response the scenario's answer; only in `build(passage=...)`): K2's two scenarios.
- No cadence: the record gives no decision period for any principal at this resolution (the West decided on 23 to 25 Jul, 21, 22 and 25 Aug; Germany on 26 Jul, 14, 23 and 25 Aug and 31 Aug), so every actor decides every tick.

## Parameter budget (`CompiledModel.budget()`, full build, no profile)

| Item | Count | Note |
|---|---|---|
| Declared variables / levels | 13 / 37 | 2 hidden objectives, 5 negotiation, 4 Case White and belief, 2 inert |
| Built-in variables | 3 | `tick`, `pending_WEST_send_missions`, `fair_polish_obligation` |
| Actions GER, WEST, USSR / Nature events | 5, 5, 6 / 5 | 21 in all |
| Guards (non-trivial) / guard parts | 21 / 39 | one hypothesis gate, one date part (`attack_poland:readiness`) |
| Speculative actions | 1 | `USSR.conclude_without_passage` |
| Delayed actions | 1 | `WEST.send_missions`, 5 ticks |
| Fairness constraints | 1 | `polish_obligation` (+ `scenario_passage` in the two scenario builds) |
| Profiles | 4 | `deterred` (behaviour), three analysis devices |
| Latches / assumes / cadence | 0 / 0 / 0 | |
| Invariants / endings | 3 / 2 | analysis predicates |
| State space bound | 111,476,736 | 80,956 states reachable from the entry state (explicit engine) |

The reduced build (`build(inert=False)`): 11 variables, 32 levels, 18 actions, 18 guards, 36 guard parts, 13,504 states reachable from the entry state.
