"""Hand-built games with known answers, shared by the analysis, report and CLI tests."""

from wavefront.model import Bump, Model, Set, V


def ladder(shielded=True):
    """Untimed. Nature may push x up by one each tick; P may pull it down by one while
    ``shield`` holds. Invariant ``low``: x <= 2; ``always`` holds everywhere.

    K_P(low) = {x <= 2} while shielded; the empty coalition's kernel is empty."""
    m = Model("ladder", horizon=None)
    m.counter("x", max=4, init=0)
    m.flag("shield", init=shielded)
    p = m.actor("P")
    p.action("pull", guard=V.shield, effect=Bump("x", -1))
    n = m.nature()
    n.event("push", effect=Bump("x", +1))
    m.invariant("low", V.x <= 2)
    m.invariant("always", V.x <= 4)
    return m


def tug():
    """Untimed. Nature pushes x up by two; A and B may each pull it down by one. Only
    both together hold x where it is. Invariant ``low``: x <= 2."""
    m = Model("tug", horizon=None)
    m.counter("x", max=4, init=0)
    a = m.actor("A")
    b = m.actor("B")
    a.action("pull", effect=Bump("x", -1))
    b.action("pull", effect=Bump("x", -1))
    m.nature().event("push", effect=Bump("x", +2))
    m.invariant("low", V.x <= 2)
    return m


def crisis():
    """Untimed escalation game with a silent phase.

    calm -(P provokes)-> tense: P and Nature guess simultaneously (matching pennies). A
    match lets Nature calm things down; a mismatch lets Nature escalate to crisis and then
    to war (ending WAR). Invariant ``peace``: pos != war. In calm P can wait forever."""
    m = Model("crisis", horizon=None)
    m.var("pos", levels=["calm", "tense", "crisis", "war"])
    m.var("pg", levels=["none", "h", "t"])
    m.var("ng", levels=["none", "h", "t"])
    p = m.actor("P", idle=False)
    p.action("provoke", guard=V.pos == "calm", effect=Set("pos", "tense"), source="test")
    p.action("wait", guard=(V.pos != "tense") | (V.pg != "none"), source="test")
    for side in ("h", "t"):
        p.action(
            f"guess_{side}", guard=(V.pos == "tense") & (V.pg == "none"), effect=Set("pg", side)
        )
    n = m.nature()
    for side in ("h", "t"):
        n.event(
            f"guess_{side}",
            guard=(V.pos == "tense") & (V.ng == "none") & (V.pg == "none"),
            effect=Set("ng", side),
        )
    n.event(
        "settle",
        guard=(V.pos == "tense") & (V.pg != "none") & (V.pg == V.ng),
        effect=[Set("pos", "calm"), Set("pg", "none"), Set("ng", "none")],
    )
    n.event(
        "escalate",
        guard=(V.pos == "tense") & (V.pg != "none") & (V.ng != "none") & (V.pg != V.ng),
        effect=Set("pos", "crisis"),
        speculative=True,
    )
    n.event("attack", guard=V.pos == "crisis", effect=Set("pos", "war"))
    m.invariant("peace", V.pos != "war")
    m.ending("WAR", V.pos == "war")
    return m


def coin(hidden=True):
    """One round: a coin is h or t (both initial states); P calls it. WIN on a correct
    call, LOSE otherwise. With ``hidden`` P does not observe the coin."""
    m = Model("coin", horizon=1)
    m.var("coin", levels=["h", "t"], init=None, hidden_from=["P"] if hidden else [])
    m.var("call", levels=["h", "t"])
    m.flag("called", init=False)
    p = m.actor("P", idle=False)
    p.action("call_h", effect=[Set("call", "h"), Set("called", True)])
    p.action("call_t", effect=[Set("call", "t"), Set("called", True)])
    m.ending("WIN", V.called & (V.call == V.coin))
    m.ending("LOSE", V.called & (V.call != V.coin))
    return m


def locks(with_alt=False, with_clash=False):
    """DONE needs A.go and B.go, whose guards never hold; C.alt (guard never holds) would
    do both at once. With ``with_clash`` relaxing D.clash makes two Sets conflict."""
    m = Model("locks", horizon=3)
    m.flag("key", init=False)
    m.flag("a_done", init=False)
    m.flag("b_done", init=False)
    m.var("v", levels=["a", "b", "c"])
    a = m.actor("A")
    b = m.actor("B")
    a.action("go", guard=V.key, effect=Set("a_done", True), source="test")
    b.action("go", guard=V.key, effect=Set("b_done", True), source="test")
    if with_alt:
        c = m.actor("C")
        c.action(
            "alt", guard=V.key, effect=[Set("a_done", True), Set("b_done", True)], speculative=True
        )
    if with_clash:
        d = m.actor("D")
        d.action("clash", guard=V.key, effect=Set("v", "b"))
        m.nature().event("drift", effect=Set("v", "c"))
    m.ending("DONE", V.a_done & V.b_done)
    return m


def door():
    """Nature may open a door at any tick; A can walk through an open door (ending OUT).
    A fairness constraint forces Nature to open within one tick of it being shut."""
    m = Model("door", horizon=3)
    m.flag("open", init=False)
    m.flag("out", init=False)
    a = m.actor("A")
    a.action("walk", guard=V.open, effect=Set("out", True), source="test")
    n = m.nature()
    n.event("open_it", guard=~V.open, effect=Set("open", True))
    m.fairness("nature_opens", actor="Nature", trigger=~V.open, within=1, responses=["open_it"])
    m.ending("OUT", V.out)
    return m


def relay():
    """One round: a coin is h or t (both initial states). A sees the coin, B does not;
    B must call it (WIN on a correct call). A can do nothing useful."""
    m = Model("relay", horizon=1)
    m.var("coin", levels=["h", "t"], init=None, hidden_from=["B"])
    m.var("call", levels=["h", "t"])
    m.flag("called", init=False)
    m.actor("A")
    b = m.actor("B", idle=False)
    b.action("call_h", effect=[Set("call", "h"), Set("called", True)])
    b.action("call_t", effect=[Set("call", "t"), Set("called", True)])
    m.ending("WIN", V.called & (V.call == V.coin))
    m.ending("LOSE", V.called & (V.call != V.coin))
    return m
