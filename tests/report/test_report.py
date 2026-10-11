"""The Markdown report rendered from run_all on hand-built games."""

from analysis.games import coin, crisis, ladder, locks, relay

from wavefront.analysis import run_all
from wavefront.report import CAVEAT, render

SECTIONS = [
    "## Parameter budget",
    "## Initial states and kernel membership",
    "## Endings",
    "## Minimal relaxation sets",
    "## Pivotal coalitions",
    "## Sensitivity",
    "## Strategy uniformity",
    "## Speculative actions used",
]


def test_caveat_first_and_sections_in_spec_order():
    text = render(run_all(crisis()))
    assert CAVEAT == (
        "Every result is conditional on the model version and the initial state; "
        "no bare reachability result is a finding."
    )
    lines = text.splitlines()
    assert lines[0] == "# Analysis report: crisis"
    assert lines[2] == CAVEAT
    positions = [text.index(s) for s in SECTIONS]
    assert positions == sorted(positions)
    assert "fingerprint `" in text


def test_crisis_report_contents():
    a = run_all(crisis())
    text = render(a)
    # budget as a table
    assert "| speculative actions | 1 |" in text
    # kernel membership per coalition
    assert "| {P} | 1 of 1 | 1 | 0 | - | 5 |" in text
    # forced/blocked/contested and the witness table
    assert "| {P} | 0 | 1 | 0 | - |" in text
    assert "| 3 | wait | attack | pos: crisis -> war |" in text
    assert "by itself it is not a finding" in text
    # relaxations and pivotal coalitions
    assert "| `WAR` | 0 | {} (no relaxation) |" in text
    assert "| `WAR` | none | {P} |" in text
    # sensitivity
    assert "| pos | calm -> tense | 1 | 1 -> 0 | 1 | 1 -> 0 |" in text
    # speculative action used by the witness
    assert "- `Nature.escalate`" in text
    assert a.speculative == ["Nature.escalate"]


def test_non_uniform_strategies_are_flagged():
    text = render(run_all(coin(hidden=True)))
    assert "Forcing `WIN` for {P} rests on a non-uniform strategy" in text
    assert "member P cannot tell states #0 and #1 apart" in text
    assert "Even with pooled observations it is not uniform." in text
    assert "upper bound" in text
    assert "The model declares no invariant" in text
    text = render(run_all(coin(hidden=False)))
    assert "non-uniform" not in text
    assert "each member can play on its own observations" in text


def test_report_distinguishes_per_member_from_pooled_uniformity():
    text = render(run_all(relay(), coalitions=[{"A", "B"}]))
    assert "Forcing `WIN` for {A, B} rests on a non-uniform strategy" in text
    assert "member B cannot tell states" in text
    assert "It would be playable if the members pooled their observations." in text


def test_relaxations_and_ill_formed_notes():
    text = render(run_all(locks(with_clash=True), max_relax=2))
    assert "| `DONE` | 2 | {A.go, B.go} |" in text
    assert "relaxing {D.clash} is ill-formed: conflicting Set" in text
    assert "| `DONE` | > 1 | none found |" in render(run_all(locks(), max_relax=1))


def test_untimed_model_without_endings():
    a = run_all(ladder(), coalitions=[{"P"}])
    text = render(a)
    assert a.endings == [] and a.coalitions == [("P",)]
    assert "untimed (no horizon)" in text
    assert "| shield | True -> False | 1 | 1 -> 0 | 1 | 3 -> 0 |" in text
    assert "None of the reported traces uses a speculative action." in text
