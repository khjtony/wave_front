# Is the PRC reducible to the USSR, the USA or "the West"? Research note for the Cold War model

Scope: historical research for the question in `docs/cw_v0_decisions.md` D2 (PRC scripted before 1969, principal from tick 22 = 1969 with `border_clash`, `rapprochement`, `normalize`), `docs/ontology_cw.md` section 8 (`align_PRC`, `china_opening`, `esc_sino`), `docs/actions_cw.md` rows 26, 43, 59 to 62, and `docs/coldwar_testbed.md` section 2 (cw_v1 adds the PRC as a nuclear actor).

How sure the citations are:
- **[V]**: checked during this research against the source online (FRUS document numbers, the NSArchive EBB 49 document list, the CNA report's identifier, the Yang Kuisong article).
- **[S]**: standard citation in the literature, given from my own knowledge of it, not checked here. Author, title and year are reliable; page numbers are left out unless I am confident of them.
- **[U]**: uncertain or disputed. Check before encoding.

The model's question for each episode, as the owner asked it:
(1) Did Beijing take a decision Moscow did not want or did not control, and did Washington's or Moscow's choice depend on it?
(2) Was it a choice among documented, contemporaneous alternatives (needed for a principal's action), or is it better modeled as a Nature event?
(3) Which state variables did it touch?

---

## 1. Episodes

### 1.1 The alliance treaty, 14 Feb 1950

- **(1)** Partly Beijing's decision. "Leaning to one side" was Mao's own choice: "On the People's Democratic Dictatorship", 30 Jun 1949 [S]. The *form* of the alliance was imposed on a reluctant Stalin. At their first meeting (16 Dec 1949) Stalin wanted to keep the 1945 treaty with the Guomindang so as not to reopen Yalta. Mao held out in Moscow for a new treaty and got it in January 1950. Sources: the Russian record of the Mao–Stalin conversation of 16 Dec 1949, CWIHP *Bulletin* 6–7 (1995/96) [S]; Goncharov, Lewis and Xue, *Uncertain Partners: Stalin, Mao, and the Korean War* (1993), ch. 3–4 [S]; Chen Jian, *Mao's China and the Cold War* (2001), ch. 2 [S]; Shen Zhihua and Xia Yafeng, *Mao and the Sino-Soviet Partnership, 1945–1959* (2015) [S].
- **(2)** A choice with documented alternatives:
  - The Huang Hua–Leighton Stuart contacts in Nanjing (May–Jun 1949), and Stuart's possible trip to Beijing, which Mao vetoed [S]. Chen Jian 2001, ch. 2, treats US recognition as never a live option for Mao. Westad, *Cold War and Revolution* (1993), sees more contingency [S].
  - Mao's choice is therefore documented, but its alternative was weak.
- **(3)** `align_PRC` = soviet_ally at its initial level. Encoding it as the initial level, as v0 does, is defensible.

### 1.2 Korea intervention, October 1950, and Stalin's role

- **(1) Yes. This is the single clearest case.**
  - Stalin approved Kim's attack in spring 1950 on condition that Mao agreed. Stalin's telegram to Mao of 14 May 1950: the question "must be decided finally by the Chinese and Korean comrades together" [S]. Weathersby, CWIHP Working Paper 8 (1993) and *Bulletin* 5 (1995) [S].
  - After Inchon, Stalin asked Beijing on 1 Oct 1950 to send "five to six divisions". The intervention was a Soviet request, but Moscow did not control the answer.
  - Two versions of Mao's reply of 2 Oct exist [V for the dispute]:
    - The Chinese text (*Jianguo yilai Mao Zedong wengao*, vol. 1) says the decision to send troops has been taken.
    - The Russian text, sent by Roshchin on 3 Oct and held in the Presidential Archive (APRF), says China will *not* send troops for now because of the risks. Mansourov, "Stalin, Mao, Kim, and China's Decision to Enter the Korean War, 16 Sep–15 Oct 1950", CWIHP *Bulletin* 6–7 [S].
    - Shen Zhihua argues the Chinese text was drafted but never sent. *Mao, Stalin and the Korean War* (Routledge 2012), the chapter on the decision to intervene [S; Shen's exact position here is not verified, U].
  - The Politburo, 4–5 Oct 1950, was divided. Lin Biao declined the command; Peng Dehuai was named on 8 Oct [S].
  - At Sochi (10–11 Oct) Stalin and Zhou agreed that Soviet air cover would not come at once. Stalin told Kim to prepare to evacuate. Mao halted the troops on 12 Oct (Roshchin cable of 12 Oct [V, the Wilson Center/UMD copy]), then re-decided on 13 Oct to go in without immediate air cover [S].
  - So Stalin was prepared to let North Korea fall. The outcome lay in Beijing's hands. Chen Jian, *China's Road to the Korean War* (1994), ch. 5–6 [S].
  - Washington's choices depended on it:
    - Zhou warned through Panikkar on 3 Oct, and Washington discounted the warning [S].
    - After the Chinese offensive, Truman's press conference of 30 Nov 1950 raised atomic use [S].
    - Later came the decision not to widen the war to China (the MacArthur dismissal, Apr 1951) [S].
- **(2)** A principal's choice with a documented, contemporaneous alternative: the Russian 2 Oct text and the Politburo majority against it. Its contemporaneous sources are Mao's telegrams of 2 Oct and 13 Oct 1950 and the CPV order of 8 Oct 1950 (CWIHP translations [S]).
- **(3)** US–PRC war, the limited-war ceiling (US atomic deliberation in Nov–Dec 1950), and alliance cohesion. In v0 this is hidden inside `korea = war` and the USSR's `approve_korea` and `enter_korea`. The model cannot then show that the US–China war turned on a Beijing decision Moscow did not control.

### 1.3 The armistice, 1953

- **(1)** Mostly Moscow's decision, after Stalin died on 5 Mar 1953.
  - The Soviet Council of Ministers resolved on 19 Mar 1953 to seek an end to the war [S] (Weathersby, "New Russian Documents on the Korean War", CWIHP *Bulletin* 6–7).
  - Zhou's statement of 30 Mar 1953 conceded on POW repatriation [S].
  - Mao had prepared to fight on through the winter of 1952–53. Chen Jian 2001, ch. 4 [S]; Zhang Shu Guang, *Mao's Military Romanticism* (1995) [S].
  - The effect of Eisenhower's nuclear signalling, via Dulles and Nehru in May 1953, is disputed. Dingman, "Atomic Diplomacy during the Korean War", *International Security* 13:3 (1988–89); Foot, *A Substitute for Victory* (1990) [S].
- **(2)** A PRC choice, but conditioned on Moscow. Better as a joint USSR+PRC action, or as a Soviet action that the PRC follows. The PRC's documented alternative (fighting on) did exist.
- **(3)** `korea` back to peace, and escalation.

### 1.4 Taiwan Strait crises, 1954–55 and 1958

**1954–55**
- Shelling of Jinmen began on 3 Sep 1954. Yijiangshan was taken in Jan 1955.
- The US–ROC Mutual Defense Treaty was signed on 2 Dec 1954. The Formosa Resolution followed in Jan 1955.
- Public US nuclear threats: Dulles on 8 Mar 1955; Eisenhower's "just exactly as you would use a bullet", 16 Mar 1955 [S].
- Zhou's Bandung offer of 23 Apr 1955 led to the ambassadorial talks from Aug 1955.
- Moscow was not consulted beforehand [S]. Gordon Chang, "To the Nuclear Brink", *International Security* 12:4 (1988) [S]; Zhang Shu Guang, *Deterrence and Strategic Culture* (1992) [S].
- Consequence: the Secretariat's enlarged meeting of 15 Jan 1955 decided to build the bomb [S]. Lewis and Xue, *China Builds the Bomb* (1988), ch. 2.

**1958**
- Mao ordered the shelling of Jinmen on 23 Aug 1958. He did not tell Khrushchev, who had been in Beijing from 31 Jul to 3 Aug 1958 [S].
- Mao's reasons, in his speeches to the Supreme State Conference of 5 and 8 Sep 1958 (the "nooses" speech), were:
  - to test US resolve;
  - to support the Middle East after Lebanon;
  - to mobilize the country for the Great Leap.
  Chen Jian 2001, ch. 7 [S].
- Documented alternative: Mao's letter to Peng Dehuai and Huang Kecheng of 27 Jul 1958 postponed the attack. Mao "slept on it" [S] (CWIHP *Bulletin* 6–7 translation).
- Later restraint: the "Message to Compatriots in Taiwan" of 6 Oct 1958 and odd-day shelling from 25 Oct [S].
- The US side:
  - Dulles's Newport statement of 4 Sep 1958.
  - JCS planning assumed early nuclear use against mainland airfields. M. Halperin, *The 1958 Taiwan Straits Crisis: A Documented History* (RAND RM-4900-ISA, 1966; declassified, NSArchive) [S].
- Moscow reacted:
  - Gromyko went to Beijing on 6–7 Sep [S].
  - Khrushchev wrote to Eisenhower on 7 and 19 Sep 1958 that an attack on the PRC was an attack on the USSR. He wrote only after Beijing had signalled de-escalation, so he was covering himself, not deterring [S]. Zubok, *A Failed Empire* (2007), ch. 5; Lüthi, *The Sino-Soviet Split* (2008), ch. 3 [S].
  - Gromyko's memoir has Mao proposing that the Soviets answer a US invasion with nuclear weapons only after the Americans were deep inland [U: memoir, disputed].
- **(1)** Yes, both times. Beijing decided and Moscow neither wanted nor controlled it. US nuclear-use planning and the Soviet guarantee letters both depended on it.
- **(2)** Principal choices with documented alternatives: the 27 Jul postponement, the 6 Oct message, and the 1955 turn to talks.
- **(3)**
  - US–PRC escalation, up to US nuclear planning.
  - US–Soviet escalation, through Khrushchev's letters (weakly).
  - Alliance alignment: the crisis fed Khrushchev's June 1959 decision on the bomb accord.
  - PRC nuclear status: the 1955 decision.
  - v0 does not model the Strait (decisions D2, "Not modeled").

### 1.5 The New Defense Technical Accord (15 Oct 1957) and its cancellation (20 Jun 1959)

- In the Accord the USSR promised a prototype bomb and technical data.
- Khrushchev's motive was Chinese support after the "anti-party group" of June 1957 and for the November 1957 Moscow conference [S].
- The Soviet letter of 20 Jun 1959 suspended delivery, citing the Geneva test-ban talks. Beijing named its first device "596" after it [S]. Lewis and Xue 1988, ch. 3–4 [S]; Lüthi 2008, ch. 3–4 [S].
- **(1)** The cancellation was Moscow's decision. The PRC's decision was to go on alone. The 1958 Strait crisis and Mao's rejection of the "joint fleet" and long-wave radio proposals (Mao–Yudin, 22 Jul 1958 [S]) fed Moscow's choice.
- **(2)** Cancellation is a USSR action. Self-reliance is a PRC action. Documented alternative: the 1961 debate on suspending the programme during the famine, where Nie Rongzhen and Chen Yi argued to continue [S/U on the exact meeting; Lewis and Xue 1988 discuss it].
- **(3)** PRC nuclear status, alliance alignment.

### 1.6 The split, 1959–63: whose decision?

- **Historiography:**
  - Lüthi 2008 puts ideology and Mao's domestic politics first: the Great Leap and Lushan in Jul–Aug 1959. Mao used the anti-Soviet line to defend the Leap and his left turns.
  - Radchenko, *Two Suns in the Heavens* (2009), shows Moscow trying to repair relations more than Beijing did in 1962–64 [S].
  - Shen and Xia 2015 stress Mao's sensitivity to equality and sovereignty [S].
  - Westad (ed.), *Brothers in Arms* (1998), introduction: the alliance was asymmetric from the start [S].
- **Sequence:**
  - Khrushchev and Mao quarrelled in Beijing on 2 Oct 1959 (Russian record, CWIHP *Bulletin* 12–13 [S]).
  - "Long Live Leninism!" (*Hongqi*, 16 Apr 1960) opened the public polemics. **Beijing's move.**
  - At Bucharest (June 1960) Khrushchev attacked the CCP.
  - Moscow withdrew its advisers by a note of 16 Jul 1960. **Moscow's move, reacting to Beijing.**
  - A truce at the 81-party conference (Nov 1960) did not hold.
  - The Moscow talks of Jul 1963 failed. The LTBT was signed on 5 Aug 1963. The Chinese government denounced it on 31 Jul 1963. Then came the "Nine Commentaries" (Sep 1963–Jul 1964) [S].
- **Documented alternative on the Chinese side:** Wang Jiaxiang's letters of Feb–Mar 1962 proposed easing tension with the USSR and the US and cutting aid: "three reconciliations and one reduction" (*san he yi shao*) [S]. Mao rejected them at the 10th Plenum, Sep 1962. Chen Jian 2001, ch. 3 [S]; Lüthi 2008, ch. 6 [S].
- **(1)** The ideological initiative and escalation came from Beijing. The decisive material act, withdrawing the advisers, came from Moscow. **v0's "the split of 1960 is Moscow's decision" is half-true.** Moscow's `withdraw_advisers` answered a Chinese challenge Moscow did not want.
- **(2)** The challenge is a principal's choice with a documented alternative (Wang Jiaxiang 1962). Lüthi would also count the Mao–Khrushchev 1959 meeting.
- **(3)** `align_PRC` (split), bloc integrity in the wide sense (the communist movement; the v0 `bloc_USSR` is Eastern Europe only), and the US reading of a monolith.

### 1.7 Cuba 1962 and the Chinese reaction

- Beijing first backed Moscow, then denounced Khrushchev for "adventurism" and then "capitulationism" (*Renmin Ribao* editorials, Nov–Dec 1962 [S]).
- It ran alongside the Sino-Indian war (20 Oct–21 Nov 1962). *Pravda*'s brief pro-Chinese turn of 25 Oct reversed after Cuba [S]. Lüthi 2008, ch. 7; Radchenko 2009, ch. 1 [S].
- **(1)** No effect on the US–Soviet outcome of the crisis. It deepened the split.
- **(2)** Nature, or not modeled.
- **(3)** Split depth only.

### 1.8 The nuclear test, 16 Oct 1964

- The decision went back to 15 Jan 1955 and the self-reliance choice of 1959–61. The H-bomb followed on 17 Jun 1967.
- **US response:**
  - The Kennedy administration explored joint action with Moscow. Harriman was instructed in July 1963 and Khrushchev showed no interest [S].
  - Johnson's principals (Rusk, McNamara, Bundy, McCone) decided on 15 Sep 1964 against a preventive strike [S].
  - Burr and Richelson, "Whether to 'Strangle the Baby in the Cradle'", *International Security* 25:3 (2000/01) [S].
- **(1)** Moscow did not want it and could not stop it. Washington weighed a strike, which depended on it. The bomb also mattered in 1969: Lyle Goldstein, "Do Nascent WMD Arsenals Deter? The Sino-Soviet Crisis of 1969", *Political Science Quarterly* 118:1 (2003) [S]. Gerson 2010 as well.
- **(2)** A principal's choice (begin in 1955 and continue in 1959–61) with documented alternatives: suspension in 1961 [S/U]. Not a 1964 event choice. The test date itself is better as Nature, a timed capability outcome.
- **(3)** `nuke_PRC` (none to few). This feeds the Soviet strike calculus in 1969 and the US preventive-strike option in 1963–64. It concerns cw_v1's "PRC as nuclear actor" (testbed section 2).

### 1.9 Vietnam aid, 1965–68

- **The PRC sent about 320,000 support troops** (engineering and anti-aircraft) in 1965–68. Chen Jian, "China's Involvement in the Vietnam War, 1964–69", *China Quarterly* 142 (1995) [S]; Zhai Qiang, *China and the Vietnam Wars, 1950–1975* (2000) [S].
- **It refused "united action" with Moscow:**
  - Mao rejected it in his conversation with Kosygin, 11 Feb 1965 (CWIHP [S]).
  - Beijing obstructed the transit of Soviet supplies [S].
- **It signalled red lines to Washington.**
  - Mao to Edgar Snow, 9 Jan 1965.
  - Zhou's four-point message through Ayub Khan, 2 Apr 1965: China would not provoke war, but would fight if the US invaded the North [S]. Hershberg and Chen Jian, "Reading and Warning the Likely Enemy", *International History Review* 27:1 (2005) [S].
- **(1)** Yes. Moscow did not control it and wanted something else (united action). Washington's choice depended on it. The decision not to invade the North, and the target limits in Rolling Thunder, were shaped by fear of a repeat of Korea. Khong, *Analogies at War* (1992) [S]; Hershberg and Chen 2005.
- **(2)** A principal's choice with documented alternatives: united action, as Moscow proposed in Feb–Apr 1965, or direct combat entry.
- **(3)** The limited-war ceiling (US escalation), the split, and alliance alignment. v0 does not model Vietnam (D2).

### 1.10 The Cultural Revolution's foreign-policy effect, 1966–69

- All ambassadors but Huang Hua (Cairo) were recalled in 1967. The British mission was burned (22 Aug 1967). The Soviet embassy was besieged (Jan–Feb 1967). The Hong Kong riots came in 1967.
- Barnouin and Yu, *Chinese Foreign Policy during the Cultural Revolution* (1998) [S]; MacFarquhar and Schoenhals, *Mao's Last Revolution* (2006) [S].
- **(1)** Moscow did not want it. It raised Soviet threat perception and the build-up on the border (from 1965–66).
- **(2)** A domestic process, not a foreign-policy choice among alternatives: **Nature**. Its later output was a principal choice: the Four Marshals' study group (Chen Yi, Ye Jianying, Nie Rongzhen, Xu Xiangqian). Their reports of 11 Jul and 17 Sep 1969 included Chen Yi's "unconventional" idea of a high-level approach to the US. CWIHP *Bulletin* 11 (1998), trans. Chen Jian and Li Danhui [S].
- **(3)** `esc_sino` pressure (the Soviet build-up), PRC isolation.

### 1.11 Zhenbao/Damansky (2 and 15 Mar 1969) and the Soviet strike soundings (Aug–Sep 1969)

- **Zhenbao, 2 Mar 1969.** A planned Chinese ambush.
  - Yang Kuisong, "The Sino-Soviet Border Clash of 1969: From Zhenbao Island to Sino-American Rapprochement", *Cold War History* 1:1 (2000), 21–52 [V citation].
  - Gerson, *The Sino-Soviet Border Conflict: Deterrence, Escalation, and the Threat of Nuclear War in 1969*, CNA CRM D0022974.A2/Final, Nov 2010 [V citation]: China initiated it to deter by a show of resistance.
  - Contemporaneous US reading: the CIA *Weekly Review* of 21 Mar 1969 judged that Beijing "triggered" it. NSArchive EBB 49 (ed. Burr, 2001), doc. 2 [V]. The INR note of 4 Mar 1969 (doc. 1) is agnostic [V].
- **Escalation.**
  - The Soviet counterattack of 15 Mar 1969.
  - The Soviet-initiated Tielieketi/Zhalanashkol clash in Xinjiang, 13 Aug 1969 [S].
- **Soviet strike soundings.**
  - KGB officer Davydov asked Stearman (State Department) how the US would react to a Soviet strike on Chinese nuclear facilities: Stearman memcon, 18 Aug 1969, EBB 49 doc. 10 [V].
  - Further reports came through Tehran (4 Sep, doc. 16) and Shevchenko at the UN (5 Sep, doc. 18) [V].
  - Rogers to Nixon on a possible strike, 10 Sep (doc. 19) [V]. Kissinger to Nixon on the US role in Soviet manoeuvring, 29 Sep (doc. 24) [V].
  - Nixon told the NSC on 14 Aug 1969 that it was against US interests for China to be "smashed" in a Sino-Soviet war [S] (Kissinger, *White House Years*, 1979). The Richardson speech of 5 Sep 1969 said the same in public [S].
  - Gerson's reading: the soundings were mostly coercive diplomacy to force Beijing to talks, and they worked [S].
- **(1)** Yes. Beijing initiated the March clash, which Moscow did not want and did not control. Moscow's choice (the soundings, the threat to strike) depended on it. So did Washington's (the 14 Aug NSC line and the 5 Sep signal).
- **(2)** A principal's choice with alternatives: earlier restraint orders on the border. Yang 2000 describes how the policy moved from not firing first to a planned counterattack in Jan–Feb 1969 [S/U on the exact dates]. v0's `border_clash` is right in kind.
- **(3)** `esc_sino` to clash, Soviet strike planning (the `strike_china` guard), `nuke_PRC` as a target, US–Soviet relations (the US signal against a strike).

### 1.12 Kosygin–Zhou, Beijing airport, 11 Sep 1969

- Kosygin returned from Ho Chi Minh's funeral. They agreed to border talks and to keep the status quo on the border. The talks opened on 20 Oct 1969.
- Beijing kept fearing a surprise attack: Lin Biao's "Order No. 1" of 18 Oct 1969, and the dispersal of the leadership [S].
- The Chinese record of the meeting is in the Wilson Center Digital Archive [S]. Yang 2000; Gerson 2010; Lüthi 2008, epilogue [S].
- **(1)** Joint. The talks were Moscow's initiative and Beijing's acceptance.
- **(2)** A PRC choice with an alternative: refusing talks, as Beijing had done in spring 1969, when it left the Soviet calls unanswered [S].
- **(3)** `esc_sino` held at clash, not raised to war. The meeting removed the occasion for `strike_china`.

### 1.13 The opening, 1970–72: whose initiative?

- **Washington:**
  - Nixon, "Asia After Viet Nam", *Foreign Affairs* (Oct 1967).
  - NSSM 14 (Feb 1969).
  - Nixon to Yahya Khan and Ceaușescu (Aug 1969).
  - Stoessel's approach in Warsaw (3 Dec 1969).
  - The Warsaw meetings of 20 Jan and 20 Feb 1970.
- **Beijing:**
  - The Four Marshals' reports (1969).
  - Snow on the Tiananmen rostrum (1 Oct 1970) and Mao's interview of 18 Dec 1970 ("welcome Nixon").
  - Zhou's message through Yahya (Dec 1970).
  - Zhou's message of 21 Apr 1971 inviting an envoy, which followed ping-pong diplomacy.
- **Meetings:** Kissinger–Zhou, 9 Jul 1971 (FRUS 1969–76, vol. XVII, doc. 139 [V]). Mao–Nixon, 21 Feb 1972 (FRUS XVII, doc. 194 [V]). The Shanghai Communiqué, 28 Feb 1972.
- MacMillan, *Nixon and Mao* (2007); Burr (ed.), *The Kissinger Transcripts* (1998) [S]; Chen Jian 2001, ch. 9 [S].
- **(1)** A mutual initiative. Neither side could open alone. The US move was conditional on Chinese replies, and Beijing chose the timing and the channel. Moscow neither wanted nor controlled it. Moscow's later choices responded to it: speeding up SALT and the May 1972 summit (Kissinger, *White House Years*; Garthoff, *Détente and Confrontation*, 1985/94 [S]).
- **(2)** A principal's choice with documented alternatives:
  - accommodation with Moscow through the border talks;
  - continuing dual hostility (the "two-fist" line);
  - Lin Biao's reported opposition [U].
- **(3)** `china_opening`, `align_PRC` to us_aligned, the US–Soviet balance (C11's pivotal coalition).

### 1.14 1973–76: the "one line" (*yitiaoxian*)

- Mao proposed a "horizontal line" (US, Japan, China, Pakistan, Iran, Turkey, Europe) against the USSR to Kissinger, 17 Feb 1973 (FRUS 1969–76, vol. XVIII, China 1973–76; the memcon is doc. 12 [U on the number]).
- Liaison offices opened in 1973.
- **Limits:**
  - Taiwan was unresolved.
  - Mao later chided Kissinger for "standing on China's shoulders" to reach Moscow (Oct 1975 [S]).
  - Deng's "Three Worlds" speech at the UN, 10 Apr 1974, kept ideological independence.
  - Burr, *The Kissinger Transcripts*; Ross, *Negotiating Cooperation* (1995) [S].
- **(1)** Beijing's decision, against Moscow. The US used it as leverage in détente.
- **(2)** A principal's choice, though largely a continuation of 1971–72.
- **(3)** `align_PRC` = us_aligned, though it fits "us_aligned" only loosely. The PRC was a strategic partner, not a bloc member.

### 1.15 The 1979 war on Vietnam and the Soviet non-response

- Deng told Carter on 29–30 Jan 1979 that China would "teach Vietnam a lesson". Carter discouraged it privately [S]. FRUS 1977–80, vol. XIII, China, the Carter–Deng memcons [S; doc. no. U].
- The attack ran from 17 Feb to 16 Mar 1979.
- The Soviet–Vietnamese treaty of 3 Nov 1978 did not trigger Soviet military action beyond naval deployments, an airlift and exercises [S].
- Beijing prepared for a Soviet response: civilians evacuated from the northern border, and the Sino-Soviet treaty denounced on 3 Apr 1979.
- Zhang Xiaoming, *Deng Xiaoping's Long War* (2015) [S]; Radchenko, *Unwanted Visionaries* (2014), ch. 1 [S]; Westad, *The Cold War: A World History* (2017), the China chapters [S].
- **(1)** Yes. Moscow neither wanted nor controlled it. Moscow's choice (not to respond) depended on it. It tested Soviet alliance credibility in Asia.
- **(2)** A principal's choice with a documented alternative: Carter's counsel against it, and internal reservations [U].
- **(3)** `esc_sino` (risk of war), Soviet bloc credibility in the wide sense.

### 1.16 Deng's "three obstacles" and the 1982 independent foreign policy

- The three obstacles: Soviet forces on the border and in Mongolia, Afghanistan, and Vietnam in Cambodia.
- Brezhnev's Tashkent speech of 24 Mar 1982 made an overture.
- At the 12th Party Congress (Sep 1982), Hu Yaobang's report announced an "independent foreign policy". Vice-ministerial consultations began in Oct 1982 [S].
- Context: the dispute over US arms sales to Taiwan, ended by the 17 Aug 1982 communiqué. Radchenko 2014, ch. 1–2 [S]; Ross 1995 [S].
- **(1)** Beijing's decision. It pulled back from alignment with the US without returning to Moscow. Neither superpower controlled it.
- **(2)** A principal's choice with a documented alternative: continuing the anti-Soviet alignment that Haig was pressing in 1981.
- **(3)** `align_PRC`. This calls for a fourth level, `independent`, or for making the variable non-monotone. v0's monotone `align_PRC` cannot represent 1982.

### 1.17 Normalization, May 1989

- The Soviet concessions came first:
  - Gorbachev's Vladivostok speech, 28 Jul 1986;
  - withdrawal from Afghanistan (Feb 1989);
  - pressure on Vietnam to leave Cambodia (announced 1989).
- Gorbachev visited Beijing from 15 to 18 May 1989. Deng: "close the past, open the future". Radchenko 2014 [S].
- **(1)** Mainly Moscow's moves, which met Beijing's stated conditions.
- **(2)** The PRC's choice was to set conditions and keep to them. v0's `normalize` guard `obstacles: afghan = withdrawn` encodes this well.
- **(3)** `esc_sino` back to peace.

---

## 2. Judgement for the model

### A. When was the PRC an independent strategic actor whose choices changed US–Soviet outcomes?

**From 1950, not only from 1969.** The strongest pre-1969 cases:

1. **Korea, Oct 1950.**
   - Stalin requested intervention but then withdrew immediate air cover and was ready to abandon Kim (Mansourov; Chen Jian 1994; Shen 2012).
   - The Chinese decision turned a US–North Korean war into a US–Chinese war. It put US atomic use on the table (30 Nov 1950).
   - A Soviet-bloc decision rule ("comply with a Moscow request") would not reproduce it: the Politburo nearly refused, and Moscow then weakened its own request.
2. **The Taiwan Strait, 1954–55 and 1958.**
   - Unilateral and unannounced to Moscow.
   - Produced US nuclear threats (1955) and nuclear planning (1958), and drew a Soviet nuclear guarantee given reluctantly and after the fact.
   - Fed the 1959 cancellation of the bomb accord.
3. **The split, 1960.** Beijing's ideological challenge started the sequence. Moscow's adviser withdrawal was the response.
4. **Vietnam, 1965–68.**
   - Chinese deterrent signalling capped US escalation.
   - The refusal of united action kept the communist side divided.

What the PRC did *not* change: the US–Soviet strategic ladder (`esc` between principals) in any crisis other than Korea. Its effects run through alignment, regional war ceilings, bloc cohesion in the wide sense, and (from 1964) a third nuclear force.

### B. Is the PRC's behaviour model distinct?

**Distinct. It does not collapse into "Soviet-bloc member" before 1959 or "US-aligned" after 1972.** The evidence:

- **Objectives include revolutionary legitimacy and domestic mobilization.**
  - Chen Jian's central thesis (2001, introduction and ch. 7): Mao used external tension to drive "continuous revolution". His own words on 1958 are the Supreme State Conference speeches.
  - Lüthi 2008: the split is driven by Mao's domestic agenda.
  - Neither the USSR nor the US used foreign crises this way.
- **Higher risk acceptance against stronger adversaries:**
  - 1950 (entering against the US without air cover);
  - 1958 (shelling under explicit US nuclear planning);
  - 1969 (ambushing a nuclear superpower; Gerson's "deterrence by provocation");
  - 1979 (attacking a Soviet treaty ally).
  
  A rule tuned to the USSR (`aims_USSR` opportunist: "retreat before counterforce") would not generate 1950 or 1969.
- **Sovereignty and equality demands inside the alliance.** The 1949–50 treaty fight and the 1958 rejection of the joint fleet show these. They make "bloc member" the wrong rule even in 1950–57, when the outcomes were aligned.
- **Triangular balancing, 1969–89.**
  - 1969–72: tilt to the US.
  - 1973–76: "one line".
  - 1982: independent policy.
  - 1989: normalization.
  
  This is balancing against the nearer threat, not alignment. Beijing kept Taiwan as a condition throughout, and moved away from Washington in 1982.

Where reduction is fair:
- **1953 armistice:** effectively Moscow's decision.
- **1962 Cuba reaction:** no effect.
- **1966–68 Cultural Revolution:** Nature.
- **1989 normalization:** mostly Soviet concessions against fixed Chinese conditions.

### C. Recommendation

**Make the PRC a principal from 1950 (tick 3, if tick 0 = 1947 as `tick ≥ 22` = 1969 implies), with occasion-gated actions. Script the episodes that were not Chinese choices as Nature or as Soviet actions.**

- If the annual model must stay small, the fallback is **from 1958** (the second Strait crisis and the split). Note the cost: the Korea intervention then stays inside `korea = war`, and relaxation analyses cannot show that a US–China war turned on Beijing's choice.
- Keeping "from 1969" is defensible only as a declared scope cut. D2 already does this by labelling `principal` a scope part. But the reason D2 gives ("the model has no PRC decision before 1969") is a modeling choice, not a historical finding.

**Model changes the evidence calls for:**
- `align_PRC` needs an `independent` level, or must become non-monotone, for 1982.
- The split should be a PRC challenge followed by the USSR's `withdraw_advisers`, not Moscow's decision alone.
- `nuke_PRC` belongs in the annual model, not only in cw_v1, because it gates the 1969 strike calculus.

**Actions for a principal PRC.** Each row gives the contemporaneous source and the documented alternative.

| # | Action | Occasion | Contemporaneous source | Documented alternative | Touches |
|---|---|---|---|---|---|
| 1 | `enter_korea` | Oct 1950 | Mao's telegrams of 2 Oct (Chinese text) and 13 Oct 1950; CPV order of 8 Oct 1950 (CWIHP) | Russian text of 2 Oct (Roshchin, 3 Oct, APRF): no troops for now; the Politburo majority of 4–5 Oct; the halt of 12 Oct | Korea war parties, escalation (US atomic deliberation) |
| 2 | `strait_pressure` (shell offshore islands) | 1954, 1958 | Mao to Peng and Huang, 27 Jul 1958; Supreme State Conference speeches, 5 and 8 Sep 1958 | The postponement of 27 Jul 1958; talks at Bandung (23 Apr 1955); the 6 Oct 1958 message | US–PRC escalation (US nuclear threats), Soviet guarantee, alliance strain |
| 3 | `build_bomb` (start and continue) | Jan 1955; 1959–61 | Secretariat enlarged meeting, 15 Jan 1955; the "596" self-reliance decision after the Soviet letter of 20 Jun 1959 (Lewis and Xue 1988) | Suspension during the 1961 famine debate [S/U] | `nuke_PRC` |
| 4 | `challenge_moscow` (public polemic) | 1960 (to 1963) | "Long Live Leninism!", 16 Apr 1960; the Nine Commentaries 1963–64 | Wang Jiaxiang's letters, Feb–Mar 1962 (*san he yi shao*), rejected Sep 1962 | `align_PRC` → split (with USSR `withdraw_advisers`) |
| 5 | `deter_in_vietnam` (support troops plus red-line signal, no united action) | 1965 | Zhou via Ayub Khan, 2 Apr 1965; Mao–Kosygin, 11 Feb 1965 | Soviet proposal of united action (Feb–Apr 1965); direct combat entry | Ceiling on US escalation; split |
| 6 | `border_clash` (as v0) | Mar 1969 | Chinese border plans of Jan–Feb 1969 (Yang 2000); CIA *Weekly Review*, 21 Mar 1969 (EBB 49 doc. 2) | The earlier rule of not firing first [S/U] | `esc_sino` |
| 7 | `rapprochement` (as v0) | 1970–71 | Four Marshals' reports, 11 Jul and 17 Sep 1969; Zhou's message of 21 Apr 1971; FRUS XVII doc. 139 (9 Jul 1971) | Settlement with Moscow via the 11 Sep 1969 Kosygin–Zhou track; continuing dual hostility | `align_PRC` → us_aligned |
| 8 | `independent_line` / `normalize` (as v0's normalize, plus the 1982 de-alignment) | 1982; 1989 | Hu Yaobang's report to the 12th Congress, Sep 1982; the three obstacles | Continuing the anti-Soviet alignment (1981) | `align_PRC` → independent; `esc_sino` → peace |

Optional ninth action: `punish_vietnam` (Feb 1979). Source: the Deng–Carter memcons, Jan 1979. Alternative: Carter's counsel against it. It tests `esc_sino` and Soviet alliance credibility, but v0 does not model Vietnam.

**Better kept as Nature or as other actors' actions:**
- the 1953 armistice (a USSR action);
- the 1957 bomb accord and its 1959 cancellation (USSR actions);
- the reaction to Cuba;
- the Cultural Revolution;
- the 1964 test date (a capability outcome of action 3);
- Kosygin–Zhou (a USSR initiative that the PRC accepts; it can be a guard on `strike_china`).

## 3. Open items to verify before encoding

- Shen Zhihua's exact position on the two 2 Oct 1950 texts (his 2012 book and the Shen–Yang exchange).
- The FRUS XVIII document number for Mao–Kissinger, 17 Feb 1973. The FRUS 1977–80 vol. XIII document numbers for Deng–Carter, Jan 1979.
- The 1961 debate on suspending the bomb programme: the meeting and its date (Lewis and Xue 1988).
- The date and wording of the shift from the not-firing-first rule to a planned counterattack on the border (Yang 2000; Gerson 2010, ch. 2).
- The Gromyko memoir episode (1958), and Lin Biao's opposition to the opening: both disputed.
- Page numbers throughout. None are given except Yang 2000 (21–52).
