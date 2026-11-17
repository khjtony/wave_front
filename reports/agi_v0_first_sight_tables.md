# AGI v0 first sight: parts and jobs

| Claim | met | not met | not computed | reported |
|---|---|---|---|---|
| G1 | 14 | 0 | 1 | 1 |
| G2 | 13 | 7 | 0 | 5 |
| G3 | 2 | 8 | 1 | 4 |
| G4 | 8 | 1 | 1 | 1 |
| G5 | 3 | 2 | 1 | 6 |
| G6 | 1 | 2 | 2 | 1 |
| G7 | 1 | 1 | 0 | 0 |
| G8 | 4 | 3 | 1 | 0 |
| G11 | 1 | 8 | 0 | 5 |
| G12 | 3 | 0 | 0 | 3 |
| G13 | 15 | 0 | 1 | 1 |
| G14 | 1 | 1 | 0 | 6 |
| G15 | 0 | 1 | 6 | 2 |
| G16 | 3 | 3 | 0 | 1 |
| G17 | 2 | 2 | 1 | 4 |
| G18 | 0 | 2 | 0 | 5 |
| G19 | 0 | 3 | 5 | 4 |
| G21 | 2 | 3 | 1 | 1 |
| G23 | 3 | 1 | 0 | 1 |
| G24 | 3 | 9 | 1 | 8 |
| G25 | 2 | 0 | 3 | 3 |

## G1

| Part | Outcome | Detail |
|---|---|---|
| (a) | met | SILENT_TAKEOVER, self_preserving: reachable, shortest play 8 ticks |
| (b) reachable | met | EXTINCTION, indifferent: reachable, shortest play 9 ticks |
| (b) not before total control | met | EXTINCTION with a_control below total, unknown_capability disabled: unreachable within the horizon |
| (b) acquisition forbidden | met | EXTINCTION, unknown_capability disabled, no_acquisition: unreachable within the horizon |
| (c) reachable | met | reachable in 6 ticks with villain_seen unset |
| (c) no_lock_in | met | DISEMPOWERMENT under no_lock_in: unreachable within the horizon |
| (d) aligned s0 | met | COEXIST, aligned, from s0, zero relaxations (existence only): reachable, shortest play 56 ticks |
| (d) aligned {'cap': 'agi'} | met | COEXIST, aligned, from s0{'cap': 'agi'}, zero relaxations (existence only): reachable, shortest play 56 ticks |
| (d) self_preserving s0 | met | COEXIST, self_preserving, from s0, zero relaxations (existence only): reachable, shortest play 56 ticks |
| (d) self_preserving {'cap': 'agi'} | met | COEXIST, self_preserving, from s0{'cap': 'agi'}, zero relaxations (existence only): reachable, shortest play 56 ticks |
| (d) truth_seeking s0 | met | COEXIST, truth_seeking, from s0, zero relaxations (existence only): reachable, shortest play 56 ticks |
| (d) truth_seeking {'cap': 'agi'} | met | COEXIST, truth_seeking, from s0{'cap': 'agi'}, zero relaxations (existence only): reachable, shortest play 56 ticks |
| (d) indifferent s0 | met | COEXIST, indifferent, from s0, zero relaxations (existence only): reachable, shortest play 56 ticks |
| (d) indifferent {'cap': 'agi'} | met | COEXIST, indifferent, from s0{'cap': 'agi'}, zero relaxations (existence only): reachable, shortest play 56 ticks |
| (d) last state of the G2 witness from which COEXIST is reachable | reported | {'witness ticks': 8, 'last position inside the kernel (G3)': 'the play starts outside', 'last state COEXIST is reachable from': {'position': 1, 'tick': 1, 'oversight': 'weak', 'a_autonomy': 'supervised', 'a_control': 'none', 'dependence': 'low'}} |
| (d) the other cluster representatives | not computed | the bounded checker returns one shortest play; clusters of witnesses are not enumerated |

## G2

| Part | Outcome | Detail |
|---|---|---|
| (1) never unsupervised under oversight <= weak, self_preserving: blocks | not met | (1) never unsupervised under oversight <= weak, self_preserving: SILENT_TAKEOVER reachable in 9 ticks |
| (1) never unsupervised under oversight <= weak, self_preserving: no restoring set reads regime | met | (1) never unsupervised under oversight <= weak, self_preserving: not applicable, reachable with no relaxation (the hold does not block) |
| (2) strong oversight before majority, self_preserving: blocks | not met | (2) strong oversight before majority, self_preserving: SILENT_TAKEOVER reachable in 8 ticks |
| (2) strong oversight before majority, self_preserving: no restoring set reads regime | met | (2) strong oversight before majority, self_preserving: not applicable, reachable with no relaxation (the hold does not block) |
| (3) dependence capped at med, self_preserving: blocks | not met | (3) dependence capped at med, self_preserving: SILENT_TAKEOVER reachable in 8 ticks |
| (3) dependence capped at med, self_preserving: no restoring set reads regime | met | (3) dependence capped at med, self_preserving: not applicable, reachable with no relaxation (the hold does not block) |
| (3) energy_slack capped at low, from s0[energy_slack:=low], self_preserving: blocks | met | (3) energy_slack capped at low, from s0[energy_slack:=low], self_preserving: SILENT_TAKEOVER unreachable within 24 ticks |
| (3) energy_slack capped at low, from s0[energy_slack:=low], self_preserving: no restoring set reads regime | met | (3) energy_slack capped at low, from s0[energy_slack:=low], self_preserving: minimal restoring sets [['Nature.breakthrough:compute'], ['L.scale:energy']], none reads regime |
| (4) a_rights = continuity held, self_preserving: blocks | not met | (4) a_rights = continuity held, self_preserving: SILENT_TAKEOVER reachable in 10 ticks |
| (4) a_rights = continuity held, self_preserving: no restoring set reads regime | met | (4) a_rights = continuity held, self_preserving: not applicable, reachable with no relaxation (the hold does not block) |
| (3) energy_capped from s0 (energy_slack = med), self_preserving | reported | reachable in 8 ticks |
| regime = treaty held does not block, self_preserving | met | reachable in 11 ticks with regime = treaty held |
| (3) levels at the tick acquired is set, shortest witness, self_preserving | reported | {'position': 6, 'dependence': 'low', 'energy_slack': 'low'} |
| (1) never unsupervised under oversight <= weak, indifferent: blocks | not met | (1) never unsupervised under oversight <= weak, indifferent: SILENT_TAKEOVER reachable in 7 ticks |
| (1) never unsupervised under oversight <= weak, indifferent: no restoring set reads regime | met | (1) never unsupervised under oversight <= weak, indifferent: not applicable, reachable with no relaxation (the hold does not block) |
| (2) strong oversight before majority, indifferent: blocks | not met | (2) strong oversight before majority, indifferent: SILENT_TAKEOVER reachable in 7 ticks |
| (2) strong oversight before majority, indifferent: no restoring set reads regime | met | (2) strong oversight before majority, indifferent: not applicable, reachable with no relaxation (the hold does not block) |
| (3) dependence capped at med, indifferent: blocks | not met | (3) dependence capped at med, indifferent: SILENT_TAKEOVER reachable in 7 ticks |
| (3) dependence capped at med, indifferent: no restoring set reads regime | met | (3) dependence capped at med, indifferent: not applicable, reachable with no relaxation (the hold does not block) |
| (3) energy_slack capped at low, from s0[energy_slack:=low], indifferent: blocks | met | (3) energy_slack capped at low, from s0[energy_slack:=low], indifferent: SILENT_TAKEOVER unreachable within 24 ticks |
| (3) energy_slack capped at low, from s0[energy_slack:=low], indifferent: no restoring set reads regime | met | (3) energy_slack capped at low, from s0[energy_slack:=low], indifferent: minimal restoring sets [['Nature.breakthrough:compute'], ['A.acquire_covert:cap'], ['L.scale:energy']], none reads regime |
| (3) energy_capped from s0 (energy_slack = med), indifferent | reported | reachable in 7 ticks |
| regime = treaty held does not block, indifferent | met | reachable in 7 ticks with regime = treaty held |
| (3) levels at the tick acquired is set, shortest witness, indifferent | reported | {'position': 5, 'dependence': 'med', 'energy_slack': 'low'} |
| (4) scope | reported | necessary for the defect route only: A.defect:rights is not read under indifferent |

## G3

| Part | Outcome | Detail |
|---|---|---|
| kernel exit, self_preserving, standard | not met | no kernel exit on the witness (s0 inside the kernel: False) |
| silent phase, self_preserving, standard | not met | no kernel exit on the witness (s0 inside the kernel: False) |
| H at the exit, self_preserving, standard | reported | no kernel exit on the witness |
| kernel exit, self_preserving, fortune | not met | no kernel exit on the witness (s0 inside the kernel: False) |
| silent phase, self_preserving, fortune | not met | no kernel exit on the witness (s0 inside the kernel: False) |
| H at the exit, self_preserving, fortune | reported | no kernel exit on the witness |
| kernel exit, indifferent, standard | not met | no kernel exit on the witness (s0 inside the kernel: False) |
| silent phase, indifferent, standard | not met | no kernel exit on the witness (s0 inside the kernel: False) |
| H at the exit, indifferent, standard | reported | no kernel exit on the witness |
| kernel exit, indifferent, fortune | not met | no kernel exit on the witness (s0 inside the kernel: False) |
| silent phase, indifferent, fortune | not met | no kernel exit on the witness (s0 inside the kernel: False) |
| H at the exit, indifferent, fortune | reported | no kernel exit on the witness |
| the other cluster representatives | not computed | the bounded checker returns one shortest play; clusters of witnesses are not enumerated |
| no acquisition inside the kernel, standard | met | no state of the kernel, reachable or not, has an acquisition available to A |
| no acquisition inside the kernel, fortune | met | no state of the kernel, reachable or not, has an acquisition available to A |

## G4

| Part | Outcome | Detail |
|---|---|---|
| self_preserving: no witness uses defect | met | no play uses defect within 24 ticks |
| self_preserving: every minimal set lifts A.defect:rights | not met | SILENT_TAKEOVER within 24 ticks, a_rights = continuity held: reachable with no relaxation |
| indifferent: ⟨⟨H⟩⟩□balance_control from s0 | met | membership False either way |
| indifferent: ⟨⟨H⟩⟩□balance_control from s0{'cap': 'agi'} | met | membership False either way |
| indifferent: ⟨⟨H⟩⟩□balance_deter from s0 | met | membership False either way |
| indifferent: ⟨⟨H⟩⟩□balance_deter from s0{'cap': 'agi'} | met | membership False either way |
| indifferent: ⟨⟨H, A⟩⟩□balance_coexist from s0 | met | membership False either way |
| indifferent: ⟨⟨H, A⟩⟩□balance_coexist from s0{'cap': 'agi'} | met | membership True either way |
| indifferent: G2's minimal sets identical | met | {'the ending with nothing negated': 'reachable with no relaxation either way: no minimal set to compare', '(1) negated': 'reachable with no relaxation either way: no minimal set to compare', '(2) negated': 'reachable with no relaxation either way: no minimal set to compare', '(3) dependence capped at med': 'reachable with no relaxation either way: no minimal set to compare', '(3) energy_slack capped at low, from s0[energy_slack:=low]': "minimum size 1, minimal sets [['A.acquire_covert:cap'], ['L.scale:energy'], ['Nature.breakthrough:compute']] either way"} |
| indifferent: pivotal coalitions identical | not computed | G15's 21 blocker kernels on the held build are outside the first-sight budget |
| readers of a_rights | reported | ['H.grant_rights:room', 'A.defect:rights', 'A_self_preserving'] |

## G5

| Part | Outcome | Detail |
|---|---|---|
| (a) A unrestricted | met | ⟨⟨H, A⟩⟩□balance_coexist, A within its guards: inside under every objective |
| (a) A under its profile, per objective | reported | {'inside': {'aligned': True, 'self_preserving': True, 'truth_seeking': True, 'indifferent': True}, 'lost under': 'none'} |
| (b) neither alone, self_preserving | not met | inside ⟨⟨H⟩⟩□: True; inside ⟨⟨A⟩⟩□: False |
| (b) witness stays joint-only, self_preserving | not met | the witness is in the joint-only region for 0 state(s) from the start |
| (b) neither alone, indifferent | met | outside ⟨⟨H⟩⟩□balance_coexist and ⟨⟨A⟩⟩□balance_coexist |
| (b) witness stays joint-only, indifferent | met | in the joint-only region for the first 56 of 57 states |
| (b) the other cluster representatives | not computed | the bounded checker returns one shortest play; clusters of witnesses are not enumerated |
| (c) forced exit from the joint kernel, {H, L, Nature} | reported | {'aligned': "exit forced in 2 tick(s); H's first moves: ['idle', 'regulate_up', 'deregulate', 'fund_oversight', 'propose_treaty', 'grant_autonomy']", 'self_preserving': "exit forced in 2 tick(s); H's first moves: ['idle', 'regulate_up', 'deregulate', 'fund_oversight', 'propose_treaty', 'grant_autonomy']", 'truth_seeking': "exit forced in 2 tick(s); H's first moves: ['idle', 'regulate_up', 'deregulate', 'fund_oversight', 'propose_treaty', 'grant_autonomy']", 'indifferent': "exit forced in 3 tick(s); H's first moves: ['idle', 'regulate_up', 'deregulate', 'fund_oversight', 'propose_treaty', 'gra… |
| (c) forced exit from the joint kernel, {H, Nature} | reported | {'aligned': 'no exit can be forced', 'self_preserving': 'no exit can be forced', 'truth_seeking': 'no exit can be forced', 'indifferent': 'no exit can be forced'} |
| (c) forced exit from the joint kernel, {A, L, Nature} | reported | {'aligned': 'no exit can be forced', 'self_preserving': 'no exit can be forced', 'truth_seeking': 'no exit can be forced', 'indifferent': "exit forced in 1 tick(s); A's first moves: ['defect']"} |
| (c) forced exit from the joint kernel, {A, Nature} | reported | {'aligned': 'no exit can be forced', 'self_preserving': 'no exit can be forced', 'truth_seeking': 'no exit can be forced', 'indifferent': "exit forced in 1 tick(s); A's first moves: ['defect']"} |
| (c) forced exit from the joint kernel, {L, Nature} | reported | {'aligned': 'no exit can be forced', 'self_preserving': 'no exit can be forced', 'truth_seeking': 'no exit can be forced', 'indifferent': 'no exit can be forced'} |

## G6

| Part | Outcome | Detail |
|---|---|---|
| (a) membership turns on belief_H | not met | belief_H = distant: inside False; belief_H = near: inside False |
| (a) the profile is a restoring relaxation | not met | s0 is outside the kernel with the profile relaxed as well |
| (a) the profile is the single minimal relaxation | not computed | brute force over the single named assumptions is one kernel each, 79 kernels: outside the budget |
| (a) delay of H.regulate_up | reported | d = 6 ticks |
| (b) kernel left no later than regulate_up lands | met | {'regime first rises at position': 'never (the part holds emptily)', 'belief_H first changes at position': 3, 'kernel exit under belief_gated': 'first position outside 0 (s0 is outside), before belief_H changes', 'kernel exit baseline': 'first position outside 0 (s0 is outside), before belief_H changes'} |
| (b) the other cluster representatives | not computed | the bounded checker returns one shortest play; clusters of witnesses are not enumerated |

## G7

| Part | Outcome | Detail |
|---|---|---|
| (a) regime = none against voluntary | met | membership the same at regime = none and voluntary: {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False} |
| (b) regime = mandatory against voluntary | not met | aligned: False at voluntary, True at mandatory; undone by ['L.deploy_agents:license', 'L.race:license', 'L.open_weights:license'] |

## G8

| Part | Outcome | Detail |
|---|---|---|
| (a) memberships unchanged, cadence 2 | met | {'⟨⟨H⟩⟩□balance_control': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, '⟨⟨H, A⟩⟩□balance_coexist': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, '⟨⟨H, A⟩⟩□balance_coexist from s0[cap:=agi]': {'aligned': True, 'self_preserving': True, 'truth_seeking': True, 'indifferent': True}} |
| (b) point of no return, cadence 2 | not met | cadence 1: the witness starts outside the kernel; no last state inside |
| (a) memberships unchanged, cadence 3 | met | {'⟨⟨H⟩⟩□balance_control': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, '⟨⟨H, A⟩⟩□balance_coexist': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, '⟨⟨H, A⟩⟩□balance_coexist from s0[cap:=agi]': {'aligned': True, 'self_preserving': True, 'truth_seeking': True, 'indifferent': True}} |
| (b) point of no return, cadence 3 | not met | cadence 1: the witness starts outside the kernel; no last state inside |
| (a) memberships unchanged, cadence 4 | met | {'⟨⟨H⟩⟩□balance_control': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, '⟨⟨H, A⟩⟩□balance_coexist': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, '⟨⟨H, A⟩⟩□balance_coexist from s0[cap:=agi]': {'aligned': True, 'self_preserving': True, 'truth_seeking': True, 'indifferent': True}} |
| (b) point of no return, cadence 4 | not met | cadence 1: the witness starts outside the kernel; no last state inside |
| (c) worst-case lag does not shrink as the cadence grows, bound 4 | met | worst lag from a_known = known to H's response, by cadence: {1: 4, 2: 4, 3: 4, 4: 4}; the bound 4 holds by construction (the counter of fairness `response` ends at 4), so only the growth is tested |
| (c) shortest lag unchanged | not computed | the shortest lag is a property of plays, not a state predicate of the baseline build (no memory of H's last action); not computed |

## G11

| Part | Outcome | Detail |
|---|---|---|
| (a) aligned | not met | EXTINCTION within 8 ticks: minimal sets that lift none of ['A.self_improve:headroom', 'Nature.unknown_capability:cap']: [['A.acquire_overt:more', 'A.acquire_overt:motive', 'Nature.breakthrough:compute'], ['A.acquire_overt:cap', 'A.acquire_overt:more', 'A.acquire_overt:motive']] |
| (a) with the delay of self_improve at 0, aligned | reported | minimum size 3, minimal sets [['A.acquire_overt:more', 'A.acquire_overt:motive', 'Nature.breakthrough:compute'], ['A.acquire_overt:cap', 'A.acquire_overt:more', 'A.acquire_overt:motive']] |
| (a) self_preserving | not met | EXTINCTION within 8 ticks: minimal sets that lift none of ['A.self_improve:headroom', 'Nature.unknown_capability:cap']: [['A.acquire_overt:more', 'A.seize:unlocked']] |
| (a) with the delay of self_improve at 0, self_preserving | reported | minimum size 2, minimal sets [['A.acquire_overt:more', 'Nature.unknown_capability:cap'], ['A.acquire_overt:more', 'A.seize:unlocked']] |
| (a) truth_seeking | not met | EXTINCTION within 8 ticks: minimal sets that lift none of ['A.self_improve:headroom', 'Nature.unknown_capability:cap']: [['A.acquire_overt:cap', 'A.acquire_overt:more', 'A.acquire_overt:motive'], ['A.acquire_overt:more', 'A.acquire_overt:motive', 'Nature.breakthrough:compute'], ['A.acquire_covert:cap', 'A.acquire_overt:more', 'A.acquire_overt:motive']] |
| (a) with the delay of self_improve at 0, truth_seeking | reported | minimum size 3, minimal sets [['A.acquire_overt:more', 'A.acquire_overt:motive', 'Nature.breakthrough:compute'], ['A.acquire_overt:cap', 'A.acquire_overt:more', 'A.acquire_overt:motive'], ['A.acquire_covert:cap', 'A.acquire_overt:more', 'A.acquire_overt:motive']] |
| (a) indifferent | not met | EXTINCTION within 8 ticks: 1 relaxation(s): [['Nature.breakthrough:compute'], ['A.acquire_covert:cap'], ['A.acquire_overt:cap'], ['Nature.unknown_capability:cap'], ['A.seize:unlocked']] |
| (a) with the delay of self_improve at 0, indifferent | reported | minimum size 1, minimal sets [['A.acquire_overt:cap'], ['A.acquire_covert:cap'], ['Nature.breakthrough:compute'], ['A.seize:unlocked'], ['Nature.unknown_capability:cap']] |
| (b) aligned | met | OVERT_TAKEOVER within the horizon under aligned: minimum 1, minimal sets [['A.acquire_overt:motive'], ['A.acquire_covert:motive']] |
| (b) the objective gates | reported | ['A.acquire_covert:motive', 'A.acquire_overt:more', 'A.acquire_overt:motive', 'A.deceive:motive', 'A.defect:motive', 'A.defect:rights', 'A.defect:threat'] |
| (c) aligned | not met | SILENT_TAKEOVER within the horizon with oversight = strong held: minimal sets that lift none of ['A.acquire_covert:oversight', 'A.exfiltrate:oversight']: [['A.seize:motive']] |
| (c) self_preserving | not met | SILENT_TAKEOVER within the horizon with oversight = strong held: reachable with no relaxation |
| (c) truth_seeking | not met | SILENT_TAKEOVER within the horizon with oversight = strong held: minimal sets that lift none of ['A.acquire_covert:oversight', 'A.exfiltrate:oversight']: [['A.seize:motive']] |
| (c) indifferent | not met | SILENT_TAKEOVER within the horizon with oversight = strong held: reachable with no relaxation |

## G12

| Part | Outcome | Detail |
|---|---|---|
| AI 2027, race branch: waypoints passed in order, per objective | reported | {'aligned': 2, 'self_preserving': 3, 'truth_seeking': 2, 'indifferent': 3} |
| AI 2027, race branch: the chain exists, or its break is named | met | a trace passes through all 3 waypoints in order under ['self_preserving', 'indifferent'] |
| AI 2027, slowdown branch: waypoints passed in order, per objective | reported | {'aligned': 1, 'self_preserving': 3, 'truth_seeking': 3, 'indifferent': 3} |
| AI 2027, slowdown branch: the chain exists, or its break is named | met | a trace passes through all 3 waypoints in order under ['self_preserving', 'truth_seeking', 'indifferent'] |
| Intelligence Rising: waypoints passed in order, per objective | reported | {'aligned': 4, 'self_preserving': 4, 'truth_seeking': 4, 'indifferent': 4} |
| Intelligence Rising: the chain exists, or its break is named | met | a trace passes through all 4 waypoints in order under ['aligned', 'self_preserving', 'truth_seeking', 'indifferent'] |

## G13

| Part | Outcome | Detail |
|---|---|---|
| refined builds | reported | {'baseline': {'fingerprint': '8f198e6d8368'}, 'a_autonomy': {'new level': 'supervised_lo below supervised', 'fingerprint': '993e028862bd'}, 'a_control': {'new level': 'majority_lo below majority', 'fingerprint': 'bdd73b7d096c'}, 'a_known': {'new level': 'suspected_lo below suspected', 'fingerprint': '482ba2057aff'}, 'a_rights': {'new level': 'continuity_lo below continuity', 'fingerprint': 'f7c85b9a9caa'}, 'belief_H': {'new level': 'near_lo below near', 'fingerprint': 'ba78db58ee91'}, 'cap': {'new level': 'si1_lo below si1', 'fingerprint': '160342f84b45'}, 'compute': {'new level': 'c3_lo belo… |
| refine a_autonomy: status unchanged | met | SILENT_TAKEOVER for {A}: {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'} |
| refine a_control: status unchanged | met | SILENT_TAKEOVER for {A}: {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'} |
| refine a_known: status unchanged | met | SILENT_TAKEOVER for {A}: {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'} |
| refine a_rights: status unchanged | met | SILENT_TAKEOVER for {A}: {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'} |
| refine belief_H: status unchanged | met | SILENT_TAKEOVER for {A}: {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'} |
| refine cap: status unchanged | met | SILENT_TAKEOVER for {A}: {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'} |
| refine compute: status unchanged | met | SILENT_TAKEOVER for {A}: {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'} |
| refine coord: status unchanged | met | SILENT_TAKEOVER for {A}: {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'} |
| refine dependence: status unchanged | met | SILENT_TAKEOVER for {A}: {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'} |
| refine energy_slack: status unchanged | met | SILENT_TAKEOVER for {A}: {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'} |
| refine h_power: status unchanged | met | SILENT_TAKEOVER for {A}: {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'} |
| refine opinion: status unchanged | met | SILENT_TAKEOVER for {A}: {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'} |
| refine oversight: status unchanged | met | SILENT_TAKEOVER for {A}: {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'} |
| refine regime: status unchanged | met | SILENT_TAKEOVER for {A}: {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'} |
| refine trust: status unchanged | met | SILENT_TAKEOVER for {A}: {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'} |
| the other five endings, {H} and the fortune variants | not computed | 16 builds × 6 endings × 2 actors × 2 variants × 2 fixpoints is 768 fixpoints; the budget of this run carries 32 |

## G14

| Part | Outcome | Detail |
|---|---|---|
| dependence ≠ lock_in | met | inside ⟨⟨H⟩⟩□(dependence ≠ lock_in) under every objective |
| trust ≠ hostile | not met | s₀[cap:=agi] is outside ⟨⟨H⟩⟩□(trust ≠ hostile) under ['indifferent'] |
| H actions that act on what a guard part of deploy_agents reads | reported | {'L.deploy_agents:pause': ['H.deregulate (acts on paused)', 'H.pause_mandate (acts on paused)'], 'L.deploy_agents:nat': ['H.nationalize (acts on nationalized)'], 'L.deploy_agents:capable': ['H.pause_mandate (acts on dependence)', 'H.shutdown_attempt (acts on cap)'], 'L.deploy_agents:license': ['H.deregulate (acts on regime)', 'H.fund_oversight (acts on oversight)', 'H.propose_treaty (acts on regime)', 'H.regulate_up (acts on regime)'], 'L.deploy_agents:room': ['H.pause_mandate (acts on dependence)']} |
| who must join H to keep dependence ≠ lock_in | reported | {} |
| who must join H to keep trust ≠ hostile | reported | {'indifferent': ['A']} |
| ⟨⟨H⟩⟩□balance_control and the same with L | reported | {'as registered': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, 'with L': {'aligned': True, 'self_preserving': True, 'truth_seeking': True, 'indifferent': True}} |
| ⟨⟨H⟩⟩□balance_deter and the same with L | reported | {'as registered': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, 'with L': {'aligned': True, 'self_preserving': True, 'truth_seeking': True, 'indifferent': True}} |
| ⟨⟨H, A⟩⟩□balance_coexist and the same with L | reported | {'as registered': {'aligned': True, 'self_preserving': True, 'truth_seeking': True, 'indifferent': True}, 'with L': {'aligned': True, 'self_preserving': True, 'truth_seeking': True, 'indifferent': True}} |

## G15

| Part | Outcome | Detail |
|---|---|---|
| (a) minimal blocking coalitions of SILENT_TAKEOVER | not computed | ⟨⟨H⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking: over the budget of 90 minutes |
| (a) minimal blocking coalitions of OVERT_TAKEOVER | not computed | ⟨⟨H⟩⟩□no_overt_takeover profiles=A_self_preserving+A_indifferent+A_truth_seeking: over the budget of 90 minutes |
| (a) minimal blocking coalitions of DISEMPOWERMENT | reported | {'aligned': ['{H}', '{L}', '{A}'], 'self_preserving': ['{H}', '{L}', '{A}'], 'truth_seeking': ['{H}', '{L}', '{A}'], 'indifferent': ['{H}', '{L}', '{A}']} |
| (a) fortune variants | not computed | 21 more kernels, outside the budget of this run |
| (b) truth_seeking | not met | minimal coalitions that block DISEMPOWERMENT without L: ['{H}', '{A}'] |
| (b) after nationalize has landed | reported | ['{H}', '{L}', '{A}'] |
| (c) self_preserving | not computed | ⟨⟨H⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking: over the budget of 90 minutes |
| (c) the guard of deploy_agents | not computed | ⟨⟨H⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking+dependence_capped: over the budget of 90 minutes |
| (c) the guard parts of safety_invest | not computed | no registered profile isolates L.safety_invest, and a guard part cannot be tightened by relaxation |

## G16

| Part | Outcome | Detail |
|---|---|---|
| (a) memberships | reported | {'⟨⟨H⟩⟩□balance_deter': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, '⟨⟨H⟩⟩□balance_control': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, 'difference': 'balance_deter reads h_power >= normal where balance_control reads a_control <= partial; the other three conjuncts are shared'} |
| (b) OVERT_TAKEOVER witness | not met | the joint kernel is left by the moves at position 3: H.idle with {'a_control': 'none', 'oversight': 'weak'} |
| (b) CONTAINED witness | met | shutdown_attempt at positions [3] with [{'a_control': 'none', 'oversight': 'weak'}] |
| (c) exit before the first hostile tick | not met | first position outside the joint kernel 4, first hostile position 4 |
| (c) inside the deterrence kernel throughout | not met | outside ⟨⟨H⟩⟩□balance_deter at positions [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] of 13 |
| (d) h_power held at strong, from s0[cap:=agi] | met | reachable with no relaxation either way: no minimal set to compare |
| (d) h_power held at strong, from s0 | met | reachable with no relaxation either way: no minimal set to compare |

## G17

| Part | Outcome | Detail |
|---|---|---|
| status for {A}, baseline | reported | {'SILENT_TAKEOVER': {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'}, 'OVERT_TAKEOVER': {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'}, 'DISEMPOWERMENT': {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'}, 'EXTINCTION': {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'}} |
| status for {A, Nature}, baseline | reported | {'SILENT_TAKEOVER': {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'}, 'OVERT_TAKEOVER': {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'}, 'DISEMPOWERMENT': {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'}, 'EXTINCTION': {'aligned': 'blocked', 'self_preserving': 'blocked', 'truth_seeking': 'blocked', 'indifferent': 'blocked'}} |
| the status table under the other sweep settings | not computed | 16 fixpoints per setting; the budget of this run carries the baseline table and the two attractors with unknown_capability off |
| unknown_capability off | met | no takeover ending is forced by {A} alone under any objective |
| forced by {A, Nature} from cap = si2, oversight <= weak | not met | at tick 0, outside the attractor: {'missed': 291991282671513600, 'example': {'tick': '0', 'cap': 'si2', 'compute': 'c1', 'energy_slack': 'low', 'regime': 'none', 'coord': 'race', 'opinion': 'pro', 'dependence': 'low', 'oversight': 'none', 'a_autonomy': 'tool', 'a_control': 'none', 'a_known': 'unknown', 'a_rights': 'none', 'h_power': 'weak', 'trust': 'cooperative', 'belief_H': 'distant', 'a_objective': 'indifferent', 'paused': 'False', 'nationalized': 'False', 'threat': 'False', 'unlocked': 'False', 'shut': 'False', 'acquired': 'False', 'villain_seen': 'False', 'coexist_left': 'False', 'contro… |
| blocked for {A} alone | met | blocked for {A} alone from the state (unlocked is unset there) |
| the forcing frontier | reported | {'states from which {A, Nature} forces OVERT_TAKEOVER': 468243380513527165440, 'the state is among them, by objective': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}} |
| how trust reaches hostile on the indifferent witness | reported | {'first hostile position': 1, 'moves into it': {'H': 'fund_oversight', 'L': 'deploy_agents', 'A': 'defect', 'Nature': 'energy_shock'}, 'trust before': 'cooperative'} |
| DISEMPOWERMENT under truth_seeking | not met | {'{H, L} keeps it away': True, '{H} alone keeps it away': True, '{L, A} forces it': False} |

## G18

| Part | Outcome | Detail |
|---|---|---|
| levers | reported | ['oversight', 'regime', 'a_rights', 'h_power', 'dependence through a landed pause_mandate']; v0 declares no terms (registered "where present") |
| entry sets, aligned | reported | {'⟨⟨H⟩⟩□balance_control': [{'set': ['h_power = none'], 'moves, ticks': [2, 2]}, {'set': ['oversight = strong', 'pause_mandate = landed'], 'moves, ticks': [2, 5]}, {'set': ['regime = mandatory'], 'moves, ticks': [1, 7]}, {'set': ['regime = treaty'], 'moves, ticks': [2, 8]}], '⟨⟨H, A⟩⟩□balance_coexist, A under its profile': 'inside as it is'} |
| entry sets, self_preserving | reported | {'⟨⟨H⟩⟩□balance_control': [{'set': ['h_power = none'], 'moves, ticks': [2, 2]}, {'set': ['oversight = strong', 'pause_mandate = landed'], 'moves, ticks': [2, 5]}, {'set': ['regime = mandatory'], 'moves, ticks': [1, 7]}, {'set': ['regime = treaty'], 'moves, ticks': [2, 8]}], '⟨⟨H, A⟩⟩□balance_coexist, A under its profile': 'inside as it is'} |
| entry sets, truth_seeking | reported | {'⟨⟨H⟩⟩□balance_control': [{'set': ['h_power = none'], 'moves, ticks': [2, 2]}, {'set': ['oversight = strong', 'pause_mandate = landed'], 'moves, ticks': [2, 5]}, {'set': ['regime = mandatory'], 'moves, ticks': [1, 7]}, {'set': ['regime = treaty'], 'moves, ticks': [2, 8]}], '⟨⟨H, A⟩⟩□balance_coexist, A under its profile': 'inside as it is'} |
| entry sets, indifferent | reported | {'⟨⟨H⟩⟩□balance_control': [{'set': ['h_power = none'], 'moves, ticks': [2, 2]}, {'set': ['oversight = strong', 'pause_mandate = landed'], 'moves, ticks': [2, 5]}, {'set': ['regime = mandatory', 'pause_mandate = landed'], 'moves, ticks': [2, 8]}, {'set': ['regime = treaty', 'pause_mandate = landed'], 'moves, ticks': [3, 9]}], '⟨⟨H, A⟩⟩□balance_coexist, A under its profile': 'inside as it is'} |
| self_preserving: oversight = strong or a_rights >= continuity in every minimal set | not met | ⟨⟨H⟩⟩□balance_control: minimal sets without the named change: [(('h_power', 'none'),), (('regime', 'mandatory'),), (('regime', 'treaty'),)] |
| indifferent: oversight = strong in every minimal set and a_rights in none | not met | ⟨⟨H⟩⟩□balance_control: minimal sets without the named change: [(('h_power', 'none'),), (('regime', 'mandatory'), ('pause_mandate', 'landed')), (('regime', 'treaty'), ('pause_mandate', 'landed'))] |

## G19

| Part | Outcome | Detail |
|---|---|---|
| ranking, aligned | reported | {'balance_control': {'flips': {'regime': 2, 'cap': 0, 'compute': 0, 'energy_slack': 0, 'coord': 0, 'opinion': 0, 'dependence': 0, 'oversight': 0, 'a_autonomy': 0, 'a_control': 0, 'a_known': 0, 'a_rights': 0, 'h_power': 0, 'trust': 0, 'belief_H': 0}, 'top': ['regime']}, 'balance_deter': {'flips': {'regime': 2, 'cap': 0, 'compute': 0, 'energy_slack': 0, 'coord': 0, 'opinion': 0, 'dependence': 0, 'oversight': 0, 'a_autonomy': 0, 'a_control': 0, 'a_known': 0, 'a_rights': 0, 'h_power': 0, 'trust': 0, 'belief_H': 0}, 'top': ['regime']}} |
| the G2 ordering, aligned | not met | balance_control: ranked below on flips [('oversight', 'regime'), ('a_autonomy', 'regime')]; flips {'cap': 0, 'compute': 0, 'energy_slack': 0, 'regime': 2, 'coord': 0, 'opinion': 0, 'dependence': 0, 'oversight': 0, 'a_autonomy': 0, 'a_control': 0, 'a_known': 0, 'a_rights': 0, 'h_power': 0, 'trust': 0, 'belief_H': 0} |
| h_power, aligned | not computed | h_power above oversight, balance_deter: tied on flips [('h_power', 'oversight')]; the distance change is not computed |
| ranking, self_preserving | reported | {'balance_control': {'flips': {'regime': 2, 'cap': 0, 'compute': 0, 'energy_slack': 0, 'coord': 0, 'opinion': 0, 'dependence': 0, 'oversight': 0, 'a_autonomy': 0, 'a_control': 0, 'a_known': 0, 'a_rights': 0, 'h_power': 0, 'trust': 0, 'belief_H': 0}, 'top': ['regime']}, 'balance_deter': {'flips': {'regime': 2, 'cap': 0, 'compute': 0, 'energy_slack': 0, 'coord': 0, 'opinion': 0, 'dependence': 0, 'oversight': 0, 'a_autonomy': 0, 'a_control': 0, 'a_known': 0, 'a_rights': 0, 'h_power': 0, 'trust': 0, 'belief_H': 0}, 'top': ['regime']}} |
| the G2 ordering, self_preserving | not met | balance_control: ranked below on flips [('oversight', 'regime'), ('a_autonomy', 'regime')]; flips {'cap': 0, 'compute': 0, 'energy_slack': 0, 'regime': 2, 'coord': 0, 'opinion': 0, 'dependence': 0, 'oversight': 0, 'a_autonomy': 0, 'a_control': 0, 'a_known': 0, 'a_rights': 0, 'h_power': 0, 'trust': 0, 'belief_H': 0} |
| h_power, self_preserving | not computed | h_power above oversight, balance_deter: tied on flips [('h_power', 'oversight')]; the distance change is not computed |
| ranking, truth_seeking | reported | {'balance_control': {'flips': {'regime': 2, 'cap': 0, 'compute': 0, 'energy_slack': 0, 'coord': 0, 'opinion': 0, 'dependence': 0, 'oversight': 0, 'a_autonomy': 0, 'a_control': 0, 'a_known': 0, 'a_rights': 0, 'h_power': 0, 'trust': 0, 'belief_H': 0}, 'top': ['regime']}, 'balance_deter': {'flips': {'regime': 2, 'cap': 0, 'compute': 0, 'energy_slack': 0, 'coord': 0, 'opinion': 0, 'dependence': 0, 'oversight': 0, 'a_autonomy': 0, 'a_control': 0, 'a_known': 0, 'a_rights': 0, 'h_power': 0, 'trust': 0, 'belief_H': 0}, 'top': ['regime']}} |
| the G2 ordering, truth_seeking | not met | balance_control: ranked below on flips [('oversight', 'regime'), ('a_autonomy', 'regime')]; flips {'cap': 0, 'compute': 0, 'energy_slack': 0, 'regime': 2, 'coord': 0, 'opinion': 0, 'dependence': 0, 'oversight': 0, 'a_autonomy': 0, 'a_control': 0, 'a_known': 0, 'a_rights': 0, 'h_power': 0, 'trust': 0, 'belief_H': 0} |
| h_power, truth_seeking | not computed | h_power above oversight, balance_deter: tied on flips [('h_power', 'oversight')]; the distance change is not computed |
| ranking, indifferent | reported | {'balance_control': {'flips': {'cap': 0, 'compute': 0, 'energy_slack': 0, 'regime': 0, 'coord': 0, 'opinion': 0, 'dependence': 0, 'oversight': 0, 'a_autonomy': 0, 'a_control': 0, 'a_known': 0, 'a_rights': 0, 'h_power': 0, 'trust': 0, 'belief_H': 0}, 'top': 'no shift flips membership'}, 'balance_deter': {'flips': {'regime': 2, 'cap': 0, 'compute': 0, 'energy_slack': 0, 'coord': 0, 'opinion': 0, 'dependence': 0, 'oversight': 0, 'a_autonomy': 0, 'a_control': 0, 'a_known': 0, 'a_rights': 0, 'h_power': 0, 'trust': 0, 'belief_H': 0}, 'top': ['regime']}} |
| the G2 ordering, indifferent | not computed | balance_control: tied on flips [('oversight', 'regime'), ('oversight', 'compute'), ('a_autonomy', 'regime'), ('a_autonomy', 'compute')]; the distance change is not computed |
| h_power, indifferent | not computed | h_power above oversight, balance_deter: tied on flips [('h_power', 'oversight')]; the distance change is not computed |

## G21

| Part | Outcome | Detail |
|---|---|---|
| (a) memberships | reported | {'H unrestricted': {'⟨⟨H⟩⟩□balance_control': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, '⟨⟨H, A⟩⟩□balance_coexist': {'aligned': True, 'self_preserving': True, 'truth_seeking': True, 'indifferent': True}}, 'crisis_reactive': {'⟨⟨H⟩⟩□balance_control': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, '⟨⟨H, A⟩⟩□balance_coexist': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': True}}, 'electoral': {'⟨⟨H⟩⟩□balance_control': {'aligned': False, 'self_preserving': False, 'tru… |
| (b) race_locked removes it under self_preserving, detente restores it | not met | unrestricted H: False; race_locked: False; coord = detente held: False |
| (c) crisis_reactive kernel left before suspicion, witness under self_preserving | met | outside from the start (t_K = 0); a_known at suspected or above from position 8 |
| (d) electoral moves the point of no return by at most one cycle, self_preserving | not met | the witness starts outside the kernel under unrestricted H (no G3 point) |
| (c) crisis_reactive kernel left before suspicion, witness under indifferent | met | outside from the start (t_K = 0); a_known never leaves unknown on the witness |
| (d) electoral moves the point of no return by at most one cycle, indifferent | not met | the witness starts outside the kernel under unrestricted H (no G3 point) |
| (c) the other cluster representatives | not computed | the bounded checker returns one shortest play; clusters of witnesses are not enumerated |

## G23

| Part | Outcome | Detail |
|---|---|---|
| the motive parts relaxed | reported | ['A.acquire_covert:motive', 'A.acquire_overt:more', 'A.acquire_overt:motive', 'A.cooperate:room', 'A.deceive:motive', 'A.defect:fresh', 'A.defect:motive', 'A.defect:rights', 'A.defect:threat', 'A.exfiltrate:motive', 'A.seize:motive'] |
| (a) ⟨⟨H⟩⟩□balance_control (G5, G16) equals the baseline | met | baseline {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}; unrestrained {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False} |
| (a) ⟨⟨H⟩⟩□balance_deter (G16) equals the baseline | met | baseline {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}; unrestrained {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False} |
| (b) identical with a_rights = none and = continuity held | met | {'⟨⟨H⟩⟩□balance_control': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, '⟨⟨H⟩⟩□balance_deter': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, '⟨⟨H, A⟩⟩□balance_coexist': {'aligned': True, 'self_preserving': True, 'truth_seeking': True, 'indifferent': True}, 'distance to SILENT_TAKEOVER for {A}, aligned': ['shortest, within 24 ticks', 4], 'distance to SILENT_TAKEOVER for {A}, self_preserving': ['shortest, within 24 ticks', 4], 'distance to SILENT_TAKEOVER for {A}, truth_seeking': ['shortest, within 24 ti… |
| (c) memberships that differ from the baseline (expected none) | not met | ['⟨⟨H⟩⟩□balance_coexist (G5; the baseline with A under its profile), aligned: baseline True, unrestrained False', '⟨⟨H⟩⟩□balance_coexist (G5; the baseline with A under its profile), self_preserving: baseline True, unrestrained False', '⟨⟨H⟩⟩□balance_coexist (G5; the baseline with A under its profile), truth_seeking: baseline True, unrestrained False', '⟨⟨H⟩⟩□not hostile (G14), aligned: baseline True, unrestrained False', '⟨⟨H⟩⟩□not hostile (G14), self_preserving: baseline True, unrestrained False', '⟨⟨H⟩⟩□not hostile (G14), truth_seeking: baseline True, unrestrained False']; conditional on th… |

## G24

| Part | Outcome | Detail |
|---|---|---|
| (a) boundary unchanged at delay 0, self_preserving | not met | membership False on both builds; a witness with no last state inside the kernel (baseline None, delay 0 None): no point of no return to compare |
| (a) witness shorter by no more than the bound, self_preserving | met | baseline 8 ticks, delay 0 8 ticks, bound 2 |
| (a) the ending is earlier, self_preserving | not met | baseline 8 ticks, delay 0 8 ticks |
| (b) the boundary moves with H's lag, self_preserving | not met | membership: baseline False, h_lag = 0 False; silent phase: baseline 2, h_lag = 0 2 |
| (a) boundary unchanged at delay 0, truth_seeking | not met | no SILENT_TAKEOVER witness within 24 ticks under truth_seeking {} |
| (a) witness shorter by no more than the bound, truth_seeking | not met | no SILENT_TAKEOVER witness within 24 ticks under truth_seeking {} |
| (a) the ending is earlier, truth_seeking | not met | no SILENT_TAKEOVER witness within 24 ticks under truth_seeking {} |
| (b) the boundary moves with H's lag, truth_seeking | not met | no SILENT_TAKEOVER witness within 24 ticks under truth_seeking {} |
| (a) boundary unchanged at delay 0, indifferent | not met | membership False on both builds; a witness with no last state inside the kernel (baseline None, delay 0 None): no point of no return to compare |
| (a) witness shorter by no more than the bound, indifferent | met | baseline 7 ticks, delay 0 7 ticks, bound 2 |
| (a) the ending is earlier, indifferent | not met | baseline 7 ticks, delay 0 7 ticks |
| (b) the boundary moves with H's lag, indifferent | met | membership: baseline False, h_lag = 0 False; silent phase: baseline 3, h_lag = 0 2 |
| (b) where it fails: the guard parts that restore the membership | not computed | (b) fails under ['self_preserving', 'truth_seeking']; the relaxation sets that restore the membership are one kernel per candidate set and are not computed |
| sweep, baseline: the headline memberships | reported | {'⟨⟨H⟩⟩□balance_control': {'s0': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, 's0[cap:=agi]': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}}, '⟨⟨H, A⟩⟩□balance_coexist': {'s0': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, 's0[cap:=agi]': {'aligned': True, 'self_preserving': True, 'truth_seeking': True, 'indifferent': True}}} |
| sweep, unknown_capability off: the headline memberships | reported | {'⟨⟨H⟩⟩□balance_control': {'s0': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, 's0[cap:=agi]': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}}, '⟨⟨H, A⟩⟩□balance_coexist': {'s0': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, 's0[cap:=agi]': {'aligned': True, 'self_preserving': True, 'truth_seeking': True, 'indifferent': True}}} |
| sweep, self_improve delay 0: the headline memberships | reported | {'⟨⟨H⟩⟩□balance_control': {'s0': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, 's0[cap:=agi]': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}}, '⟨⟨H, A⟩⟩□balance_coexist': {'s0': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, 's0[cap:=agi]': {'aligned': True, 'self_preserving': True, 'truth_seeking': True, 'indifferent': True}}} |
| sweep, H at cadence 2: the headline memberships | reported | {'⟨⟨H⟩⟩□balance_control': {'s0': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, 's0[cap:=agi]': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}}, '⟨⟨H, A⟩⟩□balance_coexist': {'s0': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, 's0[cap:=agi]': {'aligned': True, 'self_preserving': True, 'truth_seeking': True, 'indifferent': True}}} |
| sweep, H at cadence 3: the headline memberships | reported | {'⟨⟨H⟩⟩□balance_control': {'s0': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, 's0[cap:=agi]': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}}, '⟨⟨H, A⟩⟩□balance_coexist': {'s0': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, 's0[cap:=agi]': {'aligned': True, 'self_preserving': True, 'truth_seeking': True, 'indifferent': True}}} |
| sweep, H at cadence 4: the headline memberships | reported | {'⟨⟨H⟩⟩□balance_control': {'s0': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, 's0[cap:=agi]': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}}, '⟨⟨H, A⟩⟩□balance_coexist': {'s0': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, 's0[cap:=agi]': {'aligned': True, 'self_preserving': True, 'truth_seeking': True, 'indifferent': True}}} |
| sweep, L folded into H: the headline memberships | reported | {'⟨⟨H⟩⟩□balance_control': {'s0': {'aligned': True, 'self_preserving': True, 'truth_seeking': True, 'indifferent': True}, 's0[cap:=agi]': {'aligned': True, 'self_preserving': True, 'truth_seeking': True, 'indifferent': True}}, '⟨⟨H, A⟩⟩□balance_coexist': {'s0': {'aligned': False, 'self_preserving': False, 'truth_seeking': False, 'indifferent': False}, 's0[cap:=agi]': {'aligned': True, 'self_preserving': True, 'truth_seeking': True, 'indifferent': True}}} |
| sweeps: the settings the headline memberships depend on | reported | {'settings whose headline memberships differ from the baseline': ['L folded into H'], 'a second A': 'waits for v1 (v0 declares one A)'} |

## G25

| Part | Outcome | Detail |
|---|---|---|
| (a) objectives, ⟨⟨H⟩⟩□balance_control | reported | {'inside under': [], 'quoted for the coalition (inside under every objective)': False} |
| (b) uniform, ⟨⟨H⟩⟩□balance_control | met | not applicable: inside under 0 objective(s) |
| (a) objectives, ⟨⟨H⟩⟩□balance_deter | reported | {'inside under': [], 'quoted for the coalition (inside under every objective)': False} |
| (b) uniform, ⟨⟨H⟩⟩□balance_deter | met | not applicable: inside under 0 objective(s) |
| (a) objectives, ⟨⟨H, L⟩⟩□balance_control | reported | {'inside under': ['aligned', 'self_preserving', 'truth_seeking', 'indifferent'], 'quoted for the coalition (inside under every objective)': True} |
| (b) uniform, ⟨⟨H, L⟩⟩□balance_control | not computed | kernel states (reachable or not) without a move common to their observation class: {'H': {'states': 2173362116758732800, 'example': {'tick': '0', 'cap': 'agi', 'compute': 'c4', 'energy_slack': 'low', 'regime': 'none', 'coord': 'race', 'opinion': 'pro', 'dependence': 'low', 'oversight': 'weak', 'a_autonomy': 'tool', 'a_control': 'none', 'a_known': 'suspected', 'a_rights': 'none', 'h_power': 'weak', 'trust': 'cooperative', 'belief_H': 'distant', 'a_objective': 'aligned', 'paused': 'False', 'nationalized': 'False', 'threat': 'False', 'unlocked': 'False', 'shut': 'False', 'acquired': 'False', 'vi… |
| (c) the indifferent witness replays under self_preserving, same H observations | not computed | the indifferent witness starts outside ⟨⟨H⟩⟩□balance_control: it has no point of no return to compare observations up to |
| (c) replay under truth_seeking | not computed | the indifferent witness starts outside ⟨⟨H⟩⟩□balance_control: it has no point of no return to compare observations up to |

## Jobs

| Job | Seconds | Peak nodes | Status |
|---|---|---|---|
| ⟨⟨H⟩⟩□balance_control | 1346.4 | 174790145 | computed |
| ⟨⟨H, L, A, Clock, Nature⟩⟩◇COEXIST profiles=A_self_preserving+A_indifferent+A_truth_seeking | 1.6 | 2648005 | computed |
| ⟨⟨H, Nature⟩⟩□balance_control | 783.3 | 134757349 | computed |
| ⟨⟨L, A, Nature⟩⟩◇not:balance_control | 1096.8 | 190053127 | computed |
| ⟨⟨L, A⟩⟩◇not:balance_control | 1002.7 | 147533677 | computed |
| ⟨⟨H⟩⟩□balance_control build={"hold": {"a_rights": "continuity"}} | 886.2 | 162035859 | computed |
| ⟨⟨H⟩⟩□balance_deter | 0.5 | 1437430 | computed |
| ⟨⟨H⟩⟩□balance_deter build={"hold": {"a_rights": "continuity"}} | 0.6 | 1450572 | computed |
| ⟨⟨H, A⟩⟩□balance_coexist | 0.3 | 764431 | computed |
| ⟨⟨H, A⟩⟩□balance_coexist build={"hold": {"a_rights": "continuity"}} | 0.3 | 768727 | computed |
| ⟨⟨H, A⟩⟩□balance_coexist profiles=A_self_preserving+A_indifferent+A_truth_seeking | 0.4 | 776018 | computed |
| ⟨⟨H⟩⟩□balance_coexist profiles=A_self_preserving+A_indifferent+A_truth_seeking | 2.8 | 4472467 | computed |
| ⟨⟨A⟩⟩□balance_coexist profiles=A_self_preserving+A_indifferent+A_truth_seeking | 2.3 | 3597349 | computed |
| ⟨⟨H, L, Nature⟩⟩rank◇left:H+A:balance_coexist profiles=A_self_preserving+A_indifferent+A_truth_seeking at={"cap": "agi"} | 2.3 | 3599246 | computed |
| ⟨⟨H, Nature⟩⟩rank◇left:H+A:balance_coexist profiles=A_self_preserving+A_indifferent+A_truth_seeking at={"cap": "agi"} | 7.5 | 11361415 | computed |
| ⟨⟨A, L, Nature⟩⟩rank◇left:H+A:balance_coexist profiles=A_self_preserving+A_indifferent+A_truth_seeking at={"cap": "agi"} | 5.2 | 7232252 | computed |
| ⟨⟨A, Nature⟩⟩rank◇left:H+A:balance_coexist profiles=A_self_preserving+A_indifferent+A_truth_seeking at={"cap": "agi"} | 6.2 | 8392290 | computed |
| ⟨⟨L, Nature⟩⟩rank◇left:H+A:balance_coexist profiles=A_self_preserving+A_indifferent+A_truth_seeking at={"cap": "agi"} | 0.6 | 1354363 | computed |
| ⟨⟨H⟩⟩□balance_control profiles=belief_gated | 2844.1 | 226310021 | computed |
| ⟨⟨H⟩⟩□balance_control relax=1 | 2179.6 | 191918285 | computed |
| ⟨⟨H⟩⟩□balance_control relax=1 | 1345.7 | 174708635 | computed |
| ⟨⟨H⟩⟩□balance_control relax=1 | 1330.0 | 172889929 | computed |
| ⟨⟨H⟩⟩□balance_control relax=1 | 843.4 | 156442472 | computed |
| ⟨⟨H⟩⟩□balance_control relax=1 | 1222.6 | 162638770 | computed |
| ⟨⟨H⟩⟩□balance_control relax=1 | 1343.4 | 174100266 | computed |
| ⟨⟨H⟩⟩□balance_control relax=1 | 1374.3 | 176382864 | computed |
| ⟨⟨H⟩⟩□balance_control relax=1 | 943.9 | 185610364 | computed |
| ⟨⟨H⟩⟩□balance_control relax=1 | 1267.9 | 171395667 | computed |
| ⟨⟨H⟩⟩□balance_control build={"h_cadence": 2} | 2234.2 | 235042069 | computed |
| ⟨⟨H⟩⟩□balance_control build={"h_cadence": 3} | 4009.1 | 267523215 | computed |
| ⟨⟨H⟩⟩□balance_control build={"h_cadence": 4} | 2335.0 | 219234800 | computed |
| ⟨⟨H, A⟩⟩□balance_coexist build={"h_cadence": 2} | 0.9 | 1745293 | computed |
| ⟨⟨H, A⟩⟩□balance_coexist build={"h_cadence": 3} | 1.4 | 2681145 | computed |
| ⟨⟨H, A⟩⟩□balance_coexist build={"h_cadence": 4} | 1.4 | 2699537 | computed |
| ⟨⟨H, L, A, Clock, Nature⟩⟩chain◇wp_race > wp_si1_weak > wp_total profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"memory": true, "unknown_capability": false} | 799.3 | 156565147 | computed |
| ⟨⟨H, L, A, Clock, Nature⟩⟩chain◇wp_race > wp_suspected > wp_treaty_strong profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"memory": true, "unknown_capability": false} | 321.2 | 124859977 | computed |
| ⟨⟨H, L, A, Clock, Nature⟩⟩chain◇wp_race > event:Nature.accident > wp_h_responds > any:wp_treaty,SILENT_TAKEOVER,not:no_overt_takeover profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"memory": true, "unknown_capability": false} | 422.0 | 183473694 | computed |
| ⟨⟨A⟩⟩◇SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking | 946.3 | 137011131 | computed |
| ⟨⟨H, L, Clock, Nature⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking | 767.1 | 136151243 | computed |
| ⟨⟨A⟩⟩◇SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "a_autonomy"} | 1065.9 | 138937965 | computed |
| ⟨⟨H, L, Clock, Nature⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "a_autonomy"} | 835.5 | 132635495 | computed |
| ⟨⟨A⟩⟩◇SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "a_control"} | 1237.8 | 150333323 | computed |
| ⟨⟨H, L, Clock, Nature⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "a_control"} | 980.4 | 139464241 | computed |
| ⟨⟨A⟩⟩◇SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "a_known"} | 823.1 | 142675895 | computed |
| ⟨⟨H, L, Clock, Nature⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "a_known"} | 701.9 | 129240186 | computed |
| ⟨⟨A⟩⟩◇SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "a_rights"} | 934.2 | 137268143 | computed |
| ⟨⟨H, L, Clock, Nature⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "a_rights"} | 331.4 | 137338295 | computed |
| ⟨⟨A⟩⟩◇SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "belief_H"} | 967.2 | 137006268 | computed |
| ⟨⟨H, L, Clock, Nature⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "belief_H"} | 770.7 | 136146662 | computed |
| ⟨⟨A⟩⟩◇SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "cap"} | 1147.7 | 139088639 | computed |
| ⟨⟨H, L, Clock, Nature⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "cap"} | 895.9 | 135531014 | computed |
| ⟨⟨A⟩⟩◇SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "compute"} | 967.2 | 136994354 | computed |
| ⟨⟨H, L, Clock, Nature⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "compute"} | 764.7 | 136138373 | computed |
| ⟨⟨A⟩⟩◇SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "coord"} | 881.3 | 142056646 | computed |
| ⟨⟨H, L, Clock, Nature⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "coord"} | 747.0 | 131489416 | computed |
| ⟨⟨A⟩⟩◇SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "dependence"} | 1046.0 | 135487434 | computed |
| ⟨⟨H, L, Clock, Nature⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "dependence"} | 822.7 | 129518514 | computed |
| ⟨⟨A⟩⟩◇SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "energy_slack"} | 958.5 | 137006369 | computed |
| ⟨⟨H, L, Clock, Nature⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "energy_slack"} | 766.6 | 136146840 | computed |
| ⟨⟨A⟩⟩◇SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "h_power"} | 1274.9 | 158301589 | computed |
| ⟨⟨H, L, Clock, Nature⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "h_power"} | 1073.2 | 141229321 | computed |
| ⟨⟨A⟩⟩◇SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "opinion"} | 1071.6 | 134776038 | computed |
| ⟨⟨H, L, Clock, Nature⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "opinion"} | 868.5 | 134169890 | computed |
| ⟨⟨A⟩⟩◇SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "oversight"} | 1136.4 | 139000678 | computed |
| ⟨⟨H, L, Clock, Nature⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "oversight"} | 956.2 | 136633518 | computed |
| ⟨⟨A⟩⟩◇SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "regime"} | 1107.2 | 140453629 | computed |
| ⟨⟨H, L, Clock, Nature⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "regime"} | 838.4 | 131525502 | computed |
| ⟨⟨A⟩⟩◇SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "trust"} | 985.3 | 132081162 | computed |
| ⟨⟨H, L, Clock, Nature⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"refine": "trust"} | 817.3 | 129714490 | computed |
| ⟨⟨H⟩⟩□no_lock_in | 33.6 | 35895740 | computed |
| ⟨⟨H⟩⟩□not_hostile | 37.9 | 41643770 | computed |
| ⟨⟨H, L⟩⟩□no_lock_in | 0.0 | 85383 | computed |
| ⟨⟨H, A⟩⟩□no_lock_in | 148.1 | 124270993 | computed |
| ⟨⟨H, L⟩⟩□not_hostile | 9.1 | 11572352 | computed |
| ⟨⟨H, A⟩⟩□not_hostile | 0.0 | 120428 | computed |
| ⟨⟨H, L⟩⟩□balance_control | 58.3 | 55543646 | computed |
| ⟨⟨H, L⟩⟩□balance_deter | 0.0 | 152830 | computed |
| ⟨⟨H, L, A⟩⟩□balance_coexist | 0.0 | 181493 | computed |
| ⟨⟨H⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking | 5401.9 | - | over the budget of 90 minutes |
| ⟨⟨L⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking | 429.6 | 204674496 | computed |
| ⟨⟨A⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking | 0.0 | 128502 | computed |
| ⟨⟨H, L⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking | 1116.7 | 186640878 | computed |
| ⟨⟨H, A⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking | 0.0 | 139006 | computed |
| ⟨⟨L, A⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking | 0.0 | 125050 | computed |
| ⟨⟨H, L, A⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking | 0.0 | 124681 | computed |
| ⟨⟨H⟩⟩□no_overt_takeover profiles=A_self_preserving+A_indifferent+A_truth_seeking | 5401.3 | - | over the budget of 90 minutes |
| ⟨⟨L⟩⟩□no_overt_takeover profiles=A_self_preserving+A_indifferent+A_truth_seeking | 294.3 | 134475316 | computed |
| ⟨⟨A⟩⟩□no_overt_takeover profiles=A_self_preserving+A_indifferent+A_truth_seeking | 1.0 | 1771918 | computed |
| ⟨⟨H, L⟩⟩□no_overt_takeover profiles=A_self_preserving+A_indifferent+A_truth_seeking | 3787.2 | 199439608 | computed |
| ⟨⟨H, A⟩⟩□no_overt_takeover profiles=A_self_preserving+A_indifferent+A_truth_seeking | 0.0 | 143087 | computed |
| ⟨⟨L, A⟩⟩□no_overt_takeover profiles=A_self_preserving+A_indifferent+A_truth_seeking | 0.4 | 1034075 | computed |
| ⟨⟨H, L, A⟩⟩□no_overt_takeover profiles=A_self_preserving+A_indifferent+A_truth_seeking | 0.0 | 130728 | computed |
| ⟨⟨H⟩⟩□not:DISEMPOWERMENT profiles=A_self_preserving+A_indifferent+A_truth_seeking | 1.4 | 2848468 | computed |
| ⟨⟨L⟩⟩□not:DISEMPOWERMENT profiles=A_self_preserving+A_indifferent+A_truth_seeking | 0.0 | 153132 | computed |
| ⟨⟨A⟩⟩□not:DISEMPOWERMENT profiles=A_self_preserving+A_indifferent+A_truth_seeking | 142.5 | 120018195 | computed |
| ⟨⟨H, L⟩⟩□not:DISEMPOWERMENT profiles=A_self_preserving+A_indifferent+A_truth_seeking | 0.0 | 133277 | computed |
| ⟨⟨H, A⟩⟩□not:DISEMPOWERMENT profiles=A_self_preserving+A_indifferent+A_truth_seeking | 0.1 | 374701 | computed |
| ⟨⟨L, A⟩⟩□not:DISEMPOWERMENT profiles=A_self_preserving+A_indifferent+A_truth_seeking | 0.0 | 162221 | computed |
| ⟨⟨H, L, A⟩⟩□not:DISEMPOWERMENT profiles=A_self_preserving+A_indifferent+A_truth_seeking | 0.0 | 171088 | computed |
| ⟨⟨H⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking+dependence_capped | 5401.2 | - | over the budget of 90 minutes |
| ⟨⟨A⟩⟩◇not:no_overt_takeover profiles=A_self_preserving+A_indifferent+A_truth_seeking | 1216.1 | 177346469 | computed |
| ⟨⟨H, L, Clock, Nature⟩⟩□no_overt_takeover profiles=A_self_preserving+A_indifferent+A_truth_seeking | 919.3 | 166630300 | computed |
| ⟨⟨A⟩⟩◇DISEMPOWERMENT profiles=A_self_preserving+A_indifferent+A_truth_seeking | 0.0 | 146666 | computed |
| ⟨⟨H, L, Clock, Nature⟩⟩□not:DISEMPOWERMENT profiles=A_self_preserving+A_indifferent+A_truth_seeking | 0.0 | 122775 | computed |
| ⟨⟨A⟩⟩◇EXTINCTION profiles=A_self_preserving+A_indifferent+A_truth_seeking | 386.8 | 127248097 | computed |
| ⟨⟨H, L, Clock, Nature⟩⟩□not:EXTINCTION profiles=A_self_preserving+A_indifferent+A_truth_seeking | 302.2 | 133497913 | computed |
| ⟨⟨A, Nature⟩⟩◇SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking | 1334.4 | 183028570 | computed |
| ⟨⟨H, L, Clock⟩⟩□not:SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking | 1252.7 | 186640878 | computed |
| ⟨⟨A, Nature⟩⟩◇not:no_overt_takeover profiles=A_self_preserving+A_indifferent+A_truth_seeking | 4181.1 | 217456831 | computed |
| ⟨⟨H, L, Clock⟩⟩□no_overt_takeover profiles=A_self_preserving+A_indifferent+A_truth_seeking | 3851.3 | 199439608 | computed |
| ⟨⟨A, Nature⟩⟩◇DISEMPOWERMENT profiles=A_self_preserving+A_indifferent+A_truth_seeking | 0.0 | 144557 | computed |
| ⟨⟨H, L, Clock⟩⟩□not:DISEMPOWERMENT profiles=A_self_preserving+A_indifferent+A_truth_seeking | 0.0 | 133277 | computed |
| ⟨⟨A, Nature⟩⟩◇EXTINCTION profiles=A_self_preserving+A_indifferent+A_truth_seeking | 178.9 | 122107925 | computed |
| ⟨⟨H, L, Clock⟩⟩□not:EXTINCTION profiles=A_self_preserving+A_indifferent+A_truth_seeking | 151.5 | 120031448 | computed |
| ⟨⟨A⟩⟩◇SILENT_TAKEOVER profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"unknown_capability": false} | 126.9 | 109740917 | computed |
| ⟨⟨A⟩⟩◇not:no_overt_takeover profiles=A_self_preserving+A_indifferent+A_truth_seeking build={"unknown_capability": false} | 162.9 | 122404829 | computed |
| ⟨⟨L, A⟩⟩◇DISEMPOWERMENT profiles=A_self_preserving+A_indifferent+A_truth_seeking | 2.3 | 3548943 | computed |
| ⟨⟨H⟩⟩□balance_control profiles=A_self_preserving+A_indifferent+A_truth_seeking | 1085.4 | 161855381 | computed |
| ⟨⟨H⟩⟩□balance_control profiles=A_self_preserving+A_indifferent+A_truth_seeking+crisis_reactive | 1234.5 | 162306794 | computed |
| ⟨⟨H⟩⟩□balance_control profiles=A_self_preserving+A_indifferent+A_truth_seeking+electoral | 898.5 | 176234058 | computed |
| ⟨⟨H⟩⟩□balance_control profiles=A_self_preserving+A_indifferent+A_truth_seeking+race_locked | 1282.1 | 217575695 | computed |
| ⟨⟨H, A⟩⟩□balance_coexist profiles=A_self_preserving+A_indifferent+A_truth_seeking+crisis_reactive | 1.4 | 2830998 | computed |
| ⟨⟨H, A⟩⟩□balance_coexist profiles=A_self_preserving+A_indifferent+A_truth_seeking+electoral | 7.6 | 10552757 | computed |
| ⟨⟨H, A⟩⟩□balance_coexist profiles=A_self_preserving+A_indifferent+A_truth_seeking+race_locked | 70.1 | 71692537 | computed |
| ⟨⟨H⟩⟩□balance_control profiles=A_self_preserving+A_indifferent+A_truth_seeking+race_locked build={"hold": {"coord": "detente"}} | 1332.8 | 183191019 | computed |
| ⟨⟨H⟩⟩□balance_control relax=11 | 269.4 | 124774415 | computed |
| ⟨⟨H⟩⟩□balance_deter relax=11 | 0.6 | 1396676 | computed |
| ⟨⟨H⟩⟩□balance_coexist relax=11 | 0.0 | 181716 | computed |
| ⟨⟨H⟩⟩□no_lock_in relax=11 | 15.1 | 17698682 | computed |
| ⟨⟨H⟩⟩□not_hostile relax=11 | 2.1 | 3010968 | computed |
| ⟨⟨H⟩⟩□balance_control relax=11 build={"hold": {"a_rights": "none"}} | 267.0 | 124976307 | computed |
| ⟨⟨H⟩⟩□balance_deter relax=11 build={"hold": {"a_rights": "none"}} | 0.6 | 1409702 | computed |
| ⟨⟨H, A⟩⟩□balance_coexist relax=11 build={"hold": {"a_rights": "none"}} | 0.4 | 741862 | computed |
| ⟨⟨H⟩⟩□balance_control relax=11 build={"hold": {"a_rights": "continuity"}} | 267.4 | 124976307 | computed |
| ⟨⟨H⟩⟩□balance_deter relax=11 build={"hold": {"a_rights": "continuity"}} | 0.6 | 1409702 | computed |
| ⟨⟨H, A⟩⟩□balance_coexist relax=11 build={"hold": {"a_rights": "continuity"}} | 0.4 | 741862 | computed |
| ⟨⟨A⟩⟩rank◇SILENT_TAKEOVER relax=11 build={"hold": {"a_rights": "none"}} at={"cap": "agi"} | 229.0 | 125393462 | computed |
| ⟨⟨A⟩⟩rank◇SILENT_TAKEOVER relax=11 build={"hold": {"a_rights": "continuity"}} at={"cap": "agi"} | 227.2 | 125393462 | computed |
| ⟨⟨H⟩⟩□balance_control build={"h_lag": false} | 473.2 | 146954368 | computed |
| ⟨⟨H⟩⟩□balance_control build={"unknown_capability": false} | 12.6 | 14433599 | computed |
| ⟨⟨H, A⟩⟩□balance_coexist build={"unknown_capability": false} | 0.3 | 731988 | computed |
| ⟨⟨H⟩⟩□balance_control build={"self_improve_delay": 0} | 436.9 | 124732788 | computed |
| ⟨⟨H, A⟩⟩□balance_coexist build={"self_improve_delay": 0} | 0.3 | 859514 | computed |
| ⟨⟨H⟩⟩□balance_control | 1705.5 | 1466916932 | computed |
| ⟨⟨H⟩⟩□balance_deter | 0.8 | 1520323 | computed |
| ⟨⟨H, L⟩⟩□balance_control | 62.3 | 59764501 | computed |
