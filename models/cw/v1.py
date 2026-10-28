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
* **The projected count** (the owner's decisions 7d and 7g of 2026-10-28, before first sight;
  docs/cw_v1_decisions.md D9): ``belief_force_USA`` is re-declared on its own scale, the
  number of Soviet intercontinental delivery vehicles the estimates project for two to three
  years ahead, in the bands of :data:`BANDS`, and the new monotone ``count_USSR`` is the number
  in being on the same bands (its hindsight truth), set by ``USSR.heavy_bombers``,
  ``USSR.first_icbms``, ``USSR.icbm_buildup`` and ``USSR.icbm_parity``; every guard part and
  effect that reads or sets the belief is re-expressed on the bands, and Nature's
  ``bomber_gap`` (NIE 11-56) carries the belief of 1957.
* **Predicates** of coldwar_testbed.md section 9.2: ``no_war_core``, ``both_or_neither``,
  ``balance_core``, ``balance_tri``, ``no_general_war_core``; v0's ``balance_cw``,
  ``no_war``, ``no_general_war`` and ``bloc_intact`` with a US-PRC war counted as a war
  between principals.

``flat(cm)`` attaches the five sub-games (framework spec section 14).
"""

from __future__ import annotations

from dataclasses import replace

from wavefront.engine import flatten
from wavefront.engine.multires import FlatModel
from wavefront.model import FALSE, Bump, Model, Set, SetIf, V
from wavefront.model.compile import CompiledModel

from . import v0
from .crises import able_archer_1983, alert_1973, berlin_1948, cuba_1962, sino_soviet_1969
from .v0 import DATA, HORIZON, ROOT, YEAR0, raise_to, tick_of

# The number of Soviet intercontinental delivery vehicles in bands (the owner's decision 7g of
# 2026-10-28; docs/ontology_cw.md sections 3 and 12.1; docs/cw_v1_decisions.md D9): ICBM
# launchers, SLBM launchers and heavy bombers (Bear, Bison; not the Backfire), as Norris and
# Cochran count the Soviet strategic offensive forces (data/cw/v1/strategic_launchers.csv).
# Edges: 200, the force the estimates judged able to threaten SAC's operational bases (NIE
# 11-8-60 of 1 Aug 1960, para. 7: 150 to 200 ICBM launchers at the start of 1961), and 1,000,
# numbers matching the American ICBM force (1,000 Minuteman and 54 Titan II from 1967).
BANDS = ["none", "under_200", "under_1000", "over_1000"]

__all__ = [
    "BANDS",
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
    # The owner's decision 7g (2026-10-28, before first sight): the hindsight count of Soviet
    # intercontinental delivery vehicles, and belief_force_USA re-declared in place (same
    # position, so v0's state layout is otherwise kept) as the projected count on its bands.
    m.var("count_USSR", levels=BANDS, init="none", monotone=True)
    k = next(i for i, d in enumerate(m.variables) if d.name == "belief_force_USA")
    m.variables[k] = replace(m.variables[k], levels=tuple(BANDS), init=0)

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

    # -- the force count and the projected count (D9; the owner's decisions 7d and 7g) -------
    # Each guard part and effect that reads or sets belief_force_USA, re-expressed on the
    # bands of the count; the count is set by the Soviet deployments. A detection effect
    # (``seen``) sets the belief to the force the deployment brings, as projected once seen by
    # satellite (intel_USA = overhead).
    def seen(level: str) -> SetIf:
        return SetIf(V.intel_USA == "overhead", "belief_force_USA", level)

    projected = (
        "On the count scale of the owner's decision 7g of 2026-10-28 (belief_force_USA the "
        "number of Soviet intercontinental delivery vehicles that the estimate projects for "
        "about two to three years after its date, in the bands of count_USSR; "
        "docs/cw_v1_decisions.md D9)."
    )
    _edit(
        ussr,
        "build_bomb",
        effects=[raise_to("nuke_USSR", "few")],
        note=(
            projected + " The bomb detected (Truman, 23 Sep 1949) set no projected count: the "
            "Tu-4 was a medium bomber with a one-way reach of the United States, not an "
            "intercontinental vehicle (Norris and Cochran, US-USSR Strategic Offensive Nuclear "
            "Forces 1946-1989, NRDC 1990, Definitions: a bomber designed for an operating "
            "radius over 2,500 n.m.); the estimates of intercontinental bombers begin with the "
            "BISON and BEAR (NIE 11-56, 6 Mar 1956)."
        ),
    )
    _edit(
        ussr,
        "icbm_buildup",
        effects=[
            raise_to("nuke_USSR", "survivable"),
            raise_to("count_USSR", "under_1000"),
            seen("over_1000"),
        ],
        note=(
            projected + " The buildup also brings the count to at least 200 to 999 (333 ICBM "
            "launchers at the end of 1966, Norris and Cochran 1990 Table 2). Seen by satellite, "
            "it is projected past 1,000: NIE 11-8-66 (20 Oct 1966) estimated 670 to 765 ICBM "
            "launchers for mid-1968 and 800 to 1,100 for mid-1971, beside some 150 heavy "
            "bombers and the ballistic missile submarines (M/H NIE 11-8-66, 13 Mar 1967)."
        ),
    )
    _edit(
        ussr,
        "mirv",
        effects=[raise_to("nuke_USSR", "overkill"), seen("over_1000")],
        note=(
            projected + " The MIRVed missiles replaced launchers rather than adding to them "
            "(1,587 ICBM launchers at the end of 1975, 1,398 from 1978; Norris and Cochran 1990 "
            "Table 2): seen, the projected count stays above 1,000."
        ),
    )
    _edit(
        usa,
        "strategic_buildup",
        {"missile_gap": V.belief_force_USA >= "under_1000"},
        note=(
            projected + " Part missile_gap: a projected Soviet force of 200 or more "
            "intercontinental vehicles, the force the estimates judged able to threaten SAC's "
            "bases (NIE 11-8-60, 1 Aug 1960, para. 7; its program A, 400 ICBM launchers for "
            "mid-1963, was the estimate in force when Kennedy decided in Mar 1961). The guard of "
            "an American decision reads the American estimate, not the hindsight count."
        ),
    )
    _edit(
        nature,
        "missile_gap",
        {"soviet_force": V.count_USSR == "under_200"},
        effects=[Set("belief_force_USA", "under_1000")],
        note=(
            projected + " Part soviet_force: a Soviet force in being of fewer than 200 "
            "intercontinental vehicles (28 at the end of 1957, all heavy bombers; Norris and "
            "Cochran 1990 Table 2). Effect: SNIE 11-10-57 (10 Dec 1957) projected 100 ICBMs "
            "about a year after a first operational capability in mid-1958 to mid-1959 and 500 "
            "two or at most three years after it; NIE 11-4-57 (12 Nov 1957) 250 to 450 heavy "
            "bombers and tankers for mid-1960: some 580 vehicles for mid-1960, 200 to 999."
        ),
    )
    _edit(
        nature,
        "estimate_revised",
        {"gap": V.belief_force_USA > V.count_USSR},
        effects=[
            SetIf(V.count_USSR == "none", "belief_force_USA", "under_200"),
            SetIf(V.count_USSR == "under_200", "belief_force_USA", "under_1000"),
        ],
        note=(
            projected + " Part gap: the projected count above the count in being. Effect: the "
            "revised estimate projects the force seen and its programme, which on these bands "
            "is the band above the count in being: NIE 11-8/1-61 (21 Sep 1961) cut the ICBM "
            "force in being to 10 to 25 launchers and projected 75 to 125 for mid-1963, beside "
            "about 150 heavy bombers and tankers and about 20 missile submarines (NIE 11-8-61, "
            "7 Jun 1961): some 300 vehicles for mid-1963, 200 to 999, while the force in being "
            "was 187 at the end of 1961 (Norris and Cochran 1990 Table 2). On the count scale "
            "the revision of 1961 moved the projection within its band (from some 700 in NIE "
            "11-8-60 to some 300)."
        ),
    )
    nature.event(
        "bomber_gap",
        guard={
            "blind": V.intel_USA != "overhead",
            "soviet_bomb": V.nuke_USSR >= "few",
            "level": V.belief_force_USA == "none",
        },
        effect=Set("belief_force_USA", "under_1000"),
        source=(
            "The bomber-gap estimate after the BISON flypast of May Day 1955: NIE 11-56 (6 Mar "
            "1956) estimated some 400 BISON and 300 BEAR heavy bombers in operational use by "
            "mid-1959, from about 75 on 1 Jan 1956 (Steury (ed.), Intentions and Capabilities, "
            "CIA 1996, no. 1; Prados, The Soviet Estimate, 1982): some 520 for mid-1958 and 700 "
            "for mid-1959, 200 to 999. Part blind: before satellite coverage (the U-2 flights "
            "from 4 Jul 1956 reduced the bomber estimates of 1957 and 1958, NIE 11-4-57, SNIE "
            "11-7-58). The estimates of 1954 and 1955 are not in the corpus and not placed."
        ),
    )
    ussr.action(
        "heavy_bombers",
        guard={
            "level": V.count_USSR == "none",
            "bomb": V.nuke_USSR >= "few",
            "technology": V.tick >= tick_of(1955),
        },
        effect=[raise_to("count_USSR", "under_200"), seen("under_200")],
        source=(
            "The first intercontinental bombers in Long Range Aviation: the Myasishchev M-4 "
            "(BISON) from 1955 and the Tupolev Tu-95 (BEAR) from 1956, ordered by the Council "
            "of Ministers in Mar and Jul 1951 (Zaloga, The Kremlin's Nuclear Sword, 2002; "
            "Podvig (ed.), Russian Strategic Nuclear Forces, 2001; the decree dates not "
            "verified): 22 at the end of 1956, 20 BISON and 2 BEAR (Norris and Cochran, "
            "US-USSR Strategic Offensive Nuclear Forces 1946-1989, NRDC Working Paper 90-1, "
            "1990, Tables 2 and 8). Part technology: the two types were first flown on 20 Jan "
            "1953 (M-4) and 12 Nov 1952 (Tu-95) and series-built from 1954 to 1955 (Zaloga "
            "2002). Realized in the 1956 move, visible 1 Jan 1957."
        ),
    )
    ussr.action(
        "first_icbms",
        guard={"level": V.count_USSR == "under_200", "technology": V.tick >= tick_of(1959)},
        effect=[raise_to("count_USSR", "under_1000"), seen("under_1000")],
        delay=3,
        source=(
            "The first-generation ICBM force: the Council of Ministers' decree of 13 May 1959 on "
            "the R-16 (SS-7) and the Strategic Rocket Forces created on 17 Dec 1959, with the "
            "R-7A (SS-6) on combat duty at Plesetsk from 1959 to 1960 and the R-16 regiments "
            "from late 1961 (Podvig (ed.) 2001; Zaloga 2002; the decree date not verified); "
            "with the BEAR and BISON deliveries and the first ballistic missile submarines (the "
            "Golf and Hotel classes), 235 intercontinental vehicles at the end of 1962: 30 ICBM "
            "launchers, 72 SLBM launchers, 133 heavy bombers (Norris and Cochran 1990 Table "
            "2). Part technology: the R-7 was first flown to range on 21 Aug 1957, and no ICBM "
            "unit existed before 1959. Delay 3: decided 1959, visible 1 Jan 1963."
        ),
    )
    ussr.action(
        "icbm_parity",
        guard={"level": V.count_USSR == "under_1000", "silos": V.nuke_USSR >= "survivable"},
        effect=[raise_to("count_USSR", "over_1000"), seen("over_1000")],
        source=(
            "The third-generation ICBM deployment carried past the American number: from 701 "
            "ICBM launchers at the end of 1967 to 909 at the end of 1968 (the SS-11 and SS-9 in "
            "single silos), with the first Yankee-class submarines, 1,206 intercontinental "
            "vehicles at the end of 1968 (Norris and Cochran 1990 Table 2); NIE 11-8-67 (26 "
            "Oct 1967) expected about 1,000 ICBM launchers by the end of 1968, about the US "
            "number (Steury (ed.) 1996; Podvig (ed.) 2001; the date of the decision not "
            "verified). Part silos: the deployment was of the hardened third generation "
            "(docs/cw_v1_decisions.md D3). Realized in the 1968 move, visible 1 Jan 1969."
        ),
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
        # 1984 to 1991: the source search of docs/cw_v1_us_options_1984_1991.md (2026-10-27)
        # found no documented, argued and rejected American option whose adoption would have
        # opened a standing crisis across a 1 January; none is added (docs/cw_v1_decisions.md
        # D2). From 1984 the United States has no way out of balance_core of its own: V2's
        # report says so.
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
