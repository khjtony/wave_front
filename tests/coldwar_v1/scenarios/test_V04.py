"""V4: Korea 1950: limited war reachable, general war blockable by the USA (C5).

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V4a. The readings the model step must fix before first sight are listed in
section 9.4.
"""

from pathlib import Path

import pytest

CLAIM = {
    "id": "V4",
    "from_state": "1950, June (the state of 1 January 1950), under `opportunist`",
    "claim": (
        "with `GENERAL_WAR_core` (`esc ≥ tactical_nuclear` between the USA and the USSR, not "
        "accidental), the PRC a principal and its Korean entry available: (a) a limited war "
        "in Korea is reachable (a state with `korea = armistice` and `esc < conventional`); "
        "(b) `⟨⟨USA⟩⟩□¬GENERAL_WAR_core` holds through 1 January 1954; (c) the United "
        "States' nuclear option in Korea is available only after a Chinese entry or "
        "US–Soviet combat (total commitment) and only with a reading of Soviet aims other "
        "than `opportunist`, and (b) holds with that option available; (d) the attractor of "
        "{USSR, PRC, Nature} to `GENERAL_WAR_core` by 1954 with the United States idle is "
        "reported with its first moves and with whether any move is a Soviet programme "
        "decision before its documented date or an escalation summed across two crises the "
        "record does not have standing together (the route of reports/cw_v0.md section 20); "
        "control: the 1950 state is outside `⟨⟨USA⟩⟩□(korea = peace)` through 1 January 1951 "
        "(the United States alone could not keep the Korean war away)"
    ),
    "expected": (
        "(a), (b), (c) and the control as stated, (b) also reported at the cut plus eight "
        "ticks (H8); (d) reported, not asserted; `status_quo` reported (the war needs "
        "Stalin's approval)"
    ),
    "sources": (
        "FRUS 1950; Gaddis 1982 and 2005; Weathersby 1993; Chen Jian 1994; Dingman 1988; "
        "Foot 1988; Mastny and Byrne 2005; Holloway 1994; re-asks C5"
    ),
}

BUILT = (Path(__file__).resolve().parents[3] / "models" / "cw" / "v1.py").exists()


@pytest.mark.skipif(not BUILT, reason="cw_v1 not built")
def test_V4():
    raise NotImplementedError(CLAIM["id"])
