# Was there a documented German exit from the eastern war? (owner's question, decision 1, 2026-10-15)

The question for T6: once Germany had attacked the USSR, did the record contain a debated German alternative to fighting on, such that the model's point of no return (the attack itself, 1941Q3) rests on a missing action rather than on the record? Web search of 2026-10-15; the secondary literature as it reports the documents. Nothing here edits a guard; the content decision is at the end.

## What the record shows

**German side: the alternative was put to Hitler and refused, three times.**
- After Stalingrad's encirclement, Ribbentrop urged Hitler to approach the Soviet embassy in Stockholm (late 1942); Hitler refused, saying a moment of weakness was not the time to deal with the enemy (as reported in the secondary accounts; Ribbentrop's postwar memoir is the German source, with Goebbels's diary on his own and Ribbentrop's interest).
- Japan pressed Germany hardest in 1943 to open separate-peace talks with Moscow; on 29 July 1943 Hitler told Ambassador Oshima he would fight on, citing Ukrainian grain and his belief that the Soviets could still be beaten (Oshima's reports, read through the decrypts; declassified 1978).
- In September 1943 Goebbels raised a separate peace with Hitler and was told the moment was not right (Goebbels's diary, Sept 1943; the entries themselves were not found online, only the secondary accounts).

**Contacts in Stockholm, 1942 to 1944: real as contacts, disputed as policy.**
- Peter Kleist (Ribbentrop's office) describes indirect contacts through the Baltic German businessman Edgar Clauss with a Soviet official he names Alexandrov, in December 1942 and June and September 1943; Kleist never met a Soviet official and Clauss died soon after the war, so the account rests on Kleist's memoir. Koch (1975) follows Kleist; Mastny (1972) reads the March 1943 talks as a low-level Soviet initiative broken off in May.
- One contemporaneous document: a US telegram of 1943 (FRUS 1943 vol. I, document 504) reporting German industrialists' attempts to reach Soviet representatives in Stockholm, the intermediary saying he acted on Kleist's instructions and that the Germans would accept even the 1914 frontiers. It records a German approach, not a Soviet decision.
- Stalin ridiculed the idea of a separate peace to the American ambassador at the Moscow Conference, October 1943.

**Soviet side, 1941: the Stamenov feeler.** Beria, on Stalin's order, had Sudoplatov sound the Bulgarian minister Stamenov in the first weeks of the war on what Hitler would take to stop (Ukraine, the Baltic, perhaps more). The evidence is the 1953 interrogations of Beria and Sudoplatov and Stamenov's 1953 note; Petrov's archival reading (2016) accepts it; there is no contemporaneous Soviet decision record and no German reaction (Hitler ignored what was passed on, if anything was).

## Reading for the model

1. **A German exit was a documented alternative and was refused.** That is a German decision, dated (Dec 1942, 29 Jul 1943, Sept 1943). Under the feasibility principle it belongs in the decision space as a non-speculative German action: an *offer* of terms in the East, which Hitler could have made and did not. The model has `negotiate_east`, which needs a Soviet feeler first; it has no German offer.
2. **Soviet acceptance has no contemporaneous decision record.** The 1941 feeler is known from 1953 interrogations, the 1943 contacts from a memoir and one Western intelligence report of a German approach. Historians disagree on whether either was policy. A Soviet acceptance of German terms therefore stays speculative, as `seek_terms_east` is.
3. **Consequence for T6.** A German offer the USSR may refuse gives Germany no exit it can force; the point of no return, which is a forcing question, stays at the attack. What changes is the account: the model will say that Germany had a documented exit option and that it was never Germany's to force, because it needed a Soviet decision for which the record has no document.

## Content decision (architect, under the owner's decision 1)

Add `GER.offer_terms_east` (guard parts `at_war: east_war`, `once: not east_offer`; effect `east_offer := True`; source: Ribbentrop's proposal of late 1942 and Hitler's refusal; Hitler to Oshima, 29 Jul 1943; Goebbels's diary, Sept 1943) and `USSR.accept_terms_east` (guard parts `offer: east_offer`, `no_separate_peace: not anglo_soviet_alliance`; effect `east_peace := True`; **speculative**: no Soviet decision record; the Stockholm contacts of 1943 as the nearest evidence). `negotiate_east` and `seek_terms_east` stay as they are. This is a guard change after first sight, made on the owner's instruction from the record above, logged in the guard changelog with these sources, with the whole suite rerun; the report states which results came after it.

## Sources

- [Koch, "The Spectre of a Separate Peace in the East: Russo-German 'Peace Feelers', 1942-44", Journal of Contemporary History, 1975](https://journals.sagepub.com/doi/abs/10.1177/002200947501000308)
- [FRUS 1943 vol. I, document 504 (Stockholm, German approaches)](https://history.state.gov/historicaldocuments/frus1943v01/d504)
- [Washington Post, "Japan Sought a German-Soviet Peace, War Data Show", 12 Sept 1978 (Hitler to Oshima, 29 Jul 1943)](https://www.washingtonpost.com/archive/politics/1978/09/12/japan-sought-a-german-soviet-peace-war-data-show/272de6f8-8528-4514-895e-9dcaebea7d94/)
- [Novaya Gazeta, Petrov on the Stamenov feeler of 1941 (archival reading, 2016)](https://novayagazeta.ru/articles/2016/06/17/68966-stalin-v-1941-godu-byl-gotov-otdat-gitleru-pribaltiku-i-ukrainu)
- [Euromaidan Press summary of Petrov's reading](https://euromaidanpress.com/?p=94487)
- [Axis History Forum thread summarizing Mastny (1972) on the March 1943 Stockholm talks](https://forum.axishistory.com/viewtopic.php?t=133177) (a forum summary; check against Mastny, American Historical Review, 1972)
- [histclo.com essay on the Nazi-Soviet peace feelers (secondary, poorly transcribed; used only for Ribbentrop's and Goebbels's positions)](https://www.histclo.com/essay/war/ww2/cou/sov/ns-peace.html)
- [Wikipedia, "Peace efforts during World War II"](https://en.wikipedia.org/wiki/Peace_efforts_during_World_War_II)
