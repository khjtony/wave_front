"""A DeepSeek backend for the extractor, through DeepSeek's OpenAI-compatible chat API.

No SDK is needed: requests go over HTTPS with the standard library (``urllib``), and tests
pass a fake ``post`` callable instead. The key is read from ``DEEPSEEK_API_KEY`` when the first
request is made; the base URL from ``DEEPSEEK_BASE_URL`` (default ``https://api.deepseek.com``).

How a document is read, as in :mod:`.claude_backend` wherever the two APIs allow:

* The same instructions and threshold rules (:func:`~.claude_backend.system_prompt`), followed
  by a paragraph giving the answer's JSON schema (:func:`~.schema.proposal_list_schema`): the
  chat API has a JSON mode (``response_format = {"type": "json_object"}``) but does not enforce
  a schema, so the schema is stated in the prompt and the extractor's checks discard any
  proposal outside it, with the reason.
* The document is split at paragraph breaks into parts of at most ``max_chars`` characters
  (:func:`~.backend.split_paragraphs`), one request per part, the proposals merged
  (:func:`~.backend.merge_proposals`); a part whose answer stops on ``length`` is split in two
  and read again, so neither a document nor an answer is cut short silently.
* ``finish_reason == "content_filter"`` raises :class:`~.claude_backend.ExtractionRefused`.
  The answer's ``content`` is parsed as JSON (a Markdown code fence around it is tolerated);
  the reasoning text of a reasoning model (``reasoning_content``) is not read.
* ``finish_reason == "insufficient_system_resource"`` (the provider interrupted the answer)
  is a retryable :class:`~.backend.ExtractError`, not a schema failure.
* HTTP errors are mapped to :class:`~.backend.ExtractError`: 400 and 422 (a bad request),
  401 (authentication), 402 (insufficient balance), 429 (rate limit) and 5xx (server) and
  network failures (``urllib`` and socket errors, timeouts, and ``http.client.HTTPException``
  such as a body cut short), the last three ``retryable``; a body that is not UTF-8 or not
  JSON is a non-retryable one. Every failure is an ``ExtractError``, so the extractor records
  it against its document instead of ending the run. There is no SDK to retry them, so a
  retryable failure is retried here ``retries`` times with a doubling wait before it is
  raised; the replay resumes from the cache when run again.

Every response's ``usage`` is added to :attr:`DeepSeekBackend.usage` under the API's own
names (``prompt_tokens``, ``completion_tokens``, ``prompt_cache_hit_tokens``,
``prompt_cache_miss_tokens``, ``reasoning_tokens``), which the replay records per quarter.
DeepSeek caches repeated prompt prefixes on its side without a marker, so the shared system
prompt is billed at the cache-hit price after the first requests.
"""

from __future__ import annotations

import hashlib
import http.client
import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from collections.abc import Callable, Sequence
from typing import Any

from ..corpora.base import Document
from .backend import ExtractError, merge_proposals, split_paragraphs
from .claude_backend import ExtractionRefused, system_prompt
from .schema import Proposal, VariableSpec, level_from_text, proposal_list_schema

__all__ = [
    "DEFAULT_BASE_URL",
    "DEFAULT_DEEPSEEK_MODEL",
    "DEFAULT_GUIDANCE",
    "DeepSeekBackend",
    "deepseek_system_prompt",
]

DEFAULT_DEEPSEEK_MODEL = "deepseek-flash"
DEFAULT_BASE_URL = "https://api.deepseek.com"
#: The guidance adopted on the owner's decision of 2026-10-24 (data/extract/
#: deepseek_guidance_g2.txt; reports/replay_ww2_frus_deepseek/README.md).
DEFAULT_GUIDANCE = (
    "Additional instructions for this reader:\n"
    "- Propose a level when the passage reports a fact that meets the variable's "
    "threshold rule: an event, a decision, a measure in force, or an explicit statement "
    "of the state of affairs. Such a fact counts even when the document is about "
    "something else and even when the level is unchanged (for example, sanctions reported"
    " as being applied to Italy; troops reported as sent into the zone; neutrality "
    "legislation reported as in force).\n"
    '- A bare mention is not such a fact: a document that only names "the demilitarized '
    "zone\", refers to Austria's independence as a topic, or says there was no agreement "
    "does not establish a level unless it reports the fact that meets the threshold rule.\n"
    "- Read the level from what the passage states, not from a chain of inference: a "
    "phrase about restored sovereignty is not a report of troops in the zone, and a "
    "protest is not the end of a treaty.\n"
    "- Beliefs (belief_* variables) are read from what a government or its responsible "
    "minister is reported to think about another government's aims or intentions, "
    "including a reported policy of seeking a settlement with it. A description of "
    "another government's methods or a commentator's analysis is not a government's "
    "belief.\n"
    "- Confidence: high when the passage states the fact outright, medium when the "
    "threshold judgment is needed, low when the report is second-hand or partial. Low-"
    "confidence proposals are welcome: the reviewer decides.\n"
)
DEFAULT_MAX_TOKENS = 16000
DEFAULT_MAX_CHARS = 120_000
DEFAULT_TIMEOUT = 600.0
DEFAULT_RETRIES = 3
MAX_RESPLITS = 4
USAGE_FIELDS = (
    "prompt_tokens",
    "completion_tokens",
    "prompt_cache_hit_tokens",
    "prompt_cache_miss_tokens",
)

#: (url, headers, body, timeout) -> the parsed JSON answer; raises like ``urlopen``
Post = Callable[[str, dict[str, str], bytes, float], dict[str, Any]]

_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)


def deepseek_system_prompt(variables: Sequence[VariableSpec], guidance: str = "") -> str:
    """The Claude backend's instructions and threshold rules, ``guidance`` (further
    instructions for this backend, if any), then the answer's schema."""
    schema = json.dumps(proposal_list_schema(variables), indent=1, sort_keys=True)
    extra = f"\n{guidance.strip()}\n" if guidance.strip() else ""
    return (
        f"{system_prompt(variables)}{extra}\n"
        "Answer with one JSON object and nothing else, of the form "
        '{"proposals": [...]}, valid against this JSON schema (an empty list when the '
        f"document shows no level):\n{schema}\n"
    )


def _urlopen_post(url: str, headers: dict[str, str], body: bytes, timeout: float) -> Any:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _check_interrupted(response: dict[str, Any]) -> None:
    """Raise a retryable error when the provider stopped the answer for lack of resources
    (``finish_reason == "insufficient_system_resource"``): its content is cut short and is
    neither the model's answer nor a schema failure."""
    try:
        finish = response["choices"][0].get("finish_reason")
    except (KeyError, IndexError, TypeError, AttributeError):
        return  # no choice: reported by the caller
    if finish == "insufficient_system_resource":
        raise ExtractError(
            "the API interrupted the answer (insufficient_system_resource); retry later",
            retryable=True,
        )


class DeepSeekBackend:
    """Proposes levels with a DeepSeek model in JSON mode (see the module docstring)."""

    name = "deepseek"

    def __init__(
        self,
        model: str = DEFAULT_DEEPSEEK_MODEL,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        post: Post | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        max_chars: int = DEFAULT_MAX_CHARS,
        json_mode: bool = True,
        effort: str | None = None,
        guidance: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        backoff: float = 2.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.model = model
        self.base_url = (
            base_url or os.environ.get("DEEPSEEK_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.max_tokens = max_tokens
        self.max_chars = max_chars
        self.json_mode = json_mode
        self.effort = effort
        self.guidance = guidance
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self._api_key = api_key
        self._post = post or _urlopen_post
        self._sleep = sleep
        self.requests = 0
        #: tokens reported by the responses so far (:data:`USAGE_FIELDS` and reasoning_tokens)
        self.usage: Counter[str] = Counter()
        self._lock = threading.Lock()

    def guidance_for(self, variables: Sequence[VariableSpec]) -> str:
        """The guidance sent with ``variables``: the one given, else :data:`DEFAULT_GUIDANCE`
        for the WW2 episode (it was tuned there) and none for any other episode."""
        if self.guidance is not None:
            return self.guidance
        episodes = {getattr(v, "episode", "ww2") for v in variables}
        return DEFAULT_GUIDANCE if episodes <= {"ww2"} else ""

    def cache_identity(self, variables: Sequence[VariableSpec]) -> dict[str, Any]:
        """What an answer depends on besides the document (for :mod:`.cache`)."""
        return {
            "base_url": self.base_url,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "max_chars": self.max_chars,
            "json_mode": self.json_mode,
            "effort": self.effort,
            "system": hashlib.sha256(
                deepseek_system_prompt(variables, self.guidance_for(variables)).encode("utf-8")
            ).hexdigest(),
        }

    def parts(self, document: Document) -> list[str]:
        """The parts the document is read in (one request each, before any re-split)."""
        return split_paragraphs(document.text, self.max_chars)

    @property
    def api_key(self) -> str:
        if self._api_key is None:
            key = os.environ.get("DEEPSEEK_API_KEY")
            if not key:
                raise ExtractError("the DeepSeek backend needs DEEPSEEK_API_KEY in the environment")
            self._api_key = key
        return self._api_key

    # -- requests -------------------------------------------------------------------------

    def request_body(
        self,
        document: Document,
        part: str,
        index: int,
        total: int,
        variables: Sequence[VariableSpec],
    ) -> dict[str, Any]:
        """The JSON body of one ``/chat/completions`` request."""
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
        body: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [
                {
                    "role": "system",
                    "content": deepseek_system_prompt(variables, self.guidance_for(variables)),
                },
                {"role": "user", "content": user},
            ],
            "stream": False,
        }
        if self.json_mode:
            body["response_format"] = {"type": "json_object"}
        if self.effort:
            body["reasoning_effort"] = self.effort
        return body

    def _send(self, body: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = json.dumps(body).encode("utf-8")
        with self._lock:
            self.requests += 1
        try:
            return self._post(url, headers, data, self.timeout)
        except urllib.error.HTTPError as exc:
            status = exc.code
            try:
                detail = exc.read().decode("utf-8", "replace")[:300]
            except Exception:  # the body is a courtesy; the status decides
                detail = ""
            if status in (400, 422):
                raise ExtractError(f"request rejected ({status}): {detail}") from exc
            if status == 401:
                raise ExtractError("authentication failed: check DEEPSEEK_API_KEY") from exc
            if status == 402:
                raise ExtractError("insufficient balance on the DeepSeek account") from exc
            if status == 429:
                raise ExtractError("rate limited", retryable=True) from exc
            if status >= 500:
                raise ExtractError(f"server error ({status}); retry later", retryable=True) from exc
            raise ExtractError(f"API error ({status}): {detail}") from exc
        except (
            urllib.error.URLError,
            TimeoutError,
            ConnectionError,
            http.client.HTTPException,
        ) as exc:
            # HTTPException: a response cut short or malformed (IncompleteRead, BadStatusLine)
            raise ExtractError("network error reaching the API", retryable=True) from exc
        except UnicodeDecodeError as exc:
            raise ExtractError("the API answered with something other than UTF-8") from exc
        except json.JSONDecodeError as exc:
            raise ExtractError("the API answered with something other than JSON") from exc

    def _create(self, body: dict[str, Any]) -> dict[str, Any]:
        wait = self.backoff
        for attempt in range(self.retries + 1):
            try:
                response = self._send(body)
                self._count(response)
                _check_interrupted(response)
                return response
            except ExtractError as exc:
                if not exc.retryable or attempt == self.retries:
                    raise
                self._sleep(wait)
                wait *= 2
        raise AssertionError("unreachable")

    def _count(self, response: dict[str, Any]) -> None:
        usage = response.get("usage")
        if not isinstance(usage, dict):
            return
        with self._lock:
            for name in USAGE_FIELDS:
                value = usage.get(name)
                if isinstance(value, int) and not isinstance(value, bool):
                    self.usage[name] += value
            details = usage.get("completion_tokens_details")
            if isinstance(details, dict):
                value = details.get("reasoning_tokens")
                if isinstance(value, int) and not isinstance(value, bool):
                    self.usage["reasoning_tokens"] += value

    def _read_parts(
        self, document: Document, parts: list[str], variables: Sequence[VariableSpec], depth: int
    ) -> list[Proposal]:
        out: list[Proposal] = []
        for i, part in enumerate(parts):
            response = self._create(self.request_body(document, part, i, len(parts), variables))
            try:
                choice = response["choices"][0]
            except (KeyError, IndexError, TypeError) as exc:
                raise ExtractError(f"{document.id}: the answer has no choice") from exc
            finish = choice.get("finish_reason")
            if finish == "content_filter":
                raise ExtractionRefused(
                    f"{document.id}: the request was declined (content filter)", "content_filter"
                )
            if finish == "length":
                halves = split_paragraphs(part, max(1, len(part) // 2))
                if depth >= MAX_RESPLITS or len(halves) < 2:
                    raise ExtractError(
                        f"{document.id}: the answer hit max_tokens and the part cannot be "
                        "split further; raise max_tokens"
                    )
                out += self._read_parts(document, halves, variables, depth + 1)
                continue
            out += self._parse(document, choice, variables)
        return out

    def _parse(
        self, document: Document, choice: dict[str, Any], variables: Sequence[VariableSpec]
    ) -> list[Proposal]:
        message = choice.get("message") or {}
        text = message.get("content")
        if not isinstance(text, str) or not text.strip():
            raise ExtractError(f"{document.id}: the answer has no content")
        fenced = _FENCE.match(text)
        if fenced:
            text = fenced.group(1)
        try:
            items = json.loads(text)["proposals"]
            if not isinstance(items, list):
                raise TypeError("proposals is not a list")
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ExtractError(f"{document.id}: the answer is not the proposal schema") from exc
        specs = {v.name: v for v in variables}
        out = []
        for item in items:
            if not isinstance(item, dict):
                continue  # not a proposal at all; nothing to check or discard
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
