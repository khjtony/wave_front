"""Extraction of level proposals from dated documents into a fixed schema (DESIGN.md
section 5.3): a backend protocol, a deterministic rule backend and a Claude backend."""

from .backend import Backend, ExtractError, merge_proposals, split_paragraphs
from .claude_backend import ClaudeBackend, ExtractionRefused
from .extractor import Extraction, ProposalsFileError, extract, read_proposals, write_proposals
from .rules import RuleBackend
from .schema import (
    PROPOSAL_FIELDS,
    RESOURCE_VARIABLES,
    TEXT_VARIABLES,
    Proposal,
    VariableSpec,
    check_proposal,
    proposal_list_schema,
    text_variables,
)

__all__ = [
    "PROPOSAL_FIELDS",
    "RESOURCE_VARIABLES",
    "TEXT_VARIABLES",
    "Backend",
    "ClaudeBackend",
    "ExtractError",
    "Extraction",
    "ExtractionRefused",
    "Proposal",
    "ProposalsFileError",
    "RuleBackend",
    "VariableSpec",
    "check_proposal",
    "extract",
    "make_backend",
    "merge_proposals",
    "proposal_list_schema",
    "read_proposals",
    "split_paragraphs",
    "text_variables",
    "write_proposals",
]


def make_backend(name: str, model: str | None = None) -> Backend:
    """``rules`` or ``claude`` (with an optional model)."""
    if name == "rules":
        return RuleBackend()
    if name == "claude":
        return ClaudeBackend(model) if model else ClaudeBackend()
    raise ValueError(f"unknown backend {name!r} (rules, claude)")
