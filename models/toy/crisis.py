"""A domain-neutral standoff with one crisis sub-game: the multi-resolution example.

Two powers, ``EAST`` and ``WEST``, and Nature play a coarse game in years; one coarse action,
``EAST.crisis``, stands for a sub-game of three days of escalation and standing down whose
outcome returns to the coarse game as a settled or a broken standoff (or, if the three days
pass without either, as the open standoff it started from, one year later). The model
exercises :func:`wavefront.engine.flatten` and the engine on a flattened game
(``tests/toy/test_crisis.py``). It is not a domain model, its numbers carry no evidence, and
nothing computed from it is a finding about any real system.

Coarse game ``standoff`` (horizon 4 years):

* ``rivalry``  calm | tense.
* ``status``   open | settled | broken. Set only by the crisis's exit map.
* ``arms``     0..2. WEST's arsenal; at 2 a crisis starts at high escalation.

* ``WEST.build``     arms +1 while the standoff is open.
* ``EAST.provoke``   calm to tense while the standoff is open.
* ``EAST.crisis``    the crisis move (no effect of its own): open and tense only.
* ``Nature.thaw``    tense back to calm while the standoff is open.

Endings ``WAR`` (status broken) and ``DETENTE`` (status settled); invariant ``no_war``.

Sub-game ``standoff_crisis`` (horizon 3 days):

* ``esc``        low | high | brink. Entry: high if WEST's arms are at 2, else low.
* ``withdrawn``  flag, EAST's withdrawal; starts False.

* ``EAST.escalate``, ``WEST.escalate``  esc +1.
* ``EAST.stand_down``  withdraw (one-shot).
* ``WEST.stand_down``  esc -1.
* ``Nature.incident``  esc +1 at high escalation: an accident nobody chose.

Endings ``BRINK`` (esc at brink) and ``WITHDRAWAL`` (withdrawn below the brink). Exit: BRINK
breaks the standoff (``status = broken``), WITHDRAWAL settles it (``status = settled``,
``rivalry = calm``), and a crisis that runs out its three days changes nothing.

Every action carries a one-sentence rationale as its ``source``; the toy has no speculative
action.
"""

from wavefront.engine import Crisis, flatten
from wavefront.engine.multires import FlatModel
from wavefront.model import Bump, Model, Set, V

SRC = "toy mechanism: "

coarse = Model(
    "standoff",
    horizon=4,
    description=(
        "Domain-neutral two-power standoff in years with one crisis sub-game in days. An "
        "example for multi-resolution time, not a model of any real system."
    ),
)
coarse.var("rivalry", levels=["calm", "tense"], init="calm")
coarse.var("status", levels=["open", "settled", "broken"], init="open")
coarse.counter("arms", max=2, init=0)

EAST = coarse.actor("EAST")
WEST = coarse.actor("WEST")
N = coarse.nature()

WEST.action(
    "build",
    guard=(V.status == "open") & (V.arms < 2),
    effect=[Bump("arms", +1)],
    source=SRC + "an arsenal grows while the standoff lasts",
)
EAST.action(
    "provoke",
    guard=(V.status == "open") & (V.rivalry == "calm"),
    effect=[Set("rivalry", "tense")],
    source=SRC + "a challenge turns a calm rivalry tense",
)
EAST.action(
    "crisis",
    guard=(V.status == "open") & (V.rivalry == "tense"),
    effect=[],
    source=SRC + "a tense rivalry can be pushed into a crisis; its effect is the sub-game",
)
N.event(
    "thaw",
    guard=(V.status == "open") & (V.rivalry == "tense"),
    effect=[Set("rivalry", "calm")],
    source=SRC + "tension can subside on its own",
)

coarse.invariant("no_war", V.status != "broken")
coarse.ending("WAR", V.status == "broken")
coarse.ending("DETENTE", V.status == "settled")


fine = Model(
    "standoff_crisis",
    horizon=3,
    description="The crisis sub-game of the standoff toy: three days of escalation.",
)
fine.var("esc", levels=["low", "high", "brink"], init="low")
fine.flag("withdrawn", init=False)

F_EAST = fine.actor("EAST")
F_WEST = fine.actor("WEST")
F_N = fine.nature()

F_EAST.action(
    "escalate",
    guard=~V.withdrawn,
    effect=[Bump("esc", +1)],
    source=SRC + "either side can raise the stakes for a day",
)
F_EAST.action(
    "stand_down",
    guard=~V.withdrawn,
    effect=[Set("withdrawn", True)],
    source=SRC + "the side that started the crisis can withdraw",
)
F_WEST.action(
    "escalate",
    effect=[Bump("esc", +1)],
    source=SRC + "either side can raise the stakes for a day",
)
F_WEST.action(
    "stand_down",
    effect=[Bump("esc", -1)],
    source=SRC + "the other side can lower the stakes for a day",
)
F_N.event(
    "incident",
    guard=V.esc == "high",
    effect=[Bump("esc", +1)],
    source=SRC + "at high escalation an accident can take the crisis to the brink",
)

fine.ending("BRINK", V.esc == "brink")
fine.ending("WITHDRAWAL", V.withdrawn & (V.esc != "brink"))


def entry(state: dict[str, str]) -> dict[str, object]:
    """The crisis starts at high escalation when WEST's arsenal is full."""
    return {"esc": "high" if state["arms"] == "2" else "low"}


def exit_map(day: dict[str, str], year: dict[str, str]) -> dict[str, object]:
    """BRINK breaks the standoff, WITHDRAWAL settles it, a crisis that runs out changes
    nothing."""
    if day["esc"] == "brink":
        return {"status": "broken"}
    if day["withdrawn"] == "True":
        return {"status": "settled", "rivalry": "calm"}
    return {}


def flat() -> FlatModel:
    """The flattened standoff: the coarse game with its crisis sub-game inlined."""
    crisis = Crisis("EAST", "crisis", fine.compile(), entry, exit_map, name="standoff_crisis")
    return flatten(coarse.compile(), [crisis])
