"""Random models for the BMC cross-checks, and explicit-engine references.

:func:`build_rich_model` starts from the shared tiny-model generator
(:func:`helpers.random_games.build_random_model`) and adds, at random, the constructs that
generator leaves out: delayed actions, strict Bumps, ``SetIf`` and expression ``Set``s,
latches, ``remember_last``, fairness constraints, a profile (returned so the caller
selects it), ``assume`` restrictions and an invariant. Some of these can make the explicit
engine raise ``ModelError`` (conflicting Sets, a strict Bump out of range, a fairness
restriction with no available response); callers skip those models.
"""

from __future__ import annotations

import random

from helpers.random_games import _atom, _predicate, build_random_model

from wavefront.engine import attractor, explore
from wavefront.model import FALSE, Bump, ModelError, Set, SetIf, V
from wavefront.model.model import VarDecl


def build_rich_model(seed, max_vars=4, max_horizon=4):
    """A random model with extra constructs; returns ``(model, profile or None)``."""
    m = build_random_model(seed, max_vars=max_vars, max_horizon=max_horizon)
    rnd = random.Random(seed * 7919 + 17)
    sizes = [len(d.levels) for d in m.variables if isinstance(d, VarDecl)]
    users = list(m.actors)
    everyone = users + [m.nature()]

    def var():
        i = rnd.randrange(len(sizes))
        return i, f"v{i}"

    if rnd.random() < 0.4:
        actor = rnd.choice(everyone)
        i, name = var()
        effect = [Bump(name, rnd.choice((-1, 1)))]
        if rnd.random() < 0.4:
            effect.append(Set(name, f"l{rnd.randrange(sizes[i])}"))
        actor.action("d0", guard=_predicate(rnd, sizes), effect=effect, delay=rnd.choice((1, 2)))
    if rnd.random() < 0.25:
        _, name = var()
        rnd.choice(everyone).action(
            "s0", guard=_predicate(rnd, sizes), effect=Bump(name, rnd.choice((-1, 1)), strict=True)
        )
    if rnd.random() < 0.25:
        i, name = var()
        j, other = var()
        if rnd.random() < 0.5:
            effect = SetIf(_atom(rnd, sizes), name, f"l{rnd.randrange(sizes[i])}")
        else:
            effect = Set(name, V[other] + rnd.choice((-1, 1)))
        rnd.choice(everyone).action("x0", guard=_predicate(rnd, sizes), effect=effect)
    if rnd.random() < 0.3:
        rnd.choice(users).remember_last = True
    if rnd.random() < 0.3:
        _, name = var()
        m.latch("L0", of=name, when=_predicate(rnd, sizes, allow_true=False))
    if rnd.random() < 0.3:
        actor = rnd.choice(users)
        names = ["idle"] + [a.name for a in actor.actions]
        responses = rnd.sample(names, rnd.randint(1, len(names)))
        m.fairness(
            "F0",
            actor=actor.name,
            trigger=_predicate(rnd, sizes, allow_true=False),
            within=rnd.choice((1, 2)),
            responses=responses,
        )
    profile = None
    if rnd.random() < 0.3:
        actor = rnd.choice(everyone)
        names = [a.name for a in actor.actions]
        forbid = rnd.sample(names, rnd.randint(1, len(names)))
        unless = FALSE if rnd.random() < 0.3 else _predicate(rnd, sizes, allow_true=False)
        m.profile("P0", actor=actor.name, forbid=forbid, unless=unless)
        profile = "P0"
    for n in range(rnd.choice((0, 0, 1, 2))):
        m.assume(f"H{n}", _predicate(rnd, sizes, allow_true=False))
    if rnd.random() < 0.3:
        m.invariant("I0", _predicate(rnd, sizes, allow_true=False))
    return m, profile


def bound(cm):
    """The unrolling depth used by the cross-checks: the horizon, or 4 when untimed."""
    return cm.horizon if cm.timed else 4


def try_explore(cm, max_states=20_000):
    """``explore(cm)``, or ``None`` if the explicit engine raises ``ModelError``."""
    try:
        return explore(cm, max_states=max_states)
    except ModelError:
        return None


def targets(cm, rnd):
    """Targets to check: every ending, ``HORIZON``, the invariant and a random condition."""
    sizes = [v.size for v in cm.variables if v.origin == "var"]
    out = list(cm.model.endings)
    if cm.timed:
        out.append("HORIZON")
    out.extend(cm.model.invariants)
    out.append(_predicate(rnd, sizes, allow_true=False))
    return out


def target_ids(g, target):
    """State ids of ``g`` satisfying a target as :func:`wavefront.bmc.reach` reads it."""
    if isinstance(target, str) and (target in g.model.model.endings or target == "HORIZON"):
        return g.ending_states(target)
    return g.states_where(target)


def explicit_distance(g, goal):
    """Fewest transitions from some initial state to ``goal`` (rank in the attractor of
    every actor, Nature included), or ``None``."""
    rank = attractor(g, g.model.actor_names, goal).rank
    ranks = [rank[i] for i in g.initial if i in rank]
    return min(ranks) if ranks else None


def check_replay(cm, trace, holds):
    """``trace`` is a run of the explicit model ending in a state where ``holds``."""
    assert len(trace.states) == len(trace.moves) + 1
    assert trace.states[0] in set(cm.initial_states())
    for t, move in enumerate(trace.moves):
        state = trace.states[t]
        assert not cm.is_terminal(state), f"trace continues from terminal state at {t}"
        avail = cm.available(state)
        for actor, j, acts in zip(cm.actors, move, avail, strict=True):
            assert j in acts, f"{actor.name} plays unavailable action {j} at {t}"
        assert cm.step(state, move) == trace.states[t + 1], f"step {t} disagrees"
    assert holds(trace.states[-1])
