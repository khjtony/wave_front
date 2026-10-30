"""Extraction of level proposals from dated documents into a fixed schema (DESIGN.md
section 5.3): a backend protocol, a deterministic rule backend, a Claude backend and a
DeepSeek backend."""

from .backend import Backend, ExtractError, merge_proposals, split_paragraphs
from .cache import CachedBackend
from .claude_backend import ClaudeBackend, ExtractionRefused
from .deepseek_backend import DeepSeekBackend
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
    "CachedBackend",
    "ClaudeBackend",
    "DeepSeekBackend",
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


def make_backend(name: str, model: str | None = None, guidance: str | None = None) -> Backend:
    """``rules``, ``claude`` or ``deepseek`` (the last two with an optional model; ``deepseek``
    with optional ``guidance`` replacing the default guidance). ``guidance=None`` keeps the
    default guidance; any string replaces it, so an empty one (an empty ``--guidance-file``)
    means no guidance, as in ``scripts/compare_backends.py``."""
    if name == "rules":
        return RuleBackend()
    if name == "claude":
        return ClaudeBackend(model) if model else ClaudeBackend()
    if name == "deepseek":
        kw = {"guidance": guidance} if guidance is not None else {}
        return DeepSeekBackend(model, **kw) if model else DeepSeekBackend(**kw)
    raise ValueError(f"unknown backend {name!r} (rules, claude, deepseek)")
