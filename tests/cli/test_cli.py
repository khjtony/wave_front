"""The ``wf`` command line, run in-process through ``main(argv)``."""

from pathlib import Path

import pytest

from wavefront.cli import load_model, main
from wavefront.model import Model
from wavefront.report import CAVEAT

FIXTURES = Path(__file__).parent / "fixtures"
STANDOFF = str(FIXTURES / "standoff.py")
BROKEN = str(FIXTURES / "broken.py")


def run(capsys, *argv):
    code = main(list(argv))
    out, err = capsys.readouterr()
    return code, out, err


def test_load_model_default_attr_and_callable():
    m = load_model(STANDOFF)
    assert isinstance(m, Model) and m.name == "standoff"
    assert load_model(STANDOFF + ":build").name == "standoff"
    assert load_model(STANDOFF + ":").name == "standoff"


def test_load_model_errors(capsys):
    code, _, err = run(capsys, "explore", str(FIXTURES / "missing.py"))
    assert code == 1 and "does not exist" in err
    code, _, err = run(capsys, "explore", STANDOFF + ":nope")
    assert code == 1 and "no attribute 'nope'" in err
    code, _, err = run(capsys, "explore", str(FIXTURES / "not_a_model.py"))
    assert code == 1 and "not a wavefront Model" in err


def test_explore(capsys):
    code, out, err = run(capsys, "explore", STANDOFF)
    assert code == 0 and err == ""
    assert "model standoff:" in out and "1 initial" in out
    assert "WAR:" in out and "DEAL:" in out
    assert "speculative_actions: 1" in out


def test_model_error_exits_2_with_message_on_stderr(capsys):
    code, out, err = run(capsys, "explore", BROKEN)
    assert code == 2
    assert "actor Q has no available action in state" in err
    code, _, err = run(capsys, "reach", STANDOFF, "--ending", "NOPE")
    assert code == 2 and "no ending named 'NOPE'" in err
    code, _, err = run(capsys, "explore", STANDOFF, "--profile", "nope")
    assert code == 2 and "no profile 'nope'" in err


def test_budget_exceeded_exits_1(capsys):
    code, _, err = run(capsys, "explore", STANDOFF, "--max-states", "3")
    assert code == 1 and "max_states" in err


def test_reach_with_trace(capsys):
    code, out, _ = run(capsys, "reach", STANDOFF, "--ending", "WAR")
    assert code == 0
    assert "WAR: reachable from 1 of 1 initial states." in out
    assert CAVEAT in out
    assert "Shortest witness: 2 steps" in out and "| tick |" not in out
    code, out, _ = run(capsys, "reach", STANDOFF, "--ending", "WAR", "--trace")
    assert "| tick | A | B | Nature | changes |" in out
    assert "ending: WAR" in out


def test_force(capsys):
    code, out, _ = run(capsys, "force", STANDOFF, "--coalition", "A,B", "--ending", "WAR")
    assert code == 0
    assert "| #0 | forced | 2 |" in out
    assert "strategy is uniform" in out
    code, out, _ = run(capsys, "force", STANDOFF, "--coalition", "B", "--ending", "DEAL")
    assert "| #0 | forced | 1 |" in out
    code, out, _ = run(capsys, "force", STANDOFF, "--coalition", "A", "--ending", "DEAL")
    assert "| #0 | blocked |" in out
    code, _, err = run(capsys, "force", STANDOFF, "--coalition", "Z", "--ending", "DEAL")
    assert code == 2 and "unknown actor 'Z'" in err


def test_viable(capsys):
    code, out, _ = run(capsys, "viable", STANDOFF, "--coalition", "A", "--invariant", "calm")
    assert code == 0
    assert "| #0 | yes |" in out
    code, out, _ = run(capsys, "viable", STANDOFF, "--coalition", "A,B", "--invariant", "calm")
    assert "forced if A defects" in out and "forced if B defects" in out
    code, _, err = run(capsys, "viable", STANDOFF, "--coalition", "A", "--invariant", "WAR")
    assert code == 2 and "no invariant named 'WAR'" in err


def test_mine(capsys):
    code, out, _ = run(capsys, "mine", STANDOFF, "--ending", "DEAL")
    assert code == 0
    assert "{}" in out  # reachable as is
    code, out, _ = run(capsys, "mine", STANDOFF, "--ending", "DEAL", "--coalition", "A")
    assert "none of size at most 2" in out
    # relaxing B.sign lets a deal and a war happen together: reported, not a result
    assert "ill-formed: {B.sign}: endings WAR, DEAL hold together" in out
    code, out, _ = run(capsys, "mine", STANDOFF, "--ending", "WAR", "--k", "2")
    assert code == 0 and "--k applies to --bmc only" in out


def test_pivot(capsys):
    code, out, _ = run(capsys, "pivot", STANDOFF, "--ending", "DEAL")
    assert code == 0
    assert "forcing:  {B}" in out
    assert "blocking: {B}" in out
    code, out, _ = run(capsys, "pivot", STANDOFF, "--ending", "WAR", "--nature")
    assert "forcing:  {A, B}" in out


def test_report_to_stdout_and_file(capsys, tmp_path):
    code, out, _ = run(capsys, "report", STANDOFF)
    assert code == 0
    assert out.startswith("# Analysis report: standoff")
    assert CAVEAT in out
    target = tmp_path / "report.md"
    code, out, _ = run(capsys, "report", STANDOFF, "--out", str(target), "--coalition", "A,B")
    assert code == 0 and "report written" in out
    text = target.read_text()
    assert "Coalitions analysed: {A, B}" in text


def test_usage_errors_exit_through_argparse(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["force", STANDOFF, "--ending", "WAR"])
    assert exc.value.code == 2
    with pytest.raises(SystemExit):
        main([])
