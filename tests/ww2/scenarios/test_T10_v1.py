"""T10 on v1: the Japan content control (docs/ww2_v1_decisions.md E5, "T10 on v1").

The registered claim is in test_T10.py, which runs on v0 in CI as registered. On
models/ww2/v1.py the Japan control is re-run as a content control under ``aims_JPN =
hegemonic``: "Japan conquers the USSR" (the ending JPN_CONQUERS_USSR) needs at least one
relaxation and every minimal relaxation set relaxes
``Nature.campaign_siberia:japanese_superiority``, the constraint the record never lifts. The
Britain-alone control is not re-run (same mechanism as v0); the United States control stays
vacuous in v1 (the Atlantic is not modeled; ontology_ww2_v1.md section 7).

Engine: the bounded relaxation search of the package (wavefront.bmc.relax) from the
tick-0 state (``aims_GER`` hegemonic, ``aims_JPN`` hegemonic, ``aims_USSR`` swept and
restricted by ``ussr_defensive``), k = 39, up to three relaxations.
"""

import pytest

from models.ww2.hypotheses import fixed_model
from models.ww2.v1 import model
from wavefront import bmc

CLAIM_REF = "T10"  # the registered claim and its CLAIM dict are in test_T10.py


@pytest.mark.slow
def test_T10_v1_japan_conquers_ussr():
    cm = fixed_model(model, aims_GER="hegemonic", aims_JPN="hegemonic").compile()
    res = bmc.relax(cm, 39, "JPN_CONQUERS_USSR", max_relax=3)
    print(
        f"\nT10 on v1 (Japan): reachable as is {res.reachable_as_is}; minimum "
        f"{res.minimum_size}; minimal sets {res.minimal_sets}"
    )
    if res.trace is not None:
        print(res.trace.render(cm))
    assert not res.reachable_as_is
    assert res.minimum_size is not None and res.minimum_size >= 1
    assert res.minimal_sets
    assert all("Nature.campaign_siberia:japanese_superiority" in s for s in res.minimal_sets)


def test_T10_v1_germany_conquers_the_united_states_is_vacuous():
    """No v1 variable or action represents a German conquest of the United States: the
    United States enter as commit_US, arms_USA, war_us_ger and the Pacific variables, and no
    ending or region refers to an invasion of them."""
    cm = model.compile()
    assert not any("america" in v.name.lower() for v in cm.variables)
    assert not any("US" in e.split("_") for e in model.endings)
    pytest.skip("vacuous in v1: the Atlantic is not modeled")
