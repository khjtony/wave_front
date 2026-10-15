"""The harness rules of the replay and review layer (owner's decision 9 of 2026-10-15).

The rule backend's keyword table stays frozen as the FRUS baseline; these rules act on the
proposals of any backend, after extraction and before review or measurement. They are named,
can be switched off one by one (``wf replay --rules``, ``wf extract --rules``), are recorded in
every proposals file (``harness_rules``) and are stated in every generated report.

Both rules apply to the structural variables only: never to the belief and commitment
variables (:data:`READINGS`: ``belief_WEST``, ``belief_GER``, ``commit_WEST``,
``commit_US``), which are what the replay exists to read and whose flips the rules would
freeze (decision of 2026-10-15 on the FRUS measurement). A proposal for one of them is shown
and counted as the backend made it.

``two-document``
    A flip of a structural variable that changes once (a flag, or a variable the model
    declares monotone: the pacts, the regions but the Rhineland, the war, ``oil_GER``;
    :data:`ONCE`) needs two independent
    documents, that is proposals of the same level from two different document ids, both
    dated at or before the quarter. The first is *held*: it is not shown as a proposal for
    review, cannot be accepted, and is not counted by ``--measure-proposals``. The proposal
    of the second document carries the flip, so the flip is dated by it; the first is then
    shown with it as *corroborating* and never sets the level by itself. Later proposals of
    the same level are shown as usual.

``no-retrospective``
    A proposal that would move a variable back to an earlier level (a retrospective
    reading: a recollection, background, a document about the past) is never applied to a
    monotone variable (:data:`MONOTONE`; *blocked*: shown apart, cannot be accepted, never
    counted), and for any other variable it is shown flagged ``retrospective?`` and never
    auto-applied: ``--measure-proposals`` does not count it, ``--auto-accept`` rejects it
    with a note, and only a reviewer's acceptance applies it. "Back" means, for a monotone
    variable, a level below the current one in the level order; for any other variable, a
    level the variable has held earlier in the replay (its initial level included) and has
    since left.

The current level against which a proposal is a flip or a move back is the replay's own
level just before the proposal's date: in review, the level set by accepted proposals that
are in force; in a measurement, the level set by every proposal in force. Proposals are taken
in date order (file order breaks ties), as the review step builds snapshots.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from . import hindsight_ww2 as hw
from .extract.schema import TEXT_VARIABLES

__all__ = [
    "BLOCKED",
    "CORROBORATING",
    "DEFAULT_RULES",
    "HELD",
    "READINGS",
    "V0_MONOTONE",
    "MONOTONE",
    "NO_RETROSPECTIVE",
    "OK",
    "ONCE",
    "RETROSPECTIVE",
    "RULE_NAMES",
    "TWO_DOCUMENT",
    "Gate",
    "Gating",
    "RulesError",
    "describe_rules",
    "gate_records",
    "parse_rules",
    "record_key",
]

TWO_DOCUMENT = "two-document"
NO_RETROSPECTIVE = "no-retrospective"
RULE_NAMES = (TWO_DOCUMENT, NO_RETROSPECTIVE)
DEFAULT_RULES: tuple[str, ...] = RULE_NAMES

# The text variables that models/ww2/v0.py (the model the replay snapshots are for, hw.MODEL)
# declares monotone=True. tests/evidence/test_harness_rules.py keeps this equal to the model.
V0_MONOTONE = frozenset(
    {
        "belief_WEST",
        "commit_WEST",
        "commit_US",
        "oil_GER",
        "axis",
        "anticomintern",
        "nazi_soviet_pact",
        "polish_guarantee",
        "anglo_soviet_alliance",
        "ussr_axis",
        "china_war",
        "austria",
        "sudeten",
        "bohemia",
        "poland",
        "france",
        "britain",
        "balkans",
        "siberia",
        "channel_air",
        "war_west_ger",
    }
)
#: the belief and commitment variables: outside both rules, by name
READINGS = frozenset({"belief_WEST", "belief_GER", "commit_WEST", "commit_US"})
#: the monotone variables the rules treat as such: v0's, without the belief and commitment ones
MONOTONE = V0_MONOTONE - READINGS
FLAGS = frozenset(n for n in TEXT_VARIABLES if hw.BY_NAME[n].kind == "flag")
#: the variables under the two-document rule: every flag and every structural monotone variable
ONCE = (FLAGS | MONOTONE) - READINGS

OK = "ok"
HELD = "held"
CORROBORATING = "corroborating"
BLOCKED = "blocked"
RETROSPECTIVE = "retrospective?"
#: statuses that need a reviewer's decision while pending (shown as proposals for review)
FOR_REVIEW = (OK, RETROSPECTIVE)
#: statuses a reviewer cannot accept
NOT_ACCEPTABLE = (HELD, BLOCKED)


class RulesError(ValueError):
    """An unknown harness rule name, or proposals files that disagree on the rules."""


def parse_rules(text: str | Iterable[str] | None) -> tuple[str, ...]:
    """``two-document,no-retrospective`` (any order), one of them, or ``none``; ``None`` gives
    the default (both). Returned in the canonical order."""
    if text is None:
        return DEFAULT_RULES
    names = text.split(",") if isinstance(text, str) else list(text)
    names = [n.strip() for n in names if n.strip()]
    if names in ([], ["none"]):
        return ()
    unknown = [n for n in names if n not in RULE_NAMES]
    if unknown:
        raise RulesError(
            f"unknown harness rule(s) {', '.join(unknown)} (rules: {', '.join(RULE_NAMES)}, "
            "or none)"
        )
    return tuple(n for n in RULE_NAMES if n in names)


def describe_rules(rules: Sequence[str]) -> str:
    """One line for a report: the rules in force, or that none were."""
    if not rules:
        return "none (every proposal is shown and counted as the backend made it)"
    return ", ".join(f"`{r}`" for r in rules)


def record_key(rec: dict[str, Any]) -> tuple[Any, ...]:
    """Proposals repeated across files (same document, variable, level and quote) count once."""
    p = rec["proposal"]
    return (rec["document"], p["variable"], repr(p["level"]), p["quote"])


@dataclass(frozen=True)
class Gate:
    """What the harness rules make of one proposal at a cut-off."""

    status: str
    reason: str = ""

    @property
    def for_review(self) -> bool:
        return self.status in FOR_REVIEW

    @property
    def acceptable(self) -> bool:
        return self.status not in NOT_ACCEPTABLE


@dataclass
class Gating:
    """The gate of each record (parallel to the records given, ``None`` for a record dated
    after the cut-off) and the records in force: the ones that set or confirm a level, in
    the order given."""

    gates: list[Gate | None]
    in_force: list[dict[str, Any]] = field(default_factory=list)

    def counts(self, records: Sequence[dict[str, Any]]) -> dict[str, Counter[str]]:
        """Per variable, the number of records of each gate status."""
        out: dict[str, Counter[str]] = {}
        for rec, gate in zip(records, self.gates, strict=True):
            if gate is not None:
                out.setdefault(rec["proposal"]["variable"], Counter())[gate.status] += 1
        return out


def _backward(name: str, level: Any, current: Any, held: list[Any]) -> bool:
    if name in MONOTONE:
        levels = hw.BY_NAME[name].levels
        return levels.index(level) < levels.index(current)
    return level in held


def gate_records(
    records: Sequence[dict[str, Any]],
    until: date,
    rules: Sequence[str],
    *,
    measure: bool,
    proposes: Callable[[dict[str, Any]], bool] | None = None,
    accepted: Callable[[dict[str, Any]], bool] | None = None,
) -> Gating:
    """Apply ``rules`` to proposal ``records`` (deduplicated, in file order) at the cut-off
    ``until``.

    With ``measure`` every record counts as a proposing document and as accepted, except
    that a ``retrospective?`` record is never applied (not auto-applied). Otherwise (review)
    a record proposes unless rejected, and is applied only when accepted (a
    ``retrospective?`` one included: the reviewer decided). ``proposes`` and ``accepted``
    override these defaults."""
    if proposes is None:
        proposes = (lambda r: True) if measure else (lambda r: r["status"] != "rejected")
    if accepted is None:
        accepted = (lambda r: True) if measure else (lambda r: r["status"] == "accepted")
    two_doc = TWO_DOCUMENT in rules
    no_retro = NO_RETROSPECTIVE in rules
    gates: list[Gate | None] = [None] * len(records)
    state = {n: hw.BY_NAME[n].init for n in TEXT_VARIABLES}
    held = {n: [hw.BY_NAME[n].init] for n in TEXT_VARIABLES}
    candidates: dict[tuple[str, str], list[tuple[int, str]]] = {}
    applied: set[int] = set()

    def apply(i: int, name: str, level: Any) -> None:
        state[name] = level
        if level not in held[name]:
            held[name].append(level)
        applied.add(i)

    order = sorted(range(len(records)), key=lambda i: (records[i]["proposal"]["date"], i))
    for i in order:
        rec = records[i]
        p = rec["proposal"]
        if date.fromisoformat(p["date"]) > until:
            continue
        name, level = p["variable"], p["level"]
        if name not in state:
            gates[i] = Gate(OK, "not a text variable")
            continue
        current = state[name]
        if name in READINGS:  # outside both rules: shown and counted as the backend made it
            gates[i] = Gate(OK, "confirms the current level" if level == current else "a flip")
            if accepted(rec):
                apply(i, name, level)
            continue
        if level == current:
            gates[i] = Gate(OK, "confirms the current level")
            if accepted(rec):
                applied.add(i)
            continue
        if no_retro and _backward(name, level, current, held[name]):
            if name in MONOTONE:
                gates[i] = Gate(
                    BLOCKED,
                    f"no-retrospective: {name} is monotone and is at {current!r}; a move back "
                    f"to {level!r} is never applied",
                )
            else:
                gates[i] = Gate(
                    RETROSPECTIVE,
                    f"no-retrospective: {name} held {level!r} earlier and is now at "
                    f"{current!r}; a reviewer decides, nothing applies it automatically",
                )
                if not measure and accepted(rec):
                    apply(i, name, level)
            continue
        if two_doc and name in ONCE:
            bucket = candidates.setdefault((name, repr(level)), [])
            documents = {d for _j, d in bucket}
            if not proposes(rec):
                gates[i] = Gate(HELD, "rejected: does not count as a proposing document")
                continue
            if not documents or rec["document"] in documents:
                bucket.append((i, rec["document"]))
                gates[i] = Gate(
                    HELD,
                    f"two-document: the only document so far proposing {name} := {level!r}",
                )
                continue
            first = [j for j, _d in bucket]
            bucket.append((i, rec["document"]))
            for j in first:
                g = gates[j]
                if g is not None and g.status == HELD:
                    gates[j] = Gate(
                        CORROBORATING,
                        f"two-document: corroborates the flip carried by {rec['id']}",
                    )
            gates[i] = Gate(
                OK,
                "two-document: corroborated by "
                + ", ".join(sorted({records[j]["document"] for j in first})),
            )
            if accepted(rec):
                apply(i, name, level)
            continue
        gates[i] = Gate(OK, "a flip")
        if accepted(rec):
            apply(i, name, level)
    return Gating(gates=gates, in_force=[records[i] for i in range(len(records)) if i in applied])
