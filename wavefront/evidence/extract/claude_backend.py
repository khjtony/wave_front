"""A Claude backend for the extractor, written to the Claude API reference.

The ``anthropic`` SDK is an optional dependency (``pip install -e .[extract]``) and is imported
only when a request is first made, so this module imports without it; tests pass a fake
client and a fake SDK module.

How a document is read:

* The document is split at paragraph breaks into parts of at most ``max_chars`` characters
  (:func:`~.backend.split_paragraphs`); a long document is never truncated, each part is read
  in its own request and the proposals of all parts are merged
  (:func:`~.backend.merge_proposals`). A part whose answer hits ``max_tokens`` is split in two
  and read again, so an answer is never cut short silently either.
* One request per part through the Messages API on the beta namespace,
  ``client.beta.messages.create``, with: the model (the default model unless configured);
  no ``thinking`` parameter, so the model runs with adaptive thinking (its default when the
  parameter is omitted); ``output_config`` with an explicit ``effort`` and a JSON-schema
  ``format`` (structured outputs) that constrains the answer to
  :func:`~.schema.proposal_list_schema`; the server-side refusal fallback opted in with
  ``fallbacks="default"`` and the beta ``server-side-fallback-2026-07-01``; a stable system
  prompt (the instructions and the ontology's threshold rules) marked for prompt caching.
* ``stop_reason`` is checked before the content is read: ``refusal`` (after the fallback
  chain) raises :class:`ExtractionRefused` with the category; ``max_tokens`` splits the part.
  The first text block is parsed as JSON and each proposal converted to the fixed schema; the
  ``indicator_id`` and ``url`` are set from the document, not taken from the model.
* API errors are caught most specific first (bad request, authentication, permission, not
  found, rate limit, other status errors by status code, connection errors) and raised as
  :class:`~.backend.ExtractError` with ``retryable`` set for rate limits, server errors and
  network failures. The SDK already retries those a few times before raising.

Every response's ``usage`` (input, output, cache write and cache read tokens) is added to
:attr:`ClaudeBackend.usage`, and the replay records it per quarter in the proposals file, so a
pilot run measures the cost of a full run. :meth:`ClaudeBackend.cache_identity` names what an
answer depends on, for the per-document cache (:mod:`.cache`) that lets a stopped run resume.

The extractor (:mod:`.extractor`) then checks every proposal: a quote that is not verbatim in
the document, a date after the document's, or an unknown level is discarded with a reason.
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections import Counter
from collections.abc import Sequence
from typing import Any

from ..corpora.base import Document
from ..episodes import get_episode
from .backend import ExtractError, merge_proposals, split_paragraphs
from .schema import Proposal, VariableSpec, level_from_text, proposal_list_schema

__all__ = [
    "ClaudeBackend",
    "ExtractionRefused",
    "DEFAULT_MODEL",
    "FALLBACK_BETA",
    "BELIEF_PROMPT",
    "SYSTEM_PROMPT",
    "system_prompt",
]

DEFAULT_MODEL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"
DEFAULT_MAX_TOKENS = 16000
DEFAULT_MAX_CHARS = 200_000
DEFAULT_EFFORT = "high"
MAX_RESPLITS = 4
USAGE_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
)

SYSTEM_PROMPT = """\
You read one dated historical document and propose levels for the variables of a model of \
European politics, 1936 to 1940. You fill a fixed schema; you never decide anything: every \
proposal goes to a human reviewer.

This is a blind replay. Use only the text of the document you are given. Do not use what you \
know about events after the document's date, about how events turned out, or about other \
documents. If the document does not itself show that a variable is at a level, propose \
nothing for that variable. Proposing nothing is the correct answer for most variables of \
most documents.

For each proposal:
- variable and level: one of the variables listed below and one of its levels, chosen by the \
threshold rule given for it. Flags take the levels true and false.
- quote: the shortest passage of the document, copied verbatim (exact words, no paraphrase), \
from which the level is read. Use "..." only to join verbatim pieces in their order.
- date: the date of the observation, YYYY-MM-DD: the document's date, or an earlier date the \
document itself gives for the event it reports. Never a date after the document's date.
- rule: which threshold rule you applied and why the passage meets it, in one sentence.
- confidence: high when the passage states the observation outright, medium when it needs \
the threshold judgment, low when the reading is doubtful.
- indicator_id and url: any non-empty string; they are replaced by the document's.

A report of a plan, a threat, a rumour or a hypothetical is not an observation of the \
planned event. A statement by one government about another government's intentions is \
evidence of the speaker's belief, not of the other government's.

Variables and their threshold rules:
"""


# The paragraph added before the variables for an episode whose variables are beliefs.
BELIEF_PROMPT = """\
Every variable below is a belief: the estimate or reading of one government, named in its \
threshold rule. Propose a level from what the document shows that government's own estimate \
or reading to be, not from what the document shows the facts to be: an estimate that \
projects a force is evidence of the estimating government's belief whether or not the force \
was ever built. A document of one government that reports what another government believes \
or fears is evidence of the reporting government's belief, not of the other's: propose the \
other government's reading only where the document reproduces that government's own words \
(a quoted instruction, statement or document), and say so in the rule.

"""
_VARIABLES_HEADING = "Variables and their threshold rules:\n"
_WW2_SCOPE = "European politics, 1936 to 1940"


def _episode_prompt(episode: str) -> tuple[str, str]:
    """The instructions and the date of the initial levels for ``episode``. WW2's are
    :data:`SYSTEM_PROMPT` and 1 January 1936, unchanged; another episode's replace the
    period in the first sentence and add :data:`BELIEF_PROMPT` when its variables are all
    readings."""
    ep = get_episode(episode)
    if ep.name == "ww2":
        return SYSTEM_PROMPT, "1 January 1936"
    head = SYSTEM_PROMPT.replace(_WW2_SCOPE, ep.scope, 1)
    if set(ep.text_variables) <= ep.readings:
        head = head.replace(_VARIABLES_HEADING, BELIEF_PROMPT + _VARIABLES_HEADING, 1)
    return head, ep.start


def system_prompt(variables: Sequence[VariableSpec]) -> str:
    """The instructions followed by each variable's levels and threshold rule text. The
    instructions are those of the variables' episode (:attr:`VariableSpec.episode`; all the
    variables must be of one episode)."""
    episodes = {v.episode for v in variables} or {"ww2"}
    if len(episodes) > 1:
        raise ValueError(f"variables of several episodes: {', '.join(sorted(episodes))}")
    head, start = _episode_prompt(episodes.pop())
    lines = [head]
    for v in variables:
        rule = " ".join(v.rule_text.split()) or "(no threshold text in the ontology)"
        lines.append(
            f"\n## {v.name}\nlevels: {', '.join(v.level_names())}\n"
            f"initial level ({start}): {v.level_names()[v.levels.index(v.init)]}\n"
            f"threshold rule: {rule}\n"
        )
    return "".join(lines)


class ExtractionRefused(ExtractError):
    """The request was declined (``stop_reason == "refusal"``) after the fallback chain."""

    def __init__(self, message: str, category: str | None) -> None:
        super().__init__(message, retryable=False)
        self.category = category


class ClaudeBackend:
    """Proposes levels with Claude through structured outputs (see the module docstring)."""

    name = "claude"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        *,
        client: Any = None,
        sdk: Any = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        max_chars: int = DEFAULT_MAX_CHARS,
        effort: str = DEFAULT_EFFORT,
        fallbacks: bool = True,
    ) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self.max_chars = max_chars
        self.effort = effort
        self.fallbacks = fallbacks
        self._client = client
        self._sdk = sdk
        self.requests = 0
        #: tokens reported by the responses so far (:data:`USAGE_FIELDS`)
        self.usage: Counter[str] = Counter()
        self._lock = threading.Lock()

    def cache_identity(self, variables: Sequence[VariableSpec]) -> dict[str, Any]:
        """What an answer depends on besides the document (for :mod:`.cache`)."""
        return {
            "model": self.model,
            "effort": self.effort,
            "max_tokens": self.max_tokens,
            "max_chars": self.max_chars,
            "fallbacks": self.fallbacks,
            "system": hashlib.sha256(system_prompt(variables).encode("utf-8")).hexdigest(),
            "schema": hashlib.sha256(
                json.dumps(proposal_list_schema(variables), sort_keys=True).encode("utf-8")
            ).hexdigest(),
        }

    def parts(self, document: Document) -> list[str]:
        """The parts the document is read in (one request each, before any re-split)."""
        return split_paragraphs(document.text, self.max_chars)

    # -- the SDK, imported lazily ---------------------------------------------------------

    @property
    def sdk(self) -> Any:
        if self._sdk is None:
            try:
                import anthropic
            except ImportError as exc:
                raise ExtractError(
                    "the Claude backend needs the anthropic SDK: pip install -e '.[extract]'"
                ) from exc
            self._sdk = anthropic
        return self._sdk

    @property
    def client(self) -> Any:
        if self._client is None:
            # The zero-argument client resolves credentials from the environment.
            self._client = self.sdk.Anthropic()
        return self._client

    # -- requests -------------------------------------------------------------------------

    def request_params(
        self,
        document: Document,
        part: str,
        index: int,
        total: int,
        variables: Sequence[VariableSpec],
    ) -> dict[str, Any]:
        """The keyword arguments of one ``beta.messages.create`` call."""
        where = (
            f" (part {index + 1} of {total}; the other parts are read separately)"
            if total > 1
            else ""
        )
        user = (
            f"Document id: {document.id}\nDocument date: {document.date.isoformat()}\n"
            f"Source: {document.source}\nTitle: {document.title}\nURL: {document.url}\n\n"
            f"Text{where}:\n<document>\n{part}\n</document>"
        )
        params: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": [
                {
                    "type": "text",
                    "text": system_prompt(variables),
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            "messages": [{"role": "user", "content": user}],
            "output_config": {
                "effort": self.effort,
                "format": {"type": "json_schema", "schema": proposal_list_schema(variables)},
            },
        }
        if self.fallbacks:
            params["betas"] = [FALLBACK_BETA]
            params["fallbacks"] = "default"
        return params

    def _create(self, params: dict[str, Any]) -> Any:
        sdk = self.sdk
        with self._lock:
            self.requests += 1
        try:
            if self.fallbacks:
                return self.client.beta.messages.create(**params)
            return self.client.messages.create(**params)
        except sdk.BadRequestError as exc:
            raise ExtractError(f"request rejected (400): {exc.message}") from exc
        except sdk.AuthenticationError as exc:
            raise ExtractError("authentication failed: check the API credentials") from exc
        except sdk.PermissionDeniedError as exc:
            raise ExtractError("the credentials lack permission for this request") from exc
        except sdk.NotFoundError as exc:
            raise ExtractError(f"model or endpoint not found: {self.model}") from exc
        except sdk.RateLimitError as exc:
            retry = exc.response.headers.get("retry-after", "60")
            raise ExtractError(f"rate limited; retry after {retry}s", retryable=True) from exc
        except sdk.APIStatusError as exc:
            if exc.status_code >= 500:
                raise ExtractError(
                    f"server error ({exc.status_code}); retry later", retryable=True
                ) from exc
            raise ExtractError(f"API error ({exc.status_code}): {exc.message}") from exc
        except sdk.APIConnectionError as exc:
            raise ExtractError("network error reaching the API", retryable=True) from exc
        except TypeError as exc:
            # The SDK raises TypeError when the request is built without any credentials.
            if "authentication" not in str(exc):
                raise
            raise ExtractError(
                "the Claude backend found no API credentials: set ANTHROPIC_API_KEY"
            ) from exc

    def _read_parts(
        self, document: Document, parts: list[str], variables: Sequence[VariableSpec], depth: int
    ) -> list[Proposal]:
        out: list[Proposal] = []
        for i, part in enumerate(parts):
            response = self._create(self.request_params(document, part, i, len(parts), variables))
            self._count(response)
            stop = getattr(response, "stop_reason", None)
            if stop == "refusal":
                details = getattr(response, "stop_details", None)
                category = getattr(details, "category", None) if details else None
                raise ExtractionRefused(
                    f"{document.id}: the request was declined (category {category})", category
                )
            if stop == "max_tokens":
                halves = split_paragraphs(part, max(1, len(part) // 2))
                if depth >= MAX_RESPLITS or len(halves) < 2:
                    raise ExtractError(
                        f"{document.id}: the answer hit max_tokens and the part cannot be "
                        "split further; raise max_tokens"
                    )
                out += self._read_parts(document, halves, variables, depth + 1)
                continue
            out += self._parse(document, response, variables)
        return out

    def _count(self, response: Any) -> None:
        usage = getattr(response, "usage", None)
        if usage is None:
            return
        with self._lock:
            for name in USAGE_FIELDS:
                value = getattr(usage, name, None)
                if isinstance(value, int) and not isinstance(value, bool):
                    self.usage[name] += value

    def _parse(
        self, document: Document, response: Any, variables: Sequence[VariableSpec]
    ) -> list[Proposal]:
        text = next(
            (
                b.text
                for b in getattr(response, "content", [])
                if getattr(b, "type", None) == "text"
            ),
            None,
        )
        if text is None:
            raise ExtractError(f"{document.id}: the answer has no text block")
        try:
            items = json.loads(text)["proposals"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ExtractError(f"{document.id}: the answer is not the proposal schema") from exc
        specs = {v.name: v for v in variables}
        out = []
        for item in items:
            spec = specs.get(item.get("variable"))
            level: Any = item.get("level")
            if spec is not None:
                try:
                    level = level_from_text(spec, level)
                except ValueError:
                    pass  # kept as given; the extractor discards it with the reason
            out.append(
                Proposal(
                    indicator_id=f"{document.id}:{item.get('variable')}={item.get('level')}",
                    variable=str(item.get("variable")),
                    level=level,
                    date=str(item.get("date")),
                    quote=str(item.get("quote") or ""),
                    url=document.url,
                    rule=f"{self.name} backend: {item.get('rule')}",
                    confidence=str(item.get("confidence")),
                )
            )
        return out

    def propose(self, document: Document, variables: Sequence[VariableSpec]) -> list[Proposal]:
        parts = self.parts(document)
        return merge_proposals(self._read_parts(document, parts, variables, 0), document.text)
