"""Write a finding report from its data: ``reports/templates/finding_report.html`` filled with
one JSON object (the owner's template of 2026-11-25, mainly for findings that did not hold).

    PYTHONPATH=. python scripts/finding_report.py data.json reports/finding_4_D5.html
    PYTHONPATH=. python scripts/finding_report.py --specimen reports/templates/specimen.html

The page only draws; every number and sentence comes from the data. Its five sections and the
data each needs:

``finding``  id, version, claim, kind, status, date, commit, title, summary.
``claim``    registered_text (verbatim), registered_on, prediction, found, plain; ``question``
             (alliance, condition, condition_plain, start, reading); ``by_goal`` rows of
             goal, predicted, found, and an optional verdict ("held", "did not hold", "not
             predicted") where the two texts cannot be compared word for word.
``cosmos``   note; quarters (label per quarter from the start); nodes, each ``[parent, quarter,
             status, label]`` with the start state first (parent -1) and every other node after
             its parent. Status is one of ``start``, ``inside`` (inside the guarantee zone of
             the question), ``outside``, ``no_return`` (the first state outside the zone on its
             path: the glossary's point of no return) and ``exit`` (the condition is broken).
``paths``    the first ten sampled shortest paths to a point of no return: n, quarters,
             no_return_quarter, mover, move, preventing, leads_to, nodes (indices into the
             cosmos), steps (quarter, moves of who/action/speculative, no_return); and
             ``paths_note`` saying how they were found and sampled.
``readings`` for the first three paths: path, title, text (the path told as events in the
             world), basis (quarter, action, source, speculative), so that every sentence can
             be traced to a step and its source.
``other``    lists of sentences: decides, preventing, distance, robustness, srt, sources,
             method, limits; and evidence (label, href).

Rules for whoever fills it. Statuses come from a computed guarantee zone, never from a guess.
A path is an illustration of what is possible; the finding is the zone reading (CLAUDE.md).
When the start state is already outside the zone there is no later point of no return: say
so in ``cosmos.note`` and ``paths_note``, mark the start's successors as they are, and list
the shortest paths to the breaking of the condition instead. A section that could not be
computed is left out and the page says so. Names are the glossary's.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "reports" / "templates" / "finding_report.html"
STATUSES = {"start", "inside", "outside", "no_return", "exit"}
REQUIRED = {
    "finding": ("id", "version", "claim", "kind", "status", "date", "title", "summary"),
    "claim": ("registered_text", "registered_on", "prediction", "found", "plain", "question"),
}


def check(data: dict) -> None:
    """Raise ``ValueError`` on data the page cannot draw or that breaks a rule above."""
    for part, keys in REQUIRED.items():
        missing = [k for k in keys if k not in data.get(part, {})]
        if missing:
            raise ValueError(f"{part}: missing {', '.join(missing)}")
    nodes = data.get("cosmos", {}).get("nodes", [])
    for i, node in enumerate(nodes):
        parent, quarter, status = node[0], node[1], node[2]
        if status not in STATUSES:
            raise ValueError(f"cosmos node {i}: unknown status {status!r}")
        if (i == 0) != (parent == -1) or parent >= i:
            raise ValueError(f"cosmos node {i}: the start is first and a parent comes before")
        if i and quarter != nodes[parent][1] + 1:
            raise ValueError(f"cosmos node {i}: not one quarter after its parent")
    for p in data.get("paths", []):
        if any(not 0 <= n < len(nodes) for n in p.get("nodes", [])):
            raise ValueError(f"path {p.get('n')}: a node outside the cosmos")
    if len(data.get("readings", [])) > 3:
        raise ValueError("readings: the first three paths only")


def render(data: dict, out: Path) -> Path:
    check(data)
    text = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    out.write_text(TEMPLATE.read_text(encoding="utf-8").replace("/*DATA*/", text), encoding="utf-8")
    return out


def specimen() -> dict:
    """Made-up data that fills every section, to check the layout. Not a result."""
    rng = random.Random(7)
    quarters = [f"{2026 + (3 + t) // 4} Q{(3 + t) % 4 + 1}" for t in range(9)]
    nodes: list[list] = [[-1, 0, "start", ""]]
    frontier, paths = [0], []
    for t in range(1, 9):
        nxt = []
        for parent in frontier:
            status = nodes[parent][2]
            for _ in range(rng.choice((1, 2, 2, 3)) if len(frontier) < 90 else 1):
                if status in ("outside", "no_return"):
                    new = "exit" if rng.random() < 0.15 else "outside"
                elif status == "exit":
                    continue
                else:
                    new = "no_return" if t >= 3 and rng.random() < 0.08 else "inside"
                nodes.append([parent, t, new, ""])
                nxt.append(len(nodes) - 1)
        frontier = nxt
    for i, node in enumerate(nodes):
        if node[2] == "no_return" and len(paths) < 10:
            chain = [i]
            while nodes[chain[-1]][0] >= 0:
                chain.append(nodes[chain[-1]][0])
            chain.reverse()
            steps = [
                {
                    "quarter": quarters[nodes[n][1] - 1],
                    "no_return": n == i,
                    "moves": [
                        {"who": "Governments", "action": "wait", "speculative": False},
                        {"who": "Frontier AI companies", "action": "deploy AI agents"}
                        | {"speculative": n == i},
                    ],
                }
                for n in chain[1:]
            ]
            paths.append(
                {
                    "n": len(paths) + 1,
                    "quarters": len(chain) - 1,
                    "no_return_quarter": quarters[node[1] - 1],
                    "mover": "Frontier AI companies",
                    "move": "deploy AI agents",
                    "preventing": "Governments: fund oversight",
                    "leads_to": "silent takeover",
                    "nodes": chain,
                    "steps": steps,
                }
            )
    lorem = "Specimen sentence standing in for a real one."
    return {
        "specimen": True,
        "finding": {
            "id": 0,
            "version": "v0.1",
            "claim": "D0",
            "kind": "guarantee-zone reading",
            "status": "did not hold",
            "date": "2026-11-25",
            "commit": "0000000",
            "title": "Specimen: the headline says what was found, in one sentence",
            "summary": lorem
            + " Two or three sentences: the prediction, the reading, why it matters.",
        },
        "claim": {
            "registered_text": "The registered claim, word for word.",
            "registered_on": "15 November 2026",
            "prediction": "S0 is inside the zone.",
            "found": "S0 is outside the zone under all four AI goals.",
            "plain": lorem,
            "question": {
                "alliance": "Governments alone",
                "condition": "⟨⟨H⟩⟩□balance_control",
                "condition_plain": "keep control",
                "start": "S0 (reading of 9 November 2026)",
                "reading": "inside or outside the guarantee zone, per AI goal",
            },
            "by_goal": [
                {"goal": g, "predicted": "inside", "found": f}
                for g, f in (("Aligned", "inside"), ("Self-preserving", "outside"))
            ],
        },
        "cosmos": {"note": lorem, "quarters": quarters, "nodes": nodes},
        "paths_note": lorem,
        "paths": paths,
        "readings": [
            {
                "path": n,
                "title": "a short name for the story",
                "text": lorem + " " + lorem,
                "basis": [
                    {"quarter": "2027 Q3", "action": "Deploy AI agents", "source": "source text"}
                    | {"speculative": n == 2}
                ],
            }
            for n in (1, 2, 3)
        ],
        "other": {
            k: [lorem]
            for k in "decides preventing distance robustness srt sources method limits".split()
        }
        | {"evidence": [{"label": "The report this finding comes from", "href": "#"}]},
    }


def main() -> None:
    if sys.argv[1] == "--specimen":
        print(render(specimen(), Path(sys.argv[2])))
    else:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        print(render(data, Path(sys.argv[2])))


if __name__ == "__main__":
    main()
