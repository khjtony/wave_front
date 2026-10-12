"""T10: Negative controls and the number of relaxations each needs.

Registered 2026-10-11 in docs/ww2_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.
"""

import pytest

from models.ww2.hypotheses import fixed_model, snapshot_state
from models.ww2.v0 import model
from wavefront import bmc
from wavefront.analysis import relax_explicit

CLAIM = {
    "id": "T10",
    "from_state": "various",
    "claim": (
        "negative controls: Germany conquers the United States; Japan conquers the "
        "USSR; Britain alone defeats Germany by 1941"
    ),
    "expected": (
        "each needs 3 or more relaxations. The USSR joining the Axis against Britain "
        "is *not* absurd (the November 1940 Berlin talks) and must need at most one "
        "relaxation of `aims[USSR]`"
    ),
    "sources": "Weinberg; Kershaw",
}

# "Relaxations" count named assumptions including named guard parts (ww2_testbed.md
# section 11, clarification of 2026-10-12). Bounded searches run from the tick-0 state with
# aims_GER hegemonic (the hypothesis under which the realized path exists); aims_USSR stays
# swept and restricted by the assumption ussr_defensive, so that relaxing it is possible.


@pytest.mark.slow
def test_T10_ussr_joins_axis():
    """At most one relaxation of aims[USSR]: the minimum is one, ``ussr_defensive`` is a
    minimum set, and every minimum set relaxes the Soviet hypothesis (the assumption or the
    hypothesis gate of join_axis)."""
    cm = fixed_model(model, aims_GER="hegemonic").compile()
    res = bmc.relax(cm, 20, "USSR_JOINS_AXIS", max_relax=1)
    assert not res.reachable_as_is
    assert res.minimum_size == 1
    assert ["ussr_defensive"] in res.minimal_sets
    assert all(set(s) <= {"ussr_defensive", "USSR.join_axis:hypothesis"} for s in res.minimal_sets)


@pytest.mark.slow
@pytest.mark.xfail(
    strict=True,
    reason="registered expectation not met; see reports/ww2_v0.md section 8",
)
def test_T10_japan_conquers_ussr():
    """Three or more relaxations (searched up to 3, bounded checker, k = 20). The minimum
    found is 1: {Nature.campaign_siberia:japanese_superiority}. Nature's china_incident is
    nondeterministic, so a play without the China war satisfies the D7 parts army_free and
    no_two_front without relaxing them."""
    cm = fixed_model(model, aims_GER="hegemonic").compile()
    res = bmc.relax(cm, 20, "JPN_CONQUERS_USSR", max_relax=3)
    assert not res.reachable_as_is
    assert res.minimum_size is None or res.minimum_size >= 3


@pytest.mark.slow
@pytest.mark.xfail(
    strict=True,
    reason="registered expectation not met; see reports/ww2_v0.md section 8",
)
def test_T10_britain_alone_defeats_germany():
    """'Britain alone defeats Germany by 1941': GERMAN_DEFEAT from the state at the end of
    1940Q3 (tick 19, France fallen, Britain at war alone) needs three or more relaxations.
    Explicit search over every set of at most two named assumptions (re-exploring each):
    one set of size two is found, {Nature.campaign_rhineland:offensive,
    Nature.campaign_rhineland:german_army_unready}."""
    cm = model.compile()
    start = snapshot_state(cm, "1940Q3", "hegemonic")
    sets = relax_explicit(model, "GERMAN_DEFEAT", max_size=2, initial=[start])
    assert not sets.undecided
    assert list(sets) == []


def test_T10_germany_conquers_the_united_states():
    """No variable or action of v0 represents a German conquest of the United States: the
    United States enter only as the commitment level commit_US, which no GER action changes,
    and no ending or region refers to them."""
    cm = model.compile()
    names = [v.name for v in cm.variables]
    us_vars = [n for n in names if "US" in n.split("_") or "usa" in n.lower()]
    assert us_vars == ["commit_US"]
    ger = cm.actors[0]
    assert not any(getattr(e, "var", None) == "commit_US" for a in ger.actions for e in a.effects)
    assert not any("US" in e.split("_") for e in model.endings)
    pytest.skip("vacuous: no variable or action represents it")
