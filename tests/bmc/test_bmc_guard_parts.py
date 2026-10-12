"""Guards declared as named parts in the bounded encoding: one assumption Bool per part,
``reach`` and ``relax`` over part names, and agreement with ``relax_explicit``."""

import random

import pytest

from wavefront.analysis import relax_explicit
from wavefront.bmc import encode, reach, relax
from wavefront.model import Model, ModelError, Set, V


def two_of_three():
    """``A.go`` needs ``a``, ``b`` and ``c``; only ``a`` holds and nothing sets the others,
    so reaching ``DONE`` needs exactly the parts ``b`` and ``c`` relaxed. ``B.alt`` reaches
    it too but needs all three of its parts relaxed."""
    m = Model("parts", horizon=3)
    m.flag("a", init=True)
    m.flag("b")
    m.flag("c")
    m.flag("done")
    m.actor("A").action(
        "go", guard={"a": V.a, "b": V.b, "c": V.c}, effect=Set("done", True), source="test"
    )
    m.actor("B").action(
        "alt",
        guard=[("x", V.b), ("y", V.c), ("z", ~V.a)],
        effect=Set("done", True),
        source="test",
    )
    m.ending("DONE", V.done)
    return m


def test_one_assumption_bool_per_part():
    enc = encode(two_of_three().compile(), 2)
    assert enc.names == ["A.go:a", "A.go:b", "A.go:c", "B.alt:x", "B.alt:y", "B.alt:z"]


def test_relax_finds_the_two_parts():
    cm = two_of_three().compile()
    r = relax(cm, 3, "DONE")
    assert not r.reachable_as_is
    assert r.minimum_size == 2
    assert r.minimal_sets == [["A.go:b", "A.go:c"]]
    assert set(r.core) <= set(cm.assumptions()) and r.core
    assert r.trace is not None and r.trace.relaxed == ["A.go:b", "A.go:c"]
    relaxed = two_of_three().compile(relax=r.minimal_sets[0])
    state = r.trace.states[0]
    for move in r.trace.moves:
        state = relaxed.step(state, move)
    assert relaxed.ending_of(state) == "DONE"


def test_reach_over_part_names():
    cm = two_of_three().compile()
    assert reach(cm, 3, "DONE") is None
    assert reach(cm, 3, "DONE", relax={"A.go:b"}) is None
    t = reach(cm, 3, "DONE", relax={"A.go:b", "A.go:c"})
    assert t is not None and len(t) == 1 and t.relaxed == ["A.go:b", "A.go:c"]
    # the action name stands for all of its parts
    t = reach(cm, 3, "DONE", relax={"A.go"})
    assert t is not None and t.relaxed == ["A.go:a", "A.go:b", "A.go:c"]
    with pytest.raises(ModelError, match="unknown assumption"):
        reach(cm, 3, "DONE", relax={"A.go:nope"})


def test_a_model_compiled_with_relaxed_parts_needs_the_rest():
    cm = two_of_three().compile(relax={"A.go:b"})
    r = relax(cm, 3, "DONE")
    assert r.minimum_size == 1 and r.minimal_sets == [["A.go:c"]]


# -- cross-check with the explicit search --------------------------------------------------


def random_parted_model(seed):
    """Flags ``f0..f2`` and ``win``; ``A``, ``B`` and Nature each have one action whose
    guard is a plain literal or two or three named literal parts over ``f0..f2``. ``A``'s
    action sets ``win`` (the ending ``WIN``), the others set a random ``f`` flag to
    ``True`` (so no two Sets conflict)."""
    rng = random.Random(seed)
    flags = ["f0", "f1", "f2"]
    m = Model(f"r{seed}", horizon=3)
    for f in flags:
        m.flag(f, init=rng.random() < 0.4)
    m.flag("win")

    def literal():
        f = rng.choice(flags)
        return V[f] if rng.random() < 0.6 else ~V[f]

    for k, actor in enumerate([m.actor("A"), m.actor("B"), m.nature()]):
        n = rng.choice([1, 2, 2, 3])
        guard = literal() if n == 1 else {f"p{i}": literal() for i in range(n)}
        target = "win" if k == 0 else rng.choice(flags)
        actor.action("x", guard=guard, effect=Set(target, True), source="test")
    m.ending("WIN", V.win)
    return m


def test_relax_agrees_with_relax_explicit_on_parted_models():
    checked, sizes = 0, set()
    for seed in range(80):
        m = random_parted_model(seed)
        cm = m.compile()
        names = cm.assumptions()
        if len(names) > 8:
            continue
        explicit = relax_explicit(m, "WIN", max_size=len(names))
        assert explicit.ill_formed == [] and explicit.undecided == []
        bmc = relax(cm, m.horizon, "WIN", max_relax=len(names), max_sets=100)
        if not explicit:
            assert bmc.minimum_size is None, seed
            continue
        size = explicit.minimum_size
        assert bmc.minimum_size == size, seed
        expected = {frozenset(s) for s in explicit if len(s) == size}
        assert {frozenset(s) for s in bmc.minimal_sets} == expected, seed
        sizes.add(size)
        checked += 1
    assert checked >= 40 and {0, 1, 2} <= sizes
