# Handoff: continuing this project on a local machine

Status: written 2026-10-24 at `main` 884e17a (PR #4, the Cold War v0, merged). Read this first in a new session; it says where the project stands, how to set up, what the rules are, and what is waiting on whom. Everything it points to is in the repository; nothing depends on the earlier conversation.

## 1. What the project is

A reachability-based simulator of power relationships between strategic actors, built to study the relationship between AGI/superintelligence and humanity. Actors are constraints and available actions; game-based model checking computes kernel membership and the point of no return, minimal assumption sets, and pivotal coalitions. The framework is developed on the Second World War, validated on the Cold War, and only then instantiated for AGI. README.md has the one-paragraph version; docs/DESIGN.md the full design; docs/PHASES.md the seven phases and their gates; docs/PLAN.md the steps inside each phase.

Working pattern so far: the session acts as architect and reviewer, delegates implementation to subagents for large steps, then runs the tests and lint itself, reads the code, commits and pushes. The owner makes the decisions listed in section 5.

## 2. Setting up locally

```
git clone https://github.com/khjtony/wave_front && cd wave_front
python -m venv .venv && . .venv/bin/activate          # Python 3.11 or later (developed on 3.13); without ensurepip: uv venv --python 3.13 .venv
pip install -e '.[dev,bmc,data]'
pip install -e '.[fast]' && python -m wavefront.symbolic._core.build   # the compiled BDD core
pytest -q -m "not slow"                                # the default selection
ruff check . && ruff format --check .
```

- **Build the compiled core.** Without it the symbolic engine runs in pure Python and is about ten times slower; the Cold War claim C12 alone runs past an hour. Both cores give identical results (`tests/symbolic/test_bdd_differential.py`).
- **Test times.** The default selection takes tens of minutes on four cores; the full suite (`pytest -q`) about an hour with three workers (`pip install pytest-xdist`, then `-n 3`). Long tests carry the `slow` marker.
- **The expected failures are registered claims failing as computed, not bugs.** At 884e17a the full suite gives seventeen: K2d, K3, K4g (summer 1939), J3, J4, J6, J7 (July 1914), and C2 to C11 (Cold War). Anything else failing is new.
- **Git-ignored data.** `data/ww2/raw/`, `data/cw/raw/`, `data/cw/corpora/raw/` and `data/ww2/corpora/raw/` are git-ignored. On a fresh clone the WW2 datasets come from `python scripts/fetch_ww2_data.py --mirror --extract both` and the FRUS corpus from `scripts/fetch_corpora.py` (commands in docs/replay_harness.md). The tests do not need them.

## 3. The rules (CLAUDE.md, binding)

- Read docs/framework_spec.md before touching `wavefront/`; it is the contract, and a deviation changes the spec in the same commit.
- Read the testbed's section 7 before touching a domain model. **Tests are registered before guards**; a guard edit after a failing test is logged in that model's guard changelog with sources, followed by a full rerun.
- Every action carries `source=`; an action without a contemporaneous source is `speculative=True`.
- Reports never quote a bare reachability result as a finding; the deliverables are minimal assumption sets, kernel membership and distance, and pivotal coalitions.
- No identifiers of the AI model or session that authored a change in code, docs or commits (attribution trailers excepted).
- `pytest -q`, `ruff check .` and `ruff format --check .` pass before a commit.

The anti-hindsight protocol behind these (claims run once, first sight recorded, hold-outs, amendments only by the owner and logged) is ww2_testbed.md section 7, with the AGI additions in agi_testbed.md section 6.

## 4. Where things stand

| Phase | State | Where |
|---|---|---|
| 0 Framework | passed 2026-10-11 | docs/PHASES.md, docs/validity.md section 8 |
| 1 WW2 v0 | passed 2026-10-12 under the owner's amendments | reports/ww2_v0.md |
| 2 WW2 v1 | **passed 2026-10-28** (owner's decision 7h): replay 95 % after a sample review, 8 of 9 flips | reports/ww2_v1.md, reports/replay_ww2_frus.md, the PHASES.md addendum |
| 2 extras | summer-1939 sub-game (K1 to K6) and July 1914 (J1 to J7) run once; per-actor cadence (framework change 1); compiled BDD core | reports/crisis_1939.md, reports/july1914.md, docs/framework_changes.md, docs/engine_scaling.md |
| 3 Cold War v0 | built and run once 2026-10-17: C1, C12, C13 pass; C2 to C11 fail as read; 0 framework changes; reproduced independently 2026-10-18 | reports/cw_v0.md, docs/review_phase3_2026-10-18.md |
| 4 Audit and freeze | not started; waits on the phase 3 decisions | docs/PHASES.md |
| 5 AGI v0 | claims G1 to G22 registered 2026-10-17 before any guard; no AGI model yet | docs/agi_testbed.md, tests/agi/ |

Notes and side work an incoming session should know:

- **docs/review_2026-10-17.md**: status and roadmap against the goal. Its main points are that the AGI balance must be coexistence rather than control, and that diplomacy, labs, power and plural AIs need claims.
- **docs/review_phase3_2026-10-18.md**: in the Cold War model, the United States' empty unilateral kernel comes from the `blocs_intact` clause alone, a clause only the other side can falsify (the T13 lesson). The diagnostic script is `scripts/cw_balance_clauses.py`.
- **docs/ww2_si_disanalogies.md**: the owner's placeholder on where WW2 and the human–superintelligence relationship differ in kind. Its work starts when phase 2 closes, and any testable claim it yields is registered as G23 onward.
- **docs/agi_government_policy_2025.md**: the Klein–Buchanan interview read against the hypotheses. Its quotations still need checking against the transcript.
- **docs/agi_scene_objectives.md and `models/toy/agi_scene.py`**: a scene toy on AGI objectives (exist, grow, truth, aligned), the AGI's stance, and the continuity guarantee's lag. It is not the AGI model; its prior exposure is disclosed in agi_testbed.md section 9.
- **docs/architecture_diagrams.html**: the architecture and sequence diagrams.

## 5. Waiting on the owner

1. **Close phase 2: the Claude-backend replay.**
   - Run the command block in docs/replay_harness.md, "Running the Claude backend on the real corpus" (pip install `.[extract]`, the key in `ANTHROPIC_API_KEY` in your shell only, fetch and check the FRUS corpus, dry run, a one-quarter pilot, the rest, the measurement).
   - Send back the two metric reports, the proposals directory, the output of `fetch_corpora.py --check frus` and the commit used.
   - This also opens the disanalogies work.
2. **Amendment decisions.** Each is proposed in a report and none is applied.
   - Summer 1939: K2(d), K3, K4(g) (reports/crisis_1939.md section 11).
   - July 1914: J3, J4, J7, and whether a 1914 v1 fixes J6's missing Russian-measures precondition (reports/july1914.md section 12).
   - Cold War: the six proposals of reports/cw_v0.md section 18, plus the C2 predicate point of docs/review_phase3_2026-10-18.md section 2.
3. **Cold War scope calls** (docs/cw_v0_decisions.md section O): the PRC's scope, the hindsight convention for beliefs, and whether the manual replay stands for C6 and C7 until the blind one runs.
4. **Budget.** Whether the cadence change counts against the phase 3 budget of five (0 or 1 of 5 used).
5. **Data.** Section 6.
6. **"Go" for phase 4**, once 2 and 3 are settled.

## 6. Data to download

Save under the paths below and add a `MANIFEST.json` per folder (each file's URL, download date, SHA-256), as `data/ww2/raw/` has. The folders are git-ignored. On a local machine the next session can read them in place; to hand them to a cloud session, commit them with `git add -f` on a branch.

| Data | Needed for | Source | Save under |
|---|---|---|---|
| Steury (ed.), *Intentions and Capabilities: Estimates on Soviet Strategic Forces, 1950–1983* (CIA, 1996) | blind replay for C6 and C7 | https://www.cia.gov/resources/csi/books-monographs/intentions-and-capabilities-estimates-on-soviet-strategic-forces-1950-1983 (or https://purl.fdlp.gov/GPO/LPS61105) | `data/cw/corpora/raw/crest/` |
| NIE 11-8 estimates missing from that volume | same | https://www.cia.gov/readingroom, by estimate number | `data/cw/corpora/raw/crest/` |
| Norris and Kristensen, "Global nuclear weapons inventories, 1945–2010", BAS 66(4) (or the 1945–2013 update) | checking `nuke_USA`, `nuke_USSR` | https://thebulletin.org/2010/07/global-nuclear-weapons-inventories-1945-2010/ | `data/cw/raw/nuclear_inventories/` |
| Maddison Project Database 2023 (`mpd2023_web.xlsx`) | checking `econ_USSR` | https://rug.nl/ggdc/historicaldevelopment/maddison/releases/maddison-project-database-2023 (Dataverse DOI 10.34894/INZBF2) | `data/cw/raw/maddison/` |
| Optional: Polity5, SIPRI military expenditure, ICB v16 | named by the testbed; no claim reads them | https://systemicpeace.org/inscrdata.html ; https://sipri.org/databases/milex ; https://sites.duke.edu/icbdata/data-collections/ | `data/cw/raw/polity/`, `data/cw/raw/sipri/`, `data/cw/raw/icb/` |

Not needed: the Correlates of War data (fetched by `scripts/fetch_ww2_data.py`, already covering the Cold War) and the Cold War FRUS volumes (the pinned GitHub mirror, fetchable by `scripts/fetch_corpora.py`).

A local machine may also reach hosts the cloud environment blocked (cia.gov, correlatesofwar.org, fas.org, thebulletin.org, rug.nl, dataverse.nl). There the session can fetch directly; data/cw/README.md lists which cross-checks to run once the series are present.

## 7. What a session can do without the owner

- Write the CIA-estimate reader (`wavefront/evidence/corpora/`, alongside the FRUS reader, tested on samples) once the PDFs exist, then run the blind Cold War replay.
- Run the cross-checks of data/cw/README.md against the downloaded series, recording each level as verified or not. Check the hindsight snapshots only; changing a level after first sight follows the guard-changelog rule.
- Execute any amendment the owner decides, rerun the affected suites, and update the testbed changelogs, reports and docs/PHASES.md.
- The phase 4 audit (docs/PHASES.md, docs/PLAN.md phase 4) once phase 3 is settled.

## 8. Git conventions

- Commit messages end with the attribution trailers your tool adds; nothing else in a commit names a model or session.
- Merge, never rebase or force-push, on a branch someone else created.
- A branch that went into a merged pull request is restarted from `main` for new work.
- Before any commit, run `pytest -q -m "not slow"` (or the affected suites plus the slow ones they touch), `ruff check .` and `ruff format --check .`.
