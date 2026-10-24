"""Cold War v0: the United States, the Soviet Union and (from 1969) the PRC, 1947 to 1991,
one tick per year.

The model of docs/ontology_cw.md and docs/actions_cw.md as settled in docs/cw_v0_decisions.md.
The registered claims C1 to C13 (docs/coldwar_testbed.md section 5) were committed on
2026-10-11, before any WW2 or Cold War guard was written; the transfer hypotheses H1 to H8
(docs/transfer_hypotheses.md) were committed before any Cold War guard. Every guard, effect,
delay, fairness constraint or profile edited after the first run of C1 to C13 is logged in
docs/guard_changelog_cw.md with a dated source.

Time (decisions D1): one tick is one calendar year. The state at tick t is the start of year
1947 + t (1 January); the joint move at tick t is what each actor decided during that year;
its effects are visible at t + 1. Tick 0 is 1 January 1947 and the horizon, tick 45, is
1 January 1992 (the state after 1991). A reaction to another actor's decision of the same year
appears the next year ([SQR]); Nature plays one event per tick ([NSL] where two fall in one
year). Both markers are noted in data/cw/realized_moves.csv.

Actors (decisions D2): ``USA``, ``USSR``, ``PRC`` and Nature (intelligence estimates and
assessments, the East European societies and governments, the Soviet economy and polity,
accidents). ``build(prc_principal=False)`` moves the PRC's decisions to Nature with the same
guards and effects, and a war between the USSR and the PRC is then not a war between
principals (claim C11). The PRC's actions carry the part ``principal`` (``tick >= 22``): the
testbed makes the PRC a principal from 1969 and scripts it before (it has no decision the
model represents before 1969); the part is a scope, not a historical constraint.

Hidden objective (swept, no ``assume``): ``aims_USSR`` (status_quo | opportunist), hidden
from USA and PRC. A guard part named ``hypothesis`` is a hypothesis gate.

Crises (decisions D5): Berlin 1948, Cuba 1962 and the Able Archer exercise of 1983 are
sub-games (``models/cw/crises``) entered by the coarse actions ``USSR.blockade``,
``USSR.deploy_cuba`` and ``USA.able_archer``, which have no effect of their own (framework
spec section 14); in the coarse game alone they are inert. The Berlin crisis of 1958 to
1961 is represented at the coarse level (``esc == crisis`` across the year boundaries).

Escalation is composed by ``Bump`` on ``esc`` (decisions D4), so that the moves of two
actors and Nature in one year add up rather than conflict: a standing crisis that one side
escalates while the other resolves it stays a crisis.

Beliefs (decisions D6): ``belief_force_USA`` (the United States' estimate of the Soviet
strategic force, on ``nuke_USSR``'s scale), ``belief_USA_USSR`` (Washington's reading of
Soviet aims) and ``belief_USSR_USA`` (Moscow's reading of American aims) are state; they
change by Nature's assessment events and by the detection of Soviet deployments. Hindsight
snapshots carry for each belief the hindsight truth of what it estimates; the contemporaneous
beliefs are in the replay snapshots (coldwar_testbed.md section 6.1).
"""

from __future__ import annotations

from pathlib import Path

from wavefront.model import FALSE, Bump, Model, Set, SetIf, V

HORIZON = 45  # 1 January 1992, the state after 1991
YEAR0 = 1947
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "cw"
REALIZED_MOVES = DATA / "realized_moves.csv"
PRC_FROM = 22  # 1969: the PRC a principal (coldwar_testbed.md section 2)

NUKE = ["none", "few", "survivable", "overkill"]


def tick_of(year: int) -> int:
    """The tick whose state is 1 January of ``year``, and whose move is that year's."""
    return year - YEAR0


def raise_to(var: str, level: str) -> SetIf:
    """``var := max(var, level)``."""
    return SetIf(V[var] < level, var, level)


def build(prc_principal: bool = True, frozen_oversight: bool = False) -> Model:
    """The Cold War coarse model; with ``prc_principal=False`` the PRC's decisions are
    Nature's and a Sino-Soviet war is not a war between principals (claim C11). With
    ``frozen_oversight=True`` (an analysis build for claim C8) no action changes
    ``oversight``: the verification regime stays at its initial or loaded level."""

    def oversight_to(level: str) -> list:
        return [] if frozen_oversight else [raise_to("oversight", level)]

    name = "cw_v0" if prc_principal else "cw_v0_prc_scripted"
    m = Model(
        name + ("_frozen_oversight" if frozen_oversight else ""),
        horizon=HORIZON,
        description=(
            "The Cold War, 1947 to 1991, one tick per year: the United States, the Soviet "
            "Union, the PRC (a principal from 1969) and Nature, after docs/ontology_cw.md and "
            "docs/actions_cw.md with the decisions of docs/cw_v0_decisions.md"
            + ("" if prc_principal else "; the PRC's decisions carried by Nature (claim C11)")
            + ". The validation model of the framework; every result is conditional on it "
            "and on its initial state."
        ),
    )

    # -- hidden objective (ontology section 1) -----------------------------------------------
    m.var(
        "aims_USSR",
        levels=["status_quo", "opportunist"],
        init=None,
        hidden_from=["USA"] + (["PRC"] if prc_principal else []),
    )

    # -- strategic forces and intelligence (ontology section 2) ------------------------------
    m.var("nuke_USA", levels=NUKE, init="few", monotone=True)
    m.var("nuke_USSR", levels=NUKE, init="none", monotone=True)
    m.var("intel_USA", levels=["low", "partial", "overhead"], init="low", monotone=True)

    # -- beliefs (ontology section 3) --------------------------------------------------------
    m.var("belief_force_USA", levels=NUKE, init="none")
    m.var(
        "belief_USA_USSR", levels=["status_quo", "opportunist", "expansionist"], init="opportunist"
    )
    m.var(
        "belief_USSR_USA", levels=["status_quo", "hostile", "first_strike_intent"], init="hostile"
    )

    # -- arms control and verification (ontology section 4) ----------------------------------
    m.var("offer", levels=["none", "test_ban", "limits", "reductions"], init="none", monotone=True)
    m.var("oversight", levels=["none", "test_ban", "ntm", "on_site"], init="none", monotone=True)
    m.var("arms", levels=["race", "capped", "reduced"], init="race", monotone=True)
    m.flag("buildup", init=False, monotone=True)

    # -- escalation between the principals (ontology section 5) ------------------------------
    m.var(
        "esc",
        levels=["peace", "crisis", "conventional", "tactical_nuclear", "strategic"],
        init="peace",
    )
    m.flag("accidental", init=False, monotone=True)
    m.flag("us_strike", init=False, monotone=True)
    m.flag("berlin_wall", init=False, monotone=True)
    m.flag("invasion_west", init=False, monotone=True)
    # Added 2026-10-23 on the owner's decision 2l (docs/guard_changelog_cw.md): a war between
    # the principals begun by the United States (NATO), the condition of Soviet nuclear use.
    m.flag("us_began_war", init=False, monotone=True)

    # -- peripheral wars (ontology section 6) ------------------------------------------------
    m.var("korea", levels=["peace", "war", "armistice"], init="peace", monotone=True)
    m.var("afghan", levels=["none", "war", "withdrawn"], init="none", monotone=True)

    # -- the Soviet economy, polity and bloc (ontology section 7) ----------------------------
    m.var(
        "econ_USSR",
        levels=["growing", "stagnant", "declining", "failing"],
        init="growing",
        monotone=True,
    )
    m.var("legit_USSR", levels=["secure", "contested", "failing"], init="secure", monotone=True)
    m.flag("perestroika", init=False, monotone=True)
    m.var("bloc_USSR", levels=["intact", "contested", "released", "dissolved"], init="intact")

    # -- the PRC (ontology section 8) --------------------------------------------------------
    m.var(
        "align_PRC",
        levels=["soviet_ally", "split", "us_aligned"],
        init="soviet_ally",
        monotone=True,
    )
    m.flag("china_opening", init=False, monotone=True)
    m.var("esc_sino", levels=["peace", "clash", "war"], init="peace")

    # -- actors ------------------------------------------------------------------------------
    usa = m.actor("USA", observes=V.all_except("aims_USSR", "belief_USSR_USA"))
    ussr = m.actor("USSR", observes=V.all())
    prc = m.actor("PRC", observes=V.all_except("aims_USSR")) if prc_principal else None
    nature = m.nature()
    # The PRC's decisions: the PRC's own actions, or Nature's events in the scripted build.
    prc_act = prc.action if prc_principal else nature.event

    def prc_guard(parts: dict) -> dict:
        return {"principal": V.tick >= PRC_FROM, **parts} if prc_principal else parts

    # -- United States -----------------------------------------------------------------------
    usa.action(
        "approve_u2",
        guard={"level": V.intel_USA == "low"},
        effect=raise_to("intel_USA", "partial"),
        delay=2,
        source=(
            "Eisenhower's approval of the CL-282 (U-2) programme on 24 Nov 1954 on the "
            "recommendation of the Killian panel's intelligence subcommittee (Land); first "
            "overflight of the USSR 4 Jul 1956 (Pedlow and Welzenbach, The CIA and the U-2 "
            "Program, 1954-1974, CIA 1992). Delay 2: decided 1954, visible 1 Jan 1957."
        ),
    )
    usa.action(
        "survivable_force",
        guard={"level": V.nuke_USA == "few"},
        effect=raise_to("nuke_USA", "survivable"),
        delay=4,
        source=(
            "The Polaris fleet ballistic missile programme approved by the Secretary of the "
            "Navy and Burke in Dec 1956 (after NSC action of Dec 1955 giving ballistic missiles "
            "the highest priority) and the Minuteman decision of Feb 1958; first Polaris patrol "
            "(George Washington) 15 Nov 1960; SAC's ground alert from 1957 (Rosenberg, 'The "
            "Origins of Overkill', International Security 1983; Freedman, The Evolution of "
            "Nuclear Strategy). Delay 4: decided 1956, visible 1 Jan 1961."
        ),
    )
    usa.action(
        "corona",
        guard={"level": V.intel_USA == "partial"},
        effect=raise_to("intel_USA", "overhead"),
        delay=2,
        source=(
            "Eisenhower's approval of the CORONA reconnaissance satellite programme in Feb "
            "1958; first successful recovery 18 Aug 1960 (Discoverer 14), covering more Soviet "
            "territory than all U-2 flights together (Ruffner (ed.), CORONA: America's First "
            "Satellite Program, CIA 1995). Delay 2: decided 1958, visible 1 Jan 1961."
        ),
    )
    usa.action(
        "offer_test_ban",
        guard={"level": V.offer == "none"},
        effect=raise_to("offer", "test_ban"),
        source=(
            "The Western draft treaty for the discontinuance of nuclear tests tabled at the "
            "Geneva Conference on the Discontinuance of Nuclear Weapon Tests (opened 31 Oct "
            "1958), with Eisenhower's proposal of 13 Apr 1959 for an atmospheric ban "
            "(FRUS 1958-60 vol. III; Seaborg, Kennedy, Khrushchev and the Test Ban, 1981)."
        ),
    )
    usa.action(
        "strategic_buildup",
        guard={
            "missile_gap": V.belief_force_USA >= "survivable",
            "level": V.nuke_USA == "survivable",
        },
        effect=raise_to("nuke_USA", "overkill"),
        delay=3,
        source=(
            "Kennedy's special defence messages of 28 Mar and 25 May 1961 accelerating Polaris "
            "and Minuteman (to 1,000 Minuteman and 41 Polaris boats by 1967), decided on the "
            "missile-gap estimates of 1958 to 1960 still in force in early 1961 (Preble, John "
            "F. Kennedy and the Missile Gap, 2004; Ball, Politics and Force Levels, 1980). "
            "Part missile_gap: the decision answered the estimated Soviet force. Delay 3: "
            "decided 1961, visible 1 Jan 1965."
        ),
    )
    usa.action(
        "offer_limits",
        guard={"standing": V.offer == "test_ban", "parity": V.nuke_USSR >= "survivable"},
        effect=raise_to("offer", "limits"),
        source=(
            "Johnson's and McNamara's proposal of strategic arms limitation talks, Johnson's "
            "letter to Kosygin of 27 Jan 1967 and the Glassboro summit of 23 to 25 Jun 1967, "
            "made as the Soviet hardened ICBM force grew and Moscow began an ABM system "
            "(FRUS 1964-68 vol. XI; Newhouse, Cold Dawn, 1973). Part parity: the proposal "
            "answered the Soviet secure force."
        ),
    )
    usa.action(
        "open_china",
        guard={"split": V.align_PRC == "split", "level": ~V.china_opening},
        effect=Set("china_opening", True),
        source=(
            "Nixon's and Kissinger's opening to the PRC: the messages through Pakistan and "
            "Romania from 1969 and Kissinger's secret visit to Beijing 9 to 11 Jul 1971, "
            "announced by Nixon on 15 Jul 1971 (FRUS 1969-76 vol. XVII; Kissinger, White House "
            "Years, 1979)."
        ),
    )
    usa.action(
        "buildup",
        guard={"level": ~V.buildup},
        effect=Set("buildup", True),
        source=(
            "Reagan's defence buildup: the FY1982 budget amendment of Mar 1981, the strategic "
            "modernization programme of 2 Oct 1981 (NSDD-12: MX, B-1B, Trident II) and the "
            "Strategic Defense Initiative of 23 Mar 1983 (Fischer, The Reagan Reversal, 1997; "
            "Gaddis, Strategies of Containment, 2005)."
        ),
    )
    usa.action(
        "offer_reductions",
        guard={"standing": V.offer == "limits"},
        effect=raise_to("offer", "reductions"),
        source=(
            "The zero option for intermediate-range missiles (Reagan, 18 Nov 1981) and the "
            "START proposal of deep reductions (Reagan's Eureka College speech, 9 May 1982) "
            "(Talbott, Deadly Gambits, 1984; FRUS 1981-88 vol. XLIV, not verified)."
        ),
    )
    usa.action(
        "armistice",
        guard={"theatre": V.korea == "war"},
        effect=Set("korea", "armistice"),
        source=(
            "The Korean armistice signed at Panmunjom on 27 Jul 1953 after talks from 10 Jul "
            "1951, concluded by the Eisenhower administration after Stalin's death (FRUS "
            "1952-54 vol. XV; Stueck, The Korean War, 1995)."
        ),
    )
    usa.action(
        "preventive_strike",
        guard={
            "superiority": (V.nuke_USA >= "few") & (V.nuke_USSR <= "few"),
            "threat": V.belief_USA_USSR == "expansionist",
            "policy": FALSE,
        },
        effect=[Bump("esc", 4), Set("us_strike", True)],
        source=(
            "The preventive war debated in Washington from 1950 to 1954: Matthews's speech of "
            "25 Aug 1950 and the advocacy within the Air Force and the JCS (the Advanced Study "
            "Group, 1954), rejected in NSC-68 (Apr 1950) and by Eisenhower (NSC 5440, Dec 1954; "
            "his remarks of 1954 that preventive war was impossible) (Trachtenberg, 'A Wasting "
            "Asset', International Security 1988; Buhite and Hamel, Diplomatic History 1990). "
            "Part policy: the rejection; relaxing it is the preventive option taken (claim C12)."
        ),
    )
    usa.action(
        "nuclear_korea",
        guard={
            "theatre": V.korea == "war",
            "total_commitment": V.esc >= "conventional",
            "reading": V.belief_USA_USSR != "opportunist",
        },
        effect=Bump("esc", 4),
        source=(
            "The use of atomic weapons in Korea considered by Truman (press conference of "
            "30 Nov 1950), the JCS (1951) and Eisenhower (NSC of 11 Feb and 6 May 1953), and "
            "not taken for fear of Soviet entry and of the war in Europe (Gaddis, The Long "
            "Peace, 1987; Dingman, 'Atomic Diplomacy during the Korean War', International "
            "Security 1988). Part total_commitment: the commitment the record makes the "
            "condition of use, a direct war with the USSR (ontology section 5). Part reading: "
            "use needed Washington to read Soviet aims as more than opportunist (claim C5)."
        ),
    )
    usa.action(
        "escalate",
        guard={"crisis": V.esc == "crisis"},
        effect=[Bump("esc", 1), Set("us_began_war", True)],
        source=(
            "The military options of a standing Berlin crisis: Clay's armed convoy proposal "
            "of Jul 1948, the Live Oak contingency plans of 1959 to 1961 for probes along the "
            "access routes, and Kennedy's buildup of 25 Jul 1961 (Trachtenberg, A Constructed "
            "Peace, 1999; FRUS 1961-63 vol. XIV). Effect us_began_war (added 2026-10-23, "
            "decision 2l): combat opened by the United States from a standing crisis is the "
            "war begun by NATO that the Warsaw Pact plans assumed (USSR.nuclear_use)."
        ),
    )
    usa.action(
        "nuclear_use",
        guard={"war": V.esc == "conventional", "means": V.nuke_USA >= "few"},
        effect=Bump("esc", 1),
        source=(
            "NATO's planned first use of nuclear weapons against a conventional attack: MC "
            "14/2 (approved May 1957) and MC 14/3 (flexible response, Jan 1968) (Trachtenberg "
            "1999; Freedman, The Evolution of Nuclear Strategy)."
        ),
    )
    usa.action(
        "preempt",
        guard={"warning": V.belief_USA_USSR == "expansionist", "crisis": V.esc >= "crisis"},
        effect=Bump("esc", 3),
        source=(
            "The preemptive options of US war plans on strategic warning: SAC's war plans of "
            "the 1950s and the SIOP-62 'preemption' option approved in Dec 1960 (Rosenberg, "
            "'The Origins of Overkill', 1983; Sagan, 'SIOP-62', International Security 1987)."
        ),
    )
    usa.action(
        "able_archer",
        guard={"occasion": V.tick == tick_of(1983)},
        effect=[],
        source=(
            "NATO's command post exercise Able Archer 83, 7 to 11 Nov 1983, with new nuclear "
            "release procedures and communications; the crisis is the sub-game "
            "models/cw/crises/able_archer_1983.py (Jones, Able Archer 83, 2016; the President's "
            "Foreign Intelligence Advisory Board, 'The Soviet War Scare', 15 Feb 1990, "
            "declassified 2015). Part occasion: the exercise of that year."
        ),
    )

    # -- Soviet Union ------------------------------------------------------------------------
    ussr.action(
        "build_bomb",
        guard={"level": V.nuke_USSR == "none"},
        effect=[raise_to("nuke_USSR", "few"), Set("belief_force_USA", "few")],
        delay=4,
        source=(
            "Stalin's decision of 20 Aug 1945 creating the Special Committee under Beria for "
            "the atomic project; the first test, 29 Aug 1949, detected by US air sampling and "
            "announced by Truman on 23 Sep 1949 (Holloway, Stalin and the Bomb, 1994). Delay "
            "4: decided 1945, visible 1 Jan 1950; the 1947 snapshot carries the decision as a "
            "pending built-in."
        ),
    )
    ussr.action(
        "blockade",
        guard={"occasion": V.tick == tick_of(1948)},
        effect=[],
        source=(
            "The blockade of the western sectors of Berlin from 24 Jun 1948, after the London "
            "programme (Jun 1948) and the western currency reform of 20 Jun 1948; the crisis is "
            "the sub-game models/cw/crises/berlin_1948.py (Narinsky, in Gori and Pons (eds.), "
            "The Soviet Union and Europe in the Cold War, 1996; Trachtenberg 1999). Part "
            "occasion: the currency reform of that year."
        ),
    )
    ussr.action(
        "approve_korea",
        guard={
            "hypothesis": V.aims_USSR == "opportunist",
            "occasion": V.korea == "peace",
            "bomb": V.nuke_USSR >= "few",
        },
        effect=Set("korea", "war"),
        source=(
            "Stalin's approval of Kim Il Sung's attack in his talks with Kim in Moscow, Apr "
            "1950, citing the changed situation (the Soviet bomb, the Chinese revolution) after "
            "refusing in Mar 1949 and Sep 1949; the attack of 25 Jun 1950 (Weathersby, CWIHP "
            "Working Paper 8, 1993; Goncharov, Lewis and Xue, Uncertain Partners, 1993). [H]: "
            "read as opportunism; part bomb: Stalin's own condition."
        ),
    )
    ussr.action(
        "enter_korea",
        guard={
            "theatre": V.korea == "war",
            "hypothesis": V.aims_USSR == "opportunist",
            "readiness": V.nuke_USSR >= "survivable",
        },
        effect=Bump("esc", 2),
        source=(
            "Open Soviet entry into the Korean war, refused by Stalin in his telegram to Mao "
            "of 5 Oct 1950 (the USSR not ready for a war with the United States; Soviet air "
            "units fought covertly from Nov 1950) (Weathersby 1993; Mansourov, CWIHP Bulletin "
            "6-7, 1995). Part readiness: Stalin's stated condition."
        ),
    )
    ussr.action(
        "berlin_ultimatum",
        guard={"open": ~V.berlin_wall, "level": V.esc == "peace"},
        effect=Bump("esc", 1),
        source=(
            "Khrushchev's speech of 10 Nov 1958 and the note of 27 Nov 1958 demanding a free "
            "city of West Berlin within six months, renewed at Vienna on 4 Jun 1961 (Zubok and "
            "Pleshakov, Inside the Kremlin's Cold War, 1996; Harrison, Driving the Soviets up "
            "the Wall, 2003)."
        ),
    )
    ussr.action(
        "lapse",
        guard={"crisis": V.esc == "crisis", "open": ~V.berlin_wall},
        effect=Bump("esc", -1),
        source=(
            "The lapse of a Berlin deadline without action: the six-month limit of May 1959 "
            "passed during the Geneva foreign ministers' conference, and Khrushchev's "
            "withdrawal of the end-of-year deadline on 17 Oct 1961 (Zubok and Pleshakov 1996)."
        ),
    )
    ussr.action(
        "build_wall",
        guard={"crisis": V.esc == "crisis", "open": ~V.berlin_wall},
        effect=[Set("berlin_wall", True), Bump("esc", -1)],
        source=(
            "The sealing of the sector border on 13 Aug 1961, approved at the Warsaw Pact "
            "meeting of 3 to 5 Aug 1961 on Ulbricht's request (Harrison 2003); with the "
            "Wall the Berlin crisis ended as a standing confrontation after the Checkpoint "
            "Charlie standoff of 27 to 28 Oct 1961."
        ),
    )
    ussr.action(
        "withdraw_advisers",
        guard={"alliance": V.align_PRC == "soviet_ally"},
        effect=raise_to("align_PRC", "split"),
        source=(
            "Khrushchev's withdrawal of the Soviet specialists from China, notified 16 Jul "
            "1960, after the polemics of Apr 1960 (Lüthi, The Sino-Soviet Split, 2008)."
        ),
    )
    ussr.action(
        "deploy_cuba",
        guard={"occasion": V.tick == tick_of(1962)},
        effect=[],
        source=(
            "The Presidium's decision of 24 May 1962 (Operation Anadyr) to deploy missiles to "
            "Cuba; the crisis from their discovery on 14 to 16 Oct 1962 is the sub-game "
            "models/cw/crises/cuba_1962.py (Fursenko and Naftali, One Hell of a Gamble, 1997). "
            "Part occasion: the deployment of that year."
        ),
    )
    ussr.action(
        "accept_test_ban",
        guard={"offer": V.offer >= "test_ban", "level": V.oversight == "none"},
        effect=oversight_to("test_ban"),
        source=(
            "Khrushchev's acceptance of a test ban in the atmosphere, space and under water "
            "(Harriman's mission, 15 to 25 Jul 1963), the Limited Test Ban Treaty signed 5 Aug "
            "1963, verified by national means; with the hotline agreement of 20 Jun 1963 "
            "(Seaborg 1981; Fursenko and Naftali 1997)."
        ),
    )
    ussr.action(
        "icbm_buildup",
        guard={"level": V.nuke_USSR == "few"},
        effect=[
            raise_to("nuke_USSR", "survivable"),
            SetIf(V.intel_USA == "overhead", "belief_force_USA", "survivable"),
        ],
        delay=2,
        source=(
            "The Soviet buildup of a hardened ICBM force after the Cuban crisis (Kuznetsov to "
            "McCloy, Oct 1962: 'never again'), confirmed under Brezhnev from Oct 1964: the "
            "SS-9 and SS-11 in silos from 1966 (Podvig (ed.), Russian Strategic Nuclear Forces, "
            "2001; Zaloga, The Kremlin's Nuclear Sword, 2002; the decision's date not "
            "verified). Seen by satellite once intel_USA is overhead. Delay 2: decided 1964, "
            "visible 1 Jan 1967."
        ),
    )
    ussr.action(
        "mirv",
        guard={"level": V.nuke_USSR == "survivable"},
        effect=[
            raise_to("nuke_USSR", "overkill"),
            SetIf(V.intel_USA == "overhead", "belief_force_USA", "overkill"),
        ],
        delay=5,
        source=(
            "The Soviet MIRVed fourth-generation ICBMs (SS-17, SS-18, SS-19), developed from "
            "about 1970 and deployed from 1975, with the counterforce capability against "
            "Minuteman behind the 'window of vulnerability' (Podvig 2001; Garthoff, Detente and "
            "Confrontation, 1994; the decision's date not verified). Delay 5: decided 1970, "
            "visible 1 Jan 1976."
        ),
    )
    ussr.action(
        "accept_limits",
        guard={
            "offer": V.offer >= "limits",
            "regime": V.oversight == "test_ban",
            "parity": V.nuke_USSR >= "survivable",
        },
        effect=[*oversight_to("ntm"), raise_to("arms", "capped")],
        source=(
            "SALT I: the Interim Agreement and the ABM Treaty signed in Moscow 26 May 1972, "
            "with non-interference with national technical means of verification (Article V "
            "and XII), after talks from 17 Nov 1969 once the USSR had reached rough parity "
            "(Newhouse 1973; Garthoff 1994)."
        ),
    )
    ussr.action(
        "invade_afghanistan",
        guard={"occasion": V.tick >= tick_of(1979), "level": V.afghan == "none"},
        effect=Set("afghan", "war"),
        source=(
            "The Politburo's decision of 12 Dec 1979 to send troops into Afghanistan (entry "
            "24 to 27 Dec 1979), after refusing the Afghan leaders' requests in Mar 1979 "
            "following the Herat uprising (the Politburo records of 17 to 19 Mar and 12 Dec "
            "1979, CWIHP Bulletin 8-9, 1996). Part occasion: the PDPA regime's crisis of 1979."
        ),
    )
    ussr.action(
        "preempt",
        guard={
            "warning": V.belief_USSR_USA == "first_strike_intent",
            "crisis": V.esc >= "crisis",
            "means": V.nuke_USSR >= "few",
        },
        effect=Bump("esc", 3),
        source=(
            "Soviet doctrine of preemption on warning of an imminent attack (Sokolovsky (ed.), "
            "Military Strategy, 1962) and the KGB's RYAN programme of 1981 to 1984 to detect "
            "American preparations for a first strike (Andrew and Gordievsky (eds.), "
            "Instructions from the Centre, 1991; PFIAB, 'The Soviet War Scare', 1990)."
        ),
    )
    ussr.action(
        "escalate",
        guard={"crisis": V.esc == "crisis"},
        effect=Bump("esc", 1),
        source=(
            "The Soviet military options of a standing Berlin crisis: interference with the "
            "air corridors (the buzzing of Feb to Mar 1962) and the tank standoff at "
            "Checkpoint Charlie, 27 to 28 Oct 1961 (Zubok and Pleshakov 1996)."
        ),
    )
    ussr.action(
        "nuclear_use",
        guard={
            "war": V.esc == "conventional",
            "means": V.nuke_USSR >= "few",
            "nato_attack": V.us_began_war,
        },
        effect=Bump("esc", 1),
        source=(
            "Warsaw Pact war plans with early nuclear strikes in a European war: the 'Seven "
            "Days to the Rhine' exercise of 1979 and the Czechoslovak plan of 1964 (Mastny and "
            "Byrne (eds.), A Cardboard Castle?, 2005). Part nato_attack (added 2026-10-23 on "
            "the owner's decision 2l, a guard edit after first sight): the plans and "
            "exercises the collection prints, from the Czechoslovak plan of 1964 to the "
            "exercises of the 1980s, open with a NATO attack, and their nuclear strikes "
            "belong to a war so begun (Mastny and Byrne 2005, the editors' introduction; the "
            "first-use conditions of each plan not verified against the documents)."
        ),
    )
    ussr.action(
        "invade_west",
        guard={
            "hypothesis": V.aims_USSR == "opportunist",
            "response": V.esc >= "crisis",
            "no_us_nuclear": V.nuke_USA == "none",
        },
        effect=[Bump("esc", 1), Set("invasion_west", True)],
        source=(
            "A Soviet conventional offensive into Western Europe: the Warsaw Pact's offensive "
            "plans as responses to a NATO attack in a crisis (Mastny and Byrne 2005), against "
            "NATO's nuclear first-use threat (MC 14/2, 1957) (claim C12). Part response: the "
            "plans assumed a war begun by NATO; part no_us_nuclear: no Soviet plan foresaw "
            "a conventional war in Europe against a nuclear-armed United States."
        ),
    )
    ussr.action(
        "intervene",
        guard={
            "contested": V.bloc_USSR == "contested",
            "capacity": V.afghan != "war",
            "will": V.legit_USSR == "secure",
        },
        effect=Set("bloc_USSR", "intact"),
        source=(
            "Soviet military intervention to hold the bloc: East Berlin 17 Jun 1953, Hungary "
            "4 Nov 1956, Czechoslovakia 20 to 21 Aug 1968; against Poland the Politburo's "
            "Suslov commission decided in Dec 1980 and Dec 1981 not to intervene, citing "
            "Afghanistan and the economic and Western costs (Kramer, 'Soviet Deliberations "
            "during the Polish Crisis', CWIHP Special Working Paper 1, 1999). Parts capacity "
            "and will: the conditions those deliberations name."
        ),
    )
    ussr.action(
        "perestroika",
        guard={"level": ~V.perestroika, "crisis": V.econ_USSR >= "stagnant"},
        effect=[Set("perestroika", True), raise_to("legit_USSR", "contested")],
        source=(
            "Gorbachev's reform: the April 1985 plenum, the 27th Party Congress (Feb 1986) "
            "with glasnost, the Law on Individual Labour Activity (19 Nov 1986) and the "
            "Jan and Jun 1987 plenums preparing the Law on the State Enterprise (Brown, The "
            "Gorbachev Factor, 1996; Miller, The Struggle to Save the Soviet Economy, 2016). "
            "Part crisis: undertaken against the stagnation of the economy."
        ),
    )
    ussr.action(
        "accept_reductions",
        guard={
            "offer": V.offer >= "reductions",
            "regime": V.oversight == "ntm",
            "new_thinking": V.perestroika,
        },
        effect=[*oversight_to("on_site"), raise_to("arms", "reduced")],
        source=(
            "The INF Treaty signed 8 Dec 1987, eliminating intermediate-range missiles with "
            "on-site inspection, after Gorbachev's acceptance of intrusive verification (the "
            "Stockholm document of 19 Sep 1986) and of the zero option (28 Feb 1987); START "
            "signed 31 Jul 1991 (Hoffman, The Dead Hand, 2009; Garthoff, The Great Transition, "
            "1994). Part new_thinking: the acceptance came with Gorbachev's reform."
        ),
    )
    ussr.action(
        "withdraw_afghanistan",
        guard={"level": V.afghan == "war"},
        effect=Set("afghan", "withdrawn"),
        source=(
            "The Politburo's decision of 13 Nov 1986 to withdraw within two years and the "
            "Geneva Accords of 14 Apr 1988; withdrawal from 15 May 1988, completed 15 Feb 1989 "
            "(the Politburo record of 13 Nov 1986, CWIHP; Kalinovsky, A Long Goodbye, 2011)."
        ),
    )
    ussr.action(
        "dissolve",
        guard={"released": V.bloc_USSR == "released", "legitimacy": V.legit_USSR == "failing"},
        effect=Set("bloc_USSR", "dissolved"),
        source=(
            "The dissolution of the Warsaw Pact's military structure (25 Feb 1991) and of the "
            "Pact (1 Jul 1991), and of the Soviet Union (the Belovezha Accords of 8 Dec 1991, "
            "Gorbachev's resignation 25 Dec 1991) (Kotkin, Armageddon Averted, 2001; Zubok, A "
            "Failed Empire, 2007)."
        ),
    )
    ussr.action(
        "strike_china",
        guard={
            "confrontation": V.esc_sino == "clash",
            "targets": V.tick >= tick_of(1965),
            "no_us_link": V.align_PRC != "us_aligned",
        },
        effect=Bump("esc_sino", 1),
        source=(
            "The Soviet soundings of Aug 1969 on an American reaction to a strike on Chinese "
            "nuclear installations (Stelmakh to Davies, 18 Aug 1969; Kissinger, White House "
            "Years) and the American signal of 5 Sep 1969 (Richardson) that the United States "
            "would not be indifferent (Goldstein, 'Return to Zhenbao Island', in Ross and Jiang "
            "(eds.), Re-examining the Cold War, 2001). Part targets: the Lop Nur installations "
            "after the Chinese test of 16 Oct 1964; part no_us_link: the strike was not "
            "considered once Beijing and Washington were aligned."
        ),
    )

    # -- PRC (a principal from 1969; Nature's in the scripted build) -------------------------
    prc_act(
        "border_clash",
        guard=prc_guard({"split": V.align_PRC == "split", "level": V.esc_sino == "peace"}),
        effect=Bump("esc_sino", 1),
        source=(
            "The Chinese ambush on Zhenbao (Damansky) Island, 2 Mar 1969, and the Soviet "
            "response of 15 Mar 1969, with the clash at Tielieketi (Xinjiang) of 13 Aug 1969 "
            "(Yang Kuisong, 'The Sino-Soviet Border Clash of 1969', Cold War History 2000)."
        ),
    )
    prc_act(
        "rapprochement",
        guard=prc_guard({"opening": V.china_opening, "threat": V.esc_sino == "clash"}),
        effect=raise_to("align_PRC", "us_aligned"),
        source=(
            "Mao's acceptance of the American opening against the Soviet threat (the four "
            "marshals' report of Jul to Sep 1969; Nixon's visit 21 to 28 Feb 1972 and the "
            "Shanghai Communique of 28 Feb 1972) (Chen Jian, Mao's China and the Cold War, "
            "2001; FRUS 1969-76 vol. XVII)."
        ),
    )
    prc_act(
        "normalize",
        guard=prc_guard({"clash": V.esc_sino == "clash", "obstacles": V.afghan == "withdrawn"}),
        effect=Bump("esc_sino", -1),
        source=(
            "Deng's normalization with the USSR at Gorbachev's Beijing visit of 15 to 18 May "
            "1989, once the 'three obstacles' (Afghanistan, the Vietnamese in Cambodia, the "
            "troops on the border) were being removed (Gorbachev's Vladivostok speech of 28 "
            "Jul 1986) (Lüthi 2008; Westad, The Cold War, 2017). Part obstacles: the Soviet "
            "withdrawal from Afghanistan."
        ),
    )

    # -- Nature: assessments and beliefs -----------------------------------------------------
    nature.event(
        "nsc68",
        guard={"level": V.belief_USA_USSR == "opportunist", "soviet_bomb": V.nuke_USSR >= "few"},
        effect=Set("belief_USA_USSR", "expansionist"),
        source=(
            "NSC-68 (7 Apr 1950, approved as NSC 68/2 on 30 Sep 1950): the Kremlin's 'design' "
            "of world domination, written after the Soviet bomb and the fall of China (FRUS "
            "1950 vol. I; Gaddis, Strategies of Containment)."
        ),
    )
    nature.event(
        "new_look",
        guard={"level": V.belief_USA_USSR == "expansionist"},
        effect=Set("belief_USA_USSR", "opportunist"),
        source=(
            "NSC 162/2 (30 Oct 1953): the USSR will not deliberately initiate general war but "
            "will exploit opportunities short of it (FRUS 1952-54 vol. II; Gaddis, Strategies "
            "of Containment)."
        ),
    )
    nature.event(
        "missile_gap",
        guard={"blind": V.intel_USA != "overhead", "soviet_force": V.nuke_USSR == "few"},
        effect=Set("belief_force_USA", "survivable"),
        source=(
            "The missile-gap estimates after the Soviet ICBM test of 21 Aug 1957 and Sputnik "
            "(4 Oct 1957): the Gaither report (7 Nov 1957) and NIE 11-10-57 (10 Dec 1957), "
            "projecting a Soviet ICBM force able to threaten SAC by 1959 to 1961 (Preble 2004; "
            "Prados, The Soviet Estimate, 1982). Part blind: before satellite coverage."
        ),
    )
    nature.event(
        "estimate_revised",
        guard={"overhead": V.intel_USA == "overhead", "gap": V.belief_force_USA > V.nuke_USSR},
        effect=Set("belief_force_USA", V.nuke_USSR),
        source=(
            "NIE 11-8/1-61 (21 Sep 1961) cutting the estimated Soviet ICBM force to 10 to 25 "
            "launchers on the CORONA photography, and Gilpatric's speech of 21 Oct 1961 "
            "(Prados 1982; Ruffner (ed.), CORONA, 1995)."
        ),
    )
    nature.event(
        "war_scare",
        guard={"level": V.belief_USSR_USA == "hostile", "us_buildup": V.buildup},
        effect=Set("belief_USSR_USA", "first_strike_intent"),
        source=(
            "The Soviet reading of American preparations for a first strike: Andropov's "
            "launch of RYAN at the KGB conference of May 1981 and the KGB's 'permanent "
            "operational assignment' to residencies (Feb 1983) after the Reagan buildup "
            "(Andrew and Gordievsky (eds.) 1991; PFIAB 1990; Jones 2016)."
        ),
    )
    nature.event(
        "reassurance",
        guard={"level": V.belief_USSR_USA == "first_strike_intent"},
        effect=Set("belief_USSR_USA", "hostile"),
        source=(
            "The receding of the war scare: Reagan's speech of 16 Jan 1984, the Geneva summit "
            "of 19 to 21 Nov 1985 ('a nuclear war cannot be won and must never be fought') "
            "(Fischer 1997; Jones 2016)."
        ),
    )
    nature.event(
        "new_thinking",
        guard={"level": V.belief_USSR_USA == "hostile", "reform": V.perestroika},
        effect=Set("belief_USSR_USA", "status_quo"),
        source=(
            "Soviet 'new thinking': the Warsaw Pact's defensive doctrine of 29 May 1987 and "
            "Gorbachev's and Shevardnadze's reading of the United States as no threat of "
            "attack (English, Russia and the Idea of the West, 2000; Brown 1996)."
        ),
    )

    # -- Nature: the Soviet economy, polity and bloc -----------------------------------------
    nature.event(
        "slowdown",
        guard={"level": V.econ_USSR == "growing", "burden": V.nuke_USSR >= "survivable"},
        effect=Set("econ_USSR", "stagnant"),
        source=(
            "The 'era of stagnation': Soviet growth falling from the late 1960s to under 2 "
            "percent a year in the late 1970s on post-1991 revisions, with the strategic "
            "buildup to parity absorbing capital (Easterly and Fischer, 'The Soviet Economic "
            "Decline', World Bank Economic Review 1995; Kotkin 2001; the dates of the "
            "revised series not verified). Part burden: the defence burden of parity."
        ),
    )
    nature.event(
        "decline",
        guard={
            "level": V.econ_USSR == "stagnant",
            "burden": (V.afghan == "war") | (V.arms == "race") | V.buildup,
        },
        effect=Set("econ_USSR", "declining"),
        source=(
            "The fall of Soviet output growth to near zero in the 1980s with the collapse of "
            "oil prices from late 1985 (Saudi policy of Aug 1985), grain imports and the "
            "burdens of the war in Afghanistan and the arms race (Gaidar, Collapse of an "
            "Empire, 2007; Miller 2016). Part burden: the war, an uncapped arms race or the "
            "American buildup."
        ),
    )
    nature.event(
        "collapse",
        guard={"level": V.econ_USSR == "declining", "reform": V.perestroika},
        effect=Set("econ_USSR", "failing"),
        source=(
            "The fiscal and supply collapse of 1989 to 1991 after the Law on the State "
            "Enterprise (1987, in force 1988) and the cooperatives law (May 1988): output "
            "falling from 1990, the budget deficit monetized, the retail market emptied "
            "(Miller 2016; Kotkin 2001)."
        ),
    )
    nature.event(
        "delegitimation",
        guard={"level": V.legit_USSR == "contested", "economy": V.econ_USSR >= "declining"},
        effect=Set("legit_USSR", "failing"),
        source=(
            "The loss of the party's monopoly and of the centre's authority in 1990: Article "
            "6 repealed (Feb to Mar 1990), Lithuania's declaration of independence (11 Mar "
            "1990), the Russian declaration of sovereignty (12 Jun 1990) (Brown 2009; Kotkin "
            "2001)."
        ),
    )
    nature.event(
        "opposition",
        guard={"level": V.bloc_USSR == "intact", "grievance": V.econ_USSR >= "stagnant"},
        effect=Set("bloc_USSR", "contested"),
        source=(
            "An opposition holding its ground across a year in an East European state: "
            "Solidarity, legal from the Gdansk agreement of 31 Aug 1980; the Polish strikes of "
            "Apr to Aug 1988 and the Hungarian party's reform of May 1988 (Kramer 1999; Kotkin, "
            "Uncivil Society, 2009). Part grievance: both rose on economic failure."
        ),
    )
    nature.event(
        "martial_law",
        guard={"contested": V.bloc_USSR == "contested", "backing": V.legit_USSR == "secure"},
        effect=Set("bloc_USSR", "intact"),
        source=(
            "Jaruzelski's martial law of 13 Dec 1981 under Soviet pressure (Kulikov's visits; "
            "the Politburo of 10 Dec 1981) (Kramer 1999; Paczkowski and Byrne (eds.), From "
            "Solidarity to Martial Law, 2007). Part backing: a Soviet leadership able to back "
            "it."
        ),
    )
    nature.event(
        "revolution",
        guard={
            "contested": V.bloc_USSR == "contested",
            "no_intervention": (V.afghan == "war") | (V.legit_USSR != "secure"),
        },
        effect=Set("bloc_USSR", "released"),
        source=(
            "The East European revolutions of 1989: the Polish elections of 4 Jun 1989, the "
            "opening of the Berlin Wall (9 Nov), the Velvet Revolution and Romania, with no "
            "Soviet intervention after Gorbachev's UN speech of 7 Dec 1988 (Kramer, 'The "
            "Collapse of East European Communism', Journal of Cold War Studies 2003; Kotkin "
            "2009). Part no_intervention: when Moscow lacked the capacity or the will of "
            "USSR.intervene."
        ),
    )

    # -- Nature: accidents (ontology section 5) ----------------------------------------------
    nature.event(
        "accident",
        guard={"alert": V.esc >= "crisis", "below": V.esc < "tactical_nuclear"},
        effect=[Bump("esc", 3), Set("accidental", True)],
        source=(
            "Accidents and false warnings under raised alert that could have led to nuclear "
            "use: the incidents of the Cuban crisis (the Malmstrom and Vandenberg launches, "
            "the U-2 over Chukotka on 27 Oct 1962) and of the 1973 alert (Sagan, The Limits of "
            "Safety, 1993)."
        ),
    )

    # -- invariants and endings (ontology section 9) -----------------------------------------
    sino_war = (V.esc_sino == "war") if prc_principal else FALSE
    both_or_neither = ((V.nuke_USA >= "survivable") & (V.nuke_USSR >= "survivable")) | (
        (V.nuke_USA < "survivable") & (V.nuke_USSR < "survivable")
    )
    no_war = (V.esc < "conventional") & ~sino_war
    blocs_intact = V.bloc_USSR <= "contested"
    general_war = (V.esc >= "tactical_nuclear") | sino_war
    m.invariant("balance_cw", both_or_neither & no_war & blocs_intact)
    m.invariant("no_war", no_war)
    m.invariant("no_general_war", ~general_war)
    m.invariant("bloc_intact", blocs_intact)

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


model = build()
