"""Robust and fragile findings over the member states of a snapshot with a set of levels
(docs/ambiguous_levels.md), on a toy game whose answers are known."""

import pytest

from wavefront.analysis import (
    Robustness,
    robust,
    robust_attractor,
    robust_kernel,
    robust_pivotal,
    robust_sensitivity,
    robust_status,
    run_all,
)
from wavefront.engine import explore
from wavefront.evidence import snapshot_to_states
from wavefront.model import Bump, Model, ModelError, V
from wavefront.report import render

GATE_SOURCE = '''
from wavefront.model import Bump, Model, V


def gate():
    """Untimed. Nature may push x up by one each tick; P may pull it down by one while
    ``shield`` holds. ``low``: x <= 2; the ending BREACH is x == 3."""
    m = Model("gate", horizon=None)
    m.counter("x", max=3, init=0)
    m.flag("shield", init=True)
    p = m.actor("P")
    p.action("pull", guard=V.shield, effect=Bump("x", -1), source="toy")
    m.nature().event("push", effect=Bump("x", +1), source="toy")
    m.invariant("low", V.x <= 2)
    m.ending("BREACH", V.x == 3)
    return m


model = gate()
'''


def gate():
    """See ``GATE_SOURCE``. Known answers: with the shield, P keeps ``low`` and blocks
    BREACH from x <= 2; without it, nobody does, and Nature can breach."""
    m = Model("gate", horizon=None)
    m.counter("x", max=3, init=0)
    m.flag("shield", init=True)
    p = m.actor("P")
    p.action("pull", guard=V.shield, effect=Bump("x", -1), source="toy")
    m.nature().event("push", effect=Bump("x", +1), source="toy")
    m.invariant("low", V.x <= 2)
    m.ending("BREACH", V.x == 3)
    return m


def indicator(rule="r"):
    return {"id": "i", "value": "v", "source": "s", "observed": "2026-01-01", "rule": rule}


def member(level):
    return {"level": level, "confidence": "medium", "indicators": [indicator()]}


def snapshot(**variables):
    """A gate snapshot: a list value gives a set of levels, anything else one level."""
    out = {}
    for name, value in variables.items():
        if isinstance(value, list):
            out[name] = {"levels": [member(v) for v in value], "ambiguity": "contested"}
        else:
            out[name] = member(value)
    return {"date": "2026-01-01", "model": "gate", "variables": out}


def setup(**variables):
    m = gate()
    cm = m.compile()
    members = snapshot_to_states(snapshot(**variables), cm)
    g = explore(cm, initial=list(members.states))
    return m, g, members


def test_a_set_on_the_shield_makes_kernel_membership_and_the_blocking_coalition_fragile():
    _m, g, members = setup(x=0, shield=[True, False])
    assert members.ambiguous == (("shield", (False, True)),)
    rk = robust_kernel(g, members, ["P"], "low")
    assert not rk.in_kernel.robust and rk.in_kernel.verdict == "fragile"
    assert rk.in_kernel.answers == (False, True)
    assert rk.in_kernel.classes == [(False, ["shield=false"]), (True, ["shield=true"])]
    assert rk.in_kernel.summary() == "fragile: False from [shield=false]; True from [shield=true]"
    # P cannot reach BREACH from either member: robust, though for different reasons
    status = robust_status(g, members, ["P"], "BREACH")
    assert status.robust and status.value == "blocked"
    piv = robust_pivotal(g, members, "BREACH")
    assert [p.blocking for p in piv.answers] == [[], [frozenset({"P"})]]
    assert not piv.robust


def test_a_set_on_x_inside_the_kernel_is_robust_on_membership_and_fragile_on_distance():
    _m, g, members = setup(x=[0, 1], shield=True)
    rk = robust_kernel(g, members, ["P"], "low")
    assert rk.in_kernel.robust and rk.in_kernel.value is True
    assert rk.in_kernel.summary(lambda b: "yes" if b else "no") == "robust: yes"
    assert [d.shortest for d in rk.distance.answers] == [3, 2]
    assert rk.distance.verdict == "fragile"
    status = robust_status(g, members, ["P"], "BREACH")
    assert status.robust and status.value == "blocked"
    piv = robust_pivotal(g, members, "BREACH")
    assert piv.robust and piv.value.blocking == [frozenset({"P"})]
    # forcing BREACH: Nature alone is not a coalition; the empty coalition cannot force it
    att = robust_attractor(g, members, [], g.ending_states("BREACH"), "BREACH")
    assert att.robust and att.value is None


def test_robust_on_plain_states_and_on_one_state():
    m, g, members = setup(x=0, shield=True)
    assert len(members) == 1 and not members.is_set and members.label(0) == "the snapshot state"
    one = robust("x", members, lambda s: s[g.model.index["x"]])
    assert one.robust and one.labels == ("the snapshot state",)
    states = [g.states[i] for i in g.initial]
    plain = robust("x", states, lambda s: s[g.model.index["x"]])
    assert plain.labels == ("#0",) and plain.value == 0
    with pytest.raises(ModelError, match="no member state"):
        robust("x", [], lambda s: 0)
    other = explore(m.compile())
    with pytest.raises(ModelError, match="not in the graph"):
        _m, _g, two = setup(x=[0, 1], shield=False)
        robust_kernel(other, two, ["P"], "low")


def test_robust_sensitivity_asks_each_member_on_its_own():
    m, _g, members = setup(x=0, shield=[True, False])
    res = robust_sensitivity(m, members, "low", ["P"])
    assert isinstance(res, Robustness) and len(res.answers) == 2
    assert not res.robust


def test_run_all_with_members_reports_robust_and_fragile_findings():
    m = gate()
    members = snapshot_to_states(snapshot(x=0, shield=[True, False]), m.compile())
    a = run_all(m, members=members)
    assert sorted(a.graph.states[i] for i in a.graph.initial) == sorted(members.states)
    verdicts = {r.question: r.verdict for r in a.robustness}
    assert verdicts["low: in the kernel of {P}"] == "fragile"
    assert verdicts["BREACH: pivotal coalitions"] == "fragile"
    text = render(a)
    assert "## Robust and fragile findings" in text
    assert "[shield=false]; [shield=true]" in text
    with pytest.raises(ValueError, match="either initial states or members"):
        run_all(m, members=members, initial=list(members.states))
    assert run_all(m).robustness == []
    assert "Robust and fragile" not in render(run_all(m))


def test_wf_viable_and_report_print_robust_and_fragile(tmp_path, capsys):
    import json

    from wavefront.cli import main

    path = tmp_path / "gate.py"
    path.write_text(GATE_SOURCE, encoding="utf-8")
    snap = tmp_path / "set.json"
    snap.write_text(json.dumps(snapshot(x=0, shield=[True, False])), encoding="utf-8")
    args = ["viable", str(path), "--coalition", "P", "--invariant", "low", "--snapshot", str(snap)]
    assert main(args) == 0
    out = capsys.readouterr().out
    assert "a set of 2 member states" in out
    verdict = "fragile: no from [shield=false]; yes from [shield=true]"
    assert f"low: in the kernel of {{P}}: {verdict}" in out
    single = tmp_path / "one.json"
    single.write_text(json.dumps(snapshot(x=0, shield=True)), encoding="utf-8")
    assert main([*args[:-1], str(single)]) == 0
    assert "member states" not in capsys.readouterr().out
    report = tmp_path / "r.md"
    assert main(["report", str(path), "--snapshot", str(snap), "--out", str(report)]) == 0
    assert "## Robust and fragile findings" in report.read_text(encoding="utf-8")
    assert main(["report", str(path), "--snapshot", str(single), "--out", str(report)]) == 0
    assert "Robust and fragile" not in report.read_text(encoding="utf-8")
