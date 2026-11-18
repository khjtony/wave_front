"""Timing probe: one kernel of AGI v0.1 computed for one objective at a time.

In v0 and v0.1 no action writes ``a_objective``, so ``⟨⟨C⟩⟩□φ`` restricted to the states of one
objective is the kernel of ``φ ∧ a_objective = o``: the four objectives are four independent
computations that the claims run as one. This probe computes ``⟨⟨H⟩⟩□balance_control`` (``A``
under its profile; D5's kernel: 3,407 s and 10.4 GB as one computation) for one objective and
prints seconds, node counts and peaks only, never a membership.

    PYTHONPATH=. python scripts/agi_v0_1_split_probe.py --objective self_preserving --memory-gb 7
"""

from __future__ import annotations

import argparse
import resource
import time

from models.agi_v0_1 import v0_1
from tests.agi.common import heavy_encoding
from wavefront.model import V
from wavefront.symbolic import safe


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--objective", choices=v0_1.OBJECTIVES, required=True)
    ap.add_argument("--memory-gb", type=int, default=7)
    ap.add_argument(
        "--gc-million-nodes",
        type=int,
        default=40,
        help="collect garbage above this many million nodes (v0's jobs defer to 120, about "
        "6 GB, which a small cap cannot hold)",
    )
    args = ap.parse_args()
    cap = args.memory_gb << 30
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
    cm = v0_1.build().compile(profile=tuple(v0_1.OBJECTIVE_PROFILES))
    enc = heavy_encoding(cm)
    enc.mgr.gc_min_nodes = args.gc_million_nodes * 1_000_000
    t0 = time.perf_counter()
    phi = enc.mgr.AND(
        enc.predicate("balance_control"), enc.predicate(V.a_objective == args.objective)
    )
    enc.mgr.protect(phi)
    safe(enc, ["H"], phi)
    st = enc.mgr.stats()
    print(
        f"done v0.1 ⟨⟨H⟩⟩□balance_control, {args.objective} only, gc at "
        f"{args.gc_million_nodes}M: "
        f"{time.perf_counter() - t0:.1f}s peak {st['peak_nodes']} maxrss_kb "
        f"{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}",
        flush=True,
    )


if __name__ == "__main__":
    main()
