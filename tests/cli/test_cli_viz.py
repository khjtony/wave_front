"""``wf viz``: the visualizer page from the command line."""

import json
import re
from pathlib import Path

from wavefront.cli import main

FIXTURES = Path(__file__).parent / "fixtures"
STANDOFF = str(FIXTURES / "standoff.py")
TOY = str(Path(__file__).resolve().parents[2] / "models" / "toy" / "two_power.py")
SNAPSHOT = str(Path(__file__).resolve().parents[2] / "snapshots" / "toy" / "example.json")


def run(capsys, *argv):
    code = main(list(argv))
    out, err = capsys.readouterr()
    return code, out, err


def embedded(path):
    text = Path(path).read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" id="bundle">(.*?)</script>', text, re.S)
    return json.loads(m.group(1))


def test_viz_writes_a_page(capsys, tmp_path):
    out = tmp_path / "standoff.html"
    code, stdout, err = run(capsys, "viz", STANDOFF, "--out", str(out), "--max-relax", "1")
    assert code == 0 and err == ""
    assert "page written to" in stdout and "all 87 joint moves" in stdout
    data = embedded(out)
    assert data["meta"]["name"] == "standoff"
    assert [c["name"] for c in data["coalitions"]] == ["{A}", "{B}", "{A, B}"]
    assert data["endings"] == ["WAR", "DEAL", "HORIZON"]
    assert data["meta"]["max_relax"] == 1


def test_viz_coalitions_endings_profile_and_max_moves(capsys, tmp_path):
    out = tmp_path / "s.html"
    code, stdout, _ = run(
        capsys,
        "viz",
        STANDOFF,
        "--out",
        str(out),
        "--coalition",
        "B",
        "--coalition",
        "A,B",
        "--ending",
        "DEAL",
        "--ending",
        "WAR",
        "--max-moves",
        "10",
        "--max-relax",
        "0",
    )
    assert code == 0
    assert "neighborhood" in stdout
    data = embedded(out)
    assert [c["members"] for c in data["coalitions"]] == [["B"], ["A", "B"]]
    assert data["endings"] == ["DEAL", "WAR"]
    assert data["moves"]["complete"] is False


def test_viz_snapshot(capsys, tmp_path):
    out = tmp_path / "toy.html"
    code, _, err = run(
        capsys,
        "viz",
        TOY,
        "--out",
        str(out),
        "--snapshot",
        SNAPSHOT,
        "--coalition",
        "INC",
        "--ending",
        "TAKEOVER",
        "--max-relax",
        "0",
    )
    assert code == 0, err
    data = embedded(out)
    assert data["meta"]["initial_source"] == "snapshot"
    assert data["snapshot"]["variables"]["aims"]["level"] == "hegemonic"


def test_viz_errors(capsys, tmp_path):
    out = str(tmp_path / "x.html")
    code, _, err = run(capsys, "viz", STANDOFF, "--out", out, "--ending", "NOPE")
    assert code == 2 and "no ending named 'NOPE'" in err
    code, _, err = run(capsys, "viz", STANDOFF, "--out", out, "--coalition", "Z")
    assert code == 2 and "unknown actor 'Z'" in err
    code, _, err = run(capsys, "viz", str(FIXTURES / "missing.py"), "--out", out)
    assert code == 1 and "does not exist" in err
    code, _, err = run(capsys, "viz", STANDOFF, "--out", out, "--max-states", "3")
    assert code == 1 and "max_states" in err
    code, _, err = run(capsys, "viz", STANDOFF, "--out", str(tmp_path), "--max-relax", "0")
    assert code == 1 and err.startswith("error:")
    assert not Path(out).exists()
