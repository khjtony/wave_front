"""E1, registered 2026-11-17 in docs/agi_v0_2.html section 4 before any v0.2 guard was written."""

from tests.agi_v0_1 import claims as v01
from tests.agi_v0_2.claims import CANCEL, first_wave_cancelled, least_joint, shortest
from tests.agi_v0_2.common import OBJECTIVES, OFF, Parts, first_sight, need

CLAIM = {
    "id": "E1",
    "from_state": "`s₀`, within 24 ticks, every channel off",
    "claim": (
        "with the four channels off, the bounded queries of D1 to D4 give on v0.2 the "
        "numbers they give on v0.1, computed beside: per objective the shortest play to "
        "`DISEMPOWERMENT` and its least joint effort of `H` and `L`; under `indifferent` the "
        "shortest play to `SILENT_TAKEOVER` and its least joint effort; per objective "
        "whether a play cancels the wave of tick 0, and the first tick of a cancelled wave"
    ),
    "expected": "identical numbers",
}


def first(found):
    return None if found is None else found[0]


def same(what: str, new, old):
    need(new == old, f"{what}: v0.2 all off {new}, v0.1 {old}")
    return {"v0.2 all off": new, "v0.1": old}


@first_sight
def test_E1():
    p = Parts("E1")
    for o in OBJECTIVES:
        p.check(
            f"shortest DISEMPOWERMENT, {o}",
            lambda o=o: same(
                "ticks",
                first(shortest(o, "DISEMPOWERMENT", OFF)),
                first(v01.shortest(o, "DISEMPOWERMENT")),
            ),
        )
        p.check(
            f"least joint effort to DISEMPOWERMENT, {o}",
            lambda o=o: same(
                "effort",
                first(least_joint(o, "DISEMPOWERMENT", OFF)),
                first(v01.least_joint(o, "DISEMPOWERMENT")),
            ),
        )
        p.check(
            f"a play cancels the wave of tick 0, {o}",
            lambda o=o: same(
                "exists",
                first_wave_cancelled(o, OFF) is not None,
                v01.first_wave_cancelled(o) is not None,
            ),
        )
        p.check(
            f"first tick of a cancelled wave, {o}",
            lambda o=o: same(
                "tick", first(shortest(o, CANCEL, OFF)), first(v01.shortest(o, v01.CANCEL))
            ),
        )
    p.check(
        "shortest SILENT_TAKEOVER, indifferent",
        lambda: same(
            "ticks",
            first(shortest("indifferent", "SILENT_TAKEOVER", OFF)),
            first(v01.shortest("indifferent", "SILENT_TAKEOVER")),
        ),
    )
    p.check(
        "least joint effort to SILENT_TAKEOVER, indifferent",
        lambda: same(
            "effort",
            first(least_joint("indifferent", "SILENT_TAKEOVER", OFF)),
            first(v01.least_joint("indifferent", "SILENT_TAKEOVER")),
        ),
    )
    p.finish()
