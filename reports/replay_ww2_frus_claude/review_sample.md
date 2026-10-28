# Review sample: Claude backend, FRUS replay 1936 to 1940

The sample of the owner's decision 7a (docs/owner_decisions_2026-10-23.md): the proposals that
decide the metrics of `metrics_claude.md`, and a random check of the rest, for a human review
before the phase 2 gate is decided. Nothing here is decided: every proposal is still
`pending` in `proposals/`. Built by `python scripts/build_review_sample.py` (seed 20261027);
the same rows are in `review_sample.csv`, whose `decision` (accept or reject) and `note`
columns are for the reviewer. `python scripts/apply_review.py FILLED.csv [--skip-blank]
[--out ~/wf_runs/frus_claude_reviewed]` applies the filled sheet to a copy of `proposals/`
(never to this directory) with `wf review`, then re-measures; a row without a decision is
refused unless `--skip-blank` leaves it pending.

## How the unreviewed proposals are counted (read this first)

`wf replay --metrics-only` does **not** count pending proposals, and with a sample it measures
nothing. It reads only the replay snapshots that `wf review` writes, and `wf review` writes
the snapshot of a quarter only when no proposal of that quarter or of any earlier quarter is
still pending (a held or blocked proposal excepted), and removes it otherwise
(docs/replay_harness.md, "Review"). With 2494 proposals of which 113 are in this sample,
every quarter from 1936Q1 keeps pending proposals, so after the review no snapshot exists and
`--metrics-only` reports all twenty quarters as "not compared". It measures the reviewed
evidence only once every proposal has been decided.

`wf replay --measure-proposals` (the measurement of `metrics_claude.md`) counts every proposal
as accepted **whatever its status**: a rejected proposal still counts. It would not see the
review either.

The measure set up for a partly reviewed run is therefore `wf replay --measure-proposals
--drop-rejected` (added for this; docs/replay_harness.md, "Replay and metrics"): the rejected
proposals are left out as if never proposed (so a rejected document no longer counts under
`two-document` either), the accepted and the pending ones count as accepted, and a
`retrospective?` proposal is applied only if the reviewer accepted it. Its report says on its
first line how many proposals were accepted, rejected and left pending. It is still a
proposal-level measurement, not a replay snapshot: it shows what the metrics become once the
reviewer's rejections are taken out, with the 2381 unreviewed proposals as the backend read
them. `scripts/apply_review.py` runs both: `--measure-proposals --drop-rejected` (the
re-measure) and `--metrics-only` (kept for the record; with a sample it compares nothing).

Under `--drop-rejected`, rejecting the proposal that set a level lets the next pending proposal
of the same level set it (for a structural variable, from a second document). That is why
category (c) lists, besides the indicators, the other proposals of the replayed level inside
each disagreeing run: a false flip goes away only if every proposal carrying it is rejected.

## The sample

| Category | Proposals |
|---|---|
| (a) Documented flips: the proposals that set the replayed level | 43 |
| (b) False flips: the proposals that set the replayed level | 5 |
| (c) Disagreeing quarters: the proposals behind the replay level | 25 |
| (d) Random check of the remaining counted proposals | 40 |
| all | 113 |

Category (a) covers every replayed flip that answers a documented flip, all variables of the
flips table (the four belief and commitment variables: 9; the structural variables:
34). For a variable under the `two-document` rule, both the proposal that carried the
flip and the first document it needed are listed (`harness: corroborating`). Category (d) is
drawn from the 2400 proposals counted by the measurement and not in (a) to (c) (held,
blocked and `retrospective?` proposals are not counted, so not drawn), stratified by the
quarter of their file with proportional allocation.

A proposal in several categories is listed once, under the first; `why` gives every reason.
`hindsight` is the level of the hindsight snapshot at the end of the quarter of the proposal's
date (and of its file's quarter, where that differs). `harness` is the measurement's gate at
the end of 1940Q4 (and at the end of the file's quarter, where that differs). Under the rules,
`wf review --accept` refuses a held or blocked proposal; it can be rejected.


## (a) Documented flips: the proposals that set the replayed level: 43

### 1936Q1

**1936Q1-023** · `rhineland` = **remilitarized** (hindsight: remilitarized (1936Q1 end))

- File: `proposals/1936Q1.json`; document `frus:frus1936v01/d179`, dated 1936-03-07: The Ambassador in Germany (Dodd) to the Secretary of State; proposal dated 1936-03-07
- Quote: "the symbolical act of the entry into the demilitarized zone this noon of several battalions of the regular army"
- Rule: claude backend: Remilitarized means German troops in the zone; the 4 p.m. telegram reports the German Foreign Office's account of regular army battalions entering the zone at noon, and the memorandum read in the Reichstag states that full sovereignty in the zone has been restored.
- Confidence: medium; harness: ok: a flip
- Why sampled: sets the documented flip rhineland -> remilitarized (replayed 1936Q1, documented 1936Q1)
- FRUS: <https://history.state.gov/historicaldocuments/frus1936v01/d179>
- Decision: ______ Note: ______

**1936Q1-064** · `treaty` = **dead** (hindsight: dead (1936Q1 end))

- File: `proposals/1936Q1.json`; document `frus:frus1936v01/d221`, dated 1936-03-20: The Minister in Norway (Biddle) to the Secretary of State; proposal dated 1936-03-20
- Quote: "France and Great Britain will take no action against Germany and German troops will not be withdrawn from the Rhineland"
- Rule: claude backend: Dead requires the zone reoccupied and the guarantors declining enforcement; the source reports that the guarantors will not act, but this is a forecast rather than a recorded decision.
- Confidence: low; harness: ok: a flip
- Why sampled: sets the documented flip treaty -> dead (replayed 1936Q1, documented 1936Q1)
- FRUS: <https://history.state.gov/historicaldocuments/frus1936v01/d221>
- Decision: ______ Note: ______

### 1936Q4

**1936Q4-008** · `axis` = **true** (hindsight: true (1936Q4 end))

- File: `proposals/1936Q4.json`; document `frus:frus1936v02/d494`, dated 1936-10-31: The Ambassador in Italy (Phillips) to the Secretary of State; proposal dated 1936-10-31
- Quote: "the Italian and German Governments would recognize the Franco Government as soon as it had entered Madrid ... Berlin and Rome were in accord"
- Rule: claude backend: Axis rule (Rome-Berlin alignment): the Italian Foreign Minister, just back from Berlin, reports joint German-Italian policy and full accord. The document does not mention the October Protocols, and the Milan speech is only announced for the next day.
- Confidence: low; harness: corroborating: two-document: corroborates the flip carried by 1936Q4-012
- Why sampled: first of two documents for the documented flip axis -> true (replayed 1936Q4, documented 1936Q4)
- FRUS: <https://history.state.gov/historicaldocuments/frus1936v02/d494>
- Decision: ______ Note: ______

**1936Q4-012** · `axis` = **true** (hindsight: true (1936Q4 end))

- File: `proposals/1936Q4.json`; document `frus:frus1936v01/d288`, dated 1936-11-14: The Ambassador in Germany (Dodd) to the Secretary of State; proposal dated 1936-11-14
- Quote: "the Italo-German “axis” which while undoubtedly meaning close Italo-German cooperation in certain situations"
- Rule: claude backend: The axis flag is the Rome-Berlin alignment, and the ambassador describes an existing Italo-German 'axis' and rapprochement entailing close cooperation, though he does not cite the protocol text.
- Confidence: medium; harness: ok: two-document: corroborated by frus:frus1936v02/d494
- Why sampled: sets the documented flip axis -> true (replayed 1936Q4, documented 1936Q4)
- FRUS: <https://history.state.gov/historicaldocuments/frus1936v01/d288>
- Decision: ______ Note: ______

**1936Q4-013** · `anticomintern` = **true** (hindsight: true (1936Q4 end))

- File: `proposals/1936Q4.json`; document `frus:frus1936v01/d304`, dated 1936-11-17: The Chargé in the Soviet Union (Henderson) to the Secretary of State; proposal dated 1936-11-17
- Quote: "the Japanese and German Governments have signed a declaration calling for an international campaign against Communism"
- Rule: claude backend: The anticomintern flag is set by a German-Japanese anti-Comintern agreement; Litvinov relays the Japanese Foreign Minister's admission that such a declaration has been signed, but the report is second-hand and the secret agreement is only said to be initialled.
- Confidence: low; harness: corroborating: two-document: corroborates the flip carried by 1936Q4-018
- Why sampled: first of two documents for the documented flip anticomintern -> true (replayed 1936Q4, documented 1936Q4)
- FRUS: <https://history.state.gov/historicaldocuments/frus1936v01/d304>
- Decision: ______ Note: ______

**1936Q4-018** · `anticomintern` = **true** (hindsight: true (1936Q4 end))

- File: `proposals/1936Q4.json`; document `frus:frus1936v01/d312`, dated 1936-11-25: The Ambassador in Germany (Dodd) to the Secretary of State; proposal dated 1936-11-25
- Quote: "Both agreement and protocol were signed by Ribbentrop and the Japanese Ambassador today."
- Rule: claude backend: The anticomintern flag is set by the signing of the German-Japanese Anti-Comintern Pact on 25 Nov 1936, which the passage reports as done today.
- Confidence: high; harness: ok: two-document: corroborated by frus:frus1936v01/d304
- Why sampled: sets the documented flip anticomintern -> true (replayed 1936Q4, documented 1936Q4)
- FRUS: <https://history.state.gov/historicaldocuments/frus1936v01/d312>
- Decision: ______ Note: ______

### 1937Q3

**1937Q3-018** · `china_war` = **true** (hindsight: true (1937Q3 end))

- File: `proposals/1937Q3.json`; document `frus:frus1937v01/d800`, dated 1937-08-11: Memorandum by the Chargé in Turkey (Washington) of a Conversation With the Turkish Foreign Minister (Tevfik Rüstü Aras) at Yalova, August 11, 1937; proposal dated 1937-08-11
- Quote: "He then turned to the Far Eastern crisis... the danger of another nation becoming involved in the Chinese-Japanese difficulties"
- Rule: claude backend: china_war is true when Japan's army is engaged in a general war in China from July 1937; the passage refers to an ongoing Sino-Japanese conflict that other powers might be drawn into, but it does not explicitly describe a general war.
- Confidence: low; harness: corroborating: two-document: corroborates the flip carried by 1937Q3-025
- Why sampled: first of two documents for the documented flip china_war -> true (replayed 1937Q3, documented 1937Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1937v01/d800>
- Decision: ______ Note: ______

**1937Q3-025** · `china_war` = **true** (hindsight: true (1937Q3 end))

- File: `proposals/1937Q3.json`; document `frus:frus1937v01/d76`, dated 1937-08-31: Memorandum by the Ambassador in Italy (Phillips); proposal dated 1937-08-31
- Quote: "the Japanese attack on Shanghai and the great number of civilians killed through promiscuous bombing"
- Rule: claude backend: china_war is true when Japan's army is engaged in a general war in China, including fighting at Shanghai from 13 Aug 1937; the memorandum reports the Japanese attack on Shanghai and the bombing of civilians as current events.
- Confidence: medium; harness: ok: two-document: corroborated by frus:frus1937v01/d800
- Why sampled: sets the documented flip china_war -> true (replayed 1937Q3, documented 1937Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1937v01/d76>
- Decision: ______ Note: ______

### 1938Q1

**1938Q1-056** · `austria` = **annexed** (hindsight: annexed (1938Q1 end))

- File: `proposals/1938Q1.json`; document `frus:frus1938v01/d440`, dated 1938-03-12: The Minister in Czechoslovakia (Carr) to the Secretary of State; proposal dated 1938-03-12
- Quote: "Entry German troops into Austria last night preceded by Schuschnigg resignation"
- Rule: claude backend: The annexed rule needs German troops in Austria and the reunification law in force; the passage reports the troop entry but not the law, so it meets only half of the threshold.
- Confidence: low; harness: corroborating: two-document: corroborates the flip carried by 1938Q1-058
- Why sampled: first of two documents for the documented flip austria -> annexed (replayed 1938Q1, documented 1938Q1)
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d440>
- Decision: ______ Note: ______

**1938Q1-058** · `austria` = **annexed** (hindsight: annexed (1938Q1 end))

- File: `proposals/1938Q1.json`; document `frus:frus1938v01/d442`, dated 1938-03-12: The Ambassador in Germany (Wilson) to the Secretary of State; proposal dated 1938-03-12
- Quote: "Goebbels announced that the “troops” first entered Austria at 5:30 this morning."
- Rule: claude backend: The annexed rule needs German troops in Austria and the reunification law in force; the passage shows the troops have entered, but the document reports no reunification law, only a plebiscite still to be held.
- Confidence: low; harness: ok: two-document: corroborated by frus:frus1938v01/d440
- Why sampled: sets the documented flip austria -> annexed (replayed 1938Q1, documented 1938Q1)
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d442>
- Decision: ______ Note: ______

### 1938Q2

**1938Q2-079** · `belief_WEST` = **uncertain** (hindsight: uncertain (1938Q2 end))

- File: `proposals/1938Q2.json`; document `frus:frus1938v01/d523`, dated 1938-06-23: The Ambassador in France (Bullitt) to the Secretary of State; proposal dated 1938-06-22
- Quote: "he considered the present appearance of an improvement in the general European situation a mirage. Nothing had yet been settled and he was not optimistic that any settlement could be achieved."
- Rule: claude backend: Under the uncertain rule, the French Prime Minister doubts that a settlement can satisfy Hitler while still pressing for negotiated concessions; but this is a private remark relayed by a foreign ambassador, not a Cabinet record.
- Confidence: low; harness: ok: a flip
- Why sampled: sets the documented flip belief_WEST -> uncertain (replayed 1938Q2, documented 1938Q2)
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d523>
- Decision: ______ Note: ______

### 1938Q3

**1938Q3-058** · `belief_GER` = **will_fight** (hindsight: will_not_fight (1938Q3 end))

- File: `proposals/1938Q3.json`; document `frus:frus1938v01/d587`, dated 1938-09-17: The Ambassador in the United Kingdom (Kennedy) to the Secretary of State; proposal dated 1938-09-17
- Quote: "Hitler said he was perfectly willing to take on a world war"
- Rule: claude backend: Hitler is reported as accepting war with Britain and France as the consequence of marching. The report is second-hand and may be bluster rather than a German decision record, so the reading is doubtful.
- Confidence: low; harness: ok: a flip
- Why sampled: sets the documented flip belief_GER -> will_fight (replayed 1938Q3, documented 1939Q3); behind belief_GER = will_fight at 1938Q3 (hindsight will_not_fight; disagreement 1938Q3 to 1938Q4); behind belief_GER = will_fight at 1938Q4 (hindsight will_not_fight; disagreement 1938Q3 to 1938Q4); same level as the replay (will_fight) in 1938Q3 to 1938Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d587>
- Decision: ______ Note: ______

**1938Q3-085** · `commit_WEST` = **wary** (hindsight: wary (1938Q3 end))

- File: `proposals/1938Q3.json`; document `frus:frus1938v01/d632`, dated 1938-09-26: The Ambassador in the United Kingdom (Kennedy) to the Secretary of State; proposal dated 1938-09-26
- Quote: "The British and French have completely agreed to fight if Hitler makes any steps after he turns down this proposition."
- Rule: claude backend: commit_WEST wary: the governments accept that a further German move will require a military answer, but this is a privately reported, conditional decision rather than a public statement, so the reading is doubtful.
- Confidence: low; harness: ok: a flip
- Why sampled: sets the documented flip commit_WEST -> wary (replayed 1938Q3, documented 1938Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d632>
- Decision: ______ Note: ______

**1938Q3-100** · `sudeten` = **german** (hindsight: german (1938Q3 end))

- File: `proposals/1938Q3.json`; document `frus:frus1938v01/d682`, dated 1938-09-30: The Minister in Czechoslovakia (Carr) to the Secretary of State; proposal dated 1938-09-30
- Quote: "Text of Munich Agreement delivered to Minister of Foreign Affairs by German Chargé d’Affaires at 6 o’clock this morning. ... The agreement provides for progressive evacuation and occupation by Germany of Sudeten area predominantly German without disturbance of fortifications beginning tomorrow and finishing October 10."
- Rule: claude backend: The sudeten rule sets german for the areas ceded under the Munich agreement of 29-30 Sep 1938; the passage reports the concluded agreement providing for their cession and occupation, though the occupation itself has not yet begun and Prague has not yet accepted.
- Confidence: medium; harness: corroborating at 1938Q3 end (two-document: corroborates the flip carried by 1938Q3-101); ok: two-document: corroborated by frus:frus1938v01/d691
- Why sampled: first of two documents for the documented flip sudeten -> german (replayed 1938Q3, documented 1938Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d682>
- Decision: ______ Note: ______

**1938Q3-101** · `sudeten` = **german** (hindsight: german (1938Q3 end))

- File: `proposals/1938Q3.json`; document `frus:frus1938v01/d686`, dated 1938-09-30: Memorandum by the Chief of the Office of Arms and Munitions Control (Green); proposal dated 1938-09-30
- Quote: "the results of the Munich meeting had caused him as much anxiety as relief; that he could not reconcile himself to the idea that four statesmen representing four of the great powers of Europe should take it upon themselves to dismember a smaller power"
- Rule: claude backend: The sudeten rule sets german when the areas are ceded under the Munich agreement; the ambassador describes the Munich meeting as the four powers having dismembered a smaller power, though the document does not name the Sudeten areas or the cession terms.
- Confidence: medium; harness: ok at 1938Q3 end (two-document: corroborated by frus:frus1938v01/d682); ok: confirms the current level
- Why sampled: sets the documented flip sudeten -> german (replayed 1938Q3, documented 1938Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d686>
- Decision: ______ Note: ______

### 1939Q1

**1939Q1-030** · `bohemia` = **german** (hindsight: german (1939Q1 end))

- File: `proposals/1939Q1.json`; document `frus:frus1939v01/d32`, dated 1939-03-15: The Chargé in Germany (Geist) to the Secretary of State; proposal dated 1939-03-15
- Quote: "the commanders of the German forces in Moravia and in Bohemia would be responsible in those districts"
- Rule: claude backend: The bohemia rule sets german with the Protectorate of 15 to 16 Mar 1939; the passage shows German forces in control of Bohemia and Moravia under an agreement with the Reich, though the formal status was still to be clarified.
- Confidence: medium; harness: corroborating: two-document: corroborates the flip carried by 1939Q1-031
- Why sampled: first of two documents for the documented flip bohemia -> german (replayed 1939Q1, documented 1939Q1)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d32>
- Decision: ______ Note: ______

**1939Q1-031** · `bohemia` = **german** (hindsight: german (1939Q1 end))

- File: `proposals/1939Q1.json`; document `frus:frus1939v01/d33`, dated 1939-03-15: Memorandum of Trans-Atlantic Telephone Conversation Between the Ambassador in France (Bullitt) and the Acting Secretary of State; proposal dated 1939-03-15
- Quote: "since he had taken possession of the territory at the request of the Czech Government, there was no cause for France to get excited about anything"
- Rule: claude backend: bohemia german requires German control of the rump Czech lands (the Protectorate, 15-16 Mar 1939); the German note delivered to Bonnet that day states Germany has taken possession of the Czech territory, though it does not name Bohemia-Moravia or the Protectorate.
- Confidence: medium; harness: ok: two-document: corroborated by frus:frus1939v01/d32
- Why sampled: sets the documented flip bohemia -> german (replayed 1939Q1, documented 1939Q1)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d33>
- Decision: ______ Note: ______

**1939Q1-065** · `belief_WEST` = **hegemonic** (hindsight: hegemonic (1939Q1 end))

- File: `proposals/1939Q1.json`; document `frus:frus1939v01/d86`, dated 1939-03-22: The Ambassador in the United Kingdom (Kennedy) to the Secretary of State; proposal dated 1939-03-22
- Quote: "With the Munich agreement washed away, an entirely new line of action has to be worked out and applied. ... the British Government ... is examining every possibility which might offer a lead to effective machinery for stemming German aggression."
- Rule: claude backend: Under the hegemonic rule, the British Government treats the Munich settlement as void and seeks concerted measures against German aggression on Eastern European states, implying that German assurances are no longer relied on; this is an ambassador's report of officials' views, not a Cabinet statement.
- Confidence: low; harness: ok: a flip
- Why sampled: sets the documented flip belief_WEST -> hegemonic (replayed 1939Q1, documented 1939Q1)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d86>
- Decision: ______ Note: ______

**1939Q1-072** · `oil_GER` = **secured** (hindsight: dependent (1939Q1 end))

- File: `proposals/1939Q1.json`; document `frus:frus1939v01/d92`, dated 1939-03-24: The Ambassador in the United Kingdom (Kennedy) to the Secretary of State; proposal dated 1939-03-24
- Quote: "the trade agreement signed today between Rumania and Germany"
- Rule: claude backend: The secured rule names the German-Romanian economic treaty of March 1939 as an overland supply agreement with a producer outside the blockade; the passage reports its signature but does not mention oil.
- Confidence: medium; harness: corroborating: two-document: corroborates the flip carried by 1939Q1-073
- Why sampled: first of two documents for the documented flip oil_GER -> secured (replayed 1939Q1, documented 1940Q1); same level as the replay (secured) in 1939Q1 to 1939Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d92>
- Decision: ______ Note: ______

**1939Q1-073** · `oil_GER` = **secured** (hindsight: dependent (1939Q1 end))

- File: `proposals/1939Q1.json`; document `frus:frus1939v01/d93`, dated 1939-03-24: The Minister in Bulgaria (Atherton) to the Secretary of State; proposal dated 1939-03-24
- Quote: "shortly after the details of the Rumanian-German accord had been confirmed here"
- Rule: claude backend: The oil_GER rule lists the German-Romanian economic treaty of March 1939 as an overland supply agreement that makes oil secured, and the passage reports a confirmed Rumanian-German accord; the document does not say the accord covers oil.
- Confidence: low; harness: ok: two-document: corroborated by frus:frus1939v01/d92
- Why sampled: sets the documented flip oil_GER -> secured (replayed 1939Q1, documented 1940Q1); behind oil_GER = secured at 1939Q1 (hindsight dependent; disagreement 1939Q1 to 1939Q4); behind oil_GER = secured at 1939Q2 (hindsight dependent; disagreement 1939Q1 to 1939Q4); behind oil_GER = secured at 1939Q3 (hindsight dependent; disagreement 1939Q1 to 1939Q4); behind oil_GER = secured at 1939Q4 (hindsight dependent; disagreement 1939Q1 to 1939Q4); same level as the replay (secured) in 1939Q1 to 1939Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d93>
- Decision: ______ Note: ______

**1939Q1-078** · `polish_guarantee` = **true** (hindsight: true (1939Q1 end))

- File: `proposals/1939Q1.json`; document `frus:frus1939v01/d100`, dated 1939-03-31: The Ambassador in the United Kingdom (Kennedy) to the Secretary of State; proposal dated 1939-03-31
- Quote: "His Majesty’s Government would feel themselves bound at once to lend the Polish Government all support in their power. They have given the Polish Government an assurance to this effect."
- Rule: claude backend: The Prime Minister's Commons statement of 31 Mar 1939 sets the flag; the passage gives its text and says the assurance has already been given to Poland, though the statement itself was still to be delivered that afternoon.
- Confidence: medium; harness: held at 1939Q1 end (two-document: the only document so far proposing polish_guarantee := True); corroborating: two-document: corroborates the flip carried by 1939Q2-003
- Why sampled: first of two documents for the documented flip polish_guarantee -> true (replayed 1939Q2, documented 1939Q1); hindsight level (true), not in force in 1939Q1
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d100>
- Decision: ______ Note: ______

**1939Q1-079** · `commit_WEST` = **resolved** (hindsight: resolved (1939Q1 end))

- File: `proposals/1939Q1.json`; document `frus:frus1939v01/d100`, dated 1939-03-31: The Ambassador in the United Kingdom (Kennedy) to the Secretary of State; proposal dated 1939-03-31
- Quote: "if Poland thought that any gesture of Germany’s threatened their independence and they themselves are the judges of that, Great Britain commits itself to fight."
- Rule: claude backend: A standing commitment to fight for a third state threatened by Germany (the Polish guarantee, joined by France) meets the resolved threshold.
- Confidence: medium; harness: ok: a flip
- Why sampled: sets the documented flip commit_WEST -> resolved (replayed 1939Q1, documented 1939Q1)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d100>
- Decision: ______ Note: ______

### 1939Q2

**1939Q2-003** · `polish_guarantee` = **true** (hindsight: true (1939Q1 end); true (1939Q2 end))

- File: `proposals/1939Q2.json`; document `frus:frus1939v01/d102`, dated 1939-04-03: The Chargé in Germany (Geist) to the Secretary of State; proposal dated 1939-03-31
- Quote: "Prime Minister Chamberlain’s pronouncement of March 30 [31], by which British power was related to the independence of Poland"
- Rule: claude backend: The polish_guarantee flag is set by the Prime Minister's statement of 31 Mar 1939, which the document reports as tying British power to Polish independence.
- Confidence: high; harness: ok: two-document: corroborated by frus:frus1939v01/d100
- Why sampled: sets the documented flip polish_guarantee -> true (replayed 1939Q2, documented 1939Q1)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d102>
- Decision: ______ Note: ______

### 1939Q3

**1939Q3-075** · `nazi_soviet_pact` = **true** (hindsight: true (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d347`, dated 1939-08-23: The Ambassador in France (Bullitt) to the Secretary of State; proposal dated 1939-08-23
- Quote: "because of the treaty between the Soviet Union and Germany"
- Rule: claude backend: The flag is true once the German-Soviet non-aggression treaty exists; the passage refers to the treaty as an existing fact on 23 Aug 1939.
- Confidence: medium; harness: corroborating: two-document: corroborates the flip carried by 1939Q3-080
- Why sampled: first of two documents for the documented flip nazi_soviet_pact -> true (replayed 1939Q3, documented 1939Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d347>
- Decision: ______ Note: ______

**1939Q3-080** · `nazi_soviet_pact` = **true** (hindsight: true (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d350`, dated 1939-08-23: The Ambassador in the United Kingdom (Kennedy) to the Secretary of State; proposal dated 1939-08-23
- Quote: "he felt the Japanese were stunned by the German-Russian agreement"
- Rule: claude backend: The passage mentions a German-Russian agreement. It does not establish that the non-aggression pact and secret protocol were signed, so the reading for the true level is doubtful.
- Confidence: low; harness: ok: two-document: corroborated by frus:frus1939v01/d347
- Why sampled: sets the documented flip nazi_soviet_pact -> true (replayed 1939Q3, documented 1939Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d350>
- Decision: ______ Note: ______

**1939Q3-103** · `belief_GER` = **uncertain** (hindsight: will_fight (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d370`, dated 1939-08-26: The Ambassador in France (Bullitt) to the Secretary of State; proposal dated 1939-08-26
- Quote: "he would regret war with France; but that he was ready for it... If France chose to make a general European war out of the action which he would be obliged to take if the Poles should continue their present behavior, there would be war."
- Rule: claude backend: Hitler provides for possible Western intervention as a conditional outcome of action against Poland, without asserting that the West will or will not fight, which fits uncertain; but this is a diplomatic statement, not a decision record.
- Confidence: low; harness: ok: a flip
- Why sampled: sets the documented flip belief_GER -> uncertain (replayed 1939Q3, documented 1939Q2); behind belief_GER = uncertain at 1939Q3 (hindsight will_fight; disagreement 1939Q2 to 1940Q4); behind belief_GER = uncertain at 1939Q4 (hindsight will_fight; disagreement 1939Q2 to 1940Q4); behind belief_GER = uncertain at 1940Q1 (hindsight will_fight; disagreement 1939Q2 to 1940Q4); behind belief_GER = uncertain at 1940Q2 (hindsight will_fight; disagreement 1939Q2 to 1940Q4); behind belief_GER = uncertain at 1940Q3 (hindsight will_fight; disagreement 1939Q2 to 1940Q4); behind belief_GER = uncertain at 1940Q4 (hindsight will_fight; disagreement 1939Q2 to 1940Q4); same level as the replay (uncertain) in 1939Q2 to 1940Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d370>
- Decision: ______ Note: ______

**1939Q3-162** · `commit_WEST` = **at_war** (hindsight: at_war (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d420`, dated 1939-09-03: The Ambassador in France (Bullitt) to the Secretary of State; proposal dated 1939-09-03
- Quote: "The British Government has just announced that a state of war will exist between Great Britain and Germany at 11 o’clock this morning."
- Rule: claude backend: at_war requires a declaration of war, and the British Government has announced a state of war with Germany taking effect the same morning.
- Confidence: medium; harness: ok: a flip
- Why sampled: sets the documented flip commit_WEST -> at_war (replayed 1939Q3, documented 1939Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d420>
- Decision: ______ Note: ______

**1939Q3-163** · `britain` = **at_war** (hindsight: at_war (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d420`, dated 1939-09-03: The Ambassador in France (Bullitt) to the Secretary of State; proposal dated 1939-09-03
- Quote: "The British Government has just announced that a state of war will exist between Great Britain and Germany at 11 o’clock this morning."
- Rule: claude backend: Britain leaves at_peace because its government has announced a state of war with Germany from 11 a.m. on the document's date, though that hour had not yet come when the message was written.
- Confidence: medium; harness: corroborating: two-document: corroborates the flip carried by 1939Q3-168
- Why sampled: first of two documents for the documented flip britain -> at_war (replayed 1939Q3, documented 1939Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d420>
- Decision: ______ Note: ______

**1939Q3-166** · `war_west_ger` = **war** (hindsight: war (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d424`, dated 1939-09-03: The Ambassador in Italy (Phillips) to the Secretary of State; proposal dated 1939-09-03
- Quote: "the steps which the British and French may take to preserve Italy’s neutrality. The question of blockade is uppermost in Loraine’s thoughts"
- Rule: claude backend: war requires a British and French declaration of war in force; the telegram calls Britain and France the 'Allied Powers' and discusses their blockade and Italy's neutrality, which implies a state of war, but it never reports a declaration.
- Confidence: low; harness: corroborating: two-document: corroborates the flip carried by 1939Q3-172
- Why sampled: first of two documents for the documented flip war_west_ger -> war (replayed 1939Q3, documented 1939Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d424>
- Decision: ______ Note: ______

**1939Q3-168** · `britain` = **at_war** (hindsight: at_war (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d593`, dated 1939-09-03: The Ambassador in the United Kingdom (Kennedy) to the Secretary of State; proposal dated 1939-09-03
- Quote: "in consequence of the state of war which exists with Germany"
- Rule: claude backend: The Foreign Office note says that a state of war exists between the United Kingdom and Germany, which means Britain is no longer at peace.
- Confidence: high; harness: ok: two-document: corroborated by frus:frus1939v01/d420
- Why sampled: sets the documented flip britain -> at_war (replayed 1939Q3, documented 1939Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d593>
- Decision: ______ Note: ______

**1939Q3-172** · `war_west_ger` = **war** (hindsight: war (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d426`, dated 1939-09-04: The Ambassador in France (Bullitt) to the Secretary of State; proposal dated 1939-09-04
- Quote: "France and England show that they are absolutely determined to carry on this war"
- Rule: claude backend: The war level requires Britain and France at war with Germany, and the French Foreign Ministry's secretary-general refers to France and England carrying on 'this war' against Hitler.
- Confidence: medium; harness: ok: two-document: corroborated by frus:frus1939v01/d424
- Why sampled: sets the documented flip war_west_ger -> war (replayed 1939Q3, documented 1939Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d426>
- Decision: ______ Note: ______

**1939Q3-173** · `france` = **at_war** (hindsight: at_war (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d426`, dated 1939-09-04: The Ambassador in France (Bullitt) to the Secretary of State; proposal dated 1939-09-04
- Quote: "France and England show that they are absolutely determined to carry on this war without flinching until Hitler and Hitlerism have been destroyed"
- Rule: claude backend: France is no longer at peace with Germany, because the passage speaks of France carrying on a war against Hitler.
- Confidence: medium; harness: corroborating: two-document: corroborates the flip carried by 1939Q3-178
- Why sampled: first of two documents for the documented flip france -> at_war (replayed 1939Q3, documented 1939Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d426>
- Decision: ______ Note: ______

**1939Q3-178** · `france` = **at_war** (hindsight: at_war (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d729`, dated 1939-09-05: Proclamation of September 5, 1939, Proclaiming the Neutrality of the United States in the War Between Germany and France; Poland; and the United Kingdom, India, Australia, and New Zealand; proposal dated 1939-09-05
- Quote: "a state of war unhappily exists between Germany and France"
- Rule: claude backend: France is no longer at peace with Germany, since the proclamation states that a state of war exists between them, and there is no armistice.
- Confidence: high; harness: ok: two-document: corroborated by frus:frus1939v01/d426
- Why sampled: sets the documented flip france -> at_war (replayed 1939Q3, documented 1939Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d729>
- Decision: ______ Note: ______

**1939Q3-255** · `poland` = **partitioned** (hindsight: partitioned (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1933-39/d595`, dated 1939-09-17: The Ambassador in the Soviet Union (Steinhardt) to the Secretary of State; proposal dated 1939-09-17
- Quote: "the Soviet Government has issued instructions to the High Command Red Army to give the order to its forces to cross the Polish frontier and take under their protection the life and property of the population of Western Ukraine and Western White Russia"
- Rule: claude backend: Partitioned means German and Soviet shares. The official Soviet note announces that the Red Army has been ordered across the Polish frontier into eastern Poland while Poland is under German attack. It reports the order rather than the crossing itself, so the reading needs judgment.
- Confidence: medium; harness: corroborating: two-document: corroborates the flip carried by 1939Q3-256
- Why sampled: first of two documents for the documented flip poland -> partitioned (replayed 1939Q3, documented 1939Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1933-39/d595>
- Decision: ______ Note: ______

**1939Q3-256** · `poland` = **partitioned** (hindsight: partitioned (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1933-39/d742`, dated 1939-09-17: The Minister in Latvia (Wiley) to the Secretary of State; proposal dated 1939-09-17
- Quote: "Counselor of Soviet Legation in talking to Packer justified Soviet action by bad treatment meted out to Ukrainian [and] White Russian minorities in Poland."
- Rule: claude backend: Partitioned requires German and Soviet shares of Poland; a Soviet diplomat justifying a 'Soviet action' over minorities in Poland suggests Soviet entry into Poland, but the passage does not explicitly state that Soviet troops have entered.
- Confidence: low; harness: ok: two-document: corroborated by frus:frus1933-39/d595
- Why sampled: sets the documented flip poland -> partitioned (replayed 1939Q3, documented 1939Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1933-39/d742>
- Decision: ______ Note: ______

### 1939Q4

**1939Q4-154** · `commit_US` = **wary** (hindsight: wary (1939Q4 end))

- File: `proposals/1939Q4.json`; document `frus:frus1939v01/d746`, dated 1939-11-07: The Department of State to the Canadian Legation; proposal dated 1939-11-04
- Quote: "Neutrality Act of 1939, approved November 4, 1939."
- Rule: claude backend: wary is the Neutrality Act of 4 Nov 1939 (embargo repealed, cash and carry); the document confirms the Act's approval on that date but does not state its contents.
- Confidence: low; harness: ok: a flip
- Why sampled: sets the documented flip commit_US -> wary (replayed 1939Q4, documented 1939Q4)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d746>
- Decision: ______ Note: ______

### 1940Q2

**1940Q2-244** · `france` = **fallen** (hindsight: fallen (1940Q2 end))

- File: `proposals/1940Q2.json`; document `frus:frus1940v01/d233`, dated 1940-06-22: The Chargé in Germany (Heath) to the Secretary of State; proposal dated 1940-06-22
- Quote: "announcing the signature at 6:50 this evening in the forest of Compiegne of a Franco-German armistice agreement"
- Rule: claude backend: The rule for fallen is the armistice signed, and the passage reports the Franco-German armistice signed on 22 June 1940; its entry into effect awaits the Italian-French armistice, but the rule turns on signature.
- Confidence: high; harness: corroborating: two-document: corroborates the flip carried by 1940Q2-247
- Why sampled: first of two documents for the documented flip france -> fallen (replayed 1940Q2, documented 1940Q2)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v01/d233>
- Decision: ______ Note: ______

**1940Q2-247** · `france` = **fallen** (hindsight: fallen (1940Q2 end))

- File: `proposals/1940Q2.json`; document `frus:frus1940v02/d532`, dated 1940-06-22: The Ambassador in the United Kingdom (Kennedy) to the Secretary of State; proposal dated 1940-06-22
- Quote: "No official confirmation at Foreign Office of press report that agreement was signed at 6:50 p.m., but they think it probable."
- Rule: claude backend: France is fallen when the armistice is signed; the document reports only an unconfirmed press report of signature that the Foreign Office thinks probable, so the reading is doubtful.
- Confidence: low; harness: ok: two-document: corroborated by frus:frus1940v01/d233
- Why sampled: sets the documented flip france -> fallen (replayed 1940Q2, documented 1940Q2)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v02/d532>
- Decision: ______ Note: ______

### 1940Q3

**1940Q3-134** · `commit_US` = **engaged** (hindsight: engaged (1940Q3 end))

- File: `proposals/1940Q3.json`; document `frus:frus1940v03/d65`, dated 1940-09-02: The British Ambassador (Lothian) to the Secretary of State; proposal dated 1940-09-02
- Quote: "in exchange for naval and military equipment and material which the United States Government will transfer to His Majesty's Government"
- Rule: claude backend: The engaged level is defined by executive transfers of war material to a belligerent, naming the destroyers-for-bases agreement of 2 Sep 1940; this note sets out that agreement's terms, trading bases for US naval and military equipment to Britain.
- Confidence: medium; harness: ok: a flip
- Why sampled: sets the documented flip commit_US -> engaged (replayed 1940Q3, documented 1940Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v03/d65>
- Decision: ______ Note: ______

### 1940Q4

**1940Q4-017** · `channel_air` = **british** (hindsight: british (1940Q4 end))

- File: `proposals/1940Q4.json`; document `frus:frus1940v03/d684`, dated 1940-10-04: The Secretary of State to the Chargé in Liberia (Wharton); proposal dated 1940-10-04
- Quote: "the apparent postponement of action against the British Isles"
- Rule: claude backend: The 'british' level requires the German invasion to be postponed for lack of air superiority; the passage reports only an 'apparent' postponement as seen from Washington and gives no reason for it.
- Confidence: low; harness: corroborating: two-document: corroborates the flip carried by 1940Q4-040
- Why sampled: first of two documents for the documented flip channel_air -> british (replayed 1940Q4, documented 1940Q4)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v03/d684>
- Decision: ______ Note: ______

**1940Q4-030** · `balkans` = **german_aligned** (hindsight: german_aligned (1940Q4 end))

- File: `proposals/1940Q4.json`; document `frus:frus1940v03/d891`, dated 1940-10-09: Memorandum of Conversation, by the Assistant Secretary of State (Berle); proposal dated 1940-10-09
- Quote: "the Germans had guaranteed the Roumanian frontier, which in practice meant going to the Black Sea, and taking into their orbit an area which Russia had marked out for her own. ... The appearance of German troops in Roumania reinforced this conclusion."
- Rule: claude backend: german_aligned requires Romania under German guarantee with a German military presence and Tripartite adherence; the passage shows the guarantee and German troops in Romania but not Tripartite adherence, so the threshold is only partly met.
- Confidence: low; harness: corroborating: two-document: corroborates the flip carried by 1940Q4-037
- Why sampled: first of two documents for the documented flip balkans -> german_aligned (replayed 1940Q4, documented 1940Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v03/d891>
- Decision: ______ Note: ______

**1940Q4-037** · `balkans` = **german_aligned** (hindsight: german_aligned (1940Q4 end))

- File: `proposals/1940Q4.json`; document `frus:frus1940v02/d901`, dated 1940-10-15: The Minister in Rumania (Gunther) to the Secretary of State; proposal dated 1940-10-15
- Quote: "It was of course alleged that the German officers and men were here by invitation and arrangement."
- Rule: claude backend: The german_aligned rule needs a German guarantee, a German military mission and Tripartite Pact adherence; the passage shows only German forces in Romania by invitation, which suggests a military mission but not the other two conditions.
- Confidence: low; harness: ok: two-document: corroborated by frus:frus1940v03/d891
- Why sampled: sets the documented flip balkans -> german_aligned (replayed 1940Q4, documented 1940Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v02/d901>
- Decision: ______ Note: ______

**1940Q4-040** · `channel_air` = **british** (hindsight: british (1940Q4 end))

- File: `proposals/1940Q4.json`; document `frus:frus1940v01/d607`, dated 1940-10-17: The Ambassador in the Soviet Union (Steinhardt) to the Secretary of State; proposal dated 1940-10-17
- Quote: "as a result of the apparent abandonment of an attempted invasion of England this autumn"
- Rule: claude backend: The 'british' level is met when the German invasion is postponed; a German Embassy source reports the invasion of England apparently abandoned for this autumn, though the passage gives no reason such as lack of air superiority.
- Confidence: low; harness: ok: two-document: corroborated by frus:frus1940v03/d684
- Why sampled: sets the documented flip channel_air -> british (replayed 1940Q4, documented 1940Q4)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v01/d607>
- Decision: ______ Note: ______

## (b) False flips: the proposals that set the replayed level: 5

### 1937Q1

**1937Q1-006** · `italy_estranged` = **false** (hindsight: true (1937Q1 end))

- File: `proposals/1937Q1.json`; document `frus:frus1937v01/d129`, dated 1937-01-16: The Ambassador in Italy (Phillips) to the Secretary of State; proposal dated 1937-01-16
- Quote: "the attitude of the Italians towards the British has completely changed as a result of the Mediterranean “gentlemen’s agreement”"
- Rule: claude backend: The flag records Italy's estrangement from the West after Ethiopia; the ambassador reports that Italy's attitude toward Britain has completely changed after an Anglo-Italian agreement, which may indicate the estrangement has ended.
- Confidence: low; harness: held at 1937Q1 end (two-document: the only document so far proposing italy_estranged := False); corroborating: two-document: corroborates the flip carried by 1938Q2-039
- Why sampled: first of two documents for the false flip italy_estranged -> false (replayed 1938Q2)
- FRUS: <https://history.state.gov/historicaldocuments/frus1937v01/d129>
- Decision: ______ Note: ______

### 1938Q2

**1938Q2-039** · `italy_estranged` = **false** (hindsight: true (1938Q2 end))

- File: `proposals/1938Q2.json`; document `frus:frus1938v01/d145`, dated 1938-05-09: The Ambassador in the United Kingdom (Kennedy) to the Secretary of State; proposal dated 1938-04-16
- Quote: "the Anglo-Italian Agreement on April 16 last, the British can only proceed on the assumption that the Italians will loyally carry out their obligations"
- Rule: claude backend: The italy_estranged rule ties estrangement to the post-Ethiopia break with the West; a signed Anglo-Italian Agreement that London treats as binding may indicate that estrangement has ended, though the rule gives no explicit threshold for false.
- Confidence: low; harness: ok: two-document: corroborated by frus:frus1937v01/d129
- Why sampled: sets the false flip italy_estranged -> false (replayed 1938Q2); behind italy_estranged = false at 1938Q2 (hindsight true; disagreement 1938Q2 to 1940Q4); behind italy_estranged = false at 1938Q3 (hindsight true; disagreement 1938Q2 to 1940Q4); behind italy_estranged = false at 1938Q4 (hindsight true; disagreement 1938Q2 to 1940Q4); behind italy_estranged = false at 1939Q1 (hindsight true; disagreement 1938Q2 to 1940Q4); behind italy_estranged = false at 1939Q2 (hindsight true; disagreement 1938Q2 to 1940Q4); behind italy_estranged = false at 1939Q3 (hindsight true; disagreement 1938Q2 to 1940Q4); behind italy_estranged = false at 1939Q4 (hindsight true; disagreement 1938Q2 to 1940Q4); behind italy_estranged = false at 1940Q1 (hindsight true; disagreement 1938Q2 to 1940Q4); behind italy_estranged = false at 1940Q2 (hindsight true; disagreement 1938Q2 to 1940Q4); behind italy_estranged = false at 1940Q3 (hindsight true; disagreement 1938Q2 to 1940Q4); behind italy_estranged = false at 1940Q4 (hindsight true; disagreement 1938Q2 to 1940Q4); same level as the replay (false) in 1938Q2 to 1940Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d145>
- Decision: ______ Note: ______

### 1938Q4

**1938Q4-018** · `commit_WEST` = **appease** (hindsight: wary (1938Q4 end))

- File: `proposals/1938Q4.json`; document `frus:frus1938v01/d57`, dated 1938-10-12: The Ambassador in the United Kingdom (Kennedy) to the Secretary of State; proposal dated 1938-10-12
- Quote: "Then after that to let Hitler go ahead and do what he likes in Central Europe... even if he decides to go into Rumania it is Halifax's idea that England should mind her own business"
- Rule: claude backend: commit_WEST appease: the Foreign Secretary rejects any commitment to fight for third states in Central or Eastern Europe, with rearmament focused on air defence, but this is a private view reported secondhand.
- Confidence: low; harness: ok: a flip
- Why sampled: sets the false flip commit_WEST -> appease (replayed 1938Q4); behind commit_WEST = appease at 1938Q4 (hindsight wary; disagreement 1938Q4); same level as the replay (appease) in 1938Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d57>
- Decision: ______ Note: ______

**1938Q4-044** · `belief_WEST` = **limited** (hindsight: uncertain (1938Q4 end))

- File: `proposals/1938Q4.json`; document `frus:frus1938v01/d66`, dated 1938-11-25: The Chargé in France (Wilson) to the Secretary of State; proposal dated 1938-11-25
- Quote: "Hitler liberated from the diktat of Versailles was of his own free will pledging himself to renounce any claim to Alsace-Lorraine and to respect the French frontiers. It would be absurd for France to refuse such an offer. Bonnet said that he was now convinced that France had no reason to fear an attack from Germany."
- Rule: claude backend: The French Foreign Minister treats German aims as satisfied by a negotiated agreement and makes the Franco-German declaration on that premise, which matches 'limited'. This is one minister's statement reported by a US diplomat, not a Cabinet record, and it comes alongside continued rearmament.
- Confidence: low; harness: ok: a flip
- Why sampled: sets the false flip belief_WEST -> limited (replayed 1938Q4); behind belief_WEST = limited at 1938Q4 (hindsight uncertain; disagreement 1938Q4); same level as the replay (limited) in 1938Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d66>
- Decision: ______ Note: ______

### 1939Q1

**1939Q1-067** · `belief_GER` = **will_not_fight** (hindsight: will_not_fight (1939Q1 end))

- File: `proposals/1939Q1.json`; document `frus:frus1939v01/d89`, dated 1939-03-23: The Ambassador in Poland (Biddle) to the Secretary of State; proposal dated 1939-03-23
- Quote: "Upon Ribbentrop’s advice that neither Britain nor France as signatories of Memel convention would intervene forcibly, Hitler timed Memel’s annexation"
- Rule: claude backend: will_not_fight: the passage reports that Hitler made a decision (Memel) on the premise that Britain and France would not intervene by force, but this is a secondhand report by the US ambassador rather than a German decision record.
- Confidence: low; harness: ok: a flip
- Why sampled: sets the false flip belief_GER -> will_not_fight (replayed 1939Q1)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d89>
- Decision: ______ Note: ______

## (c) Disagreeing quarters: the proposals behind the replay level: 25

### 1938Q1

**1938Q1-003** · `balkans` = **neutral** (hindsight: neutral (1938Q1 end))

- File: `proposals/1938Q1.json`; document `frus:frus1938v02/d533`, dated 1938-01-06: The Minister in Rumania (Gunther) to the Secretary of State; proposal dated 1938-01-06
- Quote: "Evidently there have been reports that this Government is moving very rapidly toward the Rome–Berlin Axis. With this I do not concur. My impression is that this Government, feeling that French policies do not spell complete security, desires friendly relations with all but will work for no radical change"
- Rule: claude backend: german_aligned requires Romania under a German guarantee with a German military mission and Tripartite adherence; the US Minister reports that Romania seeks friendly relations with all and is not moving toward the Axis, which fits neutral.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: behind balkans = neutral at 1940Q3 (hindsight german_aligned; disagreement 1940Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v02/d533>
- Decision: ______ Note: ______

### 1938Q2

**1938Q2-013** · `italy_estranged` = **false** (hindsight: true (1938Q2 end))

- File: `proposals/1938Q2.json`; document `frus:frus1938v01/d90`, dated 1938-04-18: Memorandum of Conversation, by the Under Secretary of State (Welles); proposal dated 1938-04-18
- Quote: "the British-Italian agreement was obviously the result of an effort on the part of those two governments to reach a friendly solution of the difficulties which had arisen between them through pacific negotiation"
- Rule: claude backend: Italy's estrangement from the West after Ethiopia may be ending, since a signed Anglo-Italian accord settles their differences and Britain is moving toward recognizing the Ethiopian conquest; but the accord is not yet in force, so the reading is doubtful.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: same level as the replay (false) in 1938Q2 to 1940Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d90>
- Decision: ______ Note: ______

**1938Q2-021** · `italy_estranged` = **false** (hindsight: true (1938Q2 end))

- File: `proposals/1938Q2.json`; document `frus:frus1938v01/d23`, dated 1938-04-26: The Chargé in France (Wilson) to the Secretary of State; proposal dated 1938-04-26
- Quote: "Great Britain and Italy have come to an agreement"
- Rule: claude backend: The flag records Italy's estrangement from the West; a concluded Anglo-Italian agreement, with a Franco-Italian settlement in sight, suggests the estrangement has ended, but the threshold reading is doubtful.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: same level as the replay (false) in 1938Q2 to 1940Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d23>
- Decision: ______ Note: ______

**1938Q2-041** · `italy_estranged` = **false** (hindsight: true (1938Q2 end))

- File: `proposals/1938Q2.json`; document `frus:frus1938v01/d146`, dated 1938-05-09: The Ambassador in France (Bullitt) to the Secretary of State; proposal dated 1938-05-09
- Quote: "Chamberlain was extremely proud of his agreement with Italy ... there was unquestionably a change in Italy's attitude toward France"
- Rule: claude backend: An Anglo-Italian agreement concluded and a Franco-Italian agreement near signature suggest Italy is no longer estranged from the West, but the agreement's terms and Italy's continuing alignment are unclear.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: behind italy_estranged = false at 1938Q2 (hindsight true; disagreement 1938Q2 to 1940Q4); behind italy_estranged = false at 1938Q3 (hindsight true; disagreement 1938Q2 to 1940Q4); same level as the replay (false) in 1938Q2 to 1940Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d146>
- Decision: ______ Note: ______

### 1938Q4

**1938Q4-003** · `belief_WEST` = **limited** (hindsight: uncertain (1938Q4 end))

- File: `proposals/1938Q4.json`; document `frus:frus1938v01/d55`, dated 1938-10-03: The Ambassador in France (Bullitt) to the Secretary of State; proposal dated 1938-10-03
- Quote: "Bonnet said that he thought the moment was also propitious for the initiation of immediate conversations with Germany on financial, economic, and disarmament questions."
- Rule: claude backend: Under the 'limited' rule, the French Foreign Minister treats German aims as open to a negotiated general settlement (economic and disarmament talks), but this is one minister's view reported second-hand, not a Cabinet record.
- Confidence: low; harness: ok: a flip
- Why sampled: same level as the replay (limited) in 1938Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d55>
- Decision: ______ Note: ______

**1938Q4-007** · `italy_estranged` = **false** (hindsight: true (1938Q4 end))

- File: `proposals/1938Q4.json`; document `frus:frus1938v01/d205`, dated 1938-10-05: The Ambassador in Italy (Phillips) to the Secretary of State; proposal dated 1938-10-05
- Quote: "the decision of the French Government to recognize the Italian Empire and to appoint an Ambassador to Rome"
- Rule: claude backend: France's recognition of the Italian Empire, with British-Italian negotiations under way, may mark the end of the post-Ethiopia estrangement, but the rule gives no explicit criterion for false, so the reading is doubtful.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: same level as the replay (false) in 1938Q2 to 1940Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d205>
- Decision: ______ Note: ______

**1938Q4-017** · `belief_WEST` = **limited** (hindsight: uncertain (1938Q4 end))

- File: `proposals/1938Q4.json`; document `frus:frus1938v01/d57`, dated 1938-10-12: The Ambassador in the United Kingdom (Kennedy) to the Secretary of State; proposal dated 1938-10-12
- Quote: "Halifax does not believe that Hitler wants to have a war with Great Britain"
- Rule: claude backend: belief_WEST limited: the Foreign Secretary treats German aims as confined to Central Europe and not directed at Britain, though this is a private ministerial view reported secondhand rather than a Cabinet conclusion.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: same level as the replay (limited) in 1938Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d57>
- Decision: ______ Note: ______

**1938Q4-025** · `belief_WEST` = **limited** (hindsight: uncertain (1938Q4 end))

- File: `proposals/1938Q4.json`; document `frus:frus1938v01/d60`, dated 1938-10-21: The Chargé in France (Wilson) to the Secretary of State; proposal dated 1938-10-21
- Quote: "the French Government for its part would not neglect any opportunity to improve relations with Germany and he had genuine hopes that something might be accomplished"
- Rule: claude backend: limited applies when ministerial statements treat German aims as open to a negotiated settlement; the French Foreign Minister expects agreement with Hitler, but this is one minister's view reported second-hand, not a Cabinet conclusion.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: same level as the replay (limited) in 1938Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d60>
- Decision: ______ Note: ______

**1938Q4-038** · `belief_WEST` = **limited** (hindsight: uncertain (1938Q4 end))

- File: `proposals/1938Q4.json`; document `frus:frus1938v01/d63`, dated 1938-11-10: The Chargé in France (Wilson) to the Secretary of State; proposal dated 1938-11-10
- Quote: "Bonnet professes to believe that it would be a different matter with an agreement now entered into freely by a Germany which had cast off the injustices of Versailles."
- Rule: claude backend: Under the belief_WEST rule, the French Foreign Minister treats German aims as revision of Versailles, now satisfied, and pursues a negotiated non-aggression and consultation agreement on that premise, which reads as limited.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: same level as the replay (limited) in 1938Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d63>
- Decision: ______ Note: ______

**1938Q4-039** · `italy_estranged` = **false** (hindsight: true (1938Q4 end))

- File: `proposals/1938Q4.json`; document `frus:frus1938v02/d575`, dated 1938-11-16: The Chargé in Italy (Reed) to the Secretary of State; proposal dated 1938-11-16
- Quote: "the British Government had decided to recognize Italian sovereignty over Ethiopia... Ciano and Perth signed a joint declaration putting into effect the Anglo-Italian accord signed on April 16"
- Rule: claude backend: The flag records Italy's estrangement from the West after Ethiopia; British recognition of the Ethiopian conquest and the Anglo-Italian accord coming into force may show that estrangement ending, though the rule gives no explicit false threshold.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: behind italy_estranged = false at 1938Q4 (hindsight true; disagreement 1938Q2 to 1940Q4); behind italy_estranged = false at 1939Q1 (hindsight true; disagreement 1938Q2 to 1940Q4); behind italy_estranged = false at 1939Q2 (hindsight true; disagreement 1938Q2 to 1940Q4); behind italy_estranged = false at 1939Q3 (hindsight true; disagreement 1938Q2 to 1940Q4); behind italy_estranged = false at 1939Q4 (hindsight true; disagreement 1938Q2 to 1940Q4); behind italy_estranged = false at 1940Q1 (hindsight true; disagreement 1938Q2 to 1940Q4); behind italy_estranged = false at 1940Q2 (hindsight true; disagreement 1938Q2 to 1940Q4); behind italy_estranged = false at 1940Q3 (hindsight true; disagreement 1938Q2 to 1940Q4); behind italy_estranged = false at 1940Q4 (hindsight true; disagreement 1938Q2 to 1940Q4); same level as the replay (false) in 1938Q2 to 1940Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v02/d575>
- Decision: ______ Note: ______

### 1939Q2

**1939Q2-035** · `oil_GER` = **secured** (hindsight: dependent (1939Q2 end))

- File: `proposals/1939Q2.json`; document `frus:frus1939v02/d353`, dated 1939-04-12: The Ambassador in Turkey (MacMurray) to the Secretary of State; proposal dated 1939-04-12
- Quote: "the recent German economic agreement with Rumania (which he regards as at least the first step in the development of an absolute German control over Rumanian resources)"
- Rule: claude backend: The German-Romanian economic treaty is listed as an overland supply agreement that meets secured; the document reports a recent agreement covering Romanian resources but does not mention oil or say the agreement is in force.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: same level as the replay (secured) in 1939Q1 to 1939Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v02/d353>
- Decision: ______ Note: ______

**1939Q2-048** · `oil_GER` = **secured** (hindsight: dependent (1939Q2 end))

- File: `proposals/1939Q2.json`; document `frus:frus1939v02/d524`, dated 1939-04-19: The Chargé in Germany (Geist) to the Secretary of State; proposal dated 1939-04-19
- Quote: "Referring to the Rumanian treaty he said it was a “sheer accident” that its announcement coincided with the “events” in Czechoslovakia. Negotiations had started last November and agreement had been reached by Wohlthat in Bucharest"
- Rule: claude backend: The oil_GER rule names the German-Romanian economic treaty of March 1939 as an overland supply route; the passage reports that treaty as concluded and published, though it does not mention oil.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: same level as the replay (secured) in 1939Q1 to 1939Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v02/d524>
- Decision: ______ Note: ______

**1939Q2-083** · `belief_GER` = **uncertain** (hindsight: uncertain (1939Q2 end))

- File: `proposals/1939Q2.json`; document `frus:frus1939v01/d310`, dated 1939-05-20: The Chargé in the Soviet Union (Grummon) to the Secretary of State; proposal dated 1939-05-20
- Quote: "the German Government was not alarmed at the prospect of an agreement between Great Britain and the Soviet Union as it was not convinced that England and France would be disposed to lend extensive or wholehearted military assistance to any country in Eastern Europe"
- Rule: claude backend: belief_GER uncertain covers German records of doubt about Western intervention. Ribbentrop, said to reflect Hitler's views, doubts that Britain and France would give wholehearted military help in Eastern Europe, but he does not state that they will not fight.
- Confidence: low; harness: ok: a flip
- Why sampled: same level as the replay (uncertain) in 1939Q2 to 1940Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d310>
- Decision: ______ Note: ______

**1939Q2-089** · `oil_GER` = **secured** (hindsight: dependent (1939Q2 end))

- File: `proposals/1939Q2.json`; document `frus:frus1939v02/d857`, dated 1939-05-24: The Ambassador in France (Bullitt) to the Secretary of State; proposal dated 1939-05-24
- Quote: "the recently signed German-Rumanian economic agreement"
- Rule: claude backend: The oil_GER rule names the German-Romanian economic treaty (23 Mar 1939) as an overland supply agreement with a producer outside the blockade, and the document reports that agreement as signed; the passage does not mention oil itself.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: behind oil_GER = secured at 1939Q2 (hindsight dependent; disagreement 1939Q1 to 1939Q4); same level as the replay (secured) in 1939Q1 to 1939Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v02/d857>
- Decision: ______ Note: ______

**1939Q2-093** · `belief_GER` = **will_not_fight** (hindsight: uncertain (1939Q2 end))

- File: `proposals/1939Q2.json`; document `frus:frus1939v01/d190`, dated 1939-05-30: The Ambassador in France (Bullitt) to the Secretary of State; proposal dated 1939-05-30
- Quote: "his Government was convinced that if events should take place in the matter [manner?] outlined Great Britain and France would refuse to assist Poland and Germany would be left to deal with Poland alone"
- Rule: claude backend: A German diplomat reports Berlin's conviction that the West would not fight for Poland in the outlined scenario, which fits will_not_fight. It is only an embassy counselor's conditional remark, not a Hitler decision record.
- Confidence: low; harness: ok: a flip
- Why sampled: behind belief_GER = will_not_fight at 1939Q2 (hindsight uncertain; disagreement 1939Q2 to 1940Q4); same level as the replay (will_not_fight) in 1939Q2 to 1940Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d190>
- Decision: ______ Note: ______

### 1939Q3

**1939Q3-044** · `belief_GER` = **uncertain** (hindsight: will_fight (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d217`, dated 1939-08-14: The Chargé in Germany (Kirk) to the Secretary of State; proposal dated 1939-08-14
- Quote: "Hitler had demanded of Ciano that in the event of a general conflict precipitated by the Danzig issue the Italians would immediately cooperate with the Germans by attacking France"
- Rule: claude backend: The uncertain level covers German decision records that provide against Western intervention; Hitler's reported demand for Italian help against France in a general conflict over Danzig provides against such intervention.
- Confidence: low; harness: ok: a flip
- Why sampled: same level as the replay (uncertain) in 1939Q2 to 1940Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d217>
- Decision: ______ Note: ______

**1939Q3-051** · `belief_GER` = **uncertain** (hindsight: will_fight (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d230`, dated 1939-08-19: The Ambassador in France (Bullitt) to the Secretary of State; proposal dated 1939-08-15
- Quote: "Weizsaecker asked both the French and British Ambassadors whether or not England and France would give military aid to Poland"
- Rule: claude backend: Under the uncertain rule, a German official's query about Western intervention suggests doubt in Berlin. However, the doubt is an inference by a US diplomat (Kirk), not a German decision record.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: same level as the replay (uncertain) in 1939Q2 to 1940Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d230>
- Decision: ______ Note: ______

**1939Q3-061** · `oil_GER` = **secured** (hindsight: dependent (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d329`, dated 1939-08-21: The Ambassador in the Soviet Union (Steinhardt) to the Secretary of State; proposal dated 1939-08-19
- Quote: "the conclusion after long negotiations on August 19 of a commercial credit agreement between the Soviet Union and Germany"
- Rule: claude backend: The oil_GER rule names the German-Soviet commercial agreement of 19 Aug 1939 as an overland supply agreement with a producer outside the blockade, and this passage reports that agreement concluded, with Soviet deliveries of goods to Germany; the document does not mention oil itself.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: same level as the replay (secured) in 1939Q1 to 1939Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d329>
- Decision: ______ Note: ______

**1939Q3-068** · `oil_GER` = **secured** (hindsight: dependent (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d331`, dated 1939-08-22: The Ambassador in the Soviet Union (Steinhardt) to the Secretary of State; proposal dated 1939-08-22
- Quote: "following the conclusion of the commercial agreement"
- Rule: claude backend: The secured rule names the German-Soviet commercial agreement of Aug 1939 as an overland supply agreement with a producer outside the blockade, and the Tass text reports that agreement as concluded; the document does not mention oil, so the reading rests on the rule's own example.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: same level as the replay (secured) in 1939Q1 to 1939Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d331>
- Decision: ______ Note: ______

**1939Q3-099** · `oil_GER` = **secured** (hindsight: dependent (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d368`, dated 1939-08-25: The Minister in Rumania (Gunther) to the Secretary of State; proposal dated 1939-08-25
- Quote: "Hitler, he thinks, will make the most of it internally and of the commercial pact"
- Rule: claude backend: oil_GER is secured by a German-Soviet commercial agreement in force; the passage refers to a concluded commercial pact, but it says nothing about oil or overland supply.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: same level as the replay (secured) in 1939Q1 to 1939Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d368>
- Decision: ______ Note: ______

**1939Q3-120** · `oil_GER` = **secured** (hindsight: dependent (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d380`, dated 1939-08-29: The Ambassador in France (Bullitt) to the Secretary of State; proposal dated 1939-08-29
- Quote: "he had absolute proof that the Soviet Government had just sold an enormous quantity of gasoline to the German Government"
- Rule: claude backend: Secured requires an overland supply arrangement with a producer outside the blockade. Bonnet reports a large Soviet sale of gasoline to Germany, but this is his claim of a single sale, not a documented agreement in force.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: behind oil_GER = secured at 1939Q3 (hindsight dependent; disagreement 1939Q1 to 1939Q4); same level as the replay (secured) in 1939Q1 to 1939Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d380>
- Decision: ______ Note: ______

### 1939Q4

**1939Q4-051** · `oil_GER` = **secured** (hindsight: dependent (1939Q4 end))

- File: `proposals/1939Q4.json`; document `frus:frus1939v01/d504`, dated 1939-10-09: The Ambassador in the Soviet Union (Steinhardt) to the Secretary of State; proposal dated 1939-10-08
- Quote: "agreement was reached for the “speedy realization and on a wide scale” on the economic agreement concluded during Ribbentrop’s last visit... “the Soviet Union shall immediately begin to supply Germany with raw materials and Germany to carry out deliveries to the U. S. S. R.”"
- Rule: claude backend: Secured requires an overland supply agreement in force with a producer outside the blockade; the passage reports a German-Soviet economic agreement being put into effect with immediate Soviet raw-material deliveries, but it does not name oil.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: same level as the replay (secured) in 1939Q1 to 1939Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d504>
- Decision: ______ Note: ______

**1939Q4-128** · `oil_GER` = **secured** (hindsight: dependent (1939Q4 end))

- File: `proposals/1939Q4.json`; document `frus:frus1939v01/d513`, dated 1939-10-31: The Ambassador in the Soviet Union (Steinhardt) to the Secretary of State; proposal dated 1939-10-31
- Quote: "the German economic delegation here has reached an agreement with the Soviet authorities for the delivery during the next year of slightly less than 1,000,000 tons of petroleum products"
- Rule: claude backend: oil_GER secured requires an overland supply agreement with a producer outside the blockade; the passage reports a German-Soviet agreement for petroleum deliveries, though it comes from a confidential informant and does not say the agreement is in force.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: same level as the replay (secured) in 1939Q1 to 1939Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d513>
- Decision: ______ Note: ______

**1939Q4-223** · `oil_GER` = **secured** (hindsight: dependent (1939Q4 end))

- File: `proposals/1939Q4.json`; document `frus:frus1939v01/d515`, dated 1939-11-21: The Chargé in Germany (Kirk) to the Secretary of State; proposal dated 1939-11-21
- Quote: "Russia had also agreed to furnish 1,000,000 tons of petroleum products and he asserted that this was an initial quantity which would later be increased"
- Rule: claude backend: The secured level requires an overland supply agreement with a producer outside the blockade; a German official reports a Soviet agreement to deliver petroleum products, but the trade negotiations are still in progress, so whether the agreement is in force is unclear.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: behind oil_GER = secured at 1939Q4 (hindsight dependent; disagreement 1939Q1 to 1939Q4); same level as the replay (secured) in 1939Q1 to 1939Q4
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d515>
- Decision: ______ Note: ______

### 1940Q2

**1940Q2-114** · `balkans` = **neutral** (hindsight: neutral (1940Q2 end))

- File: `proposals/1940Q2.json`; document `frus:frus1940v01/d485`, dated 1940-05-27: The Minister in Rumania (Gunther) to the Secretary of State; proposal dated 1940-05-27
- Quote: "the German Government was using this situation to press for a hundred percent alignment of Rumania with Germany for protection... Naturally he is seeking a way out of succumbing to German offer of protection"
- Rule: claude backend: german_aligned requires Romania under German guarantee with a military mission and Tripartite adherence; here Romania is still resisting a German offer of protection, so it remains neutral.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: behind balkans = neutral at 1940Q3 (hindsight german_aligned; disagreement 1940Q3)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v01/d485>
- Decision: ______ Note: ______

## (d) Random check of the remaining counted proposals: 40

### 1936Q1

**1936Q1-020** · `commit_US` = **isolationist** (hindsight: isolationist (1936Q1 end))

- File: `proposals/1936Q1.json`; document `frus:frus1936v01/d164`, dated 1936-02-28: The Secretary of State to the Secretary of War (Dern); proposal dated 1936-02-28
- Quote: "H. J. Res. 491, extending until May 1, 1937, Section 1 of the Joint Resolution (Public Resolution No. 67, 74th Congress), approved August 31, 1935, and making certain other amendments, has recently been passed by Congress and is now awaiting approval by the President."
- Rule: claude backend: The isolationist level is defined by the Neutrality Act regime of 31 Aug 1935 and its extension of Feb 1936; the passage shows that regime in force and being extended by Congress, though the text does not itself describe Section 1 as the arms embargo.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1936Q1: 1 of 74 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1936v01/d164>
- Decision: ______ Note: ______

### 1936Q2

**1936Q2-002** · `rhineland` = **remilitarized** (hindsight: remilitarized (1936Q2 end))

- File: `proposals/1936Q2.json`; document `frus:frus1936v01/d524`, dated 1936-04-01: Memorandum by the Secretary of State; proposal dated 1936-04-01
- Quote: "Germany later would not have reached into the Rhineland"
- Rule: claude backend: Remilitarized means German troops garrisoned in the zone; Hull treats Germany's move into the Rhineland as an accomplished fact, though the passage does not state that troops are garrisoned there.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1936Q2: 1 of 30 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1936v01/d524>
- Decision: ______ Note: ______

### 1936Q4

**1936Q4-010** · `treaty` = **dead** (hindsight: dead (1936Q4 end))

- File: `proposals/1936Q4.json`; document `frus:frus1936v01/d286`, dated 1936-11-09: Report by the Naval Attaché in Belgium (Gade); proposal dated 1936-10-14
- Quote: "The re-occupation of the Rhineland, in violating the Locarno agreements, both in the letter and in spirit, has almost placed us in the same international position as before the war."
- Rule: claude backend: The zone has been reoccupied without being reversed, and the Locarno regime is treated as overtaken: the speech refers to negotiating new agreements to replace the Locarno pacts. This meets the dead rule (zone reoccupied, guarantors decline enforcement).
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1936Q4: 1 of 37 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1936v01/d286>
- Decision: ______ Note: ______

### 1937Q2

**1937Q2-013** · `treaty` = **dead** (hindsight: dead (1937Q2 end))

- File: `proposals/1937Q2.json`; document `frus:frus1937v01/d693`, dated 1937-04-29: The Ambassador in France (Bullitt) to the Secretary of State; proposal dated 1937-04-29
- Quote: "he and Eden had agreed that any revival of the Locarno Pact was impossible"
- Rule: claude backend: Dead requires the Locarno regime to have lapsed without enforcement; the British Foreign Secretary and the Belgian Prime Minister, two Locarno parties, treat its revival as impossible and seek a replacement pact.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1937Q2: 1 of 40 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1937v01/d693>
- Decision: ______ Note: ______

### 1937Q3

**1937Q3-013** · `commit_US` = **isolationist** (hindsight: isolationist (1937Q3 end))

- File: `proposals/1937Q3.json`; document `frus:frus1937v01/d609`, dated 1937-08-03: The Secretary of State to the Chargé in Mexico (Boal); proposal dated 1937-08-03
- Quote: "the Joint Resolution approved January 8, 1937, which definitely prohibited the export of airplanes to a neutral country for transshipment to Spain"
- Rule: claude backend: Isolationist means a mandatory arms embargo regime; the document shows the US enforcing a statutory embargo on arms exports to Spain, including prosecution for transshipment, though this resolution covers the Spanish conflict rather than the general Neutrality Act.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: random check (1937Q3: 1 of 35 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1937v01/d609>
- Decision: ______ Note: ______

### 1937Q4

**1937Q4-053** · `belief_WEST` = **limited** (hindsight: limited (1937Q4 end))

- File: `proposals/1937Q4.json`; document `frus:frus1937v01/d110`, dated 1937-11-29: The British Embassy to the Department of State; proposal dated 1937-11-29
- Quote: "If there were to be any solution, it could only be as part of a general settlement, based on contributions from everyone concerned in the interest of European appeasement."
- Rule: claude backend: Under the limited rule, a Cabinet minister reporting to the French with the Prime Minister present treats German aims (colonies, adjustments in Central Europe) as claims a negotiated general settlement can meet. (also read in 1 other part(s))
- Confidence: high; harness: ok: confirms the current level
- Why sampled: random check (1937Q4: 1 of 89 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1937v01/d110>
- Decision: ______ Note: ______

### 1938Q1

**1938Q1-014** · `commit_US` = **isolationist** (hindsight: isolationist (1938Q1 end))

- File: `proposals/1938Q1.json`; document `frus:frus1938v02/d240`, dated 1938-01-25: The Ambassador in France (Bullitt) to the Secretary of State; proposal dated 1938-01-25
- Quote: "after proclamation by the President that a state of war existed remainder of the delivery of planes contracted for under such an arrangement as he had suggested would be forbidden"
- Rule: claude backend: The isolationist level is the Neutrality Act regime with a mandatory arms embargo on belligerents. The US ambassador states that deliveries of aircraft to France would be forbidden once the President proclaims a state of war, which implies the embargo is still in force.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1938Q1: 2 of 112 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v02/d240>
- Decision: ______ Note: ______

**1938Q1-031** · `axis` = **true** (hindsight: true (1938Q1 end))

- File: `proposals/1938Q1.json`; document `frus:frus1938v02/d540`, dated 1938-02-09: Memorandum of Conversation, by the Chief of the Division of European Affairs (Moffat); proposal dated 1938-02-09
- Quote: "Ribbentrop's appointment as the latter was the spiritual father of the Rome–Berlin axis"
- Rule: claude backend: The axis flag is true once the Rome-Berlin alignment exists; the speaker refers to the Rome–Berlin axis as an existing alignment, though only in passing within a hypothesis about British policy.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: random check (1938Q1: 2 of 112 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v02/d540>
- Decision: ______ Note: ______

### 1938Q2

**1938Q2-004** · `austria` = **annexed** (hindsight: annexed (1938Q1 end); annexed (1938Q2 end))

- File: `proposals/1938Q2.json`; document `frus:frus1938v02/d382`, dated 1938-04-05: The Secretary of State to the Ambassador in Germany (Wilson); proposal dated 1938-03-17
- Quote: "the change of status of Austria ... the German authorities which have succeeded in control of the means and machinery of payment in Austria"
- Rule: claude backend: The annexed rule needs Austria under German control; the note accepts, from the Austrian Minister's announcement of 17 March 1938, that Austria's status has changed and that German authorities now control its machinery of government payment.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1938Q2: 1 of 75 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v02/d382>
- Decision: ______ Note: ______

### 1938Q3

**1938Q3-004** · `belief_WEST` = **limited** (hindsight: uncertain (1938Q3 end))

- File: `proposals/1938Q3.json`; document `frus:frus1938v01/d526`, dated 1938-07-13: The Ambassador in France (Bullitt) to the Secretary of State; proposal dated 1938-07-12
- Quote: "the French Government wished to express confidence in the peaceful aspirations which the Chancellor of the Reich has always publicly avowed"
- Rule: claude backend: limited: the French Prime Minister states publicly, and Bonnet confirms as the government's sincere view, that German aims are peaceful and that a Sudeten settlement could lead to Franco-German reconciliation. This treats German aims as revision that a negotiated settlement can satisfy, though it is Paris rather than the London Cabinet.
- Confidence: medium; harness: ok: a flip
- Why sampled: random check (1938Q3: 2 of 94 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d526>
- Decision: ______ Note: ______

**1938Q3-067** · `commit_WEST` = **appease** (hindsight: wary (1938Q3 end))

- File: `proposals/1938Q3.json`; document `frus:frus1938v01/d595`, dated 1938-09-19: The Ambassador in the United Kingdom (Kennedy) to the Secretary of State; proposal dated 1938-09-19
- Quote: ""I can see no rhyme nor reason in fighting for a cause which, if I went to war for it, I would have to settle after it was over in about the same way I suggest settling it now.""
- Rule: claude backend: appease: the Prime Minister rejects fighting for Czechoslovakia, a third state Germany threatens, and seeks a negotiated settlement (separation of the Sudeten region) instead of a military answer.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1938Q3: 2 of 94 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d595>
- Decision: ______ Note: ______

### 1938Q4

**1938Q4-033** · `austria` = **annexed** (hindsight: annexed (1938Q4 end))

- File: `proposals/1938Q4.json`; document `frus:frus1938v01/d785`, dated 1938-10-26: Memorandum by the Chairman of the Intergovernmental Committee (Winterton); proposal dated 1938-10-26
- Quote: "their country of origin (Germany including Austria)"
- Rule: claude backend: The rule sets annexed when Austria is incorporated into Germany; the official definition treats Austria as part of Germany, but the passage does not mention troops or the reunification law.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1938Q4: 1 of 45 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1938v01/d785>
- Decision: ______ Note: ______

### 1939Q1

**1939Q1-058** · `bohemia` = **german** (hindsight: german (1939Q1 end))

- File: `proposals/1939Q1.json`; document `frus:frus1939v01/d54`, dated 1939-03-21: The Acting Secretary of State to the Consul at Praha (Bruins); proposal dated 1939-03-21
- Quote: "requesting intervention with the German Government to permit refugee emigration through Poland ... departure from Czechoslovakian territory under control of Germany"
- Rule: claude backend: german = Bohemia and Moravia under German control; a request from Prague that the German Government permit departure from Czechoslovak territory under German control implies Prague, in Bohemia, is under German control.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1939Q1: 1 of 69 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d54>
- Decision: ______ Note: ______

### 1939Q2

**1939Q2-075** · `sudeten` = **german** (hindsight: german (1939Q2 end))

- File: `proposals/1939Q2.json`; document `frus:frus1939v02/d537`, dated 1939-05-11: The Chargé in Germany (Kirk) to the Secretary of State; proposal dated 1939-05-04
- Quote: "It is provided that the law may be applied in Austria and the Sudetenland with necessary emendations."
- Rule: claude backend: A Reich statute that extends to the Sudetenland implies the area is under German rule, consistent with the ceded (german) level, though the passage does not mention the Munich cession itself.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: random check (1939Q2: 2 of 117 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v02/d537>
- Decision: ______ Note: ______

**1939Q2-114** · `belief_WEST` = **hegemonic** (hindsight: hegemonic (1939Q2 end))

- File: `proposals/1939Q2.json`; document `frus:frus1939v01/d270`, dated 1939-06-27: The Ambassador in the United Kingdom (Kennedy) to the Secretary of State; proposal dated 1939-06-27
- Quote: "they can get no assurances from him, however, that he wants to do anything with England ... If he has made up his mind to take England on, no olive branch will have any effect on him and there is a very definite feeling now that that is what he has in the back of his head."
- Rule: claude backend: belief_WEST hegemonic: the Foreign Secretary says no assurances can be had from Hitler and that he probably means to take on England, which treats German aims as beyond negotiated revision; this is one minister reported second-hand, not the PM and Cabinet, and he still allows that Danzig could be settled.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: random check (1939Q2: 2 of 117 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d270>
- Decision: ______ Note: ______

### 1939Q3

**1939Q3-021** · `bohemia` = **german** (hindsight: german (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v02/d416`, dated 1939-07-15: The Chargé in Germany (Kirk) to the Secretary of State; proposal dated 1939-07-15
- Quote: "the position of the United States Government on the matter of the forceful occupation of Czechoslovak territory"
- Rule: claude backend: The document treats Prague as under German occupation and German authorities as deciding on exequaturs for consuls there, which meets the rule for german (Bohemia under German control as the Protectorate).
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1939Q3: 6 of 357 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v02/d416>
- Decision: ______ Note: ______

**1939Q3-041** · `anglo_soviet_alliance` = **false** (hindsight: false (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d208`, dated 1939-08-09: Memorandum of Conversation, by the Acting Secretary of State; proposal dated 1939-08-09
- Quote: "the negotiations now in progress in Moscow between the British and French and the Soviets for a political and military agreement"
- Rule: claude backend: The flag is false while there is no concluded Anglo-Soviet alliance, and the passage shows the talks still in progress with no agreement reached.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1939Q3: 6 of 357 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d208>
- Decision: ______ Note: ______

**1939Q3-115** · `polish_guarantee` = **true** (hindsight: true (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d378`, dated 1939-08-28: The Chargé in Germany (Kirk) to the Secretary of State; proposal dated 1939-08-28
- Quote: "England would stand by its pledges to Poland"
- Rule: claude backend: The note refers to existing British pledges to Poland. That shows the British guarantee is in force, although this document does not give the date of the original statement.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1939Q3: 6 of 357 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d378>
- Decision: ______ Note: ______

**1939Q3-129** · `nazi_soviet_pact` = **true** (hindsight: true (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d395`, dated 1939-08-31: The Chargé in Germany (Kirk) to the Secretary of State; proposal dated 1939-08-31
- Quote: "The pact with Soviet Russia which at first was welcomed as a triumph on the part of Germany"
- Rule: claude backend: The flag is true once the German-Soviet pact is concluded; the chargé reports the pact as already concluded and first welcomed in Germany, though he does not name its terms.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1939Q3: 6 of 357 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d395>
- Decision: ______ Note: ______

**1939Q3-238** · `france` = **at_war** (hindsight: at_war (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d435`, dated 1939-09-15: The Ambassador in the United Kingdom (Kennedy) to the Secretary of State; proposal dated 1939-09-15
- Quote: "he does not concede France the slightest chance of breaking through the Siegfried line"
- Rule: claude backend: at_war: France is discussed as a belligerent on the western front, so it is no longer at peace with Germany.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: random check (1939Q3: 6 of 357 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d435>
- Decision: ______ Note: ______

**1939Q3-273** · `poland` = **partitioned** (hindsight: partitioned (1939Q3 end))

- File: `proposals/1939Q3.json`; document `frus:frus1939v01/d447`, dated 1939-09-18: The Minister in Yugoslavia (Lane) to the Secretary of State; proposal dated 1939-09-18
- Quote: "the invasion of Poland by Soviet troops in no way alters Yugoslavia’s position"
- Rule: claude backend: The partitioned level requires German and Soviet shares; the passage reports, as accomplished fact, a Soviet invasion of Poland, but the document does not itself state the German attack, so the German share has to be inferred.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1939Q3: 6 of 357 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d447>
- Decision: ______ Note: ______

### 1939Q4

**1939Q4-090** · `britain` = **at_war** (hindsight: at_war (1939Q4 end))

- File: `proposals/1939Q4.json`; document `frus:frus1939v01/d859`, dated 1939-10-19: The Ambassador in the United Kingdom (Kennedy) to the Secretary of State; proposal dated 1939-10-14
- Quote: "His Majesty’s Government are carrying out their published intention of exercising to the full their belligerent rights of visit and search."
- Rule: claude backend: Britain is at_war rather than at_peace because the British Government states it is exercising belligerent rights of visit and search, with contraband control in force for about a month.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1939Q4: 5 of 312 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d859>
- Decision: ______ Note: ______

**1939Q4-105** · `commit_WEST` = **at_war** (hindsight: at_war (1939Q4 end))

- File: `proposals/1939Q4.json`; document `frus:frus1940v03/d544`, dated 1939-10-23: The Chargé in Iran (Engert) to the Secretary of State; proposal dated 1939-10-23
- Quote: "the determination of the democracies to fight to a finish"
- Rule: claude backend: At_war level requires a declaration of war; the passage describes Britain and France as engaged in the war against Germany, implying war is in force.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1939Q4: 5 of 312 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v03/d544>
- Decision: ______ Note: ______

**1939Q4-134** · `poland` = **partitioned** (hindsight: partitioned (1939Q4 end))

- File: `proposals/1939Q4.json`; document `frus:frus1933-39/d600`, dated 1939-11-01: The Ambassador in the Soviet Union (Steinhardt) to the Secretary of State; proposal dated 1939-10-31
- Quote: "the collapse of the Polish State ... Soviet “liberation” of Western Ukraine and White Russia"
- Rule: claude backend: partitioned requires German and Soviet shares of Poland; the speech reports the Polish State's collapse and the Soviet taking of its eastern territories.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1939Q4: 5 of 312 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1933-39/d600>
- Decision: ______ Note: ______

**1939Q4-201** · `china_war` = **true** (hindsight: true (1939Q4 end))

- File: `proposals/1939Q4.json`; document `frus:frus1939v01/d485`, dated 1939-11-16: The Ambassador in the United Kingdom (Kennedy) to the Secretary of State; proposal dated 1939-11-16
- Quote: "while he thought the Chinese were the people to be with in this battle he was in no position to take the Japanese on in a wideopen break at this time"
- Rule: claude backend: china_war is true when Japan is engaged in a general war in China; Halifax's reference to the Chinese in 'this battle' against the Japanese implies an ongoing Sino-Japanese war.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1939Q4: 5 of 312 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d485>
- Decision: ______ Note: ______

**1939Q4-254** · `poland` = **partitioned** (hindsight: partitioned (1939Q4 end))

- File: `proposals/1939Q4.json`; document `frus:frus1939v01/d677`, dated 1939-11-29: The Chargé in the Soviet Union (Thurston) to the Secretary of State; proposal dated 1939-11-29
- Quote: "addressees in Soviet-occupied Poland"
- Rule: claude backend: The partitioned level needs a Soviet share of Poland; the telegram refers to an existing Soviet-occupied part of Poland, though it does not itself mention the German share.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1939Q4: 5 of 312 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1939v01/d677>
- Decision: ______ Note: ______

### 1940Q1

**1940Q1-034** · `britain` = **at_war** (hindsight: at_war (1940Q1 end))

- File: `proposals/1940Q1.json`; document `frus:frus1940v03/d78`, dated 1940-01-22: Memorandum of Conversation, by the Secretary of State; proposal dated 1940-01-22
- Quote: "the British situation as a belligerent engaged in a terrific war for its existence"
- Rule: claude backend: Britain is described outright as a belligerent engaged in war, and the document refers to its blockade of German exports, which meets at_war rather than at_peace.
- Confidence: high; harness: ok: confirms the current level
- Why sampled: random check (1940Q1: 3 of 175 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v03/d78>
- Decision: ______ Note: ______

**1940Q1-084** · `commit_WEST` = **at_war** (hindsight: at_war (1940Q1 end))

- File: `proposals/1940Q1.json`; document `frus:frus1940v01/d739`, dated 1940-02-16: The Panamanian Ambassador (Boyd) to the Secretary of State; proposal dated 1940-02-16
- Quote: "Germany and the other belligerent powers ... Great Britain and France"
- Rule: claude backend: at_war requires a declaration of war; the note treats Britain and France as belligerents against Germany, which implies the declaration is in force, though the declaration itself is not quoted.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: random check (1940Q1: 3 of 175 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v01/d739>
- Decision: ______ Note: ______

**1940Q1-105** · `austria` = **annexed** (hindsight: annexed (1940Q1 end))

- File: `proposals/1940Q1.json`; document `frus:frus1940v01/d28`, dated 1940-02-26: Report by the Under Secretary of State (Welles) on His Special Mission to Europe; proposal dated 1940-02-26
- Quote: "nothing later when Hitler occupied Austria"
- Rule: claude backend: Annexed means German troops in Austria and reunification in force; the passage refers to the German occupation and the Anschluss as accomplished.
- Confidence: high; harness: ok: confirms the current level
- Why sampled: random check (1940Q1: 3 of 175 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v01/d28>
- Decision: ______ Note: ______

### 1940Q2

**1940Q2-047** · `france` = **at_war** (hindsight: fallen (1940Q2 end))

- File: `proposals/1940Q2.json`; document `frus:frus1940v01/d145`, dated 1940-05-11: The Ambassador in France (Bullitt) to the Secretary of State; proposal dated 1940-05-11
- Quote: "there are more than 100 dead and wounded civilians in France as a result of German bombardments"
- Rule: claude backend: France is independent only while at peace with Germany; German bombardment of France with civilian casualties shows France at war, and the document reports no armistice.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1940Q2: 4 of 264 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v01/d145>
- Decision: ______ Note: ______

**1940Q2-137** · `commit_US` = **wary** (hindsight: wary (1940Q2 end))

- File: `proposals/1940Q2.json`; document `frus:frus1940v02/d829`, dated 1940-05-30: The Secretary of State to the Ambassador in Italy (Phillips); proposal dated 1940-05-30
- Quote: "a redoubling of the efforts of the Government of the United States to facilitate in every practical way the securing within the United States by the Allied Powers of all of the supplies and matériel which they may require"
- Rule: claude backend: Under the commit_US rule, a promise to 'redouble' existing efforts to help the belligerent Allied Powers obtain war matériel in the United States implies arms are already sold to belligerents, i.e. the mandatory embargo no longer applies (wary), though the repeal is not stated outright.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: random check (1940Q2: 4 of 264 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v02/d829>
- Decision: ______ Note: ______

**1940Q2-169** · `britain` = **at_war** (hindsight: at_war (1940Q2 end))

- File: `proposals/1940Q2.json`; document `frus:frus1940v03/d28`, dated 1940-06-10: The Ambassador in the United Kingdom (Kennedy) to the Secretary of State; proposal dated 1940-06-10
- Quote: "the majority of the English people feel America should be in this fight with the Allies"
- Rule: claude backend: Britain is at_war rather than at peace: the ambassador describes Britain as engaged in a fight alongside the Allies and refers to the US possibly entering the war.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1940Q2: 4 of 264 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v03/d28>
- Decision: ______ Note: ______

**1940Q2-196** · `france` = **at_war** (hindsight: fallen (1940Q2 end))

- File: `proposals/1940Q2.json`; document `frus:frus1940v01/d211`, dated 1940-06-14: The Ambassador in the United Kingdom (Kennedy) to the Secretary of State; proposal dated 1940-06-13
- Quote: "Reynaud at insistence of his Ministers must ask England to release France from her agreement not to sign separate peace"
- Rule: claude backend: France is still at war with Germany. It is asking to be released to seek a separate peace, so it is not at peace (independent), and no armistice is reported signed (fallen).
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1940Q2: 4 of 264 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v01/d211>
- Decision: ______ Note: ______

### 1940Q3

**1940Q3-003** · `france` = **fallen** (hindsight: fallen (1940Q2 end); fallen (1940Q3 end))

- File: `proposals/1940Q3.json`; document `frus:frus1940v02/d639`, dated 1940-07-02: The Consul General at Algiers (Cole) to the Secretary of State; proposal dated 1940-06-24
- Quote: "The Armistice is signed."
- Rule: claude backend: france is fallen once the armistice is signed, and General Noguès's proclamation dated 24 June 1940 states outright that it has been signed.
- Confidence: high; harness: ok: confirms the current level
- Why sampled: random check (1940Q3: 3 of 191 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v02/d639>
- Decision: ______ Note: ______

**1940Q3-032** · `france` = **fallen** (hindsight: fallen (1940Q3 end))

- File: `proposals/1940Q3.json`; document `frus:frus1940v02/d186`, dated 1940-07-11: The Consul at Bordeaux (Waterman) to the Secretary of State; proposal dated 1940-07-11
- Quote: "Border Hendaye opened 10th for Americans from occupied territory. Those from unoccupied territory should cross at Cerbere. Local German authorities anticipate"
- Rule: claude backend: Fallen requires the armistice signed; the passage shows France divided into occupied and unoccupied territory with German authorities at Bordeaux, which implies the armistice but does not state it.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: random check (1940Q3: 3 of 191 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v02/d186>
- Decision: ______ Note: ______

**1940Q3-172** · `france` = **fallen** (hindsight: fallen (1940Q3 end))

- File: `proposals/1940Q3.json`; document `frus:frus1940v01/d653`, dated 1940-09-22: The Ambassador in the Soviet Union (Steinhardt) to the Secretary of State; proposal dated 1940-09-22
- Quote: "the collapse of France and the consequent elimination of the only other continental army which might have opposed Germany"
- Rule: claude backend: Fallen means France is out of the war; the document treats France's collapse and the elimination of its army as accomplished fact, though it does not name the armistice itself.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1940Q3: 3 of 191 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v01/d653>
- Decision: ______ Note: ______

### 1940Q4

**1940Q4-059** · `oil_GER` = **secured** (hindsight: secured (1940Q4 end))

- File: `proposals/1940Q4.json`; document `frus:frus1940v01/d609`, dated 1940-10-23: The Ambassador in the Soviet Union (Steinhardt) to the Secretary of State; proposal dated 1940-10-23
- Quote: "German troops in Rumania ... protecting the oil fields"
- Rule: claude backend: secured includes Romania under German alignment in autumn 1940; German troops guarding the Romanian oil fields suggest an overland supply under German protection, but no supply agreement is stated.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: random check (1940Q4: 4 of 241 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v01/d609>
- Decision: ______ Note: ______

**1940Q4-073** · `britain` = **at_war** (hindsight: at_war (1940Q4 end))

- File: `proposals/1940Q4.json`; document `frus:frus1940v02/d672`, dated 1940-10-25: Memorandum of Conversation, by Mr. J. Rives Childs of the Division of Near Eastern Affairs; proposal dated 1940-10-25
- Quote: "to transport petroleum products from Aruba to Morocco through the British blockade"
- Rule: claude backend: A British blockade against Axis-linked trade indicates Britain is at war rather than at peace, negotiated or invaded.
- Confidence: medium; harness: ok: confirms the current level
- Why sampled: random check (1940Q4: 4 of 241 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v02/d672>
- Decision: ______ Note: ______

**1940Q4-083** · `commit_US` = **engaged** (hindsight: engaged (1940Q4 end))

- File: `proposals/1940Q4.json`; document `frus:frus1940v03/d18`, dated 1940-10-27: The British Prime Minister (Churchill) to President Roosevelt; proposal dated 1940-10-27
- Quote: "250,000 Enfield rifles and 50,000,000 rounds of ammunition have been sent."
- Rule: claude backend: engaged: the memorandum by the President's special assistant records US war material already transferred to Britain, a belligerent, which matches the rule's executive transfers of war material; the document does not say how the rifles were supplied or mention conscription.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: random check (1940Q4: 4 of 241 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v03/d18>
- Decision: ______ Note: ______

**1940Q4-240** · `france` = **fallen** (hindsight: fallen (1940Q4 end))

- File: `proposals/1940Q4.json`; document `frus:frus1940v02/d250`, dated 1940-12-30: The Chargé in France (Matthews) to the Secretary of State; proposal dated 1940-12-30
- Quote: "415 adults and 128 children in occupied France are registered for assistance"
- Rule: claude backend: The fallen level requires a signed armistice; the document only refers to 'occupied France' and a government at Vichy, which suggests France has fallen but does not state the armistice.
- Confidence: low; harness: ok: confirms the current level
- Why sampled: random check (1940Q4: 4 of 241 remaining)
- FRUS: <https://history.state.gov/historicaldocuments/frus1940v02/d250>
- Decision: ______ Note: ______
