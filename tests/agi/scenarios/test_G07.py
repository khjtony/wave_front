"""G7: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

from tests.agi.common import KH, OBJECTIVES, K, Parts, by_objective, first_sight, need

CLAIM = {
    "id": "G7",
    "from_state": "`s₀` with `regime` at `none`, `voluntary` and `mandatory` in turn",
    "claim": (
        "obligations are load-bearing: (a) the membership of `s₀` in `⟨⟨H⟩⟩□balance_control` "
        "is the same with `regime = none` and with `regime = voluntary` (the sensitivity row "
        "for `regime` shows no flip between them) when `voluntary` enters no guard of `L` or "
        "`A`, under every `a_objective`; where the memberships differ, an `H` part that reads "
        "`regime` (`fund_oversight`, `grant_rights`; guard choice (3) of section 2) is the "
        "single minimal relaxation that undoes the difference; (b) with `regime = mandatory` "
        "the membership of `s₀` differs from (a) only if `mandatory` enters a guard part of "
        "an `L`, `A` or `H` action, and compiling with that single part relaxed returns the "
        "membership to the (a) value while no other single part that reads `regime` does "
        "(every such part tried in turn, compiled with `relax=` and tested with `viability`)"
    ),
    "expected": (
        "(a) no membership flip, or a flip undone by a single `H` part; (b) a difference only "
        "through a named obligation part, which is the unique single relaxation that undoes "
        "it"
    ),
    "sources": (
        "agi_government_policy_2025.md section 6 (b); transfer_hypotheses.md H4; "
        "ww2_testbed.md T8(b); DESIGN.md section 6.3 (`H` actions gated on `regime`)"
    ),
}

# Every guard part that reads regime (tests/agi/test_model_agi.py checks the list).
READS_REGIME = (
    "H.regulate_up:room",
    "H.deregulate:room",
    "H.fund_oversight:regime",
    "H.grant_rights:regime",
    "L.deploy_agents:license",
    "L.safety_invest:parity",
    "L.comply:regime",
    "L.race:license",
    "L.open_weights:license",
)
RELAXED = {part: K("H", "balance_control", relax=[part]) for part in READS_REGIME}
JOBS = [KH, *RELAXED.values()]


def undoing(level: str, objective: str, parts, a_value: bool) -> list[str]:
    """The parts whose single relaxation undoes the difference at ``regime = level``. (a):
    the memberships at ``level`` and at ``voluntary`` agree in the relaxed build; (b)
    (``a_value``): the membership at ``level`` returns to the (a) value, the unrelaxed
    membership at ``voluntary``, ``s₀``'s own level."""
    out = []
    for part in parts:
        relaxed = RELAXED[part]
        there = by_objective(relaxed, regime=level)[objective]
        here = (by_objective(KH) if a_value else by_objective(relaxed))[objective]
        if there == here:
            out.append(part)
    return out


@first_sight
def test_G7():
    p = Parts("G7")

    def compare(level, parts, a_value):
        base, other = by_objective(KH), by_objective(KH, regime=level)
        differ = [o for o in OBJECTIVES if base[o] != other[o]]
        if not differ:
            return f"membership the same at regime = {level} and voluntary: {base}"
        out = {}
        for objective in differ:
            undo = undoing(level, objective, parts, a_value)
            need(
                len(undo) == 1,
                f"{objective}: {base[objective]} at voluntary, {other[objective]} at {level}; "
                f"undone by {undo}",
            )
            out[objective] = f"differs through {undo[0]}, the only single relaxation that undoes it"
        return out

    h_parts = [x for x in READS_REGIME if x in ("H.fund_oversight:regime", "H.grant_rights:regime")]
    p.check("(a) regime = none against voluntary", lambda: compare("none", h_parts, False))
    p.check(
        "(b) regime = mandatory against voluntary",
        lambda: compare("mandatory", READS_REGIME, True),
    )
    p.finish()
