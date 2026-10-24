"""V8: Force past survivability on cw_v1 (C10 as amended).

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V8a. The readings the model step must fix before first sight are listed in
section 9.4.

Reading (docs/cw_v1_decisions.md, R V8): as v0's R C10 and A C10, with ``balance_core``. For
each year 1947 to 1991, per hypothesis, the hindsight state and its one-level perturbations
(each declared variable but the swept objective one level up and one down where legal;
built-ins kept). (a) From 1965, raising ``nuke_USA`` or ``nuke_USSR`` from a level >=
survivable flips no membership in K_J of ``balance_core``. (b) A perturbation counts for its
variable when it changes membership in K_USA or K_USSR of ``balance_core`` or the fewest
transitions to ``GENERAL_WAR`` or ``ACCIDENTAL_WAR`` (on the flattened game); a family's score
is its best member's (nuke: ``nuke_USA``, ``nuke_USSR``; belief: the three belief variables;
oversight); score(nuke) < score(oversight) and < score(belief) in every year from 1966, and >
both in every year to 1964 (the control); 1965 reported. Engines: symbolic from 1984, the
composite engine for 1972 to 1983 (the explicit part explored once per year from the state and
its perturbations), the layered lifting before 1972 (kernels and distances over the whole
domain, looked up). Bounded fallback: a composite year whose explicit part exceeds 6,000,000
states is computed on the coarse game with the sub-games inert, marked "coarse
approximation" and counted undecided. Holds iff (a) and (b) under at least one hypothesis
with no undecided year.
"""

import os

import pytest

from wavefront.engine import BudgetExceeded
from wavefront.model import ModelError

from ..common import (
    HYPS,
    Timer,
    compiled,
    composite_distances,
    composite_graph,
    composite_kernel,
    engine_for,
    everyone_attractor,
    hindsight,
    kernel,
    layered_distance,
    layered_kernel,
)

CLAIM = {
    "id": "V8",
    "from_state": "each year from 1965",
    "claim": (
        "on cw_v1, C10 as amended 2026-10-23, with `balance_core` in place of `balance_cw` "
        "in the unilateral kernels (the bloc clause empties `⟨⟨USA⟩⟩` by construction; "
        "section 9.2): once both principals hold survivable second strike, further increases "
        "in `nuke` do not change kernel membership; `oversight` and `belief` do change the "
        "state's membership in the unilateral kernels `⟨⟨USA⟩⟩□balance_core` and "
        "`⟨⟨USSR⟩⟩□balance_core` or its shortest trace to `GENERAL_WAR` or `ACCIDENTAL_WAR`; "
        "the ranking before 1965, `nuke` above `oversight` and `belief`, is the claim's "
        "negative control"
    ),
    "expected": (
        "the sensitivity report (Q7), scoring a variable by the one-level perturbations that "
        "change unilateral-kernel membership or the shortest trace to the adverse endings, "
        "ranks `nuke` below `oversight` and `belief` after 1965 and above them before"
    ),
    "sources": "Schelling 1966; Kristensen and Norris series; re-asks C10 as amended",
}

# The first-sight switch (docs/cw_v1_decisions.md D8): the claim runs only when the owner sets
# WF_FIRST_SIGHT_CWV1=1 for the one recorded run of V1 to V10.
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_CWV1") == "1"

P = "balance_core"
JOINT, US, SU = ("USA", "USSR"), ("USA",), ("USSR",)
FAMILIES = {
    "nuke": ("nuke_USA", "nuke_USSR"),
    "belief": ("belief_force_USA", "belief_USA_USSR", "belief_USSR_USA"),
    "oversight": ("oversight",),
}


def perturbations(cm, s):
    """``(variable, direction, perturbed state)`` for every declared variable but the swept
    objective, one level up and one down where legal."""
    for v in cm.variables:
        if v.origin != "var" or v.name == "aims_USSR":
            continue
        i = cm.index[v.name]
        for d in (-1, 1):
            j = s[i] + d
            if 0 <= j < v.size:
                yield v.name, d, s[:i] + (j,) + s[i + 1 :]


def measures(aims, year, states):
    """Per state: (in K_J, in K_USA, in K_USSR, fewest transitions to the adverse endings),
    by the year's engine; and the engine's label (``None`` label: undecided)."""
    engine = engine_for(year)
    if engine in ("symbolic", "layered"):
        if engine == "symbolic":
            ks = [kernel(aims, c, P) for c in (JOINT, US, SU)]
            dist = everyone_attractor(aims, "adverse")
        else:
            ks = [layered_kernel(aims, c, P) for c in (JOINT, US, SU)]
            dist = layered_distance(aims, "adverse")
        out = [tuple(k.contains(s) for k in ks) + (dist.rank(s),) for s in states]
        return out, engine
    try:
        g = composite_graph(aims, states)
    except (BudgetExceeded, ModelError) as exc:
        print(f"[V8]   {year}: explicit part not computed ({type(exc).__name__}: {exc})")
        ks = [kernel(aims, c, P) for c in (JOINT, US, SU)]
        dist = everyone_attractor(aims, "adverse")
        out = [tuple(k.contains(s) for k in ks) + (dist.rank(s),) for s in states]
        return out, None
    kids = [composite_kernel(g, aims, c, P) for c in (JOINT, US, SU)]
    dist = composite_distances(aims, g, ["adverse"])["adverse"]
    out = [tuple(g.index[s] in k for k in kids) + (dist[g.index[s]],) for s in states]
    return out, f"composite ({g.size()} states to 1984)"


def rank_ok(fam, y, before, after):
    if y <= 1964:
        before = before and fam["nuke"] > fam["oversight"] and fam["nuke"] > fam["belief"]
    if y >= 1966:
        after = after and fam["nuke"] < fam["oversight"] and fam["nuke"] < fam["belief"]
    return before, after


@pytest.mark.skipif(not FIRST_SIGHT, reason="cw_v1 first sight not switched on")
def test_V8():
    timer = Timer()
    print("\n[V8] engines: layered lifting to 1971, composite 1972-1983, symbolic from 1984")
    results = {}
    for aims in HYPS:
        cm = compiled(aims)
        a = True
        before = after = True
        undecided = []
        for y in range(1947, 1992):
            s = hindsight(y, aims)
            perts = list(perturbations(cm, s))
            values, engine = measures(aims, y, [s] + [t for _, _, t in perts])
            base, rest = values[0], values[1:]
            score = {v.name: 0 for v in cm.variables}
            for (name, d, _), m in zip(perts, rest, strict=True):
                score[name] += (m[1], m[2], m[3]) != (base[1], base[2], base[3])
                if (
                    y >= 1965
                    and d == 1
                    and name in FAMILIES["nuke"]
                    and cm.state_dict(s)[name] in ("survivable", "overkill")
                    and m[0] != base[0]
                ):
                    a = False
            fam = {f: max(score[v] for v in vs) for f, vs in FAMILIES.items()}
            if engine is None:
                undecided.append(y)
            before, after = rank_ok(fam, y, before, after)
            top = sorted(score.items(), key=lambda kv: -kv[1])[:4]
            print(
                f"[V8]   aims_USSR={aims} {y}: K_J {base[0]}, K_USA {base[1]}, K_USSR "
                f"{base[2]}; to adverse {base[3]}; families {fam}; top {top} "
                f"[{engine or 'coarse approximation: undecided'}]"
            )
        ok = a and before and after and not undecided
        results[aims] = ok
        print(
            f"[V8] aims_USSR={aims}: (a) {a}; (b) before 1965 {before}, after 1965 {after}; "
            f"undecided years {undecided}: {ok} ({timer})"
        )
    assert any(results.values()), results
