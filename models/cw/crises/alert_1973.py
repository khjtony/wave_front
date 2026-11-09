"""The October 1973 alert, from Brezhnev's message of 24 October to the ceasefire under
Resolution 340 with a UN force, one tick per day: a crisis sub-game of Cold War v1 entered by
``USSR.warn_unilateral`` in 1973.

The model of docs/ontology_cw.md section 12.2 and docs/actions_cw.md section 6
(docs/cw_v1_decisions.md D4). Tick 0 is Wednesday 24 October 1973, the evening on which
Dobrynin delivered Brezhnev's message (21:35 EDT); tick t is the day 24 October + t
(Washington time); the horizon is tick 5 (29 October). A decision falls on its day; its
effects are visible the next day.

Actors: ``USA`` (Nixon, Kissinger and the Washington Special Actions Group), ``USSR``
(Brezhnev and the Politburo) and Nature (the belligerents, Israel and Egypt, and the forces
at sea acting without an order).

``entry`` starts every variable at its declared value: the war under way with the ceasefire
of 22 October violated around the Egyptian Third Army, the Soviet airborne divisions on
alert and the Soviet Mediterranean squadron at readiness. ``exit`` maps US-Soviet combat to
``esc = conventional``, Soviet forces landed without combat to a standing confrontation
(``esc = crisis``), a UN force voted to no change, and an unresolved end to ``crisis``.
"""

from __future__ import annotations

from wavefront.engine import Crisis
from wavefront.model import Model, Set, V

HORIZON = 5
DAY0 = "1973-10-24"


def build() -> Model:
    m = Model(
        "cw_alert_1973",
        horizon=HORIZON,
        description=(
            "The October 1973 alert, 24 to 28 Oct 1973, one tick per day: a crisis sub-game "
            "of cw_v1 (docs/ontology_cw.md section 12.2)."
        ),
    )
    m.var("soviet_forces", levels=["alerted", "landed"], init="alerted", monotone=True)
    m.var("us_alert", levels=["normal", "defcon3"], init="normal", monotone=True)
    m.flag("reply", init=False, monotone=True)
    m.var("ceasefire", levels=["violated", "holding"], init="violated")
    m.flag("un_force", init=False, monotone=True)
    m.flag("fighting", init=False, monotone=True)

    usa = m.actor("USA", observes=V.all())
    ussr = m.actor("USSR", observes=V.all())
    nature = m.nature()

    usa.action(
        "defcon3",
        guard={"level": V.us_alert == "normal"},
        effect=Set("us_alert", "defcon3"),
        source=(
            "The worldwide alert at DEFCON 3 ordered at 23:41 EDT on 24 Oct 1973 by the "
            "Washington Special Actions Group (Kissinger, Schlesinger, Moorer, Haig, Colby), "
            "with the 82nd Airborne Division alerted and carriers ordered to the eastern "
            "Mediterranean (Kissinger, Years of Upheaval, 1982; Blechman and Hart, 'The "
            "Political Utility of Nuclear Weapons', International Security 1982; Sagan, "
            "'Nuclear Alerts and Crisis Management', International Security 1985; FRUS "
            "1969-76 vol. XXV)."
        ),
    )
    usa.action(
        "reply",
        guard={"level": ~V.reply},
        effect=Set("reply", True),
        source=(
            "Nixon's letter to Brezhnev delivered at 05:40 EDT on 25 Oct 1973, drafted at the "
            "WSAG meeting of 24 to 25 Oct: unilateral action would have 'incalculable "
            "consequences'; a UN force with at most American and Soviet non-combat personnel "
            "(Kissinger 1982; FRUS 1969-76 vol. XXV). Played without defcon3 it is the "
            "documented alternative of claim V3 (c), the reply without the alert (Lebow and "
            "Stein, We All Lost the Cold War, 1994)."
        ),
    )
    usa.action(
        "restrain_israel",
        guard={"level": V.ceasefire == "violated"},
        effect=Set("ceasefire", "holding"),
        source=(
            "Kissinger's demands on the Israeli government of 26 Oct 1973 to let non-military "
            "supplies through to the encircled Third Army, carried out with the convoy of 27 "
            "to 28 Oct and the talks at Kilometre 101 (Kissinger 1982; FRUS 1969-76 vol. "
            "XXV; Garthoff, Detente and Confrontation, 1994)."
        ),
    )
    usa.action(
        "oppose_landing",
        guard={"landed": V.soviet_forces == "landed", "ready": V.us_alert == "defcon3"},
        effect=Set("fighting", True),
        source=(
            "Opposing a Soviet landing in Egypt with American forces, the contingency the "
            "alert prepared (the 82nd Airborne Division at readiness to deploy) and Nixon's "
            "letter of 25 Oct threatened (Kissinger 1982; Blechman and Hart 1982; the "
            "deployment orders not verified). Not taken: no landing came. Part ready: the "
            "forces alerted under DEFCON 3."
        ),
    )

    ussr.action(
        "land_forces",
        guard={
            "forces": V.soviet_forces == "alerted",
            "occasion": V.ceasefire == "violated",
            "no_un_force": ~V.un_force,
        },
        effect=Set("soviet_forces", "landed"),
        source=(
            "Sending the alerted airborne divisions to Egypt, the unilateral step Brezhnev's "
            "message of 24 Oct 1973 threatened; the Politburo of 25 Oct decided against it and "
            "against answering the American alert (Israelyan, Inside the Kremlin during the "
            "Yom Kippur War, 1995; Garthoff 1994). Not taken. Parts occasion and no_un_force: "
            "the threat was conditioned on the Israeli violation of the ceasefire and on the "
            "refusal of a joint force."
        ),
    )
    ussr.action(
        "accept_un_force",
        guard={"level": ~V.un_force},
        effect=Set("un_force", True),
        source=(
            "Resolution 340 of 25 Oct 1973 (14 to 0, the PRC not participating), creating "
            "the second UN Emergency Force without the permanent members' troops, for which "
            "the USSR voted, dropping its demand for a joint Soviet-American force "
            "(Israelyan 1995; Garthoff 1994; UN document S/RES/340 (1973))."
        ),
    )

    nature.event(
        "ceasefire_breaks",
        guard={"level": V.ceasefire == "holding", "no_un_force": ~V.un_force},
        effect=Set("ceasefire", "violated"),
        source=(
            "The Israeli advance after the ceasefire of 22 Oct 1973 that completed the "
            "encirclement of the Third Army and reached Suez city on 23 to 24 Oct, the "
            "violation Brezhnev's message answered (Kissinger 1982; Garthoff 1994)."
        ),
    )
    nature.event(
        "naval_incident",
        guard={"alert": V.us_alert == "defcon3"},
        effect=Set("fighting", True),
        source=(
            "An incident between the Sixth Fleet and the Soviet Mediterranean squadron (about "
            "96 ships, targeting the American carriers) under the raised alert, the danger of "
            "alert operations in close contact that Sagan analysed (Sagan 1985; Zumwalt, On "
            "Watch, 1976). Part alert: the American forces at DEFCON 3; the Soviet squadron "
            "was at readiness from the war's first days."
        ),
    )

    m.invariant("no_combat", ~V.fighting)
    m.ending("WAR", V.fighting)
    m.ending(
        "CEASEFIRE",
        V.un_force & (V.ceasefire == "holding") & ~V.fighting & (V.soviet_forces == "alerted"),
    )
    return m


def entry(year: dict[str, str]) -> dict[str, object]:
    """Every fine variable at its declared value."""
    return {}


def exit_map(day: dict[str, str], year: dict[str, str]) -> dict[str, object]:
    if day["fighting"] == "True":
        return {"esc": "conventional"}
    if day["soviet_forces"] == "landed":
        return {"esc": "crisis"}
    if day["un_force"] == "True":
        return {}
    return {"esc": "crisis"}


model = build()


def crisis(sub=None) -> Crisis:
    return Crisis(
        "USSR", "warn_unilateral", sub or model.compile(), entry, exit_map, name="alert_1973"
    )
