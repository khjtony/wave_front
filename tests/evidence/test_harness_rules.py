"""The harness rules of the replay and review layer (decision 9 of 2026-10-15): the
two-document rule and the no-retrospective rule, each switchable, acting on the structural
variables only (not on the belief and commitment variables), on the fixture corpus
``corpus_rules`` (one case per rule), in measurement, review and auto-accept, and with the
Claude backend through a fake client (cache, resume, usage and the dry run included)."""

import json
import re
from datetime import date
from pathlib import Path

import pytest

from tests.evidence.test_extract import FakeClient, _fake_sdk, _response
from wavefront.cli import main
from wavefront.evidence.corpora import LocalCorpus
from wavefront.evidence.extract import TEXT_VARIABLES, ClaudeBackend, RuleBackend, read_proposals
from wavefront.evidence.harness_rules import (
    BLOCKED,
    CORROBORATING,
    DEFAULT_RULES,
    HELD,
    MONOTONE,
    NO_RETROSPECTIVE,
    OK,
    ONCE,
    READINGS,
    RETROSPECTIVE,
    TWO_DOCUMENT,
    V0_MONOTONE,
    RulesError,
    gate_records,
    parse_rules,
)
from wavefront.evidence.replay import (
    AUTO_RETRO_NOTE,
    ReplayError,
    compare,
    measured_snapshots,
    parse_quarters,
    replay,
)
from wavefront.evidence.review import (
    ReviewError,
    decide,
    file_gates,
    format_listing,
    rebuild_snapshots,
)

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "tests" / "evidence" / "fixtures" / "corpus_rules"
HINDSIGHT = ROOT / "snapshots" / "ww2" / "hindsight"
QUARTERS = parse_quarters("1936Q1..1940Q1")
SDK = _fake_sdk()

# The cases of corpus_rules (one proposal per document and variable with the rule backend,
# except where the fake Claude backend is needed):
#   china_war   true    one document (1937-07-08)                    two-document: held
#   austria     annexed two documents (1938-03-12, 1938-04-10)       two-document: flips 1938Q2
#   poland      partitioned twice (1939-09-17, 1939-09-28), then german (1940-02-26, a
#               recollection): back on a monotone variable           no-retrospective: blocked
#   rhineland   remilitarized (1936-03-07, one document: not monotone, not a flag, so not under
#               two-document), then read as demilitarized by the fake Claude backend in a
#               recollection (1937-03-08): back to its initial level  no-retrospective: flagged
#   belief_GER  uncertain (1939-05-23), then will_not_fight (1939-08-22): a belief variable,
#               outside both rules, so the move back is shown and counted as made


def _levels(snaps, name):
    return {q: s["variables"][name]["level"] for q, s in snaps.items()}


@pytest.fixture(scope="module")
def proposals(tmp_path_factory):
    """The replay's proposals for the case corpus, pending (no review)."""
    out = tmp_path_factory.mktemp("cases")
    replay(LocalCorpus(CASES), QUARTERS, out, RuleBackend())
    return out


def test_parse_rules():
    assert parse_rules(None) == DEFAULT_RULES == (TWO_DOCUMENT, NO_RETROSPECTIVE)
    assert parse_rules("no-retrospective, two-document") == DEFAULT_RULES
    assert parse_rules("two-document") == (TWO_DOCUMENT,)
    assert parse_rules("none") == parse_rules("") == ()
    with pytest.raises(RulesError, match="unknown"):
        parse_rules("two-documents")


def test_monotone_variables_are_those_the_model_declares_monotone():
    from models.ww2.v0 import model

    cm = model.compile()
    declared = {v.name for v in cm.variables if v.monotone}
    assert declared & set(TEXT_VARIABLES) == V0_MONOTONE
    assert READINGS == {"belief_WEST", "belief_GER", "commit_WEST", "commit_US"}
    assert MONOTONE == V0_MONOTONE - READINGS and not READINGS & ONCE
    assert {"axis", "austria", "poland", "war_west_ger", "italy_estranged", "oil_GER"} <= ONCE
    assert not {"rhineland", "treaty"} & ONCE


def _rec(i, doc, var, level, day, status="pending"):
    return {
        "id": f"r{i}",
        "document": doc,
        "proposal": {"variable": var, "level": level, "date": day, "quote": f"q{i}"},
        "status": status,
        "decisions": [],
    }


def test_two_document_rule_counts_documents_not_proposals():
    end = date(1938, 12, 31)
    same_doc = [
        _rec(1, "d1", "austria", "annexed", "1938-03-12"),
        _rec(2, "d1", "austria", "annexed", "1938-03-12"),
    ]
    g = gate_records(same_doc, end, DEFAULT_RULES, measure=True)
    assert [x.status for x in g.gates] == [HELD, HELD] and g.in_force == []
    two = [*same_doc, _rec(3, "d2", "austria", "annexed", "1938-04-10")]
    g = gate_records(two, end, DEFAULT_RULES, measure=True)
    assert [x.status for x in g.gates] == [CORROBORATING, CORROBORATING, OK]
    assert [r["id"] for r in g.in_force] == ["r3"]  # the second document carries the flip
    # In review a rejected proposal is not a proposing document.
    two[2]["status"] = "rejected"
    g = gate_records(two, end, DEFAULT_RULES, measure=False)
    assert [x.status for x in g.gates[:2]] == [HELD, HELD]
    # Variables outside the rule flip on one document.
    g = gate_records(
        [_rec(4, "d1", "treaty", "dead", "1936-03-19")], end, DEFAULT_RULES, measure=True
    )
    assert g.gates[0].status == OK and len(g.in_force) == 1
    # The belief and commitment variables are outside both rules: a single document flips
    # them, and a move back (here on belief_WEST, which v0 declares monotone) is applied.
    beliefs = [
        _rec(5, "d1", "belief_WEST", "uncertain", "1936-01-03"),
        _rec(6, "d2", "belief_WEST", "limited", "1936-02-03"),
        _rec(7, "d3", "commit_WEST", "at_war", "1936-03-03"),
    ]
    g = gate_records(beliefs, end, DEFAULT_RULES, measure=True)
    assert [x.status for x in g.gates] == [OK, OK, OK] and len(g.in_force) == 3


def test_measurement_with_both_rules_on_the_case_corpus(proposals):
    snaps = measured_snapshots(proposals / "proposals", QUARTERS, HINDSIGHT)
    assert set(_levels(snaps, "china_war").values()) == {False}  # one document: held
    austria = _levels(snaps, "austria")
    assert austria["1938Q1"] == "independent" and austria["1938Q2"] == "annexed"
    ind = snaps["1938Q2"]["variables"]["austria"]["indicators"][0]
    assert ind["observed"] == "1938-04-10"  # dated by the second document
    belief = _levels(snaps, "belief_GER")  # outside the rules: the move back counts
    assert belief["1939Q2"] == "uncertain" and belief["1939Q3"] == "will_not_fight"
    assert _levels(snaps, "rhineland")["1936Q1"] == "remilitarized"  # not under two-document
    poland = _levels(snaps, "poland")
    assert poland["1939Q3"] == poland["1940Q1"] == "partitioned"  # the recollection is blocked


def test_measurement_with_the_rules_off_and_one_at_a_time(proposals):
    off = measured_snapshots(proposals / "proposals", QUARTERS, HINDSIGHT, rules=())
    assert _levels(off, "china_war")["1937Q3"] is True
    assert _levels(off, "austria")["1938Q1"] == "annexed"
    assert _levels(off, "belief_GER")["1939Q3"] == "will_not_fight"
    assert _levels(off, "poland")["1940Q1"] == "german"
    two = measured_snapshots(proposals / "proposals", QUARTERS, HINDSIGHT, rules=[TWO_DOCUMENT])
    assert _levels(two, "austria")["1938Q1"] == "independent"
    # no-retrospective is off, but the move back to german is a flip of a monotone variable
    # with one document, so the two-document rule holds it.
    assert _levels(two, "poland")["1940Q1"] == "partitioned"
    assert _levels(two, "belief_GER")["1939Q3"] == "will_not_fight"
    back = measured_snapshots(
        proposals / "proposals", QUARTERS, HINDSIGHT, rules=[NO_RETROSPECTIVE]
    )
    assert _levels(back, "austria")["1938Q1"] == "annexed"  # two-document is off
    assert _levels(back, "poland")["1940Q1"] == "partitioned"
    assert _levels(back, "belief_GER")["1939Q3"] == "will_not_fight"


def test_reports_state_the_rules_in_force(proposals, tmp_path):
    for rules, expected in [
        (None, "- Harness rules in force: `two-document`, `no-retrospective`"),
        ("two-document", "- Harness rules in force: `two-document` ("),
        ("none", "- Harness rules in force: none"),
    ]:
        report = tmp_path / "m.md"
        args = ["replay", "--out", str(proposals), "--quarters", "1936Q1..1940Q1"]
        args += ["--measure-proposals", "--report", str(report)]
        assert main(args + (["--rules", rules] if rules else [])) == 0
        text = report.read_text()
        assert expected in text
        assert ("## What the harness rules did" in text) == (rules != "none")
        if rules is not None:
            assert f"--rules {rules}" in text
    m = compare(proposals, QUARTERS, HINDSIGHT, measure_proposals=True)
    assert m.gates["china_war"][HELD] == 1 and m.gates["poland"][BLOCKED] == 1
    assert m.gates["belief_GER"] == {OK: 2} and m.gates["austria"][CORROBORATING] == 1
    assert main(["replay", "--out", str(proposals), "--metrics-only", "--rules", "none"]) == 2


def test_proposals_files_record_the_rules_and_disagreeing_files_are_refused(proposals, tmp_path):
    data = read_proposals(proposals / "proposals" / "1938Q1.json")
    assert data["harness_rules"] == list(DEFAULT_RULES)
    out = tmp_path / "mixed"
    replay(LocalCorpus(CASES), QUARTERS[:1], out, RuleBackend(), rules=())
    replay(LocalCorpus(CASES), QUARTERS[1:3], out, RuleBackend())
    with pytest.raises(ReviewError, match="disagree"):
        rebuild_snapshots(out / "proposals", out)


def _ids(path, var):
    return [r["id"] for r in read_proposals(path)["proposals"] if r["proposal"]["variable"] == var]


def _accept_all(path):
    ids = [r["id"] for r in read_proposals(path)["proposals"]]
    return decide(path, ids, "accepted", note="ok", reviewer="h") if ids else []


def test_review_hides_held_and_blocked_proposals(tmp_path, capsys):
    out = tmp_path / "review"
    replay(LocalCorpus(CASES), QUARTERS, out, RuleBackend())
    files = {q: out / "proposals" / f"{q}.json" for q in QUARTERS}
    _accept_all(files["1936Q1"])  # the Rhineland: a flip on one document, outside the rule
    # 1937Q3: the one china_war proposal is held; it cannot be accepted, and it does not keep
    # the quarter's snapshot from being written.
    (china,) = _ids(files["1937Q3"], "china_war")
    assert file_gates(files["1937Q3"])[china].status == HELD
    with pytest.raises(ReviewError, match="two-document"):
        decide(files["1937Q3"], [china], "accepted", note="x", reviewer="h")
    assert out / "1937Q3.json" in rebuild_snapshots(out / "proposals", out)
    assert main(["review", str(files["1937Q3"])]) == 0
    listing = capsys.readouterr().out
    assert "not for review under the harness rules (1)" in listing and "held" in listing
    assert "harness rules: two-document, no-retrospective" in listing
    # 1938Q1 holds the first Anschluss document; 1938Q2 shows the flip with its second.
    (first,) = _ids(files["1938Q1"], "austria")
    (second,) = _ids(files["1938Q2"], "austria")
    assert file_gates(files["1938Q1"])[first].status == HELD
    assert file_gates(files["1938Q2"])[second].status == OK
    decide(files["1938Q2"], [second], "accepted", note="the plebiscite", reviewer="h")
    # 1939Q2 to 1939Q3: belief_GER is outside the rules, so the Obersalzberg address, back to
    # its initial level, is an ordinary proposal for review.
    _accept_all(files["1939Q2"])
    (obersalzberg,) = _ids(files["1939Q3"], "belief_GER")
    assert file_gates(files["1939Q3"])[obersalzberg].status == OK
    _accept_all(files["1939Q3"])
    snap = json.loads((out / "1939Q3.json").read_text())
    assert snap["variables"]["belief_GER"]["level"] == "will_not_fight"
    assert snap["variables"]["poland"]["level"] == "partitioned"
    # 1940Q1: the recollection of the German attack is blocked on the monotone poland.
    (recollection,) = _ids(files["1940Q1"], "poland")
    assert file_gates(files["1940Q1"])[recollection].status == BLOCKED
    with pytest.raises(ReviewError, match="monotone"):
        decide(files["1940Q1"], [recollection], "accepted", note="x", reviewer="h")
    # Replaying a quarter that has reviewer's decisions would reset them: refused.
    with pytest.raises(ReplayError, match="reviewer's decision"):
        replay(LocalCorpus(CASES), QUARTERS, out, RuleBackend())
    replay(LocalCorpus(CASES), ["1940Q1"], out, RuleBackend())  # an undecided quarter is fine


def test_review_flags_a_retrospective_reading_and_only_a_reviewer_applies_it(tmp_path):
    out = tmp_path / "retro"
    quarters = parse_quarters("1936Q1..1937Q1")
    backend = ClaudeBackend(client=FakeClient(_fake_reply), sdk=SDK)
    replay(LocalCorpus(CASES), quarters, out, backend)
    files = {q: out / "proposals" / f"{q}.json" for q in quarters}
    _accept_all(files["1936Q1"])
    (zone,) = _ids(files["1937Q1"], "rhineland")
    gate = file_gates(files["1937Q1"])[zone]
    assert gate.status == RETROSPECTIVE and gate.acceptable
    listing = format_listing(read_proposals(files["1937Q1"]), file_gates(files["1937Q1"]))
    assert re.search(rf"{zone}  \[pending\]  retrospective\?", listing)
    # Not counted by a measurement; it awaits a decision, so no 1937Q1 snapshot yet.
    measured = measured_snapshots(out / "proposals", quarters, HINDSIGHT)
    assert measured["1937Q1"]["variables"]["rhineland"]["level"] == "remilitarized"
    assert out / "1937Q1.json" not in rebuild_snapshots(out / "proposals", out)
    decide(files["1937Q1"], [zone], "accepted", note="read as the present", reviewer="h")
    snap = json.loads((out / "1937Q1.json").read_text())
    assert snap["variables"]["rhineland"]["level"] == "demilitarized"  # the reviewer decided


def test_auto_accept_follows_the_rules_and_says_so(tmp_path):
    out = tmp_path / "auto"
    report = tmp_path / "auto.md"
    args = ["replay", "--corpus", str(CASES), "--quarters", "1936Q1..1940Q1", "--out", str(out)]
    assert main([*args, "--auto-accept", "--report", str(report)]) == 0
    assert all((out / f"{q}.json").exists() for q in QUARTERS)
    by_var = {}
    for q in QUARTERS:
        for r in read_proposals(out / "proposals" / f"{q}.json")["proposals"]:
            by_var.setdefault(r["proposal"]["variable"], []).append(r)
    assert [r["status"] for r in by_var["china_war"]] == ["pending"]  # held, not decided
    assert [r["status"] for r in by_var["belief_GER"]] == ["accepted", "accepted"]
    assert [r["status"] for r in by_var["poland"]] == ["accepted", "accepted", "pending"]
    last = json.loads((out / "1940Q1.json").read_text())["variables"]
    assert last["poland"]["level"] == "partitioned"
    assert last["belief_GER"]["level"] == "will_not_fight"
    assert "- Harness rules in force: `two-document`, `no-retrospective`" in report.read_text()
    # A retrospective? reading is never auto-accepted: auto-accept rejects it with a note.
    claude = tmp_path / "auto_claude"
    backend = ClaudeBackend(client=FakeClient(_fake_reply), sdk=SDK)
    replay(LocalCorpus(CASES), QUARTERS[:5], claude, backend, auto_accept=True)
    (zone,) = read_proposals(claude / "proposals" / "1937Q1.json")["proposals"]
    assert zone["status"] == "rejected" and zone["decisions"][-1]["note"] == AUTO_RETRO_NOTE
    snap = json.loads((claude / "1937Q1.json").read_text())["variables"]
    assert snap["rhineland"]["level"] == "remilitarized"


# -- the Claude backend through a fake client --------------------------------------------

_FAKE_READINGS = {  # document id: (variable, level) the fake model reads
    "rules-1936-03-07-rhineland": ("rhineland", "remilitarized"),
    "rules-1937-03-08-zone-recalled": ("rhineland", "demilitarized"),
    "rules-1937-07-08-marco-polo": ("china_war", "true"),
    "rules-1938-03-12-anschluss": ("austria", "annexed"),
    "rules-1938-04-10-plebiscite": ("austria", "annexed"),
    "rules-1939-05-23-conference": ("belief_GER", "uncertain"),
    "rules-1939-08-22-obersalzberg": ("belief_GER", "will_not_fight"),
    "rules-1939-09-17-soviet-entry": ("poland", "partitioned"),
    "rules-1939-09-29-boundary-treaty": ("poland", "partitioned"),
    "rules-1940-02-26-recollection": ("poland", "german"),
}


def _fake_reply(params, fail=()):
    content = params["messages"][0]["content"]
    doc_id = re.search(r"Document id: (\S+)", content).group(1)
    day = re.search(r"Document date: (\S+)", content).group(1)
    if doc_id in fail:
        return SDK.APIConnectionError("network down")
    text = content.split("<document>\n")[1].split("\n</document>")[0]
    variable, level = _FAKE_READINGS[doc_id]
    item = {
        "indicator_id": "x",
        "variable": variable,
        "level": level,
        "date": day,
        "quote": text.split(". ")[0],
        "url": "x",
        "rule": f"{variable} {level}",
        "confidence": "medium",
    }
    response = _response([item])
    response.usage = type("U", (), {"input_tokens": 1000, "output_tokens": 50})()
    return response


def test_claude_backend_end_to_end_under_the_rules_with_cache_resume_and_usage(tmp_path):
    out = tmp_path / "claude"
    corpus = LocalCorpus(CASES)
    flaky = FakeClient(lambda p: _fake_reply(p, fail={"rules-1939-08-22-obersalzberg"}))
    with pytest.raises(ReplayError, match="run the same command again to resume"):
        replay(corpus, QUARTERS, out, ClaudeBackend(client=flaky, sdk=SDK), workers=3)
    # Every document read before the stop is cached, the failed one is not: 1936Q1 to 1939Q2
    # and the two other documents of 1939Q3.
    assert len(list((out / "cache" / "claude").glob("*.json"))) == 8
    # Resume: the same command, with the quarters already written skipped and cached
    # documents not sent again.
    client = FakeClient(_fake_reply)
    done = sorted(p.stem for p in (out / "proposals").glob("*.json"))
    rest = [q for q in QUARTERS if q not in done]
    replay(corpus, rest, out, ClaudeBackend(client=client, sdk=SDK), workers=3)
    sent = {
        re.search(r"Document id: (\S+)", c[1]["messages"][0]["content"]).group(1)
        for c in client.calls
    }
    assert sent == {"rules-1939-08-22-obersalzberg", "rules-1940-02-26-recollection"}
    q3 = read_proposals(out / "proposals" / "1939Q3.json")
    assert q3["backend"]["name"] == "claude" and q3["backend"]["model"] == ClaudeBackend().model
    assert q3["backend"]["usage"] == {"input_tokens": 1000, "output_tokens": 50}
    assert q3["backend"]["cache"] == {"hits": 2, "misses": 1}
    assert q3["harness_rules"] == list(DEFAULT_RULES)
    # The rules act on the Claude backend's proposals exactly as on the rule backend's.
    snaps = measured_snapshots(out / "proposals", QUARTERS, HINDSIGHT)
    assert set(_levels(snaps, "china_war").values()) == {False}
    assert _levels(snaps, "austria")["1938Q1"] == "independent"
    assert _levels(snaps, "austria")["1938Q2"] == "annexed"
    assert _levels(snaps, "belief_GER")["1939Q3"] == "will_not_fight"
    assert _levels(snaps, "rhineland")["1937Q1"] == "remilitarized"  # retrospective?: not counted
    assert _levels(snaps, "poland")["1940Q1"] == "partitioned"
    # Running the whole range again into the same OUT reads every document from the cache.
    silent = FakeClient(lambda p: pytest.fail("a cached document was sent again"))
    replay(corpus, QUARTERS, out, ClaudeBackend(client=silent, sdk=SDK))
    assert silent.calls == []
    assert measured_snapshots(out / "proposals", QUARTERS, HINDSIGHT) == snaps


def test_dry_run_counts_what_a_run_would_send_and_writes_nothing(tmp_path, capsys):
    out = tmp_path / "dry"
    args = ["replay", "--corpus", str(CASES), "--quarters", "1936Q1..1940Q1", "--out", str(out)]
    assert main([*args, "--backend", "claude", "--dry-run"]) == 0
    printed = capsys.readouterr().out
    assert printed.startswith("DRY RUN") and not out.exists()
    assert "total: 10 documents to read, 0 of them cached, 10 requests" in printed
    assert "input tokens, estimated at 4 characters a token" in printed
    # After a run of 1936Q1 to 1938Q2, their five documents are cached.
    replay(
        LocalCorpus(CASES),
        QUARTERS[:10],
        out,
        ClaudeBackend(client=FakeClient(_fake_reply), sdk=SDK),
    )
    assert main([*args, "--backend", "claude", "--dry-run"]) == 0
    printed = capsys.readouterr().out
    assert "total: 10 documents to read, 5 of them cached, 5 requests" in printed
    assert main(["replay", "--out", str(out), "--dry-run"]) == 2  # needs --corpus


def test_cli_extract_records_the_rules_caches_and_reads_in_parallel(tmp_path, capsys):
    base = ["extract", str(CASES), "--until", "1940-03-31"]
    one, many = tmp_path / "one.json", tmp_path / "many.json"
    assert main([*base, "--out", str(one), "--rules", "two-document"]) == 0
    cache = tmp_path / "cache"
    assert main([*base, "--out", str(many), "--workers", "4", "--cache", str(cache)]) == 0
    a, b = read_proposals(one), read_proposals(many)
    assert a["harness_rules"] == ["two-document"] and b["harness_rules"] == list(DEFAULT_RULES)
    assert [r["proposal"] for r in a["proposals"]] == [r["proposal"] for r in b["proposals"]]
    assert len(list(cache.glob("*.json"))) == 10
    assert main([*base, "--out", str(one), "--rules", "three-documents"]) == 2
    assert "unknown harness rule" in capsys.readouterr().err


def test_the_cache_key_follows_the_model_and_the_prompt():
    from wavefront.evidence.extract import text_variables
    from wavefront.evidence.extract.cache import cache_key

    doc = next(iter(LocalCorpus(CASES).iter_documents(until=date(1940, 12, 31))))
    variables = text_variables()
    key = cache_key(ClaudeBackend(), doc, variables)
    assert key == cache_key(ClaudeBackend(), doc, variables)
    assert key != cache_key(ClaudeBackend("another-model"), doc, variables)
    assert key != cache_key(ClaudeBackend(effort="low"), doc, variables)
    assert key != cache_key(ClaudeBackend(), doc, variables[:-1])
