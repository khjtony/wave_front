"""A deterministic rule backend: keyword and date rules over the ontology's threshold text.

Each :class:`Rule` reads one level of one variable. It fires on a *sentence* that matches all
of its ``all_of`` patterns and none of its ``none_of`` patterns (case-insensitive regular
expressions); the sentence is the quote. The keywords are taken from the threshold rules and
notes of docs/ontology_ww2.md (the section is cited in each rule), so a proposal says which
reading of the ontology produced it. For each variable the rules are tried in the order
listed (the more specific level first) and the first that fires anywhere in the document
gives the document's one proposal for that variable.

Date rule: the proposal is dated by the document, except that a sentence naming a full date
("17 March 1939", "March 17, 1939") within the 31 days before the document's date is dated by
that date, and "yesterday" by the day before the document.

What it is: good enough for the synthetic fixtures, whose period-style wording it was written
alongside, and a baseline that makes the pipeline testable without a language model. What it
is not: a reader. It does not resolve negation beyond its ``none_of`` patterns, who is
speaking, reported or hypothetical speech, or a level that follows from several sentences
together; on a real corpus it would both miss and misread. Real replays use a model backend
and a human review of every proposal.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from ..corpora.base import Document
from ..hindsight_ww2 import JUDGMENT
from .backend import split_sentences
from .schema import Proposal, VariableSpec

__all__ = ["Rule", "RULES", "RuleBackend", "observation_date"]


@dataclass(frozen=True)
class Rule:
    id: str
    variable: str
    level: object
    all_of: tuple[str, ...]
    why: str
    none_of: tuple[str, ...] = ()

    def matches(self, sentence: str) -> bool:
        return all(re.search(p, sentence, re.I) for p in self.all_of) and not any(
            re.search(p, sentence, re.I) for p in self.none_of
        )


def R(rid, variable, level, all_of, why, none_of=()):  # noqa: N802 - a table constructor
    return Rule(rid, variable, level, tuple(all_of), why, tuple(none_of))


GER = r"\b(german|germany|reich|fuehrer|führer|hitler)"
WEST = r"\b(britain|british|england|english|france|french|united kingdom|this country|his majesty)"
BRITAIN = r"(\bbritain|\bbritish|\bengland|united kingdom|this country|his majesty)"
DECLARE_WAR = r"(at war with germany|declared war|declaration of war|state of war exists)"

RULES: tuple[Rule, ...] = (
    # -- section 3: beliefs and commitment -------------------------------------------------
    R(
        "belief_WEST.hegemonic",
        "belief_WEST",
        "hegemonic",
        [
            r"(dominat\w* the world by force|domination by force|"
            r"assurances (can ?not|could not) be relied)"
        ],
        "ontology 3, belief_WEST hegemonic: the Prime Minister states that Germany seeks "
        "domination by force or that its assurances cannot be relied on",
    ),
    R(
        "belief_WEST.uncertain",
        "belief_WEST",
        "uncertain",
        [r"\b(warning|warnings|warned|precaution\w*|contingency)\b", r"\b(berlin|german)"],
        "ontology 3, belief_WEST uncertain: London adopts warnings or contingency measures "
        "towards Germany while still negotiating",
    ),
    R(
        "belief_WEST.limited",
        "belief_WEST",
        "limited",
        [
            r"(general settlement|negotiated settlement|no reason to suppose|"
            r"not .{0,40}threat of hostilities)"
        ],
        "ontology 3, belief_WEST limited: German aims treated as revision that a negotiated "
        "settlement can satisfy",
    ),
    R(
        "belief_GER.will_not_fight",
        "belief_GER",
        "will_not_fight",
        [r"(will not fight|little worms|saw them at munich|will not intervene)"],
        "ontology 3, belief_GER will_not_fight: Hitler, at a decision, states that the West "
        "will not fight",
    ),
    R(
        "belief_GER.will_fight",
        "belief_GER",
        "will_fight",
        [
            r"\b(fuehrer|führer|hitler|berlin|german government)\b",
            r"(war with (england|britain|the west)|(england|britain) will fight)",
        ],
        "ontology 3, belief_GER will_fight: Berlin treats war with the West as the consequence "
        "of its next step",
        [r"\b(if|must not|doubt|not certain|whether)\b"],
    ),
    R(
        "belief_GER.uncertain",
        "belief_GER",
        "uncertain",
        [
            r"\b(fuehrer|führer|hitler)\b",
            r"(doubts?|not certain|whether|must not come to|showdown with the west)",
        ],
        "ontology 3, belief_GER uncertain: a German decision record that provides against "
        "Western intervention or records doubt about it",
    ),
    R(
        "commit_WEST.at_war",
        "commit_WEST",
        "at_war",
        [WEST, DECLARE_WAR],
        "ontology 3, commit_WEST at_war: a declaration of war",
    ),
    R(
        "commit_WEST.resolved",
        "commit_WEST",
        "resolved",
        [
            BRITAIN + r"|prime minister|house of commons|french government",
            r"((polish|poland).{0,200}(all support in their power|guarantee)|"
            r"(guarantee|all support in their power).{0,200}(polish|poland)|"
            r"conscription|compulsory military (training|service))",
        ],
        "ontology 3, commit_WEST resolved: a standing commitment to fight for a third state "
        "Germany threatens (the Polish guarantee) or peacetime conscription",
    ),
    R(
        "commit_WEST.wary",
        "commit_WEST",
        "wary",
        [r"rearm\w*", r"(accelerat\w*|with all speed|press forward|field force)"],
        "ontology 3, commit_WEST wary: the government accepts that a further German move may "
        "need a military answer and prepares for it (the post-Munich acceleration)",
    ),
    R(
        "commit_US.engaged",
        "commit_US",
        "engaged",
        [r"(destroyers?.{0,120}bases|bases.{0,120}destroyers?|transfers? of war material)"],
        "ontology 3, commit_US engaged: executive transfers of war material to a belligerent "
        "(destroyers for bases)",
    ),
    R(
        "commit_US.wary",
        "commit_US",
        "wary",
        [r"(cash[- ]and[- ]carry|repeal\w* the arms embargo)"],
        "ontology 3, commit_US wary: the arms embargo repealed and arms sold on cash and carry",
    ),
    R(
        "commit_US.isolationist",
        "commit_US",
        "isolationist",
        [r"neutrality act", r"(mandatory|arms embargo)"],
        "ontology 3, commit_US isolationist: the Neutrality Act regime with a mandatory arms "
        "embargo",
        [r"repeal"],
    ),
    # -- section 4: structure ------------------------------------------------------------
    R(
        "treaty.dead",
        "treaty",
        "dead",
        [r"locarno", r"(no longer (considers itself )?bound|repudiat\w*|denounc\w*|breach)"],
        "ontology 4, treaty dead: the Rhine Pact of Locarno repudiated and the zone reoccupied, "
        "the guarantors declining enforcement",
    ),
    R(
        "axis.true",
        "axis",
        True,
        [
            r"(rome-berlin|axis powers|\baxis\b|"
            r"(germany|german).{0,80}(italy|italian).{0,120}(protocol|pact|alliance|treaty)|"
            r"(italy|italian).{0,80}(germany|german).{0,120}(protocol|pact|alliance|treaty))"
        ],
        "ontology 4, axis: the Rome-Berlin alignment (the October Protocols; later pacts "
        "confirm it)",
    ),
    R(
        "anticomintern.true",
        "anticomintern",
        True,
        [
            r"(anti-comintern|against the communist international|"
            r"(germany|german).{0,80}(japan|japanese).{0,120}(pact|agreement|alliance))"
        ],
        "ontology 4, anticomintern: the German-Japanese alignment (the Anti-Comintern Pact)",
    ),
    R(
        "nazi_soviet_pact.true",
        "nazi_soviet_pact",
        True,
        [r"non-aggression", r"(soviet|ussr|russia)", GER],
        "ontology 4, nazi_soviet_pact: the German-Soviet non-aggression pact",
    ),
    R(
        "polish_guarantee.true",
        "polish_guarantee",
        True,
        [r"(polish|poland)", r"(all support in their power|guarantee)"],
        "ontology 4, polish_guarantee: the Prime Minister's statement in the Commons",
    ),
    R(
        "anglo_soviet_alliance.false",
        "anglo_soviet_alliance",
        False,
        [
            r"(moscow|soviet)",
            r"(british|french|anglo)",
            r"(talks|negotiations|mission)",
            r"(adjourned|suspended|broke down|without agreement)",
        ],
        "ontology 4, anglo_soviet_alliance: the failure of the 1939 talks (the suspension of the "
        "military talks)",
    ),
    R(
        "ussr_axis.false",
        "ussr_axis",
        False,
        [
            r"(molotov|soviet)",
            r"(berlin|three-power pact|tripartite pact)",
            r"(without agreement|without the accession|no agreement)",
        ],
        "ontology 4, ussr_axis: the November 1940 talks end without Soviet accession",
    ),
    R(
        "china_war.true",
        "china_war",
        True,
        [
            r"(japanese|japan)",
            r"(chinese|china|peiping|marco polo)",
            r"(fire|fighting|clash\w*|hostilities|reinforcements)",
        ],
        "ontology 4, china_war: Japan's army engaged in fighting in China (the Marco Polo Bridge "
        "incident)",
    ),
    R(
        "italy_estranged.true",
        "italy_estranged",
        True,
        [r"(italy|italian)", r"(sanctions|estranged)"],
        "ontology 4, italy_estranged: Italy estranged from the West after Ethiopia (League "
        "sanctions)",
    ),
    # -- section 5: regions and war ------------------------------------------------------
    R(
        "war_west_ger.war",
        "war_west_ger",
        "war",
        [WEST, DECLARE_WAR],
        "ontology 5, war_west_ger war: a British and French declaration of war in force",
    ),
    R(
        "rhineland.remilitarized",
        "rhineland",
        "remilitarized",
        [
            r"(rhineland|demilitari[sz]ed zone)",
            r"(troops|battalions|forces)",
            r"(march\w*|occup\w*|enter\w*|garrison\w*)",
        ],
        "ontology 5, rhineland remilitarized: German troops garrisoned in the zone",
    ),
    R(
        "austria.annexed",
        "austria",
        "annexed",
        [r"(german troops.{0,80}austria|austrian frontier|anschluss|reunification of austria)"],
        "ontology 5, austria annexed: German troops in Austria and the reunification law",
    ),
    R(
        "sudeten.german",
        "sudeten",
        "german",
        [r"sudeten", r"(evacuation|cession|ceded|transfer|occupation by german)"],
        "ontology 5, sudeten german: the areas ceded under the Munich agreement",
    ),
    R(
        "bohemia.german",
        "bohemia",
        "german",
        [
            r"(prague|bohemia|moravia)",
            r"(german troops|german forces|protectorate)",
            r"(occup\w*|enter\w*|protectorate)",
        ],
        "ontology 5, bohemia german: the Protectorate of Bohemia and Moravia",
    ),
    R(
        "poland.partitioned",
        "poland",
        "partitioned",
        [
            r"(soviet|red army|russian)",
            r"(poland|polish)",
            r"(cross\w*|enter\w*|march\w*|partition\w*)",
        ],
        "ontology 5, poland partitioned: German and Soviet shares",
    ),
    R(
        "poland.german",
        "poland",
        "german",
        [GER, r"(poland|polish|warsaw)", r"\b(attacked|invaded|bombed|crossed)\b"],
        "ontology 5, poland german: Poland under German attack with no Soviet share",
    ),
    R(
        "france.fallen",
        "france",
        "fallen",
        [r"(france|french)", r"armistice", r"(signed|sign)"],
        "ontology 5, france fallen: the armistice signed",
        [r"armistice of 1918 was signed$"],
    ),
    R(
        "france.at_war",
        "france",
        "at_war",
        [r"\bfrance\b", r"(at war with germany|declared war|declaration of war)"],
        "ontology 5, france at_war: at war with Germany",
    ),
    R(
        "britain.negotiated",
        "britain",
        "negotiated",
        [BRITAIN, r"(accepted|signed|concluded)", r"(peace terms|armistice with germany)"],
        "ontology 5, britain negotiated: a negotiated peace with Germany",
    ),
    R(
        "britain.at_war",
        "britain",
        "at_war",
        [r"(this country is at war|united kingdom and germany|we shall fight on|fight on\b)"],
        "ontology 5, britain at_war: Britain at war and fighting on",
    ),
    R(
        "balkans.german_aligned",
        "balkans",
        "german_aligned",
        [
            r"(rumania|romania)",
            r"(guarantee|three-power pact|tripartite pact|military mission|axis powers)",
        ],
        "ontology 5, balkans german_aligned: Romania under German guarantee, with a German "
        "military mission and in the Tripartite Pact",
    ),
    R(
        "siberia.soviet",
        "siberia",
        "soviet",
        [r"(ceasefire|cease-fire|truce|armistice)", r"(mongolia|nomonhan|khalkhin)"],
        "ontology 5, siberia soviet: the frontier holds under Soviet control",
    ),
    R(
        "channel_air.british",
        "channel_air",
        "british",
        [
            r"(invasion.{0,80}(postponed|receded|abandoned|cannot be attempted)|"
            r"failed to win (command|superiority) of the air)"
        ],
        "ontology 5, channel_air british: the German invasion postponed for lack of air "
        "superiority",
    ),
    R(
        "channel_air.contested",
        "channel_air",
        "contested",
        [r"(air battle|air offensive|air attacks?)", r"(channel|britain|england|convoy)"],
        "ontology 5, channel_air contested: an air battle under way, neither side holding "
        "superiority",
    ),
    # -- section 2: oil, where the datasets are silent ----------------------------------
    R(
        "oil_GER.secured",
        "oil_GER",
        "secured",
        [r"(soviet|rumanian|romanian)", r"\boil\b", r"(agreement|deliver\w*)"],
        "ontology 2, oil_GER secured: an overland supply agreement in force with a producer "
        "outside the blockade",
    ),
    R(
        "oil_GER.dependent",
        "oil_GER",
        "dependent",
        [r"\boil\b", r"(imported by sea|independent of foreign|import\w* .{0,40}overseas)"],
        "ontology 2, oil_GER dependent: most of the mineral oil supply imported by sea",
    ),
)

_MONTHS = (
    "january february march april may june july august september october november december"
).split()
_DMY = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)? (?:of )?(" + "|".join(_MONTHS) + r"),? (\d{4})\b", re.I
)
_MDY = re.compile(r"\b(" + "|".join(_MONTHS) + r") (\d{1,2}),? (\d{4})\b", re.I)


def observation_date(sentence: str, document_date: date) -> date:
    """The date rule: a full date named in the sentence within the 31 days before the
    document's date, else the day before it for "yesterday", else the document's date."""
    candidates: list[date] = []
    for m in _DMY.finditer(sentence):
        candidates.append(_make(int(m.group(3)), m.group(2), int(m.group(1))))
    for m in _MDY.finditer(sentence):
        candidates.append(_make(int(m.group(3)), m.group(1), int(m.group(2))))
    window = [
        d for d in candidates if d and document_date - timedelta(days=31) <= d <= document_date
    ]
    if window:
        return max(window)
    if re.search(r"\byesterday\b", sentence, re.I):
        return document_date - timedelta(days=1)
    return document_date


def _make(year: int, month: str, day: int) -> date | None:
    try:
        return date(year, _MONTHS.index(month.lower()) + 1, day)
    except ValueError:
        return None


class RuleBackend:
    """The deterministic backend: :data:`RULES` applied sentence by sentence."""

    name = "rules"

    def __init__(self, rules: Sequence[Rule] = RULES) -> None:
        self.rules = tuple(rules)

    def propose(self, document: Document, variables: Sequence[VariableSpec]) -> list[Proposal]:
        wanted = {v.name for v in variables}
        sentences = [
            s for p in document.text.split("\n\n") for s in split_sentences(p) if s.strip()
        ]
        out: list[Proposal] = []
        done: set[str] = set()
        for rule in self.rules:
            if rule.variable not in wanted or rule.variable in done:
                continue
            hit = next((s for s in sentences if rule.matches(s)), None)
            if hit is None:
                continue
            done.add(rule.variable)
            judged = rule.variable in JUDGMENT or rule.variable.startswith("commit_")
            out.append(
                Proposal(
                    indicator_id=f"{document.id}:{rule.id}",
                    variable=rule.variable,
                    level=rule.level,
                    date=observation_date(hit, document.date).isoformat(),
                    quote=hit,
                    url=document.url,
                    rule=f"rule {rule.id}: {rule.why}",
                    confidence="medium" if judged else "high",
                )
            )
        return out
