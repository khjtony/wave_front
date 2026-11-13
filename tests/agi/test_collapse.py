"""tests/agi/collapse.py against a model small enough to read by hand, and the layouts of the
builds the claims G26 to G28 pair. Construction checks: nothing here reads a kernel, an
attractor or a bounded query of the AGI model."""

import pytest

from tests.agi import collapse
from tests.agi.collapse import FATAL, KEEPS, PARTNER, exit_at, game_of
from tests.agi.common import KHL, KJP, A, K, P, fixed, under
from wavefront.model import Model, Set, V
from wavefront.symbolic import encode, safe


def two_keepers() -> Model:
    """``P`` and ``Q`` each hold a latch up or drop it for good; ``N`` only makes noise."""
    m = Model("two_keepers", horizon=3)
    m.flag("p_down", monotone=True)
    m.flag("q_down", monotone=True)
    m.flag("rung", monotone=True)
    p = m.actor("P")
    p.action("drop", effect=[Set("p_down", True)], source="test")
    q = m.actor("Q")
    q.action("drop", effect=[Set("q_down", True)], source="test")
    n = m.actor("N")
    n.action("ring", guard=~V.rung, effect=[Set("rung", True)], source="test")
    return m


CASES = {
    # the invariant, each member's fixes when both drop, the verdict, and the table of P
    "p alone matters": (~V.p_down, {"P": ["idle"], "Q": []}, "one bad action: P's"),
    "either would do": (~(V.p_down & V.q_down), {"P": ["idle"], "Q": ["idle"]}, "each of P, Q"),
    "both are needed": (~(V.p_down | V.q_down), {"P": [], "Q": []}, "no member has"),
}


@pytest.mark.parametrize("case", CASES)
def test_the_exit_move_names_who_could_have_kept_the_kernel(case):
    invariant, expected, said = CASES[case]
    cm = two_keepers().compile()
    enc = encode(cm)
    kernel = safe(enc, ["P", "Q"], enc.predicate(invariant)).kernel
    (start,) = cm.initial_states()
    assert enc.holds(kernel, start)
    drop = {name: cm.actors[cm.actor_names.index(name)].action_index("drop") for name in "PQ"}
    played = tuple(drop.get(name, 0) for name in cm.actor_names)
    assert not enc.holds(kernel, cm.step(start, played))
    out = exit_at(cm, start, played, ["P", "Q"], lambda s: enc.holds(kernel, s))
    assert out["fixes"] == expected
    assert out["verdict"].startswith(said)
    assert out["one bad action"] == (case == "p alone matters")
    assert out["moves"]["P"] == out["moves"]["Q"] == "drop"
    by_case = {
        "p alone matters": {"idle": KEEPS, "drop": FATAL},
        "either would do": {"idle": KEEPS, "drop": PARTNER},
        "both are needed": {"idle": PARTNER, "drop": FATAL},
    }
    assert out["table"]["P"] == by_case[case]


def test_a_choice_that_keeps_the_kernel_is_not_an_exit():
    cm = two_keepers().compile()
    enc = encode(cm)
    kernel = safe(enc, ["P", "Q"], enc.predicate(~V.p_down)).kernel
    (start,) = cm.initial_states()
    with pytest.raises(RuntimeError, match="keeps the kernel"):
        exit_at(cm, start, (0, 0, 0), ["P", "Q"], lambda s: enc.holds(kernel, s))


def test_the_plays_and_the_kernels_of_the_collapse_claims_share_a_layout():
    """A state and a joint move of a play are read in the kernel's build as they are."""
    sp, agi = "self_preserving", {"cap": "agi"}
    plays = [fixed(o, under(o)) for o in (sp, "indifferent")] + [fixed(sp, under(sp), start=agi)]
    regions = [
        K("H+L", "not:SILENT_TAKEOVER", P),
        K("H+L", "no_overt_takeover", P),
        K("L+A", "not:CONTAINED", P),
        A("H+Nature", "CONTAINED", P),
        KHL,
        KJP,
    ]
    for cm in plays:
        for job in regions:
            assert game_of(job, cm) is not None


def test_the_collapse_parts_have_their_own_log():
    assert collapse.PARTS_LOG.name == "agi_v0_collapse_parts.jsonl"
    assert collapse.PARTS_LOG != collapse.common.PARTS_LOG
