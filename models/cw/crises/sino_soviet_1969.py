"""The Sino-Soviet confrontation of 1969, from the clashes of March to the opening of the
border talks on 20 October, one tick per week: a crisis sub-game of Cold War v1 entered by
the PRC's ``border_clash`` in 1969.

The model of docs/ontology_cw.md section 12.3 and docs/actions_cw.md section 6
(docs/cw_v1_decisions.md D4). Tick 0 is the week of Monday 17 March 1969, after the clashes
on Zhenbao (Damansky) Island of 2 and 15 March; tick t is the week beginning 17 March + 7t;
the horizon is tick 31, the week of 20 October 1969, when the border talks opened in Beijing.
A decision falls in its week; its effects are visible the next week.

Actors: ``USA`` (Nixon and Kissinger), ``USSR`` (Brezhnev and the Politburo), ``PRC`` (Mao and
Zhou) and Nature. ``build(prc_principal=False)`` gives the PRC's decision to Nature (the build
of coldwar_testbed.md V5 (b), in which the crisis is entered by Nature).

``entry`` starts every variable at its declared value (the sub-game is entered only in 1969,
when the Lop Nur installations exist and the PRC is not aligned with the United States).
``exit`` maps a Soviet strike to ``esc_sino = war`` and every other end to ``esc_sino =
clash``: the talks did not end the armed confrontation along the border (v0's level, to the
normalization of 1989). Agreed talks without a strike also set the coarse flag
``sino_soviet_talks`` (the owner's decision 7f(a) of 2026-10-27, before first sight): Zhou's
acceptance at the Kosygin-Zhou meeting of 11 Sep 1969 and the border talks opened in Beijing on
20 Oct 1969 are carried into the coarse game, where they close ``USSR.strike_china``
(docs/cw_v1_decisions.md D4).
"""

from __future__ import annotations

from wavefront.engine import Crisis
from wavefront.model import Model, Set, V

HORIZON = 31
DAY0 = "1969-03-17"


def build(prc_principal: bool = True) -> Model:
    m = Model(
        "cw_sino_soviet_1969" + ("" if prc_principal else "_prc_scripted"),
        horizon=HORIZON,
        description=(
            "The Sino-Soviet confrontation, 17 Mar to 20 Oct 1969, one tick per week: a crisis "
            "sub-game of cw_v1 (docs/ontology_cw.md section 12.3)"
            + ("" if prc_principal else "; the PRC's decision carried by Nature")
            + "."
        ),
    )
    m.var("border", levels=["clash", "escalated"], init="clash", monotone=True)
    m.var("talks", levels=["none", "proposed", "agreed"], init="none", monotone=True)
    m.flag("soundings", init=False, monotone=True)
    m.flag("us_signal", init=False, monotone=True)
    m.flag("strike", init=False, monotone=True)

    usa = m.actor("USA", observes=V.all())
    ussr = m.actor("USSR", observes=V.all())
    prc = m.actor("PRC", observes=V.all()) if prc_principal else None
    nature = m.nature()
    prc_act = prc.action if prc_principal else nature.event

    ussr.action(
        "propose_talks",
        guard={"level": V.talks == "none"},
        effect=Set("talks", "proposed"),
        source=(
            "The Soviet government's statement of 29 Mar 1969 proposing to resume the border "
            "consultations broken off in 1964, after Kosygin's attempt to telephone Mao on 21 "
            "Mar 1969 was refused (Yang Kuisong, 'The Sino-Soviet Border Clash of 1969', Cold "
            "War History 2000; Gerson, The Sino-Soviet Border Conflict, CNA 2010)."
        ),
    )
    ussr.action(
        "border_offensive",
        guard={"level": V.border == "clash"},
        effect=Set("border", "escalated"),
        source=(
            "The Soviet ambush of a Chinese border unit at Tielieketi (Zhalanashkol), "
            "Xinjiang, 13 Aug 1969, a Soviet-initiated escalation after the summer's "
            "incidents along the Amur and in Xinjiang (Yang 2000; Gerson 2010). Documented "
            "alternative: holding to the March positions."
        ),
    )
    ussr.action(
        "sound_out",
        guard={"level": ~V.soundings},
        effect=Set("soundings", True),
        source=(
            "The KGB officer Davydov's question to Stearman (Department of State), 18 Aug "
            "1969, on the American reaction to a Soviet strike on Chinese nuclear "
            "installations, repeated through Tehran (4 Sep) and by Shevchenko at the UN (5 "
            "Sep 1969) (Burr (ed.), 'Sino-American Relations, 1969', NSArchive Electronic "
            "Briefing Book 49, 2001, docs. 10, 16, 18; Goldstein, 'Return to Zhenbao Island', "
            "in Ross and Jiang (eds.), Re-examining the Cold War, 2001)."
        ),
    )
    ussr.action(
        "strike",
        guard={
            "sounded": V.soundings,
            "refusal": V.talks != "agreed",
            "acquiescence": ~V.us_signal,
        },
        effect=Set("strike", True),
        source=(
            "A strike on the Chinese nuclear installations at Lop Nur, the option the "
            "soundings of Aug to Sep 1969 asked about; not taken (EBB 49 docs. 10 to 24; "
            "Goldstein 2001; Gerson 2010). Part sounded: Moscow weighed it with Washington's "
            "reaction asked first. Part refusal: the threat served to bring Beijing to talks, "
            "and the agreement of 11 Sep 1969 removed its occasion (Gerson 2010; "
            "docs/prc_research.md section 1.12). Part acquiescence: the reaction asked for "
            "was American indifference, which the signals of 14 Aug and 5 Sep 1969 refused "
            "(Kissinger, White House Years, 1979; Goldstein 2001)."
        ),
    )
    usa.action(
        "signal",
        guard={"occasion": (V.border == "escalated") | V.soundings, "level": ~V.us_signal},
        effect=Set("us_signal", True),
        source=(
            "Nixon at the NSC of 14 Aug 1969, the day after Tielieketi, that it was against "
            "American interests for China to be 'smashed' in a Sino-Soviet war, and Under "
            "Secretary Richardson's speech of 5 Sep 1969 that the United States 'could not "
            "fail to be deeply concerned' by an escalation of the conflict (Kissinger 1979; "
            "Burr (ed.) 2001, EBB 49; Goldstein 2001). Part occasion: the signal answered "
            "the Soviet escalation of 13 Aug and the soundings. Documented alternative: the "
            "even-handedness urged by the State Department's Soviet specialists (Kissinger "
            "1979)."
        ),
    )
    prc_act(
        "accept_talks",
        guard={"proposal": V.talks == "proposed"},
        effect=Set("talks", "agreed"),
        source=(
            "Zhou Enlai's meeting with Kosygin at Beijing airport on 11 Sep 1969, on Kosygin's "
            "return from Ho Chi Minh's funeral, agreeing to border talks that opened in "
            "Beijing on 20 Oct 1969 (the Chinese record of the meeting, Wilson Center Digital "
            "Archive; Yang 2000; Gerson 2010). Documented alternative: leaving the Soviet "
            "proposals unanswered, as in spring 1969 (Yang 2000)."
        ),
    )

    m.invariant("no_strike", ~V.strike)
    m.ending("STRIKE", V.strike)
    return m


def entry(year: dict[str, str]) -> dict[str, object]:
    """Every fine variable at its declared value (the sub-game is entered only in 1969)."""
    return {}


def exit_map(week: dict[str, str], year: dict[str, str]) -> dict[str, object]:
    if week["strike"] == "True":
        return {"esc_sino": "war"}
    if week["talks"] == "agreed":
        # The talks agreed (Kosygin and Zhou, 11 Sep 1969; opened 20 Oct 1969) carried into
        # the coarse game (the owner's decision 7f(a), 2026-10-27).
        return {"esc_sino": "clash", "sino_soviet_talks": True}
    return {"esc_sino": "clash"}


model = build()
model_prc_scripted = build(prc_principal=False)


def crisis(sub=None, prc_principal: bool = True) -> Crisis:
    if sub is None:
        sub = (model if prc_principal else model_prc_scripted).compile()
    return Crisis(
        "PRC" if prc_principal else "Nature",
        "border_clash",
        sub,
        entry,
        exit_map,
        name="sino_soviet_1969",
    )
