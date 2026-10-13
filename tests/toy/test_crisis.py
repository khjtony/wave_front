"""Engine demonstrations on the multi-resolution toy ``models/toy/crisis.py``.

These are demonstrations, not findings. Each test asserts what the engine computes on the
flattened standoff (a coarse game in years with one crisis sub-game in days) to show that
forcing, blocking, kernels, pivotal coalitions, witnesses and the Markdown report work on a
flattened game. Nothing here says anything about a real system, and if the toy is edited the
answers here are expected to change with it.
"""

from models.toy.crisis import coarse, flat
from wavefront.analysis import (
    Analysis,
    EndingEntry,
    KernelEntry,
    RelaxSets,
    distance_table,
    fingerprint,
    is_uniform,
    pivotal,
    point_of_no_return,
    signature,
    silent_phase,
    strategy_closure,
    viability,
)
from wavefront.engine import attractor, contested, explore, witness
from wavefront.report import render

ENDINGS = ["WAR", "DETENTE", "HORIZON"]


def start(fm, **levels):
    """The coarse initial state with some variables changed (level names or integers)."""
    cm = fm.coarse
    state = list(cm.initial_states()[0])
    for name, value in levels.items():
        spec = cm.variables[cm.index[name]]
        state[cm.index[name]] = value if isinstance(value, int) else spec.levels.index(value)
    return tuple(state)


def status(g, coalition, ending):
    (s,) = g.initial
    r = contested(g, coalition, g.ending_states(ending), "reach")
    return "forced" if s in r.forced else "blocked" if s in r.blocked else "contested"


def test_flattened_toy_explores_with_crisis_states():
    fm = flat()
    g = explore(fm)
    fine = [s for s in g.states if fm.is_fine(s)]
    assert fine and len(fine) < g.size()
    assert all(not fm.is_terminal(s) for s in fine)
    assert {g.ending[i] for i in range(g.size())} == {None, *ENDINGS}


def test_east_can_force_detente_only_before_the_arsenal_is_full():
    """From the declared start EAST alone can force DETENTE (provoke, then enter the crisis
    and withdraw while escalation is low); from a tense start with WEST's arsenal full, the
    crisis opens at high escalation and WEST alone can veto detente."""
    fm = flat()
    g = explore(fm)
    assert status(g, {"EAST"}, "DETENTE") == "forced"
    assert status(g, {"WEST"}, "DETENTE") == "blocked"
    assert pivotal(g, "DETENTE").forcing == [frozenset({"EAST"})]
    armed = explore(fm, initial=[start(fm, rivalry="tense", arms=2)])
    assert status(armed, {"EAST"}, "DETENTE") == "blocked"
    assert status(armed, {"EAST", "Nature"}, "DETENTE") == "blocked"
    assert status(armed, {"EAST", "WEST"}, "DETENTE") == "forced"
    one = explore(fm, initial=[start(fm, rivalry="tense", arms=1)])
    (s,) = one.initial
    # Entry, one day, return: three transitions, one coarse tick.
    assert attractor(one, {"EAST"}, one.ending_states("DETENTE")).rank[s] == 3


def test_war_needs_both_powers_and_either_can_avoid_it():
    fm = flat()
    g = explore(fm)
    assert pivotal(g, "WAR").forcing == [frozenset({"EAST", "WEST"})]
    assert sorted(map(sorted, pivotal(g, "WAR").blocking)) == [["EAST"], ["WEST"]]
    armed = explore(fm, initial=[start(fm, rivalry="tense", arms=2)])
    (s,) = armed.initial
    assert s in viability(armed, {"EAST"}, "no_war").kernel
    assert s not in viability(armed, {"WEST"}, "no_war").kernel


def test_witness_and_strategy_through_the_crisis():
    fm = flat()
    g = explore(fm)
    (s,) = g.initial
    trace = witness(g, s, g.ending_states("WAR"))
    table = trace.render(g)
    assert "enter crisis standoff_crisis" in table
    assert "standoff_crisis.esc: low -> brink" in table
    assert "return from crisis standoff_crisis; status: open -> broken" in table
    assert any(fm.is_fine(g.states[i]) for i in trace.state_ids)
    # EAST's kernel is lost inside the crisis, on the day escalation reaches the brink.
    kernel = viability(g, {"EAST"}, "no_war").kernel
    t_k = point_of_no_return(trace, kernel)
    assert fm.is_fine(g.states[trace.state_ids[t_k]])
    assert silent_phase(trace, g, {"EAST"}, "no_war").t_K == t_k
    sig = signature(trace, g)
    assert ("EAST", "escalate") in sig and ("EAST", "crisis") in sig
    a = attractor(g, {"EAST"}, g.ending_states("DETENTE"))
    used = strategy_closure(g, ["EAST"], a.strategy, [s])
    assert any(fm.is_fine(g.states[i]) for i in used)
    assert is_uniform(g, ["EAST"], used).uniform


def test_markdown_report_renders_a_flattened_game():
    """``run_all`` compiles a ``Model`` and so does not take a flattened game; the report is
    assembled here from the parts that apply to a graph (no relaxation or sensitivity
    tables) to show that the renderer prints crisis states and traces."""
    fm = flat()
    g = explore(fm)
    init = list(g.initial)
    groups = [("EAST",), ("WEST",), ("EAST", "WEST")]
    kernels = []
    for c in groups:
        res = viability(g, c, "no_war")
        dist = distance_table(g, init, res.kernel, c, None)
        kernels.append(KernelEntry("no_war", c, res, {s: s in res.kernel for s in init}, dist))
    ends, witnesses, piv = [], {}, {}
    for e in ENDINGS:
        target = g.ending_states(e)
        for c in groups:
            res = contested(g, c, target, "reach")
            st = {s: "forced" if s in res.forced else "blocked" for s in init}
            rank = attractor(g, c, target).rank
            ends.append(EndingEntry(e, c, res, st, {s: rank[s] for s in init if s in rank}))
        witnesses[e] = witness(g, init[0], target)
        piv[e] = pivotal(g, e)
    analysis = Analysis(
        model=coarse,
        cm=fm,
        graph=g,
        profile=None,
        coalitions=groups,
        endings=ENDINGS,
        kernels=kernels,
        contested=ends,
        witnesses=witnesses,
        relaxations={e: RelaxSets() for e in ENDINGS},
        pivotal=piv,
        sensitivity={},
        uniformity=[],
        budget=fm.budget(),
        speculative=[],
        max_relax=0,
        fingerprint=fingerprint(coarse),
    )
    text = render(analysis)
    assert "enter crisis standoff_crisis" in text
    assert "| crises | 1 |" in text
    assert "1 [standoff_crisis 0]" in text
