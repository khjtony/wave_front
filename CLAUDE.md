# wave_front conventions

- Read `docs/framework_spec.md` before touching `wavefront/`. It is the contract; if the implementation needs to deviate, change the spec in the same commit and say why in the commit message.
- Read `docs/ww2_testbed.md` section 7 and `docs/coldwar_testbed.md` section 7 before touching `models/ww2/` or `models/cw/`. Tests are registered before guards; guard edits after a failing test are logged.
- Every action in a domain model carries `source=`. Actions without a contemporaneous source are `speculative=True`.
- Reports never quote a bare reachability result as a finding. The deliverables are minimal assumption sets, kernel membership and distance, and pivotal coalitions.
- No model identifiers or session links in code or docs.
- `pytest -q`, `ruff check .` and `ruff format --check .` must pass before a commit.
