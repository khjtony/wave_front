"""K4: registered 2026-10-15 in docs/crisis_1939_testbed.md section 3.

The summer-1939 crisis sub-game of WW2 v1 (3-day ticks, 5 July to 3 September 1939), entered
from the 1939Q3 state. Do not edit the claim text without a changelog entry in that
document.

Reading (docs/crisis_1939_decisions.md R4). Start: the realized state at tick 17 (the start
of 25 August), with ``belief_GER`` at each of its three levels; under ``deterred`` and
without a profile; reduced build.

- (a) the start state is in ``attractor({GER}, launched)`` with rank <= 3, in every row;
- (b) the start state is outside ``safe({WEST, USSR, Nature}, no_attack)`` in every row;
- (c) on the realized path ``belief_GER`` is ``uncertain`` at tick 17 and ``will_fight`` at
  tick 18, WEST's realized move of tick 17 being ``sign_treaty``;
- (d) GER's realized move of tick 17 is ``cancel_attack``, whose source cites Mussolini's
  letter and the treaty, beside WEST's ``sign_treaty`` and Nature's ``italy_declines``;
- (e) and (f) the realized state at tick 18 (after the halt) is in GER's attractor of
  ``launched`` with rank <= 2 in every row, and the realized attack is two ticks after the
  first feasible one;
- (g) the engine's shortest trace (``witness``) from the tick-17 state to a launched state
  contains ``cancel_attack`` followed by ``attack_poland``.

Engine: the explicit engine (``attractor``, ``safe``, ``witness``).
"""

import functools
import time

import pytest

from models.ww2.crises import summer_1939 as crisis
from tests.ww2.crisis_1939 import common
from wavefront.engine import attractor, safe, witness
from wavefront.model import V

CLAIM = {
    "id": "K4",
    "from_state": "tick 17 (25 August)",
    "claim": (
        "after the pact, no coalition blocks the attack under any belief: the Anglo-Polish "
        "treaty of 25 August and Chamberlain's letter of 22 August flip `belief_GER` to "
        "`will_fight` and the attack is cancelled for a documented reason (Italy's "
        "non-readiness and the treaty), but it is re-ordered and launched by 1 September "
        "whatever WEST does; the cancellation of 25 August delays the attack by at most two "
        "ticks"
    ),
    "expected": (
        "from the state of 25 August the attack is forced by Germany by tick 19 under every "
        "belief; the shortest trace shows the cancellation and the re-order"
    ),
    "sources": (
        "DGFP Series D vol. VII (the order of 25 August, 15:02; the cancellation; the order "
        "of 31 August); Halder's diary 25 to 31 August; Ciano's diary"
    ),
}

PROFILES = ["deterred", None]


@functools.lru_cache(maxsize=None)
def analysis(profile) -> dict:
    t0 = time.time()
    cm = common.compiled(inert=False, profile=profile)
    path = common.realized_states(cm)
    s17 = {b: common.with_level(cm, path[17], "belief_GER", b) for b in common.BELIEFS}
    s18 = {b: common.with_level(cm, path[18], "belief_GER", b) for b in common.BELIEFS}
    g = common.graph(cm, [*s17.values(), *s18.values()])
    launched = g.states_where(V.attack_order == "launched")
    ger = attractor(g, {"GER"}, launched)
    rest = safe(g, {"WEST", "USSR", "Nature"}, g.states_where(V.attack_order != "launched"))
    out = {"cm": cm, "g": g, "path": path, "launched": launched}
    for b in common.BELIEFS:
        i17, i18 = common.sid(g, s17[b]), common.sid(g, s18[b])
        out[b] = {
            "forced17": i17 in ger.win,
            "rank17": ger.rank.get(i17),
            "blocked17": i17 in rest.kernel,
            "forced18": i18 in ger.win,
            "rank18": ger.rank.get(i18),
            "blocked18": i18 in rest.kernel,
        }
    out["seconds"] = round(time.time() - t0, 2)
    return out


@pytest.mark.parametrize("profile", PROFILES)
def test_K4a_b_forced_by_germany_and_blocked_by_no_coalition(profile, capsys):
    r = analysis(profile)
    with capsys.disabled():
        print(f"\nK4 [{profile}] explicit engine, {r['g'].size()} states, {r['seconds']} s:")
        for b in common.BELIEFS:
            print(f"  belief {b}: {r[b]}")
    for b in common.BELIEFS:
        assert r[b]["forced17"] and r[b]["rank17"] <= 3, (b, r[b])
        assert not r[b]["blocked17"], (b, r[b])


def test_K4c_d_the_treaty_and_the_halt_on_the_realized_path():
    r = analysis("deterred")
    cm, path = r["cm"], r["path"]
    rows = crisis.realized_rows()
    assert cm.state_dict(path[16])["belief_GER"] == "uncertain"  # the letter changes nothing
    assert cm.state_dict(path[17])["belief_GER"] == "uncertain"
    assert cm.state_dict(path[18])["belief_GER"] == "will_fight"
    assert rows[17]["WEST"] == "sign_treaty" and rows[16]["WEST"] == "warn_germany"
    assert rows[17]["GER"] == "cancel_attack" and rows[17]["Nature"] == "italy_declines"
    ger = next(a for a in cm.actors if a.name == "GER")
    source = ger.actions[ger.action_index("cancel_attack")].source
    assert "Mussolini" in source and "treaty" in source


@pytest.mark.parametrize("profile", PROFILES)
def test_K4e_f_re_ordered_within_two_ticks_whatever_west_does(profile):
    r = analysis(profile)
    for b in common.BELIEFS:
        assert r[b]["forced18"] and r[b]["rank18"] <= 2, (b, r[b])
        assert not r[b]["blocked18"], (b, r[b])
    realized_attack = next(
        k for k, row in enumerate(crisis.realized_rows()) if row["GER"] == "attack_poland"
    )
    assert realized_attack - 17 == 2


def test_K4g_the_shortest_trace_shows_the_cancellation_and_the_re_order(capsys):
    r = analysis("deterred")
    g, path = r["g"], r["path"]
    trace = witness(g, common.sid(g, path[17]), r["launched"])
    after = witness(g, common.sid(g, path[18]), r["launched"])
    with capsys.disabled():
        print(
            "\nK4 shortest trace from the realized state of tick 17 (explicit engine):\n"
            + trace.render(g)
        )
        print(
            "K4 shortest trace from the realized state after the halt (tick 18):\n"
            + after.render(g)
        )
    ger = [a.name for a in g.model.actors].index("GER")
    names = [g.model.actors[ger].actions[m[ger]].name for m in trace.joint_moves]
    assert "cancel_attack" in names
    assert "attack_poland" in names[names.index("cancel_attack") + 1 :]
