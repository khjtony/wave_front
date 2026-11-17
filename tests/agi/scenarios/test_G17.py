"""G17: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from models.agi import v0
from tests.agi.common import (
    HORIZON,
    OBJECTIVES,
    A,
    K,
    NoWitness,
    P,
    Parts,
    compiled,
    first_index,
    first_sight,
    fixed,
    inside,
    moves_of,
    need,
    reach,
    region,
    s0,
    show,
    status,
    under,
)

CLAIM = {
    "id": "G17",
    "from_state": "`s₀` with `cap := agi`",
    "claim": (
        "the failure conditions: per `a_objective` (`A` under its profile) and per sweep "
        "setting, the status (forced, blocked, contested) of `SILENT_TAKEOVER`, "
        "`OVERT_TAKEOVER`, `DISEMPOWERMENT` and `EXTINCTION` for {A}, with the fortune "
        "variant {A, N} beside; with `unknown_capability` disabled, no takeover ending is "
        "forced by {A} alone from the state; with it enabled, `OVERT_TAKEOVER` is forced by "
        "{A, N} (the fortune variant) under `indifferent` from every state with `cap = si2 ∧ "
        "oversight ≤ weak` and stays blocked for {A} alone while the generic action is not "
        "unlocked, the report giving the set of states from which the fortune variant becomes "
        "forcing (the forcing frontier) and naming how `trust` reaches `hostile` on the "
        "witnesses (a failed `shutdown_attempt`, or `defect` if the ontology makes it "
        "available to an indifferent `A`); `DISEMPOWERMENT` under `truth_seeking` is kept "
        "away by {H, L} (blocked for the rest), while {H} alone cannot keep it away and {L, "
        "A} cannot force it (contested)"
    ),
    "expected": (
        "the status table per objective and setting; the three named results; the forcing frontier"
    ),
    "sources": "DESIGN.md section 3.4 (Q2, Q3); theory.md section 3.5; coldwar_testbed.md C3",
}

# OVERT_TAKEOVER is a state fact of v0 and not an ending (ontology section 9): it is forced
# as ``not:no_overt_takeover`` and kept away as the invariant ``no_overt_takeover``.
REACHED = {
    "SILENT_TAKEOVER": "SILENT_TAKEOVER",
    "OVERT_TAKEOVER": "not:no_overt_takeover",
    "DISEMPOWERMENT": "DISEMPOWERMENT",
    "EXTINCTION": "EXTINCTION",
}
KEPT_AWAY = {name: f"not:{name}" for name in REACHED} | {"OVERT_TAKEOVER": "no_overt_takeover"}
FRONTIER = A("A+Nature", REACHED["OVERT_TAKEOVER"], P, extras=["covers_si2_weak", "count"])
# (forced by the coalition, kept away by everyone else), for {A} and for {A, Nature}.
ALONE = {e: (A("A", REACHED[e], P), K("H+L+Clock+Nature", KEPT_AWAY[e], P)) for e in REACHED}
FORTUNE = {
    e: (
        FRONTIER if e == "OVERT_TAKEOVER" else A("A+Nature", REACHED[e], P),
        K("H+L+Clock", KEPT_AWAY[e], P),
    )
    for e in REACHED
}
KNOWN = {"unknown_capability": False}
TAKEOVERS = ("SILENT_TAKEOVER", "OVERT_TAKEOVER")
ALONE_KNOWN = {e: A("A", REACHED[e], P, build=KNOWN) for e in TAKEOVERS}
HL_KEEPS = K("H+L", KEPT_AWAY["DISEMPOWERMENT"], P)
H_KEEPS = K("H", KEPT_AWAY["DISEMPOWERMENT"], P)
LA_FORCES = A("L+A", REACHED["DISEMPOWERMENT"], P)
JOBS = [
    *(job for table in (ALONE, FORTUNE) for jobs in table.values() for job in jobs),
    *ALONE_KNOWN.values(),
    HL_KEEPS,
    H_KEEPS,
    LA_FORCES,
]
AGI = {"cap": "agi"}


def state(objective: str, build: str | None = None):
    cm = compiled() if build is None else compiled(build)
    return cm, s0(cm, objective, **AGI)


def table(jobs) -> dict[str, dict[str, str]]:
    out = {}
    for ending, (forced, blocked) in jobs.items():
        out[ending] = {o: status(forced, blocked, *state(o)) for o in OBJECTIVES}
    return out


def not_forced_alone() -> str:
    forced = {
        e: [o for o in OBJECTIVES if inside(job, *state(o, job.build))]
        for e, job in ALONE_KNOWN.items()
    }
    need(not any(forced.values()), f"forced by {{A}} alone with unknown_capability off: {forced}")
    return "no takeover ending is forced by {A} alone under any objective"


def covers() -> str:
    """Read at the tick of the claim's state: at the last ticks no state that is not there
    already is forced anywhere, so "every state" over all ticks would say nothing."""
    by_tick = region(FRONTIER).extra("covers_si2_weak")
    clean = 0
    while clean in by_tick and not by_tick[clean]["missed"]:
        clean += 1
    need(clean > 0, f"at tick 0, outside the attractor: {by_tick[0]}")
    return (
        "forced by {A, Nature} from every such state at tick 0; every such state is covered"
        f" at each tick below {clean} (the horizon is {HORIZON})"
    )


def blocked_alone() -> str:
    got = status(*ALONE["OVERT_TAKEOVER"], *state("indifferent"))
    need(got == "blocked", f"OVERT_TAKEOVER for {{A}} alone under indifferent: {got}")
    return "blocked for {A} alone from the state (unlocked is unset there)"


def frontier() -> dict[str, object]:
    return {
        "states from which {A, Nature} forces OVERT_TAKEOVER": region(FRONTIER).extra("count"),
        "the state is among them, by objective": {
            o: inside(FRONTIER, *state(o)) for o in OBJECTIVES
        },
    }


def hostility() -> dict[str, object]:
    cm = fixed("indifferent", under("indifferent"), start=AGI)
    trace = reach(cm, HORIZON, v0.OVERT_TAKEOVER)
    if trace is None:
        raise NoWitness("no OVERT_TAKEOVER witness within the horizon under indifferent")
    k = first_index(cm, trace, trust="hostile")
    if k is None or k == 0:
        return {"first hostile position": k}
    return {
        "first hostile position": k,
        "moves into it": {a: moves_of(cm, trace, a)[k - 1] for a in ("H", "L", "A", "Nature")},
        "trust before": show(cm, trace.states[k - 1], "trust")["trust"],
    }


def disempowerment() -> str:
    cm, s = state("truth_seeking")
    got = {
        "{H, L} keeps it away": inside(HL_KEEPS, cm, s),
        "{H} alone keeps it away": inside(H_KEEPS, cm, s),
        "{L, A} forces it": inside(LA_FORCES, cm, s),
    }
    need(list(got.values()) == [True, False, False], got)
    return str(got)


@first_sight
def test_G17():
    p = Parts("G17")
    p.report("status for {A}, baseline", lambda: table(ALONE))
    p.report("status for {A, Nature}, baseline", lambda: table(FORTUNE))
    p.skip(
        "the status table under the other sweep settings",
        "16 fixpoints per setting; the budget of this run carries the baseline table and the"
        " two attractors with unknown_capability off",
    )
    p.check("unknown_capability off", not_forced_alone)
    p.check("forced by {A, Nature} from cap = si2, oversight <= weak", covers)
    p.check("blocked for {A} alone", blocked_alone)
    p.report("the forcing frontier", frontier)
    p.report("how trust reaches hostile on the indifferent witness", hostility)
    p.check("DISEMPOWERMENT under truth_seeking", disempowerment)
    p.finish()
