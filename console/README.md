# The research console

A local page over this repository: the staged models and their structure, the claims and their results, the runs, the two start states S0 and Srt, the inbox and the glossary.

    console/run.sh            # http://127.0.0.1:8770, this machine only

- **Nothing is copied.** Models are compiled on request, claims are read from the test files, results from `reports/*_parts.jsonl`, readings from `reports/agi_v0_3_kernels.jsonl`, names from `docs/agi_glossary.html`.
- **What it writes:** only `research/requests.json`, `research/news.json` and `research/explorations.jsonl`. Findings and changes to Srt are edited in `research/` and committed like any other change.
- **Explore** steps any version by hand from S0 or Srt and searches it for a shortest path (24 quarters, 4 minutes at most). A path it finds is a possibility, not a finding, and every search is logged.
- **No dependencies** beyond the project's own: the service is Python's standard library, the page is plain HTML and JavaScript without a build step.

## As a service (Docker, reachable over Tailscale)

    cp console/env.example console/.env      # set WF_TAILSCALE_IP (`tailscale ip -4`)
    docker compose -f console/compose.yaml up -d --build

The container mounts the checkout, so it serves the working tree as it is, and restarts with the machine. The port is published on this machine and on its Tailscale address only, not on the local network; there is no password, so every device on the tailnet can read the reports and add requests. After a change to `console/*.py`: `docker compose -f console/compose.yaml restart`.

Without Docker: copy `console/wavefront-console.service` to `~/.config/systemd/user/`, set its `WorkingDirectory` to the checkout that should be served, and run `systemctl --user enable --now wavefront-console`.

Tests: `pytest tests/research_console`.
