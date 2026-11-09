"""The blind replay: date filtering per quarter, auto-accept only on the synthetic corpus,
the section 9 metrics on hand-made snapshot series, and the synthetic run end to end."""

import json
import shutil
from datetime import date
from pathlib import Path

import pytest

from wavefront.cli import main
from wavefront.evidence import validate_snapshot
from wavefront.evidence.corpora import LocalCorpus
from wavefront.evidence.extract import RESOURCE_VARIABLES, TEXT_VARIABLES, RuleBackend
from wavefront.evidence.harness_rules import DEFAULT_RULES
from wavefront.evidence.replay import (
    ReplayError,
    compare,
    parse_quarters,
    quarter_end,
    render_report,
    replay,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "evidence" / "fixtures" / "corpus_synthetic"
HINDSIGHT = ROOT / "snapshots" / "ww2" / "hindsight"
REPORT = ROOT / "reports" / "replay_ww2_synthetic.md"
QUARTERS = parse_quarters("1936Q1..1940Q4")


def test_parse_quarters():
    assert QUARTERS[0] == "1936Q1" and QUARTERS[-1] == "1940Q4" and len(QUARTERS) == 20
    assert parse_quarters("1939Q4..1940Q1") == ["1939Q4", "1940Q1"]
    assert parse_quarters("1939Q1,1939Q3") == ["1939Q1", "1939Q3"]
    for bad in ("1940Q1..1939Q4", "1939Q5", "1939Q3,1939Q1", "1939"):
        with pytest.raises(ReplayError):
            parse_quarters(bad)
    assert quarter_end("1939Q3") == date(1939, 9, 30)


def test_auto_accept_is_refused_on_a_corpus_that_is_not_synthetic(tmp_path):
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "1936-03-07_x.txt").write_text("date: 1936-03-07\n\nText.\n")
    with pytest.raises(ReplayError, match="synthetic"):
        replay(
            LocalCorpus(corpus_dir), QUARTERS[:1], tmp_path / "out", RuleBackend(), auto_accept=True
        )


def _run(out, *extra):
    report = out / "report.md"
    args = ["replay", "--corpus", str(FIXTURES), "--quarters", "1936Q1..1940Q4"]
    code = main([*args, "--out", str(out), "--report", str(report), *extra])
    assert code == 0
    return out, report


@pytest.fixture(scope="module")
def synthetic_run(tmp_path_factory):
    """The mechanics run of reports/replay_ww2_synthetic.md: harness rules off (the fixture
    corpus has one document per event, so the two-document rule would hold most flips)."""
    return _run(tmp_path_factory.mktemp("replay"), "--auto-accept", "--rules", "none")


@pytest.fixture(scope="module")
def synthetic_run_rules(tmp_path_factory):
    return _run(tmp_path_factory.mktemp("replay_rules"), "--auto-accept")


def test_each_quarter_reads_only_documents_dated_up_to_its_end(synthetic_run):
    out, _ = synthetic_run
    seen = set()
    previous_end = date(1935, 12, 31)
    for q in QUARTERS:
        data = json.loads((out / "proposals" / f"{q}.json").read_text())
        end = quarter_end(q)
        assert data["until"] == end.isoformat() and data["corpus"]["synthetic"] is True
        for d in data["documents"]:
            assert previous_end < date.fromisoformat(d["date"]) <= end
            assert d["id"] not in seen
            seen.add(d["id"])
        for rec in data["proposals"]:
            assert date.fromisoformat(rec["proposal"]["date"]) <= end
            assert rec["status"] == "accepted" and rec["decisions"][-1]["auto"] is True
        previous_end = end
    assert len(seen) == len(list(FIXTURES.glob("*.txt")))


def test_every_replay_snapshot_is_valid_and_dated_at_its_quarter_end(synthetic_run):
    out, _ = synthetic_run
    for q in QUARTERS:
        snap = json.loads((out / f"{q}.json").read_text())
        assert validate_snapshot(snap) == []
        assert snap["date"] == quarter_end(q).isoformat()
        for name in TEXT_VARIABLES:
            for ind in snap["variables"][name]["indicators"]:
                assert ind["observed"] <= snap["date"]
                assert "AUTO-ACCEPTED" in ind["rule"]


def test_synthetic_run_metrics_and_report_label(synthetic_run):
    out, report = synthetic_run
    m = compare(out, QUARTERS, HINDSIGHT)
    assert m.missing_replay == [] and m.auto_accepted
    agree, total = m.share(TEXT_VARIABLES)
    assert total == 20 * len(TEXT_VARIABLES) and agree / total >= 0.75
    assert m.share(RESOURCE_VARIABLES) == (20 * len(RESOURCE_VARIABLES),) * 2  # copied
    text = report.read_text()
    first, *_ = text.splitlines()
    assert first.startswith("SYNTHETIC RUN:")
    assert "# Replay metrics, WW2 1936Q1 to 1940Q4 (SYNTHETIC)" in text
    assert "auto-accepted (synthetic run only)" in text
    assert "- Harness rules in force: none" in text


def _series(tmp_path):
    """A replay directory holding copies of the hindsight snapshots: agreement 100%."""
    out = tmp_path / "series"
    out.mkdir()
    for q in ["1935Q4", *QUARTERS]:
        shutil.copy(HINDSIGHT / f"{q}.json", out / f"{q}.json")
    return out


def _set(out, quarter, name, level, observed=None):
    path = out / f"{quarter}.json"
    snap = json.loads(path.read_text())
    snap["variables"][name] = {
        "level": level,
        "confidence": "medium",
        "indicators": [
            {
                "id": "t",
                "value": "t",
                "source": "t",
                "observed": observed or quarter_end(quarter).isoformat(),
                "rule": "t",
            }
        ],
    }
    path.write_text(json.dumps(snap))


def _levels(name):
    return {
        q: json.loads((HINDSIGHT / f"{q}.json").read_text())["variables"][name]["level"]
        for q in ["1935Q4", *QUARTERS]
    }


def test_metrics_identical_series_agree_fully_with_zero_lags(tmp_path):
    m = compare(_series(tmp_path), QUARTERS, HINDSIGHT)
    for name in TEXT_VARIABLES:
        assert m.agreement[name][0] == m.agreement[name][1] == 20
        assert m.false_flips(name) == [] and m.missed_flips(name) == []
        assert all(x.lag_quarters == 0 and x.lag_days == 0 for x in m.matched(name))


def test_metrics_a_range_after_1936q1_starts_both_series_from_the_record(tmp_path):
    """--quarters 1937Q1..: the replayed and the documented flips both start from the
    hindsight snapshot of 1936Q4 (docs/replay_harness.md, "Replay and metrics"), so a
    replay that agrees in every quarter has no false flip, whether or not the directory
    holds a replay snapshot of 1936Q4, and whatever that snapshot reads."""
    out = _series(tmp_path)
    quarters = parse_quarters("1937Q1..1940Q4")
    (out / "1936Q4.json").unlink()
    m = compare(out, quarters, HINDSIGHT)
    for name in TEXT_VARIABLES:
        assert m.agreement[name] == (16, 16)
        assert m.false_flips(name) == [] and m.missed_flips(name) == [], name
    shutil.copy(HINDSIGHT / "1936Q4.json", out / "1936Q4.json")
    _set(out, "1936Q4", "rhineland", "demilitarized")
    m = compare(out, quarters, HINDSIGHT)
    assert m.false_flips("rhineland") == []


def test_report_target_names_the_hindsight_directory_compared_with(tmp_path):
    out = _series(tmp_path)
    m = compare(out, QUARTERS, HINDSIGHT)
    text = render_report(m, title="T", corpus={"source": "x"}, backend={"name": "b"}, command="c")
    assert "- Target: the hindsight snapshots in `snapshots/ww2/hindsight/`" in text
    text = render_report(
        compare(out, QUARTERS, out), title="T", corpus={"source": "x"}, backend={}, command="c"
    )
    assert f"- Target: the hindsight snapshots in `{out}/`" in text


def test_metrics_a_late_flip_has_a_lag_and_costs_agreement(tmp_path):
    out = _series(tmp_path)
    levels = _levels("belief_WEST")
    qs = ["1935Q4", *QUARTERS]
    i = next(k for k in range(1, len(qs)) if levels[qs[k]] != levels[qs[k - 1]])
    flip_q, before = qs[i], levels[qs[i - 1]]
    late_date = quarter_end(qs[i + 1]).isoformat()
    _set(out, flip_q, "belief_WEST", before)
    _set(out, qs[i + 1], "belief_WEST", levels[flip_q], observed=late_date)
    m = compare(out, QUARTERS, HINDSIGHT)
    assert m.agreement["belief_WEST"] == (19, 20)
    (late,) = [x for x in m.matched("belief_WEST") if x.lag_quarters]
    assert late.lag_quarters == 1 and late.lag_days > 0
    assert m.false_flips("belief_WEST") == []


def test_metrics_false_and_missed_flips(tmp_path):
    out = _series(tmp_path)
    levels = _levels("siberia")
    assert len(set(levels.values())) == 1  # siberia never changes in the record
    other = "japanese" if levels["1938Q1"] == "soviet" else "soviet"
    _set(out, "1938Q1", "siberia", other)
    m = compare(out, QUARTERS, HINDSIGHT)
    assert len(m.false_flips("siberia")) == 2  # there and back
    # Keep the treaty at its 1935Q4 level throughout: each documented flip is missed.
    first = json.loads((HINDSIGHT / "1935Q4.json").read_text())["variables"]["treaty"]["level"]
    for q in QUARTERS:
        _set(out, q, "treaty", first)
    m = compare(out, QUARTERS, HINDSIGHT)
    documented = [x for x in m.matches["treaty"] if x.documented]
    assert documented and len(m.missed_flips("treaty")) == len(documented)
    assert m.false_flips("treaty") == []


def test_metrics_only_and_missing_quarters(tmp_path, capsys):
    out = tmp_path / "empty"
    out.mkdir()
    report = tmp_path / "m.md"
    assert (
        main(
            [
                "replay",
                "--out",
                str(out),
                "--quarters",
                "1939Q1..1939Q2",
                "--metrics-only",
                "--report",
                str(report),
            ]
        )
        == 0
    )
    text = report.read_text()
    assert "not compared): 1939Q1, 1939Q2" in text and "SYNTHETIC" not in text
    assert main(["replay", "--out", str(out)]) == 2  # no corpus
    assert "--corpus" in capsys.readouterr().err


def test_render_report_labels_auto_accepted_runs_as_synthetic(tmp_path):
    m = compare(_series(tmp_path), QUARTERS, HINDSIGHT)
    m.auto_accepted = True
    text = render_report(
        m, title="T", corpus={"source": "x"}, backend={"name": "rules"}, command="c"
    )
    assert text.splitlines()[0].startswith("SYNTHETIC RUN") and "# T (SYNTHETIC)" in text


def test_committed_synthetic_report_is_labeled():
    text = REPORT.read_text(encoding="utf-8")
    assert text.splitlines()[0].startswith("SYNTHETIC RUN:")
    title = next(line for line in text.splitlines() if line.startswith("# "))
    assert "SYNTHETIC" in title.upper()


# -- proposal-level measurement (--measure-proposals) -------------------------------------


@pytest.fixture(scope="module")
def measured_run(tmp_path_factory):
    return _run(tmp_path_factory.mktemp("measured"), "--measure-proposals", "--rules", "none")


@pytest.fixture(scope="module")
def measured_run_rules(tmp_path_factory):
    return _run(tmp_path_factory.mktemp("measured_rules"), "--measure-proposals")


def test_measure_proposals_writes_no_snapshot_and_leaves_proposals_pending(measured_run):
    out, report = measured_run
    assert sorted(p.name for p in out.glob("*.json")) == []
    for q in QUARTERS:
        data = json.loads((out / "proposals" / f"{q}.json").read_text())
        assert all(r["status"] == "pending" and not r["decisions"] for r in data["proposals"])
    text = report.read_text()
    assert text.splitlines()[0].startswith("PROPOSAL-LEVEL MEASUREMENT: no proposal")
    assert "Review: none: proposal-level measurement" in text
    assert "## Proposals per variable" in text and "--measure-proposals" in text


@pytest.mark.parametrize("rules", ["off", "on"])
def test_measure_proposals_equals_accepting_every_proposal(rules, request):
    """Treating every proposal as accepted gives the metrics of a run that accepted them, with
    the harness rules off and on (auto-accept then accepts what a measurement counts)."""
    suffix = "" if rules == "off" else "_rules"
    measured_run = request.getfixturevalue(f"measured_run{suffix}")
    synthetic_run = request.getfixturevalue(f"synthetic_run{suffix}")
    measured = compare(measured_run[0], QUARTERS, HINDSIGHT, measure_proposals=True)
    accepted = compare(synthetic_run[0], QUARTERS, HINDSIGHT)
    assert measured.rules == accepted.rules == (() if rules == "off" else DEFAULT_RULES)
    assert measured.proposal_level and not measured.auto_accepted
    assert measured.agreement == accepted.agreement
    assert measured.levels == accepted.levels
    for name in TEXT_VARIABLES:
        pairs = [(m.documented, m.replayed) for m in measured.matches[name]]
        assert pairs == [(m.documented, m.replayed) for m in accepted.matches[name]]
    assert sum(sum(c.values()) for c in measured.counts.values()) == sum(
        len(json.loads(p.read_text())["proposals"])
        for p in (measured_run[0] / "proposals").glob("*.json")
    )


def test_measure_proposals_without_corpus_and_its_refusals(measured_run, tmp_path):
    out, _ = measured_run
    report = tmp_path / "again.md"
    args = ["replay", "--out", str(out), "--measure-proposals", "--report", str(report)]
    assert main(args) == 0
    text = report.read_text()
    assert "Corpus: local" in text and "Backend: rules" in text
    assert main([*args, "--metrics-only"]) == 2
    empty = tmp_path / "empty"
    empty.mkdir()
    assert main(["replay", "--out", str(empty), "--measure-proposals"]) == 2


def test_measure_proposals_prints_the_banner_of_its_mode(measured_run, tmp_path, capsys):
    """The stdout banner of a proposal-level measurement: every proposal treated as accepted,
    or, with --drop-rejected, the rejected ones left out; none for a reviewed measurement."""
    out, _ = measured_run
    args = ["replay", "--out", str(out), "--measure-proposals", "--report", str(tmp_path / "r")]
    capsys.readouterr()
    assert main(args) == 0
    lines = [x for x in capsys.readouterr().out.splitlines() if x.startswith("PROPOSAL-LEVEL")]
    assert lines == [
        "PROPOSAL-LEVEL: every proposal treated as accepted for the metrics; nothing written"
    ]
    assert main([*args, "--drop-rejected"]) == 0
    lines = [x for x in capsys.readouterr().out.splitlines() if x.startswith("PROPOSAL-LEVEL")]
    assert lines == [
        "PROPOSAL-LEVEL: rejected proposals left out, the accepted and the pending ones "
        "treated as accepted for the metrics; nothing written"
    ]
    assert (
        main(["replay", "--out", str(out), "--metrics-only", "--report", str(tmp_path / "m")]) == 0
    )
    assert "PROPOSAL-LEVEL" not in capsys.readouterr().out


def test_report_gives_the_reading_nothing_baseline(synthetic_run):
    m = compare(synthetic_run[0], QUARTERS, HINDSIGHT)
    unread, total = m.share(TEXT_VARIABLES, "unread")
    assert total == 20 * len(TEXT_VARIABLES) and 0 < unread < total
    moved_agree, moved = m.share(TEXT_VARIABLES, "moved")
    assert moved == total - unread and moved_agree <= moved


def test_committed_frus_baseline_report_is_labeled_proposal_level():
    path = ROOT / "reports" / "replay_ww2_frus.md"
    text = path.read_text(encoding="utf-8")
    assert text.splitlines()[0].startswith("PROPOSAL-LEVEL MEASUREMENT: no proposal")
    assert "Review: none: proposal-level measurement" in text
