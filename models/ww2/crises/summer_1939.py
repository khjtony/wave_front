"""The summer-1939 crisis sub-game of WW2 v1: 3-day ticks from 5 July to 3 September 1939.

The model of docs/ontology_crisis_1939.md and docs/actions_crisis_1939.md, with the
architect's decisions and the settled points of docs/crisis_1939_decisions.md. The registered
claims K1 to K6 (docs/crisis_1939_testbed.md section 3) were committed before any guard,
action, variable or data row of this module was written; K2 is the hold-out claim. Every
guard, effect, delay, fairness constraint or profile edited after the first run of K1 to K6
is logged in docs/guard_changelog_ww2.md with a dated source.

Time: one tick is three days. Tick 0 is 5 July 1939 (5 to 7 July), tick t covers the three
days from ``TICK0 + 3t``, and tick 20 (3 September 1939) is the horizon. The joint move at
tick t is what each actor decided during those three days; its effects are visible at t + 1.
A dated decision falls in the tick that contains its day. Two decisions of one actor in one
tick: the realized file keeps the one the claims need and notes the other ([SQR]-style
note); a reaction to another actor's move of the same tick appears one tick later ([SQR]).
Nature plays one event per tick ([NSL] where two fall together).

Actors: ``GER``, ``WEST`` (Britain and France), ``USSR`` and Nature, which carries the
Polish decisions (passage for the Red Army, mobilization) and the Italian one (Mussolini's
letter of 25 August). The sub-game has no hidden objective of its own: ``aims_GER`` and
``aims_USSR`` are fixed by the entry map from the coarse state (they are declared with
``init=None`` so that the entry map must name them), and v1's hypothesis gate on the attack
carries over.

Everything structural (armaments, regions, the China war) is frozen at the entry values and
is not represented: the sub-game moves diplomacy, military conversations, orders and
beliefs only.

``entry(coarse_state_dict)`` and ``exit(fine_state_dict, coarse_state_dict)`` are the maps
of framework_spec.md section 14; :func:`crisis` builds the :class:`~wavefront.engine.Crisis`
for a coarse action with no effect (v1 has none and is not edited here; the K1 test attaches
the sub-game to a copy of v1 with such an action and flattens it).

Coding choices (each in docs/crisis_1939_decisions.md):

* Dates and placements: ``data/ww2/crises/1939/realized_moves.csv`` (decisions C1 and C2).
* The declarations of 3 September fall in tick 20, the horizon (the British Cabinet's
  ultimatum decision of 2 September and the attack of 1 September share tick 19). On the
  realized path the attack is visible only at tick 20, so the West's declaration is the
  obligation ``polish_obligation`` falling due on return: the exit map applies
  ``declare_war``'s effects when the obligation's trigger holds in the terminal state
  (:func:`make_exit`). An attack launched by tick 18 obliges ``declare_war`` inside the
  sub-game.
* The re-order of 31 August (Directive No. 1) and the attack of 1 September fall in tick
  19: ``attack_poland`` is the order executed, and its ``order`` part needs an order to have
  been given once (``attack_order`` ordered or cancelled), so the realized re-order and
  launch are one decision.
* ``build(inert=False)`` drops the three inert Nature events (the two Polish mobilizations,
  Mussolini's letter) and their two variables, which no guard, effect of another variable,
  invariant, ending, fairness constraint or profile reads. Every question that does not mention them
  has the same answer on both builds (Nature's inert events project to ``none``); the
  analysis uses the reduced build for speed and tests/ww2/crisis_1939 checks the
  equivalence.
* ``build(passage="granted" | "refused")`` is an analysis scenario for K2 and K3: Nature's
  passage decision is fixed (it must answer Voroshilov's question at the first tick the
  question is before Warsaw, with the scenario's answer). It is not the model.
"""

from __future__ import annotations

import csv
import datetime
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from wavefront.model import Model, ModelError, Set, SetIf, V
from wavefront.model.compile import CompiledModel
from wavefront.model.expr import Expr

__all__ = [
    "HORIZON",
    "TICK0",
    "ROOT",
    "DATA",
    "REALIZED_MOVES",
    "EVENTS",
    "DECISIONS",
    "INERT_EVENTS",
    "EXIT_VARIABLES",
    "tick_of",
    "tick_days",
    "build",
    "model",
    "entry",
    "exit",
    "make_exit",
    "entry_state",
    "realized_rows",
    "realized_moves",
    "crisis",
    "replay",
]

HORIZON = 20
TICK0 = datetime.date(1939, 7, 5)
ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "ww2" / "crises" / "1939"
REALIZED_MOVES = DATA / "realized_moves.csv"
EVENTS = DATA / "events.csv"
DECISIONS = DATA / "decisions.csv"

# The coarse variables the crisis changes (docs/crisis_1939_testbed.md section 1).
EXIT_VARIABLES = (
    "poland",
    "war_west_ger",
    "france",
    "britain",
    "commit_WEST",
    "nazi_soviet_pact",
    "anglo_soviet_alliance",
    "belief_GER",
    "oil_GER",
)


# Nature's events that no guard, other effect, predicate or constraint reads.
INERT_EVENTS = ("mobilize_partial", "mobilize_general", "italy_declines")


def tick_of(day: datetime.date) -> int:
    """The tick containing ``day`` (5 July 1939 is tick 0; 3 September is tick 20)."""
    days = (day - TICK0).days
    if not 0 <= days <= 3 * HORIZON:
        raise ValueError(f"{day} is outside the sub-game (5 Jul to 3 Sep 1939)")
    return days // 3


def tick_days(t: int) -> tuple[datetime.date, datetime.date]:
    """The first and last day of tick ``t`` (the horizon is one day, 3 September)."""
    first = TICK0 + datetime.timedelta(days=3 * t)
    return first, first if t == HORIZON else first + datetime.timedelta(days=2)


def _raise_to(var: str, level: str) -> SetIf:
    """``var := max(var, level)``."""
    return SetIf(V[var] < level, var, level)


def build(
    *,
    inert: bool = True,
    passage: str | None = None,
    target: tuple[str, Expr] | None = None,
) -> Model:
    """The sub-game as a :class:`Model`.

    - ``inert=False`` drops Nature's two inert events and their variables (module
      docstring).
    - ``passage="granted"`` or ``"refused"`` is the analysis scenario of K2 and K3: Nature
      has only that answer to Voroshilov's question and must give it at the first tick the
      question is before Warsaw (fairness ``scenario_passage``, within 1).
    - ``target=(name, expr)`` replaces the two horizon endings by one ending (for
      relaxation searches, which take an ending name); a state satisfying it is terminal.
    """
    if passage not in (None, "granted", "refused"):
        raise ModelError(f"passage scenario must be 'granted' or 'refused', not {passage!r}")
    name = "crisis_1939" + ("" if inert else "_reduced") + (f"_{passage}" if passage else "")
    m = Model(
        name,
        horizon=HORIZON,
        description=(
            "The summer-1939 crisis (3-day ticks, 5 July to 3 September 1939): the "
            "Anglo-French-Soviet talks, the German approach to Moscow, Case White and the "
            "Western guarantee, after docs/ontology_crisis_1939.md and "
            "docs/actions_crisis_1939.md. A crisis sub-game of WW2 v1; every result is "
            "conditional on it and on the entry state."
        ),
    )

    # -- hidden objectives, fixed by the entry map (ontology section 1) ----------------
    m.var("aims_GER", levels=["revisionist", "hegemonic"], init=None, hidden_from=["WEST", "USSR"])
    m.var("aims_USSR", levels=["defensive", "opportunist"], init=None, hidden_from=["GER", "WEST"])

    # -- negotiations (ontology section 2) ----------------------------------------------
    m.var("talks", levels=["political", "military", "adjourned", "broken"], init="political")
    m.var(
        "passage",
        levels=["unasked", "asked", "refused", "granted"],
        init="unasked",
        monotone=True,
    )
    m.flag("west_powers", init=False, monotone=True)
    m.flag("alliance", init=False, monotone=True)
    m.var(
        "german_approach",
        levels=["none", "opened", "pact_proposed", "pact"],
        init="none",
        monotone=True,
    )

    # -- Case White, the guarantee, belief (ontology sections 3 and 4) ------------------
    m.var("attack_order", levels=["none", "ordered", "cancelled", "launched"], init="none")
    m.var("british_treaty", levels=["none", "guarantee", "treaty"], init="guarantee", monotone=True)
    m.var(
        "belief_GER",
        levels=["will_not_fight", "uncertain", "will_fight"],
        init="uncertain",
        monotone=True,
    )
    m.flag("war_declared", init=False, monotone=True)

    # -- Poland's and Italy's decisions, carried by Nature (ontology section 5) ---------
    if inert:
        m.var("mobilization_POL", levels=["none", "partial", "general"], init="none", monotone=True)
        m.var("italy_ready", levels=["unknown", "not_ready"], init="unknown", monotone=True)

    GER = m.actor("GER", observes=V.all())
    WEST = m.actor("WEST", observes=V.all())
    USSR = m.actor("USSR", observes=V.all())
    N = m.nature()

    # -- Germany --------------------------------------------------------------------------
    GER.action(
        "open_approach",
        guard={"first": V.german_approach == "none", "free": ~V.alliance},
        effect=Set("german_approach", "opened"),
        source=(
            "Weizsaecker's instruction to Schulenburg of 30 May 1939 to open political talks "
            "(DGFP Series D vol. VI); Schnurre's dinner with Astakhov and Barbarin, 26 Jul "
            "1939 (Schnurre's memorandum of 27 Jul; Nazi-Soviet Relations 1939-1941); "
            "Ribbentrop to Astakhov, 2 Aug, and Schulenburg's instructions of 3 Aug 1939."
        ),
    )
    GER.action(
        "propose_pact",
        guard={"opened": V.german_approach == "opened", "free": ~V.alliance},
        effect=Set("german_approach", "pact_proposed"),
        source=(
            "Ribbentrop to Schulenburg, 14 Aug 1939 (no question 'between the Baltic and the "
            "Black Sea' that cannot be settled; Ribbentrop ready to come to Moscow), delivered "
            "to Molotov 15 Aug; Ribbentrop to Schulenburg, 16 Aug (a non-aggression pact for "
            "25 years, a joint guarantee of the Baltic states); Hitler's telegram to Stalin, "
            "20 Aug 1939, accepting the Soviet draft and the protocol (Nazi-Soviet Relations "
            "1939-1941; DGFP Series D vol. VII)."
        ),
    )
    GER.action(
        "order_attack",
        guard={"standing": V.attack_order.is_in(["none", "cancelled"])},
        effect=Set("attack_order", "ordered"),
        source=(
            "Case White: the order of 25 Aug 1939, 15:02, for the attack at 04:30 on 26 Aug "
            "(Halder's war diary, 25 Aug; DGFP Series D vol. VII); Y-day fixed for 26 Aug on "
            "23 Aug (Halder's diary; not verified); the new date of 1 Sep recorded by Halder "
            "on 29 Aug ('1.9. use of force'; not verified)."
        ),
    )
    GER.action(
        "cancel_attack",
        guard={"standing": V.attack_order == "ordered"},
        effect=Set("attack_order", "cancelled"),
        source=(
            "Hitler's halt order of 25 Aug 1939, about 19:30, after Mussolini's letter and the "
            "news of the Anglo-Polish treaty (Halder's war diary, 25 to 26 Aug; Schmidt, "
            "Statist auf diplomatischer Buehne, 1949, postwar; Ciano's diary, 25 Aug)."
        ),
    )
    GER.action(
        "attack_poland",
        guard={
            "hypothesis": V.aims_GER == "hegemonic",
            "order": V.attack_order.is_in(["ordered", "cancelled"]),
            "readiness": V.tick >= 17,
        },
        effect=Set("attack_order", "launched"),
        source=(
            "Case White directive of 3 Apr 1939 (Nuremberg document C-120: operations possible "
            "'at any time from 1.9.39'), advanced to 26 Aug; conference of 23 May 1939 (L-79); "
            "Directive No. 1 for the Conduct of the War, 31 Aug 1939, 12:40, and the attack "
            "at 04:45 on 1 Sep 1939 (Trevor-Roper (ed.), Hitler's War Directives 1939-1945)."
        ),
    )

    # -- The West -----------------------------------------------------------------------
    WEST.action(
        "send_missions",
        guard={"political": V.talks == "political"},
        # The delayed effect cannot reopen talks the USSR broke off while the missions
        # travelled.
        effect=SetIf(V.talks == "political", "talks", "military"),
        delay=5,
        source=(
            "The Soviet draft of 2 Jun 1939 (political and military agreements to enter into "
            "force together) and Molotov's demand of 17 Jul for immediate military talks; the "
            "British and French agreement of 23 to 25 Jul 1939 (DBFP Third Series vol. VI); "
            "Chamberlain in the Commons, 31 Jul; the missions sailed on 5 Aug and opened the "
            "talks in Moscow on 12 Aug 1939 (DBFP Third Series vol. VII, appendix II)."
        ),
    )
    WEST.action(
        "authorize_convention",
        guard={"in_session": V.talks.is_in(["military", "adjourned"]), "once": ~V.west_powers},
        effect=Set("west_powers", True),
        source=(
            "Daladier's instruction to General Doumenc of 21 Aug 1939 to sign a military "
            "convention subject to the government's approval (DDF 2e serie vol. XVIII; not "
            "verified); the British delegation's written powers, requested by Voroshilov on "
            "12 Aug and sent from London on 21 Aug (DBFP Third Series vol. VII; not verified)."
        ),
    )
    WEST.action(
        "warn_germany",
        guard={"guarantee": V.british_treaty != "none"},
        effect=_raise_to("belief_GER", "uncertain"),
        source=(
            "Chamberlain's letter to Hitler of 22 Aug 1939, delivered by Henderson at "
            "Berchtesgaden on 23 Aug ('His Majesty's Government are determined to fulfil "
            "their obligation to Poland'), and Hitler's reply of 23 Aug (DBFP Third Series "
            "vol. VII; Cmd. 6106); earlier: Halifax's Chatham House speech, 29 Jun 1939."
        ),
    )
    WEST.action(
        "sign_treaty",
        guard={"once": V.british_treaty == "guarantee"},
        effect=[Set("british_treaty", "treaty"), _raise_to("belief_GER", "will_fight")],
        source=(
            "Agreement of Mutual Assistance between the United Kingdom and Poland, London, "
            "25 Aug 1939 (Cmd. 6106), announced as a treaty to come on 6 Apr 1939 and "
            "negotiated from April; its news reached Hitler on the afternoon of 25 Aug "
            "(Halder's diary, 25 Aug; Schmidt, postwar)."
        ),
    )
    WEST.action(
        "declare_war",
        guard={
            "attack": V.attack_order == "launched",
            "guarantee": V.british_treaty != "none",
            "once": ~V.war_declared,
        },
        effect=[Set("war_declared", True), Set("belief_GER", "will_fight")],
        source=(
            "The Anglo-French warnings of 1 Sep 1939; the Cabinet of 2 Sep, 23:30, deciding "
            "the ultimatum; the British declaration of 3 Sep, 11:00, and the French of 3 Sep, "
            "17:00 (CAB 23/100; HC Deb 1 to 3 Sep 1939); against Mussolini's proposal of a "
            "conference, 31 Aug to 2 Sep (Bonnet's support; DBFP Third Series vol. VII)."
        ),
    )

    # -- The USSR -----------------------------------------------------------------------
    USSR.action(
        "ask_passage",
        guard={"in_session": V.talks == "military", "first": V.passage == "unasked"},
        effect=Set("passage", "asked"),
        source=(
            "Voroshilov's 'cardinal question' to the missions, 14 Aug 1939: would Soviet "
            "forces be allowed through the Vilna corridor, Galicia and Romania (DBFP Third "
            "Series vol. VII, appendix II; Soviet record in Dokumenty vneshnei politiki 1939, "
            "vol. XXII; not verified)."
        ),
    )
    USSR.action(
        "adjourn_talks",
        guard={"in_session": V.talks == "military"},
        effect=Set("talks", "adjourned"),
        source=(
            "Voroshilov's adjournment of 17 Aug 1939 until answers came from London, Paris and "
            "Warsaw (DBFP Third Series vol. VII, appendix II)."
        ),
    )
    USSR.action(
        "break_talks",
        guard={"open": V.talks.is_in(["military", "adjourned"]), "no_alliance": ~V.alliance},
        effect=Set("talks", "broken"),
        source=(
            "Voroshilov's adjournment sine die, 21 Aug 1939, and his statement to Doumenc of "
            "22 Aug that the political situation had changed; the missions left on 25 Aug "
            "(DBFP Third Series vol. VII; Doumenc's report, not verified)."
        ),
    )
    USSR.action(
        "accept_pact",
        guard={"proposal": V.german_approach == "pact_proposed", "free": ~V.alliance},
        effect=Set("german_approach", "pact"),
        source=(
            "Molotov to Schulenburg, 17 Aug (a pact with a 'special protocol') and 19 Aug "
            "1939 (the Soviet draft; Ribbentrop received for 26 to 27 Aug); the credit "
            "agreement of 19 Aug; Stalin's reply to Hitler, 21 Aug; the non-aggression pact "
            "and secret protocol signed in the night of 23 to 24 Aug 1939 (Nazi-Soviet "
            "Relations 1939-1941; DGFP Series D vol. VII)."
        ),
    )
    USSR.action(
        "conclude_alliance",
        guard={
            "no_pact": V.german_approach != "pact",
            "in_session": V.talks.is_in(["military", "adjourned"]),
            "powers": V.west_powers,
            "passage": V.passage == "granted",
            "once": ~V.alliance,
        },
        effect=Set("alliance", True),
        source=(
            "The Soviet condition of 14 Aug 1939: a military convention once passage through "
            "Poland and Romania is granted (Voroshilov; DBFP Third Series vol. VII, appendix "
            "II); the Soviet draft treaty of 2 Jun 1939 and Molotov's position of 17 Jul that "
            "the political and military agreements be signed together."
        ),
    )
    USSR.action(
        "conclude_without_passage",
        guard={
            "no_pact": V.german_approach != "pact",
            "in_session": V.talks.is_in(["military", "adjourned"]),
            "powers": V.west_powers,
            "no_consent": V.passage != "granted",
            "once": ~V.alliance,
        },
        effect=Set("alliance", True),
        source=(
            "No Soviet record of a willingness to conclude without Polish consent: Voroshilov "
            "on 14 and 21 Aug 1939 made passage a condition of any convention. Speculative "
            "(the architect's decision for this sub-game)."
        ),
        speculative=True,
    )

    # -- Nature: Poland and Italy -------------------------------------------------------
    if passage != "granted":
        N.event(
            "passage_refused",
            guard={"question": V.passage == "asked"},
            effect=Set("passage", "refused"),
            source=(
                "Beck to the French ambassador Noel, 19 Aug 1939, and the Polish General "
                "Staff's answer of 20 Aug: no Soviet troops on Polish soil (DDF 2e serie vol. "
                "XVIII; DBFP Third Series vol. VII, Kennard's telegrams of 19 to 20 Aug)."
            ),
        )
    if passage != "refused":
        N.event(
            "passage_granted",
            guard={"question": V.passage == "asked"},
            effect=Set("passage", "granted"),
            source=(
                "The documented alternative pressed on Warsaw and refused: the French and "
                "British demarches of 18 to 21 Aug 1939 (Bonnet to Noel; Gamelin's message "
                "through the military attache; Halifax to Kennard, 20 Aug); Beck's formula of "
                "23 Aug that Polish-Soviet collaboration 'is not excluded' (DDF 2e serie vol. "
                "XVIII; DBFP Third Series vol. VII; not verified)."
            ),
        )
    if inert:
        N.event(
            "mobilize_partial",
            guard={"first": V.mobilization_POL == "none"},
            effect=Set("mobilization_POL", "partial"),
            source=(
                "The Polish alarm mobilization of 23 to 24 Aug 1939 (call-up of reservists in "
                "the western and northern corps areas; Polish General Staff records in Polskie "
                "Sily Zbrojne vol. I, not verified)."
            ),
        )
        N.event(
            "mobilize_general",
            guard={"partial": V.mobilization_POL == "partial"},
            effect=Set("mobilization_POL", "general"),
            source=(
                "General mobilization ordered 29 Aug 1939, suspended the same day at the "
                "British and French request, proclaimed on 30 Aug for 31 Aug (DBFP Third "
                "Series vol. VII, Kennard's telegrams of 29 to 30 Aug)."
            ),
        )
        N.event(
            "italy_declines",
            guard={"first": V.italy_ready == "unknown"},
            effect=Set("italy_ready", "not_ready"),
            source=(
                "Mussolini's letter to Hitler of 25 Aug 1939: Italy not ready for war without "
                "supplies it then listed on 26 Aug (DGFP Series D vol. VII; Ciano's diary, "
                "25 to 26 Aug); Ciano had said as much at Salzburg, 11 to 13 Aug."
            ),
        )

    # -- constraints --------------------------------------------------------------------
    # The obligation of the guarantee (31 Mar 1939) and of the Agreement of Mutual
    # Assistance (25 Aug 1939, article 1): an institutional constraint, as v1's
    # czech_obligation. Source: Cmd. 6106; the Cabinet of 1 to 3 Sep 1939 (CAB 23/100).
    m.fairness(
        "polish_obligation",
        actor="WEST",
        trigger=(V.attack_order == "launched") & (V.british_treaty != "none") & ~V.war_declared,
        within=1,
        responses=["declare_war"],
    )
    if passage is not None:
        answer = "passage_granted" if passage == "granted" else "passage_refused"
        m.fairness(
            "scenario_passage",
            actor="Nature",
            trigger=V.passage == "asked",
            within=1,
            responses=[answer],
        )

    # v1's profile for T9 (decisions E5), carried over: a named, relaxable behavioural
    # assumption, not feasibility.
    m.profile(
        "deterred",
        actor="GER",
        forbid=["attack_poland"],
        unless=~((V.belief_GER == "will_fight") & V.alliance),
    )
    # Analysis devices (docs/crisis_1939_decisions.md): the documented decision space only
    # (no speculative action); no Western signal to Berlin (the belief sweep of K2); no German
    # proposal (K6).
    m.profile("documented_only", actor="USSR", forbid=["conclude_without_passage"])
    m.profile("no_belief_raise", actor="WEST", forbid=["warn_germany", "sign_treaty"])
    m.profile("no_german_proposal", actor="GER", forbid=["propose_pact"])

    # -- analysis predicates and endings ------------------------------------------------
    pact = V.german_approach == "pact"
    m.invariant("no_attack", V.attack_order != "launched")
    m.invariant("no_pact", ~pact)
    # K3: no pact, and the alliance concluded by the horizon (it is still possible at every
    # earlier tick at which the coalition can keep this to the horizon).
    m.invariant("alliance_race", ~pact & (V.alliance | (V.tick < HORIZON)))
    if target is None:
        at_horizon = V.tick == HORIZON
        m.ending("ATTACK_LAUNCHED", at_horizon & (V.attack_order == "launched"))
        m.ending("NO_ATTACK", at_horizon & (V.attack_order != "launched"))
    else:
        m.ending(target[0], target[1])
    return m


model = build()


# -- entry and exit maps (framework_spec.md section 14) ----------------------------------


def _true(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value in ("True", "False"):
        return value == "True"
    raise ModelError(f"not a flag value: {value!r}")


def entry(coarse: Mapping[str, object]) -> dict[str, object]:
    """Fine initial values from a WW2 v1 state (``state_dict`` strings or plain values).

    From the coarse state: the two hidden objectives, ``belief_GER``, the guarantee (as
    ``british_treaty``), the pact (``german_approach``), the alliance, the war in the West
    and a Polish attack already made. Fine-only variables take their declared initial
    values, the record's of 5 July 1939: political talks under way, no military talks, no
    German approach, no order, Poland unmobilized, Italy's readiness unknown. The talks are
    entered as broken when the coarse state already has the pact (WEST's approach to Moscow
    no longer stands; v1's ``approach_ussr`` needs no pact)."""
    pact = _true(coarse["nazi_soviet_pact"])
    return {
        "talks": "broken" if pact else "political",
        "aims_GER": coarse["aims_GER"],
        "aims_USSR": coarse["aims_USSR"],
        "belief_GER": coarse["belief_GER"],
        "british_treaty": "guarantee" if _true(coarse["polish_guarantee"]) else "none",
        "german_approach": "pact" if pact else "none",
        "alliance": _true(coarse["anglo_soviet_alliance"]),
        "war_declared": coarse["war_west_ger"] == "war",
        "attack_order": "none" if coarse["poland"] == "independent" else "launched",
    }


def make_exit(obligation: bool = True) -> Callable[[Mapping[str, str], Mapping[str, str]], dict]:
    """The exit map; ``obligation=False`` is the map for a sub-game compiled with
    ``polish_obligation`` relaxed (the obligation then does not fall due on return)."""

    def exit_map(fine: Mapping[str, str], coarse: Mapping[str, str]) -> dict[str, object]:
        """The coarse variables the crisis changes, from a terminal fine state and the state
        the crisis was entered from. Unchanged variables are omitted.

        - ``poland`` german when the attack was launched;
        - war in the West (``war_west_ger``, ``france``, ``britain`` at war, ``commit_WEST``
          at_war, ``belief_GER`` will_fight) when WEST declared, or when the obligation's
          trigger holds in the terminal state: the obligation (within 1 tick) leaves
          ``declare_war`` as WEST's only move, and WEST's next move is the return;
        - ``nazi_soviet_pact`` and ``oil_GER`` secured with the pact (as v1's ``accept_pact``);
        - ``anglo_soviet_alliance`` with the alliance;
        - ``belief_GER`` as the sub-game left it (it only rises)."""
        out: dict[str, object] = {}
        launched = fine["attack_order"] == "launched"
        if launched and coarse["poland"] == "independent":
            out["poland"] = "german"
        declared = _true(fine["war_declared"])
        due = obligation and launched and fine["british_treaty"] != "none" and not declared
        belief = fine["belief_GER"]
        if declared or due:
            if coarse["war_west_ger"] != "war":
                out["war_west_ger"] = "war"
            for var in ("france", "britain"):
                if coarse[var] in ("independent", "at_peace"):
                    out[var] = "at_war"
            out["commit_WEST"] = "at_war"
            belief = "will_fight"
        if fine["german_approach"] == "pact":
            out["nazi_soviet_pact"] = True
            out["oil_GER"] = "secured"
        if _true(fine["alliance"]):
            out["anglo_soviet_alliance"] = True
        if belief != coarse["belief_GER"]:
            out["belief_GER"] = belief
        return out

    return exit_map


exit = make_exit()  # noqa: A001 - the name of framework_spec.md section 14


def entry_state(cm: CompiledModel, coarse: Mapping[str, object]) -> tuple[int, ...]:
    """The fine initial state for a coarse state, as :mod:`wavefront.engine.multires`
    builds it: ``entry`` on the coarse values, declared initial values elsewhere (names
    the reduced build does not declare are ignored)."""
    values = entry(coarse)
    state = [v.init[0] for v in cm.variables]
    for name, value in values.items():
        i = cm.index.get(name)
        if i is None:
            continue
        spec = cm.variables[i]
        if isinstance(value, bool):
            state[i] = int(value)
        elif isinstance(value, str) and value in spec.levels:
            state[i] = spec.levels.index(value)
        else:
            raise ModelError(f"entry gives {name}={value!r}, not a value of {name!r}")
    return tuple(state)


# -- the realized moves ----------------------------------------------------------------


def realized_rows(path: str | Path = REALIZED_MOVES) -> list[dict[str, str]]:
    """The rows of the realized move file, in tick order (ticks 0 to 19)."""
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for k, row in enumerate(rows):
        if int(row["tick"]) != k:
            raise ValueError(f"{path}: row {k} has tick {row['tick']}")
    return rows


def realized_moves(cm: CompiledModel, path: str | Path = REALIZED_MOVES) -> list[tuple[int, ...]]:
    """The realized decisions as joint moves of ``cm`` (action indices in actor order,
    Nature last). On the reduced build an inert Nature event is read as ``none``."""
    moves = []
    for row in realized_rows(path):
        move = []
        for a in cm.actors:
            name = row[a.name]
            try:
                move.append(a.action_index(name))
            except ModelError:
                if a.is_nature and name in INERT_EVENTS:
                    move.append(0)
                    continue
                raise ModelError(f"{path}: tick {row['tick']}: {a.name} has no action {name!r}")
        moves.append(tuple(move))
    return moves


def crisis(actor: str = "GER", action: str = "crisis_1939", sub: CompiledModel | None = None):
    """The :class:`~wavefront.engine.Crisis` for attaching the sub-game to a coarse action
    with no effect and no delay (``actor.action`` of the coarse model)."""
    from wavefront.engine import Crisis

    return Crisis(actor, action, sub or model.compile(), entry, exit, name="summer_1939")


def replay(
    cm: CompiledModel, start: Sequence[int], moves: Sequence[Sequence[int]]
) -> list[tuple[int, ...]]:
    """The states along ``moves`` from ``start``; raises :class:`ModelError` naming the tick
    and actor when a move is not available."""
    states = [tuple(start)]
    for move in moves:
        s = states[-1]
        avail = cm.available(s)
        for a, j, ok in zip(cm.actors, move, avail, strict=True):
            if j not in ok:
                tick = s[cm.index["tick"]]
                raise ModelError(
                    f"tick {tick}: {a.name}.{a.actions[j].name} is not available in "
                    f"{cm.format_state(s)}"
                )
        states.append(cm.step(s, tuple(move)))
    return states
