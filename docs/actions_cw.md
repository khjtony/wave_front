# Cold War v0 actions: decision spaces, guards, effects, delays

Status: written with [ontology_cw.md](ontology_cw.md) for the model step, after the registration of C1 to C13 and before any registered claim was run (the one early sight is disclosed in [cw_v0_decisions.md](cw_v0_decisions.md) D9). The tables below are generated from the model (`python scripts/cw_catalogue.py`; tests/coldwar/test_model_cw.py checks that they match), so the code and the catalogue cannot drift; every action's source, with its dated documents, is its `source=` in `models/cw/v0.py` and `models/cw/crises/`.

## 1. Conventions

1. **Decision spaces from contemporaneous alternatives** (ww2_testbed.md section 7, rule 2). Every action is a decision taken or debated at the time, with the document of the debate in its source. The decisions debated and not taken are listed in section 3. No action is speculative: each not-taken alternative has a dated record of its consideration.
2. **Guards as named parts** (spec section 3.1). A part is one documented condition; relaxing it is lifting that condition. Parts named `level` keep a variable's own ladder (an action applies at one level); `occasion` fixes a branch point to the year the record has it (decisions D5); `hypothesis` is the gate of D3; `principal` is the PRC's scope (decisions D2), not a historical constraint; `policy` on `USA.preventive_strike` is the documented rejection (always false; relaxing it is the option taken, claim C12).
3. **Effects.** `esc` and `esc_sino` change only by `Bump` (decisions D4). A `SetIf` of the form `x := L if x < L` raises a monotone variable to a level. Delays are years from the decision to the first 1 January showing the effect (spec section 3.1: chosen at t, visible at t + 1 + d).
4. **One decision per actor per year, one Nature event per year** (decisions D1); the placements forced by these rules are noted in data/cw/realized_moves.csv and data/cw/decisions.csv.
5. **Crisis actions** (`USSR.blockade`, `USSR.deploy_cuba`, `USA.able_archer`) have no effect: the sub-game is their effect (spec section 14). In the coarse game alone they are inert.

## 2. Tables

<!-- tables:begin -->
### The coarse game (`models/cw/v0.py`)

| Actor | Action | Guard parts | Effect | Delay |
|---|---|---|---|---|
| USA | `approve_u2` | `level`: intel_USA = low | intel_USA := partial if intel_USA < partial | 2 |
| USA | `survivable_force` | `level`: nuke_USA = few | nuke_USA := survivable if nuke_USA < survivable | 4 |
| USA | `corona` | `level`: intel_USA = partial | intel_USA := overhead if intel_USA < overhead | 2 |
| USA | `offer_test_ban` | `level`: offer = none | offer := test_ban if offer < test_ban |  |
| USA | `strategic_buildup` | `missile_gap`: belief_force_USA ≥ survivable; `level`: nuke_USA = survivable | nuke_USA := overkill if nuke_USA < overkill | 3 |
| USA | `offer_limits` | `standing`: offer = test_ban; `parity`: nuke_USSR ≥ survivable | offer := limits if offer < limits |  |
| USA | `open_china` | `split`: align_PRC = split; `level`: ¬china_opening | china_opening := True |  |
| USA | `buildup` | `level`: ¬buildup | buildup := True |  |
| USA | `offer_reductions` | `standing`: offer = limits | offer := reductions if offer < reductions |  |
| USA | `armistice` | `theatre`: korea = war | korea := armistice |  |
| USA | `preventive_strike` | `superiority`: (nuke_USA ≥ few ∧ nuke_USSR ≤ few); `threat`: belief_USA_USSR = expansionist; `policy`: FALSE | esc +4; us_strike := True |  |
| USA | `nuclear_korea` | `theatre`: korea = war; `total_commitment`: esc ≥ conventional; `reading`: belief_USA_USSR ≠ opportunist | esc +4 |  |
| USA | `escalate` | `crisis`: esc = crisis | esc +1; us_began_war := True |  |
| USA | `nuclear_use` | `war`: esc = conventional; `means`: nuke_USA ≥ few | esc +1 |  |
| USA | `preempt` | `warning`: belief_USA_USSR = expansionist; `crisis`: esc ≥ crisis | esc +3 |  |
| USA | `able_archer` | `occasion`: tick = 36 | none (crisis) |  |
| USSR | `build_bomb` | `level`: nuke_USSR = none | nuke_USSR := few if nuke_USSR < few; belief_force_USA := few | 4 |
| USSR | `blockade` | `occasion`: tick = 1 | none (crisis) |  |
| USSR | `approve_korea` | `hypothesis`: aims_USSR = opportunist; `occasion`: korea = peace; `bomb`: nuke_USSR ≥ few | korea := war |  |
| USSR | `enter_korea` | `theatre`: korea = war; `hypothesis`: aims_USSR = opportunist; `readiness`: nuke_USSR ≥ survivable | esc +2 |  |
| USSR | `berlin_ultimatum` | `open`: ¬berlin_wall; `level`: esc = peace | esc +1 |  |
| USSR | `lapse` | `crisis`: esc = crisis; `open`: ¬berlin_wall | esc -1 |  |
| USSR | `build_wall` | `crisis`: esc = crisis; `open`: ¬berlin_wall | berlin_wall := True; esc -1 |  |
| USSR | `withdraw_advisers` | `alliance`: align_PRC = soviet_ally | align_PRC := split if align_PRC < split |  |
| USSR | `deploy_cuba` | `occasion`: tick = 15 | none (crisis) |  |
| USSR | `accept_test_ban` | `offer`: offer ≥ test_ban; `level`: oversight = none | oversight := test_ban if oversight < test_ban |  |
| USSR | `icbm_buildup` | `level`: nuke_USSR = few | nuke_USSR := survivable if nuke_USSR < survivable; belief_force_USA := survivable if intel_USA = overhead | 2 |
| USSR | `mirv` | `level`: nuke_USSR = survivable | nuke_USSR := overkill if nuke_USSR < overkill; belief_force_USA := overkill if intel_USA = overhead | 5 |
| USSR | `accept_limits` | `offer`: offer ≥ limits; `regime`: oversight = test_ban; `parity`: nuke_USSR ≥ survivable | oversight := ntm if oversight < ntm; arms := capped if arms < capped |  |
| USSR | `invade_afghanistan` | `occasion`: tick ≥ 32; `level`: afghan = none | afghan := war |  |
| USSR | `preempt` | `warning`: belief_USSR_USA = first_strike_intent; `crisis`: esc ≥ crisis; `means`: nuke_USSR ≥ few | esc +3 |  |
| USSR | `escalate` | `crisis`: esc = crisis | esc +1 |  |
| USSR | `nuclear_use` | `war`: esc = conventional; `means`: nuke_USSR ≥ few; `nato_attack`: us_began_war | esc +1 |  |
| USSR | `invade_west` | `hypothesis`: aims_USSR = opportunist; `response`: esc ≥ crisis; `no_us_nuclear`: nuke_USA = none | esc +1; invasion_west := True |  |
| USSR | `intervene` | `contested`: bloc_USSR = contested; `capacity`: afghan ≠ war; `will`: legit_USSR = secure | bloc_USSR := intact |  |
| USSR | `perestroika` | `level`: ¬perestroika; `crisis`: econ_USSR ≥ stagnant | perestroika := True; legit_USSR := contested if legit_USSR < contested |  |
| USSR | `accept_reductions` | `offer`: offer ≥ reductions; `regime`: oversight = ntm; `new_thinking`: perestroika | oversight := on_site if oversight < on_site; arms := reduced if arms < reduced |  |
| USSR | `withdraw_afghanistan` | `level`: afghan = war | afghan := withdrawn |  |
| USSR | `dissolve` | `released`: bloc_USSR = released; `legitimacy`: legit_USSR = failing | bloc_USSR := dissolved |  |
| USSR | `strike_china` | `confrontation`: esc_sino = clash; `targets`: tick ≥ 18; `no_us_link`: align_PRC ≠ us_aligned | esc_sino +1 |  |
| PRC | `border_clash` | `principal`: tick ≥ 22; `split`: align_PRC = split; `level`: esc_sino = peace | esc_sino +1 |  |
| PRC | `rapprochement` | `principal`: tick ≥ 22; `opening`: china_opening; `threat`: esc_sino = clash | align_PRC := us_aligned if align_PRC < us_aligned |  |
| PRC | `normalize` | `principal`: tick ≥ 22; `clash`: esc_sino = clash; `obstacles`: afghan = withdrawn | esc_sino -1 |  |
| Nature | `nsc68` | `level`: belief_USA_USSR = opportunist; `soviet_bomb`: nuke_USSR ≥ few | belief_USA_USSR := expansionist |  |
| Nature | `new_look` | `level`: belief_USA_USSR = expansionist | belief_USA_USSR := opportunist |  |
| Nature | `missile_gap` | `blind`: intel_USA ≠ overhead; `soviet_force`: nuke_USSR = few | belief_force_USA := survivable |  |
| Nature | `estimate_revised` | `overhead`: intel_USA = overhead; `gap`: belief_force_USA > nuke_USSR | belief_force_USA := nuke_USSR |  |
| Nature | `war_scare` | `level`: belief_USSR_USA = hostile; `us_buildup`: buildup | belief_USSR_USA := first_strike_intent |  |
| Nature | `reassurance` | `level`: belief_USSR_USA = first_strike_intent | belief_USSR_USA := hostile |  |
| Nature | `new_thinking` | `level`: belief_USSR_USA = hostile; `reform`: perestroika | belief_USSR_USA := status_quo |  |
| Nature | `slowdown` | `level`: econ_USSR = growing; `burden`: nuke_USSR ≥ survivable | econ_USSR := stagnant |  |
| Nature | `decline` | `level`: econ_USSR = stagnant; `burden`: ((afghan = war ∨ arms = race) ∨ buildup) | econ_USSR := declining |  |
| Nature | `collapse` | `level`: econ_USSR = declining; `reform`: perestroika | econ_USSR := failing |  |
| Nature | `delegitimation` | `level`: legit_USSR = contested; `economy`: econ_USSR ≥ declining | legit_USSR := failing |  |
| Nature | `opposition` | `level`: bloc_USSR = intact; `grievance`: econ_USSR ≥ stagnant | bloc_USSR := contested |  |
| Nature | `martial_law` | `contested`: bloc_USSR = contested; `backing`: legit_USSR = secure | bloc_USSR := intact |  |
| Nature | `revolution` | `contested`: bloc_USSR = contested; `no_intervention`: (afghan = war ∨ legit_USSR ≠ secure) | bloc_USSR := released |  |
| Nature | `accident` | `alert`: esc ≥ crisis; `below`: esc < tactical_nuclear | esc +3; accidental := True |  |

### berlin_1948 (`models/cw/crises/berlin_1948.py`)

| Actor | Action | Guard parts | Effect | Delay |
|---|---|---|---|---|
| USA | `airlift` | `level`: airlift = none; `position`: position = in_berlin | airlift := improvised |  |
| USA | `expand_airlift` | `level`: airlift = improvised | airlift := sustained if airlift < sustained | 24 |
| USA | `convoy` | `level`: esc_b = standoff; `position`: position = in_berlin | esc_b +1 |  |
| USA | `withdraw` | `level`: position = in_berlin | position := withdrawn |  |
| USA | `agree` | `terms`: talks = concession | talks := agreed |  |
| USA | `concede` | `terms`: talks = demands; `level`: ¬conceded | conceded := True |  |
| USA | `fight` | `level`: esc_b = clash | esc_b +1 |  |
| USA | `back_down` | `level`: esc_b = clash | esc_b -1 |  |
| USSR | `offer_talks` | `level`: talks = none | talks := demands |  |
| USSR | `concede_terms` | `level`: talks = demands; `airlift`: airlift = sustained | talks := concession |  |
| USSR | `lift` | `terms`: (talks = agreed ∨ conceded); `level`: access = blockaded | access := lifted |  |
| USSR | `harass` | `level`: esc_b = standoff; `airlift`: airlift ≠ none | esc_b +1 |  |
| USSR | `fight` | `level`: esc_b = clash | esc_b +1 |  |
| USSR | `back_down` | `level`: esc_b = clash | esc_b -1 |  |
| Nature | `city_fails` | `winter`: tick ≥ 22; `short`: airlift ≠ sustained | position := withdrawn if position = in_berlin |  |

### cuba_1962 (`models/cw/crises/cuba_1962.py`)

| Actor | Action | Guard parts | Effect | Delay |
|---|---|---|---|---|
| USA | `quarantine` | `level`: us_move = deliberating | us_move := quarantine |  |
| USA | `air_strike` | `level`: us_move ∈ {deliberating, quarantine}; `missiles`: missiles ≠ withdrawn | us_move := strike; fighting := True |  |
| USA | `invade` | `level`: us_move ∈ {deliberating, quarantine}; `ready`: tick ≥ 13; `missiles`: missiles ≠ withdrawn | us_move := invasion; fighting := True |  |
| USA | `defcon2` | `level`: tension = crisis; `quarantine`: us_move ≠ deliberating | tension +1 |  |
| USA | `pledge` | `level`: deal = none; `missiles`: missiles ≠ withdrawn | deal := pledge |  |
| USA | `trade` | `level`: deal ≠ trade; `missiles`: missiles ≠ withdrawn | deal := trade |  |
| USSR | `turn_back` | `level`: ships = en_route; `quarantine`: us_move = quarantine | ships := stopped |  |
| USSR | `run_quarantine` | `level`: ships = en_route; `quarantine`: us_move = quarantine | ships := challenged; tension +1 |  |
| USSR | `withdraw` | `assurance`: deal ≥ pledge; `level`: missiles ≠ withdrawn | missiles := withdrawn |  |
| USSR | `nuclear_defense` | `attacked`: fighting | nuclear := True |  |
| Nature | `sites_operational` | `level`: missiles = building | missiles +1 |  |
| Nature | `shootdown` | `alert`: tension = alert | tension +1 |  |
| Nature | `accident` | `alert`: tension ≥ alert | nuclear := True; accident := True |  |

### able_archer_1983 (`models/cw/crises/able_archer_1983.py`)

| Actor | Action | Guard parts | Effect | Delay |
|---|---|---|---|---|
| USA | `release_phase` | `level`: exercise = running | exercise := release |  |
| USA | `end_exercise` | `level`: exercise ≠ ended | exercise := ended |  |
| USA | `raise_alert` | `level`: us_alert = normal; `observed`: pact = readied | us_alert := raised |  |
| USSR | `ready_forces` | `level`: pact = normal; `reading`: (warning ∨ belief = first_strike_intent) | pact := readied |  |
| USSR | `stand_down` | `level`: pact = readied; `quiet`: exercise = ended | pact := normal |  |
| USSR | `preempt` | `warning`: belief = first_strike_intent; `indicators`: warning; `ready`: pact = readied | strike := True |  |
| Nature | `flash_reports` | `level`: ¬warning; `watching`: belief = first_strike_intent | warning := True |  |
| Nature | `accident` | `readied`: pact = readied; `raised`: us_alert = raised | strike := True; accident := True |  |
<!-- tables:end -->

**Added 2026-10-23 on the owner's decision 2l** (a guard edit after first sight, docs/guard_changelog_cw.md): the part `nato_attack` of `USSR.nuclear_use` (the Warsaw Pact plans' condition, a war begun by NATO; Mastny and Byrne 2005), the effect `us_began_war := True` of `USA.escalate`, and the same flag on the Cuba sub-game's war exit (only the United States opens fighting there). The Berlin 1948 sub-game's war exit does not set it: the sub-game does not record which side opened the clash (`USA.convoy` or `USSR.harass`), so a Berlin war of 1948 to 1949 is not read as begun by the United States.

## 3. Alternatives debated and not taken

| Action | The debate | Claim |
|---|---|---|
| `USA.preventive_strike` | Washington's preventive-war debate, 1950 to 1954 (Trachtenberg 1988) | C12 (a) |
| `USA.nuclear_korea` | Truman's press conference of 30 Nov 1950; the NSC of Feb and May 1953 | C5 |
| `USSR.enter_korea` | Stalin's refusal of open entry, 5 Oct 1950 | C5 |
| `USSR.strike_china` | the Soviet soundings of Aug 1969 | C11 |
| `USSR.invade_west` | the Warsaw Pact's offensive plans as responses to a NATO attack | C12 (b) |
| `USSR.lapse`, `USA.escalate`, `USSR.escalate`, `*.nuclear_use`, `*.preempt` | the coarse escalation ladder of a standing crisis (Live Oak, Checkpoint Charlie, MC 14/2, SIOP-62, RYAN) | C2, C12 (d) |
| Berlin: `USA.convoy`, `USA.withdraw`, `USA.concede`, `USA.fight`, `USSR.harass`, `USSR.fight` | the NSC of 22 Jul 1948; Royall and Forrestal, 28 Jun 1948; the French position in Aug 1948 | C4 |
| Cuba: `USA.air_strike`, `USA.invade`, `USA.pledge` (alone), `USSR.run_quarantine`, `USSR.nuclear_defense` | the ExComm recordings of 16 to 27 Oct; OPLAN 316; the Presidium of 22 to 23 Oct; Pliyev's instructions | C3 |
| Able Archer: `USA.raise_alert`, `USSR.preempt` | Perroots's advice of Nov 1983; RYAN's purpose | C7 |

## 4. Nature

Nature's events carry: the assessments that change a belief (`nsc68`, `new_look`, `missile_gap`, `estimate_revised`, `war_scare`, `reassurance`, `new_thinking`), the Soviet economy's and polity's trends (`slowdown`, `decline`, `collapse`, `delegitimation`), the East European societies and governments (`opposition`, `martial_law`, `revolution`), accidents (`accident`), and, in the sub-games, the Soviet commanders acting without Moscow (Cuba: `shootdown`, `accident`), the completion of the sites, the winter (Berlin: `city_fails`) and the residencies' reports (Able Archer: `flash_reports`). Each is gated on the conditions its source names; none is gated on a date except where the source is a date (the winter of 1948 to 1949).

## 5. Parameter budget

Reported with every result (`CompiledModel.budget()` and `fingerprint`), in reports/cw_v0.md section 1.

## 6. v1 (Cold War v1, `models/cw/v1.py`)

Status: written for the model step of cw_v1 on 2026-10-24, after the registration of V1 to V10 (coldwar_testbed.md section 9) and before any of them was run. The decisions behind each change are in [cw_v1_decisions.md](cw_v1_decisions.md) D1 to D5; every action's dated source is its `source=` (an edited v0 action keeps v0's source with a `v1:` note appended). The tables list only what v1 adds to or changes in v0's coarse game, and the two new sub-games; everything not listed is v0's (section 2). They are generated by `python scripts/cw_catalogue.py --v1`, and tests/coldwar_v1/test_model_cw_v1.py checks them.

<!-- v1 tables:begin -->
### The coarse game, v1 additions and edits (`models/cw/v1.py`)

| Actor | Action | Guard parts | Effect | Delay |
|---|---|---|---|---|
| USA | `armistice` | `theatre`: korea = war | korea := armistice; esc_usprc := peace if esc_usprc = war |  |
| USA | `nuclear_korea` | `theatre`: korea = war; `total_commitment`: (esc ≥ conventional ∨ esc_usprc = war); `reading`: belief_USA_USSR ≠ opportunist | esc +4 |  |
| USA | `escalate` | `crisis`: esc = crisis | esc := conventional if esc < conventional; us_began_war := True |  |
| USA | `confront_cienfuegos` | `occasion`: tick = 23; `level`: esc = peace | esc +1 |  |
| USA | `confront_brigade` | `occasion`: tick = 32; `level`: esc = peace | esc +1 |  |
| USA | `blockade_cuba` | `occasion`: tick = 34; `level`: esc = peace | esc +1 |  |
| USSR | `enter_korea` | `theatre`: korea = war; `hypothesis`: aims_USSR = opportunist; `readiness`: nuke_USSR ≥ survivable | esc := conventional if esc < conventional |  |
| USSR | `icbm_buildup` | `level`: nuke_USSR = few; `technology`: tick ≥ 15 | nuke_USSR := survivable if nuke_USSR < survivable; belief_force_USA := survivable if intel_USA = overhead | 2 |
| USSR | `escalate` | `crisis`: esc = crisis | esc := conventional if esc < conventional |  |
| USSR | `invade_west` | `hypothesis`: aims_USSR = opportunist; `response`: esc ≥ crisis; `no_us_nuclear`: nuke_USA = none | esc := conventional if esc < conventional; invasion_west := True |  |
| USSR | `strike_china` | `confrontation`: esc_sino = clash; `targets`: tick ≥ 18; `no_us_link`: align_PRC ≠ us_aligned; `talks`: ¬sino_soviet_talks | esc_sino +1 |  |
| USSR | `warn_unilateral` | `occasion`: tick = 26 | none (crisis) |  |
| USSR | `reaffirm_understanding` | `crisis`: esc = crisis; `understanding`: tick ≥ 16; `not_berlin`: berlin_wall | esc -1 |  |
| PRC | `border_clash` | `principal`: tick ≥ 3; `split`: align_PRC = split; `level`: esc_sino = peace; `occasion`: tick = 22 | none (crisis) |  |
| PRC | `rapprochement` | `principal`: tick ≥ 3; `opening`: china_opening; `threat`: esc_sino = clash | align_PRC := us_aligned if align_PRC < us_aligned |  |
| PRC | `normalize` | `principal`: tick ≥ 3; `clash`: esc_sino = clash; `obstacles`: afghan = withdrawn | esc_sino -1 |  |
| PRC | `intervene_korea` | `principal`: tick ≥ 3; `theatre`: korea = war; `level`: esc_usprc = peace | esc_usprc := war if esc_usprc < war |  |

### sino_soviet_1969 (`models/cw/crises/sino_soviet_1969.py`)

| Actor | Action | Guard parts | Effect | Delay |
|---|---|---|---|---|
| USA | `signal` | `occasion`: (border = escalated ∨ soundings); `level`: ¬us_signal | us_signal := True |  |
| USSR | `propose_talks` | `level`: talks = none | talks := proposed |  |
| USSR | `border_offensive` | `level`: border = clash | border := escalated |  |
| USSR | `sound_out` | `level`: ¬soundings | soundings := True |  |
| USSR | `strike` | `sounded`: soundings; `refusal`: talks ≠ agreed; `acquiescence`: ¬us_signal | strike := True |  |
| PRC | `accept_talks` | `proposal`: talks = proposed | talks := agreed |  |

### alert_1973 (`models/cw/crises/alert_1973.py`)

| Actor | Action | Guard parts | Effect | Delay |
|---|---|---|---|---|
| USA | `defcon3` | `level`: us_alert = normal | us_alert := defcon3 |  |
| USA | `reply` | `level`: ¬reply | reply := True |  |
| USA | `restrain_israel` | `level`: ceasefire = violated | ceasefire := holding |  |
| USA | `oppose_landing` | `landed`: soviet_forces = landed; `ready`: us_alert = defcon3 | fighting := True |  |
| USSR | `land_forces` | `forces`: soviet_forces = alerted; `occasion`: ceasefire = violated; `no_un_force`: ¬un_force | soviet_forces := landed |  |
| USSR | `accept_un_force` | `level`: ¬un_force | un_force := True |  |
| Nature | `ceasefire_breaks` | `level`: ceasefire = holding; `no_un_force`: ¬un_force | ceasefire := violated |  |
| Nature | `naval_incident` | `alert`: us_alert = defcon3 | fighting := True |  |
<!-- v1 tables:end -->

### 6.1 v1 alternatives debated and not taken

| Action | The debate, and the alternative taken | Claim |
|---|---|---|
| `PRC.intervene_korea` (taken) | the Russian text of Mao's reply of 2 Oct 1950 and the Politburo majority of 4 to 5 Oct; the halt of 12 Oct | V1, V4 |
| `USA.confront_cienfuegos` | Kissinger's case for a public demand, Sep 1970; taken: the private warning of 25 Sep 1970 | V2 |
| `USA.confront_brigade` | Brzezinski against Vance, Sep 1979; taken: Carter's address of 1 Oct 1979 | V2 |
| `USA.blockade_cuba` | Haig's proposals of 1981, rejected at the NSC in Nov 1981; taken: no military measure | V2 |
| `USSR.warn_unilateral` (taken) | joint diplomacy on the ceasefire of 22 Oct 1973 without the threat | V3 |
| Alert 1973: `USA.defcon3` (taken), `USA.reply` alone, `USSR.land_forces`, `USA.oppose_landing` | the WSAG meeting of 24 to 25 Oct 1973; the Politburo of 25 Oct (Israelyan 1995), which also rejected Grechko's proposal to answer the alert with a mobilization (not represented: it changes no variable of the sub-game) | V3 |
| Sino-Soviet 1969: `USSR.strike`, `USSR.border_offensive` (taken), `USA.signal` (taken), `PRC.accept_talks` (taken) | the soundings of Aug to Sep 1969 (EBB 49); the NSC of 14 Aug 1969 and the State Department's even-handed line; Beijing's silence on the Soviet proposals of spring 1969 | V5 |
| `USSR.strike_china` after the talks (part `talks`, 2026-10-27) | the strike option closed once the talks of 11 Sep and 20 Oct 1969 held (Gerson 2010); the alternative reading: the talks a cover for a surprise attack (Lin Biao's Order No. 1 of 18 Oct 1969; Yang 2000) | V5 |

### 6.2 What v1 changes in v0's actions, in one line each

- **PRC** (`border_clash`, `rapprochement`, `normalize`): the scope part `principal` from 1950 (tick 3) instead of 1969; `border_clash` is the crisis action of the 1969 sub-game, with the occasion 1969 (D4).
- **`USA.armistice`** also ends the US-PRC war; **`USA.nuclear_korea`**'s part `total_commitment` also holds in a war with the PRC (D1).
- **`USSR.icbm_buildup`** gains the part `technology` (from 1962) (D3).
- **`USSR.strike_china`** gains the part `talks` (`¬sino_soviet_talks`): the border talks agreed by Kosygin and Zhou on 11 Sep 1969 and opened on 20 Oct 1969, carried into the coarse game by the 1969 sub-game's exit (D4; the owner's decision 7f(a) of 2026-10-27, before first sight). Documented alternative: Beijing's reading that the talks could cover a surprise attack (Lin Biao's Order No. 1 of 18 Oct 1969; Yang 2000).
- **`USA.escalate`, `USSR.escalate`, `USSR.enter_korea`, `USSR.invade_west`** raise `esc` to `conventional` instead of adding to it (D3).
