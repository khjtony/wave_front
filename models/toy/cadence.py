"""A fast actor against a slow one: the decision cadence (spec 3.1) on a toy.

An automated actor ``FAST`` decides every tick; an institution ``SLOW`` decides at most once
every ``slow_cadence`` ticks (``m.actor("SLOW", cadence=k)``): after a decision it can only
``idle`` for ``k - 1`` ticks. The model exists to show what the cadence changes
(``tests/toy/test_cadence.py``). It is not a domain model, its numbers carry no evidence, and
nothing computed from it is a finding about any real system.

Variable: ``exposure`` 0..3, how far FAST has extended an unreviewed deployment.

Actions (simultaneous, one per actor per tick; both may ``idle``; Nature only has ``none``):

* ``FAST.advance``    exposure +1.
* ``SLOW.roll_back``  exposure -1, once there is something to roll back (exposure >= 1).

Both moves in one tick cancel (the Bumps are summed). Ending ``OVERRUN``: exposure 3.
Invariant ``contained``: exposure at most 1.

What the toy is built to show, asserted in ``tests/toy/test_cadence.py`` as engine
demonstrations: with ``slow_cadence=1`` SLOW alone keeps ``contained`` from the start and
blocks ``OVERRUN``, by rolling back every tick; with ``slow_cadence=3`` the same SLOW cannot,
and FAST alone forces ``OVERRUN`` within four ticks, because every rollback buys FAST two
unopposed ticks.
"""

from wavefront.model import Bump, Model, V

HORIZON = 6
SOURCE = "toy mechanism, no evidence: "


def build(slow_cadence: int = 3) -> Model:
    """The toy with SLOW deciding at most once every ``slow_cadence`` ticks."""
    m = Model(
        "cadence",
        horizon=HORIZON,
        description=(
            "Toy for the decision cadence: a fast actor extends a deployment every tick, a "
            "slow one can roll it back at most once every few ticks. An example, not a "
            "domain model."
        ),
    )
    m.counter("exposure", max=3, init=0)
    fast = m.actor("FAST")
    slow = m.actor("SLOW", cadence=slow_cadence)
    fast.action(
        "advance",
        effect=Bump("exposure", 1),
        source=SOURCE + "the fast actor extends its deployment by one step per decision",
    )
    slow.action(
        "roll_back",
        guard=V.exposure >= 1,
        effect=Bump("exposure", -1),
        source=SOURCE + "the slow actor reviews and reverses one step per decision",
    )
    m.invariant("contained", V.exposure <= 1)
    m.ending("OVERRUN", V.exposure == 3)
    return m


model = build()
