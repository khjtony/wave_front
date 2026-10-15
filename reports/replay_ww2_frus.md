PROPOSAL-LEVEL MEASUREMENT: no proposal below was reviewed. Every proposal the rule backend made was treated as if accepted to compute these metrics, no replay snapshot was written, and the levels and quotes below are the backend's unreviewed readings, not evidence accepted by a reviewer.

# Blind replay of FRUS 1936 to 1940 with the rule backend: the real-document baseline

The first blind replay of the evidence pipeline on real documents ([docs/ww2_testbed.md](../docs/ww2_testbed.md) sections 8 and 9; [docs/replay_harness.md](../docs/replay_harness.md), section "Real FRUS baseline"). It measures the deterministic rule backend (`wavefront/evidence/extract/rules.py`) on the US diplomatic record, quarter by quarter from 1936Q1 to 1940Q4, against the hindsight snapshots in `snapshots/ww2/hindsight/` (as committed in `3e97f34`).

What it is: the baseline that the Claude backend has to beat, on the same corpus, filter and metrics. The rules were frozen before the run: they are the table written for the synthetic fixtures, with the five logged corrections of the synthetic run, and nothing in them was changed after seeing these results. The rule changes the results suggest are listed at the end and not applied. What it is not: a replay in the sense of section 8. The review step stays human, so no proposal was accepted; the metrics treat every proposal as if accepted (`wf replay --measure-proposals`), which measures what the backend proposes, not what a reviewer would keep. Blindness is by document date (section 7 item 5): each quarter reads only the documents whose own dateline is at or before the quarter's last day.

## Corpus

Twelve volumes of *Foreign Relations of the United States, Diplomatic Papers*, the General, British Commonwealth and Europe volumes for 1936 to 1940 and the Soviet Union volume for 1933 to 1939, fetched on 2026-10-13 from the Office of the Historian's TEI repository on GitHub (history.state.gov is blocked from this environment). URL pattern, given to `scripts/fetch_corpora.py frus --mirror`:

`https://raw.githubusercontent.com/HistoryAtState/frus/99d851c79a570dcd1a6594981600eaa2515c5bef/volumes/{volume}.xml`

The volume ids were read from the repository's `volumes/` listing at that commit and their titles from each file's `teiHeader`. The Far East volumes (1936 v04, 1937 v03 and v04, 1938 v03 and v04, 1939 v03 and v04, 1940 v04), the American Republics volumes (v05) and 1936 v03 (Near East and Africa) were not used. Sizes and SHA-256 of the files are in [data/ww2/corpora/frus/MANIFEST.json](../data/ww2/corpora/frus/MANIFEST.json).

| Volume | Title (volume part) | Historical documents in the volume | Indexed (dated 1936-01-01 to 1940-12-31) | Date range indexed | Bytes | SHA-256 (prefix) |
|---|---|---|---|---|---|---|
| `frus1936v01` | 1936, General, British Commonwealth | 691 | 683 | 1936-01-02 to 1937-01-27 | 5,558,969 | `39a3b4972220` |
| `frus1936v02` | 1936, Europe | 887 | 874 | 1936-01-02 to 1936-12-31 | 5,339,750 | `12138de165f8` |
| `frus1937v01` | 1937, General | 983 | 983 | 1936-11-25 to 1937-12-31 | 5,394,006 | `3a6eccb49bfc` |
| `frus1937v02` | 1937, The British Commonwealth, Europe, Near East and Africa | 752 | 751 | 1936-01-30 to 1938-01-31 | 5,437,689 | `e8ab158c0bd5` |
| `frus1938v01` | 1938, General | 955 | 955 | 1937-12-30 to 1939-02-22 | 5,353,974 | `b94431df4fde` |
| `frus1938v02` | 1938, The British Commonwealth, Europe, Near East, and Africa | 905 | 905 | 1937-01-28 to 1939-01-26 | 6,385,131 | `6d229f91ae54` |
| `frus1939v01` | 1939, General | 1,157 | 1,157 | 1939-01-10 to 1940-01-06 | 6,042,905 | `95bc517a64fd` |
| `frus1939v02` | 1939, General, The British Commonwealth and Europe | 871 | 871 | 1938-01-11 to 1940-05-28 | 5,113,798 | `328eb44b5721` |
| `frus1940v01` | 1940, General | 896 | 896 | 1939-11-09 to 1940-12-30 | 4,946,592 | `af38e46727a3` |
| `frus1940v02` | 1940, General and Europe | 1,012 | 1,005 | 1940-01-02 to 1940-12-31 | 5,568,835 | `202db7827686` |
| `frus1940v03` | 1940, The British Commonwealth, The Soviet Union, The Near East and Africa | 928 | 924 | 1939-06-12 to 1940-12-31 | 6,108,471 | `4648593328c3` |
| `frus1933-39` | The Soviet Union, 1933 to 1939 | 836 | 546 | 1936-01-09 to 1939-12-29 | 7,043,094 | `ccf5708a7e8d` |
| all | | 10,873 | **10,550** | 1936-01-02 to 1940-12-31 | 68,293,214 | |

"Historical documents" counts the documents the parser admits in the whole volume (dated, with text); the rest of the gap to the index is documents dated before 1936 or after 1940. One editorial note (`frus1940v02/d848a`) was skipped; no document was undated. Every document is dated by its own dateline (10,205 in the opener, 345 in the closer or the body), in the writer's local time; all are within one day of the editors' normalized `frus:doc-dateTime` range (165 documents of the twelve volumes differ by one day, across time zones). Excluded from the text, because the editors wrote them decades later: every `<note>` (source notes and footnotes), and the editors' bracketed insertions in the running text (found in 917 documents, 90,300 characters; 39 of them name a year later than the document's; see "Fixes to the harness" below).

Documents per quarter (dated at or before the quarter's end, and read at that quarter) are in the generated "Date filtering" table below: 266 to 937 new documents a quarter, 1,030 proposals in all, none discarded by the extractor's checks (every quote verbatim, no date after its document).

## How it was run

```
python3 scripts/fetch_corpora.py frus --since 1936-01-01 --until 1940-12-31 \
    --volumes frus1936v01,frus1936v02,frus1937v01,frus1937v02,frus1938v01,frus1938v02,frus1939v01,frus1939v02,frus1940v01,frus1940v02,frus1940v03,frus1933-39 \
    --mirror 'https://raw.githubusercontent.com/HistoryAtState/frus/99d851c79a570dcd1a6594981600eaa2515c5bef/volumes/{volume}.xml'
wf replay --corpus data/ww2/corpora/raw/frus --quarters 1936Q1..1940Q4 --out <scratch> \
    --measure-proposals --report <scratch>/metrics.md \
    --title "Replay metrics, FRUS 1936 to 1940, rule backend, proposal level"
```

`wf replay` runs the extractor once per quarter on the documents dated in that quarter (what `wf extract --since <day after the previous quarter's end> --until <quarter end>` does) and writes `<scratch>/proposals/<quarter>.json`, every proposal pending. `--measure-proposals` then builds the quarter-end snapshots in memory from all proposals, as if accepted, with the review step's own snapshot rules (a text variable takes the level of its latest proposal dated at or before the quarter's end), and computes the section 9 metrics. The section "Generated metrics" below is that `metrics.md`, unedited except that its headings are two levels lower.

## Results in brief

- **Agreement**: 356 of 500 text-variable quarters (71 percent). A replay that reads nothing and leaves every variable at its initial level scores 305 (61 percent). Split by the hindsight level: where nothing has happened yet (305 variable-quarters) the backend agrees on 182 (60 percent), so it moves a variable that should not have moved in 40 percent of them; where the level has moved (195), it agrees on 174 (89 percent), mostly structural flags that a keyword fires on once the event is in the news and that then never change again.
- **Beliefs and commitment**, the variables the replay exists for, are below the reading-nothing baseline: `belief_WEST` 3/20 (nothing: 10/20), `belief_GER` 2/20 (13/20), `commit_WEST` 8/20 (10/20), `commit_US` 14/20 (15/20). `belief_WEST` never reaches `hegemonic`; `belief_GER` reads `uncertain` from the first week of 1936.
- **Flips**: of the 9 documented belief and commitment flips, 4 are replayed within one quarter; 8 have a replayed flip to the same level within four quarters, but three of those come two or three quarters *early* (`commit_WEST` `wary` 303 days early, `resolved` 187 days early, `commit_US` `wary` 187 days early), which is a false reading paired by the window, not a timely one. Across all text variables: 29 false flips and 8 missed flips. Timely flips are the events whose own day is reported in a telegram: `rhineland` (0 days), `france` `fallen` (0), `bohemia` (-1), `commit_WEST` `at_war` (-2, from a 1 September report of the French Chamber's convocation), `commit_US` `engaged` (-4), `china_war` (+9), `belief_GER` `will_fight` (+12, from a rumour about Soviet intervention).
- **Proposals that cannot be right**: of the 724 proposals that assert a dated event (a pact signed, a region taken, a declaration of war), 191 (26 percent) are dated before the event they assert. This is a lower bound on the error rate; it does not count the proposals dated after the event that read a different sentence (a rumour, a plan, a recollection).

## What the rule backend got wrong on real diplomatic documents

The rules were written alongside period-style fixtures that state one event per document in the plain words of the ontology. FRUS documents are long, reported, conditional and retrospective, and written by American diplomats about other governments' views. Each failure below is quoted from the proposals of this run.

1. **Conditionals and hypotheticals read as facts.** Göring in conversation with the American ambassador, 23 November 1937 (`frus:frus1937v01/d100`): "because they feel that if Germany should again become involved in war with France and England, there would come a moment when the United States might again consider entering such a war against Germany". The `DECLARE_WAR` keywords ("declaration of war") and a Western party fire: `war_west_ger` = `war`, `france` = `at_war` and `commit_WEST` = `at_war` from 1937Q4, seven quarters before the war, which also makes the real flip of September 1939 count as missed. The same happens on 11 April 1939 (`frus:frus1939v01/d112`): "if Germany should attack Poland ... a French declaration of war against Germany might be delayed for some time".
2. **Negation.** 14 March 1936 (`frus:frus1936v01/d209`): "This Government does not consider the menace of the Anschluss to be immediate; in fact it considers it more remote." Rule `austria.annexed` fires on "anschluss"; Austria is annexed in the replay from 1936Q1 to the end. The correct sentence two years later, "Entry German troops into Austria last night ..." (12 March 1938, `frus:frus1938v01/d440`), changes nothing because the level is already `annexed`.
3. **Substrings and idioms.** "Daladier began by thanking Osusky for the great efforts he had made to persuade the Czechoslovak Government to make large concessions to the Sudeten." (23 June 1938, `frus:frus1938v01/d523`): the `sudeten.german` pattern `cession` matches inside "con*cession*s"; 30 of the 35 `sudeten` proposals are dated before Munich, 22 of them on "concessions". "We are prepared to fight on Far Eastern and Western frontiers simultaneously." (Soviet remarks reported 16 January 1936, `frus:frus1933-39/d297`) sets `britain` = `at_war` through the pattern `fight on\b`; "goods originating in the United Kingdom and Germany, the United States' principal competitors in this market" (30 April 1937, `frus:frus1937v02/d199`) fires the same rule through "united kingdom and germany".
4. **The same word in another field.** "It is this minimum guarantee feature (which was wrested from the Polish Government by the British Government as part of a deal wherewith new British capital was made available to Poland), which will represent the improvement over previous offers made to holders of the dollar tranche of the Stabilization Loan" (23 February 1938, `frus:frus1938v02/d507`): a bond guarantee becomes the Polish guarantee (`polish_guarantee` = true and `commit_WEST` = `resolved`).
5. **Background and recollection read as the present.** 2 April 1936 (`frus:frus1936v01/d232`): "Austen Chamberlain, the British delegate at the negotiations, refused to extend the guarantee of Great Britain to Poland" (about Locarno, 1925) sets `polish_guarantee` = true three years early. 26 February 1940 (`frus:frus1940v01/d28`, from Sumner Welles's record of his mission): "the British were willing to favor a negotiation ... but that if Germany invaded Poland Great Britain would fight" turns `poland` back from `partitioned` to `german`, because the latest proposal sets the level and a recollection is as recent as its document.
6. **Rumour and report.** "Fodor, Central European correspondent of the Chicago Daily News tells me that he feels satisfied that a non-aggression pact has recently been privately offered by Germany to Russia." (30 November 1938, `frus:frus1938v01/d69`): `nazi_soviet_pact` = true nine months before the pact.
7. **Direction of an alignment.** "the reply was “we should be very glad to do so if England would join France in guaranteeing us against Germany." (6 May 1937, `frus:frus1937v01/d59`): Romania asking for a guarantee *against* Germany reads as `balkans` = `german_aligned`, three years early (29 of the 45 `balkans` proposals are dated before the Second Vienna Award).
8. **Whose belief.** The belief rules assume a British or German speaker; FRUS reports everyone. "Exhorted Front members to the utmost discipline and warned against any infraction of “German peace.”" (9 March 1938, `frus:frus1938v01/d427`, about Schuschnigg and the Austrian Fatherland Front) is read as London adopting warnings towards Germany (`belief_WEST` = `uncertain`), and "A third alternative that the future affords might be the possible but remote contingency of conquest by, or union of, Germany and Russia." (6 June 1938, `frus:frus1933-39/d462`, an American assessment from Moscow) does the same. The rule for `belief_GER` = `uncertain` needs only "Hitler" and a word such as "whether" or "doubt", which diplomatic prose is full of: 93 proposals, the first on 3 January 1936.
9. **A precondition read as the event.** "the so-called “cash and carry” provisions of the Neutrality Act apply to articles other than arms, ammunition, and implements of war" (13 April 1938, `frus:frus1938v02/d244`) describes the 1937 Act; the rule `commit_US.wary` treats "cash and carry" as the 1939 repeal of the embargo.
10. **Paraphrase misses the keyword; long documents fire everything.** `belief_WEST` = `hegemonic` is never proposed: the rule wants the words of the Birmingham speech, and the corpus reports it as "Chamberlain’s Birmingham speech is held generally to have radically reversed the situation as to Peace prospects for the year." (30 March 1939, `frus:frus1939v01/d99`). Conversely Welles's long record of 26 February 1940 (`frus:frus1940v01/d28`) yields twelve proposals, one per variable whose keywords occur anywhere in it, including `austria` from "many who wish the Anschluss had not taken place" and `war_west_ger` from Göring's counterfactual "Germany would not have declared war on England and France."

What the structure of the backend adds to these sentence errors: one false positive on a variable that changes once (a pact, an annexation, a declaration of war) holds until the event and hides the correct reading of the event itself. Chamberlain's statement of 31 March 1939 is in the corpus verbatim (`frus:frus1939v01/d100`, "His Majesty’s Government would feel themselves bound at once to lend the Polish Government all support in their power"), and `polish_guarantee.true` fires on it correctly; the flip is still counted as missed because the flag had been true since the Locarno sentence of April 1936. The same holds for `austria`, `war_west_ger`, `france` `at_war` and `britain` `at_war`. On the belief variables the latest proposal wins, so the level follows whichever sentence with "warning" or "general settlement" came last: `belief_WEST` flips eight times without a documented flip.

Even the timely flips are mostly right by date and wrong by reading. The first `rhineland` proposal, on the right day, is a question: "I asked Litvinov if he hoped that France would march troops into the Rhineland." (7 March 1936, `frus:frus1936v01/d181`). `bohemia` flips one day early on a speculation ("It looks now as though this intervention may consist (1) of a military occupation not only of Slovakia and Ruthenia but possibly also Bohemia and Moravia", 14 March 1939, `frus:frus1939v01/d29`); `china_war` flips on a denial ("both the Chinese and Japanese authorities have been earnestly protesting any purpose on either part to bring about a general state of hostilities", 16 July 1937, `frus:frus1937v01/d711`); `treaty` flips three weeks early on "While Germany considers Franco-Soviet pact as breach of Locarno ..." (15 February 1936, `frus:frus1936v01/d173`). Read correctly: the Franco-German armistice (22 June 1940, `frus:frus1940v01/d233`), the Protectorate decree notified on 17 March 1939 (`frus:frus1939v01/d38`, after the speculative flip), and destroyers for bases (29 August 1940, `frus:frus1940v03/d63`, after a false flip on a 1938 report of a naval bases board).

## Rule changes this suggests (not applied; the rules are frozen for this baseline)

1. Word boundaries on every keyword (`\bcession\b`, not `cession`), and no bare idioms (`fight on` only with a British subject).
2. A modality filter for event rules: skip sentences with `if`, `should`, `would`, `might`, `may`, `in the event of`, `rumou?red`, `believe(s|d) that`, `possible`, `prepared to`; event rules require a past or present-perfect verb, as `poland.german` already does.
3. A negation window: `not`, `no`, `never`, `refused`, `denied` within a few words of the key.
4. A retrospective filter: skip a sentence that names a year before the document's year, or "at the time", "in 19xx", "last August".
5. Speaker and subject gates for the belief variables: `belief_WEST` only with a British government subject (Prime Minister, Foreign Secretary, His Majesty's Government, Halifax, Chamberlain, Eden) as the one who warns or settles; `belief_GER` only with Hitler or the German government as the one who doubts or expects.
6. Field exclusions: `guarantee` with `loan`, `bond`, `tranche`, `stabilization`; `united kingdom and germany` with `goods`, `exports`, `market`.
7. Direction: `balkans.german_aligned` should exclude `against Germany`.
8. `commit_US.wary` on the repeal, not on `cash and carry`.

Two changes belong to the harness or the review rather than the rules, and are listed for the decision of the owner: a variable that changes once (pacts, regions, war) could need two independent documents before a proposal is shown as a flip, and a retrospective sentence should not be able to move a region back from `partitioned` to `german`. Neither is applied here: they would change what the metric measures.

## Uncertainties

- The metrics treat every proposal as accepted. A reviewer would reject most of the failures above and accept some correct proposals, so a reviewed replay with this backend would score differently; this run does not say how.
- The hindsight snapshots were being revised in parallel with this run (the levels compared are those of commit `3e97f34`). The proposals do not depend on them; the metrics can be recomputed after a revision by running `wf replay --out <scratch> --quarters 1936Q1..1940Q4 --measure-proposals` on the same proposals.
- The mirror is a copy of the Office of the Historian's TEI on GitHub, not history.state.gov itself; it could not be compared with the official host from here. The commit is pinned and the checksums are recorded.
- Dating by the dateline follows the protocol, but a despatch sent by pouch reached Washington weeks later: about 165 documents carry a receipt stamp ("[Received ...]", kept in the text as part of the filed document) in a later quarter than their dateline. A replay dated by receipt would see them one quarter later.
- Some documents are printed in two volumes (two exact duplicates, and near-duplicates such as `frus1936v01/d273` and `frus1936v02/d104`); their proposals are counted twice, which does not change a level.
- The bracket filter is a heuristic (see the next section). Short bracketed restorations inside sentences ("[sic]", "[Washington,]", "[are denied]") and eleven longer inline brackets are kept; at least one of these ("[The first procedure envisaged had been ...]", `frus1938v02/d216`) is probably editorial. Document titles (the editors' headings, such as "The Ambassador in France (Bullitt) to the Secretary of State") are not read by the rule backend but are shown to the Claude backend.
- The hindsight snapshot of an early quarter can cite, as its latest indicator, an event after that quarter (for example `belief_GER` in 1936Q1 cites Munich, 1938-09-30); that is how the hindsight builder records the latch, not a replay leak, and it only affects the wording of the disagreement list.

## Fixes to the harness made for real documents

- **Editorial insertions in square brackets** (`wavefront/evidence/corpora/frus.py`, `strip_editorial`). The FRUS editors wrote summaries, cross-references and narrative bridges into the running text, in brackets and without markup, and some of them carry post-dated facts into a document: "[Here follows text of aide-mémoire handed to the Italian Ambassador August 31, 1939, printed infra.]" in a telegram of 30 August 1939 (`frus1939v02/d587`); "[In telegram No. 215, June 13, 1941, 7 p.m., to the Minister in Egypt, the Department stated ...]" after a despatch of October 1940 (`frus1940v03/d390`); "[Discussions with the Yugoslav Government regarding a possible trade agreement were not continued.]" (`frus1939v02/d852`). The parser now leaves out every paragraph or run of paragraphs that is one bracketed span (other than a receipt stamp), and inside paragraphs the "Here follows" summaries and the cross-references ("supra", "infra", "not printed", "here omitted", "see page"). Tested on the TEI sample of the tests (single and multi-paragraph spans, receipt stamp and restorations kept) and on the real `frus1939v01` when it is present (no insertion left; every date within a day of the editors' range).
- **`--mirror`** on `scripts/fetch_corpora.py frus` (and a `mirror` argument of `frus.fetch`): the raw-file URL pattern, so the fetch can pin a commit of the repository. The manifest records the URL actually fetched.
- **`--measure-proposals`** on `wf replay` and the reading-nothing baseline in every report (`wavefront/evidence/replay.py`; the review step marks a measured indicator NOT REVIEWED). Tested on the synthetic fixtures: no snapshot written, proposals left pending, and metrics identical to the auto-accepted synthetic run.

Nothing else in the harness broke on the real volumes: the TEI parsed with the standard library, no encoding problem, one editorial note skipped, 10,550 documents indexed and validated by `scripts/fetch_corpora.py --check frus`, and the replay of all twenty quarters took about 40 seconds.

## Generated metrics

The output of the `wf replay ... --measure-proposals` command above, unedited except that its headings are two levels lower.

### Replay metrics, FRUS 1936 to 1940, rule backend, proposal level

- Quarters: 1936Q1 to 1940Q4 (20); snapshot compared at each quarter's last day.
- Corpus: frus, `data/ww2/corpora/raw/frus`
- Backend: rules
- Review: none: proposal-level measurement (every proposal treated as accepted, nothing written)
- Command: `wf replay --quarters 1936Q1..1940Q4 --out OUT --corpus data/ww2/corpora/raw/frus --measure-proposals`
- Target: the hindsight snapshots in `snapshots/ww2/hindsight/` (levels at each quarter's end, read with full knowledge of the record).

#### Date filtering

| Quarter | Documents dated at or before its end | Read this quarter | Proposals | Discarded by the checks |
|---|---|---|---|---|
| 1936Q1 | 320 | 320 | 48 | 0 |
| 1936Q2 | 586 | 266 | 16 | 0 |
| 1936Q3 | 1118 | 532 | 18 | 0 |
| 1936Q4 | 1624 | 506 | 20 | 0 |
| 1937Q1 | 2054 | 430 | 9 | 0 |
| 1937Q2 | 2508 | 454 | 21 | 0 |
| 1937Q3 | 3003 | 495 | 13 | 0 |
| 1937Q4 | 3447 | 444 | 44 | 0 |
| 1938Q1 | 3965 | 518 | 67 | 0 |
| 1938Q2 | 4470 | 505 | 39 | 0 |
| 1938Q3 | 4978 | 508 | 71 | 0 |
| 1938Q4 | 5453 | 475 | 26 | 0 |
| 1939Q1 | 5838 | 385 | 42 | 0 |
| 1939Q2 | 6275 | 437 | 115 | 0 |
| 1939Q3 | 6957 | 682 | 144 | 0 |
| 1939Q4 | 7733 | 776 | 39 | 0 |
| 1940Q1 | 8185 | 452 | 31 | 0 |
| 1940Q2 | 9122 | 937 | 59 | 0 |
| 1940Q3 | 9824 | 702 | 71 | 0 |
| 1940Q4 | 10550 | 726 | 137 | 0 |

#### Proposals per variable

Every proposal kept by the extractor's checks over the quarters, by level.

| Variable | Proposals | By level |
|---|---|---|
| `belief_WEST` | 113 | uncertain 81, limited 32 |
| `belief_GER` | 102 | uncertain 93, will_not_fight 7, will_fight 2 |
| `commit_WEST` | 78 | resolved 49, at_war 27, wary 2 |
| `commit_US` | 11 | wary 7, engaged 4 |
| `treaty` | 14 | dead 14 |
| `axis` | 217 | true 217 |
| `anticomintern` | 59 | true 59 |
| `nazi_soviet_pact` | 27 | true 27 |
| `polish_guarantee` | 56 | true 56 |
| `anglo_soviet_alliance` | 1 | false 1 |
| `ussr_axis` | 3 | false 3 |
| `italy_estranged` | 27 | true 27 |
| `china_war` | 6 | true 6 |
| `war_west_ger` | 27 | war 27 |
| `rhineland` | 12 | remilitarized 12 |
| `austria` | 52 | annexed 52 |
| `sudeten` | 35 | german 35 |
| `bohemia` | 13 | german 13 |
| `poland` | 57 | partitioned 40, german 17 |
| `france` | 30 | at_war 18, fallen 12 |
| `britain` | 28 | at_war 27, negotiated 1 |
| `balkans` | 45 | german_aligned 45 |
| `siberia` | 1 | soviet 1 |
| `channel_air` | 8 | contested 7, british 1 |
| `oil_GER` | 8 | secured 8 |
| all | 1030 | |

#### Summary against section 9

- Text-derived variables, exact level agreement over variable-quarters: 356/500 (71%).
- For scale: a replay that reads nothing (every text variable at its initial level) agrees on 305/500 (61%). Split by the hindsight level: where it is still the initial one, this replay agrees on 182/305 (60%); where it has moved, on 174/195 (89%).
- Resource variables: 100/100 (100%), but they are copied from the hindsight snapshots (they come from the datasets), so this checks the copy, not a reading; the section 9 target of 80 percent for resource variables is not tested by a replay of documents.
- Belief and commitment flips: 4 of 9 documented flips replayed within one quarter (8 matched within 4 quarters).
- False flips (replayed, no documented flip to the same level within 4 quarters): 29. Missed flips: 8.

#### Agreement per variable

| Group | Variable | Agreement | Reading nothing | Quarters that disagree (hindsight / replay) |
|---|---|---|---|---|
| beliefs and commitment | `belief_WEST` | 3/20 (15%) | 10/20 (50%) | 1936Q1 (limited / uncertain), 1936Q2 (limited / uncertain), 1936Q3 (limited / uncertain), 1936Q4 (limited / uncertain), 1937Q1 (limited / uncertain), 1937Q2 (limited / uncertain), 1937Q3 (limited / uncertain), 1938Q2 (limited / uncertain), 1938Q4 (uncertain / limited), 1939Q1 (hegemonic / uncertain), 1939Q2 (hegemonic / limited), 1939Q3 (hegemonic / uncertain), 1939Q4 (hegemonic / uncertain), 1940Q1 (hegemonic / limited), 1940Q2 (hegemonic / uncertain), 1940Q3 (hegemonic / uncertain), 1940Q4 (hegemonic / uncertain) |
| beliefs and commitment | `belief_GER` | 2/20 (10%) | 13/20 (65%) | 1936Q1 (will_not_fight / uncertain), 1936Q2 (will_not_fight / uncertain), 1936Q3 (will_not_fight / uncertain), 1936Q4 (will_not_fight / uncertain), 1937Q1 (will_not_fight / uncertain), 1937Q2 (will_not_fight / uncertain), 1937Q3 (will_not_fight / uncertain), 1937Q4 (will_not_fight / uncertain), 1938Q1 (will_not_fight / uncertain), 1938Q2 (will_not_fight / uncertain), 1938Q3 (will_not_fight / uncertain), 1938Q4 (will_not_fight / uncertain), 1939Q1 (will_not_fight / uncertain), 1939Q4 (will_fight / uncertain), 1940Q1 (will_fight / uncertain), 1940Q2 (will_fight / will_not_fight), 1940Q3 (will_fight / uncertain), 1940Q4 (will_fight / uncertain) |
| beliefs and commitment | `commit_WEST` | 8/20 (40%) | 10/20 (50%) | 1936Q2 (appease / resolved), 1936Q3 (appease / resolved), 1936Q4 (appease / resolved), 1937Q1 (appease / resolved), 1937Q2 (appease / resolved), 1937Q3 (appease / resolved), 1937Q4 (appease / wary), 1938Q1 (appease / wary), 1938Q2 (appease / at_war), 1938Q3 (wary / resolved), 1938Q4 (wary / resolved), 1940Q1 (at_war / resolved) |
| beliefs and commitment | `commit_US` | 14/20 (70%) | 15/20 (75%) | 1938Q2 (isolationist / wary), 1938Q3 (isolationist / wary), 1938Q4 (isolationist / wary), 1939Q1 (isolationist / engaged), 1939Q2 (isolationist / wary), 1939Q3 (isolationist / wary) |
| treaty | `treaty` | 20/20 (100%) | 0/20 (0%) | - |
| pacts and structural flags | `axis` | 17/20 (85%) | 3/20 (15%) | 1936Q1 (false / true), 1936Q2 (false / true), 1936Q3 (false / true) |
| pacts and structural flags | `anticomintern` | 17/20 (85%) | 3/20 (15%) | 1936Q1 (false / true), 1936Q2 (false / true), 1936Q3 (false / true) |
| pacts and structural flags | `nazi_soviet_pact` | 17/20 (85%) | 14/20 (70%) | 1938Q4 (false / true), 1939Q1 (false / true), 1939Q2 (false / true) |
| pacts and structural flags | `polish_guarantee` | 9/20 (45%) | 12/20 (60%) | 1936Q2 (false / true), 1936Q3 (false / true), 1936Q4 (false / true), 1937Q1 (false / true), 1937Q2 (false / true), 1937Q3 (false / true), 1937Q4 (false / true), 1938Q1 (false / true), 1938Q2 (false / true), 1938Q3 (false / true), 1938Q4 (false / true) |
| pacts and structural flags | `anglo_soviet_alliance` | 20/20 (100%) | 20/20 (100%) | - |
| pacts and structural flags | `ussr_axis` | 20/20 (100%) | 20/20 (100%) | - |
| pacts and structural flags | `italy_estranged` | 20/20 (100%) | 20/20 (100%) | - |
| pacts and structural flags | `china_war` | 20/20 (100%) | 6/20 (30%) | - |
| war | `war_west_ger` | 13/20 (65%) | 14/20 (70%) | 1937Q4 (peace / war), 1938Q1 (peace / war), 1938Q2 (peace / war), 1938Q3 (peace / war), 1938Q4 (peace / war), 1939Q1 (peace / war), 1939Q2 (peace / war) |
| regions | `rhineland` | 20/20 (100%) | 0/20 (0%) | - |
| regions | `austria` | 12/20 (60%) | 8/20 (40%) | 1936Q1 (independent / annexed), 1936Q2 (independent / annexed), 1936Q3 (independent / annexed), 1936Q4 (independent / annexed), 1937Q1 (independent / annexed), 1937Q2 (independent / annexed), 1937Q3 (independent / annexed), 1937Q4 (independent / annexed) |
| regions | `sudeten` | 19/20 (95%) | 10/20 (50%) | 1938Q2 (czech / german) |
| regions | `bohemia` | 20/20 (100%) | 12/20 (60%) | - |
| regions | `poland` | 4/20 (20%) | 14/20 (70%) | 1936Q2 (independent / partitioned), 1936Q3 (independent / partitioned), 1936Q4 (independent / partitioned), 1937Q1 (independent / partitioned), 1937Q2 (independent / partitioned), 1937Q3 (independent / partitioned), 1937Q4 (independent / partitioned), 1938Q1 (independent / partitioned), 1938Q2 (independent / partitioned), 1938Q3 (independent / german), 1938Q4 (independent / german), 1939Q1 (independent / german), 1939Q2 (independent / partitioned), 1939Q3 (partitioned / german), 1940Q1 (partitioned / german), 1940Q2 (partitioned / german) |
| regions | `france` | 13/20 (65%) | 14/20 (70%) | 1937Q4 (independent / at_war), 1938Q1 (independent / at_war), 1938Q2 (independent / at_war), 1938Q3 (independent / at_war), 1938Q4 (independent / at_war), 1939Q1 (independent / at_war), 1939Q2 (independent / at_war) |
| regions | `britain` | 6/20 (30%) | 14/20 (70%) | 1936Q1 (at_peace / at_war), 1936Q2 (at_peace / at_war), 1936Q3 (at_peace / at_war), 1936Q4 (at_peace / at_war), 1937Q1 (at_peace / at_war), 1937Q2 (at_peace / at_war), 1937Q3 (at_peace / at_war), 1937Q4 (at_peace / at_war), 1938Q1 (at_peace / at_war), 1938Q2 (at_peace / at_war), 1938Q3 (at_peace / at_war), 1938Q4 (at_peace / at_war), 1939Q1 (at_peace / at_war), 1939Q2 (at_peace / at_war) |
| regions | `balkans` | 7/20 (35%) | 18/20 (90%) | 1937Q2 (neutral / german_aligned), 1937Q3 (neutral / german_aligned), 1937Q4 (neutral / german_aligned), 1938Q1 (neutral / german_aligned), 1938Q2 (neutral / german_aligned), 1938Q3 (neutral / german_aligned), 1938Q4 (neutral / german_aligned), 1939Q1 (neutral / german_aligned), 1939Q2 (neutral / german_aligned), 1939Q3 (neutral / german_aligned), 1939Q4 (neutral / german_aligned), 1940Q1 (neutral / german_aligned), 1940Q2 (neutral / german_aligned) |
| regions | `siberia` | 20/20 (100%) | 20/20 (100%) | - |
| regions | `channel_air` | 19/20 (95%) | 19/20 (95%) | 1940Q4 (british / contested) |
| oil | `oil_GER` | 16/20 (80%) | 16/20 (80%) | 1939Q1 (dependent / secured), 1939Q2 (dependent / secured), 1939Q3 (dependent / secured), 1939Q4 (dependent / secured) |
| resources (copied) | `arms_GER` | 20/20 (100%) | - | - |
| resources (copied) | `arms_WEST` | 20/20 (100%) | - | - |
| resources (copied) | `arms_USSR` | 20/20 (100%) | - | - |
| resources (copied) | `arms_JPN` | 20/20 (100%) | - | - |
| resources (copied) | `ind_GER` | 20/20 (100%) | - | - |

#### Flips: lag against the documented date

A documented flip is a change of level between consecutive hindsight snapshots, dated by the event that set the new level; a replayed flip is the same in the replay snapshots, dated by the proposal (treated as accepted) that set it. Lag is replay minus documented (positive: the replay is late).

| Variable | Level | Documented (quarter, date) | Replayed (quarter, date) | Lag (quarters) | Lag (days) |
|---|---|---|---|---|---|
| `belief_WEST` | uncertain | 1938Q3, 1938-09-12 | 1938Q2, 1938-06-06 | -1 | -98 |
| `belief_WEST` | hegemonic | 1939Q1, 1939-03-17 | none (missed) | - | - |
| `belief_WEST` | uncertain | none (false flip) | 1936Q1, 1936-01-03 | - | - |
| `belief_WEST` | limited | none (false flip) | 1937Q4, 1937-12-23 | - | - |
| `belief_WEST` | limited | none (false flip) | 1938Q4, 1938-11-29 | - | - |
| `belief_WEST` | uncertain | none (false flip) | 1939Q1, 1939-01-24 | - | - |
| `belief_WEST` | limited | none (false flip) | 1939Q2, 1939-05-03 | - | - |
| `belief_WEST` | uncertain | none (false flip) | 1939Q3, 1939-08-10 | - | - |
| `belief_WEST` | limited | none (false flip) | 1940Q1, 1940-03-01 | - | - |
| `belief_WEST` | uncertain | none (false flip) | 1940Q2, 1940-04-01 | - | - |
| `belief_GER` | uncertain | 1939Q2, 1939-05-23 | 1939Q4, 1939-11-05 | +2 | +166 |
| `belief_GER` | will_fight | 1939Q3, 1939-09-03 | 1939Q3, 1939-09-15 | +0 | +12 |
| `belief_GER` | uncertain | none (false flip) | 1936Q1, 1936-01-03 | - | - |
| `belief_GER` | will_not_fight | none (false flip) | 1940Q2, 1940-05-10 | - | - |
| `belief_GER` | uncertain | none (false flip) | 1940Q3, 1940-07-20 | - | - |
| `commit_WEST` | wary | 1938Q3, 1938-09-30 | 1937Q4, 1937-12-01 | -3 | -303 |
| `commit_WEST` | resolved | 1939Q1, 1939-03-31 | 1938Q3, 1938-09-25 | -2 | -187 |
| `commit_WEST` | at_war | 1939Q3, 1939-09-03 | 1939Q3, 1939-09-01 | +0 | -2 |
| `commit_WEST` | resolved | none (false flip) | 1936Q2, 1936-04-02 | - | - |
| `commit_WEST` | at_war | none (false flip) | 1938Q2, 1938-05-16 | - | - |
| `commit_WEST` | resolved | none (false flip) | 1940Q1, 1940-03-06 | - | - |
| `commit_WEST` | at_war | none (false flip) | 1940Q2, 1940-06-01 | - | - |
| `commit_US` | wary | 1939Q4, 1939-11-04 | 1939Q2, 1939-05-01 | -2 | -187 |
| `commit_US` | engaged | 1940Q3, 1940-09-02 | 1940Q3, 1940-08-29 | +0 | -4 |
| `commit_US` | wary | none (false flip) | 1938Q2, 1938-04-13 | - | - |
| `commit_US` | engaged | none (false flip) | 1939Q1, 1938-12-27 | - | - |
| `treaty` | dead | 1936Q1, 1936-03-07 | 1936Q1, 1936-02-15 | +0 | -21 |
| `axis` | true | 1936Q4, 1936-10-23 | 1936Q1, 1936-02-22 | -3 | -244 |
| `anticomintern` | true | 1936Q4, 1936-11-25 | 1936Q1, 1936-01-23 | -3 | -307 |
| `nazi_soviet_pact` | true | 1939Q3, 1939-08-23 | 1938Q4, 1938-11-30 | -3 | -266 |
| `polish_guarantee` | true | 1939Q1, 1939-03-31 | none (missed) | - | - |
| `polish_guarantee` | true | none (false flip) | 1936Q2, 1936-04-02 | - | - |
| `china_war` | true | 1937Q3, 1937-07-07 | 1937Q3, 1937-07-16 | +0 | +9 |
| `war_west_ger` | war | 1939Q3, 1939-09-03 | none (missed) | - | - |
| `war_west_ger` | war | none (false flip) | 1937Q4, 1937-11-23 | - | - |
| `rhineland` | remilitarized | 1936Q1, 1936-03-07 | 1936Q1, 1936-03-07 | +0 | +0 |
| `austria` | annexed | 1938Q1, 1938-03-12 | none (missed) | - | - |
| `austria` | annexed | none (false flip) | 1936Q1, 1936-03-14 | - | - |
| `sudeten` | german | 1938Q3, 1938-09-30 | 1938Q2, 1938-04-26 | -1 | -157 |
| `bohemia` | german | 1939Q1, 1939-03-15 | 1939Q1, 1939-03-14 | +0 | -1 |
| `poland` | partitioned | 1939Q3, 1939-09-17 | 1939Q2, 1939-06-05 | -1 | -104 |
| `poland` | partitioned | none (false flip) | 1936Q2, 1936-04-20 | - | - |
| `poland` | german | none (false flip) | 1938Q3, 1938-09-24 | - | - |
| `poland` | german | none (false flip) | 1939Q3, 1939-09-19 | - | - |
| `poland` | partitioned | none (false flip) | 1939Q4, 1939-11-09 | - | - |
| `poland` | german | none (false flip) | 1940Q1, 1940-02-26 | - | - |
| `poland` | partitioned | none (false flip) | 1940Q3, 1940-07-26 | - | - |
| `france` | at_war | 1939Q3, 1939-09-03 | none (missed) | - | - |
| `france` | fallen | 1940Q2, 1940-06-22 | 1940Q2, 1940-06-22 | +0 | +0 |
| `france` | at_war | none (false flip) | 1937Q4, 1937-11-23 | - | - |
| `britain` | at_war | 1939Q3, 1939-09-03 | none (missed) | - | - |
| `britain` | at_war | none (false flip) | 1936Q1, 1936-01-16 | - | - |
| `balkans` | german_aligned | 1940Q3, 1940-08-30 | none (missed) | - | - |
| `balkans` | german_aligned | none (false flip) | 1937Q2, 1937-05-06 | - | - |
| `channel_air` | british | 1940Q4, 1940-10-31 | none (missed) | - | - |
| `oil_GER` | secured | 1940Q1, 1940-02-11 | 1939Q1, 1939-02-20 | -4 | -356 |

#### Disagreements and the indicators behind them

At the first quarter of each run of disagreement: the hindsight level with its latest event, and the replay level with the latest proposal's (unreviewed) quote.

- `belief_WEST`, 1936Q1: hindsight `limited` from 1936-03-09: "Eden's Commons statement treats the reoccupation as a treaty breach, not a threat of hostilities; no British military response"; replay `uncertain` from 1936-03-25: "If it came to this latter contingency it would mean an entirely new line-up in Europe since it would mean that all ideas of collective security had been abandoned; that Central and Eastern Europe must look after themselves while the Little Entente would most necessarily turn to Germany as the great power in its region and that future trouble was delayed but not eliminated with a bloc in Western Europe strong enough to resist Germany for some time to come but with all the rest of the Continent delivered to German domination.".
- `belief_WEST`, 1938Q2: hindsight `limited` from 1938-05-20: "May crisis: Czechoslovak partial mobilization on reports of German troop movements; British warnings to Berlin (21 May)"; replay `uncertain` from 1938-06-06: "A third alternative that the future affords might be the possible but remote contingency of conquest by, or union of, Germany and Russia.".
- `belief_WEST`, 1938Q4: hindsight `uncertain` from 1938-09-12: "Sudeten demand: Hitler's Nuremberg speech demands self-determination for the Sudeten Germans; escalated at Berchtesgaden (15 September) and Godesberg (22 to 23 September)"; replay `limited` from 1938-11-29: "He replied that much to his sorrow he felt that a negotiated settlement between the parties in dispute was no longer possible.".
- `belief_GER`, 1936Q1: hindsight `will_not_fight` from 1938-09-30: "Britain and France concede the Sudetenland at Munich"; replay `uncertain` from 1936-03-18: "In this present situation in the Rhineland, there is no shadow of a legal doubt in the question, but there is plenty of equity or extenuating circumstances or whatever you like to call it, and these should not be lost sight of, even through Hitler’s brutality.".
- `belief_GER`, 1939Q4: hindsight `will_fight` from 1939-09-03: "The declarations of war disprove the expectation of 22 August"; replay `uncertain` from 1939-11-05: "The impression prevails that some delay in action has occurred but whether this apparent delay is due to continued regard for the possibility of a peace or to the perfection of plans for the further consolidation of German strength both at home and abroad or to some other consideration, it is believed that the final action either in war or in peace will now, as in the past, depend upon the conclusions at which Hitler will eventually arrive as to the means which he regards as best adapted to attain his aims and as to the time for their initiation.".
- `commit_WEST`, 1936Q2: hindsight `appease` from 1935-06-18: "Anglo-German Naval Agreement accepts German naval rearmament"; replay `resolved` from 1936-04-04: "The recent Italo-Austro-Hungarian discussions in Rome followed by the announcement of conscription in Austria, which the Foreign Office here somewhat contemptuously describes as “made in Italy,” demonstrate Italy’s continued and increasing interest in this German field of development despite Italy’s activity in Abyssinia and possibly because of her success there which flouts the British Empire, confirms the strength of French dependence on Italy, and supports the imperium romanum idea with which Mussolini seems obsessed.".
- `commit_WEST`, 1940Q1: hindsight `at_war` from 1939-09-03: "Britain and France declare war on Germany"; replay `resolved` from 1940-03-06: "He said that if the American Government would give a guarantee the British Government would respect it but that it would be very difficult for his Government to agree that American societies should carry relief to Poland because he did not know what societies might be organized and what might happen to the supplies that were permitted to reach Poland.".
- `commit_US`, 1938Q2: hindsight `isolationist` from 1935-08-31: "Neutrality Act of 1935: mandatory arms embargo on all belligerents"; replay `wary` from 1938-04-13: "In other words, the so-called “cash and carry” provisions of the Neutrality Act apply to articles other than arms, ammunition, and implements of war, the export of arms, ammunition, and implements of war to belligerents being totally prohibited as soon as the President issues a proclamation finding that a state of war exists.".
- `axis`, 1936Q1: hindsight `false` from 1936-10-23: "Rome-Berlin protocols signed by Ciano and Neurath; announced by Mussolini as an 'axis' on 1 November 1936"; replay `true` from 1936-03-18: "Sanctions to be suppressed against Italy and excluded from application to Germany while the Franco-Russian pact is eventually to be referred to Hague Tribunal.".
- `anticomintern`, 1936Q1: hindsight `false` from 1936-11-25: "Anti-Comintern Pact between Germany and Japan"; replay `true` from 1936-01-23: "The French consider it desirable to try to reach some agreement temporarily to which we should endeavor to get Japan, Germany and Russia to adhere at a later date, but that unless Japan, at least, were to become a party to the agreement they could not see that it would be of much value.".
- `nazi_soviet_pact`, 1938Q4: hindsight `false` from 1939-08-23: "Molotov-Ribbentrop Pact, with the secret protocol on spheres of interest"; replay `true` from 1938-11-30: "Fodor, Central European correspondent of the Chicago Daily News tells me that he feels satisfied that a non-aggression pact has recently been privately offered by Germany to Russia.".
- `polish_guarantee`, 1936Q2: hindsight `false` from 1939-03-31: "British guarantee to Poland announced in the Commons; France associated"; replay `true` from 1936-04-02: "The Polish representative at Locarno at the time the treaty was concluded, the then Minister for Foreign Affairs, Count Aleksander Skrzynski, had insisted that the security of Poland be provided for in the proposed treaty but Austen Chamberlain, the British delegate at the negotiations, refused to extend the guarantee of Great Britain to Poland and stated in unequivocal terms that such guarantee would be confined to the preservation of the status quo regarding the frontiers of Belgium, France and Germany.".
- `war_west_ger`, 1937Q4: hindsight `peace` from 1939-09-03: "Britain and France declare war on Germany"; replay `war` from 1937-11-23: "Goering then said: “It is true that certain persons in our Government here believe that we should attempt to organize the Germans, especially of the Middle West, because they feel that if Germany should again become involved in war with France and England, there would come a moment when the United States might again consider entering such a war against Germany and they believe that such groups of organized Germans in the United States might throw their influence decisively against a declaration of war and might prevent the United States entering such a conflict.[”]".
- `austria`, 1936Q1: hindsight `independent` from 1938-03-12: "German troops enter Austria (12 March); law on the reunification of Austria with the Reich (13 March)"; replay `annexed` from 1936-03-14: "This Government does not consider the menace of the Anschluss to be immediate; in fact it considers it more remote.".
- `sudeten`, 1938Q2: hindsight `czech` from 1938-09-30: "Munich Agreement (signed in the early hours of 30 September, dated 29 September); occupation 1 to 10 October 1938"; replay `german` from 1938-06-23: "Daladier began by thanking Osusky for the great efforts he had made to persuade the Czechoslovak Government to make large concessions to the Sudeten.".
- `poland`, 1936Q2: hindsight `independent` from 1939-09-01: "Germany attacks Poland"; replay `partitioned` from 1936-04-20: "Every feasible route for German attack leads across Polish territory and the whole basis of Polish policy is never to permit the foot of either a German or a Russian soldier to be placed on her soil.".
- `poland`, 1940Q1: hindsight `partitioned` from 1939-09-17: "Soviet forces enter eastern Poland; the partition is fixed by the German-Soviet Boundary and Friendship Treaty (28 September)"; replay `german` from 1940-02-26: "He gave me a very careful account of the statements made by the British Government to Hitler in August, 1939, to convince me that Chamberlain had made it completely clear to Hitler that the British were willing to favor a negotiation between Poland and Germany of the Danzig and German minority issues, but that if Germany invaded Poland Great Britain would fight.".
- `france`, 1937Q4: hindsight `independent` from 1939-09-03: "France declares war on Germany"; replay `at_war` from 1937-11-23: "Goering then said: “It is true that certain persons in our Government here believe that we should attempt to organize the Germans, especially of the Middle West, because they feel that if Germany should again become involved in war with France and England, there would come a moment when the United States might again consider entering such a war against Germany and they believe that such groups of organized Germans in the United States might throw their influence decisively against a declaration of war and might prevent the United States entering such a conflict.[”]".
- `britain`, 1936Q1: hindsight `at_peace` from 1939-09-03: "Britain declares war on Germany"; replay `at_war` from 1936-01-16: "Notes of his remarks made by Kuniholm who was present are: We are prepared to fight on Far Eastern and Western frontiers simultaneously.".
- `balkans`, 1937Q2: hindsight `neutral` from 1940-08-30: "Second Vienna Award: Germany and Italy guarantee the remainder of Romania"; replay `german_aligned` from 1937-05-06: "Every time that he suggested to Czechoslovakia, Rumania, Yugoslavia or Austria that they should together with France take a more decided attitude of opposition to Germany the reply was “we should be very glad to do so if England would join France in guaranteeing us against Germany.".
- `channel_air`, 1940Q4: hindsight `british` from 1940-10-31: "End of the daylight battle (British official dating); Sea Lion postponed to the spring on 12 October 1940 after the first postponement of 17 September"; replay `contested` from 1940-11-01: "Erkko thought such an opportunity had been presented by failure of German air attack on Britain as well as by success of British evacuation of Dunkirk.".
- `oil_GER`, 1939Q1: hindsight `dependent` from 1936-10-18: "Four-Year Plan decree: synthetic fuel programme to reduce dependence on imported oil"; replay `secured` from 1939-02-20: "An agreement regulating trade between the two countries on a basis of parity between exports and imports whereby the Soviet Union will purchase in Germany machinery and equipment other than those clearly for military purposes and will sell to that country an amount equal in value of some 15 categories of raw materials including timber, mostly pulp logs, manganese ore, flax, cotton and small quantities of iron and oil.".

## Harness rules adopted, 2026-10-15

The owner adopted the two harness changes left for decision above (decision 9 of 2026-10-15). They are implemented in the replay and review layer (`wavefront/evidence/harness_rules.py`), not in the keyword table, which stays frozen; their exact semantics are in [docs/replay_harness.md](../docs/replay_harness.md), section "Harness rules". In short:

- **`two-document`**: a flip of a variable that changes once (every flag, and every variable `models/ww2/v0.py` declares monotone: the pacts, the regions but `rhineland`, `war_west_ger`, and also `belief_WEST`, `commit_WEST`, `commit_US` and `oil_GER`) is shown for review and counted only when a second document (another document id, dated at or before the quarter) proposes the same level; the flip is then carried and dated by the second document's proposal.
- **`no-retrospective`**: a proposal that would move a variable back to an earlier level is never applied to a monotone variable; for another variable (`belief_GER`, `treaty`, `rhineland`, `italy_estranged`) it is flagged `retrospective?` and not counted by the measurement (a reviewer may accept it).

Both are on by default, switchable with `--rules`, recorded in the proposals files, and named in every generated report. The baseline above was measured before they existed; nothing in it changes.

### How it was measured

The same 1,030 proposals as the baseline (the proposals files of the baseline run, not re-extracted), against the same hindsight snapshots (unchanged since `3e97f34`), with the rules off, each alone, and both:

```
wf replay --out <scratch> --quarters 1936Q1..1940Q4 --measure-proposals --rules none \
    --report <scratch>/m_none.md
wf replay --out <scratch> --quarters 1936Q1..1940Q4 --measure-proposals --rules two-document \
    --report <scratch>/m_two.md
wf replay --out <scratch> --quarters 1936Q1..1940Q4 --measure-proposals --rules no-retrospective \
    --report <scratch>/m_back.md
wf replay --out <scratch> --quarters 1936Q1..1940Q4 --measure-proposals \
    --report <scratch>/m_both.md                  # the default: both rules
```

With `--rules none` the generated report is identical to the "Generated metrics" section above, line for line, apart from the new line naming the rules in force: the rule backend was not changed and the harness reproduces the baseline.

### Side by side

| Measure | Rules off (baseline) | `two-document` only | `no-retrospective` only | Both (default) |
|---|---|---|---|---|
| Text variables, agreement over 500 variable-quarters | 356 (71%) | 383 (77%) | 357 (71%) | **389 (78%)** |
| where the hindsight level is still the initial one (305) | 182 (60%) | 211 (69%) | 180 (59%) | 209 (69%) |
| where it has moved (195) | 174 (89%) | 172 (88%) | 177 (91%) | 180 (92%) |
| Reading nothing, for scale | 305 (61%) | 305 (61%) | 305 (61%) | 305 (61%) |
| Belief and commitment flips replayed within one quarter (of 9) | 4 | 4 | 1 | 2 |
| matched within four quarters | 8 | 8 | 1 | 3 |
| False flips, all text variables | 29 | 27 | 14 | **11** |
| Missed flips, all text variables | 8 | 8 | 15 | 14 |
| Proposals counted (of 1,030) | 1,030 | 1,005 | 894 | 890 |
| held: one document / first of two documents | - | 2 / 23 | - | 3 / 20 |
| blocked: monotone, back / `retrospective?` | - | - | 112 / 24 | 93 / 24 |

Per variable (quarters in agreement, of 20):

| Group | Variable | Reading nothing | Rules off (baseline) | `two-document` only | `no-retrospective` only | Both (default) |
|---|---|---|---|---|---|---|
| beliefs and commitment | `belief_WEST` | 10/20 | 3/20 | 3/20 | 2/20 | 2/20 |
| beliefs and commitment | `belief_GER` | 13/20 | 2/20 | 2/20 | 7/20 | 7/20 |
| beliefs and commitment | `commit_WEST` | 10/20 | 8/20 | 8/20 | 7/20 | 7/20 |
| beliefs and commitment | `commit_US` | 15/20 | 14/20 | 18/20 | 11/20 | 18/20 |
| treaty | `treaty` | 0/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| pacts and structural flags | `axis` | 3/20 | 17/20 | 17/20 | 17/20 | 17/20 |
| pacts and structural flags | `anticomintern` | 3/20 | 17/20 | 20/20 | 17/20 | 20/20 |
| pacts and structural flags | `nazi_soviet_pact` | 14/20 | 17/20 | 19/20 | 17/20 | 19/20 |
| pacts and structural flags | `polish_guarantee` | 12/20 | 9/20 | 12/20 | 9/20 | 12/20 |
| pacts and structural flags | `anglo_soviet_alliance` | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| pacts and structural flags | `ussr_axis` | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| pacts and structural flags | `italy_estranged` | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| pacts and structural flags | `china_war` | 6/20 | 20/20 | 18/20 | 20/20 | 18/20 |
| war | `war_west_ger` | 14/20 | 13/20 | 15/20 | 13/20 | 15/20 |
| regions | `rhineland` | 0/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| regions | `austria` | 8/20 | 12/20 | 14/20 | 12/20 | 14/20 |
| regions | `sudeten` | 10/20 | 19/20 | 19/20 | 19/20 | 19/20 |
| regions | `bohemia` | 12/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| regions | `poland` | 14/20 | 4/20 | 8/20 | 7/20 | 11/20 |
| regions | `france` | 14/20 | 13/20 | 15/20 | 13/20 | 15/20 |
| regions | `britain` | 14/20 | 6/20 | 7/20 | 3/20 | 7/20 |
| regions | `balkans` | 18/20 | 7/20 | 10/20 | 7/20 | 10/20 |
| regions | `siberia` | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| regions | `channel_air` | 19/20 | 19/20 | 19/20 | 20/20 | 19/20 |
| oil | `oil_GER` | 16/20 | 16/20 | 19/20 | 16/20 | 19/20 |

What the rules did with both on, as generated (the "What the harness rules did" table of the measurement, unedited):

| Variable | Proposals | Shown and counted | Held: one document | First of two documents | Blocked: monotone, back | retrospective? (not counted) |
|---|---|---|---|---|---|---|
| `belief_WEST` | 113 | 80 | 0 | 1 | 32 | 0 |
| `belief_GER` | 102 | 78 | 0 | 0 | 0 | 24 |
| `commit_WEST` | 78 | 34 | 0 | 2 | 42 | 0 |
| `commit_US` | 11 | 9 | 0 | 2 | 0 | 0 |
| `treaty` | 14 | 14 | 0 | 0 | 0 | 0 |
| `axis` | 217 | 216 | 0 | 1 | 0 | 0 |
| `anticomintern` | 59 | 58 | 0 | 1 | 0 | 0 |
| `nazi_soviet_pact` | 27 | 26 | 0 | 1 | 0 | 0 |
| `polish_guarantee` | 56 | 55 | 0 | 1 | 0 | 0 |
| `anglo_soviet_alliance` | 1 | 1 | 0 | 0 | 0 | 0 |
| `ussr_axis` | 3 | 3 | 0 | 0 | 0 | 0 |
| `italy_estranged` | 27 | 27 | 0 | 0 | 0 | 0 |
| `china_war` | 6 | 5 | 0 | 1 | 0 | 0 |
| `war_west_ger` | 27 | 26 | 0 | 1 | 0 | 0 |
| `rhineland` | 12 | 12 | 0 | 0 | 0 | 0 |
| `austria` | 52 | 51 | 0 | 1 | 0 | 0 |
| `sudeten` | 35 | 34 | 0 | 1 | 0 | 0 |
| `bohemia` | 13 | 12 | 0 | 1 | 0 | 0 |
| `poland` | 57 | 39 | 1 | 1 | 16 | 0 |
| `france` | 30 | 25 | 0 | 2 | 3 | 0 |
| `britain` | 28 | 26 | 1 | 1 | 0 | 0 |
| `balkans` | 45 | 44 | 0 | 1 | 0 | 0 |
| `siberia` | 1 | 1 | 0 | 0 | 0 | 0 |
| `channel_air` | 8 | 7 | 1 | 0 | 0 | 0 |
| `oil_GER` | 8 | 7 | 0 | 1 | 0 | 0 |
| all | 1030 | 890 | 3 | 20 | 93 | 24 |

### What the rules change, and what they do not

- **The two-document rule delays the rule backend's false flips more than it removes them.** Its false readings come from keywords that recur across the record, so a second document is nearly always found: of the 1,030 proposals only 2 stay held at the end. Alone it removes 2 of the 29 false flips. What it does is move them later and onto a second, often different, misreading: `austria` is annexed from 1936-07-11 instead of 1936-03-14 (the Austro-German agreement's own "the Anschluss propaganda would fall in the category, as it is contrary to the principle of the independence of Austria", `frus:frus1936v01/d256`), `britain` at war from 1936-06-04 ("get in the fight on trade barriers", `frus:frus1936v01/d625`) instead of 1936-01-16, `polish_guarantee` from 1937-02-20 ("Poland should give a guarantee to Czechoslovakia", `frus:frus1937v01/d39`) instead of 1936-04-02, `poland` partitioned from 1937-05-20 (doubts about Soviet aid over "Soviet roads and railroads leading to the west", `frus:frus1937v01/d62`) instead of 1936-04-20. The gain in agreement (356 to 383) is those quarters of delay, and four flips that only one document had made early: `anticomintern` now flips 29 days early instead of 307, `nazi_soviet_pact` 76 days early instead of 266, `oil_GER` 103 days instead of 356, and `commit_US` loses its two false flips of 1938 and 1939.
- **The no-retrospective rule removes the oscillations and freezes the first error.** `belief_WEST` flipped eight times without a documented flip in the baseline; with the rule it flips once, to `uncertain` in January 1936, and never moves again, because every later `limited` reading is a move back on a variable v0 declares monotone (32 blocked) and `hegemonic` is never proposed. `commit_WEST` goes to `resolved` in April 1936 and to `at_war` in May 1938 (a French minister's conditional about "a French declaration of war") and then stays there, so all three documented commitment flips are missed (42 blocked). `poland` no longer falls back from `partitioned` to `german` on Welles's recollection of 26 February 1940, which is the case the report named; but the same rule also keeps `poland` partitioned from the 1937 misreading on. `belief_GER`, which is not monotone, keeps `uncertain` from January 1936 because its 24 later readings of `will_not_fight` are back to its initial level and are flagged, not counted; the documented `will_fight` flip is still read twelve days late.
- **Together**: false flips fall from 29 to 11, agreement rises from 71 to 78 percent (and above the reading-nothing baseline by 17 points instead of 10), and missed flips rise from 8 to 14. The belief and commitment flips, the variables the replay exists for, get worse: 2 of 9 within a quarter instead of 4, 3 matched within four quarters instead of 8 (three of the baseline's eight were early misreadings paired by the window, as the baseline notes; with the rules on, the earlier misreading is the one that sticks). Missed flips rise because a level already in force from a misreading cannot flip to itself: `austria` (annexed since 1936), `war_west_ger`, `france` and `britain` at war since 1938 or 1936, `poland` partitioned since 1937.
- **Neither rule makes a wrong reading right.** They change which wrong reading the measurement keeps: the two-document rule asks a misreading to occur twice, which a keyword misreading does; the no-retrospective rule then keeps whichever misreading came first. A backend that reads a sentence correctly gains from both rules (a single stray reading no longer flips a pact, a recollection no longer moves a region back); a backend whose first reading of a variable is wrong is penalized harder than without them, since the error now holds to the end. The reviewer, who sees held, blocked and `retrospective?` proposals marked as such, stays the safeguard.

### What this means for the comparison with the Claude backend

The figures above change what the metric measures, as the baseline section said they would. The comparison with the Claude backend is therefore made on both settings, from the same proposals: the rules-off figures above (356/500, 29 false flips, 4 of 9 timely belief and commitment flips) remain the baseline of the backend alone, and the rules-on figures (389/500, 11 false flips, 2 of 9) are the baseline of the harness as adopted. The commands of [docs/replay_harness.md](../docs/replay_harness.md), section "Running the Claude backend on the real corpus", produce both reports for the Claude run.

Caveats. The monotone set is the v0 model's (`belief_WEST`, `commit_WEST`, `commit_US` and `oil_GER` included); if belief and commitment were meant to stay outside "a variable that changes once", the two-document set and the strict no-retrospective set both narrow by those four, and the measurement can be redone in seconds on these proposals. Documents printed in two volumes under two ids count as two documents (listed as an open item in the harness document). The rules act on a measurement here, where every proposal counts as accepted; in a reviewed replay they act on the accepted proposals, so a reviewer who rejects the January 1936 `belief_WEST` reading leaves the variable free to move later.
