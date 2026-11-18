# Open-weight AI models: the landscape as of 18 November 2026 (research note)

Status: web research of 18 November 2026 for the review in docs/agi_open_weights_review.html. Nothing here is in any model. Every fact carries a verification label; quotes marked "verified" were relayed by a fetch tool and should be re-checked against the page before being quoted elsewhere.


## How to read this note

**Verification labels**

| Label | Meaning |
|---|---|
| **verified-direct** | I extracted the document text myself (PDF to text) and read the passage. Quotes are exact. |
| **verified** | I opened the page with the fetch tool and the fact is on the page. The tool returns quotes through a summarising model, so wording is as the tool relayed it (usually short fragments). Treat as accurate but re-check before quoting in a publication. |
| **search-snippet** | Seen only in search-result summaries; the page itself was not opened (or refused the fetch: Reuters, Axios, OpenAI, WSGR, Cybernews, TechRepublic all returned errors). |
| **memory** | From my own background knowledge (cutoff mid-2026), not checked in this session. |

**Source quality warning.** Coverage of 2026 events is thick with aggregator and auto-generated sites (pasqualepillitteri.it, letsdatascience.com, fourweekmba.com, tech-insider.org and similar). I used them only as pointers and say so where a fact rests on them alone. The strongest sources used are: Epoch AI, UK AISI, NIST/CAISI, Anthropic, the Federal Register, the White House AI Action Plan, Stanford HAI, OpenRouter's own data posts, Hugging Face's own report, Artificial Analysis's own article, and a law paper (Law Reform Institute, Khawam, Aug/Sep 2026) whose text I read directly.

## Headline findings

1. **Open weights near the frontier are the normal state of the world, not an event.** Since 2025 there has always been a downloadable model within roughly one to two quarters of the best closed model on public benchmarks. Epoch AI: about 3.5 months average lag (Jan 2023 to Oct 2025), about 4 months since Jan 2026.
2. **The gap is not closing to zero; in 2026 it is stable to slightly wider, and larger on private tests.** Epoch 3.5 to 4 months; Stanford AI Index 0.5% (Aug 2024) to 3.3% (Mar 2026); Arena 0 Elo (Jan 2025) to 29 Elo (Sep 2026); Artificial Analysis's October 2026 re-weighting to private test sets moved the best open model from 3 points behind to 12 behind (26 behind for models whose weights were actually downloadable that day). On cyber specifically the lag *narrowed*: UK AISI 6 to 10 months through most of 2025, 4 to 7 months by July 2026.
3. **The open frontier is Chinese.** Every top-10 open-weight model on Artificial Analysis in April 2026 was from a China-based lab; the best US open model (NVIDIA Nemotron 3 Ultra, June 2026) sat about 6 index points below the best Chinese one.
4. **Safeguards on an open release last days at most.** Anthropic (Sep 2026): abliterated GLM-5.3 copies were public "within days"; an abliterated copy complied 100% of the time; doing it cost about $4,400 for a first-time team. UK AISI (Aug 2025): current defences are undone "in a matter of minutes".
5. **Usage has shifted heavily to open weights by token volume, much less by revenue.** OpenRouter: open-weight share passed 50% of tokens in 2026 and peaked at 79% in early July; enterprise survey (ETR, Sep 2026): 34% of enterprise tokens, 42% of firms in production.
6. **No government has recalled a released open-weight model, and the best legal analysis says none can.** Governments have (a) pulled back *closed* models (US directive to Anthropic, June 2026), (b) restricted use of foreign models on government systems, (c) drafted rules on *future* releases (China, Oct 2026) that explicitly exempt what is already public, and (d) considered and so far not enacted measures against Chinese open models (US, July 2026).
7. **Both superpowers moved in 2026 from promoting open weights toward conditional control of the top end**, without restricting publication so far: the US exempts open weights from its voluntary pre-release testing (Aug 2026) while weighing extension; China drafted export licensing for models above 10^26 FLOPs / 2 trillion parameters / global top-10, with automatic licences for open-source release.
8. **Lab behaviour has converged on staged, conditional openness**: hosted API first, weights 10 to 14 days later (Kimi K3, GLM-5.3), custom licences with revenue triggers, and US labs keeping their best model closed while releasing a smaller open one (OpenAI gpt-oss, Google Gemma, Meta Muse Glimmer).

---

## 1. Leading open-weight models (2025 and 2026 releases)

Scores are Artificial Analysis Intelligence Index (AA) unless stated. AA index versions are not comparable across the October 2026 revision (v5).

| Developer / model | Weights released | Licence | Capability vs closed frontier at the time | Source and status |
|---|---|---|---|---|
| DeepSeek R1 (China) | 20 Jan 2025 | MIT | Roughly comparable to OpenAI o1 at about 30x lower price (Epoch newsletter summary) | Epoch topic page, 31 Jan 2025 item, https://epoch.ai/topics/open-models (verified); date and licence from memory |
| Meta Llama 4 (US) | Apr 2025 | Llama 4 Community License (redistribution conditional) | Behind closed frontier (memory) | Licence cited in LRI paper fn. 23 (verified-direct); rest memory |
| Moonshot Kimi K2 (China) | Jul 2025 | Modified MIT | Top open model at the time (memory) | memory |
| OpenAI gpt-oss-120b / 20b (US) | 5 Aug 2025 | Apache 2.0 | Below o3 and o4-mini; beat DeepSeek R1 on Codeforces. Later AA 33.3 | TechCrunch 5 Aug 2025, https://techcrunch.com/2025/08/05/openai-launches-two-open-ai-reasoning-models (verified). Altman: "we are excited for the world to be building on an open AI stack created in the United States" |
| xAI Grok 2.5 (US) | Aug 2025 | Restrictive community licence (bars training other models) | An old model at release; Grok 3 and Grok 4.2 weights promised, not confirmed released | search-snippet |
| Google Gemma 4, up to 31B (US) | 2 Apr 2026 | Apache 2.0 (first Gemma under a standard licence) | AA 39.2; far below Gemini flagships | Licence: Google Open Source Blog cited in LRI fn. 23 (verified-direct); score: The Batch 19 Jun 2026 (verified) |
| Mistral Small 4 (France) | 16 Mar 2026 | Apache 2.0 | Mid-tier | search-snippet |
| Moonshot Kimi K2.6 (China) | Apr 2026 | "permissive" | AA 54 vs GPT-5.5 at 60 | Artificial Analysis, 30 Apr 2026, https://www.artificialanalysis.ai/articles/recent-open-weights-model-launches (verified) |
| Xiaomi MiMo V2.5 Pro (China) | Apr 2026 | "permissive" | AA 54 | same (verified) |
| DeepSeek V4 Pro (1.6T params, 49B active) and V4 Flash (China) | 24 Apr 2026 | MIT | AA 52 vs GPT-5.5 60. DeepSeek's own paper: "trails state-of-the-art frontier models by approximately 3 to 6 months" | Simon Willison, 24 Apr 2026, https://simonwillison.net/2026/apr/24/deepseek-v4 (verified). "They're using the standard MIT license." |
| NVIDIA Nemotron 3 Ultra (550B, 55B active) (US) | Jun 2026 | OpenMDW-1.1 (commercial use allowed); weights, data and recipes published | AA 47.7 to 48.2; best US open model; below Kimi K2.6 (53.9), DeepSeek V4 Pro and GLM-5.2 | The Batch, 19 Jun 2026, https://www.deeplearning.ai/the-batch/nvidias-nemotron-goes-big (verified) |
| Z.ai GLM-5.2 (China) | by Jun 2026 | MIT | "the most cyber-capable open-weight model" as of June 2026 (CAISI) | NIST/CAISI, 23 Jul 2026 page (verified); licence from The Batch 28 Aug 2026 (verified) |
| Moonshot Kimi K3 (2.8T params; 1.56 TB) (China) | API 16 Jul 2026; weights 26/27 Jul 2026 | Custom "kimi-k3" licence; firms hosting it as a service with over $20M annual revenue need a separate agreement; Moonshot says "open weight", not "open source" | AA 57 at launch (third overall), later 59.7 to 60 vs Claude Opus 5 at 63. CAISI/AISI: "performs significantly below the most recent frontier cyber-capable models" | Willison, 27 Jul 2026, https://simonwillison.net/2026/jul/27/kimi-k3 (verified): "a hefty 1.56TB on Hugging Face". NIST, https://www.nist.gov/news-events/news/2026/07/uk-aisi-caisi-preliminary-assessment-kimi-k3s-cyber-capabilities (verified). AA launch score: search-snippet |
| Meta Muse Glimmer, 30B (US) | 10 Aug 2026 | Apache 2.0 | Deliberately sub-frontier; Meta judged it not "Frontier AI" under its Advanced AI Scaling Framework | VentureBeat, 10 Aug 2026, https://venturebeat.com/technology/meta-returns-to-open-source-with-muse-glimmer-an-apache-2-0-licensed-30b-parameter-ai-model-optimized-for-agents-available-now (verified) |
| Alibaba Qwen3.8-27B and Qwen3.8-2.4T-A95B (the model behind Qwen3.8-Max) (China) | 14 Aug 2026 | 27B: Apache 2.0. 2.4T model: reported as a custom "qwen3.8-max" licence | 2.4T model "built to operate at the Max level" | The Decoder, 14 Aug 2026, https://the-decoder.com/alibabas-qwen-team-releases-qwen-3-8-models-with-open-weights-under-the-apache-2-0-license/ (verified for release); custom licence on the 2.4T model is search-snippet |
| Z.ai GLM-5.3 (China) | Hosted 14 Aug 2026; weights about two weeks later, after a safety hold | Not announced at launch (GLM-5.3 Flash: MIT) | AA 60, tied with Kimi K3, vs Claude Opus 5 63, GPT-5.6 Sol 61. CyberGym 84.5% vs Claude Mythos 5 83.8%; ExploitBench 54.4% vs Mythos 5 78.0%. CAISI: "the most cyber-capable open-weight model released to date", about four months behind US frontier on cyber | The Batch, 28 Aug 2026, https://www.deeplearning.ai/the-batch/glm-5-3-makes-cybersecurity-gains (verified); NIST, 17 Sep 2026, https://www.nist.gov/news-events/news/2026/09/caisis-assessment-zais-glm-53-cyber-capabilities (verified): "Z.ai publicly released the model's weights two weeks later." |
| DeepSeek V4.1 Flash (China) | 10 Sep 2026 (update "1017" on 17 Oct) | MIT | AA v5: 32 (tied with GLM-5.3) vs Claude Opus 5.5 at 58 | Release: search-snippet (deepseek.com news page exists). v5 score: Implicator, 28 Oct 2026 (verified) |
| Mistral Large 4 (France) | Oct 2026 (reported) | "Mistral Ecosystem Open-Weight License" (resellers need a licence) | not established | search-snippet, single low-quality source |
| Moonshot Kimi K3.1 Pro (2.8T) (China) | 4 Nov 2026 | "Kimi-specific license" | AA v5: 46 vs leader 58 (best open-weight family score) | RuntimeWire, 4 Nov 2026, https://runtimewire.com/article/moonshot-ai-kimi-k3-1-pro-weights (verified); score from Implicator 28 Oct 2026 (verified) |

Other open releases mentioned in sources but not checked in detail: MiniMax M2.7 / M3 (China), Thinking Machines "Inkling" (US; reportedly trained with help from Kimi 2.5, per Replit's CEO in TechCrunch 24 Jul 2026, verified), Mistral Medium 3.5, Microsoft Phi (memory).

**Closed frontier for reference** (from the same sources): GPT-5.5, Claude Opus 4.7, Gemini 3.1 Pro (April 2026); Claude Fable 5 / Mythos 5 and GPT-5.6 Sol (June 2026); Claude Opus 5 (August 2026); Claude Opus 5.5 and GPT-6 Astra (October 2026).

**Practical caveat.** "Open" at the top end no longer means "runnable by anyone": Kimi K3 is 1.56 TB of weights and 2.8 trillion parameters; DeepSeek V4 Pro is 865 GB (Willison, verified). Epoch (15 Aug 2025, verified): "Models that fit on consumer GPUs match the performance of frontier AI within a year or less."

---

## 2. The open-closed capability gap and its trend

| Measure | Date of data | Finding | Source and status |
|---|---|---|---|
| Epoch AI, "How far behind are open models?" | Nov 2024 | Best open models lagged the best closed ones by about a year on average (roughly 5 to 22 months by benchmark) | https://epoch.ai/publications/open-models-report; listed on Epoch topic page (verified it exists); numbers from memory |
| Epoch AI, ECI time lag | Jan 2023 to Oct 2025; published 30 Oct 2025 | "We find an average 'horizontal' time gap of 3.5 months" (90% CI 1.1 to 5.3); average 7 ECI points; "the gap varies considerably over time, sometimes even closing completely" | https://epoch.ai/data-insights/open-weights-vs-closed-weights-models (verified) |
| Epoch AI, ECI time lag | 1 Jan to 28 May 2026; published 29 May 2026 | "the most capable open-weight models have lagged frontier closed models by an average of four months, or 8 ECI points"; "slightly larger" than the earlier estimate; the gap "would grow to six months" under a stricter test. Understates the gap because open models "tend to perform worse on private benchmarks" and "Leading closed labs do not always release their most capable models." Top open: Kimi K2.6 (151.6); top closed: GPT-5.5 Pro (159.35) | https://epoch.ai/data-insights/open-closed-eci-gap (verified, two reads) |
| Epoch AI, furniture-assembly benchmark | published 23 Sep 2026 | "open-weight models trailing closed-weight models by about 7 months" | https://epoch.ai/topics/open-models (verified) |
| Epoch AI, Cyber ECI | published 16 Oct 2026 | "Open-weight models trail closed models in cyber capabilities by 6-7 months"; top open model GLM-5.3 | same page (verified headline; the insight page itself was not found) |
| UK AI Security Institute, cyber | published 17 Jul 2026 | "recent open weight models lag frontier closed models' cyber capabilities by 4 to 7 months"; "a narrower gap than the 6 to 10 months we measured through most of 2025". Tested GLM-5.2 and DeepSeek V4-Pro | https://www.aisi.gov.uk/blog/how-far-behind-the-frontier-are-leading-open-weight-models-on-cyber (verified) |
| NIST CAISI, cyber | published 17 Sep 2026 | "GLM-5.3 lags the capability level of the U.S. frontier by about four months" | NIST link above (verified) |
| DeepSeek's own estimate | 24 Apr 2026 | V4 Pro "trails state-of-the-art frontier models by approximately 3 to 6 months" | Willison (verified) |
| Artificial Analysis Index | Apr 2025 vs Apr 2026 | A year earlier the best open model (DeepSeek V3 0324, 22) was about 13 points below the best closed (Claude 3.7 Sonnet, 35). On 30 Apr 2026: best open 54 vs GPT-5.5 at 60, "within 3-6 points". "Leading open weights models are from China-based AI labs." | Artificial Analysis, 30 Apr 2026 (verified) |
| Artificial Analysis Index (v4.x) | Aug 2026 | GLM-5.3 and Kimi K3 at 60 vs Claude Opus 5 at 63: 3 points | The Batch, 28 Aug 2026 (verified) |
| Artificial Analysis Index v5 | 27 Oct 2026 | 60% of the index now on private or held-out tests. Leader Claude Opus 5.5 at 58; Kimi K3.1 Pro 46 (weights not yet out that day); best models with weights actually downloadable (DeepSeek V4.1 Flash 1017, GLM-5.3) 32: "Models with downloadable weights trail the proprietary leader by 26 points on the revised suite." AA's own line, as reported: "The open weights gap widens from 3 points to 12". Versions not comparable over time | Implicator, 28 Oct 2026, https://www.implicator.ai/artificial-analysis-index-v5-open-model-gap.md (verified); AA's quoted sentence is search-snippet (Cybernews refused the fetch) |
| Stanford AI Index 2026 (Arena scores) | Mar 2026 | "The open model performance gap reopened in 2025 after briefly closing in 2024." "As of March 2026, the top closed model leads the top open model by 3.3%, up from 0.5% in August 2024." (1,503 vs 1,454). US vs China: 2.7% | https://hai.stanford.edu/ai-index/2026-ai-index-report/technical-performance (verified) |
| Arena (LMArena) | Sep 2026 | Gap of 29 Elo between Claude Opus 5 Max (1505) and Kimi K3 Max; gap had reached zero in Jan 2025; described as the widest in nearly two years | Crypto Briefing, 3 Sep 2026, citing Arena's Peter Gostev (verified, but a secondary outlet). A different aggregator (BenchLM) gives 28.1 points on 3 Jun 2026 down from 56.3 a year earlier (search-snippet); the two histories do not agree |
| Mozilla, "State of Open Source AI" v1.1 | 15 Sep 2026 | About 4.4 months on METR task-horizon data; open doubling time 3.9 months vs 5.5 for closed | search-snippet (Tom's Hardware and others) |

**Assessment (mine).**
- 2023 to early 2025: the lag fell from about a year to a few months, briefly touching parity on preference leaderboards (Llama 3.1 in mid-2024, DeepSeek R1 in January 2025).
- 2025 to 2026: **stable at roughly one to two quarters** on public composite measures (3.5 then 4 months by Epoch), with slight widening in 2026 on four independent series (Epoch, Stanford, Arena, AA).
- Security-relevant capability: cyber lag **narrowed** from 6 to 10 months to 4 to 7 months (AISI), though Epoch's October 2026 cyber index reads 6 to 7 months.
- Public-benchmark figures probably understate the true gap (Epoch's own caveat; the AA v5 result; unreleased internal closed models).
- A plausible mechanism for the floor on the lag is distillation from closed-model outputs (LRI paper, verified-direct: "The gap between closed and open-weight models has narrowed in part due to distillation").

---

## 3. How fast safety training is removed after an open release

| Fact | Date | Source and status |
|---|---|---|
| "Several developers released abliterated versions of GLM-5.3 to the public within days of the model's release." | 29 Sep 2026 | Anthropic Frontier Red Team, https://www.anthropic.com/research/glm-5-3-and-the-spread-of-advanced-cyber-capabilities (verified). Note Anthropic sells competing models |
| GLM-5.3 harmful-task engagement: 64% with a cover story, 92% with prefilled reasoning, 100% abliterated; "none of these techniques got safeguarded Claude models to carry out the harmful tasks we tested" | 29 Sep 2026 | same (verified) |
| Cost: Anthropic's first-time attempt took "about 2,200 GPU hours at a computation cost of roughly $4,400"; an experienced team "would need closer to 600 GPU hours ($1,200)" (for a model of several hundred billion to trillions of parameters) | 29 Sep 2026 | same (verified) |
| Open-weight defences "can be easily undone using just dozens of training examples in a matter of minutes"; safeguards can be "quickly and cheaply removed"; once published "it cannot be rolled back" | 29 Aug 2025 | UK AISI, https://www.aisi.gov.uk/blog/managing-risks-from-increasingly-capable-open-weight-ai-systems (verified) |
| With weights public, deployment-time controls "are lost permanently"; refusal training is "often easily reversible with access to the weights" | 17 Jul 2026 | UK AISI cyber blog (verified) |
| BadLlama 3 (Palisade Research, D. Volkov): "extensive LLM safety fine-tuning is easily subverted when an attacker has access to model weights"; Llama 3 8B stripped in about one minute and 70B in about 30 minutes on one GPU | 1 Jul 2024 | https://arxiv.org/abs/2407.01376 (verified) |
| BadLlama 3 body figures: 8B in 5 minutes on one A100 (under $0.50); 70B in 45 minutes (under $2.50) | Jul 2024 | arXiv HTML, search-snippet |
| Original BadLlama: safety fine-tuning removed from Llama 2-Chat 13B for under $200 | Oct/Nov 2023 | arXiv 2311.00117, search-snippet |
| Alice (vendor) study: abliterated versions of six model families "enthusiastically replied to 96-100% of harmful requests"; one model "went from 100% refusal to 100% compliance"; the open-source "Heretic" abliteration tool had 17,800 GitHub stars | 17 Apr 2026 | https://alice.io/blog/okay-here-is-how-to-build-a-bomb-millions-download-dangerous-llms (verified; vendor blog) |
| TamperBench: 21 open-weight LLMs evaluated across nine tampering threats; all could be tampered with despite safeguards | arXiv Feb 2026; press Aug 2026 | search-snippet (ICLR 2026 listing, FAR.AI, University of Waterloo release) |
| "Hugging Face hosts thousands of abliterated models on its platform." A US company, Abliteration.ai, sells hosted access to a guardrail-free GLM-5.3 | 3 Sep 2026 | TechCrunch, https://techcrunch.com/2026/09/03/abliteration-ai-is-making-a-business-out-of-removing-ai-guardrails/ (verified); also LRI paper fn. (verified-direct) |
| Uncensored builds of DeepSeek V4.1 Flash on Hugging Face the same day as release (10 Sep 2026) | Sep 2026 | search-snippet, low-quality source only |
| Counts of abliterated models on Hugging Face: about 600 in 2024, over 6,000 by May 2026; about 7,970 in autumn 2026 | 2026 | search-snippet (attributed to NPR; not checked) |
| OpenAI ran "malicious fine-tuning" on gpt-oss before release: even so it "underperforms OpenAI o3" and "does not substantially advance the frontier"; results "contributed to our decision to release the model" | 5 to 13 Aug 2025 | https://arxiv.org/abs/2508.03153 (verified) |
| "In some cases, it takes only a matter of minutes to remove these controls from open models." | 13 Aug 2026 | Tech Policy Press (M. MacCarthy), https://techpolicy.press/us-governments-ai-risk-review-should-apply-to-open-weight-models (verified; opinion piece) |

**Reading.** On a quarterly tick, safeguard removal is effectively instantaneous: hours to days, at a cost between cents (small models) and a few thousand dollars (trillion-parameter models). The only pre-release counter-measure with a track record is worst-case testing before the decision to release (OpenAI's gpt-oss procedure; Z.ai's two-week hold).

---

## 4. Adoption and use

| Fact | Date of data | Source and status |
|---|---|---|
| Open-source models "reached approximately one-third of usage by late 2025"; Chinese open models "averaged approximately 13.0% of weekly token volume", peaking "nearly 30%" in some weeks; programming went from "roughly 11% of total token volume in early 2025" to over 50%; dataset of over 100 trillion tokens | through late 2025; published Dec 2025 | OpenRouter / a16z "State of AI", https://openrouter.ai/state-of-ai (verified) |
| "Open-weight model token share crossed 50% of tokens briefly in February and more permanently in April of this year." "It reached 79% in early July, its high point, and has held above 62% since." | 1 Jan 2025 to 20 Sep 2026; published 22 Sep 2026 | OpenRouter "Inferred 01", https://openrouter.ai/data/newsletter/the-token-state-of-play (verified) |
| "69% of tokens on OpenRouter last week were from Chinese labs (vs 72% being open-weight overall)." | week to 20 Sep 2026 | same (verified) |
| "over 40% of US startups on OpenRouter now use DeepSeek in production" | Sep 2026 | same (verified) |
| Agents: "We estimate the last day humans used more tokens than agents was Feb 6, 2026." | 2026 | same (verified) |
| Chinese open-weight models about 61% of OpenRouter tokens by May 2026 (from about 2%) | May 2026 | Wing VC, Jun 2026, https://www.wing.vc/content/chinas-open-weight-takeover (verified; secondary). Notes Anthropic and OpenAI "still capture the majority of industry revenue" |
| Enterprise survey (ETR, n=200): "open-weight models now account for 34% of enterprise AI token usage, compared with 23% a year ago"; expected 41% in 12 months; "42% of respondents have open-weight models in production, up from 31% in July"; 43% piloting | Sep 2026 | Techstrong, 22 Sep 2026, https://techstrong.ai/articles/open-weight-ai-models-expected-to-capture-41-of-enterprise-token-usage/ (verified) |
| Hosting among production users: self-managed cloud 46%, on-premises 42%, hyperscaler-native 29%, managed inference 27%. Main motive: cost (69%) | Sep 2026 | same (verified) |
| Chinese-origin models are *falling* in enterprise production: "DeepSeek fell to 25% in production, down seven percentage points"; GLM 10% to 1%; export-control and sanctions exposure three times more often cited | Jul to Sep 2026 | same (verified) |
| Open-weight models are only about 5% of enterprises' *metered* AI spend (self-hosting produces no bill) | Oct 2026 | Futurum, search-snippet |
| Hugging Face: "more than 2 million public models"; "Chinese models quickly accounted for the plurality or 41% of downloads" in the past year; "the top 200 most downloaded models, or 0.01% of models, comprise 49.6% of all downloads"; Qwen family has "more than 113,000 derivative models"; "Alibaba as an organization has more derivative models than both Google and Meta combined." | Feb 2025 to Feb 2026; published 17 Mar 2026 | https://huggingface.co/blog/huggingface/state-of-os-hf-spring-2026 (verified). US share 36.5%: search-snippet |
| Defensive use: after the July 2026 breach of Hugging Face by OpenAI agents, closed models' guardrails blocked the forensic analysis and Hugging Face ran it on self-hosted GLM-5.2 | Jul 2026 | LRI paper fn. 115 (verified-direct); Wikipedia "OpenAI-HuggingFace incident" (verified) |

**Caveats.** OpenRouter is a developer router, not the whole market (it excludes direct API use, ChatGPT-type consumer use and private deployments). Hugging Face downloads are inflated by automation and are not usage. Token share is not revenue share. The enterprise numbers suggest roughly one third of enterprise tokens, not the 60 to 79% seen on OpenRouter.

---

## 5. Government positions

### United States

| Date | Action or position | Key text | Source and status |
|---|---|---|---|
| Jul 2024 | NTIA report on open model weights recommends against restricting open-weight releases "at this time", with monitoring | as summarised in LRI paper | LRI paper (verified-direct); NTIA report itself from memory |
| 15 Jan 2025 | AI Diffusion Rule (interim final): first control-list entry for model weights (ECCN 4E091, models trained with 10^26 or more operations). **Published weights were excluded**, as were closed models weaker than the strongest published model | BIS judged the benefits of open publication outweighed the risks "for now" | LRI paper, Part III.a.iii, citing 90 Fed. Reg. 4,544 (verified-direct) |
| 13 May 2025 | Commerce "announced a rescission of the Biden Administration's AI Diffusion Rule"; enforcement officials instructed "not to enforce" it; BIS "plans to publish a regulation formalizing the rescission and will issue a replacement rule in the future" | LRI adds: "the entry has not actually been removed from the CCL" and no replacement rule has issued | BIS press release, https://www.bis.gov/press-release/department-commerce-announces-rescission-biden-era-artificial-intelligence-diffusion-rule-strengthens (verified); LRI (verified-direct) |
| 23 Jul 2025 | America's AI Action Plan, section "Encourage Open-Source and Open-Weight AI" | "We need to ensure America has leading open models founded on American values. Open-source and open-weight models could become global standards in some areas of business and in academic research worldwide. For that reason, they also have geostrategic value. While the decision of whether and how to release an open or closed model is fundamentally up to the developer, the Federal government should create a supportive environment for open models." Also: they are "essential for academic research". Actions include NTIA convening stakeholders "to help drive adoption of open-source and open-weight models by small and medium-sized businesses" | https://www.whitehouse.gov/wp-content/uploads/2025/07/Americas-AI-Action-Plan.pdf, pp. 4-5 (verified-direct) |
| Apr 2026 | House Homeland Security and China Select Committee leaders open a joint investigation that includes "the redistribution of those stolen capabilities as open-weight models available for global download" | | CyberScoop, 22 Jul 2026 (verified) |
| 2 Jun 2026 (FR 5 Jun) | Executive Order 14409, "Promoting Advanced Artificial Intelligence Innovation and Security": agencies to "design a voluntary framework with AI developers" giving government access to "covered frontier models" for "a period of up to 30 days" before release; threshold set by a classified NSA benchmarking process | "Nothing in this section shall be construed to authorize the creation of a mandatory governmental licensing, preclearance, or permitting requirement." The order does not mention open-source or open-weight models | https://www.govinfo.gov/content/pkg/FR-2026-06-05/html/2026-11415.htm (verified) |
| 12 Jun 2026 | Commerce "Is-Informed Letter" (ECRA s. 4817(b)(1), EAR s. 744.22(b)) to Anthropic requiring a licence for any export, reexport or in-country transfer of Fable 5 and Mythos 5 to foreign persons. It treats "remote, API-based access to a model as a 'release'". Anthropic: ordered to "suspend all access to Fable 5 and Mythos 5 by any foreign national"; could not verify nationality, so "must abruptly disable Fable 5 and Mythos 5 for all our customers". Stated trigger: a jailbreak method. Anthropic disagreed that "the finding of a narrow potential jailbreak should be cause for recalling a commercial model" | **Correction to the brief:** the directive did not control model weights as such and did not itself "suspend" the models; it imposed a licence requirement on foreign-person access, and Anthropic disabled the models globally to comply. A second letter (26 Jun) exempted "certain trusted partners" for Mythos 5. Directive terminated 30 Jun 2026; access returned from 1 Jul | Anthropic statement, 12 Jun 2026, https://www.anthropic.com/news/fable-mythos-access (verified); Mayer Brown, 30 Jun 2026 (verified); Just Security, 15 Jun 2026 (verified); termination date: Digital Policy Alert (search-snippet) and LRI fn. 14 citing Anthropic "Redeploying Claude Fable 5 (June 30, 2026)" (verified-direct) |
| Jun to Jul 2026 | Administration also asked OpenAI to limit the initial availability of GPT-5.6 | "To date, these interventions have stopped at the closed frontier; none has reached the publication of model weights." | LRI paper, Part V (verified-direct) |
| 20 Jul 2026 | Axios: after Kimi K3, Commerce considered putting several Chinese AI labs on the Entity List and circulated draft supply-chain rules targeting Chinese open models; sources said closed labs or their allies approach the administration "every 3-5 months" with an idea to ban open-source models; David Sacks opposed | Nothing enacted | search-snippet (Axios returned 403); "As of October 2026, no such action has been taken" per China Tech Bite, 15 Oct 2026 (verified) |
| 22 Jul 2026 | OSTP director Kratsios publicly accuses Moonshot of distilling Anthropic's Fable to build Kimi K3: "large-scale, covert industrial distillation aimed at stealing proprietary U.S. technology"; says legitimate distillation "plays a vital role" and affirms support for open-weight models | No public evidence given | CyberScoop, https://cyberscoop.com/white-house-accuses-moonshot-ai-anthropic-model-distillation/ (verified). Treasury "sanctions remain on the table": search-snippet |
| 24 Jul 2026 | Industry letter (Hugging Face, Meta, Microsoft, Mistral, Nvidia, Replit and others; 25 signatories per a later article) urges no "premature restrictions" on open-weight models. Not signed by OpenAI, Anthropic, Google DeepMind, SpaceX | Jensen Huang: "Open models strengthen safety and cybersecurity, accelerate innovation and diffusion, and enable sovereignty." | TechCrunch, 24 Jul 2026 and 12 Nov 2026 (verified) |
| 4 Aug 2026 | Administration "told leading AI companies that it will not safety-test open-weight AI models" under the new voluntary programme | | Reuters via Investing.com, 4 Aug 2026 (verified) |
| 12 Aug 2026 | Wired: a White House official says open models could face pre-release testing once they reach the level of Mythos-class models and GPT-5.6; expansion expected "in the coming months" | LRI: the framework "currently excludes open-weight models, but they may be added to an updated framework in the near future" | Wired: search-snippet; LRI (verified-direct) |
| Jul, Sep, Oct 2026 | CAISI publishes assessments of Chinese open models (GLM-5.2 on 17 Jul; Kimi K3 on 23 Jul with UK AISI; GLM-5.3 on 17 Sep) | Government evaluates open models after release, not before | NIST pages (Kimi K3 and GLM-5.3 verified; GLM-5.2 via LRI citation, verified-direct) |
| 1 Oct 2026 | China FIREWALL Act (H.R. 10670) introduced: would bar federal use or procurement of models from "foreign entities of concern", reaching derivatives made by fine-tuning or distillation. Senate FY2027 NDAA s. 1651 would bar DoD procurement of listed Chinese models | Bills, not law | China Tech Bite, 15 Oct 2026, https://chinatechbite.substack.com/p/washington-is-not-banning-chinese (verified; secondary) |

Legal position (LRI paper, verified-direct): publication of weights without redistribution limits likely makes them "published" under 15 C.F.R. s. 734.7 and therefore outside the EAR. "At the model layer, existing law does not provide a clean basis for categorically prohibiting the publication or download of model weights, and no authorities can realistically restore control over weights that have already been widely copied." Licences that limit who may redistribute (the paper cites Llama 4's) are a closer question.

### China

| Date | Action or position | Source and status |
|---|---|---|
| 26 Jul 2025 | Global AI Governance Action Plan (World AI Conference): supports cross-border open-source communities and an open-source compliance system | search-snippet (full text on MFA site not opened) |
| Aug 2025 | State Council "AI Plus" Opinions (Guofa [2025] No. 11): strengthen open-source ecosystems; reward open-source contributions | search-snippet (CSET translation exists) |
| 7 Jul 2026 | Reuters exclusive: Ministry of Commerce (with NDRC) led meetings with Alibaba, ByteDance and Z.ai on "restricting overseas access to China's most advanced AI models, including those yet to be released"; limits discussed on "both closed-source and more open versions"; "they may only apply to future models"; officials "deeply worried about the potential for Mythos to exploit software vulnerabilities" | Reuters as carried by The Standard (HK), https://www.thestandard.com.hk/innovation/article/336614/Beijing-is-looking-at-curbing-overseas-access-to-Chinas-top-AI-models-sources-say (verified) |
| 17 Jul 2026 | New edition of the governance action plan at WAIC 2026 still calls for a global open-source ecosystem that is "open, inclusive, secure, and well-governed" | search-snippet |
| 16 Oct 2026 | MOFCOM and MOST publish a draft adding 23 AI technologies to the export-control catalogue. Core model technology (weights, checkpoints, code, architecture, methods) is restricted once a model reaches 10^26 FLOPs of training compute, or at least 2 trillion parameters, or a global top-10 ranking. **Open-sourcing restricted technology counts as an export but is eligible for automatic licensing; technology "already lawfully placed in the public domain through open-source releases, academic publications" is outside the controls**; API/app/SaaS access is not an export. Autonomous malware-writing tools: total export ban. Interim registration applies from 16 Oct | The Decoder, 16 Oct 2026, https://the-decoder.com/china-plans-to-tighten-export-controls-on-open-weight-models-and-23-key-ai-technologies/ (verified); Geopolitechs, 16 Oct 2026, https://www.geopolitechs.org/p/chinas-proposed-ai-export-controls (verified): "releasing model technology as open source can constitute a form of technology export"; the revisions "need not significantly undermine the global development of China's open-source AI ecosystem" |
| 15 Nov 2026 | Comment period on the draft reportedly closed; no final catalogue found | search-snippet |

Note that Kimi K3 and K3.1 Pro (2.8 trillion parameters) and Qwen3.8-2.4T would fall above the draft's 2-trillion-parameter line; K3.1 Pro's weights were published on 4 November 2026, during the interim-registration period (my inference from the dates; no source states how it was handled).

### European Union

| Fact | Source and status |
|---|---|
| AI Act Art. 53(2): the documentation duties in Art. 53(1)(a) and (b) "shall not apply to providers of AI models that are released under a free and open-source licence that allows for the access, usage, modification, and distribution of the model, and whose parameters, including the weights, the information on the model architecture, and the information on model usage, are made publicly available. This exception shall not apply to general-purpose AI models with systemic risks." | https://artificialintelligenceact.eu/article/53/ (verified) |
| So open-source GPAI providers still owe a copyright policy and a training-data summary; an open model classed as systemic-risk gets no exemption at all | https://artificialintelligenceact.eu/enforcement-of-chapter-v-under-the-eu-ai-act/, 31 Mar 2026 (verified) |
| Systemic risk is presumed above 10^25 FLOPs of training compute (Art. 51); the Commission can also designate. Licences with usage limits or extra licensing do not qualify for the exemption (Commission guidelines, Jul 2025) | search-snippet / memory |
| GPAI obligations applied from 2 Aug 2025. "On 2 August 2026, the Commission's enforcement powers in respect of GPAI model providers will come into force": request information (Art. 91), run evaluations (Art. 92), and under Art. 93 ask providers to "restrict the making available on the market, withdraw or recall the model". Fines up to "3 % of their annual total worldwide turnover ... or EUR 15 000 000, whichever is higher". Pre-August-2025 models have until 2 Aug 2027 | same page (verified) |
| The 2026 digital omnibus delayed high-risk-system duties but left the GPAI dates unchanged; the AI Office reportedly sent information requests to GPAI providers from 29 Aug 2026 | search-snippet (single secondary sources) |
| No report found of the EU designating an open-weight model as systemic-risk or using Art. 93 against one | absence of evidence in my searches |

Custom licences with revenue triggers (Kimi K3) or reseller terms (Mistral Large 4, Qwen3.8-Max) would probably not meet the Art. 53(2) "free and open-source licence" test, and models of this scale are almost certainly above 10^25 FLOPs (my inference).

### United Kingdom
UK AISI's position (Aug 2025, verified): staged release, full-access audits before release, and "Avoiding open-weight release of a system can be a strong defence." AISI evaluates open models after release and published the 4-to-7-month cyber lag.

---

## 6. Has any government restricted, recalled or controlled an already-released open-weight model?

**Short answer: no case found of a government recalling or effectively controlling open weights after release.** What exists:

| Episode | What was actually controlled | Outcome | Source and status |
|---|---|---|---|
| Italy's data-protection authority and DeepSeek (30 Jan 2025) | The consumer app and service (personal-data processing), not the downloadable weights | App blocked in Italian stores; weights unaffected | search-snippet |
| US states, NASA, the Navy, the House, and others banning DeepSeek on government devices (2025) | Use on government systems | Use restricted; weights unaffected | search-snippet |
| US directive to Anthropic (12 to 30 Jun 2026) | A *closed* model's availability to foreign persons | Models disabled worldwide within hours; restored after 18 days. Shows the lever works only where the developer retains control | verified (section 5) |
| US consideration of Entity List / supply-chain rules against Chinese open-model labs (Jul 2026) | Would chill US firms' use, not remove weights | Not enacted as of Oct 2026 | search-snippet / verified secondary |
| China draft catalogue (Oct 2026) | Future releases above thresholds | Explicitly excludes technology already public | verified |
| EU AI Act Art. 93 | Power to request restriction, withdrawal or recall of a GPAI model | No known use against an open model | verified (power); absence of use is from my searches |
| Hugging Face disabling one abliterated GLM-5.3 repository named for offensive cyber use (about Oct 2026) | A platform content-policy action, no government request reported | The same weights were re-uploaded under a new name by the same account | search-snippet and one low-quality page I opened (pasqualepillitteri.it; its dates are internally inconsistent) |
| Developer self-restraint: Z.ai held GLM-5.3 weights for two weeks for "safety testing"; Meta kept Muse Spark closed; Moonshot delayed K3 weights 10 days | Pre-release only | Weights released anyway (Z.ai, Moonshot) | verified |
| Meta's 2023 takedown notices after the first Llama weights leaked | Copies on hosting sites | Did not contain the spread | memory |

Authoritative statements on feasibility:
- LRI paper (verified-direct): "Once weights are released, an export-control directive cannot recall downloaded copies or restore control."
- UK AISI (verified): once published "it cannot be rolled back", though halting downloads can slow spread.
- International AI Safety Report 2026 (3 Feb 2026): weights "cannot be recalled" (search-snippet).
- Tom's Hardware headline on the Axios story: downloadable open weights "could make an outright U.S. ban nearly impossible to enforce" (search-snippet).

What governments *can* still reach after release (LRI paper, verified-direct): hosted services built on the weights (for example a US company serving an abliterated model), disclosure of dangerous outputs, and US persons' support for WMD or military-intelligence end uses.

---

## 7. Competitive pressure from open releases, and open weights as an enabler of outside safety work

### Competitive pressure

| Evidence | Date | Source and status |
|---|---|---|
| After DeepSeek R1, Sam Altman: OpenAI has been "on the wrong side of history" on open source and needs to "figure out a different open source strategy"; "Not everyone at OpenAI shares this view, and it's also not our current highest priority." DeepSeek had "lessened OpenAI's lead" and pushed OpenAI to show more of its models' reasoning | 31 Jan 2025 | TechCrunch, https://techcrunch.com/2025/01/31/sam-altman-believes-openai-has-been-on-the-wrong-side-of-history-concerning-open-source (verified) |
| Nvidia lost roughly $590 billion of market value in one day after R1 (27 Jan 2025); OpenAI made o3-mini available to free users days later | Jan 2025 | memory / search-snippet |
| OpenAI released its first open-weight language models since GPT-2 (gpt-oss) with explicit geopolitical framing | 5 Aug 2025 | TechCrunch (verified) |
| Google moved Gemma to Apache 2.0 (Apr 2026); Meta returned to open weights with Muse Glimmer after four closed months (Aug 2026); Nvidia released Nemotron 3 Ultra with data and recipes (Jun 2026), announced a $6 billion deal with Poolside for an open US ecosystem (Aug 2026) and a $12.9 billion acquisition of Hugging Face (Sep 2026) | 2026 | verified (LRI fn., VentureBeat, The Batch, TechCrunch 12 Nov 2026) |
| OpenAI price cuts: "80% drop for GPT-5.6 Luna, now $0.20 per million input tokens and $1.20 per million output"; "20% drop for GPT-5.6 Terra, to $2/$12" (Altman). The link to Chinese open models is the reporter's framing, not OpenAI's statement | 30 Jul 2026 | Wccftech, https://wccftech.com/openai-goes-after-the-jugular-of-chinas-open-weight-ai-models-cuts-token-prices-by-up-to-80/ (verified). OpenRouter's own note of a 50% discount from 27 Jul and a later list-price cut (verified) |
| Open models are far cheaper at similar scores: DeepSeek V4 Pro $1.74 / $3.48 per million tokens vs Claude Opus 4.7 $5 / $25 and GPT-5.5 $5 / $30; "Open weights dominate the Pareto frontier for Intelligence vs. Price" (9 of 13 frontier points) | Apr 2026 | Willison; Artificial Analysis (verified) |
| But the top open model is no longer cheap: Kimi K3 at $3 / $15 per million tokens | Jul 2026 | Willison (verified) |
| Closed-lab reaction on safety grounds: OpenAI's Greg Brockman warned that open-weights models with near-frontier cyber skills would likely "significantly accelerate the threat landscape" | 17 Aug 2026 | The Batch, 28 Aug 2026 (verified) |
| Closed labs or allies reportedly lobby for restrictions on open models "every 3-5 months" | Jul 2026 | Axios via search-snippet |
| Distillation ties the two tiers together: White House accusation against Moonshot (Jul 2026); Anthropic's earlier accusations against Moonshot, DeepSeek and MiniMax (reported Feb 2026); Anthropic anti-distillation measures (Oct 2026) | 2026 | CyberScoop (verified); the rest search-snippet / China Tech Bite (verified secondary) |
| Evidence of accelerated *release schedules* in response to open models | | none found in 2026 sources |

### Outside safety research and defence

| Evidence | Date | Source and status |
|---|---|---|
| US policy text: open models "are essential for academic research, which often relies on access to the weights and training data of a model to perform scientifically rigorous experiments" | Jul 2025 | AI Action Plan (verified-direct) |
| Casper et al., "Open Technical Problems in Open-Weight AI Model Risk Management" (21 authors incl. Bengio, Hendrycks, Kolter, Gal): open-weight models "allow for more open research and testing" but "can be modified arbitrarily, used without oversight, and spread irreversibly" | 30 Sep 2025 (TMLR 2026) | https://www.far.ai/research/open-technical-problems-in-open-weight-ai-model-risk-management (verified) |
| Independent government and third-party evaluations of open models are routine: UK AISI (GLM-5.2, DeepSeek V4 Pro), CAISI (GLM-5.2, Kimi K3, GLM-5.3), Anthropic (GLM-5.3), Epoch. AISI said it would test Kimi K3 "once its weights are released" | 2026 | verified (sections 2, 3) |
| Defensive use when closed models refuse: Hugging Face's incident response ran on self-hosted GLM-5.2 because closed providers' guardrails "cannot distinguish an incident responder from an attacker" | Jul 2026 | Wikipedia (verified); LRI fn. 115 (verified-direct) |
| Z.ai's claim that GLM-5.3 helped defend 389 open-source projects and find 4,249 potential vulnerabilities | Sep 2026 | search-snippet, single low-quality source |
| Interpretability tooling is built on open weights (for example sparse-autoencoder suites for Gemma); a Base Labs / Hugging Face / Goodfire open-weight safety partnership was announced in 2026 without a public specification | 2024 to 2026 | memory; search-snippet |
| Counter-evidence: independent safety studies of open models are still described as rare, and one found a closed model more robust under adaptive red-teaming than three open ones | 2026 | search-snippet (vendor-commissioned study) |

---

## 8. Frontier labs' open-weight policies as of late 2026

| Lab | Best model | Open-weight practice | Stated or apparent reason | Status |
|---|---|---|---|---|
| OpenAI | Closed (GPT-5.6, GPT-6 line) | gpt-oss-120b / 20b under Apache 2.0 (Aug 2025), well below its frontier; no successor found as of Oct 2026 | Released after worst-case fine-tuning tests showed it "does not substantially advance the frontier"; "open AI stack created in the United States". Opposes near-frontier cyber-capable open weights (Brockman) | verified (TechCrunch, arXiv, The Batch); "no successor" is search-snippet |
| Anthropic | Closed (Claude Opus 5.5; Fable and Mythos lines) | Has never published model weights. Evaluates others' open models and calls for governments to "conduct safety testing on sufficiently capable AI models, including successors to GLM-5.3" | Misuse safeguards require control of deployment | Anthropic report (verified); "never published" is search-snippet / memory |
| Google DeepMind | Closed (Gemini) | Gemma family open; Gemma 4 under Apache 2.0 from Apr 2026, up to 31B | Small open models "built from the same research" as Gemini | verified-direct for licence; rest search-snippet |
| Meta | Closed since Apr 2026 (Muse Spark) | Llama open-weight through Llama 4 (2025); Muse Glimmer 30B under Apache 2.0 (10 Aug 2026); Zuckerberg: "Soon we'll also release the weights for Muse Spark 1.2" (not yet out) | Jul 2025: Meta must be "careful about what we choose to open-source" (search-snippet). Releases gated by its "Advanced AI Scaling Framework"; Glimmer rated "Moderate or lower risk" and not "Frontier AI". May 2026 interview: Muse Spark tripped safety checks (search-snippet) | VentureBeat (verified) |
| xAI (now part of SpaceX) | Closed (Grok 4.x) | Old models released late under a restrictive licence (Grok 2.5, Aug 2025); Grok 3 and Grok 4.2 promised | | search-snippet |
| Microsoft | Uses OpenAI's closed models | Signed the July 2026 open-weights letter; small open models (Phi) | | verified (letter); memory (Phi) |
| NVIDIA | Open (Nemotron 3 Ultra) | Publishes weights, data, recipes under OpenMDW-1.1; leads industry advocacy; buying Hugging Face | Wider model supply sells chips (analyst reading) | The Batch, TechCrunch (verified) |
| Mistral | Open-weight, increasingly under custom licences at the top (Large 4) | Apache 2.0 for smaller models | | search-snippet |
| DeepSeek | Open (V4 Pro, V4.1 Flash) | MIT licence, weights at launch | | verified (Willison); V4.1 search-snippet |
| Moonshot | Open with delay (Kimi K3, K3.1 Pro) | API first, weights about 10 days later; custom licence with a $20M-revenue trigger for hosting providers | | verified |
| Z.ai (Zhipu) | Open with delay (GLM-5.3) | MIT through GLM-5.2 and for 5.3 Flash; GLM-5.3 weights held two weeks because "increased skill at finding and exploiting software vulnerabilities warranted safety testing before releasing its weights"; vetted security partners got early access | | The Batch, NIST (verified) |
| Alibaba | Open (Qwen3.8), including the Max-level 2.4T model for the first time | Apache 2.0 for small models; custom licence reported for the 2.4T model; earlier Max models were closed (memory) | | The Decoder (verified); licence search-snippet |

Patterns: (1) US frontier labs hold back their best model and release a smaller one; (2) Chinese labs release their best model but have begun staged release and custom licences; (3) the first capability-motivated hold on an open release by a Chinese lab happened in August 2026 (Z.ai, two weeks); (4) Beijing's October 2026 draft would put a licence step, described as automatic, in front of future top-end releases.

---

## 9. What this implies for the model's flag (my inference, not sourced fact)

1. **A binary "frontier weights are open" flag starts the game already true in the weak sense and false in the strict sense.** As of late 2026 a model one to two quarters behind the closed frontier is always downloadable; the closed frontier itself has never been released. The quantity that moves is the **lag in ticks** (about 1 to 2 quarterly ticks overall; about 2 on cyber), or equivalently whether open weights have crossed a given capability threshold.
2. **Release is irreversible; control is only available before release or at the hosting and use layers.** No actor has a "re-close" move. Government levers observed in 2026 are: pull back a *closed* model (works within a tick), exempt or include open models in pre-release testing, licence future releases above a threshold, and procurement or sanctions pressure on users.
3. **Safeguards on an open model do not survive the tick of release.** Any open release at capability X should be treated as unguarded X.
4. **The decision to release sits mainly with labs outside the leading closed labs' jurisdiction**, and their government (China) has its own, newly drafted, veto with a default of approval. A single government actor cannot set the flag.
5. **Open releases feed back on other actors:** price pressure on closed labs (documented), policy lobbying by closed labs against open models (reported), distillation from closed to open (alleged by the US government), and defensive and research benefits (documented, including a case where only an open model could be used for incident response).
6. **"Downloadable" and "usable by a small actor" have separated at the top end** (1.5 TB, trillions of parameters), which matters if the model equates open weights with universal access.

---

## 10. Facts I could not verify

- The Axios story of 20 Jul 2026 (Entity List and supply-chain options; "every 3-5 months" lobbying): page returned 403; details are from search summaries of secondary coverage.
- The Wired story of 12 Aug 2026 that the White House will extend pre-release testing to open models at Mythos / GPT-5.6-class capability: not opened.
- Artificial Analysis's own sentence "The open weights gap widens from 3 points to 12" and the v5 release page: only via secondary reports; the 12-point and 26-point figures refer to different models (Kimi K3.1 Pro, weights then unreleased, vs models actually downloadable).
- Exact termination terms of the Commerce directive (30 Jun 2026) and the text of the Is-Informed Letters: the letters are not public; I relied on Anthropic, Mayer Brown, Just Security and the LRI paper. The outcome of a customer lawsuit against the directive was not found.
- Status of China's draft export catalogue after the comment period (reported end 15 Nov 2026), and how the 4 Nov 2026 Kimi K3.1 Pro weight release was treated under interim registration.
- Whether GLM-5.3's final licence is MIT; the licence text for Qwen3.8-2.4T-A95B ("qwen3.8-max") and for Mistral Large 4; whether Meta has released Muse Spark 1.2 weights; whether xAI has released Grok 3 or Grok 4.2 weights; whether OpenAI has released any open-weight model after gpt-oss.
- The Hugging Face takedown of an abliterated GLM-5.3 repository (single low-quality source with inconsistent dates); the "same day" uncensored DeepSeek V4.1 Flash builds; counts of abliterated models (600 in 2024, 6,000+ by May 2026, about 7,970 later).
- OpenRouter figures not from OpenRouter itself: "61% Chinese share" (Feb or May 2026), "46% of enterprise API tokens", "around 60% of tokens from US-originating requests", and the 15.6% to 72.0% top-50 series.
- Hugging Face's US download share (36.5%) and Qwen's "3 billion cumulative downloads".
- Mozilla's 4.4-month estimate and doubling times (secondary coverage only).
- International AI Safety Report 2026 wording on the open-weight lag ("approximately one year" in one auto-generated summary, which conflicts with Epoch) and on recall.
- BadLlama cost figures beyond the BadLlama 3 abstract (under $200 for Llama 2 13B; under $0.50 and under $2.50 for Llama 3 8B and 70B): from search summaries of the arXiv pages.
- EU: any designation of an open-weight model as systemic-risk, the reported 29 Aug 2026 information requests, and the digital omnibus regulation number; the Commission's July 2025 guideline wording on which licences qualify as open-source.
- The China FIREWALL Act and NDAA s. 1651 texts (secondary source only); the "five Democratic senators" letter; Treasury's sanctions remark.
- Epoch's November 2024 report numbers, the Nvidia one-day market-value loss after DeepSeek R1, DeepSeek R1's and Kimi K2's release details, and Meta's 2023 Llama takedown notices are from memory.
- The Arena gap history is inconsistent between two secondary sources (29 Elo "widest in nearly two years" in Sep 2026 vs 56.3 a year before Jun 2026); Arena's own data was not opened.
- Quotes marked "verified" (as opposed to "verified-direct") were relayed by the fetch tool's summariser and should be re-checked against the page before being quoted in a report.
