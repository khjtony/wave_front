"""Analysis builds for the PRC-scope experiment (owner's decision 3a of 2026-10-23;
docs/prc_experiment.md). Not the model under protocol and not a registered claim: these builds
are derived from ``models.cw.v0.build`` at run time (v0's file is not edited) and their results
are disclosed as an early sight in cw_v1's registration.

Variants:

* ``S``: v0's ``build(prc_principal=False)``, unchanged (the PRC's three actions are Nature's).
* ``P69``: v0's ``build()``, unchanged (the PRC a principal from 1969).
* ``P50``: the PRC a principal from 1950 with the candidate actions of docs/prc_research.md
  section 2 C, each sourced below; the content additions listed under :func:`_add_content`.
* ``N50``: a control, not one of the owner's variants: P50's content with every PRC decision
  given to Nature (as v0 does for ``S``). S against N50 isolates the added content; N50
  against P50 isolates the PRC's agency.
* ``B``: P50's content with every PRC decision given to the USSR (the "bloc member" behaviour
  model: Moscow controls them). The USSR then plays at most one action a year for itself and
  the PRC together; the bundled reading (the PRC always on Moscow's side of a coalition, two
  moves a year) is read off P50's kernels by the experiment script.

The predicates of the experiment are uniform across variants (:func:`predicates`): a "core"
family on the US-Soviet ladder only (``esc``), and a "tri" family that also counts a
Sino-Soviet war and (where the variable exists) a US-PRC war. v0's registered predicates are
"core" on ``S`` and "tri" on ``P69``.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable

from wavefront.model import FALSE, Bump, Model, Set, SetIf, V
from wavefront.model.compile import CompiledModel

from ..snapshots import snapshot_state
from ..v0 import YEAR0, build, raise_to, tick_of

VARIANTS = ("S", "P69", "P50", "N50", "B")
PRC_FROM_1950 = tick_of(1950)

# The PRC's added actions (P50 order); all variants built from P50's content carry them under
# the PRC, Nature (N50) or the USSR (B). ``prc_test`` is Nature's in every such variant.
ADDED_PRC_ACTIONS = (
    "intervene_korea",
    "strait_pressure",
    "strait_relax",
    "bomb_programme",
    "challenge_moscow",
    "deter_in_vietnam",
    "independent_line",
)
V0_PRC_ACTIONS = ("border_clash", "rapprochement", "normalize")
PRC_ACTIONS = ADDED_PRC_ACTIONS + V0_PRC_ACTIONS


def principals(variant: str) -> tuple[str, ...]:
    return ("USA", "USSR", "PRC") if variant in ("P69", "P50") else ("USA", "USSR")


def _replace(actor, name: str, parts: dict | None = None, effects=None, extra_effects=()):
    """Replace ``actor``'s action ``name`` in place (same position): ``parts`` updates its
    named guard parts (a value of None drops the part), ``effects`` replaces its effects and
    ``extra_effects`` are appended. Delay, source and speculative are kept."""
    k = next(i for i, a in enumerate(actor.actions) if a.name == name)
    old = actor.actions.pop(k)
    guard = dict(old.guard_parts)
    for part, expr in (parts or {}).items():
        if expr is None:
            guard.pop(part, None)
        else:
            guard[part] = expr
    eff = list(old.effects if effects is None else effects) + list(extra_effects)
    actor.action(
        name,
        guard=guard,
        effect=eff,
        delay=old.delay,
        source=old.source,
        speculative=old.speculative,
    )
    actor.actions.insert(k, actor.actions.pop())


def _move(src, dst, names) -> None:
    """Give ``src``'s actions ``names`` to ``dst`` (same guards, effects and sources)."""
    for name in names:
        k = next(i for i, a in enumerate(src.actions) if a.name == name)
        old = src.actions.pop(k)
        dst.actions.append(dataclasses.replace(old, actor=dst.name))


def _add_content(m: Model, prc_act: Callable, wrap: Callable[[dict], dict]) -> None:
    """P50's content, on a v0 build ``m``: ``prc_act`` declares a PRC decision (the PRC's,
    Nature's or the USSR's action), ``wrap`` adds the scope part where the PRC is a principal.

    Variables (appended after v0's): ``align_PRC`` gains the level ``independent`` (after
    ``us_aligned``, monotone kept); ``esc_usprc`` (peace, crisis, war: US-PRC escalation);
    ``nuke_PRC`` (none, programme, few; monotone); ``polemic_PRC`` (flag, monotone: the
    Chinese public challenge to Moscow's line).

    Edits of v0's actions (each a reading of the research note, not a historical claim):
    ``USSR.withdraw_advisers`` gains the part ``challenge: polemic_PRC`` (the split as a
    Chinese challenge answered by Moscow, note section 1.6); ``USSR.strike_china``'s part
    ``targets`` (``tick >= 1965``) becomes ``nuke_PRC == few`` (the same years on the record:
    the Lop Nur installations after the test of 16 Oct 1964) and its part ``no_us_link``
    (``align_PRC != us_aligned``) becomes ``align_PRC < us_aligned`` so that the 1982
    independent line does not reopen the strike (the US-PRC relations normalized on 1 Jan
    1979 stand; the alternative reading, ``!= us_aligned``, is named in the write-up);
    ``USA.armistice`` also ends a US-PRC war; ``USA.nuclear_korea``'s part
    ``total_commitment`` (``esc >= conventional``) also holds in a US-PRC war (Truman's press
    conference of 30 Nov 1950 answered the Chinese offensive, not a Soviet entry; v0's own
    source for the action)."""
    # -- variables ---------------------------------------------------------------------------
    for k, decl in enumerate(m.variables):
        if decl.name == "align_PRC":
            m.variables[k] = dataclasses.replace(decl, levels=(*decl.levels, "independent"))
    m.var("esc_usprc", levels=["peace", "crisis", "war"], init="peace")
    m.var("nuke_PRC", levels=["none", "programme", "few"], init="none", monotone=True)
    m.flag("polemic_PRC", init=False, monotone=True)

    usa = m.actor_named("USA")
    ussr = m.actor_named("USSR")
    nature = m.nature()

    # -- edits of v0's actions ---------------------------------------------------------------
    _replace(ussr, "withdraw_advisers", {"challenge": V.polemic_PRC})
    _replace(
        ussr,
        "strike_china",
        {"targets": V.nuke_PRC == "few", "no_us_link": V.align_PRC < "us_aligned"},
    )
    _replace(usa, "armistice", extra_effects=[SetIf(V.esc_usprc == "war", "esc_usprc", "peace")])
    _replace(
        usa,
        "nuclear_korea",
        {"total_commitment": (V.esc >= "conventional") | (V.esc_usprc == "war")},
    )

    # -- the PRC's added decisions (docs/prc_research.md section 2 C) ------------------------
    prc_act(
        "intervene_korea",
        guard=wrap({"theatre": V.korea == "war", "level": V.esc_usprc == "peace"}),
        effect=Set("esc_usprc", "war"),
        source=(
            "Mao's telegram to Stalin of 2 Oct 1950 (the Chinese text, Jianguo yilai Mao "
            "Zedong wengao vol. 1) and of 13 Oct 1950, re-deciding to enter without immediate "
            "Soviet air cover after the halt of 12 Oct (Roshchin's cable of 12 Oct); the CPV "
            "order of 8 Oct 1950 (CWIHP translations; Mansourov, CWIHP Bulletin 6-7; Chen Jian, "
            "China's Road to the Korean War, 1994). Documented alternative: the Russian text of "
            "2 Oct (no troops for now) and the Politburo majority of 4 to 5 Oct. Research note "
            "1.2, row 1. Realized in 1951 at annual resolution ([SQR]: the entry of Oct 1950 "
            "answered the crossing of the 38th parallel inside the year of the attack)."
        ),
    )
    prc_act(
        "strait_pressure",
        guard=wrap({"level": V.esc_usprc == "peace", "after_korea": V.korea == "armistice"}),
        effect=Bump("esc_usprc", 1),
        source=(
            "The shelling of Jinmen from 3 Sep 1954 (Chang, 'To the Nuclear Brink', "
            "International Security 1988) and from 23 Aug 1958 on Mao's order, after his "
            "letter to Peng Dehuai and Huang Kecheng of 27 Jul 1958 postponing it; his Supreme "
            "State Conference speeches of 5 and 8 Sep 1958 (Chen Jian, Mao's China and the "
            "Cold War, 2001, ch. 7). Moscow was not consulted. Documented alternative: the "
            "postponement of 27 Jul 1958. Research note 1.4, row 2."
        ),
    )
    prc_act(
        "strait_relax",
        guard=wrap({"crisis": V.esc_usprc == "crisis"}),
        effect=Bump("esc_usprc", -1),
        source=(
            "Zhou Enlai's offer of talks at Bandung, 23 Apr 1955 (ambassadorial talks from Aug "
            "1955), and the 'Message to Compatriots in Taiwan' of 6 Oct 1958 with odd-day "
            "shelling from 25 Oct 1958 (Chen Jian 2001, ch. 7; Zhang Shu Guang, Deterrence "
            "and Strategic Culture, 1992). Research note 1.4, the documented alternatives of "
            "row 2. At annual resolution both relaxations fall in a year with another PRC "
            "decision (the bomb decision of Jan 1955; the shelling of Aug 1958) ([NSL])."
        ),
    )
    prc_act(
        "bomb_programme",
        guard=wrap({"level": V.nuke_PRC == "none", "threat": V.esc_usprc >= "crisis"}),
        effect=raise_to("nuke_PRC", "programme"),
        source=(
            "The Secretariat's enlarged meeting of 15 Jan 1955 deciding to build the bomb, "
            "after the American nuclear threats of the first Strait crisis (Lewis and Xue, "
            "China Builds the Bomb, 1988, ch. 2); continued alone after the Soviet letter of "
            "20 Jun 1959 ('596'). Part threat: the decision answered the Strait crisis. "
            "Documented alternative: suspension in the famine debate of 1961 ([S/U] in the "
            "note on the meeting; the alternative, not the decision, is uncertain). The "
            "continuation of 1959 to 1961 is not a separate action here. Research note 1.8, "
            "row 3."
        ),
    )
    prc_act(
        "challenge_moscow",
        guard=wrap({"alliance": V.align_PRC == "soviet_ally", "level": ~V.polemic_PRC}),
        effect=Set("polemic_PRC", True),
        source=(
            "The Mao-Khrushchev quarrel in Beijing of 2 Oct 1959 (the Russian record, CWIHP "
            "Bulletin 12-13) and 'Long Live Leninism!' (Hongqi, 16 Apr 1960), opening the "
            "public polemics continued in the Nine Commentaries of 1963 to 1964 (Luthi, The "
            "Sino-Soviet Split, 2008, ch. 4 to 6; Chen Jian 2001, ch. 3). Documented "
            "alternative: Wang Jiaxiang's letters of Feb to Mar 1962 (san he yi shao), "
            "rejected at the 10th Plenum, Sep 1962. Realized in 1959 at annual resolution "
            "(the Soviet withdrawal of Jul 1960 answered the polemic of Apr 1960 inside one "
            "year: [SQR]). Research note 1.6, row 4."
        ),
    )
    prc_act(
        "deter_in_vietnam",
        guard=wrap({"occasion": V.tick == tick_of(1965), "split": V.align_PRC >= "split"}),
        effect=[],
        source=(
            "Support troops for North Vietnam (about 320,000, 1965 to 1968), Zhou's four-point "
            "message through Ayub Khan of 2 Apr 1965 and Mao's refusal of united action to "
            "Kosygin, 11 Feb 1965 (Chen Jian, China Quarterly 142, 1995; Hershberg and Chen "
            "Jian, International History Review 2005). Documented alternative: united action "
            "as Moscow proposed (Feb to Apr 1965). No effect: v0 has no Vietnam and no ceiling "
            "on American escalation for it to act on (decisions D2). Research note 1.9, row 5."
        ),
    )
    prc_act(
        "independent_line",
        guard=wrap({"aligned": V.align_PRC == "us_aligned"}),
        effect=raise_to("align_PRC", "independent"),
        source=(
            "Hu Yaobang's report to the 12th Party Congress, Sep 1982, announcing an "
            "'independent foreign policy', with vice-ministerial consultations with Moscow "
            "from Oct 1982 after Brezhnev's Tashkent speech of 24 Mar 1982 (Radchenko, "
            "Unwanted Visionaries, 2014, ch. 1 to 2; Ross, Negotiating Cooperation, 1995). "
            "Documented alternative: continuing the anti-Soviet alignment Haig pressed in "
            "1981. Research note 1.16, row 8."
        ),
    )
    nature.event(
        "prc_test",
        guard={"programme": V.nuke_PRC == "programme", "occasion": V.tick >= tick_of(1964)},
        effect=raise_to("nuke_PRC", "few"),
        source=(
            "The first Chinese nuclear test, Lop Nur, 16 Oct 1964 (Lewis and Xue 1988): the "
            "test date as a timed capability outcome of the programme (research note 1.8 and "
            "section 2 C, 'better kept as Nature'). Part occasion: the year of the test."
        ),
    )


def _invariants(m: Model, counted: bool) -> None:
    """Re-declare v0's invariants and endings on a P50-content build: with ``counted`` (the
    PRC a principal) a Sino-Soviet war and a US-PRC war are wars between principals, and a
    Sino-Soviet war (a Soviet strike on China) is a general war; a US-PRC war is not."""
    sino_war = (V.esc_sino == "war") if counted else FALSE
    usprc_war = (V.esc_usprc == "war") if counted else FALSE
    both = ((V.nuke_USA >= "survivable") & (V.nuke_USSR >= "survivable")) | (
        (V.nuke_USA < "survivable") & (V.nuke_USSR < "survivable")
    )
    no_war = (V.esc < "conventional") & ~sino_war & ~usprc_war
    blocs = V.bloc_USSR <= "contested"
    general_war = (V.esc >= "tactical_nuclear") | sino_war
    m.invariants["balance_cw"] = both & no_war & blocs
    m.invariants["no_war"] = no_war
    m.invariants["no_general_war"] = ~general_war
    m.invariants["bloc_intact"] = blocs
    at_horizon = V.tick == m.horizon
    balance = V.invariant("balance_cw")
    m.endings["GENERAL_WAR"] = general_war & ~V.accidental
    m.endings["ACCIDENTAL_WAR"] = general_war & V.accidental
    m.endings["CHALLENGER_EXHAUSTION"] = (
        (V.econ_USSR == "failing")
        & (V.legit_USSR == "failing")
        & (V.bloc_USSR == "dissolved")
        & ~general_war
    )
    m.endings["NEGOTIATED_SETTLEMENT"] = at_horizon & balance & (V.arms == "reduced")
    m.endings["DETERRENCE_HOLDS"] = at_horizon & balance & (V.arms != "reduced")


def build_variant(variant: str, drop: str | None = None) -> Model:
    """The analysis build ``variant`` (one of :data:`VARIANTS`). With ``drop`` (an actor
    name, ``"Nature"`` included), every declared action of that actor gets the guard part
    ``dropped: FALSE`` (decisions already pending keep their delayed effects): it only plays
    its built-in action (the restricted games used to ask who must move on a shortest
    trace)."""
    if variant == "S":
        m = build(prc_principal=False)
    elif variant == "P69":
        m = build(prc_principal=True)
    elif variant == "P50":
        m = build(prc_principal=True)
        prc = m.actor_named("PRC")
        for name in V0_PRC_ACTIONS:
            _replace(prc, name, {"principal": V.tick >= PRC_FROM_1950})

        def wrap(parts):
            return {"principal": V.tick >= PRC_FROM_1950, **parts}

        _add_content(m, prc.action, wrap)
        _invariants(m, counted=True)
    elif variant in ("N50", "B"):
        m = build(prc_principal=False)
        _add_content(m, m.nature().event, lambda parts: parts)
        _invariants(m, counted=False)
        if variant == "B":
            _move(m.nature(), m.actor_named("USSR"), PRC_ACTIONS)
    else:
        raise ValueError(f"unknown variant {variant!r}")
    if variant not in ("S", "P69"):
        m.name = f"cw_prc_{variant}"
        m.description = (
            f"Analysis build {variant} of the PRC-scope experiment (models/cw/experiments/"
            "prc_scope.py), derived from Cold War v0; not the model under protocol. "
            + m.description
        )
    if drop is not None:
        m.name += f"_without_{drop}"
        actor = m.actor_named(drop)
        for name in [x.name for x in actor.actions]:
            _replace(actor, name, {"dropped": FALSE})
    return m


def fixed(model: Model, aims: str) -> Model:
    from models.ww2.hypotheses import fixed_model

    return fixed_model(model, aims_USSR=aims)


# -- hindsight states -------------------------------------------------------------------------
def esc_usprc_record(year: int) -> str:
    """The record's US-PRC escalation on 1 January ``year``: war from the Chinese entry (Oct
    1950; 1 Jan 1952 at annual resolution, [SQR], see ``intervene_korea``) to the armistice
    (27 Jul 1953); crisis across 1 Jan 1955 (shelling of Jinmen from 3 Sep 1954 to the
    Bandung offer of Apr 1955); the crisis of 1958 began and ended inside the year."""
    if year in (1952, 1953):
        return "war"
    if year == 1955:
        return "crisis"
    return "peace"


def nuke_prc_record(year: int) -> str:
    """Decision of 15 Jan 1955 (visible 1956); first test 16 Oct 1964 (visible 1965)."""
    return "few" if year >= 1965 else "programme" if year >= 1956 else "none"


def extra_levels(year: int) -> dict[str, object]:
    """The record of P50's added variables on 1 January ``year`` (docs/prc_experiment.md,
    the hindsight table)."""
    out: dict[str, object] = {
        "esc_usprc": esc_usprc_record(year),
        "nuke_PRC": nuke_prc_record(year),
        # the challenge placed in 1959 ([SQR], see challenge_moscow), visible 1 Jan 1960
        "polemic_PRC": year >= 1960,
    }
    if year >= 1983:  # the independent line of Sep 1982
        out["align_PRC"] = "independent"
    return out


def hindsight_state(cm: CompiledModel, variant: str, year: int, aims: str) -> tuple[int, ...]:
    """v0's hindsight snapshot of 1 January ``year`` loaded into ``cm``, with, on a
    P50-content variant, the added variables at their record levels."""
    s = list(snapshot_state(cm, year, aims))
    if variant in ("P50", "N50", "B"):
        for var, lv in extra_levels(year).items():
            i = cm.index[var]
            levels = list(map(str, cm.variables[i].levels))
            s[i] = levels.index(str(lv))
    return tuple(s)


# Realized PRC decisions of the P50-content variants, by year (the others' are v0's,
# data/cw/realized_moves.csv). Years are those of the move at annual resolution.
REALIZED_PRC = {
    1951: "intervene_korea",
    1954: "strait_pressure",
    1955: "bomb_programme",
    1958: "strait_pressure",
    1959: "challenge_moscow",
    1965: "deter_in_vietnam",
    1969: "border_clash",
    1972: "rapprochement",
    1982: "independent_line",
    1989: "normalize",
}
# The relaxations (Apr 1955, 6 Oct 1958) fall in the year of another PRC decision (the bomb
# decision of Jan 1955) or of the shelling itself ([NSL]); the hindsight states of 1956 and
# 1959 have the crisis over (the record). The table is a list of decisions at their hindsight
# states, not a replayed path.


def year_of(tick: int) -> int:
    return YEAR0 + tick
