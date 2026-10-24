"""The episodes the replay harness can read: WW2 (the default) and the Cold War.

An :class:`Episode` names what the extractor, the harness rules, the review step and the
replay metrics read for one domain model: the text-derived variables with their levels and
initial levels, the ontology their threshold rules come from, the wording of the prompt's
first paragraph, the model the replay snapshots are for, the hindsight snapshots, and the
periods of the replay.

``ww2``
    The WW2 v0 model (``ww2_v0``; docs/ontology_ww2.md; ``snapshots/ww2/hindsight/``), by
    quarter (``1936Q1``): a quarter's cut-off is its last day and its snapshot is dated by it.
    The tables are those of :mod:`.hindsight_ww2`; nothing here changes them.
``cw``
    The Cold War v0 model (``cw_v0``; docs/ontology_cw.md; ``snapshots/cw/hindsight/``), by
    year, as the model ticks: the period ``1958`` is the state on 1 January 1958 (tick 11),
    read from the documents dated at or before 31 December 1957 (decisions D1 and D7 of
    docs/cw_v0_decisions.md: "documents dated before the snapshot's date"). The text-derived
    variables are the three belief variables of the ontology's section 3
    (:data:`CW_TEXT_VARIABLES`); every other variable of a replay snapshot is carried from the
    hindsight snapshot of the year as ``assumed``, as in the manual replay of D7. The belief
    variables are readings, outside both harness rules, as WW2's belief and commitment
    variables are.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from . import hindsight_ww2 as hw

__all__ = [
    "CW",
    "CW_TEXT_VARIABLES",
    "CW_VARIABLES",
    "EPISODES",
    "Episode",
    "EpisodeError",
    "WW2",
    "WW2_RESOURCE_VARIABLES",
    "WW2_TEXT_VARIABLES",
    "get_episode",
]

ROOT = Path(__file__).resolve().parents[2]


class EpisodeError(ValueError):
    """An unknown episode, a period that is not one of the episode's, or proposals files of
    different episodes in one directory."""


@dataclass(frozen=True)
class EpisodeVariable:
    """A text-derived variable of an episode: ``kind`` is ``level``, ``flag`` or ``integer``."""

    name: str
    kind: str
    levels: tuple[Any, ...]
    init: Any
    section: str


NUKE = ("none", "few", "survivable", "overkill")
# The belief variables of docs/ontology_cw.md section 3, as models/cw/v0.py declares them
# (tests/evidence/test_episode_cw.py keeps this equal to the model and the ontology).
CW_VARIABLES: tuple[EpisodeVariable, ...] = (
    EpisodeVariable("belief_force_USA", "level", NUKE, "none", "3"),
    EpisodeVariable(
        "belief_USA_USSR",
        "level",
        ("status_quo", "opportunist", "expansionist"),
        "opportunist",
        "3",
    ),
    EpisodeVariable(
        "belief_USSR_USA", "level", ("status_quo", "hostile", "first_strike_intent"), "hostile", "3"
    ),
)
CW_TEXT_VARIABLES = tuple(v.name for v in CW_VARIABLES)

# The WW2 variables a replay reads from text (ww2_testbed.md section 8: commitment, belief,
# treaty, pacts, war, regions, and oil where the datasets are silent) and the resource
# variables it copies from the dataset-derived hindsight snapshot instead.
WW2_TEXT_VARIABLES = (
    "belief_WEST",
    "belief_GER",
    "commit_WEST",
    "commit_US",
    "treaty",
    "axis",
    "anticomintern",
    "nazi_soviet_pact",
    "polish_guarantee",
    "anglo_soviet_alliance",
    "ussr_axis",
    "italy_estranged",
    "china_war",
    "war_west_ger",
    "rhineland",
    "austria",
    "sudeten",
    "bohemia",
    "poland",
    "france",
    "britain",
    "balkans",
    "siberia",
    "channel_air",
    "oil_GER",
)
WW2_RESOURCE_VARIABLES = ("arms_GER", "arms_WEST", "arms_USSR", "arms_JPN", "ind_GER")

_YEAR = re.compile(r"\d{4}")


@dataclass(frozen=True)
class Episode:
    """One domain model as the replay harness reads it (see the module docstring)."""

    name: str
    title: str
    #: the end of the prompt's first sentence: "... the variables of a model of <scope>."
    scope: str
    #: the date of the initial levels, as the prompt states it
    start: str
    ontology: Path
    model: str
    hindsight: Path
    #: ``quarter`` or ``year``
    period: str
    text_variables: tuple[str, ...]
    #: variables copied from the hindsight snapshot, marked as copied (WW2: the resources)
    resource_variables: tuple[str, ...]
    #: variables outside both harness rules (shown and counted as the backend made them)
    readings: frozenset[str]
    #: periods within which a replayed flip may answer a documented one
    match_window: int
    #: the variable whose levels are the scale of another (a rule text appended to it)
    scales: tuple[tuple[str, str], ...] = ()
    #: the variable of the hindsight snapshot each text variable is compared with
    truth: tuple[tuple[str, str], ...] = ()

    # -- variables ------------------------------------------------------------------------

    def variable(self, name: str) -> Any:
        """The table entry of a text variable (``name``, ``kind``, ``levels``, ``init``,
        ``section``)."""
        if self.name == "ww2":
            return hw.BY_NAME[name]
        for v in CW_VARIABLES:
            if v.name == name:
                return v
        raise KeyError(name)

    def truth_of(self, name: str) -> str:
        return dict(self.truth).get(name, name)

    # -- periods --------------------------------------------------------------------------

    def parse_periods(self, text: str) -> list[str]:
        """``1936Q1..1940Q4`` (quarters, WW2) or ``1957..1962`` (years, the Cold War), a
        single period, or a comma-separated increasing list."""
        text = text.strip()
        if ".." in text:
            a, b = (t.strip() for t in text.split("..", 1))
            i, j = self.index(a), self.index(b)
            if j < i:
                raise EpisodeError(f"empty {self.period} range {text!r}")
            return [self.label(k) for k in range(i, j + 1)]
        periods = [p.strip() for p in text.split(",") if p.strip()]
        indices = [self.index(p) for p in periods]
        if not periods or indices != sorted(set(indices)):
            raise EpisodeError(f"{self.period}s {text!r} must be increasing and distinct")
        return periods

    def index(self, label: str) -> int:
        if self.period == "quarter":
            m = re.fullmatch(r"(\d{4})Q([1-4])", label)
            if not m:
                raise EpisodeError(f"{label!r} is not a quarter of the form YYYYQn")
            return int(m.group(1)) * 4 + int(m.group(2)) - 1
        if not _YEAR.fullmatch(label):
            raise EpisodeError(f"{label!r} is not a year of the form YYYY")
        return int(label)

    def label(self, index: int) -> str:
        if self.period == "quarter":
            return f"{index // 4}Q{index % 4 + 1}"
        return str(index)

    def cutoff(self, label: str) -> date:
        """The last document date read for the period ``label``."""
        self.index(label)
        if self.period == "quarter":
            return hw.quarter_bounds(label)[1]
        return date(int(label) - 1, 12, 31)

    def snapshot_date(self, label: str) -> date:
        """The date of the period's snapshot: a quarter's last day, a year's 1 January."""
        if self.period == "quarter":
            return self.cutoff(label)
        self.index(label)
        return date(int(label), 1, 1)

    def label_for(self, until: date) -> str:
        """The period whose cut-off is ``until``, else the ISO date."""
        if self.period == "quarter":
            quarter = hw.quarter_of(until)
            return quarter if hw.quarter_bounds(quarter)[1] == until else until.isoformat()
        return str(until.year + 1) if (until.month, until.day) == (12, 31) else until.isoformat()


WW2 = Episode(
    name="ww2",
    title="WW2",
    scope="European politics, 1936 to 1940",
    start="1 January 1936",
    ontology=hw.DEFAULT_ONTOLOGY,
    model=hw.MODEL,
    hindsight=ROOT / "snapshots" / "ww2" / "hindsight",
    period="quarter",
    text_variables=WW2_TEXT_VARIABLES,
    resource_variables=WW2_RESOURCE_VARIABLES,
    readings=frozenset({"belief_WEST", "belief_GER", "commit_WEST", "commit_US"}),
    match_window=4,
)

CW = Episode(
    name="cw",
    title="Cold War",
    scope="the Cold War between the United States and the Soviet Union, 1947 to 1991",
    start="1 January 1947",
    ontology=ROOT / "docs" / "ontology_cw.md",
    model="cw_v0",
    hindsight=ROOT / "snapshots" / "cw" / "hindsight",
    period="year",
    text_variables=CW_TEXT_VARIABLES,
    resource_variables=(),
    readings=frozenset(CW_TEXT_VARIABLES),
    match_window=2,
    # belief_force_USA is on nuke_USSR's scale, whose thresholds are nuke_USA's
    scales=(("belief_force_USA", "nuke_USA"),),
    truth=(("belief_force_USA", "nuke_USSR"),),
)

EPISODES = {"ww2": WW2, "cw": CW}


def get_episode(episode: str | Episode | None) -> Episode:
    """The episode named ``episode`` (``None``: WW2)."""
    if isinstance(episode, Episode):
        return episode
    if episode is None:
        return WW2
    try:
        return EPISODES[episode]
    except KeyError:
        raise EpisodeError(
            f"unknown episode {episode!r} (episodes: {', '.join(EPISODES)})"
        ) from None
