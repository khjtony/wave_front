"""Construction checks of the PRC-scope analysis builds (models/cw/experiments/prc_scope.py;
docs/prc_experiment.md). Not registered claims and not checks of the model under protocol:
the builds compile, are well-formed from hindsight states, S and P69 are v0's two builds,
every added action carries a dated source, and the hindsight states of the added variables
admit the realized PRC decisions."""

import re

import pytest

from models.cw.experiments.prc_scope import (
    ADDED_PRC_ACTIONS,
    PRC_ACTIONS,
    REALIZED_PRC,
    VARIANTS,
    build_variant,
    fixed,
    hindsight_state,
    principals,
)
from models.cw.v0 import build
from wavefront.analysis import fingerprint
from wavefront.engine import explore

HYPS = ("status_quo", "opportunist")


def owner(m, name):
    """The actor (Nature included) that holds action ``name``."""
    for a in [*m.actors, m.nature()]:
        if any(x.name == name for x in a.actions):
            return a.name
    return None


def test_s_and_p69_are_v0s_two_builds():
    assert fingerprint(build_variant("S")) == fingerprint(build(prc_principal=False))
    assert fingerprint(build_variant("P69")) == fingerprint(build(prc_principal=True))


@pytest.mark.parametrize("variant", VARIANTS)
def test_each_variant_compiles_with_its_principals(variant):
    m = build_variant(variant)
    assert tuple(a.name for a in m.actors) == principals(variant)
    for aims in HYPS:
        cm = fixed(m, aims).compile()
        assert cm.actors[-1].name == "Nature"


def test_who_holds_the_prc_decisions():
    expected = {"P50": "PRC", "N50": "Nature", "B": "USSR"}
    for variant, holder in expected.items():
        m = build_variant(variant)
        assert {owner(m, n) for n in PRC_ACTIONS} == {holder}, variant
        assert owner(m, "prc_test") == "Nature"
    p50 = build_variant("P50")
    for x in next(a for a in p50.actors if a.name == "PRC").actions:
        assert x.guard_parts[0] == ("principal", x.guard_parts[0][1]), x.name


@pytest.mark.parametrize("variant", ("P50", "N50", "B"))
def test_added_actions_carry_dated_sources(variant):
    m = build_variant(variant)
    for a in [*m.actors, m.nature()]:
        for x in a.actions:
            if x.name in (*ADDED_PRC_ACTIONS, "prc_test"):
                assert len(x.source) > 100 and re.search(r"19[4-9]\d", x.source), x.name
                assert not x.speculative, x.name


@pytest.mark.parametrize("variant", VARIANTS)
def test_well_formed_from_1975_and_1985(variant):
    cm = fixed(build_variant(variant), "opportunist").compile()
    for year in (1975, 1985):
        g = explore(cm, initial=[hindsight_state(cm, variant, year, "opportunist")])
        assert g.size() > 100


@pytest.mark.parametrize("aims", HYPS)
def test_realized_prc_decisions_are_available_at_their_hindsight_states(aims):
    cm = fixed(build_variant("P50"), aims).compile()
    prc = next(a for a in cm.actors if a.name == "PRC")
    for year, action in REALIZED_PRC.items():
        s = hindsight_state(cm, "P50", year, aims)
        assert prc.action_index(action) in cm.available(s)[prc.index], (year, action)
