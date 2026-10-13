"""The extractor: the fixed proposal schema, paragraph splitting, the rule backend on the
fixtures, the checks every proposal passes, and the Claude backend through a fake client."""

import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import jsonschema
import pytest

from wavefront.evidence import hindsight_ww2 as hw
from wavefront.evidence.corpora import Document, LocalCorpus
from wavefront.evidence.extract import (
    PROPOSAL_FIELDS,
    RESOURCE_VARIABLES,
    TEXT_VARIABLES,
    ClaudeBackend,
    ExtractError,
    ExtractionRefused,
    Proposal,
    RuleBackend,
    check_proposal,
    extract,
    merge_proposals,
    proposal_list_schema,
    split_paragraphs,
    text_variables,
)
from wavefront.evidence.extract import claude_backend as cb
from wavefront.evidence.extract.rules import RULES, observation_date
from wavefront.evidence.extract.schema import ontology_rule_text, quote_in_text

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "evidence" / "fixtures" / "corpus_synthetic"
VARS = text_variables()
BY_NAME = {v.name: v for v in VARS}
DOC = Document(
    id="doc-1",
    date=date(1939, 3, 17),
    source="test",
    title="Birmingham",
    text="Speaking at Birmingham, the Prime Minister asked whether this was a step in the "
    "direction of an attempt to dominate the world by force.\n\nA second paragraph.",
    url="https://example.org/doc-1",
)


def _p(**kw):
    base = dict(
        indicator_id="doc-1:x",
        variable="belief_WEST",
        level="hegemonic",
        date="1939-03-17",
        quote="an attempt to dominate the world by force",
        url=DOC.url,
        rule="test rule",
        confidence="medium",
    )
    return Proposal(**(base | kw))


# -- the schema ------------------------------------------------------------------------------


def test_text_and_resource_variables_partition_the_ontology_variables():
    names = {v.name for v in hw.VARIABLES}
    assert set(TEXT_VARIABLES) | set(RESOURCE_VARIABLES) == names
    assert not set(TEXT_VARIABLES) & set(RESOURCE_VARIABLES)
    rules = ontology_rule_text()
    for v in VARS:
        assert v.levels == hw.BY_NAME[v.name].levels
        assert v.rule_text == rules[v.name] and len(v.rule_text) > 20, v.name


def test_proposal_list_schema_is_a_valid_json_schema_with_the_fixed_fields():
    schema = proposal_list_schema(VARS)
    jsonschema.Draft202012Validator.check_schema(schema)
    item = schema["properties"]["proposals"]["items"]
    assert tuple(item["required"]) == PROPOSAL_FIELDS
    assert item["additionalProperties"] is False
    example = {"proposals": [_p(level="hegemonic").to_json()]}
    jsonschema.validate(example, schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"proposals": [{**example["proposals"][0], "extra": 1}]}, schema)


def test_check_proposal_rejects_what_a_document_cannot_support():
    assert check_proposal(_p(), BY_NAME, DOC.date, DOC.text) == []
    assert check_proposal(_p(level="total"), BY_NAME, DOC.date, DOC.text)
    assert check_proposal(_p(variable="arms_GER", level="high"), BY_NAME, DOC.date, DOC.text)
    later = check_proposal(_p(date="1939-03-18"), BY_NAME, DOC.date, DOC.text)
    assert any("after the document" in r for r in later)
    assert check_proposal(_p(quote="dominate Europe by force"), BY_NAME, DOC.date, DOC.text)
    assert check_proposal(_p(confidence="assumed"), BY_NAME, DOC.date, DOC.text)
    assert check_proposal(_p(variable="axis", level="true"), BY_NAME, DOC.date, DOC.text)
    assert (
        check_proposal(
            _p(variable="axis", level=True, quote="Birmingham"), BY_NAME, DOC.date, DOC.text
        )
        == []
    )


def test_quote_matching_tolerates_whitespace_case_curly_quotes_and_ellipsis():
    text = "He said: “We shall\n fight on.” Then he sat down."
    assert quote_in_text('we shall fight on."', text)
    assert quote_in_text("He said ... sat down", text)
    assert not quote_in_text("sat down ... He said", text)
    assert not quote_in_text("...", text)


# -- splitting -------------------------------------------------------------------------------


def test_split_paragraphs_never_drops_text():
    paragraphs = [f"Paragraph {i}. " + "Words here. " * (i * 7) for i in range(1, 30)]
    text = "\n\n".join(paragraphs)
    for limit in (40, 200, 1000, 10**6):
        chunks = split_paragraphs(text, limit)
        assert all(len(c) <= limit for c in chunks)
        assert " ".join(" ".join(chunks).split()) == " ".join(text.split())
    assert split_paragraphs("a" * 25, 10) == ["a" * 10, "a" * 10, "a" * 5]
    with pytest.raises(ValueError):
        split_paragraphs("x", 0)


def test_merge_proposals_keeps_one_per_variable_level_and_date():
    a, b = _p(), _p(quote="Birmingham")
    c = _p(level="uncertain")
    merged = merge_proposals([a, b, c])
    assert [m.level for m in merged] == ["hegemonic", "uncertain"]
    assert merged[0].quote == a.quote and "1 other part" in merged[0].rule
    # With the text, an unfounded quote neither hides nor is hidden by a sound one.
    fake = _p(quote="Germany will rule the world")
    kept = merge_proposals([fake, a], DOC.text)
    assert [k.quote for k in kept] == [fake.quote, a.quote]


# -- the rule backend -------------------------------------------------------------------------


def test_rule_backend_proposals_on_the_fixtures_all_pass_the_checks():
    corpus = LocalCorpus(FIXTURES)
    backend = RuleBackend()
    total = 0
    for doc in corpus.iter_documents(until=date(1940, 12, 31)):
        proposals = backend.propose(doc, VARS)
        assert len({p.variable for p in proposals}) == len(proposals)  # one per variable
        for p in proposals:
            assert check_proposal(p, BY_NAME, doc.date, doc.text) == [], (doc.id, p)
            assert p.url == doc.url and p.indicator_id.startswith(doc.id + ":")
            assert p.rule.startswith("rule ") and "ontology" in p.rule
        total += len(proposals)
    assert total >= 40


def test_rules_cover_only_text_variables_with_their_levels():
    for rule in RULES:
        assert rule.variable in TEXT_VARIABLES
        assert rule.level in BY_NAME[rule.variable].levels
    assert not any(r.variable in RESOURCE_VARIABLES for r in RULES)
    # Asking for fewer variables gives fewer proposals.
    doc = next(LocalCorpus(FIXTURES).iter_documents(until=date(1936, 3, 7)))
    only = RuleBackend().propose(doc, [BY_NAME["treaty"]])
    assert [p.variable for p in only] == ["treaty"]


def test_observation_date_rule():
    d = date(1939, 3, 18)
    assert observation_date("Speaking on 17 March 1939 at Birmingham", d) == date(1939, 3, 17)
    assert observation_date("on March 17, 1939", d) == date(1939, 3, 17)
    assert observation_date("the Act of 31 August 1935", d) == d  # outside the 31-day window
    assert observation_date("on 19 March 1939", d) == d  # after the document: never
    assert observation_date("The Prime Minister spoke yesterday", d) == date(1939, 3, 17)


# -- the extractor ---------------------------------------------------------------------------


class _Backend:
    name = "fake"

    def __init__(self, fail_on=None):
        self.seen = []
        self.fail_on = fail_on

    def propose(self, document, variables):
        self.seen.append(document)
        if document.id == self.fail_on:
            raise ExtractError("boom", retryable=True)
        return [
            Proposal(
                f"{document.id}:ok",
                "treaty",
                "dead",
                document.date.isoformat(),
                document.text.split(".")[0],
                document.url,
                "r",
                "high",
            ),
            Proposal(
                f"{document.id}:bad",
                "treaty",
                "dead",
                "1999-01-01",
                "not in the text at all",
                document.url,
                "r",
                "high",
            ),
        ]


def test_extract_reads_only_documents_up_to_the_cut_off_and_records_discards_and_errors():
    corpus = LocalCorpus(FIXTURES)
    backend = _Backend(fail_on="syn-1936-03-09-eden-statement")
    result = extract(
        corpus,
        until=date(1936, 10, 18),
        backend=backend,
        variables=VARS,
        skip_ids=["syn-1936-03-07-rhineland"],
    )
    assert all(d.date <= date(1936, 10, 18) for d in backend.seen)
    assert "syn-1936-03-07-rhineland" not in [d.id for d in backend.seen]
    assert [e["document"] for e in result.errors] == ["syn-1936-03-09-eden-statement"]
    assert result.errors[0]["retryable"] is True
    assert len(result.kept) == len(backend.seen) - 1
    assert len(result.discarded) == len(backend.seen) - 1
    reasons = result.discarded[0]["reasons"]
    assert any("after the document" in r for r in reasons)
    assert any("quote" in r for r in reasons)
    with pytest.raises(ExtractError):
        extract(
            corpus,
            until=date(1936, 10, 18),
            backend=_Backend(fail_on="syn-1936-03-09-eden-statement"),
            stop_on_error=True,
        )


# -- the Claude backend, through a fake client -------------------------------------------------


class _StatusError(Exception):
    def __init__(self, message="error", status_code=400, headers=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = SimpleNamespace(headers=headers or {})


def _fake_sdk():
    sdk = SimpleNamespace()
    sdk.APIStatusError = _StatusError
    for name, code in [
        ("BadRequestError", 400),
        ("AuthenticationError", 401),
        ("PermissionDeniedError", 403),
        ("NotFoundError", 404),
        ("RateLimitError", 429),
        ("InternalServerError", 500),
    ]:
        cls = type(name, (_StatusError,), {})
        cls.code = code
        setattr(sdk, name, cls)
    sdk.APIConnectionError = type("APIConnectionError", (Exception,), {})
    sdk.Anthropic = lambda: pytest.fail("the backend must use the client it was given")
    return sdk


def _response(proposals=(), stop="end_turn", category=None):
    content = [
        SimpleNamespace(type="thinking", thinking=""),
        SimpleNamespace(type="text", text=json.dumps({"proposals": list(proposals)})),
    ]
    details = SimpleNamespace(category=category) if category else None
    return SimpleNamespace(stop_reason=stop, stop_details=details, content=content)


class FakeClient:
    """Records every request; answers with ``reply(params)``."""

    def __init__(self, reply):
        self.calls = []
        self.reply = reply
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))
        self.messages = SimpleNamespace(create=self._plain)

    def _create(self, **params):
        self.calls.append(("beta", params))
        result = self.reply(params)
        if isinstance(result, Exception):
            raise result
        return result

    def _plain(self, **params):
        self.calls.append(("plain", params))
        return self.reply(params)


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


def test_claude_backend_module_imports_without_the_sdk():
    code = (
        "import sys; import wavefront.evidence.extract.claude_backend, wavefront.cli; "
        "assert 'anthropic' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], check=True, cwd=ROOT)


def test_claude_backend_request_follows_the_reference():
    client = FakeClient(lambda params: _response([_item()]))
    backend = ClaudeBackend(client=client, sdk=_fake_sdk())
    proposals = backend.propose(DOC, VARS)
    ((kind, params),) = client.calls
    assert kind == "beta"
    assert params["model"] == cb.DEFAULT_MODEL
    assert "thinking" not in params  # adaptive thinking by omission
    assert params["betas"] == ["server-side-fallback-2026-07-01"]
    assert params["fallbacks"] == "default"
    assert params["max_tokens"] == cb.DEFAULT_MAX_TOKENS
    fmt = params["output_config"]["format"]
    assert fmt == {"type": "json_schema", "schema": proposal_list_schema(VARS)}
    assert params["output_config"]["effort"] == "high"
    system = params["system"][0]
    assert system["cache_control"] == {"type": "ephemeral"}
    assert (
        "blind replay" in system["text"] and BY_NAME["belief_WEST"].rule_text[:60] in system["text"]
    )
    user = params["messages"][0]
    assert (
        user["role"] == "user" and DOC.text in user["content"] and "1939-03-17" in user["content"]
    )
    (p,) = proposals
    assert p.url == DOC.url  # never the model's URL
    assert p.indicator_id == "doc-1:belief_WEST=hegemonic"
    assert p.rule.startswith("claude backend: ")
    assert check_proposal(p, BY_NAME, DOC.date, DOC.text) == []


def test_claude_backend_model_is_configurable_and_fallbacks_can_be_turned_off():
    client = FakeClient(
        lambda params: _response([_item(variable="axis", level="true", quote="Birmingham")])
    )
    backend = ClaudeBackend("another-model", client=client, sdk=_fake_sdk(), fallbacks=False)
    (p,) = backend.propose(DOC, VARS)
    ((kind, params),) = client.calls
    assert kind == "plain" and params["model"] == "another-model"
    assert "betas" not in params and "fallbacks" not in params
    assert p.level is True  # "true" converted to the flag's level


def test_claude_backend_splits_a_long_document_and_reads_every_part():
    paragraphs = [f"Paragraph {i} " + "text " * 50 for i in range(12)]
    doc = Document("long", date(1939, 3, 17), "t", "t", "\n\n".join(paragraphs), "u")
    client = FakeClient(lambda params: _response([]))
    backend = ClaudeBackend(client=client, sdk=_fake_sdk(), max_chars=700)
    assert backend.propose(doc, VARS) == []
    sent = [
        c[1]["messages"][0]["content"].split("<document>\n")[1].split("\n</document>")[0]
        for c in client.calls
    ]
    assert len(sent) > 1 and all(len(s) <= 700 for s in sent)
    assert " ".join(" ".join(sent).split()) == " ".join(doc.text.split())
    assert f"part 1 of {len(sent)}" in client.calls[0][1]["messages"][0]["content"]


def test_claude_backend_resplits_a_part_whose_answer_hits_max_tokens():
    doc = Document("d", date(1939, 3, 17), "t", "t", "First half.\n\nSecond half.", "u")

    def reply(params):
        text = params["messages"][0]["content"]
        if "First half." in text and "Second half." in text:
            return _response(stop="max_tokens")
        return _response([])

    client = FakeClient(reply)
    ClaudeBackend(client=client, sdk=_fake_sdk()).propose(doc, VARS)
    assert len(client.calls) == 3
    stubborn = FakeClient(lambda params: _response(stop="max_tokens"))
    with pytest.raises(ExtractError, match="max_tokens"):
        ClaudeBackend(client=stubborn, sdk=_fake_sdk()).propose(doc, VARS)


def test_claude_backend_refusal_is_raised_with_its_category():
    client = FakeClient(lambda params: _response(stop="refusal", category="cyber"))
    with pytest.raises(ExtractionRefused) as info:
        ClaudeBackend(client=client, sdk=_fake_sdk()).propose(DOC, VARS)
    assert info.value.category == "cyber" and info.value.retryable is False


@pytest.mark.parametrize(
    "error_name, kwargs, retryable, message",
    [
        ("BadRequestError", {}, False, "rejected"),
        ("AuthenticationError", {}, False, "authentication"),
        ("PermissionDeniedError", {}, False, "permission"),
        ("NotFoundError", {}, False, "not found"),
        ("RateLimitError", {"headers": {"retry-after": "7"}}, True, "retry after 7s"),
        ("InternalServerError", {"status_code": 529}, True, r"server error \(529\)"),
        ("APIConnectionError", None, True, "network"),
    ],
)
def test_claude_backend_error_chain(error_name, kwargs, retryable, message):
    sdk = _fake_sdk()
    cls = getattr(sdk, error_name)
    error = cls("network down") if kwargs is None else cls("bad", **kwargs)
    client = FakeClient(lambda params: error)
    with pytest.raises(ExtractError, match=message) as info:
        ClaudeBackend(client=client, sdk=sdk).propose(DOC, VARS)
    assert info.value.retryable is retryable


def test_claude_backend_rejects_an_answer_outside_the_schema():
    bad = SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text="{}")])
    with pytest.raises(ExtractError, match="schema"):
        ClaudeBackend(client=FakeClient(lambda p: bad), sdk=_fake_sdk()).propose(DOC, VARS)


def test_claude_backend_without_the_sdk_says_how_to_install_it(monkeypatch):
    monkeypatch.setitem(sys.modules, "anthropic", None)
    with pytest.raises(ExtractError, match=r"\[extract\]"):
        ClaudeBackend().propose(DOC, VARS)


def test_claude_backend_proposals_go_through_the_extractor_checks():
    # A fabricated quote and a future date are discarded by the extractor, with reasons.
    items = [_item(), _item(quote="Germany will conquer Europe"), _item(date="1939-09-03")]
    backend = ClaudeBackend(client=FakeClient(lambda p: _response(items)), sdk=_fake_sdk())

    class One:
        synthetic = False

        def iter_documents(self, until, since=None):
            yield DOC

    result = extract(One(), until=date(1939, 3, 31), backend=backend, variables=VARS)
    assert len(result.kept) == 1 and len(result.discarded) == 2


def test_pyproject_declares_the_extract_extra():
    text = (ROOT / "pyproject.toml").read_text()
    assert 'extract = ["anthropic"]' in text
