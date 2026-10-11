# Theory

This note gives the formal objects behind the `wavefront` framework, the logic fragment it decides, the algorithms, and the statements the engine's outputs rest on. It is written against [framework_spec.md](framework_spec.md) (cited as "spec §n"); where the two disagree, the spec is the contract and this note is wrong. Design motivation is in [DESIGN.md](DESIGN.md). Phase 0 status: sections 1 to 6, 8 and 9 describe what phase 0 implements; section 7 is a design hook only.

Notation. `Agt` is the set of actors, Nature `N` included. For a coalition `C ⊆ Agt`, `C̄ = Agt ∖ C` is the rest, which contains Nature unless `N ∈ C`. Levels are indices. `[[e]]` is the set of states where expression `e` holds.

---

## 1. Objects

### 1.1 The game

A compiled model (spec §1, §4) is a finite concurrent game

```
G = (Var, D, I, Agt, Act, avail, δ, Term, Obs)
```

| Component | Definition |
|---|---|
| `Var` | variables in declaration order, followed by the built-ins: `tick`, `last_<a>`, `pending_<a>_<α>`, `fair_<f>`, latch variables |
| `D(v)` | `{0, …, n_v − 1}`: level indices, counter values `0..max`, or `{0, 1}` for flags |
| `S` | `Π_v D(v)`; a state is a tuple of indices. Only the reachable part is built |
| `I ⊆ S` | `Π_v I_v` with `I_v = {init(v)}`, or `I_v = D(v)` when `init=None`; built-ins start at 0, `none` or `unset` |
| `Agt` | the declared actors, then `N` |
| `Act_a` | `a`'s declared actions plus `idle` (unless `idle=False`); `Act_N` contains `none` |
| `avail(a, s)` | the actions of `a` available in `s` (below) |
| `δ : S × Π_a Act_a → S` | deterministic step: effects, then system updates (below) |
| `Term ⊆ S` | `[[tick = horizon]] ∪ ⋃_E [[E]]` over the declared endings |
| `Obs(a) ⊆ Var` | the variables `a` observes; `Obs(N) = Var` |

**Availability.** `α ∈ avail(a, s)` iff all of the following hold:
1. `s ⊨ guard_α`;
2. `pending_<a>_<α>(s) = 0` when `α` has a delay;
3. for every fairness constraint `f` of `a` with `fair_f(s) = within_f`, `α ∈ responses_f`;
4. if a profile `p` is selected and forbids `α` for `a`, then `s ⊨ unless_p`.

The engine checks that `avail(a, s) ≠ ∅` for every actor and every non-terminal reachable state (spec §1). This matters below: the universal quantifier in the controllable predecessor is never vacuous.

**Joint moves.** `Moves(s) = Π_a avail(a, s)` for `s ∉ Term`, and `Moves(s) = ∅` for `s ∈ Term`. For a coalition, `Moves_C(s) = Π_{a∈C} avail(a, s)`. A joint move is a pair `(m_C, m_C̄)`. For `C = ∅`, `Moves_∅(s)` holds only the empty tuple.

**Step.** `δ(s, m)` is computed in two stages (spec §3.4). First, every chosen action's effects are evaluated on `s`; per variable, a `Set` value is taken if present (two different `Set`s are a `ModelError`), all `Bump`s are summed and added, and the result is clamped. Second, the system updates run in this order: `tick := tick + 1`; delay counters (set to `d` for a delayed action chosen now, decremented each tick, delayed effect applied in the update in which the counter goes from 1 to 0); `last_<a> := chosen action`; latches; fairness counters (section 6). Nature's nondeterminism is its choice of event; given the joint move there is no further choice.

**Consequences used throughout.**
- Every move increments `tick`, and `tick = horizon` is terminal. The state graph is therefore acyclic and every play is finite, of length at most `horizon − tick(s₀)`. "Forever" in this framework means "until a terminal state".
- The explicit graph (spec §5.1) is the part of `S` reachable from `I`. It is closed under successors, so every fixpoint below, restricted to it, equals the global fixpoint on those states.
- Latches and `remember_last` make chosen path facts (the value of `a_known` when control first reached `majority`; the last action) into state facts. This is a product with a small deterministic monitor, and it is why reachability and safety objectives suffice for the endings in DESIGN.md §3.3 without LTL.

### 1.2 Correspondence with the DSL

| DSL construct (spec §3) | Formal object |
|---|---|
| `m.var(name, levels, init)` | `v ∈ Var`, `D(v)`, `I_v` |
| `init=None` | `I_v = D(v)`: one initial state per value; hidden objectives and parameters are swept this way |
| `m.counter`, `m.flag` | `v ∈ Var` with an integer or boolean domain |
| `monotone=True` | a static and run-time check on `δ`; no semantic content |
| `m.actor(name, observes=…)`, `hidden_from` | `a ∈ Agt`, `Obs(a)` |
| `m.nature()`, `N.event` | `N ∈ Agt`, `Act_N` |
| `action(guard, effect)` | `α ∈ Act_a`, clause 1 of `avail`, the effect part of `δ` |
| `delay=d` | built-in `pending_<a>_<α>`, clause 2 of `avail`, delayed effect in `δ` |
| `remember_last=True` | built-in `last_<a>` |
| `m.latch(name, of, when)` | latch variable with `unset` prepended to the levels of `of` |
| `m.fairness(...)` | built-in `fair_<f>`, clause 3 of `avail` |
| `m.profile(...)`, selected at explore time | clause 4 of `avail` |
| `m.invariant(name, e)` | the set `[[e]]`, used as `φ` |
| `m.ending(name, e)` | the set `[[e]]`, part of `Term`; endings are mutually exclusive on reachable states |
| `horizon` | `[[tick = horizon]] ⊆ Term`; reported as `HORIZON` when no ending holds |

---

## 2. Strategies

A **history strategy** for `C` maps each finite history `s₀ s₁ … s_i` with `s_i ∉ Term` to some `m_C ∈ Moves_C(s_i)`. A **memoryless strategy** depends on `s_i` only: `σ_C : S ∖ Term → Π_{a∈C} Act_a` with `σ_C(s) ∈ Moves_C(s)`. The outcome set `out(s, σ_C)` is the set of maximal plays from `s` in which every step uses `σ_C`'s move for `C` and any move in `Moves_C̄` for the rest. Randomized strategies are not used: for the sure-winning objectives below, a randomized strategy wins only if every deterministic strategy in its support wins, so randomization adds nothing in the qualitative layer.

**Uniformity.** Write `s ~_a s'` when `s` and `s'` agree on `Obs(a)`. A strategy is uniform when every member's component is constant on `~_a` classes. The spec requires the guard of each action of `a` to mention only variables in `Obs(a)` (spec §1, §4 `observation_check`). Three things follow, and one does not.

1. **Uniform availability (holds, with conditions).** If `s ~_a s'`, clause 1 of `avail` gives the same answer in both states. Clauses 2 to 4 also agree when the built-in counters are in `Obs(a)` and the fairness triggers and profile `unless` conditions of `a` mention only `Obs(a)`. The spec's check covers guards only, so the last condition is the modeler's responsibility (the DESIGN.md §6.3 sketch has a fairness trigger for `H` on `a_control`, which `H` does not observe).
2. **Information as explicit state (holds).** What an actor has learned is carried by belief variables (`a_known`, `belief[P][Q]`) updated by effects and Nature events, and guards are written on those beliefs. This is the abstraction: the modeler writes the knowledge dynamics instead of deriving them from observation histories.
3. **Negative results transfer (holds).** Uniform strategies are a subset of all strategies, so "no strategy of `C` exists" (section 3) remains true under any information assumption.
4. **Positive results are perfect-information results (the loss).** The fixpoints in section 3 choose a move per state. Nothing forces that choice to be constant on observation classes. Example: `x ∈ {0, 1}` with `init=None`, hidden from actor `a`; `a` picks `left` or `right`; the target is reached iff `left` is picked when `x = 0` and `right` when `x = 1`. The attractor for `{a}` contains both initial states; no uniform strategy wins from both. So "`C` can force `T`" or "`s` is in `C`'s kernel" is an upper bound on `C`'s ability whenever a member of `C` lacks observations. DESIGN.md §4.2 states this correctly ("this keeps the engine in perfect-information ATL").

**What the full problem would cost.** ATL under imperfect information with perfect recall is undecidable in general (Dima and Tiplea 2011); the difficulty comes from coalitions of two or more agents with different information. With memoryless (imperfect-recall) uniform strategies the problem is decidable (Schobbens 2004): a uniform strategy assigns one move per observation class, and these can be guessed and checked, which is the SAT encoding planned for phase 6.

**A cheap sufficient check.** If the strategy returned by `attractor` or `safe` is constant on each `~_a` class among the winning states it is used in, extend it to the other states of each class by the same value. The result is a uniform memoryless strategy that wins from the same states, so the positive result also holds under imperfect information. Failure of the check proves nothing, since another winning strategy may be uniform. The check is not in the spec.

**Testing consequence.** The brute-force cross-check (spec §5.3, §11) must enumerate memoryless state-based strategies to agree exactly with the fixpoints. An enumeration of observation-based uniform strategies gives a subset of the winning states, equal only when the coalition's members observe every variable that matters.

**Subjective reading.** Kernel membership is a statement about one state. For a coalition unsure of a hidden variable, the claim worth reporting is that every state of the observation class is in the kernel (necessary for a uniform win), together with the sufficient check above.

---

## 3. Logic

### 3.1 The fragment

Plays are maximal: they end in a terminal state. For a play `ρ = s₀ s₁ … s_n`: `ρ ⊨ ◇T` iff some `s_i ∈ T`; `ρ ⊨ □φ` iff every `s_i ∈ φ`. Then `s ⊨ ⟨⟨C⟩⟩ψ` iff some history strategy `σ_C` has `ρ ⊨ ψ` for every `ρ ∈ out(s, σ_C)`.

| Formula | Reading | Engine |
|---|---|---|
| `⟨⟨C⟩⟩◇T` | `C` can force a visit to `T` | `attractor(g, C, T)` |
| `⟨⟨C⟩⟩□φ` | `C` can keep `φ` until a terminal state | `safe(g, C, φ)` |
| `⟨⟨C⟩⟩◇^{≤k}T`, `⟨⟨C⟩⟩□^{≤k}φ` | the same within `k` ticks | `rank ≤ k`; BMC depth `k` |
| `EF T` | some play reaches `T` | `attractor(g, Agt, T)` |
| `⟨⟨∅⟩⟩◇T`, `⟨⟨∅⟩⟩□φ` | `AF T`, `AG φ` | `C = ∅` |

No nesting of strategic operators is used in phase 0; the analysis layer composes results set-wise (section 4).

### 3.2 Controllable predecessor and fixpoints

For `X ⊆ S`, the controllable predecessor (spec §1) is defined on non-terminal states only:

```
CPre_C(X) = { s ∉ Term | ∃ m_C ∈ Moves_C(s) . ∀ m_C̄ ∈ Moves_C̄(s) . δ(s, (m_C, m_C̄)) ∈ X }
```

```
Attr_C(T) = μX . T ∪ CPre_C(X)                 (reachability)
Safe_C(φ) = νX . φ ∩ (Term ∪ CPre_C(X))        (safety)
```

**Terminal states.** A terminal state has no moves, so it is never in `CPre_C`. It is in `Attr_C(T)` iff it is in `T`, and in `Safe_C(φ)` iff it satisfies `φ` (spec §1). The `Term ∪` term makes the second rule explicit; the spec's shorthand `νX. φ ∩ CPre_C(X)` must be read with it, or no terminal state would ever be safe. One consequence: an ending state that satisfies `φ` counts as "kept". Endings should be written so that this is intended.

**Stages and rank.** `X₀ = T`, `X_{i+1} = T ∪ CPre_C(X_i)`. The rank of `s` is the least `i` with `s ∈ X_i`, the forced distance in ticks (spec §5.3). The stages give the bounded operator: `s ⊨ ⟨⟨C⟩⟩◇^{≤k}T` iff `rank(s) ≤ k`. Since the graph is acyclic, both fixpoints are reached within `horizon + 1` stages and each operator has a unique fixpoint; the μ/ν distinction matters again only if the tick is abstracted away (section 6.3).

**Equivalence with a turn-based game.** Under the ∃∀ quantifier order, `C` commits to `m_C` and the rest answers knowing it. `⟨⟨C⟩⟩` in the concurrent game is therefore winning in the turn-based game where `C` moves first at every step. All turn-based results apply to that game. The rest-moves-first game is a different game, and the gap between the two is the contested region (3.5).

### 3.3 Theorem 1: memoryless strategies suffice

For every `s`: `s ⊨ ⟨⟨C⟩⟩◇T` iff `s ∈ Attr_C(T)`, and `s ⊨ ⟨⟨C⟩⟩□φ` iff `s ∈ Safe_C(φ)`. In both cases a memoryless strategy wins from every winning state. (Alur, Henzinger and Kupferman 2002 give the fixpoint characterization of ATL model checking over concurrent game structures; the statement here is its specialization to this semantics.)

*Sketch (if).* Reachability: for `s` of rank `r > 0`, let `σ(s)` be a C-move witnessing `s ∈ CPre_C(X_{r−1})` (the `strategy[s]` of spec §5.3). Every completion leads to a state of rank `< r`. Ranks strictly decrease along any play consistent with `σ`, so `T` is reached within `rank(s)` steps; rank-0 states are in `T`. Safety: for non-terminal `s ∈ K = Safe_C(φ)`, `s ∈ CPre_C(K)`, so pick `σ(s)` with every completion in `K`. Every play consistent with `σ` stays in `K ⊆ φ` until it ends. *(Only if)* is Theorem 2.

### 3.4 Theorem 2: soundness

If `s ∉ Attr_C(T)`, then for every history strategy `σ_C` of `C`, memoryful included, some play in `out(s, σ_C)` never visits `T`. Likewise for `Safe_C(φ)` and `□φ`. Hence: if the engine reports that `C` has no strategy, none exists in the model, under perfect information and therefore under any weaker information.

*Sketch.* Let `W = Attr_C(T)`; it satisfies `W = T ∪ CPre_C(W)`. Take `s ∉ W` and any `σ_C`. Then `s ∉ T`, and either `s` is terminal (the play ends outside `T`) or `s ∉ CPre_C(W)`: for the move `m_C` that `σ_C` picks on the current history, some completion `m_C̄` leads outside `W`. Choose it and repeat. The play is consistent with `σ_C` and never enters `W ⊇ T`. Note that the completion depends on `m_C`; this is a play in the outcome set, not a strategy of the rest. For safety, the complement `S ∖ Safe_C(φ)` is the least fixpoint of `Y ↦ ¬φ ∪ {s ∉ Term | ∀ m_C ∃ m_C̄ . δ(s, m) ∈ Y}`; following the rank of that fixpoint downward from `s` produces a play consistent with `σ_C` that reaches `¬φ`.

The guarantee is relative to `G`: if the transition relation is wrong, so is the answer (section 9).

### 3.5 Theorem 3: non-determinacy and the contested region

Concurrent games are not determined. Matching pennies: actors `P` and `Q` (declared with `idle=False`) each pick `h` or `t`; Nature has only `none`; the next state is terminal, in `T` iff the picks agree.

| | `Q: h` | `Q: t` |
|---|---|---|
| `P: h` | `T` | not `T` |
| `P: t` | not `T` | `T` |

`⟨⟨P⟩⟩◇T` fails (each `P` move has a refuting `Q` move) and `⟨⟨Q⟩⟩□¬T` fails (each `Q` move has a refuting `P` move). So the two questions are asked separately (spec §5.3):

| `kind` | `forced` | `blocked` |
|---|---|---|
| `reach` (target `T`) | `Attr_C(T)` | `Safe_C̄(¬T)` |
| `keep` (invariant `φ`) | `Safe_C(φ)` | `Attr_C̄(¬φ)` |

`contested = S ∖ (forced ∪ blocked)`.

**Disjointness.** `forced ∩ blocked = ∅`. *Sketch:* the winning strategies of `C` and of `C̄` act on disjoint actors and combine into one joint move per state; the resulting play would both visit `T` and avoid it.

**Reading.** In the turn-based terms of 3.2, `forced` means `C` wins while committing first, `blocked` means the rest wins while committing first, and `contested` means whoever commits first loses. In a contested state the outcome depends on the simultaneous choice, which in reality turns on information, timing and belief that the qualitative model leaves open. Probabilistic values for such states exist (de Alfaro, Henzinger and Kupferman 2007) but belong to the quantitative layer.

**Nature's side.** Nature is in `C̄` unless named in `C`, so it plays against `C` in `forced` and with the rest in `blocked`. An outcome decided by Nature alone is therefore `blocked`, not `contested`. To separate "blocked by the other actors" from "blocked by chance", also compute the query for `C ∪ {N}`.

### 3.6 Theorem 4: complexity

Let `M = Σ_s |Moves(s)|`, the size of the move relation. `attractor` and `safe` run in time and space `O(|S| + M)`.

*Sketch (attractor, spec §5.3).* For every state `s` and C-move `m_C`, a counter holds the number of completions whose successor is not yet winning. For every state `t`, a predecessor list holds the `(s, m_C)` pairs with a completion into `t`. When `t` joins, each pair in its list is decremented once per such completion; a pair reaching zero adds `s`. Each joint move is touched once. If the worklist is FIFO, a state's join time equals its rank, because states leave the queue in non-decreasing rank and a pair hits zero only after its slowest completion. *Safety* is the dual: a C-move at `s` dies when any completion leaves the candidate set, a counter per state holds the number of live C-moves, and `s` leaves when it hits zero; again linear.

The number of joint moves per state is `Π_a |avail(a, s)|`, so `M` grows exponentially in the number of actors; this, not the fixpoint, bounds the explicit engine. Pivotal analysis (4.5) multiplies the cost by the number of coalitions examined, at most `2^|Agt|`.

---

## 4. Derived objects

### 4.1 Viability kernels

`K_C(φ) = Safe_C(φ)` (spec §7 `viability`). It is unilateral when `C` is one actor and joint when `C` has several. Kernels are monotone in the coalition: `C ⊆ C'` implies `K_C(φ) ⊆ K_{C'}(φ)`, because a C-move can be extended by any moves of `C' ∖ C`. The joint-only region `K_{A,B}(φ) ∖ (K_A(φ) ∪ K_B(φ))` holds the states where the balance can be kept only if both choose to keep it (coldwar_testbed.md C2).

Because plays end at the horizon, `K_C(φ)` means "can keep `φ` until a terminal state". States near the horizon are in the kernel more easily. Comparisons of kernel membership across ticks should keep the remaining horizon in view.

### 4.2 Point of no return and the silent phase

For a trace `ρ = s₀ … s_n` and a kernel `K = K_C(φ)`, three indices are defined (each is `None` if the condition never occurs):

| Index | Definition | Meaning |
|---|---|---|
| `t_K` | first `i` with `s_i ∉ K` | point of no return: `C` alone can no longer guarantee `φ` (spec §7 `point_of_no_return`) |
| `t_L` | first `i` with `s_i ∈ Attr_C̄(¬φ)` | loss is certain: the rest can force `¬φ` |
| `t_φ` | first `i` with `s_i ∉ φ` | the invariant visibly fails |

`t_K ≤ t_L ≤ t_φ`, because `Attr_C̄(¬φ)` is disjoint from `K` (Theorem 3) and contains `¬φ` at rank 0. The **silent phase** is `[t_K, t_φ)`: nothing visible has happened but the outcome is no longer in `C`'s hands. It splits into a contested part `[t_K, t_L)` and a lost part `[t_L, t_φ)`. A trace can re-enter `K` after `t_K` if the rest happens to cooperate; that is what a near miss looks like (C3).

### 4.3 Forced distance

For an adversary `A ⊆ Agt` and a target region `Z`, the forced distance `d_A(s, Z)` is the rank of `s` in `Attr_A(Z)`, or `None`. Spec §7 `distance` is `d_A(s, S ∖ K)`.

**Lemma 5.** If `A ∩ C = ∅` and `s ∈ K_C(φ)`, then `d_A(s, S ∖ K_C(φ)) = None`.
*Sketch:* `Attr_A ⊆ Attr_C̄` by monotonicity, `K` is its own safety kernel, and `Attr_C̄(S ∖ K)` is disjoint from `Safe_C(K) = K` by Theorem 3.

So distance from inside a unilateral kernel against the rest is never finite. The informative uses are:
1. **Joint kernel against a member.** `d_{B∪{N}}(s, S ∖ K_{A,B}(φ))`: how fast `B` alone can break a balance that needs both.
2. **Outside the kernel.** `d_C̄(s, ¬φ)`: the longest the rest needs to force a visible failure. This bounds the lost part of the silent phase.
3. **Margin for error** (not in the spec). The shortest path, under `EF`, from `s` to `S ∖ K`: how many steps of `C` playing off its kernel strategy it takes to lose the guarantee.

DESIGN.md Q6 ("min adversarial steps from s₀ to S∖V") and C8 ("the distance to the boundary increases") need one of these named before phase 3.

### 4.4 Plain reachability

`EF T = Attr_Agt(T)`. It holds iff some joint choice of every actor and of Nature leads to `T`. Adding actions only adds plays (Lemma 6 below), and a model with loose guards reaches nearly every ending. A reachable/unreachable bit carries no measure of how much has to go right. The headline outputs are therefore:
- the **minimum relaxation size** `ρ(E)` and the **minimal relaxation sets** for each ending (section 5), a graded measure of how much of the stated world must fail for `E`;
- **kernel membership** and **forced distance** (4.1 to 4.3), which carry a ∃∀ quantifier instead of ∃∃;
- **pivotal coalitions** (4.5), which attach a result to the actors who decide it.

### 4.5 Pivotal coalitions

Fix a universe `U` of candidate members (the declared actors, plus `N` when `include_nature=True`) and an initial set `I₀` (by default all of `I`). For an ending `E`:

```
F(E) = { C ⊆ U | I₀ ⊆ Attr_C([[E]]) }       (forcing family)
B(E) = { C ⊆ U | I₀ ⊆ Safe_C(¬[[E]]) }      (blocking family)
```

Both families are upward closed in the subset lattice, by the monotonicity of `CPre_C` in `C`. Each is described by its antichain of minimal elements, the pivotal coalitions (spec §7 `pivotal`). If `C ∈ F(E)` and `I₀ ≠ ∅`, then `Agt ∖ C` cannot block `E` from `I₀` (Theorem 3). Coalitions are enumerated by increasing size and supersets of found minimal elements are skipped. "From every initial state" quantifies over the swept hidden values as well. When `init=None` sweeps a hypothesis such as `a_objective`, pivotal coalitions are usually more informative per hypothesis, with `I₀` restricted to one value.

---

## 5. Assumption mining

### 5.1 Assumptions and relaxations

The **assumption set** `𝒜` of a model has one element per action guard that is not the constant `TRUE`, one per fairness constraint, one per profile, and one per named initial-state restriction declared with `assume` (spec §3.1). A **relaxation** `R ⊆ 𝒜` produces the model `G[R]`: every guard in `R` is replaced by `TRUE`; every fairness constraint in `R` is removed, together with its counter and its restriction on `avail`; every profile in `R` is not applied; every `assume` in `R` no longer filters the initial states. Relaxation is loosening only. No guard is tightened, no action is removed, and no delay or effect changes. The registered claims that speak of "assumptions" such as an embargo maintained or an actor's aims (T7, C9) are expressed through profiles and `assume` restrictions, so they fall inside `𝒜`.

**Lemma 6 (monotonicity).** If `R ⊆ R'`, every play of `G[R]`, with removed fairness counters projected out, is a play of `G[R']`. Hence `EF T` in `G[R]` implies `EF T` in `G[R']`.
*Sketch:* `avail` only grows, the initial set only grows, and `δ` on a given joint move does not depend on guards; fairness counters influence nothing but `avail`. A relaxed model can still fail to compile or explore (conflicting `Set`s or non-exclusive endings on newly reachable states). Such a relaxation is reported as ill-formed, not as a result.

For forcing objectives monotonicity is partial. Relaxing an assumption owned by a member of `C` can only help `C`. Relaxing one owned by the rest, Nature included, can only help the rest. A minimal relaxation for `⟨⟨C⟩⟩◇E` must therefore be found by search over inclusion, or the search restricted to `C`'s own assumptions. The spec's `relax_explicit` takes an optional coalition for this case and answers it by brute force only; the bounded encoding answers reachability only.

Define `ρ_k(E) = min { |R| : E reachable within k ticks in G[R] }`. A relaxation set is **minimal** if no proper subset works and **minimum** if its size is `ρ_k(E)`. `ρ_k(E)` is non-increasing in `k` and constant once `k` covers the horizon. Every report states the `k` used.

### 5.2 The bounded encoding

`encode(cm, k)` (spec §6; Biere, Cimatti, Clarke and Zhu 1999) introduces integer variables `x_v^t` for `t = 0..k`, a choice variable `c_a^t` per actor and tick, and one Boolean `assume_i` per `i ∈ 𝒜`.

```
Φ_k =  Dom(x^0..x^k) ∧ Init(x^0)
     ∧ ⋀_{t<k} [ Term(x^t) → x^{t+1} = x^t ]
     ∧ ⋀_{t<k} [ ¬Term(x^t) → Step(x^t, c^t, x^{t+1}) ∧ Avail(x^t, c^t) ]
Avail ⊇  (c_a^t = α) → (¬assume_α ∨ guard_α(x^t))                for each guarded α
         (fair_f^t = within_f) → (¬assume_f ∨ c_a^t ∈ responses_f)   for each f
         delay and profile clauses, unconditional
Reach_k(E) = ⋁_{t≤k} E(x^t)
```

**Lemma 7.** `Φ_k ∧ Reach_k(E) ∧ ⋀_{i∉R} assume_i` is satisfiable iff `E` is reachable within `k` ticks in `G[R]`. Setting `assume_i` false permits the guard to fail; it does not require it to.

### 5.3 Cores, MaxSAT and enumeration

- **Blocking sets.** If `E` is unreachable with every assumption asserted, an unsat core `Q ⊆ 𝒜` is a set of assumptions that jointly block `E`. Every working relaxation intersects every core. Minimal relaxation sets are the minimal hitting sets of the minimal unsatisfiable subsets (Reiter 1987; Liffiton and Sakallah 2008). A solver's core need not be minimal; it is reported as a blocking set, not as a minimal one.
- **Minimum relaxation.** Hard constraints `Φ_k ∧ Reach_k(E)`, soft unit clauses `assume_i` of weight 1. The optimum cost is `ρ_k(E)`, and the falsified softs form a minimum set, which is also minimal by inclusion. Z3's `Optimize` solves this (Bjørner, Phan and Fleckenstein 2015).
- **All minimum sets.** After finding `R`, add the clause `⋁_{i∈R} assume_i` and re-solve. Stop when the cost exceeds `ρ_k(E)` or the enumeration limit is hit. Each clause removes `R` and its supersets, so the loop returns every minimum set once.
- **Explicit variant** (spec §7 `relax_explicit`). Enumerate `R` by increasing size up to `max_size`, re-explore `G[R]`, test `EF E`, and skip supersets of sets that worked (Lemma 6). This returns every minimal set up to `max_size`, at a cost of `Σ_{j≤max_size} C(|𝒜|, j)` explorations. On models with at most six guards it must agree with the BMC sizes (spec §6).

**Granularity.** A guard counts as one assumption, however many conjuncts it has. Splitting a guard into named conjuncts changes `ρ`. Guard granularity is a modeling decision, reported with the parameter budget.

### 5.4 Informativeness and the parameter budget

A negative control is a triple `(E_j, op_j, r_j)` with `op_j ∈ {≥, =, ≤}`: ending `E_j` should need a number of relaxations that stands in relation `op_j` to `r_j`. For a list `N` of controls (spec §7):

```
Inf(G, N) = |{ j : ρ(E_j) op_j r_j }| / |N|
```

Checking `ρ(E_j) ≥ r_j` needs a search up to size `r_j − 1` only; `=` and `≤` need the search up to `r_j`. This covers T10's "at most one relaxation of `aims[USSR]`" and C12's "exactly one" and "zero" as well as the "at least three" controls.

The **parameter budget** `β(G)` is the vector of counts returned by `budget()`: variables, levels, actions, guards, speculative actions, fairness constraints, delays, latches. The anti-hindsight rule (ww2_testbed.md §7.4) is that a change raising `β` must not lower `Inf`. Each parameter is a degree of freedom that could fit the known outcome, and `Inf` measures whether the model still rules things out.

---

## 6. Bounded fairness

### 6.1 Encoding

For `fairness(f, actor=a, trigger=θ, within=k, responses=Rsp)`, the counter `fair_f ∈ 0..k` starts at 0 and is updated last in the system update (spec §3.1):

```
fair_f' = min(fair_f + 1, k)   if s' ⊨ θ and a's chosen action ∉ Rsp
fair_f' = 0                    otherwise
```

When `fair_f = k`, `avail(a, ·)` is restricted to the responses whose guards hold. If none is available, the engine raises `ModelError`, so fairness cannot create a deadlock.

### 6.2 Meaning

**Proposition.** On every play, if `θ` holds continuously in `s_j, s_{j+1}, …` and the play lasts long enough, then `a` plays a response at one of the moves made in `s_j, …, s_{j+k}`. When the move entering `s_j` was not a response (the usual case, since it caused `θ`), the bound tightens to `s_j, …, s_{j+k−1}`: a response within `k` ticks.

Two properties follow from the reset to 0:
- It is **bounded weak fairness**: continuous triggering is served within `k`. A trigger that lapses for one state restarts the clock, and an intermittent trigger can be ignored indefinitely. DESIGN.md §2.5 phrases response fairness as "holds infinitely often", which is strong fairness. Resetting only on a response would give a bounded strong version.
- It is part of the **arena**, not of the objective. It restricts `a`'s moves. If `a ∈ C`, `C` cannot rely on `a` being unresponsive; if `a ∉ C`, the adversary cannot be.

### 6.3 Why bounded, and what the unbounded version needs

With the bound compiled into the state, every query stays a reachability or safety game on the product with counters, solved by the linear algorithms of section 3. The state space grows by at most `Π_f (k_f + 1)`. With a finite horizon, an unbounded "eventually" would also be close to vacuous, because a play can end before the response is due.

An unbounded version is needed only if the tick is abstracted away, giving a cyclic graph and the "forever" kernels that DESIGN.md §2.1 mentions. Then fairness becomes part of the objective: `C` must satisfy `□φ ∨ ¬Fair_C̄`, where `Fair_C̄` says the rest's fairness constraints hold on the infinite play. Weak fairness gives Büchi and co-Büchi conditions; strong fairness gives Streett conditions, whose winning strategies need memory in general. Through the turn-based reading of 3.2, these can be solved as turn-based ω-regular games, for example by reduction to parity games solved with Zielonka's recursive algorithm (Zielonka 1998). This is not planned before phase 2.

---

## 7. Multi-resolution time (design hook; not implemented in phase 0)

The Cold War needs annual ticks with crises at daily or weekly resolution (coldwar_testbed.md §0). PLAN.md step 2.2 schedules the implementation. The definitions here fix what it must satisfy.

**Setting.** A coarse game `G` and, for some coarse states, a fine sub-game `H` with:
- an entry map `ι : S_G → S_H`, so the sub-game's initial state is determined by the coarse state, with fine-only variables at declared initial values;
- an exit map `λ : Term_H → S_G`, so each terminal fine state returns one coarse state, with the coarse tick advanced by a fixed amount;
- an actor map: each fine actor is a coarse actor, and `Obs_H(a)` reveals nothing that `Obs_G(a)` hides.

**Macro-transition.** At a coarse state `s` where the crisis applies, a coarse action `crisis` stands for playing `H` from `ι(s)`. For plain reachability its successor set is `λ(Term_H ∩ Reach_H(ι(s)))`. For a coalition `C`, the lift must preserve the ∃∀ semantics:

```
s ∈ CPre_C^G(X) via crisis   iff   ι(s) ∈ Attr_C^H( λ⁻¹(X) )
```

For safety, the fine invariant `φ_H` (the coarse `φ` read on fine states) must also hold during the crisis: replace `Attr_C^H(λ⁻¹(X))` by the constrained attractor `μY. (λ⁻¹(X) ∩ φ_H) ∪ (φ_H ∩ CPre_C^H(Y))`.

**Soundness condition.** Under these conditions the lifted fixpoints equal the fixpoints of the flattened game, in which the crisis states are inlined. That flattened game is again a finite concurrent game, so Theorems 1 to 4 apply. Flattening is a valid implementation; repeated sub-game solves are the alternative.

**The unsound shortcut.** Replacing the crisis by a single set-valued outcome, resolved by Nature, makes the outcome adversarial to every coalition. Positive forcing results remain true. Theorem 2 fails: `C` might win by playing the crisis well. The contested region then grows artificially.

Ranks in a composed game count coarse ticks; fine steps inside the crisis are reported separately.

---

## 8. Scenario clustering

For a trace `ρ`, the **guard signature** (spec §7 `cluster`) is

```
sig(ρ) = { (a, α) | a chose α at some step of ρ, and guard_α is not the constant TRUE }
```

Traces with equal signatures form a cluster, represented by its shortest trace. A cluster is a narrative: the set of guarded options it relied on.

**Limitations.**
- **Order and timing are ignored.** DESIGN.md §4.5 describes a *sequence* of guard activations; the spec uses a set. Two plots that differ only in order collapse together.
- **Unguarded actions are invisible.** A decisive unguarded `attack` or `idle` leaves no mark, so moving a condition from a guard into an effect changes the clusters.
- **Granularity.** One guard is one element, whatever it tests.
- **Relaxation.** A relaxed guard is `TRUE` and drops out, so signatures from `G[R]` are not comparable with those from `G`.
- **Input.** The partition covers only the traces supplied (witnesses or samples). Enumerating every trace is exponential. A cluster that does not appear is not shown to be impossible.
- **Purpose.** Signatures are descriptive. They do not separate traces that use the same options for different reasons.

---

## 9. What the theory does not claim

- **The transition relation is a hypothesis.** Theorems 1 to 4 are about `G`. Guards, effects, delays, levels and the action sets are modeling claims. Nothing here shows that they describe the world.
- **Soundness is relative to the model.** "No strategy exists" means none exists in `G`. An action missing from the model is a path missing from every result.
- **Positive results for imperfectly informed coalitions are upper bounds** (section 2), unless the uniformity check passes.
- **Discretization hides thresholds.** A result that flips when a variable's levels are refined was caused by the level boundary. Refinement stability (T13, C13) is evidence; it is not a theorem.
- **Horizon effects.** Kernels and distances are defined over finite plays, and their values near the horizon reflect the horizon.
- **No probabilities.** `contested` means neither side can force the result. It does not mean even odds.
- **Bounded mining is bounded.** `ρ_k(E)` concerns traces of length `k`. A longer horizon can only lower it.

---

## 10. References

- Alur, R., Henzinger, T. A., Kupferman, O. Alternating-time temporal logic. *Journal of the ACM* 49(5):672-713, 2002.
- Aubin, J.-P. *Viability Theory*. Birkhäuser, Boston, 1991.
- Biere, A., Cimatti, A., Clarke, E., Zhu, Y. Symbolic model checking without BDDs. *TACAS 1999*, LNCS 1579, Springer, 1999.
- Bjørner, N., Phan, A.-D., Fleckenstein, L. νZ: an optimizing SMT solver. *TACAS 2015*, LNCS 9035, Springer, 2015.
- Chen, T., Forejt, V., Kwiatkowska, M., Parker, D., Simaitis, A. Automatic verification of competitive stochastic systems. *Formal Methods in System Design* 43(1):61-92, 2013.
- Clarke, E., Grumberg, O., Jha, S., Lu, Y., Veith, H. Counterexample-guided abstraction refinement. *CAV 2000*, LNCS 1855, Springer, 2000.
- de Alfaro, L., Henzinger, T. A., Kupferman, O. Concurrent reachability games. *Theoretical Computer Science* 386(3):188-217, 2007.
- de Moura, L., Bjørner, N. Z3: an efficient SMT solver. *TACAS 2008*, LNCS 4963, Springer, 2008.
- Dima, C., Tiplea, F. L. Model-checking ATL under imperfect information and perfect recall semantics is undecidable. arXiv:1102.4225, 2011.
- Grädel, E., Thomas, W., Wilke, T. (eds.). *Automata, Logics, and Infinite Games*. LNCS 2500, Springer, 2002.
- Liffiton, M. H., Sakallah, K. A. Algorithms for computing minimal unsatisfiable subsets of constraints. *Journal of Automated Reasoning* 40(1):1-33, 2008.
- Reiter, R. A theory of diagnosis from first principles. *Artificial Intelligence* 32(1):57-95, 1987.
- Schobbens, P.-Y. Alternating-time logic with imperfect recall. *Electronic Notes in Theoretical Computer Science* 85(2), 2004.
- Zielonka, W. Infinite games on finitely coloured graphs with applications to automata on infinite trees. *Theoretical Computer Science* 200(1-2):135-183, 1998.

CEGAR (Clarke et al. 2000) is the intended route if abstraction refinement is needed for larger models (DESIGN.md §1.2). Grädel, Thomas and Wilke is the standard reference for attractors and turn-based ω-regular games. Aubin is the source of the viability-kernel concept; the discrete version used here is the safety fixpoint.
