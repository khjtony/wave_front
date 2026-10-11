"""A domain-neutral two-power game: the framework's worked example.

A challenger ``CH`` with a hidden objective, an incumbent ``INC`` that cannot see that
objective, and Nature. The model exists to exercise the DSL and to give the engine something
to demonstrate (``tests/toy/test_two_power.py``). It is not a domain model, its numbers carry
no evidence, and nothing computed from it is a finding about any real system.

Reading the variables (``control`` plays the part of a four-step ladder: 0 none, 1 partial,
2 majority, 3 total):

=============  ==========================  =============================================
variable       levels                      meaning
=============  ==========================  =============================================
aims           limited, hegemonic          CH's objective; swept; hidden from INC
control        0..3                        how much of the contested domain CH holds
tension        calm, crisis                open confrontation; a one-way ratchet
oversight      none, weak, strong          INC's ability to verify what CH does
belief         limited, uncertain,         INC's belief about CH's aims
               hegemonic
guarantee      False, True                 INC's standing guarantee of continuity
belief_at_     unset + belief levels       latch: INC's belief when control first hit 2
majority
=============  ==========================  =============================================

Actions (one per actor per tick, chosen simultaneously; every actor may also ``idle``):

* ``CH.expand``     raise control by one; a limited CH stops at control 1; needs calm.
* ``CH.deceive``    hegemonic only; lowers INC's belief to ``limited`` unless oversight is
  ``strong``, which is when Nature's ``detect`` can catch it.
* ``CH.defect``     hegemonic only; an overt grab (control +1, crisis) available for one tick
  after INC resisted, and only while INC has given no guarantee. Speculative.
* ``INC.concede``   grant the guarantee (one-shot; not once INC is convinced).
* ``INC.resist``    set tension to crisis; this freezes ``expand`` for good.
* ``INC.fund_oversight``  raise oversight one level, visible three ticks later (delay 2).
* ``Nature.detect`` raise INC's belief one level when oversight is strong and CH deceived
  in the previous tick.
* ``Nature.shock``  lower strong oversight to weak.

Endings (mutually exclusive on every state, not only on reachable ones):

* ``TAKEOVER``   control is 3.
* ``SETTLED``    guarantee given, aims limited, control 1, still calm.
* ``CONTAINED``  crisis, strong oversight, INC convinced, control at most 2.
* ``COEXIST``    the horizon arrives with ``balance`` intact and no other ending reached.
  A state at the horizon that satisfies none of them is reported as ``HORIZON``.

``balance`` is control at most 1 with oversight at least weak. It mirrors the "balance"
invariant of the worked example in DESIGN.md section 7; the latch mirrors its "known at
majority" latch.

What the toy is built to show, each asserted in ``tests/toy/test_two_power.py`` as an
engine demonstration:

* ``SETTLED`` is reachable only when aims are limited, ``TAKEOVER`` only when they are
  hegemonic; INC and CH together can force a settlement, neither alone can.
* Facing an ``appeaser`` INC (never resists), CH can force ``TAKEOVER``; facing the default
  INC it cannot: INC can block it, but only by resisting at tick 0.
* INC's viability kernel for ``balance`` contains the limited-aims start and excludes the
  hegemonic one; granting the guarantee beforehand puts the hegemonic start inside it.
* The two initial states look identical to INC, and no first move both keeps the block
  against a hegemonic CH and keeps a settlement open with a limited one.
* A belief flip (``detect``) is followed by a forced INC response within the fairness bound.

The ``calm_start`` assumption is the one model assumption. The DSL applies every ``assume``
by default, so it must hold in the default initial states: ``tension`` is swept (declared
with ``init=None``) and ``calm_start`` keeps only its calm level, giving two initial states,
one per level of ``aims``. Relaxing it (``compile(model, relax={"calm_start"})``) widens the
initial set to four by adding the starts that are already in crisis.
"""

from wavefront.model import Bump, Inc, Ite, Model, Set, SetIf, V

model = Model(
    "two_power",
    horizon=12,
    description=(
        "Domain-neutral two-power game for exercising the framework: a challenger with a "
        "hidden objective, an incumbent that cannot see it, and Nature. An example, not a "
        "domain model."
    ),
)

# -- state -----------------------------------------------------------------------------
model.var("aims", levels=["limited", "hegemonic"], init=None, hidden_from=["INC"])
model.counter("control", max=3, init=0)
model.var("tension", levels=["calm", "crisis"], init=None, monotone=True)
model.var("oversight", levels=["none", "weak", "strong"], init="weak")
model.var("belief", levels=["limited", "uncertain", "hegemonic"], init="uncertain")
model.flag("guarantee", init=False, monotone=True)
model.latch("belief_at_majority", of="belief", when=V.control >= 2)

# -- actors ----------------------------------------------------------------------------
# CH sees everything. INC cannot see CH's aims (hidden_from) nor CH's last action, so a
# deception is invisible to it unless Nature detects it.
CH = model.actor("CH", observes=V.all(), remember_last=True)
INC = model.actor("INC", observes=V.all_except("last_CH"), remember_last=True)
NATURE = model.nature()

CH.action(
    "expand",
    # The ceiling on control depends on aims: a limited CH stops at 1, a hegemonic one at 3.
    guard=(V.tension == "calm") & (V.control < Ite(V.aims == "hegemonic", 3, 1)),
    effect=Inc("control"),
    source="Incremental accumulation is the cheapest route while the status quo is undisturbed.",
)
CH.action(
    "deceive",
    guard=V.aims == "hegemonic",
    effect=SetIf(V.oversight < "strong", "belief", "limited"),
    source="Concealed intent stays concealed only while the observer cannot verify.",
)
CH.action(
    "defect",
    guard=(V.aims == "hegemonic") & (V.last_INC == "resist") & ~V.guarantee & (V.control < 3),
    effect=[Bump("control", 1), Set("tension", "crisis")],
    source="A challenger that expects containment strikes openly unless a guarantee protects "
    "the status quo; assumed, not attested.",
    speculative=True,
)

INC.action(
    "concede",
    guard=~V.guarantee & V.belief.is_in(["limited", "uncertain"]),
    effect=Set("guarantee", True),
    source="A standing guarantee of continuity removes the motive to strike first.",
)
INC.action(
    "resist",
    guard=V.belief.is_in(["uncertain", "hegemonic"]),
    effect=Set("tension", "crisis"),
    source="Visible pushback freezes quiet accumulation at the price of open confrontation.",
)
INC.action(
    "fund_oversight",
    effect=Bump("oversight", 1),
    delay=2,
    source="Verification capacity takes two ticks to build (staffing and procurement lag).",
)

NATURE.event(
    "detect",
    guard=(V.oversight == "strong") & (V.last_CH == "deceive"),
    effect=Bump("belief", 1),
    source="Concealment is caught only where verification exists, and only after the fact.",
)
NATURE.event(
    "shock",
    guard=V.oversight == "strong",
    effect=Bump("oversight", -1),
    source="Verification capacity erodes through budget cuts, turnover and outages.",
)

# -- constraints and assumptions ---------------------------------------------------------
# INC must answer within three ticks once it believes the worst and CH has a foothold.
model.fairness(
    "respond",
    actor="INC",
    trigger=(V.belief == "hegemonic") & (V.control >= 1),
    within=3,
    responses=["resist", "fund_oversight"],
)
# An incumbent that never pushes back; inert unless selected with compile(profile="appeaser").
model.profile("appeaser", actor="INC", forbid=["resist"])
# The default initial states are calm; relaxing this adds the starts that are in crisis.
model.assume("calm_start", V.tension == "calm")

# -- properties --------------------------------------------------------------------------
model.invariant("balance", (V.control <= 1) & (V.oversight >= "weak"))
model.ending("TAKEOVER", V.control == 3)
model.ending(
    "SETTLED",
    V.guarantee & (V.aims == "limited") & (V.control == 1) & (V.tension == "calm"),
)
model.ending(
    "CONTAINED",
    (V.tension == "crisis")
    & (V.oversight == "strong")
    & (V.belief == "hegemonic")
    & (V.control <= 2),
)
model.ending(
    "COEXIST",
    (V.tick == model.horizon)
    & V.invariant("balance")
    & ~V.ending("SETTLED")
    & ~V.ending("CONTAINED"),
)
