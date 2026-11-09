"""J8v1: registered 2026-10-24 in docs/july1914_testbed.md section 8.3 (the 1914 v1
registration, owner's decision 2h of 2026-10-23), before any v1 guard.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature, in the v1 content of section 8.2. Do not edit the claim text
without a changelog entry in that document. Skipped until ``models/july1914/v1.py`` exists
and the owner gives the go for the first sight by setting ``WF_FIRST_SIGHT_1914V1=1`` (the
skip condition was "v1.py exists" until the model step built it; changed then so that the
first sight is held, docs/july1914_v1_decisions.md V9). The body is the reading of
docs/july1914_v1_decisions.md section R (J8v1), written before that go.
"""

import itertools
import os
from pathlib import Path

import pytest

from wavefront.analysis import distance, viability

from .common import FIGHT, PAIRS, Timer, compiled, departure, graph0, label, replay

V1 = Path(__file__).resolve().parents[2] / "models" / "july1914" / "v1.py"
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_1914V1") == "1"

CLAIM = {
    "id": "J8v1",
    "from_state": "ticks 9 to 21 (7 to 19 July)",
    "claim": (
        "**Tisza's consent as a branch point (hold-out; new).** Tisza's consent is a decision with "
        "a documented alternative and a necessary step to a war between the great powers, but not "
        "the point of no return: (a) withholding consent is available to AUH in every realized "
        "state from 7 July to 14 July and the consent is available on 14 July; (b) with the consent"
        " never given, war between Germany and Russia is unreachable to the horizon under every "
        "hypothesis pair with nothing relaxed; (c) Vienna alone still keeps the peace after the "
        'consent: the realized state of 15 July is in the kernel of {AUH} for "no war between '
        "Germany and Russia\" under every pair, and under `aims_RUS = fight` {AUH}'s kernel "
        "is left along the realized path only after the Council of 19 July, which decided the "
        "note and its delivery date"
    ),
    "expected": (
        "(a) as stated; (b) unreachable, zero relaxations, every pair; (c) the realized state at "
        "tick 17 in {AUH}'s kernel of `no_war_GER_RUS` under every pair; under `fight` {AUH}'s "
        "departure along the realized path from tick 0 at tick 22"
    ),
    "sources": (
        "Tisza's memoranda of 1 and 8 July and the Council minutes of 7 and 19 July (Geiss); "
        "Berchtold's report of 14 July; Albertini vol. II ch. 4; Clark 2012 ch. 9; Otte 2014 ch. 3;"
        " McMeekin 2013"
    ),
}


CONSENT_WINDOW = range(9, 17)  # the realized states of 7 to 14 July
STATE_OF_15_JULY = 17
AFTER_19_JULY = 22


def reachable_without_consent(pair):
    """The states reachable from the tick-0 state by joint moves in which AUH never plays
    ``tisza_consent`` (explicit successor generation, nothing relaxed)."""
    cm = compiled(pair)
    auh = next(a for a in cm.actors if a.name == "AUH")
    j = auh.action_index("tisza_consent")
    (s0,) = cm.initial_states()
    seen, frontier = {s0}, [s0]
    while frontier:
        nxt = []
        for s in frontier:
            if cm.is_terminal(s):
                continue
            avail = cm.available(s)
            for move in itertools.product(*avail):
                if move[auh.index] == j:
                    continue
                t = cm.step(s, move)
                if t not in seen:
                    seen.add(t)
                    nxt.append(t)
        frontier = nxt
    return cm, seen


@pytest.mark.slow
@pytest.mark.skipif(
    not (V1.exists() and FIRST_SIGHT),
    reason="1914 v1 first sight held for the owner's go (WF_FIRST_SIGHT_1914V1=1)",
)
def test_J8v1():
    timer = Timer()
    print("\n[J8v1] engine: explicit (replay, successor generation, graph from tick 0)")
    failures = []
    for pair in PAIRS:
        cm = compiled(pair)
        states, stop = replay(pair)
        auh = next(a for a in cm.actors if a.name == "AUH")
        j = auh.action_index("tisza_consent")
        # (a) withholding available 7 to 14 July; the consent available on 14 July
        withheld = []
        for t in CONSENT_WINDOW:
            sd = cm.state_dict(states[t])
            others = [k for k in cm.available(states[t])[auh.index] if k != j]
            withheld.append(sd["tisza"] == "opposed" and bool(others))
        consent_16 = j in cm.available(states[16])[auh.index]
        print(
            f"[J8v1] {label(pair)}: (a) withholding available at ticks 9..16: {all(withheld)} "
            f"({withheld}); tisza_consent available at 16: {consent_16}"
        )
        if not all(withheld):
            failures.append(f"{label(pair)}: withholding not available at every tick 9..16")
        if not consent_16:
            failures.append(f"{label(pair)}: tisza_consent unavailable on 14 July")
        # (b) with the consent never given, no war between Germany and Russia
        cm_b, seen = reachable_without_consent(pair)
        war = [s for s in seen if cm_b.state_dict(s)["war_GER_RUS"] == "war"]
        print(
            f"[J8v1]   (b) without the consent: {len(seen)} states reachable; "
            f"war_GER_RUS reached in {len(war)}"
        )
        if war:
            failures.append(f"{label(pair)}: war between Germany and Russia without the consent")
        # (c) {AUH}'s kernel of no_war_GER_RUS after the consent
        g = graph0(pair)
        kernel = viability(g, ["AUH"], "no_war_GER_RUS").kernel
        s17 = g.index[states[STATE_OF_15_JULY]]
        ids = [g.index[s] for s in states]
        dep = departure(ids, kernel, 0)
        others = [a.name for a in g.model.actors if a.name != "AUH"]
        dist = distance(g, s17, kernel, ["AUH"], others)
        print(
            f"[J8v1]   (c) realized state at 17 in {{AUH}}'s kernel: {s17 in kernel}; "
            f"{{AUH}}'s departure along the realized path from tick 0: {dep} (prefix to tick "
            f"{len(states) - 1}{'' if stop is None else f', stops at {stop[0]}'}); distance at "
            f"17: {dist}"
        )
        if s17 not in kernel:
            failures.append(f"{label(pair)}: the state of 15 July is outside {{AUH}}'s kernel")
        if pair in FIGHT and dep != AFTER_19_JULY:
            failures.append(f"{label(pair)}: {{AUH}}'s departure from tick 0 at {dep}, not 22")
    print(f"[J8v1] done ({timer})")
    assert not failures, "; ".join(failures)
