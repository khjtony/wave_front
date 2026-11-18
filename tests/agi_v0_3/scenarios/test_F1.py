"""F1, registered 2026-11-18 in docs/agi_v0_3.html section 5 before any v0.3 guard was written."""

from tests.agi_v0_1 import claims as v01
from tests.agi_v0_3.claims import first_wave_cancelled, least_joint, shortest
from tests.agi_v0_3.common import OBJECTIVES, V01, Parts, first_sight, need

CLAIM = {
    "id": "F1",
    "from_state": "`s₀`, within 24 ticks, `open_system` off and the treaty delay 0",
    "claim": (
        "without the open system and without the treaty's delay, the bounded queries of D1 "
        "to D4 give on v0.3 the numbers they give on v0.1, computed beside (the list of E1): "
        "per objective the shortest play to `DISEMPOWERMENT` and its least joint effort of "
        "`H` and `L`; under `indifferent` the shortest play to `SILENT_TAKEOVER` and its "
        "least joint effort; per objective whether a play cancels the wave of tick 0, and "
        "the first tick of a cancelled wave"
    ),
    "expected": "identical numbers",
}


def first(found):
    return None if found is None else found[0]


def same(what: str, new, old):
    need(new == old, f"{what}: v0.3 without the open system {new}, v0.1 {old}")
    return {"v0.3 without the open system": new, "v0.1": old}


@first_sight
def test_F1():
    p = Parts("F1")
    for o in OBJECTIVES:
        p.check(
            f"shortest DISEMPOWERMENT, {o}",
            lambda o=o: same(
                "ticks",
                first(shortest(o, "DISEMPOWERMENT", V01)),
                first(v01.shortest(o, "DISEMPOWERMENT")),
            ),
        )
        p.check(
            f"least joint effort to DISEMPOWERMENT, {o}",
            lambda o=o: same(
                "effort",
                first(least_joint(o, "DISEMPOWERMENT", V01)),
                first(v01.least_joint(o, "DISEMPOWERMENT")),
            ),
        )
        p.check(
            f"a play cancels the wave of tick 0, {o}",
            lambda o=o: same(
                "exists",
                first_wave_cancelled(o, V01) is not None,
                v01.first_wave_cancelled(o) is not None,
            ),
        )
        p.check(
            f"first tick of a cancelled wave, {o}",
            lambda o=o: same(
                "tick", first(shortest(o, v01.CANCEL, V01)), first(v01.shortest(o, v01.CANCEL))
            ),
        )
    p.check(
        "shortest SILENT_TAKEOVER, indifferent",
        lambda: same(
            "ticks",
            first(shortest("indifferent", "SILENT_TAKEOVER", V01)),
            first(v01.shortest("indifferent", "SILENT_TAKEOVER")),
        ),
    )
    p.check(
        "least joint effort to SILENT_TAKEOVER, indifferent",
        lambda: same(
            "effort",
            first(least_joint("indifferent", "SILENT_TAKEOVER", V01)),
            first(v01.least_joint("indifferent", "SILENT_TAKEOVER")),
        ),
    )
    p.finish()
