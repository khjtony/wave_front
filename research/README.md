# research/

The console's own data (`python -m console.server`). Everything else the console shows is read from the models, tests, reports and logs.

- `states/s0.json`: the reference start state S0, frozen on the reading of 9 November 2026.
- `states/srt.json`: the real-time state Srt and the dated history of its changes.
- `findings.json`: the registry of findings. Each is a guarantee-zone reading, a no-return analysis or an assumption set, with its claim and report; never a bare reachability result.
- `requests.json`: the owner's pending runs and explore requests, added from the console.
- `news.json`: the inbox of news, blogs and articles that bear on Srt.
- `explorations.jsonl`: the log of searches run from the Explore page (possibilities, not findings).
