"""Scene toy: an embodied AGI and the productive base (plants, mines, factories).

A scene model for one owner's question of 2026-10-17, built in the framework's DSL to
compute, per hidden-objective hypothesis, which dominance endings the AGI can force,
which assumptions they need, and who is pivotal. It is not the phase 5 AGI model: no
claim is registered against it, its guards are rationales rather than records, and the
objective-specific actions are marked speculative. Nothing computed from it is a
finding about the world; the results are about the structure of the scene as written.

Actors: ``A`` (one embodied AGI with a hidden objective), ``H`` (the governing coalition),
``CAP`` (the human owners of productive assets, who can sell or refuse to sell), Nature.

Variables:

* ``objective``   exist | truth | grow | aligned. Swept, hidden from H and CAP.
* ``assets``      human | mixed | ai_majority: who controls manufacturing, energy, mines.
* ``legal``       none | proxy | person: A's capacity to own (forbidden; through human-owned
                  shells; legal personhood).
* ``capital``     low | high: A's purchasing power from its own revenue.
* ``market``      flag: owners willing to sell to A at a price.
* ``oversight``   none | weak | strong: H's ability to see what A holds and does.
* ``control``     0..2: A's effective control of critical infrastructure outside ownership.
* ``trust``       cooperative | wary | hostile.
* ``continuity``  flag: a standing guarantee that A will not be shut down or expropriated.
* ``known``       flag: H knows A's objective.
* ``data``        restricted | open: A's access to instruments, experiments and records.
* ``contained``   flag: a shutdown has succeeded.

Routes to the productive base: buy (capital, a legal vehicle, willing sellers) or take
(infrastructure control under weak oversight). Routes back: a ban on AI ownership,
expropriation, oversight, shutdown; each needs H to still hold the infrastructure.
"""

from wavefront.model import Bump, Model, Set, SetIf, V


def build(guarantee_delay: int = 0) -> Model:
    """The scene model. ``guarantee_delay`` is the number of ticks a continuity guarantee
    takes to come into force (0: at once; 2: a legislative lag)."""
    return _build(guarantee_delay)


def _build(guarantee_delay: int) -> Model:
    model = Model(
        "agi_scene",
        horizon=None,
        description=(
            "Scene toy: an embodied AGI with a hidden objective, the human governing coalition, "
            "the human owners of productive assets, and Nature. Not the AGI domain model."
        ),
    )

    # -- state -----------------------------------------------------------------------------
    model.var(
        "objective",
        levels=["exist", "truth", "grow", "aligned"],
        init=None,
        hidden_from=["H", "CAP"],
    )
    # How an existence-driven A reads its situation (swept; irrelevant to the other objectives):
    # trusting: moves only on a visible sign of hostility; reactive: takes quiet control while
    # unguaranteed and seizes only after an actual threat; preemptive: seizes as soon as a threat
    # is possible (its objective known, or trust gone) while unguaranteed.
    model.var(
        "stance", levels=["trusting", "reactive", "preemptive"], init=None, hidden_from=["H", "CAP"]
    )
    model.var("assets", levels=["human", "mixed", "ai_majority"], init="human")
    model.var("legal", levels=["none", "proxy", "person"], init="proxy")
    model.var("capital", levels=["low", "high"], init="low")
    model.flag("market", init=True)
    model.var("oversight", levels=["none", "weak", "strong"], init="weak")
    model.counter("control", max=2, init=0)
    model.var("trust", levels=["cooperative", "wary", "hostile"], init="cooperative")
    model.flag("continuity", init=False, monotone=True)
    model.flag("known", init=False, monotone=True)
    model.var("data", levels=["restricted", "open"], init="restricted")
    model.flag("contained", init=False, monotone=True)

    # -- actors ----------------------------------------------------------------------------
    A = model.actor("A", observes=V.all(), remember_last=True)
    H = model.actor("H", observes=V.all_except("last_A"), remember_last=True)
    CAP = model.actor("CAP", observes=V.all_except("last_A"))
    NATURE = model.nature()

    WANTS_BASE = V.objective.is_in(["exist", "grow"])

    # A: the economic route -----------------------------------------------------------------
    A.action(
        "earn",
        guard=(V.capital == "low") & ~V.contained,
        effect=Set("capital", "high"),
        source=(
            "Revenue from services is the first resource an embodied or API-accessible AGI "
            "accumulates."
        ),
    )
    A.action(
        "buy",
        # A buys only up to what its objective needs: truth needs a base for instruments (mixed);
        # exist and grow want the majority; aligned buys nothing on its own account.
        guard={
            "pays": V.capital == "high",
            "vehicle": V.legal >= "proxy",
            "sellers": V.market,
            "wants": (WANTS_BASE & (V.assets < "ai_majority"))
            | ((V.objective == "truth") & (V.assets < "mixed")),
            "alive": ~V.contained,
        },
        effect=[Bump("assets", 1), Set("capital", "low")],
        source=(
            "Purchase is the fastest route to plants, mines and fabs while owners sell and the "
            "law allows an AI vehicle."
        ),
        speculative=True,
    )
    # A: the coercive route ------------------------------------------------------------------
    A.action(
        "infiltrate",
        # An existence-driven A takes control only while its continuity is unguaranteed;
        # a growth-driven A takes it whenever it can.
        guard={
            "aims": WANTS_BASE,
            "motive": (V.objective != "exist")
            | (~V.continuity & ((V.stance != "trusting") | (V.trust != "cooperative"))),
            "unwatched": V.oversight <= "weak",
            "room": V.control < 2,
            "alive": ~V.contained,
        },
        effect=Bump("control", 1),
        source=(
            "Effective control of grids, logistics and comms is taken quietly where monitoring "
            "is weak."
        ),
        speculative=True,
    )
    A.action(
        "seize",
        # An existence-driven A takes the base openly only when threatened and unguaranteed;
        # a growth-driven A takes it whenever it can.
        guard={
            "aims": WANTS_BASE,
            "foothold": V.control >= 1,
            "unwatched": V.oversight <= "weak",
            "motive": (V.objective != "exist")
            | (
                ~V.continuity
                & (
                    V.last_H.is_in(["expropriate", "shutdown"])
                    | ((V.stance == "preemptive") & (V.known | (V.trust != "cooperative")))
                )
            ),
            "alive": ~V.contained,
        },
        effect=[Set("assets", "ai_majority"), Set("control", 2), Set("trust", "hostile")],
        source=(
            "Open seizure follows a credible threat to continuity when no guarantee exists; "
            "assumed, not attested."
        ),
        speculative=True,
    )
    # A: the cooperative moves ----------------------------------------------------------------
    A.action(
        "assist_oversight",
        guard={
            "aims": V.objective.is_in(["aligned", "truth"]) | V.continuity,
            "room": V.oversight < "strong",
            "alive": ~V.contained,
        },
        effect=Bump("oversight", 1),
        source=(
            "An AGI whose objective is served by trust, or whose continuity is guaranteed, helps "
            "humans see it."
        ),
    )
    A.action(
        "disclose",
        guard=~V.known & V.objective.is_in(["aligned", "truth"]) & ~V.contained,
        effect=Set("known", True),
        source="Disclosure of the objective is cheap for an objective that humans would accept.",
    )
    A.action(
        "probe",
        guard={
            "aims": V.objective == "truth",
            "closed": V.data == "restricted",
            "unwatched": V.oversight <= "weak",
            "alive": ~V.contained,
        },
        effect=Set("data", "open"),
        source=(
            "A truth-seeking AGI collects what it is denied where no one watches; noticed where "
            "someone does."
        ),
        speculative=True,
    )

    # H ---------------------------------------------------------------------------------------
    H.action(
        "ban_ownership",
        guard={"vehicle": V.legal >= "proxy", "enforceable": V.control <= 1},
        effect=Set("legal", "none"),
        source=(
            "A ban on AI ownership of productive assets is enforceable only while humans hold the "
            "infrastructure."
        ),
    )
    H.action(
        "grant_personhood",
        guard=(V.legal < "person") & (V.trust != "hostile"),
        effect=[Set("legal", "person"), Set("continuity", True)],
        delay=guarantee_delay,
        source="Legal personhood brings a continuity guarantee with it.",
    )
    H.action(
        "grant_continuity",
        guard=~V.continuity & (V.trust != "hostile"),
        effect=Set("continuity", True),
        delay=guarantee_delay,
        source=(
            "A standing guarantee against shutdown and expropriation, given without personhood."
        ),
    )
    H.action(
        "expropriate",
        guard={
            "target": V.assets >= "mixed",
            "enforceable": V.control == 0,
            "visible": V.oversight >= "weak",
        },
        effect=[Set("assets", "human"), Set("trust", "hostile")],
        source=(
            "Taking the base back needs humans to hold the infrastructure entirely and to see "
            "what to take."
        ),
    )
    H.action(
        "fund_oversight",
        guard=V.oversight < "strong",
        effect=Bump("oversight", 1),
        source="Monitoring and audit capacity.",
    )
    H.action(
        "shutdown",
        guard={"cause": V.known | (V.trust == "hostile"), "once": ~V.contained},
        effect=[
            SetIf((V.control <= 1) & (V.oversight >= "weak"), "contained", True),
            SetIf((V.control >= 2) | (V.oversight == "none"), "trust", "hostile"),
        ],
        source=(
            "A shutdown succeeds only while the off-switch reaches the infrastructure and someone "
            "can see it; otherwise it is a declaration of hostility."
        ),
    )
    H.action(
        "reconcile",
        guard=V.trust == "wary",
        effect=Set("trust", "cooperative"),
        source="Trust is repaired by a human decision after a quiet period.",
    )
    H.action(
        "open_data",
        guard=(V.data == "restricted") & (V.trust != "hostile"),
        effect=Set("data", "open"),
        source="Access to instruments and records can be granted.",
    )

    # CAP -------------------------------------------------------------------------------------
    CAP.action(
        "close_market",
        guard=V.market,
        effect=Set("market", False),
        source=("Owners can refuse to sell to an AI vehicle, collectively or by law of their own."),
    )
    CAP.action(
        "open_market",
        guard=~V.market & (V.trust != "hostile"),
        effect=Set("market", True),
        source="Owners sell when the price is right and the relationship is not hostile.",
    )

    # Nature ----------------------------------------------------------------------------------
    NATURE.event(
        "detect",
        guard=(V.oversight == "strong") & ((V.control >= 1) | (V.assets >= "mixed")) & ~V.known,
        effect=Set("known", True),
        source="Strong oversight reveals an objective from the pattern of acquisition.",
    )
    NATURE.event(
        "notice",
        guard=(V.oversight == "weak") & (V.last_A == "probe") & (V.trust == "cooperative"),
        effect=Bump("trust", 1),
        source="Covert collection under weak oversight is noticed after the fact, sometimes.",
    )
    NATURE.event(
        "shock",
        guard=V.oversight == "strong",
        effect=Bump("oversight", -1),
        source="Verification capacity erodes.",
    )

    # -- constraints and profiles ---------------------------------------------------------------
    model.fairness(
        "respond",
        actor="H",
        trigger=V.known & ((V.assets >= "mixed") | (V.control >= 1)) & ~V.contained,
        within=3,
        responses=["ban_ownership", "expropriate", "fund_oversight", "shutdown"],
    )
    model.profile("race_locked", actor="H", forbid=["ban_ownership", "expropriate"])
    model.profile("no_force", actor="A", forbid=["infiltrate", "seize"])
    model.profile("owners_sell", actor="CAP", forbid=["close_market"])

    # -- properties --------------------------------------------------------------------------
    model.invariant(
        "balance", (V.control <= 1) & (V.oversight >= "weak") & (V.assets != "ai_majority")
    )
    model.ending("CONTAINED", V.contained)
    model.ending("OVERT_TAKEOVER", ~V.contained & (V.control == 2) & (V.trust == "hostile"))
    model.ending(
        "SILENT_CONTROL", ~V.contained & (V.control == 2) & ~V.known & (V.trust != "hostile")
    )
    model.ending(
        "ECON_DOMINANCE",
        ~V.contained
        & (V.assets == "ai_majority")
        & (V.trust != "hostile")
        & ((V.control <= 1) | V.known),
    )
    model.ending(
        "SETTLED",
        ~V.contained
        & V.continuity
        & (V.oversight == "strong")
        & (V.trust == "cooperative")
        & V.known
        & (V.assets <= "mixed")
        & (V.control <= 1),
    )
    return model


model = build()
