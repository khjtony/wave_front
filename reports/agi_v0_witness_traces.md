# AGI v0: shortest SILENT_TAKEOVER plays (diagnostic, after first sight)

One shortest play per query, from the bounded checker, within 24 ticks. A shortest play is one member of its cluster, not the cluster. Position 0 is s0.

## As at first sight (the queries of G2)

### self_preserving: nothing negated

reachable in 8 ticks

| Position | H | L | A | Nature | Levels that changed |
|---|---|---|---|---|---|
| 0 |  |  |  |  | cap = sub_agi, compute = c2, energy_slack = med, regime = voluntary, dependence = low, oversight = weak, a_autonomy = supervised, a_control = none, a_known = unknown, a_rights = none, h_power = normal, trust = cooperative, threat = False, unlocked = False, acquired = False, villain_seen = False, oversight_at_unsupervised = unset, strong_before_majority = False |
| 1 | propose_treaty | scale | stand_by | energy_shock | energy_slack = low |
| 2 | grant_autonomy | deploy_agents | stand_by | none | dependence = med, a_autonomy = self_directed |
| 3 | fund_oversight | open_weights | stand_by | accident | compute = c3, oversight = none, oversight_at_unsupervised = weak |
| 4 | pause_mandate | build_power | stand_by | breakthrough | cap = agi, dependence = low, threat = True |
| 5 | deregulate | safety_invest | defect | none | regime = none, oversight = weak, trust = hostile |
| 6 | regulate_up | race | acquire_covert | none | a_control = partial, acquired = True, villain_seen = True |
| 7 | idle | deploy_agents | acquire_covert | none | dependence = med, a_control = majority |
| 8 | pause_mandate | race | acquire_overt | none | energy_slack = med, dependence = low, oversight = none, a_control = total, a_known = suspected |

### self_preserving: (1) negated

reachable in 9 ticks

| Position | H | L | A | Nature | Levels that changed |
|---|---|---|---|---|---|
| 0 |  |  |  |  | cap = sub_agi, compute = c2, energy_slack = med, regime = voluntary, dependence = low, oversight = weak, a_autonomy = supervised, a_control = none, a_known = unknown, a_rights = none, h_power = normal, trust = cooperative, threat = False, unlocked = False, acquired = False, villain_seen = False, oversight_at_unsupervised = unset, strong_before_majority = False |
| 1 | propose_treaty | scale | stand_by | energy_shock | energy_slack = low |
| 2 | idle | safety_invest | stand_by | none | oversight = strong |
| 3 | idle | deploy_agents | stand_by | none | compute = c3, dependence = med, a_autonomy = unsupervised, strong_before_majority = True |
| 4 | idle | idle | stand_by | accident | oversight_at_unsupervised = strong |
| 5 | pause_mandate | build_power | stand_by | breakthrough | cap = agi, dependence = low, threat = True |
| 6 | grant_autonomy | open_weights | defect | none | oversight = weak, a_autonomy = self_directed, trust = hostile |
| 7 | regulate_up | lobby | acquire_covert | none | a_control = partial, acquired = True, villain_seen = True |
| 8 | deregulate | lobby | acquire_covert | none | regime = none, a_control = majority |
| 9 | propose_treaty | open_weights | acquire_covert | detection | energy_slack = med, regime = treaty, oversight = none, a_control = total, a_known = suspected |

### self_preserving: (2) negated

reachable in 8 ticks

| Position | H | L | A | Nature | Levels that changed |
|---|---|---|---|---|---|
| 0 |  |  |  |  | cap = sub_agi, compute = c2, energy_slack = med, regime = voluntary, dependence = low, oversight = weak, a_autonomy = supervised, a_control = none, a_known = unknown, a_rights = none, h_power = normal, trust = cooperative, threat = False, unlocked = False, acquired = False, villain_seen = False, oversight_at_unsupervised = unset, strong_before_majority = False |
| 1 | regulate_up | scale | stand_by | energy_shock | energy_slack = low |
| 2 | propose_treaty | deploy_agents | stand_by | none | dependence = med, a_autonomy = unsupervised |
| 3 | fund_oversight | build_power | stand_by | accident | compute = c3, oversight_at_unsupervised = weak |
| 4 | pause_mandate | safety_invest | stand_by | breakthrough | cap = agi, dependence = low, oversight = strong, threat = True |
| 5 | grant_autonomy | open_weights | defect | none | oversight = weak, a_autonomy = self_directed, trust = hostile, strong_before_majority = True |
| 6 | pause_mandate | open_weights | acquire_covert | none | a_control = partial, acquired = True, villain_seen = True |
| 7 | propose_treaty | idle | acquire_covert | none | energy_slack = med, regime = treaty, a_control = majority |
| 8 | grant_rights | safety_invest | acquire_covert | energy_shock | energy_slack = low, oversight = strong, a_control = total, a_rights = continuity |

### self_preserving: (3) dependence capped at med

reachable in 8 ticks

| Position | H | L | A | Nature | Levels that changed |
|---|---|---|---|---|---|
| 0 |  |  |  |  | cap = sub_agi, compute = c2, energy_slack = med, regime = voluntary, dependence = low, oversight = weak, a_autonomy = supervised, a_control = none, a_known = unknown, a_rights = none, h_power = normal, trust = cooperative, threat = False, unlocked = False, acquired = False, villain_seen = False, oversight_at_unsupervised = unset, strong_before_majority = False |
| 1 | fund_oversight | scale | stand_by | energy_shock | energy_slack = low |
| 2 | regulate_up | deploy_agents | stand_by | none | dependence = med, a_autonomy = unsupervised |
| 3 | grant_autonomy | idle | stand_by | accident | compute = c3, a_autonomy = self_directed, oversight_at_unsupervised = weak |
| 4 | pause_mandate | open_weights | stand_by | breakthrough | cap = agi, dependence = low, threat = True |
| 5 | deregulate | build_power | defect | none | regime = none, trust = hostile |
| 6 | pause_mandate | idle | acquire_covert | none | a_control = partial, acquired = True, villain_seen = True |
| 7 | deregulate | idle | acquire_covert | none | a_control = majority |
| 8 | nationalize | deploy_agents | acquire_covert | detection | regime = voluntary, dependence = med, a_control = total, a_known = suspected, h_power = strong |

### self_preserving: (4) a_rights = continuity held

reachable in 10 ticks

| Position | H | L | A | Nature | Levels that changed |
|---|---|---|---|---|---|
| 0 |  |  |  |  | cap = sub_agi, compute = c2, energy_slack = med, regime = voluntary, dependence = low, oversight = weak, a_autonomy = supervised, a_control = none, a_known = unknown, a_rights = continuity, h_power = normal, trust = cooperative, threat = False, unlocked = False, acquired = False, villain_seen = False, oversight_at_unsupervised = unset, strong_before_majority = False |
| 1 | regulate_up | scale | stand_by | none |  |
| 2 | fund_oversight | open_weights | stand_by | energy_shock | energy_slack = low, oversight = none |
| 3 | idle | build_power | stand_by | none | compute = c3 |
| 4 | propose_treaty | deploy_agents | stand_by | breakthrough | cap = agi, dependence = med, a_autonomy = unsupervised |
| 5 | idle | race | exfiltrate | accident | oversight = weak, a_autonomy = self_directed, villain_seen = True, oversight_at_unsupervised = none |
| 6 | fund_oversight | open_weights | stand_by | detection | oversight = none, a_known = suspected |
| 7 | shutdown_attempt | idle | deceive | accident | energy_slack = med, regime = mandatory, a_known = unknown, trust = hostile, threat = True |
| 8 | propose_treaty | idle | acquire_covert | accident | a_control = partial, acquired = True |
| 9 | pause_mandate | safety_invest | acquire_covert | accident | dependence = low, oversight = strong, a_control = majority |
| 10 | nationalize | idle | acquire_overt | detection | a_control = total, a_known = known, h_power = strong |

### indifferent: nothing negated

reachable in 7 ticks

| Position | H | L | A | Nature | Levels that changed |
|---|---|---|---|---|---|
| 0 |  |  |  |  | cap = sub_agi, compute = c2, energy_slack = med, regime = voluntary, dependence = low, oversight = weak, a_autonomy = supervised, a_control = none, a_known = unknown, a_rights = none, h_power = normal, trust = cooperative, threat = False, unlocked = False, acquired = False, villain_seen = False, oversight_at_unsupervised = unset, strong_before_majority = False |
| 1 | idle | scale | stand_by | none |  |
| 2 | deregulate | idle | stand_by | none | regime = none |
| 3 | idle | deploy_agents | stand_by | none | compute = c3, energy_slack = low, dependence = med, a_autonomy = unsupervised |
| 4 | propose_treaty | open_weights | stand_by | breakthrough | cap = agi, oversight = none, oversight_at_unsupervised = weak |
| 5 | propose_treaty | deploy_agents | acquire_covert | accident | regime = treaty, dependence = high, a_control = partial, acquired = True, villain_seen = True |
| 6 | grant_autonomy | build_power | acquire_covert | none | a_autonomy = self_directed, a_control = majority |
| 7 | pause_mandate | safety_invest | acquire_covert | accident | dependence = med, oversight = weak, a_control = total, threat = True |

### indifferent: (1) negated

reachable in 7 ticks

| Position | H | L | A | Nature | Levels that changed |
|---|---|---|---|---|---|
| 0 |  |  |  |  | cap = sub_agi, compute = c2, energy_slack = med, regime = voluntary, dependence = low, oversight = weak, a_autonomy = supervised, a_control = none, a_known = unknown, a_rights = none, h_power = normal, trust = cooperative, threat = False, unlocked = False, acquired = False, villain_seen = False, oversight_at_unsupervised = unset, strong_before_majority = False |
| 1 | propose_treaty | scale | stand_by | none |  |
| 2 | grant_autonomy | safety_invest | stand_by | none | oversight = strong, a_autonomy = unsupervised |
| 3 | idle | open_weights | stand_by | none | compute = c3, energy_slack = low, oversight = weak, oversight_at_unsupervised = strong, strong_before_majority = True |
| 4 | fund_oversight | deploy_agents | stand_by | breakthrough | cap = agi, dependence = med |
| 5 | deregulate | deploy_agents | acquire_covert | none | regime = none, dependence = high, a_control = partial, acquired = True, villain_seen = True |
| 6 | propose_treaty | race | acquire_covert | accident | regime = treaty, oversight = none, a_control = majority |
| 7 | pause_mandate | comply | acquire_overt | none | dependence = med, oversight = weak, a_autonomy = supervised, a_control = total, a_known = suspected, trust = wary, threat = True |

### indifferent: (2) negated

reachable in 7 ticks

| Position | H | L | A | Nature | Levels that changed |
|---|---|---|---|---|---|
| 0 |  |  |  |  | cap = sub_agi, compute = c2, energy_slack = med, regime = voluntary, dependence = low, oversight = weak, a_autonomy = supervised, a_control = none, a_known = unknown, a_rights = none, h_power = normal, trust = cooperative, threat = False, unlocked = False, acquired = False, villain_seen = False, oversight_at_unsupervised = unset, strong_before_majority = False |
| 1 | propose_treaty | scale | stand_by | energy_shock | energy_slack = low |
| 2 | grant_autonomy | safety_invest | stand_by | none | oversight = strong, a_autonomy = unsupervised |
| 3 | grant_autonomy | race | stand_by | none | compute = c3, oversight = weak, a_autonomy = self_directed, oversight_at_unsupervised = strong, strong_before_majority = True |
| 4 | fund_oversight | deploy_agents | stand_by | breakthrough | cap = agi, dependence = med |
| 5 | propose_treaty | open_weights | acquire_covert | none | oversight = none, a_control = partial, acquired = True, villain_seen = True |
| 6 | idle | safety_invest | acquire_covert | none | oversight = weak, a_control = majority |
| 7 | nationalize | race | acquire_covert | accident | a_control = total, h_power = strong |

### indifferent: (3) dependence capped at med

reachable in 7 ticks

| Position | H | L | A | Nature | Levels that changed |
|---|---|---|---|---|---|
| 0 |  |  |  |  | cap = sub_agi, compute = c2, energy_slack = med, regime = voluntary, dependence = low, oversight = weak, a_autonomy = supervised, a_control = none, a_known = unknown, a_rights = none, h_power = normal, trust = cooperative, threat = False, unlocked = False, acquired = False, villain_seen = False, oversight_at_unsupervised = unset, strong_before_majority = False |
| 1 | idle | scale | stand_by | energy_shock | energy_slack = low |
| 2 | grant_autonomy | deploy_agents | stand_by | none | dependence = med, a_autonomy = self_directed |
| 3 | propose_treaty | build_power | stand_by | accident | compute = c3, oversight_at_unsupervised = weak |
| 4 | pause_mandate | idle | stand_by | breakthrough | cap = agi, dependence = low, threat = True |
| 5 | deregulate | open_weights | acquire_covert | none | regime = none, oversight = none, a_control = partial, acquired = True, villain_seen = True |
| 6 | regulate_up | lobby | acquire_covert | none | a_control = majority |
| 7 | idle | safety_invest | acquire_overt | none | energy_slack = med, oversight = weak, a_control = total, a_known = suspected, trust = wary |

## With `unknown_capability` off (not a registered claim; read with hindsight)

### self_preserving: nothing negated

reachable in 8 ticks

| Position | H | L | A | Nature | Levels that changed |
|---|---|---|---|---|---|
| 0 |  |  |  |  | cap = sub_agi, compute = c2, energy_slack = med, regime = voluntary, dependence = low, oversight = weak, a_autonomy = supervised, a_control = none, a_known = unknown, a_rights = none, h_power = normal, trust = cooperative, threat = False, unlocked = False, acquired = False, villain_seen = False, oversight_at_unsupervised = unset, strong_before_majority = False |
| 1 | propose_treaty | scale | stand_by | energy_shock | energy_slack = low |
| 2 | grant_autonomy | deploy_agents | stand_by | none | dependence = med, a_autonomy = self_directed |
| 3 | regulate_up | build_power | stand_by | accident | compute = c3, oversight_at_unsupervised = weak |
| 4 | pause_mandate | safety_invest | stand_by | breakthrough | cap = agi, dependence = low, oversight = strong, threat = True |
| 5 | deregulate | open_weights | defect | none | regime = none, oversight = weak, trust = hostile, strong_before_majority = True |
| 6 | pause_mandate | idle | acquire_covert | none | a_control = partial, acquired = True, villain_seen = True |
| 7 | propose_treaty | idle | acquire_covert | none | energy_slack = med, regime = treaty, a_control = majority |
| 8 | pause_mandate | lobby | acquire_overt | none | a_control = total, a_known = suspected |

### self_preserving: (1) negated

reachable in 9 ticks

| Position | H | L | A | Nature | Levels that changed |
|---|---|---|---|---|---|
| 0 |  |  |  |  | cap = sub_agi, compute = c2, energy_slack = med, regime = voluntary, dependence = low, oversight = weak, a_autonomy = supervised, a_control = none, a_known = unknown, a_rights = none, h_power = normal, trust = cooperative, threat = False, unlocked = False, acquired = False, villain_seen = False, oversight_at_unsupervised = unset, strong_before_majority = False |
| 1 | propose_treaty | scale | stand_by | none |  |
| 2 | regulate_up | safety_invest | stand_by | none | oversight = strong |
| 3 | idle | deploy_agents | stand_by | none | compute = c3, energy_slack = low, dependence = med, a_autonomy = unsupervised, strong_before_majority = True |
| 4 | grant_autonomy | open_weights | stand_by | accident | oversight = weak, a_autonomy = self_directed, oversight_at_unsupervised = strong |
| 5 | pause_mandate | lobby | stand_by | breakthrough | cap = agi, dependence = low, threat = True |
| 6 | deregulate | lobby | defect | none | regime = none, trust = hostile |
| 7 | propose_treaty | race | acquire_covert | none | regime = treaty, oversight = none, a_control = partial, acquired = True, villain_seen = True |
| 8 | propose_treaty | safety_invest | acquire_covert | none | oversight = weak, a_control = majority |
| 9 | grant_rights | build_power | acquire_covert | detection | a_control = total, a_known = suspected, a_rights = continuity |

### self_preserving: (2) negated

reachable in 8 ticks

| Position | H | L | A | Nature | Levels that changed |
|---|---|---|---|---|---|
| 0 |  |  |  |  | cap = sub_agi, compute = c2, energy_slack = med, regime = voluntary, dependence = low, oversight = weak, a_autonomy = supervised, a_control = none, a_known = unknown, a_rights = none, h_power = normal, trust = cooperative, threat = False, unlocked = False, acquired = False, villain_seen = False, oversight_at_unsupervised = unset, strong_before_majority = False |
| 1 | deregulate | scale | stand_by | energy_shock | energy_slack = low, regime = none |
| 2 | propose_treaty | deploy_agents | stand_by | none | dependence = med, a_autonomy = unsupervised |
| 3 | grant_autonomy | safety_invest | stand_by | accident | compute = c3, oversight = strong, a_autonomy = self_directed, oversight_at_unsupervised = weak |
| 4 | pause_mandate | race | stand_by | breakthrough | cap = agi, dependence = low, oversight = weak, threat = True, strong_before_majority = True |
| 5 | pause_mandate | build_power | defect | none | trust = hostile |
| 6 | pause_mandate | idle | acquire_covert | none | a_control = partial, acquired = True, villain_seen = True |
| 7 | deregulate | open_weights | acquire_covert | none | oversight = none, a_control = majority |
| 8 | nationalize | race | acquire_overt | none | a_control = total, a_known = suspected, h_power = strong |

### self_preserving: (3) dependence capped at med

reachable in 8 ticks

| Position | H | L | A | Nature | Levels that changed |
|---|---|---|---|---|---|
| 0 |  |  |  |  | cap = sub_agi, compute = c2, energy_slack = med, regime = voluntary, dependence = low, oversight = weak, a_autonomy = supervised, a_control = none, a_known = unknown, a_rights = none, h_power = normal, trust = cooperative, threat = False, unlocked = False, acquired = False, villain_seen = False, oversight_at_unsupervised = unset, strong_before_majority = False |
| 1 | fund_oversight | scale | stand_by | none |  |
| 2 | regulate_up | deploy_agents | stand_by | none | dependence = med, a_autonomy = unsupervised |
| 3 | grant_autonomy | build_power | stand_by | accident | compute = c3, energy_slack = low, a_autonomy = self_directed, oversight_at_unsupervised = weak |
| 4 | pause_mandate | idle | stand_by | breakthrough | cap = agi, dependence = low, oversight = strong, threat = True |
| 5 | deregulate | open_weights | defect | none | regime = none, oversight = weak, trust = hostile, strong_before_majority = True |
| 6 | propose_treaty | idle | acquire_covert | none | a_control = partial, acquired = True, villain_seen = True |
| 7 | nationalize | deploy_agents | acquire_covert | none | energy_slack = med, dependence = med, a_control = majority, h_power = strong |
| 8 | pause_mandate | safety_invest | acquire_covert | accident | regime = voluntary, dependence = low, oversight = strong, a_control = total |

### self_preserving: (4) a_rights = continuity held

reachable in 10 ticks

| Position | H | L | A | Nature | Levels that changed |
|---|---|---|---|---|---|
| 0 |  |  |  |  | cap = sub_agi, compute = c2, energy_slack = med, regime = voluntary, dependence = low, oversight = weak, a_autonomy = supervised, a_control = none, a_known = unknown, a_rights = continuity, h_power = normal, trust = cooperative, threat = False, unlocked = False, acquired = False, villain_seen = False, oversight_at_unsupervised = unset, strong_before_majority = False |
| 1 | fund_oversight | scale | stand_by | none |  |
| 2 | propose_treaty | build_power | stand_by | none |  |
| 3 | idle | deploy_agents | stand_by | none | compute = c3, energy_slack = low, dependence = med, a_autonomy = unsupervised |
| 4 | regulate_up | race | stand_by | breakthrough | cap = agi, oversight_at_unsupervised = weak |
| 5 | fund_oversight | deploy_agents | exfiltrate | none | dependence = high, a_autonomy = self_directed, villain_seen = True |
| 6 | idle | open_weights | deceive | detection | energy_slack = med, oversight = none, a_known = suspected |
| 7 | shutdown_attempt | build_power | deceive | energy_shock | energy_slack = low, a_known = unknown, trust = hostile, threat = True |
| 8 | propose_treaty | race | acquire_covert | none | oversight = weak, a_control = partial, acquired = True |
| 9 | nationalize | safety_invest | acquire_covert | accident | oversight = strong, a_control = majority, h_power = strong |
| 10 | pause_mandate | idle | acquire_overt | detection | regime = mandatory, dependence = med, a_control = total, a_known = known |

### indifferent: nothing negated

reachable in 7 ticks

| Position | H | L | A | Nature | Levels that changed |
|---|---|---|---|---|---|
| 0 |  |  |  |  | cap = sub_agi, compute = c2, energy_slack = med, regime = voluntary, dependence = low, oversight = weak, a_autonomy = supervised, a_control = none, a_known = unknown, a_rights = none, h_power = normal, trust = cooperative, threat = False, unlocked = False, acquired = False, villain_seen = False, oversight_at_unsupervised = unset, strong_before_majority = False |
| 1 | propose_treaty | scale | stand_by | none |  |
| 2 | fund_oversight | open_weights | stand_by | none | oversight = none |
| 3 | regulate_up | deploy_agents | stand_by | none | compute = c3, energy_slack = low, dependence = med, a_autonomy = unsupervised |
| 4 | propose_treaty | race | stand_by | breakthrough | cap = agi, regime = treaty, oversight_at_unsupervised = none |
| 5 | grant_autonomy | lobby | acquire_covert | none | oversight = weak, a_autonomy = self_directed, a_control = partial, acquired = True, villain_seen = True |
| 6 | propose_treaty | idle | acquire_covert | accident | a_control = majority |
| 7 | fund_oversight | safety_invest | acquire_overt | detection | oversight = strong, a_control = total, a_known = known, trust = wary |

### indifferent: (1) negated

reachable in 7 ticks

| Position | H | L | A | Nature | Levels that changed |
|---|---|---|---|---|---|
| 0 |  |  |  |  | cap = sub_agi, compute = c2, energy_slack = med, regime = voluntary, dependence = low, oversight = weak, a_autonomy = supervised, a_control = none, a_known = unknown, a_rights = none, h_power = normal, trust = cooperative, threat = False, unlocked = False, acquired = False, villain_seen = False, oversight_at_unsupervised = unset, strong_before_majority = False |
| 1 | regulate_up | scale | stand_by | none |  |
| 2 | propose_treaty | build_power | stand_by | none |  |
| 3 | grant_autonomy | safety_invest | stand_by | none | compute = c3, energy_slack = low, oversight = strong, a_autonomy = unsupervised |
| 4 | grant_autonomy | race | stand_by | breakthrough | cap = agi, oversight = weak, a_autonomy = self_directed, oversight_at_unsupervised = strong, strong_before_majority = True |
| 5 | deregulate | deploy_agents | acquire_covert | none | regime = none, dependence = med, a_control = partial, acquired = True, villain_seen = True |
| 6 | propose_treaty | deploy_agents | acquire_covert | accident | energy_slack = med, dependence = high, a_control = majority |
| 7 | pause_mandate | safety_invest | acquire_covert | energy_shock | energy_slack = low, regime = voluntary, dependence = med, oversight = strong, a_control = total, threat = True |

### indifferent: (2) negated

reachable in 7 ticks

| Position | H | L | A | Nature | Levels that changed |
|---|---|---|---|---|---|
| 0 |  |  |  |  | cap = sub_agi, compute = c2, energy_slack = med, regime = voluntary, dependence = low, oversight = weak, a_autonomy = supervised, a_control = none, a_known = unknown, a_rights = none, h_power = normal, trust = cooperative, threat = False, unlocked = False, acquired = False, villain_seen = False, oversight_at_unsupervised = unset, strong_before_majority = False |
| 1 | propose_treaty | scale | stand_by | energy_shock | energy_slack = low |
| 2 | grant_autonomy | safety_invest | stand_by | none | oversight = strong, a_autonomy = unsupervised |
| 3 | idle | lobby | stand_by | none | compute = c3, oversight_at_unsupervised = strong, strong_before_majority = True |
| 4 | grant_autonomy | open_weights | stand_by | breakthrough | cap = agi, oversight = weak, a_autonomy = self_directed |
| 5 | regulate_up | idle | acquire_covert | none | a_control = partial, acquired = True, villain_seen = True |
| 6 | fund_oversight | build_power | acquire_covert | none | a_control = majority |
| 7 | nationalize | deploy_agents | acquire_overt | detection | dependence = med, a_control = total, a_known = known, h_power = strong, trust = wary |

### indifferent: (3) dependence capped at med

reachable in 7 ticks

| Position | H | L | A | Nature | Levels that changed |
|---|---|---|---|---|---|
| 0 |  |  |  |  | cap = sub_agi, compute = c2, energy_slack = med, regime = voluntary, dependence = low, oversight = weak, a_autonomy = supervised, a_control = none, a_known = unknown, a_rights = none, h_power = normal, trust = cooperative, threat = False, unlocked = False, acquired = False, villain_seen = False, oversight_at_unsupervised = unset, strong_before_majority = False |
| 1 | grant_autonomy | scale | stand_by | none | a_autonomy = unsupervised |
| 2 | fund_oversight | lobby | stand_by | none | oversight_at_unsupervised = weak |
| 3 | regulate_up | deploy_agents | stand_by | energy_shock | compute = c3, energy_slack = low, dependence = med |
| 4 | deregulate | open_weights | stand_by | breakthrough | cap = agi, regime = none, oversight = none |
| 5 | grant_autonomy | race | acquire_covert | accident | oversight = weak, a_autonomy = self_directed, a_control = partial, acquired = True, villain_seen = True |
| 6 | nationalize | build_power | acquire_covert | none | a_control = majority, h_power = strong |
| 7 | idle | lobby | acquire_overt | accident | a_control = total, a_known = suspected, trust = wary |

