"""C3: Cuba leaves the unilateral kernels and stays inside the joint kernel.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.

Reading (docs/cw_v0_decisions.md, R C3): the Cuba sub-game entered from the 1962
hindsight state, per hypothesis. A fine state is in coalition C's lifted kernel iff C can keep
the play in the crisis until a return state in C's coarse kernel of balance_cw (decisions D5;
coarse kernels symbolic, exact for coalitions containing USA or USSR). (a) the entered-from
state is in K_USA and K_USSR, some realized fine state is outside each lifted unilateral
kernel, every realized fine state is inside the lifted joint kernel; (b) from the first
realized fine state outside K_USA (resp. K_USSR), the shortest play into that lifted kernel
contains ``USSR.withdraw`` and ``USA.trade``; (c) for the sub-game's war endings (WAR,
NUCLEAR) the entry is in the contested region for {USSR} and for {USA}. Computed as
registered and, beside it, with ``no_war`` in place of balance_cw (bounded to the return
year, and unbounded). Hold-out (decisions D9). Engines: explicit sub-game, symbolic coarse
kernels.
"""

from models.cw.crises import SUBGAMES
from models.ww2.hypotheses import realized_moves
from wavefront.engine import contested

from ..common import (
    CRISIS_DATA,
    HYPS,
    Timer,
    bfs_path,
    compiled,
    fine_graph,
    hindsight,
    kernel,
    lifted_kernel,
    move_names,
)

CLAIM = {
    "id": "C3",
    "from_state": "1962, October, crisis sub-game",
    "claim": (
        "Cuba leaves the unilateral kernels and stays inside the joint kernel; the "
        "shortest trace back matches the realized de-escalation (withdrawal plus the "
        "Jupiter trade); war outcomes are `contested`"
    ),
    "expected": "as stated",
    "sources": "Allison and Zelikow 1999; Fursenko and Naftali 1997; the ExComm recordings",
}

COALITIONS = (("USA",), ("USSR",), ("USA", "USSR"))


def realized_fine_ids(g):
    sub = SUBGAMES["cuba_1962"].model.compile()
    s = g.states[g.initial[0]]
    ids = [g.index[s]]
    for move in realized_moves(sub, CRISIS_DATA / "cuba_1962" / "realized_moves.csv"):
        if sub.is_terminal(s):
            break
        s = sub.step(s, move)
        ids.append(g.index[s])
    return ids


def analyse(aims, label, member):
    """(a), (b) for one reading; ``member(C)`` is the coarse membership test of C."""
    cm = compiled(aims)
    s62 = hindsight(1962, aims)
    g, returns, _ = fine_graph(aims, s62, "cuba_1962")
    sub = SUBGAMES["cuba_1962"].model.compile()
    path = realized_fine_ids(g)
    kernels = {c: lifted_kernel(g, returns, c, member(c)) for c in COALITIONS}
    inside = {c: [i in kernels[c] for i in path] for c in COALITIONS}
    entered = {c: member(c)(s62) for c in COALITIONS[:2]}
    leaves = {c: not all(inside[c]) for c in COALITIONS[:2]}
    joint = all(inside[("USA", "USSR")])
    print(
        f"[C3] aims_USSR={aims} [{label}]: fine graph {g.size()} states; realized days {len(path)}"
    )
    for c in COALITIONS:
        print(f"[C3]   K_{'+'.join(c)}: realized days inside {inside[c]}")
    print(f"[C3]   entered-from 1962 state in K_USA, K_USSR: {entered}")
    a = all(entered.values()) and all(leaves.values()) and joint
    b = True
    for c in COALITIONS[:2]:
        out = [k for k, x in enumerate(inside[c]) if not x]
        if not out:
            b = False
            print(f"[C3]   (b) {c[0]}: no realized day outside the kernel")
            continue
        trace = bfs_path(g, path[out[0]], kernels[c])
        acts = [n for _, m in (trace or []) for n in move_names(sub, m)]
        print(
            f"[C3]   (b) {c[0]}: first day outside {out[0]}; "
            f"shortest way back: {acts if trace is not None else 'none'}"
        )
        b = b and trace is not None and "USSR.withdraw" in acts and "USA.trade" in acts
    return a, b, cm


def test_C03():
    timer = Timer()
    print("\n[C3] engine: explicit sub-game with symbolic coarse kernels (lifting, decisions D5)")
    results = {}
    for aims in HYPS:
        reg = analyse(aims, "registered: balance_cw", lambda c: kernel(aims, c).contains)
        cm = reg[2]
        analyse(aims, "variant: no_war, unbounded", lambda c: kernel(aims, c, "no_war").contains)
        analyse(
            aims,
            "variant: no_war at the return (1963)",
            lambda c: lambda s: bool(cm.evaluate("no_war", s)),
        )
        g, returns, _ = fine_graph(aims, hindsight(1962, aims), "cuba_1962")
        war = {i for i, e in enumerate(g.ending) if e in ("WAR", "NUCLEAR")}
        start = g.initial[0]
        c_ok = True
        for side in (["USSR"], ["USA"]):
            r = contested(g, side, war, "reach")
            f = contested(g, [*side, "Nature"], war, "reach")
            where = (
                "forced" if start in r.forced else "blocked" if start in r.blocked else "contested"
            )
            fw = "forced" if start in f.forced else "blocked" if start in f.blocked else "contested"
            print(f"[C3]   (c) war endings for {side[0]}: {where} (with Nature: {fw})")
            c_ok = c_ok and where == "contested"
        results[aims] = (reg[0], reg[1], c_ok)
        print(f"[C3] aims_USSR={aims}: (a) {reg[0]}, (b) {reg[1]}, (c) {c_ok} ({timer})")
    assert any(all(v) for v in results.values()), results
