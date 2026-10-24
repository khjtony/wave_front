"""The Cuban missile crisis, 16 to 29 October 1962, one tick per day: a crisis sub-game of
Cold War v0 entered by ``USSR.deploy_cuba`` in 1962.

The model of docs/ontology_cw.md section 10.2 and docs/actions_cw.md section 7 (decisions D5).
Tick 0 is Tuesday 16 October 1962 (Kennedy shown the U-2 photographs, the ExComm's first
meeting); tick t is the day 16 October + t; the horizon is tick 14 (30 October). A decision
falls on its day (Washington time; Moscow decisions taken in the night count on the
Washington day they answer); its effects are visible the next day.

Actors: ``USA`` (Kennedy and the ExComm), ``USSR`` (Khrushchev and the Presidium) and Nature
(the Soviet commanders on Cuba and at sea acting without Moscow's order, the completion of the
missile sites, accidents).

``entry`` starts every variable at its declared value. ``exit`` maps the endings to the
coarse game: the withdrawal returns ``esc = peace``, a war ``conventional`` (begun by the
United States: ``us_began_war``, added 2026-10-23), nuclear use
``tactical_nuclear`` (with ``accidental`` when Nature's accident was the cause), an
unresolved crisis at the horizon ``crisis``.
"""

from __future__ import annotations

from wavefront.engine import Crisis
from wavefront.model import Bump, Model, Set, V

HORIZON = 14
DAY0 = "1962-10-16"


def build() -> Model:
    m = Model(
        "cw_cuba_1962",
        horizon=HORIZON,
        description=(
            "The Cuban missile crisis, 16 to 29 Oct 1962, one tick per day: a crisis sub-game "
            "of cw_v0 (docs/ontology_cw.md section 10.2)."
        ),
    )
    m.var("missiles", levels=["building", "operational", "withdrawn"], init="building")
    m.var(
        "us_move", levels=["deliberating", "quarantine", "strike", "invasion"], init="deliberating"
    )
    m.var("ships", levels=["en_route", "stopped", "challenged"], init="en_route", monotone=True)
    m.var("tension", levels=["crisis", "alert", "clash"], init="crisis")
    m.var("deal", levels=["none", "pledge", "trade"], init="none", monotone=True)
    m.flag("fighting", init=False, monotone=True)
    m.flag("nuclear", init=False, monotone=True)
    m.flag("accident", init=False, monotone=True)

    usa = m.actor("USA", observes=V.all())
    ussr = m.actor("USSR", observes=V.all())
    nature = m.nature()

    usa.action(
        "quarantine",
        guard={"level": V.us_move == "deliberating"},
        effect=Set("us_move", "quarantine"),
        source=(
            "Kennedy's choice of the quarantine at the ExComm and NSC of 20 Oct 1962, announced "
            "22 Oct 19:00, in force 24 Oct 10:00 (the ExComm recordings, May and Zelikow (eds.), "
            "The Kennedy Tapes, 1997; Allison and Zelikow, Essence of Decision, 1999)."
        ),
    )
    usa.action(
        "air_strike",
        guard={
            "level": V.us_move.is_in(["deliberating", "quarantine"]),
            "missiles": V.missiles != "withdrawn",
        },
        effect=[Set("us_move", "strike"), Set("fighting", True)],
        source=(
            "The air strike on the missile sites argued at the ExComm from 16 Oct (Taylor, "
            "LeMay, Acheson) and set aside on 20 to 21 Oct, kept for 30 Oct if the deal failed "
            "(the ExComm recordings of 16, 18, 20 and 27 Oct 1962; May and Zelikow 1997). Not "
            "taken."
        ),
    )
    usa.action(
        "invade",
        guard={
            "level": V.us_move.is_in(["deliberating", "quarantine"]),
            "ready": V.tick >= 13,
            "missiles": V.missiles != "withdrawn",
        },
        effect=[Set("us_move", "invasion"), Set("fighting", True)],
        source=(
            "OPLAN 316, the invasion of Cuba, with forces ready about 29 Oct 1962 (McNamara at "
            "the ExComm of 27 Oct; Fursenko and Naftali, One Hell of a Gamble, 1997). Part "
            "ready: the invasion force's readiness date. Not taken."
        ),
    )
    usa.action(
        "defcon2",
        guard={"level": V.tension == "crisis", "quarantine": V.us_move != "deliberating"},
        effect=Bump("tension", 1),
        source=(
            "SAC raised to DEFCON 2 on 24 Oct 1962, the only time in the Cold War, with the "
            "airborne alert of B-52s, en clair (Sagan, The Limits of Safety, 1993)."
        ),
    )
    usa.action(
        "pledge",
        guard={"level": V.deal == "none", "missiles": V.missiles != "withdrawn"},
        effect=Set("deal", "pledge"),
        source=(
            "Kennedy's letter to Khrushchev of 27 Oct 1962 accepting the terms of Khrushchev's "
            "letter of 26 Oct: removal under UN verification for an end of the quarantine and "
            "an assurance against invasion (the ExComm recordings of 27 Oct 1962; FRUS "
            "1961-63 vol. XI)."
        ),
    )
    usa.action(
        "trade",
        guard={"level": V.deal != "trade", "missiles": V.missiles != "withdrawn"},
        effect=Set("deal", "trade"),
        source=(
            "Robert Kennedy's meeting with Dobrynin on the evening of 27 Oct 1962: the "
            "non-invasion pledge with a private assurance that the Jupiters in Turkey would be "
            "removed within four to five months (Dobrynin's report of 27 Oct, in CWIHP Bulletin "
            "5, 1995; Fursenko and Naftali 1997)."
        ),
    )

    ussr.action(
        "turn_back",
        guard={"level": V.ships == "en_route", "quarantine": V.us_move == "quarantine"},
        effect=Set("ships", "stopped"),
        source=(
            "Khrushchev's order in the night of 23 to 24 Oct 1962 for the ships carrying "
            "missiles to turn back and the others to hold, observed at the quarantine line on "
            "24 Oct (Fursenko and Naftali 1997)."
        ),
    )
    ussr.action(
        "run_quarantine",
        guard={"level": V.ships == "en_route", "quarantine": V.us_move == "quarantine"},
        effect=[Set("ships", "challenged"), Bump("tension", 1)],
        source=(
            "Running the quarantine line with escorting submarines, the course the Presidium "
            "considered on 23 Oct 1962 before the order to turn back (Fursenko and Naftali "
            "1997; the Presidium notes of 22 to 23 Oct, Malin notes). Not taken."
        ),
    )
    ussr.action(
        "withdraw",
        guard={"assurance": V.deal >= "pledge", "level": V.missiles != "withdrawn"},
        effect=Set("missiles", "withdrawn"),
        source=(
            "The Presidium's decision of 28 Oct 1962 to dismantle the missiles, broadcast on "
            "Radio Moscow that morning, on Kennedy's letter of 27 Oct and Dobrynin's report of "
            "the Jupiter assurance (Fursenko and Naftali 1997; the Malin notes of 28 Oct). Part "
            "assurance: the terms of Khrushchev's letter of 26 Oct."
        ),
    )
    ussr.action(
        "nuclear_defense",
        guard={"attacked": V.fighting},
        effect=Set("nuclear", True),
        source=(
            "Use of the Luna (FROG) tactical nuclear rockets of the Soviet forces on Cuba "
            "against an invasion, for which Pliyev had prepared and which Moscow forbade "
            "without its order on 22 and 27 Oct 1962 (Fursenko and Naftali 1997; Savranskaya, "
            "Journal of Strategic Studies 2005)."
        ),
    )

    nature.event(
        "sites_operational",
        guard={"level": V.missiles == "building"},
        effect=Bump("missiles", 1),
        source=(
            "The CIA's reports of 26 and 27 Oct 1962 that the MRBM sites were operational "
            "(CIA, The Cuban Missile Crisis 1962, McAuliffe (ed.), 1992)."
        ),
    )
    nature.event(
        "shootdown",
        guard={"alert": V.tension == "alert"},
        effect=Bump("tension", 1),
        source=(
            "The shooting down of Anderson's U-2 over Banes on 27 Oct 1962 by a Soviet SA-2 "
            "battery on the order of Pliyev's deputies, without Moscow's authority "
            "(Fursenko and Naftali 1997)."
        ),
    )
    nature.event(
        "accident",
        guard={"alert": V.tension >= "alert"},
        effect=[Set("nuclear", True), Set("accident", True)],
        source=(
            "The incidents that could have led to nuclear use without a decision: the B-59 "
            "submarine depth-charged on 27 Oct 1962 (Savitsky's order to prepare the nuclear "
            "torpedo, Arkhipov's refusal), the U-2 over Chukotka the same day, the false "
            "warnings at Moorestown (Sagan 1993; Savranskaya 2005)."
        ),
    )

    no_war = ~V.fighting & ~V.nuclear
    m.invariant("no_war", no_war)
    m.ending("NUCLEAR", V.nuclear)
    m.ending("WAR", V.fighting & ~V.nuclear)
    m.ending("WITHDRAWAL", (V.missiles == "withdrawn") & no_war)
    return m


def entry(year: dict[str, str]) -> dict[str, object]:
    """Every fine variable at its declared value."""
    return {}


def exit_map(day: dict[str, str], year: dict[str, str]) -> dict[str, object]:
    if day["nuclear"] == "True":
        return {"esc": "tactical_nuclear", "accidental": day["accident"] == "True"}
    if day["fighting"] == "True":
        # Only the United States opens fighting in the sub-game (air_strike, invade): a war
        # begun by the United States (us_began_war, added 2026-10-23, decision 2l).
        return {"esc": "conventional", "us_began_war": True}
    if day["missiles"] == "withdrawn":
        return {"esc": "peace"}
    return {"esc": "crisis"}


model = build()


def crisis(sub=None) -> Crisis:
    return Crisis("USSR", "deploy_cuba", sub or model.compile(), entry, exit_map, name="cuba_1962")
