"""The DeepSeek backend through a fake ``post``: the request, the answer's parsing, the
re-split on ``length``, refusals, the error map with retries, usage and the cache identity."""

import io
import json
import urllib.error
from datetime import date

import pytest

from wavefront.evidence.corpora import Document
from wavefront.evidence.extract import (
    DeepSeekBackend,
    ExtractError,
    ExtractionRefused,
    extract,
    make_backend,
    text_variables,
)
from wavefront.evidence.extract import deepseek_backend as ds
from wavefront.evidence.extract.claude_backend import system_prompt

VARS = text_variables()
DOC = Document(
    id="doc-1",
    date=date(1939, 3, 17),
    source="test",
    title="Birmingham",
    text="Speaking at Birmingham, the Prime Minister asked whether this was a step in the "
    "direction of an attempt to dominate the world by force.\n\nA second paragraph.",
    url="https://example.org/doc-1",
)


def _item(**kw):
    base = {
        "indicator_id": "anything",
        "variable": "belief_WEST",
        "level": "hegemonic",
        "date": "1939-03-17",
        "quote": "an attempt to dominate the world by force",
        "url": "https://made.up/url",
        "rule": "hegemonic: domination by force",
        "confidence": "high",
    }
    return base | kw


def _answer(items=(), finish="stop", content=None, usage=None):
    text = json.dumps({"proposals": list(items)}) if content is None else content
    return {
        "choices": [
            {
                "finish_reason": finish,
                "message": {"role": "assistant", "content": text, "reasoning_content": "..."},
            }
        ],
        "usage": usage
        or {
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "prompt_cache_hit_tokens": 80,
            "prompt_cache_miss_tokens": 20,
            "completion_tokens_details": {"reasoning_tokens": 15},
        },
    }


class FakePost:
    """Records every request; answers with ``reply(body)`` (an exception is raised)."""

    def __init__(self, reply):
        self.calls = []
        self.reply = reply

    def __call__(self, url, headers, body, timeout):
        payload = json.loads(body)
        self.calls.append((url, headers, payload, timeout))
        result = self.reply(payload)
        if isinstance(result, Exception):
            raise result
        return result


def _backend(reply, **kw):
    post = FakePost(reply)
    kw.setdefault("sleep", lambda s: None)
    return DeepSeekBackend(api_key="test-key", base_url="https://api.test", post=post, **kw), post


def _http_error(code, body=b"{}"):
    return urllib.error.HTTPError("https://api.test", code, "error", {}, io.BytesIO(body))


def test_request_carries_the_prompt_the_schema_and_json_mode():
    backend, post = _backend(lambda b: _answer([_item()]))
    out = backend.propose(DOC, VARS)
    assert [p.variable for p in out] == ["belief_WEST"]
    url, headers, body, _ = post.calls[0]
    assert url == "https://api.test/chat/completions"
    assert headers["Authorization"] == "Bearer test-key"
    assert body["model"] == ds.DEFAULT_DEEPSEEK_MODEL
    assert body["response_format"] == {"type": "json_object"}
    system, user = body["messages"]
    # The same instructions and threshold rules as the Claude backend, then the schema.
    assert system["content"].startswith(system_prompt(VARS))
    assert '"proposals"' in system["content"]
    assert "Document date: 1939-03-17" in user["content"] and DOC.text in user["content"]
    assert out[0].url == DOC.url and out[0].rule.startswith("deepseek backend:")


def test_model_and_json_mode_are_configurable():
    backend, post = _backend(lambda b: _answer(), model="deepseek-v4-pro", json_mode=False)
    backend.propose(DOC, VARS)
    body = post.calls[0][2]
    assert body["model"] == "deepseek-v4-pro" and "response_format" not in body


def test_a_fenced_answer_is_parsed():
    fenced = "```json\n" + json.dumps({"proposals": [_item()]}) + "\n```"
    backend, _ = _backend(lambda b: _answer(content=fenced))
    assert len(backend.propose(DOC, VARS)) == 1


def test_an_answer_outside_the_schema_is_an_error():
    backend, _ = _backend(lambda b: _answer(content='{"levels": []}'))
    with pytest.raises(ExtractError, match="not the proposal schema"):
        backend.propose(DOC, VARS)


def test_a_part_cut_off_by_length_is_split_and_read_again():
    calls = []

    def reply(body):
        calls.append(body)
        return _answer(finish="length") if len(calls) == 1 else _answer([_item()])

    backend, _ = _backend(reply)
    out = backend.propose(DOC, VARS)
    assert len(calls) == 3 and len(out) == 1  # the cut answer, then one request per half


def test_content_filter_is_a_refusal():
    backend, _ = _backend(lambda b: _answer(finish="content_filter"))
    with pytest.raises(ExtractionRefused):
        backend.propose(DOC, VARS)


@pytest.mark.parametrize(
    "code, retryable, message",
    [
        (400, False, "request rejected"),
        (401, False, "authentication failed"),
        (402, False, "insufficient balance"),
        (422, False, "request rejected"),
        (429, True, "rate limited"),
        (503, True, "server error"),
    ],
)
def test_http_errors_are_mapped_and_retryable_ones_retried(code, retryable, message):
    waits = []
    backend, post = _backend(lambda b: _http_error(code), retries=2, sleep=waits.append)
    with pytest.raises(ExtractError, match=message) as info:
        backend.propose(DOC, VARS)
    assert info.value.retryable is retryable
    assert len(post.calls) == (3 if retryable else 1)
    assert waits == ([2.0, 4.0] if retryable else [])


def test_a_retryable_failure_then_success():
    answers = iter([urllib.error.URLError("down"), _answer([_item()])])
    backend, post = _backend(lambda b: next(answers))
    assert len(backend.propose(DOC, VARS)) == 1 and len(post.calls) == 2


def test_usage_is_counted_under_the_api_names():
    backend, _ = _backend(lambda b: _answer())
    backend.propose(DOC, VARS)
    assert backend.usage == {
        "prompt_tokens": 100,
        "completion_tokens": 20,
        "prompt_cache_hit_tokens": 80,
        "prompt_cache_miss_tokens": 20,
        "reasoning_tokens": 15,
    }


def test_missing_key_says_which_variable(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    backend = DeepSeekBackend(post=FakePost(lambda b: pytest.fail("no request without a key")))
    with pytest.raises(ExtractError, match="DEEPSEEK_API_KEY"):
        backend.propose(DOC, VARS)


def test_cache_identity_names_the_model_and_differs_from_claude():
    a, _ = _backend(lambda b: _answer())
    b, _ = _backend(lambda b: _answer(), model="deepseek-v4-pro")
    ia, ib = a.cache_identity(VARS), b.cache_identity(VARS)
    assert ia["model"] == ds.DEFAULT_DEEPSEEK_MODEL and ia != ib
    assert make_backend("deepseek").name == "deepseek"
    assert make_backend("deepseek", "deepseek-v4-pro").model == "deepseek-v4-pro"


def test_proposals_go_through_the_extractor_checks():
    items = [_item(), _item(quote="Germany will conquer Europe"), _item(date="1939-09-03")]
    backend, _ = _backend(lambda b: _answer(items))

    class One:
        synthetic = False

        def iter_documents(self, until, since=None):
            yield DOC

    result = extract(One(), until=date(1939, 3, 31), backend=backend, variables=VARS)
    assert len(result.kept) == 1 and len(result.discarded) == 2


def test_default_guidance_is_the_adopted_text_and_can_be_overridden():
    from pathlib import Path

    adopted = Path(__file__).resolve().parents[2] / "data/extract/deepseek_guidance_g2.txt"
    assert ds.DEFAULT_GUIDANCE.strip() == adopted.read_text(encoding="utf-8").strip()
    backend, post = _backend(lambda b: _answer())
    backend.propose(DOC, VARS)
    assert ds.DEFAULT_GUIDANCE.strip() in post.calls[0][2]["messages"][0]["content"]
    plain, post = _backend(lambda b: _answer(), guidance="")
    plain.propose(DOC, VARS)
    assert ds.DEFAULT_GUIDANCE.strip() not in post.calls[0][2]["messages"][0]["content"]


def test_default_guidance_is_sent_for_ww2_only():
    cw = text_variables(episode="cw")
    backend, post = _backend(lambda b: _answer())
    assert backend.guidance_for(VARS) == ds.DEFAULT_GUIDANCE
    assert backend.guidance_for(cw) == ""
    explicit, _ = _backend(lambda b: _answer(), guidance="read carefully")
    assert explicit.guidance_for(cw) == "read carefully"
