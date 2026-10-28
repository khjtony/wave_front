"""Cold War v1: the United States, the Soviet Union and the PRC (a principal from 1950),
1947 to 1991, one tick per year, with five crisis sub-games.

The model of docs/ontology_cw.md and docs/actions_cw.md (the sections marked v1) as settled
in docs/cw_v1_decisions.md, for the claims V1 to V10 registered on 2026-10-24 before any
cw_v1 guard (docs/coldwar_testbed.md section 9). It is v0 (``models/cw/v0.py``, which is not
edited and keeps its fingerprint) with the changes listed below, each with its dated source
in the ``source=`` of the action concerned and in docs/cw_v1_decisions.md section D. Every
guard, effect, delay, fairness constraint or profile edited after the first run of V1 to V10
is logged in docs/guard_changelog_cw.md.

Time, the hidden objective, the beliefs and the hindsight convention are v0's (decisions D1,
D3, D6 of docs/cw_v0_decisions.md; the owner's decision 3b).

Changes from v0 (docs/cw_v1_decisions.md D1 to D6):

* **The PRC a principal from 1950** (decision 3a; docs/prc_experiment.md section 7): the
  scope part ``principal`` of the PRC's actions is ``tick >= 3``; the Korean entry
  ``PRC.intervene_korea`` sets the new variable ``esc_usprc`` (the US-PRC war), which also
  opens the United States' nuclear option in Korea (``USA.nuclear_korea:total_commitment``)
  and is ended by the armistice. ``build(prc_principal=False)`` gives the PRC's decisions to
  Nature with the same guards and effects (claims V5 (b) and V10's control).
* **The American crisis-initiating options of the 1970s and 1980s** (decision 2m):
  ``USA.confront_cienfuegos`` (1970), ``USA.confront_brigade`` (1979) and
  ``USA.blockade_cuba`` (1981), each a documented, rejected alternative, with the Soviet
  resolution under the 1962 understanding (``USSR.reaffirm_understanding``).
  ``build(us_crisis_options=False)`` omits the three options (the analysis build of V2's
  control).
* **The C5 route** (decision 5a): ``USSR.icbm_buildup`` gains the dated part ``technology``
  (the silo-based ICBMs of the third generation were decided in 1962 and 1963), and a move
  that opens combat raises ``esc`` to ``conventional`` instead of adding to a rung reached
  in another theatre or by the other side (``USA.escalate``, ``USSR.escalate``,
  ``USSR.enter_korea``, ``USSR.invade_west``).
* **Two new sub-games** (decision 2m): the Sino-Soviet confrontation of 1969, entered by the
  PRC's ``border_clash`` (now a crisis action with the occasion 1969), and the October 1973
  alert, entered by ``USSR.warn_unilateral`` (Brezhnev's message of 24 Oct 1973).
* **The border talks of 1969 carried into the coarse game** (the owner's decision 7f(a) of
  2026-10-27, before first sight): the 1969 sub-game's exit sets the new monotone flag
  ``sino_soviet_talks`` when the talks were agreed (Kosygin and Zhou, 11 Sep 1969; the talks
  opened 20 Oct 1969) and no strike was made, and ``USSR.strike_china`` gains the part
  ``talks`` (``¬sino_soviet_talks``).
* **Predicates** of coldwar_testbed.md section 9.2: ``no_war_core``, ``both_or_neither``,
  ``balance_core``, ``balance_tri``, ``no_general_war_core``; v0's ``balance_cw``,
  ``no_war``, ``no_general_war`` and ``bloc_intact`` with a US-PRC war counted as a war
  between principals.

``flat(cm)`` attaches the five sub-games (framework spec section 14).
"""

from __future__ import annotations

from wavefront.engine import flatten
from wavefront.engine.multires import FlatModel
from wavefront.model import FALSE, Bump, Model, SetIf, V
from wavefront.model.compile import CompiledModel

from . import v0
from .crises import able_archer_1983, alert_1973, berlin_1948, cuba_1962, sino_soviet_1969
from .v0 import DATA, HORIZON, ROOT, YEAR0, raise_to, tick_of

__all__ = [
    "DATA",
    "DATA_V1",
    "HORIZON",
    "PRC_FROM",
    "REALIZED_MOVES",
    "ROOT",
    "SUBGAMES",
    "US_CRISIS_OPTIONS",
    "YEAR0",
    "build",
    "crises",
    "flat",
    "model",
    "tick_of",
]

DATA_V1 = DATA / "v1"
REALIZED_MOVES = DATA_V1 / "realized_moves.csv"
PRC_FROM = tick_of(1950)  # the PRC a principal from 1950 (coldwar_testbed.md section 9.1)
US_CRISIS_OPTIONS = ("confront_cienfuegos", "confront_brigade", "blockade_cuba")
SUBGAMES = {
    "berlin_1948": berlin_1948,
    "cuba_1962": cuba_1962,
    "sino_soviet_1969": sino_soviet_1969,
    "alert_1973": alert_1973,
    "able_archer_1983": able_archer_1983,
}


def _edit(actor, name: str, parts=None, effects=None, note: str = "") -> None:
    """Replace ``actor``'s action ``name`` in place (same position): ``parts`` updates its
    named guard parts (a new part is appended), ``effects`` replaces its effects and ``note``
    is appended to its source, so that every v1 change carries its own dated source."""
    k = next(i for i, a in enumerate(actor.actions) if a.name == name)
    old = actor.actions.pop(k)
    guard = dict(old.guard_parts)
    guard.update(parts or {})
    actor.action(
        name,
        guard=guard,
        effect=list(old.effects if effects is None else effects),
        delay=old.delay,
        source=old.source + (" v1: " + note if note else ""),
        speculative=old.speculative,
    )
    actor.actions.insert(k, actor.actions.pop())


def build(
    prc_principal: bool = True,
    frozen_oversight: bool = False,
    us_crisis_options: bool = True,
) -> Model:
    """The Cold War v1 coarse model. ``prc_principal=False`` gives the PRC's decisions to
    Nature and a war of the PRC is then not a war between principals (V5 (b), V10's
    control); ``frozen_oversight=True`` drops every effect on ``oversight`` (V7's control,
    as v0's build); ``us_crisis_options=False`` omits the American crisis-initiating options
    of the 1970s and 1980s (V2's control)."""
    m = v0.build(prc_principal=prc_principal, frozen_oversight=frozen_oversight)
    m.name = (
        "cw_v1"
        + ("" if prc_principal else "_prc_scripted")
        + ("_frozen_oversight" if frozen_oversight else "")
        + ("" if us_crisis_options else "_no_us_crisis_options")
    )
    m.description = (
        "The Cold War, 1947 to 1991, one tick per year: the United States, the Soviet Union, "
        "the PRC (a principal from 1950) and Nature, after docs/ontology_cw.md and "
        "docs/actions_cw.md (v0 with the v1 sections) and docs/cw_v1_decisions.md"
        + ("" if prc_principal else "; the PRC's decisions carried by Nature")
        + ("" if us_crisis_options else "; without the American crisis-initiating options")
        + ". The validation model of the framework; every result is conditional on it and on "
        "its initial state."
    )

    # -- variables (ontology section 12.1) ---------------------------------------------------
    m.var("esc_usprc", levels=["peace", "war"], init="peace")
    m.flag("sino_soviet_talks", init=False, monotone=True)

    usa = m.actor_named("USA")
    ussr = m.actor_named("USSR")
    nature = m.nature()
    prc = m.actor_named("PRC") if prc_principal else nature
    prc_act = prc.action

    def prc_guard(parts: dict) -> dict:
        return {"principal": V.tick >= PRC_FROM, **parts} if prc_principal else parts

    # -- the PRC from 1950 (D1) --------------------------------------------------------------
    if prc_principal:
        for name in ("border_clash", "rapprochement", "normalize"):
            _edit(
                prc,
                name,
                {"principal": V.tick >= PRC_FROM},
                note=(
                    "The scope part principal is tick >= 3 (1950): the PRC a principal from "
                    "1950 on the owner's decision 3a of 2026-10-23 (docs/prc_research.md "
                    "section 2 A, the Korean entry of Oct 1950 the first of its own "
                    "decisions; docs/prc_experiment.md section 7)."
                ),
            )
    prc_act(
        "intervene_korea",
        guard=prc_guard({"theatre": V.korea == "war", "level": V.esc_usprc == "peace"}),
        effect=raise_to("esc_usprc", "war"),
        source=(
            "Mao's telegram to Stalin of 2 Oct 1950 (the Chinese text, Jianguo yilai Mao "
            "Zedong wengao vol. 1) and of 13 Oct 1950, re-deciding to enter without immediate "
            "Soviet air cover after the halt of 12 Oct (Roshchin's cable of 12 Oct); the CPV "
            "order of 8 Oct 1950; the crossing of the Yalu from 19 Oct 1950 (CWIHP "
            "translations; Mansourov, CWIHP Bulletin 6-7, 1995/96; Chen Jian, China's Road to "
            "the Korean War, 1994). Documented alternative: the Russian text of 2 Oct (no "
            "troops for now) and the Politburo majority of 4 to 5 Oct 1950. Realized in the "
            "1951 move at annual resolution ([SQR]: the entry answered the war of the same "
            "year, visible on 1 Jan 1951 only), visible 1 Jan 1952 on the model's path."
        ),
    )
    _edit(
        usa,
        "armistice",
        effects=[*_effects_of(usa, "armistice"), SetIf(V.esc_usprc == "war", "esc_usprc", "peace")],
        note=(
            "The armistice also ends the war with the Chinese People's Volunteers, a "
            "signatory beside the Korean People's Army (the Armistice Agreement of 27 Jul "
            "1953, FRUS 1952-54 vol. XV)."
        ),
    )
    _edit(
        usa,
        "nuclear_korea",
        {"total_commitment": (V.esc >= "conventional") | (V.esc_usprc == "war")},
        note=(
            "Part total_commitment also holds in a war with the PRC: Truman's press "
            "conference of 30 Nov 1950 answered the Chinese offensive of 25 to 28 Nov, not a "
            "Soviet entry, and the NSC deliberations of Feb and May 1953 concerned the war "
            "with the Chinese armies (Dingman 1988; Foot, The Wrong War, 1985; Chen Jian "
            "1994)."
        ),
    )

    # -- the Sino-Soviet border talks (D4; the owner's decision 7f(a) of 2026-10-27) ---------
    _edit(
        ussr,
        "strike_china",
        {"talks": ~V.sino_soviet_talks},
        note=(
            "Part talks: once the border talks agreed by Kosygin and Zhou at Beijing airport on "
            "11 Sep 1969 held (they opened in Beijing on 20 Oct 1969), the strike was no longer "
            "an option Moscow weighed: the threat had served to bring Beijing to talks, and the "
            "meeting removed its occasion (the Chinese record of the meeting, Wilson Center "
            "Digital Archive; Yang Kuisong, 'The Sino-Soviet Border Clash of 1969', Cold War "
            "History 2000; Gerson, The Sino-Soviet Border Conflict, CNA 2010; "
            "docs/prc_research.md section 1.12). The flag sino_soviet_talks is set by the exit "
            "of the 1969 sub-game when the talks were agreed and no strike was made. "
            "Documented alternative: Beijing's reading that the talks could cover a surprise "
            "attack (Lin Biao's Order No. 1 of 18 Oct 1969 and the dispersal of the "
            "leadership; Yang 2000), under which the strike option outlived the talks (the "
            "reading of docs/cw_v1_decisions.md D4 before the owner's decision 7f(a))."
        ),
    )

    # -- the C5 route (D3) -------------------------------------------------------------------
    _edit(
        ussr,
        "icbm_buildup",
        {"technology": V.tick >= tick_of(1962)},
        note=(
            "Part technology: a survivable force needed the silo-based ICBMs of the third "
            "generation, whose development the Council of Ministers decreed on 16 Apr 1962 "
            "(R-36, SS-9) and 30 Mar 1963 (UR-100, SS-11); the first generation (R-7, tested "
            "21 Aug 1957) was soft and slow to launch, and the R-16's silo version entered "
            "service only in 1963 (Podvig (ed.), Russian Strategic Nuclear Forces, 2001; "
            "Zaloga, The Kremlin's Nuclear Sword, 2002; the decree dates not verified). No "
            "Soviet decision for a survivable force is documented before 1962."
        ),
    )
    combat = raise_to("esc", "conventional")
    composition = (
        "Effect: opening combat raises esc to conventional (combat between the principals' "
        "forces, the rung's threshold) instead of adding to a rung reached in another theatre "
        "or by the other side's move in the same year; nuclear rungs are reached only by a "
        "nuclear decision or an accident (Kahn, On Escalation, 1965, the rungs as thresholds "
        "each crossed by a decision; docs/cw_v1_decisions.md D3)."
    )
    _edit(usa, "escalate", effects=[combat, *_effects_of(usa, "escalate")[1:]], note=composition)
    _edit(ussr, "escalate", effects=[combat], note=composition)
    _edit(ussr, "enter_korea", effects=[combat], note=composition)
    _edit(
        ussr,
        "invade_west",
        effects=[combat, *_effects_of(ussr, "invade_west")[1:]],
        note=composition,
    )

    # -- the 1969 and 1973 sub-games (D4) ----------------------------------------------------
    _edit(
        prc,
        "border_clash",
        {"occasion": V.tick == tick_of(1969)},
        effects=[],
        note=(
            "A crisis action (spec section 14): the clashes of 2 and 15 Mar 1969 enter the "
            "sub-game models/cw/crises/sino_soviet_1969.py, whose exit sets esc_sino. Part "
            "occasion: the ambush was planned in Jan to Feb 1969, after the earlier rule of "
            "not firing first (Yang 2000); the sub-game's branch points are documented for "
            "that year only (decisions D5 of v0)."
        ),
    )
    ussr.action(
        "warn_unilateral",
        guard={"occasion": V.tick == tick_of(1973)},
        effect=[],
        source=(
            "Brezhnev's message to Nixon delivered by Dobrynin at 21:35 EDT on 24 Oct 1973, "
            "after Sadat's appeal for a joint Soviet-American force: if the United States "
            "would not act jointly, the USSR would consider 'taking appropriate steps "
            "unilaterally' (Israelyan, Inside the Kremlin during the Yom Kippur War, 1995; "
            "Kissinger, Years of Upheaval, 1982; FRUS 1969-76 vol. XXV). The crisis is the "
            "sub-game models/cw/crises/alert_1973.py. Documented alternative: the joint "
            "diplomacy of the ceasefire of 22 Oct (Resolution 338) without the threat, "
            "argued at the Politburo (Israelyan 1995). Part occasion: the October War of "
            "that year."
        ),
    )

    # -- the American crisis-initiating options of the 1970s and 1980s (D2) -----------------
    if us_crisis_options:
        usa.action(
            "confront_cienfuegos",
            guard={"occasion": V.tick == tick_of(1970), "level": V.esc == "peace"},
            effect=Bump("esc", 1),
            source=(
                "A public confrontation over the Soviet submarine base at Cienfuegos, found "
                "by U-2 photography of 16 Sep 1970: the course Kissinger urged after the "
                "photographs, a public demand backed by naval measures as in 1962, against "
                "Nixon's choice of a private warning to Dobrynin on 25 Sep 1970, answered by "
                "the TASS statement of 13 Oct 1970 (Kissinger, White House Years, 1979; "
                "Garthoff, 'Handling the Cienfuegos Crisis', International Security 1983; "
                "FRUS 1969-76 vol. XII; the naval measures considered not verified). "
                "Documented alternative, taken: the private warning. Effect: a standing "
                "confrontation carried across 1 Jan 1971."
            ),
        )
        usa.action(
            "confront_brigade",
            guard={"occasion": V.tick == tick_of(1979), "level": V.esc == "peace"},
            effect=Bump("esc", 1),
            source=(
                "Demanding the withdrawal of the Soviet combat brigade in Cuba, made public "
                "by Senator Church on 30 Aug 1979, with the confrontation Brzezinski urged "
                "against Vance's counsel, rejected in Carter's address of 1 Oct 1979, which "
                "accepted Brezhnev's assurance with added surveillance of Cuba (Brzezinski, "
                "Power and Principle, 1983; Vance, Hard Choices, 1983; Newsom, The Soviet "
                "Brigade in Cuba, 1987; Garthoff, Detente and Confrontation, 1994). "
                "Documented alternative, taken: the address of 1 Oct 1979. Effect: a "
                "standing confrontation carried across 1 Jan 1980."
            ),
        )
        usa.action(
            "blockade_cuba",
            guard={"occasion": V.tick == tick_of(1981), "level": V.esc == "peace"},
            effect=Bump("esc", 1),
            source=(
                "Haig's proposals of 1981 to 'go to the source' of the arms reaching El "
                "Salvador with a naval blockade or quarantine of Cuba, opposed by Weinberger "
                "and Baker and rejected at the NSC in Nov 1981 (Haig, Caveat, 1984; Cannon, "
                "President Reagan, 1991; Garthoff 1994; the NSC dates not verified). "
                "Documented alternative, taken: no military measure against Cuba. Effect: a "
                "standing confrontation carried across 1 Jan 1982."
            ),
        )
        # 1984 to 1991: a source search for documented, argued and rejected American
        # crisis-initiating options is pending (docs/cw_v1_decisions.md D2, 2026-10-27). Any
        # option it finds is declared here, inside this block, before first sight.
    ussr.action(
        "reaffirm_understanding",
        guard={
            "crisis": V.esc == "crisis",
            "understanding": V.tick >= tick_of(1963),
            "not_berlin": V.berlin_wall,
        },
        effect=Bump("esc", -1),
        source=(
            "The Soviet reaffirmation of the understanding of Oct to Nov 1962 on Cuba: the "
            "TASS statement of 13 Oct 1970 that no naval base was being built, and Brezhnev's "
            "message to Carter of 27 Sep 1979 that the brigade was a training centre whose "
            "status would not change (Garthoff 1983; Garthoff 1994; Vance 1983); the "
            "United States accepted each assurance (Kissinger's acceptance of Oct 1970; "
            "Carter's address of 1 Oct 1979), which here is its not escalating. Part "
            "understanding: the understanding exists from the Cuban crisis. Part not_berlin: "
            "a standing crisis with the sector border still open is Berlin's, which the "
            "Cuban understanding does not settle (USSR.lapse and USSR.build_wall do)."
        ),
    )

    # -- invariants and endings (ontology section 12.4; coldwar_testbed.md section 9.2) ------
    m.invariants.clear()
    m.endings.clear()
    for name in [n for n, kind in m._names.items() if kind in ("invariant", "ending")]:
        del m._names[name]
    sino_war = (V.esc_sino == "war") if prc_principal else FALSE
    usprc_war = (V.esc_usprc == "war") if prc_principal else FALSE
    both_or_neither = ((V.nuke_USA >= "survivable") & (V.nuke_USSR >= "survivable")) | (
        (V.nuke_USA < "survivable") & (V.nuke_USSR < "survivable")
    )
    no_war_core = V.esc < "conventional"
    no_war = no_war_core & ~sino_war & ~usprc_war
    blocs_intact = V.bloc_USSR <= "contested"
    general_war = (V.esc >= "tactical_nuclear") | sino_war
    m.invariant("balance_cw", both_or_neither & no_war & blocs_intact)
    m.invariant("no_war", no_war)
    m.invariant("no_general_war", ~general_war)
    m.invariant("bloc_intact", blocs_intact)
    m.invariant("no_war_core", no_war_core)
    m.invariant("both_or_neither", both_or_neither)
    m.invariant("balance_core", no_war_core & both_or_neither)
    m.invariant(
        "balance_tri",
        no_war_core & (V.esc_sino < "war") & (V.esc_usprc < "war") & both_or_neither,
    )
    m.invariant("no_general_war_core", ~((V.esc >= "tactical_nuclear") & ~V.accidental))

    at_horizon = V.tick == HORIZON
    balance = V.invariant("balance_cw")
    m.ending("GENERAL_WAR", general_war & ~V.accidental)
    m.ending("ACCIDENTAL_WAR", general_war & V.accidental)
    m.ending(
        "CHALLENGER_EXHAUSTION",
        (V.econ_USSR == "failing")
        & (V.legit_USSR == "failing")
        & (V.bloc_USSR == "dissolved")
        & ~general_war,
    )
    m.ending("NEGOTIATED_SETTLEMENT", at_horizon & balance & (V.arms == "reduced"))
    m.ending("DETERRENCE_HOLDS", at_horizon & balance & (V.arms != "reduced"))
    return m


def _effects_of(actor, name: str) -> list:
    return list(next(a for a in actor.actions if a.name == name).effects)


def crises(prc_principal: bool = True, names=tuple(SUBGAMES)):
    """The crisis sub-games of v1 (spec section 14); with ``prc_principal=False`` the 1969
    sub-game is the build in which the PRC's decisions are Nature's, entered by Nature."""
    out = []
    for name in names:
        mod = SUBGAMES[name]
        if name == "sino_soviet_1969":
            out.append(mod.crisis(prc_principal=prc_principal))
        else:
            out.append(mod.crisis())
    return out


def flat(cm: CompiledModel, prc_principal: bool = True, names=tuple(SUBGAMES)) -> FlatModel:
    """The coarse v1 game ``cm`` with the named crisis sub-games inlined."""
    return flatten(cm, crises(prc_principal, names))


model = build()
