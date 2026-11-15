"""Timing probe for the kernels of AGI v0.1 (docs/agi_v0_1.md section 6).

Computes ``⟨⟨H⟩⟩□balance_control`` (the baseline kernel, ``A`` unrestricted, every objective
at once) on v0 and on v0.1 with v0's engine settings (FORCE order, deferred collection) and
prints seconds, node counts and peaks only: never a membership, a status or a trace.

    python scripts/agi_v0_1_probe.py --version v0.1 --memory-gb 24
"""

from __future__ import annotations

import argparse
import resource
import time

from models.agi import v0
from models.agi_v0_1 import v0_1
from tests.agi.common import heavy_encoding
from wavefront.symbolic import safe


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", choices=["v0", "v0.1"], required=True)
    ap.add_argument("--memory-gb", type=int, default=24)
    args = ap.parse_args()
    cap = args.memory_gb << 30
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
    mod = v0 if args.version == "v0" else v0_1
    cm = mod.model.compile()
    enc = heavy_encoding(cm)
    t0 = time.perf_counter()

    def tell(st: dict) -> None:
        print(f"layer {st['tick']} {st['seconds']}s nodes {st['nodes']}", flush=True)

    safe(enc, ["H"], enc.predicate("balance_control"), on_iteration=tell)
    st = enc.mgr.stats()
    print(
        f"done {args.version} ⟨⟨H⟩⟩□balance_control: {time.perf_counter() - t0:.1f}s "
        f"peak {st['peak_nodes']} core {enc.mgr.core} maxrss_kb "
        f"{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}",
        flush=True,
    )


if __name__ == "__main__":
    main()
