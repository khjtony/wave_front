"""Multi-resolution time: the flattened crisis game (spec section 14, theory section 7).

1. Soundness by flattening: a coarse game with a crisis sub-game, flattened by
   :func:`flatten`, against the same game written by hand as one untimed model with the
   crisis inlined (a ``phase`` variable, explicit coarse and fine tick counters and a
   one-move ``Clock`` actor that advances them and applies the exit map). The two graphs
   are isomorphic state by state, and attractors (with ranks), safety kernels, contested
   regions and witness lengths agree on every state, coarse states included.
2. Controllability through the crisis.
3. Nondeterministic exit.
4. Error cases.
5. A random cross-check of 1 (hypothesis, plus a fixed sweep of seeds).

The inlined model needs one restriction on the coarse game: whenever the crisis action is
available, the other actors have only their built-in ``idle``/``none`` (their declared
guards include ``~crisis_guard``). The flattening discards the other actors' coarse moves in
a joint move that enters the crisis, which a single-level model cannot express; that rule is
tested on its own below.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from wavefront.engine import (
    Crisis,
    attractor,
    contested,
    explore,
    flatten,
    safe,
    witness,
)
from wavefront.model import FALSE, TRUE, Bump, Model, ModelError, Set, SetIf, V
from wavefront.model.expr import Expr

# -- a game given once, built two ways --------------------------------------------------


@dataclass
class Spec:
    """A coarse game with one crisis. Variables are ``(name, levels, init)``; actions are
    ``(actor, name, guard, effects)`` with actor ``"Nature"`` for events. Entry values are
    ``("copy", coarse_var)`` (index copied, clamped) or ``("const", level)``. Exit rules are
    ``(fine condition, coarse_var, value)`` with value ``("copy", fine_var)`` or
    ``("const", level)``; per coarse variable the first rule whose condition holds wins."""

    horizon: int
    fine_horizon: int
    coarse_vars: list[tuple[str, list[str], str | None]]
    fine_vars: list[tuple[str, list[str], str]]
    actors: list[str]
    fine_actors: list[str]
    crisis_actor: str
    crisis_guard: Expr
    coarse_actions: list[tuple[str, str, Expr, list]]
    fine_actions: list[tuple[str, str, Expr, list]]
    entry: dict[str, tuple[str, str]]
    exit: list[tuple[Expr, str, tuple[str, str]]]
    coarse_endings: dict[str, Expr] = field(default_factory=dict)
    fine_endings: dict[str, Expr] = field(default_factory=dict)
    invariants: dict[str, Expr] = field(default_factory=dict)


def _declare(m, variables):
    for name, levels, init in variables:
        m.var(name, levels=levels, init=init)


def _actions(actors, actions, guard_prefix=TRUE):
    for actor, name, guard, effects in actions:
        actors[actor].action(name, guard=guard_prefix & guard, effect=effects)


def build_flat(spec: Spec):
    """The coarse and fine models, compiled and flattened."""
    coarse = Model("coarse", horizon=spec.horizon)
    _declare(coarse, spec.coarse_vars)
    actors = {a: coarse.actor(a) for a in spec.actors} | {"Nature": coarse.nature()}
    _actions(actors, spec.coarse_actions)
    actors[spec.crisis_actor].action("crisis", guard=spec.crisis_guard, effect=[])
    for name, e in spec.coarse_endings.items():
        coarse.ending(name, e)
    for name, e in spec.invariants.items():
        coarse.invariant(name, e)

    fine = Model("fine", horizon=spec.fine_horizon)
    _declare(fine, spec.fine_vars)
    factors = {a: fine.actor(a) for a in spec.fine_actors} | {"Nature": fine.nature()}
    _actions(factors, spec.fine_actions)
    for name, e in spec.fine_endings.items():
        fine.ending(name, e)
    sub = fine.compile()
    cm = coarse.compile()

    def entry(year):
        out = {}
        for fv, (kind, x) in spec.entry.items():
            levels = sub.variables[sub.index[fv]].levels
            if kind == "const":
                out[fv] = x
            else:
                src = cm.variables[cm.index[x]].levels.index(year[x])
                out[fv] = levels[min(src, len(levels) - 1)]
        return out

    def exit_map(day, year):
        h = tuple(v.levels.index(day[v.name]) for v in sub.variables)
        out = {}
        for cond, cv, (kind, x) in spec.exit:
            if cv in out or not sub.evaluate(cond, h):
                continue
            levels = cm.variables[cm.index[cv]].levels
            if kind == "const":
                out[cv] = x
            else:
                src = sub.variables[sub.index[x]].levels.index(day[x])
                out[cv] = levels[min(src, len(levels) - 1)]
        return out

    return flatten(cm, [Crisis(spec.crisis_actor, "crisis", sub, entry, exit_map)])


def _any(exprs):
    out = FALSE
    for e in exprs:
        out = out | e
    return out


def build_inlined(spec: Spec):
    """The same game as one untimed model with the crisis inlined."""
    m = Model("inlined", horizon=None)
    _declare(m, spec.coarse_vars)
    _declare(m, spec.fine_vars)
    m.counter("t", max=spec.horizon, init=0)
    m.counter("ft", max=spec.fine_horizon, init=0)
    m.var("phase", levels=["coarse", "fine"], init="coarse")
    actors = {a: m.actor(a) for a in spec.actors} | {"Nature": m.nature()}
    clock = m.actor("Clock", idle=False)
    coarse = V.phase == "coarse"
    over = (V.ft == spec.fine_horizon) | _any(spec.fine_endings.values())
    active = (V.phase == "fine") & ~over
    ret = (V.phase == "fine") & over

    _actions(actors, spec.coarse_actions, coarse)
    entry = [Set(fv, V[x] if kind == "copy" else x) for fv, (kind, x) in spec.entry.items()]
    actors[spec.crisis_actor].action(
        "crisis",
        guard=coarse & spec.crisis_guard,
        effect=[Set("phase", "fine"), Bump("t", -1), *entry],
    )
    _actions(actors, spec.fine_actions, active)

    effects = [
        SetIf(coarse, "t", V.t + 1),
        SetIf(active, "ft", V.ft + 1),
        SetIf(ret, "t", V.t + 1),
        SetIf(ret, "ft", 0),
        SetIf(ret, "phase", "coarse"),
        *(SetIf(ret, fv, init) for fv, _, init in spec.fine_vars),
    ]
    earlier: dict[str, Expr] = {}
    for cond, cv, (kind, x) in spec.exit:
        prior = earlier.get(cv, FALSE)
        effects.append(SetIf(ret & cond & ~prior, cv, V[x] if kind == "copy" else x))
        earlier[cv] = prior | cond
    clock.action("tick", effect=effects)

    endings = list(spec.coarse_endings.values())
    for name, e in spec.coarse_endings.items():
        m.ending(name, coarse & e)
    m.ending("HORIZON_", coarse & (V.t == spec.horizon) & ~_any(endings))
    for name, e in spec.invariants.items():
        m.invariant(name, (V.phase == "fine") | e)
    return m.compile()


def mapping(fm, ci, g):
    """Flat state id -> the inlined state with the same values."""
    sub = fm.crises[0].sub
    out = {}
    for sid, state in enumerate(g.states):
        s, c, h = fm.split(state)
        vals = [v.init[0] for v in ci.variables]
        for v in fm.variables:
            if v.origin == "var":
                vals[ci.index[v.name]] = s[fm.index[v.name]]
        vals[ci.index["t"]] = s[fm.index["tick"]]
        if c is not None:
            vals[ci.index["phase"]] = 1
            vals[ci.index["ft"]] = h[sub.index["tick"]]
            for v in sub.variables:
                if v.origin == "var":
                    vals[ci.index[v.name]] = h[sub.index[v.name]]
        out[sid] = tuple(vals)
    return out


def compare(spec: Spec):
    """Explore both builds and check that every fixpoint agrees on every state."""
    fm = build_flat(spec)
    ci = build_inlined(spec)
    g = explore(fm, max_states=20_000)
    gi = explore(ci, max_states=20_000)
    to_state = mapping(fm, ci, g)
    assert len(set(to_state.values())) == g.size()
    assert set(to_state.values()) == set(gi.states)
    m = {sid: gi.index[t] for sid, t in to_state.items()}
    assert sorted(m[i] for i in g.initial) == sorted(gi.initial)

    def image(ids):
        return {m[i] for i in ids}

    players = [*spec.actors, "Nature"]
    coalitions = [
        set(c) for r in range(len(players) + 1) for c in itertools.combinations(players, r)
    ]
    endings = [*spec.coarse_endings, "HORIZON"]
    for e in endings:
        target, target_i = g.ending_states(e), gi.ending_states("HORIZON_" if e == "HORIZON" else e)
        assert image(target) == target_i
        for c in coalitions:
            a, ai = attractor(g, c, target), attractor(gi, c, target_i)
            assert image(a.win) == ai.win
            assert {m[s]: r for s, r in a.rank.items()} == ai.rank
            r, ri = contested(g, c, target, "reach"), contested(gi, c, target_i, "reach")
            assert (image(r.forced), image(r.blocked)) == (ri.forced, ri.blocked)
        for s in g.initial:
            w, wi = witness(g, s, target), witness(gi, m[s], target_i)
            assert (w is None) == (wi is None)
            if w is not None:
                assert len(w) == len(wi)
    for inv in spec.invariants:
        phi, phi_i = g.states_where(inv), gi.states_where(inv)
        assert image(phi) == phi_i
        for c in coalitions:
            assert image(safe(g, c, phi).kernel) == safe(gi, c, phi_i).kernel
            r, ri = contested(g, c, phi, "keep"), contested(gi, c, phi_i, "keep")
            assert (image(r.forced), image(r.blocked)) == (ri.forced, ri.blocked)
    return fm, g


# -- 1. soundness by flattening on a hand-built game -------------------------------------


def hand_spec() -> Spec:
    hot = (V.tension == "high") & (V.status == "open")
    return Spec(
        horizon=3,
        fine_horizon=2,
        coarse_vars=[
            ("tension", ["low", "mid", "high"], "low"),
            ("deal", ["no", "yes"], "no"),
            ("status", ["open", "settled", "broken"], "open"),
        ],
        fine_vars=[("esc", ["low", "high", "brink"], "low"), ("talks", ["none", "open"], "none")],
        actors=["A", "B"],
        fine_actors=["A", "B"],
        crisis_actor="A",
        crisis_guard=hot,
        coarse_actions=[
            ("A", "provoke", (V.status == "open") & (V.tension < "high"), [Bump("tension", 1)]),
            ("B", "offer", (V.deal == "no") & ~hot, [Set("deal", "yes")]),
            ("Nature", "cool", (V.tension == "mid") & ~hot, [Bump("tension", -1)]),
        ],
        fine_actions=[
            ("A", "escalate", TRUE, [Bump("esc", 1)]),
            ("A", "talk", V.talks == "none", [Set("talks", "open")]),
            ("B", "escalate", TRUE, [Bump("esc", 1)]),
            ("B", "calm", TRUE, [Bump("esc", -1)]),
            ("Nature", "incident", V.esc == "high", [Bump("esc", 1)]),
        ],
        entry={"esc": ("copy", "deal")},
        exit=[
            (V.esc == "brink", "status", ("const", "broken")),
            (V.talks == "open", "status", ("const", "settled")),
            (TRUE, "tension", ("copy", "esc")),
        ],
        coarse_endings={"WAR": V.status == "broken", "PEACE": V.status == "settled"},
        fine_endings={
            "BRINK": V.esc == "brink",
            "DEAL": (V.talks == "open") & (V.esc != "brink"),
        },
        invariants={"stable": V.status != "broken", "cool": V.tension != "high"},
    )


def test_soundness_by_flattening_hand_built():
    fm, g = compare(hand_spec())
    fine = [s for s in g.states if fm.is_fine(s)]
    assert fine and len(fine) < g.size()
    # Both coarse outcomes of the crisis are reached.
    assert g.ending_states("WAR") and g.ending_states("PEACE")


def test_lifted_crisis_step_equals_subgame_attractor():
    """Theory section 7: a coarse state ``s`` is in ``CPre_C(X)`` via the crisis iff
    ``iota(s)`` is in ``Attr_C^H(lambda^-1(X))``, the attractor of the sub-game solved on its
    own. Checked for the flattened attractor and safety kernel of every coalition."""
    fm = build_flat(hand_spec())
    g = explore(fm)
    sub = fm.crises[0].sub
    entries = {
        t: s
        for s in range(g.size())
        for t in g.succ[s]
        if not fm.is_fine(g.states[s]) and fm.is_fine(g.states[t])
    }
    assert entries
    for c in [set(c) for r in range(4) for c in itertools.combinations(["A", "B", "Nature"], r)]:
        win = attractor(g, c, g.ending_states("PEACE")).win
        kernel = safe(g, c, g.states_where("stable")).kernel
        for t, s in entries.items():
            coarse_s, _, iota = fm.split(g.states[t])
            h = explore(sub, initial=[iota])

            returns = {}  # terminal sub-game state id -> flat id of lambda(h, s)
            for i in range(h.size()):
                if h.terminal[i]:
                    state = (*coarse_s, 0, *h.states[i])
                    (move,) = itertools.product(*fm.available(state))
                    returns[i] = g.index[fm.step(state, move)]
            for goal in (win, kernel):
                preimage = {i for i, r in returns.items() if r in goal}
                assert (t in goal) == (h.initial[0] in attractor(h, c, preimage).win)


# -- the rules of the flattening ---------------------------------------------------------


def frozen_spec_models():
    """A coarse game with a delayed action, remember_last, a latch and a fairness counter
    around a one-day crisis."""
    coarse = Model("frozen", horizon=4)
    coarse.counter("arms", max=3, init=0)
    coarse.var("mood", levels=["calm", "tense"], init="calm")
    coarse.latch("arms_at_tension", of="arms", when=V.mood == "tense")
    A = coarse.actor("A", remember_last=True)
    B = coarse.actor("B")
    coarse.nature()
    A.action("build", effect=[Bump("arms", 1)], delay=2)
    A.action("crisis", guard=V.mood == "calm", effect=[])
    B.action("taunt", effect=[Set("mood", "tense")])
    coarse.fairness("answer", actor="B", trigger=V.arms >= 1, within=2, responses=["taunt"])
    fine = Model("day", horizon=1)
    fine.flag("hit", init=False)
    fa = fine.actor("A")
    fine.nature()
    fa.action("strike", effect=[Set("hit", True)])
    return coarse.compile(), fine.compile()


def test_entry_discards_other_moves_and_freezes_counters():
    cm, sub = frozen_spec_models()
    crisis = Crisis("A", "crisis", sub, lambda y: {}, lambda d, y: {"mood": "tense"})
    fm = flatten(cm, [crisis])
    s0 = cm.initial_states()[0]
    A = fm.actors[0]
    s1 = fm.step(s0, (A.action_index("build"), 0, 0))
    assert cm.state_dict(s1)["pending_A_build"] == "2"
    # A enters the crisis while B taunts: B's move is discarded and the tick holds.
    taunt = fm.actors[1].action_index("taunt")
    inside = fm.step(s1, (A.action_index("crisis"), taunt, 0))
    assert fm.is_fine(inside) and fm.coarse_part(inside) == s1
    assert inside == fm.step(s1, (A.action_index("crisis"), 0, 0))
    assert fm.state_dict(inside)["mood"] == "calm"
    # One fine step: the coarse part (pending counter, last action, fairness) is frozen.
    av = fm.available(inside)
    assert [len(a) for a in av] == [2, 1, 1]
    assert fm.actors[0].actions[av[0][1]].name == "strike"
    day1 = fm.step(inside, tuple(a[-1] for a in av))
    assert fm.coarse_part(day1) == s1 and fm.fine_ending_of(day1) == "HORIZON"
    assert not fm.is_terminal(day1) and fm.ending_of(day1) is None
    # The return: one forced move (the crisis actor plays the crisis), one coarse tick.
    (ret,) = itertools.product(*fm.available(day1))
    assert fm.format_move(ret) == "A.crisis, B.idle, Nature.none"
    back = fm.step(day1, ret)
    d = fm.state_dict(back)
    assert not fm.is_fine(back)
    assert d["tick"] == str(int(cm.state_dict(s1)["tick"]) + 1)
    assert d["pending_A_build"] == "1"  # resumed: decremented once across the crisis
    assert d["last_A"] == "crisis"
    assert d["mood"] == "tense" and d["arms_at_tension"] == "0"  # the latch fires on return
    g = explore(fm)
    assert all(fm.coarse_part(s) in g.index for s in g.states)


def test_fairness_counters_frozen_inside_crisis():
    cm, sub = frozen_spec_models()
    fm = flatten(cm, [Crisis("A", "crisis", sub, lambda y: {}, lambda d, y: {})])
    g = explore(fm)
    frozen = [cm.index[n] for n in ("fair_answer", "pending_A_build", "last_A", "tick")]
    entries = 0
    for sid, state in enumerate(g.states):
        for t in g.succ[sid]:
            nxt = g.states[t]
            if fm.is_fine(nxt):  # entering or inside the crisis: the coarse part holds
                entries += not fm.is_fine(state)
                assert all(nxt[i] == state[i] for i in frozen)
    assert entries > 1
    assert any(s[cm.index["fair_answer"]] for s in g.states if fm.is_fine(s))


def test_predicates_and_rendering_on_fine_states():
    spec = hand_spec()
    fm = build_flat(spec)
    g = explore(fm)
    fine = [sid for sid, s in enumerate(g.states) if fm.is_fine(s)]
    assert fine
    assert set(fine) <= g.states_where("stable") and set(fine) <= g.states_where("cool")
    assert not set(fine) & g.states_where("WAR")
    assert not any(g.terminal[s] for s in fine)
    # Ad-hoc expressions read the frozen coarse state, which is "high" on every crisis.
    assert set(fine) <= g.states_where(V.tension == "high")
    text = g.format_state(fine[0])
    assert text.startswith("[crisis crisis from {tick=") and "esc=" in text
    d = g.state_dict(fine[0])
    assert d["tension"] == "high" and "crisis.esc" in d and "crisis.tick" in d
    obs = fm.observe("B", g.states[fine[0]])
    assert obs[0] == "crisis" and obs != fm.observe("B", fm.coarse_part(g.states[fine[0]]))
    target = g.ending_states("WAR")
    trace = witness(g, g.initial[0], target)
    table = trace.render(g)
    assert "enter crisis crisis" in table and "return from crisis crisis" in table
    assert "crisis.esc:" in table and "ending: WAR" in table
    assert "[crisis " in table
    # Explicit initial states are coarse states.
    g2 = explore(fm, initial=[g.states[g.initial[0]]])
    assert g2.size() == g.size()
    assert fm.budget()["crises"] == 1


# -- 2. controllability through the crisis ------------------------------------------------


def _by_outcome(day, year):
    return {"status": "settled" if day["outcome"] == "good" else "broken"}


def standoff(fine_model, exit_map=_by_outcome):
    """A coarse game in which A must enter the crisis at tick 0 (A has no idle) and the
    crisis alone decides between SETTLED and BROKEN."""
    coarse = Model("standoff", horizon=2)
    coarse.var("status", levels=["open", "settled", "broken"], init="open")
    A = coarse.actor("A", idle=False)
    coarse.actor("B")
    coarse.nature()
    A.action("crisis", guard=V.status == "open", effect=[])
    A.action("wait", guard=V.status != "open", effect=[])
    coarse.ending("SETTLED", V.status == "settled")
    coarse.ending("BROKEN", V.status == "broken")
    crisis = Crisis("A", "crisis", fine_model.compile(), lambda y: {}, exit_map)
    fm = flatten(coarse.compile(), [crisis])
    return fm, explore(fm)


def status_of(g, coalition, ending):
    r = contested(g, coalition, g.ending_states(ending), "reach")
    (s,) = g.initial
    return "forced" if s in r.forced else "blocked" if s in r.blocked else "contested"


def test_subgame_controlled_by_one_side_lifts_to_coarse_forcing():
    fine = Model("decide", horizon=2)
    fine.var("outcome", levels=["bad", "good"], init="bad")
    A = fine.actor("A")
    fine.actor("B")
    fine.nature()
    A.action("settle", effect=[Set("outcome", "good")])
    A.action("rupture", effect=[Set("outcome", "bad")])
    fm, g = standoff(fine)
    assert status_of(g, {"A"}, "SETTLED") == "forced"
    assert status_of(g, {"A"}, "BROKEN") == "forced"
    assert status_of(g, {"B", "Nature"}, "SETTLED") == "blocked"
    assert status_of(g, {"B", "Nature"}, "BROKEN") == "blocked"
    # The rank counts transitions: entry, two fine steps, return.
    (s,) = g.initial
    assert attractor(g, {"A"}, g.ending_states("SETTLED")).rank[s] == 4


def test_subgame_neither_side_controls_is_contested_at_the_coarse_level():
    """Matching pennies inside the crisis: A wants to match, B to differ."""
    fine = Model("pennies", horizon=1)
    fine.var("a", levels=["heads", "tails"], init="heads")
    fine.var("b", levels=["heads", "tails"], init="heads")
    A = fine.actor("A", idle=False)
    B = fine.actor("B", idle=False)
    fine.nature()
    A.action("heads", effect=[Set("a", "heads")])
    A.action("tails", effect=[Set("a", "tails")])
    B.action("heads", effect=[Set("b", "heads")])
    B.action("tails", effect=[Set("b", "tails")])

    def exit_map(day, year):
        return {"status": "settled" if day["a"] == day["b"] else "broken"}

    fm, g = standoff(fine, exit_map)
    for c in ({"A"}, {"B"}, {"A", "Nature"}, {"B", "Nature"}):
        assert status_of(g, c, "SETTLED") == "contested"
        assert status_of(g, c, "BROKEN") == "contested"
    assert status_of(g, {"A", "B"}, "SETTLED") == "forced"


# -- 3. nondeterministic exit -------------------------------------------------------------


def test_nature_inside_the_crisis_gives_several_coarse_outcomes():
    fine = Model("weather", horizon=1)
    fine.var("outcome", levels=["bad", "good"], init="bad")
    fine.actor("A")
    N = fine.nature()
    N.event("luck", effect=[Set("outcome", "good")])
    fm, g = standoff(fine)
    (s,) = g.initial
    entered = {t for t in g.succ[s]}
    assert len(entered) == 1  # every joint move with the crisis enters the same state
    returns = {
        tuple(fm.state_dict(g.states[t]).items())
        for sid in range(g.size())
        if fm.is_fine(g.states[sid])
        for t in g.succ[sid]
        if not fm.is_fine(g.states[t])
    }
    assert {dict(r)["status"] for r in returns} == {"settled", "broken"}
    for ending in ("SETTLED", "BROKEN"):
        assert status_of(g, {"A"}, ending) == "blocked"
        assert status_of(g, {"Nature"}, ending) == "forced"
        assert status_of(g, {"A", "B", "Nature"}, ending) == "forced"


# -- 4. errors ------------------------------------------------------------------------------


def two_crisis_models():
    coarse = Model("two", horizon=2)
    coarse.flag("done", init=False)
    A = coarse.actor("A")
    B = coarse.actor("B")
    coarse.nature()
    A.action("c1", effect=[])
    B.action("c2", effect=[])
    A.action("loud", effect=[Set("done", True)])
    fine = Model("f", horizon=1)
    fine.var("x", levels=["lo", "hi"], init=None)
    fine.var("y", levels=["lo", "hi"], init="lo")
    fine.actor("A")
    fine.nature()
    return coarse, fine


def test_two_crises_in_one_joint_move_is_an_error():
    coarse, fine = two_crisis_models()
    sub = fine.compile()
    crises = [
        Crisis("A", "c1", sub, lambda y: {"x": "lo"}, lambda d, y: {}),
        Crisis("B", "c2", sub, lambda y: {"x": "hi"}, lambda d, y: {}),
    ]
    fm = flatten(coarse.compile(), crises)
    with pytest.raises(ModelError, match=r"crises 'c1', 'c2' are entered together.*at most one"):
        explore(fm)


@pytest.mark.parametrize(
    ("entry", "exit_map", "message"),
    [
        (lambda y: {"x": "lo", "z": "lo"}, lambda d, y: {}, r"crisis 'c1'.*entry map names 'z'"),
        (lambda y: {"x": "lo", "tick": 0}, lambda d, y: {}, r"entry map names 'tick'"),
        (lambda y: {"x": "mid"}, lambda d, y: {}, r"entry map gives x='mid'.*levels: lo, hi"),
        (lambda y: {"y": "hi"}, lambda d, y: {}, r"crisis 'c1'.*does not fix 'x'.*sweeps"),
        (lambda y: {"x": "lo"}, lambda d, y: {"nope": True}, r"exit map names 'nope'"),
        (lambda y: {"x": "lo"}, lambda d, y: {"done": "maybe"}, r"exit map gives done='maybe'"),
        (lambda y: {"x": "lo"}, lambda d, y: {"done": 3}, r"exit map gives done=3"),
        (lambda y: ["x"], lambda d, y: {}, r"entry map must return a mapping"),
    ],
)
def test_map_errors_name_the_crisis(entry, exit_map, message):
    coarse, fine = two_crisis_models()
    fm = flatten(coarse.compile(), [Crisis("A", "c1", fine.compile(), entry, exit_map)])
    with pytest.raises(ModelError, match=message):
        explore(fm)


def test_maps_accept_state_dict_strings_and_python_values():
    coarse, fine = two_crisis_models()
    for value in (True, "True"):
        fm = flatten(
            coarse.compile(),
            [
                Crisis(
                    "A", "c1", fine.compile(), lambda y: {"x": "hi"}, lambda d, y: {"done": value}
                )
            ],
        )
        g = explore(fm)
        assert any(fm.state_dict(s)["done"] == "True" for s in g.states if not fm.is_fine(s))


def test_flatten_errors():
    coarse, fine = two_crisis_models()
    cm, sub = coarse.compile(), fine.compile()

    def crisis(actor="A", action="c1", sub=sub, **kw):
        return Crisis(actor, action, sub, lambda y: {"x": "lo"}, lambda d, y: {}, **kw)

    other = Model("other", horizon=1)
    other.actor("C")
    other.nature()
    with pytest.raises(ModelError, match=r"actor 'C' of the sub-game 'other' is not an actor"):
        flatten(cm, [crisis(sub=other.compile())])
    untimed = Model("untimed", horizon=None)
    untimed.nature()
    with pytest.raises(ModelError, match=r"sub-game 'untimed' must be timed"):
        flatten(cm, [crisis(sub=untimed.compile())])
    with pytest.raises(ModelError, match=r"A.loud must have no effect"):
        flatten(cm, [crisis(action="loud")])
    with pytest.raises(ModelError, match=r"A.idle is not a declared action"):
        flatten(cm, [crisis(action="idle")])
    with pytest.raises(ModelError, match=r"A.nothing is not a declared action"):
        flatten(cm, [crisis(action="nothing")])
    with pytest.raises(ModelError, match=r"'Z' is not an actor"):
        flatten(cm, [crisis(actor="Z")])
    with pytest.raises(ModelError, match=r"two crises share this name"):
        flatten(cm, [crisis(), crisis(actor="B", action="c2", name="c1")])
    with pytest.raises(ModelError, match=r"already enters another crisis"):
        flatten(cm, [crisis(), crisis(name="again")])


def test_exit_may_not_lower_a_monotone_variable():
    coarse = Model("mono", horizon=2)
    coarse.var("level", levels=["a", "b"], init="b", monotone=True)
    A = coarse.actor("A")
    coarse.nature()
    A.action("c", effect=[])
    fine = Model("f", horizon=1)
    fine.nature()
    fm = flatten(
        coarse.compile(),
        [Crisis("A", "c", fine.compile(), lambda y: {}, lambda d, y: {"level": "a"})],
    )
    with pytest.raises(ModelError, match=r"lowers monotone variable 'level'"):
        explore(fm)


def test_actor_without_idle_waits_during_a_crisis():
    coarse = Model("noidle", horizon=2)
    coarse.flag("f", init=False)
    A = coarse.actor("A")
    B = coarse.actor("B", idle=False)
    coarse.nature()
    A.action("c", effect=[])
    B.action("push", effect=[Set("f", True)])
    fine = Model("day", horizon=1)
    fine.actor("A")
    fine.nature()
    fm = flatten(
        coarse.compile(), [Crisis("A", "c", fine.compile(), lambda y: {}, lambda d, y: {})]
    )
    g = explore(fm)
    fine_states = [sid for sid, s in enumerate(g.states) if fm.is_fine(s)]
    assert fine_states
    for sid in fine_states:
        for jm in g.moves[sid]:
            assert fm.actors[1].actions[jm[1]].name == "idle"


# -- 5. random cross-check ----------------------------------------------------------------

OPS = ("==", "!=", "<", "<=", ">", ">=")


def _atom(rnd, variables):
    name, levels, _ = rnd.choice(variables)
    ref, level = V[name], rnd.choice(levels)
    return {
        "==": ref == level,
        "!=": ref != level,
        "<": ref < level,
        "<=": ref <= level,
        ">": ref > level,
        ">=": ref >= level,
    }[rnd.choice(OPS)]


def _pred(rnd, variables):
    kind = rnd.choice((0, 1, 1, 2))
    if kind == 0:
        return TRUE
    if kind == 1:
        return _atom(rnd, variables)
    return _atom(rnd, variables) & _atom(rnd, variables)


def _effects(rnd, variables, owned):
    out, used = [], set()
    for _ in range(rnd.choice((1, 1, 2))):
        name, levels, _ = rnd.choice(variables)
        if name in owned and name not in used and rnd.random() < 0.5:
            out.append(Set(name, rnd.choice(levels)))
            used.add(name)
        else:
            out.append(Bump(name, rnd.choice((-1, 1))))
    return out


def _endings(rnd, variables, prefix):
    out, first = {}, None
    for e in range(rnd.choice((0, 1, 1, 2))):
        pred = _atom(rnd, variables) & _atom(rnd, variables)
        out[f"{prefix}{e}"] = pred if first is None else pred & ~first
        first = pred if first is None else first
    return out


def random_spec(seed) -> Spec:
    rnd = random.Random(seed)

    def variables(prefix, count, sweep):
        out = []
        for i in range(count):
            levels = [f"l{k}" for k in range(rnd.choice((2, 3)))]
            init = None if sweep and rnd.random() < 0.2 else rnd.choice(levels)
            out.append((f"{prefix}{i}", levels, init))
        return out

    cvars = variables("c", rnd.randint(2, 3), True)
    fvars = variables("f", rnd.randint(1, 2), False)
    actors = ["A0", "A1"][: rnd.randint(1, 2)]
    fine_actors = ["A0"] + [a for a in actors[1:] if rnd.random() < 0.6]
    crisis_guard = _pred(rnd, cvars)
    players = [*actors, "Nature"]
    owner = {name: rnd.choice(players) for name, _, _ in cvars}
    coarse_actions = []
    for a in players:
        owned = {v for v, o in owner.items() if o == a}
        for k in range(rnd.randint(0, 2)):
            guard = _pred(rnd, cvars)
            if a != "A0":
                guard = guard & ~crisis_guard
            coarse_actions.append((a, f"a{k}", guard, _effects(rnd, cvars, owned)))
    fine_players = [*fine_actors, "Nature"]
    fowner = {name: rnd.choice(fine_players) for name, _, _ in fvars}
    fine_actions = []
    for a in fine_players:
        owned = {v for v, o in fowner.items() if o == a}
        for k in range(rnd.randint(1, 2)):
            fine_actions.append((a, f"b{k}", _pred(rnd, fvars), _effects(rnd, fvars, owned)))
    entry = {}
    for name, levels, _ in fvars:
        r = rnd.random()
        if r < 0.5:
            entry[name] = ("copy", rnd.choice(cvars)[0])
        elif r < 0.8:
            entry[name] = ("const", rnd.choice(levels))
    exits = []
    for _ in range(rnd.randint(1, 3)):
        name, levels, _ = rnd.choice(cvars)
        cond = TRUE if rnd.random() < 0.3 else _atom(rnd, fvars)
        value = (
            ("copy", rnd.choice(fvars)[0]) if rnd.random() < 0.5 else ("const", rnd.choice(levels))
        )
        exits.append((cond, name, value))
    return Spec(
        horizon=rnd.randint(1, 3),
        fine_horizon=rnd.randint(1, 2),
        coarse_vars=cvars,
        fine_vars=fvars,
        actors=actors,
        fine_actors=fine_actors,
        crisis_actor="A0",
        crisis_guard=crisis_guard,
        coarse_actions=coarse_actions,
        fine_actions=fine_actions,
        entry=entry,
        exit=exits,
        coarse_endings=_endings(rnd, cvars, "E"),
        fine_endings=_endings(rnd, fvars, "F"),
        invariants={"inv": _atom(rnd, cvars)},
    )


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(st.integers(0, 2**32 - 1))
def test_random_flattening_matches_inlined(seed):
    compare(random_spec(seed))


def test_random_flattening_sweep():
    entered = 0
    for seed in range(300):
        fm, g = compare(random_spec(seed))
        entered += any(fm.is_fine(s) for s in g.states)
    assert entered > 100  # the sweep does exercise crises
