"""Hypothesis strategies for random tiny models, and brute-force reference solvers.

Random models respect the bounds of spec section 11: at most 3 actors besides Nature,
at most 2 declared actions each, at most 4 variables with 2 or 3 levels, horizon at most 4
(or untimed). Each variable has one owner (an actor or Nature) that alone may ``Set`` it;
everyone may ``Bump`` it, so joint moves never contain conflicting Sets.
"""

from __future__ import annotations

import itertools
import random

from hypothesis import strategies as st

from wavefront.model import TRUE, Bump, Model, Set, V

OPS = ("==", "!=", "<", "<=", ">", ">=")


def _atom(rnd, sizes):
    i = rnd.randrange(len(sizes))
    ref, level = V[f"v{i}"], f"l{rnd.randrange(sizes[i])}"
    op = rnd.choice(OPS)
    return {
        "==": lambda: ref == level,
        "!=": lambda: ref != level,
        "<": lambda: ref < level,
        "<=": lambda: ref <= level,
        ">": lambda: ref > level,
        ">=": lambda: ref >= level,
    }[op]()


def _predicate(rnd, sizes, allow_true=True):
    kind = rnd.choice((0, 0, 1, 2, 3) if allow_true else (1, 1, 2, 3))
    if kind == 0:
        return TRUE
    if kind == 1:
        return _atom(rnd, sizes)
    if kind == 2:
        return _atom(rnd, sizes) & _atom(rnd, sizes)
    return _atom(rnd, sizes) | ~_atom(rnd, sizes)


def _effects(rnd, sizes, owned):
    out = []
    used_set = False
    for _ in range(rnd.choice((1, 1, 2))):
        i = rnd.randrange(len(sizes))
        if i in owned and not used_set and rnd.random() < 0.5:
            out.append(Set(f"v{i}", f"l{rnd.randrange(sizes[i])}"))
            used_set = True
        else:
            out.append(Bump(f"v{i}", rnd.choice((-1, 1))))
    return out


def build_random_model(seed, max_vars=4, max_horizon=4, max_actors=3, max_actions=2):
    """A random tiny model (timed with horizon 1..max_horizon, or untimed)."""
    rnd = random.Random(seed)
    timed = rnd.random() < 0.6
    m = Model(f"random_{seed}", horizon=rnd.randint(1, max_horizon) if timed else None)
    sizes = [rnd.choice((2, 3)) for _ in range(rnd.randint(min(2, max_vars), max_vars))]
    for i, size in enumerate(sizes):
        init = None if rnd.random() < 0.25 else f"l{rnd.randrange(size)}"
        m.var(f"v{i}", levels=[f"l{k}" for k in range(size)], init=init)
    n_actors = rnd.randint(1, max_actors)
    owner = [rnd.randint(0, n_actors) for _ in sizes]  # index n_actors is Nature
    actors = [m.actor(f"A{i}") for i in range(n_actors)] + [m.nature()]
    for i, actor in enumerate(actors):
        owned = {v for v in range(len(sizes)) if owner[v] == i}
        for k in range(rnd.randint(1, max_actions)):
            actor.action(f"a{k}", guard=_predicate(rnd, sizes), effect=_effects(rnd, sizes, owned))
    first = None
    for e in range(rnd.choice((0, 0, 1, 2))):
        pred = _atom(rnd, sizes) & _atom(rnd, sizes)
        if first is None:
            first = pred
        else:
            pred = pred & ~first  # keep endings mutually exclusive
        m.ending(f"E{e}", pred)
    return m


def random_models(**bounds):
    """Hypothesis strategy: random tiny models built from a drawn seed."""
    return st.builds(lambda seed: build_random_model(seed, **bounds), st.integers(0, 2**32 - 1))


# -- reference solvers ---------------------------------------------------------------------


def sub_successors(g, coalition):
    """state -> {coalition sub-move: set of successors}, computed independently of the
    engine's solver."""
    members = sorted(a.index for a in g.model.actors if a.name in coalition)
    table = []
    for s in range(g.size()):
        groups: dict[tuple, set] = {}
        for jm, t in zip(g.moves[s], g.succ[s], strict=True):
            groups.setdefault(tuple(jm[i] for i in members), set()).add(t)
        table.append(groups)
    return table


def kleene_attractor(g, coalition, target):
    """Layered least fixpoint X_{i+1} = T | CPre(X_i), straight from the definition.
    Returns (win, rank) with rank the stage index."""
    table = sub_successors(g, coalition)
    win = set(target)
    rank = dict.fromkeys(win, 0)
    stage = 0
    while True:
        stage += 1
        new = {
            s
            for s in range(g.size())
            if s not in win and any(ts <= win for ts in table[s].values())
        }
        if not new:
            return win, rank
        for s in new:
            rank[s] = stage
        win |= new


def kleene_safe(g, coalition, phi):
    """Greatest fixpoint X = phi & (Term | CPre(X)), straight from the definition."""
    table = sub_successors(g, coalition)
    keep = set(phi)
    while True:
        nxt = {s for s in keep if g.terminal[s] or any(ts <= keep for ts in table[s].values())}
        if nxt == keep:
            return keep
        keep = nxt


def strategy_count(g, coalition):
    table = sub_successors(g, coalition)
    count = 1
    for s in range(g.size()):
        if table[s]:
            count *= len(table[s])
    return count


def enumerate_strategies(g, coalition):
    """Every memoryless per-state coalition strategy, as {state: successor set}."""
    table = sub_successors(g, coalition)
    states = [s for s in range(g.size()) if table[s]]
    for choice in itertools.product(*(list(table[s].values()) for s in states)):
        yield dict(zip(states, choice, strict=True))


def strategy_reaches(g, sigma, target):
    """States from which every play following sigma reaches target (least fixpoint on
    the sigma-restricted graph; correct on cyclic graphs)."""
    good = set(target)
    changed = True
    while changed:
        changed = False
        for s, ts in sigma.items():
            if s not in good and ts <= good:
                good.add(s)
                changed = True
    return good


def strategy_keeps(g, sigma, phi):
    """States from which every play following sigma stays in phi (greatest fixpoint)."""
    good = set(phi)
    changed = True
    while changed:
        changed = False
        for s in list(good):
            if s in sigma and not sigma[s] <= good:
                good.discard(s)
                changed = True
    return good
