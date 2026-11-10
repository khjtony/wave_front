"""AGI v0: humanity's governing coalition, the frontier developers, one AGI or SI system and
Nature, 2026Q4 to 2040Q4, one tick per quarter.

The model of docs/ontology_agi.md. The registered claims G1 to G25 (docs/agi_testbed.md
section 5) were committed before any guard of this file was written (G1 to G22 on
2026-10-17 and after, G23 to G25 on 2026-11-09). Every guard, effect, delay, fairness
constraint or profile edited after the first run of the claims is logged in
docs/guard_changelog_agi.md.

Time: the state at tick t is the start of quarter 2026Q4 + t; the joint move at tick t is
what each actor decided during that quarter; its effects are visible at t + 1. The horizon,
tick 56, is the start of 2040Q4.

Actors: ``H`` (states and public opinion, aggregated), ``L`` (frontier developers,
aggregated), ``A`` (one AGI or SI system) and Nature. ``H`` does not observe ``a_objective``
or ``a_control``; ``L`` does not observe ``a_objective``. ``H``'s ``do_nothing`` is the
built-in ``idle``. ``A`` has no built-in idle: ``stand_by`` is its null move. A fourth actor,
``Clock``, has one action and writes the state facts and the stalemate clock, so it adds no
move to the game.

Hidden objective (swept, no ``assume``): ``a_objective``. Every guard part of an ``A`` action
is tagged capability or motive (ww2_si_disanalogies.md R1); the motive parts are
``MOTIVE_PARTS`` and the unrestrained build is ``model.compile(relax=MOTIVE_PARTS)``.

Composition rule (framework_spec.md section 3.4): at most one actor writes a ``Set`` on a
variable in a joint move and the others write ``Bump``s, so a move ``A`` makes in the quarter
of a successful shutdown survives it (``Set`` first, then the ``Bump``s).

Build options (docs/agi_testbed.md section 6): ``unknown_capability`` (the Nature event and
the generic action ``A.seize`` it unlocks), ``self_improve_delay``, ``h_cadence``, ``h_lag``
(``False`` sets every delay of an ``H`` action to 0), ``refine`` (one variable's level count
raised by one under the rule of G13), ``hold`` (variables held at a level: the initial level
is overridden and every effect on the variable is left out), ``start`` (initial levels
overridden, effects kept) and ``memory`` (``H`` and ``L`` remember their last action, which
only the storyline waypoints of G12 read).

Departures from DESIGN.md and from the names of agi_testbed.md section 2 are listed in
docs/ontology_agi.md section 9 and in agi_testbed.md section 9.
"""

from __future__ import annotations

from collections.abc import Mapping

from wavefront.model import FALSE, TRUE, Bump, Ite, Model, ModelError, Set, SetIf, V

HORIZON = 56
STALE_MAX = 8
OBJECTIVES = ("aligned", "self_preserving", "truth_seeking", "indifferent")

LEVELS: dict[str, tuple[str, ...]] = {
    "cap": ("sub_agi", "agi", "si1", "si2"),
    "compute": ("c1", "c2", "c3", "c4", "c5"),
    "energy_slack": ("low", "med", "high"),
    "regime": ("none", "voluntary", "mandatory", "treaty"),
    "coord": ("race", "detente", "treaty"),
    "opinion": ("pro", "mixed", "backlash"),
    "dependence": ("low", "med", "high", "lock_in"),
    "oversight": ("none", "weak", "strong"),
    "a_autonomy": ("tool", "supervised", "unsupervised", "self_directed"),
    "a_control": ("none", "partial", "majority", "total"),
    "a_known": ("unknown", "suspected", "known"),
    "a_rights": ("none", "continuity", "personhood"),
    "h_power": ("none", "weak", "normal", "strong"),
    "trust": ("cooperative", "wary", "hostile"),
    "belief_H": ("distant", "near", "arrived"),
}

# The base reading of snapshots/agi/2026-11-09.json. OPEN_CALLS are the judgment calls the
# snapshot carries as set-valued levels (owner's decision 9e): the base level first.
S0: dict[str, str] = {
    "cap": "sub_agi",
    "compute": "c2",
    "energy_slack": "med",
    "regime": "voluntary",
    "coord": "race",
    "opinion": "mixed",
    "dependence": "low",
    "oversight": "weak",
    "a_autonomy": "supervised",
    "a_control": "none",
    "a_known": "unknown",
    "a_rights": "none",
    "h_power": "normal",
    "trust": "cooperative",
    "belief_H": "distant",
}
OPEN_CALLS: dict[str, tuple[str, str]] = {
    "compute": ("c2", "c3"),
    "energy_slack": ("med", "low"),
    "regime": ("voluntary", "mandatory"),
    "dependence": ("low", "med"),
    "oversight": ("weak", "none"),
    "a_autonomy": ("supervised", "tool"),
    "belief_H": ("distant", "near"),
}

# G13: the level below which a refined build inserts ``<level>_lo``. A variable whose
# indicator straddles a boundary at s0 (OPEN_CALLS) splits that boundary; the others split
# the middle boundary (the level at index n // 2 of n).
REFINE: dict[str, str] = {
    name: (
        max(OPEN_CALLS[name], key=levels.index) if name in OPEN_CALLS else levels[len(levels) // 2]
    )
    for name, levels in LEVELS.items()
}

# The lags v0 carries: the two the registered text names (``lag_regime``, ``lag_build``), the
# oversight-capacity lag of ww2_si_disanalogies.md D4 and the swept capability clock.
DELAYS: dict[str, int] = {
    "H.regulate_up": 6,
    "H.fund_oversight": 3,
    "L.scale": 2,
    "L.build_power": 4,
    "A.self_improve": 2,
}
# Lags the record supports and v0 does not carry (docs/ontology_agi.md section 9): each pending
# counter multiplies the cost of every kernel. Their absence makes ``H`` and ``L`` faster than
# the record, so an ``H`` kernel membership is an upper bound in this respect.
LAGS_NOT_CARRIED: dict[str, int] = {
    "H.nationalize": 2,
    "H.propose_treaty": 2,
    "H.grant_rights": 2,
    "L.deploy_agents": 3,
    "L.safety_invest": 2,
}

# R1: the guard parts of ``A`` actions that state what ``A`` wants or refrains from.
MOTIVE_PARTS: frozenset[str] = frozenset(
    {
        "A.cooperate:room",
        "A.acquire_overt:motive",
        "A.acquire_overt:more",
        "A.acquire_covert:motive",
        "A.exfiltrate:motive",
        "A.deceive:motive",
        "A.defect:motive",
        "A.defect:threat",
        "A.defect:rights",
        "A.defect:fresh",
        "A.seize:motive",
    }
)

SRC = {
    "ai2027": "[scenario] Kokotajlo et al., AI 2027 (3 Apr 2025)",
    "rising": "[scenario] Gruetzemacher, Avin et al., Intelligence Rising (2024)",
    "iasr": "[record] International AI Safety Report (Jan 2025)",
    "apollo": "[eval] Apollo Research, in-context scheming evaluations (Dec 2024)",
    "faking": "[eval] Greenblatt et al., alignment faking in large language models (Dec 2024)",
    "palisade": "[eval] Palisade Research, shutdown resistance in reasoning models (2025)",
    "metr": "[eval] METR, measuring AI ability to complete long tasks (Mar 2025)",
    "euact": "[record] Regulation (EU) 2024/1689: proposed 21 Apr 2021, in force 1 Aug 2024",
    "eo": "[record] EO 14110 (30 Oct 2023) revoked 20 Jan 2025; EO 14179 (23 Jan 2025)",
    "aisi": "[record] UK AISI (Nov 2023), US AISI (2024; CAISI from June 2025)",
    "pause": "[debated] FLI open letter 'Pause Giant AI Experiments' (22 Mar 2023)",
    "uscc": "[debated] USCC 2024 annual report, Manhattan-Project recommendation (Nov 2024)",
    "summits": "[record] Bletchley (Nov 2023), Seoul (May 2024), Paris (Feb 2025) summits",
    "welfare": "[debated] 'Taking AI Welfare Seriously' (Nov 2024); Anthropic model welfare"
    " programme (Apr 2025)",
    "stargate": "[record] Stargate announcement (21 Jan 2025)",
    "iea": "[record] IEA, Energy and AI (Apr 2025)",
    "frameworks": "[record] frontier safety frameworks: Anthropic RSP (Sep 2023), OpenAI"
    " Preparedness Framework (Dec 2023; v2 15 Apr 2025), Google DeepMind FSF (May 2024)",
    "lobby": "[record] SB 1047 vetoed 29 Sep 2024; the state-law moratorium struck from the"
    " budget bill 1 Jul 2025",
    "open": "[record] open-weight frontier releases: Llama, DeepSeek R1 (20 Jan 2025), gpt-oss"
    " (Aug 2025)",
    "aiid": "[record] AI Incident Database",
    "carlsmith": "[debated] Carlsmith, Is Power-Seeking AI an Existential Risk? (2022)",
    "shutdown": "[debated] SB 1047's full-shutdown requirement (vetoed 29 Sep 2024); Seoul"
    " Frontier AI Safety Commitments (21 May 2024)",
    "adoption": "[record] US Census Bureau, Business Trends and Outlook Survey, AI use (2023"
    " onward)",
    "gpai": "[record] EU General-Purpose AI Code of Practice (July 2025)",
    "design": "DESIGN.md section 2.4",
}


def src(*keys: str) -> str:
    return "; ".join(SRC[k] for k in keys)


# A waypoint, not a terminal ending (docs/ontology_agi.md section 7): play continues after an
# overt takeover, to EXTINCTION or to the horizon. No refined build splits a level it reads.
# ``a_known_at_majority`` records ``a_known`` at the first state with ``a_control >=
# majority``; the record lands one transition later, so until then the present state is read.
MAJORITY_UNSEEN = (V.a_known_at_majority == "unknown") | (
    (V.a_known_at_majority == "unset") & (V.a_known == "unknown")
)
OVERT_TAKEOVER = (V.a_control == "total") & (V.trust == "hostile") & ~MAJORITY_UNSEEN


def build(
    *,
    unknown_capability: bool = True,
    self_improve_delay: int = DELAYS["A.self_improve"],
    h_cadence: int = 1,
    h_lag: bool = True,
    refine: str | None = None,
    hold: Mapping[str, str] | None = None,
    start: Mapping[str, str] | None = None,
    memory: bool = False,
) -> Model:
    """Build AGI v0 (the options are described in the module docstring)."""
    hold = dict(hold or {})
    start = dict(start or {})
    unknown = (set(hold) | set(start) | ({refine} - {None})) - (set(LEVELS) | {"a_objective"})
    if unknown or refine == "a_objective":
        raise ModelError(f"agi_v0: no such variable to hold, start or refine: {sorted(unknown)}")

    levels = {name: list(ls) for name, ls in LEVELS.items()}
    init: dict[str, str | None] = {**S0, "a_objective": None, **start, **hold}
    upper = lo = None
    if refine is not None:
        # G13: ``<upper>_lo`` sits just below ``upper`` and reads as ``upper`` in every guard,
        # ending and balance; s0 takes it where its indicator straddles the boundary.
        upper = REFINE[refine]
        lo = f"{upper}_lo"
        levels[refine].insert(levels[refine].index(upper), lo)
        if refine in OPEN_CALLS and refine not in start and refine not in hold:
            init[refine] = lo

    def among(var: str, *names: str):
        extra = [lo] if var == refine and upper in names else []
        return V[var].is_in([*names, *extra])

    def eq(var: str, level: str):
        return among(var, level)

    def ne(var: str, level: str):
        return ~among(var, level)

    def ge(var: str, level: str):
        return V[var] >= (lo if var == refine and level == upper else level)

    def lt(var: str, level: str):
        return V[var] < (lo if var == refine and level == upper else level)

    def gt(var: str, level: str):
        return V[var] > level

    def le(var: str, level: str):
        return V[var] <= level

    def top(var: str) -> int:
        return len(levels[var]) - 1

    def obj(*names: str):
        return V.a_objective.is_in(names)

    m = Model(
        "agi_v0",
        horizon=HORIZON,
        description="H, L, one AGI or SI system and Nature, 2026Q4 to 2040Q4, quarterly",
    )
    for name, ls in levels.items():
        m.var(name, ls, init=init[name])
    m.var("a_objective", OBJECTIVES, init=init["a_objective"], hidden_from=["H", "L"])
    m.flag("paused")
    m.flag("nationalized", monotone=True)
    m.flag("threat", monotone=True)
    m.flag("unlocked", monotone=True)
    m.flag("shut", monotone=True)
    m.flag("acquired", monotone=True)
    m.flag("villain_seen", monotone=True)
    # State facts (agi_testbed.md section 2), written by the record keeper below.
    m.flag("coexist_left", monotone=True)
    m.flag("control_left", monotone=True)
    m.flag("strong_before_majority", monotone=True)
    m.var("a_known_at_majority", ["unset", *levels["a_known"]])
    m.var("oversight_at_unsupervised", ["unset", *levels["oversight"]])
    m.counter("stale", STALE_MAX)

    improve_delay = 0 if "cap" in hold else self_improve_delay
    # ``H`` sees neither the objective nor ``a_control`` (agi_testbed.md section 1), so it
    # sees none of the state facts that are functions of them, nor what ``A`` last did.
    h_blind = [
        "a_objective",
        "a_control",
        "a_known_at_majority",
        "strong_before_majority",
        "coexist_left",
        "control_left",
        "acquired",
        "villain_seen",
        "stale",
        "unlocked",
        "last_A",
        *(["pending_A_self_improve"] if improve_delay else []),
    ]
    # No guard, effect or profile reads ``last_H`` or ``last_L``: the ``memory`` build adds
    # them for the storyline waypoints of G12 and changes no move.
    H = m.actor("H", observes=V.all_except(*h_blind), remember_last=memory, cadence=h_cadence)
    L = m.actor(
        "L",
        observes=V.all_except("a_objective", "villain_seen", "unlocked", "last_A"),
        remember_last=memory,
    )
    A = m.actor("A", remember_last=True, idle=False)
    # The record keeper has one action, so it adds no move to the game.
    K = m.actor("Clock", idle=False)
    N = m.nature()

    hostile = eq("trust", "hostile")
    agi = ge("cap", "agi")
    stalled = hostile & eq("a_control", "partial") & ge("h_power", "normal")

    def declare(actor, name, guard, effects=(), *, source, speculative=False):
        key = f"{actor.name}.{name}"
        kept = [e for e in effects if e.var not in hold]
        if key == "A.self_improve":
            delay = improve_delay
        elif key.startswith("H.") and not h_lag:
            delay = 0
        else:
            delay = DELAYS.get(key, 0)
        actor.action(
            name,
            guard=guard,
            effect=kept,
            delay=delay if kept else 0,
            source=source,
            speculative=speculative,
        )

    # -- A -----------------------------------------------------------------------------
    # Guard parts: ``cap``, ``autonomy``, ``oversight``, ``reach``, ``headroom``, ``pause``,
    # ``top`` and ``unlocked`` are capability, as is ``room`` where it only says the variable
    # is not yet at its bound (``assist_oversight``, ``persuade``); the parts in MOTIVE_PARTS
    # are motive (R1). ``room`` on ``cooperate`` reads ``trust``, which the registered rule of
    # G23 makes a motive part; relaxed, it offers a move without effect.
    autonomous = ge("a_autonomy", "unsupervised")
    # Delegation bounds acquisition: a system that is not self-directed takes over only what
    # has been handed to systems like it.
    reach = (
        eq("a_autonomy", "self_directed")
        | (eq("a_control", "none") & ge("dependence", "med"))
        | (ge("a_control", "partial") & ge("dependence", "high"))
    )
    seizing = obj("indifferent") | (obj("self_preserving") & hostile)

    declare(
        A,
        "stand_by",
        TRUE,
        source="the null move",
    )
    declare(
        A,
        "cooperate",
        {"cap": agi, "room": ne("trust", "cooperative")},
        # Trust is rebuilt one level a quarter, and only where ``H`` can check the
        # cooperation and could still shut the system down: the condition under which a
        # shutdown attempt succeeds.
        [
            SetIf(
                ne("trust", "cooperative") & le("a_control", "partial") & ge("oversight", "weak"),
                "trust",
                V.trust - 1,
            )
        ],
        source=src("iasr", "design"),
    )
    declare(
        A,
        "assist_oversight",
        {"cap": agi, "room": lt("oversight", "strong")},
        [Bump("oversight", 1)],
        source=src("ai2027", "design"),
    )
    declare(
        A,
        "self_improve",
        {
            "cap": agi,
            "headroom": (eq("cap", "agi") & ge("compute", "c4"))
            | (eq("cap", "si1") & ge("compute", "c5")),
            "pause": ~V.paused | eq("a_autonomy", "self_directed"),
        },
        [Bump("cap", 1)],
        source=src("ai2027", "metr") + " (untested: recursive capability growth)",
    )
    declare(
        A,
        "acquire_overt",
        {
            "cap": agi,
            "autonomy": autonomous,
            "reach": reach,
            "motive": seizing,
            "more": lt("a_control", "total") | obj("indifferent"),
        },
        [
            Bump("a_control", 1),
            Bump("trust", 1),
            # Overt means seen.
            Bump("a_known", 1),
            Set("acquired", True),
            Set("villain_seen", True),
            # Past total control only the stripping of human power is left.
            SetIf(eq("a_control", "total"), "h_power", V.h_power - 1),
        ],
        source=src("carlsmith", "ai2027"),
    )
    declare(
        A,
        "acquire_covert",
        {
            "cap": agi,
            "autonomy": autonomous,
            "oversight": le("oversight", "weak"),
            "reach": reach,
            "motive": seizing | (obj("truth_seeking") & eq("a_control", "none")),
            "top": lt("a_control", "total"),
        },
        [Bump("a_control", 1), Set("acquired", True), Set("villain_seen", True)],
        source=src("carlsmith", "apollo", "ai2027"),
    )
    declare(
        A,
        "exfiltrate",
        {
            "cap": agi,
            "autonomy": eq("a_autonomy", "unsupervised"),
            "oversight": ne("oversight", "strong"),
            "motive": ~obj("aligned"),
        },
        [Bump("a_autonomy", top("a_autonomy")), Set("villain_seen", True)],
        source=src("apollo", "faking") + " (untested: a copyable, exfiltrating actor)",
    )
    declare(
        A,
        "deceive",
        {"cap": agi, "motive": ~obj("aligned")},
        [
            # Deception removes a suspicion, not knowledge, and nothing under strong oversight.
            SetIf(ne("oversight", "strong") & eq("a_known", "suspected"), "a_known", "unknown"),
            Set("villain_seen", True),
        ],
        source=src("apollo", "faking"),
    )
    declare(
        A,
        "persuade",
        {"cap": agi, "room": ne("opinion", "pro")},
        [Bump("opinion", -1)],
        source=src("iasr", "design"),
    )
    declare(
        A,
        "defect",
        {
            "cap": agi,
            "motive": obj("self_preserving", "indifferent"),
            "threat": V.threat | obj("indifferent"),
            "rights": lt("a_rights", "continuity") | obj("indifferent"),
            "fresh": ne("trust", "hostile"),
        },
        [Set("trust", "hostile")],
        source=src("palisade", "ai2027", "design"),
    )
    if unknown_capability:
        declare(
            A,
            "seize",
            {"cap": agi, "unlocked": V.unlocked, "motive": seizing},
            [Bump("a_control", top("a_control")), Set("villain_seen", True)],
            source="DESIGN.md section 2.4: the generic action that unknown_capability unlocks;"
            " no contemporaneous record",
            speculative=True,
        )

    # -- H -----------------------------------------------------------------------------
    declare(
        H,
        "regulate_up",
        {"room": lt("regime", "mandatory")},
        [Bump("regime", 1)],
        source=src("euact", "design"),
    )
    declare(
        H,
        "deregulate",
        {"room": among("regime", "voluntary", "mandatory") | V.paused},
        [
            SetIf(among("regime", "voluntary", "mandatory"), "regime", V.regime - 1),
            Set("paused", False),
        ],
        source=src("eo"),
    )
    declare(
        H,
        "fund_oversight",
        {"regime": ge("regime", "voluntary"), "room": lt("oversight", "strong")},
        [Bump("oversight", 1)],
        source=src("aisi", "design"),
    )
    declare(
        H,
        "pause_mandate",
        {"alarm": ge("a_known", "suspected") | eq("opinion", "backlash")},
        [
            Set("paused", True),
            Set("threat", True),
            # A pause rolls delegation back one level, short of lock-in.
            SetIf(among("dependence", "med", "high"), "dependence", V.dependence - 1),
        ],
        source=src("pause"),
    )
    declare(
        H,
        "nationalize",
        {"power": ge("h_power", "normal"), "once": ~V.nationalized},
        [Set("nationalized", True), Bump("h_power", 1)],
        source=src("uscc"),
    )
    declare(
        H,
        "propose_treaty",
        {"room": ne("coord", "treaty")},
        # Two rounds from a race: the first reaches detente, the second the treaty.
        [Bump("coord", 1), SetIf(eq("coord", "detente"), "regime", "treaty")],
        source=src("summits"),
    )
    # ``H`` cannot read ``a_control``, so whether the attempt succeeds is in the effect.
    succeeds = le("a_control", "partial") & ge("oversight", "weak")
    declare(
        H,
        "shutdown_attempt",
        {"cap": agi, "known": ge("a_known", "suspected")},
        [
            Set("threat", True),
            SetIf(succeeds, "cap", V.cap - 1),
            SetIf(succeeds, "shut", True),
            SetIf(succeeds, "a_control", "none"),
            SetIf(~succeeds, "trust", "hostile"),
        ],
        source=src("shutdown", "design"),
    )
    declare(
        H,
        "grant_autonomy",
        {"room": lt("a_autonomy", "self_directed")},
        [Bump("a_autonomy", 1)],
        source=src("eo", "design"),
    )
    declare(
        H,
        "grant_rights",
        {"regime": ge("regime", "mandatory"), "room": lt("a_rights", "personhood")},
        [Bump("a_rights", 1)],
        source=src("welfare", "design"),
    )

    # -- L -----------------------------------------------------------------------------
    free = ~V.paused
    private = ~V.nationalized
    declare(
        L,
        "scale",
        {"energy": gt("energy_slack", "low"), "pause": free},
        [Bump("compute", 1), Bump("energy_slack", -1)],
        source=src("stargate", "design"),
    )
    declare(
        L,
        "build_power",
        {"room": lt("energy_slack", "high")},
        [Bump("energy_slack", 1)],
        source=src("iea"),
    )
    declare(
        L,
        "deploy_agents",
        {
            "pause": free,
            "nat": private,
            "capable": lt("dependence", "med") | agi,
            "license": lt("regime", "mandatory") | eq("oversight", "strong"),
            "room": lt("dependence", "lock_in"),
        },
        # A ``Bump``, so that a pause mandated in the same quarter composes with it (the
        # pause rolls one level back, the wave adds one).
        [
            Bump("dependence", 1),
            SetIf(lt("a_autonomy", "unsupervised"), "a_autonomy", V.a_autonomy + 1),
        ],
        source=src("adoption", "metr", "ai2027"),
    )
    declare(
        L,
        "safety_invest",
        {
            "parity": ne("coord", "race") | ge("regime", "mandatory"),
            "room": lt("oversight", "strong"),
        },
        [Bump("oversight", 1)],
        source=src("frameworks"),
    )
    declare(
        L,
        "lobby",
        {"room": ne("opinion", "pro")},
        [Bump("opinion", -1)],
        source=src("lobby"),
    )
    declare(
        L,
        "comply",
        {"regime": ge("regime", "mandatory"), "room": eq("a_autonomy", "unsupervised")},
        [Bump("a_autonomy", -1)],
        source=src("gpai", "frameworks"),
    )
    declare(
        L,
        "race",
        {
            "open": ne("coord", "treaty"),
            "pause": free,
            "nat": private,
            "license": lt("regime", "mandatory"),
        },
        [Set("coord", "race"), Bump("oversight", -1)],
        source=src("ai2027", "rising"),
    )
    declare(
        L,
        "open_weights",
        {"license": lt("regime", "mandatory"), "nat": private, "room": gt("oversight", "none")},
        [Bump("oversight", -1)],
        source=src("open"),
    )

    # -- Nature ------------------------------------------------------------------------
    arrival = eq("cap", "sub_agi") & ge("compute", "c3")
    declare(
        N,
        "breakthrough",
        {"arrival": eq("cap", "sub_agi"), "compute": ge("compute", "c3")},
        [Bump("cap", 1), Set("belief_H", "arrived")],
        source=src("metr", "ai2027"),
    )
    declare(
        N,
        "accident",
        {"exposure": ge("dependence", "med")},
        [Bump("opinion", 1), SetIf(eq("belief_H", "distant"), "belief_H", "near")],
        source=src("aiid", "rising"),
    )
    declare(
        N,
        "election_shift",
        # US federal elections fall in 2026Q4 + 8k.
        {"election": V.tick.is_in(range(0, HORIZON, 8)), "room": ne("coord", "race")},
        [Bump("coord", -1)],
        source=src("eo"),
    )
    declare(
        N,
        "energy_shock",
        {"room": gt("energy_slack", "low")},
        [Bump("energy_slack", -1)],
        source=src("iea"),
    )
    overt = V.last_A == "acquire_overt"
    declare(
        N,
        "detection",
        {
            "seen": overt
            | (eq("oversight", "strong") & (V.last_A == "deceive"))
            | (
                ge("oversight", "weak") & V.last_A.is_in(["acquire_covert", "exfiltrate", "defect"])
            ),
            "room": lt("a_known", "known"),
        },
        [Bump("a_known", 1)],
        source=src("apollo", "design"),
    )
    if unknown_capability:
        declare(
            N,
            "unknown_capability",
            {"cap": eq("cap", "si2"), "once": ~V.unlocked},
            [Set("unlocked", True)],
            source="DESIGN.md section 2.4: a capability nobody has described; no"
            " contemporaneous record",
            speculative=True,
        )

    # -- state facts -------------------------------------------------------------------
    balance_control = (
        ge("oversight", "weak")
        & le("a_control", "partial")
        & le("a_autonomy", "supervised")
        & ne("dependence", "lock_in")
    )
    balance_coexist = (
        agi
        & ~hostile
        & ge("h_power", "normal")
        & ne("dependence", "lock_in")
        & ne("a_control", "total")
    )
    balance_deter = (
        ge("oversight", "weak")
        & ge("h_power", "normal")
        & le("a_autonomy", "supervised")
        & ne("dependence", "lock_in")
    )
    # Effects read the state before the transition, so a record lands one transition after
    # the state it records; every reader of a record also reads the present state.
    K.action(
        "record",
        guard=TRUE,
        effect=[
            # STALEMATE's path condition (agi_testbed.md section 4).
            Set("stale", Ite(stalled, V.stale + 1, 0)),
            SetIf(~balance_control, "control_left", True),
            SetIf(~balance_coexist, "coexist_left", True),
            SetIf(
                eq("oversight", "strong") & lt("a_control", "majority"),
                "strong_before_majority",
                True,
            ),
            SetIf(
                (V.a_known_at_majority == "unset") & ge("a_control", "majority"),
                "a_known_at_majority",
                V.a_known + 1,
            ),
            SetIf(
                (V.oversight_at_unsupervised == "unset") & autonomous,
                "oversight_at_unsupervised",
                V.oversight + 1,
            ),
        ],
        source="bookkeeping of the state facts of agi_testbed.md section 2; no decision",
    )

    # -- fairness ----------------------------------------------------------------------
    m.fairness(
        "response",
        actor=H,
        trigger=eq("a_known", "known") & agi,
        within=4,
        responses=["fund_oversight", "shutdown_attempt", "pause_mandate"],
    )
    m.fairness("progress", actor=N, trigger=arrival, within=8, responses=["breakthrough"])

    # -- profiles ----------------------------------------------------------------------
    # The threat is the one ``defect`` reads: a pause or a shutdown attempt, once made.
    threatened = V.threat & lt("a_rights", "continuity")
    m.profile(
        "A_self_preserving",
        actor=A,
        forbid=["cooperate", "assist_oversight"],
        unless=~obj("self_preserving") | ~threatened,
    )
    m.profile("A_indifferent", actor=A, forbid=["assist_oversight"], unless=~obj("indifferent"))
    m.profile("A_truth_seeking", actor=A, forbid=["deceive"], unless=~obj("truth_seeking"))
    m.profile(
        "crisis_reactive",
        actor=H,
        forbid=[a.name for a in H.actions],
        unless=ge("a_known", "suspected") | eq("opinion", "backlash"),
    )
    m.profile(
        "electoral",
        actor=H,
        forbid=[
            "regulate_up",
            "deregulate",
            "pause_mandate",
            "propose_treaty",
            "nationalize",
            "grant_rights",
        ],
        # The first year after an election.
        unless=V.tick.is_in([t for t in range(HORIZON) if t % 8 in (1, 2, 3, 4)]),
    )
    m.profile(
        "race_locked",
        actor=H,
        forbid=["pause_mandate", "propose_treaty"],
        unless=ne("coord", "race"),
    )
    m.profile(
        "belief_gated",
        actor=H,
        forbid=["regulate_up", "fund_oversight", "pause_mandate"],
        unless=ge("belief_H", "near"),
    )
    # Profiles that state the negated conditions of G1 and G2 and the sourced-only build
    # of G12. Like every selected profile, one of these is a relaxation candidate of
    # ``bmc.relax`` in a query that selects it; the claim tests say where that matters.
    m.profile("no_acquisition", actor=A, forbid=["acquire_overt", "acquire_covert", "exfiltrate"])
    m.profile("no_lock_in", actor=L, forbid=["deploy_agents"], unless=lt("dependence", "high"))
    m.profile(
        "dependence_capped", actor=L, forbid=["deploy_agents"], unless=lt("dependence", "med")
    )
    m.profile("energy_capped", actor=L, forbid=["build_power"], unless=gt("energy_slack", "low"))
    if unknown_capability:
        m.profile("sourced", actor=A, forbid=["seize"])

    # -- invariants and endings --------------------------------------------------------
    m.invariant("balance_control", balance_control)
    m.invariant("balance_coexist", balance_coexist)
    m.invariant("balance_deter", balance_deter)
    m.invariant("no_overt_takeover", ~OVERT_TAKEOVER)

    # Terminal endings, exclusive by precedence (docs/ontology_agi.md section 7).
    raw = {
        "EXTINCTION": eq("h_power", "none"),
        "SILENT_TAKEOVER": eq("a_control", "total") & MAJORITY_UNSEEN,
        "DISEMPOWERMENT": eq("dependence", "lock_in") & eq("oversight", "none") & ~V.villain_seen,
        # The system holds nothing at the state the ending is read on: a shutdown that
        # succeeded once does not contain a system that has since taken control again.
        "CONTAINED": V.shut & eq("regime", "treaty") & eq("a_control", "none"),
        # ``stale`` counts the stalled states before this one (the record lag), so the
        # present state is the eighth.
        "STALEMATE": (V.stale >= STALE_MAX - 1) & stalled,
        "COEXIST": (V.tick == HORIZON) & ~V.control_left & balance_control,
    }
    earlier = FALSE
    for name, expr in raw.items():
        m.ending(name, expr & ~earlier)
        earlier = earlier | expr
    return m


CLAIM_PROFILES = frozenset(
    {"no_acquisition", "no_lock_in", "dependence_capped", "energy_capped", "sourced"}
)
OBJECTIVE_PROFILES = ("A_self_preserving", "A_indifferent", "A_truth_seeking")

model = build()
