"""Draft 1 of the two-power toy model (experiment)."""

from wavefront.model import Bump, Inc, Model, Set, SetIf, V

m = Model("two_power", horizon=12, description="draft")

m.var("aims", levels=["limited", "hegemonic"], init=None, hidden_from=["INC"])
m.counter("control", max=3, init=0)
m.var("tension", levels=["calm", "crisis"], init=None, monotone=True)
m.var("oversight", levels=["none", "weak", "strong"], init="weak")
m.var("belief", levels=["limited", "uncertain", "hegemonic"], init="uncertain")
m.flag("guarantee", init=False, monotone=True)
m.latch("belief_at_majority", of="belief", when=V.control >= 2)

CH = m.actor("CH", observes=V.all(), remember_last=True)
INC = m.actor("INC", observes=V.all_except("last_CH"), remember_last=True)
N = m.nature()

CH.action(
    "expand",
    guard=(V.tension == "calm")
    & (V.control < 3)
    & ((V.aims == "hegemonic") | (V.control < 1)),
    effect=Inc("control"),
    source="r",
)
CH.action(
    "deceive",
    guard=V.aims == "hegemonic",
    effect=SetIf(V.oversight < "strong", "belief", "limited"),
    source="r",
)
CH.action(
    "defect",
    guard=(V.aims == "hegemonic") & (V.last_INC == "resist") & ~V.guarantee & (V.control < 3),
    effect=[Bump("control", 1), Set("tension", "crisis")],
    source="r",
    speculative=True,
)

INC.action("concede", guard=~V.guarantee & (V.belief <= "uncertain"), effect=Set("guarantee", True), source="r")
INC.action("resist", guard=V.belief >= "uncertain", effect=Set("tension", "crisis"), source="r")
INC.action("fund_oversight", effect=Bump("oversight", 1), delay=2, source="r")

N.event("detect", guard=(V.oversight == "strong") & (V.last_CH == "deceive"), effect=Bump("belief", 1), source="r")
N.event("shock", guard=V.oversight == "strong", effect=Bump("oversight", -1), source="r")

m.fairness(
    "respond",
    actor="INC",
    trigger=(V.belief == "hegemonic") & (V.control >= 1),
    within=3,
    responses=["resist", "fund_oversight"],
)
m.profile("appeaser", actor="INC", forbid=["resist"])
m.assume("calm_start", V.tension == "calm")

m.invariant("balance", (V.control <= 1) & (V.oversight >= "weak"))
m.ending("TAKEOVER", V.control == 3)
m.ending(
    "SETTLED",
    V.guarantee & (V.aims == "limited") & (V.control == 1) & (V.tension == "calm"),
)
m.ending(
    "CONTAINED",
    (V.tension == "crisis") & (V.oversight == "strong") & (V.belief == "hegemonic") & (V.control <= 2),
)
m.ending(
    "COEXIST",
    (V.tick == m.horizon) & V.invariant("balance") & ~V.ending("SETTLED") & ~V.ending("CONTAINED"),
)

model = m
