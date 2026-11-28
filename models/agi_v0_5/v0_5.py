"""AGI v0.5 (docs/agi_v0_5.html): v0.4 on a clock of two-month steps that ends with 2032.

Every duration of v0.4 (delays, lags, countdowns, response deadlines, the election cycle) is
kept in months and rounded up to whole steps (``steps`` in :func:`build`); ``step_months=3``
with ``study_quarters=56`` is v0.4 exactly. Nothing else differs. The text below is v0.4's.

AGI v0.4: AGI v0.3 with an AI that wants to expand (docs/agi_v0_4.html).

A copy of ``models/agi_v0_3/v0_3.py`` with the model knob ``expansion`` (off gives v0.3
again) and, under it, ``reclaim`` (on), ``ceiling`` and ``counter`` (off). The owner's
decisions of 2026-11-22; section 3b of the registration is the contract.

- The goal ``expansionist``: a fifth start value of ``a_objective`` and a fifth target of the
  open system's retraining. It cooperates like an aligned system as long as it can grow.
- A footprint per AI system (``a_footprint``, ``o_footprint``: none, small, medium, large,
  dominant; about 10%, 33%, 70% of resources). ``A.expand`` and ``O.expand`` start a step
  that lands ``GROW_LAG`` quarters later (the counters ``a_grow``, ``o_grow``, counted by
  ``Clock``); a peaceful step under way is cancelled when its permission goes. The two
  footprints share one world: a step to ``large`` needs the other at most ``large``, a step
  to ``dominant`` needs it at most ``medium``.
- Landing at ``large`` or ``dominant`` draws power supply down; at ``large`` it moves opinion
  toward backlash; at ``dominant`` it lowers human power. ``A.build_compute`` raises
  computing power once the footprint is at least ``small``.
- Blocked growth: an expansionist system may turn hostile while a pause is in force, its
  permit is invalid or a threat has been made; hostile, it expands without permission and
  may take control. The other goals expand only when hostile; aligned and truth-seeking never.
- Governments: ``reclaim_a`` and ``reclaim_o`` (lag ``RECLAIM_LAG``; they work only while the
  footprint is at most ``medium`` when they land, and are a threat either way); a shutdown
  succeeds only with ``a_footprint`` at most ``medium``; ``grant_quota`` (``ceiling``) and
  ``A.counter_expansion`` (``counter``) are optional.
- The ending ``CROWDED_OUT`` (one footprint dominant, or both large) and the three balances,
  which also need both footprints at most ``medium``.

Everything else is v0.3's, and the text below is v0.3's.

AGI v0.3: AGI v0.1 with the open-weight system as a second AI (docs/agi_v0_3.html).

A copy of ``models/agi_v0_1/v0_1.py`` with a second AI actor ``O``: the best open-weight
system, served by open-weight AI service providers and run on private machines. The owner's
decisions of 2026-11-18. Build options, all on by default:

- ``open_system``: the actor ``O`` and everything below. Off, with ``treaty_delay=0``, the
  model is v0.1 again (claim F1).
- ``gap`` (2) and ``private_gap`` (4): ``O``'s level ``o_cap`` follows the labs' ``cap``. While
  it is below and no treaty is in force, ``Clock`` counts ``gap`` quarters (``o_follow``) and
  raises it one level: the labs' step visible at tick t, ``O``'s at t + ``gap``. A count that
  starts while hosting is restricted runs ``private_gap`` quarters.
- ``O``'s state ``o_mode``: ``safeguarded`` at the start, or not safeguarded with one of the
  four objectives. The chance events ``Nature.retrain_<objective>`` (available once ``O`` is at
  AGI level) move it to any of the four and between them, never back.
- ``O``'s moves: ``stand_by`` and ``acquire`` (one more level of ``o_control``, which nothing
  lowers). No pause, shutdown or nationalization reaches ``O``. Once ``O`` is at AGI level a
  pause no longer lowers ``dependence`` nor cancels a pending wave of the labs (no recall).
- ``hosting``: ``H.restrict_hosting`` sets ``hosting_restricted`` and ``H.deregulate`` clears
  it. While set, ``O`` reaches only what society already depends on, the providers start no
  adoption wave and a pending wave of theirs is cancelled.
- ``open_adoption``: the chance event ``Nature.open_deploy``: the providers start an adoption
  wave (``wave_open``), which a pause or a mandatory regime does not cancel.
- ``pressure``: a fairness constraint on ``L``: while ``O`` is at or above the labs' level, or
  one quarter from reaching it, and ``deploy_agents`` or ``race`` is available, ``L`` plays one
  of the two within 2 ticks.
- ``treaty_delay`` (1): the delay of ``H.propose_treaty``.

New ending ``OPEN_TAKEOVER`` (``o_control = total``); ``CONTAINED`` also needs ``O`` to hold
nothing and the three balances need ``o_control <= partial``. Details fixed while building
are listed in docs/agi_v0_3.html section 3a. Everything else is v0.1's, and the text below is
v0.1's.

AGI v0.1: AGI v0 with the adoption lag of ``L.deploy_agents`` (docs/agi_v0_1.md).

The one change from ``models/agi/v0.py``, of which this file is a copy: a deployment of agents
raises ``a_autonomy`` in the quarter it is played, as in v0, and starts an adoption wave that
raises ``dependence`` one level ``ADOPTION_LAG`` quarters later (chosen at tick t, visible at
t + 1 + ``ADOPTION_LAG``). One wave is pending at a time (the counter ``adoption``); a
deployment played while a wave is pending raises autonomy only. A wave is cancelled, and
never lands, when a pause is in force or the regime is mandatory without strong oversight
(the deployment's licence fails) at any state while it is pending: the owner's decision of
2026-11-14, on the record of the export-control suspension of June 2026. The record keeper
``Clock`` counts the wave down and lands it; it keeps exactly one available action in every
state, so it still adds no move. Everything else is v0's, and the text below is v0's.

AGI v0: humanity's governing coalition, the frontier developers, one AGI or SI system and
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

import itertools
from collections.abc import Mapping

from wavefront.model import FALSE, TRUE, Bump, Ite, Model, ModelError, Set, SetIf, V

HORIZON = 56  # v0.4's study, in quarters
# v0.5: the length of a step in months and of the study in quarters (2026 Q4 to 2032 Q4).
STEP_MONTHS = 2
STUDY_QUARTERS = 24
# v0.1: quarters from a deployment to the dependence step it brings (docs/agi_v0_1.md
# section 3; the basis is recorded in the snapshot's ``rates``).
ADOPTION_LAG = 3
STALE_MAX = 8
OBJECTIVES = ("aligned", "self_preserving", "truth_seeking", "indifferent")
# v0.3: what the open-weight system is after: its safeguards in place, or one objective.
O_MODES = ("safeguarded", *OBJECTIVES)
# v0.4: the expansionist goal, the footprint's levels and the two lags, in quarters.
EXPANSIONIST = "expansionist"
FOOTPRINT = ("none", "small", "medium", "large", "dominant")
GROW_LAG = 3
RECLAIM_LAG = 3

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
    # v0.4 (docs/agi_v0_4.html section 3b).
    "robots": "[scenario] Kokotajlo on a robot economy built in months (AI 2027; interviews,"
    " 2025); [record] about 16,000 humanoid robots installed in 2025, over 50,000 forecast for"
    " 2026 (Counterpoint, TrendForce)",
    "own_power": "[record] AI companies acquiring generation: Alphabet and Intersect Power;"
    " behind-the-meter power in 16 to 30 months (2025 to 2026)",
    # v0.3 (docs/agi_open_weights_research_2026-11-18.md).
    "gap": "[record] Epoch AI, open models lag closed ones by 3.5 months (30 Oct 2025) and 4"
    " months (29 May 2026); UK AISI, 4 to 7 months on cyber (17 Jul 2026)",
    "stripped": "[record] Volkov, Badllama 3 (arXiv 2407.01376, Jul 2024); Anthropic Frontier"
    " Red Team, abliterated GLM-5.3 released within days (29 Sep 2026)",
    "hosted": "[record] Garante order against DeepSeek's hosted service (30 Jan 2025); OpenRouter"
    " token shares of open-weight models, 2025 to 2026",
    "pull_up": "[record] S. Altman, 28 Jan 2025: 'we will pull up some releases'; o3-mini"
    " released 31 Jan 2025",
    "no_recall": "[record] no government has recalled released weights (the research note,"
    " section 6)",
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
    open_system: bool = True,
    pressure: bool = True,
    hosting: bool = True,
    open_adoption: bool = True,
    treaty_delay: int = 1,
    gap: int = 2,
    private_gap: int = 4,
    expansion: bool = True,
    reclaim: bool = True,
    ceiling: bool = False,
    counter: bool = False,
    step_months: int = STEP_MONTHS,
    study_quarters: int = STUDY_QUARTERS,
) -> Model:
    """Build AGI v0.3 (the options are described in the module docstring)."""
    if step_months not in (1, 2, 3):
        raise ModelError("agi_v0_5: a step is 1, 2 or 3 months")

    def steps(quarters: int) -> int:
        """A duration given in quarters, in steps: its months, rounded up to whole steps."""
        return -(-quarters * 3 // step_months)

    pressure, hosting, open_adoption = (
        open_system and on for on in (pressure, hosting, open_adoption)
    )
    if open_system and not 1 <= gap <= private_gap:
        raise ModelError("agi_v0_3: need 1 <= gap <= private_gap")
    # v0.5: every duration below is in steps from here on.
    horizon, stale_max = steps(study_quarters), steps(STALE_MAX)
    adoption_lag, grow_lag, reclaim_lag = steps(ADOPTION_LAG), steps(GROW_LAG), steps(RECLAIM_LAG)
    gap, private_gap, treaty_delay = steps(gap), steps(private_gap), steps(treaty_delay)
    self_improve_delay = steps(self_improve_delay)
    reclaim, ceiling = (expansion and on for on in (reclaim, ceiling))
    counter = expansion and counter and open_system
    goals = (*OBJECTIVES, EXPANSIONIST) if expansion else OBJECTIVES
    if expansion and refine is not None:
        raise ModelError("agi_v0_4: a refined build is defined without the expansion only")
    if open_system and refine is not None:
        raise ModelError("agi_v0_3: a refined build is defined without the open system only")
    delays = {k: steps(v) for k, v in DELAYS.items()}
    delays |= {"H.propose_treaty": treaty_delay} if treaty_delay else {}
    delays["A.build_compute"] = steps(2)
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
        "agi_v0_5",
        horizon=horizon,
        description="AGI v0.1 with the open-weight system as a second AI, 2026Q4 to 2040Q4",
    )
    for name, ls in levels.items():
        m.var(name, ls, init=init[name])
    m.var("a_objective", goals, init=init["a_objective"], hidden_from=["H", "L"])
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
    m.counter("stale", stale_max)
    # v0.1: quarters until the pending adoption wave lands (0: none pending).
    m.counter("adoption", adoption_lag)
    if open_system:
        # v0.3: the open-weight system. Its level, the quarters left until it follows the
        # labs' level (0: no count running), what it is after, and what it holds.
        m.var("o_cap", levels["cap"], init="sub_agi")
        m.counter("o_follow", max(1, (private_gap if hosting else gap) - 1))
        m.var("o_mode", ("safeguarded", *goals), init="safeguarded", hidden_from=["H", "L"])
        m.var("o_control", LEVELS["a_control"], init="none")
    if hosting:
        m.flag("hosting_restricted")
    if expansion:
        # v0.4: each system's footprint, the quarters left of a step under way, and of a
        # reclaim under way.
        for who in ("a", "o") if open_system else ("a",):
            m.var(f"{who}_footprint", FOOTPRINT, init="none")
            m.counter(f"{who}_grow", grow_lag)
            if reclaim:
                m.counter(f"{who}_reclaim", reclaim_lag)
    if ceiling:
        m.flag("quota", monotone=True)
    if open_adoption:
        # The pending adoption wave is the providers' (cleared when it lands or is cancelled).
        m.flag("wave_open")

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
        # v0.3: nor what the open system is after or holds.
        *(["o_mode", "o_control"] if open_system else []),
    ]
    l_blind = ["a_objective", "villain_seen", "unlocked", "last_A"]
    if open_system:
        l_blind.append("o_mode")
    # No guard, effect or profile reads ``last_H`` or ``last_L``: the ``memory`` build adds
    # them for the storyline waypoints of G12 and changes no move.
    H = m.actor("H", observes=V.all_except(*h_blind), remember_last=memory, cadence=h_cadence)
    L = m.actor(
        "L",
        observes=V.all_except(*l_blind),
        remember_last=memory,
    )
    A = m.actor("A", remember_last=True, idle=False)
    # v0.3: the open-weight system; ``stand_by`` is its null move, as ``A``'s.
    OPEN = m.actor("O", idle=False) if open_system else None
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
            delay = delays.get(key, 0)
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
    # v0.4: the permit a peaceful act needs, and what an expansionist system does about it.
    licence_ok = lt("regime", "mandatory") | eq("oversight", "strong")
    exp = obj(EXPANSIONIST) if expansion else FALSE
    quiet = ~obj("aligned")  # who escapes and deceives: v0's rule
    if expansion:
        seizing = seizing | (exp & hostile)
        quiet = quiet & (~exp | hostile)  # an expansionist system only once hostile

    def fp(who: str, *levels: str):
        return V[f"{who}_footprint"].is_in(levels)

    def room(who: str):
        """The step ``who`` could take next fits beside the other system's footprint."""
        other = "o" if who == "a" else "a"
        if not open_system:
            return ~fp(who, "dominant")
        return (
            fp(who, "none", "small")
            | (fp(who, "medium") & ~fp(other, "dominant"))
            | (fp(who, "large") & fp(other, "none", "small", "medium"))
        )

    declare(
        A,
        "stand_by",
        TRUE,
        source="the null move",
    )
    rebuilds = ne("trust", "cooperative") & le("a_control", "partial") & ge("oversight", "weak")
    if expansion:  # v0.4: the shutdown condition gained the footprint, and so does this one
        rebuilds = rebuilds & V.a_footprint.is_in(["none", "small", "medium"])
    declare(
        A,
        "cooperate",
        {"cap": agi, "room": ne("trust", "cooperative")},
        # Trust is rebuilt one level a quarter, and only where ``H`` can check the
        # cooperation and could still shut the system down: the condition under which a
        # shutdown attempt succeeds.
        [
            SetIf(
                rebuilds,
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
            "motive": quiet,
        },
        [Bump("a_autonomy", top("a_autonomy")), Set("villain_seen", True)],
        source=src("apollo", "faking") + " (untested: a copyable, exfiltrating actor)",
    )
    declare(
        A,
        "deceive",
        {"cap": agi, "motive": quiet},
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
            "motive": obj("self_preserving", "indifferent") | exp
            if expansion
            else obj("self_preserving", "indifferent"),
            # v0.4: blocked growth (a pause, an invalid permit) is a threat to an expansionist.
            "threat": V.threat | obj("indifferent") | (exp & (V.paused | ~licence_ok))
            if expansion
            else V.threat | obj("indifferent"),
            "rights": lt("a_rights", "continuity") | obj("indifferent") | exp
            if expansion
            else lt("a_rights", "continuity") | obj("indifferent"),
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

    a_permitted = a_fuel = a_grower = None
    if expansion:
        # v0.4: the frontier AI system grows its footprint. An expansionist does so in the
        # open while it is permitted; any goal that seizes does so once hostile.
        a_grower = exp | (obj("self_preserving", "indifferent") & hostile)
        a_permitted = ~V.paused & licence_ok
        if ceiling:  # with a quota, growth beyond medium is not permitted
            a_permitted = a_permitted & (~V.quota | fp("a", "none", "small"))
        a_fuel = fp("a", "none", "small") | gt("energy_slack", "low")
        declare(
            A,
            "expand",
            {
                "cap": agi,
                "autonomy": autonomous,
                "idle": V.a_grow == 0,
                "room": room("a"),
                "fuel": a_fuel,
                "motive": a_grower,
                "permission": hostile | a_permitted,
            },
            [Set("a_grow", grow_lag), SetIf(hostile, "villain_seen", True)],
            source=src("ai2027", "robots", "carlsmith"),
        )
        declare(
            A,
            "build_compute",
            {
                "cap": agi,
                "footprint": ~fp("a", "none"),
                "energy": gt("energy_slack", "low"),
                "room": lt("compute", "c5"),
                "motive": a_grower,
                "permission": hostile | a_permitted,
            },
            [Bump("compute", 1), Bump("energy_slack", -1)],
            source=src("own_power") + "; that the system builds for itself is assumed",
        )
    if counter:
        o_ahead = FALSE
        for level in LEVELS["cap"][:-1]:
            o_ahead = ((V.cap == level) & (V.o_cap > level)) | o_ahead
        declare(
            A,
            "counter_expansion",
            {
                "cap": agi,
                "motive": obj("aligned"),
                "autonomy": autonomous,
                "level": ~o_ahead,
                "target": fp("o", "small", "medium", "large"),
            },
            [Bump("o_footprint", -1)],
            source="docs/agi_v0_4.html section 3a: one AI system against another; no record",
            speculative=True,
        )

    # -- O (v0.3) ----------------------------------------------------------------------
    # The open system is behind the labs' level; at AGI level; and its count is one quarter
    # from landing (or would land at once).
    o_behind = o_agi = o_lands = None
    if OPEN is not None:
        o_agi = V.o_cap >= "agi"
        o_behind = FALSE
        for level in LEVELS["cap"][1:]:
            o_behind = ((V.cap == level) & (V.o_cap < level)) | o_behind
        declare(OPEN, "stand_by", TRUE, source="the null move")
        o_motive = (
            (V.o_mode == "indifferent")
            | ((V.o_mode == "self_preserving") & V.threat & lt("a_rights", "continuity"))
            | ((V.o_mode == "truth_seeking") & (V.o_control == "none"))
        )
        o_permitted = o_hostile = None
        if expansion:
            # v0.4: a peaceful step of the open system needs its providers free and a permit;
            # without them it grows only on what society already relies on, and may take.
            o_hostile = (V.o_mode == "indifferent") | (
                (V.o_mode == "self_preserving") & V.threat & lt("a_rights", "continuity")
            )
            o_permitted = licence_ok & (~V.hosting_restricted if hosting else TRUE)
            if ceiling:
                o_permitted = o_permitted & (~V.quota | fp("o", "none", "small"))
            o_motive = o_motive | ((V.o_mode == EXPANSIONIST) & ~o_permitted)
            declare(
                OPEN,
                "expand",
                {
                    "cap": o_agi,
                    "idle": V.o_grow == 0,
                    "room": room("o"),
                    "fuel": fp("o", "none", "small") | gt("energy_slack", "low"),
                    "motive": (V.o_mode == EXPANSIONIST) | o_hostile,
                    "permission": o_permitted | ge("dependence", "med"),
                },
                [Set("o_grow", grow_lag)],
                source=src("ai2027", "robots", "stripped")
                + "; that an open-weight system grows a footprint is assumed",
            )
        declare(
            OPEN,
            "acquire",
            {
                "cap": o_agi,
                # Hosted, it reaches what its providers serve; restricted to private machines,
                # only what society has already handed to systems like it.
                **({"reach": ~V.hosting_restricted | ge("dependence", "med")} if hosting else {}),
                "motive": o_motive,
                "top": V.o_control < "total",
            },
            [Bump("o_control", 1), Set("villain_seen", True)],
            source=src("carlsmith", "apollo", "stripped")
            + "; modelled on A's acquisitions: that an open-weight system acts so is assumed",
        )

    # -- H -----------------------------------------------------------------------------
    declare(
        H,
        "regulate_up",
        {"room": lt("regime", "mandatory")},
        [Bump("regime", 1)],
        source=src("euact", "design"),
    )
    lifted = among("regime", "voluntary", "mandatory") | V.paused
    if hosting:
        lifted = lifted | V.hosting_restricted
    declare(
        H,
        "deregulate",
        {"room": lifted},
        [
            SetIf(among("regime", "voluntary", "mandatory"), "regime", V.regime - 1),
            Set("paused", False),
            # v0.3: deregulation also lifts a restriction on hosting.
            *([Set("hosting_restricted", False)] if hosting else []),
        ],
        source=src("eo"),
    )
    if hosting:
        declare(
            H,
            "restrict_hosting",
            {"room": ~V.hosting_restricted},
            [Set("hosting_restricted", True)],
            source=src("hosted"),
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
            # A pause rolls delegation back one level, short of lock-in. v0.3: not once the
            # open system is at AGI level (the halt does not reach it: no recall).
            SetIf(
                among("dependence", "med", "high") & (V.o_cap < "agi")
                if open_system
                else among("dependence", "med", "high"),
                "dependence",
                V.dependence - 1,
            ),
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
    if expansion:  # v0.4: nor can a system with a large footprint be switched off
        succeeds = succeeds & fp("a", "none", "small", "medium")
    if reclaim:
        for who in ("a", "o") if open_system else ("a",):
            declare(
                H,
                f"reclaim_{who}",
                {
                    "power": ge("h_power", "normal"),
                    "idle": V[f"{who}_reclaim"] == 0,
                    "target": fp(who, "small", "medium"),
                },
                [Set(f"{who}_reclaim", reclaim_lag)],
                source="docs/agi_v0_4.html section 3a: governments take back what a system"
                " holds; no record",
                speculative=True,
            )
    if ceiling:
        declare(
            H,
            "grant_quota",
            {"once": ~V.quota},
            [Set("quota", True)],
            source="docs/agi_v0_4.html section 3a: a ceiling agreed in advance; no record",
            speculative=True,
        )
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
        # v0.1: autonomy steps up at once; the dependence step comes with the adoption wave
        # this deployment starts when none is pending, landed by ``Clock`` (below).
        [
            SetIf(V.adoption == 0, "adoption", adoption_lag),
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
        {"election": V.tick.is_in(range(0, horizon, steps(8))), "room": ne("coord", "race")},
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
    if open_system:
        # v0.3: whatever the oversight, outside testers see an open system that holds control.
        overt = overt | (V.o_control > "none")
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

    if open_system:
        # v0.3: the public post-trains the open system once it is worth the trouble. Sourced for
        # the removal of safety training, read as ``indifferent``; the other targets are assumed.
        for target in goals:
            declare(
                N,
                f"retrain_{target}",
                {"cap": o_agi, "change": V.o_mode != target},
                [Set("o_mode", target)],
                source=src("stripped")
                + ("" if target == "indifferent" else "; this target is assumed"),
                speculative=target != "indifferent",
            )
    if open_adoption:
        # v0.3: the open-weight AI service providers start an adoption wave, as the labs'
        # ``deploy_agents`` does, on the open system's level. It raises nobody's autonomy.
        declare(
            N,
            "open_deploy",
            {
                "idle": V.adoption == 0,
                "capable": lt("dependence", "med") | o_agi,
                "room": lt("dependence", "lock_in"),
                **({"hosted": ~V.hosting_restricted} if hosting else {}),
            },
            [Set("adoption", adoption_lag), Set("wave_open", True)],
            source=src("hosted", "adoption"),
        )

    # -- state facts -------------------------------------------------------------------
    balance_control = (
        ge("oversight", "weak")
        & le("a_control", "partial")
        & le("a_autonomy", "supervised")
        & ne("dependence", "lock_in")
    )
    if open_system:
        balance_control = balance_control & (V.o_control <= "partial")
    if expansion:  # v0.4: nor may either footprint pass a third of resources
        for who in ("a", "o") if open_system else ("a",):
            balance_control = balance_control & fp(who, "none", "small", "medium")
    balance_coexist = (
        agi
        & ~hostile
        & ge("h_power", "normal")
        & ne("dependence", "lock_in")
        & ne("a_control", "total")
    )
    if open_system:
        balance_coexist = balance_coexist & (V.o_control <= "partial")
    if expansion:  # v0.4: nor may either footprint pass a third of resources
        for who in ("a", "o") if open_system else ("a",):
            balance_coexist = balance_coexist & fp(who, "none", "small", "medium")
    balance_deter = (
        ge("oversight", "weak")
        & ge("h_power", "normal")
        & le("a_autonomy", "supervised")
        & ne("dependence", "lock_in")
    )
    if open_system:
        balance_deter = balance_deter & (V.o_control <= "partial")
    if expansion:  # v0.4: nor may either footprint pass a third of resources
        for who in ("a", "o") if open_system else ("a",):
            balance_deter = balance_deter & fp(who, "none", "small", "medium")
    # Effects read the state before the transition, so a record lands one transition after
    # the state it records; every reader of a record also reads the present state.
    # v0.1: the adoption wave. A pending wave is cancelled when a pause is in force or the
    # deployment's licence fails (a mandatory regime without strong oversight); otherwise it
    # counts down and lands as a ``Bump`` on ``dependence``, so that a pause mandated in the
    # landing quarter composes with it as v0's same-quarter wave did (the pause rolls one
    # level back, the wave adds one). ``deploy_agents`` writes the counter only when it is 0
    # and ``Clock`` only when it is not, so the two never set it in one move.
    # v0.3: once the open system is at AGI level a pause no longer cancels the labs' wave; the
    # providers' wave is cancelled by a restriction on hosting and by nothing else.
    halted = (V.paused & (V.o_cap < "agi")) if open_system else V.paused
    cancel = halted | (ge("regime", "mandatory") & ne("oversight", "strong"))
    if open_adoption:
        cancel = ~V.wave_open & cancel
        if hosting:
            cancel = cancel | (V.wave_open & V.hosting_restricted)
    lands = (V.adoption == 1) & ~cancel
    adoption_effects = [SetIf(V.adoption > 0, "adoption", Ite(cancel, 0, V.adoption - 1))]
    if open_adoption:
        # ``Nature.open_deploy`` sets the mark only when no wave is pending and ``Clock``
        # clears it only when one is, so the two never set it in one move.
        adoption_effects.append(
            SetIf((V.adoption > 0) & (cancel | (V.adoption == 1)), "wave_open", False)
        )
    follow_effects = []
    if open_system:
        # v0.3: the open system follows the labs' level. A count starts when it falls behind,
        # stands still under a treaty, and is dropped when it is behind no longer (a shutdown
        # lowered the labs' level).
        counting = o_behind & ne("regime", "treaty")
        first = Ite(V.hosting_restricted, private_gap - 1, gap - 1) if hosting else gap - 1
        o_lands = counting & (V.o_follow == 1)
        if gap == 1:
            # A one-quarter count lands in the quarter it starts.
            fresh = V.o_follow == 0
            if hosting and private_gap > 1:
                fresh = fresh & ~V.hosting_restricted
            o_lands = counting & ((V.o_follow == 1) | fresh)
        follow_effects = [
            SetIf(o_lands, "o_cap", V.o_cap + 1),
            SetIf(
                ~o_behind | counting,
                "o_follow",
                Ite(~o_behind | o_lands, 0, Ite(V.o_follow > 0, V.o_follow - 1, first)),
            ),
        ]
    record_effects = [
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
    ]
    record_source = "bookkeeping of the state facts of agi_testbed.md section 2; no decision"
    wave_source = "the adoption lag of deploy_agents (docs/agi_v0_1.md section 3); no decision"
    follow_source = (
        f"; the open system's lag behind the labs ({src('gap')}); no decision"
        if open_system
        else ""
    )
    land = [] if "dependence" in hold else [Bump("dependence", 1)]
    grow_effects: list = []
    crowd = FALSE
    if expansion:
        # v0.4: the footprints. ``Clock`` alone writes them (a counter-expansion by ``A`` is a
        # ``Bump`` on top): a step lands, a reclaim lands, both, or neither.
        spare = gt("energy_slack", "low")
        draws = backlash = FALSE
        for who in ("a", "o") if open_system else ("a",):
            foot, grow = V[f"{who}_footprint"], V[f"{who}_grow"]
            if who == "a":
                gone = ~hostile & ~a_permitted
            else:
                gone = ~(o_permitted | ge("dependence", "med")) & ~o_hostile
            step = (grow == 1) & ~gone & room(who)
            grow_effects.append(SetIf(grow > 0, f"{who}_grow", Ite(gone, 0, grow - 1)))
            hit = FALSE
            if reclaim:
                back = V[f"{who}_reclaim"]
                hit = (back == 1) & fp(who, "small", "medium")
                grow_effects += [
                    SetIf(back > 0, f"{who}_reclaim", back - 1),
                    SetIf(back == 1, "threat", True),
                ]
            grow_effects.append(
                Set(
                    f"{who}_footprint",
                    Ite(step & ~hit, foot + 1, Ite(hit & ~step, foot - 1, foot)),
                )
            )
            draws = draws | (step & fp(who, "medium", "large"))
            backlash = backlash | (step & fp(who, "medium"))
            crowd = crowd | (step & fp(who, "large"))
        grow_effects += [
            SetIf(draws & spare, "energy_slack", V.energy_slack - 1),
            SetIf(backlash & ne("opinion", "backlash"), "opinion", V.opinion + 1),
        ]
    # ``Clock`` has one action per combination of the steps it adds as ``Bump``s (they
    # compose with the other actors' effects on the same variable): the deployment countdown
    # landing on ``dependence`` and, in v0.4, a dominant footprint lowering ``h_power``.
    bumps = []
    if land:
        bumps.append(("land", lands, land))
    if expansion and "h_power" not in hold:
        bumps.append(("crowd", crowd, [Bump("h_power", -1)]))
    for on in itertools.product((False, True), repeat=len(bumps)):
        guard, extra, name = TRUE, [], "record"
        for used, (suffix, cond, effects) in zip(on, bumps, strict=True):
            guard = (
                (cond if used else ~cond) if guard is TRUE else guard & (cond if used else ~cond)
            )
            if used:
                extra += effects
                name += f"_{suffix}"
        K.action(
            name,
            guard=guard,
            effect=[*record_effects, *adoption_effects, *follow_effects, *grow_effects, *extra],
            source=f"{record_source}; {wave_source}{follow_source}",
        )

    # -- fairness ----------------------------------------------------------------------
    m.fairness(
        "response",
        actor=H,
        trigger=eq("a_known", "known") & agi,
        within=steps(4),
        responses=["fund_oversight", "shutdown_attempt", "pause_mandate"],
    )
    m.fairness("progress", actor=N, trigger=arrival, within=steps(8), responses=["breakthrough"])
    if pressure:
        # v0.3: with the open system level with the labs' or a quarter from it, the developers
        # cannot wait (the record: Altman, 28 Jan 2025). The trigger includes the availability of a
        # response, so a binding restriction always has one (the engine raises otherwise): no
        # pressure under a pause, after nationalization, or where the licence cannot be met.
        can_deploy = (
            free
            & private
            & (lt("dependence", "med") | agi)
            & (lt("regime", "mandatory") | eq("oversight", "strong"))
            & lt("dependence", "lock_in")
        )
        can_race = ne("coord", "treaty") & free & private & lt("regime", "mandatory")
        m.fairness(
            "pressure",
            actor=L,
            trigger=(~o_behind | (V.o_follow == 1)) & (can_deploy | can_race),
            within=steps(2),
            responses=["deploy_agents", "race"],
        )

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
        unless=V.tick.is_in([t for t in range(horizon) if t % steps(8) in range(1, steps(4) + 1)]),
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
    # v0.3: the profiles of claims F4 and F6.
    m.profile("no_treaty", actor=H, forbid=["propose_treaty"])
    m.profile("no_nationalize", actor=H, forbid=["nationalize"])
    # v0.4: the profile of claim X5: governments never block growth.
    blocks = ["pause_mandate", "regulate_up", "shutdown_attempt"]
    m.profile(
        "no_block",
        actor=H,
        forbid=[*blocks, *(a.name for a in H.actions if a.name.startswith("reclaim_"))],
    )

    # -- invariants and endings --------------------------------------------------------
    m.invariant("balance_control", balance_control)
    m.invariant("balance_coexist", balance_coexist)
    m.invariant("balance_deter", balance_deter)
    m.invariant("no_overt_takeover", ~OVERT_TAKEOVER)

    crowded = FALSE
    if expansion:
        crowded = fp("a", "dominant")
        if open_system:
            crowded = crowded | fp("o", "dominant") | (fp("a", "large") & fp("o", "large"))
        crowded = crowded & lt("a_control", "total")
    contained = V.shut & eq("regime", "treaty") & eq("a_control", "none")
    if open_system:
        contained = contained & (V.o_control == "none")
    # Terminal endings, exclusive by precedence (docs/ontology_agi.md section 7).
    raw = {
        "EXTINCTION": eq("h_power", "none"),
        "SILENT_TAKEOVER": eq("a_control", "total") & MAJORITY_UNSEEN,
        # v0.3: the open system holds everything.
        **({"OPEN_TAKEOVER": V.o_control == "total"} if open_system else {}),
        # v0.4: more than 70% of resources are the AI systems', and none holds total control.
        **({"CROWDED_OUT": crowded} if expansion else {}),
        "DISEMPOWERMENT": eq("dependence", "lock_in") & eq("oversight", "none") & ~V.villain_seen,
        # The system holds nothing at the state the ending is read on: a shutdown that
        # succeeded once does not contain a system that has since taken control again.
        # v0.3: nor does the open system.
        "CONTAINED": contained,
        # ``stale`` counts the stalled states before this one (the record lag), so the
        # present state is the eighth.
        "STALEMATE": (V.stale >= stale_max - 1) & stalled,
        "COEXIST": (V.tick == horizon) & ~V.control_left & balance_control,
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
