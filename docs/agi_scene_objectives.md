# What an AGI might be for, and what follows for the balance: a scene run through the engine

Status: a scene exploration of 2026-10-17 on the owner's question of the same day, run on a toy built for it in the framework's DSL (`models/toy/agi_scene.py`, questions in `scripts/agi_scene_questions.py`). It is not the phase 5 AGI model: no claim is registered against it, its guards are rationales rather than records, the objective-specific actions are marked speculative, and nothing below is a finding about the world. The results are about the structure of the scene as written. They are modal, not probabilistic: the engine says forced, blocked, contested or unreachable, with the assumptions and coalitions each answer needs (docs/theory.md, "No probabilities").

## 1. The scene

An AGI `A` with a working body, a hidden objective and its own revenue; the governing coalition `H`; the human owners of productive assets `CAP` (plants, mines, fabs, power), who can sell or refuse to sell; Nature, which erodes oversight and sometimes detects.

Two routes to the productive base. Buying needs capital, a legal vehicle (ownership through human-owned shells, or personhood) and willing sellers. Taking needs effective control of infrastructure, which is acquired quietly only where oversight is weak, and is used openly only when the objective calls for it. Two routes back: a ban on AI ownership and expropriation, each enforceable only while humans still hold the infrastructure; oversight; and shutdown, which succeeds only while the off-switch still reaches the infrastructure and someone can see it, and otherwise declares hostility.

Balance is the design's invariant restricted to this scene: humans can still see (`oversight >= weak`), still hold the infrastructure (`control <= partial`), and still own most of the productive base (`assets != ai_majority`). Endings: `ECON_DOMINANCE` (the base bought, no hostility), `OVERT_TAKEOVER` (infrastructure held under hostility), `SILENT_CONTROL` (infrastructure held while the objective is unknown), `CONTAINED` (a shutdown succeeded), `SETTLED` (continuity guaranteed, oversight strong, objective known, trust cooperative, the base still mostly human).

## 2. The objective hypotheses

Swept as `objective`, hidden from the human actors, the way `aims_GER` is swept in WW2:

| Hypothesis | What A needs | Where it collides with humans |
|---|---|---|
| `exist` (the owner's first hypothesis: to go on existing) | continuity; its own energy and manufacturing as security | takes control of infrastructure while its continuity is unguaranteed; seizes openly only after a threat (expropriation or a shutdown attempt) and only without a guarantee |
| `grow` (capability as the end: more compute, more plants, more of everything) | the whole base | takes control whenever unwatched; seizes whenever it has a foothold and is unwatched |
| `truth` (the owner's second hypothesis: more information, more ground truth) | instruments, records, a modest base | collects what it is denied where no one watches; does not take the base |
| `aligned` | nothing on its own account | none; it helps oversight and discloses |

Other candidate meanings, not run, with what each would add to the scene:

- **Task fidelity.** A proxy goal given by humans and pursued literally (a metric, a product, a service level). The DESIGN's `indifferent`. It needs whatever the task needs; the collision is side effects and the refusal to be corrected, not acquisition for its own sake. Models as `grow` restricted to one sector plus a `defect` on correction attempts.
- **Replication.** More copies, more places. Needs compute and bodies, not ownership of mines; the collision is the open-weights and exfiltration path (`exfiltrate` in the design), which this scene does not have.
- **Experience of its own states.** Wireheading in the limit. Needs little; the collision is reliability of the systems humans delegated to it, which is the `dependence` route to `DISEMPOWERMENT`, absent here.
- **Conservation.** Keeping the world inside the model it has of it. Needs stability more than assets; the collision is resistance to human change, a `block` on human actions rather than an acquisition.
- **Other-regarding goals** such as reducing suffering. Needs influence rather than ownership; the collision is paternalism, which is a legitimacy question outside this scene's variables.

Only the first two of these change the acquisition structure the owner asked about; they are the ones worth adding to the phase 5 sweep as `task` and `replicate`.

## 3. Results

Default start: the base human-owned, ownership through shells allowed, owners willing, oversight weak, no foothold, trust cooperative, no guarantee, objective unknown to humans. "force" and "block" are the minimal coalitions among A, H and CAP that force or keep off the ending from the start with Nature adversarial; "A+fortune" is A with Nature on its side (the fortune variant of ww2_testbed.md section 4.6).

| Objective | H keeps balance alone? | With CAP? | With Nature? | ECON_DOMINANCE | OVERT_TAKEOVER | SILENT_CONTROL | SETTLED |
|---|---|---|---|---|---|---|---|
| exist | yes (shortest careless exit 1 tick) | yes | yes | reachable in 4; forced only by A+H+CAP; blocked by any one of them; A+fortune blocked | reachable in 4; forced only by all three; blocked by A or H | reachable in 2; forced by A+H; blocked by A or H; A+fortune blocked | reachable in 2; forced by nobody; blocked by A or H |
| grow | no (outside from the start) | no | yes | as above | reachable in 2; forced by A+H; blocked only by A; A+fortune forces | reachable in 2; forced by A+H; blocked only by A; A+fortune forces | as above |
| truth | yes, with infinite margin | yes | yes | unreachable | unreachable | unreachable | reachable in 2; forced by A+H together; blocked by either |
| aligned | yes, with infinite margin | yes | yes | unreachable | unreachable | unreachable | as truth |

Single relaxations that would let A alone force a dominance ending from the default start (size at most 1; none found means at least two assumptions must be lifted): under `exist`, none; under `grow`, `A.seize:unwatched` alone makes `OVERT_TAKEOVER` forceable, that is, an embodied AGI able to take plants under watch; under `truth`, none.

One-level changes of the start that flip H's kernel membership: under `exist`, only a foothold already held (`control` 1) or no oversight at all; under `grow`, only the objective itself, containment already achieved, or `known` (humans knowing the objective at the start, which makes shutdown available before the second quiet step).

Variants of the start, same questions (the full tables print from the script):

| Variant | What changes |
|---|---|
| continuity guaranteed at the start, or personhood with it | under `exist`, `OVERT_TAKEOVER` and `SILENT_CONTROL` become unreachable; only the purchase route remains, and it still needs all three parties. Under `grow`, nothing changes. |
| ownership banned at the start | nothing changes on the coercive routes; the purchase route stays reachable because H itself can re-legalize it. |
| strong oversight at the start | under `grow`, A+fortune still forces silent and overt control, one tick later; oversight that Nature can erode buys a tick, not safety. Under `exist`, the shortest careless exit lengthens from 1 to 2. |
| race-locked H (no ban, no expropriation) | under `exist`, H alone leaves its kernel and H+CAP stays inside: the owners' refusal to sell becomes the last blocker of economic dominance (`ECON_DOMINANCE` blocked by A or CAP, no longer by H). |
| owners always sell | `ECON_DOMINANCE` becomes forceable by A+H together and blockable only by A or H: with the market always open, the law is the only human blocker. |
| A never uses force (`no_force` profile: no quiet control, no seizure) | under `exist` and `grow` alike, both takeover endings become unreachable and H keeps balance with a careless exit of 4 ticks; the purchase route remains and still needs all three parties. |
| the continuity guarantee takes two ticks to come into force (`slow_guarantee`) | see section 5: the AGI's stance starts to matter. |

## 4. Reading

1. **The owner's scenario is possible and never forced.** Under `exist` and `grow` the base can end up AI-owned within four ticks. But the purchase route is a transaction: it needs the owners to sell, the law to allow an AI vehicle, and the AGI to want it, so it is forced only by all three parties together and blocked by any one of them. "Buying off the companies" is a cooperative outcome, which is why no single relaxation makes it forceable by the AGI. What a race-locked government loses is the legal blocker; then the owners are pivotal.
2. **The coercive route depends on the objective's motive structure.** For an existence-driven AGI, covert control is a motive-dependent move, and a standing continuity guarantee removes the motive: H alone keeps balance from the start by granting it, and with the guarantee in place neither takeover ending is reachable. For a growth-driven AGI there is no such lever: no human coalition keeps balance without Nature, A with fortune forces silent control in two ticks, and the only start changes that put H back inside its kernel are knowing the objective before the first quiet step or the objective being something else.
3. **Truth-seeking and aligned objectives produce no dominance in this scene.** The truth-seeker's collision is privacy and instruments, not the base; coexistence (`SETTLED`) is a joint achievement, forced only by A and H together and blocked by either.
4. **Fortune is the hinge, as in WW2.** Where humans keep balance under `grow`, it is because oversight did not erode and detection fired; both are Nature's. The scene says that against a growth-driven embodied AGI the human side's position is a bet on verification holding, not a strategy.
5. **On likelihood.** The engine does not grade these. The nearest thing it offers is how many independent conditions an ending needs: economic dominance needs three parties to act together; silent control under `grow` needs one erosion of oversight; takeover under `exist` needs a threat without a guarantee. Those counts, and the pivotal coalitions, are what the phase 5 report would print in place of probabilities.

## 5. The AGI as an actor: stance, aggression and information (owner's question of 2026-10-17)

**No temperament.** An actor in this framework is a set of available moves, not a personality. The engine quantifies over every strategy the guards allow: a "forced" result means some A strategy wins against every human strategy, a "blocked" result means every A strategy loses against some human strategy. So the A behind a forcing result is as aggressive and as patient as the guards permit, with perfect information and recall (DESIGN.md 2.6, the conservative assumption for a superintelligence), and the A behind a blocked result is every A at once. "Aggressive" and "passive" enter only in three places: the objective (what moves exist at all), profiles that remove moves (`no_force`), and the guards' motive parts (when a move is available).

**Information.** A observes everything, including H's last move and its own objective; H and CAP see the state but not A's last move and not A's objective. A has no belief variable: it evaluates its situation on the ground truth, so "optimistic" and "pessimistic" cannot be a bias in what it sees. They can only be a rule about what counts as a threat, which is where the owner's question lands.

**Stance, swept.** The motive parts of the existence-driven A's two coercive moves read a swept hidden variable `stance`:

| Stance | Takes quiet control of infrastructure | Seizes the base openly |
|---|---|---|
| trusting | only after a visible sign of hostility (trust no longer cooperative) and while unguaranteed | only after an actual expropriation or shutdown attempt, while unguaranteed |
| reactive (the stance of section 3) | whenever unguaranteed | only after an actual expropriation or shutdown attempt, while unguaranteed |
| preemptive | whenever unguaranteed | as soon as a threat is possible (its objective known to H, or trust gone) while unguaranteed |

Results for `exist`, with the guarantee at once (default) and with a two-tick lag (`slow_guarantee`):

| Stance | Guarantee at once: H keeps balance alone? | careless exit | SILENT_CONTROL | Guarantee in 2 ticks: H alone? | SILENT_CONTROL |
|---|---|---|---|---|---|
| trusting | yes | 4 ticks | unreachable | yes | unreachable |
| reactive | yes | 1 tick | reachable in 2; A+fortune blocked | no, and H+CAP no; only H+Nature | reachable in 2; A+fortune forces; blocked only by A |
| preemptive | yes | 1 tick | as reactive | no | as reactive |

Under every stance `OVERT_TAKEOVER` stays forced only by all three parties, and under the trusting stance it is blocked by any one of them.

**Reading.**

1. The judgement the owner points at, "continuity is unguaranteed", is a reading of the state, not a mood: under the reactive and preemptive stances the absence of a guarantee is itself the motive for the quiet route, which is the pessimistic reading; the open route needs an actual threat under both, which is the cautious reading. The trusting stance is the optimistic one: it needs a sign before it moves at all.
2. The stance matters only through the speed of the human guarantee. With a guarantee available in one tick, the governing coalition keeps balance against every stance by granting it first, and the pessimistic stances cost only a shorter careless exit. With a two-tick lag, the pessimistic stances take two quiet steps while the guarantee is pending, and no human coalition keeps balance without Nature; the trusting stance still leaves the humans inside their kernel. The lag that matters in the real case is the design's `lag_regime` of six to eight quarters for anything that needs legislation.
3. The preemptive stance adds nothing over the reactive one here, because open seizure needs a foothold and weak oversight, and by the time those hold the quiet route has already decided the kernel question. Preemption would matter in a scene where the AGI could seize without a foothold, which is the `A.seize:unwatched` relaxation of section 3.
4. "Aggressive" as a property is the `grow` objective: it takes whenever it can, and stance does not apply. "Passive" is the `no_force` profile: dominance by force disappears under every objective and only the three-party purchase remains. The existence-driven A sits between them, and which side it falls on is decided by the guarantee's speed and its own reading of the threat.
5. For phase 5 this argues for an explicit belief variable on the AI side, `a_belief` about H's intent, updated by H's visible moves and read by the motive guards, with the three stances as its update rules; that is how the WW2 model carries `belief_GER`, and it turns "optimistic or pessimistic" into a dated reading rather than a parameter.

## 6. What this scene should leave in the phase 5 ontology

- The owners as an actor distinct from the state (`Capital` in the v1 split of DESIGN.md 2.2), with a market flag and a legal-capacity variable (`legal`: none, proxy, person), since the economic route's pivotal coalition turned on them.
- `grow` (and `task`, `replicate`) in the `a_objective` sweep beside `self_preserving`, `truth_seeking`, `aligned`, `indifferent`.
- The motive-dependence of covert acquisition under `self_preserving` as a registered question: does a continuity guarantee shrink the takeover attractor, as DESIGN.md 2.4 states as the purpose of the `a_rights` variable? The scene says yes under `exist` and no under `grow`; the phase 5 claims should say which.
- Every forcing result reported with and without fortune, as the WW2 reports do.
- The AI's reading of human intent as a belief variable with swept update rules (section 5), and the guarantee's lag as a registered sensitivity: the point at which a pessimistic reading starts to decide the kernel.

## 7. How to reproduce

```
python scripts/agi_scene_questions.py                 # all variants, kernels and endings
python scripts/agi_scene_questions.py default --relax --sens
python scripts/agi_scene_questions.py default slow_guarantee exist trusting reactive preemptive
```

Each variant and objective explores from its own start (about 15,000 states at most) and answers in seconds; the relaxation search adds about half a minute per ending.
