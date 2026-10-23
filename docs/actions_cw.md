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
| USA | `escalate` | `crisis`: esc = crisis | esc +1 |  |
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
| USSR | `nuclear_use` | `war`: esc = conventional; `means`: nuke_USSR ≥ few | esc +1 |  |
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
