"""The war scare of Able Archer 83, 7 to 12 November 1983, one tick per day: a crisis
sub-game of Cold War v0 entered by ``USA.able_archer`` in 1983.

The model of docs/ontology_cw.md section 10.3 and docs/actions_cw.md section 8 (decisions D5).
Tick 0 is Monday 7 November 1983 (the exercise begins); tick t is the day 7 November + t; the
horizon is tick 6 (13 November). A decision falls on its day; its effects are visible the next
day.

Actors: ``USA`` (NATO's exercise directors and the US command in Europe), ``USSR`` (the
Soviet General Staff and the KGB centre) and Nature (the reports of the KGB and GRU
residencies, accidents).

``entry`` copies the coarse ``belief_USSR_USA`` into the fine ``belief``: the Soviet reading
of American aims with which the exercise is watched (claim C7). ``exit`` maps a strike to a
strategic exchange in the coarse game (``esc = strategic``, ``accidental`` when Nature's
accident was the cause); any other end of the exercise changes nothing.
"""

from __future__ import annotations

from wavefront.engine import Crisis
from wavefront.model import Model, Set, V

HORIZON = 6
DAY0 = "1983-11-07"


def build() -> Model:
    m = Model(
        "cw_able_archer_1983",
        horizon=HORIZON,
        description=(
            "The Able Archer 83 war scare, 7 to 12 Nov 1983, one tick per day: a crisis "
            "sub-game of cw_v0 (docs/ontology_cw.md section 10.3)."
        ),
    )
    m.var("belief", levels=["status_quo", "hostile", "first_strike_intent"], init=None)
    m.var("exercise", levels=["running", "release", "ended"], init="running", monotone=True)
    m.flag("warning", init=False)
    m.var("pact", levels=["normal", "readied"], init="normal")
    m.var("us_alert", levels=["normal", "raised"], init="normal", monotone=True)
    m.flag("strike", init=False, monotone=True)
    m.flag("accident", init=False, monotone=True)

    usa = m.actor("USA", observes=V.all_except("belief"))
    ussr = m.actor("USSR", observes=V.all())
    nature = m.nature()

    usa.action(
        "release_phase",
        guard={"level": V.exercise == "running"},
        effect=Set("exercise", "release"),
        source=(
            "The exercise's simulated move to general nuclear release, with new message "
            "formats and radio silences, on 9 to 10 Nov 1983 (Jones, Able Archer 83, 2016; "
            "PFIAB, 'The Soviet War Scare', 15 Feb 1990)."
        ),
    )
    usa.action(
        "end_exercise",
        guard={"level": V.exercise != "ended"},
        effect=Set("exercise", "ended"),
        source="The end of Able Archer 83 on 11 Nov 1983 (Jones 2016; PFIAB 1990).",
    )
    usa.action(
        "raise_alert",
        guard={"level": V.us_alert == "normal", "observed": V.pact == "readied"},
        effect=Set("us_alert", "raised"),
        source=(
            "Raising the alert of US forces in Europe in answer to the observed Soviet "
            "readiness, which Lt Gen Perroots (USAFE intelligence) advised against in Nov 1983 "
            "(PFIAB 1990; Perroots's memorandum of Jan 1989). The documented alternative, not "
            "taken."
        ),
    )

    ussr.action(
        "ready_forces",
        guard={
            "level": V.pact == "normal",
            "reading": V.warning | (V.belief == "first_strike_intent"),
        },
        effect=Set("pact", "readied"),
        source=(
            "The readying of nuclear-capable aircraft of the 4th Air Army in the GDR and Poland "
            "and the alert of Soviet forces in Eastern Europe, 8 to 11 Nov 1983 (PFIAB 1990; "
            "Jones 2016)."
        ),
    )
    ussr.action(
        "stand_down",
        guard={"level": V.pact == "readied", "quiet": V.exercise == "ended"},
        effect=Set("pact", "normal"),
        source=(
            "The Soviet stand-down after the exercise ended, from 11 to 12 Nov 1983 (PFIAB 1990)."
        ),
    )
    ussr.action(
        "preempt",
        guard={
            "warning": V.belief == "first_strike_intent",
            "indicators": V.warning,
            "ready": V.pact == "readied",
        },
        effect=Set("strike", True),
        source=(
            "A preemptive strike on warning, the purpose of RYAN (the KGB's instructions of "
            "Feb 1983 to report preparations for a surprise nuclear attack) and of the Soviet "
            "doctrine of preemption (Andrew and Gordievsky (eds.), Instructions from the "
            "Centre, 1991; PFIAB 1990). Not taken."
        ),
    )

    nature.event(
        "flash_reports",
        guard={"level": ~V.warning, "watching": V.belief == "first_strike_intent"},
        effect=Set("warning", True),
        source=(
            "The KGB's flash telegrams of 8 or 9 Nov 1983 to the residencies reporting alerts "
            "at US bases in Europe, read through RYAN's indicators (Andrew and Gordievsky "
            "(eds.) 1991; Jones 2016; the date of the telegram not verified)."
        ),
    )
    nature.event(
        "accident",
        guard={"readied": V.pact == "readied", "raised": V.us_alert == "raised"},
        effect=[Set("strike", True), Set("accident", True)],
        source=(
            "An unintended release with both sides' forces at raised alert, the danger the "
            "PFIAB report of 1990 names in concluding that the United States 'may have "
            "inadvertently placed our relations with the Soviet Union on a hair trigger' "
            "(PFIAB 1990; Sagan 1993)."
        ),
    )

    m.invariant("no_war", ~V.strike)
    m.ending("STRIKE", V.strike)
    return m


def entry(year: dict[str, str]) -> dict[str, object]:
    """The Soviet reading of American aims with which the exercise is watched."""
    return {"belief": year["belief_USSR_USA"]}


def exit_map(day: dict[str, str], year: dict[str, str]) -> dict[str, object]:
    if day["strike"] == "True":
        return {"esc": "strategic", "accidental": day["accident"] == "True"}
    return {}


model = build()


def crisis(sub=None) -> Crisis:
    return Crisis(
        "USA", "able_archer", sub or model.compile(), entry, exit_map, name="able_archer_1983"
    )
