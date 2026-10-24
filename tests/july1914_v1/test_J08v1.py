"""J8v1: registered 2026-10-24 in docs/july1914_testbed.md section 8.3 (the 1914 v1
registration, owner's decision 2h of 2026-10-23), before any v1 guard.

The July 1914 crisis at daily ticks (28 June to 4 August 1914), five principals with per-
actor cadence and Nature, in the v1 content of section 8.2. Do not edit the claim text
without a changelog entry in that document. Skipped until ``models/july1914/v1.py`` exists;
the model step replaces the body with the reading of the v1 decisions document.
"""

from pathlib import Path

import pytest

V1 = Path(__file__).resolve().parents[2] / "models" / "july1914" / "v1.py"

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


@pytest.mark.skipif(not V1.exists(), reason="1914 v1 not built")
def test_J8v1():
    raise NotImplementedError(CLAIM["id"])
