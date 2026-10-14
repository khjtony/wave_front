"""WW2 v1: both theatres, 1936Q1 to 1945Q3, four principals and Nature.

The model of docs/ontology_ww2_v1.md and docs/actions_ww2_v1.md (written as deltas on v0,
docs/ontology_ww2.md and docs/actions_ww2.md) as settled by the architect's decisions E1 to
E8 (docs/ww2_v1_decisions.md). Everything v0 declares and the v1 catalogue does not change
is carried over verbatim from ``models/ww2/v0.py`` (tests/ww2/test_model_ww2_v1.py compares
every shared action and event with v0). The registered claims T1 to T13
(docs/ww2_testbed.md section 5) were committed before any guard was written; T6, T7, T11
and T12 are hold-out tests (kickoff D2), and every guard, effect, delay, fairness
constraint, profile or assumption edited after the first run of the v1 suite is logged in
docs/guard_changelog_ww2.md with a source.

Time: one tick is one quarter; tick 0 is the start of 1936Q1, tick 38 the start of 1945Q3,
tick 39 (the horizon) the start of 1945Q4. The joint move at tick t is what each actor
decided during quarter t; its effects are visible at t + 1. Same-quarter reactions appear
one tick later ([SQR]); Nature plays one event per tick, so two Nature outcomes dated in one
quarter cannot both sit in it ([NSL]); both are marked in data/ww2/realized_moves_v1.csv.

Actors: ``GER``, ``WEST`` (the United Kingdom and France, and from v1 the United States'
executive decisions; decisions E2 item 1), ``USSR`` (with ``remember_last``; E2 item 2),
``JPN`` and Nature (Italy, Poland, the smaller states, campaign resolution, the United
States' domestic decisions of v0, the oil clock, the bomb's use).

Hidden objectives (swept, ``init=None``): ``aims_GER`` and ``aims_USSR`` as in v0, and
``aims_JPN`` (status_quo | regional | hegemonic, hidden from GER, WEST and USSR). A guard
part named ``hypothesis`` is a hypothesis gate. Guards that join independent documented
constraints are declared as named parts with the catalogue's part names.

Coding choices of the model step (each in the report, reports/ww2_v1.md section 1):

* The v0 guard of WEST ``negotiate`` and ``fight_on`` becomes the part ``occasion`` (the
  catalogue names only the added part ``no_separate_peace``), and v0's guard of Nature
  ``purge`` becomes the part ``officer_corps`` beside the adopted ``prewar`` (E2 item 10).
* ``lift_embargo`` has the part ``before_clock: fair_oil_clock < 8`` (E3), so that it never
  meets Nature's forced ``stocks_run_down`` in one joint move.
* Raises of ``commit_US`` to ``total`` are clamped ``Bump("commit_US", 3)`` (E2 item 4).
* ``SEASON`` (second and third quarters) is a disjunction of ``V.tick == t`` (the DSL has
  no modulo).
* The profile ``deterred`` exists for T9 only (E5); the invariants ``undefeated``,
  ``poland_blocked``, ``european_peace`` and ``european_peace_t20`` are the analysis
  predicates of E5 (T6, T9, T13).
"""

from wavefront.model import FALSE, Bump, Inc, Ite, Model, Set, SetIf, V

HORIZON = 39

model = Model(
    "ww2_v1",
    horizon=HORIZON,
    description=(
        "Both theatres, 1936Q1 to 1945Q3 (one tick per quarter): Germany, the West (Britain, "
        "France and the United States' executive), the USSR, Japan and Nature, after "
        "docs/ontology_ww2_v1.md and docs/actions_ww2_v1.md (deltas on v0) with the "
        "architect's decisions E1 to E8. A development model of the historical testbed; every "
        "result is conditional on it and on the initial state."
    ),
)


def raise_to(var: str, level: str) -> SetIf:
    """``var := max(var, level)``: raise ``var`` to ``level`` if it is lower."""
    return SetIf(V[var] < level, var, level)


def _any(terms):
    expr = terms[0]
    for t in terms[1:]:
        expr = expr | t
    return expr


# Actions convention 1: the second and third quarters (April to September).
SEASON_TICKS = tuple(t for t in range(HORIZON) if t % 4 in (1, 2))
SEASON = _any([V.tick == t for t in SEASON_TICKS])

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
model.var(
    "aims_JPN",
    levels=["status_quo", "regional", "hegemonic"],
    init=None,
    hidden_from=["GER", "WEST", "USSR"],
)

# -- capability and resources (ontology section 2; v1 section 2.1) --------------------------
model.var("arms_GER", levels=["low", "rising", "high", "total"], init="rising", monotone=True)
model.var("arms_WEST", levels=["low", "rising", "high"], init="low", monotone=True)
model.var("arms_USSR", levels=["weak", "strong"], init="strong")
model.var("arms_JPN", levels=["high", "total"], init="high")  # constant, as in v0
model.counter("ind_GER", max=5, init=3, monotone=True)  # ordinal 3..5 of the ontology
model.var("oil_GER", levels=["dependent", "secured"], init="dependent", monotone=True)
model.var("arms_USA", levels=["low", "rising", "high"], init="low", monotone=True)
model.var("mob_USSR", levels=["peace", "total"], init="peace", monotone=True)
model.var(
    "exhaustion_GER",
    levels=["sustainable", "strained", "exhausted"],
    init="sustainable",
    monotone=True,
)
model.var("oil_JPN", levels=["secure", "dependent", "embargoed", "critical"], init="dependent")
model.var("jpn_navy", levels=["strong", "attrited"], init="strong", monotone=True)
model.flag("bomb_ready", init=False, monotone=True)
model.flag("strategic_bombing", init=False, monotone=True)
model.var("air_west", levels=["contested", "allied"], init="contested", monotone=True)

# -- beliefs and commitment (ontology section 3; v1 section 3) ------------------------------
model.var(
    "belief_WEST", levels=["limited", "uncertain", "hegemonic"], init="limited", monotone=True
)
model.var(
    "belief_GER",
    levels=["will_not_fight", "uncertain", "will_fight"],
    init="will_not_fight",
    monotone=True,
)  # no longer constant in v1 (two raises; E2 item 3)
model.var(
    "commit_WEST", levels=["appease", "wary", "resolved", "at_war"], init="appease", monotone=True
)
model.var(
    "commit_US",
    levels=["isolationist", "wary", "engaged", "total"],
    init="isolationist",
    monotone=True,
)

# -- structure (ontology section 4; v1 section 4) -------------------------------------------
model.var("treaty", levels=["enforced", "eroded", "dead"], init="eroded")
model.flag("axis", init=False, monotone=True)
model.flag("anticomintern", init=False, monotone=True)
model.flag("nazi_soviet_pact", init=False, monotone=True)
model.flag("polish_guarantee", init=False, monotone=True)
model.flag("anglo_soviet_alliance", init=False, monotone=True)
model.flag("ussr_axis", init=False, monotone=True)
model.flag("italy_estranged", init=True)
model.flag("china_war", init=False, monotone=True)
model.flag("east_war", init=False, monotone=True)
model.var("war_us_ger", levels=["peace", "war"], init="peace", monotone=True)
model.var(
    "pacific_war", levels=["peace", "colonial", "war", "surrendered"], init="peace", monotone=True
)
model.var("reich", levels=["fighting", "surrendered"], init="fighting", monotone=True)
model.flag("east_feeler", init=False, monotone=True)
model.flag("east_peace", init=False, monotone=True)
model.flag("midway_ordered", init=False, monotone=True)

# -- regions (ontology section 5; v1 section 5) ---------------------------------------------
model.var("rhineland", levels=["demilitarized", "remilitarized"], init="demilitarized")
model.var("austria", levels=["independent", "annexed"], init="independent", monotone=True)
model.var("sudeten", levels=["czech", "german"], init="czech", monotone=True)
model.var("bohemia", levels=["czech", "german"], init="czech", monotone=True)
model.var(
    "poland", levels=["independent", "german", "partitioned"], init="independent", monotone=True
)
model.var(
    "france",
    levels=["independent", "at_war", "fallen", "liberated"],
    init="independent",
    monotone=True,
)
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
model.var("w_ussr", levels=["soviet", "contested", "german"], init="soviet")
model.var("caucasus", levels=["soviet", "contested", "german"], init="soviet")
model.var(
    "italy",
    levels=["nonbelligerent", "at_war", "surrendered"],
    init="nonbelligerent",
    monotone=True,
)
model.var("indochina", levels=["french", "north_occupied", "occupied"], init="french")
model.var("dei", levels=["dutch", "japanese"], init="dutch", monotone=True)

# -- additions of the v0 model step (not ontology variables) --------------------------------
model.flag("north_strike", init=False, monotone=True)
model.flag("german_defeat", init=False, monotone=True)

# -- latch (ontology section 5) -------------------------------------------------------------
model.latch("belief_at_munich", of="belief_WEST", when=V.sudeten == "german")

# -- actors ---------------------------------------------------------------------------------
GER = model.actor("GER", observes=V.all(), remember_last=True)
WEST = model.actor("WEST", observes=V.all(), remember_last=True)
USSR = model.actor("USSR", observes=V.all(), remember_last=True)  # E2 item 2
JPN = model.actor("JPN", observes=V.all())
NATURE = model.nature()

# -- Germany (v0, unchanged) ----------------------------------------------------------------
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

# -- Germany, new in v1 (actions_ww2_v1.md) -------------------------------------------------
_ARMY_READY = V.arms_GER >= "high"
_RESERVES = V.exhaustion_GER != "exhausted"
GER.action(
    "attack_ussr",
    guard={
        "hypothesis": _HEGEMONIC,
        "peace": ~V.east_war,
        "west_closed": V.france == "fallen",
        "army_ready": _ARMY_READY,
        "season": SEASON,
    },
    effect=[
        Set("east_war", True),
        Set("w_ussr", "contested"),
        Set("anglo_soviet_alliance", True),
    ],
    source=(
        "Hitler's conference at the Berghof, 31 Jul 1940 (Halder's war diary: the decision to "
        "attack the USSR in spring 1941); Directive No. 21 (Barbarossa), 18 Dec 1940; the "
        "conference of 30 Apr 1941 fixing 22 Jun; the attack of 22 Jun 1941 (Trevor-Roper "
        "(ed.), Hitler's War Directives)."
    ),
)
GER.action(
    "offensive_east",
    guard={
        "at_war": V.east_war,
        "front": V.w_ussr == "contested",
        "army_ready": _ARMY_READY,
        "season": SEASON,
        "reserves": _RESERVES,
    },
    source=(
        "Directives No. 33 (19 Jul 1941) and No. 34 (30 Jul 1941); Hitler's instruction of "
        "21 Aug 1941 giving Kiev priority over Moscow, against Halder's and Brauchitsch's "
        "proposal of 18 Aug; Directive No. 35, 6 Sep 1941 (Typhoon); Operations Order No. 6, "
        "15 Apr 1943 (Citadel); Hitler's conference with Kluge and Manstein, 13 Jul 1943, "
        "calling Citadel off after the Sicily landing."
    ),
)
GER.action(
    "offensive_caucasus",
    guard={
        "at_war": V.east_war,
        "target": V.caucasus != "german",
        "flank": V.w_ussr != "soviet",
        "army_ready": _ARMY_READY,
        "season": SEASON,
        "reserves": _RESERVES,
    },
    effect=SetIf(V.caucasus == "soviet", "caucasus", "contested"),
    source=(
        "Directive No. 41, 5 Apr 1942 (Blue: the oil regions of the Caucasus as the "
        "objective); Directive No. 45, 23 Jul 1942 (simultaneous advance on Stalingrad and "
        "the Caucasus); Hitler's statement to the army group commanders at Poltava, 1 Jun "
        "1942, that without Maikop and Grozny he would have to end the war (as reported by "
        "Paulus, postwar; check)."
    ),
)
GER.action(
    "declare_war_us",
    guard={
        "not_yet": V.war_us_ger == "peace",
        "japanese_war": V.pacific_war == "war",
    },
    effect=[Set("war_us_ger", "war"), Bump("commit_US", 3)],
    source=(
        "Ribbentrop's assurance to Oshima of late Nov 1941 that Germany would join a Japanese "
        "war against the United States; the draft agreement of early Dec 1941 against a "
        "separate peace; Hitler's Reichstag speech and the declaration of war, 11 Dec 1941 "
        "(DGFP Series D vol. XIII; Kershaw 2007, the chapter on Hitler's decision to declare "
        "war on the United States)."
    ),
)
GER.action(
    "negotiate_east",
    guard={"at_war": V.east_war, "feeler": V.east_feeler},
    effect=Set("east_peace", True),
    source=(
        "Goebbels's diary, Sep 1943, on proposing a separate peace with the USSR to Hitler "
        "and Hitler's answer that the moment was not right; Ribbentrop's proposals of 1942 to "
        "1943 for a settlement with Moscow (Ribbentrop, Zwischen London und Moskau, 1953, "
        "postwar)."
    ),
)

# -- the West (v0; guarantee_poland, declare_war, negotiate and fight_on changed in v1) ------
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
        # v1: observed resolve (3 Sep 1939); ontology_ww2_v1.md section 3.
        Set("belief_GER", "will_fight"),
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
    effect=[
        Set("polish_guarantee", True),
        raise_to("commit_WEST", "resolved"),
        # v1: the conference of 23 May 1939 (L-79); ontology_ww2_v1.md section 3.
        raise_to("belief_GER", "uncertain"),
    ],
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
# v1: the Anglo-Soviet Agreement of 12 Jul 1941 (no separate armistice or peace), renewed
# 26 May 1942 and in the Declaration by United Nations of 1 Jan 1942 (actions_ww2_v1.md,
# changed v0 actions). The v0 guard is kept whole as the part ``occasion``.
_NEGOTIATE_PARTS = {
    "occasion": _NEGOTIATE_GUARD,
    "no_separate_peace": ~(V.anglo_soviet_alliance & V.east_war),
}
WEST.action("negotiate", guard=_NEGOTIATE_PARTS, effect=Bump("britain", 1), source=_MAY_1940)
WEST.action(
    "fight_on",
    guard=_NEGOTIATE_PARTS,
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

# -- the West, new in v1: the United States' decisions and the 1943 to 1944 landings ---------
WEST.action(
    "us_rearm",
    guard=V.arms_USA == "low",
    effect=Set("arms_USA", "rising"),
    delay=4,
    source=(
        "Roosevelt's message to Congress of 16 May 1940 (50,000 aircraft a year); the defence "
        "appropriations of Jun 1940; the Two-Ocean Navy Act, 19 Jul 1940; the Selective "
        "Training and Service Act, 16 Sep 1940. Earlier, partial steps: the Naval Act of "
        "17 May 1938 and the White House meeting of 14 Nov 1938 on aircraft."
    ),
)
WEST.action(
    "lend_lease",
    guard={
        "us_policy": V.commit_US.is_in(["wary", "engaged"]),
        "belligerent": V.britain == "at_war",
    },
    effect=raise_to("commit_US", "engaged"),
    source=(
        "Roosevelt's press conference of 17 Dec 1940 and fireside chat of 29 Dec 1940; H.R. "
        "1776 introduced 10 Jan 1941; the Lend-Lease Act, 11 Mar 1941; extended to the USSR "
        "7 Nov 1941 after the Moscow Protocol of 1 Oct 1941."
    ),
)
WEST.action(
    "embargo_jpn",
    guard={
        "instrument": V.tick >= 18,
        "trade_link": V.oil_JPN == "dependent",
        "peace": V.pacific_war == "peace",
    },
    effect=Set("oil_JPN", "embargoed"),
    source=(
        "Notice of termination of the Japanese-American commercial treaty of 1911, 26 Jul 1939 "
        "(lapsed 26 Jan 1940); the Export Control Act, 2 Jul 1940; the licensing of aviation "
        "fuel (Jul 1940) and the scrap-iron embargo (announced 26 Sep 1940) as partial steps; "
        "Executive Order 8832 freezing Japanese assets, 26 Jul 1941, and the refusal of oil "
        "export licences from 1 Aug 1941; the Cabinet and departmental debate of Jul 1941 "
        "between a partial and a total stop (FRUS 1941 vol. IV; Utley, Going to War with "
        "Japan 1937-1941, 1985)."
    ),
)
WEST.action(
    "lift_embargo",
    guard={
        "in_force": V.oil_JPN.is_in(["embargoed", "critical"]),
        "peace": V.pacific_war == "peace",
        # Decisions E3: well-formedness edit before any test; the quarter in which the stocks
        # run out is Nature's (stocks_run_down is forced at fair_oil_clock == 8).
        "before_clock": V.fair_oil_clock < 8,
    },
    effect=Set("oil_JPN", "dependent"),
    source=(
        "Japan's Proposal B, delivered 20 Nov 1941 (withdrawal from southern Indochina against "
        "a resumption of oil supply); Hull's draft modus vivendi of 22 to 25 Nov 1941 and its "
        "abandonment; the Hull note of 26 Nov 1941 (FRUS Japan 1931-1941 vol. II; FRUS 1941 "
        "vol. IV)."
    ),
)
WEST.action(
    "victory_program",
    guard={
        "programme": V.arms_USA == "rising",
        "belligerent": V.commit_US == "total",
    },
    effect=Set("arms_USA", "high"),
    delay=5,
    source=(
        "Joint Board estimate of United States over-all production requirements, 11 Sep 1941 "
        "(the Victory Program; 1 Jul 1943 as the earliest date for major offensive "
        "operations); the production goals of the State of the Union message, 6 Jan 1942; the "
        "War Production Board, 16 Jan 1942 (Matloff and Snell 1953; Kirkpatrick 1990)."
    ),
)
WEST.action(
    "atomic_program",
    guard={
        "knowledge": V.tick >= 22,
        "emergency": V.commit_US >= "engaged",
        "once": ~V.bomb_ready,
    },
    effect=Set("bomb_ready", True),
    delay=12,
    source=(
        "The MAUD Committee report, Jul 1941, transmitted officially in Oct 1941; Roosevelt's "
        "meeting with Bush and Wallace, 9 Oct 1941 (go-ahead to expand the work); the "
        "Bush-Conant report of 13 Jun 1942, approved by Roosevelt on 17 Jun 1942 (the decision "
        "to build production plants); the Manhattan District, 13 Aug 1942; Groves in command, "
        "17 Sep 1942 (Hewlett and Anderson 1962; Rhodes 1986)."
    ),
)
_US_AT_WAR = V.war_us_ger == "war"
WEST.action(
    "bomber_offensive",
    guard={
        "us_at_war": _US_AT_WAR,
        "us_arms": V.arms_USA >= "rising",
        "once": ~V.strategic_bombing,
    },
    effect=Set("strategic_bombing", True),
    source=(
        "The Casablanca directive of the Combined Chiefs, 21 Jan 1943; the Pointblank "
        "directive, 10 Jun 1943 (Webster and Frankland 1961); the RAF area-bombing directive "
        "of 14 Feb 1942 as the British precursor."
    ),
)
WEST.action(
    "invade_italy",
    guard={
        "target": V.italy == "at_war",
        "us_at_war": _US_AT_WAR,
        "us_arms": V.arms_USA >= "rising",
    },
    source=(
        "Casablanca conference, 14 to 24 Jan 1943 (Husky, the invasion of Sicily); the Trident "
        "conference, 12 to 25 May 1943 (the directive to eliminate Italy from the war); "
        "Sicily 10 Jul 1943; Salerno 9 Sep 1943."
    ),
)
WEST.action(
    "land_france",
    guard={
        "at_war": V.war_west_ger == "war",
        "us_at_war": _US_AT_WAR,
        "us_arms": V.arms_USA == "high",
        "air_superiority": V.air_west == "allied",
        "season": SEASON,
        "france_occupied": V.france == "fallen",
    },
    source=(
        "Marshall's memorandum and the London talks of 8 to 14 Apr 1942 (Bolero and Roundup); "
        "the rejection of Sledgehammer, 22 Jul 1942; the Trident decision of May 1943 fixing "
        "1 May 1944; the COSSAC outline plan, 15 Jul 1943, approved at Quebec (Quadrant), Aug "
        "1943; Tehran, 28 Nov to 1 Dec 1943; Eisenhower's decision of 5 Jun 1944 and the "
        "landing of 6 Jun 1944."
    ),
)
WEST.action(
    "us_declare_war",
    guard={
        "not_yet": V.war_us_ger == "peace",
        "engaged": V.commit_US >= "engaged",
    },
    effect=[Set("war_us_ger", "war"), Bump("commit_US", 3)],
    source=(
        "Stimson's and Knox's advice to the President in 1941 that he ask Congress for a "
        "declaration (Stimson's diary; Stimson and Bundy, On Active Service in Peace and War, "
        "1948); the House vote of 12 Aug 1941 extending the term of service, 203 to 202; "
        "Roosevelt's Boston speech of 30 Oct 1940."
    ),
)
WEST.action(
    "us_declare_war_jpn",
    guard={"colonial_war": V.pacific_war == "colonial"},
    effect=[Set("pacific_war", "war"), Bump("commit_US", 3)],
    source=(
        "Roosevelt's assurance to Halifax, 1 and 3 Dec 1941, of American support if Japan "
        "attacked British or Dutch territory, and his statement that he would have to go to "
        "Congress (Halifax's telegrams; Reynolds, The Creation of the Anglo-American Alliance "
        "1937-41, 1981); the ADB staff conversations at Singapore, Apr 1941."
    ),
)

# -- the Soviet Union (v0, unchanged) -------------------------------------------------------
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

# -- the Soviet Union, new in v1 ------------------------------------------------------------
USSR.action(
    "mobilize_total",
    guard={"at_war": V.east_war, "once": V.mob_USSR == "peace"},
    effect=Set("mob_USSR", "total"),
    delay=3,
    source=(
        "The Evacuation Council, 24 Jun 1941; the State Defence Committee (GKO), 30 Jun 1941; "
        "the mobilization plan for the third quarter of 1941 and the war-economic plan for the "
        "Volga, Urals and Western Siberia, 16 Aug 1941 (Harrison 1985; Harrison (ed.) 1998, "
        "the chapter on the USSR)."
    ),
)
USSR.action(
    "counteroffensive",
    guard={"at_war": V.east_war},
    source=(
        "Zhukov's plan for the Moscow counteroffensive, approved by Stalin 30 Nov 1941 "
        "(launched 5 Dec 1941); the Stavka directive of 10 Jan 1942 for a general offensive; "
        "the Kharkov offensive of 12 May 1942; the Stavka planning of Sep to Oct 1942 for "
        "Uranus (launched 19 Nov 1942); Little Saturn (Dec 1942); Star and Gallop (Jan to Feb "
        "1943); the Stavka decision of Apr 1943 to receive the German summer offensive on the "
        "defensive and counter-attack (Kutuzov, 12 Jul; Rumyantsev, 3 Aug 1943); the Dnieper "
        "and right-bank Ukraine offensives (Nov 1943 to Apr 1944); Bagration (plan approved "
        "end of May 1944, launched 22 Jun 1944); Vistula-Oder (12 Jan 1945); Berlin (16 Apr "
        "1945) (Erickson, The Road to Stalingrad, 1975, and The Road to Berlin, 1983; Glantz "
        "and House, When Titans Clashed, 1995)."
    ),
)
USSR.action(
    "seek_terms_east",
    guard={
        "at_war": V.east_war,
        "no_separate_peace": ~V.anglo_soviet_alliance,
        "once": ~V.east_feeler,
    },
    effect=Set("east_feeler", True),
    source=(
        "No dated Soviet decision record. The evidence is postwar testimony on an approach "
        "through the Bulgarian minister Stamenov in Jul 1941 (the Beria case, 1953; "
        "Sudoplatov's memoir, 1994) and the contested Stockholm contacts of 1942 to 1943 "
        "(Mastny, 'Stalin and the prospects of a separate peace in World War II', American "
        "Historical Review, 1972)."
    ),
    speculative=True,
)

# -- Japan (v0 sign_anticomintern unchanged; strike_north rewritten from the 1941 record) ----
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
        "hypothesis": V.aims_JPN == "hegemonic",
        "pact": V.anticomintern,
        "ussr_collapsing": V.w_ussr == "german",
    },
    effect=Set("north_strike", True),
    source=(
        "Liaison Conferences of 25 Jun to 1 Jul 1941 (Matsuoka's case for an immediate attack "
        "on the USSR); the Imperial Conference of 2 Jul 1941: 'if the German-Soviet war should "
        "develop to the advantage of our Empire, we will resort to arms to settle the northern "
        "question' (Ike); the Kwantung Army special manoeuvres (Kantokuen), Jul to Aug 1941; "
        "the army's decision of 9 Aug 1941 to give up a northern operation in 1941 (date as "
        "given in the literature, not verified)."
    ),
)

# -- Japan, new in v1 -----------------------------------------------------------------------
_JPN_NOT_STATUS_QUO = V.aims_JPN != "status_quo"
_FLEET = V.jpn_navy == "strong"
_FUEL = V.oil_JPN != "critical"
_BASES = V.indochina == "occupied"
JPN.action(
    "enter_north_indochina",
    guard={"target": V.indochina == "french", "vichy_weak": V.france == "fallen"},
    effect=Set("indochina", "north_occupied"),
    source=(
        "Japanese demand of Jun 1940 to close the Haiphong-Yunnan route and the Nishihara "
        "mission (from 29 Jun 1940); the Liaison Conference decision of 27 Jul 1940; the "
        "Matsuoka-Henry agreement, 30 Aug 1940; the local military agreement of 22 Sep 1940 "
        "and the entry of 22 to 23 Sep 1940 (Morley (ed.), The Fateful Choice, 1980; Iriye "
        "1987)."
    ),
)
JPN.action(
    "occupy_south_indochina",
    guard={
        "hypothesis": _JPN_NOT_STATUS_QUO,
        "north_held": V.indochina == "north_occupied",
        "vichy_weak": V.france == "fallen",
    },
    effect=Set("indochina", "occupied"),
    source=(
        "Liaison Conferences of 25 Jun to 1 Jul 1941 and the Imperial Conference of 2 Jul 1941 "
        "('Outline of national policies in view of the changing situation': the southern "
        "advance to proceed and Japan 'will not be deterred by the possibility of being "
        "involved in a war with Great Britain and the United States', Ike); the agreement with "
        "Vichy of 29 Jul 1941; the entry of 28 Jul 1941."
    ),
)
JPN.action(
    "withdraw_south_indochina",
    guard={"held": V.indochina == "occupied", "peace": V.pacific_war == "peace"},
    effect=Set("indochina", "north_occupied"),
    source=(
        "Proposal B, adopted at the Imperial Conference of 5 Nov 1941 and delivered by Nomura "
        "and Kurusu on 20 Nov 1941 (Ike; FRUS Japan 1931-1941 vol. II)."
    ),
)
JPN.action(
    "attack_south",
    guard={
        "hypothesis": _JPN_NOT_STATUS_QUO,
        "us_not_at_war": V.pacific_war.is_in(["peace", "colonial"]),
        "fleet": _FLEET,
        "fuel": _FUEL,
        "southern_bases": _BASES,
    },
    effect=[Set("pacific_war", "war"), Bump("commit_US", 3)],
    source=(
        "Imperial Conference of 6 Sep 1941 ('Essentials for carrying out the Empire's "
        "policies': war preparations to be completed by the end of Oct; war if diplomacy has "
        "not succeeded by early Oct); the Liaison Conference of 1 Nov 1941 (the three options: "
        "avoid war and accept gradual decline, war at once, war preparations with diplomacy) "
        "and the Imperial Conference of 5 Nov 1941; the Imperial Conference of 1 Dec 1941 "
        "deciding for war; the attacks of 7 to 8 Dec 1941 on Pearl Harbor, Malaya, the "
        "Philippines and Hong Kong (Ike)."
    ),
)
JPN.action(
    "strike_colonies_only",
    guard={
        "hypothesis": _JPN_NOT_STATUS_QUO,
        "peace": V.pacific_war == "peace",
        "fleet": _FLEET,
        "fuel": _FUEL,
        "southern_bases": _BASES,
    },
    effect=Set("pacific_war", "colonial"),
    source=(
        "The Liaison Conference principles of 27 Jul 1940 contemplated force in the south "
        "'confined to Britain as far as possible' while avoiding war with the United States "
        "(Morley (ed.) 1980; Iriye 1987, chapter not verified). No 1941 conference record of "
        "attacking British and Dutch territory while sparing the Philippines as an option put "
        "to decision; the navy's plans from the spring of 1941 assumed war with the United "
        "States."
    ),
    speculative=True,
)
JPN.action(
    "offensive_midway",
    guard={
        "at_war": V.pacific_war == "war",
        "first_stage_done": V.dei == "japanese",
        "fleet": _FLEET,
        "once": ~V.midway_ordered,
    },
    effect=Set("midway_ordered", True),
    source=(
        "The Combined Fleet's plan accepted by the Naval General Staff in early Apr 1942 and "
        "the IGHQ Navy Order of 5 May 1942 for the Midway and Aleutians operation, after the "
        "Doolittle raid of 18 Apr 1942 (Frank 1999; Morison vol. IV)."
    ),
)

# -- Nature (v0; purge gains the part prewar, decisions E2 item 10) --------------------------
NATURE.event(
    "purge",
    guard={
        "officer_corps": V.arms_USSR == "strong",
        # E2 item 10: the purge of the officer corps was a peacetime event of 1937 to 1938.
        "prewar": ~V.east_war,
    },
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

# -- Nature, new in v1 ----------------------------------------------------------------------
_NO_SECOND_FRONT = ~V.last_WEST.is_in(["invade_italy", "land_france"]) & (V.france != "liberated")
_MOBILIZED = V.mob_USSR == "total"
_SOVIET_OFFENSIVE = V.last_USSR == "counteroffensive"
NATURE.event(
    "italy_enters",
    guard={
        "axis": V.axis,
        "war": V.war_west_ger == "war",
        "nonbelligerent": V.italy == "nonbelligerent",
    },
    effect=Set("italy", "at_war"),
    source=(
        "Mussolini at the Brenner, 18 Mar 1940, and his memorandum of 31 Mar 1940 (Italy to "
        "enter the war at Germany's side, timing reserved); the decision on timing of late May "
        "1940 and the declaration of war of 10 Jun 1940 (Knox, Mussolini Unleashed 1939-1941, "
        "1982; Ciano's diary)."
    ),
)
NATURE.event(
    "campaign_east_german",
    guard={
        "offensive": V.last_GER.is_in(["attack_ussr", "offensive_east"]),
        "front": V.w_ussr == "contested",
        "army_ready": _ARMY_READY,
        "red_army_unmobilized": V.mob_USSR == "peace",
        "no_second_front": _NO_SECOND_FRONT,
    },
    effect=Set("w_ussr", "german"),
    source=(
        "Directive No. 21, 18 Dec 1940 (the Red Army to be destroyed west of the Dnieper and "
        "Dvina and the line Archangel to the Volga reached); Halder's war diary, 11 Aug 1941, "
        "on the Soviet reserve divisions; the Moscow battle of Oct to Dec 1941; Hitler's "
        "calling off of Citadel, 13 Jul 1943, after the Sicily landing."
    ),
)
NATURE.event(
    "campaign_caucasus_german",
    guard={
        "offensive": V.last_GER == "offensive_caucasus",
        "front": V.caucasus == "contested",
        "army_ready": _ARMY_READY,
        "no_second_front": _NO_SECOND_FRONT,
    },
    effect=Set("caucasus", "german"),
    source=(
        "Directive No. 41, 5 Apr 1942; Directive No. 45, 23 Jul 1942; Maikop reached 9 Aug "
        "1942 with its fields wrecked; the halt before Grozny and Ordzhonikidze, Oct to Nov "
        "1942."
    ),
)
NATURE.event(
    "caucasus_relieved",
    guard={
        "offensive": _SOVIET_OFFENSIVE,
        "front": V.caucasus != "soviet",
        "mobilized": _MOBILIZED,
    },
    effect=Set("caucasus", "soviet"),
    source=(
        "Uranus, 19 to 23 Nov 1942 (the Sixth Army encircled); the German order of 28 Dec 1942 "
        "to withdraw from the Caucasus; Army Group A's withdrawal, Jan 1943."
    ),
)
NATURE.event(
    "east_liberated",
    guard={
        "offensive": _SOVIET_OFFENSIVE,
        "front": V.w_ussr != "soviet",
        "mobilized": _MOBILIZED,
        "german_strain": V.exhaustion_GER >= "strained",
    },
    effect=Set("w_ussr", "soviet"),
    source=(
        "The Red Army on the Prut, 26 Mar 1944; Crimea retaken, May 1944; Bagration, from "
        "22 Jun 1944 (Minsk 3 Jul, Brest 28 Jul 1944)."
    ),
)
NATURE.event(
    "german_strain",
    guard={
        "two_fronts": V.east_war & (V.war_us_ger == "war"),
        "soviet_mobilized": _MOBILIZED,
        "level": V.exhaustion_GER == "sustainable",
    },
    effect=Set("exhaustion_GER", "strained"),
    source=(
        "The Sixth Army's surrender at Stalingrad, 31 Jan to 2 Feb 1943; the decree of 13 Jan "
        "1943 on the deployment of men and women for Reich defence; Goebbels's Sportpalast "
        "speech, 18 Feb 1943."
    ),
)
NATURE.event(
    "german_exhaustion",
    guard={
        "strained": V.exhaustion_GER == "strained",
        "bombing": V.strategic_bombing & (V.air_west == "allied"),
        "two_fronts": V.east_war & (V.war_west_ger == "war"),
        "territory_lost": (V.w_ussr == "soviet") | (V.france == "liberated"),
    },
    effect=Set("exhaustion_GER", "exhausted"),
    source=(
        "The oil offensive from 12 May 1944; Speer's memoranda to Hitler on fuel, summer 1944 "
        "(date not verified); the loss of Romania, 23 to 30 Aug 1944; the fall of the "
        "armaments output index from Jul 1944 (USSBS, hindsight)."
    ),
)
NATURE.event(
    "air_war_won",
    guard={
        "bombing": V.strategic_bombing,
        "us_arms": V.arms_USA == "high",
        "level": V.air_west == "contested",
    },
    effect=Set("air_west", "allied"),
    source=(
        "Big Week, 20 to 25 Feb 1944, and the defeat of the German day-fighter force by May "
        "1944 with long-range escort fighters; the Schweinfurt raid of 14 Oct 1943 as the "
        "record that unescorted daylight bombing could not win it (Murray 1983)."
    ),
)
NATURE.event(
    "italy_capitulates",
    guard={"landing": V.last_WEST == "invade_italy", "at_war": V.italy == "at_war"},
    effect=Set("italy", "surrendered"),
    source=(
        "Sicily, 10 Jul 1943; Mussolini deposed, 25 Jul 1943; the armistice of Cassibile, "
        "3 Sep, announced 8 Sep 1943."
    ),
)
NATURE.event(
    "campaign_france",
    guard={
        "landing": V.last_WEST == "land_france",
        "france_occupied": V.france == "fallen",
        "air_superiority": V.air_west == "allied",
        "reserves_bound": V.east_war,
    },
    effect=Set("france", "liberated"),
    source=(
        "Normandy, 6 Jun 1944; the breakout (Cobra, from 25 Jul 1944); Falaise closed 21 Aug; "
        "Paris 25 Aug 1944. COSSAC's condition on German mobile reserves in France, met "
        "because the German army was held in the East."
    ),
)
NATURE.event(
    "reich_collapses",
    guard={
        "exhausted": V.exhaustion_GER == "exhausted",
        "east": V.w_ussr == "soviet",
        "west": V.france == "liberated",
        "level": V.reich == "fighting",
    },
    effect=Set("reich", "surrendered"),
    source=(
        "Vistula-Oder, Jan 1945; the Rhine crossings, Mar 1945; the surrender at Reims, 7 May, "
        "and Berlin, 8 May 1945."
    ),
)
NATURE.event(
    "campaign_south",
    guard={
        "at_war": V.pacific_war.is_in(["colonial", "war"]),
        "target": V.dei == "dutch",
        "fleet": _FLEET,
    },
    effect=[Set("dei", "japanese"), Set("oil_JPN", "secure")],
    source=(
        "Malaya and Singapore (15 Feb 1942); Palembang, 14 to 16 Feb 1942; the Dutch "
        "capitulation on Java, 8 Mar 1942; the first-stage plan's estimate of about 150 days, "
        "beaten in practice."
    ),
)
NATURE.event(
    "midway",
    guard={
        "operation": V.midway_ordered,
        "fleet": _FLEET,
        "at_war": V.pacific_war == "war",
    },
    effect=Set("jpn_navy", "attrited"),
    source=(
        "Midway, 4 to 7 Jun 1942: four fleet carriers lost; the American foreknowledge from "
        "the Pacific Fleet's codebreakers (Morison vol. IV; Frank 1999)."
    ),
)
NATURE.event(
    "naval_attrition",
    guard={
        "at_war": V.pacific_war == "war",
        "fleet": _FLEET,
        "us_arms": V.arms_USA == "high",
    },
    effect=Set("jpn_navy", "attrited"),
    source=(
        "The Solomons campaign, Aug 1942 to Feb 1943; the Philippine Sea, 19 to 20 Jun 1944; "
        "the American carrier programme of the Two-Ocean Navy Act delivering from 1943."
    ),
)
NATURE.event(
    "stocks_run_down",
    guard={
        "embargo": V.oil_JPN == "embargoed",
        "clock": ((V.fair_oil_clock >= 6) & V.pacific_war.is_in(["colonial", "war"]))
        | (V.fair_oil_clock >= 8),
    },
    effect=Set("oil_JPN", "critical"),
    source=(
        "The navy's estimates put to the Imperial Conferences of 6 Sep and 5 Nov 1941 and the "
        "Liaison Conferences of Oct to Nov 1941: stocks for about two years, about eighteen "
        "months at war consumption (Ike); Suzuki Teiichi's materials report of 5 Nov 1941."
    ),
)
NATURE.event(
    "sea_lanes_cut",
    guard={
        "at_war": V.pacific_war == "war",
        "fleet": V.jpn_navy == "attrited",
        "us_arms": V.arms_USA == "high",
        "supply": V.oil_JPN != "critical",
    },
    effect=Set("oil_JPN", "critical"),
    source=(
        "The American submarine campaign against tankers, 1943 to 1944; Leyte Gulf, 23 to "
        "26 Oct 1944; the last tanker convoys from the southern area, Feb to Mar 1945 (USSBS, "
        "Oil in Japan's War, 1946, hindsight)."
    ),
)
NATURE.event(
    "atomic",
    guard={
        "weapon": V.bomb_ready,
        "at_war": V.pacific_war == "war",
        "delivery": V.jpn_navy == "attrited",
    },
    effect=Set("pacific_war", "surrendered"),
    source=(
        "Hiroshima, 6 Aug 1945; Nagasaki, 9 Aug 1945; the Imperial Conferences of 9 to 10 Aug "
        "and 14 Aug 1945 and the Emperor's decision to accept the Potsdam terms (Butow, "
        "Japan's Decision to Surrender, 1954; Frank 1999)."
    ),
)

# -- constraints (v0, unchanged) ------------------------------------------------------------
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
# -- constraints, new in v1 -----------------------------------------------------------------
# The embargo clock (actions_ww2_v1.md, constraints). Source: the navy's estimates put to the
# Imperial Conferences of 6 Sep and 5 Nov 1941 and the Liaison Conferences of Oct to Nov 1941
# (Ike); Suzuki Teiichi's materials report of 5 Nov 1941. A physical clock, not a behaviour:
# at eight quarters under embargo Nature must play stocks_run_down.
# Well-formedness edit before any registered test (guard changelog, 2026-10-13): Nature's
# one event per tick cannot carry both forced resolutions when the clock reaches 8 in the
# quarter after a French offensive against the unready German army (rhineland_resolution);
# campaign_rhineland is then also a response of the clock. It ends the run in
# GERMAN_DEFEAT, so the clock has no later quarter to bind in.
model.fairness(
    "oil_clock",
    actor="Nature",
    trigger=V.oil_JPN == "embargoed",
    within=8,
    responses=["stocks_run_down", "campaign_rhineland"],
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
# T11's profile. Source: Roosevelt's Boston speech of 30 Oct 1940; the House vote of 12 Aug
# 1941 on extending the term of service (203 to 202); the Gallup (AIPO) series of 1941;
# Roosevelt's refusal to ask Congress for a declaration after the Greer, Kearny and Reuben
# James incidents (Heinrichs, Threshold of War, 1988).
model.profile(
    "electoral",
    actor="WEST",
    forbid=["us_declare_war", "us_declare_war_jpn"],
    unless=V.pacific_war.is_in(["war", "surrendered"]),
)
# T7's "embargo maintained" (testbed changelog, 2026-10-11).
model.profile("embargo_maintained", actor="WEST", forbid=["lift_embargo"])
# T9 only (decisions E5): a named, relaxable behavioural assumption, not feasibility. Germany
# does not attack Poland while it reads Britain as resolved to fight and an Anglo-Soviet
# alliance exists.
model.profile(
    "deterred",
    actor="GER",
    forbid=["attack_poland"],
    unless=~((V.belief_GER == "will_fight") & V.anglo_soviet_alliance),
)
model.assume("ussr_defensive", V.aims_USSR == "defensive")

# -- balance, kernels, endings (v1 ontology section 6) --------------------------------------
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
GERMAN_REGIONS_V1 = (
    GERMAN_REGIONS + Ite(V.w_ussr == "german", 1, 0) + Ite(V.caucasus == "german", 1, 0)
)
model.invariant(
    "balance_europe",
    (V.reich == "surrendered")
    | ((GERMAN_REGIONS_V1 < 5) & (V.france != "fallen") & V.britain.is_in(["at_peace", "at_war"])),
)
model.invariant("balance_asia", (V.pacific_war == "surrendered") | (V.dei != "japanese"))
model.invariant(
    "commitment_alive",
    (V.treaty != "dead") | V.polish_guarantee | V.anglo_soviet_alliance | (V.war_west_ger == "war"),
)
PEACE_EUROPE = (V.war_west_ger == "peace") & ~V.east_war & (V.war_us_ger == "peace")
model.invariant("peace_europe", PEACE_EUROPE)
# Analysis predicates of decisions E5.
# T6: V_GER is GER's kernel for undefeated (a non-defeat ending is reached iff it holds
# through the horizon).
model.invariant("undefeated", (V.reich == "fighting") & ~V.german_defeat)
# T9: "block" is keeping Poland independent through tick 20.
model.invariant("poland_blocked", (V.poland == "independent") | (V.tick > 20))
# T13 refinement on v1: the European predicate through tick 20.
model.invariant("european_peace", PEACE_EUROPE & (V.poland == "independent"))
model.invariant("european_peace_t20", V.invariant("european_peace") | (V.tick > 20))

# Endings are mutually exclusive on every state: each excludes the ones declared before it
# (the order of v1 ontology section 6).
_earlier = []


def _ending(name: str, expr) -> None:
    cond = expr
    for prev in _earlier:
        cond = cond & ~V.ending(prev)
    model.ending(name, cond)
    _earlier.append(name)


_AT_HORIZON = V.tick == HORIZON
_ending("GERMAN_DEFEAT", V.german_defeat)
_ending("NEGOTIATED_PEACE", (V.britain == "negotiated") | V.east_peace)
_ending(
    "AXIS_HEGEMONY_EUROPE",
    (V.britain == "invaded") | ((V.w_ussr == "german") & (V.caucasus == "german")),
)
_ending("JPN_CONQUERS_USSR", V.siberia == "japanese")
_ending("USSR_JOINS_AXIS", V.ussr_axis)
_ending("ALLIED_VICTORY", (V.reich == "surrendered") & (V.pacific_war == "surrendered"))
_ending(
    "AXIS_HEGEMONY_ASIA",
    _AT_HORIZON
    & (V.dei == "japanese")
    & (V.indochina == "occupied")
    & V.pacific_war.is_in(["peace", "colonial"]),
)
_ending(
    "PACIFIC_WAR_CONTINUES",
    _AT_HORIZON & (V.reich == "surrendered") & V.pacific_war.is_in(["colonial", "war"]),
)
_ending(
    "NO_GENERAL_WAR",
    _AT_HORIZON & PEACE_EUROPE & (V.poland == "independent") & (V.pacific_war == "peace"),
)
_ending("LIMITED_WAR", _AT_HORIZON & PEACE_EUROPE)
_ending("WAR_UNRESOLVED", _AT_HORIZON)
