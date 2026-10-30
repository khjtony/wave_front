"""The Cold War episode of the replay harness: its variables and prompt as the extractor sees
them, the WW2 prompt left byte-identical, annual periods, and a synthetic Cold War replay end to
end with a fake backend (auto-accept, review, measurement, metrics and the CLI)."""

import copy
import hashlib
import json
from datetime import date
from pathlib import Path

import pytest

from models.cw import v1 as cw_model
from models.cw.snapshots_v1 import REPLAY_YEARS
from wavefront.cli import main
from wavefront.evidence import validate_snapshot
from wavefront.evidence.corpora import LocalCorpus
from wavefront.evidence.episodes import CW, WW2, EpisodeError, get_episode
from wavefront.evidence.extract import (
    TEXT_VARIABLES,
    ClaudeBackend,
    Proposal,
    proposal_list_schema,
    read_proposals,
    text_variables,
)
from wavefront.evidence.extract.claude_backend import BELIEF_PROMPT, system_prompt
from wavefront.evidence.extract.deepseek_backend import deepseek_system_prompt
from wavefront.evidence.extract.schema import ontology_rule_text
from wavefront.evidence.harness_rules import DEFAULT_RULES, OK, gate_records
from wavefront.evidence.replay import ReplayError, compare, plan, render_report, replay
from wavefront.evidence.replay_cw import YearMetrics, contemporaneous
from wavefront.evidence.review import ReviewError, decide, label_for

ROOT = Path(__file__).resolve().parents[2]
YEARS = CW.parse_periods("1957..1962")

# Computed before the Cold War episode was added; a replay with the Claude backend caches its
# answers under these (cache_identity), so they must not move.
WW2_SYSTEM_SHA256 = "254e93e4b228b4fcac692008f5ddcb24bebe2d93d4f29789fac44ab914ace2a9"
WW2_SCHEMA_SHA256 = "8223efeb4858f020808ec81bce59668f95dd22160bf85991453327378919753a"
WW2_VARIABLES_SHA256 = "5b34850584c577749beeb392b7ad5b687b84b38e30ecbc79b3d9f2c2a2cf5537"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# -- WW2 unchanged --------------------------------------------------------------------------


def test_the_ww2_system_prompt_schema_and_variables_are_byte_identical():
    variables = text_variables()
    assert _sha(system_prompt(variables)) == WW2_SYSTEM_SHA256
    assert text_variables(episode="ww2") == variables
    assert _sha(system_prompt(text_variables(episode="ww2"))) == WW2_SYSTEM_SHA256
    schema = json.dumps(proposal_list_schema(variables), sort_keys=True)
    assert _sha(schema) == WW2_SCHEMA_SHA256
    table = repr([(s.name, s.kind, s.levels, s.init, s.section, s.rule_text) for s in variables])
    assert _sha(table) == WW2_VARIABLES_SHA256
    assert [v.name for v in variables] == list(TEXT_VARIABLES) == list(WW2.text_variables)
    assert {v.episode for v in variables} == {"ww2"}


# -- the Cold War variables and prompt ------------------------------------------------------


def test_cw_variables_match_the_model_and_the_ontology():
    declared = {d.name: d for d in cw_model.model.variables}
    rules = ontology_rule_text(CW.ontology)
    specs = text_variables(episode="cw")
    assert [s.name for s in specs] == [
        "belief_force_USA",
        "belief_USA_USSR",
        "belief_USSR_USA",
    ]
    for spec in specs:
        decl = declared[spec.name]
        assert list(spec.levels) == list(decl.levels), spec.name
        assert spec.levels.index(spec.init) == decl.init, spec.name
        assert spec.kind == "level" and spec.episode == "cw"
        assert spec.rule_text.startswith(rules[spec.name])
    force = specs[0]
    # the count scale of the owner's decision 7g, the bands of its hindsight truth count_USSR
    assert force.levels == ("none", "under_200", "under_1000", "over_1000")
    assert force.levels == tuple(declared["count_USSR"].levels)
    assert CW.truth_of("belief_force_USA") == "count_USSR" and CW.scales == ()
    assert CW.model == "cw_v1" and CW.hindsight == ROOT / "snapshots" / "cw_v1" / "hindsight"
    for band in ("**none**", "**under_200**: 1 to 199", "**under_1000**: 200 to 999"):
        assert band in force.rule_text
    assert "**over_1000**: 1,000 or more" in force.rule_text
    # no appended scale of another variable, and nothing of the survivability scale
    for gone in ("survivable", "overkill", "nuke_USA", "nuke_USSR", "thresholds of", "Monotone"):
        assert gone not in force.rule_text


def test_cw_prompt_wording_and_no_hindsight_in_it():
    prompt = system_prompt(text_variables(episode="cw"))
    assert "the Cold War between the United States and the Soviet Union, 1947 to 1991" in prompt
    assert "European politics" not in prompt and "1936" not in prompt
    assert "initial level (1 January 1947): none" in prompt
    assert BELIEF_PROMPT in prompt
    for name in CW.text_variables:
        assert f"\n## {name}\n" in prompt
    # the ontology's dated indicators (the record, read with hindsight) stay out of the prompt
    for leak in (
        "NIE 11-10-57",
        "NIE 11-56",
        "NIE 11-8",
        "11-8/1-61",
        "bomber gap",
        "missile gap",
        "Norris",
        "count_USSR",
        "Novikov",
        "RYAN",
        "NSC-68",
        "Gaither",
        "visible 19",
        "events.csv",
    ):
        assert leak not in prompt, leak
    assert deepseek_system_prompt(text_variables(episode="cw")).startswith(prompt)
    with pytest.raises(ValueError, match="several episodes"):
        system_prompt([*text_variables(episode="cw"), *text_variables(["treaty"])])


def test_cw_cache_identity_differs_from_ww2():
    backend = ClaudeBackend(client=object())
    ww2 = backend.cache_identity(text_variables())
    cw = backend.cache_identity(text_variables(episode="cw"))
    assert ww2["system"] != cw["system"] and ww2["schema"] != cw["schema"]


# -- periods --------------------------------------------------------------------------------


def test_cw_periods_are_years_read_to_the_31_december_before():
    assert YEARS == ["1957", "1958", "1959", "1960", "1961", "1962"]
    assert CW.parse_periods("1958,1983") == ["1958", "1983"]
    for bad in ("1962..1957", "1958Q1", "1983,1958"):
        with pytest.raises(EpisodeError):
            CW.parse_periods(bad)
    assert CW.cutoff("1958") == date(1957, 12, 31)
    assert CW.snapshot_date("1958") == date(1958, 1, 1)
    assert CW.label_for(date(1957, 12, 31)) == "1958"
    assert label_for(date(1957, 12, 31), "cw") == "1958"
    assert label_for(date(1957, 6, 30), "cw") == "1957-06-30"
    assert label_for(date(1939, 3, 31)) == "1939Q1"
    assert WW2.cutoff("1939Q1") == date(1939, 3, 31)
    assert get_episode(None) is WW2
    with pytest.raises(EpisodeError):
        get_episode("1914")


def test_contemporaneous_series_follows_the_manual_replay():
    """The events.csv fallback gives what the manual replay snapshots carry, in their years."""
    years = [str(y) for y in REPLAY_YEARS]
    from_files = contemporaneous(years)
    from_events = contemporaneous(years, manual_dir=ROOT / "no-such-dir")
    for name in CW.text_variables:
        for y in years:
            assert from_files[name][y][0] == from_events[name][y][0], (name, y)
    assert from_files["belief_force_USA"]["1958"][0] == "under_1000"
    assert from_files["belief_force_USA"]["1962"][0] == "under_1000"
    assert from_files["belief_force_USA"]["1983"][0] == "over_1000"
    assert from_files["belief_USSR_USA"]["1983"][0] == "first_strike_intent"


def test_harness_rules_act_on_no_cw_variable():
    def rec(n, level, day):
        p = Proposal(f"d{n}:x", "belief_force_USA", level, day, "q", "u", "r", "high").to_json()
        return {"id": f"p{n}", "document": f"d{n}", "proposal": p, "status": "pending"}

    records = [rec(1, "under_1000", "1957-12-10"), rec(2, "under_200", "1961-09-21")]
    g = gate_records(records, date(1961, 12, 31), DEFAULT_RULES, measure=True, episode="cw")
    assert [x.status for x in g.gates] == [OK, OK]
    assert len(g.in_force) == 2


# -- a synthetic Cold War replay, end to end ------------------------------------------------

DOCS = {
    "1957-12-10_estimate": (
        "The Soviet ICBM force will be able to threaten SAC bases by 1959.",
        ("belief_force_USA", "under_1000"),
    ),
    "1959-11-03_estimate": (
        "We continue to estimate a Soviet ICBM force able to threaten SAC.",
        ("belief_force_USA", "under_1000"),
    ),
    "1961-09-21_estimate": (
        "The Soviets have only 10 to 25 ICBM launchers, vulnerable to attack.",
        ("belief_force_USA", "under_200"),
    ),
}


def _corpus(root: Path) -> LocalCorpus:
    root.mkdir(parents=True, exist_ok=True)
    for name, (text, _p) in DOCS.items():
        day = name[:10]
        (root / f"{name}.txt").write_text(
            "SYNTHETIC FIXTURE: written for pipeline tests, not a source\n"
            f"id: syn-{name}\ndate: {day}\nsource: synthetic fixture corpus (not a source)\n"
            f"title: {name}\nurl: synthetic:cw/{name}\n\n{text}\n",
            encoding="utf-8",
        )
    return LocalCorpus(root)


class FakeBackend:
    """Proposes the level written into each synthetic document, quoting its sentence."""

    name = "fake"

    def __init__(self):
        self.seen_variables = None

    def propose(self, document, variables):
        self.seen_variables = [v.name for v in variables]
        key = document.id.removeprefix("syn-")
        text, (variable, level) = DOCS[key]
        return [
            Proposal(
                f"{document.id}:{variable}",
                variable,
                level,
                document.date.isoformat(),
                text,
                document.url,
                f"{variable}: the estimate's planning case",
                "high",
            )
        ]


@pytest.fixture(scope="module")
def cw_run(tmp_path_factory):
    base = tmp_path_factory.mktemp("cw")
    corpus = _corpus(base / "corpus")
    out = base / "replay"
    backend = FakeBackend()
    runs = replay(corpus, YEARS, out, backend, auto_accept=True, cache=False, episode="cw")
    return corpus, out, backend, runs


def test_cw_replay_reads_by_year_and_writes_cw_snapshots(cw_run):
    _corpus_, out, backend, runs = cw_run
    assert backend.seen_variables == list(CW.text_variables)
    assert [r.quarter for r in runs] == YEARS
    # 1958 reads the estimate of 10 Dec 1957; 1962 the one of 21 Sep 1961
    assert [r.read for r in runs] == [0, 1, 0, 1, 0, 1]
    data = read_proposals(out / "proposals" / "1958.json")
    assert data["episode"] == "cw" and data["until"] == "1957-12-31"
    hindsight_1958 = json.loads((CW.hindsight / "1958.json").read_text())
    expected = {"1957": "none", "1958": "under_1000", "1960": "under_1000", "1962": "under_200"}
    for year, level in expected.items():
        snap = json.loads((out / f"{year}.json").read_text())
        assert validate_snapshot(snap) == []
        assert snap["date"] == f"{year}-01-01" and snap["model"] == "cw_v1"
        assert snap["variables"]["belief_force_USA"]["level"] == level
        assert snap["variables"]["belief_USSR_USA"]["confidence"] == "assumed"
        assert snap["variables"]["nuke_USA"]["confidence"] == "assumed"
        assert (
            "not read in the blind replay"
            in (snap["variables"]["nuke_USA"]["indicators"][0]["rule"])
        )
    snap = json.loads((out / "1958.json").read_text())
    assert snap["builtins"] == hindsight_1958["builtins"]
    for name in ("nuke_USSR", "count_USSR"):
        assert snap["variables"][name]["level"] == hindsight_1958["variables"][name]["level"]
        assert snap["variables"][name]["confidence"] == "assumed"
    assert "AUTO-ACCEPTED" in snap["variables"]["belief_force_USA"]["indicators"][0]["rule"]


def test_cw_metrics_and_report(cw_run):
    _corpus_, out, _backend, _runs = cw_run
    m = compare(out, YEARS, episode="cw")
    assert isinstance(m, YearMetrics) and m.auto_accepted
    assert m.replay["belief_force_USA"] == {
        "1957": "none",
        "1958": "under_1000",
        "1959": "under_1000",
        "1960": "under_1000",
        "1961": "under_1000",
        "1962": "under_200",
    }
    # the hindsight count_USSR: 1 to 199 vehicles in being from the end of 1956 to 1961
    assert all(m.hindsight["belief_force_USA"][y] == "under_200" for y in YEARS)
    assert [m.exceeds(y) for y in YEARS] == [False, True, True, True, True, False]
    # 1957: none against NIE 11-56's under_1000; 1962: under_200 against NIE 11-8/1-61's
    assert m.agreement("belief_force_USA", "contemporaneous") == (4, 6)
    assert m.agreement("belief_USA_USSR", "hindsight") == (0, 0)
    flips = m.matches["belief_force_USA"]
    # the record's flip to under_1000 is NIE 11-56's (visible 1957), answered a year late; the
    # replayed flip to under_200 in 1962 has no documented counterpart (the record stays)
    assert [(d and d.year, r and r.year) for d, r in flips] == [
        ("1957", "1958"),
        (None, "1962"),
    ]
    text = render_report(
        m,
        title="Replay metrics, Cold War 1957 to 1962",
        corpus={"source": "local", "synthetic": True},
        backend={"name": "fake"},
        command="test",
    )
    assert text.startswith("SYNTHETIC RUN") and "1947 to 1991" in text
    assert "## C6:" in text and "exceeds the hindsight force in 4 of them" in text
    assert "## C7:" not in text


def test_cw_measurement_and_cli(cw_run, tmp_path, capsys):
    corpus, out, _backend, _runs = cw_run
    m = compare(out, YEARS, episode="cw", measure_proposals=True)
    assert m.proposal_level and m.replay["belief_force_USA"]["1961"] == "under_1000"
    assert sum(sum(c.values()) for c in m.counts.values()) == 3
    report = tmp_path / "m.md"
    code = main(
        ["replay", "--episode", "cw", "--years", "1957..1962", "--out", str(out)]
        + ["--measure-proposals", "--report", str(report)]
    )
    assert code == 0
    text = report.read_text()
    assert text.startswith("PROPOSAL-LEVEL MEASUREMENT") and "Cold War 1957 to 1962" in text
    assert "--episode cw --years 1957..1962" in text
    # the dry run counts by year; the rule backend reads the corpus and proposes nothing here
    capsys.readouterr()
    code = main(
        ["replay", "--episode", "cw", "--years", "1958..1962", "--corpus", str(corpus.root)]
        + ["--out", str(tmp_path / "dry"), "--backend", "claude", "--dry-run"]
    )
    assert code == 0
    printed = capsys.readouterr().out
    assert "year " in printed and "1958" in printed and not (tmp_path / "dry").exists()
    assert main(["replay", "--episode", "cw", "--out", str(tmp_path / "x")]) == 2
    assert main(["replay", "--episode", "cw", "--quarters", "1958Q1", "--out", "x"]) == 2
    assert main(["replay", "--years", "1958", "--out", str(tmp_path / "x")]) == 2


def test_cw_plan_counts_by_year(cw_run, tmp_path):
    corpus = cw_run[0]
    rows = plan(corpus, YEARS, tmp_path / "plan", ClaudeBackend(client=object()), episode="cw")
    assert [(r.quarter, r.visible, r.to_read) for r in rows] == [
        ("1957", 0, 0),
        ("1958", 1, 1),
        ("1959", 1, 0),
        ("1960", 2, 1),
        ("1961", 2, 0),
        ("1962", 3, 1),
    ]


def test_cw_review_and_refusals(cw_run, tmp_path):
    corpus = cw_run[0]
    out = tmp_path / "rev"
    real = LocalCorpus(corpus.root)
    replay(real, ["1958"], out, FakeBackend(), cache=False, episode="cw")
    path = out / "proposals" / "1958.json"
    assert not (out / "1958.json").exists()
    written = decide(path, "1958-001", "accepted", note="reads the estimate", reviewer="t")
    assert written == [out / "1958.json"]
    snap = json.loads(written[0].read_text())
    assert snap["variables"]["belief_force_USA"]["level"] == "under_1000"
    assert "accepted by t" in snap["variables"]["belief_force_USA"]["indicators"][0]["rule"]
    # one episode per directory
    with pytest.raises(ReplayError, match="episode"):
        replay(real, ["1936Q1"], out, FakeBackend(), cache=False)
    # an annual snapshot needs a 31 December cut-off
    from wavefront.evidence.review import build_snapshot

    with pytest.raises(ReviewError, match="31 December"):
        build_snapshot(date(1958, 6, 30), [], episode="cw")


def test_cw_flips_start_from_the_record_of_the_year_before(tmp_path):
    """1982 and 1983 (a range the harness plans): the record's belief_force_USA is over_1000
    from 1968, not the initial none. The replayed and the documented flips both start from
    the record's level of 1981, so a replay that agrees with the record in both years has no
    false flip; its own 1981 snapshot, if any, is not read."""
    years = ["1982", "1983"]
    record = contemporaneous(["1981", *years])
    for y in years:
        snap = json.loads((CW.hindsight / f"{y}.json").read_text())
        for name in CW.text_variables:
            snap["variables"][name] = {
                "level": record[name][y][0],
                "confidence": "medium",
                "indicators": [],
            }
        (tmp_path / f"{y}.json").write_text(json.dumps(snap))
    m = compare(tmp_path, years, episode="cw")
    assert m.agreement("belief_force_USA", "contemporaneous") == (2, 2)
    text = render_report(m, title="t", corpus={"source": "s"}, backend={"name": "b"}, command="c")
    assert "Both series start from the record's level on 1 January 1981" in text
    assert [(d and d.year, r and r.year) for d, r in m.matches["belief_force_USA"]] == []
    # the documented 1983 flip of belief_USSR_USA (hostile -> first_strike_intent) is matched
    assert [(d and d.year, r and r.year) for d, r in m.matches["belief_USSR_USA"]] == [
        ("1983", "1983")
    ]
    stale = json.loads((tmp_path / "1982.json").read_text())
    stale["variables"]["belief_force_USA"]["level"] = "none"
    (tmp_path / "1981.json").write_text(json.dumps(stale))
    m = compare(tmp_path, years, episode="cw")
    assert m.matches["belief_force_USA"] == []


def test_a_set_valued_hindsight_entry_is_carried_as_a_set(tmp_path):
    """A Cold War snapshot carries a set-valued hindsight entry (a contested window) as a
    set: no confidence at the set level, each member marked assumed with its indicators."""
    from wavefront.evidence.review import build_snapshot

    snap = json.loads((CW.hindsight / "1958.json").read_text())
    concrete = snap["variables"]["intel_USA"]
    other = "overhead"
    snap["variables"]["intel_USA"] = {
        "levels": [concrete, {**copy.deepcopy(concrete), "level": other}],
        "ambiguity": "the crossing is a judgement",
    }
    assert validate_snapshot(snap) == []
    (tmp_path / "1958.json").write_text(json.dumps(snap))
    out = build_snapshot(date(1957, 12, 31), [], hindsight_dir=tmp_path, episode="cw")
    entry = out["variables"]["intel_USA"]
    assert set(entry) == {"levels", "ambiguity"}
    assert [m["level"] for m in entry["levels"]] == ["partial", other]
    for m in entry["levels"]:
        assert m["confidence"] == "assumed"
        assert m["indicators"][0]["rule"].startswith("not read in the blind replay")
