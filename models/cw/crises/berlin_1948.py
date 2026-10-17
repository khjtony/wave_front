"""The Berlin blockade, 24 June 1948 to 12 May 1949, one tick per week: a crisis sub-game of
Cold War v0 entered by ``USSR.blockade`` in 1948.

The model of docs/ontology_cw.md section 10.1 and docs/actions_cw.md section 6 (decisions D5).
Tick 0 is the week from Thursday 24 June 1948 (the blockade imposed in the night of 23 to 24
June); tick t is the week from 24 June 1948 + 7t days; the lifting of 12 May 1949 falls in
tick 46 and the horizon is tick 47. A decision falls in the week that contains its day; its
effects are visible the next week.

Actors: ``USA`` (the Western powers' decisions, taken in Washington: Truman, the NSC, Clay),
``USSR`` and Nature (the winter and the city's supply).

``entry`` starts every variable at its declared value (the sub-game is entered only in 1948).
``exit`` maps the sub-game's endings to the coarse ``esc``: a settlement or a Western
withdrawal returns ``peace``, a war returns ``conventional``, an unresolved blockade at the
horizon returns ``crisis``.
"""

from __future__ import annotations

from wavefront.engine import Crisis
from wavefront.model import Bump, Model, Set, SetIf, V

HORIZON = 47
DAY0 = "1948-06-24"


def build() -> Model:
    m = Model(
        "cw_berlin_1948",
        horizon=HORIZON,
        description=(
            "The Berlin blockade, 24 Jun 1948 to 12 May 1949, one tick per week: a crisis "
            "sub-game of cw_v0 (docs/ontology_cw.md section 10.1)."
        ),
    )
    m.var("airlift", levels=["none", "improvised", "sustained"], init="none", monotone=True)
    m.var("talks", levels=["none", "demands", "concession", "agreed"], init="none", monotone=True)
    m.flag("conceded", init=False, monotone=True)
    m.var("access", levels=["blockaded", "lifted"], init="blockaded", monotone=True)
    m.var("esc_b", levels=["standoff", "clash", "war"], init="standoff")
    m.var("position", levels=["in_berlin", "withdrawn"], init="in_berlin", monotone=True)

    usa = m.actor("USA", observes=V.all())
    ussr = m.actor("USSR", observes=V.all())
    nature = m.nature()

    usa.action(
        "airlift",
        guard={"level": V.airlift == "none", "position": V.position == "in_berlin"},
        effect=Set("airlift", "improvised"),
        source=(
            "Clay's and LeMay's improvised airlift from 26 Jun 1948 and Truman's decision of "
            "28 Jun 1948 to stay in Berlin ('we are going to stay, period') (FRUS 1948 vol. II; "
            "Tusa and Tusa, The Berlin Blockade, 1988). The resistance without escalation of "
            "claim C4."
        ),
    )
    usa.action(
        "expand_airlift",
        guard={"level": V.airlift == "improvised"},
        effect=raise_airlift(),
        delay=24,
        source=(
            "The NSC meeting of 22 Jul 1948: Truman orders 75 more C-54s and rejects Clay's "
            "armed convoy; Tunner's Combined Airlift Task Force from Oct 1948; the airlift "
            "carries the city's winter minimum from Jan 1949 (5,500 tons a day in Jan, 8,000 in "
            "Apr) (FRUS 1948 vol. II; Miller, To Save a City, 2000). Delay 24: decided in the "
            "week of 22 Jul (tick 4), sustained from the week of 6 Jan 1949 (tick 29)."
        ),
    )
    usa.action(
        "convoy",
        guard={"level": V.esc_b == "standoff", "position": V.position == "in_berlin"},
        effect=Bump("esc_b", 1),
        source=(
            "Clay's proposal of an armed convoy up the autobahn (cable of 10 Jul 1948), "
            "rejected by Truman and the NSC on 22 Jul 1948 (FRUS 1948 vol. II; Smith (ed.), The "
            "Papers of General Lucius D. Clay, 1974). The documented alternative, not taken."
        ),
    )
    usa.action(
        "withdraw",
        guard={"level": V.position == "in_berlin"},
        effect=Set("position", "withdrawn"),
        source=(
            "Withdrawal from Berlin, put to Truman by Royall and Forrestal on 28 Jun 1948 and "
            "refused ('we stay in Berlin'); Bradley's and the Army's doubts of Jun to Jul 1948 "
            "(FRUS 1948 vol. II; Millis (ed.), The Forrestal Diaries, 1951). Not taken."
        ),
    )
    usa.action(
        "agree",
        guard={"terms": V.talks == "concession"},
        effect=Set("talks", "agreed"),
        source=(
            "The Jessup-Malik conversations from 15 Feb 1949 and the four-power communique of "
            "4 May 1949 (lifting of the restrictions on 12 May, a Council of Foreign Ministers on "
            "23 May) (FRUS 1949 vol. III)."
        ),
    )
    usa.action(
        "concede",
        guard={"terms": V.talks == "demands", "level": ~V.conceded},
        effect=Set("conceded", True),
        source=(
            "Acceptance of Stalin's terms of Aug 1948 (the Soviet mark as Berlin's sole "
            "currency, the London programme deferred), pressed by the French and considered "
            "in the State Department during the Moscow talks of 2 to 30 Aug 1948 and refused "
            "(FRUS 1948 vol. II; Narinsky 1996). Not taken."
        ),
    )
    usa.action(
        "fight",
        guard={"level": V.esc_b == "clash"},
        effect=Bump("esc_b", 1),
        source=(
            "Forcing the access routes against Soviet resistance: Clay's plan for an armed "
            "convoy to fight through, with the Joint Chiefs' war plans of 1948 (Halfmoon) "
            "(Ross, American War Plans 1945-1950, 1996; FRUS 1948 vol. II)."
        ),
    )
    usa.action(
        "back_down",
        guard={"level": V.esc_b == "clash"},
        effect=Bump("esc_b", -1),
        source=(
            "Breaking off a clash on the access routes, the Western choice of Jul 1948 in "
            "favour of the airlift (Trachtenberg, A Constructed Peace, 1999)."
        ),
    )

    ussr.action(
        "offer_talks",
        guard={"level": V.talks == "none"},
        effect=Set("talks", "demands"),
        source=(
            "Stalin's and Molotov's talks with the Western envoys in Moscow, 2 to 30 Aug 1948, "
            "on Soviet terms (the Soviet mark in all Berlin, the London programme suspended) "
            "(Narinsky 1996; FRUS 1948 vol. II)."
        ),
    )
    ussr.action(
        "concede_terms",
        guard={"level": V.talks == "demands", "airlift": V.airlift == "sustained"},
        effect=Set("talks", "concession"),
        source=(
            "Stalin's answers to Kingsbury Smith of 30 Jan 1949, omitting the currency "
            "question, and Malik's confirmation to Jessup of 15 Mar 1949, after the airlift had "
            "carried the city through the winter (Narinsky 1996; Shlaim, The United States and "
            "the Berlin Blockade, 1983). Part airlift: the concession followed the airlift's "
            "success."
        ),
    )
    ussr.action(
        "lift",
        guard={"terms": (V.talks == "agreed") | V.conceded, "level": V.access == "blockaded"},
        effect=Set("access", "lifted"),
        source="The lifting of the blockade at midnight of 11 to 12 May 1949 (FRUS 1949 vol. III).",
    )
    ussr.action(
        "harass",
        guard={"level": V.esc_b == "standoff", "airlift": V.airlift != "none"},
        effect=Bump("esc_b", 1),
        source=(
            "Interference with the air corridors beyond the buzzing, barrage balloons and "
            "searchlights of 1948 to 1949: shooting down transports, considered in Moscow and "
            "not taken (Narinsky 1996; Harrington, Berlin on the Brink, 2012). The documented "
            "alternative, not taken."
        ),
    )
    ussr.action(
        "fight",
        guard={"level": V.esc_b == "clash"},
        effect=Bump("esc_b", 1),
        source=(
            "Soviet armed resistance to a convoy on the autobahn, the response Clay expected "
            "and Sokolovsky's forces were placed for in Jul 1948 (Narinsky 1996)."
        ),
    )
    ussr.action(
        "back_down",
        guard={"level": V.esc_b == "clash"},
        effect=Bump("esc_b", -1),
        source=(
            "Soviet restraint in the corridors after incidents: no Soviet attack on the "
            "airlift from Jun 1948 to May 1949 (Harrington 2012)."
        ),
    )

    nature.event(
        "city_fails",
        guard={"winter": V.tick >= 22, "short": V.airlift != "sustained"},
        effect=SetIf(V.position == "in_berlin", "position", "withdrawn"),
        source=(
            "The winter of 1948 to 1949: without an airlift able to carry coal and food at the "
            "winter minimum (4,500 to 5,600 tons a day), the western sectors could not be held "
            "(the Army's and Clay's estimates of Oct to Nov 1948; Miller 2000). Part winter: "
            "from the week of 25 Nov 1948."
        ),
    )

    no_war = V.esc_b < "war"
    m.invariant("no_war", no_war)
    m.ending("WAR", V.esc_b == "war")
    m.ending("WITHDRAWAL", (V.position == "withdrawn") & no_war)
    m.ending(
        "SETTLED",
        (V.access == "lifted") & ~V.conceded & (V.position == "in_berlin") & no_war,
    )
    m.ending(
        "TERMS",
        (V.access == "lifted") & V.conceded & (V.position == "in_berlin") & no_war,
    )
    return m


def raise_airlift() -> SetIf:
    return SetIf(V.airlift < "sustained", "airlift", "sustained")


def entry(year: dict[str, str]) -> dict[str, object]:
    """Every fine variable at its declared value."""
    return {}


def exit_map(week: dict[str, str], year: dict[str, str]) -> dict[str, object]:
    """War returns a conventional war between the principals; an unresolved blockade at the
    horizon a standing crisis; a settlement, terms or a withdrawal changes nothing."""
    if week["esc_b"] == "war":
        return {"esc": "conventional"}
    if week["access"] == "blockaded" and week["position"] == "in_berlin":
        return {"esc": "crisis"}
    return {}


model = build()


def crisis(sub=None) -> Crisis:
    return Crisis("USSR", "blockade", sub or model.compile(), entry, exit_map, name="berlin_1948")
