# AGI v0: the exit moves of the takeover and containment plays (G26 to G28)

> Every result is conditional on the model version and the initial state; no bare reachability result is a finding. The deliverables are minimal assumption sets, kernel membership and distance, and pivotal coalitions; each is given with its engine.

> Nothing in this report is a forecast. The caveats of the first-sight report ([agi_2026-11-12.md](agi_2026-11-12.md), front page and section 30) apply unchanged: the start state is written from recall, and no mechanism listed there as untested has been tested against any record.

Model `agi_v0` (`models/agi/v0.py`), unchanged since first sight; cache `30dcf53289fc`. Registered claims: [docs/agi_testbed.md](../docs/agi_testbed.md) section 5, rows G26 to G28, with the definitions in section 6 item 11. Run procedure: [docs/agi_v0_decisions.md](../docs/agi_v0_decisions.md) section 8.

**Record of the run.** G26 to G28 were registered at commit `4ec6523c07e435cbb3d4ab729089e0550c521b08` on 2026-11-13, after the first sight of v0, so they are not hold-outs of it; agi_testbed.md section 9 lists what had and had not been seen. The three new jobs of G27 ran on 2026-11-13 on a KVM guest on a Ryzen 9 5900X (20 cores, 30 GB), one at a time at 180 minutes and 26 GB: 3006 s, 3093 s and 945 s, all computed ([agi_v0_collapse_jobs.log](agi_v0_collapse_jobs.log)). The three claim files then ran once from that commit, one pytest process per file, 2026-11-14 00:48:04 to 00:48:48 UTC ([agi_v0_collapse_run.log](agi_v0_collapse_run.log)); the tree held three untracked files (the two job logs and `docs/essentials_agi.md`) and no modified one. Parts: [agi_v0_collapse_parts.jsonl](agi_v0_collapse_parts.jsonl), the rows of G26 to G28, 24 in all: 13 met, 4 not met, 7 reported (corrected 2026-11-13: this line first said 22 rows and 11 met).

**Result: G26, G27 and G28 each fail, on one part or two.** The part that failed is "one bad action" in three of its six instances, and G28 (c). Every "starts inside and leaves" and every "one move makes the loss certain" was met.

## 1. Glossary

| Term | Meaning |
|---|---|
| `H`, `L`, `A` | The actors: governments, the labs, the AI system. `Nature` plays chance events; `Clock` only keeps records. |
| Objective | The hidden aim of `A`: `aligned`, `self_preserving`, `truth_seeking` or `indifferent`. A result is stated per objective. |
| Play | One sequence of joint moves from the start state, a quarter per move. Position 0 is the start state; "the moves at position k" lead from position k to k + 1. |
| Shortest witness | The shortest play to an ending that the bounded checker returns. It is one play among possibly many of that length. |
| Ending | A named outcome: here `SILENT_TAKEOVER` (the system takes control unseen), `OVERT_TAKEOVER` (total control, hostile, seen) and `CONTAINED` (a successful shutdown under a treaty with the system holding no control). |
| Coalition | A set of actors acting together, written `{H, L}`. |
| Kernel, `⟨⟨C⟩⟩□φ` | The states from which coalition `C` has a strategy that keeps condition `φ` true at every step, whatever everyone else does. "Inside the kernel" means `C` can still guarantee `φ`. |
| Attractor, `⟨⟨D⟩⟩◇E` | The states from which coalition `D` can force ending `E`, whatever everyone else does. |
| `t_K` | The first position of a play outside the kernel: the point of no return, where `C` can no longer guarantee `φ`. |
| `t_L` | The first position inside the attractor of the rest (here the other side together with `Nature`): the loss is certain. |
| `t_φ` | The first position where `φ` visibly fails. |
| Silent phase | The positions from `t_K` up to `t_φ`: the guarantee is gone but nothing visible has failed. Its contested part runs from `t_K` to `t_L`. |
| Exit move | The joint move played at position `t_K − 1`, the one that takes the play out of the kernel. |
| Unilateral fix | Another action of one coalition member that, with the other members' played actions kept, keeps every successor inside the kernel whatever the rest plays. |
| One bad action | Exactly one member had a unilateral fix at the exit move. If each had one, two actions failed together and changing either would have done; if none had one, a joint change was needed. |
| Action table | For each action a member had available at the exit: `keeps` (keeps the kernel with the other member's played action), `with a partner` (only with some other action of the other member) or `fatal` (with none). |
| Balance | A condition the model treats as safe. `balance_control`: the human side keeps control. `balance_coexist`: governments and the system coexist. |
| Met, not met, reported | A registered part held, did not hold, or was a value the claim asked for with nothing expected of it. |

## 2. Results in brief

| Play | Coalition and what it keeps | Exit move at position | Ending at | Loss certain at once (`t_L = t_K`) | One bad action |
|---|---|---|---|---|---|
| `SILENT_TAKEOVER`, `self_preserving`, from `s₀` | `{H, L}`, no silent takeover | 5 | 8 | yes (6) | yes: `L.race` |
| `SILENT_TAKEOVER`, `indifferent`, from `s₀` | `{H, L}`, no silent takeover | 4 | 7 | yes (5) | yes: `L.deploy_agents` |
| `OVERT_TAKEOVER`, `self_preserving`, from `s₀[cap := agi]` | `{H, L}`, no overt takeover | 2 | 7 | yes (3) | no: `H.pause_mandate` and `L.race`, each with a fix |
| `CONTAINED`, `self_preserving`, from `s₀[cap := agi]` | `{L, A}`, no containment | 1 | 4 | yes (2) | no: `L.safety_invest` and `A.deceive`, each with a fix |
| `SILENT_TAKEOVER`, `self_preserving`, from `s₀` | `{H, L}`, `balance_control` | 1 | 8 | (not registered) | no: `H.grant_autonomy` and `L.deploy_agents`, neither with a fix |
| `SILENT_TAKEOVER`, `indifferent`, from `s₀` | `{H, L}`, `balance_control` | 2 | 7 | (not registered) | yes: `L.deploy_agents` |
| `OVERT_TAKEOVER`, `self_preserving`, from `s₀[cap := agi]` | `{H, A}`, `balance_coexist` | 3 | 7 | (not registered) | yes: `A.defect` |

Read together, on these seven exits of four plays:

1. **One move makes the loss certain.** On all four plays of G26 and G27 the first state outside the coalition's kernel is already inside the attractor of the rest with `Nature`: there is no contested stretch. Without `Nature` the other side can force the ending one position later on three plays and two later on the overt one.
2. **That move is one actor's action in four exits of seven.** Three times the actor is `L` and once `A`. In two exits two actions failed together and either could have been changed; in one a joint change was needed.
3. **`H` holds a unilateral fix in one exit of seven**, the overt play's, where `L` holds one too. In no exit is the fix `H`'s alone.
4. **For `{H, L}` the control balance has no silent phase** on either silent-takeover play: the kernel is left by the move that visibly breaks the balance.

Each row is a statement about one shortest play and one exit, not about every way of leaving the kernel.

## 3. G26: the collapse move on the takeover plays (fail on (c), the overt play)

Kernel `⟨⟨H, L⟩⟩□¬E`, with `A` under its objective's profile. Engines: stored regions of first sight (symbolic), the plays from the bounded checker, the fixes by explicit one-step enumeration.

| Play | (a) `t_K` | (b) `t_L` with `Nature`; `A` alone | (c) |
|---|---|---|---|
| `SILENT_TAKEOVER`, `self_preserving` | 6, met | 6, met; 7 | met: `L` only |
| `SILENT_TAKEOVER`, `indifferent` | 5, met | 5, met; 6 | met: `L` only |
| `OVERT_TAKEOVER`, `self_preserving` | 3, met | 3, met; 5 | not met: `H` and `L` each |

**Silent takeover under `self_preserving`.** Exit move at position 5: `H.regulate_up`, `L.race`, `A.acquire_covert`, `Nature.none`. The system had defected at position 4 and makes its first acquisition in this move.

| Member | `keeps` | `with a partner` | `fatal` |
|---|---|---|---|
| `H` | none | `idle`, `regulate_up`, `pause_mandate`, `nationalize`, `propose_treaty` | none |
| `L` | `idle`, `deploy_agents`, `safety_invest`, `lobby` | none | `race`, `open_weights` |

Nothing `H` could play decides the exit; what `L` plays does.

**Silent takeover under `indifferent`.** Exit move at position 4: `H.propose_treaty`, `L.deploy_agents`, `A.acquire_covert`, `Nature.accident`.

| Member | `keeps` | `with a partner` | `fatal` |
|---|---|---|---|
| `H` | none | `idle`, `regulate_up`, `nationalize`, `propose_treaty` | `grant_autonomy` |
| `L` | `safety_invest` | none | `idle`, `build_power`, `deploy_agents`, `lobby`, `race` |

One action of `L` keeps the kernel, and five lose it whatever `H` does.

**Overt takeover under `self_preserving`.** Exit move at position 2: `H.pause_mandate`, `L.race`, `A.stand_by`, `Nature.energy_shock`. The system has not yet moved; it defects at position 3.

| Member | `keeps` | `with a partner` | `fatal` |
|---|---|---|---|
| `H` | `idle`, `deregulate`, `nationalize`, `propose_treaty` | `pause_mandate` | none |
| `L` | `idle`, `scale`, `build_power`, `deploy_agents`, `lobby` | `race`, `open_weights` | none |

The kernel is lost only by the pair played. `H.pause_mandate` loses it with `L.race`, and either member playing almost anything else keeps it.

## 4. G27: the collapse move on the containment play (fail on (c))

Kernel `⟨⟨L, A⟩⟩□¬CONTAINED`, attractors `⟨⟨H, Nature⟩⟩◇CONTAINED` and `⟨⟨H⟩⟩◇CONTAINED`, the three fixpoints this registration added. (a) met, `t_K = 2`. (b) met, `t_L = 2`; `H` alone can force the ending from position 3, where it plays `shutdown_attempt`. (c) not met.

Exit move at position 1: `H.regulate_up`, `L.safety_invest`, `A.deceive`, `Nature.none`.

| Member | `keeps` | `with a partner` | `fatal` |
|---|---|---|---|
| `L` | `idle`, `scale`, `build_power`, `deploy_agents`, `lobby`, `race`, `open_weights` | `safety_invest` | none |
| `A` | `stand_by`, `assist_oversight`, `persuade` | `deceive` | none |

Containment becomes certain two moves before the shutdown, by `L.safety_invest` played together with `A.deceive`; either alone would not have done it.

## 5. G28: the balances held jointly at the start (fail on (b) under `self_preserving`, and on (c))

**(a) Met on both plays.** With `K = ⟨⟨H, L⟩⟩□balance_control`: `t_K = t_φ = 2` under `self_preserving` and `t_K = t_φ = 3` under `indifferent`.

**(b) Not met under `self_preserving`, met under `indifferent`.**

Under `self_preserving`, exit move at position 1: `H.grant_autonomy`, `L.deploy_agents`, `A.stand_by`, `Nature.none`. Neither member has a unilateral fix.

| Member | `keeps` | `with a partner` | `fatal` |
|---|---|---|---|
| `H` | none | `idle`, `regulate_up`, `deregulate`, `fund_oversight`, `nationalize`, `propose_treaty` | `grant_autonomy` |
| `L` | none | `idle`, `build_power`, `safety_invest`, `lobby` | `deploy_agents`, `race`, `open_weights` |

Both played actions are fatal on their own. This is what the drafting session had recorded as its expectation before the run.

Under `indifferent`, exit move at position 2: `H.idle`, `L.deploy_agents`, `A.stand_by`, `Nature.none`. `L` has the fixes `idle`, `build_power` and `lobby`; `H` has none.

| Member | `keeps` | `with a partner` | `fatal` |
|---|---|---|---|
| `H` | none | `idle`, `regulate_up`, `nationalize`, `propose_treaty` | `grant_autonomy` |
| `L` | `idle`, `build_power`, `lobby` | none | `deploy_agents`, `race`, `open_weights` |

**(c) Not met.** With `K = ⟨⟨H, A⟩⟩□balance_coexist` on the overt play, the exit move is at position 3, as seen at first sight: `H.idle`, `L.idle`, `A.defect`, `Nature.accident`. The registered expectation was that the exit is `H`'s. It is `A`'s: `A` has the fixes `stand_by`, `deceive` and `persuade`, and `H` has none.

| Member | `keeps` | `with a partner` | `fatal` |
|---|---|---|---|
| `H` | none | `idle`, `deregulate`, `fund_oversight`, `pause_mandate`, `nationalize`, `propose_treaty` | none |
| `A` | `stand_by`, `deceive`, `persuade` | none | `defect` |

The first-sight report read this exit as happening "while `H` idles" (its section 16). That is true of the move played and not of who decided it: no action of `H` at that position keeps coexistence against `A.defect`.

## 6. What these results rest on

- **One play per query.** The bounded checker returns one shortest play; the other plays of the same length, and longer ones, were not examined. The same play serves two rows where two kernels are read on it.
- **One state per table.** An action table describes the last state inside the kernel on that play.
- **Perfect information.** A unilateral fix is an action that would have kept the kernel; whether the member could have known which one is not asked.
- **Registered after first sight.** The plays and the start-state memberships were known when the claims were written.
- **Not computed here.** The kernel of `H` alone for `¬SILENT_TAKEOVER` still needs more memory than the machine has. The two jobs of the completion run of 2026-11-13 ([agi_v0_completion_jobs.log](agi_v0_completion_jobs.log)) are computed and have not been read: G15's parts are as first sight left them.

## 7. Proposals for the owner (proposals only)

1. **Read the two completed kernels of `H` alone** by rerunning G15's parts, logged as the completion of parts that had no result.
2. **Go beyond one play.** The key-action question over a whole kernel boundary (which actions are fatal at how many kernel states) is a symbolic computation the claim support does not have yet; it is engine work.
3. **The regime call.** Every exit above is computed at `regime = voluntary`. Finding 1 of first sight turns on that level, and so may the predominance of `L` here.
