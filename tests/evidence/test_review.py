"""The review step: proposals change nothing until a reviewer accepts them; replay snapshots
are rebuilt from accepted proposals only and are schema-valid with full provenance."""

import json
import shutil
from datetime import date
from pathlib import Path

import jsonschema
import pytest

from wavefront.cli import main
from wavefront.evidence import hindsight_ww2 as hw
from wavefront.evidence import validate_snapshot
from wavefront.evidence.corpora import LocalCorpus
from wavefront.evidence.extract import (
    RESOURCE_VARIABLES,
    TEXT_VARIABLES,
    RuleBackend,
    extract,
    read_proposals,
    write_proposals,
)
from wavefront.evidence.review import (
    AUTO_REVIEWER,
    ReviewError,
    decide,
    format_listing,
    label_for,
    rebuild_snapshots,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "evidence" / "fixtures" / "corpus_synthetic"
SCHEMA = json.loads((ROOT / "snapshots" / "schema.json").read_text())
HINDSIGHT = ROOT / "snapshots" / "ww2" / "hindsight"


def _extract(corpus_dir, out_dir, until, label=None, since=None, rules=()):
    """Proposals file for ``until``; the harness rules are off unless given (these tests
    check the review mechanics; tests/evidence/test_harness_rules.py checks the rules)."""
    corpus = LocalCorpus(corpus_dir)
    result = extract(corpus, until=until, since=since, backend=RuleBackend())
    path = out_dir / "proposals" / f"{label or label_for(until)}.json"
    write_proposals(
        path,
        result,
        label=label or label_for(until),
        corpus=corpus.describe(),
        backend={"name": "rules"},
        harness_rules=rules,
    )
    return path


@pytest.fixture
def real_corpus(tmp_path):
    """A copy of a few fixtures without the synthetic header: a stand-in for a real corpus."""
    out = tmp_path / "corpus"
    out.mkdir()
    for f in sorted(FIXTURES.glob("193[68]-*.txt")):
        text = f.read_text(encoding="utf-8").split("\n", 1)[1]
        (out / f.name).write_text(text, encoding="utf-8")
    return out


def test_label_for():
    assert label_for(date(1939, 3, 31)) == "1939Q1"
    assert label_for(date(1939, 3, 17)) == "1939-03-17"


def test_nothing_is_written_until_every_proposal_is_decided(real_corpus, tmp_path):
    out = tmp_path / "replay"
    path = _extract(real_corpus, out, date(1936, 12, 31))
    data = read_proposals(path)
    assert data["corpus"]["synthetic"] is False
    ids = [r["id"] for r in data["proposals"]]
    assert len(ids) >= 4 and all(r["status"] == "pending" for r in data["proposals"])
    assert rebuild_snapshots(path.parent, out) == []
    listing = format_listing(data)
    assert "SYNTHETIC" not in listing and all(i in listing for i in ids)
    assert decide(path, ids[:1], "accepted", note="checked", reviewer="historian") == []
    assert not (out / "1936Q4.json").exists()
    written = decide(path, ids[1:2], "rejected", note="misread", reviewer="historian")
    assert written == []
    written = decide(path, ids[2:], "accepted", note="checked", reviewer="historian")
    assert written == [out / "1936Q4.json"]


def test_replay_snapshot_levels_come_only_from_accepted_proposals(real_corpus, tmp_path):
    out = tmp_path / "replay"
    path = _extract(real_corpus, out, date(1936, 12, 31))
    data = read_proposals(path)
    by_var = {}
    for r in data["proposals"]:
        by_var.setdefault(r["proposal"]["variable"], r)  # the first proposal sets the level
    rejected = by_var["axis"]["id"]
    others = [r["id"] for r in data["proposals"] if r["id"] != rejected]
    decide(path, [rejected], "rejected", note="not an alignment yet", reviewer="historian")
    (snap_path,) = decide(path, others, "accepted", note="read the quote", reviewer="historian")
    snap = json.loads(snap_path.read_text())
    assert validate_snapshot(snap) == [] and hw.check_against_ontology(snap) == []
    jsonschema.validate(snap, SCHEMA)
    assert snap["date"] == "1936-12-31" and snap["model"] == hw.MODEL
    # The rejected proposal leaves its variable at the initial level, assumed.
    assert snap["variables"]["axis"] == {"level": False, "confidence": "assumed", "indicators": []}
    # An accepted proposal becomes the level, with the quote, URL and rule as its indicator.
    treaty = snap["variables"]["treaty"]
    assert treaty["level"] == "dead"
    ind = treaty["indicators"][0]
    rec = by_var["treaty"]
    assert ind["value"] == rec["proposal"]["quote"] and ind["source"] == rec["proposal"]["url"]
    assert ind["observed"] == rec["proposal"]["date"]
    assert rec["proposal"]["rule"] in ind["rule"] and "accepted by historian" in ind["rule"]
    # Resource variables are copied from the hindsight snapshot of the quarter, marked so.
    hind = json.loads((HINDSIGHT / "1936Q4.json").read_text())["variables"]
    for name in RESOURCE_VARIABLES:
        assert snap["variables"][name]["level"] == hind[name]["level"]
        assert all(
            i["rule"].startswith("copied from the hindsight snapshot 1936Q4")
            for i in snap["variables"][name]["indicators"]
        )
    # Every other text variable without an accepted proposal is assumed at its initial level.
    for name in TEXT_VARIABLES:
        entry = snap["variables"][name]
        if not entry["indicators"]:
            assert entry["confidence"] == "assumed"
            assert entry["level"] == hw.BY_NAME[name].init


def test_later_snapshots_include_earlier_accepted_evidence_and_decisions_keep_history(
    real_corpus, tmp_path
):
    out = tmp_path / "replay"
    p1 = _extract(real_corpus, out, date(1936, 12, 31))
    p2 = _extract(real_corpus, out, date(1938, 12, 31), since=date(1937, 1, 1))
    ids1 = [r["id"] for r in read_proposals(p1)["proposals"]]
    ids2 = [r["id"] for r in read_proposals(p2)["proposals"]]
    assert decide(p2, ids2, "accepted", note="ok", reviewer="h") == []  # 1936Q4 still pending
    written = decide(p1, ids1, "accepted", note="ok", reviewer="h")
    assert written == [out / "1936Q4.json", out / "1938Q4.json"]
    later = json.loads((out / "1938Q4.json").read_text())["variables"]
    assert later["treaty"]["level"] == "dead"  # from a 1936 document
    assert later["sudeten"]["level"] == "german"
    decide(p1, ids1[:1], "rejected", note="second thoughts", reviewer="h")
    rec = read_proposals(p1)["proposals"][0]
    assert [d["status"] for d in rec["decisions"]] == ["accepted", "rejected"]
    assert rec["status"] == "rejected"


def test_review_refusals(real_corpus, tmp_path):
    out = tmp_path / "replay"
    path = _extract(real_corpus, out, date(1936, 12, 31))
    with pytest.raises(ReviewError, match="note"):
        decide(path, "1936Q4-001", "accepted", note=" ", reviewer="h")
    with pytest.raises(ReviewError, match="no proposals"):
        decide(path, "1936Q4-999", "accepted", note="x", reviewer="h")
    with pytest.raises(ReviewError, match="synthetic"):
        decide(path, "1936Q4-001", "accepted", note="x", reviewer=AUTO_REVIEWER, auto=True)
    with pytest.raises(ReviewError, match="reserved"):
        decide(path, "1936Q4-001", "accepted", note="x", reviewer=AUTO_REVIEWER)
    with pytest.raises(ReviewError, match="status"):
        decide(path, "1936Q4-001", "pending", note="x", reviewer="h")
    loose = tmp_path / "loose.json"
    shutil.copy(path, loose)
    with pytest.raises(ReviewError, match="--snapshots"):
        decide(loose, "1936Q4-001", "accepted", note="x", reviewer="h")


def test_auto_accept_is_allowed_on_the_synthetic_corpus_and_says_so(tmp_path):
    out = tmp_path / "replay"
    path = _extract(FIXTURES, out, date(1936, 3, 31))
    ids = [r["id"] for r in read_proposals(path)["proposals"]]
    (snap_path,) = decide(
        path, ids, "accepted", note="synthetic", reviewer=AUTO_REVIEWER, auto=True
    )
    snap = json.loads(snap_path.read_text())
    inds = [
        i
        for v in snap["variables"].values()
        for i in v["indicators"]
        if not i["rule"].startswith("copied from")
    ]
    assert inds and all("AUTO-ACCEPTED in a synthetic run" in i["rule"] for i in inds)
    assert all(i["source"].startswith("synthetic:") for i in inds)


def test_cli_extract_and_review(real_corpus, tmp_path, capsys):
    out = tmp_path / "replay"
    proposals = out / "proposals" / "1936Q4.json"
    assert (
        main(
            [
                "extract",
                str(real_corpus),
                "--until",
                "1936-12-31",
                "--out",
                str(proposals),
                "--rules",
                "none",
            ]
        )
        == 0
    )
    printed = capsys.readouterr().out
    assert "proposals written" in printed and "SYNTHETIC" not in printed
    assert main(["review", str(proposals)]) == 0
    listing = capsys.readouterr().out
    assert "1936Q4-001  [pending]" in listing
    ids = [r["id"] for r in read_proposals(proposals)["proposals"]]
    assert main(["review", str(proposals), "--accept", ids[0]]) == 2
    assert "note" in capsys.readouterr().err
    assert (
        main(["review", str(proposals), "--reject", ids[0], "--note", "misread", "--reviewer", "h"])
        == 0
    )
    assert "still pending" in capsys.readouterr().out
    assert (
        main(
            [
                "review",
                str(proposals),
                "--accept",
                ",".join(ids[1:]),
                "--note",
                "ok",
                "--reviewer",
                "h",
            ]
        )
        == 0
    )
    assert "replay snapshot written" in capsys.readouterr().out
    assert (out / "1936Q4.json").exists()
    assert main(["review", str(tmp_path / "missing.json")]) == 2
    assert (
        main(
            ["extract", str(tmp_path / "nowhere"), "--until", "1936-12-31", "--out", str(proposals)]
        )
        == 2
    )
    assert main(
        [
            "extract",
            str(real_corpus),
            "--until",
            "1936-12-31",
            "--out",
            str(proposals),
            "--backend",
            "claude",
        ]
    ) in (1, 2)  # no SDK or no credentials
