"""G7: registered 2026-10-17 in docs/agi_testbed.md section 5.

The AGI model of DESIGN.md sections 2 and 3 (quarterly ticks, 2026Q4 to 2040Q4) with the
hidden objective swept; phase 5. Do not edit the claim text without a changelog entry in that
document.
"""

import pytest

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


@pytest.mark.skip(reason="registered before any guard is written; the model does not exist yet")
def test_G7():
    raise NotImplementedError(CLAIM["id"])
