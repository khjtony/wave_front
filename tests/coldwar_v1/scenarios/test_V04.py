"""V4: Korea 1950: limited war reachable, general war blockable by the USA (C5).

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V4a. The readings the model step must fix before first sight are listed in
section 9.4.

Reading (docs/cw_v1_decisions.md, R V4): the 1950 hindsight state under ``opportunist`` (the
registered hypothesis; ``status_quo`` reported), the flattened game from it cut at tick 7 (1
January 1954; no sub-game falls in 1950 to 1953), explicit. (a) A state with ``korea =
armistice`` and ``esc < conventional`` is reachable (zero relaxations). (b) The state is in
``safe({USA}, no_general_war_core)`` with the cut states kept; beside, H8: the symbolic coarse
kernel with ``tick >= 15`` kept. (c) Structural: ``USA.nuclear_korea`` is the only American
action whose guard reads ``korea`` with an effect that can raise ``esc`` to a nuclear rung; its
parts ``total_commitment`` and ``reading`` are as registered; some state of the graph has it
available, (b) being computed on that graph. (d) Reported: the attractor of {USSR, PRC,
Nature} to ``GENERAL_WAR_core`` with every declared American action forbidden, its rank and
the moves of one play along the strategy (the others' best delay), each marked (i) a Soviet
programme decision before its documented year in data/cw/decisions.csv or (ii) an escalation
taken while ``esc`` already stood at ``crisis`` or above (the record has no standing
US-Soviet crisis in 1950 to 1953). Control: the 1950 state is outside ``safe({USA}, korea =
peace)`` on the flattened game cut at tick 4, the cut states kept iff ``korea = peace``.
Holds iff (a), (b), (c) and the control under ``opportunist``. Engine: explicit.
"""

import csv
import os

import pytest

from models.cw import v1
from wavefront.engine import attractor, safe
from wavefront.model import Bump, Set, SetIf, V

from ..common import (
    HYPS,
    OPP,
    Forbid,
    Timer,
    bfs_distance,
    bounded_kernel,
    compiled,
    flat_of,
    graph,
    hindsight,
    model_of,
    move_names,
)

CLAIM = {
    "id": "V4",
    "from_state": "1950, June (the state of 1 January 1950), under `opportunist`",
    "claim": (
        "with `GENERAL_WAR_core` (`esc ≥ tactical_nuclear` between the USA and the USSR, not "
        "accidental), the PRC a principal and its Korean entry available: (a) a limited war "
        "in Korea is reachable (a state with `korea = armistice` and `esc < conventional`); "
        "(b) `⟨⟨USA⟩⟩□¬GENERAL_WAR_core` holds through 1 January 1954; (c) the United "
        "States' nuclear option in Korea is available only after a Chinese entry or "
        "US–Soviet combat (total commitment) and only with a reading of Soviet aims other "
        "than `opportunist`, and (b) holds with that option available; (d) the attractor of "
        "{USSR, PRC, Nature} to `GENERAL_WAR_core` by 1954 with the United States idle is "
        "reported with its first moves and with whether any move is a Soviet programme "
        "decision before its documented date or an escalation summed across two crises the "
        "record does not have standing together (the route of reports/cw_v0.md section 20); "
        "control: the 1950 state is outside `⟨⟨USA⟩⟩□(korea = peace)` through 1 January 1951 "
        "(the United States alone could not keep the Korean war away)"
    ),
    "expected": (
        "(a), (b), (c) and the control as stated, (b) also reported at the cut plus eight "
        "ticks (H8); (d) reported, not asserted; `status_quo` reported (the war needs "
        "Stalin's approval)"
    ),
    "sources": (
        "FRUS 1950; Gaddis 1982 and 2005; Weathersby 1993; Chen Jian 1994; Dingman 1988; "
        "Foot 1988; Mastny and Byrne 2005; Holloway 1994; re-asks C5"
    ),
}

# The first-sight switch (docs/cw_v1_decisions.md D8): the claim runs only when the owner sets
# WF_FIRST_SIGHT_CWV1=1 for the one recorded run of V1 to V10.
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_CWV1") == "1"

CUT = 7  # 1 January 1954
CONTROL_CUT = 4  # 1 January 1951
H8_CUT = 15  # 1 January 1962
GENERAL_WAR_CORE = (V.esc >= "tactical_nuclear") & ~V.accidental
LIMITED = (V.korea == "armistice") & (V.esc < "conventional")
PROGRAMME = ("build_bomb", "icbm_buildup", "mirv")
NUCLEAR = ("tactical_nuclear", "strategic")


def documented_years():
    """The documented year of each Soviet programme decision (data/cw/decisions.csv)."""
    with open(v1.DATA / "decisions.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return {
        r["action"]: int(r["year"])
        for r in rows
        if r["actor"] == "USSR" and r["action"] in PROGRAMME
    }


def raises_to_nuclear(effect) -> bool:
    if getattr(effect, "var", None) != "esc":
        return False
    if isinstance(effect, Bump):
        return effect.amount > 0
    if isinstance(effect, (Set, SetIf)):
        return str(effect.value) in NUCLEAR
    return False


def structural(aims):
    """(c): the American actions in Korea that can reach a nuclear rung, and the parts of
    ``USA.nuclear_korea`` as registered."""
    usa = model_of(aims).actor_named("USA")
    korea = [
        x.name
        for x in usa.actions
        if "VarRef(name='korea')" in repr(dict(x.guard_parts))
        and any(raises_to_nuclear(e) for e in x.effects)
    ]
    parts = dict(next(x for x in usa.actions if x.name == "nuclear_korea").guard_parts)
    expected = {
        "total_commitment": (V.esc >= "conventional") | (V.esc_usprc == "war"),
        "reading": V.belief_USA_USSR != "opportunist",
    }
    same = {k: repr(parts.get(k)) == repr(v) for k, v in expected.items()}
    return korea, same


def escalation(cm, actor, action) -> bool:
    a = next(x for x in [*cm.model.actors, cm.model.nature()] if x.name == actor)
    x = next(y for y in a.actions if y.name == action)
    return any(
        getattr(e, "var", None) == "esc" and (not isinstance(e, Bump) or e.amount > 0)
        for e in x.effects
    )


def forcing_play(aims, s50):
    """(d): the attractor of {USSR, PRC, Nature} to GENERAL_WAR_core with the United States
    idle; the rank and one play (the coalition's strategy, the rest maximizing the rank)."""
    fm = flat_of(aims)
    cm = fm.coarse
    usa_spec = next(a for a in cm.actors if a.name == "USA")
    usa = [("USA", x.name) for x in usa_spec.actions if not x.is_idle]
    g = graph(Forbid(fm, usa), s50, cut=CUT)
    target = g.states_where(lambda s: not fm.is_fine(s) and cm.evaluate(GENERAL_WAR_CORE, s))
    coalition = ["USSR", "PRC", "Nature"]
    res = attractor(g, coalition, target)
    start = g.index[s50]
    if start not in res.win:
        return None, [], g.size()
    dated = documented_years()
    esc = cm.index["esc"]
    moves, i = [], start
    while i not in target:
        best = None
        for move, j in zip(g.moves[i], g.succ[i], strict=True):
            sub = tuple(move[a.index] for a in cm.actors if a.name in coalition)
            if sub != res.strategy[i]:
                continue
            if best is None or res.rank[j] > res.rank[best[1]]:
                best = (move, j)
        move, j = best
        s = g.states[i]
        year = v1.YEAR0 + s[cm.index["tick"]]
        for name in move_names(cm, move):
            actor, action = name.split(".")
            marks = []
            if action in dated and year < dated[action]:
                marks.append(f"(i) before its documented year {dated[action]}")
            if escalation(cm, actor, action) and s[esc] >= cm.variables[esc].levels.index("crisis"):
                marks.append("(ii) escalation over a standing crisis")
            moves.append(f"{year} {name}" + (f" [{'; '.join(marks)}]" if marks else ""))
        i = j
    return res.rank[start], moves, g.size()


@pytest.mark.skipif(not FIRST_SIGHT, reason="cw_v1 first sight not switched on")
def test_V4():
    timer = Timer()
    print("\n[V4] engine: explicit, the flattened game cut at 1 Jan 1954 (no sub-game inside)")
    korea, parts = structural(OPP)
    results = {}
    for aims in HYPS:
        cm = compiled(aims)
        fm = flat_of(aims)
        s50 = hindsight(1950, aims)
        g = graph(fm, s50, cut=CUT)
        start = g.index[s50]
        coarse = [i for i, s in enumerate(g.states) if not fm.is_fine(s)]
        limited = {i for i in coarse if cm.evaluate(LIMITED, g.states[i])}
        d = bfs_distance(g, start, limited)
        a = d is not None
        keep = {
            i
            for i, s in enumerate(g.states)
            if fm.is_fine(s) or g.ending[i] == "CUT" or cm.evaluate("no_general_war_core", s)
        }
        b = start in safe(g, ["USA"], keep).kernel
        h8 = bounded_kernel(aims, ("USA",), "no_general_war_core", H8_CUT).contains(s50)
        usa = next(x for x in cm.actors if x.name == "USA")
        nk = usa.action_index("nuclear_korea")
        offered = sum(1 for i in range(g.size()) if nk in g.avail[i][usa.index])
        c = korea == ["nuclear_korea"] and all(parts.values()) and offered > 0
        print(
            f"[V4] aims_USSR={aims}: graph {g.size()} states; (a) limited war reachable with "
            f"zero relaxations: {a} (in {d} transitions); (b) in USA's kernel of "
            f"no_general_war_core to 1954: {b}; beside, H8 (symbolic, to 1962): {h8}"
        )
        print(
            f"[V4]   (c) American nuclear actions in Korea {korea}; parts as registered "
            f"{parts}; states offering USA.nuclear_korea {offered}: {c}"
        )
        rank, moves, size = forcing_play(aims, s50)
        print(
            f"[V4]   (d) {{USSR, PRC, Nature}} with the USA idle ({size} states): "
            + ("cannot force GENERAL_WAR_core" if rank is None else f"forces it in {rank}: {moves}")
        )
        gc = graph(fm, s50, cut=CONTROL_CUT)
        phi = {
            i
            for i, s in enumerate(gc.states)
            if fm.is_fine(s) or cm.evaluate(V.korea == "peace", s)
        }
        control = gc.index[s50] not in safe(gc, ["USA"], phi).kernel
        print(f"[V4]   control: outside USA's kernel of korea = peace to 1951: {control}")
        results[aims] = (a, b, c, control)
        print(f"[V4] aims_USSR={aims}: (a) {a}, (b) {b}, (c) {c}, control {control} ({timer})")
    print(f"[V4] registered hypothesis {OPP}: {results[OPP]}")
    assert all(results[OPP]), results
