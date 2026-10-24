"""J6v1: registered 2026-10-24 in docs/july1914_testbed.md section 8.3 (the 1914 v1
registration, owner's decision 2h of 2026-10-23), before any v1 guard.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature, in the v1 content of section 8.2. Do not edit the claim text
without a changelog entry in that document. Skipped until ``models/july1914/v1.py`` exists
and the owner gives the go for the first sight by setting ``WF_FIRST_SIGHT_1914V1=1`` (the
skip condition was "v1.py exists" until the model step built it; changed then so that the
first sight is held, docs/july1914_v1_decisions.md V9). The body is the reading of
docs/july1914_v1_decisions.md section R (J6v1), written before that go.
"""

import os
from pathlib import Path

import pytest

from models.ww2 import bounded
from wavefront.bmc import relax

from .common import PAIRS, Timer, compiled, label, minimal_relaxation_sets

V1 = Path(__file__).resolve().parents[2] / "models" / "july1914" / "v1.py"
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_1914V1") == "1"

CLAIM = {
    "id": "J6v1",
    "from_state": "tick 0",
    "claim": (
        "**negative control (hold-out), re-registered on v1.** A general European war by 15 July "
        "(before the ultimatum) needs at least two relaxations under every hypothesis pair, because"
        " every power's first step answered another's: Vienna's note waited on its own decision "
        "cycle, Russia's measures on Vienna's note, Germany's mobilization on Russia's measures. "
        "Every minimal set relaxes an Austro-Hungarian decision-cycle part (a part of Tisza's "
        "consent or of the note that reads it, or the harvest leave of the army, which the record "
        "never lifts) or a part by which a German mobilization step answers a Russian measure "
        "(`russian_measures` or [H] of `GER.kriegsgefahr` or `GER.mobilize`); "
        "`GER.mobilize:sequence` alone, v0's route, no longer suffices"
    ),
    "expected": "as stated",
    "sources": (
        "the Council of 7 July and Tisza's memoranda of 1 and 8 July; Conrad's harvest-leave "
        "constraint; the Russian Council of 24 July (measures only after the note); Bethmann's "
        "policy of letting Russia move first (Müller's diary, 1 August; Mombauer (ed.) 2013); Clark"
        " 2012 chs. 9 to 11; Otte 2014"
    ),
}


# docs/july1914_v1_decisions.md R J6v1: an Austro-Hungarian decision-cycle part (any part of
# Tisza's consent or of the note that reads it, or the harvest leave) or a part by which a
# German mobilization step answers a Russian measure.
AUH_CYCLE_PREFIXES = ("AUH.tisza_consent:", "AUH.ultimatum:")
AUH_CYCLE = {"AUH.mobilize_partial:harvest_leave"}
GER_ANSWERS = {
    "GER.kriegsgefahr:russian_measures",
    "GER.kriegsgefahr:hypothesis",
    "GER.mobilize:russian_measures",
    "GER.mobilize:hypothesis",
}
V0_ROUTE = ["GER.mobilize:sequence"]
K = 17
MAX_SETS = 40


def answers(s):
    return any(a in AUH_CYCLE or a.startswith(AUH_CYCLE_PREFIXES) or a in GER_ANSWERS for a in s)


@pytest.mark.slow
@pytest.mark.skipif(
    not (V1.exists() and FIRST_SIGHT),
    reason="1914 v1 first sight held for the owner's go (WF_FIRST_SIGHT_1914V1=1)",
)
def test_J6v1():
    timer = Timer()
    print(f"\n[J6v1] engine: bounded (Z3), GENERAL_WAR within {K} transitions from tick 0")
    failures = []
    for pair in PAIRS:
        t = Timer()
        cm = compiled(pair)
        (s0,) = cm.initial_states()
        sets = minimal_relaxation_sets(cm, s0, K, "GENERAL_WAR", max_size=3, max_sets=MAX_SETS)
        res = relax(cm, K, "GENERAL_WAR", max_relax=3, max_sets=20)
        print(
            f"[J6v1] {label(pair)}: inclusion-minimal sets up to size 3: {sets}; "
            f"bmc.relax minimum {res.minimum_size}, sets {res.minimal_sets} ({t})"
        )
        if sets and sets[0]:
            trace = bounded.reach_from(cm, s0, K, "GENERAL_WAR", relax=sets[0])
            print(trace.render(cm) if trace else "(no trace)")
        if any(len(s) < 2 for s in sets):
            failures.append(f"{label(pair)}: a set of size < 2: {[s for s in sets if len(s) < 2]}")
        if len(sets) >= MAX_SETS:
            print(f"[J6v1]   cap of {MAX_SETS} sets reached: read on the sets found")
        if V0_ROUTE in sets:
            failures.append(f"{label(pair)}: GER.mobilize:sequence alone suffices (v0's route)")
        for s in sets:
            if not answers(s):
                failures.append(
                    f"{label(pair)}: {s} relaxes no Austro-Hungarian decision-cycle part and no "
                    "German answer to a Russian measure"
                )
    print(f"[J6v1] done ({timer})")
    assert not failures, "; ".join(failures)
