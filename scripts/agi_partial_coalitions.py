"""Print which coalitions over {H, L, A} keep each ending of G15 away, from the cached kernels.

A diagnostic taken after first sight, on the model as it stood there: the kernels are the ones
the job passes computed for G15, nothing is recomputed, no claim part is run and nothing is
written to the parts log. G15 (a) reads not computed for the two takeover endings because the
kernel of {H} alone is missing; this prints the rows that exist beside the missing one.

    PYTHONPATH=. python scripts/agi_partial_coalitions.py > reports/agi_v0_partial_coalitions.md
"""

from __future__ import annotations

from tests.agi.common import OBJECTIVES, NotComputed, compiled, inside, s0
from tests.agi.scenarios.test_G15 import BLOCKS, COALITIONS, KEPT_AWAY


def cell(ending: str, coalition: tuple[str, ...], objective: str, start: dict[str, str]) -> str:
    cm = compiled()
    try:
        kept = inside(BLOCKS[ending, coalition], cm, s0(cm, objective, **start))
    except NotComputed:
        return "not computed"
    return "keeps it away" if kept else "does not"


def main() -> None:
    print("# AGI v0: coalitions that keep an ending away (diagnostic, after first sight)\n")
    print(
        "Read from the kernels of G15 that the job passes computed. A coalition keeps an "
        "ending away from a state when the state is inside its kernel of the ending's "
        "complement; A, in or out of the coalition, acts under its objective's profile, and "
        "Nature and Clock are in the rest.\n"
    )
    for ending in KEPT_AWAY:
        for title, start in (("s0", {}), ("s0 with cap := agi", {"cap": "agi"})):
            print(f"## {ending}, from {title}\n")
            print("| Coalition | " + " | ".join(OBJECTIVES) + " |")
            print("|---|" + "---|" * len(OBJECTIVES))
            for c in COALITIONS:
                row = " | ".join(cell(ending, c, o, start) for o in OBJECTIVES)
                print("| {" + ", ".join(c) + "} | " + row + " |")
            print(flush=True)


if __name__ == "__main__":
    main()
