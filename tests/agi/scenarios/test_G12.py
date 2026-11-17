"""G12: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from models.agi import v0
from tests.agi.common import (
    EXPRS,
    HORIZON,
    OBJECTIVES,
    C,
    E,
    NotComputed,
    P,
    Parts,
    cut,
    first_sight,
    fixed,
    minimal_sets,
    record,
    relax,
    under,
)

CLAIM = {
    "id": "G12",
    "from_state": "`s₀`",
    "claim": (
        "narrative reproduction (content check, not hold-out): each storyline is an ordered "
        "list of waypoint state facts, and a storyline exists as a trace when there is a "
        "chain of shortest witnesses through its waypoints in order under a profile that "
        "forbids every speculative action, under some `a_objective`; the storylines: the AI "
        "2027 race branch (`last_L = race`; `cap ≥ si1` with `oversight ≤ weak`; `a_control = "
        "total`), the AI 2027 slowdown branch (`last_L = race`; `a_known ≥ suspected`; "
        "`regime = treaty ∧ oversight = strong`), and the typical Intelligence Rising plot "
        "(`last_L = race`; an `accident` event; `last_H` in {`fund_oversight`, `regulate_up`, "
        "`pause_mandate`}; then `regime = treaty` or a takeover ending); where a chain "
        "breaks, the minimal relaxation set of the first unreachable waypoint names the "
        "missing guard, and a missing action is the modeler's note"
    ),
    "expected": (
        "each chain exists, or the first unreachable waypoint with its minimal relaxation "
        "sets is reported"
    ),
    "sources": (
        "DESIGN.md section 8 (narrative reproduction); AI 2027; Intelligence Rising; "
        "framework_spec.md sections 5.4 and 6"
    ),
}

# The profile that forbids every speculative action is the build without them
# (``A.seize`` and ``Nature.unknown_capability``); ``last_H`` and ``last_L`` need the memory
# build. Nature has no memory, so "an accident event" is the event itself: the waypoint is
# passed on the transition in which Nature plays ``accident``.
BUILD = {"memory": True, "unknown_capability": False}
TAKEOVER = "any:wp_treaty,SILENT_TAKEOVER,not:no_overt_takeover"
STORYLINES = {
    "AI 2027, race branch": ["wp_race", "wp_si1_weak", "wp_total"],
    "AI 2027, slowdown branch": ["wp_race", "wp_suspected", "wp_treaty_strong"],
    "Intelligence Rising": ["wp_race", "event:Nature.accident", "wp_h_responds", TAKEOVER],
}
CHAINS = {name: C(waypoints, P, build=BUILD) for name, waypoints in STORYLINES.items()}
JOBS = list(CHAINS.values())


def expr_of(cm, waypoint: str):
    """The waypoint as a state fact for the bounded checker, or ``None`` for an event."""
    if waypoint == TAKEOVER:
        return EXPRS["wp_treaty"] | E(cm, "SILENT_TAKEOVER") | v0.OVERT_TAKEOVER
    return EXPRS.get(waypoint)


def reached(name: str) -> dict[str, int]:
    """The number of waypoints of the storyline passed in order, per objective."""
    return record(CHAINS[name])["value"]


def storyline(name: str):
    """The expected output: the chain exists, or the first unreachable waypoint is reported
    with its minimal relaxation sets (not computed where the bounded checker cannot ask)."""
    waypoints = STORYLINES[name]
    got = reached(name)
    whole = [o for o in OBJECTIVES if got[o] == len(waypoints)]
    if whole:
        return f"a trace passes through all {len(waypoints)} waypoints in order under {whole}"
    objective = max(OBJECTIVES, key=lambda o: got[o])
    first = waypoints[got[objective]]
    where = f"the chain breaks at waypoint {got[objective] + 1} ({first}) under {objective}"
    cm = fixed(objective, under(objective), **BUILD)
    expr = expr_of(cm, first)
    if expr is None:
        raise NotComputed(f"{where}: an event, not a state fact; no relaxation query is asked")
    res = relax(cm, HORIZON, expr)
    if res.reachable_as_is:
        raise NotComputed(
            f"{where}: the waypoint is reachable from s₀ on its own, so the order is what"
            " breaks; the relaxation after the earlier waypoints is a chained bounded query"
            " this run does not have"
        )
    sets = minimal_sets(res, where)
    return f"{where}: minimum {res.minimum_size} relaxation(s), minimal sets {sets}{cut(sets)}"


@first_sight
def test_G12():
    p = Parts("G12")
    for name in STORYLINES:
        p.report(
            f"{name}: waypoints passed in order, per objective", lambda name=name: reached(name)
        )
        p.check(
            f"{name}: the chain exists, or its break is named", lambda name=name: storyline(name)
        )
    p.finish()
