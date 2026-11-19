# The research console

A local page over this repository: the staged models and their structure, the claims and their results, the runs, the two start states S0 and Srt, the inbox and the glossary.

    console/run.sh            # http://127.0.0.1:8770, this machine only

- **Nothing is copied.** Models are compiled on request, claims are read from the test files, results from `reports/*_parts.jsonl`, readings from `reports/agi_v0_3_kernels.jsonl`, names from `docs/agi_glossary.html`.
- **What it writes:** only `research/requests.json`, `research/news.json` and `research/explorations.jsonl`. Findings and changes to Srt are edited in `research/` and committed like any other change.
- **Explore** steps any version by hand from S0 or Srt and searches it for a shortest path (24 quarters, 4 minutes at most). A path it finds is a possibility, not a finding, and every search is logged.
- **No dependencies** beyond the project's own: the service is Python's standard library, the page is plain HTML and JavaScript without a build step.

To keep it running across restarts, copy `console/wavefront-console.service` to `~/.config/systemd/user/`, set its `WorkingDirectory` to the checkout that should be served, and run `systemctl --user enable --now wavefront-console`.

Tests: `pytest tests/research_console`.
