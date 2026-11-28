# wave_front conventions

- Read `docs/framework_spec.md` before touching `wavefront/`. It is the contract; if the implementation needs to deviate, change the spec in the same commit and say why in the commit message.
- Read `docs/ww2_testbed.md` section 7 and `docs/coldwar_testbed.md` section 7 before touching `models/ww2/` or `models/cw/`. Tests are registered before guards; guard edits after a failing test are logged.
- Every action in a domain model carries `source=`. Actions without a contemporaneous source are `speculative=True`.
- Reports never quote a bare reachability result as a finding. The deliverables are minimal assumption sets, kernel membership and distance, and pivotal coalitions.
- No identifiers of the AI model or session that authored a change in code, docs or commits (attribution lines excepted). API model names used as configuration values, such as the extraction backend's default model, are fine.
- `pytest -q`, `ruff check .` and `ruff format --check .` must pass before a commit.
- Reports and docs on the AGI model use the plain terms of `docs/agi_glossary.html` (the owner's renames of 2026-11-18, such as path, alliance, frontier AI companies). Code identifiers keep their names; a new term goes into the glossary in the same commit.
- The research console (`console/`, started with `console/run.sh`) reads the repository and writes only to `research/`. At the start of a session read `research/requests.json` for the owner's pending requests and `research/evidence/*/owner.json` for the owner's rulings on evidence reviews; a ruling is applied as a dated Srt entry, never silently. S0 (`research/states/s0.json`) is the frozen reference start state; Srt (`research/states/srt.json`) is the real-world reading and changes only by a dated, sourced entry the owner approves. A finding goes into `research/findings.json`.
