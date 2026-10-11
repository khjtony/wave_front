"""Markdown rendering of an :class:`~wavefront.analysis.Analysis` (spec section 8)."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from ..analysis import Analysis, Distance

__all__ = ["render", "CAVEAT"]

CAVEAT = (
    "Every result is conditional on the model version and the initial state; "
    "no bare reachability result is a finding."
)

MAX_LISTED_STATES = 20
MAX_SENSITIVITY_ROWS = 25


def _coalition(c: Iterable[str]) -> str:
    return "{" + ", ".join(c) + "}"


def _cell(text: object) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def _table(header: Sequence[str], rows: Iterable[Sequence[object]]) -> list[str]:
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(_cell(x) for x in row) + " |" for row in rows]
    return out


def _num(x: int | float | None, none: str = "-") -> str:
    if x is None:
        return none
    if isinstance(x, float) and math.isinf(x):
        return "unbounded"
    return str(x)


def _plural(n: int, noun: str) -> str:
    return f"{n} {noun}" if n == 1 else f"{n} {noun}s"


def _smallest(values: Iterable[int | float | None]) -> int | float | None:
    finite = [v for v in values if v is not None]
    return min(finite) if finite else None


def _header(a: Analysis) -> list[str]:
    m, g = a.model, a.graph
    horizon = f"horizon {m.horizon}" if m.timed else "untimed (no horizon)"
    profile = (
        "none"
        if not a.profile
        else (a.profile if isinstance(a.profile, str) else ", ".join(a.profile))
    )
    origin = "explicit (given to the analysis)" if a.explicit_initial else "the model's declared"
    k = f"the full horizon ({m.horizon} ticks)" if m.timed else "the full reachable graph"
    lines = [
        f"# Analysis report: {m.name}",
        "",
        CAVEAT,
        "",
        f"- Model: `{m.name}`, {horizon}, fingerprint `{a.fingerprint}`",
    ]
    if m.description:
        lines.append(f"- Description: {m.description}")
    lines += [
        f"- Profile: {profile}",
        f"- Initial states: {len(g.initial)} ({origin} initial states)",
        f"- Reachable states: {g.size()}",
        f"- Coalitions analysed: {', '.join(_coalition(c) for c in a.coalitions) or 'none'}",
        f"- Relaxation search: explicit re-exploration over {k}, sets of at most "
        f"{a.max_relax} assumptions",
        "- Strategies are perfect-information (one move per state); for coalitions with "
        "hidden variables a forcing or keeping result is an upper bound unless the "
        "strategy is uniform (see the uniformity section).",
        "",
    ]
    return lines


def _budget(a: Analysis) -> list[str]:
    lines = ["## Parameter budget", ""]
    lines += _table(["quantity", "count"], [(k.replace("_", " "), v) for k, v in a.budget.items()])
    return [*lines, ""]


def _distance_cell(member: bool, d: Distance) -> str:
    if not member:
        return "no"
    return f"yes (shortest {_num(d.shortest, 'never')}, margin {_num(d.margin)})"


def _kernels(a: Analysis) -> list[str]:
    g = a.graph
    lines = ["## Initial states and kernel membership", ""]
    init = list(g.initial)
    shown = init[:MAX_LISTED_STATES]
    lines += _table(["id", "state"], [(f"#{s}", g.format_state(s)) for s in shown])
    if len(init) > len(shown):
        lines.append(f"\n({len(init) - len(shown)} more initial states not listed.)")
    lines.append("")
    if not a.model.invariants:
        return [*lines, "The model declares no invariant, so there is no kernel to report.", ""]
    lines += [
        "A state is in the kernel of a coalition when the coalition can keep the invariant "
        "whatever the others and Nature do. *Shortest* is the fewest steps of some play that "
        "leave the kernel; *margin* the number of ticks of arbitrary play that certainly "
        "stay inside it; *if X defects* the forced distance out of a joint kernel when "
        "member X plays against the rest of the coalition.",
        "",
    ]
    for inv in a.model.invariants:
        lines += [f"### Invariant `{inv}`", ""]
        rows = []
        for e in (e for e in a.kernels if e.invariant == inv):
            n_in = sum(e.in_kernel.values())
            inside = [s for s in init if e.in_kernel[s]]
            defect = (
                "; ".join(
                    f"{m}: {_num(_smallest(d.values()), 'cannot')}" for m, d in e.defection.items()
                )
                or "-"
            )
            rows.append(
                (
                    _coalition(e.coalition),
                    f"{n_in} of {len(init)}",
                    _num(_smallest(e.distances[s].shortest for s in inside), "never"),
                    _num(_smallest(e.distances[s].margin for s in inside)),
                    defect,
                    len(e.kernel.kernel),
                )
            )
        lines += _table(
            [
                "coalition",
                "initial states in kernel",
                "min shortest",
                "min margin",
                "min forced if X defects",
                "kernel size",
            ],
            rows,
        )
        lines.append("")
        if len(init) <= MAX_LISTED_STATES:
            entries = [e for e in a.kernels if e.invariant == inv]
            per_state = [
                (f"#{s}", *(_distance_cell(e.in_kernel[s], e.distances[s]) for e in entries))
                for s in init
            ]
            lines += _table(
                ["initial state", *(_coalition(e.coalition) for e in entries)], per_state
            )
            lines.append("")
    return lines


def _endings(a: Analysis) -> list[str]:
    g = a.graph
    lines = [
        "## Endings",
        "",
        "Per coalition, the initial states from which it can force the ending (*forced*), "
        "from which the others and Nature can keep it from happening (*blocked*), and "
        "neither (*contested*: the game is not determined there).",
        "",
    ]
    for ending in a.endings:
        lines += [f"### `{ending}`", ""]
        rows = []
        for e in (e for e in a.contested if e.ending == ending):
            counts = {k: sum(v == k for v in e.status.values()) for k in ("forced", "blocked")}
            counts["contested"] = len(e.status) - counts["forced"] - counts["blocked"]
            rows.append(
                (
                    _coalition(e.coalition),
                    counts["forced"],
                    counts["blocked"],
                    counts["contested"],
                    _num(max(e.rank.values()) if e.rank else None),
                )
            )
        lines += _table(
            ["coalition", "forced", "blocked", "contested", "forced within (ticks, worst case)"],
            rows,
        )
        lines.append("")
        trace = a.witnesses.get(ending)
        if trace is None:
            lines += ["No play reaches this ending from any initial state.", ""]
        else:
            lines += [
                f"Shortest witness from initial state #{trace[0][0]} "
                f"({_plural(len(trace) - 1, 'step')}). "
                "It shows that some joint choice of every actor and Nature reaches the ending; "
                "by itself it is not a finding.",
                "",
                trace.render(g),
                "",
            ]
    return lines


def _relaxations(a: Analysis) -> list[str]:
    lines = [
        "## Minimal relaxation sets",
        "",
        "The smallest sets of named assumptions (guards, fairness constraints, selected "
        "profiles, `assume` restrictions) whose relaxation makes each ending reachable "
        f"from some initial state, searched up to size {a.max_relax}.",
        "",
    ]
    rows = []
    notes = []
    for ending in a.endings:
        r = a.relaxations[ending]
        if not r:
            size, sets = f"> {r.max_size}", "none found"
        else:
            size = str(r.minimum_size)
            sets = "; ".join("{" + ", ".join(s) + "}" if s else "{} (no relaxation)" for s in r)
        rows.append((f"`{ending}`", size, sets))
        for s, msg in r.ill_formed:
            notes.append(f"- `{ending}`: relaxing {{{', '.join(s)}}} is ill-formed: {msg}")
        for s, msg in r.undecided:
            notes.append(f"- `{ending}`: relaxing {{{', '.join(s)}}} is undecided: {msg}")
    lines += _table(["ending", "minimum size", "minimal sets"], rows)
    if notes:
        lines += ["", "Relaxations not counted as results:", "", *notes]
    return [*lines, ""]


def _pivotal(a: Analysis) -> list[str]:
    lines = [
        "## Pivotal coalitions",
        "",
        "Minimal coalitions of declared actors (Nature always adversarial) that can force, "
        "or block, each ending from every initial state.",
        "",
    ]

    def fmt(cs: list[frozenset[str]]) -> str:
        order = {n: i for i, n in enumerate(a.cm.actor_names)}
        return "; ".join(_coalition(sorted(c, key=order.__getitem__)) for c in cs) if cs else "none"

    rows = [(f"`{e}`", fmt(a.pivotal[e].forcing), fmt(a.pivotal[e].blocking)) for e in a.endings]
    lines += _table(["ending", "forcing", "blocking"], rows)
    return [*lines, ""]


def _sensitivity(a: Analysis) -> list[str]:
    lines = [
        "## Sensitivity",
        "",
        "Each row moves one variable's initial value one level and compares kernel "
        "membership and the shortest distance out of the kernel for the initial states "
        "concerned; rows are sorted by effect.",
        "",
    ]
    if not a.sensitivity:
        return [*lines, "No invariant is declared, so there is nothing to perturb against.", ""]
    for (inv, c), rows in a.sensitivity.items():
        lines += [f"### `{inv}` for {_coalition(c)}", ""]
        if not rows:
            lines += ["No variable has a legal one-level change.", ""]
            continue
        body = []
        for r in rows[:MAX_SENSITIVITY_ROWS]:
            if r.error:
                body.append(
                    (r.variable, f"{r.from_level} -> {r.to_level}", r.states, "error", "-", r.error)
                )
                continue
            body.append(
                (
                    r.variable,
                    f"{r.from_level} -> {r.to_level}",
                    r.states,
                    f"{r.base_in_kernel} -> {r.new_in_kernel}",
                    r.flips,
                    f"{_num(r.base_shortest, 'never')} -> {_num(r.new_shortest, 'never')}",
                )
            )
        lines += _table(
            ["variable", "initial value", "states", "in kernel", "flips", "min shortest"], body
        )
        if len(rows) > MAX_SENSITIVITY_ROWS:
            lines.append(
                f"\n({len(rows) - MAX_SENSITIVITY_ROWS} rows with smaller effect omitted.)"
            )
        lines.append("")
    return lines


def _uniformity(a: Analysis) -> list[str]:
    lines = ["## Strategy uniformity", ""]
    bad = [n for n in a.uniformity if not n.result.uniform]
    if not a.uniformity:
        return [*lines, "No forcing or keeping result holds from an initial state.", ""]
    for n in bad:
        what = "Keeping" if n.kind == "keep" else "Forcing"
        member, s, t = n.result.conflicts[0]
        pooled = (
            "It would be playable if the members pooled their observations."
            if n.result.jointly_uniform
            else "Even with pooled observations it is not uniform."
        )
        lines.append(
            f"- {what} `{n.subject}` for {_coalition(n.coalition)} rests on a non-uniform "
            f"strategy: {_plural(len(n.result.conflicts), 'conflict')}, for example member "
            f"{member} cannot tell states #{s} and #{t} apart but must move differently in "
            f"them. {pooled} The result is an upper bound on what the members can do each "
            "acting on their own observations."
        )
    good = len(a.uniformity) - len(bad)
    if not bad:
        lines.append(
            f"Every forcing and keeping result above ({good}) rests on a strategy that each "
            "member can play on its own observations."
        )
    elif good:
        lines.append(
            f"- The other {_plural(good, 'forcing or keeping result')} rest on uniform strategies."
        )
    return [*lines, ""]


def _speculative(a: Analysis) -> list[str]:
    lines = ["## Speculative actions used", ""]
    if not a.speculative:
        return [*lines, "None of the reported traces uses a speculative action.", ""]
    lines.append("The reported witness traces use these actions marked `speculative=True`:")
    lines.append("")
    lines += [f"- `{name}`" for name in a.speculative]
    return [*lines, ""]


def render(analysis: Analysis) -> str:
    """Markdown report of an analysis, in the order of spec section 8: the caveat, the
    model and its parameter budget, initial states and kernel membership per coalition,
    endings with forced/blocked/contested status and shortest witness traces, minimal
    relaxation sets, pivotal coalitions, the sensitivity table, strategy uniformity notes
    and the speculative actions used by any reported trace."""
    parts = [
        _header(analysis),
        _budget(analysis),
        _kernels(analysis),
        _endings(analysis),
        _relaxations(analysis),
        _pivotal(analysis),
        _sensitivity(analysis),
        _uniformity(analysis),
        _speculative(analysis),
    ]
    return "\n".join(line for part in parts for line in part).rstrip() + "\n"
