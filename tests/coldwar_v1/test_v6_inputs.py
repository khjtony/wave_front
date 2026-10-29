"""Construction tests of V6's inputs (the owner's decisions 7i and 7k of 2026-10-28, before
first sight; docs/cw_v1_decisions.md D9 and R V6). They check the input coding and the path the
V6 body takes, never V6's quantities: no first-sight switch, no API call, no comparison of a
replayed belief with a count.

* The manual replay rows of 1957 to 1962 record the estimate's date, the date it projects for
  and the projected number, and the replay snapshots carry them (through the builder).
* The count is the 1990 edition of Norris and Cochran throughout; v1 reads none of v0's
  survivability-scale replay rows of ``nuke_USSR``.
* The blind path: a synthetic replay with a fake backend, read at proposal level by the
  harness, gives the replay states and the projected dates by the rule of decision 7k; a
  missing blind directory fails clearly.
"""

import csv
import json
from datetime import date
from pathlib import Path

import pytest

from models.cw import v1
from models.cw.snapshots_v1 import (
    BLIND_REPLAY_ENV,
    DROPPED_V0_ROWS,
    EVENTS_V1,
    SNAPSHOTS,
    blind_snapshots,
    estimate_date,
    projected_year,
    projection,
    rule_projected_date,
    rule_year,
    snapshot_state,
)
from tests.coldwar_v1.common import HYPS, compiled, hindsight
from tests.coldwar_v1.scenarios import test_V06 as v6
from wavefront.evidence.corpora import LocalCorpus
from wavefront.evidence.extract import Proposal
from wavefront.evidence.replay import replay

YEARS = list(range(1957, 1963))


def _rows():
    with open(EVENTS_V1, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(line for line in fh if not line.startswith("#")))


def _band(n: int) -> str:
    return v1.BANDS[(n > 0) + (n >= 200) + (n >= 1000)]


def _replay(year: int) -> dict:
    return json.loads((SNAPSHOTS / "replay" / f"{year}.json").read_text(encoding="utf-8"))


# -- the manual replay's projected dates (decision 7i) --------------------------------------
def test_the_belief_rows_record_the_estimate_and_its_projection():
    rows = [r for r in _rows() if r["variable"] == "belief_force_USA"]
    others = [r for r in _rows() if r["variable"] != "belief_force_USA"]
    assert all(not (r["estimate_date"] or r["projected_for"]) for r in others)
    for r in rows:
        if not r["projected_for"]:
            assert r["year"] in ("1946", "1967") and not r["projected_count"]
            continue
        estimate = date.fromisoformat(r["estimate_date"])
        projected = date.fromisoformat(r["projected_for"])
        # dated before the snapshot it serves; a mid-year about two to three years ahead
        assert estimate <= date(int(r["year"]), 12, 31), r["year"]
        assert (projected.month, projected.day) == (7, 1), r["year"]
        assert projected.year - estimate.year in (2, 3), r["year"]
        # the projected number, on the midpoints, is in the band the row codes
        assert _band(int(r["projected_count"])) == r["level"], r["year"]


def test_each_replay_snapshot_of_1957_to_1962_carries_its_projection():
    rows = {int(r["visible_year"]): r for r in _rows() if r["variable"] == "belief_force_USA"}
    for y in YEARS:
        r = max((k for k in rows if k <= y), default=None)
        row = rows[r]
        assert projection(y) == (
            date.fromisoformat(row["projected_for"]),
            int(row["projected_count"]),
        )
        entry = _replay(y)["variables"]["belief_force_USA"]
        assert estimate_date(entry) == date.fromisoformat(row["estimate_date"])
        # the hindsight snapshot read: the latest 1 January not after the projected date
        assert projected_year(y) == date.fromisoformat(row["projected_for"]).year > y
    assert projection(1983) is None  # NIE 11-8-67 states no total for a mid-year


def test_v1_reads_none_of_v0s_survivability_replay_rows():
    assert ("nuke_USSR", "replay") in DROPPED_V0_ROWS
    for y in YEARS:
        entry = _replay(y)["variables"]["nuke_USSR"]
        assert entry["confidence"] == "assumed"
        assert all(i["id"].endswith("_record") for i in entry["indicators"]), y


def test_the_count_is_the_1990_edition_throughout():
    path = v1.DATA_V1 / "strategic_launchers.csv"
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(line for line in fh if not line.startswith("#")))
    for r in rows:
        assert r["source"].startswith("Norris and Cochran 1990 (NRDC Working Paper 90-1)"), r
        assert "1997" not in r["source"]
        assert "1997" not in r["note"] or "not used" in r["note"], r["year"]


# -- the rule of decision 7k ----------------------------------------------------------------
def test_the_rule_is_the_estimates_date_plus_thirty_months():
    assert rule_projected_date(date(1957, 12, 10)) == date(1960, 6, 10)
    assert rule_projected_date(date(1960, 8, 1)) == date(1963, 2, 1)
    assert rule_projected_date(date(1958, 8, 31)) == date(1961, 2, 28)
    no_estimate = {"level": "none", "confidence": "assumed", "indicators": []}
    assert rule_year(1957, no_estimate) == 1957
    # the manual series, printed beside, takes the rule from its own estimate's date
    manual = v6.manual_snapshots()
    rule = v6.read_years(manual)
    for y in YEARS:
        est = estimate_date(manual[y]["variables"]["belief_force_USA"])
        assert rule[y] == rule_projected_date(est).year
    assert v6.read_years(manual, recorded=True) == {y: projected_year(y) for y in YEARS}


# -- the blind path, synthetic (no switch, no API call) -------------------------------------
DOCS = {
    "1957-12-10_estimate": ("A synthetic sentence on the projected force.", "under_1000"),
    "1960-08-01_estimate": ("A synthetic sentence on the projected force.", "under_1000"),
    "1961-09-21_estimate": ("A synthetic sentence on the revised force.", "under_200"),
}


class FakeBackend:
    """Proposes the level written into each synthetic document."""

    name = "fake"

    def propose(self, document, variables):
        text, level = DOCS[document.id.removeprefix("syn-")]
        return [
            Proposal(
                f"{document.id}:belief_force_USA",
                "belief_force_USA",
                level,
                document.date.isoformat(),
                text,
                document.url,
                "belief_force_USA: synthetic",
                "high",
            )
        ]


@pytest.fixture(scope="module")
def blind_dir(tmp_path_factory) -> Path:
    base = tmp_path_factory.mktemp("cw_v6")
    root = base / "corpus"
    root.mkdir()
    for name, (text, _level) in DOCS.items():
        (root / f"{name}.txt").write_text(
            "SYNTHETIC FIXTURE: written for pipeline tests, not a source\n"
            f"id: syn-{name}\ndate: {name[:10]}\nsource: synthetic fixture corpus (not a source)\n"
            f"title: {name}\nurl: synthetic:cw/{name}\n\n{text}\n",
            encoding="utf-8",
        )
    out = base / "replay"
    labels = [str(y) for y in YEARS]
    replay(LocalCorpus(root), labels, out, FakeBackend(), cache=False, episode="cw")
    return out


def test_the_blind_series_is_read_at_proposal_level(blind_dir, monkeypatch):
    monkeypatch.setenv(BLIND_REPLAY_ENV, str(blind_dir))
    assert v6.blind_dir() == blind_dir
    snaps = blind_snapshots(v6.blind_dir(), YEARS)
    assert sorted(snaps) == YEARS
    entries = {y: snaps[y]["variables"]["belief_force_USA"] for y in YEARS}
    assert all("NOT REVIEWED" in i["rule"] for y in YEARS[1:] for i in entries[y]["indicators"])
    assert estimate_date(entries[1957]) is None
    assert estimate_date(entries[1958]) == date(1957, 12, 10)
    assert estimate_date(entries[1961]) == date(1960, 8, 1)  # the latest at the level in force
    assert estimate_date(entries[1962]) == date(1961, 9, 21)
    assert v6.read_years(snaps) == {
        1957: 1957,
        1958: 1960,
        1959: 1960,
        1960: 1960,
        1961: 1963,
        1962: 1964,
    }
    # the states V6 starts from, per hypothesis; the hindsight read at each projected year
    for aims in HYPS:
        cm = compiled(aims)
        for y in YEARS:
            s = snapshot_state(cm, y, aims, "replay", snaps[y])
            assert s[cm.index["tick"]] == y - v1.YEAR0
            assert cm.state_dict(s)["belief_force_USA"] == entries[y]["level"]
            assert cm.state_dict(s)["count_USSR"] == cm.state_dict(hindsight(y, aims))["count_USSR"]


def test_a_missing_blind_replay_fails_clearly(tmp_path, monkeypatch):
    monkeypatch.delenv(BLIND_REPLAY_ENV, raising=False)
    with pytest.raises(RuntimeError, match=BLIND_REPLAY_ENV):
        v6.blind_dir()
    monkeypatch.setenv(BLIND_REPLAY_ENV, str(tmp_path))
    with pytest.raises(RuntimeError, match="no proposals"):
        v6.blind_dir()
    with pytest.raises(FileNotFoundError):
        blind_snapshots(tmp_path, YEARS)


def test_the_v6_body_runs_its_comparisons_on_a_synthetic_blind_series(blind_dir, capsys):
    """(a), (c) and the control of the V6 body on the synthetic series (not evidence: the
    fixture's levels are made up); only that they run and return booleans is checked."""
    snaps = blind_snapshots(blind_dir, YEARS)
    aims = HYPS[0]
    cm = compiled(aims)
    states = {y: snapshot_state(cm, y, aims, "replay", snaps[y]) for y in YEARS}
    out = v6.gap_and_closing(cm, aims, states, v6.read_years(snaps), "synthetic")
    capsys.readouterr()
    assert all(isinstance(x, bool) for x in out)
