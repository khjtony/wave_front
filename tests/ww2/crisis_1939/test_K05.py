"""K5: registered 2026-10-15 in docs/crisis_1939_testbed.md section 3.

The summer-1939 crisis sub-game of WW2 v1 (3-day ticks, 5 July to 3 September 1939), entered
from the 1939Q3 state. Do not edit the claim text without a changelog entry in that
document.

Reading (docs/crisis_1939_decisions.md R5). Target ``EARLY_ATTACK := attack_order ==
launched and tick <= 17`` (an attack decided at tick 16 or earlier, before 26 August), the
one ending of ``build(inert=False, target=...)``; ``relax_explicit(..., max_size=2,
initial=[entry state])``, no profile. The claim holds when the target is unreachable as is
and every minimal set found contains ``GER.attack_poland:readiness``.

Engine: the explicit engine (``relax_explicit``, brute force over the named assumptions).
"""

import time

from models.ww2.crises import summer_1939 as crisis
from tests.ww2.crisis_1939 import common
from wavefront.analysis import relax_explicit
from wavefront.model import V

CLAIM = {
    "id": "K5",
    "from_state": "tick 0",
    "claim": (
        "negative control: an attack launched before 26 August (tick 17) needs at least one "
        "relaxation, and every minimal set relaxes Case White's readiness part (the date of 1 "
        "September fixed on 3 April, a constraint the record never lifts)"
    ),
    "expected": "as stated",
    "sources": "Case White directive of 3 April 1939 (C-120)",
}


def test_K5(capsys):
    t0 = time.time()
    target = ("EARLY_ATTACK", (V.attack_order == "launched") & (V.tick <= 17))
    model = crisis.build(inert=False, target=target)
    start = crisis.entry_state(model.compile(), common.COARSE_Q2)
    sets = relax_explicit(model, "EARLY_ATTACK", max_size=2, initial=[start])
    with capsys.disabled():
        print(
            f"\nK5 relax_explicit (explicit engine, {time.time() - t0:.1f} s): minimal sets "
            f"{list(sets)}; minimum size {sets.minimum_size}; searched {len(sets.assumptions)} "
            f"assumptions up to size {sets.max_size}; ill-formed {len(sets.ill_formed)} "
            f"{[s for s, _ in sets.ill_formed]}; undecided {len(sets.undecided)}"
        )
    assert [] not in sets
    assert sets and sets.minimum_size >= 1
    assert all("GER.attack_poland:readiness" in s for s in sets)
    assert not sets.undecided
