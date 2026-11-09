"""J9v1: registered 2026-10-24 in docs/july1914_testbed.md section 8.3 (the 1914 v1
registration, owner's decision 2h of 2026-10-23), before any v1 guard.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature, in the v1 content of section 8.2. Do not edit the claim text
without a changelog entry in that document. Skipped until ``models/july1914/v1.py`` exists
and the owner gives the go for the first sight by setting ``WF_FIRST_SIGHT_1914V1=1`` (the
skip condition was "v1.py exists" until the model step built it; changed then so that the
first sight is held, docs/july1914_v1_decisions.md V9). The body is the reading of
docs/july1914_v1_decisions.md section R (J9v1), written before that go.
"""

import os
from pathlib import Path

import pytest

from wavefront.analysis import viability

from .common import FIGHT, PAIRS, Timer, departure, graph_from, label, path_ids
from .test_J02v1 import realized_ticks_inside

V1 = Path(__file__).resolve().parents[2] / "models" / "july1914" / "v1.py"
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_1914V1") == "1"

CLAIM = {
    "id": "J9v1",
    "from_state": "tick 32 (30 July)",
    "claim": (
        "**Russia's exit alone (hold-out; new).** With Germany's mobilization answering a Russian "
        "measure as its Kriegsgefahr did, Russia alone could still have kept the peace with Germany"
        " on 30 July, before the general order took effect: the realized state of 30 July is in the"
        ' kernel of {RUS} for "no war between Germany and Russia" under every hypothesis pair (the '
        "Tsar could withhold the general order, as he had cancelled one on 29 July, and the partial"
        " measures could still be revoked), and {RUS}'s kernel along the realized path is left at "
        "the state after the general order (31 July)"
    ),
    "expected": (
        "the realized state at tick 32 in {RUS}'s kernel of `no_war_GER_RUS` under every pair; "
        "under `fight` {RUS}'s departure along the realized path from tick 32 at tick 33"
    ),
    "sources": (
        "the Tsar's countermand of 29 July and the order of 30 July (Lieven 2015; Albertini vol. "
        "II); the German ultimatum to Russia of 31 July (Geiss); Clark 2012 ch. 11; McMeekin 2013; "
        "Trachtenberg 1990/91"
    ),
}


V0_RECORDED = "v0: {RUS}'s kernel kept to tick 32 under localize and to 31 under continental"


@pytest.mark.slow
@pytest.mark.skipif(
    not (V1.exists() and FIRST_SIGHT),
    reason="1914 v1 first sight held for the owner's go (WF_FIRST_SIGHT_1914V1=1)",
)
def test_J9v1():
    timer = Timer()
    print("\n[J9v1] engine: explicit, graph from the realized state at tick 32")
    failures = []
    for pair in PAIRS:
        g = graph_from(pair, 32)
        ids = path_ids(g, pair, 32)
        kernel = viability(g, ["RUS"], "no_war_GER_RUS").kernel
        inside = ids[0] in kernel
        dep = departure(ids, kernel, 32)
        inside0, n = realized_ticks_inside(pair, ("RUS",))
        print(
            f"[J9v1] {label(pair)}: ({g.size()} states) realized state at 32 in {{RUS}}'s kernel: "
            f"{inside}; departure along the realized path from 32: {dep} (path to tick "
            f"{32 + len(ids) - 1}); from tick 0, realized states inside: {len(inside0)} of "
            f"ticks 0..{n - 1}, last {inside0[-1] if inside0 else None}"
        )
        if pair[0] == "continental":
            print(f"[J9v1]   ({V0_RECORDED})")
        if not inside:
            failures.append(f"{label(pair)}: the state of 30 July is outside {{RUS}}'s kernel")
        if pair in FIGHT and dep != 33:
            failures.append(f"{label(pair)}: {{RUS}}'s departure from 32 at {dep}, not 33")
    print(f"[J9v1] done ({timer})")
    assert not failures, "; ".join(failures)
