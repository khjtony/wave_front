"""Print the membership of the start state in H's two control kernels at each level of ``regime``.

A diagnostic taken after first sight, on the model as it stood there: the kernels are the ones
the job passes computed for G19, nothing is recomputed, no claim part is run and nothing is
written to the parts log. G19 counts the flips of ``regime`` over two states and two
directions without saying where they fall, and the snapshot carries ``regime`` as an open call
(voluntary, with mandatory as the alternative); this prints the cells behind the count.

    PYTHONPATH=. python scripts/agi_regime_call.py > reports/agi_v0_regime_call.md
"""

from __future__ import annotations

from models.agi import v0
from tests.agi.common import KD, KH, OBJECTIVES, NotComputed, compiled, inside, s0

KERNELS = {"⟨⟨H⟩⟩□balance_control": KH, "⟨⟨H⟩⟩□balance_deter": KD}


def cell(job, objective: str, start: dict[str, str]) -> str:
    cm = compiled()
    try:
        return "inside" if inside(job, cm, s0(cm, objective, **start)) else "outside"
    except NotComputed:
        return "not computed"


def main() -> None:
    print("# AGI v0: the start state at each level of `regime` (diagnostic, after first sight)\n")
    print(
        "Read from the kernels of G19 that the job passes computed. The snapshot gives "
        "`regime = voluntary` and names `mandatory` as its open alternative; every other "
        "level of the start state is as in the snapshot. `H` is unrestricted and `A` is "
        "outside the coalition, so each membership is an upper bound for `H` in the respects "
        "of agi_v0_decisions.md section 6.\n"
    )
    for name, job in KERNELS.items():
        for title, start in (("s0", {}), ("s0 with cap := agi", {"cap": "agi"})):
            print(f"## {name}, from {title}\n")
            print("| regime | " + " | ".join(OBJECTIVES) + " |")
            print("|---|" + "---|" * len(OBJECTIVES))
            for regime in v0.LEVELS["regime"]:
                row = " | ".join(cell(job, o, {**start, "regime": regime}) for o in OBJECTIVES)
                print(f"| {regime} | {row} |")
            print(flush=True)


if __name__ == "__main__":
    main()
