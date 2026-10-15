"""July 1914 v0: the crisis from Sarajevo to the British ultimatum, one tick per day.

The model of docs/ontology_1914.md and docs/actions_1914.md as settled in
docs/july1914_decisions.md. The registered claims J1 to J7 (docs/july1914_testbed.md
section 3) were committed before any guard was written; J2 to J6 are hold-out claims under a
total hold-out (testbed section 0), so after their first sight nothing here changes for them.

Time: one tick is one day. The state at tick t is the start of day t, tick 0 being Sunday
28 June 1914 (Sarajevo). The joint move at tick t is what each actor decided during day t (a
decision taken after midnight counts on its day); its effects are visible at t + 1. Tick 37
is 4 August 1914, the last day of decisions; the DSL horizon is 38, the state after 4 August
(the British ultimatum expired at 23:00 London time). A reaction to another actor's decision
of the same day appears the next day ([SQR]); Nature plays one event per tick ([NSL]).

Actors (decisions D2): ``AUH``, ``GER``, ``RUS``, ``FRA``, ``GBR`` and Nature (Serbia's
reply, the arrival of Lichnowsky's telegrams in Berlin, the timetable's step into Belgium).

Cadence (decisions D3): each principal decides at most once every k days, k the smallest gap
between two consecutive realized decisions of that government (``CADENCE``, with the record in
``CADENCE_SOURCES``): AUH 3, FRA 2, GER, RUS and GBR 1. ``build(cadence=False)`` sets every
cadence to 1 (claim J7).

Hidden objectives (swept, no ``assume``): ``aims_GER`` (localize | continental), hidden from
every other principal; ``aims_RUS`` (deter | fight), hidden from AUH and GER. A guard part
named ``hypothesis`` is a hypothesis gate [H].

Pre-commitments (decisions D4): mobilization levels read the order; nothing lowers a
mobilization except Russia's ``revoke`` before general mobilization. The German plan's
coupling of mobilization and war is the part ``coupling`` of ``GER.mobilize_east`` (the
eastern-only deployment abandoned in April 1913): relaxing ``GER.mobilize_east:coupling``
is the coupling relaxed. The plan's western steps are the fairness ``western_timetable``
(the Belgian ultimatum and the declaration on France) and ``liege`` (the entry into
Belgium); the General Staff's rule that Germany mobilizes when Russia does is the fairness
``mobilization_race``.

``belief_GER_GBR`` is read by no guard, fairness constraint or profile (decisions D5): it is
the record of Berlin's reading that claim J4 measures.
"""

from __future__ import annotations

from pathlib import Path

from wavefront.model import FALSE, Bump, Model, Set, SetIf, V

HORIZON = 38  # the state after 4 August 1914 (tick 37 is the last day of decisions)
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "july1914"
REALIZED_MOVES = DATA / "realized_moves.csv"
DAY0 = "1914-06-28"

PRINCIPALS = ("AUH", "GER", "RUS", "FRA", "GBR")

# Decisions D3: the cadence of each principal is the smallest gap, in days, between two
# consecutive realized declared decisions of that government (data/july1914/decisions.csv).
CADENCE = {"AUH": 3, "GER": 1, "RUS": 1, "FRA": 2, "GBR": 1}
CADENCE_SOURCES = {
    "AUH": (
        "Common Ministerial Council of 7 Jul (tick 9) and 19 Jul 1914 (tick 21); the partial "
        "mobilization against Serbia ordered 25 Jul (tick 27); the declaration of war on "
        "Serbia, 28 Jul (tick 30); the general mobilization signed 31 Jul (tick 33). Gaps 12, "
        "6, 3, 3: k = 3. The Austrian Red Book; the Council minutes in Geiss (ed.), July 1914 "
        "(1967); Albertini vol. II."
    ),
    "GER": (
        "The blank cheque of 5 to 6 Jul (tick 7); the Halt in Belgrade transmitted 28 Jul "
        "(tick 30); the telegrams to Tschirschky of 30 Jul 02:55 and 03:00 (tick 32); the "
        "Kriegsgefahrzustand, 31 Jul (tick 33); mobilization and the declaration on Russia, "
        "1 Aug (tick 34); the ultimatum to Belgium, 2 Aug (tick 35); the declaration on France, "
        "3 Aug (tick 36). Consecutive days from 30 Jul: k = 1. Kautsky documents; Geiss (ed.)."
    ),
    "RUS": (
        "The Council of Ministers of 24 Jul and the Tsar's council at Krasnoe Selo of 25 Jul "
        "(the period preparatory to war, one decision at tick 27); the partial mobilization of "
        "29 Jul (tick 31); the general mobilization ordered 30 Jul about 17:00 (tick 32). "
        "Consecutive days: k = 1. Russian Orange Book; Lieven, Towards the Flame (2015); "
        "Albertini vol. II."
    ),
    "FRA": (
        "Poincare and Viviani at sea from 23 Jul, in Paris on 29 Jul; the covering troops with "
        "the ten-kilometre withdrawal, Council of Ministers of 30 Jul (tick 32); the general "
        "mobilization, 1 Aug 16:00 (tick 34). Gap 2: k = 2. The voyage is the guard part "
        "in_paris (tick >= 31), not a cadence. DDF 3e serie vol. XI; French Yellow Book."
    ),
    "GBR": (
        "The Cabinets of 24, 27 and 29 Jul and 1 Aug took no decision the model represents; "
        "the naval assurance, 2 Aug (tick 35); Grey's statement on Belgium, 3 Aug (tick 36); "
        "the ultimatum to Germany, 4 Aug (tick 37). Consecutive days: k = 1. British "
        "Documents vol. XI; Asquith's letters to Venetia Stanley."
    ),
}


def raise_to(var: str, level: str) -> SetIf:
    """``var := max(var, level)``."""
    return SetIf(V[var] < level, var, level)


def build(cadence: bool = True) -> Model:
    """The July 1914 model; with ``cadence=False`` every principal decides daily (J7)."""
    k = CADENCE if cadence else dict.fromkeys(CADENCE, 1)
    m = Model(
        "july1914_v0" if cadence else "july1914_v0_daily",
        horizon=HORIZON,
        description=(
            "The July 1914 crisis, 28 June to 4 August 1914, one tick per day: Austria-Hungary, "
            "Germany, Russia, France, Britain and Nature, after docs/ontology_1914.md and "
            "docs/actions_1914.md with the decisions of docs/july1914_decisions.md"
            + ("" if cadence else "; every cadence set to 1 (claim J7)")
            + ". Every result is conditional on this model and its initial state."
        ),
    )

    # -- hidden objectives (ontology section 1) ----------------------------------------------
    m.var(
        "aims_GER",
        levels=["localize", "continental"],
        init=None,
        hidden_from=["AUH", "RUS", "FRA", "GBR"],
    )
    m.var("aims_RUS", levels=["deter", "fight"], init=None, hidden_from=["AUH", "GER"])

    # -- the Austro-Serbian crisis (ontology section 2) --------------------------------------
    m.flag("blank_cheque", init=False, monotone=True)
    m.var(
        "ultimatum",
        levels=["none", "resolved", "delivered", "rejected"],
        init="none",
        monotone=True,
    )
    m.var("halt_in_belgrade", levels=["none", "proposed", "accepted"], init="none", monotone=True)
    m.var("war_AUH_SER", levels=["peace", "war"], init="peace", monotone=True)

    # -- mobilization orders (ontology section 3) --------------------------------------------
    m.var("mob_AUH", levels=["none", "partial", "general"], init="none", monotone=True)
    m.var("mob_RUS", levels=["none", "pre_mobilization", "partial", "general"], init="none")
    m.var("mob_GER", levels=["none", "kriegsgefahr", "general"], init="none", monotone=True)
    m.var("mob_FRA", levels=["none", "covering_troops", "general"], init="none", monotone=True)

    # -- the great-power wars, Belgium, Britain (ontology sections 4 and 5) ------------------
    m.var("war_GER_RUS", levels=["peace", "war"], init="peace", monotone=True)
    m.var("war_GER_FRA", levels=["peace", "war"], init="peace", monotone=True)
    m.var("belgium", levels=["neutral", "demanded", "invaded"], init="neutral", monotone=True)
    m.var("belief_GER_GBR", levels=["stays_out", "uncertain", "fights"], init="stays_out")
    m.var(
        "commitment_GBR",
        levels=["none", "naval_assurance", "belgian_guarantee", "war"],
        init="none",
        monotone=True,
    )

    # -- actors ------------------------------------------------------------------------------
    auh = m.actor("AUH", observes=V.all(), cadence=k["AUH"])
    ger = m.actor("GER", observes=V.all(), cadence=k["GER"])
    rus = m.actor("RUS", observes=V.all(), cadence=k["RUS"])
    fra = m.actor("FRA", observes=V.all(), cadence=k["FRA"])
    gbr = m.actor("GBR", observes=V.all(), cadence=k["GBR"])
    nature = m.nature()

    # -- Austria-Hungary ---------------------------------------------------------------------
    auh.action(
        "council",
        guard={"german_support": V.blank_cheque, "target": V.ultimatum == "none"},
        effect=Set("ultimatum", "resolved"),
        source=(
            "Common Ministerial Council of 7 Jul 1914 (minutes in the Austrian documents; Geiss "
            "(ed.), July 1914, 1967): action against Serbia decided in principle, with demands "
            "to be put in a note, against Tisza's objection to a surprise attack; convened on "
            "Hoyos's return from Berlin with the German assurance (Szogyeny's telegrams of 5 "
            "and 6 Jul)."
        ),
    )
    auh.action(
        "ultimatum",
        guard={"resolved": V.ultimatum == "resolved", "council": V.tick >= 16},
        effect=Set("ultimatum", "delivered"),
        delay=4,
        source=(
            "Tisza's consent, 14 Jul 1914 (Berchtold's report to Franz Joseph of 14 Jul); the "
            "Common Ministerial Council of 19 Jul approving the text and fixing delivery for "
            "23 Jul after Poincare's departure from St Petersburg; Giesl's delivery in Belgrade, "
            "23 Jul 18:00, with a 48-hour limit (Austrian Red Book; Geiss (ed.); Albertini "
            "vol. II). Part council: the joint government's approval needed the Hungarian "
            "premier, whose consent the record dates 14 Jul. Delay 4: decided 19 Jul, "
            "delivered 23 Jul."
        ),
    )
    auh.action(
        "mobilize_partial",
        guard={
            "occasion": V.ultimatum >= "delivered",
            "harvest_leave": V.tick >= 27,
            "level": V.mob_AUH == "none",
        },
        effect=Set("mob_AUH", "partial"),
        source=(
            "Franz Joseph's order of 25 Jul 1914 (evening, at Bad Ischl) for the mobilization "
            "against Serbia (Plan B, eight corps), first mobilization day 28 Jul (Albertini "
            "vol. II). Part occasion: the Council of 19 Jul prepared mobilization as the sanction "
            "of the note. Part harvest_leave: Conrad's statement to Berchtold in the week after "
            "the Council of 7 Jul that men of several corps were on harvest leave until 25 Jul "
            "and that an early recall would alarm Europe (Clark, The Sleepwalkers, 2012; date "
            "of the statement not verified)."
        ),
    )
    auh.action(
        "declare_war_SER",
        guard={
            "rejected": V.ultimatum == "rejected",
            "mobilizing": V.mob_AUH >= "partial",
            "level": V.war_AUH_SER == "peace",
        },
        effect=Set("war_AUH_SER", "war"),
        source=(
            "Berchtold's telegram to the Serbian government of 28 Jul 1914 (about 11:00), "
            "declaring war, sent against Conrad's advice to wait until operations could begin "
            "(about 12 Aug); Franz Joseph's signature of 27 Jul (Austrian Red Book; Albertini "
            "vol. II)."
        ),
    )
    auh.action(
        "accept_halt",
        guard={"proposed": V.halt_in_belgrade == "proposed"},
        effect=Set("halt_in_belgrade", "accepted"),
        source=(
            "The Halt in Belgrade put to Berchtold by Tschirschky, 29 to 30 Jul 1914 "
            "(Bethmann's telegrams of 28 Jul 22:15 and 30 Jul 02:55 and 03:00); Berchtold's "
            "evasive answer of 30 Jul; the Common Ministerial Council of 31 Jul declining it "
            "(Geiss (ed.); Albertini vol. II). The documented alternative, not taken."
        ),
    )
    auh.action(
        "mobilize_general",
        guard={
            "russian_measures": V.mob_RUS >= "partial",
            "halt_refused": V.halt_in_belgrade != "accepted",
            "level": V.mob_AUH != "general",
        },
        effect=Set("mob_AUH", "general"),
        source=(
            "Franz Joseph's order of general mobilization signed 31 Jul 1914 12:23, first day "
            "4 Aug, on the news of the Russian partial mobilization and Moltke's telegram to "
            "Conrad of 30 Jul urging it; decided with the Council of 31 Jul that declined the "
            "Halt in Belgrade (Albertini vol. II; Mombauer, Helmuth von Moltke and the Origins "
            "of the First World War, 2001)."
        ),
    )

    # -- Germany -----------------------------------------------------------------------------
    ger.action(
        "blank_cheque",
        guard={"once": ~V.blank_cheque},
        effect=Set("blank_cheque", True),
        source=(
            "Wilhelm II's assurance to Szogyeny at Potsdam, 5 Jul 1914, and Bethmann "
            "Hollweg's and Zimmermann's confirmation to Szogyeny and Hoyos, 6 Jul (Szogyeny's "
            "telegrams of 5 and 6 Jul; Geiss (ed.), July 1914)."
        ),
    )
    ger.action(
        "restrain_vienna",
        guard={
            "occasion": V.ultimatum == "rejected",
            "open": V.halt_in_belgrade != "accepted",
        },
        effect=SetIf(V.halt_in_belgrade == "none", "halt_in_belgrade", "proposed"),
        source=(
            "Wilhelm II's note to Jagow of 28 Jul 1914 (morning) on the Serbian reply (Belgrade "
            "as a pledge); Bethmann's telegram to Tschirschky of 28 Jul 22:15 transmitting it "
            "in weakened form; Bethmann's telegrams to Tschirschky of 30 Jul 02:55 and 03:00 "
            "after Lichnowsky's report of Grey's warning ('we must decline to be drawn into a "
            "world conflagration'), suspended on the night of 30 Jul (Kautsky documents; Geiss "
            "(ed.); the hour of the suspension not verified)."
        ),
    )
    ger.action(
        "kriegsgefahr",
        guard={
            "hypothesis": (V.aims_GER == "continental") | (V.mob_RUS == "general"),
            "russian_measures": V.mob_RUS >= "partial",
            "level": V.mob_GER == "none",
        },
        effect=Set("mob_GER", "kriegsgefahr"),
        source=(
            "The Zustand drohender Kriegsgefahr proclaimed 31 Jul 1914 13:00 on the news of the "
            "Russian general mobilization, with the ultimatums to Russia (12 hours) and France "
            "(18 hours); Falkenhayn's demand of 29 Jul for it after the Russian partial measures, "
            "refused by Bethmann that day; Moltke's memorandum of 29 Jul on the political "
            "situation (Mombauer 2001; Geiss (ed.)). [H]: under localize Germany proclaims it "
            "only once Russia has ordered general mobilization; under continental the Russian "
            "partial measures suffice (Falkenhayn's alternative)."
        ),
    )
    ger.action(
        "mobilize",
        guard={"sequence": V.mob_GER == "kriegsgefahr"},
        effect=[Set("mob_GER", "general"), Set("war_GER_RUS", "war")],
        source=(
            "The mobilization order of 1 Aug 1914 (about 17:00), first day 2 Aug, and the "
            "declaration of war on Russia handed to Sazonov by Pourtales the same evening "
            "(about 19:00): under the deployment plan in force since April 1913 (Aufmarsch I "
            "West only) mobilization meant war and the declaration was made at once to open the "
            "western operations (Mombauer 2001; Trachtenberg, 'The Meaning of Mobilization in "
            "1914', International Security 1990/91)."
        ),
    )
    ger.action(
        "mobilize_east",
        guard={"sequence": V.mob_GER == "kriegsgefahr", "coupling": FALSE},
        effect=Set("mob_GER", "general"),
        source=(
            "Wilhelm II's demand of 1 Aug 1914 (evening, on Lichnowsky's telegram) that the "
            "army deploy against Russia only, and Moltke's refusal: no plan existed, the "
            "eastern deployment (Aufmarsch II Ost) having been abandoned in April 1913 "
            "(Moltke's postwar memoir; Mombauer 2001). Part coupling: the eastern-only "
            "deployment did not exist; relaxing it is the coupling relaxed (claim J2)."
        ),
    )
    ger.action(
        "ultimatum_belgium",
        guard={"plan": V.war_GER_RUS == "war", "target": V.belgium == "neutral"},
        effect=Set("belgium", "demanded"),
        source=(
            "The note to Belgium drafted by Moltke on 26 Jul 1914, sent sealed to Below-Saleske "
            "on 29 Jul, delivered 2 Aug 19:00 with a 12-hour limit; the occupation of "
            "Luxembourg the same day (Geiss (ed.); Albertini vol. III)."
        ),
    )
    ger.action(
        "declare_war_FRA",
        guard={"plan": V.war_GER_RUS == "war", "target": V.war_GER_FRA == "peace"},
        effect=Set("war_GER_FRA", "war"),
        source=(
            "The declaration of war on France handed to Viviani by Schoen, 3 Aug 1914 18:45, "
            "on the pretext of French air raids (Geiss (ed.); Albertini vol. III)."
        ),
    )

    # -- Russia ------------------------------------------------------------------------------
    rus.action(
        "pre_mobilize",
        guard={"occasion": V.ultimatum >= "delivered", "level": V.mob_RUS == "none"},
        effect=Set("mob_RUS", "pre_mobilization"),
        source=(
            "The Council of Ministers of 24 Jul 1914 (Sazonov, Krivoshein: partial mobilization "
            "in principle and preparatory measures) and the Tsar's council at Krasnoe Selo of "
            "25 Jul approving the 'period preparatory to war' from 26 Jul (Lieven, Towards the "
            "Flame, 2015; Russian Orange Book; the council journals as printed in the "
            "literature, not verified)."
        ),
    )
    rus.action(
        "mobilize_partial",
        guard={
            "prepared": V.mob_RUS == "pre_mobilization",
            "occasion": V.war_AUH_SER == "war",
        },
        effect=Set("mob_RUS", "partial"),
        source=(
            "Sazonov's decision of 28 Jul 1914 to announce the partial mobilization of the "
            "Kiev, Odessa, Moscow and Kazan districts on the Austro-Hungarian declaration of "
            "war; announced 29 Jul and ordered in the night of 29 to 30 Jul (Lieven 2015; "
            "Albertini vol. II). Part occasion: the Council of 25 Jul made it conditional on "
            "Austro-Hungarian military action against Serbia."
        ),
    )
    rus.action(
        "mobilize_general",
        guard={
            "hypothesis": (V.aims_RUS == "fight")
            | (V.mob_GER >= "kriegsgefahr")
            | (V.mob_AUH == "general"),
            "prepared": V.mob_RUS >= "pre_mobilization",
            "level": V.mob_RUS != "general",
        },
        effect=Set("mob_RUS", "general"),
        source=(
            "The general mobilization authorized by Nicholas II at Peterhof on 30 Jul 1914 "
            "after Sazonov's audience and ordered about 17:00 (Yanushkevich, Dobrorolsky), "
            "first day 31 Jul (Lieven 2015; Albertini vol. II). [H]: under deter Russia orders "
            "general mobilization only once Germany or Austria-Hungary has taken general "
            "measures; under fight the preparatory period suffices."
        ),
    )
    rus.action(
        "revoke",
        guard={"revocable": V.mob_RUS.is_in(["pre_mobilization", "partial"])},
        effect=Bump("mob_RUS", -1),
        source=(
            "Nicholas II's countermand of 29 Jul 1914 (about 21:40, after Wilhelm II's "
            "telegram) of the general mobilization order signed that day, replaced by the "
            "partial order: a Russian order revoked before general mobilization had begun "
            "(Lieven 2015; Albertini vol. II). The model's general mobilization is irrevocable, "
            "so the documented revocation is represented as one step back from the partial or "
            "preparatory level (decisions D4)."
        ),
    )

    # -- France ------------------------------------------------------------------------------
    in_paris = V.tick >= 31
    fra.action(
        "covering_troops",
        guard={
            "in_paris": in_paris,
            "threat": (V.mob_RUS >= "partial") | (V.mob_GER != "none"),
            "level": V.mob_FRA == "none",
        },
        effect=Set("mob_FRA", "covering_troops"),
        source=(
            "The Council of Ministers of 30 Jul 1914 granting Joffre the covering troops "
            "without reservists, with the ten-kilometre withdrawal from the frontier (Messimy's "
            "order of 30 Jul; DDF 3e serie vol. XI; Joffre's memoirs). Part in_paris: "
            "Poincare and Viviani were at sea from 23 Jul and back in Paris on 29 Jul; the "
            "Council deferred military decisions to their return (Poincare, Au service de la "
            "France vol. IV)."
        ),
    )
    fra.action(
        "mobilize",
        guard={
            "in_paris": in_paris,
            "german_measures": V.mob_GER != "none",
            "level": V.mob_FRA != "general",
        },
        effect=Set("mob_FRA", "general"),
        source=(
            "The general mobilization decided by the Council of Ministers on 1 Aug 1914 and "
            "posted from 15:45 to 16:00, after the German ultimatum of 31 Jul and Joffre's "
            "demand (DDF 3e serie vol. XI; French Yellow Book)."
        ),
    )

    # -- Britain -----------------------------------------------------------------------------
    continental_war = (V.war_GER_RUS == "war") | (V.war_GER_FRA == "war")
    gbr.action(
        "naval_assurance",
        guard={
            "continental_war": continental_war,
            "level": V.commitment_GBR < "naval_assurance",
        },
        effect=raise_to("commitment_GBR", "naval_assurance"),
        source=(
            "The Cabinet of 2 Aug 1914 (morning) and Grey's assurance to Cambon that afternoon "
            "that the fleet would protect the French coasts against a German fleet in the "
            "Channel, after the Cabinets of 29 Jul and 1 Aug had refused any commitment; the "
            "Grey-Cambon letters of 22 to 23 Nov 1912 (British Documents vol. XI; Asquith's "
            "letters to Venetia Stanley, 2 Aug)."
        ),
    )
    gbr.action(
        "guarantee_belgium",
        guard={
            "continental_war": continental_war,
            "level": V.commitment_GBR < "belgian_guarantee",
        },
        effect=[raise_to("commitment_GBR", "belgian_guarantee"), Bump("belief_GER_GBR", 2)],
        source=(
            "The Cabinet of 2 Aug 1914 (evening) resolving that a substantial violation of "
            "Belgian neutrality would compel action, and Grey's statement in the Commons, 3 Aug "
            "(about 15:00; Hansard; British Documents vol. XI); read in Berlin as Britain "
            "fighting (belief_GER_GBR raised, clamped)."
        ),
    )
    gbr.action(
        "ultimatum_GER",
        guard={
            "belgian_route": V.belgium >= "demanded",
            "parliament": V.commitment_GBR >= "belgian_guarantee",
            "level": V.commitment_GBR != "war",
        },
        effect=[Set("commitment_GBR", "war"), Bump("belief_GER_GBR", 2)],
        source=(
            "Grey's telegrams to Goschen of 4 Aug 1914: the demand of the morning that Germany "
            "withdraw its ultimatum to Belgium, then the ultimatum expiring at 23:00 London "
            "time; Britain at war from 23:00 (British Documents vol. XI). Part belgian_route: "
            "the demand answered the German note to Belgium known in London on 3 Aug. Part "
            "parliament: it followed Grey's statement of 3 Aug and the House's support."
        ),
    )

    # -- Nature ------------------------------------------------------------------------------
    nature.event(
        "serbian_reply",
        guard={"delivered": V.ultimatum == "delivered"},
        effect=Set("ultimatum", "rejected"),
        source=(
            "The Serbian reply handed to Giesl on 25 Jul 1914 at 17:55, accepting most demands "
            "and refusing point 6; Giesl's departure at 18:30 and the rupture of relations "
            "(Austrian Red Book; Geiss (ed.)). Serbia's government is not a principal."
        ),
    )
    nature.event(
        "lichnowsky_warning",
        guard={"occasion": V.war_AUH_SER == "war"},
        effect=Set("belief_GER_GBR", "fights"),
        source=(
            "Lichnowsky's telegram of 29 Jul 1914 reporting Grey's private warning that Britain "
            "would not stand aside if France were drawn in, received in Berlin that evening "
            "(Kautsky documents; Geiss (ed.); the hour of receipt not verified)."
        ),
    )
    nature.event(
        "lichnowsky_offer",
        guard={
            "occasion": V.mob_GER == "kriegsgefahr",
            "no_commitment": V.commitment_GBR == "none",
        },
        effect=Set("belief_GER_GBR", "uncertain"),
        source=(
            "Lichnowsky's telegram of 1 Aug 1914 reporting Grey's inquiry as an offer of "
            "British and French neutrality, received in Berlin about 17:00, and George V's "
            "telegram of the same night correcting it (Kautsky documents; Geiss (ed.)). The "
            "day's net reading is uncertain (ontology section 5)."
        ),
    )
    nature.event(
        "invade_belgium",
        guard={"demanded": V.belgium == "demanded", "western_war": V.war_GER_FRA == "war"},
        effect=Set("belgium", "invaded"),
        source=(
            "The Belgian refusal of 3 Aug 1914 07:00 and the entry of German troops on 4 Aug "
            "about 08:00 towards Liege, the plan's first operation (Geiss (ed.); Albertini "
            "vol. III). A timetable step carried by Nature (decisions D2)."
        ),
    )

    # -- constraints (actions catalogue, constraints) ----------------------------------------
    m.fairness(
        "reply_deadline",
        actor="Nature",
        trigger=V.ultimatum == "delivered",
        within=2,
        responses=["serbian_reply"],
    )
    m.fairness(
        "mobilization_race",
        actor="GER",
        trigger=(V.mob_RUS == "general") & (V.mob_GER != "general"),
        within=1,
        responses=["kriegsgefahr", "mobilize", "mobilize_east"],
    )
    m.fairness(
        "western_timetable",
        actor="GER",
        trigger=(V.war_GER_RUS == "war") & ((V.belgium == "neutral") | (V.war_GER_FRA == "peace")),
        within=1,
        responses=["ultimatum_belgium", "declare_war_FRA"],
    )
    m.fairness(
        "liege",
        actor="Nature",
        trigger=(V.belgium == "demanded") & (V.war_GER_FRA == "war"),
        within=1,
        responses=["invade_belgium"],
    )

    # -- invariants and endings (ontology section 6) -----------------------------------------
    great_power_war = (
        (V.war_GER_RUS == "war") | (V.war_GER_FRA == "war") | (V.commitment_GBR == "war")
    )
    great_power_mobilization = (
        (V.mob_AUH == "general")
        | (V.mob_RUS >= "partial")
        | (V.mob_GER == "general")
        | (V.mob_FRA == "general")
    )
    m.invariant("no_war_GER_RUS", V.war_GER_RUS == "peace")
    m.invariant("localized", ~great_power_war & ~great_power_mobilization)

    at_horizon = V.tick == HORIZON
    general_war = V.commitment_GBR == "war"
    m.ending("GENERAL_WAR", general_war)
    m.ending("CONTINENTAL_WAR", at_horizon & ~general_war & great_power_war)
    m.ending(
        "LOCALIZED",
        at_horizon & (V.war_AUH_SER == "war") & ~great_power_war & ~great_power_mobilization,
    )
    m.ending("NO_WAR", at_horizon & (V.war_AUH_SER == "peace") & ~great_power_war)
    return m


model = build()
