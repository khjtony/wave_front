"""J6: registered 2026-10-15 in docs/july1914_testbed.md section 3.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature. Do not edit the claim text without a changelog entry in that
document.

Reading (docs/july1914_decisions.md, R J6): per hypothesis pair, the bounded checker
from the tick-0 state (the encoding of ``wavefront.bmc`` unrolled from that state) with
target ``GENERAL_WAR`` within 17 transitions (Britain at war in a state at tick 17 or
earlier, "by 15 July"), every inclusion-minimal relaxation set up to size 3. Holds iff under
every pair nothing of size 0 or 1 works and every set found contains
``AUH.ultimatum:council`` or ``AUH.mobilize_partial:harvest_leave``. The cadence itself is
not a named assumption (framework_spec.md 3.1) and cannot be relaxed. The minimum-size sets
of ``wavefront.bmc.relax`` are printed as a cross-check. Engine: bounded (Z3).
"""

import pytest

from models.ww2 import bounded
from wavefront.bmc import relax

from .common import PAIRS, Timer, compiled, label, minimal_relaxation_sets

CLAIM = {
    "id": "J6",
    "from_state": "tick 0",
    "claim": (
        "**negative control.** A general European war by 15 July (before the ultimatum) needs "
        "at least two relaxations, and every minimal set relaxes the Austro-Hungarian "
        "decision cadence (the Common Ministerial Council of 7 and 19 July and the harvest "
        "leave of the army, which the record never lifts)"
    ),
    "expected": "as stated",
    "sources": (
        "the Council of 7 July; Conrad's harvest-leave constraint; Berchtold's timing of the "
        "ultimatum for Poincaré's departure from St Petersburg (23 July)"
    ),
}


AUH_CYCLE = {"AUH.ultimatum:council", "AUH.mobilize_partial:harvest_leave"}
K = 17


@pytest.mark.slow
def test_J6():
    timer = Timer()
    print(f"\n[J6] engine: bounded (Z3), GENERAL_WAR within {K} transitions from tick 0")
    failures = []
    for pair in PAIRS:
        t = Timer()
        cm = compiled(pair)
        (s0,) = cm.initial_states()
        sets = minimal_relaxation_sets(cm, s0, K, "GENERAL_WAR", max_size=3)
        res = relax(cm, K, "GENERAL_WAR", max_relax=3, max_sets=20)
        print(
            f"[J6] {label(pair)}: inclusion-minimal sets up to size 3: {sets}; "
            f"bmc.relax minimum {res.minimum_size}, sets {res.minimal_sets} ({t})"
        )
        if sets and sets[0]:
            trace = bounded.reach_from(cm, s0, K, "GENERAL_WAR", relax=sets[0])
            print(trace.render(cm) if trace else "(no trace)")
        if any(len(s) < 2 for s in sets):
            failures.append(f"{label(pair)}: a set of size < 2: {[s for s in sets if len(s) < 2]}")
        for s in sets:
            if not AUH_CYCLE & set(s):
                failures.append(f"{label(pair)}: {s} relaxes no Austro-Hungarian cycle part")
    print(f"[J6] done ({timer})")
    assert not failures, "; ".join(failures)
