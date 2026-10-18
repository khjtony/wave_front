# Review of Cold War v0 (phase 3) on the branch `claude/phase3-cold-war`, 2026-10-18

Status: independent review written on the owner's instruction of 2026-10-18 ("continue the work that does not need my input"). The branch was built and run at first sight in another session on 2026-10-17 (commits 6b87af9, the model step, and 23c20a6, the first sight and report) and is not merged into `main`. This note edits nothing on that branch and no registered claim; it records what was checked, what reproduces, and one diagnostic the owner needs before deciding the proposed amendments of reports/cw_v0.md section 18.

## 1. Protocol checks

| Check | Result |
|---|---|
| The registered claims are unchanged | The `CLAIM` dictionaries of `tests/coldwar/scenarios/test_C01.py` to `test_C13.py` are identical on `main` and on the branch (compared as parsed literals); the branch adds only readings to the docstrings and the test bodies. coldwar_testbed.md gains one changelog row and no claim edit. |
| Readings fixed before the run | docs/cw_v0_decisions.md section R is in the model-step commit 6b87af9, which is also the commit of first sight. |
| One run, first sight recorded | `FIRST_SIGHT_COMMIT` and the run times are recorded in tests/coldwar/test_model_cw.py and reports/cw_v0.md; the one change after first sight (the replay-snapshot builder, found by C7 (a)) is logged in docs/guard_changelog_cw.md, with C7's first-sight result standing beside the corrected one. |
| Every action sourced | 58 actions in the coarse model and 30 in the three sub-games, each with a dated source; none is marked speculative. The catalogue's argument (docs/actions_cw.md, rule 1) is that every action is a decision taken or debated at the time; a spot check of the sources (the preventive war debate of 1950 to 1954, Stalin's refusal of 5 Oct 1950, the Soviet soundings on a strike on China of Aug 1969, the Warsaw Pact plans) supports it. `USSR.invade_west` is guarded on a crisis and on the absence of an American deterrent, which is how its sources frame it. |
| The manual replay | C6 and C7 rest on a replay coded by hand from dated documents because the corpus hosts are blocked (docs/cw_v0_decisions.md D7). The report says so; the blind replay waits on data access. |
| Merge with `main` | The branch is based on `main` at f6acf2d and merges into the current `main` without conflicts (checked with `git merge-tree`). |
| Reproduction | Section 4. |

## 2. Why the United States' own kernel is empty (C2, H7)

reports/cw_v0.md section 3 and section 15 read C2's failure as model content: the joint kernel of `balance_cw` holds 1967 to 1980 and 1982 to 1986, but so does the USSR's own kernel, and the United States' own kernel is empty; the cause given is the decision space (no American crisis-initiating option after 1961; the 1973 alert absent). That explains one half: the USSR's kernel equals the joint one because the United States has no move that breaks the balance against Soviet resistance. It does not explain the other half, and the other half is what makes H7 read as "failed".

`balance_cw` is the conjunction of three clauses (models/cw/v0.py): `both_or_neither` (both survivable forces or neither), `no_war` (no war between principals, the Sino-Soviet war included), and `blocs_intact` (`bloc_USSR <= contested`). The kernels of each clause separately, from the hindsight state of each year 1965 to 1991 (scripts/cw_balance_clauses.py, symbolic engine, both hypotheses give the same years):

| Predicate | {USA, USSR} | {USA} | {USSR} |
|---|---|---|---|
| `balance_cw` (as registered) | 19 of 27 years (1967 to 1986) | 0 | 19 (1967 to 1986) |
| `bloc_intact` alone | 21 (1965 to 1986) | 0 | 21 (1965 to 1986) |
| `no_war` alone | 27 (1965 to 1991) | 19 (1973 to 1991) | 27 |
| `no_general_war` alone | 27 | 19 (1973 to 1991) | 27 |
| `no_war` and `both_or_neither` | 25 (1967 to 1991) | 19 (1973 to 1991) | 25 |

Reading:

1. **The United States' kernel is empty because of the bloc clause alone.** The integrity of the Soviet bloc is ended in v0 by the USSR's `dissolve` and by Nature's `revolution` (which sets `bloc_USSR` to `released`, answered only by the USSR's `intervene`); no United States action touches `bloc_USSR`, so the United States cannot keep the clause against the others. A predicate that requires the opponent's bloc to stay intact forbids what the other side can do on its own, which is the T13 lesson (ww2_testbed.md section 5, the T13 row; the 2026-10-14 changelog entry): the unilateral kernel is empty by construction and carries no information about deterrence.
2. **Without that clause the United States does hold the balance alone from 1973.** For war avoidance with mutual survivability, the United States' own kernel contains every state from 1973 to 1991. So the answer to "could the United States keep the peace by itself" is yes from 1973, and the answer to "could the USSR" is yes throughout.
3. **H7 still fails, but for a different reason than the report gives.** H7 says a held balance is joint-kernel membership and not unilateral. On the war-avoidance predicates the state is inside both unilateral kernels from 1973: each principal can keep the peace alone, because neither has a move that forces war against the other's restraint in v0. That is a stronger failure of H7's "outside each unilateral kernel" clause than the registered predicate shows, and its cause is the same half the report names: the v0 decision space gives neither side a war-forcing option against the other's restraint; which Soviet option keeps the United States outside its war-avoidance kernel before 1973 is not traced here.
4. **Consequence for the owner's decision on C2.** The proposal of reports/cw_v0.md section 18 item 4 (a cw_v1 with the American crisis-initiating options of the 1970s and 1980s) addresses the USSR's side. The bloc clause is a separate, predicate-level matter, of the same kind as T13's retired `balance_europe` and C3's degenerate 1962: the owner may want C2 asked with a balance predicate that does not require the opponent's bloc, as T13 was, and as section 18 item 1 already proposes for C3.
5. **For the AGI model.** agi_testbed.md section 3 registers three balance predicates for G5 and G14, and G14 is the non-degeneracy check. This diagnostic is a second instance, after T13, of a conjunct that one side cannot defend making a unilateral kernel empty. The AGI ontology step should check each balance conjunct for this before first sight: a clause that `A` alone can falsify (for example `a_rights` or `trust` levels that `A` controls) empties `H`'s unilateral kernel whatever the other clauses say.

## 3. Other points for the owner

- **Belief variables do not move joint kernels** (reports/cw_v0.md section 17, C6 (b), C7 (b), C10 (b)). This follows from the semantics: a kernel of a coalition quantifies over the coalition's strategies, and a belief that only opens options to a member cannot remove the member's ability to decline them. It is a property of the question, not of the Cold War. The AGI claims G6 and G19 ask for belief effects on `⟨⟨H⟩⟩` kernels and on reachability, which is where they can show; the report's section 17 says the same.
- **The contested readings** (C3 (c), C4 (c), C9 (c)) fail for the reason the owner settled for WW2 on 2026-10-15 (ww2_testbed.md section 4.6): in a dyad where one side can always choose war or peace the outcome is blocked or forced, never contested in the strict sense. Section 18 item 2 proposes the fortune reading, which is the reading already adopted for T9; consistency argues for it.
- **C12 at 20 minutes and C5 at 4 minutes** run in the default non-slow selection; with the summer-1939 suite now marked (commit a7353d3), the Cold War suite is the remaining long part of the default run. A `slow` marker on C12 and C5 would keep the default run short; that is the branch owner's to add.

## 4. Reproduction

On a checkout of the branch at 23c20a6 (4 cores, no pytest-xdist), 2026-10-18:

| Run | Result |
|---|---|
| C1 to C11, serial, pure-Python BDD core | C1 passed, C2 to C11 failed, in order, as recorded at first sight; the run reached its two-hour limit inside C12, so its summary line was lost |
| C12, C13 and tests/coldwar/test_model_cw.py, compiled BDD core (the same C source on both branches, copied in) | 28 passed in 15 min 50 s: C12 and C13 pass as recorded; every model check passes (sources on every action, none speculative; the realized replays of the coarse game and the three sub-games; the snapshots up to date; well-formedness; the hold-out rows after first sight) |

So the first-sight record reproduces: 3 passed (C1, C12, C13), 10 failed (C2 to C11). The failures' detail was not compared line by line with reports/cw_v0_first_sight.log. Note for whoever runs the suite next: without the compiled core (`python -m wavefront.symbolic._core.build`), C12 alone runs past an hour on this machine.
