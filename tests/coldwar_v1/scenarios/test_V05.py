"""V5: The 1969 confrontation: {USA, PRC} pivotal against the USSR (C11).

Registered 2026-10-24 in docs/coldwar_testbed.md section 9, before any cw_v1 guard. Do not
edit the claim text without a changelog entry in that document (section 8); an amended claim
is a new row V5a. The readings the model step must fix before first sight are listed in
section 9.4.

Reading (docs/cw_v1_decisions.md, R V5): ``balance_tri`` bounded to 1 January 1973 (tick 26):
states at tick 26 or later count as kept. (a) The sub-game entered from the 1969 hindsight
state by its realized coarse move (``PRC.border_clash``), at its first fine state. A fine
state is in coalition C's lifted kernel iff C keeps the play to a terminal fine state whose
return state (1970) is in C's symbolic coarse kernel of ``balance_tri`` with ``tick >= 26``
kept (exact: no crisis action from 1970 to 1972). For 1970, 1971 and 1972, the hindsight state
and the same bounded kernel. The pivotal family is the set of inclusion-minimal C ⊆ {USA,
PRC} (the empty one included) whose kernel contains the state; it must be exactly {{USA,
PRC}} at the entry and in each year. (b) On the PRC-to-Nature build, with ``balance_core``
bounded the same way, the family of minimal C ⊆ {USA} is {{USA}} at the entry (the scripted
sub-game entered by Nature from that build's 1969 hindsight state) and in each year. Control:
the 1968 hindsight state is in ``safe({PRC}, esc_sino < war)`` on the flattened game cut at
tick 23, the cut states kept iff ``esc_sino < war`` (explicit). Beside: the fortune variant
(each coalition joined by Nature) and the unbounded kernels (layered lifting). Holds iff (a),
(b) and the control under at least one hypothesis. Hold-out: total.
"""

import os

import pytest

from wavefront.engine import safe
from wavefront.model import V

from ..common import (
    HYPS,
    Timer,
    bounded_kernel,
    fine_graph,
    flat_of,
    fmt,
    graph,
    hindsight,
    layered_kernel,
    lifted_kernel,
    minimal_coalitions,
)

CLAIM = {
    "id": "V5",
    "from_state": (
        "1969 to 1972: the Sino-Soviet confrontation sub-game, entered after the clashes of "
        "2 and 15 Mar 1969, and the coarse states of 1970, 1971 and 1972; the control from "
        "1968"
    ),
    "claim": (
        "with `balance_tri := esc < conventional ∧ esc_sino < war ∧ esc_usprc < war ∧ "
        "both_or_neither`, bounded to 1 January 1973: (a) on cw_v1 the inclusion-minimal "
        "coalitions of {USA, PRC} whose kernel of `balance_tri` contains the state (the "
        "pivotal coalitions against the USSR) are exactly {{USA, PRC}} at the sub-game's "
        "entry and in each coarse year: neither the United States' signal against a strike "
        "nor Beijing's acceptance of talks keeps the Soviet strike away alone; (b) on the "
        "build with the PRC's decisions given to Nature, where a Sino-Soviet war is not a "
        "war between principals, the family for `balance_core` bounded the same way is "
        "{{USA}}; control: from the 1968 hindsight state, before the clash, "
        "`⟨⟨PRC⟩⟩□(esc_sino < war)` holds through 1 January 1970 (Beijing opened the clash "
        "that opened the strike option)"
    ),
    "expected": (
        "as stated, with the fortune variant (each coalition joined by Nature) and the "
        "unbounded kernels reported beside"
    ),
    "sources": (
        "Westad 2017; FRUS 1969–1976 vol. XVII; Burr (ed.), NSArchive EBB 49 (2001); Yang "
        "Kuisong 2000; Gerson 2010; Goldstein 2003; Kissinger 1979; re-asks C11"
    ),
}

# The first-sight switch (docs/cw_v1_decisions.md D8): the claim runs only when the owner sets
# WF_FIRST_SIGHT_CWV1=1 for the one recorded run of V1 to V10.
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_CWV1") == "1"

NAME = "sino_soviet_1969"
CUT = 26  # 1 January 1973
YEARS = (1970, 1971, 1972)
SCRIPTED = {"prc_principal": False}


def families(aims, universe, invariant, member_of, **build):
    """The pivotal family at the sub-game's entry and in each coarse year: the minimal
    coalitions of ``universe`` whose kernel (``member_of(C)``, a coarse membership test)
    contains the state, the entry valued by lifting."""
    fm = flat_of(aims, **build)
    g, returns, _ = fine_graph(fm, hindsight(1969, aims, **build), NAME)
    first = g.initial[0]
    out = {
        "entry": minimal_coalitions(
            universe, lambda c: first in lifted_kernel(g, returns, c, member_of(c))
        )
    }
    for y in YEARS:
        s = hindsight(y, aims, **build)
        out[y] = minimal_coalitions(universe, lambda c, s=s: member_of(c)(s))
    return out, g.size()


def bounded(aims, invariant, nature=False, **build):
    def member_of(c):
        c = tuple(sorted({*c, "Nature"})) if nature else tuple(c)
        return bounded_kernel(aims, c, invariant, CUT, **build).contains

    return member_of


def unbounded(aims, invariant, **build):
    def member_of(c):
        return layered_kernel(aims, tuple(c), invariant, **build).contains

    return member_of


def show(fam):
    return {k: fmt(v) for k, v in fam.items()}


@pytest.mark.skipif(not FIRST_SIGHT, reason="cw_v1 first sight not switched on")
def test_V5():
    timer = Timer()
    print("\n[V5] engine: explicit sub-game lifted to symbolic bounded kernels (to 1 Jan 1973)")
    results = {}
    for aims in HYPS:
        fam, size = families(aims, ("USA", "PRC"), "balance_tri", bounded(aims, "balance_tri"))
        a = all(v == [frozenset({"USA", "PRC"})] for v in fam.values())
        print(
            f"[V5] aims_USSR={aims}: sub-game {size} states; (a) pivotal families {show(fam)}: {a}"
        )
        fortune, _ = families(
            aims, ("USA", "PRC"), "balance_tri", bounded(aims, "balance_tri", nature=True)
        )
        unb, _ = families(aims, ("USA", "PRC"), "balance_tri", unbounded(aims, "balance_tri"))
        print(f"[V5]   beside (a): fortune {show(fortune)}; unbounded {show(unb)}")
        famb, sizeb = families(
            aims, ("USA",), "balance_core", bounded(aims, "balance_core", **SCRIPTED), **SCRIPTED
        )
        b = all(v == [frozenset({"USA"})] for v in famb.values())
        print(f"[V5]   (b) PRC-to-Nature build ({sizeb} states): families {show(famb)}: {b}")
        fortune_b, _ = families(
            aims,
            ("USA",),
            "balance_core",
            bounded(aims, "balance_core", nature=True, **SCRIPTED),
            **SCRIPTED,
        )
        unb_b, _ = families(
            aims, ("USA",), "balance_core", unbounded(aims, "balance_core", **SCRIPTED), **SCRIPTED
        )
        print(f"[V5]   beside (b): fortune {show(fortune_b)}; unbounded {show(unb_b)}")
        fm = flat_of(aims)
        s68 = hindsight(1968, aims)
        g = graph(fm, s68, cut=23)
        phi = {
            i
            for i, s in enumerate(g.states)
            if fm.is_fine(s) or fm.coarse.evaluate(V.esc_sino < "war", s)
        }
        control = g.index[s68] in safe(g, ["PRC"], phi).kernel
        print(f"[V5]   control: 1968 state in PRC's kernel of esc_sino < war to 1970: {control}")
        results[aims] = (a, b, control)
        print(f"[V5] aims_USSR={aims}: (a) {a}, (b) {b}, control {control} ({timer})")
    assert any(all(v) for v in results.values()), results
