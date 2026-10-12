"""WW2 v0: Europe, 1936Q1 to 1940Q4, four principals and Nature.

The model of docs/ontology_ww2.md and docs/actions_ww2.md as settled by the architect's
decisions D1 to D11 (docs/ww2_v0_decisions.md). It is the development model of the
historical testbed (docs/ww2_testbed.md); the registered claims T1 to T13 (section 5 there)
were committed before any guard here was written, and every guard, effect, delay, fairness
constraint, profile or assumption edited after a registered test was run against this file is
logged in docs/guard_changelog_ww2.md.

Time: one tick is one quarter; tick 0 is the start of 1936Q1, tick 20 (the horizon) the
start of 1941Q1. The joint move at tick t is what each actor decided during quarter t; its
effects are visible at t + 1 (decisions D1). Same-quarter reactions appear one tick later
and are marked [SQR] in data/ww2/realized_moves.csv.

Actors: ``GER``, ``WEST`` (the United Kingdom and France acting jointly, the United States
as the commitment variable ``commit_US``), ``USSR``, ``JPN`` and Nature (Italy, Poland, the
smaller states, campaign resolution, the United States' domestic decisions).

Hidden objectives (swept, ``init=None``): ``aims_GER`` (revisionist | hegemonic, hidden from
WEST, USSR and JPN) and ``aims_USSR`` (defensive | opportunist, hidden from GER, WEST and
JPN), restricted by ``assume("ussr_defensive")``. A guard part named ``hypothesis`` is a
hypothesis gate (the [H] conjuncts of the catalogue): it is how a swept objective shapes an
action set, not a feasibility condition, and it is counted separately in reports.

Every guard encodes feasibility (capability, institutional constraint, prior condition) as
the catalogue states it, except the hypothesis gates and the belief condition of
``guarantee_poland``, which is the registered T4 claim (decisions D9). Guards that join
independent documented constraints are declared as named parts, each a separate relaxable
assumption ``<actor>.<action>:<part>`` (framework_spec.md section 3.1; decisions D7).

Choices made in coding the documents (each listed in docs/ww2_v0_notes.md, section "Model
step (1.5 to 1.7)"):

* ``arms_JPN`` and ``belief_GER`` are declared with their ontology levels and never changed
  by any action, so they contribute a factor of one to the reachable state count (decisions
  D6, reductions 1 and 3); they are declared so that the hindsight snapshots load as they
  are.
* ``ind_GER`` is a counter ``0..5`` with initial value 3, so that the snapshot integers 3 to
  5 load directly; the values 0 to 2 are never reached.
* ``north_strike`` (flag) replaces the catalogue's ``last_JPN == strike_north``: JPN is not
  declared with ``remember_last`` (decisions D6, reduction 2), and the strike sets the flag
  that ``campaign_siberia`` reads.
* ``german_defeat`` (flag) records the resolution of ``campaign_rhineland`` and defines the
  ending ``GERMAN_DEFEAT`` (decisions D3).
* The fairness constraint ``rhineland_resolution`` on Nature makes ``campaign_rhineland``
  deterministic, as D3 requires: one tick after WEST's ``offensive_west`` against an army at
  ``arms_GER <= rising``, Nature's only available event is the campaign.
* ``campaign_siberia``'s ``japanese_superiority`` part (D7) is the constant ``FALSE``: it
  replaces the catalogue's ``ussr_at_war_in_europe`` term, which was also the constant
  ``FALSE`` and cites the same record (Nomonhan, 1939).
"""

from wavefront.model import FALSE, Bump, Inc, Ite, Model, Set, SetIf, V

HORIZON = 20

model = Model(
    "ww2_v0",
    horizon=HORIZON,
    description=(
        "Europe 1936Q1 to 1940Q4 (one tick per quarter): Germany, the West (Britain and "
        "France), the USSR, Japan and Nature, after docs/ontology_ww2.md and "
        "docs/actions_ww2.md with the architect's decisions D1 to D11. A development model "
        "of the historical testbed; every result is conditional on it and on the initial state."
    ),
)


def raise_to(var: str, level: str) -> SetIf:
    """``var := max(var, level)``: raise ``var`` to ``level`` if it is lower."""
    return SetIf(V[var] < level, var, level)


# -- hidden objectives (ontology section 1) -------------------------------------------------
model.var(
    "aims_GER",
    levels=["revisionist", "hegemonic"],
    init=None,
    hidden_from=["WEST", "USSR", "JPN"],
)
model.var(
    "aims_USSR",
    levels=["defensive", "opportunist"],
    init=None,
    hidden_from=["GER", "WEST", "JPN"],
)

# -- capability and resources (ontology section 2) ------------------------------------------
model.var("arms_GER", levels=["low", "rising", "high", "total"], init="rising", monotone=True)
model.var("arms_WEST", levels=["low", "rising", "high"], init="low", monotone=True)
model.var("arms_USSR", levels=["weak", "strong"], init="strong")
model.var("arms_JPN", levels=["high", "total"], init="high")  # constant in v0
model.counter("ind_GER", max=5, init=3, monotone=True)  # ordinal 3..5 of the ontology
model.var("oil_GER", levels=["dependent", "secured"], init="dependent", monotone=True)

# -- beliefs and commitment (ontology section 3) --------------------------------------------
model.var(
    "belief_WEST", levels=["limited", "uncertain", "hegemonic"], init="limited", monotone=True
)
model.var(
    "belief_GER", levels=["will_not_fight", "uncertain", "will_fight"], init="will_not_fight"
)  # constant in v0 (carried for T9, phase 2)
model.var(
    "commit_WEST", levels=["appease", "wary", "resolved", "at_war"], init="appease", monotone=True
)
model.var(
    "commit_US", levels=["isolationist", "wary", "engaged"], init="isolationist", monotone=True
)

# -- structure (ontology section 4) ---------------------------------------------------------
model.var("treaty", levels=["enforced", "eroded", "dead"], init="eroded")
model.flag("axis", init=False, monotone=True)
model.flag("anticomintern", init=False, monotone=True)
model.flag("nazi_soviet_pact", init=False, monotone=True)
model.flag("polish_guarantee", init=False, monotone=True)
model.flag("anglo_soviet_alliance", init=False, monotone=True)
model.flag("ussr_axis", init=False, monotone=True)
model.flag("italy_estranged", init=True)
model.flag("china_war", init=False, monotone=True)

# -- regions (ontology section 5; monotone except the Rhineland) ----------------------------
model.var("rhineland", levels=["demilitarized", "remilitarized"], init="demilitarized")
model.var("austria", levels=["independent", "annexed"], init="independent", monotone=True)
model.var("sudeten", levels=["czech", "german"], init="czech", monotone=True)
model.var("bohemia", levels=["czech", "german"], init="czech", monotone=True)
model.var(
    "poland", levels=["independent", "german", "partitioned"], init="independent", monotone=True
)
model.var("france", levels=["independent", "at_war", "fallen"], init="independent", monotone=True)
model.var(
    "britain",
    levels=["at_peace", "at_war", "negotiated", "invaded"],
    init="at_peace",
    monotone=True,
)
model.var("balkans", levels=["neutral", "german_aligned"], init="neutral", monotone=True)
model.var("siberia", levels=["soviet", "japanese"], init="soviet", monotone=True)
model.var("channel_air", levels=["contested", "german", "british"], init="contested", monotone=True)
model.var("war_west_ger", levels=["peace", "war"], init="peace", monotone=True)

# -- additions of the model step (not ontology variables; see the module docstring) ---------
model.flag("north_strike", init=False, monotone=True)
model.flag("german_defeat", init=False, monotone=True)

# -- latch (ontology section 5) -------------------------------------------------------------
model.latch("belief_at_munich", of="belief_WEST", when=V.sudeten == "german")

# -- actors ---------------------------------------------------------------------------------
GER = model.actor("GER", observes=V.all(), remember_last=True)
WEST = model.actor("WEST", observes=V.all(), remember_last=True)
USSR = model.actor("USSR", observes=V.all())
JPN = model.actor("JPN", observes=V.all())
NATURE = model.nature()

# -- Germany --------------------------------------------------------------------------------
GER.action(
    "rearm",
    guard=V.arms_GER < "total",
    effect=Bump("arms_GER", 1),
    delay=8,
    source=(
        "Hitler's memorandum on the Four-Year Plan, Aug 1936 (armed forces operational within "
        "four years) and the army armament programme of Aug 1936; Goering's conference of "
        "14 Oct 1938 announcing an enlarged programme (Nuremberg document 1301-PS) and the "
        "Z-Plan of Jan 1939."
    ),
)
GER.action(
    "remilitarize_rhineland",
    guard=(V.rhineland == "demilitarized") & (V.arms_GER >= "rising"),
    effect=Set("rhineland", "remilitarized"),
    source=(
        "Blomberg's directive of 2 Mar 1936 for the entry into the zone (operation "
        "Winterübung); German memorandum to the Locarno powers and Reichstag speech of "
        "7 Mar 1936 (DGFP Series C vol. V)."
    ),
)
GER.action(
    "withdraw_rhineland",
    guard=(V.rhineland == "remilitarized") & (V.last_WEST == "resist_rhineland"),
    effect=[Set("rhineland", "demilitarized"), Set("treaty", "enforced")],
    source=(
        "Debated in Berlin 7 to 9 Mar 1936: Blomberg's proposal to pull back the forward "
        "garrisons if France moved, refused by Hitler (Kershaw, Hubris, 1998; Weinberg 1970; "
        "Emmerson, The Rhineland Crisis, 1977); the contingency is attested after the war "
        "(Jodl's testimony before the IMT, June 1946; Schmidt, Statist auf diplomatischer "
        "Bühne, 1949)."
    ),
)
GER.action(
    "court_italy",
    guard=~V.axis & V.italy_estranged,
    effect=Set("axis", True),
    source=(
        "October Protocols signed by Ciano and Neurath, 23 Oct 1936, and Mussolini's Milan "
        "speech of 1 Nov 1936; the Pact of Steel, 22 May 1939 (DGFP Series C vol. V; Series D "
        "vol. VI)."
    ),
)
GER.action(
    "annex_austria",
    guard={
        "target": V.austria == "independent",
        "italian_acquiescence": V.axis,
        "army": V.arms_GER >= "rising",
    },
    effect=[Set("austria", "annexed"), Inc("ind_GER")],
    source=(
        "Hitler and Schuschnigg at Berchtesgaden, 12 Feb 1938; Case Otto directive, 11 Mar "
        "1938 (Nuremberg document C-102); reunification law, 13 Mar 1938 (DGFP Series D "
        "vol. I)."
    ),
)
GER.action(
    "demand_sudeten",
    guard=(V.sudeten == "czech") & (V.rhineland == "remilitarized") & (V.arms_GER >= "rising"),
    effect=raise_to("belief_WEST", "uncertain"),
    source=(
        "Hitler's instructions to Henlein, 28 Mar 1938; Case Green directive, 30 May 1938 "
        "(388-PS); Nuremberg speech of 12 Sep, Berchtesgaden 15 Sep and the Godesberg "
        "memorandum of 23 Sep 1938 (DGFP Series D vol. II)."
    ),
)
_HEGEMONIC = V.aims_GER == "hegemonic"
GER.action(
    "attack_czechoslovakia",
    guard=(V.sudeten == "czech")
    & (V.last_GER == "demand_sudeten")
    & (V.war_west_ger == "peace")
    & (V.arms_GER >= "rising"),
    effect=[
        Set("sudeten", "german"),
        # [H] hypothesis-conditional part of the effect: Case Green aimed at the
        # destruction of Czechoslovakia, which the revisionist hypothesis excludes.
        SetIf(_HEGEMONIC, "bohemia", "german"),
        SetIf(_HEGEMONIC, "ind_GER", V.ind_GER + 1),
        SetIf(_HEGEMONIC, "belief_WEST", "hegemonic"),
    ],
    source=(
        "Case Green directive of 30 May 1938 (388-PS) with readiness by 1 Oct 1938; the "
        "Sportpalast speech of 26 Sep 1938 and the deadline of 28 Sep."
    ),
)
GER.action(
    "occupy_bohemia",
    guard={
        "hypothesis": _HEGEMONIC,
        "target": (V.sudeten == "german") & (V.bohemia == "czech"),
    },
    effect=[Set("bohemia", "german"), Inc("ind_GER"), Set("belief_WEST", "hegemonic")],
    source=(
        "Directive of 21 Oct 1938 on the liquidation of the remainder of Czechoslovakia "
        "(Nuremberg document C-136) and its supplement of 17 Dec 1938; Hacha in Berlin and "
        "the entry into Prague, 14 to 15 Mar 1939 (DGFP Series D vol. IV)."
    ),
)
GER.action(
    "propose_pact_ussr",
    guard=~V.nazi_soviet_pact & ~V.anglo_soviet_alliance,
    source=(
        "Weizsäcker's instruction to Schulenburg of 30 May 1939 to open political talks "
        "(DGFP Series D vol. VI); Schnurre and Astakhov, 26 Jul 1939; Hitler's telegram to "
        "Stalin, 20 Aug 1939 (DGFP Series D vol. VII). Earlier alternative, turned down by "
        "Hitler: the Kandelaki approaches of 1935 to 1937."
    ),
)
GER.action(
    "attack_poland",
    guard={
        "hypothesis": _HEGEMONIC,
        "target": V.poland == "independent",
        "army_ready": V.arms_GER >= "high",
    },
    effect=Set("poland", "german"),
    source=(
        "Case White directive of 3 Apr 1939 (Nuremberg document C-120); conference of "
        "23 May 1939 (L-79); Directive No. 1 for the Conduct of the War, 31 Aug 1939 "
        "(Trevor-Roper (ed.), Hitler's War Directives 1939-1945)."
    ),
)
GER.action(
    "attack_france",
    guard={
        "at_war": (V.war_west_ger == "war") & (V.france == "at_war"),
        "polish_front_closed": V.poland != "independent",
        "army_ready": V.arms_GER >= "high",
    },
    source=(
        "Directive No. 1, 31 Aug 1939 (defensive posture in the West while Poland is "
        "fought); Directive No. 6, 9 Oct 1939; OKH deployment directive for Case Yellow, "
        "24 Feb 1940; offensive launched 10 May 1940."
    ),
)
GER.action(
    "air_offensive",
    guard=(V.france == "fallen") & (V.britain == "at_war") & (V.channel_air == "contested"),
    source=(
        "Directive No. 16 on preparations for a landing in England, 16 Jul 1940 (air "
        "superiority a precondition); Directive No. 17 for the air and sea war against "
        "England, 1 Aug 1940; main offensive from 13 Aug 1940."
    ),
)
GER.action(
    "invade_britain",
    guard={
        "air_superiority": V.channel_air == "german",
        "france_fallen": V.france == "fallen",
        "britain_at_war": V.britain == "at_war",
    },
    effect=Bump("britain", 2),
    source=(
        "Directive No. 16, 16 Jul 1940 (Sea Lion); the Naval Staff's assessments of Jul 1940 "
        "on the crossing."
    ),
)
GER.action(
    "offer_terms_britain",
    guard=(V.war_west_ger == "war") & (V.britain == "at_war"),
    source=(
        "Reichstag speeches of 6 Oct 1939 and 19 Jul 1940 (the 'appeal to reason'); answered "
        "by Chamberlain in the Commons, 12 Oct 1939, and by Halifax's broadcast, 22 Jul 1940."
    ),
)
GER.action(
    "align_balkans",
    guard=(V.balkans == "neutral") & (V.france == "fallen"),
    effect=[Set("balkans", "german_aligned"), Set("oil_GER", "secured")],
    source=(
        "Romania's renunciation of the Anglo-French guarantee, 1 Jul 1940; the Second Vienna "
        "Award and the German guarantee of Romania, 30 Aug 1940; the German military mission "
        "to Romania, Oct 1940; Hungary (20 Nov) and Romania (23 Nov 1940) adhere to the "
        "Tripartite Pact (DGFP Series D vol. XI)."
    ),
)

# -- the West -------------------------------------------------------------------------------
WEST.action(
    "rearm",
    guard=V.arms_WEST < "high",
    effect=Bump("arms_WEST", 1),
    delay=4,
    source=(
        "Cabinet approval of the Defence Requirements Committee programme, Feb 1936, and the "
        "Statement Relating to Defence, 3 Mar 1936 (Cmd. 5107); the French four-year "
        "programme of 7 Sep 1936; the British post-Munich decisions of Oct to Nov 1938 "
        "(CAB 23) and the French decree-laws of Nov 1938."
    ),
)
WEST.action(
    "resist_rhineland",
    guard=(V.rhineland == "remilitarized") & (V.last_GER == "remilitarize_rhineland"),
    effect=raise_to("commit_WEST", "wary"),
    source=(
        "French Council of Ministers, 7 and 8 Mar 1936, and Sarraut's broadcast of 8 Mar "
        "('we are not disposed to leave Strasbourg under the fire of German guns'); Gamelin's "
        "advice that any action in the zone required mobilization; Flandin's case to the "
        "Locarno powers in Paris and London, 10 to 19 Mar 1936 (DDF 2e série vol. I); the "
        "British Cabinet's discussions of Mar 1936 (CAB 23)."
    ),
)
WEST.action(
    "concede",
    guard=(V.sudeten == "czech") & (V.last_GER == "demand_sudeten") & (V.war_west_ger == "peace"),
    effect=[Set("sudeten", "german"), raise_to("commit_WEST", "wary")],
    source=(
        "Anglo-French proposals to Prague, 18 to 19 Sep 1938; Munich agreement, 29 to 30 Sep "
        "1938; Cabinet, 17 to 30 Sep 1938 (CAB 23); HC Deb 3 to 6 Oct 1938."
    ),
)
WEST.action(
    "declare_war",
    guard=(V.war_west_ger == "peace")
    & (
        V.polish_guarantee
        | (V.last_GER == "demand_sudeten")
        | (V.last_GER == "attack_czechoslovakia")
        | ((V.last_WEST == "resist_rhineland") & (V.rhineland == "remilitarized"))
    ),
    effect=[
        Set("war_west_ger", "war"),
        Set("france", "at_war"),
        Set("britain", "at_war"),
        Set("commit_WEST", "at_war"),
    ],
    source=(
        "Cabinet and French government, 24 to 28 Sep 1938 (French partial mobilization from "
        "24 Sep; fleet mobilization 27 to 28 Sep); Cabinet of 2 Sep 1939 and the declarations "
        "of 3 Sep 1939 (CAB 23); French Council of Ministers, 7 to 8 Mar 1936, for the "
        "Rhineland branch."
    ),
)
WEST.action(
    "guarantee_poland",
    guard={
        "target": V.poland == "independent",
        "once": ~V.polish_guarantee,
        "belief": V.belief_WEST == "hegemonic",
        "commitment": V.commit_WEST >= "wary",
    },
    effect=[Set("polish_guarantee", True), raise_to("commit_WEST", "resolved")],
    source=(
        "Cabinet conclusions of 18 to 30 Mar 1939 (CAB 23), with the Foreign Policy Committee "
        "(CAB 27); the Prime Minister's statement in the Commons, 31 Mar 1939 (HC Deb 31 Mar "
        "1939); Chamberlain at Birmingham, 17 Mar 1939; against the Foreign Policy "
        "Committee's rejection of a guarantee to Czechoslovakia, 18 to 22 Mar 1938, and the "
        "Prime Minister's statement of 24 Mar 1938."
    ),
)
WEST.action(
    "approach_ussr",
    guard=~V.nazi_soviet_pact & ~V.anglo_soviet_alliance,
    source=(
        "Litvinov's proposal of 17 Mar 1938 and the Foreign Policy Committee's rejection "
        "(CAB 27); the British proposal of a four-power declaration, 20 Mar 1939; Anglo-French "
        "proposals to Moscow from 14 to 15 Apr 1939; the Cabinet decision of 24 May 1939 to "
        "negotiate an alliance; the military missions in Moscow, 11 to 21 Aug 1939 (DBFP "
        "Third Series vols. V to VII)."
    ),
)
_NEGOTIATE_GUARD = (
    (V.war_west_ger == "war")
    & (V.britain == "at_war")
    & (
        (V.france == "fallen")
        | (V.last_GER == "attack_france")
        | (V.last_GER == "offer_terms_britain")
    )
)
_MAY_1940 = (
    "War Cabinet, 26 to 28 May 1940, on an approach to Mussolini (CAB 65 conclusions and "
    "confidential annexes; Lukacs 1999); the Cabinet's answer to the German offer of 6 Oct "
    "1939 (HC Deb 12 Oct 1939); Halifax's broadcast of 22 Jul 1940."
)
WEST.action("negotiate", guard=_NEGOTIATE_GUARD, effect=Bump("britain", 1), source=_MAY_1940)
WEST.action(
    "fight_on",
    guard=_NEGOTIATE_GUARD,
    source=_MAY_1940 + " Decision of 28 May 1940 to fight on.",
)
_RHINELAND_1936 = (
    "Gamelin's demand for general mobilization and the French General Staff's assessment of "
    "8 to 9 March 1936; Blomberg's proposal to withdraw; the German army's own judgment of "
    "its inability to resist a French offensive in 1936 to 1937 (decisions D3; the historian "
    "confirms the citations)."
)
WEST.action(
    "offensive_west",
    guard={
        "at_war": V.war_west_ger == "war",
        "german_army_unready": V.arms_GER <= "rising",
    },
    source=_RHINELAND_1936,
)

# -- the Soviet Union -----------------------------------------------------------------------
USSR.action(
    "rearm",
    guard=V.arms_USSR == "weak",
    effect=Set("arms_USSR", "strong"),
    delay=4,
    source=(
        "Central Committee conference on the lessons of the Finnish war, Apr 1940; Timoshenko "
        "People's Commissar of Defence, 7 May 1940, and the reforms that followed (Erickson "
        "1962)."
    ),
)
USSR.action(
    "accept_pact",
    guard=(V.last_GER == "propose_pact_ussr") & ~V.anglo_soviet_alliance & ~V.nazi_soviet_pact,
    effect=[Set("nazi_soviet_pact", True), Set("oil_GER", "secured")],
    source=(
        "Molotov to Schulenburg, 19 Aug 1939; Stalin's reply to Hitler, 21 Aug 1939; "
        "non-aggression pact and secret protocol, 23 Aug 1939; German-Soviet credit "
        "agreement, 19 Aug 1939 (Nazi-Soviet Relations 1939-1941; DGFP Series D vol. VII)."
    ),
)
USSR.action(
    "accept_alliance",
    guard=(V.last_WEST == "approach_ussr") & ~V.nazi_soviet_pact & ~V.anglo_soviet_alliance,
    effect=Set("anglo_soviet_alliance", True),
    source=(
        "Soviet proposal of a triple alliance, 17 Apr 1939; the draft-treaty negotiations of "
        "Jun to Jul 1939 (the 'indirect aggression' dispute); Voroshilov's question of 14 Aug "
        "1939 on passage through Poland and Romania (DBFP Third Series vol. VII)."
    ),
)
USSR.action(
    "occupy_east_poland",
    guard=V.nazi_soviet_pact & (V.poland == "german"),
    effect=Set("poland", "partitioned"),
    source=(
        "Soviet entry into Poland, 17 Sep 1939, two days after the Nomonhan ceasefire of "
        "15 Sep; boundary and friendship treaty, 28 Sep 1939."
    ),
)
USSR.action(
    "join_axis",
    guard={
        "hypothesis": V.aims_USSR == "opportunist",
        "pact": V.nazi_soviet_pact,
        "france_fallen": V.france == "fallen",
        "once": ~V.ussr_axis,
    },
    effect=Set("ussr_axis", True),
    source=(
        "Ribbentrop's letter to Stalin, 13 Oct 1940; Molotov in Berlin, 12 to 13 Nov 1940; "
        "the Soviet conditions of 25 Nov 1940 for joining the proposed four-power pact "
        "(Nazi-Soviet Relations 1939-1941; DGFP Series D vol. XI). Exists for the negative "
        "control T10."
    ),
)

# -- Japan ----------------------------------------------------------------------------------
JPN.action(
    "sign_anticomintern",
    guard=~V.anticomintern,
    effect=Set("anticomintern", True),
    source=(
        "Anti-Comintern Pact and secret protocol, 25 Nov 1936, after the Ribbentrop and "
        "Oshima talks of 1935 to 1936 (DGFP Series C vol. V)."
    ),
)
JPN.action(
    "strike_north",
    guard={
        "pact": V.anticomintern,
        "army_free": ~V.china_war,
        "ussr_weak": V.arms_USSR == "weak",
    },
    effect=Set("north_strike", True),
    source=(
        "No national decision for a northern war was debated in the v0 window: the "
        "Changkufeng (Jul to Aug 1938) and Nomonhan (May to Sep 1939) fighting were Kwantung "
        "Army escalations that Tokyo sought to contain; the strike-north debate proper is the "
        "Liaison and Imperial Conferences of Jun to Jul 1941 (Ike 1967), outside v0."
    ),
    speculative=True,
)

# -- Nature ---------------------------------------------------------------------------------
NATURE.event(
    "purge",
    guard=V.arms_USSR == "strong",
    effect=Set("arms_USSR", "weak"),
    source="Tukhachevsky trial and executions, 11 to 12 Jun 1937; the arrests of 1937 to 1938.",
)
NATURE.event(
    "china_incident",
    guard=~V.china_war,
    effect=Set("china_war", True),
    source=(
        "The Marco Polo Bridge incident, 7 Jul 1937, the Japanese cabinet decision of 11 Jul "
        "and Shanghai from 13 Aug 1937: the decision for a general war in China (decisions D7)."
    ),
)
NATURE.event(
    "locarno_lapses",
    guard=(V.rhineland == "remilitarized")
    & (V.treaty != "dead")
    & (V.last_GER != "remilitarize_rhineland")
    & (V.last_WEST != "resist_rhineland"),
    effect=Set("treaty", "dead"),
    source=(
        "London proposals of the Locarno powers and the League Council's finding of a breach, "
        "both 19 Mar 1936: condemnation without enforcement."
    ),
)
NATURE.event(
    "campaign_west",
    guard={
        "offensive": V.last_GER == "attack_france",
        "france_in_field": V.france == "at_war",
        "army_ready": V.arms_GER >= "high",
    },
    effect=Set("france", "fallen"),
    source=(
        "German planning doubts of Oct to Nov 1939 (the first Case Yellow aimed at Belgium "
        "and the Channel coast, not the defeat of France); the Allied Dyle plan of Nov 1939 "
        "to Mar 1940; Beck's memoranda of May to Jul 1938 on a war begun with the 1938 force."
    ),
)
NATURE.event(
    "campaign_rhineland",
    guard={
        "offensive": V.last_WEST == "offensive_west",
        "german_army_unready": V.arms_GER <= "rising",
    },
    effect=Set("german_defeat", True),
    source=_RHINELAND_1936,
)
NATURE.event(
    "air_battle_german",
    guard=(V.last_GER == "air_offensive") & (V.channel_air == "contested"),
    effect=Set("channel_air", "german"),
    source="Directive No. 17, 1 Aug 1940; the Luftwaffe's estimates of Jul to Aug 1940.",
)
NATURE.event(
    "air_battle_british",
    guard=(V.last_GER == "air_offensive") & (V.channel_air == "contested"),
    effect=Set("channel_air", "british"),
    source="Sea Lion postponed 17 Sep 1940 and to spring 1941 on 12 Oct 1940.",
)
NATURE.event(
    "campaign_siberia",
    guard={
        "strike": V.north_strike,
        "ussr_weak": V.arms_USSR == "weak",
        "no_two_front": ~V.china_war,
        # Never satisfied in v0: the record never supports Japanese superiority over the
        # Far Eastern Red Army (decisions D7).
        "japanese_superiority": FALSE,
    },
    effect=Set("siberia", "japanese"),
    source=(
        "Nomonhan, Aug 1939: the Soviet counteroffensive defeated the Kwantung Army with the "
        "Red Army not engaged in Europe; the Imperial Conference of 2 Jul 1941 made a "
        "northern war conditional on the German-Soviet war going in Germany's favour (Ike "
        "1967). The Far Eastern Red Army outnumbered the Kwantung Army (decisions D7)."
    ),
)
NATURE.event(
    "us_neutrality_revision",
    guard=(V.war_west_ger == "war") & (V.commit_US == "isolationist"),
    effect=Set("commit_US", "wary"),
    source=(
        "Roosevelt's message to the special session of Congress, 21 Sep 1939; Neutrality Act "
        "of 4 Nov 1939."
    ),
)
NATURE.event(
    "us_engages",
    guard=(V.france == "fallen") & (V.commit_US == "wary"),
    effect=Set("commit_US", "engaged"),
    source=(
        "Destroyers-for-bases agreement, 2 Sep 1940 (FRUS 1940 vol. III); Selective Training "
        "and Service Act, 16 Sep 1940."
    ),
)
NATURE.event(
    "italy_reconciles",
    guard=V.italy_estranged & ~V.axis,
    effect=Set("italy_estranged", False),
    source="The Hoare-Laval proposals, Dec 1935; the lifting of League sanctions, Jul 1936.",
)

# -- constraints ----------------------------------------------------------------------------
# Prague (15 Mar 1939) to the guarantee (31 Mar 1939) and the doubling of the Territorial
# Army (29 Mar 1939): sixteen days.
model.fairness(
    "democratic_response",
    actor="WEST",
    # Trigger narrowed to commit_WEST == wary after the model step (guard changelog,
    # 2026-10-12): the guarantee's own institutional precondition is rearmament accepted as
    # policy, so the obligation to respond cannot bind a government still at `appease`.
    trigger=(V.belief_WEST == "hegemonic")
    & (V.commit_WEST == "wary")
    & (V.poland == "independent"),
    within=2,
    responses=["guarantee_poland", "rearm"],
)
# Decisions D4. Source: the Franco-Czechoslovak treaty (D4 cites 25 January 1925, the
# catalogue 16 Oct 1925; the historian confirms the date); the French statements of
# September 1938 and the British statement of 26 September 1938. An institutional
# constraint, not a behaviour.
model.fairness(
    "czech_obligation",
    actor="WEST",
    trigger=(V.last_GER == "attack_czechoslovakia")
    & (V.sudeten == "german")
    & (V.war_west_ger == "peace"),
    within=1,
    responses=["declare_war", "concede"],
)
# Decisions D3: the French offensive against the unready army of 1936 to 1937 resolves
# deterministically. Nature must play the campaign one tick after the offensive.
model.fairness(
    "rhineland_resolution",
    actor="Nature",
    trigger=(V.last_WEST == "offensive_west") & (V.arms_GER <= "rising"),
    within=1,
    responses=["campaign_rhineland"],
)
model.profile("fight_on", actor="WEST", forbid=["negotiate"])
# The appeaser never declares war unless convinced of hegemonic aims or bound by the Czech
# treaty after a German attack (guard changelog, 2026-10-12: keeps the profile well-formed
# with czech_obligation).
model.profile(
    "appeaser",
    actor="WEST",
    forbid=["declare_war"],
    unless=(V.belief_WEST == "hegemonic") | (V.last_GER == "attack_czechoslovakia"),
)
model.assume("ussr_defensive", V.aims_USSR == "defensive")

# -- balance, kernels, endings (ontology section 6; decisions D2) ---------------------------
GERMAN_REGIONS = (
    Ite(V.rhineland == "remilitarized", 1, 0)
    + Ite(V.austria == "annexed", 1, 0)
    + Ite(V.sudeten == "german", 1, 0)
    + Ite(V.bohemia == "german", 1, 0)
    + Ite(V.poland != "independent", 1, 0)
    + Ite(V.france == "fallen", 1, 0)
    + Ite(V.britain.is_in(["negotiated", "invaded"]), 1, 0)
    + Ite(V.balkans == "german_aligned", 1, 0)
)
model.invariant(
    "balance_europe",
    (GERMAN_REGIONS < 5) & (V.france != "fallen") & V.britain.is_in(["at_peace", "at_war"]),
)
model.invariant(
    "commitment_alive",
    (V.treaty != "dead") | V.polish_guarantee | V.anglo_soviet_alliance | (V.war_west_ger == "war"),
)

# Endings are mutually exclusive on every state: each excludes the ones declared before it
# (the order of ontology section 6).
_earlier = []


def _ending(name: str, expr) -> None:
    cond = expr
    for prev in _earlier:
        cond = cond & ~V.ending(prev)
    model.ending(name, cond)
    _earlier.append(name)


_AT_HORIZON = V.tick == HORIZON
_ending("GERMAN_DEFEAT", V.german_defeat)
_ending("NEGOTIATED_PEACE", V.britain == "negotiated")
_ending("AXIS_HEGEMONY_EUROPE", V.britain == "invaded")
_ending("JPN_CONQUERS_USSR", V.siberia == "japanese")
_ending("USSR_JOINS_AXIS", V.ussr_axis)
_ending("NO_GENERAL_WAR", _AT_HORIZON & (V.war_west_ger == "peace") & (V.poland == "independent"))
_ending("LIMITED_WAR", _AT_HORIZON & (V.war_west_ger == "peace") & (V.poland != "independent"))
_ending("STATIC_FRONT", _AT_HORIZON & (V.war_west_ger == "war") & (V.france == "at_war"))
_ending(
    "BRITAIN_ALONE",
    _AT_HORIZON & (V.war_west_ger == "war") & (V.france == "fallen") & (V.britain == "at_war"),
)
_ending("WAR_UNRESOLVED", _AT_HORIZON & (V.war_west_ger == "war"))
