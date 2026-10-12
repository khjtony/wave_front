"""``--fix VAR=LEVEL``: fixing swept variables that a snapshot omits (``viable``, ``viz``)."""

import json
import re
from pathlib import Path

import pytest

from wavefront.cli import main

ROOT = Path(__file__).resolve().parents[2]
TOY = str(ROOT / "models" / "toy" / "two_power.py")
SNAPSHOT = ROOT / "snapshots" / "toy" / "example.json"


def run(capsys, *argv):
    code = main(list(argv))
    out, err = capsys.readouterr()
    return code, out, err


@pytest.fixture
def partial(tmp_path):
    """The toy example snapshot without its two swept variables (``aims``, ``tension``)."""
    data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    del data["variables"]["aims"]
    del data["variables"]["tension"]
    path = tmp_path / "partial.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def viable(capsys, snapshot, *extra):
    return run(
        capsys,
        "viable",
        TOY,
        "--coalition",
        "INC",
        "--invariant",
        "balance",
        "--snapshot",
        snapshot,
        *extra,
    )


def test_fix_gives_the_same_state_as_a_full_snapshot(capsys, partial):
    code, full, err = viable(capsys, str(SNAPSHOT))
    assert code == 0, err
    code, fixed, err = viable(capsys, partial, "--fix", "aims=hegemonic", "--fix", "tension=calm")
    assert code == 0, err
    assert fixed == full


def test_fix_changes_the_hypothesis(capsys, partial):
    _, heg, _ = viable(capsys, partial, "--fix", "aims=hegemonic", "--fix", "tension=calm")
    code, lim, err = viable(capsys, partial, "--fix", "aims=limited", "--fix", "tension=calm")
    assert code == 0, err
    assert lim != heg


def test_fix_errors(capsys, partial):
    code, _, err = viable(capsys, partial, "--fix", "aims=hegemonic")
    assert code == 2 and "'tension'" in err and "must fix" in err
    code, _, err = viable(capsys, partial, "--fix", "aims=hegemonic", "--fix", "oversight=weak")
    assert code == 2 and "not swept" in err
    code, _, err = viable(capsys, str(SNAPSHOT), "--fix", "aims=limited")
    assert code == 2 and "already fixes 'aims'" in err
    code, _, err = viable(capsys, partial, "--fix", "aims=bogus", "--fix", "tension=calm")
    assert code == 2 and "no level 'bogus'" in err
    code, _, err = viable(capsys, partial, "--fix", "nope=1", "--fix", "tension=calm")
    assert code == 2 and "not a variable" in err
    code, _, err = run(
        capsys, "viable", TOY, "--coalition", "INC", "--invariant", "balance", "--fix", "aims=x"
    )
    assert code == 2 and "--fix needs --snapshot" in err
    with pytest.raises(SystemExit) as exc:
        viable(capsys, partial, "--fix", "aims")
    assert exc.value.code == 2


def test_fix_on_viz(capsys, partial, tmp_path):
    out = tmp_path / "toy.html"
    code, _, err = run(
        capsys,
        "viz",
        TOY,
        "--out",
        str(out),
        "--snapshot",
        partial,
        "--fix",
        "aims=hegemonic",
        "--fix",
        "tension=calm",
        "--coalition",
        "INC",
        "--ending",
        "TAKEOVER",
        "--max-relax",
        "0",
    )
    assert code == 0, err
    text = out.read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" id="bundle">(.*?)</script>', text, re.S)
    data = json.loads(m.group(1))
    assert data["meta"]["initial_source"] == "snapshot"
    assert data["snapshot"]["variables"]["aims"]["level"] == "hegemonic"
    assert data["snapshot"]["variables"]["aims"]["confidence"] == "assumed"
    code, _, err = run(capsys, "viz", TOY, "--out", str(out), "--fix", "aims=hegemonic")
    assert code == 2 and "--fix needs --snapshot" in err
