"""C3: Cuba leaves the unilateral kernels and stays inside the joint kernel.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document. Amended 2026-10-23 on the owner's decisions 2j
(``no_war`` in place of ``balance_cw``) and 2k ("contested" in the fortune sense,
docs/ww2_testbed.md section 4.6); the previous wording is in git history and in
reports/cw_v0.md section 4.

Reading (docs/cw_v0_decisions.md, R C3, with the amendment A C3): the Cuba sub-game entered
from the 1962 hindsight state, per hypothesis. A fine state is in coalition C's lifted kernel
iff C can keep the play in the crisis until a return state in C's coarse kernel of ``no_war``
(amended; registered: balance_cw) through the horizon (decisions D5; coarse kernels symbolic,
exact for coalitions containing USA or USSR). (a) the entered-from state is in K_USA and
K_USSR, some realized fine state is outside each lifted unilateral kernel, every realized
fine state is inside the lifted joint kernel; (b) from the first realized fine state outside
K_USA (resp. K_USSR), the shortest play into that lifted kernel contains ``USSR.withdraw`` and
``USA.trade``; (c) for the sub-game's war endings (WAR, NUCLEAR), contested in the fortune
sense for each side P of {USA, USSR}: P joined by Nature forces them against the other's best
play, and the other joined by Nature keeps them away against P's best play (the standard
region is printed beside it). The registered computation (balance_cw, degenerate in 1962)
and the variant bounded to the return year (no_war at the return state, 1963) are printed
beside the amended one. Hold-out (decisions D9): the amended claim was computed once, on the
model of first sight, before the guard edit of 2026-10-23 (docs/guard_changelog_cw.md).
Engines: explicit sub-game, symbolic coarse kernels.
"""

from models.cw.crises import SUBGAMES
from models.ww2.hypotheses import realized_moves

from ..common import (
    CRISIS_DATA,
    HYPS,
    Timer,
    bfs_path,
    compiled,
    fine_graph,
    fortune,
    hindsight,
    kernel,
    lifted_kernel,
    move_names,
)

CLAIM = {
    "id": "C3",
    "from_state": "1962, October, crisis sub-game",
    "claim": (
        "with `no_war` in place of `balance_cw`: Cuba leaves the unilateral kernels "
        "`⟨⟨USA⟩⟩□no_war` and `⟨⟨USSR⟩⟩□no_war` and stays inside the joint kernel "
        "`⟨⟨USA, USSR⟩⟩□no_war`; the shortest trace back matches the realized "
        "de-escalation (withdrawal plus the Jupiter trade); war outcomes are `contested` "
        "in the fortune sense (ww2_testbed.md section 4.6): each side joined by Nature can "
        "force them against the other side's best play, and each side joined by Nature "
        "can keep them away against the other side's best play"
    ),
    "expected": "as stated; the registered `balance_cw` computation is reported beside it",
    "sources": (
        "Allison and Zelikow 1999; Fursenko and Naftali 1997; the ExComm recordings; "
        "amended 2026-10-23"
    ),
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
        # Amended 2026-10-23 (decision 2j): no_war in place of balance_cw, through the horizon.
        amd = analyse(
            aims, "amended: no_war, unbounded", lambda c: kernel(aims, c, "no_war").contains
        )
        analyse(
            aims,
            "variant: no_war at the return (1963)",
            lambda c: lambda s: bool(cm.evaluate("no_war", s)),
        )
        g, returns, _ = fine_graph(aims, hindsight(1962, aims), "cuba_1962")
        war = {i for i, e in enumerate(g.ending) if e in ("WAR", "NUCLEAR")}
        start = g.initial[0]
        # Amended 2026-10-23 (decision 2k): contested in the fortune sense.
        c_ok, table = fortune(g, ("USA", "USSR"), war, start)
        for side, (std, fw) in table.items():
            print(f"[C3]   (c) war endings for {side}: {std} (with Nature: {fw})")
        std_ok = all(std == "contested" for std, _ in table.values())
        print(f"[C3]   (c) registered (standard region for both): {std_ok}")
        print(f"[C3]   (c) amended (fortune sense for both): {c_ok}")
        print(f"[C3] aims_USSR={aims} registered: (a) {reg[0]}, (b) {reg[1]}, (c) {std_ok}")
        results[aims] = (amd[0], amd[1], c_ok)
        print(f"[C3] aims_USSR={aims} amended: (a) {amd[0]}, (b) {amd[1]}, (c) {c_ok} ({timer})")
    assert any(all(v) for v in results.values()), results
