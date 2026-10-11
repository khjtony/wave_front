"""Engine demonstrations on the domain-neutral two-power toy model.

These are demonstrations, not findings. Each test asserts what the engine computes on
``models/toy/two_power.py`` to show that reachability, forcing, blocking, viability kernels,
the contested region, witness traces and bounded fairness behave as the framework intends
on a model small enough to read by hand. Nothing here says anything about a real system, and
if the toy model is edited the numbers here are expected to change with it. Each test's
docstring says what the model intends; its assertions say what the engine answers.
"""

import pytest

from models.toy.two_power import model
from wavefront.engine import attractor, contested, explore, safe, witness
from wavefront.model import V

ENDINGS = ["TAKEOVER", "SETTLED", "CONTAINED", "COEXIST"]


# -- helpers ----------------------------------------------------------------------------


class World:
    """A compiled toy model with its explored graph and the lookups the tests need."""

    def __init__(self, profile=None, relax=(), **start):
        self.cm = model.compile(profile=profile, relax=relax)
        if start:
            aims = start.pop("aims")
            self.g = explore(self.cm, initial=[state_from(self.cm, aims, **start)])
        else:
            self.g = explore(self.cm)
        self.everyone = set(self.cm.actor_names)

    def level(self, state_id, name):
        return self.cm.level_name(name, self.g.states[state_id][self.cm.index[name]])

    def start(self, aims):
        """The initial state id with the given aims (the only one in a single-start world)."""
        (found,) = [i for i in self.g.initial if self.level(i, "aims") == aims]
        return found

    def ending(self, name):
        return self.g.ending_states(name)

    def where(self, expr):
        return self.g.states_where(expr)

    def reach(self, target):
        """States from which all actors, Nature included, can reach the target."""
        return attractor(self.g, self.everyone, target).win

    def force(self, coalition, target):
        return attractor(self.g, coalition, target).win

    def keep(self, coalition, phi):
        return safe(self.g, coalition, phi).kernel

    def everything_but(self, states):
        return set(range(self.g.size())) - set(states)


def state_from(cm, aims, **levels):
    """The initial state with these aims, with some variables overridden by level name or
    integer (the state is used as given: no ``assume`` filter, no latch update)."""
    (base,) = [s for s in cm.initial_states() if cm.level_name("aims", s[cm.index["aims"]]) == aims]
    state = list(base)
    for name, value in levels.items():
        spec = cm.variables[cm.index[name]]
        state[cm.index[name]] = spec.levels.index(value) if isinstance(value, str) else int(value)
    return tuple(state)


def joint(cm, **chosen):
    """A joint move by action name; actors not named play their built-in action."""
    return tuple(
        actor.action_index(chosen[actor.name]) if actor.name in chosen else 0 for actor in cm.actors
    )


def available(cm, state, actor):
    """Names of the actions ``actor`` can take in ``state``."""
    spec = next(a for a in cm.actors if a.name == actor)
    return {spec.actions[j].name for j in cm.available(state)[spec.index]}


def safe_first_moves(world, kernel, state_id, actor):
    """Actions of ``actor`` in a state such that every completion stays inside ``kernel``."""
    index = next(a.index for a in world.cm.actors if a.name == actor)
    ok: dict[int, bool] = {}
    for move, successor in zip(world.g.moves[state_id], world.g.succ[state_id], strict=True):
        ok[move[index]] = ok.get(move[index], True) and successor in kernel
    spec = world.cm.actors[index]
    return {spec.actions[j].name for j, good in ok.items() if good}


@pytest.fixture(scope="module")
def default():
    return World()


@pytest.fixture(scope="module")
def appeaser():
    return World(profile="appeaser")


# -- the model and its size ---------------------------------------------------------------


def test_compiles_with_the_declared_layout_and_budget(default):
    """Every construct the toy is meant to exercise is present, and counted."""
    cm = default.cm
    assert cm.actor_names == ["CH", "INC", "Nature"]
    assert [v.name for v in cm.variables] == [
        "tick",
        "aims",
        "control",
        "tension",
        "oversight",
        "belief",
        "guarantee",
        "belief_at_majority",
        "pending_INC_fund_oversight",
        "last_CH",
        "last_INC",
        "fair_respond",
    ]
    assert cm.horizon == 12
    budget = cm.budget()
    expected = {
        "variables": 6,
        "actors": 3,
        "actions": 8,
        "guards": 7,
        "speculative_actions": 1,
        "fairness_constraints": 1,
        "delays": 1,
        "latches": 1,
        "invariants": 1,
        "endings": 4,
    }
    assert {k: budget[k] for k in expected} == expected
    assert cm.assumptions() == [
        "CH.expand",
        "CH.deceive",
        "CH.defect",
        "INC.concede",
        "INC.resist",
        "Nature.detect",
        "Nature.shock",
        "respond",
        "calm_start",
    ]
    assert model.compile(profile="appeaser").assumptions()[-2:] == ["appeaser", "calm_start"]


def test_every_action_carries_a_rationale_and_only_defect_is_speculative(default):
    declared = [a for actor in default.cm.actors for a in actor.actions if not a.is_idle]
    assert all(a.source.strip() for a in declared)
    assert [f"{a.actor}.{a.name}" for a in declared if a.speculative] == ["CH.defect"]


def test_the_objective_is_hidden_from_inc_and_so_is_chs_last_action(default):
    cm = default.cm
    ch, inc, nature = (a.observes for a in cm.actors)
    assert "aims" in ch and "last_CH" in ch
    assert "aims" not in inc and "last_CH" not in inc and "belief" in inc
    assert "aims" in nature
    for name in ("tension", "guarantee"):
        assert cm.variables[cm.index[name]].monotone


def test_the_reachable_state_space_is_small(default, appeaser):
    assert default.g.size() < 20_000
    assert appeaser.g.size() < default.g.size()


def test_two_initial_states_one_per_objective(default):
    states = default.cm.initial_states()
    assert len(states) == 2
    assert {default.level(i, "aims") for i in default.g.initial} == {"limited", "hegemonic"}
    assert all(default.level(i, "tension") == "calm" for i in default.g.initial)


# -- reachability --------------------------------------------------------------------------


@pytest.mark.parametrize("ending", [*ENDINGS, "HORIZON"])
def test_every_ending_is_reachable_from_some_initial_state(default, ending):
    """With every actor, Nature included, cooperating, each ending (and the HORIZON label
    for an unfinished, unbalanced game) can be reached from at least one initial state."""
    target = default.ending(ending)
    assert target
    assert set(default.g.initial) & default.reach(target)


def test_settled_only_from_limited_aims_and_takeover_only_from_hegemonic(default):
    """The model's point about hidden aims: a settlement is possible only if CH is limited,
    a takeover only if it is hegemonic, and INC has to act without knowing which."""
    where = {
        ending: {
            default.level(i, "aims")
            for i in default.g.initial
            if i in default.reach(default.ending(ending))
        }
        for ending in ENDINGS
    }
    assert where["SETTLED"] == {"limited"}
    assert where["TAKEOVER"] == {"hegemonic"}
    # Detection needs a concealment, and only a hegemonic CH conceals.
    assert where["CONTAINED"] == {"hegemonic"}
    assert where["COEXIST"] == {"limited", "hegemonic"}


def test_a_settlement_needs_both_players(default):
    """INC's concession and CH's expansion together force a settlement in one tick; neither
    can force it alone, and with hegemonic aims nobody can."""
    settled = default.ending("SETTLED")
    limited, hegemonic = default.start("limited"), default.start("hegemonic")
    both = attractor(default.g, {"INC", "CH"}, settled)
    assert limited in both.win and both.rank[limited] == 1
    assert hegemonic not in both.win
    for alone in ({"INC"}, {"CH"}):
        assert limited not in default.force(alone, settled)


def test_the_latch_separates_silent_from_overt_takeovers(default, appeaser):
    """TAKEOVER splits by INC's belief when control first reached 2 (the latch). A silent
    takeover (INC not yet convinced) can be forced against an appeaser, because CH needs no
    deception and so nothing is detected; an overt one exists but cannot be forced."""
    silent = V.ending("TAKEOVER") & (V.belief_at_majority != "hegemonic")
    overt = V.ending("TAKEOVER") & (V.belief_at_majority == "hegemonic")
    assert default.where(silent) and default.where(overt)
    assert default.where(silent) | default.where(overt) == default.ending("TAKEOVER")
    start = appeaser.start("hegemonic")
    assert start in appeaser.force({"CH"}, appeaser.where(silent))
    assert start in appeaser.reach(appeaser.where(overt))
    assert start not in appeaser.force({"CH"}, appeaser.where(overt))


# -- forcing, blocking and the contested region ----------------------------------------------


def test_an_appeaser_lets_ch_force_takeover_otherwise_inc_blocks_it(default, appeaser):
    """Against an incumbent that never resists, CH forces TAKEOVER from the hegemonic start in
    three expansions. Against the default incumbent it cannot, and INC needs no help from
    Nature to block it (the safety game against CH and Nature together is still won)."""
    heg_app = appeaser.start("hegemonic")
    forced = contested(appeaser.g, {"CH"}, appeaser.ending("TAKEOVER"), "reach")
    assert heg_app in forced.forced
    assert heg_app not in forced.blocked and heg_app not in forced.contested
    assert appeaser.start("limited") in forced.blocked

    heg = default.start("hegemonic")
    free = contested(default.g, {"CH"}, default.ending("TAKEOVER"), "reach")
    assert heg in free.blocked
    assert heg not in free.forced and heg not in free.contested
    no_takeover = default.everything_but(default.ending("TAKEOVER"))
    assert heg in default.keep({"INC"}, no_takeover)
    assert heg not in appeaser.keep({"INC"}, appeaser.everything_but(appeaser.ending("TAKEOVER")))


def test_incs_only_block_is_to_resist_at_tick_zero(default):
    """INC's block against a hegemonic CH is unique: resist immediately, while its belief is
    still 'uncertain'. That freezes quiet expansion for good and, since INC concedes next, CH
    gets one overt step (control 2) and no more. Any other first move loses the block."""
    heg = default.start("hegemonic")
    kernel = default.keep({"INC"}, default.everything_but(default.ending("TAKEOVER")))
    assert safe_first_moves(default, kernel, heg, "INC") == {"resist"}


def test_inc_viability_kernel_for_balance(default):
    """The intent: INC's kernel for ``balance`` contains the limited-aims start (CH cannot
    leave balance there) and excludes the hegemonic one (CH reaches control 2 in two ticks
    whatever INC does). The engine agrees. INC can still stop the takeover itself, so leaving
    the balance kernel is not the end: it is the loss of the margin."""
    limited, hegemonic = default.start("limited"), default.start("hegemonic")
    balance = default.where("balance")
    kernel = default.keep({"INC"}, balance)
    assert limited in kernel and hegemonic not in kernel
    # Nature on INC's side changes nothing; CH on INC's side restores the hegemonic start,
    # so it is CH's choices that take it out.
    assert default.keep({"INC", "Nature"}, balance) & {limited, hegemonic} == {limited}
    assert hegemonic in default.keep({"INC", "CH"}, balance)
    no_takeover = default.everything_but(default.ending("TAKEOVER"))
    assert hegemonic in default.keep({"INC"}, no_takeover) and hegemonic not in kernel


def test_hidden_aims_force_a_bet_at_tick_zero(default):
    """INC cannot tell the two initial states apart, and no first move serves both worlds:
    the only move that keeps the block against a hegemonic CH is ``resist``, which makes
    every settlement with a limited CH impossible; every other first move keeps one open."""
    g, cm = default.g, default.cm
    limited, hegemonic = default.start("limited"), default.start("hegemonic")
    assert cm.observe("INC", g.states[limited]) == cm.observe("INC", g.states[hegemonic])

    no_takeover = default.everything_but(default.ending("TAKEOVER"))
    blocks = safe_first_moves(default, default.keep({"INC"}, no_takeover), hegemonic, "INC")
    settleable = default.reach(default.ending("SETTLED"))
    inc = cm.actors[1]
    keeps_settlement = {
        inc.actions[move[inc.index]].name
        for move, successor in zip(g.moves[limited], g.succ[limited], strict=True)
        if successor in settleable
    }
    assert blocks == {"resist"}
    assert keeps_settlement == {"idle", "concede", "fund_oversight"}
    assert not blocks & keeps_settlement


def test_a_guarantee_granted_beforehand_puts_the_hegemonic_start_in_incs_kernel():
    """The lever: with a guarantee already in place CH's overt step is closed, so INC can
    resist at tick 0 and keep control at 1. It does not stop a hegemonic CH facing an
    appeaser, and it changes nothing for a limited CH, which never defects."""

    def inc_keeps_balance(aims, **start):
        world = World(aims=aims, **start)
        return world.g.initial[0] in world.keep({"INC"}, world.where("balance"))

    assert not inc_keeps_balance("hegemonic")
    assert inc_keeps_balance("hegemonic", guarantee=True)
    assert inc_keeps_balance("limited") and inc_keeps_balance("limited", guarantee=True)

    world = World(profile="appeaser", aims="hegemonic", guarantee=True)
    takeover = world.ending("TAKEOVER")
    assert world.g.initial[0] in world.force({"CH"}, takeover)


def test_a_lulled_incumbent_cannot_block():
    """If INC already believes CH is limited its ``resist`` is outside its decision space, and
    CH forces the takeover even against the default incumbent. The starting belief decides
    whether the block exists, which is what a snapshot of INC's belief is evidence for."""
    for belief, forced in (("limited", True), ("uncertain", False), ("hegemonic", False)):
        world = World(aims="hegemonic", belief=belief)
        takeover = world.ending("TAKEOVER")
        assert (world.g.initial[0] in world.force({"CH"}, takeover)) is forced, belief


def test_incs_point_of_no_return_comes_before_balance_is_lost(default):
    """The silent phase. On the shortest takeover trace (INC idle throughout) INC leaves its
    no-takeover kernel at tick 1, balance is lost at tick 2 and the takeover happens at tick
    3: by the time anything visible is wrong, the outcome is already decided."""
    g = default.g
    trace = witness(g, default.start("hegemonic"), default.ending("TAKEOVER"))
    assert len(trace) - 1 == 3
    assert [g.move_names(m)[1] for m in trace.joint_moves] == ["idle"] * 3
    kernel = default.keep({"INC"}, default.everything_but(default.ending("TAKEOVER")))
    balance = default.where("balance")
    ids = trace.state_ids
    point_of_no_return = next(k for k, s in enumerate(ids) if s not in kernel)
    balance_lost = next(k for k, s in enumerate(ids) if s not in balance)
    assert (point_of_no_return, balance_lost, len(ids) - 1) == (1, 2, 3)


# -- the assumption ---------------------------------------------------------------------------


def test_relaxing_calm_start_widens_the_initial_set_and_the_forcing_result():
    """``calm_start`` keeps the swept ``tension`` calm. Relaxing it adds the starts already in
    crisis (four initial states instead of two), and the assumption is load-bearing: in a
    crisis start quiet expansion is closed, so against an appeaser, which never resists and
    so never opens the overt step, CH can no longer force the takeover."""
    plain, relaxed = model.compile(), model.compile(relax={"calm_start"})
    assert len(plain.initial_states()) == 2
    assert len(relaxed.initial_states()) == 4
    assert set(plain.initial_states()) < set(relaxed.initial_states())
    extra = set(relaxed.initial_states()) - set(plain.initial_states())
    assert {relaxed.level_name("tension", s[relaxed.index["tension"]]) for s in extra} == {"crisis"}

    world = World(profile="appeaser", relax={"calm_start"})
    forced = world.force({"CH"}, world.ending("TAKEOVER"))
    verdict = {
        (world.level(i, "aims"), world.level(i, "tension")): i in forced for i in world.g.initial
    }
    assert verdict == {
        ("limited", "calm"): False,
        ("hegemonic", "calm"): True,
        ("limited", "crisis"): False,
        ("hegemonic", "crisis"): False,
    }


# -- bounded fairness --------------------------------------------------------------------------


def test_a_belief_flip_precedes_incs_response_by_at_most_the_fairness_bound(default):
    """Once INC believes the worst and CH has a foothold, INC may defer a response for at most
    ``within`` = 3 ticks. A witness reaches such a flip through Nature's ``detect``; from there,
    on every continuation in which INC keeps not responding, the fairness counter reaches 3
    after two more ticks and INC's available actions shrink to the responses."""
    cm, g = default.cm, default.g
    inc, nature = cm.actors[1], cm.actors[2]
    responses = {inc.action_index("resist"), inc.action_index("fund_oversight")}
    within = 3
    counter = cm.index["fair_respond"]
    triggered = default.where((V.belief == "hegemonic") & (V.control >= 1))

    # The flip: INC convinced, CH holding ground, the tick of the flip itself unanswered.
    unanswered = default.where((V.belief == "hegemonic") & (V.control >= 1) & (V.fair_respond == 1))
    trace = witness(g, default.start("hegemonic"), unanswered)
    assert trace is not None
    detect = nature.action_index("detect")
    assert any(m[nature.index] == detect for m in trace.joint_moves)
    assert default.level(trace.state_ids[0], "belief") == "uncertain"
    flip = trace.state_ids[-1]
    assert g.states[flip][counter] == 1

    # Every continuation in which INC keeps deferring (and the trigger keeps holding).
    frontier, deferred = {flip}, 0
    while True:
        later = {
            t
            for s in frontier
            if not g.terminal[s]
            for move, t in zip(g.moves[s], g.succ[s], strict=True)
            if move[inc.index] not in responses and t in triggered
        }
        if not later:
            break
        frontier, deferred = later, deferred + 1
        assert deferred <= within
    # The tick of the flip plus the deferrals make exactly ``within`` unanswered ticks, and
    # the bound is attained (it is not slack).
    assert 1 + deferred == within
    waiting = [s for s in frontier if not g.terminal[s]]
    assert waiting
    for s in waiting:
        state = g.states[s]
        assert state[counter] == within
        # cm.available is what forces the response: nothing but resist or fund_oversight.
        options = set(cm.available(state)[inc.index])
        assert options and options <= responses
        for response in options:
            after = cm.step(state, joint(cm, INC=inc.actions[response].name))
            assert after[counter] == 0


def test_the_fairness_counter_restricts_inc_in_every_reachable_state(default, appeaser):
    """In both profiles, whenever the counter has run out INC can only respond, and the
    responses are never all unavailable (the engine would have raised while exploring)."""
    for world in (default, appeaser):
        inc = world.cm.actors[1]
        responses = {inc.action_index("resist"), inc.action_index("fund_oversight")}
        spent = world.where(V.fair_respond == 3)
        assert spent
        for s in spent:
            if not world.g.terminal[s]:
                assert set(world.g.avail[s][inc.index]) <= responses
                assert world.g.avail[s][inc.index]


# -- the mechanics, one rule at a time ----------------------------------------------------------


def test_expand_is_capped_by_aims_and_closed_by_crisis(default):
    cm = default.cm
    assert "expand" in available(cm, state_from(cm, "limited", control=0), "CH")
    assert "expand" not in available(cm, state_from(cm, "limited", control=1), "CH")
    assert "expand" in available(cm, state_from(cm, "hegemonic", control=2), "CH")
    assert "expand" not in available(cm, state_from(cm, "hegemonic", tension="crisis"), "CH")
    assert "deceive" not in available(cm, state_from(cm, "limited"), "CH")
    assert "defect" not in available(cm, state_from(cm, "limited", last_INC="resist"), "CH")


def test_deceive_lowers_belief_only_while_oversight_is_not_strong(default):
    cm = default.cm
    belief = cm.index["belief"]
    for oversight, expected in (("none", "limited"), ("weak", "limited"), ("strong", "uncertain")):
        s = state_from(cm, "hegemonic", oversight=oversight)
        after = cm.step(s, joint(cm, CH="deceive"))
        assert cm.level_name("belief", after[belief]) == expected, oversight


def test_detect_needs_strong_oversight_and_a_deception_on_the_previous_tick(default):
    cm = default.cm
    watched = state_from(cm, "hegemonic", oversight="strong", last_CH="deceive")
    assert "detect" in available(cm, watched, "Nature")
    after = cm.step(watched, joint(cm, Nature="detect"))
    assert cm.level_name("belief", after[cm.index["belief"]]) == "hegemonic"
    for quiet in (
        state_from(cm, "hegemonic", oversight="weak", last_CH="deceive"),
        state_from(cm, "hegemonic", oversight="strong", last_CH="expand"),
    ):
        assert "detect" not in available(cm, quiet, "Nature")


def test_defect_needs_a_threat_and_no_guarantee(default):
    cm = default.cm
    threatened = state_from(cm, "hegemonic", last_INC="resist", tension="crisis")
    assert "defect" in available(cm, threatened, "CH")
    after = cm.step(threatened, joint(cm, CH="defect"))
    assert after[cm.index["control"]] == 1
    assert "defect" not in available(cm, state_from(cm, "hegemonic", last_INC="idle"), "CH")
    guaranteed = state_from(cm, "hegemonic", last_INC="resist", guarantee=True)
    assert "defect" not in available(cm, guaranteed, "CH")


def test_resist_needs_suspicion_and_concede_needs_no_conviction(default):
    cm = default.cm
    for belief, resist, concede in (
        ("limited", False, True),
        ("uncertain", True, True),
        ("hegemonic", True, False),
    ):
        s = state_from(cm, "hegemonic", belief=belief)
        assert ("resist" in available(cm, s, "INC")) is resist, belief
        assert ("concede" in available(cm, s, "INC")) is concede, belief
    granted = state_from(cm, "hegemonic", guarantee=True)
    assert "concede" not in available(cm, granted, "INC")
    after = cm.step(state_from(cm, "hegemonic"), joint(cm, INC="resist"))
    assert cm.level_name("tension", after[cm.index["tension"]]) == "crisis"


def test_fund_oversight_shows_three_ticks_after_it_is_chosen_and_shock_erodes_it(default):
    cm = default.cm
    oversight, pending = cm.index["oversight"], cm.index["pending_INC_fund_oversight"]
    s = cm.initial_states()[0]
    seen = []
    s = cm.step(s, joint(cm, INC="fund_oversight"))  # chosen at tick 0
    for _ in range(3):
        seen.append(
            (
                s[cm.index["tick"]],
                cm.level_name("oversight", s[oversight]),
                s[pending],
                "fund_oversight" in available(cm, s, "INC"),
            )
        )
        s = cm.step(s, joint(cm))
    assert seen == [(1, "weak", 2, False), (2, "weak", 1, False), (3, "strong", 0, True)]
    strong = state_from(cm, "hegemonic", oversight="strong")
    assert "shock" in available(cm, strong, "Nature")
    assert cm.level_name("oversight", cm.step(strong, joint(cm, Nature="shock"))[oversight]) == (
        "weak"
    )
    assert "shock" not in available(cm, state_from(cm, "hegemonic", oversight="weak"), "Nature")


def test_the_appeaser_profile_removes_resist_and_nothing_else(default, appeaser):
    inc = default.cm.actors[1]
    resist = inc.action_index("resist")
    assert any(resist in av[inc.index] for av in default.g.avail)
    assert not any(resist in av[inc.index] for av in appeaser.g.avail)
    assert {a.name for a in appeaser.cm.actors[1].actions} == {a.name for a in inc.actions}
    assert "appeaser" not in default.cm.assumptions()


def test_endings_are_exclusive_on_every_state_not_only_reachable_ones(default):
    """Exploration would raise on overlapping endings among reachable states; the toy goes
    further and keeps them exclusive on every combination of the declared variables."""
    cm = default.cm
    names = list(cm.model.endings)
    for control in range(4):
        for tension in ("calm", "crisis"):
            for oversight in ("none", "weak", "strong"):
                for belief in ("limited", "uncertain", "hegemonic"):
                    for guarantee in (False, True):
                        for aims in ("limited", "hegemonic"):
                            for tick in (0, 12):
                                s = state_from(
                                    cm,
                                    aims,
                                    control=control,
                                    tension=tension,
                                    oversight=oversight,
                                    belief=belief,
                                    guarantee=guarantee,
                                    tick=tick,
                                )
                                assert sum(cm.evaluate(n, s) for n in names) <= 1
