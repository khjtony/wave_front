# AGI v0: the no-return moves of the takeover and AI contained paths (G26 to G28)

> Terms updated on 18 November 2026 to match docs/agi_glossary.html. Numbers and findings are unchanged.

> Every result is conditional on the model version and the initial state; no bare reachability result is a finding. The deliverables are minimal assumption sets, guarantee zone readings (inside or outside) and distance, and pivotal players; each is given with its engine.

> Nothing in this report is a forecast. The caveats of the first-run report ([agi_2026-11-12.md](agi_2026-11-12.md), front page and section 30) apply unchanged: the start state is written from recall, and no mechanism listed there as untested has been tested against any record.

Model `agi_v0` (`models/agi/v0.py`), unchanged since the first run; cache `30dcf53289fc`. Pre-registered claims: [docs/agi_testbed.md](../docs/agi_testbed.md) section 5, rows G26 to G28, with the definitions in section 6 item 11. Run procedure: [docs/agi_v0_decisions.md](../docs/agi_v0_decisions.md) section 8.

**Record of the run.** G26 to G28 were pre-registered at commit `4ec6523c07e435cbb3d4ab729089e0550c521b08` on 2026-11-13, after the first run of v0, so they are not hold-outs of it; agi_testbed.md section 9 lists what had and had not been seen. The three new jobs of G27 ran on 2026-11-13 on a KVM guest on a Ryzen 9 5900X (20 cores, 30 GB), one at a time at 180 minutes and 26 GB: 3006 s, 3093 s and 945 s, all computed ([agi_v0_collapse_jobs.log](agi_v0_collapse_jobs.log)). The three claim files then ran once from that commit, one pytest process per file, 2026-11-14 00:48:04 to 00:48:48 UTC ([agi_v0_collapse_run.log](agi_v0_collapse_run.log)); the tree held three untracked files (the two job logs and `docs/essentials_agi.md`) and no modified one. Parts: [agi_v0_collapse_parts.jsonl](agi_v0_collapse_parts.jsonl), the rows of G26 to G28, 24 in all: 13 held, 4 did not hold, 7 reported (corrected 2026-11-13: this line first said 22 rows and 11 held).

**Result: G26, G27 and G28 each did not hold, on one part or two.** The part that did not hold is "one bad action" in three of its six instances, and G28 (c). Every "starts inside and leaves" and every "one round makes the loss certain" held.

## 1. Glossary

| Term | Meaning |
|---|---|
| `H`, `L`, `A` | The actors: governments, the frontier AI companies, the frontier AI system. `Nature` is By chance, the events nobody chooses; `Clock` is the record writer, which only writes records. |
| AI goal | The hidden aim of `A`: `aligned`, `self_preserving`, `truth_seeking` or `indifferent`. A result is stated per goal. |
| Path | One sequence of rounds from the start state, a quarter per round. Position 0 is the start state; "the round at position k" leads from position k to k + 1. |
| Shortest path | The shortest path to an ending that the bounded checker returns. It is one path among possibly many of that length. |
| Ending | A named outcome: here `SILENT_TAKEOVER` (the frontier AI system takes control unseen), `OVERT_TAKEOVER` (total control, hostile, seen) and `CONTAINED` (a successful shutdown under a treaty with the frontier AI system holding no control). |
| Alliance | A set of actors acting together, written `{H, L}`. |
| Guarantee zone, `⟨⟨C⟩⟩□φ` | The states from which alliance `C` has a strategy that keeps condition `φ` true at every step, whatever everyone else does. "Inside the guarantee zone" means `C` can still guarantee `φ`. |
| Forcing zone, `⟨⟨D⟩⟩◇E` | The states from which alliance `D` can force ending `E`, whatever everyone else does. |
| `t_K` | The first position of a path outside the guarantee zone: the point of no return, where `C` can no longer guarantee `φ`. |
| `t_L` | The first position inside the forcing zone of the rest (here the other side together with `Nature`): the loss is certain. |
| `t_φ` | The first position where `φ` visibly fails. |
| Silent phase | The positions from `t_K` up to `t_φ`: the guarantee is gone but nothing visible has failed. Its contested part runs from `t_K` to `t_L`. |
| No-return move | The round at position `t_K − 1`, the one that takes the path out of the guarantee zone. |
| Preventing action | Another action of one alliance member that, with the other members' chosen actions kept, keeps every successor inside the guarantee zone whatever the rest chooses. |
| One bad action | Exactly one member had a preventing action at the no-return move. If each had one, two actions failed together and changing either would have done; if none had one, a joint change was needed. |
| Action table | For each action a member had available at the no-return move: `keeps` (keeps the guarantee zone with the other member's chosen action), `with a partner` (only with some other action of the other member) or `fatal` (with none). |
| Safe condition | A condition the model treats as safe. `balance_control`: governments with the frontier AI companies keep control. `balance_coexist`: governments and the frontier AI system coexist. |
| Held, did not hold, reported | A pre-registered part held, did not hold, or was a value the claim asked for with nothing predicted for it. |

## 2. Results in brief

| Path | Alliance and what it keeps | No-return move at position | Ending at | Loss certain at once (`t_L = t_K`) | One bad action |
|---|---|---|---|---|---|
| `SILENT_TAKEOVER`, `self_preserving`, from `s₀` | `{H, L}`, no silent takeover | 5 | 8 | yes (6) | yes: `L.race` |
| `SILENT_TAKEOVER`, `indifferent`, from `s₀` | `{H, L}`, no silent takeover | 4 | 7 | yes (5) | yes: `L.deploy_agents` |
| `OVERT_TAKEOVER`, `self_preserving`, from `s₀[cap := agi]` | `{H, L}`, no visible takeover | 2 | 7 | yes (3) | no: `H.pause_mandate` and `L.race`, each with a preventing action |
| `CONTAINED`, `self_preserving`, from `s₀[cap := agi]` | `{L, A}`, AI not contained | 1 | 4 | yes (2) | no: `L.safety_invest` and `A.deceive`, each with a preventing action |
| `SILENT_TAKEOVER`, `self_preserving`, from `s₀` | `{H, L}`, `balance_control` | 1 | 8 | (not pre-registered) | no: `H.grant_autonomy` and `L.deploy_agents`, neither with a preventing action |
| `SILENT_TAKEOVER`, `indifferent`, from `s₀` | `{H, L}`, `balance_control` | 2 | 7 | (not pre-registered) | yes: `L.deploy_agents` |
| `OVERT_TAKEOVER`, `self_preserving`, from `s₀[cap := agi]` | `{H, A}`, `balance_coexist` | 3 | 7 | (not pre-registered) | yes: `A.defect` |

Read together, on these seven points of no return on four paths:

1. **One round makes the loss certain.** On all four paths of G26 and G27 the first state outside the alliance's guarantee zone is already inside the forcing zone of the rest with `Nature`: there is no contested stretch. Without `Nature` the other side can force the ending one position later on three paths and two later on the visible takeover one.
2. **That round is one actor's action at four points of no return of seven.** Three times the actor is `L` and once `A`. At two points of no return two actions failed together and either could have been changed; at one a joint change was needed.
3. **`H` holds a preventing action at one point of no return of seven**, the visible takeover path's, where `L` holds one too. At no point of no return is the preventing action `H`'s alone.
4. **For `{H, L}` the control balance has no silent phase** on either silent-takeover path: the guarantee zone is left by the round that visibly breaks the balance.

Each row is a statement about one shortest path and one point of no return, not about every way of leaving the guarantee zone.

## 3. G26: the collapse move on the takeover paths (did not hold on (c), the visible takeover path)

Guarantee zone `⟨⟨H, L⟩⟩□¬E`, with `A` true to its goal. Engines: stored zones of the first run (symbolic), the paths from the bounded checker, the preventing actions by explicit one-step enumeration.

| Path | (a) `t_K` | (b) `t_L` with `Nature`; `A` alone | (c) |
|---|---|---|---|
| `SILENT_TAKEOVER`, `self_preserving` | 6, held | 6, held; 7 | held: `L` only |
| `SILENT_TAKEOVER`, `indifferent` | 5, held | 5, held; 6 | held: `L` only |
| `OVERT_TAKEOVER`, `self_preserving` | 3, held | 3, held; 5 | did not hold: `H` and `L` each |

**Silent takeover under `self_preserving`.** No-return move at position 5: `H.regulate_up`, `L.race`, `A.acquire_covert`, `Nature.none`. The frontier AI system had turned hostile at position 4 and makes its first acquisition in this round.

| Member | `keeps` | `with a partner` | `fatal` |
|---|---|---|---|
| `H` | none | `idle`, `regulate_up`, `pause_mandate`, `nationalize`, `propose_treaty` | none |
| `L` | `idle`, `deploy_agents`, `safety_invest`, `lobby` | none | `race`, `open_weights` |

Nothing `H` could choose decides the point of no return; what `L` chooses does.

**Silent takeover under `indifferent`.** No-return move at position 4: `H.propose_treaty`, `L.deploy_agents`, `A.acquire_covert`, `Nature.accident`.

| Member | `keeps` | `with a partner` | `fatal` |
|---|---|---|---|
| `H` | none | `idle`, `regulate_up`, `nationalize`, `propose_treaty` | `grant_autonomy` |
| `L` | `safety_invest` | none | `idle`, `build_power`, `deploy_agents`, `lobby`, `race` |

One action of `L` keeps the guarantee zone, and five lose it whatever `H` does.

**Visible takeover under `self_preserving`.** No-return move at position 2: `H.pause_mandate`, `L.race`, `A.stand_by`, `Nature.energy_shock`. The frontier AI system has not yet acted; it turns hostile at position 3.

| Member | `keeps` | `with a partner` | `fatal` |
|---|---|---|---|
| `H` | `idle`, `deregulate`, `nationalize`, `propose_treaty` | `pause_mandate` | none |
| `L` | `idle`, `scale`, `build_power`, `deploy_agents`, `lobby` | `race`, `open_weights` | none |

The guarantee zone is lost only by the pair chosen. `H.pause_mandate` loses it with `L.race`, and either member choosing almost anything else keeps it.

## 4. G27: the collapse move on the AI contained path (did not hold on (c))

Guarantee zone `⟨⟨L, A⟩⟩□¬CONTAINED`, forcing zones `⟨⟨H, Nature⟩⟩◇CONTAINED` and `⟨⟨H⟩⟩◇CONTAINED`, the three fixpoints this pre-registration added. (a) held, `t_K = 2`. (b) held, `t_L = 2`; `H` alone can force the ending from position 3, where it chooses `shutdown_attempt`. (c) did not hold.

No-return move at position 1: `H.regulate_up`, `L.safety_invest`, `A.deceive`, `Nature.none`.

| Member | `keeps` | `with a partner` | `fatal` |
|---|---|---|---|
| `L` | `idle`, `scale`, `build_power`, `deploy_agents`, `lobby`, `race`, `open_weights` | `safety_invest` | none |
| `A` | `stand_by`, `assist_oversight`, `persuade` | `deceive` | none |

AI contained becomes certain two rounds before the shutdown, by `L.safety_invest` chosen together with `A.deceive`; either alone would not have done it.

## 5. G28: the safe conditions held jointly at the start (did not hold on (b) under `self_preserving`, and on (c))

**(a) Held on both paths.** With `K = ⟨⟨H, L⟩⟩□balance_control`: `t_K = t_φ = 2` under `self_preserving` and `t_K = t_φ = 3` under `indifferent`.

**(b) Did not hold under `self_preserving`, held under `indifferent`.**

Under `self_preserving`, no-return move at position 1: `H.grant_autonomy`, `L.deploy_agents`, `A.stand_by`, `Nature.none`. Neither member has a preventing action.

| Member | `keeps` | `with a partner` | `fatal` |
|---|---|---|---|
| `H` | none | `idle`, `regulate_up`, `deregulate`, `fund_oversight`, `nationalize`, `propose_treaty` | `grant_autonomy` |
| `L` | none | `idle`, `build_power`, `safety_invest`, `lobby` | `deploy_agents`, `race`, `open_weights` |

Both chosen actions are fatal on their own. This is what the drafting session had recorded as its predicted result before the run.

Under `indifferent`, no-return move at position 2: `H.idle`, `L.deploy_agents`, `A.stand_by`, `Nature.none`. `L` has the preventing actions `idle`, `build_power` and `lobby`; `H` has none.

| Member | `keeps` | `with a partner` | `fatal` |
|---|---|---|---|
| `H` | none | `idle`, `regulate_up`, `nationalize`, `propose_treaty` | `grant_autonomy` |
| `L` | `idle`, `build_power`, `lobby` | none | `deploy_agents`, `race`, `open_weights` |

**(c) Did not hold.** With `K = ⟨⟨H, A⟩⟩□balance_coexist` on the visible takeover path, the no-return move is at position 3, as seen at the first run: `H.idle`, `L.idle`, `A.defect`, `Nature.accident`. The pre-registered predicted result was that the no-return move is `H`'s. It is `A`'s: `A` has the preventing actions `stand_by`, `deceive` and `persuade`, and `H` has none.

| Member | `keeps` | `with a partner` | `fatal` |
|---|---|---|---|
| `H` | none | `idle`, `deregulate`, `fund_oversight`, `pause_mandate`, `nationalize`, `propose_treaty` | none |
| `A` | `stand_by`, `deceive`, `persuade` | none | `defect` |

The first-run report read this point of no return as passed "while `H` does nothing" (its section 16). That is true of the round chosen and not of who decided it: no action of `H` at that position keeps peaceful coexistence against `A.defect`.

## 6. What these results rest on

- **One path per query.** The bounded checker returns one shortest path; the other paths of the same length, and longer ones, were not examined. The same path serves two rows where two guarantee zones are read on it.
- **One state per table.** An action table describes the last state inside the guarantee zone on that path.
- **Perfect information.** A preventing action is an action that would have kept the guarantee zone; whether the member could have known which one is not asked.
- **Pre-registered after the first run.** The paths and the start-state inside/outside readings were known when the claims were written.
- **Not computed here.** The guarantee zone of `H` alone for `¬SILENT_TAKEOVER` still needs more memory than the machine has. The two jobs of the completion run of 2026-11-13 ([agi_v0_completion_jobs.log](agi_v0_completion_jobs.log)) are computed and have not been read: G15's parts are as the first run left them.

## 7. Proposals for the owner (proposals only)

1. **Read the two completed guarantee zones of `H` alone** by rerunning G15's parts, logged as the completion of parts that had no result.
2. **Go beyond one path.** The key-action question over a whole guarantee zone boundary (which actions are fatal at how many guarantee zone states) is a symbolic computation the claim support does not have yet; it is engine work.
3. **The uncertain reading of regulation strictness.** Every point of no return above is computed at `regime = voluntary`. Finding 1 of the first run turns on that level, and so may the predominance of `L` here.
