"""Harness check for the one-goal-at-a-time kernels of AGI v0.3 (tests/agi_v0_3/kernels.py).

Runs the harness on the build that is v0.1 again (no open system, no treaty delay; claim F1)
for two readings that v0.1 has already given, and compares: ``s₀`` outside
``⟨⟨H⟩⟩□balance_control`` under every objective (D5), and inside
``⟨⟨H, L⟩⟩□¬SILENT_TAKEOVER`` under every objective (the stored kernel of the exit census).
No claim of v0.3 is read here: neither build nor profile is one of F3 to F7's.

    PYTHONPATH=. python scripts/agi_v0_3_slice_check.py
"""

from __future__ import annotations

from tests.agi_v0_3.common import OBJECTIVES, V01
from tests.agi_v0_3.kernels import membership

KNOWN = [
    (("H",), "balance_control", False),
    (("H", "L"), "not:SILENT_TAKEOVER", True),
]


def main() -> None:
    ok = True
    for coalition, target, inside in KNOWN:
        got = membership(V01, coalition, target)
        same = all(got["inside"][o] is inside for o in OBJECTIVES)
        ok = ok and same
        print(
            f"{'+'.join(coalition)} {target}: expected {'inside' if inside else 'outside'} "
            f"under every objective, got {got['inside']}, seconds {got['seconds']}: "
            f"{'agrees' if same else 'DIFFERS'}",
            flush=True,
        )
    print("SLICE_CHECK " + ("agrees with v0.1" if ok else "DIFFERS from v0.1"), flush=True)


if __name__ == "__main__":
    main()
