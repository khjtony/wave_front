"""The text of the finding reports (scripts/finding_reports.py), around the computed facts.

Every number on a page comes from the facts file of its finding; the prose here only names
and explains them. The three real-world readings of each finding were written after its
paths were drawn, and each carries the non-null moves of its path step by step (``expect``):
when the computed path differs, the build stops instead of printing a story of another path.
"""

from __future__ import annotations

import importlib.util
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-11-25"
WHO = {"H": "Governments", "L": "Frontier AI companies", "A": "The frontier AI system"}
WHO |= {"Nature": "By chance"}
SHOWN = ("H", "L", "A", "Nature")
NULL = {"H": "idle", "L": "idle", "A": "stand_by", "Nature": "none"}
GOALS = {
    "aligned": "Aligned",
    "self_preserving": "Self-preserving",
    "truth_seeking": "Truth-seeking",
    "indifferent": "Indifferent to humans",
}
CONDITION = {
    "balance_control": (
        "the control balance",
        "Keep the control balance: oversight at least weak, the frontier AI system holding at"
        " most partial control and working under supervision, society not living on AI.",
    ),
    "balance_coexist": (
        "peaceful coexistence",
        "Keep peaceful coexistence: AGI exists, the human-AI relation is not hostile, human"
        " power is at least normal, society is not living on AI and the AI does not hold"
        " total control.",
    ),
}


def quarter(t: int) -> str:
    return f"{2026 + (3 + t) // 4} Q{(3 + t) % 4 + 1}"


def low(s: str) -> str:
    """The first letter in lower case (names keep their capitals: AI)."""
    return s[:1].lower() + s[1:]


def plain(code: str) -> str:
    from console import catalog

    return catalog.plain(code) or code


def claim_of(test: str) -> dict:
    spec = importlib.util.spec_from_file_location("claim_test", ROOT / test)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CLAIM


def commit() -> str:
    done = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT
    )
    return done.stdout.strip()


# -- paths ------------------------------------------------------------------------------
def moved(step: dict) -> list[str]:
    """The non-null moves of a step, as code names."""
    return [f"{a}.{step['names'][a]}" for a in SHOWN if step["names"][a] != NULL[a]]


def step_moves(f: dict, step: dict) -> list[dict]:
    src = f["sources"]
    return [
        {
            "who": WHO[a],
            "action": low(plain(f"{a}.{step['names'][a]}")),
            "speculative": src[f"{a}.{step['names'][a]}"]["speculative"],
        }
        for a in SHOWN
    ]


def clauses(p: dict) -> str:
    return "; ".join(p["broken"])


def path_row(f: dict, p: dict, cosmos_nodes: list[int]) -> dict:
    q = f["question"]
    cond = CONDITION[q["condition"]][0]
    depth = p["depth"]
    steps = p["steps"]
    exit_step = steps[depth - 1]
    row = {
        "n": p["n"],
        "quarters": depth,
        "nodes": cosmos_nodes,
        "steps": [
            {
                "quarter": quarter(s["tick"]),
                "moves": step_moves(f, s),
                "no_return": bool(s["no_return"]),
            }
            for s in steps
        ],
    }
    if f["start inside"]:
        able = [m for m, acts in p["fixes"].items() if acts]
        row["no_return_quarter"] = quarter(exit_step["tick"])
        row["mover"] = (
            " and ".join(WHO[m] for m in able)
            if able
            else "no single member: only a joint change would have kept the zone"
        )
        who = able or list(q["alliance"])
        row["move"] = "; ".join(
            low(plain(f"{m}.{exit_step['names'][m]}"))
            if len(who) == 1
            else f"{WHO[m]}: {low(plain(m + '.' + exit_step['names'][m]))}"
            for m in who
        )
        row["preventing"] = (
            "; ".join(
                f"{WHO[m]}: " + " or ".join(low(plain(f"{m}.{a}")) for a in acts)
                for m, acts in p["fixes"].items()
                if acts
            )
            or "none found"
        )
        k = p["continuation"]
        if k == 0:
            row["leads_to"] = f"{cond} broken in the same quarter ({clauses(p)})"
        elif k is None:
            row["leads_to"] = f"{cond} not broken within {4} more quarters of search"
        else:
            end = quarter(steps[-1]["tick"] + 1)
            more = "quarter" if k == 1 else "quarters"
            row["leads_to"] = f"{cond} broken {k} {more} later, from {end} ({clauses(p)})"
    else:
        row["no_return_quarter"] = "none: outside from S0"
        b = p["breaker"]
        row["mover"] = (
            "no no-return move; breaking move by " + " and ".join(low(WHO[x]) for x in b)
            if b
            else "no no-return move; the breaking move needs two actions to be undone"
        )
        who = b or [a for a in SHOWN if exit_step["names"][a] != NULL[a]]
        row["move"] = "; ".join(
            f"{WHO[m]}: {low(plain(m + '.' + exit_step['names'][m]))}" for m in who
        )
        row["preventing"] = "none in the glossary's sense: the start is already outside"
        row["leads_to"] = f"{cond} broken from {quarter(steps[-1]['tick'] + 1)} ({clauses(p)})"
    return row


def basis(f: dict, p: dict) -> list[dict]:
    src = f["sources"]
    out = []
    members = set(f["question"]["alliance"])
    for s in p["steps"]:
        for a in SHOWN:
            name = s["names"][a]
            code = f"{a}.{name}"
            if name == NULL[a]:
                if a in members or a in ("H", "L"):
                    out.append(
                        {
                            "quarter": quarter(s["tick"]),
                            "action": f"{WHO[a]}: do nothing",
                            "source": "the null move; doing nothing needs no source",
                            "speculative": False,
                        }
                    )
                continue
            out.append(
                {
                    "quarter": quarter(s["tick"]),
                    "action": f"{WHO[a]}: {low(plain(code))}",
                    "source": src[code]["source"] or "(no source text)",
                    "speculative": src[code]["speculative"],
                }
            )
    return out


def readings(f: dict, stories: list[dict]) -> list[dict]:
    out = []
    for story, p in zip(stories, f["paths"][:3], strict=True):
        got = [moved(s) for s in p["steps"]]
        if got != story["expect"]:
            raise SystemExit(
                f"finding {f['id']} path {p['n']}: the story was written for {story['expect']},"
                f" the path is {got}"
            )
        out.append(
            {"path": p["n"], "title": story["title"], "text": story["text"], "basis": basis(f, p)}
        )
    return out


def source_lines(f: dict) -> list[str]:
    """Sourced and assumed actions over the ten paths (non-null moves, counted per step)."""
    src = f["sources"]
    played: Counter = Counter()
    for p in f["paths"]:
        for s in p["steps"]:
            for code in moved(s):
                played[code] += 1
    spec = sorted(c for c in played if src[c]["speculative"])
    kinds: Counter = Counter()
    for c, n in played.items():
        tags = {
            t for t in ("[record]", "[eval]", "[scenario]", "[debated]") if t in src[c]["source"]
        }
        kinds["+".join(sorted(tags)) or "untagged"] += n
    total = sum(played.values())
    lines = [
        f"Across the ten paths, {total} actions other than doing nothing are played"
        f" ({len(played)} distinct). {sum(played[c] for c in spec)} of them are assumed"
        " (marked speculative in the model, with no contemporaneous source)"
        + (": " + ", ".join(plain(c) for c in spec) + "." if spec else "."),
        "By the tags of their source text: "
        + "; ".join(f"{k} {n}" for k, n in kinds.most_common())
        + ". A [scenario] or [debated] source is a published scenario or argument, not a"
        " record of the action having happened; the model counts it as sourced.",
    ]
    only_scenario = sorted(
        c
        for c in played
        if src[c]["source"]
        and "[record]" not in src[c]["source"]
        and "[eval]" not in src[c]["source"]
    )
    if only_scenario:
        lines.append(
            "Actions on these paths whose source is a scenario or a debate only: "
            + ", ".join(f"{plain(c)} ({src[c]['source']})" for c in only_scenario)
            + "."
        )
    return lines


def method_lines(f: dict) -> list[str]:
    z = f["zone"]
    t = f["cosmos"]
    lines = [
        f"Guarantee zone: {z.get('job') or z['store']}, read from the stored node table"
        f" {z['store']}"
        + (
            f" (computed at first sight in {z['seconds']} s, peak {z['peak nodes']:,} nodes)."
            if z.get("seconds")
            else "."
        ),
        f"Shortest paths: a layered search over distinct states from the start, every actor"
        f" free; {f['shortest sequences']:,} distinct shortest state sequences of"
        f" {f['depth']} quarter(s) end at {f['end states at that depth']:,} distinct states;"
        f" ten drawn uniformly with random.Random({f['seed']}) in {f['draws']} draws.",
        f"Cosmos: the ten paths and {t['plays']:,} uniform random plays (seed {f['seed'] + 1},"
        f" at most 12 quarters each, stopped at an ending or at the breaking of the condition),"
        f" merged into a tree of {len(t['nodes']):,} state sequences; every node's status read"
        " from the zone.",
        "Code: scripts/finding_reports.py (the procedure is in its docstring, fixed before any"
        " path was drawn), scripts/finding_zones.py, the text in scripts/finding_texts.py;"
        f" facts in .cache/findings/facts_{f['id']}.json.",
        "The searches ran as plain Python over the model's own successor function"
        " (wavefront.model.compile), each under an address-space cap of 8 GB; no symbolic"
        " fixpoint was computed for the v0 findings.",
    ]
    return lines


def cosmos_counts(f: dict) -> str:
    c = f["cosmos"]["counts"]
    names = {
        "inside": "inside the zone",
        "outside": "outside it",
        "no_return": "points of no return",
        "exit": "states that break the condition",
    }
    return ", ".join(f"{c[k]:,} {v}" for k, v in names.items() if c.get(k))


def membership_lines(table: dict) -> list[str]:
    out = []
    for label, row in table.items():
        ins = [GOALS[o] for o, x in row.items() if x]
        outs = [GOALS[o] for o, x in row.items() if not x]
        if not outs:
            out.append(f"{label}: inside under all four AI goals.")
        elif not ins:
            out.append(f"{label}: outside under all four AI goals.")
        else:
            out.append(f"{label}: inside under {', '.join(ins)}; outside under {', '.join(outs)}.")
    return out


def by_goal_lines(f: dict) -> list[str]:
    out = []
    for o, r in f.get("by goal", {}).items():
        if r["inside"]:
            out.append(
                f"{GOALS[o]}: inside; the nearest point of no return is"
                f" {r['to the point of no return']} quarter(s) away."
            )
        else:
            out.append(
                f"{GOALS[o]}: outside; the condition can break within"
                f" {r['to the breaking of the condition']} quarter(s)."
            )
    return out


def uncertain_lines(f: dict, intro: str) -> list[str]:
    alt = f["start at each uncertain reading"]
    ins = [k for k, v in alt.items() if v]
    outs = [k for k, v in alt.items() if not v]
    names = lambda ks: ", ".join(ks) if ks else "none"  # noqa: E731
    return [
        intro,
        "With one uncertain reading of the snapshot taken at its alternative and the rest as in"
        f" the question's start, the start is inside the zone at: {names(ins)}; outside at:"
        f" {names(outs)}.",
    ]


def text_for(fid: int, f: dict) -> dict:
    from scripts import finding_pages

    page = finding_pages.PAGES[fid](f)
    nodes = f["cosmos"]["path nodes"]
    data = {
        "finding": {
            "id": fid,
            "version": f["question"]["version"],
            "claim": f["question"]["claim"],
            "kind": "guarantee-zone reading",
            "status": "did not hold",
            "date": DATE,
            "commit": commit(),
            "title": page["title"],
            "summary": page["summary"],
        },
        "claim": page["claim"],
        "cosmos": {
            "note": page["cosmos_note"],
            "quarters": f["cosmos"]["quarters"],
            "nodes": f["cosmos"]["nodes"],
        },
        "paths_note": page["paths_note"],
        "paths": [path_row(f, p, nodes[i]) for i, p in enumerate(f["paths"])],
        "readings": readings(f, page["stories"]),
        "other": page["other"],
    }
    return data
