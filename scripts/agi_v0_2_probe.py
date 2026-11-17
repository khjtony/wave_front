"""Timing probe for the kernels of AGI v0.2 (docs/agi_v0_2.html section 5).

Computes ``⟨⟨H⟩⟩□balance_control`` with ``A`` under its profile on a v0.2 build named by its
channels, with v0's engine settings, and prints seconds, node counts and peaks only: never a
membership, a status or a trace.

    PYTHONPATH=. python scripts/agi_v0_2_probe.py --channels all --memory-gb 26
"""

from __future__ import annotations

import argparse
import resource
import time

from models.agi_v0_2 import v0_2
from tests.agi.common import heavy_encoding
from tests.agi_v0_2.common import CHANNELS, OFF, ON, only
from wavefront.symbolic import safe


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--channels", choices=["all", "none", *CHANNELS], required=True)
    ap.add_argument("--memory-gb", type=int, default=26)
    args = ap.parse_args()
    cap = args.memory_gb << 30
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
    switches = {"all": ON, "none": OFF}.get(args.channels) or only(args.channels)
    cm = v0_2.build(**switches).compile(profile=v0_2.OBJECTIVE_PROFILES)
    enc = heavy_encoding(cm)
    t0 = time.perf_counter()

    def tell(st: dict) -> None:
        print(f"layer {st['tick']} {st['seconds']}s nodes {st['nodes']}", flush=True)

    safe(enc, ["H"], enc.predicate("balance_control"), on_iteration=tell)
    st = enc.mgr.stats()
    print(
        f"done v0.2 channels={args.channels} ⟨⟨H⟩⟩□balance_control: "
        f"{time.perf_counter() - t0:.1f}s peak {st['peak_nodes']} core {enc.mgr.core} maxrss_kb "
        f"{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}",
        flush=True,
    )


if __name__ == "__main__":
    main()
