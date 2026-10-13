"""The fixed proposal schema of the extractor (DESIGN.md section 5.3).

An extractor reads one dated document against the ontology's threshold rules and proposes
levels, each as a :class:`Proposal` with exactly these fields:

``indicator_id``
    a stable id for the observation (``<document id>:<rule or variable>``)
``variable``, ``level``
    an ontology variable and one of its levels (a level name, an integer, or a boolean)
``date``
    the date of the observation, ``YYYY-MM-DD``: the document's date, or an earlier date the
    document itself states for the event it reports; never after the document's date
``quote``
    the passage of the document the level is read from, verbatim
``url``
    where the document is read
``rule``
    the threshold rule applied, citing the ontology
``confidence``
    ``high``, ``medium`` or ``low``

A proposal is a proposal: it changes nothing until a reviewer accepts it
(:mod:`wavefront.evidence.review`). The schema here is also what a language-model backend is
constrained to emit (:data:`PROPOSAL_LIST_SCHEMA`), and :func:`check_proposal` is applied to
every proposal of every backend before it is written.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from .. import hindsight_ww2 as hw

__all__ = [
    "PROPOSAL_FIELDS",
    "CONFIDENCE",
    "TEXT_VARIABLES",
    "RESOURCE_VARIABLES",
    "Proposal",
    "VariableSpec",
    "text_variables",
    "ontology_rule_text",
    "proposal_list_schema",
    "check_proposal",
    "quote_in_text",
    "level_from_text",
]

PROPOSAL_FIELDS = (
    "indicator_id",
    "variable",
    "level",
    "date",
    "quote",
    "url",
    "rule",
    "confidence",
)
CONFIDENCE = ("high", "medium", "low")

# The variables a replay reads from text (ww2_testbed.md section 8: commitment, belief,
# treaty, pacts, war, regions, and oil where the datasets are silent) and the resource
# variables it copies from the dataset-derived hindsight snapshot instead.
TEXT_VARIABLES = (
    "belief_WEST",
    "belief_GER",
    "commit_WEST",
    "commit_US",
    "treaty",
    "axis",
    "anticomintern",
    "nazi_soviet_pact",
    "polish_guarantee",
    "anglo_soviet_alliance",
    "ussr_axis",
    "italy_estranged",
    "china_war",
    "war_west_ger",
    "rhineland",
    "austria",
    "sudeten",
    "bohemia",
    "poland",
    "france",
    "britain",
    "balkans",
    "siberia",
    "channel_air",
    "oil_GER",
)
RESOURCE_VARIABLES = ("arms_GER", "arms_WEST", "arms_USSR", "arms_JPN", "ind_GER")


@dataclass(frozen=True)
class Proposal:
    """One proposed level, in the fixed schema."""

    indicator_id: str
    variable: str
    level: Any
    date: str
    quote: str
    url: str
    rule: str
    confidence: str

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> Proposal:
        missing = [f for f in PROPOSAL_FIELDS if f not in data]
        extra = [k for k in data if k not in PROPOSAL_FIELDS]
        if missing or extra:
            raise ValueError(f"proposal fields: missing {missing}, unexpected {extra}")
        return cls(**{f: data[f] for f in PROPOSAL_FIELDS})


@dataclass(frozen=True)
class VariableSpec:
    """An ontology variable as an extractor sees it: its levels and threshold rule text."""

    name: str
    kind: str  # "level", "flag" or "integer"
    levels: tuple[Any, ...]
    init: Any
    section: str
    rule_text: str = field(default="", compare=False)

    def level_names(self) -> list[str]:
        return [level_to_text(v) for v in self.levels]


def level_to_text(level: Any) -> str:
    return "true" if level is True else "false" if level is False else str(level)


def level_from_text(spec: VariableSpec, text: Any) -> Any:
    """The level of ``spec`` named by ``text`` (``true``/``false`` for a flag, digits for an
    integer variable); raises ``ValueError`` for a level the variable does not have."""
    if spec.kind == "flag":
        if isinstance(text, bool):
            return text
        low = str(text).strip().lower()
        if low in ("true", "false"):
            return low == "true"
    elif spec.kind == "integer":
        if isinstance(text, int) and not isinstance(text, bool) and text in spec.levels:
            return text
        if str(text).strip().isdigit() and int(str(text).strip()) in spec.levels:
            return int(str(text).strip())
    elif isinstance(text, str) and text.strip() in spec.levels:
        return text.strip()
    raise ValueError(f"{spec.name} has no level {text!r} (levels: {', '.join(spec.level_names())})")


_ROW = re.compile(r"^\|\s*`([A-Za-z_][A-Za-z0-9_]*)`\s*\|")


def ontology_rule_text(path: str | Path = hw.DEFAULT_ONTOLOGY) -> dict[str, str]:
    """The threshold rule (or note) of each variable in the ontology's tables, by name: the
    ``Threshold rule`` column where the table has one, else the ``Note`` column."""
    out: dict[str, str] = {}
    column: int | None = None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            column = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if column is None:
            names = ("Threshold rule", "Note")
            column = next((i for n in names for i, c in enumerate(cells) if c == n), -1)
            continue
        m = _ROW.match(line)
        if m and 0 <= column < len(cells) and m.group(1) not in out:
            out[m.group(1)] = cells[column]
    return out


def text_variables(
    names: Iterable[str] = TEXT_VARIABLES, ontology: str | Path = hw.DEFAULT_ONTOLOGY
) -> list[VariableSpec]:
    """The ontology variables ``names`` with their levels (from the hindsight builder's table,
    which a test keeps equal to the ontology) and their threshold rule text."""
    rules = ontology_rule_text(ontology) if Path(ontology).exists() else {}
    specs = []
    for name in names:
        var = hw.BY_NAME[name]
        specs.append(
            VariableSpec(
                name=var.name,
                kind=var.kind,
                levels=tuple(var.levels),
                init=var.init,
                section=var.section,
                rule_text=rules.get(name, ""),
            )
        )
    return specs


def proposal_list_schema(variables: Iterable[VariableSpec]) -> dict[str, Any]:
    """The JSON Schema a structured-output backend must fill: ``{"proposals": [...]}`` with
    every field of :data:`PROPOSAL_FIELDS` required and nothing else allowed. Levels are
    strings (``true``/``false`` for flags) and are converted by :func:`level_from_text`."""
    names = [v.name for v in variables]
    item = {
        "type": "object",
        "properties": {
            "indicator_id": {"type": "string"},
            "variable": {"type": "string", "enum": names},
            "level": {"type": "string"},
            "date": {"type": "string", "description": "YYYY-MM-DD"},
            "quote": {"type": "string"},
            "url": {"type": "string"},
            "rule": {"type": "string"},
            "confidence": {"type": "string", "enum": list(CONFIDENCE)},
        },
        "required": list(PROPOSAL_FIELDS),
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {"proposals": {"type": "array", "items": item}},
        "required": ["proposals"],
        "additionalProperties": False,
    }


_WS = re.compile(r"\s+")
_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})


def _norm(text: str) -> str:
    return _WS.sub(" ", text.translate(_QUOTES)).strip().lower()


def quote_in_text(quote: str, text: str) -> bool:
    """Whether ``quote`` occurs in ``text`` verbatim, up to whitespace, case and curly
    quotes. An ellipsis (``...``) may join verbatim pieces that occur in order."""
    pieces = [p for p in re.split(r"\s*(?:\.\.\.|…)\s*", quote) if p.strip()]
    if not pieces:
        return False
    hay = _norm(text)
    pos = 0
    for piece in pieces:
        found = hay.find(_norm(piece), pos)
        if found < 0:
            return False
        pos = found + len(_norm(piece))
    return True


def check_proposal(
    proposal: Proposal, variables: Mapping[str, VariableSpec], document_date: date, text: str
) -> list[str]:
    """Why ``proposal`` cannot be kept for a document dated ``document_date`` with ``text``:
    an unknown variable or level, a malformed or later date, a quote not in the document, an
    empty field or an unknown confidence. Empty when it can be kept."""
    problems = []
    spec = variables.get(proposal.variable)
    if spec is None:
        problems.append(f"variable {proposal.variable!r} is not extracted from text")
    elif proposal.level not in spec.levels or (
        isinstance(proposal.level, bool) != (spec.kind == "flag")
    ):
        problems.append(f"{proposal.variable} has no level {proposal.level!r}")
    try:
        day = date.fromisoformat(proposal.date)
    except (TypeError, ValueError):
        problems.append(f"date {proposal.date!r} is not YYYY-MM-DD")
    else:
        if day > document_date:
            problems.append(
                f"date {proposal.date} is after the document's date {document_date} "
                "(a document cannot observe its future)"
            )
    for name in ("indicator_id", "quote", "url", "rule"):
        if not isinstance(getattr(proposal, name), str) or not getattr(proposal, name).strip():
            problems.append(f"{name} is empty")
    if proposal.confidence not in CONFIDENCE:
        problems.append(f"confidence {proposal.confidence!r} is not one of {CONFIDENCE}")
    if isinstance(proposal.quote, str) and proposal.quote.strip():
        if not quote_in_text(proposal.quote, text):
            problems.append("the quote is not in the document")
    return problems
