# Implementation delays of the AGI model: sources and proposed values (2026-11-14)

Status: research note, web sources only, for the owner's review (docs/agi_v0_1.md section 7). Nothing here is in any model yet; each value enters a later version, one at a time. Verification status is stated per fact ("verified": the page was read; "search-snippet"; "memory": not fetched).

## Mapping rule (used throughout)

Let L be the observed lag from the action (decision, announcement or launch) to the first
measurable effect. Then delay d = round(L / 3 months), and any L shorter than about 6 weeks gives 0.
This matches the convention that 0 means "visible next quarter". It also reproduces the owner's
EU AI Act value: 13 Mar 2024 to 2 Aug 2025 is 16.6 months, 5.5 quarters, which rounds to 6.

Caveat: a strict reading of "0 = visible next quarter" would be d = round(L/3mo) - 1. Under that
reading, every value below drops by 1, floored at 0. The model should pick one rule and state it.

"Verified" below means I fetched the page and read the quoted text. "Search-snippet" means the
text appeared in search results but I could not open the page. "Memory" means I did not fetch it
this session.

## Summary table

| action | proposed d (quarters) | source(s) with date | quote (key fact) | mapping rule | confidence |
|---|---|---|---|---|---|
| H.regulate_up (statute) | **6** if counted from the Parliament vote; **5** from final Council adoption; **4** from entry into force | EU AI Act, Reg. (EU) 2024/1689, Art. 113 (https://artificialintelligenceact.eu/article/113/; OJ 12 Jul 2024). Parliament vote 13 Mar 2024, Council adoption 21 May 2024, entry into force 1 Aug 2024 (memory) | Art. 113: Chapter V (GPAI) applies "from 2 August 2025"; Chapters I–II from 2 Feb 2025 | 13 Mar 2024 to 2 Aug 2025 = 16.6 mo, rounds to 6. 21 May 2024 to 2 Aug 2025 = 14.4 mo, rounds to 5. 1 Aug 2024 to 2 Aug 2025 = 12 mo, which is 4 | High for the dates; the anchor choice is a modelling decision |
| H.regulate_up (executive / export control) | **0** | Anthropic statement, 12 Jun 2026, https://www.anthropic.com/news/fable-mythos-access ; Mayer Brown, 30 Jun 2026 | "has issued an export control directive to suspend all access to Fable 5 and Mythos 5"; the directive arrived "today at 5:21pm (ET)" and the models were removed the same day | Lag of hours, under 6 weeks, so 0 | High (verified) |
| H.fund_oversight | **3** (range 2–4) | UK AISI, "Advanced AI evaluations at AISI: May update", 20 May 2024, https://www.aisi.gov.uk/blog/advanced-ai-evaluations-may-update . Frontier AI Taskforce £100m announced 24 Apr 2023; AISI launched 2 Nov 2023 (memory) | "Our first technical blog post shares a snapshot of our methods and results." | Funding (24 Apr 2023) to first published results (20 May 2024) = 13 mo, which is 4. Institute launch to results = 6.6 mo, which is 2. Midpoint 3 | Medium. The results date is verified; the two start dates are from memory |
| H.nationalize | **1** (assumed; equity stake alone is 0) | Intel press release, 22 Aug 2025, https://www.intc.com/news-events/press-releases/detail/1748/ ; closing 27 Aug 2025 (secondary source citing an SEC filing, not verified) | US to buy "433.3 million primary shares … equivalent to a 9.9 percent stake" | Equity stake took 5 days, so 0. Operational control of a lab (staff, weights, compute) has no precedent; assumed about one quarter | Low |
| H.propose_treaty | **2** (non-binding declaration); binding treaty much longer | Bletchley Declaration, gov.uk, 1 Nov 2023 (https://www.gov.uk/government/publications/ai-safety-summit-2023-the-bletchley-declaration/...). UK announced the summit 7 Jun 2023 (memory; not confirmed by search) | Signed by "28 countries and the European Union" on 1 Nov 2023 | 7 Jun 2023 to 1 Nov 2023 = 4.8 mo, rounds to 2. The Council of Europe AI Convention was adopted 17 May 2024 and opened for signature 5 Sep 2024 (memory); I did not verify an entry-into-force date | Medium for 2; low for the binding variant |
| H.grant_rights | **4** (assumed) | None. No jurisdiction has granted legal rights to AI systems. | n/a | Assumed. A statutory change takes about as long as the AI Act (5–6 quarters); an executive or judicial route might take 2. 4 is the middle | Low (assumed) |
| H.pause_mandate | **0** | (1) Anthropic, 12 Jun 2026 (above). (2) Garante privacy, urgent order n. 112 of 30 Mar 2023; OpenAI blocked ChatGPT in Italy on 31 Mar 2023; Garante press release 12 Apr 2023, https://www.garanteprivacy.it/home/docweb/-/docweb-display/print/9874751 | (1) "we must abruptly disable Fable 5 and Mythos 5 for all our customers". (2) 12 Apr 2023: "OpenAI avrà tempo fino al 30 aprile per adempiere…" (OpenAI has until 30 April to comply) | Lag of 0–1 days, so 0. Both precedents also show reversal within 3–4 weeks | High |
| H.shutdown_attempt | **0** | Same as pause_mandate | Same | Same. A shutdown of an already-released model happened within hours (Jun 2026) | High for a lab that complies; untested against a non-complying actor or an exfiltrated model |
| H.deregulate (executive) | **0** | US EO 14148, 20 Jan 2025, revoked EO 14110 on day one (memory); BIS rescinded the AI Diffusion Rule 13 May 2025, before its 15 May compliance date (memory) | n/a (not fetched) | Effective on signature, so 0 | Medium-high |
| H.deregulate (statute) | **3** | EU Digital Omnibus on AI: proposed 19 Nov 2025 (memory), Reg. (EU) 2026/1744 in force 27 Jul 2026 (Orrick, Jul 2026: https://www.orrick.com/en/Insights/2026/07/EU-AI-Act-Update-Digital-Omnibus-Finalizes-8-Compliance-Changes ; secondary) | Annex III high-risk obligations move from Aug 2026 to "2 December 2027" | 19 Nov 2025 to 27 Jul 2026 = 8.3 mo, rounds to 3 | Medium (secondary sources; Council dates differ: 29 Jun vs 8 Jul 2026) |
| L.scale | **1** (fast end); **2** (typical) | xAI Colossus: Musk post / coverage, 2 Sep 2024 (https://convergedigest.com/xai-activates-project-colossus-in-memphis-with-100k-h100-gpus/ ; https://www.tomshardware.com/...xai-colossus-supercomputer-with-100k-h100-gpus-comes-online...) | 100,000 H100s online "122 days" after the build started; Musk said it would double to 200k "in a few months" (a later report: 92 days) | 122 d = 4.0 mo, which is 1.3 q and rounds to 1; 92 d rounds to 1 | Medium. The 122-day figure is Musk's own claim, and the build reused an existing factory shell with chips already bought. Greenfield builds are slower; 2 is a defensible typical value |
| L.build_power | **4** (onsite / behind-the-meter fast end only); grid-connected new firm power is **8–16+** | IEA, Energy and AI, Apr 2025, exec. summary https://www.iea.org/reports/energy-and-ai/executive-summary (search-snippet; page returned 403) | "Building new transmission lines can take four to eight years in advanced economies"; gas turbines "face lead times of several years" | Transmission 4–8 yr = 16–32 q; new gas plant "several years" = 8+ q. 4 (one year) is only supportable for onsite or mobile generation, as at Colossus | Medium that 4 is the fast end; the IEA text does not itself support 4 |
| A.self_improve | **2** | METR, "Measuring AI Ability to Complete Long Tasks", 19 Mar 2025, https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/ | "with a doubling time of around 7 months"; a SWE-bench Verified subset gave "under 3 months" | If one capability level is one doubling of task horizon: 7 mo, which is 2.3 q and rounds to 2 (1 on the fast subset) | Medium as a capability-trend proxy. There is no source for recursive self-improvement itself (assumed) |
| L.deploy_agents (a) autonomy | **0** | Fable 5 launch 9 Jun 2026 (iClarified, 9 Jun 2026: https://www.iclarified.com/101151/...); Vercel changelog, 1 Jul 2026, https://vercel.com/changelog/claude-fable-5-access-restored-on-ai-gateway | Available at launch on the API, Claude Code and the clouds; Vercel: the same model as "available June 9–12" | Capability is live on the launch day, so 0 | High |
| L.deploy_agents (b) dependence | **3** for a society- or enterprise-wide level step (keep 3); **1** for early-adopter usage | (1) Anthropic Series F post, 2 Sep 2025, https://www.anthropic.com/news/anthropic-raises-series-f-at-usd183b-post-money-valuation . (2) Anthropic Economic Index, 15 Sep 2025, https://www.anthropic.com/research/anthropic-economic-index-september-2025-report . (3) McKinsey State of AI, Nov 2025 (secondary). (4) Census BTOS (https://census.gov/library/stories/2026/05/ai-use-businesses.html) | (1) Claude Code usage "growing more than 10x in just three months" after GA (22 May 2025), run-rate over $500M. (2) "Directive" (full delegation) conversations rose from 27% to 39%, Dec 2024/Jan 2025 to Aug 2025; 77% of API use shows automation patterns. (3) 23% of firms scaling an agentic system, 39% experimenting. (4) Under the old wording, business AI use was about 10% in late 2025, double mid-2024 | Usage uptake: under 1 q, but 10x within 3 mo, which is 1. Delegation shift of one level: about 8 mo, which is 3. BTOS doubling: about 15–18 mo, which is 5–6. Use 3 as the middle | Medium. Different metrics give 1 to 6 quarters |
| L.safety_invest | **2** (assumed); targeted mitigation **0–1** | Anthropic "Redeploying Fable 5", 30 Jun 2026, https://www.anthropic.com/news/redeploying-fable-5 ; Vercel 1 Jul 2026 | "As of today, June 30, the export controls on Fable 5 and Mythos 5 have been lifted"; redeployed with "updated and strengthened" safety classifiers (Vercel) | Targeted classifier fix: 12 Jun to 30 Jun = 18 d, so 0. General safety research or staffing to results has no clean source; assumed 2 | Low for 2; medium for the 0 targeted case |
| L.lobby | **2** (assumed) | Weak proxy: EU Digital Omnibus delay, which industry sought in 2025 and which came into force 27 Jul 2026 (see H.deregulate) | n/a | Lobbying to policy outcome takes months to quarters. No clean attribution exists. Assumed 2 | Low (assumed) |
| L.comply | **0** | Anthropic, 12 Jun 2026 (above); Mayer Brown, 30 Jun 2026 | "We are complying with the government's legal directive and are removing access to Fable 5 and Mythos 5 for all users." | Same day, so 0 | High |
| L.race | **1** | Anthropic frontier release cadence in 2025: Claude 3.7 Sonnet 24 Feb, Claude 4 22 May, Opus 4.1 5 Aug, Sonnet 4.5 29 Sep, Opus 4.5 24 Nov (memory; anthropic.com/news) | n/a (not fetched) | Interval 2–3 mo between frontier releases, so 1 | Medium-low (dates from memory) |
| L.open_weights | **0** | DeepSeek-R1 released 20 Jan 2025; #1 on the US App Store and Nvidia down about 17% on 27 Jan 2025 (memory) | n/a (not fetched) | Diffusion within 7 days, so 0. Irreversible once released | Medium (dates from memory) |

## Changes against current values

- **H.regulate_up 6**: keep 6 only if the anchor is the Parliament vote. From formal adoption it is 5, and from entry into force it is 4. Split it from executive regulation, which is 0.
- **H.fund_oversight 3**: now partly verified. The AISI first-results date (20 May 2024) is confirmed; the plausible range is 2–4.
- **L.scale 2**: the fast end (Colossus) supports 1. Keep 2 only as a "typical" value.
- **L.build_power 4**: justified only for onsite generation. The IEA's own numbers for grid and new gas plants imply 8 or more.
- **A.self_improve 2**: consistent with METR's 7-month doubling as a proxy.
- **Not yet carried**: H.nationalize 2 to 1 (assumed). H.propose_treaty 2 confirmed for a declaration. H.grant_rights 2 to 4 (assumed). L.deploy_agents is split into 0 (autonomy) and 3 (dependence). L.safety_invest 2 (assumed).

## L.deploy_agents in detail

**Part (a), autonomy step: 0. This confirms the owner's view.** A frontier agent product is usable at full capability on its launch day. Fable 5 was on the API, Claude Code and the cloud platforms from 9 Jun 2026. Vercel describes the same model as having been "available June 9–12". Claude Code went GA on 22 May 2025 and was usable that day.

**Part (b), dependence step.** Each measure gives a different lag:

| measure | source | lag | quarters |
|---|---|---|---|
| Product usage among early adopters (Claude Code) | Anthropic, 2 Sep 2025: usage "more than 10x in just three months", run-rate over $500M | under 3 mo to 10x | 1 |
| Codex daily usage | OpenAI (Oct 2025 GA, via secondary OfficeChai): over 10x since early Aug 2025. Primary page openai.com/index/codex-now-generally-available returned 403; not verified | about 2 mo | 1 |
| Shift in how people rely on AI (delegation over collaboration) | Anthropic Economic Index, 15 Sep 2025: directive conversations went from 27% to 39%, Dec 2024–Jan 2025 to Aug 2025 | about 8 mo for +12 points | 3 |
| Enterprise scaling of agents | McKinsey State of AI, Nov 2025 (secondary): 23% scaling, 39% experimenting. That is about 1 year after the first agent products (Operator Jan 2025, Claude Code Feb 2025 preview) | about 9–12 mo to roughly a quarter of firms | 3–4 |
| Economy-wide business AI use | Census BTOS: about 10% in late 2025 under the old wording, double mid-2024; 17–20% Dec 2025–May 2026 under the new wording (census.gov story, May 2026) | about 15–18 mo per doubling | 5–6 |

**Recommendation.** The dependence step lags: 3 if a "level" means measurable reliance among enterprises and power users, and 5 if it means economy-wide use. Usage itself responds within 1. Note that all these figures describe AI use broadly. None of them isolates the effect of one launch.

## The June 2026 Fable 5 / Mythos 5 event

| date (2026) | event | source | status |
|---|---|---|---|
| Tue 9 Jun | Claude Fable 5 launched publicly (API, Claude Code, AWS/GCP/Foundry); Mythos 5 to Glasswing / Mythos Preview partners only | iClarified, 9 Jun 2026 (https://www.iclarified.com/101151/anthropic-launches-claude-fable-5-with-unprecedented-coding-and-vision-capabilities); Vercel changelog, 1 Jul ("June 9–12") | Verified (secondary plus Vercel); Anthropic's launch post URL not found |
| Fri 12 Jun, 5:21pm ET | Commerce (BIS) export-control "is-informed" letter signed by Sec. Lutnick: no access by any foreign national, in or outside the US. Anthropic disabled both models for all users the same day | Anthropic, https://www.anthropic.com/news/fable-mythos-access (12 Jun); Mayer Brown, 30 Jun (https://www.mayerbrown.com/en/insights/publications/2026/06/commerce-department-extends-export-controls-to-advanced-ai-models-authorizes-release-to-specific-trusted-partners); GT Law, 17 Jun; Bloomberg, 16 Jun ("Read the Lutnick letter…") | Verified. The letter itself is not public; there is no Federal Register notice |
| Fri 26 Jun | Second Lutnick letter exempts "certain trusted partners" for Mythos 5. Anthropic restores Mythos 5 to a set of US critical-infrastructure organizations | Mayer Brown, 30 Jun; Anthropic redeploy post | Verified |
| Tue 30 Jun | Export controls on Fable 5 and Mythos 5 lifted | Anthropic, "Redeploying Fable 5", https://www.anthropic.com/news/redeploying-fable-5 : "As of today, June 30, the export controls on Fable 5 and Mythos 5 have been lifted." | Verified |
| Wed 1 Jul | Fable 5 restored globally on the Claude Platform, Claude.ai, Claude Code and Cowork. The clouds followed later ("as quickly as possible"). Mythos 5 still limited; broader Glasswing access "being coordinated with the government" | Anthropic redeploy post; Vercel changelog, 1 Jul 2026 | Verified |

Release to suspension was 3 days. Suspension to lift was 18 days, and to restoration 19 days. In
model terms, a government pause takes effect at delay 0, can roll back a model already in public
use, and can be reversed within the same quarter. The sources disagree on the trigger: one says a
jailbreak report attributed to Amazon, another (single-sourced) says China-access concerns. Neither
is verified.

**The claimed second pause (NewsBytes, dated 5 Oct 2026): not verified.**
- Both NewsBytes URLs returned 403/Access Denied, so I could not read the article or its date:
  - https://www.newsbytesapp.com/news/science/anthropic-pauses-fable-5-and-mythos-5-after-us-order/tldr
  - https://www.newsbytesapp.com/news/science/anthropic-pauses-claude-fable-5-mythos-5-citing-national-security/tldr
- Their slugs match the June story.
- Searches for a September–October 2026 suspension found nothing, and later articles describe the suspension in the past tense as lasting about three weeks.
- One search result noted that Anthropic's 12 Jun statement page carries a modified timestamp of 14 Oct 2026.
- **Most likely explanation:** an October date on a re-indexed or updated copy of the June story, not a second event. Do not carry it as a second pause unless a primary source turns up.

## Facts I could not verify

- The exact date of Anthropic's own Fable 5 launch post. The date 9 Jun rests on secondary coverage and the Vercel changelog.
- The text of the Lutnick letter (not public), and the trigger for the directive.
- NewsBytes, 5 Oct 2026: unreadable, and no corroborating second pause found.
- IEA quotes: search snippets only, because the IEA page returned 403.
- OpenAI's Codex GA wording: the primary page returned 403.
- McKinsey figures: secondary coverage only.
- The Intel closing date (27 Aug 2025).
- These dates are from memory and were not fetched:
  - EU AI Act Parliament and Council dates.
  - Digital Omnibus proposal date.
  - Taskforce and AISI launch dates.
  - Bletchley announcement (7 Jun 2023).
  - EO 14148 and the diffusion-rule rescission.
  - The 2025 Anthropic release dates.
  - The DeepSeek-R1 dates.
- Colossus 122 days is Musk's own claim and has no independent verification.
