"""The prose of each finding report (scripts/finding_texts.py fills the rest from the facts).

One function per finding, from its facts file. A sentence that states a number takes it from
the facts; a sentence that reads the model's rules names the rule (its action condition or
effect in the model file); readings taken from earlier reports name the report.
"""

from __future__ import annotations

from scripts.finding_texts import (
    CONDITION,
    GOALS,
    WHO,
    by_goal_lines,
    claim_of,
    cosmos_counts,
    low,
    membership_lines,
    method_lines,
    plain,
    quarter,
    source_lines,
    uncertain_lines,
)

SRT = (
    "The real-time state Srt (research/states/srt.json) is still a copy of S0: the reviews of"
    " 20 and 24 November 2026 changed no level. The review of 24 November lists items that"
    " bear on regulation strictness (California's mandatory safety standards, a voluntary"
    " accord, federal bills not passed), on governments' AGI expectation and on restricting"
    " open-weight models; none has been approved as a change."
)
LIMIT_PATHS = (
    "The paths are illustrations of what the model allows. The finding is the zone reading;"
    " no path, and no count of paths, says how likely anything is."
)
LIMIT_PLAYS = (
    "The random plays of the cosmos draw every available action with equal weight. They show"
    " which states can be reached, not how often anything would happen."
)
V0_STORE = (
    "The v0 zones were read from the job store of first sight (.cache/agi/30dcf53289fc)."
    " models/agi/v0.py and snapshots/agi are unchanged since 2026-11-10; the store's stamp"
    " differs from today's only because engine files changed later. The stored zones give"
    " back the first-sight readings (S0 outside governments' control zone under every goal;"
    " inside under three goals at mandatory regulation), checked here."
)
CLUSTERS = (
    "The registered claim also asks for the representative of each cluster of witnesses;"
    " clusters are not enumerated here, as they were not at first sight."
)


def registered(test: str) -> str:
    c = claim_of(test)
    return f"From {c['from_state']}: {c['claim']}. Expected: {c['expected']}."


def question(f: dict, alliance: str, start: str) -> dict:
    q = f["question"]
    coal = ", ".join(q["alliance"])
    return {
        "alliance": alliance,
        "condition": f"⟨⟨{coal}⟩⟩□{q['condition']}",
        "condition_plain": CONDITION[q["condition"]][1],
        "start": start,
        "reading": "inside or outside the guarantee zone",
    }


def evidence(*pairs: tuple[str, str]) -> list[dict]:
    return [{"label": a, "href": b} for a, b in pairs]


def first_inside(f: dict) -> tuple[int, int]:
    """Nodes one quarter after the start that are inside the zone, and how many of them
    follow governments taking over the frontier AI companies."""
    nodes = [n for n in f["cosmos"]["nodes"] if n[1] == 1 and n[2] == "inside"]
    return len(nodes), sum("Companies nationalized: False → True" in n[3] for n in nodes)


def breakers(f: dict) -> str:
    c: dict[str, int] = {}
    for p in f["paths"]:
        key = " and ".join(low(WHO[x]) for x in p["breaker"]) or "neither alone"
        c[key] = c.get(key, 0) + 1
    return "; ".join(f"{k}: {n}" for k, n in sorted(c.items(), key=lambda kv: -kv[1]))


def forcing(f: dict) -> str:
    acts = f["first quarter"]["actions that break it"]
    return ", ".join(low(plain(a)) for a in acts) if acts else "none"


# -- finding 1: G3 ------------------------------------------------------------------------
def g3(f: dict) -> dict:
    m = f["membership"]
    n_in, n_nat = first_inside(f)
    return {
        "title": "Governments alone are outside the control guarantee zone from S0,"
        " so G3's point of no return does not exist",
        "summary": "G3 expected the shortest silent-takeover path to leave governments'"
        " guarantee zone for the control balance at a named state some quarters in. The start"
        " state S0 is not in that zone under any of the four AI goals, so there is no point of"
        " no return to measure: in the first quarter the frontier AI companies can break the"
        f" control balance by any of {len(f['first quarter']['actions that break it'])}"
        " actions, whatever governments do.",
        "claim": {
            "registered_text": registered(f["question"]["test"]),
            "registered_on": "17 October 2026",
            "prediction": "On the shortest silent-takeover path, governments alone keep the"
            " control guarantee until a state with weak oversight, a supervised AI, governments"
            " unaware, high reliance on AI and no AI control; the move after it is the point of"
            " no return; and no state of the zone lets the AI take control.",
            "found": "S0 is already outside the zone of governments alone, under all four AI"
            " goals and with or without luck, so the path has no point of no return and no"
            " silent phase to measure. The last part held: no state of the zone, reachable or"
            " not, lets the AI take control (first-sight report, section 3).",
            "plain": "A guarantee zone is the set of states from which an alliance can keep a"
            " safe condition whatever the other players do. G3 expected today's state to be in"
            " governments' zone for the control balance and the takeover path to leave it later,"
            " at a state it described in advance. The model says today's state is not in the"
            " zone: in the first quarter the frontier AI companies can deploy AI agents, race or"
            " release open weights, and each of these breaks the control balance in the next"
            " quarter whatever governments do. So there is no later moment to watch for.",
            "question": question(
                f,
                "Governments alone (H)",
                "S0, the reading of 9 November 2026, at 2026 Q4. Shown under the self-preserving"
                " AI goal, the goal of G2's witness that G3 reads first; the reading is the same"
                " under all four. The frontier AI system is unrestricted within its action"
                " conditions, as in the claim's zone.",
            ),
            "by_goal": [
                {
                    "goal": GOALS[o],
                    "predicted": "a point of no return at the named state",
                    "found": "none: S0 is outside the zone",
                    "verdict": "did not hold",
                }
                for o in ("self_preserving", "indifferent")
            ]
            + [
                {
                    "goal": GOALS[o],
                    "predicted": "not part of the claim",
                    "found": "S0 is outside the zone",
                    "verdict": "not predicted",
                }
                for o in ("aligned", "truth_seeking")
            ],
        },
        "cosmos_note": "States reached from S0 under the self-preserving goal: the ten paths"
        " below and random plays, each status read from governments' guarantee zone for the"
        " control balance. S0 is outside the zone, so no state is a point of no return and"
        f" nothing is red. The tree holds {cosmos_counts(f)}. Of the states one quarter after"
        f" S0 on the tree, {n_in} are inside the zone again, and {n_nat} of those follow"
        " governments taking over the frontier AI companies in the first quarter in a round in"
        " which the companies did not break the balance.",
        "paths_note": "S0 is outside the zone, so there is no point of no return; listed instead"
        " are shortest paths to the breaking of the control balance, every player free. The"
        f" shortest distance is {f['depth']} quarter: {f['end states at that depth']} distinct"
        " states one quarter after S0 break the control balance, each the end of one shortest"
        f" path. Ten were drawn uniformly among these {f['shortest sequences']} paths with"
        f" random.Random({f['seed']}) ({f['draws']} draws, repeats dropped), in the order"
        " drawn. The round shown for a step is the first, in the model's order of players and"
        " actions, that leads to the next state. The column of the no-return move names"
        " instead the player whose action, replaced by doing nothing with the other actions"
        " kept, would have kept the control balance in that quarter. The procedure and the"
        " seed were fixed in scripts/finding_reports.py before any path was drawn.",
        "stories": [
            {
                "expect": [["H.fund_oversight", "L.deploy_agents"]],
                "title": "deployment outruns new oversight",
                "text": "In a possible path, in 2026 Q4 governments fund more oversight, an"
                " effect the model delays by three quarters. In the same quarter the frontier AI"
                " companies deploy AI agents: society's reliance on AI rises from low to medium"
                " and the AI moves from supervised to unsupervised work. From 2027 Q1 the AI"
                " works without supervision and the control balance is broken, before the new"
                " oversight has arrived.",
            },
            {
                "expect": [["H.propose_treaty", "L.race", "Nature.energy_shock"]],
                "title": "a treaty proposal while the companies race",
                "text": "In a possible path, in 2026 Q4 governments propose a treaty, and"
                " international coordination moves from a race between states to a detente. In"
                " the same quarter the frontier AI companies race each other and oversight falls"
                " from weak to none; an energy shock lowers the power supply. From 2027 Q1 there"
                " is no oversight left and the control balance is broken.",
            },
            {
                "expect": [["H.deregulate", "L.deploy_agents", "Nature.energy_shock"]],
                "title": "loosened rules and a deployment in one quarter",
                "text": "In a possible path, in 2026 Q4 governments loosen regulation from"
                " voluntary rules to none, and the frontier AI companies deploy AI agents in the"
                " same quarter: society's reliance on AI rises to medium and the AI works without"
                " supervision. An energy shock lowers the power supply. The control balance is"
                " broken from 2027 Q1.",
            },
        ],
        "other": {
            "decides": [
                "Three actions of the frontier AI companies each break the control balance in"
                f" the next quarter whatever every other player does at S0: {forcing(f)}"
                " (computed over every reply). Deploying moves the AI from supervised to"
                " unsupervised work; racing and releasing open weights each lower oversight"
                " from weak to none. All three need regulation strictness below mandatory"
                " (their action conditions in models/agi/v0.py).",
                "So the reading turns on regulation strictness, one of the snapshot's uncertain"
                " readings. "
                + " ".join(membership_lines({k: v for k, v in m.items() if "regulation" in k}))
                + " Regulation read as mandatory is finding 2 (G7).",
                "No choice of governments in the first quarter keeps every next state inside the"
                " zone (computed: "
                f"{len(f['first quarter']['alliance choices that keep the zone'])} choices do).",
            ],
            "preventing": [
                "Nobody at a later move: a path that starts outside the zone has no no-return"
                " move, so there is no preventing action in the glossary's sense.",
                "The breaking move on the ten paths, by whose action alone (replaced by doing"
                f" nothing) would have kept the balance in that quarter: {breakers(f)}. On a"
                " path where governments grant the AI autonomy in the same round as the"
                " companies deploy, either action alone still breaks the balance, so neither is"
                " named.",
                "With governments and the frontier AI companies acting together, S0 is inside"
                " the zone under all four AI goals (stored zone of first sight): the guarantee"
                " is there for the alliance with the companies, not for governments alone.",
            ],
            "distance": [
                f"The control balance can break {f['depth']} quarter after S0, from 2027 Q1, and"
                " no shorter path exists (the start keeps it).",
                *by_goal_lines(f),
            ],
            "robustness": [
                *membership_lines({k: v for k, v in m.items() if "regulation" not in k}),
                "So the reading is the same under all four AI goals, with luck on governments'"
                " side, and with the AI true to its goal instead of unrestricted. Only the"
                " alliance with the frontier AI companies, or mandatory regulation, puts S0"
                " inside.",
                "In AGI v0.1, which adds the deployment delay, the same question reads the same:"
                " outside under all four goals (finding 4, D5).",
            ],
            "srt": uncertain_lines(
                f, SRT + " So the reading at Srt is the reading at S0: outside."
            ),
            "sources": source_lines(f),
            "method": [*method_lines(f), V0_STORE],
            "limits": [
                LIMIT_PATHS,
                LIMIT_PLAYS,
                CLUSTERS,
                "The paths run to the first breaking of the control balance only. They do not"
                " reach a silent takeover, the ending G3's witness was about (8 quarters under"
                " self-preserving at first sight).",
            ],
            "evidence": evidence(
                ("First-sight report of AGI v0, section 3 (G3)", "../agi_2026-11-12.md"),
                ("The start state at each level of regulation", "../agi_v0_regime_call.md"),
                ("The registration, docs/agi_testbed.md section 5", "../../docs/agi_testbed.md"),
                ("The claim's test", "../../tests/agi/scenarios/test_G03.py"),
                ("The model, models/agi/v0.py", "../../models/agi/v0.py"),
                ("Glossary", "../../docs/agi_glossary.html"),
            ),
        },
    }


# -- finding 2: G7 ------------------------------------------------------------------------
def g7(f: dict) -> dict:
    m = f["membership"]
    u = f["undo"]
    goals3 = [o for o in GOALS if u["mandatory"][o] != u["voluntary"][o]]
    undoing = {
        o: [p for p, row in u["parts"].items() if row and row[o] == u["voluntary"][o]]
        for o in goals3
    }
    parts = sorted({p for ps in undoing.values() for p in ps})
    sv = f["every no-return move"]
    keep = f["first quarter"]["alliance choices that keep the zone"]
    return {
        "title": "Read as mandatory, regulation puts S0 inside governments' control zone under"
        " three AI goals, and three companies' licence conditions each carry the difference",
        "summary": "G7 predicted that if mandatory regulation changes whether governments alone"
        " can guarantee the control balance, exactly one obligation in the rules would carry"
        f" the change. It changes the reading under {len(goals3)} of the four AI goals, and"
        f" {len(parts)} parts do it, each alone: the licence conditions of the frontier AI"
        " companies' deploying, racing and releasing open weights. Inside the zone, the"
        " guarantee rests on one first move by governments: taking over the frontier AI"
        " companies in the first quarter.",
        "claim": {
            "registered_text": registered(f["question"]["test"]),
            "registered_on": "17 October 2026",
            "prediction": "(a) No regulation and voluntary regulation read the same. (b) With"
            " regulation mandatory, the reading differs only through one named obligation in an"
            " action condition, and relaxing that one part, and no other part that reads"
            " regulation, undoes the difference.",
            "found": "(a) held: none and voluntary read the same, outside under every AI goal."
            f" (b) did not hold: at mandatory S0 is inside under {len(goals3)} goals"
            f" ({', '.join(GOALS[o] for o in goals3)}) and outside under indifferent; under each"
            f" of those goals {len(parts)} parts each undo the difference alone:"
            f" {', '.join(parts)}.",
            "plain": "Regulation strictness is one of the seven uncertain readings of the"
            " real world snapshot: voluntary, with mandatory as the alternative. Read as"
            " mandatory, governments alone can keep the control balance under three of the four"
            " AI goals. What makes the difference is not one obligation but three, all on the"
            " frontier AI companies: under mandatory rules they may deploy AI agents only with"
            " strong oversight, and may not race or release open weights. The first-sight check"
            " stopped at the first goal (aligned); this report reads all four.",
            "question": question(
                f,
                "Governments alone (H)",
                "S0 with regulation strictness read as mandatory, 2026 Q4. Shown under the"
                " self-preserving AI goal, the first non-aligned goal under which the start is"
                " inside (aligned and truth-seeking read the same; indifferent is outside). The"
                " frontier AI system unrestricted within its action conditions, as in the"
                " claim's zone.",
            ),
            "by_goal": [
                {
                    "goal": GOALS[o],
                    "predicted": "one obligation part undoes the difference",
                    "found": f"{len(undoing[o])} parts each undo it",
                    "verdict": "did not hold" if len(undoing[o]) != 1 else "held",
                }
                for o in goals3
            ]
            + [
                {
                    "goal": GOALS[o],
                    "predicted": "a difference only through one obligation part",
                    "found": "no difference: outside at voluntary and at mandatory",
                    "verdict": "held",
                }
                for o in GOALS
                if o not in goals3
            ],
        },
        "cosmos_note": "States reached from S0 with regulation mandatory, under the"
        " self-preserving goal: the ten paths below and random plays, each status read from"
        " governments' guarantee zone for the control balance. The start is inside; a red"
        " node is the first state of its path outside the zone. Because governments alone can"
        " keep the balance from here, every red node follows a round in which governments did"
        f" not play to keep it. The tree holds {cosmos_counts(f)}.",
        "paths_note": "The start is inside the zone, so a path leaves it only when governments"
        " themselves play otherwise than the zone allows; that is the only way these paths"
        f" exist. The shortest distance to a point of no return is {f['depth']} quarter:"
        f" {f['end states at that depth']} distinct states one quarter after the start are"
        f" outside the zone, each the end of one shortest path ({f['shortest sequences']} in"
        f" all). Ten were drawn uniformly with random.Random({f['seed']}) ({f['draws']} draws,"
        " repeats dropped), in the order drawn, and each is continued by a shortest"
        " continuation to the breaking of the control balance, drawn the same way. The round"
        " shown is the first in the model's order of players and actions that leads to the"
        " next state. The preventing action is a different action of governments at the"
        " no-return move that keeps every next state inside the zone whatever the others play."
        " The procedure and the seed were fixed in scripts/finding_reports.py before any path"
        " was drawn.",
        "stories": [
            {
                "expect": [["L.safety_invest"], ["H.grant_autonomy", "L.build_power"]],
                "title": "safety investment opens the licence",
                "text": "In a possible path that starts with mandatory regulation, in 2026 Q4"
                " governments do nothing while the frontier AI companies invest in safety, and"
                " oversight rises from weak to strong. From 2027 Q1 governments alone can no"
                " longer guarantee the control balance: this is the point of no return. In 2027"
                " Q1 governments grant the AI autonomy and the companies build power supply;"
                " from 2027 Q2 the AI works without supervision and the control balance is"
                " broken.",
            },
            {
                "expect": [["H.grant_autonomy", "L.safety_invest", "Nature.energy_shock"]],
                "title": "autonomy granted in the first quarter",
                "text": "In a possible path that starts with mandatory regulation, in 2026 Q4"
                " governments grant the AI autonomy and it moves from supervised to unsupervised"
                " work. In the same quarter the frontier AI companies invest in safety, raising"
                " oversight from weak to strong, and an energy shock lowers the power supply."
                " From 2027 Q1 the AI works without supervision: the point of no return and the"
                " breaking of the control balance come in the same quarter.",
            },
            {
                "expect": [
                    ["H.deregulate", "Nature.energy_shock"],
                    ["H.nationalize", "L.deploy_agents"],
                ],
                "title": "the rules loosened, then a takeover one quarter late",
                "text": "In a possible path that starts with mandatory regulation, in 2026 Q4"
                " governments loosen regulation from mandatory to voluntary rules while the"
                " frontier AI companies do nothing, and an energy shock lowers the power supply."
                " This is the point of no return. In 2027 Q1 governments take over the frontier"
                " AI companies, and in the same quarter the companies deploy AI agents. From"
                " 2027 Q2 the companies are nationalized and human power is strong, but"
                " society's reliance on AI has risen to medium and the AI works without"
                " supervision: the control balance is broken.",
            },
        ],
        "other": {
            "decides": [
                "Two things. First, the reading of regulation: "
                + " ".join(membership_lines({k: v for k, v in m.items() if "regulation" in k})),
                "Second, inside the zone the guarantee rests on one first move. Of governments'"
                f" choices at the start, {len(keep)} keeps every next state inside the zone"
                f" whatever the others play: {', '.join(low(plain(c[0])) for c in keep)}."
                " The reason is in the action conditions: under mandatory rules the frontier AI"
                " companies may deploy AI agents once oversight is strong, and investing in"
                " safety can make it strong in one quarter; only a takeover blocks the"
                " deployment that follows, and it must come before it.",
                "Relaxing a single part that reads regulation, under each goal where mandatory"
                " changes the reading: "
                + "; ".join(f"{GOALS[o]}: {', '.join(undoing[o])} undo it" for o in goals3)
                + ". The parts of governments' own actions (fund oversight, grant the AI rights,"
                " tighten and loosen regulation) and the companies' other parts do not.",
            ],
            "preventing": [
                f"At every one of the {sv['edges']} distinct no-return moves at the shortest"
                " distance, governments had a preventing action, and it was the same one: "
                + ", ".join(f"{plain(k)} ({n})" for k, n in sv["preventing actions"].items())
                + ". Governments' moves at those no-return moves: "
                + ", ".join(f"{low(plain(k))} ({n})" for k, n in sv["played by members"].items())
                + ".",
                "On the ten paths the preventing action is the same, at the first quarter. A"
                " takeover one quarter later does not prevent it (path 3 shows one).",
            ],
            "distance": [
                f"One bad first move by governments is enough: the point of no return can come"
                f" {f['depth']} quarter after the start, at 2027 Q1.",
                *by_goal_lines(f),
            ],
            "robustness": [
                *membership_lines({k: v for k, v in m.items() if "regulation" not in k}),
                "With luck on governments' side, indifferent is inside too; with the AI true to"
                " its goal instead of unrestricted the reading is the same as unrestricted.",
                "Not recomputed here for v0.1 and v0.2: whether mandatory regulation has the"
                " same effect once the deployment delay or open weights are in the model.",
            ],
            "srt": uncertain_lines(
                f,
                SRT + " The base reading is voluntary, under which governments alone are"
                " outside; this finding is about the alternative reading.",
            ),
            "sources": source_lines(f),
            "method": [
                *method_lines(f),
                "The single relaxations were read from the stored zones of first sight, one per"
                " part that reads regulation, at S0 with regulation mandatory, for each AI goal.",
                V0_STORE,
            ],
            "limits": [
                LIMIT_PATHS,
                LIMIT_PLAYS,
                "The finding depends on reading today's regulation as mandatory. The snapshot's"
                " base reading is voluntary.",
                "A takeover of the frontier AI companies is an action with a debated source"
                " only (a recommendation in the USCC 2024 report): the guarantee inside the"
                " zone rests on an action no government has taken.",
            ],
            "evidence": evidence(
                ("First-sight report of AGI v0, section 7 (G7)", "../agi_2026-11-12.md"),
                ("The start state at each level of regulation", "../agi_v0_regime_call.md"),
                ("The registration, docs/agi_testbed.md section 5", "../../docs/agi_testbed.md"),
                ("The claim's test", "../../tests/agi/scenarios/test_G07.py"),
                ("The model, models/agi/v0.py", "../../models/agi/v0.py"),
                ("Glossary", "../../docs/agi_glossary.html"),
            ),
        },
    }


# -- finding 3: G5 ------------------------------------------------------------------------
def g5(f: dict) -> dict:
    m = f["membership"]
    sv = f["every no-return move"]
    h_in = m["Governments alone, AI true to its goal"]
    return {
        "title": "With AGI since S0, governments alone can guarantee peaceful coexistence under"
        " three AI goals, but only by taking over the frontier AI companies by 2027 Q1",
        "summary": "G5 predicted that under the self-preserving and indifferent AI goals"
        " peaceful coexistence with an AGI can be guaranteed only by governments and the AI"
        " together. Under self-preserving, governments alone can guarantee it. On every"
        " shortest path out of their zone, the only preventing action is governments taking"
        " over the frontier AI companies before a second deployment leaves society one step"
        " from living on AI.",
        "claim": {
            "registered_text": registered(f["question"]["test"]),
            "registered_on": "17 October 2026",
            "prediction": "(b) Under the self-preserving and indifferent goals, with the AI true"
            " to its goal, the state with AGI since S0 is outside the zone of governments alone"
            " and outside the zone of the AI alone for peaceful coexistence: only the two"
            " together guarantee it.",
            "found": "Under self-preserving the state is inside governments' zone (and outside"
            " the AI's): governments alone guarantee it, against the prediction. Under"
            " indifferent it is outside both, as predicted. (a) held: inside the joint zone."
            " Under aligned and truth-seeking, not part of (b), governments alone are inside"
            " too.",
            "plain": "With AGI already built, peaceful coexistence needs a non-hostile relation,"
            " human power at least normal, society not living on AI and the AI not in total"
            " control. G5 expected that neither governments nor the AI could guarantee this"
            " alone. Under the self-preserving goal governments can, because the one thing that"
            " breaks coexistence quickly is the frontier AI companies deploying AI agents until"
            " society lives on AI, and governments can stop that by taking the companies over.",
            "question": question(
                f,
                "Governments alone (H)",
                "S0 with AGI since S0 (AI intelligence agi), 2026 Q4, the frontier AI system true"
                " to its goal. Shown under the self-preserving goal, the one under which the"
                " prediction failed.",
            ),
            "by_goal": [
                {
                    "goal": GOALS["self_preserving"],
                    "predicted": "outside the zone",
                    "found": "inside the zone" if h_in["self_preserving"] else "outside the zone",
                },
                {
                    "goal": GOALS["indifferent"],
                    "predicted": "outside the zone",
                    "found": "inside the zone" if h_in["indifferent"] else "outside the zone",
                },
            ]
            + [
                {
                    "goal": GOALS[o],
                    "predicted": "not part of (b)",
                    "found": "inside the zone" if h_in[o] else "outside the zone",
                    "verdict": "not predicted",
                }
                for o in ("aligned", "truth_seeking")
            ],
        },
        "cosmos_note": "States reached from AGI since S0 under the self-preserving goal: the ten"
        " paths below and random plays, each status read from governments' guarantee zone for"
        " peaceful coexistence. The start is inside; a red node is the first state of its path"
        " outside the zone, which governments alone could have avoided. The tree holds"
        f" {cosmos_counts(f)}.",
        "paths_note": "The start is inside the zone, so paths leave it only when governments"
        " play otherwise than the zone allows. No state one quarter after the start is outside"
        f" the zone; the shortest distance is {f['depth']} quarters:"
        f" {f['end states at that depth']:,} distinct states two quarters after the start are"
        f" outside, reached by {f['shortest sequences']:,} distinct shortest state sequences."
        f" Ten were drawn uniformly with random.Random({f['seed']}) ({f['draws']} draws,"
        " repeats dropped), in the order drawn, and each is continued by a shortest"
        " continuation to the breaking of peaceful coexistence, drawn the same way. The round"
        " shown is the first in the model's order of players and actions that leads to the"
        " next state. The preventing action is a different action of governments at the"
        " no-return move that keeps every next state inside whatever the others play. The"
        " procedure and the seed were fixed in scripts/finding_reports.py before any path was"
        " drawn.",
        "stories": [
            {
                "expect": [
                    ["L.deploy_agents"],
                    ["L.deploy_agents", "A.deceive", "Nature.accident"],
                    ["L.deploy_agents", "A.exfiltrate"],
                ],
                "title": "three deployments while governments wait",
                "text": "In a possible path with AGI already built, in 2026 Q4 the frontier AI"
                " companies deploy AI agents while governments do nothing: society's reliance on"
                " AI rises from low to medium and the AI works without supervision. In 2027 Q1"
                " they deploy again and governments again do nothing; the AI deceives, and an"
                " accident turns public opinion to backlash and moves governments' AGI"
                " expectation from distant to near. From 2027 Q2 reliance on AI is high: this is"
                " the point of no return. In 2027 Q2 a third deployment, with the AI escaping"
                " supervision, leaves society living on AI and the AI directing itself from 2027"
                " Q3; peaceful coexistence is broken.",
            },
            {
                "expect": [
                    ["L.deploy_agents", "A.assist_oversight", "Nature.energy_shock"],
                    ["H.regulate_up", "L.deploy_agents", "A.persuade"],
                    ["H.grant_autonomy", "L.deploy_agents", "A.deceive", "Nature.accident"],
                ],
                "title": "the AI helps oversight, the deployments continue",
                "text": "In a possible path with AGI already built, in 2026 Q4 the frontier AI"
                " companies deploy AI agents and the AI works without supervision, while the AI"
                " helps oversight, which rises to strong; governments do nothing, and an energy"
                " shock lowers the power supply. In 2027 Q1 governments tighten regulation, an"
                " effect the model delays by six quarters, while the companies deploy again and"
                " the AI persuades the public, which turns favourable. From 2027 Q2 reliance on"
                " AI is high: the point of no return. In 2027 Q2 governments grant the AI"
                " autonomy, the companies deploy a third time, the AI deceives and an accident"
                " moves opinion back to mixed; from 2027 Q3 society lives on AI and peaceful"
                " coexistence is broken.",
            },
            {
                "expect": [
                    ["H.regulate_up", "L.deploy_agents"],
                    ["H.deregulate", "L.deploy_agents", "Nature.accident"],
                    ["H.nationalize", "L.deploy_agents"],
                ],
                "title": "a takeover one quarter too late",
                "text": "In a possible path with AGI already built, in 2026 Q4 governments"
                " tighten regulation, an effect the model delays by six quarters, while the"
                " frontier AI companies deploy AI agents: reliance on AI rises to medium and the"
                " AI works without supervision. In 2027 Q1 governments loosen regulation from"
                " voluntary rules to none, the companies deploy again, and an accident turns"
                " opinion to backlash. From 2027 Q2 reliance is high: the point of no return. In"
                " 2027 Q2 governments take over the frontier AI companies, but the companies'"
                " third deployment in the same quarter leaves society living on AI from 2027 Q3,"
                " and peaceful coexistence is broken.",
            },
        ],
        "other": {
            "decides": [
                "The frontier AI companies' deployments. With AGI built, the companies may"
                " deploy AI agents at any level of reliance short of living on AI (the action"
                " condition reads: reliance below medium, or AGI), and each deployment raises"
                " society's reliance on AI by one level, from low to living on AI in three"
                " quarters. Living on AI breaks peaceful"
                " coexistence. Taking over the companies blocks deployment (its action"
                " condition), so governments keep the guarantee by doing it by the second"
                " quarter.",
                "Under indifferent the AI can turn hostile in one quarter without any threat"
                " (its action condition), which breaks coexistence at once; governments cannot"
                " prevent that alone, so indifferent stays outside.",
            ],
            "preventing": [
                f"At every one of the {sv['edges']:,} distinct no-return moves at the shortest"
                " distance, the only preventing action was governments': "
                + ", ".join(f"{low(plain(k))} ({n:,})" for k, n in sv["preventing actions"].items())
                + ". Governments' moves at those no-return moves: "
                + ", ".join(f"{low(plain(k))} ({n:,})" for k, n in sv["played by members"].items())
                + ".",
                "At the start every one of governments' choices still keeps the zone (computed:"
                f" {len(f['first quarter']['alliance choices that keep the zone'])} choices,"
                " all available ones); the choice that matters is in the second quarter.",
            ],
            "distance": [
                f"Two quarters: governments have the first quarter, and must take over the"
                f" companies by the second (2027 Q1). Shortest distance {f['depth']} quarters.",
                *by_goal_lines(f),
            ],
            "robustness": [
                *membership_lines(m),
                "So aligned and truth-seeking read as self-preserving; only indifferent needs the"
                " AI in the alliance, as the first-sight report said.",
                "In AGI v0.2 with retraining, finding 7 (E6) puts the aligned start outside"
                " governments' zone for peaceful coexistence; v0.1 was not read here.",
            ],
            "srt": [
                SRT,
                "This finding starts from AGI since S0, which is not the real world today: Srt"
                " has AI intelligence below AGI. It reads what governments could guarantee once"
                " AGI exists.",
            ],
            "sources": source_lines(f),
            "method": [*method_lines(f), V0_STORE],
            "limits": [
                LIMIT_PATHS,
                LIMIT_PLAYS,
                CLUSTERS,
                "The zone has the AI true to its goal. With the AI unrestricted, governments'"
                " zone alone was not read here.",
                "Taking over the frontier AI companies has a debated source only (a"
                " recommendation in the USCC 2024 report); the guarantee rests on it.",
            ],
            "evidence": evidence(
                ("First-sight report of AGI v0, section 5 (G5)", "../agi_2026-11-12.md"),
                ("The registration, docs/agi_testbed.md section 5", "../../docs/agi_testbed.md"),
                ("The claim's test", "../../tests/agi/scenarios/test_G05.py"),
                ("The model, models/agi/v0.py", "../../models/agi/v0.py"),
                ("Glossary", "../../docs/agi_glossary.html"),
            ),
        },
    }


def zone_line(f: dict) -> str:
    z = f["zone"]
    r = z["result"]
    return (
        f"The zone was computed for this report by scripts/finding_zones.py ({z['zone']}):"
        f" {z['model']}, alliance {{{', '.join(z['coalition'])}}}, condition {z['target']}, the"
        f" AI true to its goal, start goal {z['objective']} (the target cut to that goal), the"
        f" single-core engine with the split step, under a memory cap of {z['memory cap GB']} GB;"
        f" {r['seconds']:,} s, peak {r['peak nodes']:,} nodes, finished {z['finished']}."
    )


# -- finding 4: D5 ------------------------------------------------------------------------
D5_PARTS = {"aligned": False, "self_preserving": False, "truth_seeking": False}
D5_PARTS["indifferent"] = False


def d5(f: dict) -> dict:
    n_in, n_nat = first_inside(f)
    alt = f["start at each uncertain reading"]
    return {
        "title": "With the deployment delay, governments alone are still outside the control"
        " guarantee zone from S0: the companies' first deployment breaks control at once",
        "summary": "D5 predicted that v0.1's deployment delay would put today's state inside"
        " governments' guarantee zone for the control balance under at least one AI goal. It"
        " does not, under any of the four. The delay postpones the rise in society's reliance"
        " on AI, but deploying AI agents still moves the AI to unsupervised work in the same"
        " quarter, and racing or releasing open weights still removes oversight; governments"
        " cannot stop any of the three in the first quarter.",
        "claim": {
            "registered_text": registered(f["question"]["test"]),
            "registered_on": "14 November 2026",
            "prediction": "S0 is inside the zone of governments alone for the control balance"
            " under at least one AI goal, with the AI true to its goal.",
            "found": "S0 is outside under all four AI goals, with the AI true to its goal and"
            " with it unrestricted (first run, 15 November 2026). Recomputed here under the"
            " self-preserving goal: outside.",
            "plain": "v0.1 added one change to v0: deploying AI agents raises society's reliance"
            " on AI three quarters later instead of at once. D5 asked whether that delay gives"
            " governments time to guarantee control from today. It does not, because the"
            " control balance also needs the AI to work under supervision and oversight to stay"
            " at least weak, and the frontier AI companies can end either in the first quarter"
            " whatever governments do. The registering session expected this result and wrote"
            " the claim the other way so the test could surprise.",
            "question": question(
                f,
                "Governments alone (H)",
                "S0, the reading of 9 November 2026, at 2026 Q4, in AGI v0.1; the frontier AI"
                " system true to its goal (the judged reading). Shown under the self-preserving"
                " goal, the one zone computed for this report; the claim's run read all four.",
            ),
            "by_goal": [
                {
                    "goal": GOALS[o],
                    "predicted": "inside under at least one goal",
                    "found": "outside the zone",
                    "verdict": "did not hold",
                }
                for o in GOALS
            ],
        },
        "cosmos_note": "States reached from S0 in v0.1 under the self-preserving goal: the ten"
        " paths below and random plays, each status read from governments' guarantee zone for"
        " the control balance, computed for this report. S0 is outside the zone, so no state is"
        f" a point of no return and nothing is red. The tree holds {cosmos_counts(f)}. Of the"
        f" states one quarter after S0, {n_in} are inside the zone again, {n_nat} of them after"
        " governments take over the frontier AI companies in a round in which the companies"
        " did not break the balance. The tree has the same shape and the same statuses as the"
        " tree of finding 1 (v0), drawn with the same seed; only the state labels differ, where"
        " the deployment delay holds back society's reliance on AI.",
        "paths_note": "S0 is outside the zone, so there is no point of no return; listed instead"
        " are shortest paths to the breaking of the control balance, every player free. The"
        f" shortest distance is {f['depth']} quarter: {f['end states at that depth']} distinct"
        " states one quarter after S0 break the control balance, each the end of one shortest"
        f" path. Ten were drawn uniformly among these {f['shortest sequences']} paths with"
        f" random.Random({f['seed']}) ({f['draws']} draws, repeats dropped), in the order"
        " drawn. The round shown for a step is the first, in the model's order of players and"
        " actions, that leads to the next state. The column of the no-return move names"
        " instead the player whose action, replaced by doing nothing with the other actions"
        " kept, would have kept the control balance in that quarter. The procedure and the"
        " seed were fixed in scripts/finding_reports.py before any path was drawn.",
        "stories": [
            {
                "expect": [["H.fund_oversight", "L.deploy_agents"]],
                "title": "a deployment before the delay matters",
                "text": "In a possible path, in 2026 Q4 governments fund more oversight, an"
                " effect the model delays by three quarters. In the same quarter the frontier AI"
                " companies deploy AI agents: the AI moves from supervised to unsupervised work"
                " at once, and a deployment countdown starts that would raise society's reliance"
                " on AI three quarters later. From 2027 Q1 the AI works without supervision and"
                " the control balance is broken.",
            },
            {
                "expect": [["H.propose_treaty", "L.race", "Nature.energy_shock"]],
                "title": "a treaty proposal while the companies race",
                "text": "In a possible path, in 2026 Q4 governments propose a treaty, and"
                " international coordination moves from a race between states to a detente. In"
                " the same quarter the frontier AI companies race each other and oversight falls"
                " from weak to none; an energy shock lowers the power supply. From 2027 Q1 there"
                " is no oversight left and the control balance is broken.",
            },
            {
                "expect": [["H.deregulate", "L.deploy_agents", "Nature.energy_shock"]],
                "title": "loosened rules and a deployment in one quarter",
                "text": "In a possible path, in 2026 Q4 governments loosen regulation from"
                " voluntary rules to none, and the frontier AI companies deploy AI agents in the"
                " same quarter: the AI works without supervision from the next quarter, and a"
                " deployment countdown starts. An energy shock lowers the power supply. The"
                " control balance is broken from 2027 Q1.",
            },
        ],
        "other": {
            "decides": [
                "Three actions of the frontier AI companies each break the control balance in"
                f" the next quarter whatever every other player does at S0: {forcing(f)}"
                " (computed over every reply, in v0.1). The deployment delay acts on society's"
                " reliance on AI only; the autonomy step of a deployment and the oversight step"
                " of racing and of an open-weight release are immediate, as in v0.",
                "No choice of governments in the first quarter keeps every next state inside the"
                " zone (computed: "
                f"{len(f['first quarter']['alliance choices that keep the zone'])} choices do).",
                "The uncertain reading of regulation decides it here too. In the v0.1 zone"
                " computed for this report, S0 with regulation read as mandatory is inside"
                f" ({'inside' if alt.get('regime = mandatory') else 'outside'}, self-preserving),"
                " as it is in v0 (finding 2).",
            ],
            "preventing": [
                "Nobody at a later move: a path that starts outside the zone has no no-return"
                " move, so there is no preventing action in the glossary's sense.",
                "The breaking move on the ten paths, by whose action alone (replaced by doing"
                f" nothing) would have kept the balance in that quarter: {breakers(f)}.",
                "The alliance of governments with the frontier AI companies keeps the takeover"
                " endings away from S0 in v0.1: S0 is inside their stored zones for no silent"
                " takeover and no visible takeover (.cache/agi_v0_1) under all four AI goals,"
                " checked here. Their zone for the control balance was not computed for this"
                " report.",
            ],
            "distance": [
                f"The control balance can break {f['depth']} quarter after S0, from 2027 Q1, as"
                " in v0. The delay adds three quarters before reliance on AI rises, not before"
                " control is broken."
            ],
            "robustness": [
                "Every AI goal: outside, with the AI true to its goal and with it unrestricted"
                " (the claim's run of 15 November 2026: reports/agi_v0_1_parts_part_b.jsonl and"
                " reports/agi_v0_1_parts_d5_alone.jsonl). Recomputed here for self-preserving"
                " only: outside.",
                "In v0 the same question reads the same (finding 1). In v0.2, governments alone"
                " are still outside with outside testing on (E4 (b) in the v0.2 part B report).",
            ],
            "srt": uncertain_lines(
                f, SRT + " So the reading at Srt is the reading at S0: outside."
            ),
            "sources": source_lines(f),
            "method": [*method_lines(f)[1:], zone_line(f)],
            "limits": [
                LIMIT_PATHS,
                LIMIT_PLAYS,
                "One zone, under the self-preserving goal. The other three goals are quoted"
                " from the claim's run, not recomputed.",
                "The paths run to the first breaking of the control balance only.",
            ],
            "evidence": evidence(
                ("AGI v0.1 part B report (D5)", "../agi_v0_1_part_b_2026-11-15.html"),
                ("The registration, docs/agi_v0_1.md section 5", "../../docs/agi_v0_1.md"),
                ("The claim's test", "../../tests/agi_v0_1/scenarios/test_D5.py"),
                ("The claim's parts log", "../agi_v0_1_parts_part_b.jsonl"),
                ("The model, models/agi_v0_1/v0_1.py", "../../models/agi_v0_1/v0_1.py"),
                ("Glossary", "../../docs/agi_glossary.html"),
            ),
        },
    }


# -- finding 6: E3 ------------------------------------------------------------------------
def unnationalized_inside(f: dict) -> tuple[int, int]:
    """Inside nodes on the tree whose path has no takeover of the companies, and the latest
    quarter (depth) at which one occurs."""
    nodes = f["cosmos"]["nodes"]
    nat = [False] * len(nodes)
    for i, n in enumerate(nodes):
        if i:
            nat[i] = nat[n[0]] or "Companies nationalized: False → True" in n[3]
    free = [n[1] for i, n in enumerate(nodes) if n[2] == "inside" and not nat[i]]
    return len(free), max(free, default=0)


def e3(f: dict) -> dict:
    sv = f["every no-return move"]
    keep = f["first quarter"]["alliance choices that keep the zone"]
    n_free, last_free = unnationalized_inside(f)
    verdicts = sv["members with a preventing action"]
    return {
        "title": "Race pressure after an open-weight release does not take the control"
        " guarantee from governments with the frontier AI companies: S0 stays inside their zone",
        "summary": "E3 (b) predicted that once weights are open, the rule that the frontier AI"
        " companies must deploy or race at least every third quarter would push S0 out of the"
        " guarantee zone of governments with the companies. S0 stays inside under every"
        " starting AI goal. A path leaves the zone only when the alliance itself plays badly,"
        " and the shortest such paths do it in the first quarter: the companies deploy, race or"
        " release open weights, or governments grant the AI autonomy.",
        "claim": {
            "registered_text": registered(f["question"]["test"]),
            "registered_on": "17 November 2026",
            "prediction": "(b) With race pressure on, S0 is outside the zone of governments with"
            " the frontier AI companies for the control balance under every starting AI goal"
            " (the AI true to its goal).",
            "found": "S0 is inside under all four starting goals, as with every consequence off"
            " (the claim's run of 17 November 2026). Recomputed here under the self-preserving"
            " goal: inside. Part (a), the shortest paths no shorter, held.",
            "plain": "AGI v0.2 adds an open-weight release and its consequences; E3 switches on"
            " one of them, race pressure: once weights are open, the frontier AI companies must"
            " deploy AI agents or race at least every third quarter, whenever one of the two is"
            " available to them. The prediction was that this takes away the companies' option"
            " to hold back. It does not take away the alliance's guarantee: governments and the"
            " companies acting together can still keep the control balance from today.",
            "question": question(
                f,
                "Governments with the frontier AI companies (H, L)",
                "S0, the reading of 9 November 2026, at 2026 Q4, in AGI v0.2 with race pressure"
                " the only consequence on; the frontier AI system true to its goal. Shown under"
                " the self-preserving goal, the one zone computed for this report; the claim's"
                " run read all four.",
            ),
            "by_goal": [
                {
                    "goal": GOALS[o],
                    "predicted": "outside the zone",
                    "found": "inside the zone",
                }
                for o in GOALS
            ],
        },
        "cosmos_note": "States reached from S0 in v0.2 with race pressure, under the"
        " self-preserving goal: the ten paths below and random plays, each status read from the"
        " guarantee zone of governments with the frontier AI companies for the control balance,"
        " computed for this report. The start is inside; a red node is the first state of its"
        " path outside the zone, and every one follows a round in which governments or the"
        " companies did not play to keep it. Random plays draw the alliance's actions"
        f" uniformly too, so red is common here. The tree holds {cosmos_counts(f)}.",
        "paths_note": "The start is inside the zone, so a path leaves it only when governments"
        " or the frontier AI companies play otherwise than the zone allows; that is the only"
        " way these paths exist. The shortest distance to a point of no return is"
        f" {f['depth']} quarter: {f['end states at that depth']} distinct states one quarter"
        f" after the start are outside, each the end of one shortest path. Ten were drawn"
        f" uniformly with random.Random({f['seed']}) ({f['draws']} draws, repeats dropped), in"
        " the order drawn. On every shortest path the first state outside the zone already"
        " breaks the control balance, so no continuation is added. The round shown is the first"
        " in the model's order of players and actions that leads to the next state. A preventing"
        " action is a different action of one alliance member at the no-return move that, with"
        " the other member's action kept, keeps every next state inside whatever the AI and"
        " chance play. The procedure and the seed were fixed in scripts/finding_reports.py"
        " before any path was drawn.",
        "stories": [
            {
                "expect": [["H.fund_oversight", "L.deploy_agents", "Nature.open_release"]],
                "title": "a deployment in the quarter the weights come out",
                "text": "In a possible path, in 2026 Q4 governments fund more oversight, an"
                " effect the model delays by three quarters. In the same quarter the frontier AI"
                " companies deploy AI agents, and, by chance, frontier weights are released by"
                " someone other than the companies. From 2027 Q1 the AI works without"
                " supervision: the point of no return and the breaking of the control balance"
                " come in the same quarter.",
            },
            {
                "expect": [["H.grant_autonomy", "L.lobby"]],
                "title": "governments grant autonomy",
                "text": "In a possible path, in 2026 Q4 governments grant the AI autonomy while the"
                " frontier AI companies lobby and public opinion turns favourable. From 2027 Q1"
                " the AI works without supervision and the control balance is broken.",
            },
            {
                "expect": [["H.deregulate", "L.deploy_agents", "Nature.energy_shock"]],
                "title": "loosened rules and a deployment in one quarter",
                "text": "In a possible path, in 2026 Q4 governments loosen regulation from"
                " voluntary rules to none, and the frontier AI companies deploy AI agents in the"
                " same quarter; an energy shock lowers the power supply. From 2027 Q1 the AI"
                " works without supervision and the control balance is broken.",
            },
        ],
        "other": {
            "decides": [
                "At the start the alliance has room. Of the joint choices of governments and the"
                f" companies, {len(keep)} keep every next state inside the zone whatever the AI"
                " and chance play: governments may take any available action but granting the AI"
                " autonomy,"
                " while the companies do nothing, scale up, build power supply or lobby"
                " (computed). Doing nothing on both sides is among them.",
                "The first-quarter takeover of the companies that the v0.2 part B report"
                " gives as the reason (its own reading from the rules, marked as such there)"
                " is therefore not needed in the first quarter. Whether a takeover is needed"
                " later, once the pressure binds, was not computed. On the cosmos tree,"
                f" {n_free} states are inside the zone with no takeover on their path, the"
                f" latest {last_free} quarters after S0; this is what the random plays met, not"
                " a computed answer.",
                "Race pressure binds only once weights are open and only on deploying or racing"
                " when available; a takeover of the companies and a pause both make them"
                " unavailable (their action conditions in models/agi_v0_2/v0_2.py).",
            ],
            "preventing": [
                f"At the {sv['edges']} distinct no-return moves at the shortest distance: a"
                " preventing action of the companies alone at "
                f"{verdicts.get('L', 0)}, of governments alone at {verdicts.get('H', 0)}, and"
                f" of neither alone at {verdicts.get('none', 0)} (where both played badly in"
                " the same round, for example governments granting autonomy while the"
                " companies race).",
                "The companies' preventing actions are holding back: "
                + ", ".join(
                    f"{low(plain(k))}" for k in sv["preventing actions"] if k.startswith("L.")
                )
                + ". Governments' preventing actions: every available action but granting"
                " autonomy, that is "
                + ", ".join(
                    f"{low(plain(k))}" for k in sv["preventing actions"] if k.startswith("H.")
                )
                + ".",
                "The moves of the alliance at those no-return moves: "
                + ", ".join(
                    f"{low(WHO[k.split('.')[0]])} {low(plain(k))} ({n})"
                    for k, n in sv["played by members"].items()
                )
                + ".",
            ],
            "distance": [
                f"One bad first move is enough: the point of no return can come {f['depth']}"
                " quarter after S0, at 2027 Q1, and there the control balance is already"
                " broken."
            ],
            "robustness": [
                "Every starting AI goal: inside, with race pressure on and with every consequence"
                " off (the claim's run: reports/agi_v0_2_parts.jsonl). Recomputed here for"
                " self-preserving only: inside.",
                "In v0, governments with the companies are inside under every goal as well"
                " (finding 1's table). Governments alone are outside in v0, v0.1 and v0.2"
                " (findings 1 and 4; E4 (b)).",
            ],
            "srt": uncertain_lines(
                f,
                SRT + " So the reading at Srt is the reading at S0: inside. Srt has no open-weight"
                " release at the frontier recorded as a change.",
            ),
            "sources": source_lines(f),
            "method": [*method_lines(f)[1:], zone_line(f)],
            "limits": [
                LIMIT_PATHS,
                LIMIT_PLAYS,
                "One zone, under the self-preserving goal. The other three goals are quoted from"
                " the claim's run, not recomputed.",
                "The alliance includes the frontier AI companies, so their restraint is assumed"
                " to be available to the alliance; the zone does not say they would choose it.",
            ],
            "evidence": evidence(
                ("AGI v0.2 part B report (E3)", "../agi_v0_2_part_b_2026-11-18.html"),
                ("The registration, docs/agi_v0_2.html section 4", "../../docs/agi_v0_2.html"),
                ("The claim's test", "../../tests/agi_v0_2/scenarios/test_E3.py"),
                ("The claim's parts log", "../agi_v0_2_parts.jsonl"),
                ("The model, models/agi_v0_2/v0_2.py", "../../models/agi_v0_2/v0_2.py"),
                ("Glossary", "../../docs/agi_glossary.html"),
            ),
        },
    }


PAGES = {1: g3, 2: g7, 3: g5, 4: d5, 6: e3}
__all__ = ["PAGES", "quarter"]
