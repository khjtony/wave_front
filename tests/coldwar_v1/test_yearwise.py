"""Validation of the layered lifting of docs/cw_v1_decisions.md D7 (tests/coldwar_v1/layered.py),
written before first sight and computed without any registered claim's quantity.

The layered lifting computes kernels, attractors and distances of a flattened game (spec
section 14) on the coarse BDD encoding, one tick layer at a time, with each sub-game explored
once; its explicit form (``Window``) does the same on an explicit coarse graph for a window
ending one tick after a crisis. Each is checked state by state against the explicit engine
on the flattened game itself:

1. random coarse games with a crisis sub-game (the generator of tests/engine/test_multires.py)
   and its hand-built game: kernel and attractor membership of every coarse state, lifted
   membership of every fine state, strategy moves, and the fewest transitions to a target and
   out of a kernel, for every coalition;
2. a small synthetic game with two crises at different ticks, an entry map reading a coarse
   variable, exits setting several variables, a delayed action and a restricted game;
3. the toy standoff (models/toy/crisis.py);
4. the explicit form on random games whose crisis has one occasion, cut one tick after it;
5. cw_v1 itself, on predicates and targets that no V claim reads (``esc == peace``,
   ``~us_began_war``, ``esc >= crisis``, ``esc == crisis``): the flattened game from the 1983
   hindsight state to the horizon (Able Archer inside), the explicit form against the
   flattened game cut at 1963 from the 1961 hindsight state (Cuba inside), and (slow) the
   composite engine of D7 (explicit to 1984, symbolic beyond) from the 1975 hindsight state;
   and the conditions the lifting relies on (exit maps reading only the fine state, entry maps
   constant except Able Archer's, no two crises at one tick, no exit variable written by a
   delayed effect).

No kernel of ``balance_core``, ``no_war_core``, ``balance_tri`` or any predicate a V claim
reads is computed here, from any state.
"""

from __future__ import annotations

import itertools
import random

import pytest

from models.toy import crisis as toy
from tests.coldwar.common import Cut, Forbid, bfs_distance
from tests.coldwar_v1.common import encoding, flat_of, hindsight, kernel
from tests.coldwar_v1.layered import ENTRY_READS, Lift, Window, dag_distance
from tests.engine.test_multires import build_flat, hand_spec, random_spec
from wavefront.engine import Crisis, attractor, explore, flatten, safe
from wavefront.model import Bump, Model, Set, V
from wavefront.symbolic import encode
from wavefront.symbolic.bdd import FALSE

SRC = "synthetic validation game: "


def coalitions(players):
    return [c for r in range(len(players) + 1) for c in itertools.combinations(players, r)]


def crisis_of(lift, fm, state):
    return next(c for c in lift.crises if c.k == state[fm.n])


def compare_layered(fm, lift, g, players, invariants, targets, distances=True, moves=True):
    """Every fixpoint of the layered lifting against the explicit engine on ``g`` (the
    flattened game explored from its initial states), on every state of ``g``; with
    ``moves``, a strategy move exists in every non-terminal state of a kernel or attractor
    outside the target."""
    cm = fm.coarse
    enc = lift.enc
    coarse = [i for i, s in enumerate(g.states) if not fm.is_fine(s)]
    fine = [i for i, s in enumerate(g.states) if fm.is_fine(s)]
    checked = 0
    for inv in invariants:
        phi = {
            i for i in range(g.size()) if fm.is_fine(g.states[i]) or cm.evaluate(inv, g.states[i])
        }
        for c in coalitions(players):
            k = safe(g, list(c), phi).kernel
            lk = lift.kernel(c, enc.predicate(inv))
            for i in coarse:
                assert lk.contains(g.states[i]) == (i in k), (inv, c, g.format_state(i))
                if moves and i in k and not g.terminal[i]:
                    assert lift.strategy_move(lk, g.states[i]) is not None
            for i in fine:
                s, _, h = fm.split(g.states[i])
                crisis = crisis_of(lift, fm, g.states[i])
                ids = lift.lifted_ids(crisis, s, c, lk.contains)
                entry = lift.entry_of(crisis, s)
                assert (entry.g.index[h] in ids) == (i in k), ("fine", inv, c)
            if distances:
                d = lift.distance(None, kernel=lk)
                out = set(range(g.size())) - k
                for i in coarse:
                    assert d.rank(g.states[i]) == bfs_distance(g, i, out), (inv, c)
            checked += 1
    for name, expr in targets.items():
        tgt = {i for i in coarse if cm.evaluate(expr, g.states[i])}
        for c in coalitions(players):
            a = attractor(g, list(c), tgt).win
            la = lift.attractor(c, enc.predicate(expr))
            for i in coarse:
                assert la.contains(g.states[i]) == (i in a), (name, c, g.format_state(i))
                if moves and i in a and i not in tgt:
                    assert lift.strategy_move(la, g.states[i]) is not None
            checked += 1
        if distances:
            d = lift.distance(enc.predicate(expr))
            for i in coarse:
                assert d.rank(g.states[i]) == bfs_distance(g, i, tgt), (name, g.format_state(i))
    return checked


def random_case(spec):
    fm = build_flat(spec)
    enc = encode(fm.coarse)
    reads = tuple(x for kind, x in spec.entry.values() if kind == "copy")
    return fm, Lift(fm, enc, entry_reads={"crisis": reads})


# -- 1. random games and the hand-built game -----------------------------------------------
def test_layered_lifting_on_the_hand_built_game():
    spec = hand_spec()
    fm, lift = random_case(spec)
    g = explore(fm)
    targets = {e: _ending(e) for e in spec.coarse_endings}
    assert compare_layered(fm, lift, g, ["A", "B", "Nature"], spec.invariants, targets) > 0


def _ending(name):
    return {"WAR": V.status == "broken", "PEACE": V.status == "settled"}[name]


@pytest.mark.parametrize("block", range(4))
def test_layered_lifting_on_random_flattened_games(block):
    entered = 0
    for seed in range(block * 30, block * 30 + 30):
        spec = random_spec(seed)
        fm, lift = random_case(spec)
        g = explore(fm, max_states=20_000)
        targets = dict(spec.coarse_endings)
        compare_layered(fm, lift, g, [*spec.actors, "Nature"], spec.invariants, targets)
        entered += any(fm.is_fine(s) for s in g.states)
    assert entered >= 5  # the sweep enters crises


# -- 2. a synthetic game with two crises ---------------------------------------------------
def two_crisis_game():
    """A coarse game of four years with two crisis sub-games at different ticks: ``A.press``
    at tick 1 (its entry reads ``arms``; its exits set ``status`` and ``alert``) and
    ``B.standoff`` at tick 2 when tension is high (its exit sets ``tension``); ``B.build``
    has a delayed effect on ``arms``. Not a model of anything."""
    c = Model("two_crises", horizon=4)
    c.var("tension", levels=["low", "mid", "high"], init=None)
    c.var("status", levels=["open", "settled", "broken"], init="open")
    c.counter("arms", max=2, init=0)
    c.flag("alert", init=False)
    a, b, n = c.actor("A"), c.actor("B"), c.nature()
    a.action("provoke", guard=V.tension < "high", effect=Bump("tension", 1), source=SRC + "x")
    a.action("press", guard=(V.tick == 1) & (V.status == "open"), effect=[], source=SRC + "x")
    b.action("build", guard=V.arms < 2, effect=Bump("arms", 1), delay=1, source=SRC + "x")
    b.action("calm", guard=V.tension > "low", effect=Bump("tension", -1), source=SRC + "x")
    b.action(
        "standoff",
        guard=(V.tick == 2) & (V.tension == "high"),
        effect=[],
        source=SRC + "x",
    )
    n.event("incident", guard=V.tension == "high", effect=Set("alert", True), source=SRC + "x")
    c.invariant("stable", V.status != "broken")
    c.invariant("quiet", ~V.alert)
    c.ending("WAR", V.status == "broken")

    f1 = Model("press_days", horizon=2)
    f1.var("esc", levels=["low", "high", "brink"], init="low")
    f1.flag("talks", init=False)
    fa, fb, fn = f1.actor("A"), f1.actor("B"), f1.nature()
    fa.action("escalate", effect=Bump("esc", 1), source=SRC + "x")
    fa.action("talk", guard=~V.talks, effect=Set("talks", True), source=SRC + "x")
    fb.action("escalate", effect=Bump("esc", 1), source=SRC + "x")
    fb.action("calm", effect=Bump("esc", -1), source=SRC + "x")
    fn.event("slip", guard=V.esc == "high", effect=Bump("esc", 1), source=SRC + "x")
    f1.ending("BRINK", V.esc == "brink")

    f2 = Model("standoff_days", horizon=2)
    f2.var("pressure", levels=["none", "some", "full"], init="some")
    gb, gn = f2.actor("B"), f2.nature()
    gb.action("push", effect=Bump("pressure", 1), source=SRC + "x")
    gb.action("ease", effect=Bump("pressure", -1), source=SRC + "x")
    gn.event("rumour", guard=V.pressure == "some", effect=Bump("pressure", 1), source=SRC + "x")

    def entry1(year):
        return {"esc": "high" if year["arms"] == "2" else "low"}

    def exit1(day, year):
        if day["esc"] == "brink":
            return {"status": "broken", "alert": True}
        if day["talks"] == "True":
            return {"status": "settled"}
        return {}

    def exit2(day, year):
        return {"tension": {"none": "low", "some": "mid", "full": "high"}[day["pressure"]]}

    crises = [
        Crisis("A", "press", f1.compile(), entry1, exit1, name="press"),
        Crisis("B", "standoff", f2.compile(), lambda y: {}, exit2, name="standoff"),
    ]
    return flatten(c.compile(), crises)


TWO_TARGETS = {"WAR": V.status == "broken", "alerted": V.alert, "calm": V.tension == "low"}


def test_layered_lifting_on_a_two_crisis_game():
    fm = two_crisis_game()
    lift = Lift(fm, encode(fm.coarse), entry_reads={"press": ("arms",)})
    assert [len(c.entries) for c in lift.crises] == [3, 1]
    g = explore(fm)
    assert {fm.split(s)[1].label for s in g.states if fm.is_fine(s)} == {"press", "standoff"}
    n = compare_layered(fm, lift, g, ["A", "B", "Nature"], ["stable", "quiet"], TWO_TARGETS)
    assert n > 0


def test_layered_lifting_on_a_restricted_two_crisis_game():
    fm = two_crisis_game()
    pairs = {("A", "provoke"), ("B", "escalate"), ("Nature", "rumour")}
    lift = Lift(fm, encode(fm.coarse), entry_reads={"press": ("arms",)}, forbid=pairs)
    g = explore(Forbid(fm, sorted(pairs)))
    n = compare_layered(fm, lift, g, ["A", "B", "Nature"], ["stable", "quiet"], TWO_TARGETS)
    assert n > 0


# -- 3. the toy standoff -------------------------------------------------------------------
def test_layered_lifting_on_the_toy_standoff():
    fm = toy.flat()
    lift = Lift(fm, encode(fm.coarse), entry_reads={"standoff_crisis": ("arms",)})
    g = explore(fm)
    targets = {"WAR": V.status == "broken", "DETENTE": V.status == "settled"}
    assert compare_layered(fm, lift, g, ["EAST", "WEST", "Nature"], ["no_war"], targets) > 0


# -- 4. the explicit form ------------------------------------------------------------------
def test_explicit_form_on_random_games_with_one_occasion():
    checked = 0
    for seed in range(200):
        spec = random_spec(seed)
        if spec.horizon < 2:
            continue
        crisis_tick = random.Random(seed).randint(1, spec.horizon - 1)
        spec.crisis_guard = spec.crisis_guard & (V.tick == crisis_tick)
        fm, lift = random_case(spec)
        cut = crisis_tick + 1
        g = explore(Cut(fm, cut), max_states=20_000)
        starts = [g.states[i] for i in g.initial]
        w = Window(lift, starts, cut)
        cm = fm.coarse
        for inv in spec.invariants:

            def holds(s, inv=inv):
                return bool(cm.evaluate(inv, s))

            phi = {i for i, s in enumerate(g.states) if fm.is_fine(s) or holds(s)}
            for c in coalitions([*spec.actors, "Nature"]):
                k = safe(g, list(c), phi).kernel
                kw = w.kernel(c, holds)
                for i, s in enumerate(w.g.states):
                    assert (g.index[s] in k) == (i in kw), (seed, inv, c)
                out = set(range(g.size())) - k
                for s in starts:
                    d = w.distance(s, holds, kernel=kw, coalition=c)
                    assert d == bfs_distance(g, g.index[s], out), (seed, inv, c)
                checked += 1
        for name in spec.coarse_endings:
            tgt = g.ending_states(name)
            for s in starts:
                d = w.distance(s, lambda r, name=name: cm.ending_of(r) == name)
                assert d == bfs_distance(g, g.index[s], tgt), (seed, name)
            dd = dag_distance(g, fm, tgt, None)
            for s in starts:
                assert dd[g.index[s]] == bfs_distance(g, g.index[s], tgt), (seed, name)
    assert checked > 50


# -- 5. cw_v1, on predicates no claim reads ------------------------------------------------
MADE_UP = {"peace": V.esc == "peace", "no_us_war": ~V.us_began_war}
MADE_UP_TARGETS = {"crisis_or_more": V.esc >= "crisis"}


@pytest.mark.parametrize("build", [{}, {"prc_principal": False}, {"us_crisis_options": False}])
def test_conditions_of_the_lifting_hold_on_cw_v1(build):
    """The exits read only the fine state, the entries are constant except Able Archer's,
    no two crises share a tick, no exit variable is written by a delayed effect (checked
    when the lift is built), and the crisis ticks are 1948, 1962, 1969, 1973 and 1983."""
    for aims in ("status_quo", "opportunist"):
        fm = flat_of(aims, **build)
        lift = Lift(fm, encoding(aims, **build))
        cm = fm.coarse
        years = (1947, 1962, 1975, 1990)
        dicts = [dict(cm.state_dict(hindsight(y, aims, **build))) for y in years]
        ticks = {}
        for crisis in lift.crises:
            c = fm._compiled[crisis.k].crisis
            reads = ENTRY_READS.get(crisis.label, ())
            assert len(crisis.entries) == max(1, 3 ** len(reads))
            for entry in crisis.entries:
                g = entry.g
                for i, e in entry.exit_of.items():
                    day = dict(c.sub.state_dict(g.states[i]))
                    assert len({tuple(sorted(c.exit(day, y).items())) for y in dicts}) == 1
            if not reads:
                assert len({tuple(sorted(c.entry(y).items())) for y in dicts}) == 1
            enc = lift.enc
            ticks[crisis.label] = [
                t for t in range(len(lift.at)) if enc.mgr.AND(crisis.avail, lift.at[t]) != FALSE
            ]
        assert ticks == {
            "berlin_1948": [1],
            "cuba_1962": [15],
            "sino_soviet_1969": [22],
            "alert_1973": [26],
            "able_archer_1983": [36],
        }


@pytest.mark.parametrize("aims", ["status_quo", "opportunist"])
def test_cw_v1_layered_against_the_flattened_game_from_1983(aims):
    """Every state of the flattened game from the 1983 hindsight state to the horizon (Able
    Archer inside), on predicates and targets no claim reads."""
    fm = flat_of(aims)
    lift = Lift(fm, encoding(aims))
    g = explore(fm, initial=[hindsight(1983, aims)], max_states=100_000)
    assert any(fm.is_fine(s) for s in g.states)
    players = ["USA", "USSR", "Nature"]
    invariants = list(MADE_UP.values())
    n = compare_layered(fm, lift, g, players, invariants, MADE_UP_TARGETS, False, False)
    assert n > 0
    # distances for two coalitions (the whole-domain distance layers are the slow part)
    cm = fm.coarse
    for c in (("USA",), ("USA", "USSR")):
        inv = MADE_UP["peace"]
        phi = {
            i for i in range(g.size()) if fm.is_fine(g.states[i]) or cm.evaluate(inv, g.states[i])
        }
        k = safe(g, list(c), phi).kernel
        d = lift.distance(None, kernel=lift.kernel(c, lift.enc.predicate(inv)))
        out = set(range(g.size())) - k
        for i, s in enumerate(g.states):
            if not fm.is_fine(s):
                assert d.rank(s) == bfs_distance(g, i, out), (c, g.format_state(i))
    tgt_expr = V.esc == "crisis"
    tgt = {i for i, s in enumerate(g.states) if not fm.is_fine(s) and cm.evaluate(tgt_expr, s)}
    d = lift.distance(lift.enc.predicate(tgt_expr))
    for i, s in enumerate(g.states):
        if not fm.is_fine(s):
            assert d.rank(s) == bfs_distance(g, i, tgt)


def test_cw_v1_explicit_form_against_the_flattened_game_cut_at_1963():
    """The explicit form (R V6) from the 1961 hindsight state, cut at 1 January 1963 with
    the Cuba sub-game inside, against the flattened game cut there, on predicates no claim
    reads."""
    aims = "opportunist"
    fm = flat_of(aims)
    cm = fm.coarse
    lift = Lift(fm, encoding(aims))
    s0 = hindsight(1961, aims)
    g = explore(Cut(fm, 16), initial=[s0], max_states=1_000_000)
    w = Window(lift, [s0], 16)
    assert w.crisis_of  # Cuba is inside the window
    for inv in MADE_UP.values():

        def holds(s, inv=inv):
            return bool(cm.evaluate(inv, s))

        phi = {i for i, s in enumerate(g.states) if fm.is_fine(s) or holds(s)}
        for c in coalitions(["USA", "USSR"]):
            k = safe(g, list(c), phi).kernel
            kw = w.kernel(c, holds)
            for i, s in enumerate(w.g.states):
                assert (g.index[s] in k) == (i in kw)
            out = set(range(g.size())) - k
            assert w.distance(s0, holds, kernel=kw, coalition=c) == bfs_distance(
                g, g.index[s0], out
            )
    for expr in (V.esc == "peace", V.esc == "conventional", V.us_began_war):
        tgt = {i for i, s in enumerate(g.states) if not fm.is_fine(s) and cm.evaluate(expr, s)}
        d = w.distance(s0, lambda r, expr=expr: bool(cm.evaluate(expr, r)))
        assert d == bfs_distance(g, g.index[s0], tgt)


@pytest.mark.slow
@pytest.mark.parametrize("aims", ["status_quo", "opportunist"])
def test_cw_v1_layered_against_the_composite_engine_from_1975(aims):
    """The composite engine of D7 (the flattened game explored from the 1975 hindsight state
    to 1 January 1984, the cut states valued by the symbolic coarse kernel) against the
    layered lifting, state by state, on a predicate no claim reads; and the composite
    distance (explicit to the cut, the symbolic all-actor attractor's rank beyond it)."""
    from wavefront.symbolic import attractor as sattractor

    fm = flat_of(aims)
    cm = fm.coarse
    enc = encoding(aims)
    lift = Lift(fm, enc)
    g = explore(Cut(fm, 37), initial=[hindsight(1975, aims)], max_states=3_000_000)
    inv = MADE_UP["peace"]
    phi = {i for i in range(g.size()) if fm.is_fine(g.states[i]) or cm.evaluate(inv, g.states[i])}
    for c in (("USA",), ("USSR",), ("USA", "USSR")):
        sym = kernel(aims, c, inv)
        keep = {i for i in phi if g.ending[i] != "CUT" or sym.contains(g.states[i])}
        k = safe(g, list(c), keep).kernel
        lk = lift.kernel(c, enc.predicate(inv))
        for i, s in enumerate(g.states):
            if fm.is_fine(s):
                crisis = crisis_of(lift, fm, s)
                ids = lift.lifted_ids(crisis, s[: fm.n], c, lk.contains)
                h = fm.split(s)[2]
                assert (lift.entry_of(crisis, s[: fm.n]).g.index[h] in ids) == (i in k)
            else:
                assert lk.contains(s) == (i in k), (c, g.format_state(i))
    expr = V.esc == "crisis"
    target = enc.predicate(expr)
    everyone = ["USA", "USSR", "PRC", "Nature"]
    beyond = sattractor(enc, everyone, target)
    tgt = {i for i, s in enumerate(g.states) if not fm.is_fine(s) and cm.evaluate(expr, s)}
    dd = dag_distance(g, fm, tgt, beyond.rank)
    d = lift.distance(target)
    for i, s in enumerate(g.states):
        if not fm.is_fine(s):
            assert dd[i] == d.rank(s), g.format_state(i)
