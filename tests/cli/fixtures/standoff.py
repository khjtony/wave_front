"""A small fixture model for the CLI tests: two actors, a deal and a war."""

from wavefront.model import Bump, Model, Set, V


def build():
    m = Model("standoff", horizon=4)
    m.counter("tension", max=3, init=0)
    m.flag("deal", init=False)
    a = m.actor("A")
    b = m.actor("B")
    a.action("provoke", effect=Bump("tension", +1), source="fixture", speculative=True)
    a.action("negotiate", guard=V.tension >= 1, effect=Bump("tension", -1), source="fixture")
    b.action("provoke", effect=Bump("tension", +1), source="fixture")
    b.action("sign", guard=V.tension <= 1, effect=Set("deal", True), source="fixture")
    m.nature().event("incident", guard=V.tension >= 2, effect=Bump("tension", +1))
    m.invariant("calm", V.tension <= 2)
    m.ending("WAR", V.tension == 3)
    m.ending("DEAL", V.deal)
    return m


model = build()
