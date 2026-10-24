"""K2: registered 2026-10-15 in docs/crisis_1939_testbed.md section 3; clause (d) amended
2026-10-23 on the owner's decision 2a (docs/owner_decisions_2026-10-23.md).

The summer-1939 crisis sub-game of WW2 v1 (3-day ticks, 5 July to 3 September 1939), entered
from the 1939Q3 state. Do not edit the claim text without a changelog entry in that
document. K2 is the hold-out claim of the sub-game.

Reading (docs/crisis_1939_decisions.md R2). Reduced build, the two passage scenarios
(``build(passage="granted" | "refused")``), profiles ``deterred`` and ``documented_only``
unless stated. Start: the entry state with ``belief_GER`` at each of its three levels.
"Raises forbidden" adds ``no_belief_raise``. The belief condition holds in a row when the
entry level is ``will_fight`` or raises are allowed. "Blocks": the start state is in
``safe(C, not ATTACK_LAUNCHED)``; minimal blocking coalitions by ``pivotal`` over
{WEST, USSR}.

- (a) granted scenario, belief condition holds: the minimal blocking coalitions are exactly
  [{WEST, USSR}]; and the minimal coalitions over {WEST, USSR} forcing ``alliance`` by
  tick 17 are exactly [{WEST, USSR}].
- (b) granted scenario, belief condition fails: no coalition over {WEST, USSR} blocks.
- (c) refused scenario: under ``documented_only`` nothing blocks in any row; with the
  speculative ``conclude_without_passage`` available, {WEST, USSR} blocks wherever the
  belief condition holds.
- (d) as amended 2026-10-23: where the belief condition fails (entry below ``will_fight``,
  raises forbidden; granted, refused and free), the start state is in the standard forced
  region for {GER} and ``ATTACK_LAUNCHED`` (Germany forces the attack); and with Polish
  passage left open (the free model, Nature not fixed, documented decision space) and the
  West's raises available, every entry level is contested in the fortune sense
  (ww2_testbed.md section 4.6): {GER, Nature} forces ``ATTACK_LAUNCHED`` (Nature refuses
  passage) and {WEST, USSR, Nature} keeps ``attack_order != launched`` to the horizon
  (Nature grants it). The registered computation (the standard contested region in the rows
  where the belief condition fails, which first sight found ``forced``) is printed beside it.

Engine: the explicit engine (``explore``, ``safe``, ``attractor``, ``contested``,
``pivotal``). Every cell of the grid, the free model and the grid without ``deterred`` are
printed as diagnostics.
"""

import functools
import time

import pytest

from tests.ww2.crisis_1939 import common
from wavefront.analysis import pivotal
from wavefront.engine import attractor, contested, safe
from wavefront.model import V

CLAIM = {
    "id": "K2",
    "from_state": "tick 0",
    "claim": (
        "re-asking T9: a UK, France, USSR alliance concluded before the pact blocks the "
        "attack on Poland only if `belief_GER` is `will_fight`; the coalition that can "
        "conclude it in time is {WEST, USSR} with Nature granting Polish passage, and Polish "
        "passage is pivotal (without it the alliance needs a Soviet decision the record does "
        "not show)"
    ),
    "expected": (
        "pivotal coalition {WEST, USSR} with the belief condition and the passage condition; "
        "without the belief condition, the attack is forced by Germany; with Polish passage "
        "left open (Nature free) and the West's raises available, the attack is `contested` "
        "in the fortune sense (ww2_testbed.md section 4.6): Germany with Nature's refusal "
        "forces it, {WEST, USSR} with Nature's consent keeps it out; registered 2026-10-15: "
        "without the belief condition, `contested` (the attack is not blocked, and Germany "
        "cannot force it before the pact under `deterred` while the alliance is possible), "
        "which first sight found forced"
    ),
    "sources": (
        "the Moscow talks (DBFP vol. VII); Voroshilov's question of 14 August; Beck's "
        "refusal; the profile `deterred` as adopted for T9; amended 2026-10-23"
    ),
}

WU = frozenset({"WEST", "USSR"})


def belief_condition(belief: str, raises: bool) -> bool:
    return belief == "will_fight" or raises


@functools.lru_cache(maxsize=None)
def cell(passage, documented: bool, raises: bool, deterred: bool = True) -> dict:
    """Per entry level of belief_GER: the minimal blocking coalitions over {WEST, USSR},
    GER's forcing of the attack, the standard contested status for {GER}, and the minimal
    coalitions forcing the alliance by tick 17."""
    t0 = time.time()
    profile = [
        p
        for p, on in (
            ("deterred", deterred),
            ("documented_only", documented),
            ("no_belief_raise", not raises),
        )
        if on
    ]
    cm = common.compiled(inert=False, passage=passage, profile=profile or None)
    starts = [common.entry(cm, b) for b in common.BELIEFS]
    g = common.graph(cm, starts)
    attack = g.ending_states("ATTACK_LAUNCHED")
    region = contested(g, {"GER"}, attack, "reach")
    # the fortune sense (ww2_testbed.md section 4.6; clause (d) as amended 2026-10-23)
    ger_nature = attractor(g, {"GER", "Nature"}, attack).win
    rest_nature = safe(
        g, {"WEST", "USSR", "Nature"}, g.states_where(V.attack_order != "launched")
    ).kernel
    alliance_in_time = g.states_where(V.alliance & (V.tick <= 17))
    out = {}
    for b, s in zip(common.BELIEFS, starts, strict=True):
        i = common.sid(g, s)
        piv = pivotal(g, "ATTACK_LAUNCHED", actors=["WEST", "USSR"], initial=[i])
        status = (
            "forced"
            if i in region.forced
            else "blocked"
            if i in region.blocked
            else "contested"
            if i in region.contested
            else "?"
        )
        out[b] = {
            "blocking": piv.blocking,
            "ger_forces": i in attractor(g, {"GER"}, attack).win,
            "status": status,
            "alliance_by_17": common.forcing_coalitions(g, i, alliance_in_time),
            "fortune": (i in ger_nature, i in rest_nature),
        }
    out["_meta"] = {"states": g.size(), "seconds": round(time.time() - t0, 2)}
    return out


def _fmt(cs):
    return "[" + ", ".join("{" + ", ".join(sorted(c)) + "}" for c in cs) + "]"


def table(deterred: bool = True) -> str:
    lines = [
        "| passage | decision space | raises | entry belief | blocking over {WEST, USSR} | "
        "GER forces | status ({GER}) | fortune: {GER, Nature} forces / rest with Nature keeps "
        "out | forcing alliance by 17 | states, s |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for passage in ("granted", "refused", None):
        for documented in (True, False):
            for raises in (True, False):
                c = cell(passage, documented, raises, deterred)
                for b in common.BELIEFS:
                    r = c[b]
                    lines.append(
                        f"| {passage or 'free'} | "
                        f"{'documented' if documented else 'with speculative'} | "
                        f"{'allowed' if raises else 'forbidden'} | {b} | {_fmt(r['blocking'])} | "
                        f"{r['ger_forces']} | {r['status']} | "
                        f"{r['fortune'][0]} / {r['fortune'][1]} | {_fmt(r['alliance_by_17'])} | "
                        f"{c['_meta']['states']}, {c['_meta']['seconds']} |"
                    )
    return "\n".join(lines)


@pytest.mark.slow
def test_K2_grid_printed(capsys):
    """Diagnostics: every cell, with and without ``deterred`` (explicit engine)."""
    t0 = time.time()
    with_d = table(True)
    without = table(False)
    with capsys.disabled():
        print(f"\nK2 grid under deterred (explicit engine):\n{with_d}")
        print(f"\nK2 grid without deterred (explicit engine):\n{without}")
        print(f"K2 grids: {time.time() - t0:.1f} s")
    assert with_d and without


def test_K2a_pivotal_coalition_with_the_belief_and_passage_conditions():
    for raises in (True, False):
        c = cell("granted", True, raises)
        for b in common.BELIEFS:
            if belief_condition(b, raises):
                assert c[b]["blocking"] == [WU], (raises, b, c[b])
            assert c[b]["alliance_by_17"] == [WU], (raises, b, c[b])


def test_K2b_only_if_will_fight():
    c = cell("granted", True, False)
    for b in ("will_not_fight", "uncertain"):
        assert c[b]["blocking"] == [], (b, c[b])


def test_K2c_polish_passage_is_pivotal():
    for raises in (True, False):
        documented = cell("refused", True, raises)
        speculative = cell("refused", False, raises)
        for b in common.BELIEFS:
            assert documented[b]["blocking"] == [], (raises, b, documented[b])
            if belief_condition(b, raises):
                assert speculative[b]["blocking"] == [WU], (raises, b, speculative[b])


def test_K2d_without_the_belief_condition_forced_and_contested_in_the_fortune_sense(capsys):
    """Clause (d) as amended 2026-10-23 (owner's decision 2a). The registered reading (the
    standard contested region in the rows where the belief condition fails, granted and
    refused) is printed beside the amended one; at first sight it gave ``forced``."""
    below = ("will_not_fight", "uncertain")
    registered = {
        (p, b): cell(p, True, False)[b]["status"] for p in ("granted", "refused") for b in below
    }
    free = cell(None, True, True)
    with capsys.disabled():
        print(
            "\nK2 (d) registered reading (standard region for {GER}, expected contested), "
            f"belief condition failing: {registered}"
        )
        print(
            "K2 (d) amended: free model, documented, raises allowed, ({GER, Nature} forces, "
            "{WEST, USSR, Nature} keeps out) per entry level: "
            f"{ {b: free[b]['fortune'] for b in common.BELIEFS} }; standard status "
            f"{ {b: free[b]['status'] for b in common.BELIEFS} }"
        )
    # without the belief condition the attack is forced by Germany
    for passage in ("granted", "refused", None):
        c = cell(passage, True, False)
        for b in below:
            assert c[b]["status"] == "forced" and c[b]["ger_forces"], (passage, b, c[b])
    # with passage left open and the West's raises available: contested in the fortune sense
    for b in common.BELIEFS:
        assert free[b]["fortune"] == (True, True), (b, free[b])
        assert not free[b]["ger_forces"], (b, free[b])
