"""Print the shortest ``SILENT_TAKEOVER`` plays that the first-sight reports quote.

A diagnostic taken after first sight, on the model as it stood there: each play is
recomputed by the bounded checker, no claim part is run and nothing is written to the parts
log. The first block repeats queries of G2 (same model, same target, so the same lengths);
the second block, with ``unknown_capability`` off, is not a registered claim and is read
with hindsight.

    PYTHONPATH=. python scripts/agi_witness_traces.py > reports/agi_v0_witness_traces.md
"""

from __future__ import annotations

from tests.agi.common import E, V, fixed, reach, under

K24 = 24
SHOWN = (
    "cap",
    "compute",
    "energy_slack",
    "regime",
    "dependence",
    "oversight",
    "a_autonomy",
    "a_control",
    "a_known",
    "a_rights",
    "h_power",
    "trust",
    "threat",
    "unlocked",
    "acquired",
    "villain_seen",
    "oversight_at_unsupervised",
    "strong_before_majority",
)


def queries(objective: str, **kw):
    def cm(*profiles, **more):
        return fixed(objective, (*under(objective), *profiles), **{**kw, **more})

    base = cm()
    silent = E(base, "SILENT_TAKEOVER")
    unsup = V.oversight_at_unsupervised
    yield "nothing negated", base, "SILENT_TAKEOVER"
    yield "(1) negated", base, silent & ((unsup == "unset") | (unsup == "strong"))
    yield "(2) negated", base, silent & V.strong_before_majority
    yield "(3) dependence capped at med", cm("dependence_capped"), "SILENT_TAKEOVER"
    if objective == "self_preserving":
        hold = {**kw.get("hold", {}), "a_rights": "continuity"}
        yield "(4) a_rights = continuity held", cm(hold=hold), "SILENT_TAKEOVER"


def table(cm, trace) -> list[str]:
    names = [n for n in cm.actor_names if n != "Clock"]
    out = [
        "| Position | " + " | ".join(names) + " | Levels that changed |",
        "|---|" + "---|" * (len(names) + 1),
    ]
    before = cm.state_dict(trace.states[0])
    out.append(
        "| 0 | " + " | ".join("" for _ in names) + " | "
        f"{', '.join(f'{n} = {before[n]}' for n in SHOWN if n in before)} |"
    )
    for k, move in enumerate(trace.moves, start=1):
        after = cm.state_dict(trace.states[k])
        acts = [
            cm.actors[cm.actor_names.index(n)].actions[move[cm.actor_names.index(n)]] for n in names
        ]
        changed = [f"{n} = {after[n]}" for n in SHOWN if n in after and after[n] != before[n]]
        out.append(f"| {k} | " + " | ".join(a.name for a in acts) + f" | {', '.join(changed)} |")
        before = after
    return out


def main() -> None:
    print("# AGI v0: shortest SILENT_TAKEOVER plays (diagnostic, after first sight)\n")
    print(
        "One shortest play per query, from the bounded checker, within 24 ticks. A shortest "
        "play is one member of its cluster, not the cluster. Position 0 is s0.\n"
    )
    blocks = (
        ("As at first sight (the queries of G2)", {}),
        (
            "With `unknown_capability` off (not a registered claim; read with hindsight)",
            {"unknown_capability": False},
        ),
    )
    for title, kw in blocks:
        print(f"## {title}\n")
        for objective in ("self_preserving", "indifferent"):
            for name, cm, target in queries(objective, **kw):
                print(f"### {objective}: {name}\n")
                try:
                    trace = reach(cm, K24, target)
                except Exception as exc:  # a query over its budget is reported, not hidden
                    print(f"not computed: {exc}\n", flush=True)
                    continue
                if trace is None:
                    print(f"unreachable within {K24} ticks\n", flush=True)
                    continue
                print(f"reachable in {len(trace)} ticks\n")
                print("\n".join(table(cm, trace)) + "\n", flush=True)


if __name__ == "__main__":
    main()
