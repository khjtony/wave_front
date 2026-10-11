"""A fixture model that fails at explore time: Q runs out of actions."""

from wavefront.model import Bump, Model, V

model = Model("broken", horizon=3)
model.counter("x", max=2, init=0)
q = model.actor("Q", idle=False)
q.action("step", guard=V.x == 0, effect=Bump("x", +1))
